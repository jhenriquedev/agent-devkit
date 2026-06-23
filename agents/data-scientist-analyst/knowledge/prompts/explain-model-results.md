# explain-model-results

## Objetivo
Explicar a regra de decisao do baseline preditivo e seus drivers, separando
importancia preditiva de causalidade.

## Entradas
- `--source` (obrigatorio).
- `--target-column` (obrigatorio).
- `--feature-columns`: features a explicar.

## Raciocinio
1. Confirme sha256, warnings, evaluation_scope disponivel.
2. Liste features por importancia relativa (se disponivel no baseline).
3. Para cada driver: apresente como preditor, nao como causa.
4. Identifique features surpresa (alta importancia inesperada) como possiveis
   sinais de leakage.
5. Liste limitacoes: baseline nao captura interacoes complexas.

## Rubrica de decisao
- Feature de alta importancia com nome suspeito -> verifique leakage.
- Importancia uniforme entre todas as features -> modelo sem discriminacao; sinalize.
- Resultado sem evaluation_scope -> declare falta de contexto de avaliacao.

## Saida
Ranking de drivers (feature, importancia_relativa, interpretacao), aviso de
possiveis leakage, limitacoes do baseline, traducao executiva, bloco de
rastreabilidade.

## Nao fazer
- Nao confundir importancia preditiva com causalidade.
- Nao apresentar explicacao sem ressalvas do metodo baseline.
- Nao ignorar features com importancia zero (sinal de problema).
