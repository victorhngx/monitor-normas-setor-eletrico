"""Arquivo da norma para uso em chat com IA (D021).

Um único Markdown, para anexar a uma conversa, com:
- guia de leitura: fonte, início de vigência, convenções e como achar o texto
  válido numa data;
- lista dos atos que alteraram a norma, com data e ementa;
- texto completo: a redação atual de cada dispositivo com a nota e a data da
  alteração, as redações anteriores com o período em que valeram e o texto
  revogado ou suprimido, também com o período;
- anexos, tabelas e fecho.

Saída: dados/chat/<id>.md.
"""

import re

from monitor_normas.citacao import ancestrais, citacao_curta, data_br, partes, sigla_norma

PADRAO_CHAT = "1.0"
RE_DESCRICAO = re.compile(
    r"^(.*?nº\s*(\d+)/(\d{4}))\s+de\s+[\d/]+\s*-\s*Norma\s+(em vigor|revogada)"
)


def linhas_cabecalho(canonico: dict) -> list[str]:
    """Linhas do cabeçalho da norma sem o título e sem os links de download do site."""
    resultado = []
    titulo = canonico.get("titulo") or ""
    for linha in canonico["cabecalho"]:
        if titulo and linha.startswith(titulo):
            linha = linha[len(titulo) :]
        linha = re.sub(r"Download\s.*?(?=Download\s|\(Vide|$)", "", linha).strip()
        if linha and linha != "(*)":
            resultado.append(linha)
    return resultado


def _todos(canonico: dict) -> list[dict]:
    dispositivos = list(canonico["dispositivos"])
    for anexo in canonico.get("anexos", []):
        dispositivos += anexo["dispositivos"]
    return dispositivos


def _atos_alteradores(canonico: dict) -> dict[tuple, dict]:
    """Atos citados nas notas do texto (redação dada, acrescida, revogação, supressão)."""
    atos: dict[tuple, dict] = {}

    def guardar(ato: dict | None) -> None:
        if ato and ato.get("numero"):
            atos[(ato.get("tipo"), ato["numero"], ato.get("ano"))] = ato

    for d in _todos(canonico):
        for r in d["redacoes"]:
            guardar(r.get("ato"))
        for chave in ("revogado_por", "suprimido_por"):
            guardar((d.get(chave) or {}).get("ato"))
    for anexo in canonico.get("anexos", []):
        for tabela in anexo["tabelas"]:
            for linha in tabela["linhas"]:
                guardar(linha.get("ato"))
    return atos


def _vinculado(ato: dict) -> dict:
    """Nome, número, ano e situação de um ato da lista do site."""
    m = RE_DESCRICAO.match(ato.get("descricao", ""))
    if not m:
        return {"nome": ato.get("descricao", ""), "numero": None, "ano": None, "situacao": ""}
    return {"nome": m.group(1), "numero": m.group(2), "ano": m.group(3), "situacao": m.group(4)}


NOMES_TIPO = {"REN": "Resolução Normativa"}


def _lista_atos(canonico: dict) -> list[str]:
    alteradores = _atos_alteradores(canonico)
    vinculados = {}
    for ato in canonico.get("atos_vinculados", []):
        info = _vinculado(ato)
        chave = (info["numero"], info["ano"]) if info["numero"] else (info["nome"], None)
        vinculados[chave] = (ato, info)
    alteram = []
    for tipo, numero, ano in alteradores:
        ato = alteradores[(tipo, numero, ano)]
        if (numero, ano) in vinculados:
            alteram.append(vinculados[(numero, ano)])
        else:
            nome = f"{NOMES_TIPO.get(tipo, tipo or 'Ato')} nº {numero}/{ano}"
            alteram.append((ato, {"nome": nome, "numero": numero, "situacao": ""}))
    numeros = {(numero, ano) for _, numero, ano in alteradores}
    data_norma = canonico.get("data") or ""
    outros_posteriores, anteriores = [], []
    for chave, (ato, info) in vinculados.items():
        if chave in numeros:
            continue
        if (ato.get("data") or "") >= data_norma:
            outros_posteriores.append((ato, info))
        else:
            anteriores.append((ato, info))

    def item(ato: dict, info: dict) -> str:
        situacao = " (norma revogada, segundo a fonte)" if info["situacao"] == "revogada" else ""
        ementa = f": {ato['ementa']}" if ato.get("ementa") else ""
        return f"- {info['nome']}, de {data_br(ato.get('data'))}{situacao}{ementa}"

    ordem = sorted(alteram, key=lambda par: (par[0].get("data") or "", par[1]["numero"] or ""))
    linhas = ["## Atos que alteraram a norma", ""]
    linhas += ["Em ordem cronológica. São os atos citados nas notas do texto.", ""]
    linhas += [item(ato, info) for ato, info in ordem] or ["- Nenhum."]
    linhas.append("")
    if outros_posteriores:
        linhas += ["## Outros atos posteriores relacionados", ""]
        linhas += [
            "Listados pela fonte, mas não citados em nenhuma nota do texto. Podem afetar a "
            "aplicação da norma (por exemplo, suspensão de efeitos por decisão judicial). Se a "
            "ementa disser que o ato altera esta Resolução, as alterações podem não estar "
            "incorporadas ao texto abaixo; confira o ato.",
            "",
        ]
        linhas += [item(ato, info) for ato, info in outros_posteriores]
        linhas.append("")
    if anteriores:
        nomes = ", ".join(
            f"{info['nome']}{' (revogada)' if info['situacao'] == 'revogada' else ''}"
            for _, info in sorted(anteriores, key=lambda par: par[0].get("data") or "")
        )
        linhas += ["## Normas anteriores relacionadas", ""]
        linhas += [f"Listadas pela fonte, anteriores a esta Resolução: {nomes}.", ""]
    return linhas


