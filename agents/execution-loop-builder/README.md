# Execution Loop Builder

Agente especialista em projetar loops de execucao pequenos, controlados e
auditaveis.

## Capabilities

- `plan-execution-loop`: valida e planeja contrato de loop.
- `generate-loop-runner`: gera runner Python output-only.
- `generate-loop-project-files`: planeja ou escreve pacote local de loop.
- `review-loop-safety`: revisa riscos de loop infinito, side effects,
  budgets, notificacao e idempotencia.
- `register-loop-task`: registra loop no scheduler local existente, apenas com
  `--execute`.

## Politica

O agente nao executa as capabilities reais do loop no MVP. Ele gera contrato,
runner seguro, auditoria local e registro de task para execucao controlada.
