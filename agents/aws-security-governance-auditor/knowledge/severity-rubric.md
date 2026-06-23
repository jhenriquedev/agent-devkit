# Rubrica de Severidade — AWS Security Governance Auditor

Esta rubrica é a fonte de verdade para classificação de achados. Os prompts das
capabilities a referenciam. O código em `auditors.py` a implementa deterministicamente.

## Tabela de Severidade (condição → severidade)

| Domínio | Condição (evidência) | Severidade | Status |
|---|---|---|---|
| IAM | Statement Allow Action=`*` E Resource=`*` | **critical** | confirmed |
| IAM | Permissão ampla por serviço (ex.: `iam:*`, `s3:*`) sem Condition | high | confirmed |
| IAM | Admin legado sem uso recente | medium | potential |
| Security Group | Ingress 0.0.0.0/0 ou ::/0 em porta 22 ou 3389 | **critical** | confirmed |
| Security Group | Ingress 0.0.0.0/0 ou ::/0 em outra porta | high | confirmed |
| S3 | Qualquer flag de PAB faltando (BlockPublicAcls, IgnorePublicAcls, BlockPublicPolicy, RestrictPublicBuckets) | high | confirmed |
| S3/Encryption | Sem metadado de encryption | medium | potential |
| Secrets | `RotationEnabled` ausente/false | medium | potential |
| CloudTrail | Nenhum trail presente | **critical** | confirmed |
| AWS Config | Nenhum configuration recorder | high | confirmed |
| Qualquer | Dado do domínio não coletado | (não é severidade — é LACUNA DE COLETA) | lacuna |

## Regras de elevação e não-rebaixamento

- **Elevação:** exposição pública + dado sensível na mesma superfície sobe um nível de severidade.
- **Não-rebaixamento:** ausência de evidência NUNCA resulta em "seguro". Use `status=potential` ou registre como LACUNA.
- **Níveis válidos:** `critical`, `high`, `medium`, `low`, `info`. Não use outros valores.

## Rubrica de Conformidade (quality_gates de `policies.yaml`)

Avaliar cada gate como PASS / FAIL / N-A por execução:

| Gate | Critério de PASS |
|---|---|
| `read_only_allowlist_enforced` | Nenhum comando fora de `ALLOWED_COMMANDS` foi tentado. |
| `findings_have_severity` | Todo finding tem `severity ∈ {critical,high,medium,low,info}`. |
| `findings_have_evidence` | Todo finding tem `evidence` não-vazio. |
| `remediation_is_plan_only` | `remediation-plan.md` não contém execução; `execution: unsupported`. |
| `secrets_redacted` | Nenhum secret value / access key / session token / policy cru / connection string na saída humana. |
