# AWS CloudWatch Integration

Integracao local com AWS CloudWatch Logs.

## Objetivo

Expor um repository Python sem dependencias externas, usando AWS CLI via
subprocess, para capabilities do agente consultarem logs.

## Execucao local

```bash
python agents/aws-cloudwatch-log-analyzer/infra/integrations/aws-cloudwatch/cli.py list-log-groups --region us-east-1
python agents/aws-cloudwatch-log-analyzer/infra/integrations/aws-cloudwatch/cli.py filter-log-events --region us-east-1 --log-group "/aws/example" --start-time "2026-06-21T10:00:00-03:00" --end-time "2026-06-21T11:00:00-03:00"
```

## Credenciais

Use o credential chain padrao da AWS: `AWS_PROFILE`, AWS SSO, env vars ou
configuracao local.