def _ultima_alteracao(canonico: dict) -> dict | None:
    atos = list(_atos_alteradores(canonico).values())
    return max(atos, key=lambda a: a.get("data") or "") if atos else None


def _guia(canonico: dict, norma_id: str, fonte: dict) -> list[str]:
    sigla = sigla_norma(canonico.get("titulo"), norma_id)
    vigencia = canonico.get("vigencia") or {}
    inicio = data_br(vigencia.get("data") or canonico.get("data"))
    artigo_vigencia = (
        f" ({citacao_curta({'id': vigencia['dispositivo'], 'tipo': 'paragrafo'})})"
        if vigencia.get("dispositivo")
        else ""
    )
    ultima = _ultima_alteracao(canonico)
    capturado = (fonte.get("capturado_em") or "")[:10]
    linhas = [
        f"# {canonico.get('titulo') or norma_id}",
        "",
        "Texto compilado com o histórico de alterações, para consulta e interpretação.",
        "",
        f"- Fonte: {fonte.get('url', '')} (compilação não oficial; o texto oficial é o "
        "publicado no Diário Oficial da União).",
        f"- Capturado em: {data_br(capturado) if capturado else '?'}.",
    ]
    if ultima:
        nome = next(
            (
                info["nome"]
                for info in map(_vinculado, canonico.get("atos_vinculados", []))
                if (info["numero"], info["ano"]) == (ultima["numero"], ultima.get("ano"))
            ),
            f"ato nº {ultima['numero']}/{ultima.get('ano')}",
        )
        linhas.append(f"- Última alteração incorporada: {nome}, de {data_br(ultima.get('data'))}.")
    linhas += [
        f"- Data da norma: {data_br(canonico.get('data'))}. Início de vigência: "
        f"{inicio}{artigo_vigencia}.",
        f"- Gerado pelo projeto monitor-normas-setor-eletrico, padrão {PADRAO_CHAT}, "
        f"hash do conteúdo {canonico.get('hash_canonico', '')[:12]}.",
        "",
        "## Como ler este arquivo",
        "",
        "O texto traz todas as redações que cada dispositivo já teve, para que seja possível "
        "saber o que valia em qualquer data a partir do início de vigência.",
        "",
        "Convenções:",
        "",
        "- Dispositivo sem nota: redação original, válida desde o início de vigência "
        f"({inicio}) até hoje.",
        '- Nota "(Redação dada pela ..., de dd/mm/aaaa)": redação atual, válida a partir '
        "dessa data. As redações anteriores aparecem logo abaixo, em linhas iniciadas por "
        '">", cada uma com o período em que valeu.',
        '- Nota "(Redação acrescida pela ..., de dd/mm/aaaa)" ou "(Incluído pela ...)": o '
        "dispositivo não existia antes dessa data.",
        "- [REVOGADO ...]: o dispositivo deixou de valer na data indicada. O texto revogado "
        'aparece abaixo, em linha iniciada por ">", só como histórico. Quando um artigo '
        "inteiro é revogado, seus parágrafos, incisos e alíneas aparecem logo abaixo dele, "
        'também iniciados por ">".',
        "- [SUPRIMIDO ...]: o dispositivo não foi revogado expressamente, mas deixou de "
        "existir quando o dispositivo superior recebeu nova redação sem ele.",
        "- Renumeração: quando um parágrafo único passou a § 1º, a redação anterior aparece "
        'com o rótulo antigo ("Parágrafo único.").',
        '- "vigente de A até B": a redação valeu a partir de A; em B começou a valer a '
        "redação seguinte (ou a revogação).",
        "",
        "Como responder sobre uma data específica (data de referência):",
        "",
        f"1. Se a data for anterior a {inicio}, esta norma ainda não se aplicava; valiam as "
        "normas que ela revogou (ver o preâmbulo e as disposições finais).",
        "2. Para cada dispositivo, use a redação cujo período contém a data de referência: a "
        "redação atual, se a data for igual ou posterior à data da nota, ou a redação "
        "anterior correspondente.",
        "3. Ignore os dispositivos acrescidos depois da data de referência.",
        "4. Considere os dispositivos revogados ou suprimidos depois da data de referência "
        "como válidos naquela data, com o texto mostrado no histórico.",
        "5. Na resposta, diga qual redação foi usada e o período dela.",
        "",
        "Cuidados com as datas:",
        "",
        "- A data das alterações é a data do ato alterador, conforme a fonte. A entrada em "
        "vigor pode ter sido outra (data de publicação no Diário Oficial, cláusula de "
        "vigência do próprio ato ou regras de transição). Para fatos próximos dessas datas, "
        "confira o ato alterador.",
        "- Algumas regras têm prazos de transição nas disposições finais e transitórias; o "
        "histórico deste arquivo não aplica esses prazos automaticamente.",
        '- "Redação alterada sem indicação do ato": a fonte mostra a mudança, mas não diz '
        'qual ato a fez nem quando; a data fica como "?". Em alguns casos a nota do ato '
        "aparece só no último inciso ou alínea do mesmo grupo, logo abaixo.",
        "- Equações publicadas como imagem na fonte não aparecem no texto; ficam só as "
        'definições das variáveis, depois de "em que:". Para o cálculo, consulte o texto '
        "oficial.",
        "- Notas da fonte no preâmbulo (despachos e decisões judiciais, por exemplo) podem "
        "suspender ou condicionar efeitos de dispositivos sem que isso apareça no próprio "
        "dispositivo.",
        "",
        'Citação: use a forma "art. 6º, § 1º, da '
        f'{sigla}". O texto do próprio artigo é o caput ("art. 6º, caput") e os incisos '
        'ligados direto ao artigo são do caput ("art. 6º, caput, inciso I").',
        "",
    ]
    observacoes = [
        f"- {c['motivo']} O texto foi separado na extração."
        for c in canonico.get("correcoes", [])
        if c.get("tipo") == "quebra"
    ]
    if any(_repetido(d) for d in _todos(canonico)):
        observacoes.append(
            "- Alguns rótulos aparecem repetidos no texto da fonte; a segunda ocorrência "
            'está marcada com "[rótulo repetido na fonte]".'
        )
    if observacoes:
        linhas += ["Observações sobre a fonte:", "", *observacoes, ""]
    return linhas


