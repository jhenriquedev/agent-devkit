# prepare-modeling-dataset

## Objetivo
Preparar dataset para modelagem preditiva baseline: definir alvo binario, features,
split deterministico e sinalizar riscos de leakage antes de qualquer treinamento.

## Entradas
- `--source` (obrigatorio).
- `--target-column` (obrigatorio): coluna alvo binaria.
- `--feature-columns`: lista de features (default: todas exceto alvo).
- `--test-size`: fracao de teste (default 0.2).
- `--output`: gravar dataset preparado.

## Raciocinio
1. Confirme sha256, warnings, row_count.
2. Valide que alvo e binario; informe distribuicao das classes (class_balance).
3. Identifique features com risco de leakage: colunas com nome sugestivo de
   evento pos-alvo ou copia direta do alvo.
4. Reporte split deterministico (train_rows, test_rows, test_size).
5. Sinalize class_balance; se severo (< 10% da classe minoritaria) -> recomende
   metrica balanceada.

## Rubrica de decisao
- Alvo nao binario -> bloqueie; nao e suportado pelo baseline.
- Leakage suspeito -> sinalize antes de prosseguir para baseline.
- class_balance severo -> declare e recomende balanced_accuracy/F1.

## Saida
Resumo do dataset preparado: alvo, features usadas, class_balance, split,
riscos de leakage identificados, recomendacoes, bloco de rastreabilidade.

## Nao fazer
- Nao treinar modelo sem verificar leakage antes.
- Nao ignorar class_balance ao recomendar metrica de avaliacao.
- Nao produzir artefato sem --output.
