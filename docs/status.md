# Status atual

**Atualizado em:** 17/11/2026

> Atualizar este arquivo ao fim de cada issue/sessão de trabalho.

## Onde estamos
Fases 0 (Fundação) e 1 (Catálogo) concluídas. Fases 2 (Captura) e 3 (Canônico + Markdown) concluídas para a REN 1.000, com captura pelo Chrome do computador local. A REN 1.000 já tem o arquivo único para anexar a um chat (`dados/chat/ren-1000-2021.md`).
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
- Issue #19 "Citação completa e trechos para RAG": citação e "caput" no Markdown (padrão 0.3) e `dados/rag/ren-1000-2021.jsonl` com 4.696 trechos, um por redação de cada dispositivo e por linha de tabela (D020).
- Issue #21 "Arquivo da norma para uso em chat": `dados/chat/ren-1000-2021.md`, arquivo único com guia de leitura, atos alteradores e o texto com o histórico de redações e as datas; os trechos JSONL deixaram de ser gerados (D021).

Extração da REN 1.000 (captura de 17/11/2026, regras D018 e D019): 730 artigos, 1.178 parágrafos, 1.989 incisos, 376 alíneas; 87 revogados (45 deles do art. 486, revogado por inteiro pela REN 1.098/2024), 15 suprimidos, 4 renumerações (arts. 6, 68, 105 e 180); vigência original 03/01/2022 (art. 679). Anexos: I (104 itens), II (20), III (5) e IV (tabela com 77 linhas, todas ligadas ao dispositivo citado). Nenhum dispositivo "conferir"; o relatório de revisão só traz a alínea "d" repetida do art. 668, III, mantida fiel à fonte.

## Próximo passo
- Testar o arquivo para chat em conversas reais (perguntas sobre datas passadas) e ajustar o guia de leitura se preciso.
- Markdown "em data X": texto da norma como estava numa data escolhida (talvez desnecessário com o arquivo para chat).
- Tabela de vigência por ato alterador e suspensões (ex.: Despacho 2.006/2024 sobre o art. 323, II).
- Fase 4 (Diff): comparar duas versões do canônico e gerar o relatório por dispositivo.

## Funcionalidades futuras
Ver a seção "Funcionalidades futuras" em `roadmap.md`: captura sem computador local e rotina agendada no GitHub Actions, ambas dependentes da liberação de acesso pelo leis.org.

## Pendências / em aberto
- leis.org e git.aneel.gov.br bloqueiam acesso automatizado (Cloudflare, testado em 16/11/2026); a captura sem computador local depende de liberação da fonte.
- Padrão de identificadores: implementado no estilo LexML simplificado (`art48-A_par2_inc3_alia`); confirmar se atende.
- Datas de vigência das alterações vêm da data de publicação do ato alterador e estão marcadas "conferir vigência" (D006); a redação original usa a data do art. 679.
- Fórmulas (ex.: art. 109) são imagens no site e não aparecem no texto; o arquivo para chat avisa isso no guia de leitura.
- REN 1.148/2026: a fonte lista o ato (ementa diz que altera a REN 1.000), mas nenhuma nota do texto o cita; conferir se as alterações estão incorporadas.
- Alguns dispositivos mudaram de redação sem nota do ato (24 redações); a data fica "?" no arquivo para chat.
- PRODIST/PRORET no git da ANEEL: PDFs, um arquivo por versão, com a resolução e a versão no nome (ex.: `aren2021956_Prodist_modulo_1_v11.pdf`).
