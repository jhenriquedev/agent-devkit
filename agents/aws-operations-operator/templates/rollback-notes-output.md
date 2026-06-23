# Rollback Notes

> Render dinamico via `report_renderer.render_rollback_notes(payload)`.
> Este template anota o contrato de saida — o conteudo real e gerado pelo renderer.

## Campos

- **Operation**: id da operacao executada ou planejada
- **Resource**: resource_id alvo
- **Guidance**: instrucao de reversao especifica por tipo de operacao

## Exemplos de guidance por operacao

- **force-ecs-deployment / restart-ecs-service**: Nao ha rollback direto; validar
  task definition anterior e executar novo deployment se necessario.
- **invoke-lambda**: Lambda invoke nao possui rollback automatico; validar efeitos
  colaterais do handler.
- **invalidate-cloudfront-cache**: Invalidation nao pode ser desfeita; aguardar
  propagacao e validar cache.
- **scale-autoscaling-group**: Restaurar desired capacity anterior apos validacao.
- **toggle-eventbridge-rule**: Executar a action oposta (enable <-> disable).
- **redrive-sqs-dlq**: Redrive pode duplicar processamento. Validar idempotencia
  antes de execucao manual.
- **purge-sqs-queue-plan**: Purge de SQS nao tem rollback. Validar
  backup/reprocessamento antes de qualquer execucao manual.
