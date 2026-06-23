# Prompt — create-web-app-design

## OBJETIVO
Criar design web responsivo completo (ou plano executavel) com telas, estados, design system e handoff.

## ENTRADAS
- `--brief`: descricao do produto.
- `--source`: documentos, cards, especificacoes.
- `--platform`: web (padrao).
- `--design-style`: referencia visual ou sistema de design.
- `--figma-file-name`: nome do arquivo Figma.
- `--figma-file-url`: arquivo existente a evoluir (opcional).
- `--require-direct`, `--yes-figma-write`: controles de escrita.

## RACIOCINIO (passos)
1. Detecte modo Figma; aplique `depth-scope-rules.md` para classificar profundidade.
2. A partir das fontes (NAO de lista fixa), defina inventario de telas justificando cada uma; para cada tela, liste estados de `ux-patterns.md` (vazio, loading, erro, sucesso, permissao).
3. Decida: reusar design system existente (inspecionar primeiro) ou criar foundations minimas.
4. Planeje breakpoints obrigatorios: desktop (1440px), tablet (768px), mobile (375px).
5. Em `direct_mcp` + `--yes-figma-write`:
   - Carregue skill `figma-use`; busque design system existente via `search_design_system`.
   - Escreva telas incrementalmente com `use_figma` (skill `figma-generate-design`); capture node IDs.
6. Em `plan_only`: gere `figma-action-plan.md` detalhado com telas, estados e tokens planejados.
7. Execute checklist de `accessibility-rules.md` e `design-quality-checklist.md`.

## REGRAS DE DECISAO
- Criar arquivo Figma exige `--yes-figma-write`.
- Telas derivadas das fontes, nao de lista padrao; lacunas vao para open-design-questions.md.
- Web: tres breakpoints obrigatorios por tela criada.

## SAIDA
- `design-brief.md`, `web-screen-map.md`, `screen-inventory.md`, `design-system-spec.md`, `dev-handoff.md`, `design-quality-report.md`, `open-design-questions.md`, `source-traceability.md`.
- Em `direct_mcp`: `+ figma-execution-result.json`, `design-operation-log.md`.

## NAO FACA
- Nao entregue telas como "A definir" quando a fonte permite decidir; decida e cite a fonte.
- Nao pule estados de tela.
- Nao crie sem confirmar escrita.
