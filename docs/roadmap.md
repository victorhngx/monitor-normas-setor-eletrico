# Roadmap

| Fase | Entrega | Status |
|---|---|---|
| 0. Fundação | Repo público, README, docs/, testes (pytest), estilo (ruff), trava de privacidade (gitleaks + bloqueio de PDF/HTML brutos), proteção do main, merge automático | Concluída |
| 1. Catálogo | `catalogo.toml` (norma, link, fonte, formato, se está ativa) → lista de links | Concluída |
| 2. Captura | Baixar REN 1.000 do leis.org; impressão digital (hash) para detectar mudança | Em andamento: captura pronta, aguardando acesso autorizado ao leis.org (D016) |
| 3. Canônico + Markdown RAG | Texto canônico (JSON por dispositivo, com redações e vigência) → Markdown vigente | Planejada |
| 4. Diff | Comparação entre versões do canônico; relatório por dispositivo (alterado/incluído/revogado) | Planejada |
| 5. Monitoramento | GitHub Actions diário (dias úteis, 7h) + issue automática quando houver mudança | Planejada |
| 6. Histórico | Reconstrução de redações anteriores (a partir do texto compilado) + Markdown "em data X" | Planejada |
| 7. PRODIST / PRORET | Captura do git da ANEEL (procreg) e conversão (provavelmente PDF) | Planejada |
| 8. Página | GitHub Pages com lista de normas, downloads e últimas alterações | Planejada |

A ordem pode mudar conforme decisões registradas em `decisoes.md`.
