# Padrão Markdown para RAG — RASCUNHO v0.1

Status: rascunho, será detalhado na Fase 3.

## Camadas
1. **Captura**: conteúdo baixado da fonte (não versionado).
2. **Texto canônico** (`dados/canonico/<norma>.json`): estrutura da norma por dispositivo, com histórico de redações.
3. **Markdown** (`dados/markdown/<norma>/...`): gerado a partir do canônico.

## Texto canônico (ideia)
Cada dispositivo tem:
- `id` estável (proposta, a aprovar: estilo LexML, ex.: `art12_par1_inc2`);
- hierarquia (Título, Capítulo, Seção, Artigo, §, inciso, alínea, item);
- lista de `redacoes`: `texto`, `vigente_de`, `vigente_ate`, `alterado_por`, `fonte_data` ("publicacao — conferir vigência" ou "confirmada"), `situacao` (vigente / revogado).

## Markdown — versão vigente
- Cabeçalho YAML: `norma`, `titulo`, `fonte_url`, `data_captura`, `padrao`, `hash_canonico`.
- Títulos Markdown seguindo a hierarquia (Título/Capítulo/Seção → `#`/`##`/`###`; artigo como título próprio).
- Cada dispositivo começa com seu rótulo oficial (Art. 12, § 1º, I, a) e tem âncora com o `id`.
- Revogado: `Art. 45. (Revogado pela REN nº X/AAAA)` sem texto antigo.
- Nota de redação mantida abaixo do dispositivo: `> Redação dada pela REN nº X/AAAA`.

## Markdown — histórico / "em data X"
- Cada trecho leva metadados `vigente_de`, `vigente_ate`, `alterado_por` para filtro temporal na RAG.

## Versionamento do padrão
Mudanças neste padrão incrementam `padrao` e geram PR próprio regenerando todos os Markdowns.
