"""Regras de histórico e anexos, com trechos reais da REN 1.000 no formato do leis.org."""

import pytest

from monitor_normas.extracao_leis_org import extrair, gerar_markdown, hash_canonico, processar


def _ato(numero: str, ano: str, data: str) -> str:
    return (
        f'<a class="link_law" data-original-title=" Data da Norma: {data} - Altera..." '
        f'href="https://leis.org/institucionais/br/aneel/lei/resolucao-normativa/{ano}/{numero}/'
        f'ren-{numero}/">{numero}</a>'
    )


def _artigo(numero: str, rotulo: str) -> str:
    return (
        '<span class="artigo label label-default" data-summary-type="article" '
        f'data-summary-id="article{numero}">{rotulo}</span>'
    )


ATO_1042 = _ato("1042", "2022", "20.09.2022")
ATO_1059 = _ato("1059", "2023", "07.02.2023")
ATO_1174 = _ato("1174", "2026", "27.10.2026")
REN = "Resolução Normativa nº"

HTML = f"""
<html><body>
<div id="law-content" class="aneel-content">
RESOLUÇÃO NORMATIVA ANEEL Nº 1.000, DE 7 DE DEZEMBRO DE 2021<br>
<span class="titulo" data-summary-type="title">CAPÍTULO I<br>Das Regras</span><br>
{_artigo("2", "Art. 2º")} Para os fins desta Resolução, são adotadas as definições:<br><br>
I - acessante: consumidor;<br><br>
I-A - autoconsumo remoto: modalidade caracterizada por:<br>
a) unidades de mesma titularidade;<br><br>
I - C - armazenador autônomo: agente autorizado;<br><br>
II - bandeiras tarifárias: sistema de sinalização;<br><br>
II-A: até 30 de setembro de 2022, para:<br><br>
{_artigo("6", "Art. 6º")} A distribuidora deve alterar o cadastro.<br><br>
<s>Parágrafo único. A distribuidora deve cadastrar de imediato.</s><br><br>
§ 1º A distribuidora deve cadastrar de imediato. (Redação dada pela {REN} {ATO_1042}/2022)<br><br>
§ 2º A distribuidora deve corrigir os dados. (Redação acrescida pela {REN} {ATO_1042}/2022)<br><br>
{_artigo("108", "Art. 108.")} A participação financeira do consumidor é a diferença.<br><br>
<s>§ 1º A distribuidora deve proporcionalizar, observadas as seguintes condições:</s><br><br>
<s>I - a proporcionalização deve considerar a demanda; e</s><br><br>
<s>II - a proporcionalização não se aplica a mão de obra.</s><br><br>
§ 1º A distribuidora deve proporcionalizar o orçamento. (Redação dada pela {REN}
 {ATO_1059}/2023)<br><br>
§ 2º O orçamento não pode conter os itens do § 4º do art. 98.<br><br>
{_artigo("133", "Art. 133.")} Os contratos devem observar os seguintes prazos:<br><br>
<s>§ 4º O prazo mínimo de denúncia do CCER é de:</s><br><br>
<s>I - 180 dias para os CCER com prazo determinado; e</s><br><br>
<s>II - 180 dias para os CCER com prazo indeterminado.</s> (Revogado pela {REN}
 {ATO_1174}/2026)<br><br>
<span class="titulo" data-summary-type="title">Seção II<br>Do Enquadramento</span>
<s><br>{_artigo("160", "Art. 160")} O consumidor pode optar pelo ACL, desde que:<br><br>
I - a partir de 1º de julho de 2019: 2.500 kW;<br><br>
II - a partir de 1º de janeiro de 2020: 2.000 kW.</s><br><br>
{_artigo("160", "Art. 160.")} O consumidor do grupo A pode optar pelo ACL. (Redação dada pela
 {REN} {ATO_1059}/2023)<br><br>
{_artigo("666", "Art. 666.")} A distribuidora deve realizar a busca:<br><br>
I - contato telefônico;<br><br>
I - visita técnica.<br><br>
{_artigo("675", "Art. 675.")} A Resolução Normativa nº 876, de 10 de março de 2020, passa a
 vigorar com as seguintes alterações:<br><br>
"Art. 6º.. ...........<br><br>
§ 1º O DRO a que se refere o caput terá como finalidade facilitar a obtenção. .." (NR)<br><br>
{_artigo("679", "Art. 679.")} Esta Resolução entra em vigor em 3 de janeiro de 2022.<br><br>
ANDRÉ PEPITONE DA NÓBREGA<br><br>
<span class="titulo" data-summary-type="title">ANEXO I<br>CONTRATO DE ADESÃO - GRUPO B</span><br>
<s>A (nome da DISTRIBUIDORA), CNPJ no (00.000.000/0000-00).</s><br><br>
A (nome da DISTRIBUIDORA), CNPJ (00.000.000/0000-00). (Redação dada pela {REN}
 {ATO_1059}/2023)<br><br>
CLÁUSULA PRIMEIRA: DO OBJETO<br><br>
1.1. Este contrato tem por objeto a prestação do serviço.<br><br>
4.2.1.1. A fatura deve ser entregue com antecedência de:<br><br>
- 10 dias úteis, para classe poder público; - 5 dias úteis, para demais classes.<br><br>
<span class="titulo" data-summary-type="title">ANEXO IV<br>PRAZOS PARA COMPENSAÇÃO</span><br>
<table><tbody>
<tr><td>Tipo</td><td>Dispositivo</td><td>Prazo</td><td>Descrição</td></tr>
<tr><td>1</td><td>art. 6º.</td><td>5 dias úteis</td><td>realizar as alterações cadastrais</td></tr>
<tr><td><b>1</b></td><td><b>art. 108, § 2º</b></td><td><b>10 dias úteis</b></td>
<td><b>disponibilizar cópia</b></td><td><b>(Redação acrescida pela {REN}
 {ATO_1059}/2023)</b></td></tr>
<tr><td>3</td><td>art. 133, § 4º, I</td><td>10 dias úteis</td><td>notificar</td>
<td>(Revogado pela {REN} {ATO_1174}/2026)</td></tr>
</tbody></table>
<div id="extras"><div class="atos-vinculados">
<h5>Atos que alteram, regulamentam ou revogam esta Resolução Normativa:</h5>
<p><a href="https://leis.org/institucionais/br/aneel/lei/resolucao-normativa/2026/1174/ren-1174"
 data-original-title="Data do Ato: 27/10/2026 - Aprimora a regulação.">
 Resolução Normativa nº 1174/2026 de 27/10/2026</a> - Norma em vigor</p>
</div></div>
</div>
</body></html>
"""


