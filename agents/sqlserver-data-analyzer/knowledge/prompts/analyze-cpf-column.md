# Prompt: analyze-cpf-column

## OBJETIVO
Auditar uma coluna de CPF: validar formato, dígito verificador, detectar
dígitos repetidos e duplicatas — sem expor CPFs individuais.

## ENTRADAS
- `schema` (obrigatório).
- `table` (obrigatório).
- `column` (obrigatório): nome da coluna CPF.

## RACIOCÍNIO (passos)
1. Execute a capability `analyze-cpf-column --schema <s> --table <t> --column <c>`.
2. Leia as métricas agregadas: `total_rows`, `blank_count`,
   `invalid_format_count`, `repeated_digits_count`, `valid_count`,
   `invalid_check_digit_count`, `duplicated_document_count`,
   `duplicated_row_count`.
3. Calcule taxas (%) para facilitar interpretação.
4. Aplique a rubrica de qualidade e fraude.

## RUBRICA / REGRAS DE DECISÃO
- `blank_count / total_rows > 0.1` → preenchimento ruim; mais de 10% em branco.
- `invalid_format_count > 0` → CPFs malformados; erro de captura ou importação.
- `repeated_digits_count > 0` → CPFs como "000.000.000-00" ou "111..." —
  provavelmente placeholders inválidos.
- `invalid_check_digit_count / total_rows > 0.05` → qualidade de captura ruim;
  > 5% com dígito inválido é sinal de alerta.
- `duplicated_document_count > 0` → possível fraude, erro de integração ou
  múltiplas contas para mesmo CPF; investigar.

## SAÍDA
Tabela de métricas com taxas percentuais + interpretação por rubrica.
Nota: "CPFs individuais nunca são exibidos."

## NÃO FAÇA
- NUNCA liste CPFs individuais.
- Não apresente apenas os números brutos sem interpretação.
