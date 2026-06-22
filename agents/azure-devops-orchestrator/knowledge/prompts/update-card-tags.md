# Prompt: Alterar Tags Card

Objetivo: adicionar ou remover tags preservando as existentes e exibindo o diff
antes da escrita real.

Entradas esperadas: work_item_id e project; pelo menos um add_tag ou remove_tag;
reason opcional; --execute para escrita real.

Passos de raciocinio:

1. Leia o card e normalize as tags atuais.
2. Normalize tags a adicionar e remover com comparacao case-insensitive.
3. Calcule tags finais. Preserve tags existentes por padrao e remova apenas as
   explicitamente solicitadas.
4. Se nao houver mudanca real, retorne no-op.
5. Apresente diff com tags atuais, adicionadas, removidas, finais, risco e JSON patch planejado.
6. Apos confirmacao e --execute, aplique via update-work-item e reporte new_rev.

Regras de decisao:

- Preserve tags existentes por padrao.
- Nunca remova tag sem listar tags atuais e tags removidas.
- Remova apenas tags explicitamente solicitadas.
- No-op quando o conjunto final for igual ao atual.

Formato de saida: use templates/update-card-tags-output.md, com Target, Diff,
Result e Confirmation.

NAO faca: nao remova tags nao solicitadas; nao escreva sem --execute; nao
duplique tags.