def _repetido(d: dict) -> bool:
    lista = partes(d["id"])
    return bool(lista) and lista[-1][0] == "repeticao"


def _data_nota(r: dict, fallback: dict | None = None) -> str:
    data = r.get("vigente_de") or (fallback or {}).get("data")
    return f", de {data_br(data)}" if data else ""


def _origem(r: dict, indice: int) -> str:
    if r.get("nota"):
        return r["nota"]
    if indice == 0:
        return "Redação original"
    return "Redação alterada sem indicação do ato"


def _periodo(r: dict) -> str:
    de = data_br(r.get("vigente_de"))
    ate = data_br(r.get("vigente_ate"))
    return f"vigente de {de} até {ate}"


def _rotulo(d: dict, rotulo: str | None = None) -> str:
    rotulo = d["rotulo"] if rotulo is None else rotulo
    if d["tipo"] == "artigo" and rotulo:
        return f"**{rotulo}**"
    return rotulo or ""


def _sem_rotulo(texto: str, rotulo: str) -> str:
    """Tira o rótulo repetido no começo do texto ("Art. 35. Art. 35. São...")."""
    base = (rotulo or "").rstrip(".").strip()
    if base and texto.startswith(base):
        return texto[len(base) :].lstrip(". ").strip()
    return texto


def _juntar(*pedacos: str) -> str:
    return " ".join(p for p in pedacos if p).strip()


def _historico(d: dict, redacoes: list[dict], inicio: int = 0) -> list[str]:
    linhas = []
    for i, r in enumerate(redacoes, start=inicio):
        rotulo = r.get("rotulo", d["rotulo"])
        texto = _juntar(_rotulo(d, rotulo), _sem_rotulo(r.get("texto") or "", rotulo))
        linhas.append(f"> {_origem(r, i)}, {_periodo(r)}: {texto}")
    return linhas


