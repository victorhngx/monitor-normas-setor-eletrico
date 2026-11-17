import pytest

from monitor_normas.chat import PADRAO_CHAT, gerar_chat
from monitor_normas.extracao_leis_org import extrair, hash_canonico, processar
from tests.test_extracao_regras import HTML

FONTE = {"url": "https://leis.org/x", "capturado_em": "2026-11-17T09:36:44"}


@pytest.fixture(scope="module")
def texto():
    canonico = extrair(HTML)
    canonico["hash_canonico"] = hash_canonico(canonico)
    return gerar_chat(canonico, "ren-1000-2021", FONTE)


def test_guia_de_leitura(texto):
    assert texto.startswith("# RESOLUÇÃO NORMATIVA ANEEL Nº 1.000, DE 7 DE DEZEMBRO DE 2021\n")
    assert "- Capturado em: 17/11/2026." in texto
    assert "Início de vigência: 03/01/2022 (art. 679)." in texto
    assert f"padrão {PADRAO_CHAT}," in texto
    assert "## Como ler este arquivo" in texto
    assert "Como responder sobre uma data específica" in texto
    assert 'Citação: use a forma "art. 6º, § 1º, da REN nº 1.000/2021"' in texto
    assert '"[rótulo repetido na fonte]"' in texto


def test_atos_que_alteraram_em_ordem(texto):
    lista = texto.split("## Atos que alteraram a norma")[1].split("## Texto da norma")[0]
    itens = [linha for linha in lista.splitlines() if linha.startswith("- ")]
    assert itens == [
        "- Resolução Normativa nº 1042/2022, de 20/09/2022",
        "- Resolução Normativa nº 1059/2023, de 07/02/2023",
        "- Resolução Normativa nº 1174/2026, de 27/10/2026: Aprimora a regulação.",
    ]


def test_redacao_atual_com_data_e_anterior_com_periodo(texto):
    assert (
        "§ 1º A distribuidora deve cadastrar de imediato. (Redação dada pela Resolução "
        "Normativa nº 1042/2022, de 20/09/2022)\n"
        "> Redação original, vigente de 03/01/2022 até 20/09/2022: Parágrafo único. "
        "A distribuidora deve cadastrar de imediato.\n"
    ) in texto
    assert (
        "§ 2º A distribuidora deve corrigir os dados. (Redação acrescida pela Resolução "
        "Normativa nº 1042/2022, de 20/09/2022)\n"
    ) in texto


def test_suprimido_mantem_texto_e_periodo(texto):
    assert (
        "I - [SUPRIMIDO: Suprimido pela nova redação do § 1º (Redação dada pela Resolução "
        "Normativa nº 1059/2023), a partir de 07/02/2023]\n"
        "> Redação original, vigente de 03/01/2022 até 07/02/2023: I - a proporcionalização "
        "deve considerar a demanda; e\n"
    ) in texto


def test_grupo_revogado_traz_os_filhos_como_historico(texto):
    assert (
        "§ 4º [REVOGADO: Revogado pela Resolução Normativa nº 1174/2026, a partir de "
        "27/10/2026]\n"
        "> Redação original, vigente de 03/01/2022 até 27/10/2026: § 4º O prazo mínimo de "
        "denúncia do CCER é de:\n\n"
        "> I - 180 dias para os CCER com prazo determinado; e\n"
    ) in texto


def test_artigo_rotulo_repetido_texto_transcrito_e_tabela(texto):
    assert "**Art. 160.** O consumidor do grupo A pode optar pelo ACL." in texto
    assert "I - [rótulo repetido na fonte] visita técnica." in texto
    assert '"Art. 6º.. ...........' in texto
    assert (
        "| 3 | art. 133, § 4º, I | 10 dias úteis | notificar | Revogado pela Resolução "
        "Normativa nº 1174/2026, de 27/10/2026 |"
    ) in texto
    assert "<a id=" not in texto


def test_processar_grava_e_regrava_se_faltar(tmp_path):
    html = tmp_path / "20261117T093644-abc.html"
    html.write_text(HTML, encoding="utf-8")
    pastas = {
        nome: tmp_path / nome
        for nome in (
            "pasta_canonico",
            "pasta_markdown",
            "pasta_revisao",
            "pasta_chat",
            "pasta_correcoes",
        )
    }
    resultado = processar(html, "ren-1000-2021", "https://leis.org/x", **pastas)
    assert resultado["chat"].name == "ren-1000-2021.md"
    assert "## Texto da norma" in resultado["chat"].read_text(encoding="utf-8")

    resultado["chat"].unlink()
    assert processar(html, "ren-1000-2021", "https://leis.org/x", **pastas)["chat"].exists()
