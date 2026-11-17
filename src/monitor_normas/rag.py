"""Citação de dispositivos e trechos para consulta por IA (RAG), a partir do canônico (D020).

Citação: montada a partir do id (`art6_par1_inc2_alia` -> art. 6º, § 1º, inciso II,
alínea "a"). O texto do próprio artigo é o caput (`art. 6º, caput`) e os incisos
ligados direto ao artigo são do caput (`art. 6º, caput, inciso I`).

Trechos (dados/rag/<id>.jsonl): um por redação de cada dispositivo, com a citação,
a estrutura, o contexto (caput e dispositivos pais na redação válida na data da
redação), a situação, o período de vigência e o ato alterador. O campo `conteudo`
junta tudo num texto pronto para indexar.
"""

import json
import re

RE_PARTE = re.compile(
    r"^(?:(art)(\d+(?:-[A-Z]+)?)|(parunico)|(par)(\d+)(-[A-Z])?|(inc)(\d+)(-[A-Z])?"
    r"|(ali)([a-z])|(item)(\d+)|(texto)(\d+)|(\d+))$"
)
RE_ANEXO = re.compile(r"^anexo(\d+)(?:_(cl|it|texto)(.+))?$")
RE_TITULO_NORMA = re.compile(r"RESOLUÇÃO NORMATIVA.*?Nº\s*([\d.]+).*?(\d{4})", re.IGNORECASE)
AVISO_DATA = {
    "publicacao - conferir vigencia": " (data de publicação do ato; conferir vigência)",
    "inferida - conferir": " (data inferida; conferir)",
}


def romano(numero: int) -> str:
    valores = [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]
    texto = ""
    for valor, letra in valores:
        while numero >= valor:
            texto += letra
            numero -= valor
    return texto


def sigla_norma(titulo: str | None, norma_id: str) -> str:
    """ "RESOLUÇÃO NORMATIVA ANEEL Nº 1.000, DE 7 DE DEZEMBRO DE 2021" -> "REN nº 1.000/2021"."""
    m = RE_TITULO_NORMA.search(titulo or "")
    return f"REN nº {m.group(1)}/{m.group(2)}" if m else norma_id


def _ordinal(numero: str) -> str:
    """Artigo e parágrafo: ordinal até 9 (art. 9º), cardinal a partir de 10 (art. 10)."""
    base = re.match(r"\d+", numero).group()
    return f"{base}º{numero[len(base) :]}" if int(base) < 10 else numero


def partes(ident: str) -> list[tuple[str, str]]:
    """Divide o id em (nível, valor): art6_par1_inc2 -> [(art, 6), (par, 1), (inc, 2)]."""
    resultado = []
    for parte in ident.split("_"):
        m = RE_PARTE.match(parte)
        if not m:
            return []
        g = m.groups()
        if g[0]:
            resultado.append(("art", g[1]))
        elif g[2]:
            resultado.append(("parunico", ""))
        elif g[3]:
            resultado.append(("par", g[4] + (g[5] or "")))
        elif g[6]:
            resultado.append(("inc", g[7] + (g[8] or "")))
        elif g[9]:
            resultado.append(("ali", g[10]))
        elif g[11]:
            resultado.append(("item", g[12]))
        elif g[13]:
            resultado.append(("texto", g[14]))
        else:
            resultado.append(("repeticao", g[15]))
    return resultado


def ancestrais(ident: str) -> list[str]:
    """Ids dos dispositivos pais, do artigo para baixo (sem o próprio)."""
    if m := RE_ANEXO.match(ident):
        if m.group(2) != "it":
            return []
        numeros = m.group(3).split(".")
        return [f"anexo{m.group(1)}_it{'.'.join(numeros[:i])}" for i in range(1, len(numeros))]
    lista = partes(ident)
    if not lista:
        return []
    fim = len(lista) - 1
    if lista[-1][0] == "repeticao":
        # art668_inc3_alid_2 é irmão de art668_inc3_alid, não filho
        fim -= 1
    pedacos = ident.split("_")
    return ["_".join(pedacos[:i]) for i in range(1, fim + 1)]


