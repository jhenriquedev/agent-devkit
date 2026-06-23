# Capability: Auditar IAM Principals (read-only)

## Objetivo
Identificar policies IAM excessivamente permissivas — em especial wildcard admin
(Allow Action=* Resource=*) — e principals de risco.

## Entradas esperadas
- snapshot.iam.{users, roles, policies}. Se `policies` estiver vazio, isso é uma
  LACUNA DE COLETA, não evidência de ausência de risco.

## Raciocínio
1. Para cada policy, inspecionar Statements com Effect=Allow.
2. Marcar achado crítico quando existir Statement com Action `*` E Resource `*`.
3. Registrar users com acesso console nunca usado / roles administrativas como
   risco potencial (status=potential).

## Regras de decisão (rubrica)
- Wildcard admin (Action=* e Resource=*) → severity=critical, status=confirmed.
- Permissão ampla por serviço (ex.: iam:*, s3:*) sem condição → high.
- Acesso administrativo legado sem uso recente → medium, status=potential.
- Se `policies` vazio → emitir item de LACUNA ("IAM policies não coletadas").

## Saída
findings[] com id, severity, category=iam, resource_type, resource_id, title,
evidence, recommendation, status. NUNCA incluir o documento de policy cru.

## NÃO faça
Não imprima policy documents; não conclua "IAM seguro" se policies não foram
coletadas; não proponha alteração executável.
