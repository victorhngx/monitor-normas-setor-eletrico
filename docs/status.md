# Status atual

**Atualizado em:** 16/11/2026

> Atualizar este arquivo ao fim de cada issue/sessão de trabalho.

## Onde estamos
Fase 0 (Fundação), em andamento.
- Repositório criado com `.gitignore` e a documentação de planejamento em `docs/`.
- Issue #1 "Escrever o README": apresentação do projeto, fontes e funcionamento.
- Issue #3 "Base Python com testes e estilo": `pyproject.toml`, pacote `monitor_normas` em `src/`, pytest e ruff (D012).
- Issue #5 "Trava de privacidade": verificador `monitor_normas.trava_privacidade` que bloqueia documentos brutos, `dados/brutos/` e arquivos de segredo (D013).

## Próximo passo
Restante da Fase 0, nesta ordem: checagem automática nos PRs (GitHub Actions, com testes, ruff, trava de privacidade e gitleaks); proteção do main e merge automático.

## Pendências / em aberto
- Aprovar padrão de identificadores de dispositivos (proposta: estilo LexML — ver `padrao-markdown-rag.md`).
- Confirmar como o leis.org apresenta textos alterados/revogados (tachado + notas?) → define a reconstrução do histórico.
- Confirmar formato dos arquivos do PRODIST/PRORET no git da ANEEL (pasta procreg).
