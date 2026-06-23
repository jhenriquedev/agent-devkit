# analyze-cohorts

## Objetivo
Segmentar e comparar cohorts (grupos definidos por data/evento de entrada)
ao longo do tempo, medindo retencao, atividade ou metrica por cohort.

## Entradas
- `--source` (obrigatorio).
- `--cohort-column` (obrigatorio): coluna que identifica o cohort (ex.: mes de
  cadastro).
- `--event-date-column`: data do evento a medir (ex.: ultima atividade).
- `--metric-column`: metrica numerica por cohort.
- `--granularity`: periodos de analise.

## Raciocinio
1. Confirme sha256, warnings, cobertura temporal dos cohorts.
2. Agrupe por cohort; calcule n, metrica_media e periodos de vida observados.
3. Distinga cohorts maduros (observados por >= 3 periodos) de cohorts jovens.
4. Sinalize cohort com n < 30 como "insuficiente para conclusao isolada".

## Rubrica de decisao
- Cohort jovem (< 3 periodos observados) -> resultado indicativo apenas.
- n < 30 por cohort -> nao extrapole conclusao.
- truncated=true -> cohorts podem estar incompletos; declare.

## Saida
Tabela por cohort (n, media_metrica, n_periodos_observados, maturidade),
tendencia entre cohorts, limitacoes, bloco de rastreabilidade.

## Nao fazer
- Nao comparar cohorts de maturidade muito diferente sem sinalizar.
- Nao atribuir causa a diferenca entre cohorts.
- Nao ignorar cohorts com n pequeno.
