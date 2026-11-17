import json

import pytest

from monitor_normas.extracao_leis_org import (
    ErroExtracao,
    extrair,
    gerar_markdown,
    hash_canonico,
    processar,
)

ATO_1162 = (
    '<a class="link_law" data-original-title=" Data da Norma: 02.06.2026 - Estabelecer..." '
    'href="https://leis.org/institucionais/br/aneel/lei/resolucao-normativa/2026/1162/ren-1162/">'
    "1162</a>"
)
ATO_1059 = (
    '<a class="link_law" data-original-title=" Data da Norma: 07.02.2023 - Aprimora..." '
    'href="https://leis.org/institucionais/br/aneel/lei/resolucao-normativa/2023/1059/ren-1059/">'
    "1059</a>"
)

# Trecho no mesmo formato de marcação da página da REN 1.000 no leis.org.
HTML = f"""
<html><body>
<div id="law-content" class="w-full">
<div id="law-content" class="aneel-content">
AGÊNCIA NACIONAL DE ENERGIA ELÉTRICA - ANEEL<br>
RESOLUÇÃO NORMATIVA ANEEL Nº 1.000, DE 7 DE DEZEMBRO DE 2021(*)<br>
<a href="#">Download Voto</a><br>
Estabelece as Regras de Prestação do Serviço Público de Distribuição de Energia Elétrica.<br>
O DIRETOR-GERAL DA ANEEL resolve :<br>
<span class="titulo"><span class="titulo" data-summary-type="title"><br>TÍTULO I<br>PARTE GERAL<br>
</span></span>
<span class="titulo" data-summary-type="title">Seção I<br>Do Objeto</span><br>
<span class="artigo label label-default" data-summary-type="article"
 data-summary-id="article1º">Art. 1º</span> Esta Resolução estabelece as regras.<br><br>
§ 1º Aplica-se ao usuário, a exemplo de:<br><br>
I - consumidor;<br><br>
<s>IV - agente exportador; e</s><br><br>
<b>IV - agente exportador; (Redação dada pela Resolução Normativa nº {ATO_1162}/2026)</b><br><br>
VI - armazenador autônomo. (Redação acrescida pela Resolução Normativa nº {ATO_1162}/2026)<br><br>
Parágrafo único. Texto do parágrafo único.<br><br>
<span class="artigo label label-default" data-summary-type="article"
 data-summary-id="article48-A">Art. 48-A.</span> Artigo inserido:<br>
a) primeira alínea;<br>
b) segunda alínea.<br><br>
<span class="artigo label label-default" data-summary-type="article"
 data-summary-id="article59.">Art. 59.</span> O consumidor deve fornecer as informações.<br><br>
<s>§ 2º Para microgeração, a solicitação deve usar o formulário.</s>
 (Revogado pela Resolução Normativa nº {ATO_1059}/2023)<br><br>
§ 3º Parágrafo vigente.<br><br>
<span class="titulo" data-summary-type="title">ANEXO I<br>CONTRATO</span><br>
Cláusula do contrato.<br>
</div>
</div>
</body></html>
"""


@pytest.fixture
def canonico():
    return extrair(HTML)


def por_id(canonico):
    return {d["id"]: d for d in canonico["dispositivos"]}


def test_cabecalho_titulo_e_data(canonico):
    assert canonico["titulo"] == "RESOLUÇÃO NORMATIVA ANEEL Nº 1.000, DE 7 DE DEZEMBRO DE 2021"
    assert canonico["data"] == "2021-12-07"
    assert any(linha.startswith("Estabelece as Regras") for linha in canonico["cabecalho"])


def test_ids_e_tipos(canonico):
    d = por_id(canonico)
    for ident, tipo in [
        ("art1", "artigo"),
        ("art1_par1", "paragrafo"),
        ("art1_par1_inc1", "inciso"),
        ("art1_par1_inc4", "inciso"),
        ("art1_par1_inc6", "inciso"),
        ("art1_parunico", "paragrafo"),
        ("art48-A", "artigo"),
        ("art48-A_alia", "alinea"),
        ("art48-A_alib", "alinea"),
        ("art59_par2", "paragrafo"),
    ]:
        assert d[ident]["tipo"] == tipo, ident


