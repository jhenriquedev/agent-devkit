# Prompt: Preparar Analise Card

Objetivo: transformar um card em analise operacional de sustentacao, separando
fatos, hipoteses, lacunas e proximos passos, opcionalmente com um rascunho de
comentario. Sem escrita.

Entradas esperadas: work_item_id e project para Azure real, ou --fixture.
analysis_type default support; include_comment_draft opcional.

Passos de raciocinio:

1. Leia o card com comentarios e anexos quando disponiveis.
2. Classifique a demanda a partir de titulo, descricao e tags.
3. Liste fatos coletados, depois hipoteses, depois lacunas, depois proximos
   passos.
4. Se include_comment_draft, gere um comentario sugerido e marque claramente que
   ele nao foi publicado.

Regras de decisao:

- Nunca afirme causa raiz sem evidencia; use hipotese.
- Hipoteses tecnicas so devem aparecer quando o texto do card as suportar.
- Lacuna obrigatoria quando faltam criterio de aceite, descricao ou responsavel.
- Comentario sugerido so vira escrita pela capability comment-card.

Formato de saida: use templates/prepare-card-analysis-output.md, com Summary,
Collected Facts, Evidence, Hypotheses, Gaps, Next Steps, Suggested Comment e
Write Operations="none".

NAO faca: sem escrita; nao apresente comentario como publicado; nao conclua
diagnostico definitivo apenas com os dados carregados.
