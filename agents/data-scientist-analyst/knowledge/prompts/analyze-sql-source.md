# analyze-sql-source

## Objetivo
Delegar consulta SQL read-only a um agente de banco (postgres-data-analyzer ou
sqlserver-data-analyzer) e tratar o retorno como fonte analitica tabular
reutilizavel — sem reimplementar conexao nem parsear texto como tabela.

## Entradas
- `--database-agent {postgres-data-analyzer|sqlserver-data-analyzer}` (obrigatorio).
- `--database-capability`: capability do agente de banco (default: profile-table).
- `--database`: nome do banco.
- `--schema`: schema alvo.
- `--table`: tabela alvo.
- `--query`: query SQL read-only alternativa.
- `--limit`: limite de linhas (default: 1000).
- `--dataset-output`: caminho para gravar artifact tabular reutilizavel.

## Raciocinio
1. Escolha o agente correto pelo backend declarado; nunca reimplemente conexao.
2. Execute delegacao via subprocess `agent run <database-agent>
   <database-capability> --json ...`.
3. Verifique quality_gates retornados: delegation_success, tabular_result_available,
   dataset_artifact_written (se --dataset-output).
4. Se result.kind != "tabular_dataset" -> trate como raw_output; avise que
   capabilities tabulares downstream sao bloqueadas.
5. Com --dataset-output: encaminhe artifact para profile-dataset/EDA; registre
   sha256 do artifact.

## Rubrica de decisao
- delegation_success=false -> propague stderr do agente de banco; nao prossiga.
- Resultado nao tabular -> bloqueie capabilities tabulares downstream; declare.
- Mutation suspeita na query (INSERT/UPDATE/DELETE/DROP) -> bloqueie delegacao.
- sha256 ausente do artifact -> nao use para analise auditavel.

## Saida
Status da delegacao (agente, capability, status), resumo do dataset normalizado
(row_count, colunas, sha256 se artifact), caminho do artifact se --dataset-output,
quality_gates, proximo passo sugerido.

## Nao fazer
- Nao escrever no banco nem redirecionar queries com mutacao.
- Nao parsear texto livre como tabela estruturada.
- Nao analisar como tabular um retorno nao normalizado (kind != tabular_dataset).
- Nao reimplementar conexao SQL; sempre delegar ao agente de banco.
