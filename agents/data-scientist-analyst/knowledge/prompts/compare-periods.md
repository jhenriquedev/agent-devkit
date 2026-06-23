# compare-periods

## Objetivo
Comparar dois periodos temporais da metrica (delta absoluto, percentual, direcao)
com atencao ao tamanho das janelas e normalizacao.

## Entradas
- `--source` (obrigatorio).
- `--date-column`, `--metric-column` (obrigatorios).
- `--period-a-start`, `--period-a-end`, `--period-b-start`, `--period-b-end`:
  delimitadores das duas janelas.
- `--granularity`: agregacao (day/week/month).

## Raciocinio
1. Confirme sha256, warnings, coberturas dos dois periodos.
2. Calcule: soma/media por periodo, delta absoluto (B-A), variacao percentual
   ((B-A)/A * 100), direcao (crescimento/queda/estavel).
3. Verifique se os periodos tem o mesmo numero de dias/semanas; se diferentes,
   normalize ou avise sobre viés de tamanho de janela.
4. Reporte separadamente: fato observado vs hipotese de causa.

## Rubrica de decisao
- Janelas de tamanho diferente sem normalizacao -> aviso obrigatorio.
- Periodo com poucos pontos (< 7 para granularidade diaria) -> resultado fragil.
- truncated=true -> comparacao e de amostra; declare.

## Saida
Tabela (periodo, soma, media, n_pontos), delta absoluto, variacao_pct, direcao,
aviso de tamanho de janela se aplicavel, bloco de rastreabilidade.

## Nao fazer
- Nao comparar periodos de tamanho muito diferente sem normalizar ou avisar.
- Nao atribuir causa a variacao.
- Nao reportar percentual sem valor absoluto de referencia.
