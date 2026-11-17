from monitor_normas.captura_navegador import TITULO_VERIFICACAO, analisar_estrutura


def test_reconhece_titulos_da_tela_de_verificacao():
    assert TITULO_VERIFICACAO.search("Um momento…")
    assert TITULO_VERIFICACAO.search("Just a moment...")
    assert not TITULO_VERIFICACAO.search("Regras de Prestação do Serviço Público - Leis.org")


def test_analisar_estrutura_acha_o_conteiner_e_os_formatos():
    html = """
    <html><head><title>Norma</title></head><body>
    <nav>Menu</nav>
    <div id="law-content" class="aneel-content">
      <span class="artigo">Art. 1º</span> Texto.<br><br>
      I - inciso;<br><br>
      <s>II - antigo</s><br><br>
      § 1º Parágrafo. (Redação dada pela Resolução Normativa nº 1/2022)<br><br>
      <span class="artigo">Art. 2º</span> Outro.
    </div></body></html>
    """
    estrutura = analisar_estrutura(html)
    assert estrutura["titulo"] == "Norma"
    assert estrutura["artigos_encontrados"] == 2
    assert estrutura["conteiner_provavel"]["id"] == "law-content"
    assert estrutura["tachados"]["quantidade"] == 1
    assert estrutura["notas"]["Redação dada"] == 1
