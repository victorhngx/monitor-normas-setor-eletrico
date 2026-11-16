import pytest

from monitor_normas import catalogo
from monitor_normas.catalogo import ErroCatalogo, carregar_catalogo, validar


def norma_valida(**alteracoes):
    norma = {
        "id": "ren-1000-2021",
        "titulo": "Resolução Normativa ANEEL nº 1.000/2021",
        "fonte": "leis.org",
        "url": "https://leis.org/aneel/lei/resolucao-normativa/2021/1000/",
        "formato": "html",
        "ativa": True,
    }
    norma.update(alteracoes)
    return norma


def test_catalogo_real_e_valido_e_tem_a_ren_1000_ativa():
    normas = carregar_catalogo()
    ren = {n.id: n for n in normas}["ren-1000-2021"]
    assert ren.ativa
    assert ren.fonte == "leis.org"


def test_catalogo_valido():
    normas = validar(
        {
            "normas": [
                norma_valida(),
                norma_valida(
                    id="prodist-modulo-1",
                    titulo="PRODIST Módulo 1",
                    fonte="aneel-git",
                    url="https://git.aneel.gov.br/publico/centralconteudo/-/tree/main/procreg",
                    formato="pdf",
                    ativa=False,
                ),
            ]
        }
    )
    assert [n.id for n in normas] == ["ren-1000-2021", "prodist-modulo-1"]


@pytest.mark.parametrize(
    "dados",
    [
        None,
        {},
        {"normas": []},
        {"normas": "ren-1000"},
        {"normas": [norma_valida()], "extra": 1},
    ],
)
def test_estrutura_invalida(dados):
    with pytest.raises(ErroCatalogo):
        validar(dados)


@pytest.mark.parametrize(
    ("alteracoes", "trecho_da_mensagem"),
    [
        ({"id": "REN 1000"}, "id deve ter"),
        ({"id": "ren--1000"}, "id deve ter"),
        ({"titulo": "  "}, "titulo não pode ficar vazio"),
        ({"fonte": "dou"}, "fonte deve ser"),
        ({"formato": "docx"}, "formato deve ser"),
        ({"ativa": "sim"}, "ativa deve ser true ou false"),
        ({"url": "http://leis.org/aneel/x"}, "https://"),
        ({"url": "https://exemplo.com/norma"}, "endereço leis.org"),
        ({"url": 123}, "url deve ser um texto"),
        ({"obs": "campo a mais"}, "campos desconhecidos: obs"),
    ],
)
def test_campo_invalido(alteracoes, trecho_da_mensagem):
    with pytest.raises(ErroCatalogo, match=trecho_da_mensagem):
        validar({"normas": [norma_valida(**alteracoes)]})


def test_campo_faltando():
    norma = norma_valida()
    del norma["url"]
    with pytest.raises(ErroCatalogo, match="campos faltando: url"):
        validar({"normas": [norma]})


def test_id_repetido():
    with pytest.raises(ErroCatalogo, match="id repetido"):
        validar({"normas": [norma_valida(), norma_valida()]})


def test_toml_quebrado(tmp_path):
    arquivo = tmp_path / "catalogo.toml"
    arquivo.write_text("[[normas]]\nid = ", encoding="utf-8")
    with pytest.raises(ErroCatalogo, match="TOML inválido"):
        carregar_catalogo(arquivo)


def test_arquivo_inexistente(tmp_path):
    with pytest.raises(ErroCatalogo, match="não encontrado"):
        carregar_catalogo(tmp_path / "nao-existe.toml")


def test_comando_lista_so_as_normas_ativas(tmp_path, capsys):
    arquivo = tmp_path / "catalogo.toml"
    arquivo.write_text(
        """
[[normas]]
id = "ativa"
titulo = "Norma ativa"
fonte = "leis.org"
url = "https://leis.org/ativa"
formato = "html"
ativa = true

[[normas]]
id = "inativa"
titulo = "Norma inativa"
fonte = "leis.org"
url = "https://leis.org/inativa"
formato = "html"
ativa = false
""",
        encoding="utf-8",
    )
    assert catalogo.main(arquivo) == 0
    saida = capsys.readouterr().out
    assert "2 norma(s), 1 ativa(s)" in saida
    assert "https://leis.org/ativa" in saida
    assert "https://leis.org/inativa" not in saida


def test_comando_com_catalogo_invalido(tmp_path, capsys):
    arquivo = tmp_path / "catalogo.toml"
    arquivo.write_text('[[normas]]\nid = "x"\n', encoding="utf-8")

    assert catalogo.main(arquivo) == 1
    assert "Catálogo inválido" in capsys.readouterr().out
