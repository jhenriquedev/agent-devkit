# Prompt — create-design-system-foundation

## OBJETIVO
Criar ou planejar foundations e componentes base de design system (web/mobile).

## ENTRADAS
- `--brief`: descricao do produto e contexto de marca.
- `--source`: guia de estilo existente, tokens, exemplos visuais.
- `--figma-file-url`: arquivo Figma existente a enriquecer (opcional).
- `--platform`: web | mobile | both.
- `--yes-figma-write`: confirmacao para escrita real.

## RACIOCINIO (passos)
1. Se houver arquivo Figma existente, inspecione primeiro (`analyze-existing-figma-project`) para mapear o que ja existe.
2. Defina tokens minimos: cor (primaria, secundaria, neutral, feedback — success/warning/error/info), tipografia (escala de tamanhos, pesos), spacing (multiplos de 4px), border-radius, sombra.
3. Defina componentes base: Button (variantes: primario/secundario/texto; estados: idle/hover/focus/disabled/loading), Input (estados: idle/focus/error/disabled), Card, Navigation/NavBar, Feedback (Alert, Toast, Badge), Empty State, Loading (spinner/skeleton).
4. Para cada componente: liste variantes e estados; verifique criterios de `accessibility-rules.md`.
5. Em `direct_mcp`: use skill `figma-generate-library`; acione bridge incrementalmente; capture node IDs.
6. Profundidade e sempre >= deep para esta operacao estrategica.

## REGRAS DE DECISAO
- Prefira reusar design system existente; so crie foundations se nao houver base utilizavel.
- Confirme escrita antes de criar pagina de Design System no Figma.
- Tokens devem seguir convencao `{categoria}/{escala}` (ex.: `color/primary/500`).

## SAIDA
- `design-system-spec.md`: tokens, componentes, variantes, estados.
- `figma-action-plan.md`: passos de criacao no Figma.
- Em `direct_mcp`: `+ figma-execution-result.json`, `design-operation-log.md`.

## NAO FACA
- Nao crie design system sem inspecionar o que ja existe.
- Nao afirme criacao Figma sem evidencia do bridge.
