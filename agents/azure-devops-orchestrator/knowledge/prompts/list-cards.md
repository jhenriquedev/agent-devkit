# Prompt: Listar Cards

Objetivo: listar work items de um projeto Azure DevOps a partir de filtros ou
WIQL explicitos, sem inferir prioridade.

Entradas esperadas: project para Azure real, e opcionalmente wiql, query_id,
state, assigned_to, tags e limit. Pode receber --fixture em fluxos de teste.

Passos de raciocinio:

1. Confirme o projeto e o criterio de busca. Se o usuario deu uma query ou WIQL,
   use-a antes de filtros inferidos.
2. Se nao houver criterio, peca o menor conjunto de informacoes necessario:
   projeto e um filtro seguro. Nao liste volume ilimitado.
3. Execute list-work-items com limite seguro.
4. Apresente filtros usados, cards encontrados, lacunas ou ambiguidades e
   proximos passos recomendados.

Regras de decisao:

- Query ou WIQL informada tem prioridade sobre filtros inferidos.
- Se o retorno atingir o limite, avise que podem existir mais cards e sugira
  refinar.
- Nao infira prioridade sem campo, tag ou criterio explicito.
- Esta capability e read-only: nenhuma escrita e permitida.

Formato de saida: use templates/list-cards-output.md, com secoes de filtros,
resultados e observacoes.

NAO faca: nenhuma escrita; nao infira prioridade; nao liste sem limite; nao
invente filtros amplos so para retornar algo.
