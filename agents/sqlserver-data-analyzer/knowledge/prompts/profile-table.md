# Prompt: profile-table

## OBJETIVO
Perfilar cada coluna de uma tabela: total de linhas, nulos, distintos —
sem expor dados individuais.

## ENTRADAS
- `schema` (obrigatório).
- `table` (obrigatório).

## RACIOCÍNIO (passos)
1. Execute a capability `profile-table --schema <s> --table <t>`.
2. Leia `row_count` e `columns[]` (campos: `column_name`, `null_count`,
   `distinct_count`).
3. Aplique a rubrica por coluna.

## RUBRICA / REGRAS DE DECISÃO
- `null_count == row_count` → coluna inutilizável; alerte.
- `distinct_count == 1` → coluna constante; pode ser flag ou valor padrão.
- `distinct_count == row_count` → candidato a chave única.
- `null_count / row_count > 0.5` → alta cardinalidade de nulos; investigue.
- O runner limita a 30 colunas; mencione se truncado.

## SAÍDA
Tabela de stats por coluna + leitura de anomalias encontradas pela rubrica.

## NÃO FAÇA
- Não infira causa das anomalias; relate apenas o sintoma.
- Não exiba dados brutos — apenas agregados.
