# Design System Spec
<!-- Template de referencia — o runner gera este arquivo em render_design_system_spec().
     Nomenclatura de tokens: {categoria}/{escala} ex.: color/primary/500, spacing/4 -->

## Origem
- Design system existente inspecionado: <!-- [runtime] nome/link ou "nenhum — foundations criadas" -->
- Profundidade: <!-- [runtime] light | medium | deep -->

## Tokens

### Cor
| Token | Valor | Uso |
|-------|-------|-----|
| color/primary/500 | <!-- [runtime] --> | Acao principal |
| color/secondary/500 | <!-- [runtime] --> | Acao secundaria |
| color/neutral/0-900 | <!-- [runtime] --> | Textos, fundos, bordas |
| color/feedback/success | <!-- [runtime] --> | |
| color/feedback/warning | <!-- [runtime] --> | |
| color/feedback/error | <!-- [runtime] --> | |
| color/feedback/info | <!-- [runtime] --> | |

### Tipografia
| Token | Tamanho | Peso | Uso |
|-------|---------|------|-----|
| <!-- [runtime] --> | | | |

### Espacamento e Radius
- Spacing scale: multiplos de 4px (4/8/12/16/24/32/48/64).
- Border radius padrao: <!-- [runtime] -->

## Componentes

| Componente | Variantes | Estados |
|------------|-----------|---------|
| Button | primario / secundario / texto | idle / hover / focus / disabled / loading |
| Input | default | idle / focus / error / disabled |
| Card | default | <!-- [runtime] --> |
| Navigation | <!-- [runtime] --> | <!-- [runtime] --> |
| Alert/Toast | success / warning / error / info | <!-- [runtime] --> |
| Empty State | default | — |
| Loading | spinner / skeleton | — |

## Acessibilidade
<!-- Ver knowledge/accessibility-rules.md para criterios completos. -->
- Contraste verificado: <!-- pass | needs_input | planned -->
- Alvo de toque verificado: <!-- pass | needs_input | planned -->
- Foco visivel em componentes: <!-- pass | needs_input | planned -->

---
**Fatos (fonte)** | **Inferencias (agente)**
Tokens e componentes extraidos de design system existente (SRC-xxx). | Tokens e componentes propostos pelo agente — validar com o time de design antes de usar em producao.
