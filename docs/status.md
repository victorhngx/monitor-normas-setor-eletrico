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
- Issue #15 "Corrigir a extração da REN 1.000 e estruturar os anexos": regras de renumeração, supressão, revogação de grupo, incisos com letra, citações de alteração, vigência original, fecho, anexos e tabelas; relatório de revisão em `dados/revisao/` (D018).
- Issue #17 "Correções manuais e revogação do art. 672": arquivo `correcoes/ren-1000-2021.toml` (art. 666) e nota de revogação depois de texto citado (D019).

Extração da REN 1.000 (captura de 17/11/2026, regras D018 e D019): 730 artigos, 1.178 parágrafos, 1.989 incisos, 376 alíneas; 87 revogados (45 deles do art. 486, revogado por inteiro pela REN 1.098/2024), 15 suprimidos, 4 renumerações (arts. 6, 68, 105 e 180); vigência original 03/01/2022 (art. 679). Anexos: I (104 itens), II (20), III (5) e IV (tabela com 77 linhas, todas ligadas ao dispositivo citado). Nenhum dispositivo "conferir"; o relatório de revisão só traz a alínea "d" repetida do art. 668, III, mantida fiel à fonte.

## Próximo passo
- Plano para uso em IA/RAG: citação completa e rótulo "caput" no Markdown; arquivo de trechos para RAG com datas de vigência; Markdown "em data X"; tabela de vigência por ato alterador e suspensões (ex.: Despacho 2.006/2024 sobre o art. 323, II).
- Fase 4 (Diff): comparar duas versões do canônico e gerar o relatório por dispositivo.

## Funcionalidades futuras
Ver a seção "Funcionalidades futuras" em `roadmap.md`: captura sem computador local e rotina agendada no GitHub Actions, ambas dependentes da liberação de acesso pelo leis.org.

## Pendências / em aberto
- leis.org e git.aneel.gov.br bloqueiam acesso automatizado (Cloudflare, testado em 16/11/2026); a captura sem computador local depende de liberação da fonte.
- Padrão de identificadores: implementado no estilo LexML simplificado (`art48-A_par2_inc3_alia`); confirmar se atende.
- Datas de vigência das alterações vêm da data de publicação do ato alterador e estão marcadas "conferir vigência" (D006); a redação original usa a data do art. 679.
- Fórmulas (ex.: art. 109) ainda saem como texto simples.
- PRODIST/PRORET no git da ANEEL: PDFs, um arquivo por versão, com a resolução e a versão no nome (ex.: `aren2021956_Prodist_modulo_1_v11.pdf`).
