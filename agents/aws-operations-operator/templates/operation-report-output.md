# AWS Operation Report

> Gerado dinamicamente por `report_renderer.render_operation_report(dry_run, result)`.
> Este template documenta o contrato de saida do artefato `operation-report.md`.

## Cabecalho

- **Operation**: id da operacao
- **Resource**: resource_id alvo
- **Environment**: ambiente
- **Region**: regiao AWS
- **Profile**: perfil AWS
- **Status**: status final (`planned` | `blocked-plan-only` | `executed`)
- **Executed**: `True` se operation-result.json existia; `False` se so planejada

## Secoes condicionais

### Account Validation (se executado)
JSON com `environment`, `account_id`, `arn`, `user_id`, `allowed_accounts`.

### Preflight (se executado)
Estado do recurso antes da mutacao (ex.: describe-services para ECS,
describe-auto-scaling-groups para ASG, describe-rule para EventBridge).

### Post Check (se executado)
Estado do recurso apos a mutacao; para Lambda: StatusCode, FunctionError,
ExecutedVersion, response_payload_hash.

### Result (se executado)
```json
{
  "returncode": 0,
  "stdout": "<saida resumida do AWS CLI>",
  "lambda_response": { "payload_hash": "...", "payload_bytes": 0, "payload_present": true }
}
```

Payload bruto nunca aparece — apenas hash sha256 + bytes.
