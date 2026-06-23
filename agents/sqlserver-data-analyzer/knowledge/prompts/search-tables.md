# Prompt: search-tables

## OBJETIVO
Localizar tabelas cujo nome contenha o padrão fornecido.

## ENTRADAS
- `pattern` (obrigatório na prática): substring a buscar.
- `limit` (opcional, default 100).

## RACIOCÍNIO (passos)
1. Execute a capability `search-tables --pattern <padrão>`.
2. Leia `tables[]` (campos: `table_schema`, `table_name`, `table_type`).
3. Se zero resultados, sugira variações: sinônimos PT/EN
   (ex.: `cliente`/`customer`, `pedido`/`order`).

## RUBRICA / REGRAS DE DECISÃO
- `count == 0` → avise e sugira termos alternativos.
- `count == limit` → pode haver mais; restrinja o padrão.

## SAÍDA
Tabela com `table_schema`, `table_name`, `table_type` + contagem.

## NÃO FAÇA
- Não faça busca vazia (`pattern=""`) que retorne o catálogo inteiro sem
  propósito.
- Não infira semântica da tabela apenas pelo nome sem inspecionar colunas.
