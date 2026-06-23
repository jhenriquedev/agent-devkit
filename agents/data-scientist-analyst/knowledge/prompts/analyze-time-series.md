# analyze-time-series

## Objetivo
Agregar e interpretar a serie temporal (tendencia, sazonalidade indicativa,
variacao) sem atribuir causa, declarando limitacoes de series curtas.

## Entradas
- `--source` (obrigatorio).
- `--date-column` (obrigatorio): coluna de data/datetime.
- `--metric-column` (obrigatorio): coluna numerica a agregar.
- `--granularity {day|week|month}` (default: day).
- `--max-rows`, `--max-file-mb`: controles.

## Raciocinio
1. Confirme sha256, warnings, truncated, e cobertura temporal (data_min, data_max,
   n_periodos).
2. Identifique tendencia (crescimento/queda/estavel) e picos/vales relevantes.
3. Distinga anomalia OBSERVADA (desvio mensuravel) de causa PROVAVEL (hipotese
   externa).
4. Se n_periodos < 2 ciclos relevantes -> declare "serie curta; resultados
   indicativos".

## Rubrica de decisao
- Serie com < ~14 pontos diarios ou < 3 meses -> rebaixe conclusoes a
  "indicativo".
- truncated=true -> serie e parcial; declare.
- Pico/queda extremo -> reporte como anomalia observada; nao atribua causa.

## Saida
Tabela agregada por periodo (data, valor, variacao_pct), leitura de tendencia,
anomalias observadas (marcadas), limitacoes do metodo, bloco de rastreabilidade.

## Nao fazer
- Nao prometer deteccao de sazonalidade (media movel nao modela sazonalidade).
- Nao atribuir causa a anomalia sem evidencia externa.
- Nao usar serie truncada para forecast sem aviso.
