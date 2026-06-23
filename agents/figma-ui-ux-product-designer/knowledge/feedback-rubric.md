# Rubrica de Feedback de Design — Taxonomia e Triagem

## Categorias de feedback

### Visual
- **O que e:** layout, hierarquia visual, cor, tipografia, espacamento, alinhamento, iconografia, densidade de informacao.
- **Acao tipica:** ajuste no Figma (token, componente ou frame especifico).
- **Responsavel:** designer.
- **Requer confirmacao de regra de negocio?** Nao (salvo mudanca de cor de marca).

### UX
- **O que e:** fluxo de navegacao, ordem de passos, nomenclatura de elementos, feedback de acao (loading/sucesso/erro), discoverability, consistencia de interacao.
- **Acao tipica:** ajuste de fluxo ou estado; pode exigir nova tela.
- **Responsavel:** designer + PO para validar se altera regra de negocio.
- **Requer confirmacao de regra de negocio?** Frequentemente sim — confirmar com stakeholder antes de alterar fluxo.

### Negocio
- **O que e:** criterios de aceite, permissoes, limites de dados, mensagens de erro de dominio, condicoes especiais.
- **Acao tipica:** abrir pergunta em open-design-questions.md; NAO alterar design sem confirmacao.
- **Responsavel:** PO/stakeholder decide; designer implementa apos confirmacao.
- **Requer confirmacao de regra de negocio?** Sempre.

### Acessibilidade
- **O que e:** contraste insuficiente, alvo de toque pequeno, foco ausente, label faltando, hierarquia de cabecalho quebrada.
- **Acao tipica:** correcao obrigatoria (nao opcional); registrar em design-quality-report.md.
- **Responsavel:** designer; pode envolver dev para implementacao de aria/foco.
- **Requer confirmacao de regra de negocio?** Nao.

### Handoff
- **O que e:** especificacao de componente incompleta, token nao documentado, microcopy ausente, interacao nao descrita, link Figma desatualizado.
- **Acao tipica:** atualizar dev-handoff.md e/ou design-system-spec.md.
- **Responsavel:** designer.
- **Requer confirmacao de regra de negocio?** Somente se a falta for de regra de negocio.

## Niveis de prioridade

| Prioridade | Criterio | Acao |
|-----------|----------|------|
| critico | Bloqueia uso, viola acessibilidade obrigatoria, erro de regra de negocio | Resolver antes de qualquer handoff |
| alto | Degrada UX significativamente, inconsistencia visivel, fluxo quebrado | Resolver nesta iteracao |
| medio | Melhoria de qualidade, ajuste estetico relevante | Resolver na proxima iteracao |
| baixo | Opiniao estetica, nice-to-have | Backlog de design |

## Formato de saida para feedback-triage.md

```
| # | Fonte | Descricao resumida | Categoria | Prioridade | Acao | Responsavel | Status |
|---|-------|--------------------|-----------|-----------|------|-------------|--------|
| 1 | ...   | ...                | Visual    | medio     | Ajustar espacamento | Designer | pendente |
```

## Regras de triagem automatica

1. Qualquer item que mencione "regra de negocio", "permissao", "limite", "criterio de aceite" → categoria Negocio → abrir pergunta antes de agir.
2. Qualquer item que mencione "contraste", "foco", "aria", "acessibilidade", "touch target" → categoria Acessibilidade → prioridade minima alto.
3. Itens contraditórios entre si → registrar conflito em open-design-questions.md e escalar ao PO.
4. Sem responsavel declarado: designer assume o feedback Visual/UX/Handoff; PO assume Negocio.
