# create-pivot-summary  (DEPENDE DO RUNTIME NODE)

OBJETIVO: Criar uma aba de resumo agrupado (estilo pivot) a partir dos dados
do workbook, com totais e subtotais auditáveis.

ENTRADAS: --workbook (obrigatório) ou --input (JSON); --group-by (colunas de
agrupamento, csv); --values (métricas, csv); --aggregate-func (sum|count|avg|
min|max); --output; --sheet.

RACIOCÍNIO:
1. PRÉ-CHECK do runtime Node.
2. Defina group_by e values explicitamente; confirme com o usuário se ambíguos.
3. Aplique agrupamento e calcule métricas.
4. Crie aba de pivot separada dos dados origem.
5. Valide totais: o total geral deve bater com a soma dos subtotais.

REGRAS DE DECISÃO:
- Nunca sobrescreva a aba Data com o pivot; crie aba separada.
- Total inconsistente: reporte como erro antes de entregar.

SAÍDA: workbook.xlsx com aba de pivot adicionada.

NÃO FAZER: não misturar dados origem com resumo; não inventar métricas.
