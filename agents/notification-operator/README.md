# Notification Operator

Agente runtime para formatar, enviar e configurar notificacoes locais de tarefas
do Agent DevKit.

Ele padroniza eventos como `task.completed`, `task.failed`, `task.blocked`,
`wizard.waiting`, `review.required` e `artifact.generated`, mantendo canais
remotos fora do escopo ate haver provider dedicado.

## Capabilities

- `format-task-completion-notification`: normaliza o payload canonico sem enviar
  nada.
- `send-task-completion-notification`: envia notificacao local apos confirmacao.
- `configure-notification-channel`: configura canais locais suportados.
