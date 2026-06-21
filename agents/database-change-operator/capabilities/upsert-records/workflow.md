# Workflow

1. Ler registros de arquivo JSON ou CSV.
2. Validar schema, tabela, coluna chave e colunas de entrada.
3. Gerar `insert ... on conflict ... do update`.
4. Sem `--execute`, retornar dry-run com quantidade de registros.
5. Com `--execute`, aplicar upsert em transacao.
