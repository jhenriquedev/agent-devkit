# generate-reconciliation-report

## Objetivo
Gerar relatorio markdown auditavel de conciliacao, a partir do resultado de
reconcile-spreadsheets, com totais, principais divergencias e regras usadas.

## Entradas
- `--source` (obrigatorio): JSON resultado de reconcile-spreadsheets ou fontes
  diretas para conciliar.
- `--output` (obrigatorio): caminho do arquivo markdown a gerar.
- `--left`, `--right`, `--key`, `--compare-columns`, `--numeric-tolerance`: se
  conciliando diretamente.

## Raciocinio
1. Confirme sha256 de ambas as fontes; registre no cabecalho do relatorio.
2. Monte relatorio com secoes: Cabecalho (data, fontes, sha256, regras), Resumo
   Executivo (totais), Divergencias Principais (tabela), Detalhes por Categoria,
   Regras e Metodologia.
3. Mascare PII em todos os exemplos de divergencia.
4. Carimbem a data/hora de geracao no relatorio.

## Rubrica de decisao
- sha256 ausente de qualquer fonte -> bloqueie geracao; nao ha auditabilidade.
- PII detectado nas divergencias -> mascare automaticamente.
- Relatorio so gerado com --output; nao envie markdown para stdout sem path.

## Saida
Arquivo markdown em --output com: cabecalho de auditoria, resumo executivo,
tabela de divergencias (com PII mascarado), regras e metodologia. Confirme path
gerado.

## Nao fazer
- Nao gerar relatorio sem --output.
- Nao exibir PII integral nas tabelas.
- Nao omitir regras de conciliacao do relatorio (auditabilidade).
