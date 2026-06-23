# Prompt: search-columns

> Operação read-only. Separe dados coletados de inferências.

## Objetivo
Buscar colunas por padrão de nome em todas as tabelas (opcionalmente filtrado por schema),
para localizar onde um campo específico existe no banco.

## Entradas esperadas
- `pattern` (obrigatório): padrão de busca (ex: `%cpf%`, `%email%`).
- `schema` (opcional): restringir ao schema.
- `database` (opcional).
- `limit` (default 100).

## Passos de raciocínio
1. Confirme que `pattern` foi fornecido. Se não, peça ao usuário.
2. Execute `search-columns`.
3. Apresente resultados agrupados por `table_schema.table_name`.
4. Destaque colunas cujo nome sugere PII (cpf, email, phone, token) como candidatas —
   **INFERÊNCIA por nome**.

## Regras de decisão
- Se 0 resultados, sugira padrão mais amplo (ex: `%cpf%` → `%doc%`).
- Coluna encontrada aqui não confirma que tem PII — use `detect-sensitive-columns` para
  classificação sistemática.

## Saída
Tabela markdown: `table_schema`, `table_name`, `column_name`, `data_type` + contagem.

## NÃO faça
- Não afirme que coluna contém PII só pelo nome — é inferência.
- Não leia dados de linha.
