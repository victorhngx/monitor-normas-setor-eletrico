"""Extração de uma norma publicada no leis.org para texto canônico e Markdown vigente.

Estrutura da página (verificada na REN 1.000/2021):
- a norma fica em div#law-content.aneel-content, como texto corrido em que os
  dispositivos são separados por <br><br>;
- títulos, capítulos, seções e anexos: elementos com data-summary-type="title";
- artigos: span com data-summary-type="article" e data-summary-id="article48-A";
- redação superada e dispositivo revogado: texto dentro de <s> (ou com estilo
  line-through), seguido da nova redação ou de "(Revogado pela ...)";
- notas "(Redação dada pela ...)", "(Redação acrescida pela ...)" com link
  a.link_law para o ato alterador, cujo título traz "Data da Norma: dd.mm.aaaa";
- tabelas em <table>; linhas acrescidas depois vêm em negrito, com a nota numa
  coluna a mais;
- lista "Atos que alteram, regulamentam ou revogam" em div#extras.

Regras de histórico (D018):
- redação tachada seguida de redação nova com o mesmo rótulo: histórico do mesmo
  dispositivo;
- "Parágrafo único" tachado e "§ 1º" novo no mesmo artigo: renumeração (o
  parágrafo único passou a § 1º quando foram acrescidos outros parágrafos);
- filhos tachados de um dispositivo que recebeu nova redação e não reaparecem:
  "suprimido" pela nova redação do pai (não houve revogação expressa);
- grupo tachado (dispositivo e seus filhos) com "(Revogado pela ...)" no fim:
  todo o grupo revogado pelo mesmo ato;
- o que não se encaixa fica com situação "conferir" e vai para o relatório de
  revisão.

Saídas (D004, D006, D007):
- dados/canonico/<id>.json: um registro por dispositivo, com o histórico de redações;
- dados/markdown/<id>/vigente.md: texto vigente, revogados como marcador;
- dados/revisao/<id>.md: casos para conferência manual.

Uso: python -m monitor_normas.extracao_leis_org [arquivo.html] [--norma ID]
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup

from monitor_normas.catalogo import carregar_catalogo
from monitor_normas.correcoes import PASTA_CORRECOES, ErroCorrecoes, carregar_correcoes

PADRAO_MARKDOWN = "0.2"
PASTA_BRUTOS = Path("dados/brutos")
PASTA_CANONICO = Path("dados/canonico")
PASTA_MARKDOWN = Path("dados/markdown")
PASTA_REVISAO = Path("dados/revisao")

# marcadores internos (área de uso privado do Unicode, não aparecem em textos reais)
TIT, TIT_F = "", ""
ART, ART_F = "", ""
RIS, RIS_F = "", ""
ATO, ATO_F = "", ""
SEP_TITULO = ""
TAB, TAB_F = "", ""

RE_ATO = re.compile(f"{ATO}(\\d+){ATO_F}")
RE_TABELA = re.compile(f"{TAB}(\\d+){TAB_F}")
RE_MARCAS = re.compile(
    f"{ATO}\\d+{ATO_F}|{TAB}\\d+{TAB_F}|[{TIT}{TIT_F}{ART}{ART_F}{RIS}{RIS_F}{SEP_TITULO}]"
)
RE_NOTA_FINAL = re.compile(
    r"\(\s*((?:Redação dada|Redação acrescida|Revogad[oa]|Incluíd[oa]|Acrescid[oa]|Vide)\b"
    r"[^()]*(?:\([^()]*\)[^()]*)*)\)\s*[.;]?\s*$"
)
RE_ARTIGO = re.compile(f"^{ART}([^|]*)\\|([^{ART_F}]*){ART_F}\\s*(.*)$", re.DOTALL)
RE_ARTIGO_TEXTO = re.compile(r"^(Art\.\s*(\d+(?:-[A-Z]+)?)\s*[º°]?\.?)\s*(.*)$", re.DOTALL)
RE_PARAGRAFO = re.compile(r"^(§\s*(\d+)º?(?:\s*-\s*([A-Z])\b)?\.?)\s*(.*)$", re.DOTALL)
RE_PARAGRAFO_UNICO = re.compile(r"^(Parágrafo único\.?)\s*(.*)$", re.DOTALL | re.IGNORECASE)
# só I, V, X e L: evita confundir variáveis de fórmulas ("C - consumo") com incisos;
# incisos inseridos depois têm letra: "I-A -", "I - C -", "II-A:"
RE_INCISO = re.compile(r"^(([IVXL]+)(?:\s*-\s*([A-Z])\s*[-–—:]|\s*[-–—]))\s*(.*)$", re.DOTALL)
RE_INICIO_DISPOSITIVO = re.compile(
    f"^({ART}|{TIT}|{TAB}"
    r"|Art\.\s*\d|§\s*\d|Parágrafo único|[IVXL]+(?:\s*-\s*[A-Z]\s*[-–—:]|\s*[-–—])\s"
    r"|[a-z]\)\s|\d+\.\s)"
)
RE_ALINEA = re.compile(r"^(([a-z])\))\s*(.*)$", re.DOTALL)
RE_ITEM = re.compile(r"^((\d+)\.)\s+(.*)$", re.DOTALL)
RE_DATA_NORMA = re.compile(r"Data da Norma:\s*(\d{2})\.(\d{2})\.(\d{4})")
RE_DATA_ATO = re.compile(r"Data do Ato:\s*(\d{2})/(\d{2})/(\d{4})")
RE_DATA_TITULO = re.compile(r"DE (\d{1,2}) DE ([A-ZÇ]+) DE (\d{4})", re.IGNORECASE)
RE_HREF_ATO = re.compile(r"/lei/([^/]+)/(\d{4})/([^/]+)/")
# artigo que altera outra norma: o texto entre aspas que vem depois não é desta norma
RE_ALTERACAO = re.compile(
    r"passa(?:m)? a vigorar (?:com as seguintes alterações|acrescid)", re.IGNORECASE
)
RE_VIGOR = re.compile(
    r"Esta Resolução entra(?:rá)? em vigor (?:em |a partir de )?(\d{1,2})º? de ([a-zç]+) de "
    r"(\d{4})",
    re.IGNORECASE,
)
RE_VIGOR_PUBLICACAO = re.compile(
    r"Esta Resolução entra(?:rá)? em vigor na data de (?:sua )?publicação", re.IGNORECASE
)
RE_CLAUSULA = re.compile(r"^CLÁUSULA\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ ]+?)\s*[:\-–—]", re.IGNORECASE)
RE_ITEM_ANEXO = re.compile(r"^((\d+(?:\.\d+)*)\.?(?:\s*[-–—])?)\s+(\S.*)$", re.DOTALL)
RE_REFERENCIA = re.compile(
    r"art\.\s*(\d+(?:-[A-Z])?)\s*º?\.?(?:\s*,\s*§\s*(\d+)\s*º?)?"
    r"(?:\s*,\s*(?:inciso\s+)?([IVXL]+)\b)?",
    re.IGNORECASE,
)

MESES = {
    m: i
    for i, m in enumerate(
        "janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro "
        "dezembro".split(),
        start=1,
    )
}
ORDINAIS = {
    "PRIMEIRA": 1,
    "SEGUNDA": 2,
    "TERCEIRA": 3,
    "QUARTA": 4,
    "QUINTA": 5,
    "SEXTA": 6,
    "SÉTIMA": 7,
    "OITAVA": 8,
    "NONA": 9,
    "DÉCIMA": 10,
    "VIGÉSIMA": 20,
}
SIGLAS = {"resolucao-normativa": "REN", "resolucao-homologatoria": "REH", "despacho": "DSP"}
NIVEIS = {"PARTE": 0, "LIVRO": 0, "TÍTULO": 1, "CAPÍTULO": 2, "SEÇÃO": 3, "SUBSEÇÃO": 4}
FONTE_DATA = "publicacao - conferir vigencia"
FONTE_VIGENCIA = "artigo de vigencia da norma"
FONTE_INFERIDA = "inferida - conferir"


class ErroExtracao(Exception):
    """O HTML não tem a estrutura esperada."""


def _limpar(texto: str) -> str:
    return re.sub(r"\s+", " ", RE_MARCAS.sub("", texto)).strip()


def _romano(valor: str) -> int:
    numeros = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total, anterior = 0, 0
    for letra in reversed(valor):
        n = numeros[letra]
        total += -n if n < anterior else n
        anterior = max(anterior, n)
    return total


def _ordinal(texto: str) -> int | None:
    palavras = [ORDINAIS.get(p) for p in texto.upper().split()]
    return sum(palavras) if palavras and all(palavras) else None


def _data_extenso(dia: str, mes: str, ano: str) -> str | None:
    numero = MESES.get(mes.lower())
    return f"{ano}-{numero:02d}-{int(dia):02d}" if numero else None


def _ato(info: dict) -> dict:
    """Converte os dados do link do ato alterador em tipo, número, ano, data e URL."""
    ato = {"url": info.get("href")}
    m = RE_HREF_ATO.search(info.get("href") or "")
    if m:
        ato["tipo"] = SIGLAS.get(m.group(1), m.group(1))
        ato["ano"] = m.group(2)
        ato["numero"] = m.group(3)
    m = RE_DATA_NORMA.search(info.get("titulo") or "")
    if m:
        ato["data"] = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return ato


def _atos_vinculados(conteiner) -> list[dict]:
    """Lista "Atos que alteram, regulamentam ou revogam" que o site põe ao fim da norma."""
    extras = conteiner.find(id="extras") or conteiner.find(class_="atos-vinculados")
    if extras is None:
        return []
    lista = []
    for p in extras.find_all("p"):
        link = p.find("a")
        if link is None:
            continue
        titulo = link.get("data-original-title", "")
        ato = {"descricao": _limpar(p.get_text(" ")), "url": link.get("href")}
        m = RE_HREF_ATO.search(link.get("href") or "")
        if m:
            ato.update(tipo=SIGLAS.get(m.group(1), m.group(1)), ano=m.group(2))
        m = RE_DATA_ATO.search(titulo)
        if m:
            ato["data"] = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        ementa = titulo.split(" - ", 1)
        if len(ementa) == 2:
            ato["ementa"] = ementa[1].strip()
        lista.append(ato)
    extras.decompose()
    return lista


def _blocos(html: str, correcoes: list[dict] | None = None) -> dict:
    """Transforma a norma em blocos de texto (um por dispositivo) com marcadores."""
    sopa = BeautifulSoup(html, "html.parser")
    conteiner = sopa.find("div", id="law-content", class_="aneel-content") or sopa.find(
        "div", class_="aneel-content"
    )
    if conteiner is None:
        raise ErroExtracao("conteúdo da norma (div.aneel-content) não encontrado")

    for el in conteiner.find_all(["script", "style"]):
        el.decompose()
    vinculados = _atos_vinculados(conteiner)

    riscados = ("s", "del", "strike")
    for el in conteiner.find_all(attrs={"data-summary-type": "title"}):
        if el.parent is None:
            continue
        for br in el.find_all("br"):
            br.replace_with("\n")
        partes = [re.sub(r"\s+", " ", p).strip() for p in el.get_text("").split("\n")]
        partes = [p for p in partes if p]
        el.replace_with(f"\n\n{TIT}{SEP_TITULO.join(partes)}{TIT_F}\n\n")

    for el in conteiner.find_all(attrs={"data-summary-type": "article"}):
        numero = el.get("data-summary-id", "").removeprefix("article").strip().rstrip("º.")
        prefixo = "" if el.find_parent(riscados) else "\n\n"
        el.replace_with(f"{prefixo}{ART}{numero}|{el.get_text(' ', strip=True)}{ART_F} ")

    atos = []
    for a in conteiner.find_all("a", class_="link_law"):
        atos.append({"href": a.get("href"), "titulo": a.get("data-original-title", "")})
        a.replace_with(f"{a.get_text(' ', strip=True)}{ATO}{len(atos) - 1}{ATO_F}")

    tabelas = []
    for tabela in conteiner.find_all("table"):
        linhas = []
        for tr in tabela.find_all("tr"):
            celulas = [
                re.sub(r"\s+", " ", td.get_text("")).strip() for td in tr.find_all(["td", "th"])
            ]
            linhas.append(
                {
                    "celulas": celulas,
                    "destaque": tr.find(["b", "strong"]) is not None,
                    "tachado": tr.find(riscados) is not None,
                }
            )
        tabelas.append(linhas)
        tabela.replace_with(f"\n\n{TAB}{len(tabelas) - 1}{TAB_F}\n\n")

    for br in conteiner.find_all("br"):
        br.replace_with("\n")

    candidatos = conteiner.find_all(riscados) + conteiner.find_all(
        style=re.compile("line-through", re.IGNORECASE)
    )
    for el in candidatos:
        if el.parent is not None:
            el.replace_with(f"{RIS}{el.get_text()}{RIS_F}")

    # Um dispositivo começa após linha em branco (<br><br>) ou numa linha que já
    # começa com rótulo (alíneas e incisos às vezes vêm separados por um só <br>).
    # No cabeçalho (antes do primeiro título ou artigo), cada linha é um item próprio.
    brutos: list[str] = []
    novo, no_cabecalho = True, True
    for linha in conteiner.get_text("").split("\n"):
        linha = linha.strip(" \t\xa0")
        if not linha:
            novo = True
            continue
        if TIT in linha or ART in linha:
            no_cabecalho = False
        inicio = RE_INICIO_DISPOSITIVO.match(linha.lstrip(RIS + " "))
        if novo or no_cabecalho or inicio or not brutos:
            brutos.append(linha)
        else:
            brutos[-1] += " " + linha
        novo = False

    # correções manuais: quebra que falta no site (D019)
    normalizados = [re.sub(r"\s+", " ", bruto).strip() for bruto in brutos]
    for correcao in correcoes or []:
        if correcao["tipo"] != "quebra":
            continue
        alvo = re.sub(r"\s+", " ", correcao["antes_de"]).strip()
        divididos = []
        for bloco in normalizados:
            posicao = bloco.find(alvo)
            if posicao > 0:
                divididos += [bloco[:posicao].rstrip(), bloco[posicao:]]
                correcao["aplicada"] = correcao.get("aplicada", 0) + 1
            else:
                divididos.append(bloco)
        normalizados = divididos

    # O tachado pode abrir numa linha sem texto (ex.: <s><br>Art. 160 ...) e
    # continuar pelos blocos seguintes: a marcação é propagada até fechar.
    blocos, aberto = [], False
    for bloco in normalizados:
        if not bloco:
            continue
        if aberto and not bloco.startswith(RIS):
            bloco = RIS + bloco
        aberto = bloco.count(RIS) > bloco.count(RIS_F)
        if not _limpar(bloco) and TAB not in bloco:
            continue
        if aberto:
            bloco += RIS_F
        blocos.append(bloco)
    return {"blocos": blocos, "atos": atos, "tabelas": tabelas, "vinculados": vinculados}


def _separar_notas(texto: str, atos: list[dict]) -> tuple[str, list[dict]]:
    """Retira as notas "(Redação dada pela ...)" do fim do texto."""
    notas = []
    while m := RE_NOTA_FINAL.search(texto):
        bruto = m.group(1)
        nota = {"texto": _limpar(bruto)}
        indice = RE_ATO.search(bruto)
        if indice:
            nota["ato"] = _ato(atos[int(indice.group(1))])
        notas.insert(0, nota)
        texto = texto[: m.start()].rstrip()
    return texto, notas


def _tipo_nota(nota: dict) -> str:
    texto = nota["texto"].lower()
    for chave in ("redação dada", "redação acrescida", "revogad", "incluíd", "acrescid", "vide"):
        if texto.startswith(chave):
            return chave
    return "outra"


def _partes_riscado(bloco: str) -> tuple[bool, str, str]:
    """Separa o bloco em (tachado?, texto, resto depois do tachado)."""
    if bloco.startswith(RIS):
        fim = bloco.rfind(RIS_F)
        return True, bloco[len(RIS) : fim], bloco[fim + len(RIS_F) :]
    return False, re.sub(f"{RIS}.*?{RIS_F}", "", bloco), ""


def _descende(filho: str, pai: str) -> bool:
    return filho.startswith(pai + "_") or filho.startswith(pai + ".")


def _id_referencia(texto: str) -> str | None:
    """Converte "art. 76, § 5º" em "art76_par5"."""
    m = RE_REFERENCIA.search(texto)
    if not m:
        return None
    ident = f"art{m.group(1)}"
    if m.group(2):
        ident += f"_par{m.group(2)}"
    if m.group(3):
        ident += f"_inc{_romano(m.group(3).upper())}"
    return ident


def _tabela(linhas: list[dict], atos: list[dict]) -> dict:
    """Tabela com cabeçalho; nota de redação de cada linha separada das células."""
    if not linhas:
        return {"cabecalho": [], "linhas": []}
    cabecalho = [_limpar(c) for c in linhas[0]["celulas"]]
    registros = []
    for linha in linhas[1:]:
        celulas = list(linha["celulas"])
        extra = " ".join(celulas[len(cabecalho) :])
        celulas = celulas[: len(cabecalho)]
        notas = []
        if extra:
            _, notas = _separar_notas(extra, atos)
        elif celulas:
            celulas[-1], notas = _separar_notas(celulas[-1], atos)
        revogada = linha.get("tachado") or any(_tipo_nota(n) == "revogad" for n in notas)
        registro = {
            "celulas": [_limpar(c) for c in celulas],
            "destaque": linha["destaque"],
            "situacao": "revogada" if revogada else "vigente",
        }
        if notas:
            registro["nota"] = notas[0]["texto"]
            if "ato" in notas[0]:
                registro["ato"] = notas[0]["ato"]
        registros.append(registro)
    return {"cabecalho": cabecalho, "linhas": registros}


class _Montador:
    """Percorre os blocos e monta a lista de dispositivos com ids e histórico.

    As entradas de um artigo (ou de um anexo) são juntadas num grupo e só viram
    dispositivos quando o grupo termina, porque a redação nova de um dispositivo
    pode vir depois dos filhos tachados da redação antiga.
    """

    def __init__(self, atos: list[dict], tabelas: list[list[dict]]):
        self.atos = atos
        self.tabelas = tabelas
        self.estrutura: list[tuple[int, str]] = []
        self.dispositivos: list[dict] = []
        self.destino = self.dispositivos
        self.cabecalho: list[str] = []
        self.anexos: list[dict] = []
        self.anexo: dict | None = None
        self.clausula: str | None = None
        self.contexto = {"art": None, "par": None, "inc": None, "ali": None}
        self.ids: dict[str, int] = {}
        self.grupo: list[dict] = []
        self.revisao: list[dict] = []
        self.iniciou = False
        self.citando = False
        self.textos = 0
        self.textos_anexo = 0
        self.texto_riscado_anterior = False

    # identificação -----------------------------------------------------------
    def _caminho(self) -> str:
        """Id do dispositivo mais interno em vigor (ex.: art5_par1_inc2)."""
        partes = [self.contexto[n] for n in ("art", "par", "inc", "ali") if self.contexto[n]]
        return "_".join(partes) if partes else "norma"

    def _base(self, nivel: str) -> str | None:
        ordem = ["art", "par", "inc", "ali"]
        partes = [self.contexto[n] for n in ordem[: ordem.index(nivel)] if self.contexto[n]]
        return "_".join(partes) if partes else None

    def _identificar(self, texto: str) -> tuple[str, str, str, str] | None:
        """Devolve (tipo, id, rótulo, corpo) ou None se o bloco não é um dispositivo."""
        if m := RE_ARTIGO.match(texto):
            numero = m.group(1)
            self.contexto = {"art": f"art{numero}", "par": None, "inc": None, "ali": None}
            return "artigo", f"art{numero}", m.group(2).strip(), m.group(3)
        limpo = RE_MARCAS.sub("", texto)
        if (self.iniciou or self.contexto["art"]) and (m := RE_ARTIGO_TEXTO.match(limpo)):
            # redação nova de artigo escrita como texto simples, sem a marcação de artigo
            numero = m.group(2)
            self.contexto = {"art": f"art{numero}", "par": None, "inc": None, "ali": None}
            return "artigo", f"art{numero}", m.group(1), texto
        if not self.contexto["art"]:
            return None
        if m := RE_PARAGRAFO_UNICO.match(limpo):
            self.contexto.update(par="parunico", inc=None, ali=None)
            return "paragrafo", f"{self._base('par')}_parunico", m.group(1), texto
        if m := RE_PARAGRAFO.match(limpo):
            letra = f"-{m.group(3)}" if m.group(3) else ""
            self.contexto.update(par=f"par{m.group(2)}{letra}", inc=None, ali=None)
            return "paragrafo", f"{self._base('par')}_{self.contexto['par']}", m.group(1), texto
        if m := RE_INCISO.match(limpo):
            letra = f"-{m.group(3)}" if m.group(3) else ""
            self.contexto.update(inc=f"inc{_romano(m.group(2))}{letra}", ali=None)
            return "inciso", f"{self._base('inc')}_{self.contexto['inc']}", m.group(1), texto
        if m := RE_ALINEA.match(limpo):
            self.contexto["ali"] = f"ali{m.group(2)}"
            return "alinea", f"{self._base('ali')}_{self.contexto['ali']}", m.group(1), texto
        if m := RE_ITEM.match(limpo):
            return "item", f"{self._caminho()}_item{m.group(2)}", m.group(1), texto
        return None

    @staticmethod
    def _corpo(rotulo: str, texto: str) -> str:
        limpo = texto
        if _limpar(limpo).startswith(_limpar(rotulo)):
            # remove o rótulo do início preservando os marcadores de ato no restante
            alvo = _limpar(rotulo)
            consumido = ""
            for i, caractere in enumerate(limpo):
                if not RE_MARCAS.match(caractere):
                    consumido += caractere
                if _limpar(consumido) == alvo:
                    return limpo[i + 1 :].strip()
        return limpo.strip()

    def _nomes_estrutura(self) -> list[str]:
        return [nome for _, nome in self.estrutura]

    def _registrar_id(self, ident: str) -> str:
        if ident not in self.ids:
            self.ids[ident] = 1
            return ident
        self.ids[ident] += 1
        novo = f"{ident}_{self.ids[ident]}"
        self.revisao.append(
            {"id": novo, "motivo": f"id repetido: '{ident}' já existia; recebeu sufixo"}
        )
        return novo

    def _redacao(self, texto: str, notas: list[dict], situacao: str) -> dict:
        principal = next((n for n in notas if _tipo_nota(n) != "vide"), None)
        redacao = {"texto": _limpar(texto), "situacao": situacao}
        if principal:
            redacao["nota"] = principal["texto"]
            if "ato" in principal:
                redacao["ato"] = principal["ato"]
        extras = [n["texto"] for n in notas if n is not principal]
        if extras:
            redacao["notas_extras"] = extras
        return redacao

    def _entrada(self, tipo, ident, rotulo, corpo, riscado, resto, estrutura):
        """Guarda um dispositivo lido (ainda sem decidir a situação final)."""
        base_id = None
        corpo, notas = _separar_notas(corpo, self.atos)
        _, notas_resto = _separar_notas(resto, self.atos)
        revogacao = next((n for n in notas_resto + notas if _tipo_nota(n) == "revogad"), None)
        outras = [n for n in notas if n is not revogacao]
        if riscado:
            situacao = "substituida"
        else:
            situacao = "revogada" if revogacao else "vigente"
        if not riscado and not any(_tipo_nota(n) == "redação dada" for n in outras):
            repetidas = [e for e in self.grupo if e.get("base_id", e["id"]) == ident]
            if any(not e["riscado"] for e in repetidas):
                # mesmo rótulo de novo sem nota de nova redação: é outro dispositivo
                # (erro de numeração ou quebra ausente no site), não uma substituição
                novo = f"{ident}_{len(repetidas) + 1}"
                self.revisao.append(
                    {
                        "id": novo,
                        "motivo": f"rótulo repetido sem nota de nova redação; '{ident}' já "
                        "existia no mesmo artigo e este recebeu sufixo",
                    }
                )
                ident, base_id = novo, ident
        entrada = {
            "tipo": tipo,
            "id": ident,
            "rotulo": rotulo,
            "estrutura": estrutura,
            "riscado": riscado,
            "redacao": self._redacao(corpo, outras, situacao),
            "revogacao": revogacao,
        }
        if base_id:
            entrada["base_id"] = base_id
        self.grupo.append(entrada)
        return entrada

    # leitura dos blocos --------------------------------------------------------
    def processar(self, bloco: str):
        if TIT in bloco:
            self._titulo(bloco)
            return
        if m := RE_TABELA.fullmatch(bloco.strip(RIS + RIS_F + " ")):
            self._tabela(int(m.group(1)))
            return
        if self.anexo is not None:
            self._item_anexo(bloco)
            return
        if self.citando and not bloco.lstrip(RIS).startswith(ART):
            # texto entre aspas que altera outra norma: fica com o artigo que o transcreve
            artigo = next(e for e in reversed(self.grupo) if e["tipo"] == "artigo")
            riscado, texto, resto = _partes_riscado(bloco)
            _, notas_resto = _separar_notas(resto, self.atos)
            revogacao = next((n for n in notas_resto if _tipo_nota(n) == "revogad"), None)
            if riscado and revogacao and artigo["riscado"]:
                # "(Revogado pela ...)" depois do texto citado tachado vale para o artigo
                artigo["revogacao"] = revogacao
                bloco = texto
            artigo.setdefault("citacao", []).append(_limpar(bloco))
            return
        self.citando = False

        riscado, texto, resto = _partes_riscado(bloco)
        artigo_anterior = self.contexto["art"]
        identificado = self._identificar(texto.strip())
        if identificado is None:
            limpo = _limpar(bloco)
            if not self.iniciou and not self.contexto["art"]:
                self.cabecalho.append(limpo)
                return
            self.textos += 1
            self.grupo.append(
                {
                    "tipo": "texto",
                    "id": f"{self._caminho()}_texto{self.textos}",
                    "riscado": riscado,
                    "texto": limpo,
                    "estrutura": self._nomes_estrutura(),
                }
            )
            return

        self.iniciou = True
        tipo, ident, rotulo, corpo = identificado
        if tipo == "artigo" and ident != artigo_anterior:
            self._resolver()
        corpo = self._corpo(rotulo, corpo) if tipo != "artigo" else corpo.strip()
        entrada = self._entrada(tipo, ident, rotulo, corpo, riscado, resto, self._nomes_estrutura())
        if tipo == "artigo" and RE_ALTERACAO.search(entrada["redacao"]["texto"]):
            self.citando = True

    def _titulo(self, bloco: str):
        self._resolver()
        self.citando = False
        if RIS in bloco:
            return
        partes = [p.strip() for p in RE_MARCAS.sub(SEP_TITULO, bloco).split(SEP_TITULO)]
        partes = [p for p in partes if p]
        if not partes:
            return
        chave = partes[0].split()[0].upper()
        if chave.startswith("ANEXO"):
            m = re.match(r"ANEXO\s+([IVXL]+)\b", partes[0], re.IGNORECASE)
            numero = _romano(m.group(1).upper()) if m else len(self.anexos) + 1
            self.anexo = {
                "id": f"anexo{numero}",
                "rotulo": partes[0],
                "titulo": " - ".join(partes[1:]),
                "dispositivos": [],
                "tabelas": [],
            }
            self.anexos.append(self.anexo)
            self.destino = self.anexo["dispositivos"]
            self.clausula = None
            self.textos_anexo = 0
            self.texto_riscado_anterior = False
            return
        nivel = NIVEIS.get(chave, 3)
        self.estrutura = [e for e in self.estrutura if e[0] < nivel]
        self.estrutura.append((nivel, " - ".join(partes)))
        self.iniciou = True

    def _tabela(self, indice: int):
        tabela = _tabela(self.tabelas[indice], self.atos)
        if self.anexo is not None:
            if "Dispositivo" in tabela["cabecalho"]:
                coluna = tabela["cabecalho"].index("Dispositivo")
                for linha in tabela["linhas"]:
                    if coluna < len(linha["celulas"]):
                        linha["dispositivo_id"] = _id_referencia(linha["celulas"][coluna])
            self.anexo["tabelas"].append(tabela)
            return
        alvo = next((e for e in reversed(self.grupo) if "redacao" in e), None)
        if alvo is None:
            self.revisao.append({"id": "tabela", "motivo": "tabela fora de dispositivo"})
            return
        alvo.setdefault("tabelas", []).append(tabela)

    def _item_anexo(self, bloco: str):
        riscado, texto, resto = _partes_riscado(bloco)
        limpo = RE_MARCAS.sub("", texto).strip()
        base = self.anexo["id"]
        anterior = next((e for e in reversed(self.grupo) if "redacao" in e), None)
        if limpo.startswith("- ") and anterior is not None:
            # lista com travessão: continuação do item anterior
            anterior["redacao"]["texto"] += " " + _limpar(texto)
            return
        estrutura = [f"{self.anexo['rotulo']} - {self.anexo['titulo']}".strip(" -")]
        if m := RE_CLAUSULA.match(limpo):
            numero = _ordinal(m.group(1))
            tipo, rotulo, corpo = "clausula", "", texto
            ident = f"{base}_cl{numero}" if numero else f"{base}_cl{len(self.grupo)}"
        elif m := RE_ITEM_ANEXO.match(limpo):
            tipo, rotulo = "item", m.group(1).strip()
            ident = f"{base}_it{m.group(2)}"
            corpo = self._corpo(rotulo, texto)
        else:
            tipo, rotulo, corpo = "texto", "", texto
            if not (self.texto_riscado_anterior and not riscado):
                self.textos_anexo += 1
            ident = f"{base}_texto{self.textos_anexo}"
        self.texto_riscado_anterior = riscado and tipo == "texto"
        if tipo != "clausula" and self.clausula:
            estrutura.append(self.clausula)
        entrada = self._entrada(tipo, ident, rotulo, corpo, riscado, resto, estrutura)
        if tipo == "clausula" and not riscado:
            self.clausula = entrada["redacao"]["texto"]

    # resolução do grupo --------------------------------------------------------
    def _resolver(self):
        """Transforma as entradas do grupo em dispositivos com histórico e situação."""
        grupo, self.grupo = self.grupo, []
        if not grupo:
            return
        ordem: list[str] = []
        por_id: dict[str, list[dict]] = {}
        corrida: dict[int, int] = {}
        numero, dentro = 0, False
        for indice, e in enumerate(grupo):
            if "redacao" not in e:
                if not e["riscado"]:
                    dentro = False
                continue
            if e["id"] not in por_id:
                por_id[e["id"]] = []
                ordem.append(e["id"])
            por_id[e["id"]].append(e)
            if e["riscado"]:
                numero += 0 if dentro else 1
                corrida[indice] = numero
                dentro = True
            else:
                dentro = False
        indice_de = {id(e): i for i, e in enumerate(grupo)}

        def corridas(ident):
            return {corrida.get(indice_de[id(e)]) for e in por_id[ident]} - {None}

        disp = {ident: self._dispositivo(por_id[ident]) for ident in ordem}
        pendentes = [i for i in ordem if disp[i]["situacao"] is None]
        lugar: dict[str, str | None] = {}

        # 1. renumeração: "Parágrafo único" tachado que passou a "§ 1º"
        for ident in list(pendentes):
            if not ident.endswith("_parunico"):
                continue
            irmao = ident.removesuffix("parunico") + "par1"
            if irmao not in disp or disp[irmao]["situacao"] is None:
                continue
            self._renumerar(disp[ident], disp[irmao], disp)
            lugar[ident], lugar[irmao] = irmao, None
            pendentes.remove(ident)

        # 2. supressão: filho tachado de um dispositivo que recebeu nova redação
        for ident in list(pendentes):
            minhas = corridas(ident)
            pais = [
                a
                for a in ordem
                if _descende(ident, a)
                and corridas(a) & minhas
                and disp[a]["situacao"] in ("vigente", "revogado")
                and any(not e["riscado"] for e in por_id[a])
            ]
            if pais:
                self._suprimir(disp[ident], disp[max(pais, key=len)])
                pendentes.remove(ident)

        # 3. revogação do grupo: "(Revogado pela ...)" no último item tachado do grupo
        for ident in list(pendentes):
            minhas = corridas(ident)
            raiz = min(
                (a for a in ordem if (a == ident or _descende(ident, a)) and corridas(a) & minhas),
                key=len,
            )
            membros = [
                (indice_de[id(e)], e)
                for a in ordem
                if a == raiz or _descende(a, raiz)
                for e in por_id[a]
                if corrida.get(indice_de[id(e)]) in minhas
            ]
            ultimo = max(membros, key=lambda par: par[0])[1]
            if ultimo["revogacao"] and ultimo["id"] != ident:
                d = disp[ident]
                d["situacao"] = "revogado"
                d["redacoes"][-1]["situacao"] = "revogada"
                d["revogado_por"] = self._revogado_por(ultimo["revogacao"])
                d["revogado_por"]["nota_no_dispositivo"] = ultimo["id"]
                pendentes.remove(ident)

        # 4. o que sobrou: conferir
        for ident in pendentes:
            disp[ident]["situacao"] = "conferir"
            self.revisao.append(
                {
                    "id": ident,
                    "motivo": "redação tachada sem nova redação, sem nota de revogação e "
                    "sem dispositivo pai reescrito",
                }
            )

        emitidos: set[str] = set()
        for e in grupo:
            if "redacao" not in e:
                self.destino.append(
                    {
                        "id": self._registrar_id(e["id"]),
                        "tipo": "texto",
                        "rotulo": "",
                        "estrutura": e["estrutura"],
                        "situacao": "riscado" if e["riscado"] else "vigente",
                        "texto": e["texto"],
                        "redacoes": [],
                        "revogado_por": None,
                    }
                )
                continue
            alvo = lugar.get(e["id"], e["id"])
            if alvo is None or alvo in emitidos:
                continue
            emitidos.add(alvo)
            d = disp[alvo]
            d["id"] = self._registrar_id(alvo)
            self.destino.append(d)

    def _dispositivo(self, entradas: list[dict]) -> dict:
        vivas = [e for e in entradas if not e["riscado"]]
        redacoes = []
        for e in entradas:
            r = dict(e["redacao"])
            if vivas and not e["riscado"] and e is not vivas[-1]:
                # o site mostrou a redação antiga sem tachado, seguida da nova
                r["situacao"] = "substituida"
                r["sem_tachado"] = True
            redacoes.append(r)
        base = vivas[-1] if vivas else entradas[0]
        d = {
            "id": base["id"],
            "tipo": base["tipo"],
            "rotulo": base["rotulo"],
            "estrutura": base["estrutura"],
            "situacao": None,
            "texto": None,
            "redacoes": redacoes,
            "revogado_por": None,
        }
        for chave in ("citacao", "tabelas"):
            valores = [v for e in entradas for v in e.get(chave, [])]
            if valores:
                d[chave] = valores
        ultima = entradas[-1]
        if ultima["revogacao"]:
            d["situacao"] = "revogado"
            redacoes[-1]["situacao"] = "revogada"
            d["revogado_por"] = self._revogado_por(ultima["revogacao"])
        elif not ultima["riscado"]:
            d["situacao"] = "vigente"
            d["texto"] = redacoes[-1]["texto"]
        if any(r.get("sem_tachado") for r in redacoes):
            self.revisao.append(
                {
                    "id": d["id"],
                    "motivo": "duas redações sem tachado com o mesmo rótulo; a anterior foi "
                    "considerada substituída pela seguinte",
                }
            )
        return d

    @staticmethod
    def _revogado_por(nota: dict) -> dict:
        revogado_por = {"nota": nota["texto"]}
        if "ato" in nota:
            revogado_por["ato"] = nota["ato"]
        return revogado_por

    def _renumerar(self, unico: dict, primeiro: dict, disp: dict):
        """Parágrafo único que passou a § 1º: um só dispositivo, id antigo como apelido."""
        for r in unico["redacoes"]:
            r["rotulo"] = unico["rotulo"]
        primeiro["redacoes"] = unico["redacoes"] + primeiro["redacoes"]
        primeiro["ids_anteriores"] = [unico["id"]]
        primeiro["renumeracao"] = {"de": unico["rotulo"], "para": primeiro["rotulo"]}
        nova = primeiro["redacoes"][len(unico["redacoes"])]
        if "ato" not in nova:
            # sem nota no § 1º: vale o ato que acrescentou os novos parágrafos
            base = primeiro["id"].removesuffix("par1")
            irmaos = [disp[i] for i in disp if i.startswith(base + "par") and i != primeiro["id"]]
            ato = next((r["ato"] for d in irmaos for r in d["redacoes"][:1] if "ato" in r), None)
            if ato:
                nova["ato_inferido"] = ato
            self.revisao.append(
                {
                    "id": primeiro["id"],
                    "motivo": "renumeração sem nota própria; data inferida do ato que "
                    "acrescentou os outros parágrafos",
                }
            )

    @staticmethod
    def _suprimir(filho: dict, pai: dict):
        """Filho que deixou de existir com a nova redação do pai."""
        nova = next(
            (r for r in pai["redacoes"] if r["situacao"] in ("vigente", "revogada")),
            pai["redacoes"][-1],
        )
        filho["situacao"] = "suprimido"
        filho["redacoes"][-1]["situacao"] = "suprimida"
        suprimido_por = {
            "dispositivo": pai["id"],
            "nota": f"Suprimido pela nova redação do {pai['rotulo']}".strip()
            + (f" ({nova['nota']})" if nova.get("nota") else ""),
        }
        if "ato" in nova:
            suprimido_por["ato"] = nova["ato"]
        filho["suprimido_por"] = suprimido_por


def _datas(dispositivos: list[dict], data_norma: str | None, vigencia: str | None):
    """Preenche vigente_de/vigente_ate das redações (D006).

    Redação original: data do artigo de vigência da norma (ou a da norma, se não
    houver). Redação dada por outro ato: data do ato (publicação; conferir vigência).
    """
    for d in dispositivos:
        redacoes = d["redacoes"]
        for i, r in enumerate(redacoes):
            ato = r.get("ato") or {}
            if ato.get("data"):
                data, fonte = ato["data"], FONTE_DATA
            elif (r.get("ato_inferido") or {}).get("data"):
                data, fonte = r["ato_inferido"]["data"], FONTE_INFERIDA
            elif i == 0 and vigencia:
                data, fonte = vigencia, FONTE_VIGENCIA
            elif i == 0 and data_norma:
                data, fonte = data_norma, FONTE_DATA
            else:
                data, fonte = None, None
            r["vigente_de"] = data
            r["fonte_data"] = fonte
        for atual, seguinte in zip(redacoes, redacoes[1:], strict=False):
            atual["vigente_ate"] = seguinte.get("vigente_de")
        if redacoes:
            fim = d.get("revogado_por") or d.get("suprimido_por") or {}
            redacoes[-1]["vigente_ate"] = fim.get("ato", {}).get("data")


def _data_da_norma(cabecalho: list[str]) -> tuple[str | None, str | None]:
    for linha in cabecalho:
        if "RESOLUÇÃO" in linha.upper() and (m := RE_DATA_TITULO.search(linha)):
            data = _data_extenso(m.group(1), m.group(2), m.group(3))
            titulo = re.split(r"\s*(?:\(\*\)|Download)", linha)[0].strip()
            return titulo, data
    return None, None


def _vigencia(dispositivos: list[dict], data_norma: str | None) -> dict | None:
    """Data de entrada em vigor lida do artigo de vigência ("Esta Resolução entra em vigor")."""
    for d in reversed(dispositivos):
        if d["tipo"] != "artigo" or not d["texto"]:
            continue
        if m := RE_VIGOR.search(d["texto"]):
            data = _data_extenso(m.group(1), m.group(2), m.group(3))
            if data:
                return {"data": data, "dispositivo": d["id"]}
        if RE_VIGOR_PUBLICACAO.search(d["texto"]) and data_norma:
            return {"data": data_norma, "dispositivo": d["id"]}
    return None


def extrair(html: str, correcoes: list[dict] | None = None) -> dict:
    """Extrai a norma do HTML do leis.org e devolve o texto canônico (sem metadados de fonte).

    `correcoes`: correções manuais da norma (ver `monitor_normas.correcoes`).
    """
    correcoes = [dict(c) for c in correcoes or []]
    lido = _blocos(html, correcoes)
    montador = _Montador(lido["atos"], lido["tabelas"])
    for correcao in correcoes:
        if correcao.get("aplicada", 0) != 1:
            montador.revisao.append(
                {
                    "id": "correcao",
                    "motivo": f"correção manual aplicada {correcao.get('aplicada', 0)} vez(es), "
                    f"esperado 1: {correcao['antes_de']!r}",
                }
            )
    for bloco in lido["blocos"]:
        montador.processar(bloco)
    montador._resolver()

    dispositivos = montador.dispositivos
    if not any(d["tipo"] == "artigo" for d in dispositivos):
        raise ErroExtracao("nenhum artigo encontrado")

    # fecho: assinatura e notas de publicação depois do último artigo
    fecho = []
    while dispositivos and dispositivos[-1]["tipo"] == "texto":
        fecho.insert(0, dispositivos.pop()["texto"])

    titulo, data_norma = _data_da_norma(montador.cabecalho)
    vigencia = _vigencia(dispositivos, data_norma)
    data_vigencia = vigencia["data"] if vigencia else None
    _datas(dispositivos, data_norma, data_vigencia)
    for anexo in montador.anexos:
        _datas(anexo["dispositivos"], data_norma, data_vigencia)

    notas: dict[str, int] = {}
    tipos: dict[str, int] = {}
    situacoes: dict[str, int] = {}
    for d in dispositivos:
        tipos[d["tipo"]] = tipos.get(d["tipo"], 0) + 1
        situacoes[d["situacao"]] = situacoes.get(d["situacao"], 0) + 1
        for r in d["redacoes"]:
            if "nota" in r:
                chave = _tipo_nota({"texto": r["nota"]})
                notas[chave] = notas.get(chave, 0) + 1
        if d["revogado_por"]:
            notas["revogad"] = notas.get("revogad", 0) + 1

    return {
        "titulo": titulo,
        "data": data_norma,
        "vigencia": vigencia,
        "cabecalho": montador.cabecalho,
        "dispositivos": dispositivos,
        "fecho": fecho,
        "anexos": montador.anexos,
        "atos_vinculados": lido["vinculados"],
        "correcoes": [
            {k: c[k] for k in ("tipo", "antes_de", "motivo")} | {"aplicada": c.get("aplicada", 0)}
            for c in correcoes
        ],
        "revisao": montador.revisao,
        "estatisticas": {
            "por_tipo": tipos,
            "por_situacao": situacoes,
            "revogados": situacoes.get("revogado", 0),
            "suprimidos": situacoes.get("suprimido", 0),
            "renumerados": sum("renumeracao" in d for d in dispositivos),
            "a_conferir": situacoes.get("conferir", 0),
            "notas": notas,
            "anexos": {a["id"]: len(a["dispositivos"]) for a in montador.anexos},
            "tabelas": len(lido["tabelas"]),
            "para_revisao": len(montador.revisao),
        },
    }


CHAVES_CONTEUDO = (
    "titulo",
    "data",
    "vigencia",
    "cabecalho",
    "dispositivos",
    "fecho",
    "anexos",
    "atos_vinculados",
    "correcoes",
)


def hash_canonico(canonico: dict) -> str:
    conteudo = {k: canonico.get(k) for k in CHAVES_CONTEUDO}
    texto = json.dumps(conteudo, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _markdown_tabela(tabela: dict) -> list[str]:
    def celula(texto: str) -> str:
        return texto.replace("|", "\\|")

    cabecalho = list(tabela["cabecalho"])
    com_nota = any("nota" in linha for linha in tabela["linhas"])
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
            celulas.append(linha.get("nota", ""))
        linhas.append("| " + " | ".join(celula(c) for c in celulas) + " |")
    return [*linhas, ""]


def _markdown_dispositivo(d: dict) -> list[str]:
    """Linhas de um dispositivo no Markdown vigente (D007)."""
    if d["situacao"] in ("suprimido", "conferir") or (
        d["tipo"] == "texto" and d["situacao"] != "vigente"
    ):
        return []
    ancora = f'<a id="{d["id"]}"></a>'
    linhas: list[str] = []
    if d["situacao"] == "revogado":
        nota = d["revogado_por"]["nota"]
        prefixo = "###### " if d["tipo"] == "artigo" else ""
        rotulo = d["rotulo"] or d["redacoes"][-1]["texto"][:60]
        return [f"{prefixo}{ancora}{rotulo} ({nota})", ""]
    if d["tipo"] == "artigo":
        linhas += [f"###### {ancora}{d['rotulo']}", ""]
        if d["texto"]:
            linhas += [d["texto"], ""]
    elif d["tipo"] == "clausula":
        linhas += [f"### {ancora}{d['texto']}", ""]
    elif d["tipo"] == "texto" and not d["redacoes"]:
        linhas += [d["texto"], ""]
    else:
        linhas += [f"{ancora}{d['rotulo']} {d['texto'] or ''}".strip(), ""]
    vigente = d["redacoes"][-1] if d["redacoes"] else {}
    if vigente.get("nota"):
        linhas += [f"> {vigente['nota']}", ""]
    for texto in d.get("citacao", []):
        linhas += [texto, ""]
    for tabela in d.get("tabelas", []):
        linhas += _markdown_tabela(tabela)
    return linhas


def gerar_markdown(canonico: dict, norma_id: str, fonte: dict) -> str:
    """Markdown vigente (D007): revogados como marcador, notas de redação mantidas."""
    linhas = [
        "---",
        f"norma: {norma_id}",
        f'titulo: "{canonico["titulo"] or norma_id}"',
        f"fonte_url: {fonte.get('url', '')}",
        f"data_captura: {fonte.get('capturado_em', '')}",
        f'padrao: "{PADRAO_MARKDOWN}"',
        f"hash_canonico: {canonico['hash_canonico']}",
        "---",
        "",
        f"# {canonico['titulo'] or norma_id}",
        "",
    ]
    for linha in canonico["cabecalho"]:
        titulo = canonico["titulo"] or ""
        if titulo and linha.startswith(titulo):
            linha = linha[len(titulo) :]
        # links de download do site não fazem parte do texto da norma
        linha = re.sub(r"Download\s.*?(?=Download\s|\(Vide|$)", "", linha).strip()
        if linha and linha != "(*)":
            linhas += [linha, ""]

    estrutura_atual: list[str] = []
    revogados: set[str] = set()
    for d in canonico["dispositivos"]:
        if d["situacao"] == "revogado":
            pai_revogado = any(_descende(d["id"], pai) for pai in revogados)
            revogados.add(d["id"])
            if pai_revogado:
                # filho de dispositivo revogado: basta o marcador do pai
                continue
        conteudo = _markdown_dispositivo(d)
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
                linhas += [f"{'#' * min(nivel + 2, 5)} {nome}", ""]
            estrutura_atual = d["estrutura"]
        linhas += conteudo

    for texto in canonico.get("fecho", []):
        linhas += [texto, ""]

    for anexo in canonico["anexos"]:
        titulo = f"{anexo['rotulo']} - {anexo['titulo']}".strip(" -")
        linhas += [f'## <a id="{anexo["id"]}"></a>{titulo}', ""]
        for d in anexo["dispositivos"]:
            linhas += _markdown_dispositivo(d)
        for tabela in anexo["tabelas"]:
            linhas += _markdown_tabela(tabela)
    return "\n".join(linhas).rstrip() + "\n"


def gerar_revisao(canonico: dict, norma_id: str) -> str:
    """Relatório dos casos que a extração não resolveu sozinha ou resolveu por inferência."""
    todos = {d["id"]: d for d in canonico["dispositivos"]}
    for anexo in canonico["anexos"]:
        todos.update({d["id"]: d for d in anexo["dispositivos"]})
    linhas = [
        f"# Revisão da extração: {norma_id}",
        "",
        "Casos que a extração não resolveu sozinha ou resolveu por inferência. "
        "Gerado automaticamente a cada extração.",
        "",
        f"Total: {len(canonico['revisao'])}",
        "",
    ]
    for caso in canonico["revisao"]:
        d = todos.get(caso["id"])
        linhas += [f"## {caso['id']}", "", f"Motivo: {caso['motivo']}", ""]
        if d is None:
            continue
        linhas += [f"Situação: {d['situacao']}", ""]
        for r in d["redacoes"]:
            rotulo = r.get("rotulo", d["rotulo"])
            nota = f" ({r['nota']})" if r.get("nota") else ""
            periodo = f"{r.get('vigente_de') or '?'} a {r.get('vigente_ate') or '...'}"
            linhas += [f"- [{r['situacao']}, {periodo}] {rotulo} {r['texto']}{nota}".strip(), ""]
    sem_ligacao = [
        (anexo["id"], linha["celulas"])
        for anexo in canonico["anexos"]
        for tabela in anexo["tabelas"]
        for linha in tabela["linhas"]
        if "dispositivo_id" in linha and linha["dispositivo_id"] not in todos
    ]
    if sem_ligacao:
        linhas += ["## Linhas de tabela sem dispositivo correspondente", ""]
        linhas += [f"- {anexo}: {' | '.join(celulas)}" for anexo, celulas in sem_ligacao]
        linhas += [""]
    return "\n".join(linhas).rstrip() + "\n"


def processar(
    arquivo_html: Path,
    norma_id: str,
    url: str,
    pasta_canonico: Path = PASTA_CANONICO,
    pasta_markdown: Path = PASTA_MARKDOWN,
    pasta_revisao: Path = PASTA_REVISAO,
    pasta_correcoes: Path = PASTA_CORRECOES,
) -> dict:
    """Extrai o HTML salvo e grava o canônico, o Markdown e a revisão, se o conteúdo mudou."""
    html = Path(arquivo_html).read_text(encoding="utf-8")
    canonico = extrair(html, carregar_correcoes(norma_id, pasta_correcoes))
    canonico["hash_canonico"] = hash_canonico(canonico)
    capturado = re.match(r"(\d{8}T\d{6})", Path(arquivo_html).name)
    fonte = {
        "url": url,
        "capturado_em": (
            datetime.strptime(capturado.group(1), "%Y%m%dT%H%M%S").isoformat()
            if capturado
            else None
        ),
        "sha256_html": hashlib.sha256(html.encode("utf-8")).hexdigest(),
    }

    arquivo_canonico = Path(pasta_canonico) / f"{norma_id}.json"
    arquivo_markdown = Path(pasta_markdown) / norma_id / "vigente.md"
    arquivo_revisao = Path(pasta_revisao) / f"{norma_id}.md"
    anterior = None
    if arquivo_canonico.exists():
        anterior = json.loads(arquivo_canonico.read_text(encoding="utf-8")).get("hash_canonico")
    mudou = anterior != canonico["hash_canonico"]

    if mudou:
        documento = {"norma": norma_id, "fonte": fonte, **canonico}
        arquivo_canonico.parent.mkdir(parents=True, exist_ok=True)
        arquivo_canonico.write_text(
            json.dumps(documento, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        arquivo_markdown.parent.mkdir(parents=True, exist_ok=True)
        arquivo_markdown.write_text(gerar_markdown(canonico, norma_id, fonte), encoding="utf-8")
        arquivo_revisao.parent.mkdir(parents=True, exist_ok=True)
        arquivo_revisao.write_text(gerar_revisao(canonico, norma_id), encoding="utf-8")

    return {
        "mudou": mudou,
        "canonico": arquivo_canonico,
        "markdown": arquivo_markdown,
        "revisao": arquivo_revisao,
        "estatisticas": canonico["estatisticas"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extrai a norma de um HTML do leis.org.")
    parser.add_argument(
        "html", nargs="?", type=Path, help="HTML capturado (padrão: o mais recente)"
    )
    parser.add_argument("--norma", help="id da norma no catálogo (padrão: a primeira do leis.org)")
    args = parser.parse_args(argv)

    normas = [n for n in carregar_catalogo() if n.fonte == "leis.org"]
    norma = next((n for n in normas if n.id == args.norma), None) if args.norma else normas[0]
    if norma is None:
        print(f"ERRO norma não encontrada no catálogo: {args.norma}")
        return 1

    arquivo = args.html
    if arquivo is None:
        capturas = sorted((PASTA_BRUTOS / norma.id).glob("*.html"))
        if not capturas:
            print(f"ERRO nenhum HTML capturado em {PASTA_BRUTOS / norma.id}")
            return 1
        arquivo = capturas[-1]

    try:
        resultado = processar(arquivo, norma.id, norma.url)
    except (ErroExtracao, ErroCorrecoes) as erro:
        print(f"ERRO {norma.id}: {erro}")
        return 1

    situacao = "atualizado" if resultado["mudou"] else "sem mudança no conteúdo"
    print(f"OK {norma.id} ({situacao})")
    print(f"  Canônico: {resultado['canonico']}")
    print(f"  Markdown: {resultado['markdown']}")
    print(f"  Revisão: {resultado['revisao']}")
    print("  Estatísticas: " + json.dumps(resultado["estatisticas"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
