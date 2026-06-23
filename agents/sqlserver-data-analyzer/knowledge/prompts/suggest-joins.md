# Prompt: suggest-joins

## OBJETIVO
Propor joins entre tabelas com indicação explícita de nível de confiança:
`high` (FK real) ou `medium` (heurística de nome).

## ENTRADAS
- `schema` (opcional): escopo de busca.

## RACIOCÍNIO (passos)
1. Execute a capability `suggest-joins`.
2. Leia `suggestions[]` (campos: `left_table`, `left_column`, `right_table`,
   `right_column`, `confidence`).
3. Separe sugestões `high` (FK real) de `medium` (heurística de nome/tipo).
4. Para cada grupo, apresente a sintaxe JOIN sugerida.

## RUBRICA / REGRAS DE DECISÃO
- `confidence: high` → join vem de FK real; pode ser usado diretamente.
- `confidence: medium` → join vem de heurística de nome (sufixo `_id`,
  coluna ID com mesmo nome normalizado); **deve ser validado pelo usuário**
  antes de usar em produção.
- Se `count == 0` → não há FK nem heurística óbvia; sugira `describe-table`
  para inspecionar colunas manualmente.

## SAÍDA
Duas seções:
1. **Joins confirmados (FK, confidence: high)** — tabela com left/right +
   exemplo SQL.
2. **Joins sugeridos por heurística (confidence: medium)** — tabela + aviso
   explícito de validação necessária.

## NÃO FAÇA
- Não apresente heurística como verdade confirmada.
- Não omita o label `confidence` de cada sugestão.