def test_estrutura_hierarquica(canonico):
    assert por_id(canonico)["art1"]["estrutura"] == [
        "TÍTULO I - PARTE GERAL",
        "Seção I - Do Objeto",
    ]


def test_redacao_dada_guarda_historico_e_datas(canonico):
    inciso = por_id(canonico)["art1_par1_inc4"]
    assert inciso["situacao"] == "vigente"
    assert inciso["texto"] == "agente exportador;"
    antiga, nova = inciso["redacoes"]
    assert antiga == {
        "texto": "agente exportador; e",
        "situacao": "substituida",
        "vigente_de": "2021-12-07",
        "fonte_data": "publicacao - conferir vigencia",
        "vigente_ate": "2026-06-02",
    }
    assert nova["nota"] == "Redação dada pela Resolução Normativa nº 1162/2026"
    assert nova["ato"]["tipo"] == "REN"
    assert nova["ato"]["numero"] == "1162"
    assert nova["ato"]["data"] == "2026-06-02"
    assert nova["vigente_de"] == "2026-06-02"
    assert nova["vigente_ate"] is None


def test_redacao_acrescida(canonico):
    inciso = por_id(canonico)["art1_par1_inc6"]
    assert len(inciso["redacoes"]) == 1
    assert inciso["redacoes"][0]["nota"].startswith("Redação acrescida")
    assert inciso["redacoes"][0]["vigente_de"] == "2026-06-02"


def test_revogado(canonico):
    paragrafo = por_id(canonico)["art59_par2"]
    assert paragrafo["situacao"] == "revogado"
    assert paragrafo["texto"] is None
    assert paragrafo["revogado_por"]["ato"]["numero"] == "1059"
    assert paragrafo["redacoes"][-1]["vigente_ate"] == "2023-02-07"


def test_alineas_separadas_por_quebra_simples(canonico):
    d = por_id(canonico)
    assert d["art48-A_alia"]["texto"] == "primeira alínea;"
    assert d["art48-A_alib"]["texto"] == "segunda alínea."


def test_anexo_fica_separado(canonico):
    assert canonico["anexos"] == [
        {"titulo": "ANEXO I - CONTRATO", "texto": ["Cláusula do contrato."]}
    ]


def test_estatisticas(canonico):
    est = canonico["estatisticas"]
    assert est["por_tipo"]["artigo"] == 3
    assert est["revogados"] == 1
    assert est["notas"]["redação dada"] == 1
    assert est["notas"]["redação acrescida"] == 1


def test_markdown_vigente(canonico):
    canonico["hash_canonico"] = hash_canonico(canonico)
    md = gerar_markdown(canonico, "ren-1000-2021", {"url": "https://leis.org/x"})

    assert md.startswith("---\nnorma: ren-1000-2021\n")
    assert 'padrao: "0.1"' in md
    assert "# RESOLUÇÃO NORMATIVA ANEEL Nº 1.000, DE 7 DE DEZEMBRO DE 2021\n" in md
    assert "## TÍTULO I - PARTE GERAL" in md
    assert '<a id="art1_par1_inc4"></a>IV - agente exportador;\n' in md
    assert "> Redação dada pela Resolução Normativa nº 1162/2026" in md
    assert "agente exportador; e" not in md
    assert '<a id="art59_par2"></a>§ 2º (Revogado pela Resolução Normativa nº 1059/2023)' in md
    assert "formulário" not in md
    assert "Download" not in md


def test_sem_conteudo_da_norma():
    with pytest.raises(ErroExtracao):
        extrair("<html><title>Um momento…</title></html>")


def test_processar_grava_e_nao_regrava_sem_mudanca(tmp_path):
    html = tmp_path / "20261117T093644-abc.html"
    html.write_text(HTML, encoding="utf-8")
    pastas = {"pasta_canonico": tmp_path / "canonico", "pasta_markdown": tmp_path / "md"}

    primeiro = processar(html, "ren-1000-2021", "https://leis.org/x", **pastas)
    assert primeiro["mudou"]
    documento = json.loads(primeiro["canonico"].read_text(encoding="utf-8"))
    assert documento["fonte"]["capturado_em"] == "2026-11-17T09:36:44"
    assert primeiro["markdown"].exists()

    segundo = processar(html, "ren-1000-2021", "https://leis.org/x", **pastas)
    assert not segundo["mudou"]
