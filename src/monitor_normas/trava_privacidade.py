"""Trava de privacidade: impede que arquivos proibidos entrem no repositório.

Regras (ver D004 em docs/decisoes.md):
- documentos brutos (PDF, DOC/DOCX, HTML/HTM) não entram; HTML só é aceito em site/;
- nada em dados/brutos/;
- arquivos de segredo (.env, *.env, *.key, *.pem) não entram.

Uso: python -m monitor_normas.trava_privacidade
"""

import subprocess
import sys
from pathlib import PurePosixPath

EXTENSOES_BRUTAS = {".pdf", ".doc", ".docx"}
EXTENSOES_HTML = {".html", ".htm"}
EXTENSOES_SEGREDO = {".env", ".key", ".pem"}
PASTA_BRUTOS = ("dados", "brutos")
PASTA_SITE = "site"


def motivo_bloqueio(caminho: str) -> str | None:
    """Devolve o motivo pelo qual o arquivo é proibido, ou None se ele é permitido.

    `caminho` usa barras normais (/), como o Git informa.
    """
    p = PurePosixPath(caminho)
    nome = p.name.lower()
    extensao = p.suffix.lower()

    if p.parts[:2] == PASTA_BRUTOS:
        return "arquivo em dados/brutos/ (dados brutos não entram no repositório)"
    if extensao in EXTENSOES_BRUTAS:
        return f"documento bruto ({extensao})"
    if extensao in EXTENSOES_HTML and p.parts[0] != PASTA_SITE:
        return "HTML fora de site/"
    if nome == ".env" or extensao in EXTENSOES_SEGREDO:
        return "possível arquivo de segredo"
    return None


def encontrar_problemas(caminhos: list[str]) -> list[tuple[str, str]]:
    """Lista (caminho, motivo) de cada arquivo proibido."""
    problemas = []
    for caminho in caminhos:
        motivo = motivo_bloqueio(caminho)
        if motivo:
            problemas.append((caminho, motivo))
    return problemas


def arquivos_do_repositorio() -> list[str]:
    """Arquivos controlados pelo Git, incluindo os já preparados para commit."""
    saida = subprocess.run(
        ["git", "ls-files", "-z"],
        capture_output=True,
        check=True,
    ).stdout
    return [c for c in saida.decode("utf-8").split("\0") if c]


def main() -> int:
    problemas = encontrar_problemas(arquivos_do_repositorio())
    if not problemas:
        print("Trava de privacidade: nenhum arquivo proibido.")
        return 0
    print("Trava de privacidade: arquivos proibidos encontrados:")
    for caminho, motivo in problemas:
        print(f"  {caminho}: {motivo}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
