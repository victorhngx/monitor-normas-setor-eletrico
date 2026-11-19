# Roadmap

| Fase | Entrega | Status |
|---|---|---|
| 0. Fundação | Repo público, README, docs/, testes (pytest), estilo (ruff), trava de privacidade (gitleaks + bloqueio de PDF/HTML brutos), proteção do main, merge automático | Concluída |
| 1. Catálogo | `catalogo.toml` (norma, link, fonte, formato, se está ativa) → lista de links | Concluída |
| 2. Captura | Baixar REN 1.000 do leis.org; impressão digital (hash) para detectar mudança | Concluída pelo Chrome do computador local (D017); captura sem computador local é funcionalidade futura |
| 3. Canônico + Markdown | Texto canônico (JSON por dispositivo, com redações e vigência) → Markdown vigente e arquivo para chat | Concluída para a REN 1.000 (D017, D018, D021), com anexos e tabelas estruturados |
| 4. Diff | Comparação entre versões do canônico; relatório por dispositivo (alterado/incluído/revogado) | Planejada |
| 5. Monitoramento | GitHub Actions diário (dias úteis, 7h) + issue automática quando houver mudança | Planejada |
| 6. Histórico | Reconstrução de redações anteriores (a partir do texto compilado) + Markdown "em data X" | Planejada |
| 7. PRODIST / PRORET | Captura do git da ANEEL (procreg) e conversão (provavelmente PDF) | Planejada |
| 8. Página | GitHub Pages com lista de normas, downloads e últimas alterações | Planejada |

A ordem pode mudar conforme decisões registradas em `decisoes.md`.

## Estrutura alvo (D022)

Objetivo final: página (GitHub Pages) com as normas mais importantes do setor elétrico, cada uma com texto vigente, texto com histórico completo para uso em chat de IA, texto em uma data escolhida, diff das alterações e aviso de alterações aprovadas com vigência futura. Atualização feita por scripts, com o mínimo de intervenção manual e sem IA na rotina.

Base comum: um registro dos atos que alteram cada norma, com a data em que cada alteração passa a valer, lida do próprio ato. Todas as saídas saem dessa base.

| Etapa | Entrega | Status |
|---|---|---|
| A. Captura dos atos alteradores | `monitor_normas.captura_atos`: páginas dos atos listados pela norma, em `dados/brutos/atos/` | Concluída (issue #23); testada com RENs 1.148/2026, 1.174/2026 e 1.059/2023 |
| B. Extração dos atos e vigência | Canônico de cada ato; vigência lida da cláusula "entra em vigor" (data fixa, data de publicação, efeitos escalonados por dispositivo); datas do histórico da norma corrigidas pela vigência | Planejada |
| C. Alterações e redações futuras | Leitura dos blocos "passa a vigorar com as seguintes alterações" (NR, acréscimo, revogação); redações futuras na linha do tempo; aviso de alteração aprovada no texto vigente e no arquivo para chat; conferência quando o site incorporar o ato | Planejada |
| D. Diff | Por ato (antes e depois de cada dispositivo alterado) e entre duas datas | Planejada (fase 4) |
| E. Página | GitHub Pages com texto vigente, histórico, seletor de data, diffs e downloads | Planejada (fase 8) |
| F. Aviso de atos novos | A cada captura, ato novo na lista da norma abre issue | Planejada (fase 5) |
| G. PRODIST / PRORET | Mesmo modelo, com cada versão de módulo como um "ato" | Planejada (fase 7) |

Intervenção manual prevista: concluir a verificação do site na captura, olhar os casos do relatório de revisão e aprovar os PRs.

## Funcionalidades futuras

| Funcionalidade | Depende de | Situação |
|---|---|---|
| Captura totalmente automática do leis.org, sem computador local | Liberação do robô do projeto pelo leis.org (exceção no Cloudflare para um cabeçalho secreto, chave de API ou exportação) | Código pronto em `monitor_normas.captura` (D016); falta a credencial |
| Rotina agendada no GitHub Actions (dias úteis, 7h) com aviso por issue | A captura totalmente automática acima | Workflow `Captura` existe só com execução manual; o agendamento volta quando houver acesso |
| Estruturação de fórmulas (ex.: art. 109) | — | Anexos e tabelas já estruturados (D018); fórmulas ainda saem como texto simples |
