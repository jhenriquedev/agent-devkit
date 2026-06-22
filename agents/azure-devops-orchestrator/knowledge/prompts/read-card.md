# Prompt: Ler Card

Objetivo: ler um work item por ID e produzir uma analise estruturada para
decisao, separando fato de inferencia.

Entradas esperadas: work_item_id e project para Azure real, ou --fixture.
include_comments e include_relations sao opcionais.

Passos de raciocinio:

1. Valide projeto e ID.
2. Execute get-work-item com relacoes quando disponivel.
3. Se relevante ou solicitado, execute get-work-item-comments.
4. Reporte ID, tipo, titulo, estado, coluna, datas, responsavel, tags, anexos,
   comentarios e URL.
5. Identifique lacunas, riscos, bloqueios e proximos passos.

Regras de decisao:

- Sempre separe Fatos coletados de Inferencias.
- Criterio de aceite ausente e lacuna marcada explicitamente.
- Conflito entre descricao e comentarios deve ser sinalizado; nao escolha um
  lado sem evidencia.
- Nao infira o responsavel real por nome parcial.

Formato de saida: use templates/read-card-output.md, com Identification,
Collected Facts, Attachments, Acceptance Criteria, Comments, Gaps/Risks,
Inferencias e Next Steps.

NAO faca: nao altere o card; nao assuma criterios ausentes; nao recomende
escrita como se ja tivesse sido executada; se a descricao tiver logs sensiveis,
resuma em vez de reproduzir o bloco bruto.