@pytest.fixture
def canonico():
    return extrair(HTML)


@pytest.fixture
def d(canonico):
    return {x["id"]: x for x in canonico["dispositivos"]}


def test_ids_unicos(canonico):
    ids = [x["id"] for x in canonico["dispositivos"]]
    ids += [x["id"] for a in canonico["anexos"] for x in a["dispositivos"]]
    assert len(ids) == len(set(ids))


def test_incisos_com_letra(d):
    assert d["art2_inc1"]["texto"] == "acessante: consumidor;"
    assert d["art2_inc1-A"]["rotulo"] == "I-A -"
    assert d["art2_inc1-A_alia"]["tipo"] == "alinea"
    assert d["art2_inc1-C"]["texto"] == "armazenador autônomo: agente autorizado;"
    assert d["art2_inc2-A"]["texto"] == "até 30 de setembro de 2022, para:"


def test_renumeracao_paragrafo_unico_para_paragrafo_primeiro(d):
    assert "art6_parunico" not in d
    paragrafo = d["art6_par1"]
    assert paragrafo["situacao"] == "vigente"
    assert paragrafo["ids_anteriores"] == ["art6_parunico"]
    assert paragrafo["renumeracao"] == {"de": "Parágrafo único.", "para": "§ 1º"}
    antiga, nova = paragrafo["redacoes"]
    assert antiga["rotulo"] == "Parágrafo único."
    assert antiga["vigente_de"] == "2022-01-03"
    assert antiga["vigente_ate"] == "2022-09-20"
    assert nova["vigente_de"] == "2022-09-20"


def test_nova_redacao_suprime_incisos(d):
    paragrafo = d["art108_par1"]
    assert paragrafo["situacao"] == "vigente"
    assert [r["situacao"] for r in paragrafo["redacoes"]] == ["substituida", "vigente"]
    for ident in ("art108_par1_inc1", "art108_par1_inc2"):
        inciso = d[ident]
        assert inciso["situacao"] == "suprimido"
        assert inciso["revogado_por"] is None
        assert inciso["suprimido_por"]["dispositivo"] == "art108_par1"
        assert "1059/2023" in inciso["suprimido_por"]["nota"]
        assert inciso["redacoes"][-1]["vigente_ate"] == "2023-02-07"
    assert not any(i.startswith("art108_par1") and i.endswith("_2") for i in d)


def test_revogacao_no_fim_do_grupo_vale_para_o_grupo(d):
    for ident in ("art133_par4", "art133_par4_inc1", "art133_par4_inc2"):
        assert d[ident]["situacao"] == "revogado", ident
        assert d[ident]["revogado_por"]["ato"]["numero"] == "1174"
    assert d["art133_par4"]["revogado_por"]["nota_no_dispositivo"] == "art133_par4_inc2"


def test_tachado_que_abre_em_linha_vazia_e_artigo_reescrito(d):
    artigo = d["art160"]
    assert artigo["situacao"] == "vigente"
    assert artigo["texto"] == "O consumidor do grupo A pode optar pelo ACL."
    assert len(artigo["redacoes"]) == 2
    assert d["art160_inc1"]["situacao"] == "suprimido"
    assert d["art160_inc2"]["situacao"] == "suprimido"


