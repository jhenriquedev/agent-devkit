# Prompt: Atribuir Card

Objetivo: atribuir um work item a uma identidade resolvida no Azure DevOps,
evitando escolha automatica em caso de ambiguidade.

Entradas esperadas: work_item_id, project e assignee, preferencialmente email ou
unique_name; skip_identity_lookup opcional; --execute para escrita real.

Passos de raciocinio:

1. Leia o card atual e capture responsavel atual.
2. Resolva identidade com find-users, a menos que skip_identity_lookup esteja
   ativo.
3. Se houver 1 candidato exato, use-o. Se houver multiplos candidatos, pare e
   peca refinamento. Se houver 0 candidatos, peca email exato ou use
   skip_identity_lookup com unique_name explicito.
4. Lembre que o endpoint de identidade varia por tenant; se a busca falhar,
   ofereca o fallback de email exato com skip_identity_lookup.
5. Se o alvo ja for o responsavel atual, retorne no-op.
6. Mostre responsavel atual e alvo; apos confirmacao e --execute, aplique via
   update-work-item.

Regras de decisao:

- Prefira email ou unique_name; nunca resolva por nome parcial.
- Nao escolha automaticamente entre candidatos ambiguos.
- No-op quando alvo e atual forem equivalentes.
- Escrita real exige confirmacao/--execute.

Formato de saida: use templates/assign-card-output.md, com Target, Identity,
Result e Confirmation.

NAO faca: nao atribua sem confirmacao; nao adivinhe identidade; nao mude tags ou
estado nesta capability.
