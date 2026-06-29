# Decision Rules

- Nunca enviar notificacao nesta capability.
- Usar `task.completed` quando o evento nao for informado.
- Redigir segredos em `summary`, `artifact` e `next_step`.
- Retornar `notification-event` mesmo quando o evento representar falha,
  bloqueio ou artefato gerado.
