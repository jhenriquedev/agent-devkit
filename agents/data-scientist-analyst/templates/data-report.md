# Relatorio de Dados

> Contrato de saida de `generate-data-report`. A geracao real e feita por
> `reporting.py:render_data_report()`. Este arquivo documenta o formato fixo.

## Fonte

- Arquivo: {dataset.name}
- Formato: {dataset.format}
- Linhas: {dataset.row_count}
- Linhas originais: {dataset.original_row_count}
- Truncado/amostrado: {dataset.truncated | sim/nao}
- Colunas: {dataset.column_count}
- SHA-256: {dataset.sha256}
- Warnings de leitura: {dataset.warnings | lista ou "nenhum"}

## Qualidade

- Score: {quality.quality_score}
- Linhas duplicadas: {quality.duplicate_row_count}
- Linhas vazias: {quality.empty_row_count}
- Colunas com nulos: {quality.columns_with_missing_values | lista ou "nenhuma"}

## Dados sensiveis

- Possui dados sensiveis: {sensitive_data.has_sensitive_data | sim/nao}
- {coluna}: {categorias} [repetido por coluna sensivel — somente exemplos mascarados]

## Colunas

- {coluna}: tipo={inferred_type}, nulos={missing_count}, unicos={unique_count}
  [repetido por coluna]

## Reprodutibilidade

- Dataset hash: {dataset.sha256}
- Fonte nao e alterada pela capability.
- Reexecute o mesmo comando com os mesmos controles de leitura para reproduzir.

## Limitacoes

- Inferencia de tipos e qualidade e baseline.
- Analises sobre amostra truncada devem ser tratadas como indicativas.
- Deteccao de dados sensiveis usa heuristicas.

## Base para PDF

- Este markdown e o formato canonico para conversao posterior em PDF.
- Preserve as secoes Fonte, Qualidade, Dados sensiveis, Colunas, Reprodutibilidade
  e Limitacoes na exportacao.

---
*Separacao: Fatos (fonte do runner) x Inferencias (interpretacao do agente)*
