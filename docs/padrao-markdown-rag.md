# Padrão Markdown para RAG — RASCUNHO v0.2

Status: rascunho em uso na REN 1.000 (v0.2, D018).

## Camadas
1. **Captura**: conteúdo baixado da fonte (não versionado).
2. **Texto canônico** (`dados/canonico/<norma>.json`): estrutura da norma por dispositivo, com histórico de redações.
3. **Markdown** (`dados/markdown/<norma>/...`): gerado a partir do canônico.
4. **Revisão** (`dados/revisao/<norma>.md`): casos que a extração não resolveu sozinha ou resolveu por inferência.

## Texto canônico
Cada dispositivo tem:
- `id` estável no estilo LexML simplificado (ex.: `art12_par1_inc2`, `art2_inc1-A_alia`); anexos com `anexo1_cl1` (cláusula), `anexo1_it4.1.2` (item) e `anexo1_texto1` (texto sem rótulo);
- `estrutura` (Título, Capítulo, Seção; nos anexos, anexo e cláusula);
- `situacao`: `vigente`, `revogado`, `suprimido` (deixou de existir com a nova redação do dispositivo pai, sem revogação expressa) ou `conferir`;
- lista de `redacoes`: `texto`, `situacao` (vigente / substituida / revogada / suprimida), `nota`, `ato` (tipo, número, ano, data, link), `vigente_de`, `vigente_ate`, `fonte_data` ("artigo de vigencia da norma", "publicacao - conferir vigencia" ou "inferida - conferir");
- `revogado_por` ou `suprimido_por` (nota e ato);
- quando houver: `ids_anteriores` e `renumeracao` (ex.: parágrafo único que passou a § 1º), `citacao` (texto entre aspas que altera outra norma) e `tabelas`.

Também no canônico: `vigencia` (data lida do artigo "Esta Resolução entra em vigor"), `fecho` (assinatura e notas de publicação), `anexos` (com dispositivos e tabelas) e `atos_vinculados` (lista de atos que alteram a norma, como o site informa).

## Markdown — versão vigente
- Cabeçalho YAML: `norma`, `titulo`, `fonte_url`, `data_captura`, `padrao`, `hash_canonico`.
- Títulos Markdown seguindo a hierarquia (Título/Capítulo/Seção → `##`/`###`/`####`; artigo como `######`).
- Cada dispositivo começa com seu rótulo oficial (Art. 12, § 1º, I, a) e tem âncora com o `id`.
- Revogado: `Art. 45 (Revogado pela REN nº X/AAAA)` sem texto antigo; os filhos de um dispositivo revogado não são repetidos.
- Suprimido e `conferir`: não aparecem (ficam no canônico e, no caso de `conferir`, no relatório de revisão).
- Nota de redação mantida abaixo do dispositivo: `> Redação dada pela REN nº X/AAAA`.
- Texto entre aspas que altera outra norma: logo abaixo do artigo que o transcreve, sem virar dispositivo.
- Tabelas em formato Markdown, com a coluna "Nota" quando alguma linha tiver nota de redação.
- Fecho (assinatura e notas de publicação) depois do último artigo; anexos depois, com `##` para o anexo e `###` para cláusulas.

## Markdown — histórico / "em data X"
- Cada trecho leva metadados `vigente_de`, `vigente_ate`, `alterado_por` para filtro temporal na RAG.

## Versionamento do padrão
Mudanças neste padrão incrementam `padrao` e geram PR próprio regenerando todos os Markdowns.
