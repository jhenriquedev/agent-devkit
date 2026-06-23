# Capability: Auditar Exposição Pública (read-only)

## Objetivo
Visão consolidada de exposição à internet: Security Groups públicos + buckets S3
publicamente acessíveis (PAB incompleto).

## Raciocínio
1. Reusar a lógica de Security Groups.
2. Acrescentar achados S3 cujo id começa com "s3-public" (Public Access Block
   incompleto).
3. Priorizar superfícies que combinam exposição + dado sensível.

## Regras de decisão
- Herdar severidade de SG (seção 5.2) e de S3 PAB (seção 5.4).
- Combinação SG público + recurso de dado → tratar como high+ mesmo que isolados sejam medium.

## Saída
findings[] consolidados de exposição. Marcar LACUNA se PAB não foi coletado por bucket.

## NÃO faça
Não duplique achados já cobertos; não classifique como "exposto" sem CIDR público confirmado.
