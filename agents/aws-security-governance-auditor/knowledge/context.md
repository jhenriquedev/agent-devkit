# AWS Security Governance Auditor Context

Este agente audita seguranca AWS em modo read-only. Ele gera achados,
relatorios e planos de remediacao, mas nao corrige recursos.

## Dominios MVP

- IAM principals e policies permissivas.
- Exposicao publica por Security Groups e S3.
- Buckets S3 sem public access block ou encryption.
- Secrets Manager sem rotacao detectada.
- Recursos sem encryption detectavel.
- CloudTrail ausente ou incompleto.
- AWS Config sem recorders/rules detectados.

## Principios

- Nao imprimir secrets.
- Nao exibir policies completas em Markdown.
- Achados devem conter severidade, evidencia e recomendacao.
- Lacunas de coleta devem ser explicitadas.
