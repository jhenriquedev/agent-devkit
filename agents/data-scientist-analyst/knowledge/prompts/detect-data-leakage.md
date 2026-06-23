# detect-data-leakage

## Objetivo
Identificar possiveis vazamentos de dados (leakage) antes de confiar em metricas
do modelo: colunas que copiam ou derivam do alvo, ou eventos pos-decisao.

## Entradas
- `--source` (obrigatorio).
- `--target-column` (obrigatorio).
- `--feature-columns`: features a verificar.

## Raciocinio
1. Confirme sha256, warnings, colunas presentes.
2. Verifique: correlacao direta coluna-alvo >= 0.99, nomes suspeitos (sufixo
   _result, _label, _outcome similar ao alvo), colunas com valores identicos ao
   alvo.
3. Classifique: "leakage confirmado" (correlacao quase perfeita) vs "suspeita"
   (nome ou dominio suspeito).
4. Recomende remocao antes de treinar.

## Rubrica de decisao
- Leakage confirmado -> invalide baseline ate correcao; nao reporte metricas.
- Suspeita -> sinalize; deixe decisao ao analista.
- Ausencia de leakage detectado com base truncada -> declare limitacao.

## Saida
Lista de colunas suspeitas (coluna, tipo_leakage, correlacao_com_alvo,
classificacao), recomendacao, bloco de rastreabilidade.

## Nao fazer
- Nao treinar baseline com leakage confirmado sem avisar.
- Nao declarar "sem leakage" em base truncada sem ressalva.
- Nao ignorar nomes de colunas como sinal heuristico.
