# Padrão Markdown — RASCUNHO v0.3

Status: rascunho em uso na REN 1.000 (Markdown vigente v0.3, D018 e D020; arquivo para chat v1.0, D021).

## Camadas
1. **Captura**: conteúdo baixado da fonte (não versionado).
2. **Texto canônico** (`dados/canonico/<norma>.json`): estrutura da norma por dispositivo, com histórico de redações.
3. **Markdown** (`dados/markdown/<norma>/...`): gerado a partir do canônico.
4. **Revisão** (`dados/revisao/<norma>.md`): casos que a extração não resolveu sozinha ou resolveu por inferência.
5. **Arquivo para chat** (`dados/chat/<norma>.md`): arquivo único para anexar a uma conversa com IA (ver abaixo).

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
- Cada dispositivo tem âncora com o `id`, a citação curta entre colchetes e o rótulo oficial: `[art. 6º, § 1º] § 1º texto`. O texto do artigo vem como `[art. 6º, caput] texto`; incisos ligados direto ao artigo são do caput (`[art. 2º, caput, inciso I-A]`).
- Revogado: `Art. 45 (Revogado pela REN nº X/AAAA)` sem texto antigo; os filhos de um dispositivo revogado não são repetidos.
- Suprimido e `conferir`: não aparecem (ficam no canônico e, no caso de `conferir`, no relatório de revisão).
- Nota de redação mantida abaixo do dispositivo: `> Redação dada pela REN nº X/AAAA`.
- Texto entre aspas que altera outra norma: logo abaixo do artigo que o transcreve, sem virar dispositivo.
- Tabelas em formato Markdown, com a coluna "Nota" quando alguma linha tiver nota de redação.
- Fecho (assinatura e notas de publicação) depois do último artigo; anexos depois, com `##` para o anexo e `###` para cláusulas.

## Arquivo para chat (padrão 1.0)
Um único Markdown para anexar a uma conversa com IA, gerado a partir do canônico, sem âncoras nem colchetes de citação. Ordem:
1. Título e dados da fonte: link, data da captura, última alteração incorporada, data da norma e início de vigência, padrão e hash do conteúdo.
2. "Como ler este arquivo": convenções, passo a passo para responder sobre uma data de referência, cuidados com as datas (data do ato alterador não é necessariamente a de vigência; prazos de transição; redação alterada sem indicação do ato; notas do preâmbulo; equações em imagem), forma de citação e observações sobre a fonte (correções manuais e rótulos repetidos).
3. "Atos que alteraram a norma": atos citados nas notas do texto, em ordem cronológica, com data e ementa. Depois, outros atos posteriores listados pela fonte e as normas anteriores relacionadas.
4. "Texto da norma": preâmbulo, estrutura em títulos Markdown (`###` em diante), dispositivos, fecho e anexos.

Cada dispositivo:
- vigente sem alteração: `§ 2º texto` (artigo em negrito: `**Art. 6º** texto`);
- com nova redação: `§ 1º texto (Redação dada pela Resolução Normativa nº 1042/2022, de 20/09/2022)` e, logo abaixo, cada redação anterior: `> Redação original, vigente de 03/01/2022 até 20/09/2022: Parágrafo único. texto`;
- revogado: `§ 4º [REVOGADO: Revogado pela ..., a partir de dd/mm/aaaa]` e o texto revogado em linha `>` com o período; os filhos revogados junto vêm só como `> I - texto`;
- suprimido: `I - [SUPRIMIDO: Suprimido pela nova redação do § 1º (...), a partir de dd/mm/aaaa]` e o texto em linha `>` com o período;
- rótulo repetido na fonte: `d) [rótulo repetido na fonte] texto`;
- texto entre aspas que altera outra norma e tabelas logo abaixo do dispositivo; nas tabelas, a coluna "Nota" traz a data do ato.

## Markdown — histórico / "em data X"
- Planejado: texto da norma como estava numa data escolhida, a partir do canônico.

## Versionamento do padrão
Mudanças neste padrão incrementam `padrao` e geram PR próprio regenerando todos os Markdowns.
