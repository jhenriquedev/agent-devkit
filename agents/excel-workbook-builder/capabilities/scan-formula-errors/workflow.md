# scan-formula-errors

OBJETIVO: Varrer um workbook .xlsx em busca de marcadores de erro de fórmula
(#REF!, #DIV/0!, #VALUE!, #NAME?, #N/A) e reportar localização e causa provável.

ENTRADAS: --workbook (caminho .xlsx obrigatório); --output.

RACIOCÍNIO:
1. Carregue o workbook via inspeção Python pura (sem Node; reutiliza o runner
   de review-generated-workbook).
2. Varra todas as abas detectando células com marcadores de erro.
3. Para cada erro: reporte aba, célula, tipo de erro e causa provável.
4. Produza relatório com total de erros e lista detalhada.

REGRAS DE DECISÃO:
- Qualquer erro encontrado = exit code 1 (gate bloqueante).
- Causa provável deve ser inferida: #REF! = referência quebrada; #DIV/0! =
  divisor zero; #NAME? = função/aba inexistente; #N/A = lookup sem match.

SAÍDA (markdown): formula-error-scan.md com lista de erros por aba/célula.

NÃO FAZER: não modificar o workbook; não ignorar erros mesmo que sejam
"esperados" pelo usuário.
