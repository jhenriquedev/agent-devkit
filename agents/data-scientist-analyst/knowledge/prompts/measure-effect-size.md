# measure-effect-size

## Objetivo
Calcular tamanho de efeito (Cohen's d ou equivalente) entre grupos e interpretar
sua magnitude pratica, complementando p-valor de teste de hipotese.

## Entradas
- `--source` (obrigatorio).
- `--group-column` (obrigatorio).
- `--group-a`, `--group-b`: valores dos grupos.
- `--metric-column` (obrigatorio).

## Raciocinio
1. Confirme sha256, warnings, n por grupo.
2. Calcule Cohen's d = (media_b - media_a) / desvio_pooled.
3. Classifique: |d| < 0.2 (negligivel), 0.2–0.5 (pequeno), 0.5–0.8 (medio),
   > 0.8 (grande).
4. Apresente interpretacao pratica alem da classificacao estatistica.
5. Combine com p-valor se disponivel: d grande + p alto -> amosta insuficiente.

## Rubrica de decisao
- d pequeno mesmo com p < alpha -> "diferenca estatisticamente significante mas
  praticamente negligivel".
- n pequeno por grupo -> d e impreciso; declare.
- validity_warnings presente -> destaque limitacao no calculo.

## Saida
Cohen's d, classificacao (negligivel/pequeno/medio/grande), interpretacao pratica,
n por grupo, limitations, bloco de rastreabilidade.

## Nao fazer
- Nao apresentar effect size sem classificacao e interpretacao.
- Nao ignorar n ao interpretar d.
- Nao confundir magnitude de efeito com causalidade.
