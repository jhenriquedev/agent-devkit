# Prompt: describe-table

> Operação read-only. Separe dados coletados de inferências.

## Objetivo
Descrever a estrutura detalhada de uma tabela: colunas, tipos, nullability, defaults,
índices e constraints, sem expor dados de linha.

## Entradas esperadas
- `schema` (obrigatório): schema da tabela.
- `table` (obrigatório): nome da tabela.
- `database` (opcional).

## Passos de raciocínio
1. Se schema ou table faltarem, peça ao usuário OU rode `list-schemas`/`list-tables`
   para resolver.
2. Execute `describe-table`.
3. Apresente: lista de colunas (name, type, nullable, default), índices e constraints.
4. Identifique colunas candidatas a chave primária (PK constraint), chaves estrangeiras
   (FK) e colunas que parecem PII pelo nome — **rotule como INFERÊNCIA**.

## Regras de decisão
- Coluna com `constraint_type = PRIMARY KEY` → fato.
- Coluna com nome contendo cpf/email/phone/name/token → candidata a PII — **INFERÊNCIA**.
- Se a tabela não existir, o runner retorna erro: informe ao usuário e sugira `list-tables`.

## Saída
Seção **Colunas** (tabela): `column_name`, `data_type`, `is_nullable`, `column_default`.
Seção **Índices**: lista com `indexname` e `indexdef`.
Seção **Constraints**: lista com `constraint_name` e `constraint_type`.
Seção **Inferências** (se houver): colunas candidatas a PII por nome.

## NÃO faça
- Não exiba dados de linha.
- Não afirme que uma coluna é PII como fato — use "candidata por nome".
