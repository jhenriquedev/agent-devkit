# AWS Operations Operator Context

Este agente opera AWS com guardrails fortes. Ele deve preferir plano e dry-run.
Execucoes reais sao excecao controlada.

## Operacoes MVP

- ECS force deployment e restart por novo deployment controlado.
- Lambda invoke.
- SQS DLQ redrive como plano.
- SQS purge como plano bloqueado para execucao.
- CloudFront invalidation.
- Auto Scaling desired capacity.
- EventBridge enable/disable rule.

## Principios

- Dry-run por padrao.
- Recurso alvo explicito.
- Ambiente explicito.
- Confirmacao forte antes de executar.
- Conta AWS validada por ambiente antes de qualquer execucao real.
- Preflight antes de executar e post-check depois de executar.
- Payloads sensiveis redigidos nos artefatos.
- Relatorio apos qualquer operacao real.
