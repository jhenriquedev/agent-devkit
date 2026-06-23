# Prompt: describe-table

## OBJETIVO
Obter a estrutura completa de uma tabela: colunas, índices e constraints.

## ENTRADAS
- `schema` (obrigatório): schema da tabela.
- `table` (obrigatório): nome da tabela.

## RACIOCÍNIO (passos)
1. Se faltar `schema` ou `table`, peça ao usuário antes de executar.
2. Execute a capability `describe-table --schema <s> --table <t>`.
3. Leia três blocos: `columns[]`, `indexes[]`, `constraints[]`.
4. Identifique: colunas identity/PK, colunas nullable, colunas com default.
5. Indique candidatos a FK com base em nomes terminados em `_id` / `Id`.

## RUBRICA / REGRAS DE DECISÃO
- Coluna `is_identity=true` → é a chave surrogate automática; não filtre por ela.
- Coluna `is_nullable=false` sem default → campo obrigatório; relevante para
  quality analysis.
- Index `is_primary_key=true` → PK da tabela.
- Se tabela não encontrada (0 colunas), confirme schema/nome com o usuário.

## SAÍDA
Três blocos Markdown:
1. **Colunas** — tabela com `column_name`, `data_type`, `is_nullable`,
   `is_identity`, `column_default`.
2. **Índices** — tabela com `index_name`, `type_desc`, `is_unique`,
   `is_primary_key`.
3. **Constraints** — tabela com `constraint_name`, `type_desc`.

## NÃO FAÇA
- Não execute a capability sem schema e table.
- Não infira relacionamentos além dos nomes de coluna; use `list-relationships`
  para FKs reais.
