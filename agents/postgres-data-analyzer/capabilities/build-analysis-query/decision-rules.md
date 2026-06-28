# Decision Rules: Build Analysis Query

- Gerar apenas SQL read-only iniciado por `SELECT`, `WITH` ou `EXPLAIN`.
- Bloquear keywords de escrita, DDL, privilegios, procedures e comandos administrativos.
- Sempre incluir limite explicito para exploracao, salvo quando a query for agregado sem linhas pessoais.
- Qualificar schema e tabela quando o contexto estiver disponivel.
- Preferir agregacoes e contagens antes de selecionar linhas brutas.
- Nao incluir connection string, credenciais ou dados pessoais em comentarios SQL.
- Quando a solicitacao exigir mutacao, responder com bloqueio e alternativa read-only.
- A query gerada deve ser consumivel por `validate-readonly-query` antes de execucao.