def citacao_curta(d: dict) -> str:
    """Citação sem o nome da norma: "art. 6º, § 1º, inciso II" ou "art. 6º, caput"."""
    ident = d["id"]
    if m := RE_ANEXO.match(ident):
        anexo = f"Anexo {romano(int(m.group(1)))}"
        tipo, valor = m.group(2), m.group(3)
        if tipo == "it":
            return f"{anexo}, item {valor}"
        if tipo == "cl":
            texto = d.get("texto") or (d["redacoes"][-1]["texto"] if d.get("redacoes") else "")
            nome = texto.split(":")[0].strip().capitalize() if texto else f"cláusula {valor}"
            return f"{anexo}, {nome}"
        return anexo
    lista = partes(ident)
    if not lista:
        return ident
    trechos: list[str] = []
    tem_paragrafo = False
    for nivel, valor in lista:
        if nivel == "art":
            trechos.append(f"art. {_ordinal(valor)}")
        elif nivel == "parunico":
            trechos.append("parágrafo único")
            tem_paragrafo = True
        elif nivel == "par":
            trechos.append(f"§ {_ordinal(valor)}")
            tem_paragrafo = True
        elif nivel == "inc":
            if not tem_paragrafo:
                trechos.append("caput")
            numero, _, letra = valor.partition("-")
            trechos.append(f"inciso {romano(int(numero))}{'-' + letra if letra else ''}")
        elif nivel == "ali":
            trechos.append(f'alínea "{valor}"')
        elif nivel == "item":
            trechos.append(f"item {valor}")
        elif nivel == "repeticao":
            trechos[-1] += f" ({valor}ª ocorrência)"
    if lista[-1][0] == "art" and d.get("tipo") == "artigo":
        trechos.append("caput")
    return ", ".join(trechos)


def citacao(d: dict, sigla: str) -> str:
    """Citação completa: "art. 6º, § 1º, da REN nº 1.000/2021"."""
    return f"{citacao_curta(d)}, da {sigla}"


def _data_br(data: str | None) -> str:
    return f"{data[8:10]}/{data[5:7]}/{data[:4]}" if data else "?"


def redacao_em(d: dict, data: str | None) -> dict | None:
    """Redação do dispositivo válida na data (sem data: a vigente ou a última)."""
    redacoes = d.get("redacoes") or []
    if data:
        for r in redacoes:
            inicio, fim = r.get("vigente_de") or "", r.get("vigente_ate")
            if inicio <= data and (fim is None or data < fim):
                return r
    vigentes = [r for r in redacoes if r["situacao"] == "vigente"]
    if vigentes:
        return vigentes[-1]
    return redacoes[-1] if redacoes else None


def _texto(d: dict, r: dict | None) -> str:
    return (r or {}).get("texto") or d.get("texto") or ""


def _linha_situacao(d: dict, r: dict) -> str:
    de = _data_br(r.get("vigente_de")) + AVISO_DATA.get(r.get("fonte_data"), "")
    ate = _data_br(r.get("vigente_ate"))
    nota = f"; {r['nota']}" if r.get("nota") else ""
    situacao = r["situacao"]
    if situacao == "vigente":
        return f"Situação: vigente desde {de}{nota}"
    if situacao == "substituida":
        return f"Situação: redação substituída; vigorou de {de} a {ate}{nota}"
    if situacao == "revogada":
        return f"Situação: {d['revogado_por']['nota']}; vigorou de {de} a {ate}"
    if situacao == "suprimida":
        return f"Situação: {d['suprimido_por']['nota']}; vigorou de {de} a {ate}"
    return f"Situação: {situacao}"


def _tabela_texto(tabela: dict) -> list[str]:
    linhas = [" | ".join(tabela["cabecalho"])]
    linhas += [" | ".join(linha["celulas"]) for linha in tabela["linhas"]]
    return linhas


