# Prompt: list-relationships

> Operação read-only. Separe dados coletados de inferências.

## Objetivo
Listar foreign keys reais (pg_constraint) entre tabelas para mapear relacionamentos
do modelo de dados, sem ler conteúdo de linhas.

## Entradas esperadas
- `schema` (opcional): restringir ao schema.
- `database` (opcional).
- `limit` (default 200).

## Passos de raciocínio
1. Execute `list-relationships`.
2. Leia `count` e `relationships`.
3. Apresente tabela com: `relationship_name`, `parent_table`, `parent_column`,
   `referenced_table`, `referenced_column`.
4. Se `count == 0`, declare que nenhuma FK foi encontrada — não invente relacionamentos.

## Regras de decisão
- Relacionamentos aqui são **fatos** (FKs reais de pg_constraint), não heurísticas.
- Se o usuário quiser sugestões de join sem FK, use `suggest-joins` (heurística).

## Saída
Tabela markdown: `relationship_name`, `parent_table`, `parent_column`,
`referenced_table`, `referenced_column` + contagem total.

## NÃO faça
- Não misture FKs reais com sugestões heurísticas sem deixar explícito.
- Não leia dados de linha.
