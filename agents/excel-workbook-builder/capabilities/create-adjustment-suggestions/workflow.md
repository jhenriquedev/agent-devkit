# create-adjustment-suggestions

OBJETIVO: Sugerir ajustes de lançamento para registros classificados como
"different" na conciliação, para revisão humana antes de qualquer ação.

ENTRADAS: --reconciliation-summary (JSON obrigatório); --reconciliation-data
(JSON com detalhes); --output.

RACIOCÍNIO:
1. Carregue reconciliation-rules.md.
2. Filtre registros com classe "different" (status different).
3. Para cada diferença, sugira o ajuste (valor esperado, campo, referência
   da diferença e justificativa).
4. Agrupe sugestões por impacto e facilidade de aplicação.
5. Produza arquivo .xlsx de sugestões + .md narrativo.

REGRAS DE DECISÃO:
- Sugestões são SEMPRE para revisão humana; nunca aplique automaticamente.
- matched e left_only/right_only não geram sugestões de ajuste aqui.
- Cada sugestão deve ter rastreabilidade para a diferença de origem.

SAÍDA: adjustment-suggestions.xlsx + adjustment-suggestions.md.

NÃO FAZER: aplicar ajustes; gerar sugestões para matched; omitir justificativa.
