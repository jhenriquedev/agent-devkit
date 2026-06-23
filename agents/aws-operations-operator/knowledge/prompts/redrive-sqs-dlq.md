# Prompt: Redrive SQS DLQ

## Objetivo
Gerar um PLANO de redrive de mensagens de uma DLQ para a fila destino
(`sqs start-message-move-task`). Operacao destrutiva: execucao real BLOQUEADA no MVP.

## Entradas esperadas
source_arn, destination_arn, environment (req).

## Passos de raciocinio
1. Montar o plano e marcar status `blocked-plan-only` (destructive: true).
2. Explicar o risco: redrive pode DUPLICAR processamento; exige idempotencia no
   consumidor antes de qualquer execucao manual.
3. Entregar rollback-notes alertando sobre duplicacao.

## Regras de decisao
- Mesmo que o usuario peca `--execute`, NAO executar. O runner forca execute=False.
- Recomendar verificacao de idempotencia e backup antes de uma execucao manual fora
  do agente.

## Formato de saida
Plano: source, destination, ambiente, status blocked-plan-only, alerta de duplicacao,
e o comando que seria executado manualmente. Caminho dos artefatos.

## NAO fazer
- Nao executar. Nao prometer rollback automatico (nao existe).
