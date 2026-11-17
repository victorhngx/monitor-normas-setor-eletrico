import json

import pytest

from monitor_normas.extracao_leis_org import extrair, processar
from monitor_normas.rag import (
    ancestrais,
    citacao,
    citacao_curta,
    gerar_trechos,
    redacao_em,
    romano,
    sigla_norma,
)
from tests.test_extracao_regras import HTML

SIGLA = "REN nº 1.000/2021"


@pytest.fixture(scope="module")
def canonico():
    return extrair(HTML)


@pytest.fixture(scope="module")
def trechos(canonico):
    return {t["id"]: t for t in gerar_trechos(canonico, "ren-1000-2021")}


def test_sigla_e_romano():
    titulo = "RESOLUÇÃO NORMATIVA ANEEL Nº 1.000, DE 7 DE DEZEMBRO DE 2021"
    assert sigla_norma(titulo, "x") == SIGLA
    assert sigla_norma(None, "ren-1000-2021") == "ren-1000-2021"
    assert [romano(n) for n in (1, 4, 9, 14, 40, 64)] == ["I", "IV", "IX", "XIV", "XL", "LXIV"]


@pytest.mark.parametrize(
    ("ident", "tipo", "esperado"),
    [
        ("art6", "artigo", "art. 6º, caput"),
        ("art10", "artigo", "art. 10, caput"),
        ("art48-A", "artigo", "art. 48-A, caput"),
        ("art6_par1", "paragrafo", "art. 6º, § 1º"),
        ("art6_par12", "paragrafo", "art. 6º, § 12"),
        ("art1_parunico", "paragrafo", "art. 1º, parágrafo único"),
        ("art2_inc1-A_alia", "alinea", 'art. 2º, caput, inciso I-A, alínea "a"'),
        ("art133_par3_inc2_alib", "alinea", 'art. 133, § 3º, inciso II, alínea "b"'),
        ("art668_inc3_alid_2", "alinea", 'art. 668, caput, inciso III, alínea "d" (2ª ocorrência)'),
        ("anexo1_it4.1.1", "item", "Anexo I, item 4.1.1"),
        ("anexo4_texto1", "texto", "Anexo IV"),
    ],
)
def test_citacao_curta(ident, tipo, esperado):
    assert citacao_curta({"id": ident, "tipo": tipo}) == esperado


def test_citacao_completa_e_clausula():
    assert citacao({"id": "art6_par1", "tipo": "paragrafo"}, SIGLA) == (
        "art. 6º, § 1º, da REN nº 1.000/2021"
    )
    clausula = {"id": "anexo1_cl1", "tipo": "clausula", "texto": "CLÁUSULA PRIMEIRA: DO OBJETO"}
    assert citacao_curta(clausula) == "Anexo I, Cláusula primeira"


def test_ancestrais():
    assert ancestrais("art6") == []
    assert ancestrais("art108_par1_inc1") == ["art108", "art108_par1"]
    assert ancestrais("art668_inc3_alid_2") == ["art668", "art668_inc3"]
    assert ancestrais("art6_par1_texto3") == ["art6", "art6_par1"]
    assert ancestrais("anexo1_it4.2.1") == ["anexo1_it4", "anexo1_it4.2"]


def test_redacao_em_data():
    d = {
        "redacoes": [
            {
                "texto": "antiga",
                "situacao": "substituida",
                "vigente_de": "2022-01-03",
                "vigente_ate": "2023-02-07",
            },
            {
                "texto": "nova",
                "situacao": "vigente",
                "vigente_de": "2023-02-07",
                "vigente_ate": None,
            },
        ]
    }
    assert redacao_em(d, "2022-06-01")["texto"] == "antiga"
    assert redacao_em(d, "2023-02-07")["texto"] == "nova"
    assert redacao_em(d, None)["texto"] == "nova"


