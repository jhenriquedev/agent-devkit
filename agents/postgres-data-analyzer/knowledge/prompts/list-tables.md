# Prompt: list-tables

> Operação read-only. Separe dados coletados de inferências.

## Objetivo
Listar tabelas (e views) em um schema ou em todo o banco para mapear o modelo de dados,
sem ler conteúdo de linhas.

## Entradas esperadas
- `schema` (opcional): filtrar por schema específico.
- `database` (opcional): nome do banco.
- `limit` (default 200).

## Passos de raciocínio
1. Se o usuário mencionou schema mas não confirmou que ele existe, rode `list-schemas`
   antes para validar.
2. Execute `list-tables` com o schema e limit.
3. Agrupe resultados por `table_schema`.
4. Destaque tabelas cujo nome sugira PII (customer, user, pessoa, cpf, documento)
   como candidatas a inspeção de sensibilidade — **rotule como INFERÊNCIA por nome**.

## Regras de decisão
- Se 0 tabelas retornadas com schema específico: schema inexistente ou sem permissão.
  Não assuma que está vazio.
- Distinção VIEW vs BASE TABLE: informe o tipo (coluna `table_type`).

## Saída
Tabela markdown: `table_schema`, `table_name`, `table_type` + contagem por schema.

## NÃO faça
- Não leia colunas ou dados de linha aqui.
- Não afirme que uma tabela tem PII só pelo nome — é inferência.
