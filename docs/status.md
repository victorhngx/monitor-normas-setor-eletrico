# Status atual

**Atualizado em:** 17/11/2026

> Atualizar este arquivo ao fim de cada issue/sessão de trabalho.

## Onde estamos
Fases 0 (Fundação) e 1 (Catálogo) concluídas. Fases 2 (Captura) e 3 (Canônico + Markdown) concluídas para a REN 1.000, com captura pelo Chrome do computador local.
- Repositório criado com `.gitignore` e a documentação de planejamento em `docs/`.
- Issue #1 "Escrever o README": apresentação do projeto, fontes e funcionamento.
- Issue #3 "Base Python com testes e estilo": `pyproject.toml`, pacote `monitor_normas` em `src/`, pytest e ruff (D012).
- Issue #5 "Trava de privacidade": verificador `monitor_normas.trava_privacidade` que bloqueia documentos brutos, `dados/brutos/` e arquivos de segredo (D013).
- Issue #7 "Checagem automática nos PRs e proteção do main": workflow `Verificações` (pytest, ruff, trava, gitleaks), main protegido e merge automático (D014).
- Issue #9 "Catálogo de normas": `catalogo.toml` com a REN 1.000 e leitor com validação `monitor_normas.catalogo` (D015).
- Issue #11 "Captura automática com acesso autorizado": módulo `monitor_normas.captura` e workflow `Captura` (só execução manual), prontos para quando o leis.org liberar o acesso (D016).
- Issue #13 "Captura pelo navegador do notebook e extração": `monitor_normas.captura_navegador` e `monitor_normas.extracao_leis_org`; primeira extração da REN 1.000 em `dados/canonico/` e `dados/markdown/` (D017).

Primeira extração da REN 1.000 (captura de 17/11/2026): 760 artigos, 1.190 parágrafos, 2.000 incisos, 380 alíneas, 23 dispositivos revogados, 166 notas "Redação dada" e 224 "Redação acrescida"; 30 dispositivos com situação `conferir` (renumerações) e 4 anexos como texto simples.

## Próximo passo
- Revisar os 30 dispositivos com situação `conferir` e decidir como registrar renumerações.
- Fase 4 (Diff): comparar duas versões do canônico e gerar o relatório por dispositivo.

## Funcionalidades futuras
Ver a seção "Funcionalidades futuras" em `roadmap.md`: captura sem computador local e rotina agendada no GitHub Actions, ambas dependentes da liberação de acesso pelo leis.org.

## Pendências / em aberto
- leis.org e git.aneel.gov.br bloqueiam acesso automatizado (Cloudflare, testado em 16/11/2026); a captura sem computador local depende de liberação da fonte.
- Padrão de identificadores: implementado no estilo LexML simplificado (`art48-A_par2_inc3_alia`); confirmar se atende.
- Datas de vigência vêm da data de publicação do ato alterador e estão marcadas "conferir vigência" (D006).
- PRODIST/PRORET no git da ANEEL: PDFs, um arquivo por versão, com a resolução e a versão no nome (ex.: `aren2021956_Prodist_modulo_1_v11.pdf`).
