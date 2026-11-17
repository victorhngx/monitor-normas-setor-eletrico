# monitor-normas-setor-eletrico

Monitoramento de normas do setor elétrico brasileiro. A ferramenta acompanha as normas nas fontes oficiais, avisa quando alguma é alterada, mostra o que mudou entre versões e converte o texto em Markdown estruturado, pronto para uso em sistemas de busca e IA (RAG).

Projeto em construção. O planejamento está em [`docs/`](docs/).

Resultados da REN 1.000/2021:

- texto canônico: [`dados/canonico/ren-1000-2021.json`](dados/canonico/ren-1000-2021.json)
- Markdown vigente: [`dados/markdown/ren-1000-2021/vigente.md`](dados/markdown/ren-1000-2021/vigente.md)

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

## Captura e extração (leis.org)

No computador local, com o Google Chrome instalado:

```powershell
.venv\Scripts\python -m pip install -e ".[navegador]"
.venv\Scripts\python -m monitor_normas.captura_navegador
```

Abre o Chrome normal (não controlado por automação), com um perfil próprio do projeto, na página de cada norma ativa do leis.org. Se o site pedir a verificação, conclua-a na janela; o script só acompanha o título da aba e, quando a norma carrega, lê a página. Em seguida salva o HTML em `dados/brutos/` (fora do Git) e roda a extração, que atualiza o canônico e o Markdown quando o conteúdo da norma muda.

A extração também pode ser rodada sozinha, sobre o HTML mais recente já capturado:

```powershell
.venv\Scripts\python -m monitor_normas.extracao_leis_org
```

O que a extração faz:

- separa a norma em dispositivos (artigo, parágrafo, inciso, alínea, item), com ids estáveis no estilo `art48-A_par2_inc3_alia` e a estrutura (título, capítulo, seção) de cada um;
- guarda o histórico de redações: texto riscado no site vira redação substituída; as notas "Redação dada", "Redação acrescida" e "Revogado" viram o ato alterador (tipo, número, ano, data e link) e as datas de vigência, marcadas como "conferir vigência";
- reconhece renumerações (parágrafo único que passou a § 1º), filhos suprimidos pela nova redação do dispositivo pai e revogações que valem para um grupo inteiro;
- separa o texto entre aspas que altera outras normas, a assinatura e as notas de publicação (fecho);
- usa a data do artigo de vigência ("Esta Resolução entra em vigor em ...") para a redação original;
- estrutura os anexos (cláusulas, itens, histórico de redações) e as tabelas, ligando cada linha ao dispositivo citado;
- gera o Markdown vigente: só a redação em vigor, revogados como marcador e nota de redação abaixo do dispositivo.

O que a extração não resolve sozinha vai para `dados/revisao/<norma>.md`, com o motivo e as redações de cada caso.

### Captura sem computador local (funcionalidade futura)

`monitor_normas.captura` e o workflow `Captura` acessam a fonte com identificação própria e enviam uma credencial de acesso (`LEIS_ORG_CABECALHO_ACESSO`, no formato `Nome-Do-Cabecalho: valor`) quando houver. Sem liberação do leis.org, a fonte responde com a verificação anti-robô e a captura termina com o código 2, sem tentar contornar. O workflow está só com execução manual até o acesso ser liberado.

## Como funciona

1. **Captura**: o conteúdo é baixado da fonte. PDFs e HTMLs originais não são guardados no repositório.
2. **Texto canônico**: cada norma é convertida em JSON, dispositivo por dispositivo (artigo, parágrafo, inciso, alínea), com o histórico de redações, as datas de vigência e o ato que fez cada alteração.
3. **Markdown**: gerado a partir do canônico. Na versão vigente, dispositivos revogados aparecem apenas como marcador, sem o texto antigo. Também está prevista uma versão histórica, com o texto válido em uma data escolhida.

As diferenças entre versões são calculadas sobre o texto canônico. Assim, uma mudança no formato do Markdown não é confundida com uma mudança na norma.

Uma página no GitHub Pages vai reunir as normas, os downloads e as últimas mudanças. A verificação diária automática no GitHub Actions depende da liberação de acesso pelo leis.org (ver [`docs/roadmap.md`](docs/roadmap.md)).

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
