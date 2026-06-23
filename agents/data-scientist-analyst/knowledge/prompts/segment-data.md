# segment-data

## Objetivo
Agregar e comparar a base por segmentos categoricos, destacando distribuicoes,
participacoes e segmentos com volume insuficiente para conclusao.

## Entradas
- `--source` (obrigatorio).
- `--segment-column` (obrigatorio): coluna categorica de segmentacao.
- `--metric-column`: metrica numerica a agregar por segmento.
- `--max-rows`, `--max-file-mb`: controles.

## Raciocinio
1. Confirme sha256, warnings, truncated.
2. Agrupe por segmento; calcule n, %, media/mediana/soma da metrica se presente.
3. Ordene por participacao (decrescente); destaque os 3 maiores e os menores.
4. Classifique segmentos com n < 30 como "insuficiente para conclusao isolada".
5. Reporte distribuicao e hipoteses de diferenca entre segmentos — nunca causas.

## Rubrica de decisao
- Segmento com n < 30 -> sinalize; nao extraia conclusao isolada.
- truncated=true -> participacoes sao "estimadas" (amostra parcial).
- Coluna de segmento com muitos valores unicos (alta cardinalidade) -> avise
  sobre fragmentacao.

## Saida
Tabela por segmento (n, %, media_metrica, mediana_metrica), classificacao de
tamanho, hipoteses a validar, bloco de rastreabilidade.

## Nao fazer
- Nao concluir diferenca causal entre segmentos; use hipotese.
- Nao ignorar segmentos minusculos sem sinalizar.
- Nao gerar artefato sem --output.
