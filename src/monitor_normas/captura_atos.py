"""Captura dos atos que alteram uma norma, pelo Chrome do computador local.

A lista vem do canônico da norma (`atos_vinculados`, o quadro "Atos que alteram,
regulamentam ou revogam" do leis.org). São capturados os atos posteriores à norma
(resoluções e despachos) que ainda não têm captura salva. O processo é o mesmo da
captura da norma (monitor_normas.captura_navegador): Chrome normal, verificação do
site feita pela pessoa quando aparecer, leitura da página pela porta de depuração.
Cada ato abre numa aba própria, fechada depois da leitura, com uma pausa entre um
ato e outro.

Salva em dados/brutos/atos/<ato>/ (fora do Git), por exemplo
dados/brutos/atos/ren-1148-2026/<momento>-<hash>.html.

Uso:
  python -m monitor_normas.captura_atos                     (atos pendentes)
  python -m monitor_normas.captura_atos --ato ren-1148-2026 (um ato, mesmo já capturado)
  python -m monitor_normas.captura_atos --listar            (só lista, sem abrir o Chrome)
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from monitor_normas.captura_navegador import (
    FUSO,
    ErroNavegador,
    abrir_chrome,
    aguardar_pagina,
    fechar_aba,
    ler_html,
    salvar,
)

PASTA_CANONICO = Path("dados/canonico")
PASTA_ATOS = Path("dados/brutos/atos")
ESPERA_TEXTO_SEGUNDOS = 60
RE_URL_ATO = re.compile(r"leis\.org/.*?/lei/([a-z-]+)/(\d{4})/(\d+)/")


class ErroAtos(Exception):
    """Lista de atos indisponível ou ato não encontrado."""


def atos_da_norma(canonico: dict) -> list[dict]:
    """Atos posteriores à norma, com id (ex.: ren-1148-2026), tipo, número, ano, data e url."""
    data_norma = canonico.get("data") or ""
    atos = []
    for ato in canonico.get("atos_vinculados", []):
        m = RE_URL_ATO.search(ato.get("url") or "")
        if not m or (ato.get("data") or "") < data_norma:
            continue
        tipo = (ato.get("tipo") or m.group(1)).lower()
        atos.append(
            {
                "id": f"{tipo}-{m.group(3)}-{m.group(2)}",
                "tipo": ato.get("tipo"),
                "numero": m.group(3),
                "ano": m.group(2),
                "data": ato.get("data"),
                "descricao": ato.get("descricao"),
                "url": ato["url"],
                "trecho_url": f"/{m.group(2)}/{m.group(3)}/",
            }
        )
    return sorted(atos, key=lambda a: (a["data"] or "", a["numero"]))


def capturado(ato: dict, pasta: Path = PASTA_ATOS) -> bool:
    return any((Path(pasta) / ato["id"]).glob("*.html"))


def validar_pagina(html: str) -> None:
    """Confere se a página lida é a de uma norma (e não a verificação ou um erro)."""
    if "aneel-content" not in html:
        raise ErroNavegador("a página lida não tem o texto da norma (div.aneel-content)")


def aguardar_texto(trecho_url: str, segundos: float) -> str:
    """Lê a aba até o texto da norma aparecer (a página pode carregar depois do título)."""
    limite = time.monotonic() + segundos
    while True:
        _, html = ler_html(trecho_url)
        try:
            validar_pagina(html)
            return html
        except ErroNavegador:
            if time.monotonic() >= limite:
                raise
        time.sleep(3)


def capturar(ato: dict, pasta: Path, espera_minutos: float) -> Path:
    print(f"Abrindo o Chrome em {ato['id']}...")
    abrir_chrome(ato["url"])
    aba = aguardar_pagina(ato["trecho_url"], espera_minutos)
    try:
        html = aguardar_texto(ato["trecho_url"], ESPERA_TEXTO_SEGUNDOS)
        titulo = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
        print(f"Página carregada: {titulo.group(1).strip() if titulo else '?'}")
        arquivo_html, _ = salvar(html, ato["id"], pasta, datetime.now(FUSO))
    finally:
        fechar_aba(aba)
    return arquivo_html


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Captura dos atos que alteram uma norma.")
    parser.add_argument("--norma", default="ren-1000-2021", help="id da norma no catálogo")
    parser.add_argument("--ato", action="append", help="id do ato (ex.: ren-1148-2026)")
    parser.add_argument("--listar", action="store_true", help="só lista os atos")
    parser.add_argument("--saida", type=Path, default=PASTA_ATOS, help="pasta de destino")
    parser.add_argument("--espera-minutos", type=float, default=5, help="espera por ato")
    parser.add_argument("--pausa-segundos", type=float, default=10, help="pausa entre atos")
    args = parser.parse_args(argv)

    arquivo = PASTA_CANONICO / f"{args.norma}.json"
    if not arquivo.exists():
        print(f"ERRO canônico não encontrado: {arquivo} (capture a norma primeiro)")
        return 1
    atos = atos_da_norma(json.loads(arquivo.read_text(encoding="utf-8")))

    if args.listar:
        for ato in atos:
            situacao = "capturado" if capturado(ato, args.saida) else "pendente"
            print(f"{ato['id']:<16} {ato['data']}  {situacao}")
        return 0

    if args.ato:
        por_id = {a["id"]: a for a in atos}
        faltando = [i for i in args.ato if i not in por_id]
        if faltando:
            print(f"ERRO ato não listado em {args.norma}: {', '.join(faltando)}")
            return 1
        fila = [por_id[i] for i in args.ato]
    else:
        fila = [a for a in atos if not capturado(a, args.saida)]
    if not fila:
        print("Nenhum ato pendente.")
        return 0

    codigo = 0
    for n, ato in enumerate(fila):
        if n:
            time.sleep(args.pausa_segundos)
        try:
            arquivo_html = capturar(ato, args.saida, args.espera_minutos)
        except ErroNavegador as erro:
            print(f"ERRO {ato['id']}: {erro}")
            codigo = 1
            continue
        print(f"OK {ato['id']}: {arquivo_html}")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
