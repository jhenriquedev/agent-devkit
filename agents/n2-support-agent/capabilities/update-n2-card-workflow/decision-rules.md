# Decision Rules

- Planejar automacoes Azure explicitas para o fluxo N2 a partir dos parametros recebidos.
- Sem `--execute`, retornar `azureActions` com `commandPreview` e sem mutacao externa.
- Com `--execute`, chamar `update-card-tags`, `comment-card`, `move-card`, `assign-card` e `attach-file` somente quando cada contrato estiver completo.
- `target-column` sem `target-state` nao deve mover card; retornar `skipped` com lacuna clara.
- Sempre planejar tag N2 quando houver card valido e a tag ainda nao estiver presente.
- Incluir `assign-card` apenas quando `assign_to` estiver informado.
- Anexar `patch_plan.md` somente quando houver artefato existente e adequado para anexo.
- Preservar rastreabilidade de projeto, card, estado, coluna, responsavel e modo.
- Nao alterar dados de negocio ou executar patch por meio desta capability.
- Mascarar dados sensiveis em comentarios e summaries de acoes.
