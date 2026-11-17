"""Extração de uma norma publicada no leis.org para texto canônico e Markdown vigente.

Estrutura da página (verificada na REN 1.000/2021):
- a norma fica em div#law-content.aneel-content, como texto corrido em que os
  dispositivos são separados por <br><br>;
- títulos, capítulos e seções: elementos com data-summary-type="title";
- artigos: span com data-summary-type="article" e data-summary-id="article48-A";
- redação superada e dispositivo revogado: texto dentro de <s> (ou com estilo
  line-through), seguido da nova redação ou de "(Revogado pela ...)";
- notas "(Redação dada pela ...)", "(Redação acrescida pela ...)" com link
  a.link_law para o ato alterador, cujo título traz "Data da Norma: dd.mm.aaaa".

Saídas (D004, D006, D007):
- dados/canonico/<id>.json: um registro por dispositivo, com o histórico de redações;
- dados/markdown/<id>/vigente.md: texto vigente, revogados como marcador.

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

PADRAO_MARKDOWN = "0.1"
PASTA_BRUTOS = Path("dados/brutos")
PASTA_CANONICO = Path("dados/canonico")
PASTA_MARKDOWN = Path("dados/markdown")

# marcadores internos (área de uso privado do Unicode, não aparecem em textos reais)
TIT, TIT_F = "", ""
ART, ART_F = "", ""
RIS, RIS_F = "", ""
ATO, ATO_F = "", ""
SEP_TITULO = ""

RE_ATO = re.compile(f"{ATO}(\\d+){ATO_F}")
RE_MARCAS = re.compile(f"[{TIT}{TIT_F}{ART}{ART_F}{RIS}{RIS_F}{SEP_TITULO}]|{ATO}\\d+{ATO_F}")
RE_NOTA_FINAL = re.compile(
    r"\(\s*((?:Redação dada|Redação acrescida|Revogad[oa]|Incluíd[oa]|Acrescid[oa]|Vide)\b"
    r"[^()]*(?:\([^()]*\)[^()]*)*)\)\s*[.;]?\s*$"
)
RE_ARTIGO = re.compile(f"^{ART}([^|]*)\\|([^{ART_F}]*){ART_F}\\s*(.*)$", re.DOTALL)
RE_ARTIGO_TEXTO = re.compile(r"^(Art\.\s*(\d+(?:-[A-Z]+)?)\s*[º°]?\.?)\s*(.*)$", re.DOTALL)
RE_PARAGRAFO = re.compile(r"^(§\s*(\d+)º?\.?)\s*(.*)$", re.DOTALL)
RE_PARAGRAFO_UNICO = re.compile(r"^(Parágrafo único\.?)\s*(.*)$", re.DOTALL | re.IGNORECASE)
# só I, V, X e L: evita confundir variáveis de fórmulas ("C - consumo") com incisos
RE_INCISO = re.compile(r"^(([IVXL]+)\s*[-–—])\s*(.*)$", re.DOTALL)
RE_INICIO_DISPOSITIVO = re.compile(
    f"^({ART}|{TIT}"
    r"|Art\.\s*\d|§\s*\d|Parágrafo único|[IVXL]+\s*[-–—]\s|[a-z]\)\s|\d+\.\s)"
)
RE_ALINEA = re.compile(r"^(([a-z])\))\s*(.*)$", re.DOTALL)
RE_ITEM = re.compile(r"^((\d+)\.)\s+(.*)$", re.DOTALL)
RE_DATA_NORMA = re.compile(r"Data da Norma:\s*(\d{2})\.(\d{2})\.(\d{4})")
RE_DATA_TITULO = re.compile(r"DE (\d{1,2}) DE ([A-ZÇ]+) DE (\d{4})", re.IGNORECASE)
RE_HREF_ATO = re.compile(r"/lei/([^/]+)/(\d{4})/([^/]+)/")

MESES = {
    m: i
    for i, m in enumerate(
        "janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro "
        "dezembro".split(),
        start=1,
    )
}
SIGLAS = {"resolucao-normativa": "REN", "resolucao-homologatoria": "REH", "despacho": "DSP"}
NIVEIS = {"PARTE": 0, "LIVRO": 0, "TÍTULO": 1, "CAPÍTULO": 2, "SEÇÃO": 3, "SUBSEÇÃO": 4}
FONTE_DATA = "publicacao - conferir vigencia"


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


def _blocos(html: str) -> tuple[list[str], list[dict]]:
    """Transforma a norma em blocos de texto (um por dispositivo) com marcadores."""
    sopa = BeautifulSoup(html, "html.parser")
    conteiner = sopa.find("div", id="law-content", class_="aneel-content") or sopa.find(
        "div", class_="aneel-content"
    )
    if conteiner is None:
        raise ErroExtracao("conteúdo da norma (div.aneel-content) não encontrado")

    for el in conteiner.find_all(["script", "style"]):
        el.decompose()

    riscados = ("s", "del", "strike")
    for el in conteiner.find_all(attrs={"data-summary-type": "title"}):
        if el.parent is None:
            continue
        partes = [p.strip() for p in el.get_text("\n").split("\n") if p.strip()]
        el.replace_with(f"\n\n{TIT}{SEP_TITULO.join(partes)}{TIT_F}\n\n")

    for el in conteiner.find_all(attrs={"data-summary-type": "article"}):
        numero = el.get("data-summary-id", "").removeprefix("article").strip().rstrip("º.")
        prefixo = "" if el.find_parent(riscados) else "\n\n"
        el.replace_with(f"{prefixo}{ART}{numero}|{el.get_text(' ', strip=True)}{ART_F} ")

    atos = []
    for a in conteiner.find_all("a", class_="link_law"):
        atos.append({"href": a.get("href"), "titulo": a.get("data-original-title", "")})
        a.replace_with(f"{a.get_text(' ', strip=True)}{ATO}{len(atos) - 1}{ATO_F}")

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
        linha = linha.strip(" \t ")
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

    blocos, aberto = [], False
    for bruto in brutos:
        bloco = re.sub(r"\s+", " ", bruto).strip()
        if not bloco or not _limpar(bloco):
            continue
        if aberto and not bloco.startswith(RIS):
            bloco = RIS + bloco
        aberto = bloco.count(RIS) > bloco.count(RIS_F)
        if aberto:
            bloco += RIS_F
        blocos.append(bloco)
    return blocos, atos


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


class _Montador:
    """Percorre os blocos e monta a lista de dispositivos com ids e histórico."""

    def __init__(self, atos: list[dict]):
        self.atos = atos
        self.estrutura: list[tuple[int, str]] = []
        self.dispositivos: list[dict] = []
        self.cabecalho: list[str] = []
        self.anexos: list[dict] = []
        self.contexto = {"art": None, "par": None, "inc": None, "ali": None}
        self.ids: dict[str, int] = {}
        self.pendentes: list[dict] = []
        self.pendente_id: str | None = None
        self.pendente_info: tuple[str, str, str] | None = None
        self.iniciou = False
        self.textos = 0

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
            self.contexto.update(par=f"par{m.group(2)}", inc=None, ali=None)
            return "paragrafo", f"{self._base('par')}_par{m.group(2)}", m.group(1), texto
        if m := RE_INCISO.match(limpo):
            self.contexto.update(inc=f"inc{_romano(m.group(2))}", ali=None)
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

    # montagem ----------------------------------------------------------------
    def _registrar_id(self, ident: str) -> str:
        if ident not in self.ids:
            self.ids[ident] = 1
            return ident
        self.ids[ident] += 1
        return f"{ident}_{self.ids[ident]}"

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

    def _fechar_pendentes(self):
        if not self.pendentes:
            return
        tipo, ident, rotulo = self.pendente_info
        self._emitir(tipo, ident, rotulo, self.pendentes, situacao="conferir")
        self.pendentes = []
        self.pendente_id = None

    def _emitir(self, tipo, ident, rotulo, redacoes, situacao, revogado_por=None):
        ident = self._registrar_id(ident)
        atual = next((r for r in reversed(redacoes) if r["situacao"] == "vigente"), None)
        self.dispositivos.append(
            {
                "id": ident,
                "tipo": tipo,
                "rotulo": rotulo,
                "estrutura": [nome for _, nome in self.estrutura],
                "situacao": situacao,
                "texto": atual["texto"] if atual else None,
                "redacoes": redacoes,
                "revogado_por": revogado_por,
            }
        )

    def processar(self, bloco: str):
        limpo = _limpar(bloco)
        if TIT in bloco:
            self._fechar_pendentes()
            if RIS in bloco:
                return
            partes = [p.strip() for p in RE_MARCAS.sub(SEP_TITULO, bloco).split(SEP_TITULO)]
            partes = [p for p in partes if p]
            if not partes:
                return
            chave = partes[0].split()[0].upper()
            if chave.startswith("ANEXO"):
                self.anexos.append({"titulo": " - ".join(partes), "texto": []})
                return
            nivel = NIVEIS.get(chave, 3)
            self.estrutura = [e for e in self.estrutura if e[0] < nivel]
            self.estrutura.append((nivel, " - ".join(partes)))
            self.iniciou = True
            return

        if self.anexos:
            self.anexos[-1]["texto"].append(limpo)
            return

        riscado = bloco.startswith(RIS)
        if riscado:
            fim = bloco.rfind(RIS_F)
            texto, resto = bloco[len(RIS) : fim], bloco[fim + len(RIS_F) :]
        else:
            texto, resto = re.sub(f"{RIS}.*?{RIS_F}", "", bloco), ""

        identificado = self._identificar(texto.strip())
        if identificado is None:
            if not self.iniciou and not self.contexto["art"]:
                self.cabecalho.append(limpo)
            else:
                self._fechar_pendentes()
                self.textos += 1
                self.dispositivos.append(
                    {
                        "id": self._registrar_id(f"{self._caminho()}_texto{self.textos}"),
                        "tipo": "texto",
                        "rotulo": "",
                        "estrutura": [nome for _, nome in self.estrutura],
                        "situacao": "riscado" if riscado else "vigente",
                        "texto": limpo,
                        "redacoes": [],
                        "revogado_por": None,
                    }
                )
            return

        self.iniciou = True
        tipo, ident, rotulo, corpo = identificado
        corpo = self._corpo(rotulo, corpo) if tipo != "artigo" else corpo.strip()

        if self.pendentes and ident != self.pendente_id:
            self._fechar_pendentes()

        if riscado:
            corpo, notas = _separar_notas(corpo, self.atos)
            _, notas_resto = _separar_notas(resto, self.atos)
            revogacao = next((n for n in notas_resto if _tipo_nota(n) == "revogad"), None)
            self.pendentes.append(self._redacao(corpo, notas, "substituida"))
            self.pendente_id = ident
            self.pendente_info = (tipo, ident, rotulo)
            if revogacao is None:
                revogacao = next((n for n in notas if _tipo_nota(n) == "revogad"), None)
            if revogacao:
                self.pendentes[-1]["situacao"] = "revogada"
                revogado_por = {"nota": revogacao["texto"]}
                if "ato" in revogacao:
                    revogado_por["ato"] = revogacao["ato"]
                self._emitir(
                    tipo,
                    ident,
                    rotulo,
                    self.pendentes,
                    situacao="revogado",
                    revogado_por=revogado_por,
                )
                self.pendentes = []
                self.pendente_id = None
            return

        corpo, notas = _separar_notas(corpo, self.atos)
        revogacao = next((n for n in notas if _tipo_nota(n) == "revogad"), None)
        if revogacao:
            # revogado sem texto riscado: o site só acrescentou a nota "(Revogado pela ...)"
            outras = [n for n in notas if n is not revogacao]
            redacoes = [*self.pendentes, self._redacao(corpo, outras, "revogada")]
            revogado_por = {"nota": revogacao["texto"]}
            if "ato" in revogacao:
                revogado_por["ato"] = revogacao["ato"]
            self._emitir(tipo, ident, rotulo, redacoes, "revogado", revogado_por=revogado_por)
        else:
            redacoes = [*self.pendentes, self._redacao(corpo, notas, "vigente")]
            self._emitir(tipo, ident, rotulo, redacoes, situacao="vigente")
        self.pendentes = []
        self.pendente_id = None


def _datas(dispositivos: list[dict], data_norma: str | None):
    """Preenche vigente_de/vigente_ate das redações a partir das datas dos atos (D006)."""
    for d in dispositivos:
        redacoes = d["redacoes"]
        for i, r in enumerate(redacoes):
            data = r.get("ato", {}).get("data") or (data_norma if i == 0 else None)
            r["vigente_de"] = data
            r["fonte_data"] = FONTE_DATA if data else None
        for atual, seguinte in zip(redacoes, redacoes[1:], strict=False):
            atual["vigente_ate"] = seguinte.get("vigente_de")
        if redacoes:
            fim = (d.get("revogado_por") or {}).get("ato", {}).get("data")
            redacoes[-1]["vigente_ate"] = fim


def _data_da_norma(cabecalho: list[str]) -> tuple[str | None, str | None]:
    for linha in cabecalho:
        if "RESOLUÇÃO" in linha.upper() and (m := RE_DATA_TITULO.search(linha)):
            mes = MESES.get(m.group(2).lower())
            data = f"{m.group(3)}-{mes:02d}-{int(m.group(1)):02d}" if mes else None
            titulo = re.split(r"\s*(?:\(\*\)|Download)", linha)[0].strip()
            return titulo, data
    return None, None


def extrair(html: str) -> dict:
    """Extrai a norma do HTML do leis.org e devolve o texto canônico (sem metadados de fonte)."""
    blocos, atos = _blocos(html)
    montador = _Montador(atos)
    for bloco in blocos:
        montador.processar(bloco)
    montador._fechar_pendentes()

    titulo, data_norma = _data_da_norma(montador.cabecalho)
    _datas(montador.dispositivos, data_norma)

    dispositivos = montador.dispositivos
    if not any(d["tipo"] == "artigo" for d in dispositivos):
        raise ErroExtracao("nenhum artigo encontrado")

    notas: dict[str, int] = {}
    for d in dispositivos:
        for r in d["redacoes"]:
            if "nota" in r:
                chave = _tipo_nota({"texto": r["nota"]})
                notas[chave] = notas.get(chave, 0) + 1
        if d["revogado_por"]:
            notas["revogad"] = notas.get("revogad", 0) + 1

    tipos: dict[str, int] = {}
    for d in dispositivos:
        tipos[d["tipo"]] = tipos.get(d["tipo"], 0) + 1

    return {
        "titulo": titulo,
        "data": data_norma,
        "cabecalho": montador.cabecalho,
        "dispositivos": dispositivos,
        "anexos": montador.anexos,
        "estatisticas": {
            "por_tipo": tipos,
            "revogados": sum(d["situacao"] == "revogado" for d in dispositivos),
            "a_conferir": sum(d["situacao"] == "conferir" for d in dispositivos),
            "notas": notas,
        },
    }


def hash_canonico(canonico: dict) -> str:
    conteudo = {k: canonico[k] for k in ("titulo", "data", "cabecalho", "dispositivos", "anexos")}
    texto = json.dumps(conteudo, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


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
    for d in canonico["dispositivos"]:
        if d["tipo"] == "texto" and d["situacao"] != "vigente":
            continue
        if d["situacao"] == "conferir" and not d["texto"]:
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

        ancora = f'<a id="{d["id"]}"></a>'
        if d["situacao"] == "revogado":
            nota = d["revogado_por"]["nota"]
            prefixo = "###### " if d["tipo"] == "artigo" else ""
            linhas += [f"{prefixo}{ancora}{d['rotulo']} ({nota})", ""]
            continue
        if d["tipo"] == "artigo":
            linhas += [f"###### {ancora}{d['rotulo']}", ""]
            if d["texto"]:
                linhas += [d["texto"], ""]
        elif d["tipo"] == "texto":
            linhas += [d["texto"], ""]
        else:
            linhas += [f"{ancora}{d['rotulo']} {d['texto'] or ''}".rstrip(), ""]
        vigente = d["redacoes"][-1] if d["redacoes"] else {}
        if vigente.get("nota"):
            linhas += [f"> {vigente['nota']}", ""]

    for anexo in canonico["anexos"]:
        linhas += [f"## {anexo['titulo']}", ""]
        linhas += [t for texto in anexo["texto"] for t in (texto, "")]
    return "\n".join(linhas).rstrip() + "\n"


def processar(
    arquivo_html: Path,
    norma_id: str,
    url: str,
    pasta_canonico: Path = PASTA_CANONICO,
    pasta_markdown: Path = PASTA_MARKDOWN,
) -> dict:
    """Extrai o HTML salvo e grava o canônico e o Markdown, se o conteúdo mudou."""
    html = Path(arquivo_html).read_text(encoding="utf-8")
    canonico = extrair(html)
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

    return {
        "mudou": mudou,
        "canonico": arquivo_canonico,
        "markdown": arquivo_markdown,
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
    except ErroExtracao as erro:
        print(f"ERRO {norma.id}: {erro}")
        return 1

    situacao = "atualizado" if resultado["mudou"] else "sem mudança no conteúdo"
    print(f"OK {norma.id} ({situacao})")
    print(f"  Canônico: {resultado['canonico']}")
    print(f"  Markdown: {resultado['markdown']}")
    print("  Estatísticas: " + json.dumps(resultado["estatisticas"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
