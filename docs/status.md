# Status atual

**Atualizado em:** 16/11/2026

> Atualizar este arquivo ao fim de cada issue/sessão de trabalho.

## Onde estamos
Fases 0 (Fundação) e 1 (Catálogo) concluídas.
- Repositório criado com `.gitignore` e a documentação de planejamento em `docs/`.
- Issue #1 "Escrever o README": apresentação do projeto, fontes e funcionamento.
- Issue #3 "Base Python com testes e estilo": `pyproject.toml`, pacote `monitor_normas` em `src/`, pytest e ruff (D012).
- Issue #5 "Trava de privacidade": verificador `monitor_normas.trava_privacidade` que bloqueia documentos brutos, `dados/brutos/` e arquivos de segredo (D013).
- Issue #7 "Checagem automática nos PRs e proteção do main": workflow `Verificações` (pytest, ruff, trava, gitleaks), main protegido e merge automático (D014).
- Issue #9 "Catálogo de normas": `catalogo.toml` com a REN 1.000 e leitor com validação `monitor_normas.catalogo` (D015).

## Próximo passo
Fase 2 (Captura): baixar a REN 1.000 do leis.org e calcular a impressão digital (hash) para detectar mudanças. Antes, investigar como o leis.org apresenta textos alterados e revogados (ver pendências).

## Pendências / em aberto
- Aprovar padrão de identificadores de dispositivos (proposta: estilo LexML — ver `padrao-markdown-rag.md`).
- Confirmar como o leis.org apresenta textos alterados/revogados (tachado + notas?) → define a reconstrução do histórico.
- Confirmar formato dos arquivos do PRODIST/PRORET no git da ANEEL (pasta procreg).
