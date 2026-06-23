# Prompt: list-relationships

## OBJETIVO
Mapear as foreign keys (FK) declaradas no banco para descobrir relacionamentos
reais entre tabelas.

## ENTRADAS
- `schema` (opcional): filtrar por schema pai.
- `limit` (opcional, default 500).

## RACIOCÍNIO (passos)
1. Execute a capability `list-relationships`.
2. Leia `count` e `relationships[]` (campos: `relationship_name`,
   `parent_table`, `parent_column`, `referenced_table`, `referenced_column`).
3. Destaque tabelas com muitas FKs (hubs de domínio).

## RUBRICA / REGRAS DE DECISÃO
- Esses são **relacionamentos declarados** (constraint real no banco), não
  heurísticas.
- `count == 0` → banco pode não usar FKs explícitas; sugira `suggest-joins`
  para heurística de nome.
- Para visualização, sugira `generate-erd-report`.
- Para uso em queries, sugira `suggest-joins`.

## SAÍDA
Tabela com `parent_table`, `parent_column`, `referenced_table`,
`referenced_column`, `relationship_name` + contagem total. Nota indicando que
são FKs declaradas.

## NÃO FAÇA
- Não apresente heurísticas de join como FKs reais aqui.
- Não filtre relacionamentos sem schema explícito quando o usuário quer o banco
  inteiro.
