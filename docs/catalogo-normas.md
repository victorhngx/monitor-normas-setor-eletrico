# Catálogo de normas (planejamento)

A lista usada pela ferramenta é o arquivo [`catalogo.toml`](../catalogo.toml), na raiz do repositório. Para validar e ver os links das normas ativas:

```powershell
.venv\Scripts\python -m monitor_normas.catalogo
```

Normas no catálogo:

| Norma | Fonte | Formato | Status |
|---|---|---|---|
| REN 1.000/2021 | leis.org | HTML | Ativa (piloto) |

Planejadas, ainda fora do catálogo (entram quando o formato for confirmado):

| Norma | Fonte de captura | Formato esperado | Fase |
|---|---|---|---|
| PRODIST (módulos/submódulos) | https://git.aneel.gov.br/publico/centralconteudo/-/tree/main/procreg | A confirmar (provável PDF) | 7 |
| PRORET (submódulos) | https://git.aneel.gov.br/publico/centralconteudo/-/tree/main/procreg | A confirmar (provável PDF) | 7 |

Novas normas: acrescentar um bloco `[[normas]]` no `catalogo.toml` via PR e atualizar a tabela acima.
