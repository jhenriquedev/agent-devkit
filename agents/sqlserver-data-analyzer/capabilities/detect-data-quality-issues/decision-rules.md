# Decision Rules: detect-data-quality-issues

## Rubrica de severidade de issue

| issue_type | Interpretação | Severidade | Ação sugerida |
|---|---|---|---|
| `all_null` | Coluna sem dados | Alta | Investigar antes de usar a tabela em análises |
| `constant_value` | Coluna com apenas 1 valor distinto | Média | Verificar se é intencional (flag/default) ou erro |

## Regras de decisão

1. Priorizar colunas-chave (PK, FK, colunas de negócio) ao reportar.
2. `all_null` em coluna NOT NULL → indica dado nunca foi preenchido; alerta de
   integridade.
3. `constant_value` com valor = default (0, 'N', 'A') → pode ser intencional;
   anotar sem concluir causa.
4. Reportar apenas o sintoma; não concluir a causa sem evidência adicional.
5. Se nenhum issue: confirmar explicitamente "sem problemas detectados" para
   `all_null`/`constant_value` nesta tabela.

## Quando pedir info

- `schema` ou `table` ausente → pedir antes de executar.
