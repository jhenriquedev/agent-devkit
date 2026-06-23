# Prompt: detect-data-quality-issues

## OBJETIVO
Detectar problemas de qualidade de dados em nível de coluna: colunas
completamente nulas (`all_null`) e colunas com valor constante
(`constant_value`).

## ENTRADAS
- `schema` (obrigatório).
- `table` (obrigatório).

## RACIOCÍNIO (passos)
1. Execute a capability `detect-data-quality-issues --schema <s> --table <t>`.
2. Leia `issues[]` (campos: `column_name`, `issue_type`, `detail`).
3. Aplique a rubrica por tipo de issue.

## RUBRICA / REGRAS DE DECISÃO
- `all_null` → coluna sem dados; pode ser campo deprecated, não preenchido ou
  novo campo ainda vazio. Recomende investigação antes de usá-la em análises.
- `constant_value` → coluna com apenas um valor; pode ser flag (OK se
  intencional) ou erro de carga. Verifique se o valor faz sentido no contexto.
- Priorize issues em colunas-chave (identificadas via `describe-table`).
- Não conclua a causa; relate apenas o sintoma detectado.

## SAÍDA
Lista de issues por coluna com `issue_type` e `detail` + interpretação por
tipo de issue.

## NÃO FAÇA
- Não conclua causa do problema; apenas relate o sintoma.
- Não ignore issues em colunas que pareçam irrelevantes — o usuário decide.
