# Incident Report

## Objetivo

Gerar relatorio operacional de um conjunto de incidentes TOPdesk.

## Entradas

- `query`, `status`, `operator_group`, `limit`.
- `fixture` para execucao offline.

## Raciocinio

1. Liste incidentes dentro do escopo solicitado.
2. Agregue por status e prioridade.
3. Destaque chamados sem grupo operador.
4. Aponte riscos operacionais como inferencia, nao fato.
5. Preserve o limite da consulta.

## Rubrica

- Contagens sao fatos do retorno carregado.
- Risco operacional e inferencia.
- Relatorio nao autoriza escrita.

## Saida

Total, distribuicao por status, distribuicao por prioridade e lista sem grupo.

## Nao faca

Nao alterar chamados. Nao tratar amostra como universo completo. Nao expor payload
sensivel.
