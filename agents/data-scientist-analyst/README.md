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
- `run-data-pipeline`: executa pipeline local com perfil, EDA e relatorio versionado.

## Exemplos

```bash
agent run data-scientist-analyst profile-dataset --source dados.csv
agent run data-scientist-analyst reconcile-spreadsheets \
  --left erp.csv --right banco.csv --key id --compare-columns amount,status \
  --numeric-tolerance 0.02
agent run data-scientist-analyst generate-data-report \
  --source dados.csv --output docs/data-report.md
agent run data-scientist-analyst run-data-pipeline \
  --source dados.csv --target-column converted --segment-column channel \
  --output docs/pipeline
agent run data-scientist-analyst run-exploratory-analysis \
  --source dados.csv --target-column converted --segment-column channel
agent run data-scientist-analyst profile-dataset \
  --source dados.xlsx --sheet Base --max-rows 1000
agent run data-scientist-analyst profile-dataset \
  --source nested.json --json-path payload.items --sample-rows 25
agent run data-scientist-analyst detect-outliers \
  --source dados.csv --columns amount --method iqr
agent run data-scientist-analyst analyze-correlation \
  --source dados.csv --target-column score
agent run data-scientist-analyst segment-data \
  --source dados.csv --segment-column status --metric-column amount
agent run data-scientist-analyst analyze-time-series \
  --source dados.csv --date-column created_at --metric-column amount --granularity day
agent run data-scientist-analyst compare-periods \
  --source dados.csv --date-column created_at --metric-column amount \
  --baseline-start 2026-01-01 --baseline-end 2026-01-15 \
  --comparison-start 2026-01-16 --comparison-end 2026-01-31
agent run data-scientist-analyst analyze-cohorts \
  --source dados.csv --cohort-column signup_date --event-date-column event_date \
  --metric-column converted
agent run data-scientist-analyst detect-anomalies \
  --source dados.csv --date-column created_at --metric-column amount --threshold 2
agent run data-scientist-analyst forecast-series \
  --source dados.csv --date-column created_at --metric-column amount --periods 3 --window 3
agent run data-scientist-analyst test-hypothesis \
  --source experimento.csv --test-type mean-difference --group-column variant \
  --group-a control --group-b treatment --metric-column revenue
agent run data-scientist-analyst calculate-confidence-intervals \
  --source dados.csv --metric-column amount --confidence 0.95
agent run data-scientist-analyst calculate-sample-size \
  --baseline-rate 0.5 --minimum-detectable-effect 0.1 --alpha 0.05 --power 0.8
agent run data-scientist-analyst measure-effect-size \
  --source experimento.csv --group-column variant --group-a control \
  --group-b treatment --metric-column revenue
agent run data-scientist-analyst explain-statistical-result \
  --p-value 0.01 --alpha 0.05 --effect-size 0.8
agent run data-scientist-analyst prepare-modeling-dataset \
  --source base.csv --target-column converted --feature-columns score,income,channel
agent run data-scientist-analyst baseline-predictive-model \
  --source base.csv --target-column converted --feature-columns score,income
agent run data-scientist-analyst evaluate-model \
  --source base.csv --target-column converted --feature-columns score,income
agent run data-scientist-analyst explain-model-results \
  --source base.csv --target-column converted --feature-columns score,income
agent run data-scientist-analyst detect-data-leakage \
  --source base.csv --target-column converted
agent run data-scientist-analyst monitor-model-drift \
  --reference-source treino.csv --source producao.csv --columns score,income
```

## Operacao

Use `--max-file-mb`, `--max-rows` e `--sample-rows` para controlar custo,
memoria e tempo em bases grandes. Para XLSX, use `--sheet` quando a aba correta
nao for a primeira. Para JSON aninhado, use `--json-path` apontando para a lista
de registros que deve virar dataset tabular.

Os fluxos recomendados para uso real sao:

- `profile-dataset` antes de qualquer conclusao, para registrar hash, tamanho,
  truncamento, qualidade e dados sensiveis.
- `run-data-pipeline` quando precisar de um pacote reprodutivel com
  `manifest.json`, perfil, EDA e relatorio Markdown.
- `analyze-sql-source --dataset-output` quando a consulta delegada para banco
  precisar virar artifact tabular reutilizavel por outras capabilities.
- `generate-data-report` como base Markdown pronta para revisao tecnica e
  conversao posterior para PDF.

Quality gates operacionais:

- revisar `dataset.warnings`, `dataset.truncated` e `quality.quality_score`;
- tratar `validity_warnings` como bloqueio para conclusoes fortes;
- revisar `sensitive_data.has_sensitive_data` antes de compartilhar artefatos;
- preferir metricas balanceadas quando houver desbalanceamento de classes.

Troubleshooting rapido:

- CSV carregado como uma coluna: informe o delimitador na origem ou normalize o
  arquivo; o leitor tenta fallback automatico, mas nao corrige arquivos ambiguos.
- XLSX com aba incorreta: reexecute com `--sheet`.
- JSON sem registros: reexecute com `--json-path` ate uma lista de objetos.
- Modelo baseline instavel: reduza conclusoes, revise `class_balance` e aumente
  a amostra.

Contratos versionados ficam em `knowledge/contracts/`. O checklist operacional
fica em `knowledge/health-checklist.md` e o runbook em
`knowledge/operational-runbook.md`.
