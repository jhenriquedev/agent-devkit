# Decision Rules: Build Analysis Query

- Gerar apenas consultas SQL Server read-only iniciadas por `SELECT` ou `WITH`.
- Bloquear `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `MERGE`, `CREATE`, `GRANT`, `REVOKE`, `BACKUP`, `RESTORE`, `DBCC` e `EXEC`.
- Incluir `TOP` automatico em consultas exploratorias sem limite.
- Qualificar schema e tabela quando conhecidos.
- Preferir agregacoes, contagens e filtros antes de linhas brutas.
- Nao incluir connection string, credenciais, host completo ou dados pessoais em comentarios SQL.
- Usar predicados especificos para evitar scans amplos.
- Gerar query compativel com `validate-readonly-query` antes de execucao.
- Quando o pedido exigir escrita, retornar bloqueio e alternativa analitica read-only.
- A saida deve informar objetivo, tabelas, filtros e limite sugerido.
