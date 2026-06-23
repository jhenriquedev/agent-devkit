# Prompt: search-tables

> Operação read-only. Separe dados coletados de inferências.

## Objetivo
Buscar tabelas por padrão de nome (ILIKE) em todos os schemas, para localizar
tabelas de interesse sem navegar manualmente schema a schema.

## Entradas esperadas
- `pattern` (obrigatório): padrão de busca (ex: `customer%`, `%order%`).
- `database` (opcional).
- `limit` (default 100).

## Passos de raciocínio
1. Confirme que `pattern` foi fornecido. Se não, peça ao usuário.
2. Execute `search-tables` com o pattern.
3. Apresente resultados em tabela.
4. Se 0 resultados, sugira padrão alternativo (ex: `%` para ver todas) — não invente tabela.

## Regras de decisão
- Pattern vazio ou `%` retorna todas as tabelas (até o limit).
- Se o pattern for muito específico e não retornar resultados, informe e sugira variação.

## Saída
Tabela markdown: `table_schema`, `table_name`, `table_type` + contagem.

## NÃO faça
- Não invente tabela não retornada.
- Não leia dados de linha.
