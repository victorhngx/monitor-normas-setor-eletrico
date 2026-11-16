"""Catálogo de normas monitoradas (catalogo.toml, na raiz do repositório).

Uso: python -m monitor_normas.catalogo
Valida o catálogo e lista os links das normas ativas.
"""

import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

CAMINHO_PADRAO = Path(__file__).resolve().parents[2] / "catalogo.toml"

# fonte -> endereço (host) que os links dessa fonte devem ter
FONTES = {
    "leis.org": "leis.org",
    "aneel-git": "git.aneel.gov.br",
}
FORMATOS = {"html", "pdf"}
CAMPOS = ("id", "titulo", "fonte", "url", "formato", "ativa")
PADRAO_ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class ErroCatalogo(Exception):
    """O catálogo não pôde ser lido ou tem formato inválido."""


@dataclass(frozen=True)
class Norma:
    id: str
    titulo: str
    fonte: str
    url: str
    formato: str
    ativa: bool


def _erros_da_norma(item: dict, rotulo: str) -> list[str]:
    erros = []

    faltando = [c for c in CAMPOS if c not in item]
    desconhecidos = sorted(set(item) - set(CAMPOS))
    if faltando:
        erros.append(f"{rotulo}: campos faltando: {', '.join(faltando)}")
    if desconhecidos:
        erros.append(f"{rotulo}: campos desconhecidos: {', '.join(desconhecidos)}")
    if faltando:
        return erros

    if not isinstance(item["id"], str) or not PADRAO_ID.match(item["id"]):
        erros.append(f"{rotulo}: id deve ter só letras minúsculas, números e hífens")
    if not isinstance(item["titulo"], str) or not item["titulo"].strip():
        erros.append(f"{rotulo}: titulo não pode ficar vazio")
    if item["fonte"] not in FONTES:
        erros.append(f"{rotulo}: fonte deve ser uma de: {', '.join(FONTES)}")
    if item["formato"] not in FORMATOS:
        erros.append(f"{rotulo}: formato deve ser um de: {', '.join(sorted(FORMATOS))}")
    if not isinstance(item["ativa"], bool):
        erros.append(f"{rotulo}: ativa deve ser true ou false")

    url = item["url"]
    if not isinstance(url, str):
        erros.append(f"{rotulo}: url deve ser um texto")
    else:
        partes = urlparse(url)
        if partes.scheme != "https":
            erros.append(f"{rotulo}: url deve começar com https://")
        host_esperado = FONTES.get(item["fonte"])
        if host_esperado and partes.hostname != host_esperado:
            erros.append(f"{rotulo}: url deve ser do endereço {host_esperado}")

    return erros


def validar(dados) -> list[Norma]:
    """Valida o conteúdo já lido do TOML e devolve a lista de normas."""
    if not isinstance(dados, dict) or set(dados) != {"normas"}:
        raise ErroCatalogo("o catálogo deve ter apenas a chave 'normas'")
    if not isinstance(dados["normas"], list) or not dados["normas"]:
        raise ErroCatalogo("'normas' deve ser uma lista com ao menos uma norma")

    erros = []
    normas = []
    ids_vistos = set()
    for posicao, item in enumerate(dados["normas"], start=1):
        rotulo = f"norma {posicao}"
        if not isinstance(item, dict):
            erros.append(f"{rotulo}: deve ser um conjunto de campos")
            continue
        if isinstance(item.get("id"), str):
            rotulo = f"norma {posicao} ({item['id']})"

        erros_item = _erros_da_norma(item, rotulo)
        if item.get("id") in ids_vistos:
            erros_item.append(f"{rotulo}: id repetido")
        ids_vistos.add(item.get("id"))

        if erros_item:
            erros.extend(erros_item)
        else:
            normas.append(Norma(**item))

    if erros:
        raise ErroCatalogo("\n".join(erros))
    return normas


def carregar_catalogo(caminho: Path = CAMINHO_PADRAO) -> list[Norma]:
    """Lê e valida o catálogo."""
    try:
        dados = tomllib.loads(Path(caminho).read_text(encoding="utf-8"))
    except FileNotFoundError as erro:
        raise ErroCatalogo(f"catálogo não encontrado: {caminho}") from erro
    except tomllib.TOMLDecodeError as erro:
        raise ErroCatalogo(f"TOML inválido: {erro}") from erro
    return validar(dados)


def main(caminho: Path = CAMINHO_PADRAO) -> int:
    try:
        normas = carregar_catalogo(caminho)
    except ErroCatalogo as erro:
        print("Catálogo inválido:")
        for linha in str(erro).splitlines():
            print(f"  {linha}")
        return 1

    ativas = [n for n in normas if n.ativa]
    print(f"Catálogo válido: {len(normas)} norma(s), {len(ativas)} ativa(s).")
    for norma in ativas:
        print(f"  {norma.id} [{norma.formato}] {norma.url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
