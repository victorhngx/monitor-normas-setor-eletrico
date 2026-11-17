"""Captura das normas ativas do catálogo (Fase 2).

O acesso é sempre autorizado e identificado:
- toda requisição se identifica com o User-Agent do projeto;
- quando a fonte fornece uma credencial (por exemplo, um cabeçalho liberado
  no firewall do site ou uma chave de API), ela é lida de uma variável de
  ambiente e enviada como cabeçalho;
- se a fonte responder com bloqueio ou verificação anti-robô, a captura
  falha com AcessoBloqueado. Não há nenhuma tentativa de contornar a
  verificação.

O conteúdo baixado vai para dados/brutos/<id>/, pasta ignorada pelo Git (D004).

Uso: python -m monitor_normas.captura [--saida PASTA]
Códigos de saída: 0 sucesso, 1 erro, 2 acesso bloqueado pela fonte.
"""

import argparse
import hashlib
import os
import re
import sys
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from monitor_normas import __version__
from monitor_normas.catalogo import Norma, carregar_catalogo

USER_AGENT = f"monitor-normas-setor-eletrico/{__version__}"
PASTA_SAIDA = Path("dados/brutos")
TEMPO_LIMITE = 60

# fonte -> variável de ambiente com a credencial, no formato "Nome-Do-Cabecalho: valor"
VARIAVEL_CREDENCIAL = {
    "leis.org": "LEIS_ORG_CABECALHO_ACESSO",
    "aneel-git": "ANEEL_GIT_CABECALHO_ACESSO",
}

STATUS_BLOQUEIO = {401, 403, 429}
TITULO_DESAFIO = re.compile(
    rb"<title>\s*(Just a moment|Um momento|Attention Required)", re.IGNORECASE
)

SAIDA_OK, SAIDA_ERRO, SAIDA_BLOQUEIO = 0, 1, 2


class ErroCaptura(Exception):
    """Falha na captura de uma norma."""


class AcessoBloqueado(ErroCaptura):
    """A fonte recusou o acesso automatizado."""


@dataclass(frozen=True)
class Resposta:
    status: int
    corpo: bytes
    cabecalhos: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Captura:
    norma_id: str
    url: str
    momento: datetime
    sha256: str
    tamanho: int
    arquivo: Path


def abrir_url(url: str, cabecalhos: Mapping[str, str]) -> Resposta:
    """Faz o GET e devolve status, corpo e cabeçalhos, inclusive em respostas de erro."""
    requisicao = urllib.request.Request(url, headers=dict(cabecalhos))
    try:
        with urllib.request.urlopen(requisicao, timeout=TEMPO_LIMITE) as r:
            return Resposta(r.status, r.read(), {k.lower(): v for k, v in r.headers.items()})
    except urllib.error.HTTPError as erro:
        cabecalhos_erro = {k.lower(): v for k, v in erro.headers.items()}
        return Resposta(erro.code, erro.read(), cabecalhos_erro)
    except urllib.error.URLError as erro:
        raise ErroCaptura(f"não foi possível acessar {url}: {erro.reason}") from erro


def cabecalho_credencial(fonte: str, ambiente: Mapping[str, str]) -> dict[str, str]:
    """Lê a credencial da fonte, se configurada, e devolve o cabeçalho correspondente."""
    variavel = VARIAVEL_CREDENCIAL.get(fonte)
    valor = ambiente.get(variavel, "").strip() if variavel else ""
    if not valor:
        return {}
    nome, separador, conteudo = valor.partition(":")
    if not separador or not nome.strip() or not conteudo.strip():
        raise ErroCaptura(f"{variavel} deve ter o formato 'Nome-Do-Cabecalho: valor'")
    return {nome.strip(): conteudo.strip()}


def _bloqueado(resposta: Resposta) -> bool:
    if resposta.status in STATUS_BLOQUEIO:
        return True
    if resposta.cabecalhos.get("cf-mitigated", "").lower() == "challenge":
        return True
    return bool(TITULO_DESAFIO.search(resposta.corpo[:20000]))


def capturar(
    norma: Norma,
    pasta: Path = PASTA_SAIDA,
    abrir: Callable[[str, Mapping[str, str]], Resposta] = abrir_url,
    ambiente: Mapping[str, str] = os.environ,
    agora: datetime | None = None,
) -> Captura:
    """Baixa uma norma, calcula o SHA-256 e salva o conteúdo em pasta/<id>/."""
    cabecalhos = {"User-Agent": USER_AGENT, **cabecalho_credencial(norma.fonte, ambiente)}
    resposta = abrir(norma.url, cabecalhos)

    if _bloqueado(resposta):
        raise AcessoBloqueado(
            f"{norma.id}: a fonte recusou o acesso automatizado (HTTP {resposta.status}). "
            f"É preciso acesso autorizado; configure {VARIAVEL_CREDENCIAL.get(norma.fonte)} "
            "com a credencial fornecida pela fonte."
        )
    if resposta.status != 200:
        raise ErroCaptura(f"{norma.id}: resposta inesperada (HTTP {resposta.status})")
    if not resposta.corpo:
        raise ErroCaptura(f"{norma.id}: resposta vazia")

    sha256 = hashlib.sha256(resposta.corpo).hexdigest()
    momento = agora or datetime.now(UTC)
    arquivo = Path(pasta) / norma.id / f"{momento:%Y%m%dT%H%M%SZ}-{sha256[:12]}.{norma.formato}"
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_bytes(resposta.corpo)

    return Captura(norma.id, norma.url, momento, sha256, len(resposta.corpo), arquivo)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Captura as normas ativas do catálogo.")
    parser.add_argument("--saida", type=Path, default=PASTA_SAIDA, help="pasta de destino")
    args = parser.parse_args(argv)

    codigo = SAIDA_OK
    for norma in (n for n in carregar_catalogo() if n.ativa):
        try:
            captura = capturar(norma, args.saida)
        except AcessoBloqueado as erro:
            print(f"BLOQUEADO {erro}")
            codigo = max(codigo, SAIDA_BLOQUEIO)
        except ErroCaptura as erro:
            print(f"ERRO {erro}")
            codigo = max(codigo, SAIDA_ERRO)
        else:
            print(
                f"OK {captura.norma_id} sha256={captura.sha256} "
                f"tamanho={captura.tamanho} arquivo={captura.arquivo}"
            )
    return codigo


if __name__ == "__main__":
    sys.exit(main())
