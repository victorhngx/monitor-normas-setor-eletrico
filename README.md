# monitor-normas-setor-eletrico

Monitoramento de normas do setor elétrico brasileiro. A ferramenta acompanha as normas nas fontes oficiais, avisa quando alguma é alterada, mostra o que mudou entre versões e converte o texto em Markdown estruturado, pronto para uso em sistemas de busca e IA (RAG).

Projeto em construção: ainda não há código. O planejamento está em [`docs/`](docs/).

## Normas e fontes

| Norma | Fonte |
|---|---|
| REN 1.000/2021 (piloto) | [leis.org/aneel](https://leis.org/aneel) |
| PRODIST | [git.aneel.gov.br/publico/centralconteudo](https://git.aneel.gov.br/publico/centralconteudo/-/tree/main/procreg) (pasta procreg) |
| PRORET | idem |

As normas monitoradas ficam em [`catalogo.toml`](catalogo.toml). Para validar o catálogo e listar os links das normas ativas:

```powershell
.venv\Scripts\python -m monitor_normas.catalogo
```

O planejamento das próximas normas está em [`docs/catalogo-normas.md`](docs/catalogo-normas.md).

## Captura

```powershell
.venv\Scripts\python -m monitor_normas.captura
```

Baixa as normas ativas do catálogo para `dados/brutos/` (fora do Git) e calcula o SHA-256 de cada uma. O acesso é sempre identificado (User-Agent do projeto) e, quando a fonte fornece uma credencial de acesso, ela é enviada como cabeçalho, lida da variável `LEIS_ORG_CABECALHO_ACESSO` no formato `Nome-Do-Cabecalho: valor`. Se a fonte responder com bloqueio ou verificação anti-robô, a captura termina com o código 2, sem tentar contornar.

No GitHub Actions, o workflow `Captura` roda em dias úteis às 7h (e manualmente), desde que o secret `LEIS_ORG_CABECALHO_ACESSO` esteja configurado. O conteúdo baixado fica disponível por 7 dias como artefato da execução, sem entrar no repositório.

## Como funciona

1. **Captura**: o conteúdo é baixado da fonte. PDFs e HTMLs originais não são guardados no repositório.
2. **Texto canônico**: cada norma é convertida em JSON, dispositivo por dispositivo (artigo, parágrafo, inciso, alínea), com o histórico de redações, as datas de vigência e o ato que fez cada alteração.
3. **Markdown**: gerado a partir do canônico. Na versão vigente, dispositivos revogados aparecem apenas como marcador, sem o texto antigo. Também está prevista uma versão histórica, com o texto válido em uma data escolhida.

As diferenças entre versões são calculadas sobre o texto canônico. Assim, uma mudança no formato do Markdown não é confundida com uma mudança na norma.

Uma rotina diária no GitHub Actions vai verificar as fontes e abrir uma issue quando houver alteração. Uma página no GitHub Pages vai reunir as normas, os downloads e as últimas mudanças.

## Desenvolvimento

Requer Python 3.12 ou mais recente. No Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
```

Verificações (as mesmas que o GitHub Actions roda em cada pull request, junto com o gitleaks):

```powershell
.venv\Scripts\python -m pytest            # testes
.venv\Scripts\python -m ruff check .      # erros e estilo
.venv\Scripts\python -m ruff format --check .   # formatação
.venv\Scripts\python -m monitor_normas.trava_privacidade   # arquivos proibidos
```

A trava de privacidade recusa documentos brutos (PDF, DOC/DOCX, HTML fora de `site/`), qualquer arquivo em `dados/brutos/` e arquivos de segredo (`.env`, `.key`, `.pem`).

## Documentação

- [`docs/status.md`](docs/status.md): onde o projeto está e próximos passos
- [`docs/roadmap.md`](docs/roadmap.md): fases planejadas
- [`docs/decisoes.md`](docs/decisoes.md): registro de decisões
- [`docs/padrao-markdown-rag.md`](docs/padrao-markdown-rag.md): padrão do Markdown gerado
- [`docs/guia-git.md`](docs/guia-git.md): glossário de Git e GitHub
