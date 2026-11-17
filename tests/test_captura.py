from datetime import UTC, datetime

import pytest

from monitor_normas.captura import (
    USER_AGENT,
    AcessoBloqueado,
    ErroCaptura,
    Resposta,
    cabecalho_credencial,
    capturar,
)
from monitor_normas.catalogo import Norma

NORMA = Norma(
    id="ren-1000-2021",
    titulo="REN 1.000/2021",
    fonte="leis.org",
    url="https://leis.org/aneel/ren-1000",
    formato="html",
    ativa=True,
)
AGORA = datetime(2026, 11, 17, 10, 0, 0, tzinfo=UTC)
PAGINA = "<html><title>REN 1.000</title><body>Art. 1º Texto.</body></html>".encode()


class FonteFalsa:
    """Substitui o acesso à internet nos testes e guarda os cabeçalhos enviados."""

    def __init__(self, resposta):
        self.resposta = resposta
        self.cabecalhos = None

    def __call__(self, url, cabecalhos):
        self.cabecalhos = dict(cabecalhos)
        return self.resposta


def test_captura_salva_arquivo_e_calcula_hash(tmp_path):
    fonte = FonteFalsa(Resposta(200, PAGINA))
    captura = capturar(NORMA, tmp_path, abrir=fonte, ambiente={}, agora=AGORA)

    assert captura.arquivo.read_bytes() == PAGINA
    assert captura.arquivo.parent == tmp_path / "ren-1000-2021"
    assert captura.arquivo.name.startswith("20261117T100000Z-")
    assert captura.arquivo.suffix == ".html"
    assert len(captura.sha256) == 64
    assert captura.tamanho == len(PAGINA)


def test_mesmo_conteudo_gera_mesmo_hash(tmp_path):
    a = capturar(NORMA, tmp_path / "a", abrir=FonteFalsa(Resposta(200, PAGINA)), ambiente={})
    b = capturar(NORMA, tmp_path / "b", abrir=FonteFalsa(Resposta(200, PAGINA)), ambiente={})
    assert a.sha256 == b.sha256


def test_identifica_se_com_user_agent_do_projeto(tmp_path):
    fonte = FonteFalsa(Resposta(200, PAGINA))
    capturar(NORMA, tmp_path, abrir=fonte, ambiente={})
    assert fonte.cabecalhos == {"User-Agent": USER_AGENT}


def test_envia_credencial_configurada(tmp_path):
    fonte = FonteFalsa(Resposta(200, PAGINA))
    ambiente = {"LEIS_ORG_CABECALHO_ACESSO": "X-Acesso-Autorizado: abc123"}
    capturar(NORMA, tmp_path, abrir=fonte, ambiente=ambiente)
    assert fonte.cabecalhos["X-Acesso-Autorizado"] == "abc123"


@pytest.mark.parametrize("valor", ["semdoispontos", ": valor", "Nome:  "])
def test_credencial_mal_formatada(valor):
    with pytest.raises(ErroCaptura, match="formato"):
        cabecalho_credencial("leis.org", {"LEIS_ORG_CABECALHO_ACESSO": valor})


def test_sem_credencial_nao_envia_cabecalho_extra():
    assert cabecalho_credencial("leis.org", {}) == {}


@pytest.mark.parametrize(
    "resposta",
    [
        Resposta(403, b"<html><title>Just a moment...</title></html>"),
        Resposta(403, b"forbidden"),
        Resposta(429, b"too many requests"),
        Resposta(200, b"<html>...</html>", {"cf-mitigated": "challenge"}),
        Resposta(200, b"<html><head><title>Um momento\xe2\x80\xa6</title></head></html>"),
    ],
)
def test_bloqueio_ou_verificacao_anti_robo(tmp_path, resposta):
    with pytest.raises(AcessoBloqueado, match="acesso autorizado"):
        capturar(NORMA, tmp_path, abrir=FonteFalsa(resposta), ambiente={})
    assert not any(tmp_path.rglob("*.html"))


@pytest.mark.parametrize("resposta", [Resposta(500, b"erro"), Resposta(200, b"")])
def test_erro_da_fonte(tmp_path, resposta):
    with pytest.raises(ErroCaptura) as erro:
        capturar(NORMA, tmp_path, abrir=FonteFalsa(resposta), ambiente={})
    assert not isinstance(erro.value, AcessoBloqueado)
