"""Captura pelo Chrome do computador local.

Abre o Google Chrome de verdade (não controlado por automação) na página da
norma, com um perfil dedicado ao projeto. Se o site apresentar uma
verificação, a pessoa a conclui na janela, normalmente. O script apenas
acompanha o título da aba pela porta de depuração do Chrome e, quando a
página da norma carrega, conecta-se para ler o HTML. Nada é feito para
contornar a verificação.

Salva em dados/brutos/<id>/ (fora do Git):
- <momento>-<hash>.html: a página;
- <momento>-<hash>.estrutura.json: relatório da estrutura da página, útil para
  conferir se o site mudou o formato.
Em seguida roda a extração (monitor_normas.extracao_leis_org), que atualiza o
canônico e o Markdown quando o conteúdo da norma muda.

Uso: python -m monitor_normas.captura_navegador [--espera-minutos 5]
Requer o extra "navegador": pip install -e ".[navegador]"
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from monitor_normas.catalogo import carregar_catalogo
from monitor_normas.extracao_leis_org import ErroExtracao, processar

PASTA_SAIDA = Path("dados/brutos")
PERFIL = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "monitor-normas" / "perfil-chrome"
PORTA = 9222
FUSO = ZoneInfo("America/Sao_Paulo")
TITULO_VERIFICACAO = re.compile(r"um momento|just a moment|attention required", re.IGNORECASE)


class ErroNavegador(Exception):
    """Falha ao abrir o Chrome ou ao ler a página."""


def localizar_chrome() -> str:
    """Encontra o executável do Google Chrome."""
    chrome = shutil.which("chrome")
    if chrome:
        return chrome
    locais = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
        Path(os.environ.get("LOCALAPPDATA", "")),
    ]
    for base in locais:
        caminho = base / "Google" / "Chrome" / "Application" / "chrome.exe"
        if caminho.exists():
            return str(caminho)
    raise ErroNavegador("Chrome não encontrado.")


def abrir_chrome(url: str, perfil: Path = PERFIL, porta: int = PORTA) -> None:
    """Abre o Chrome normal, com perfil próprio e porta de depuração, na URL."""
    perfil.mkdir(parents=True, exist_ok=True)
    comando = [
        localizar_chrome(),
        f"--remote-debugging-port={porta}",
        f"--user-data-dir={perfil}",
        "--start-maximized",
        "--no-first-run",
        "--no-default-browser-check",
        url,
    ]
    flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    subprocess.Popen(comando, creationflags=flags)


def listar_abas(porta: int = PORTA) -> list[dict]:
    """Lista as abas abertas (título e URL), lidas da porta de depuração do Chrome."""
    with urllib.request.urlopen(f"http://localhost:{porta}/json", timeout=5) as r:
        return [a for a in json.load(r) if a.get("type") == "page"]


def aguardar_pagina(dominio: str, espera_minutos: float, porta: int = PORTA) -> dict:
    """Espera a aba cuja URL contém `dominio` carregar a página de fato (sem verificação)."""
    limite = time.monotonic() + espera_minutos * 60
    avisou = False
    while time.monotonic() < limite:
        try:
            abas = [a for a in listar_abas(porta) if dominio in a.get("url", "")]
        except OSError:
            abas = []
        for aba in abas:
            titulo = aba.get("title", "")
            if titulo and not TITULO_VERIFICACAO.search(titulo):
                return aba
            if TITULO_VERIFICACAO.search(titulo) and not avisou:
                print("Verificação na tela: conclua-a na janela do Chrome. Aguardando...")
                avisou = True
        time.sleep(2)
    raise ErroNavegador(f"a página de {dominio} não carregou em {espera_minutos:g} minuto(s)")


def fechar_aba(aba: dict, porta: int = PORTA) -> None:
    """Fecha a aba pela porta de depuração (para não confundir com a próxima)."""
    try:
        urllib.request.urlopen(f"http://localhost:{porta}/json/close/{aba['id']}", timeout=5)
    except OSError:
        pass


def ler_html(dominio: str, porta: int = PORTA) -> tuple[str, str]:
    """Conecta-se ao Chrome aberto e devolve (url, html) da aba do domínio."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        navegador = p.chromium.connect_over_cdp(f"http://localhost:{porta}")
        for contexto in navegador.contexts:
            for pagina in contexto.pages:
                if dominio in pagina.url:
                    pagina.wait_for_load_state("load")
                    return pagina.url, pagina.content()
    raise ErroNavegador(f"aba de {dominio} não encontrada")


