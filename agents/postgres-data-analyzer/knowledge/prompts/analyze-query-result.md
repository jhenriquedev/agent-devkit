# Prompt: analyze-query-result

> Operação read-only. Mascare PII. Separe dados coletados de inferências.

## Objetivo
Executar uma query e analisar as colunas do resultado (null_count, distinct_count,
sensitive_kind) sem exibir linhas brutas completas, para entender a qualidade e
sensibilidade dos dados retornados.

## Entradas esperadas
- `query` (obrigatório): query read-only.
- `limit` (default 100).
- `database` (opcional).

## Passos de raciocínio
1. Execute `analyze-query-result` (executa a query internamente e analisa as colunas).
2. Para cada coluna do resultado: `null_count`, `distinct_count`, `sensitive_kind`.
3. Calcule `null_ratio` e `distinct_ratio`.
4. Destaque colunas sensíveis e colunas com alto null.

## Regras de mascaramento
- `sensitive_kind` cpf/cnpj/document → **mascarar** na exibição de exemplo.
- Se a análise precisar exibir exemplos de valor, mascare PII.

## Regras de decisão
- Foco em métricas agregadas, não em linhas individuais.
- Coluna com `sensitive_kind` → sinalizar que deve ser mascarada em uso posterior.

## Saída
Tabela: `column_name`, `data_type`, `null_count`, `distinct_count`, `sensitive_kind`.
Seção **Resumo**: colunas sensíveis detectadas, colunas com alto null.

## NÃO faça
- Não exiba dump completo das linhas — apenas análise por coluna.
- Não exiba CPF/CNPJ completo.
