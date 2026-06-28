# Regras

- Inspecionar arquivo, paginas e node IDs antes de qualquer alteracao.
- Preferir nova pagina/frame ou versao para design validado.
- Escrita exige `--yes-figma-write` ou confirmacao equivalente, direct mode e evidencia real.
- Registrar `mutated_node_ids`, `created_node_ids` ou `inspected_node_ids`.
- Mudancas destrutivas sao proibidas por padrao.
- Sem bridge/permissao, gerar `figma-action-plan.md` sem afirmar update real.
