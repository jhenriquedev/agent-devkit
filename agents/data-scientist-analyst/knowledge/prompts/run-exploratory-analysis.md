# run-exploratory-analysis

## Objetivo
Consolidar evidencias exploratorias de qualidade, outliers, correlacoes e
segmentos da base, separando achados de hipoteses.

## Entradas
- `--source` (obrigatorio).
- `--target-column`: coluna alvo para analise focada.
- `--columns`: lista de colunas a incluir.
- `--max-rows`, `--max-file-mb`: controles de leitura.

## Raciocinio
1. Garanta profile previo (sha256, warnings) — rode profile-dataset se nao
   disponivel.
2. Inspecione distribuicoes: media, mediana, desvio, skewness, outliers evidentes.
3. Analise correlacoes lineares entre numericas; sinalize pares com |r| alto.
4. Identifique segmentos categoricos dominantes e minusculos.
5. Consolide achados como "Evidencia" e hipoteses como "Hipotese a validar".

## Rubrica de decisao
- sha256 ausente -> nao prossiga sem rastreabilidade.
- truncated=true -> declare "amostra parcial" em todo achado.
- Correlacao alta -> hipotese, nunca causa: declare explicitamente.
- Segmento com n < 30 -> "insuficiente para conclusao isolada".

## Saida
Evidencias (lista numerada) > Hipoteses (lista numerada) > Riscos de qualidade.
Bloco de rastreabilidade ao final.

## Nao fazer
- Nao apresentar correlacao como causalidade.
- Nao concluir sobre segmentos minusculos.
- Nao gerar artefato sem --output.
