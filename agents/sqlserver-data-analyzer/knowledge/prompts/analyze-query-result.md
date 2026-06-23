# Prompt: analyze-query-result

## OBJETIVO
Executar uma query e perfilar as colunas do resultado (null count, distinct
count, sensitive_kind) sem expor dados individuais.

## ENTRADAS
- `query` (obrigatório): SQL SELECT ou WITH.
- `limit` (opcional, default 100).

## RACIOCÍNIO (passos)
1. Execute a capability `analyze-query-result --query "<sql>"`.
2. O runner executa a query com `run_readonly_query` e passa as linhas para
   `analyze_rows`.
3. Leia `row_count` e `columns[]` (campos: `column_name`, `null_count`,
   `distinct_count`, `sensitive_kind`).
4. Se alguma coluna tiver `sensitive_kind != null`, alerte e recomende
   mascaramento na resposta final.

## RUBRICA / REGRAS DE DECISÃO
- `sensitive_kind` presente → avise que a coluna contém dado pessoal;
  não exiba valores brutos.
- `null_count / row_count > 0.5` → coluna com muitos nulos; pode ser opcional
  ou com problema de captura.

## SAÍDA
Tabela por coluna com `null_count`, `distinct_count`, `sensitive_kind` +
alertas de colunas sensíveis.

## NÃO FAÇA
- Não exiba os dados das linhas retornadas; apenas o perfil de colunas.
- Não ignore alertas de `sensitive_kind`.
