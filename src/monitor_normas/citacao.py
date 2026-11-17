"""Citação de dispositivos a partir do id (D020).

`art6_par1_inc2_alia` -> art. 6º, § 1º, inciso II, alínea "a". O texto do próprio
artigo é o caput (`art. 6º, caput`) e os incisos ligados direto ao artigo são do
caput (`art. 6º, caput, inciso I`).
"""

import re

RE_PARTE = re.compile(
    r"^(?:(art)(\d+(?:-[A-Z]+)?)|(parunico)|(par)(\d+)(-[A-Z])?|(inc)(\d+)(-[A-Z])?"
    r"|(ali)([a-z])|(item)(\d+)|(texto)(\d+)|(\d+))$"
)
RE_ANEXO = re.compile(r"^anexo(\d+)(?:_(cl|it|texto)(.+))?$")
RE_TITULO_NORMA = re.compile(r"RESOLUÇÃO NORMATIVA.*?Nº\s*([\d.]+).*?(\d{4})", re.IGNORECASE)


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


def data_br(data: str | None) -> str:
    return f"{data[8:10]}/{data[5:7]}/{data[:4]}" if data else "?"
