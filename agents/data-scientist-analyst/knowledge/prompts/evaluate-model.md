# evaluate-model

## Objetivo
Avaliar baseline preditivo com metricas completas (accuracy, precision, recall,
F1, balanced_accuracy, matriz de confusao) e verificar class_balance e
evaluation_scope.

## Entradas
- `--source` (obrigatorio).
- `--target-column` (obrigatorio).
- `--feature-columns`: features usadas.
- `--test-size`: fracao de teste (default 0.2).

## Raciocinio
1. Confirme sha256, warnings, class_balance, evaluation_scope.
2. Calcule: accuracy, precision, recall, F1, balanced_accuracy, specificity,
   negative_predictive_value, matriz de confusao (tp, tn, fp, fn).
3. Se classes desbalanceadas: priorize balanced_accuracy e F1 sobre accuracy.
4. Verifique validity_warnings; se presente, bloqueie conclusao forte.
5. Reporte evaluation_scope: conjunto de teste, n, periodos se relevante.

## Rubrica de decisao
- class_balance severo + foco em accuracy -> exija metrica balanceada.
- validity_warnings -> nao aceite qualidade do modelo sem resolver avisos.
- test_rows < 30 -> avaliacao fragil; sinalize.

## Saida
Tabela de metricas, matriz de confusao, class_balance, evaluation_scope,
validity_warnings, interpretacao executiva, limitacoes, bloco de rastreabilidade.

## Nao fazer
- Nao reportar accuracy isolada em base desbalanceada.
- Nao aceitar modelo com leakage nao resolvido.
- Nao omitir matriz de confusao.
