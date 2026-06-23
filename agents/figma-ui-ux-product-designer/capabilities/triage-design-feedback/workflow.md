# Prompt — triage-design-feedback

## OBJETIVO
Classificar feedback de design e registrar o que pode ser executado diretamente versus o que exige decisao.

## ENTRADAS
- `--source`: feedback em texto, arquivo ou comentarios.
- `--brief`: contexto do design sendo revisado.

## RACIOCINIO (passos)
1. Leia todos os itens de feedback fornecidos.
2. Classifique cada item usando a taxonomia de `feedback-rubric.md`:
   - **Visual:** layout, cor, tipografia, espacamento.
   - **UX:** fluxo, estado, interacao, nomenclatura.
   - **Negocio:** regra, permissao, criterio de aceite.
   - **Acessibilidade:** contraste, foco, alvo de toque, labels.
   - **Handoff:** spec incompleta, token ausente, microcopy faltando.
3. Atribua prioridade: critico / alto / medio / baixo (ver `feedback-rubric.md`).
4. Para cada item Negocio: abra pergunta em open-design-questions.md; NAO aplique sem confirmacao.
5. Para cada item Acessibilidade: prioridade minima "alto".
6. Identifique conflitos entre itens de feedback.

## REGRAS DE DECISAO
- Item de negocio: jamais aplicar sem confirmacao do PO/stakeholder.
- Itens conflitantes: registrar como pergunta e escalar.
- Feedback sem contexto suficiente: solicitar clarificacao antes de classificar.

## SAIDA
- `feedback-triage.md`: tabela com #, fonte, descricao, categoria, prioridade, acao, responsavel, status.
- `open-design-questions.md`: perguntas derivadas de itens Negocio e conflitos.

## NAO FACA
- Nao aplique mudanca de regra de negocio sem confirmacao.
- Nao ignore itens de acessibilidade.
