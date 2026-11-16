# Registro de decisões

Formato: ID | data | decisão | motivo. Decisões não são apagadas; se mudarem, marcar "substituída por Dxxx" e criar nova linha.

| ID | Data | Decisão | Motivo |
|---|---|---|---|
| D001 | 16/11/2026 | Repositório no GitHub, conta pessoal, **público**, nome `monitor-normas-setor-eletrico` | Na conta gratuita, só repo público tem GitHub Pages e proteção do main (necessária ao merge automático). Conteúdo são normas públicas. |
| D002 | 16/11/2026 | Execução na nuvem via GitHub Actions; página via GitHub Pages | Gratuito em repo público. |
| D003 | 16/11/2026 | Fontes: leis.org/aneel para normas ANEEL; git.aneel.gov.br/publico/centralconteudo (procreg) para PRODIST e PRORET. DOU não será usado. | Definição do mantenedor. |
| D004 | 16/11/2026 | Arquitetura em camadas: captura → texto canônico (JSON) → Markdown. PDF/HTML brutos não entram no repo; canônico e Markdown são versionados. | Mudança de padrão do Markdown não exige recaptura nem gera falso "diff de norma". |
| D005 | 16/11/2026 | Diff da norma é calculado sobre o texto canônico, não sobre o Markdown. | Separar mudança de norma de mudança de formato. |
| D006 | 16/11/2026 | Canônico guarda, por dispositivo, as redações com início/fim de vigência e ato alterador. Datas derivadas de publicação ficam marcadas "conferir vigência". | Permitir RAG temporal (pareceres sobre situações passadas). |
| D007 | 16/11/2026 | Markdown vigente: dispositivo revogado vira marcador "(Revogado pela …)", sem texto antigo; notas "Redação dada por …" mantidas. Markdown histórico/"em data X" com metadados de vigência por trecho. | Evitar que a RAG recupere texto que não vale mais, sem perder o histórico. |
| D008 | 16/11/2026 | Monitoramento diário (dias úteis, 7h), aviso por issue automática no GitHub. Frequência ajustável. | Custo zero; e-mail do GitHub avisa sem serviço extra. |
| D009 | 16/11/2026 | Markdown registra a versão do padrão no cabeçalho (`padrao: x.y`). Mudança de padrão = PR próprio regenerando tudo. | Rastreabilidade. |
| D010 | 16/11/2026 | Desenvolvimento no computador local, com git e gh pelo terminal. | Usa o Git/gh já instalados e logados. |
| D011 | 16/11/2026 | Documentação de planejamento (status, roadmap, decisões, catálogo, padrão) vive em `docs/` no repositório, como fonte única. | Evitar duas versões desencontradas; histórico no Git. |
| D012 | 16/11/2026 | Base Python: versão mínima 3.12; pacote `monitor_normas` em `src/`; configuração no `pyproject.toml`; testes com pytest; estilo com ruff (versão fixa). Ambiente local em `.venv`. | Estrutura padrão e simples; versão fixa do ruff evita que regras novas quebrem a checagem sem aviso. |
| D013 | 16/11/2026 | Trava de privacidade em Python (`monitor_normas.trava_privacidade`), sobre os arquivos do Git: bloqueia PDF, DOC/DOCX, HTML/HTM fora de `site/`, tudo em `dados/brutos/` e arquivos `.env`, `.key`, `.pem`. Busca de segredos no texto (gitleaks) roda só no GitHub Actions. | Reforça o `.gitignore` contra `git add -f` e descuidos; gitleaks no Actions dispensa instalação no Windows. |
| D014 | 16/11/2026 | Workflow `Verificações` no GitHub Actions (Python 3.12) em cada PR e push no main: pytest, ruff, trava de privacidade e gitleaks. Main protegido: só por PR, com os jobs `verificacoes` e `gitleaks` obrigatórios, sem exigir revisão humana. Merge automático ativado; branch apagado após o merge. | Merge sem intervenção manual, garantido pelas checagens; revisão obrigatória impediria o dono de mergear o próprio PR. |
