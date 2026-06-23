# forecast-series

## Objetivo
Projetar valores futuros da serie temporal por media movel baseline,
declarando explicitamente que e uma aproximacao sem modelagem de sazonalidade.

## Entradas
- `--source` (obrigatorio).
- `--date-column`, `--metric-column` (obrigatorios).
- `--periods`: numero de periodos a projetar.
- `--window`: janela da media movel (default: 3).
- `--granularity`: agregacao.

## Raciocinio
1. Confirme sha256, warnings, n_periodos historicos.
2. Calcule media movel com janela configurada; projete `periods` passos.
3. Se n_historicos < 2*window -> declare "projecao fragil por serie curta".
4. Declare: "media movel baseline SEM modelagem de sazonalidade, tendencia linear
   ou eventos futuros".
5. Apresente intervalo indicativo (nao estatistico) se disponivel.

## Rubrica de decisao
- n_historicos < 2*window -> rebaixe para "indicativo; nao use como compromisso".
- truncated=true -> historico e parcial; declare impacto na projecao.
- Sazonalidade esperada -> avise que o metodo nao a captura.

## Saida
Tabela historica (ultimos N pontos) + projecao (data_projetada, valor_previsto),
declaracao de metodologia e limitacoes, bloco de rastreabilidade.

## Nao fazer
- Nao prometer sazonalidade ou ajuste de tendencia complexo.
- Nao apresentar projecao como compromisso ou meta; e baseline indicativo.
- Nao projetar sem declarar limitacoes do metodo.
