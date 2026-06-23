# Prompt: analyze-cpf-column

> Operação read-only. NUNCA exiba CPFs individuais — apenas métricas agregadas.

## Objetivo
Avaliar a qualidade de uma coluna de CPF (formato, dígitos verificadores, repetidos,
duplicados) usando cálculos no banco, sem expor documentos individuais.

## Entradas esperadas
- `schema` (obrigatório).
- `table` (obrigatório).
- `column` (obrigatório): nome da coluna de CPF.
- `database` (opcional).

## Passos de raciocínio
1. Execute `analyze-cpf-column`.
2. Interprete as métricas retornadas:
   - `blank_count`: CPFs vazios/nulos.
   - `invalid_format_count`: CPFs com ≠ 11 dígitos.
   - `repeated_digits_count`: CPFs como 00000000000, 11111111111, etc. (inválidos).
   - `invalid_check_digit_count`: 11 dígitos mas dígito verificador errado.
   - `valid_count`: CPFs válidos.
   - `duplicated_document_count`: CPFs únicos que aparecem mais de 1 vez.
   - `duplicated_row_count`: total de linhas com CPF duplicado.
3. Calcule `taxa_validade = valid_count / total_rows`.
4. Destaque riscos: alto blank, alto inválido, duplicatas.

## Regras de decisão
- **NUNCA** exiba CPFs individuais, nem inválidos, nem exemplos.
- Se `invalid_format_count + repeated_digits_count + invalid_check_digit_count > 20% de total_rows`
  → recomendar limpeza na origem.
- Duplicatas altas → possível problema de integridade; recomendar investigação.

## Saída
Lista de métricas agregadas:
- total_rows, blank_count, invalid_format_count, repeated_digits_count,
  invalid_check_digit_count, valid_count, duplicated_document_count, duplicated_row_count
- Taxa de validade: N%

Parágrafo de diagnóstico com recomendações (INFERÊNCIA baseada nas métricas).

## NÃO faça
- Não liste exemplos de CPF, nem válidos nem inválidos.
- Não deduza identidade de pessoas.
- Não exiba o conteúdo bruto da coluna.
