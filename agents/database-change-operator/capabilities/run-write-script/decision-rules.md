# Decision Rules

- Use para scripts pontuais que nao devem virar migration versionada.
- Preferir migration quando a mudanca precisa de historico permanente.
- Sem `--execute`, retornar dry-run com plano, checksum e flags de risco.
- Nunca executar comandos bloqueados.
- Destacar scripts destrutivos no plano antes de executar.
- Script destrutivo exige confirmacao destrutiva reforcada antes de `--execute`.
- Registrar execucoes reais em `ai_devkit_write_audit`.
