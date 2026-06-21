# Data Scientist Analyst

Agente para analise de dados tabulares, conciliacao de planilhas e geracao de
relatorios tecnicos ou executivos.

## Capacidades MVP

- `ingest-dataset`: inventaria arquivos CSV, JSON, JSONL, XLSX e diretorios.
- `inspect-dataset-schema`: infere schema, tipos e chaves provaveis.
- `profile-dataset`: gera perfil estatistico, qualidade e dados sensiveis.
- `detect-sensitive-data`: identifica CPF, CNPJ, e-mail, telefone e nomes.
- `run-exploratory-analysis`: consolida EDA com qualidade, outliers, correlacoes e segmentos.
- `detect-outliers`: identifica valores atipicos por IQR, z-score ou ambos.
- `analyze-correlation`: calcula correlacoes de Pearson entre colunas numericas.
- `segment-data`: agrupa dados por segmento e calcula metricas agregadas.
- `analyze-time-series`: agrega metricas por dia, semana ou mes.
- `compare-periods`: compara metricas entre dois intervalos.
- `analyze-cohorts`: acompanha cohorts por idade em dias desde a entrada.
- `detect-anomalies`: detecta picos e quedas por z-score em serie temporal.
- `forecast-series`: projeta proximos periodos por media movel baseline.
- `test-hypothesis`: testa diferenca de medias entre dois grupos.
- `calculate-confidence-intervals`: calcula intervalo de confianca para media.
- `calculate-sample-size`: estima amostra para duas proporcoes balanceadas.
- `measure-effect-size`: calcula Cohen's d entre dois grupos.
- `explain-statistical-result`: explica p-valor, alpha e tamanho de efeito.
- `prepare-modeling-dataset`: prepara contrato de modelagem com alvo, features e split.
- `baseline-predictive-model`: treina baseline explicavel por threshold numerico.
- `evaluate-model`: calcula metricas de classificacao e matriz de confusao.
- `explain-model-results`: explica driver principal, regra e limitacoes do baseline.
- `detect-data-leakage`: detecta colunas suspeitas de vazamento de alvo.
- `monitor-model-drift`: compara referencia e amostra atual por drift de medias.
- `reconcile-spreadsheets`: concilia duas bases por chave e tolerancias.
- `generate-reconciliation-report`: gera relatorio markdown de conciliacao.
- `generate-data-report`: gera relatorio markdown de perfil da base.
- `analyze-sql-source`: delega analises SQL para agentes de banco existentes.

## Exemplos

```bash
./ai-devkit run data-scientist-analyst profile-dataset --source dados.csv
./ai-devkit run data-scientist-analyst reconcile-spreadsheets \
  --left erp.csv --right banco.csv --key id --compare-columns amount,status \
  --numeric-tolerance 0.02
./ai-devkit run data-scientist-analyst generate-data-report \
  --source dados.csv --output docs/data-report.md
./ai-devkit run data-scientist-analyst run-exploratory-analysis \
  --source dados.csv --target-column converted --segment-column channel
./ai-devkit run data-scientist-analyst detect-outliers \
  --source dados.csv --columns amount --method iqr
./ai-devkit run data-scientist-analyst analyze-correlation \
  --source dados.csv --target-column score
./ai-devkit run data-scientist-analyst segment-data \
  --source dados.csv --segment-column status --metric-column amount
./ai-devkit run data-scientist-analyst analyze-time-series \
  --source dados.csv --date-column created_at --metric-column amount --granularity day
./ai-devkit run data-scientist-analyst compare-periods \
  --source dados.csv --date-column created_at --metric-column amount \
  --baseline-start 2026-01-01 --baseline-end 2026-01-15 \
  --comparison-start 2026-01-16 --comparison-end 2026-01-31
./ai-devkit run data-scientist-analyst analyze-cohorts \
  --source dados.csv --cohort-column signup_date --event-date-column event_date \
  --metric-column converted
./ai-devkit run data-scientist-analyst detect-anomalies \
  --source dados.csv --date-column created_at --metric-column amount --threshold 2
./ai-devkit run data-scientist-analyst forecast-series \
  --source dados.csv --date-column created_at --metric-column amount --periods 3 --window 3
./ai-devkit run data-scientist-analyst test-hypothesis \
  --source experimento.csv --test-type mean-difference --group-column variant \
  --group-a control --group-b treatment --metric-column revenue
./ai-devkit run data-scientist-analyst calculate-confidence-intervals \
  --source dados.csv --metric-column amount --confidence 0.95
./ai-devkit run data-scientist-analyst calculate-sample-size \
  --baseline-rate 0.5 --minimum-detectable-effect 0.1 --alpha 0.05 --power 0.8
./ai-devkit run data-scientist-analyst measure-effect-size \
  --source experimento.csv --group-column variant --group-a control \
  --group-b treatment --metric-column revenue
./ai-devkit run data-scientist-analyst explain-statistical-result \
  --p-value 0.01 --alpha 0.05 --effect-size 0.8
./ai-devkit run data-scientist-analyst prepare-modeling-dataset \
  --source base.csv --target-column converted --feature-columns score,income,channel
./ai-devkit run data-scientist-analyst baseline-predictive-model \
  --source base.csv --target-column converted --feature-columns score,income
./ai-devkit run data-scientist-analyst evaluate-model \
  --source base.csv --target-column converted --feature-columns score,income
./ai-devkit run data-scientist-analyst explain-model-results \
  --source base.csv --target-column converted --feature-columns score,income
./ai-devkit run data-scientist-analyst detect-data-leakage \
  --source base.csv --target-column converted
./ai-devkit run data-scientist-analyst monitor-model-drift \
  --reference-source treino.csv --source producao.csv --columns score,income
```
