# Prompt: Review Observability

## Objetivo
Avaliar cobertura de observabilidade: CloudWatch alarms, log groups, retention
e sinais operacionais ausentes.

## Entradas esperadas
- inventory.json (obrigatorio).

## Passos de raciocinio
1. Verifique presenca de alarms e log groups; cheque retention dos logs.
2. Cruze: compute sem alarm correspondente, log group sem retention definida.
3. Marque ausencia total de alarms como risco medio.

## Regras de decisao (rubrica)
- medium: nenhum alarm no inventario; logs criticos sem retention.
- info: retention generosa porem possivelmente custosa (apenas observar).
- gap: inventario nao coletou alarms/logs daquele servico => lacuna de dados.

## Formato de saida
- observability-review.md, observability-findings.json.

## Nao faca
- Nao confunda "nao coletado" com "nao existe". Declare a lacuna.
