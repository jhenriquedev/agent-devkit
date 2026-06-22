# Execute Specialist Validation

## Objetivo

Planejar ou executar validacoes especialistas selecionadas com contrato seguro.

## Entradas

- Checks selecionados.
- Contexto N2 e entidades.
- `--execute` para execucao real.
- Fixture para testes locais quando suportada.

## Raciocinio

1. Monte comando apenas quando parametros obrigatorios existirem.
2. BPO por proposta pode executar com `proposalNumber`.
3. Logs Elasticsearch exigem `source`, `from_time` e `to_time`.
4. CloudWatch exige `region`, `log_group`, `start_time`, `end_time`.
5. Banco exige query read-only explicita em `readonly_query`, `postgres_query`,
   `sqlserver_query`, `sql_query` ou `database_query`; nao reaproveite `query`
   generica de logs como SQL.
6. N1 exige `project` e `card`.
7. Sem contrato seguro, retorne `skipped` com `missingInputs`.

## Rubrica/Regras

- Sem `--execute`, status fica `planned` quando ha comando.
- Com `--execute`, rode apenas comando seguro.
- Falha de subprocesso vira `failed`, nao excecao silenciosa.

## Saida

JSON com `validations`, cada item contendo status, `commandPreview`,
`missingInputs` quando houver, e `resultSummary`.

## Nao faca

- Nao execute query de escrita.
- Nao passe CPF mascarado.
- Nao esconda requisito ausente.
