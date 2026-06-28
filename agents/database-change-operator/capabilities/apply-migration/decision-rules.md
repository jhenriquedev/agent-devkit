# Decision Rules

- Nunca aplicar sem `--execute`.
- Nunca aplicar migration destrutiva sem rollback.
- Nunca reaplicar migration com mesmo ID e checksum diferente.
- Registrar toda aplicacao em `ai_devkit_migrations`.
- Aplicar com `statement_timeout` e `lock_timeout` configurados.
- Mostrar o target database antes de qualquer escrita real.