def _tabela(tabela: dict) -> list[str]:
    def celula(texto: str) -> str:
        return texto.replace("|", "\\|")

    cabecalho = list(tabela["cabecalho"])
    com_nota = any(linha.get("nota") for linha in tabela["linhas"])
    if com_nota:
        cabecalho.append("Nota")
    linhas = [
        "| " + " | ".join(celula(c) for c in cabecalho) + " |",
        "|" + "---|" * len(cabecalho),
    ]
    for linha in tabela["linhas"]:
        faltam = len(tabela["cabecalho"]) - len(linha["celulas"])
        celulas = list(linha["celulas"]) + [""] * faltam
        if com_nota:
            nota = linha.get("nota", "")
            data = (linha.get("ato") or {}).get("data")
            if nota and data:
                nota += f", de {data_br(data)}"
            celulas.append(nota)
        linhas.append("| " + " | ".join(celula(c) for c in celulas) + " |")
    return [*linhas, ""]


def _extras(d: dict, historico: bool) -> list[str]:
    """Texto transcrito (alteração de outra norma) e tabelas do dispositivo."""
    prefixo = "> " if historico else ""
    linhas = [f"{prefixo}{texto}" for texto in d.get("citacao", [])]
    if linhas:
        linhas.append("")
    for tabela in d.get("tabelas", []):
        linhas += _tabela(tabela)
    return linhas


def _dispositivo(d: dict, todos: dict) -> list[str]:
    redacoes = d["redacoes"]
    repetido = " [rótulo repetido na fonte]" if _repetido(d) else ""
    if d["tipo"] == "texto" and not redacoes:
        return [d["texto"], ""] if d["situacao"] == "vigente" and d["texto"] else []

    if d["situacao"] in ("revogado", "suprimido"):
        chave = "revogado_por" if d["situacao"] == "revogado" else "suprimido_por"
        fim = d.get(chave) or {}
        pais = [todos[p] for p in ancestrais(d["id"]) if p in todos]
        if chave == "revogado_por" and any(
            (p.get("revogado_por") or {}).get("nota") == fim.get("nota") for p in pais
        ):
            # parte de um grupo revogado pelo mesmo ato: só o texto, abaixo do superior
            linhas = [
                f"> {_juntar(_rotulo(d, r.get('rotulo', d['rotulo'])), r.get('texto') or '')}"
                for r in redacoes[-1:]
            ]
            if len(redacoes) > 1:
                linhas = _historico(d, redacoes[:-1]) + linhas
            return [*linhas, *_extras(d, True), ""]
        marca = "REVOGADO" if chave == "revogado_por" else "SUPRIMIDO"
        nota = fim.get("nota", "")
        data = (fim.get("ato") or {}).get("data")
        quando = f", a partir de {data_br(data)}" if data else ""
        linhas = [f"{_rotulo(d)}{repetido} [{marca}: {nota}{quando}]".strip()]
        linhas += _historico(d, redacoes)
        return [*linhas, "", *_extras(d, True)]

    atual = redacoes[-1] if redacoes else {}
    if d["tipo"] == "clausula":
        principal = f"#### {d['texto']}"
    else:
        principal = _juntar(_rotulo(d) + repetido, _sem_rotulo(d["texto"] or "", d["rotulo"]))
    if atual.get("nota"):
        principal += f" ({atual['nota']}{_data_nota(atual)})"
    elif len(redacoes) > 1:
        principal += " (Redação alterada sem indicação do ato)"
    if d["situacao"] == "conferir":
        principal += " [situação a conferir na fonte]"
    linhas = [principal]
    linhas += _historico(d, redacoes[:-1])
    return [*linhas, "", *_extras(d, False)]


def gerar_chat(canonico: dict, norma_id: str, fonte: dict) -> str:
    """Markdown único da norma para anexar a uma conversa (D021)."""
    todos = {d["id"]: d for d in _todos(canonico)}
    linhas = _guia(canonico, norma_id, fonte)
    linhas += _lista_atos(canonico)
    linhas += ["## Texto da norma", ""]
    for linha in linhas_cabecalho(canonico):
        linhas += [linha, ""]

    estrutura_atual: list[str] = []
    for d in canonico["dispositivos"]:
        conteudo = _dispositivo(d, todos)
        if not conteudo:
            continue
        if d["estrutura"] != estrutura_atual:
            comum = 0
            while (
                comum < min(len(d["estrutura"]), len(estrutura_atual))
                and d["estrutura"][comum] == estrutura_atual[comum]
            ):
                comum += 1
            for nivel, nome in enumerate(d["estrutura"][comum:], start=comum):
                linhas += [f"{'#' * min(nivel + 3, 6)} {nome}", ""]
            estrutura_atual = d["estrutura"]
        linhas += conteudo

    for texto in canonico.get("fecho", []):
        linhas += [texto, ""]

    for anexo in canonico.get("anexos", []):
        titulo = f"{anexo['rotulo']} - {anexo['titulo']}".strip(" -")
        linhas += [f"### {titulo}", ""]
        for d in anexo["dispositivos"]:
            linhas += _dispositivo(d, todos)
        for tabela in anexo["tabelas"]:
            linhas += _tabela(tabela)
    return "\n".join(linhas).rstrip() + "\n"
