# Workflow

1. Receber `project` e `card`.
2. Chamar `azure-devops-orchestrator/read-card` com comentarios.
3. Extrair titulo, descricao, comentarios, anexos, tags, estado e coluna.
4. Extrair entidades: CPF, proposta, contrato, TOPdesk, request id e correlation id.
5. Executar check de base restritiva quando houver CPF.
6. Executar check BPO quando houver CPF ou proposta.
7. Chamar `azure-devops-orchestrator/update-card-tags` para planejar ou aplicar `Analise N1`.
8. Se `target-column` ou `target-state` forem informados, chamar `azure-devops-orchestrator/move-card`.
9. Montar checks operacionais na ordem do runbook.
10. Gerar decisao N1 inicial e artefatos.
11. Renderizar contrato fixo.

Sem `--execute`, tags e movimentacao ficam em dry-run.
