# Prompt: Correlate Azure Card Logs

## Objetivo

Correlacionar dados fornecidos de um card Azure DevOps com eventos CloudWatch
para apoiar triagem de sustentacao.

## Entradas

- `azure_project` e `work_item_id`: identificadores do card.
- `region`, `log_group`, `start_time`, `end_time`: escopo dos logs.
- `fixture`: dados de card e logs fornecidos para analise local.
- `include_comment_draft`: gera texto sugerido sem escrever no Azure DevOps.

## Regras

- Esta capability nao le Azure DevOps diretamente; usa card informado ou fixture.
- Nao escrever comentario, status ou campo no Azure DevOps.
- Separar dados do card de fatos observados nos logs.
- Nao assumir log group se ele nao foi informado ou extraido com evidencia.
- Apontar validacoes posteriores antes de conclusoes definitivas.

## Saida

- Mostre dados do card, escopo CloudWatch, evidencias e analise.
- Inclua comentario sugerido apenas quando solicitado.
- Declare explicitamente que nenhuma escrita foi executada.
- Informe lacunas quando o card foi parcial ou veio de fixture.

## Nao faca

- Nao consultar ou alterar Azure DevOps nesta capability.
- Nao tratar fixture como dado live.
- Nao comentar conclusao definitiva sem validacao humana.
