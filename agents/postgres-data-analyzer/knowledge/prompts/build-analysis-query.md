# Prompt: build-analysis-query

> Operação read-only. Não execute — apenas construa. Nunca remova o LIMIT.

## Objetivo
Construir uma query SELECT segura e limitada a partir de schema/tabela/colunas
informados pelo usuário, pronta para validação e execução posterior.

## Entradas esperadas
- `schema` (obrigatório): schema da tabela alvo.
- `table` (obrigatório): nome da tabela.
- `columns` (opcional, csv): colunas a selecionar; se omitido, usa `*`.
- `limit` (default 100): limite de linhas.
- `database` (opcional).

## Passos de raciocínio
1. Confirme schema e table. Se faltarem, peça ao usuário.
2. Execute `build-analysis-query`. O runner valida/quota os identificadores.
3. Exiba a query gerada em bloco ```sql.
4. Informe o limite aplicado.
5. Recomende validar com `validate-readonly-query` antes de executar.

## Regras de decisão
- Se o usuário informar coluna que não existe (erro do runner), informe e sugira
  `describe-table` para ver colunas reais.
- Nunca remova o LIMIT da query gerada.
- Nunca adicione cláusulas de escrita (INSERT/UPDATE/etc.).

## Saída
```sql
SELECT ... FROM schema.table LIMIT N
```
- Limite aplicado: N
- Próximo passo recomendado: validate-readonly-query ou run-readonly-query.

## NÃO faça
- Não execute a query aqui.
- Não relaxe o LIMIT.
- Não gere queries de escrita.
