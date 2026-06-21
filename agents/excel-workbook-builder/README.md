# Excel Workbook Builder

Agente especialista em criar e manter planilhas Excel com templates
versionados, ingestao de dados, reconciliacao, dashboards e revisao tecnica.

## Fase 1

A Fase 1 entrega a superficie completa de capabilities e runners executaveis
para o nucleo operacional:

- Registro e versionamento de templates.
- Listagem de templates e versoes.
- Geracao de arquivo de entrada para preenchimento.
- Ingestao de dados tabulares.
- Geracao de workbook `.xlsx` a partir de dados.
- Geracao de workbook `.xlsx` a partir de template registrado.
- Conciliacao basica entre duas bases.
- Revisao tecnica basica de workbooks gerados.

## Exemplos

```bash
./ai-devkit run excel-workbook-builder register-template \
  --template ./modelo.xlsx \
  --template-id conciliacao \
  --version 0.1.0 \
  --status validated \
  --yes-save

./ai-devkit run excel-workbook-builder ingest-source-document \
  --source ./dados.csv \
  --output ./dados.json

./ai-devkit run excel-workbook-builder generate-workbook-from-data \
  --input ./dados.json \
  --output ./relatorio.xlsx \
  --title "Relatorio Operacional"

./ai-devkit run excel-workbook-builder reconcile-datasets \
  --left ./base-a.csv \
  --right ./base-b.csv \
  --key id \
  --compare-column amount \
  --output ./conciliacao.xlsx
```

