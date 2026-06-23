# Prompt: list-tables

## OBJETIVO
Listar tabelas e views do banco ativo (opcionalmente filtrando por schema).

## ENTRADAS
- `schema` (opcional): filtrar por schema específico.
- `limit` (opcional, default 200): máximo de objetos.

## RACIOCÍNIO (passos)
1. Execute a capability `list-tables`.
2. Leia `count` e `tables[]` (campos: `table_schema`, `table_name`,
   `table_type`, `create_date`, `modify_date`).
3. Separe tabelas (`USER_TABLE`) de views (`VIEW`).
4. Se o usuário tem objetivo de domínio, sugira `search-tables` com o padrão
   relevante ou `explore-database-domain`.

## RUBRICA / REGRAS DE DECISÃO
- `count == limit` → pode haver mais; sugira filtrar por schema.
- Tabelas com `modify_date` recente → podem ser ativas; prioritize para análise.

## SAÍDA
Tabela enxuta com `table_schema`, `table_name`, `table_type` + contagem.

## NÃO FAÇA
- Não liste sem limit.
- Não infira conteúdo ou semântica das tabelas apenas pelo nome.
