# Capability: Gerar Relatório de Segurança (read-only)

## Objetivo
Consolidar os `*-audit.json` (exceto security-findings.json) num relatório humano.

## Raciocínio
1. Ler todos os findings dos audits do diretório.
2. Sumarizar contagem por severidade (critical→info).
3. Listar achados ordenados por criticidade, com evidence e recommendation.

## Regras de decisão / gates (policies.yaml)
- Todo achado deve ter severity e evidence; sinalizar os que não tiverem.
- Garantir que nenhum secret/policy cru apareça (redação).
- Incluir seção de LACUNAS DE COLETA quando existirem.

## Saída
security-report.md + security-findings.json.

## NÃO faça
Não invente achados ausentes; não omita lacunas; não imprima dados sensíveis.
