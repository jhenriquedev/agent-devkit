# Prompt: Purge SQS Queue Plan

## Objetivo
Gerar um PLANO de purge de uma fila SQS (`sqs purge-queue`). Operacao destrutiva e
irreversivel: execucao real BLOQUEADA no MVP.

## Entradas esperadas
queue_url, environment (req).

## Passos de raciocinio
1. Montar plano, status `blocked-plan-only` (destructive: true).
2. Deixar EXPLICITO: purge apaga TODAS as mensagens, sem rollback.
3. Entregar rollback-notes orientando backup/reprocessamento antes de qualquer
   execucao manual.

## Regras de decisao
- NUNCA executar, mesmo com `--execute`.
- Exigir mentalmente confirmacao de que nao ha consumidor que perderia dados.

## Formato de saida
Plano: queue_url, ambiente, status blocked-plan-only, aviso de perda total de
mensagens, comando manual. Caminho dos artefatos.

## NAO fazer
- Nao executar. Nao minimizar o risco de perda de dados.
