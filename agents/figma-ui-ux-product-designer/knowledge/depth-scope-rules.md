# Regras de Profundidade e Escopo — Classificacao de design

## Dimensao 1: Profundidade (quanto detalhe produzir)

### light
- **Quando:** brief vago, <2 fontes substanciais, entrevista nao realizada, prazo urgente.
- **Entrega:** design-brief.md com objetivo/publico/plataforma; inventario de telas (so nomes + objetivos); open-design-questions.md completo; sem wireframes detalhados.
- **NAO inclui:** tokens de design system, especificacoes de componente, interacoes.

### medium
- **Quando:** brief claro, >=2 fontes substanciais, publico e plataforma definidos.
- **Entrega:** tudo de `light` + inventario com estados obrigatorios por tela; arquitetura de informacao; design system parcial (tokens basicos + 3–5 componentes principais); figma-action-plan.md detalhado; dev-handoff.md parcial.

### deep
- **Quando:** produto novo ou redesign estrategico, design system sendo criado/refatorado, brief rico com requisitos de acessibilidade e multi-plataforma.
- **Entrega:** tudo de `medium` + design system completo (tokens + componentes + variantes + estados); todos os frames responsivos/mobile; revisao de acessibilidade WCAG AA; dev-handoff.md completo com microcopy e interacoes.

## Dimensao 2: Escopo (o que entregar)

### tela
- Uma view/screen especifica. Entrega: inventario de estados desta tela, componentes usados, handoff desta tela.

### fluxo
- Sequencia de 2–7 telas com objetivo transacional. Entrega: jornada do usuario, todas as telas do fluxo com transicoes, estados de erro no meio do fluxo.

### modulo
- Conjunto de fluxos relacionados (ex.: autenticacao, gestao de usuarios, relatorios).
- Entrega: tudo do escopo `fluxo` para cada sub-fluxo + navegacao entre fluxos do modulo + design system do modulo.

### produto
- Todos os modulos. Exige depth=deep obrigatoriamente.
- Entrega: design system completo, todas as telas, guia de componentes, handoff completo.

## Matriz de decisao automatica

| # fontes | Brief claro? | Plataforma? | Profundidade sugerida | Escopo minimo |
|----------|-------------|-------------|----------------------|---------------|
| 0–1      | nao         | nao         | light                | tela          |
| 0–1      | sim         | sim         | light → medium       | fluxo         |
| 2–3      | sim         | sim         | medium               | fluxo         |
| >=4      | sim         | sim         | medium → deep        | modulo        |
| qualquer | explicitado pelo usuario | qualquer | usar o explicitado | usar o explicitado |

## Regra de escalonamento
- Se durante o trabalho a complexidade real exceder o escopo inicial, registre em open-design-questions.md e proponha upgrade de escopo ao usuario antes de continuar.
- Nunca reduza o escopo silenciosamente sem registrar.

## Relacao com `resolve_depth` no runner
A heuristica em `design_support.py:resolve_depth` usa `len(sources)` e `brief_length` como proxy dessas regras. O host LLM deve aplicar estas regras explicitas e, se discordar da heuristica, passar `--depth` explicitamente.
