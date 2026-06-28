# Regras

- Delegar leitura do card ao `azure-devops-orchestrator` em modo read-only.
- Exigir ID do card e resolver projeto explicitamente ou por configuracao local.
- Separar campos do card, comentarios, anexos citados e inferencias do agente.
- Nao escrever comentario, tag, assignee ou estado no Azure DevOps.
- Resumir logs ou dados sensiveis presentes no card antes de enviar para diagramacao.
- Registrar o card como fonte rastreavel para a spec intermediaria.