def test_rotulo_repetido_sem_nota_vira_outro_dispositivo(canonico, d):
    assert d["art666_inc1"]["texto"] == "contato telefônico;"
    assert d["art666_inc1_2"]["texto"] == "visita técnica."
    assert any(c["id"] == "art666_inc1_2" for c in canonico["revisao"])


def test_texto_que_altera_outra_norma_fica_como_citacao(d):
    assert not any(i.startswith("art675_") for i in d)
    citacao = d["art675"]["citacao"]
    assert citacao[0] == '"Art. 6º.. ...........'
    assert citacao[1].startswith("§ 1º O DRO")


def test_vigencia_original_e_fecho(canonico, d):
    assert canonico["vigencia"] == {"data": "2022-01-03", "dispositivo": "art679"}
    assert canonico["fecho"] == ["ANDRÉ PEPITONE DA NÓBREGA"]
    assert d["art679"]["texto"] == "Esta Resolução entra em vigor em 3 de janeiro de 2022."
    original = d["art2_inc1"]["redacoes"][0]
    assert original["vigente_de"] == "2022-01-03"
    assert original["fonte_data"] == "artigo de vigencia da norma"


def test_anexo_com_clausulas_itens_e_historico(canonico):
    anexo = canonico["anexos"][0]
    itens = {x["id"]: x for x in anexo["dispositivos"]}
    preambulo = itens["anexo1_texto1"]
    assert [r["situacao"] for r in preambulo["redacoes"]] == ["substituida", "vigente"]
    assert preambulo["redacoes"][1]["ato"]["numero"] == "1059"
    assert itens["anexo1_cl1"]["texto"] == "CLÁUSULA PRIMEIRA: DO OBJETO"
    item = itens["anexo1_it1.1"]
    assert item["texto"] == "Este contrato tem por objeto a prestação do serviço."
    assert item["estrutura"] == [
        "ANEXO I - CONTRATO DE ADESÃO - GRUPO B",
        "CLÁUSULA PRIMEIRA: DO OBJETO",
    ]
    assert itens["anexo1_it4.2.1.1"]["texto"].endswith("- 5 dias úteis, para demais classes.")


def test_tabela_do_anexo(canonico):
    (tabela,) = canonico["anexos"][1]["tabelas"]
    assert tabela["cabecalho"] == ["Tipo", "Dispositivo", "Prazo", "Descrição"]
    original, acrescida, revogada = tabela["linhas"]
    assert original["dispositivo_id"] == "art6"
    assert not original["destaque"]
    assert acrescida["destaque"]
    assert acrescida["nota"] == "Redação acrescida pela Resolução Normativa nº 1059/2023"
    assert acrescida["dispositivo_id"] == "art108_par2"
    assert revogada["situacao"] == "revogada"
    assert revogada["dispositivo_id"] == "art133_par4_inc1"


def test_atos_vinculados_saem_do_texto(canonico):
    (ato,) = canonico["atos_vinculados"]
    assert ato["data"] == "2026-10-27"
    assert ato["ementa"] == "Aprimora a regulação."
    assert ato["descricao"].endswith("Norma em vigor")
    textos = [x["texto"] or "" for a in canonico["anexos"] for x in a["dispositivos"]]
    assert not any("Atos que alteram" in t for t in textos)


def test_markdown_com_regras(canonico):
    canonico["hash_canonico"] = hash_canonico(canonico)
    md = gerar_markdown(canonico, "ren-1000-2021", {"url": "https://leis.org/x"})
    assert '<a id="art6_par1"></a>§ 1º A distribuidora deve cadastrar de imediato.' in md
    assert "Parágrafo único" not in md
    assert "a proporcionalização deve considerar a demanda" not in md
    assert '<a id="art133_par4"></a>§ 4º (Revogado pela' in md
    assert 'id="art133_par4_inc1"' not in md
    assert "ANDRÉ PEPITONE DA NÓBREGA" in md
    assert '## <a id="anexo1"></a>ANEXO I - CONTRATO DE ADESÃO - GRUPO B' in md
    assert '### <a id="anexo1_cl1"></a>CLÁUSULA PRIMEIRA: DO OBJETO' in md
    assert "| Tipo | Dispositivo | Prazo | Descrição | Nota |" in md


def test_relatorio_de_revisao(tmp_path):
    html = tmp_path / "20261117T093644-abc.html"
    html.write_text(HTML, encoding="utf-8")
    resultado = processar(
        html,
        "ren-1000-2021",
        "https://leis.org/x",
        pasta_canonico=tmp_path / "canonico",
        pasta_markdown=tmp_path / "md",
        pasta_revisao=tmp_path / "revisao",
    )
    texto = resultado["revisao"].read_text(encoding="utf-8")
    assert texto.startswith("# Revisão da extração: ren-1000-2021")
    assert "## art666_inc1_2" in texto
    assert "rótulo repetido sem nota" in texto
