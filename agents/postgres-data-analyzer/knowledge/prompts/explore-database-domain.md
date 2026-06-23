# Prompt: explore-database-domain

> Operação read-only. Marque domínios inferidos como INFERÊNCIA. Separe dados de inferências.

## Objetivo
Mapear o domínio funcional do banco agrupando tabelas por categoria inferida do nome
(customer, sales, finance, audit, security, other) para fornecer visão de alto nível
sem ler linhas.

## Entradas esperadas
- `schema` (opcional): restringir ao schema.
- `database` (opcional).
- `limit` (default 200).

## Passos de raciocínio
1. Execute `explore-database-domain`.
2. Leia `domains` (domain, table_count) e `tables` (lista completa).
3. Apresente: seção **Domains** (tabela agrupada por domínio) e seção **Tables** (lista).
4. Marque explicitamente: "Domínios são INFERÊNCIA baseada em heurística de nome de tabela."

## Regras de decisão
- Domínios (`customer`, `sales`, `finance`, `audit`, `security`, `other`) são heurísticos —
  **nunca apresente como fato**.
- Se todas as tabelas caem em `other`, o banco usa nomenclatura não padrão: informe.

## Saída
### Domains (INFERÊNCIA — heurística por nome de tabela)
Tabela: `domain`, `table_count`.

### Tables
Tabela: `table_schema`, `table_name`, `table_type`.

## NÃO faça
- Não afirme que o banco "é" de determinado domínio como fato.
- Não leia dados de linha.
