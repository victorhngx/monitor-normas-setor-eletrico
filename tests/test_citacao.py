import pytest

from monitor_normas.citacao import ancestrais, citacao, citacao_curta, romano, sigla_norma

SIGLA = "REN nº 1.000/2021"


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
