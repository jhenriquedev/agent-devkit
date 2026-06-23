# Prompt: estimate-table-size

## OBJETIVO
Dimensionar tabelas por número de linhas e espaço em disco (KB total/usado)
para priorizar análises e alertar sobre custo de scan.

## ENTRADAS
- `schema` (opcional): filtrar por schema.
- `limit` (opcional, default 100).

## RACIOCÍNIO (passos)
1. Execute a capability `estimate-table-size`.
2. Leia `tables[]` (campos: `table_schema`, `table_name`, `row_count`,
   `total_kb`, `used_kb`).
3. Ordene por tamanho; destaque as maiores.

## RUBRICA / REGRAS DE DECISÃO
- Tabelas grandes (> 1M linhas ou > 1 GB) → avisar custo de `sample-table`
  sem filtro; recomendar `profile-table` (usa agregações) em vez de
  `run-readonly-query` sem WHERE.
- Tabelas pequenas → podem ser tabelas de referência/lookup.

## SAÍDA
Tabela ordenada por `total_kb` descrescente + alertas para tabelas grandes.

## NÃO FAÇA
- Não sugira scan sem filtro em tabelas grandes.
- Não confundir `total_kb` (alocado) com `used_kb` (ocupado).
