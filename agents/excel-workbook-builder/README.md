# Excel Workbook Builder

Agente especialista em criar e manter planilhas Excel com templates
versionados, ingestao de dados, reconciliacao, dashboards e revisao tecnica.

## Fase 3

O agente entrega a superficie completa de capabilities e runners executaveis
para o nucleo operacional de Excel:

- Registro e versionamento de templates.
- Listagem de templates e versoes.
- Geracao de arquivo de entrada para preenchimento.
- Ingestao de dados tabulares.
- Geracao de workbook `.xlsx` a partir de dados.
- Geracao de workbook `.xlsx` a partir de template registrado, preservando o
  workbook base e atualizando a aba `Data`.
- Atualizacao de workbooks existentes preservando abas e estrutura fora da aba
  de dados alvo.
- Conciliacao basica entre duas bases.
- Revisao tecnica de workbooks gerados com checagem de abas obrigatorias,
  formulas, validacoes e marcadores de erro.
- Delegacao segura para agentes de dados, com execucao apenas quando solicitada
  explicitamente.

## Exemplos

```bash
agent run excel-workbook-builder register-template \
  --template ./modelo.xlsx \
  --template-id conciliacao \
  --version 0.1.0 \
  --status validated \
  --yes-save

agent run excel-workbook-builder ingest-source-document \
  --source ./dados.csv \
  --output ./dados.json

agent run excel-workbook-builder generate-workbook-from-data \
  --input ./dados.json \
  --output ./relatorio.xlsx \
  --title "Relatorio Operacional"

agent run excel-workbook-builder reconcile-datasets \
  --left ./base-a.csv \
  --right ./base-b.csv \
  --key id \
  --compare-column amount \
  --output ./conciliacao.xlsx
```
