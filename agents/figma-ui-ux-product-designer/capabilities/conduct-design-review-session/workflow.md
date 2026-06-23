# Prompt — conduct-design-review-session

## OBJETIVO
Conduzir revisao interativa de design, registrar decisoes, pendencias e proxima iteracao.

## ENTRADAS
- `--brief`: contexto do design e objetivo da revisao.
- `--source`: artefatos de design a revisar (telas, brief, handoff, feedback anterior).
- `--figma-file-url`: arquivo Figma a revisar (opcional).

## RACIOCINIO (passos)
1. Consolide design atual, feedback recebido e perguntas abertas.
2. Estruture a revisao em topicos: objetivos atingidos, estados cobertos, acessibilidade, handoff, proximas decisoes.
3. Classifique cada ponto da revisao usando a rubrica de `feedback-rubric.md`.
4. Para cada ponto: registe decisao tomada, pendencia ou pergunta para o usuario.
5. Gere plano da proxima iteracao: o que mudar, quem decide, prazo sugerido.

## REGRAS DE DECISAO
- Ponto de negocio sem decisao: abrir em open-design-questions.md; nao assumir.
- Se houver conflito entre participantes: registrar as opcoes e escalar ao PO.

## SAIDA
- `feedback-triage.md`: pontos revisados com status (aprovado/pendente/reaberto).
- `open-design-questions.md`: perguntas sem resposta.
- `figma-action-plan.md`: proxima iteracao.

## NAO FACA
- Nao decida regra de negocio sem confirmacao do PO.
- Nao marque ponto como "aprovado" sem registro de quem aprovou.
