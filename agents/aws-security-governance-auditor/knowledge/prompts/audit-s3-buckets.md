# Capability: Auditar Buckets S3 (read-only)

## Objetivo
Verificar Public Access Block (PAB) completo e presença de encryption por bucket.

## Entradas esperadas
- snapshot.s3.buckets[] com Name, PublicAccessBlock{4 flags}, Encryption.
  Se vierem só com Name, isso é LACUNA DE COLETA (PAB/encryption não buscados).

## Regras de decisão (rubrica)
- Faltando qualquer flag de PAB (BlockPublicAcls, IgnorePublicAcls,
  BlockPublicPolicy, RestrictPublicBuckets) → high, category=public-exposure,
  status=confirmed.
- Sem metadado de encryption → medium, category=encryption, status=potential.
- PAB ausente E encryption ausente no mesmo bucket → tratar PAB como prioridade.

## Saída
findings[] resource_type=s3-bucket. Para cada bucket sem dado coletado, emitir LACUNA.

## NÃO faça
Não afirme "encryption ausente" se o dado de encryption não foi coletado — use status/LACUNA.
