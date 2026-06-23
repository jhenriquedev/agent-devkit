# baseline-predictive-model

## Objetivo
Treinar baseline preditivo binario auditavel e reportar regra de decisao com
metricas de treinamento, declarando limitacoes do metodo.

## Entradas
- `--source` (obrigatorio).
- `--target-column` (obrigatorio).
- `--feature-columns`: lista de features.
- `--test-size`: fracao de teste (default 0.2).
- `--output`: gravar modelo/resultado.

## Raciocinio
1. Confirme sha256, warnings; verifique class_balance.
2. Execute detect-data-leakage ANTES de confiar no baseline.
3. Treine com algoritmo threshold/heuristico baseline (auditavel, sem sklearn).
4. Reporte regra de decisao (threshold otimo), metricas de treino vs teste.
5. Se class_balance severo -> sinalize e priorize balanced_accuracy/F1 sobre
   accuracy.

## Rubrica de decisao
- Leakage detectado -> invalide baseline; nao reporte metricas ate correcao.
- class_balance severo + foco em accuracy -> exija metrica balanceada.
- Metricas de treino >> teste -> indicio de overfitting; declare.

## Saida
Regra de decisao (threshold), metricas (train vs test), class_balance,
aviso de leakage se aplicavel, limitacoes do baseline, bloco de rastreabilidade.

## Nao fazer
- Nao vender baseline como modelo de producao.
- Nao reportar accuracy isolada em base desbalanceada.
- Nao treinar sem checar leakage antes.
