# Status atual

**Atualizado em:** 16/11/2026

> Atualizar este arquivo ao fim de cada issue/sessão de trabalho.

## Onde estamos
Fase 0 (Fundação) concluída.
- Repositório criado com `.gitignore` e a documentação de planejamento em `docs/`.
- Issue #1 "Escrever o README": apresentação do projeto, fontes e funcionamento.
- Issue #3 "Base Python com testes e estilo": `pyproject.toml`, pacote `monitor_normas` em `src/`, pytest e ruff (D012).
- Issue #5 "Trava de privacidade": verificador `monitor_normas.trava_privacidade` que bloqueia documentos brutos, `dados/brutos/` e arquivos de segredo (D013).
- Issue #7 "Checagem automática nos PRs e proteção do main": workflow `Verificações` (pytest, ruff, trava, gitleaks), main protegido e merge automático (D014).

## Próximo passo
Fase 1 (Catálogo): criar o `catalogo.yaml` com a REN 1.000 como primeira norma, com testes que validem o formato.

## Pendências / em aberto
- Aprovar padrão de identificadores de dispositivos (proposta: estilo LexML — ver `padrao-markdown-rag.md`).
- Confirmar como o leis.org apresenta textos alterados/revogados (tachado + notas?) → define a reconstrução do histórico.
- Confirmar formato dos arquivos do PRODIST/PRORET no git da ANEEL (pasta procreg).
