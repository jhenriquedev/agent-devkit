# Decision Rules: analyze-cpf-column

## Rubrica de qualidade CPF

| Métrica | Limiar de alerta | Severidade | Interpretação |
|---|---|---|---|
| `blank_count / total_rows` | > 10% | Alta | Preenchimento ruim de CPF |
| `invalid_format_count` | > 0 | Alta | CPFs malformados (não são 11 dígitos) |
| `repeated_digits_count` | > 0 | Alta | Placeholders (000...000, 111...111) inválidos |
| `invalid_check_digit_count / total_rows` | > 5% | Alta | Qualidade de captura ruim |
| `duplicated_document_count` | > 0 | Crítica | Possível fraude, erro de integração, múltiplas contas |

## Regras de decisão

1. NUNCA listar CPFs individuais na resposta; apenas métricas agregadas.
2. `duplicated_document_count > 0` → alertar como caso crítico; recomendar
   investigação de fraude ou erro de integração.
3. `repeated_digits_count > 0` → CPFs "000...000" são inválidos por definição;
   tratar como placeholder, não como CPF real.
4. Calcular taxas percentuais para facilitar interpretação.
5. Classificar qualidade geral: ≥ 95% válidos = boa; 80–95% = aceitável;
   < 80% = ruim.

## Quando pedir info

- `schema`, `table` ou `column` ausente → pedir antes de executar.
