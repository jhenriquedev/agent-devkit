# Decision Rules: Redrive SQS DLQ

## Objetivo de decisao

Gerar plano de redrive de DLQ para fila destino sem executar a mutacao no MVP.

## Entradas minimas

- `--source-arn`, `--destination-arn` e `--environment` sao obrigatorios.
- A source deve ser a DLQ e a destination deve ser a fila de reprocessamento
  esperada.

## Quando executar

Execute apenas como plano quando:

- o usuario precisa avaliar redrive de mensagens;
- ha ARNs explicitos de origem e destino;
- a idempotencia dos consumidores ainda precisa ser validada.

Nao execute de fato:

- mesmo que o usuario peca `--execute`;
- mesmo que forneca confirmacao;
- enquanto a politica MVP mantiver destrutivas como plan-only.

## Regras de decisao

1. O runner deve forcar `execute=False`.
2. O status deve ser `blocked-plan-only`.
3. Marcar `destructive: true`.
4. Explicar risco de duplicacao de processamento.
5. Exigir validacao de idempotencia antes de qualquer acao manual fora do agente.
6. Nao chamar AWS para `start-message-move-task` nesta versao.

## Criterios de qualidade

- `operation-plan.md` e `operation-dry-run.json` indicam bloqueio de execucao.
- `rollback-notes.md` alerta que redrive pode duplicar efeitos.
- Nenhum `operation-result.json` deve ser criado.

## Escalacao

Encaminhar para aprovacao operacional quando o redrive envolver producao,
mensagens financeiras, eventos de cliente ou consumidores sem idempotencia
confirmada.
