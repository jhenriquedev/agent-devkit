# Health Checklist

## Checagens antes de usar em decisao

- A fonte tem `sha256` registrado no resultado.
- `dataset.truncated` e `dataset.warnings` foram revisados.
- `sensitive_data.has_sensitive_data` foi considerado antes de compartilhar artifacts.
- Capabilities estatisticas possuem `assumptions`, `validity_warnings` e `limitations`.
- Modelagem possui `evaluation_scope`, `class_balance`, `test_metrics` e `validity_warnings`.
- Pipelines possuem `manifest.json` com `cache_key`.

## Sinais de alerta

- Amostra pequena ou truncada usada para conclusao executiva.
- Classes muito desbalanceadas com foco apenas em `accuracy`.
- Serie temporal curta avaliada por z-score.
- JSON aninhado sem `--json-path` explicito.
- XLSX multi-aba sem `--sheet` explicito.
- Resultado SQL retornado como texto em vez de tabular JSON.

## Riscos residuais

- O agente ainda usa algoritmos baseline sem `pandas`, `scipy` ou `sklearn`.
- Testes estatisticos usam aproximacoes normais.
- Forecast por media movel nao modela sazonalidade.
- PII e inferencia de tipos usam heuristicas.
- Bases muito grandes ainda exigem controles de leitura e amostragem.

## Acoes recomendadas

- Para bases grandes, comece com `--max-rows` e aumente progressivamente.
- Para resultados compartilhaveis, use `run-data-pipeline` e envie o manifest.
- Para SQL, prefira `--dataset-output` e analise o artifact tabular gerado.
- Para decisao operacional, valide resultados com especialista de dados antes de automatizar acao.