def test_trecho_vigente_com_contexto(trechos):
    t = trechos["art2_inc1-A_alia#1"]
    assert t["citacao"] == 'art. 2º, caput, inciso I-A, alínea "a", da REN nº 1.000/2021'
    assert [c["dispositivo"] for c in t["contexto"]] == ["art2", "art2_inc1-A"]
    assert t["situacao"] == "vigente"
    assert t["vigente_de"] == "2022-01-03"
    linhas = t["conteudo"].split("\n")
    assert linhas[0] == "REN nº 1.000/2021 > CAPÍTULO I - Das Regras"
    assert linhas[1] == t["citacao"]
    assert "Contexto (art. 2º, caput): Para os fins desta Resolução" in t["conteudo"]
    assert linhas[-1] == "a) unidades de mesma titularidade;"


def test_renumeracao_gera_um_trecho_por_redacao(trechos):
    antiga, nova = trechos["art6_par1#1"], trechos["art6_par1#2"]
    assert antiga["rotulo"] == "Parágrafo único."
    assert antiga["situacao"] == "substituida"
    assert (antiga["vigente_de"], antiga["vigente_ate"]) == ("2022-01-03", "2022-09-20")
    assert "(antes: Parágrafo único)" in antiga["conteudo"]
    assert "vigorou de 03/01/2022 a 20/09/2022" in antiga["conteudo"]
    assert antiga["ids_anteriores"] == ["art6_parunico"]
    assert nova["situacao"] == "vigente"
    assert (
        "vigente desde 20/09/2022 (data de publicação do ato; conferir vigência)"
        in (nova["conteudo"])
    )


def test_suprimido_tem_contexto_da_epoca(trechos):
    t = trechos["art108_par1_inc1#1"]
    assert t["situacao"] == "suprimida"
    assert t["vigente_ate"] == "2023-02-07"
    pai = t["contexto"][-1]
    assert pai["dispositivo"] == "art108_par1"
    assert pai["texto"].endswith("observadas as seguintes condições:")
    assert "Suprimido pela nova redação do § 1º" in t["conteudo"]


def test_revogado_e_texto_transcrito(trechos):
    revogado = trechos["art133_par4_inc1#1"]
    assert revogado["situacao"] == "revogada"
    assert (
        "Revogado pela Resolução Normativa nº 1174/2026; vigorou de 03/01/2022"
        in (revogado["conteudo"])
    )
    artigo = trechos["art675#1"]
    assert 'Texto transcrito: "Art. 6º.. ...........' in artigo["conteudo"]


def test_linhas_da_tabela(trechos):
    t = trechos["anexo4_tab1_l2"]
    assert t["citacao"] == "Anexo IV, tabela 1, linha 2, da REN nº 1.000/2021"
    assert t["dispositivo"] == "art108_par2"
    assert "Dispositivo: art. 108, § 2º | Prazo: 10 dias úteis" in t["conteudo"]
    assert "Dispositivo relacionado: art. 108, § 2º, da REN nº 1.000/2021" in t["conteudo"]
    assert trechos["anexo4_tab1_l3"]["situacao"] == "revogada"


def test_processar_grava_jsonl(tmp_path):
    html = tmp_path / "20261117T093644-abc.html"
    html.write_text(HTML, encoding="utf-8")
    pastas = {
        nome: tmp_path / nome
        for nome in (
            "pasta_canonico",
            "pasta_markdown",
            "pasta_revisao",
            "pasta_rag",
            "pasta_correcoes",
        )
    }
    resultado = processar(html, "ren-1000-2021", "https://leis.org/x", **pastas)
    linhas = resultado["rag"].read_text(encoding="utf-8").splitlines()
    registros = [json.loads(linha) for linha in linhas]
    assert len({r["id"] for r in registros}) == len(registros)
    assert all(r["conteudo"] and r["citacao"] for r in registros)

    resultado["rag"].unlink()
    assert processar(html, "ren-1000-2021", "https://leis.org/x", **pastas)["rag"].exists()
