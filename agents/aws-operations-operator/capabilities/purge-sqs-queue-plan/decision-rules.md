# Decision Rules: Purge SQS Queue Plan

## Objetivo de decisao

Gerar plano de purge de fila SQS sem executar a remocao de mensagens no MVP.

## Entradas minimas

- `--queue-url` e `--environment` sao obrigatorios.
- A fila alvo deve ser explicitamente identificada pela URL completa.

## Quando executar

Execute apenas como plano quando:

- o usuario precisa avaliar limpeza total de fila;
- a fila alvo esta explicita;
- o impacto de perda de mensagens precisa ser documentado.

Nao execute de fato:

- mesmo que o usuario peca `--execute`;
- mesmo que a fila esteja em `dev`;
- enquanto destrutivas permanecerem bloqueadas no MVP.

## Regras de decisao

1. O runner deve forcar `execute=False`.
2. O status deve ser `blocked-plan-only`.
3. Marcar `destructive: true`.
4. Declarar que purge apaga todas as mensagens e nao possui rollback nativo.
5. Orientar backup, reprocessamento ou validacao de descarte antes de qualquer
   acao manual externa.
6. Nao chamar AWS para `sqs purge-queue` nesta versao.

## Criterios de qualidade

- `operation-plan.md` destaca perda total de mensagens.
- `operation-dry-run.json` mostra comando planejado, mas `execute: false`.
- `rollback-notes.md` deixa claro que rollback depende de backup/replay.
- Nenhum `operation-result.json` deve ser criado.

## Escalacao

Exigir aprovacao operacional se a fila for de producao, contiver mensagens de
cliente, financeiro, onboarding ou qualquer processo sem replay confiavel.
