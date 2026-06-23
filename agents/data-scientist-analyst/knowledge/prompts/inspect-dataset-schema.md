# inspect-dataset-schema

## Objetivo
Inspecionar e documentar o schema da base: tipos por coluna, nulos, unicos,
chaves provaveis — fixando rastreabilidade antes de qualquer analise.

## Entradas
- `--source` (obrigatorio): caminho do arquivo (CSV, JSON, JSONL, XLSX).
- `--sheet` (XLSX multi-aba): nome ou indice da aba.
- `--json-path` (JSON aninhado): caminho para a lista de registros.
- `--max-rows`, `--max-file-mb`: controles de custo.

## Raciocinio
1. Confirme carga: row_count vs original_row_count, truncated, warnings, sha256.
2. Se XLSX multi-aba sem --sheet ou JSON sem --json-path com 0/poucos registros:
   PARE e pergunte qual aba/lista usar.
3. Para cada coluna reporte: tipo inferido, % nulos, contagem de unicos,
   exemplos mascarados, indicador de chave provavel (unicidade >= 99%).
4. Marque explicitamente tipos inferidos como "inferencia heuristica" — nao sao
   tipos declarados pelo schema da fonte.

## Rubrica de decisao
- sha256 ausente -> resultado inutilizavel; bloqueie uso downstream.
- truncated=true -> schema derivado de amostra; declare isso.
- Coluna com 100% de nulos -> sinalize como candidata a remocao.
- Coluna unica e nao nula -> candidata a chave primaria.

## Saida
Tabela por coluna: nome, tipo_inferido, pct_nulos, qtd_unicos, exemplo_mascarado,
chave_provavel. Bloco "Rastreabilidade": fonte, sha256, row_count, truncado,
warnings.

## Nao fazer
- Nao exibir PII integral em exemplos.
- Nao declarar tipo como definitivo sem mencionar que e heuristico.
- Nao adivinhar aba/json-path.
