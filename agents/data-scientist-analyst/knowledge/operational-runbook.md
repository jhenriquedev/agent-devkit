# Operational Runbook

## Objetivo

Operar o `data-scientist-analyst` de forma previsivel para analises locais,
pipelines reproduziveis e troubleshooting de fontes tabulares.

## Quality gates

Execute antes de liberar mudancas no agente:

```bash
python3 -m unittest agents/data-scientist-analyst/tests/test_runners.py
python3 -m py_compile agents/data-scientist-analyst/infra/integrations/file-dataset/*.py agents/data-scientist-analyst/capabilities/_shared/runner_support.py
./ai-devkit --json capabilities data-scientist-analyst
```

Smoke tests recomendados:

```bash
./ai-devkit --json run data-scientist-analyst profile-dataset --source dados.csv --max-rows 1000
./ai-devkit --json run data-scientist-analyst run-data-pipeline --source dados.csv --output docs/pipeline
./ai-devkit --json run data-scientist-analyst evaluate-model --source base.csv --target-column converted --feature-columns score --test-size 0.3
```

## Limites operacionais

- Use `--max-file-mb` para evitar leitura acidental de arquivos grandes.
- Use `--max-rows` para inspecao inicial de bases extensas.
- Use `--sample-rows` quando precisar amostra deterministica distribuida.
- Use `--sheet` em XLSX multi-aba para evitar analisar a primeira aba errada.
- Use `--json-path` em JSON aninhado para apontar a lista de registros.

## Troubleshooting

- `source not found`: confira caminho absoluto ou relativo ao root do repo.
- `unsupported dataset format`: converta para CSV, JSON, JSONL ou XLSX.
- `xlsx sheet not found`: liste abas no arquivo e informe `--sheet`.
- `json path segment not found`: revise o caminho pontuado, por exemplo `payload.items`.
- `baseline classification requires exactly two target classes`: confirme alvo binario e split com duas classes no treino.
- `database result is not tabular JSON`: use capability SQL que retorne `rows` e `columns`, ou salve a query como CSV antes da analise.

## Artifacts

- `generate-data-report` grava markdown canonico para leitura humana e futura conversao PDF.
- `run-data-pipeline` grava `manifest.json`, `profile.json`, `exploratory.json` e `data-report.md`.
- `analyze-sql-source --dataset-output` grava dataset JSON reutilizavel quando o retorno delegado e tabular.
