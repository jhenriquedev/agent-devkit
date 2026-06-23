# Regras de Acessibilidade — Criterios verificaveis (WCAG 2.1 AA)

## Contraste de cor (criterio 1.4.3 / 1.4.11)
- Texto normal (<18pt regular / <14pt bold): contraste minimo **4.5:1** contra fundo.
- Texto grande (>=18pt regular ou >=14pt bold): contraste minimo **3:1** contra fundo.
- Componentes de UI (bordas de input, icones significativos, graficos): contraste minimo **3:1**.
- Verificar: use a relacao de luminancia relativa (formula WCAG) ou ferramenta Figma Color Blindness.
- Excecao: texto decorativo e texto em logotipos nao tem requisito de contraste.

## Alvo de toque / area de clique (criterio 2.5.5 nivel AAA / 2.5.8 nivel AA em WCAG 2.2)
- Alvo de toque minimo: **44x44px** (iOS) / **48x48dp** (Material Android) / **24x24px** web (AA 2.2).
- Garantir espacamento entre alvos adjacentes >= 8px para evitar ativacao acidental.

## Foco e navegacao por teclado (criterio 2.4.7)
- Todo elemento interativo (link, botao, input, select, checkbox, radio) deve ter foco visivel.
- Indicador de foco: outline de 2px solido em cor de alto contraste (>= 3:1 contra fundo adjacente).
- Ordem de foco (tab order) deve seguir ordem visual logica: esquerda para direita, cima para baixo.

## Labels e textos alternativos (criterio 1.1.1, 3.3.2)
- Toda imagem informativa tem texto alternativo descritivo.
- Imagem decorativa: alt="" ou role="presentation".
- Todo campo de formulario tem label associado (nao apenas placeholder).
- Botoes com somente icone: aria-label descritivo obrigatorio.
- Erros de validacao: descricao textual do erro proxima ao campo, nao apenas cor.

## Cores nao como unico indicador (criterio 1.4.1)
- Erro/sucesso/alerta: nunca indicado somente por cor; use icone + texto.
- Links em texto corrido: sublinhado ou outro diferenciador visual alem de cor.

## Hierarquia de cabecalhos
- Pagina deve ter um H1 unico descrevendo o proposito principal.
- Cabecalhos seguem hierarquia logica (H1 > H2 > H3); nao pule niveis.

## Checklist de revisao rapida (usar em review-design-quality)

| Item | Criterio | Verificavel no Figma |
|------|----------|---------------------|
| Contraste texto normal | >= 4.5:1 | Plugin Figma "Contrast" / Color Blindness |
| Contraste texto grande | >= 3:1 | idem |
| Contraste componentes UI | >= 3:1 | idem |
| Alvo de toque | >= 44x44px (iOS) / 48dp (Android) | Verificar frame sizes |
| Foco visivel | outline 2px alto contraste | Verificar estado focus em componentes |
| Labels em campos | label associado, nao so placeholder | Verificar camadas de texto |
| Botoes icone | aria-label no handoff | Verificar anotacao em dev-handoff |
| Erros por texto | descricao textual presente | Verificar tela de estado de erro |
| Imagens alt | alt text descrito | Verificar anotacao em dev-handoff |
| Hierarquia H1 unica | somente um H1 por pagina | Verificar tipografia |
