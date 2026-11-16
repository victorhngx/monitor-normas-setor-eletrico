import pytest

from monitor_normas.trava_privacidade import (
    arquivos_do_repositorio,
    encontrar_problemas,
    motivo_bloqueio,
)


@pytest.mark.parametrize(
    "caminho",
    [
        "README.md",
        "docs/status.md",
        "src/monitor_normas/__init__.py",
        "dados/canonico/ren-1000.json",
        "dados/markdown/ren-1000/vigente.md",
        "site/index.html",
        "site/normas/ren-1000.htm",
        "pyproject.toml",
        ".gitignore",
    ],
)
def test_arquivos_permitidos(caminho):
    assert motivo_bloqueio(caminho) is None


@pytest.mark.parametrize(
    "caminho",
    [
        "norma.pdf",
        "docs/anexo.PDF",
        "dados/ren-1000.docx",
        "modelo.doc",
        "pagina.html",
        "docs/copia.htm",
        "dados/site/index.html",
        "dados/brutos/ren-1000.json",
        "dados/brutos/qualquer.txt",
        ".env",
        "config/producao.env",
        "chave.key",
        "certificados/servidor.pem",
    ],
)
def test_arquivos_proibidos(caminho):
    assert motivo_bloqueio(caminho) is not None


def test_encontrar_problemas_lista_so_os_proibidos():
    problemas = encontrar_problemas(["README.md", "norma.pdf", "site/index.html", ".env"])
    assert [caminho for caminho, _ in problemas] == ["norma.pdf", ".env"]


def test_repositorio_atual_esta_limpo():
    arquivos = arquivos_do_repositorio()
    assert arquivos, "o Git deveria listar ao menos um arquivo"
    assert encontrar_problemas(arquivos) == []