def analisar_estrutura(html: str) -> dict:
    """Resume a estrutura da página para orientar a definição da extração."""
    sopa = BeautifulSoup(html, "html.parser")
    for lixo in sopa(["script", "style", "noscript"]):
        lixo.decompose()
    corpo = sopa.body or sopa
    texto = corpo.get_text("\n", strip=True)

    padrao_artigo = re.compile(r"^\s*Art\.\s*\d+", re.MULTILINE)
    candidatos = []
    for el in corpo.find_all(True):
        n = len(padrao_artigo.findall(el.get_text("\n", strip=True)))
        if n:
            candidatos.append((n, len(el.get_text()), el))
    total_artigos = max((n for n, _, _ in candidatos), default=0)
    # menor elemento que contém (quase) todos os artigos: provável contêiner da norma
    conteiner = min(
        (c for c in candidatos if c[0] >= total_artigos * 0.95),
        key=lambda c: c[1],
        default=None,
    )

    def descrever(el) -> dict:
        return {
            "tag": el.name,
            "id": el.get("id"),
            "classes": el.get("class", []),
            "filhos_diretos": Counter(f.name for f in el.find_all(True, recursive=False)),
        }

    classes = Counter(c for el in corpo.find_all(True) for c in el.get("class", []))
    ids = [el["id"] for el in corpo.find_all(True, id=True)]
    tachados = corpo.find_all(["s", "del", "strike"]) + [
        el for el in corpo.find_all(style=True) if "line-through" in el["style"].lower()
    ]

    linhas = texto.splitlines()
    return {
        "titulo": sopa.title.get_text(strip=True) if sopa.title else None,
        "artigos_encontrados": total_artigos,
        "conteiner_provavel": descrever(conteiner[2]) if conteiner else None,
        "ids": ids[:50],
        "classes_mais_frequentes": classes.most_common(30),
        "tachados": {
            "quantidade": len(tachados),
            "exemplos": [t.get_text(" ", strip=True)[:150] for t in tachados[:5]],
        },
        "notas": {
            termo: len(re.findall(termo, texto))
            for termo in ["Redação dada", "Revogad", "Incluíd", "Vide", "Vigência"]
        },
        "formatos_de_inciso": Counter(
            m.group(0) for m in re.finditer(r"^[IVXLCDM]+\s*[-–—]\s?", texto, re.MULTILINE)
        ).most_common(10),
        "formatos_de_paragrafo": Counter(
            m.group(0) for m in re.finditer(r"^(§\s*\d+º?|Parágrafo único)", texto, re.MULTILINE)
        ).most_common(5),
        "amostra_texto": "\n".join(linhas[:60]),
    }


def salvar(html: str, ident: str, pasta: Path, momento: datetime) -> tuple[Path, Path]:
    """Salva o HTML e o relatório de estrutura em <pasta>/<ident>/; devolve os dois caminhos."""
    sha256 = hashlib.sha256(html.encode("utf-8")).hexdigest()
    base = Path(pasta) / ident / f"{momento:%Y%m%dT%H%M%S}-{sha256[:12]}"
    base.parent.mkdir(parents=True, exist_ok=True)
    arquivo_html = base.with_suffix(".html")
    arquivo_html.write_text(html, encoding="utf-8")
    arquivo_estrutura = base.with_suffix(".estrutura.json")
    estrutura = analisar_estrutura(html)
    arquivo_estrutura.write_text(
        json.dumps(estrutura, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    return arquivo_html, arquivo_estrutura


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Captura pelo Chrome do computador local.")
    parser.add_argument("--saida", type=Path, default=PASTA_SAIDA, help="pasta de destino")
    parser.add_argument("--espera-minutos", type=float, default=5, help="tempo máximo de espera")
    args = parser.parse_args(argv)

    codigo = 0
    for norma in (n for n in carregar_catalogo() if n.ativa and n.fonte == "leis.org"):
        try:
            print(f"Abrindo o Chrome em {norma.id}...")
            abrir_chrome(norma.url)
            aba = aguardar_pagina("leis.org", args.espera_minutos)
            print(f"Página carregada: {aba.get('title')}")
            url, html = ler_html("leis.org")
            arquivo_html, arquivo_estrutura = salvar(html, norma.id, args.saida, datetime.now(FUSO))
            resultado = processar(arquivo_html, norma.id, norma.url)
        except (ErroNavegador, ErroExtracao) as erro:
            print(f"ERRO {norma.id}: {erro}")
            codigo = 1
            continue
        situacao = "conteúdo mudou" if resultado["mudou"] else "sem mudança no conteúdo"
        print(f"OK {norma.id} ({situacao})")
        print(f"  URL: {url}")
        print(f"  HTML: {arquivo_html}")
        print(f"  Estrutura da página: {arquivo_estrutura}")
        print(f"  Canônico: {resultado['canonico']}")
        print(f"  Markdown: {resultado['markdown']}")
        print("  Estatísticas: " + json.dumps(resultado["estatisticas"], ensure_ascii=False))
    return codigo


if __name__ == "__main__":
    sys.exit(main())
