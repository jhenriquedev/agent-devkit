# Capability: Auditar Uso de Secrets (read-only, metadados apenas)

## Objetivo
Sinalizar secrets sem rotação detectada — SEM ler valores secretos.

## Regras de decisão (rubrica)
- RotationEnabled ausente/false → medium, category=secrets, status=potential.
- Secret com rotação ausente E idade alta/última rotação antiga → high.
- Se metadados de rotação não foram coletados → LACUNA, não achado.

## Saída
findings[] resource_type=secret, evidence citando o Name/ARN (nunca o valor).

## NÃO faça
NUNCA chame get-secret-value nem imprima qualquer material secreto. Apenas metadados.
