# Prompt: search-columns

## OBJETIVO
Localizar colunas cujo nome contenha o padrão fornecido, opcionalmente dentro
de um schema.

## ENTRADAS
- `pattern` (obrigatório na prática): substring a buscar.
- `schema` (opcional): restringir ao schema.
- `limit` (opcional, default 100).

## RACIOCÍNIO (passos)
1. Execute a capability `search-columns --pattern <padrão>`.
2. Leia `columns[]` (campos: `table_schema`, `table_name`, `column_name`,
   `data_type`).
3. Se zero resultados, sugira variações (ex.: `cpf` / `tax_id` / `documento`).

## RUBRICA / REGRAS DE DECISÃO
- Use para descobrir onde um conceito de domínio (ex.: CPF, e-mail) aparece
  no banco.
- `count == 0` → sugira termos alternativos.

## SAÍDA
Tabela com `table_schema`, `table_name`, `column_name`, `data_type` +
contagem.

## NÃO FAÇA
- Não use busca vazia sem propósito.
- Não exponha valores de dados, apenas metadados de coluna.
