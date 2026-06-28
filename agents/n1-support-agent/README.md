# N1 Support Agent

Agente N1 para triagem operacional de cards Azure DevOps.

## Objetivo

Receber um projeto e numero de card Azure, ler o contexto completo do card,
executar o roteiro operacional N1, extrair entidades importantes, planejar ou
aplicar a tag `Analise N1`, planejar ou mover o card de coluna e gerar um
contrato fixo de saida com evidencias, checks, decisao e artefatos.

## Uso

```bash
agent run n1-support-agent execute-n1-card-runbook --project "$AZURE_DEVOPS_PROJECT" --card 7710
agent run n1-support-agent execute-n1-card-runbook --project "$AZURE_DEVOPS_PROJECT" --card 7710 --target-column "Em Analise N1"
agent run n1-support-agent execute-n1-card-runbook --project "$AZURE_DEVOPS_PROJECT" --card 7710 --target-column "Em Analise N1" --execute
agent run n1-support-agent route-customer-symptom --text "cliente nao consegue concluir cadastro" --format json
agent run n1-support-agent analyze-restrictive-base --cpf "123.456.789-09" --format json
agent run n1-support-agent analyze-bpo-proposal --proposal-number 123456 --format json
```

Sem `--execute`, o agente apenas le o card e planeja tags/movimentacao. Com
`--execute`, ele usa o `azure-devops-orchestrator` para escrever no card.

A capability `analyze-restrictive-base` executa consulta read-only via
`sqlserver-data-analyzer`, priorizando `DB_RESTRICTIVE_CONN_STRING` quando essa
variavel existir no `.env` local. O contrato retorna `hit`, `clear`, `skipped`
ou `unavailable`, sempre com CPF mascarado.

A capability `route-customer-symptom` usa o knowledge de suporte ao cliente para escolher
dominio, checks minimos e regras de negocio relevantes antes da decisao N1.

A capability `analyze-bpo-proposal` consulta evidencias de proposta por meio do
agente `bpo-analyser`. Ela deve ser usada quando o card trouxer CPF, proposta,
formalizacao, CCB, margem, convenio ou onboarding preso em analise. O resultado
normaliza status como `found`, `not_found`, `pending`, `rejected`,
`unavailable` ou `skipped`.

## Dependencias

- `azure-devops-orchestrator`: leitura, tags e movimentacao de card.
- `sqlserver-data-analyzer`: checks de base restritiva.
- `bpo-analyser`: proposta BPO, documentos anexados, formalizacao e situacao
  operacional externa.
- `aws-cloudwatch-log-analyzer` e `elasticsearch-log-analyzer`: checks de logs.
- `topdesk-orchestrator`: contexto do chamado quando houver referencia TOPdesk.

## Contrato de saida

A capability principal sempre gera um bloco `N1 Contract` com JSON contendo:

- `card`;
- `entities`;
- `symptomRoute`;
- `checks`;
- `evidenceLedger`;
- `businessRulesApplied`;
- `diagnosticGaps`;
- `qualityGate`;
- `decision`;
- `recommendedAction`;
- `azureActions`;
- `artifacts`;
- `audit`.
