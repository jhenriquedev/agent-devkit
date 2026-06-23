# Prompt — create-mobile-app-design

## OBJETIVO
Criar design mobile (iOS/Android) completo (ou plano executavel) com frames, navegacao, estados e handoff.

## ENTRADAS
- `--brief`: descricao do produto.
- `--source`: documentos, specs, cards.
- `--platform`: mobile (ios | android | both).
- `--design-style`: referencia visual.
- `--figma-file-name`: nome do arquivo Figma.
- `--figma-file-url`: arquivo existente a evoluir (opcional).
- `--require-direct`, `--yes-figma-write`: controles de escrita.

## RACIOCINIO (passos)
1. Detecte modo Figma; aplique `depth-scope-rules.md` para classificar profundidade.
2. A partir das fontes (NAO de lista fixa), defina inventario de telas com objetivo e estados (`ux-patterns.md`).
3. Decida navegacao conforme plataforma:
   - iOS: TabBar (2–5 destinos) + NavigationStack; frames iPhone 14 (390x844) + iPhone SE (375x667).
   - Android/Material: NavigationBar base; frames Pixel 7 (412x915dp).
   - Respeite safe area insets em todos os frames.
4. Defina ou reuse design system; verifique alvos de toque (44x44pt iOS / 48dp Android).
5. Em `direct_mcp` + `--yes-figma-write`:
   - Carregue skill `figma-use`; escreva frames incrementalmente; capture node IDs.
6. Em `plan_only`: gere `figma-action-plan.md` com frames, navegacao e estados planejados.
7. Execute checklist de `accessibility-rules.md`.

## REGRAS DE DECISAO
- Criar arquivo Figma exige `--yes-figma-write`.
- Telas derivadas das fontes; lacunas → open-design-questions.md.
- Mobile: alvo de toque verificado em todos os componentes interativos.

## SAIDA
- `design-brief.md`, `mobile-screen-map.md`, `screen-inventory.md`, `design-system-spec.md`, `dev-handoff.md`, `design-quality-report.md`, `open-design-questions.md`, `source-traceability.md`.
- Em `direct_mcp`: `+ figma-execution-result.json`, `design-operation-log.md`.

## NAO FACA
- Nao use frames de desktop para mobile.
- Nao ignore safe area e alvos de toque.
- Nao entregue telas como "A definir" quando a fonte permite decidir.
