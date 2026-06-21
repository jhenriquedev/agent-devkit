# Decision Rules

- Nunca aplicar sem `--execute`.
- Nunca aplicar migration destrutiva sem rollback.
- Nunca reaplicar migration com mesmo ID e checksum diferente.
- Registrar toda aplicacao em `ai_devkit_migrations`.
