# Roadmap

| Fase | Entrega | Status |
|---|---|---|
| 0. Fundação | Repo público, README, docs/, testes (pytest), estilo (ruff), trava de privacidade (gitleaks + bloqueio de PDF/HTML brutos), proteção do main, merge automático | Concluída |
| 1. Catálogo | `catalogo.toml` (norma, link, fonte, formato, se está ativa) → lista de links | Concluída |
| 2. Captura | Baixar REN 1.000 do leis.org; impressão digital (hash) para detectar mudança | Concluída pelo Chrome do computador local (D017); captura sem computador local é funcionalidade futura |
| 3. Canônico + Markdown RAG | Texto canônico (JSON por dispositivo, com redações e vigência) → Markdown vigente | Concluída para a REN 1.000 (D017); anexos ainda como texto simples |
| 4. Diff | Comparação entre versões do canônico; relatório por dispositivo (alterado/incluído/revogado) | Planejada |
| 5. Monitoramento | GitHub Actions diário (dias úteis, 7h) + issue automática quando houver mudança | Planejada |
| 6. Histórico | Reconstrução de redações anteriores (a partir do texto compilado) + Markdown "em data X" | Planejada |
| 7. PRODIST / PRORET | Captura do git da ANEEL (procreg) e conversão (provavelmente PDF) | Planejada |
| 8. Página | GitHub Pages com lista de normas, downloads e últimas alterações | Planejada |

A ordem pode mudar conforme decisões registradas em `decisoes.md`.

## Funcionalidades futuras

| Funcionalidade | Depende de | Situação |
|---|---|---|
| Captura totalmente automática do leis.org, sem computador local | Liberação do robô do projeto pelo leis.org (exceção no Cloudflare para um cabeçalho secreto, chave de API ou exportação) | Código pronto em `monitor_normas.captura` (D016); falta a credencial |
| Rotina agendada no GitHub Actions (dias úteis, 7h) com aviso por issue | A captura totalmente automática acima | Workflow `Captura` existe só com execução manual; o agendamento volta quando houver acesso |
| Estruturação dos anexos (contratos, formulários, tabelas, fórmulas) | — | Hoje os anexos saem como texto simples |
