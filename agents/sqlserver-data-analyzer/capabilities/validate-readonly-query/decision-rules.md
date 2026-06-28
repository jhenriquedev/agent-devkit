# Decision Rules: Validate Read-Only Query

- Validar query antes de qualquer execucao livre.
- Permitir apenas `SELECT` ou `WITH` read-only e explain logico implementado pelo agente.
- Bloquear `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `MERGE`, `CREATE`, `GRANT`, `REVOKE`, `BACKUP`, `RESTORE`, `DBCC` e `EXEC`.
- Rejeitar multiplas statements e tentativas de bypass por comentario, casing ou batch separator.
- Aplicar ou recomendar `TOP` quando consulta exploratoria nao tiver limite.
- Nao executar a query nesta capability quando o objetivo for apenas validacao.
- Mascarar literais pessoais e segredos ao renderizar preview.
- Retornar motivo objetivo para bloqueio e alternativa read-only.
- Nao aceitar confirmacao do usuario para liberar keyword bloqueada.
- A saida deve ser consumivel por `run-readonly-query`.
