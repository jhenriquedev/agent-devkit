# Decision Rules: Validate Read-Only Query

- Validar sintaticamente e por guardrails antes de qualquer execucao de SQL.
- Permitir apenas `SELECT`, `WITH` ou `EXPLAIN`.
- Bloquear keywords de escrita, DDL, privileges, procedures, `COPY`, `DO`, `VACUUM` e comandos administrativos.
- Rejeitar multiplas statements, comentarios suspeitos e tentativa de bypass por casing.
- Exigir ou sugerir `LIMIT` para consultas exploratorias.
- Nao executar a query nesta capability quando o objetivo for apenas validacao.
- Mascarar literais pessoais e segredos ao renderizar a query validada.
- Retornar motivo objetivo para bloqueio e alternativa read-only quando possivel.
