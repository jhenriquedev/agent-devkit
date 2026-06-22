# AWS CloudWatch Log Analyzer

Agente especialista para analisar logs de servicos no AWS CloudWatch Logs.

## Objetivo

Fornecer uma superficie padronizada para agentes como Codex consultarem logs,
identificarem erros, rastrearem requests, agruparem padroes e gerarem relatorios
operacionais sem montar comandos AWS manualmente.

## Regra de idioma

Todo codigo e identificadores tecnicos ficam em ingles. A documentacao humana
fica em portugues.

## Capabilities

```bash
./ai-devkit run aws-cloudwatch-log-analyzer list-log-groups --region us-east-1 --log-group-prefix "/aws/elasticbeanstalk/"
./ai-devkit run aws-cloudwatch-log-analyzer search-log-events --region us-east-1 --log-group "/aws/example" --start-time "2026-06-21T10:00:00-03:00" --end-time "2026-06-21T11:00:00-03:00"
./ai-devkit run aws-cloudwatch-log-analyzer analyze-service-error --region us-east-1 --service mcc-api --environment prd --log-group "/aws/example" --start-time "2026-06-21T10:00:00-03:00" --end-time "2026-06-21T11:00:00-03:00"
./ai-devkit run aws-cloudwatch-log-analyzer trace-request --region us-east-1 --log-group "/aws/example" --start-time "2026-06-21T10:00:00-03:00" --end-time "2026-06-21T11:00:00-03:00" --identifier "request-id"
./ai-devkit run aws-cloudwatch-log-analyzer detect-error-patterns --region us-east-1 --log-group "/aws/example" --start-time "2026-06-21T10:00:00-03:00" --end-time "2026-06-21T11:00:00-03:00"
./ai-devkit run aws-cloudwatch-log-analyzer extract-log-samples --region us-east-1 --log-group "/aws/example" --start-time "2026-06-21T10:00:00-03:00" --end-time "2026-06-21T11:00:00-03:00"
./ai-devkit run aws-cloudwatch-log-analyzer generate-incident-report --region us-east-1 --service mcc-api --environment prd --log-group "/aws/example" --start-time "2026-06-21T10:00:00-03:00" --end-time "2026-06-21T11:00:00-03:00"
./ai-devkit run aws-cloudwatch-log-analyzer correlate-azure-card-logs --azure-project "Sustentação" --work-item-id 7710 --region us-east-1 --log-group "/aws/example" --start-time "2026-06-21T10:00:00-03:00" --end-time "2026-06-21T11:00:00-03:00"
./ai-devkit run aws-cloudwatch-log-analyzer list-log-streams --region us-east-1 --log-group "/aws/example" --log-stream-prefix "app/"
./ai-devkit run aws-cloudwatch-log-analyzer run-insights-query --region us-east-1 --log-group "/aws/example" --start-time "2026-06-21T10:00:00-03:00" --end-time "2026-06-21T11:00:00-03:00" --query "fields @timestamp, @message | sort @timestamp desc | limit 20"
./ai-devkit run aws-cloudwatch-log-analyzer run-insights-query --region us-east-1 --query-id "query-id-retornado"
```

## Infra

A integracao fica em `infra/integrations/aws-cloudwatch/` e usa AWS CLI via
subprocess. Credenciais seguem o credential chain padrao da AWS (`AWS_PROFILE`,
SSO, env vars ou configuracao local).

## Guardrails

- Consultas de eventos exigem `--region`, `--log-group`, `--start-time` e
  `--end-time`.
- Capabilities sao read-only.
- Logs podem conter dados sensiveis; respostas humanas devem privilegiar resumo
  e amostras controladas.
- `correlate-azure-card-logs` nao le Azure DevOps diretamente e nao escreve
  comentarios; ela correlaciona dados de card fornecidos por argumento ou
  fixture com eventos CloudWatch.
