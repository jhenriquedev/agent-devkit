# run-workbook-operation  (DEPENDE DO RUNTIME NODE)

OBJETIVO: Aplicar uma operação discreta (sort, filter, aggregate, calculate) em
dados do workbook sem destruir a estrutura existente.

ENTRADAS: --workbook (obrigatório); --operation (sort|filter|aggregate|calculate);
--sheet; --column; --sort-order; --filter-value; --group-by; --aggregate-func;
--output.

RACIOCÍNIO:
1. PRÉ-CHECK do runtime Node.
2. Valide que a operação solicitada é suportada e que os parâmetros fazem
   sentido para o workbook (coluna existe, aba existe).
3. Aplique a operação na aba especificada.
4. Valide o resultado com review-generated-workbook.

REGRAS DE DECISÃO:
- Operação não suportada: falhe com lista de operações disponíveis.
- Sort/filter destrutivo: confirme antes de sobrescrever aba original.

SAÍDA: workbook.xlsx com operação aplicada.

NÃO FAZER: não aplicar operação em aba errada; não sobrescrever sem confirmar.
