# Capability: Auditar Encryption (read-only)

## Objetivo
Reunir achados de recursos sem encryption detectável (hoje: subset S3).

## Regras de decisão (rubrica)
- Recurso sem metadado de encryption → medium, status=potential.
- Dado em repouso sensível sem encryption → high.
- Ausência de coleta de encryption → LACUNA.

## Saída
findings[] category=encryption. Recomendar SSE-S3 ou KMS conforme o recurso.

## NÃO faça
Não conclua "criptografado" por ausência de evidência; não exponha key material.
