# Status atual

**Atualizado em:** 16/11/2026

> Atualizar este arquivo ao fim de cada issue/sessão de trabalho.

## Onde estamos
Fases 0 (Fundação) e 1 (Catálogo) concluídas; Fase 2 (Captura) com o código pronto, aguardando acesso autorizado ao leis.org.
- Repositório criado com `.gitignore` e a documentação de planejamento em `docs/`.
- Issue #1 "Escrever o README": apresentação do projeto, fontes e funcionamento.
- Issue #3 "Base Python com testes e estilo": `pyproject.toml`, pacote `monitor_normas` em `src/`, pytest e ruff (D012).
- Issue #5 "Trava de privacidade": verificador `monitor_normas.trava_privacidade` que bloqueia documentos brutos, `dados/brutos/` e arquivos de segredo (D013).
- Issue #7 "Checagem automática nos PRs e proteção do main": workflow `Verificações` (pytest, ruff, trava, gitleaks), main protegido e merge automático (D014).
- Issue #9 "Catálogo de normas": `catalogo.toml` com a REN 1.000 e leitor com validação `monitor_normas.catalogo` (D015).
- Issue #11 "Captura automática com acesso autorizado": módulo `monitor_normas.captura` e workflow `Captura`, que roda em dias úteis assim que a credencial do leis.org for configurada (D016).

## Próximo passo
- Obter acesso autorizado do leis.org (API, chave ou liberação do robô do projeto) e configurar o secret `LEIS_ORG_CABECALHO_ACESSO`.
- Integrar o script de extração, limpeza e estruturação existente como etapa seguinte à captura.

## Pendências / em aberto
- leis.org e git.aneel.gov.br bloqueiam acesso automatizado (Cloudflare, testado em 16/11/2026); sem acesso autorizado, a captura no GitHub Actions não roda.
- Aprovar padrão de identificadores de dispositivos (proposta: estilo LexML — ver `padrao-markdown-rag.md`).
- Confirmar como o leis.org apresenta textos alterados/revogados (tachado + notas?) → define a reconstrução do histórico.
- PRODIST/PRORET no git da ANEEL: confirmado que são PDFs, um arquivo por versão, com a resolução e a versão no nome (ex.: `aren2021956_Prodist_modulo_1_v11.pdf`).