def _trechos_dispositivo(d: dict, todos: dict, sigla: str, norma_id: str) -> list[dict]:
    if d["tipo"] == "texto" and not d.get("redacoes"):
        if d["situacao"] != "vigente":
            return []
        redacoes = [{"texto": d["texto"], "situacao": "vigente"}]
    else:
        redacoes = d["redacoes"]
    trechos = []
    for numero, r in enumerate(redacoes, start=1):
        data = r.get("vigente_de")
        contexto = []
        for pai in ancestrais(d["id"]):
            if pai in todos:
                texto_pai = _texto(todos[pai], redacao_em(todos[pai], data))
                contexto.append(
                    {"dispositivo": pai, "citacao": citacao_curta(todos[pai]), "texto": texto_pai}
                )
        rotulo = r.get("rotulo", d["rotulo"])
        linhas = [" > ".join([sigla, *d["estrutura"]])]
        cit = citacao(d, sigla)
        if rotulo != d["rotulo"]:
            cit += f" (antes: {rotulo.rstrip('.')})"
        linhas.append(cit)
        if r.get("vigente_de") or r["situacao"] != "vigente":
            linhas.append(_linha_situacao(d, r))
        linhas += [f"Contexto ({c['citacao']}): {c['texto']}" for c in contexto]
        linhas.append(f"{rotulo} {r['texto']}".strip())
        if numero == len(redacoes):
            linhas += [f"Texto transcrito: {t}" for t in d.get("citacao", [])]
            for tabela in d.get("tabelas", []):
                linhas += _tabela_texto(tabela)
        trechos.append(
            {
                "id": f"{d['id']}#{numero}",
                "dispositivo": d["id"],
                "norma": norma_id,
                "citacao": citacao(d, sigla),
                "tipo": d["tipo"],
                "rotulo": rotulo,
                "estrutura": d["estrutura"],
                "contexto": contexto,
                "texto": r["texto"],
                "situacao": r["situacao"],
                "vigente_de": r.get("vigente_de"),
                "vigente_ate": r.get("vigente_ate"),
                "fonte_data": r.get("fonte_data"),
                "nota": r.get("nota"),
                "ato": r.get("ato"),
                "ids_anteriores": d.get("ids_anteriores", []),
                "conteudo": "\n".join(linhas),
            }
        )
    return trechos


def _trechos_tabela(anexo: dict, todos: dict, sigla: str, norma_id: str) -> list[dict]:
    rotulo = f"Anexo {romano(int(anexo['id'].removeprefix('anexo')))}"
    trechos = []
    for t, tabela in enumerate(anexo["tabelas"], start=1):
        for n, linha in enumerate(tabela["linhas"], start=1):
            pares = [
                f"{c}: {v}" for c, v in zip(tabela["cabecalho"], linha["celulas"], strict=False)
            ]
            cit = f"{rotulo}, tabela {t}, linha {n}, da {sigla}"
            linhas = [
                " > ".join([sigla, f"{anexo['rotulo']} - {anexo['titulo']}".strip(" -")]),
                cit,
                f"Situação: {'revogada' if linha.get('situacao') == 'revogada' else 'vigente'}"
                + (f"; {linha['nota']}" if linha.get("nota") else ""),
                " | ".join(pares),
            ]
            relacionado = linha.get("dispositivo_id")
            if relacionado in todos:
                linhas.append(f"Dispositivo relacionado: {citacao(todos[relacionado], sigla)}")
            trechos.append(
                {
                    "id": f"{anexo['id']}_tab{t}_l{n}",
                    "dispositivo": relacionado,
                    "norma": norma_id,
                    "citacao": cit,
                    "tipo": "linha_tabela",
                    "rotulo": "",
                    "estrutura": [f"{anexo['rotulo']} - {anexo['titulo']}".strip(" -")],
                    "contexto": [],
                    "texto": " | ".join(pares),
                    "situacao": linha.get("situacao", "vigente"),
                    "vigente_de": (linha.get("ato") or {}).get("data"),
                    "vigente_ate": None,
                    "fonte_data": None,
                    "nota": linha.get("nota"),
                    "ato": linha.get("ato"),
                    "ids_anteriores": [],
                    "conteudo": "\n".join(linhas),
                }
            )
    return trechos


def gerar_trechos(canonico: dict, norma_id: str) -> list[dict]:
    """Um trecho por redação de cada dispositivo, mais as linhas das tabelas dos anexos."""
    sigla = sigla_norma(canonico.get("titulo"), norma_id)
    dispositivos = list(canonico["dispositivos"])
    for anexo in canonico.get("anexos", []):
        dispositivos += anexo["dispositivos"]
    todos = {d["id"]: d for d in dispositivos}
    trechos = []
    for d in dispositivos:
        trechos += _trechos_dispositivo(d, todos, sigla, norma_id)
    for anexo in canonico.get("anexos", []):
        trechos += _trechos_tabela(anexo, todos, sigla, norma_id)
    return trechos


def gerar_jsonl(canonico: dict, norma_id: str) -> str:
    linhas = [json.dumps(t, ensure_ascii=False) for t in gerar_trechos(canonico, norma_id)]
    return "\n".join(linhas) + "\n"
