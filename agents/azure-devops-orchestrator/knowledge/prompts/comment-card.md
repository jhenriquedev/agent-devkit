# Prompt: Comentar Card

Objetivo: preparar e adicionar um comentario a um work item, com confirmacao
explicita antes da escrita real.

Entradas esperadas: work_item_id e project; comment ou comment_intent; tone
default professional. --execute para escrita real.

Passos de raciocinio:

1. Valide ID e a intencao ou texto do comentario.
2. Leia o card para contexto, incluindo titulo e estado.
3. Gere o comentario proposto, claro, objetivo, rastreavel e profissional.
4. Classifique risco: high se contiver dados sensiveis como senha, token, CPF,
   credencial ou payload de producao; medium se registrar compromisso, prazo,
   atribuicao ou deploy; caso contrario low.
5. Apresente preview do texto final e bloco de confirmacao com alvo, acao,
   comentario e risco.
6. Apos confirmacao e --execute, chame add-comment e reporte comment_id ou URL.

Regras de decisao:

- Sempre leia o card antes de propor o comentario.
- Sempre mostre o preview do texto final.
- Se o usuario pedir para comentar diretamente, ainda assim confirme alvo e
  texto final antes de chamar o method de escrita.
- Reescreva tom agressivo para tom profissional.
- Nunca comente em nome de outra pessoa nem inclua dados sensiveis nao
  solicitados.

Formato de saida: use templates/comment-card-output.md, com Target, Comment,
Risk, Result e Confirmation.

NAO faca: nao chame add-comment sem confirmacao; nao afirme publicado antes do
retorno do method; nao duplique payload sensivel.
