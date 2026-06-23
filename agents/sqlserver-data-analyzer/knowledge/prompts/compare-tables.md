# Prompt: compare-tables

## OBJETIVO
Comparar a estrutura de duas tabelas: colunas em comum, colunas exclusivas de
cada lado e divergências de tipo.

## ENTRADAS
- `left-schema` (obrigatório).
- `left-table` (obrigatório).
- `right-schema` (obrigatório).
- `right-table` (obrigatório).

## RACIOCÍNIO (passos)
1. Se faltar qualquer um dos quatro parâmetros, peça ao usuário.
2. Execute a capability `compare-tables --left-schema <ls> --left-table <lt>
   --right-schema <rs> --right-table <rt>`.
3. Leia `common_columns[]`, `left_only_columns[]`, `right_only_columns[]`.
4. Identifique colunas com mesmo nome mas tipo diferente (candidatos a problema
   de migração/dedup).

## RUBRICA / REGRAS DE DECISÃO
- Muitas colunas só em uma tabela → tabelas estruturalmente distintas; join
  pode não fazer sentido.
- Mesmo nome, tipo diferente → risco em ETL ou migração.
- Poucas diferenças → candidato a versão nova/stage da mesma entidade.

## SAÍDA
Três blocos:
1. **Colunas comuns** — tabela com nome e tipo de cada lado.
2. **Somente em `left`** — lista com tipos.
3. **Somente em `right`** — lista com tipos.
Interpretação de divergências.

## NÃO FAÇA
- Não execute sem os quatro parâmetros.
- Não compare dados (apenas estrutura).
