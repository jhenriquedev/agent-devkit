# Decision Rules

- Ler ou receber o estado atual do card antes de planejar tag ou movimentacao.
- Sem `--execute`, retornar apenas plano `dry_run` para tag e movimentacao.
- Com `--execute`, aplicar somente as acoes explicitamente solicitadas e justificadas.
- Nao adicionar tag duplicada quando o card ja possuir a tag alvo.
- Nao mover card quando `target-state` ou `target-column` estiver ausente ou conflitar com o fluxo informado.
- Incluir motivo operacional claro para cada acao Azure planejada ou aplicada.
- Nao escrever no Azure quando o quality gate indicar falta de informacao minima para iniciar analise.
- Usar apenas `azure-devops-orchestrator/update-card-tags` e `azure-devops-orchestrator/move-card`.
- Preservar rastreabilidade com projeto, card, estado atual, destino e modo da acao.
- Nunca incluir dados sensiveis do cliente no nome da tag, estado, coluna ou motivo publico.
