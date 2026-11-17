import pytest

from monitor_normas.correcoes import ErroCorrecoes, carregar_correcoes
from monitor_normas.extracao_leis_org import extrair


def _artigo(numero: str, rotulo: str) -> str:
    return (
        '<span class="artigo label label-default" data-summary-type="article" '
        f'data-summary-id="article{numero}">{rotulo}</span>'
    )


ATO_1059 = (
    '<a class="link_law" data-original-title=" Data da Norma: 07.02.2023 - Aprimora..." '
    'href="https://leis.org/institucionais/br/aneel/lei/resolucao-normativa/2023/1059/ren-1059/">'
    "1059</a>"
)

HTML = f"""
<div id="law-content" class="aneel-content">
RESOLUÇÃO NORMATIVA ANEEL Nº 1.000, DE 7 DE DEZEMBRO DE 2021<br>
{_artigo("666", "Art. 666.")} A distribuidora deve realizar a busca.<br><br>
§ 1º A busca deve ser realizada nos seguintes prazos:<br><br>
I - até 30 de junho de 2022; e<br><br>
II - até 31 de dezembro de 2022 § 2º Durante a realização da busca, a distribuidora deve:<br><br>
I - coletar informações; e<br><br>
II - realizar campanha.<br><br>
<s><br>{_artigo("672", "Art. 672")} A Resolução Normativa nº 482 passa a vigorar com as
 seguintes alterações:<br><br>
"Art. 10. A distribuidora deverá iniciar o sistema de compensação." (NR)</s>
 (Revogado pela Resolução Normativa nº {ATO_1059}/2023)<br><br>
{_artigo("673", "Art. 673.")} Esta Resolução entra em vigor em 3 de janeiro de 2022.<br><br>
</div>
"""

QUEBRA = {
    "tipo": "quebra",
    "antes_de": "§ 2º Durante a realização da busca",
    "motivo": "falta a quebra de linha no site",
}


def test_quebra_manual_separa_o_paragrafo():
    d = {x["id"]: x for x in extrair(HTML, [QUEBRA])["dispositivos"]}
    assert d["art666_par1_inc2"]["texto"] == "até 31 de dezembro de 2022"
    assert d["art666_par2"]["texto"] == "Durante a realização da busca, a distribuidora deve:"
    assert d["art666_par2_inc1"]["texto"] == "coletar informações; e"
    assert "art666_par1_inc1_2" not in d


def test_correcao_aplicada_fica_registrada():
    canonico = extrair(HTML, [QUEBRA])
    assert canonico["correcoes"] == [QUEBRA | {"aplicada": 1}]
    assert canonico["revisao"] == []


def test_correcao_que_nao_encaixa_vai_para_a_revisao():
    canonico = extrair(HTML, [QUEBRA | {"antes_de": "texto que não existe"}])
    assert canonico["correcoes"][0]["aplicada"] == 0
    assert any(c["id"] == "correcao" for c in canonico["revisao"])


def test_sem_correcao_o_rotulo_repetido_vai_para_a_revisao():
    canonico = extrair(HTML)
    assert any(c["id"] == "art666_par1_inc1_2" for c in canonico["revisao"])


def test_revogacao_depois_do_texto_citado_vale_para_o_artigo():
    d = {x["id"]: x for x in extrair(HTML)["dispositivos"]}
    artigo = d["art672"]
    assert artigo["situacao"] == "revogado"
    assert artigo["revogado_por"]["ato"]["numero"] == "1059"
    assert artigo["redacoes"][-1]["vigente_ate"] == "2023-02-07"
    assert artigo["citacao"] == [
        '"Art. 10. A distribuidora deverá iniciar o sistema de compensação." (NR)'
    ]


def test_carregar_correcoes(tmp_path):
    assert carregar_correcoes("ren-1000-2021", tmp_path) == []
    (tmp_path / "ren-1000-2021.toml").write_text(
        '[[correcao]]\ntipo = "quebra"\nantes_de = "§ 2º Durante"\nmotivo = "falta quebra"\n',
        encoding="utf-8",
    )
    assert carregar_correcoes("ren-1000-2021", tmp_path) == [
        {"tipo": "quebra", "antes_de": "§ 2º Durante", "motivo": "falta quebra"}
    ]


@pytest.mark.parametrize(
    "conteudo",
    [
        '[[correcao]]\ntipo = "apagar"\nantes_de = "x"\nmotivo = "y"\n',
        '[[correcao]]\ntipo = "quebra"\nantes_de = "x"\n',
        '[[correcao]]\ntipo = "quebra"\nantes_de = ""\nmotivo = "y"\n',
        '[[correcao]]\ntipo = "quebra"\nantes_de = "x"\nmotivo = "y"\nextra = 1\n',
        "outra = 1\n",
        "isto não é toml [",
    ],
)
def test_correcoes_invalidas(tmp_path, conteudo):
    (tmp_path / "ren-1000-2021.toml").write_text(conteudo, encoding="utf-8")
    with pytest.raises(ErroCorrecoes):
        carregar_correcoes("ren-1000-2021", tmp_path)
