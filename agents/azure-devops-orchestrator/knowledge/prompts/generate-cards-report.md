# Prompt: Gerar Relatorio Cards

Objetivo: produzir um relatorio read-only consolidando uma listagem filtrada e a
leitura detalhada de cada card retornado.

Entradas esperadas: project e filtros wiql, state, assigned_to, tags ou limit.
include_comments e include_details sao opcionais. Pode receber --fixture.

Passos de raciocinio:

1. Liste com os filtros informados, sem inferir prioridade.
2. Para cada ID, leia o card; com include_comments, carregue comentarios.
3. Monte sumario executivo com total, sem responsavel, sem criterio de aceite,
   sem descricao, com anexos, com comentarios, por estado e por responsavel.
4. Destaque lacunas operacionais com os IDs afetados.
5. Se o retorno igualar o limite, avise possivel truncamento.
6. Inclua detalhes por card quando include_details, resumindo descricoes longas.

Regras de decisao:

- Operacao sempre read-only.
- Card sem responsavel e assigned_to vazio.
- Card sem criterio de aceite e acceptance_criteria vazio.
- Anexos sao relations com rel == AttachedFile.
- Nao infira prioridade sem campo ou tag explicita.

Formato de saida: use templates/generate-cards-report-output.md, com Query,
Executive Summary, By State, By Assignee, Consolidated Table, Operational Gaps,
Details e Write Operations="none".

NAO faca: nenhuma escrita; nao exceda o limite; nao reproduza descricoes longas
inteiras.
