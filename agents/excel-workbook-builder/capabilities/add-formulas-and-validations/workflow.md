# add-formulas-and-validations  (DEPENDE DO RUNTIME NODE)

OBJETIVO: Aplicar um plano JSON de fórmulas, validações de dados e comentários
em um workbook .xlsx existente, produzindo fórmulas auditáveis.

ENTRADAS: --workbook (obrigatório); --formula-plan (JSON com sheet, cells[{cell,
formula|value,format}], validations[{range,type,values|formula1/2,operator}],
comments[]); --output.

RACIOCÍNIO:
1. PRÉ-CHECK do runtime Node (ver runtime.md).
2. Carregue e valide o formula-plan (carregue formula-rules.md): referências
   explícitas, sem números mágicos, abas de parâmetros para premissas.
3. Aplique fórmulas, validações e comentários célula a célula conforme o plano.
4. Execute scan-formula-errors após aplicar para confirmar ausência de erros.

REGRAS DE DECISÃO:
- Fórmula com número mágico: avise e sugira aba de parâmetros.
- Referência a aba inexistente: falhe com erro claro antes de aplicar.
- Validação de dados: tipos suportados são list, whole, decimal, date, textLength,
  custom.

SAÍDA: workbook.xlsx com fórmulas e validações aplicadas.

NÃO FAZER: não aplicar fórmulas sem validar o plano; não ignorar erros de
referência.
