"""Correções manuais de falhas do texto no site, uma lista por norma (D019).

Arquivo: correcoes/<id da norma>.toml, versionado e aplicado em toda extração.

Exemplo:

    [[correcao]]
    tipo = "quebra"
    antes_de = "§ 2º Durante a realização da busca"
    motivo = "No site, o § 2º do art. 666 vem colado ao fim do inciso II do § 1º."

Tipos:
- quebra: começa um novo dispositivo no ponto em que aparece o texto `antes_de`
  (para quando falta a quebra de linha no site). O texto deve aparecer uma vez só
  no meio de um bloco; se não aparecer, a extração avisa no relatório de revisão.
"""

import tomllib
from pathlib import Path

PASTA_CORRECOES = Path("correcoes")
TIPOS = {"quebra"}
CAMPOS = {"tipo", "antes_de", "motivo"}


class ErroCorrecoes(Exception):
    """Arquivo de correções com formato inválido."""


def carregar_correcoes(norma_id: str, pasta: Path = PASTA_CORRECOES) -> list[dict]:
    """Lê as correções da norma; sem arquivo, não há correções."""
    arquivo = Path(pasta) / f"{norma_id}.toml"
    if not arquivo.exists():
        return []
    try:
        dados = tomllib.loads(arquivo.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as erro:
        raise ErroCorrecoes(f"{arquivo}: TOML inválido ({erro})") from erro

    desconhecidas = set(dados) - {"correcao"}
    if desconhecidas:
        raise ErroCorrecoes(f"{arquivo}: chaves desconhecidas {sorted(desconhecidas)}")

    correcoes = []
    for numero, item in enumerate(dados.get("correcao", []), start=1):
        local = f"{arquivo}, correção {numero}"
        if set(item) != CAMPOS:
            faltam, sobram = CAMPOS - set(item), set(item) - CAMPOS
            raise ErroCorrecoes(f"{local}: faltam {sorted(faltam)}, sobram {sorted(sobram)}")
        if item["tipo"] not in TIPOS:
            raise ErroCorrecoes(f"{local}: tipo deve ser um de {sorted(TIPOS)}")
        for campo in ("antes_de", "motivo"):
            if not isinstance(item[campo], str) or not item[campo].strip():
                raise ErroCorrecoes(f"{local}: {campo} deve ser um texto não vazio")
        correcoes.append(dict(item))
    return correcoes
