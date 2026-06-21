# Decision Rules

- Rollback deve ser explicito e apontar para arquivo `.down.sql`.
- Rollback tambem passa por classificacao de risco.
- Se o rollback falhar, retornar erro sem esconder stderr do `psql`.
- Nao inventar rollback automaticamente.
