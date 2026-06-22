# Direct Mode Requirements

## Regras

1. `FIGMA_ACCESS_TOKEN` sozinho nao habilita edicao completa de canvas.
2. Escrita real exige Figma MCP bridge ou runtime equivalente.
3. Operacoes de escrita exigem confirmacao: `--yes-figma-write` ou prompt
   interativo.
4. `--require-direct` deve falhar quando o bridge nao estiver configurado.
5. O agente so pode afirmar que criou ou editou Figma quando houver evidencia
   retornada pelo bridge.

## Evidencias Aceitas

- `file_key`
- `file_url`
- `created_node_ids`
- `mutated_node_ids`
- `inspected_node_ids`
- screenshots ou referencias de captura associadas ao arquivo/frame

## Modos

- `direct_mcp`: bridge configurado e direct mode ativado.
- `local_mcp_bridge`: bridge configurado, mas direct mode nao ativado.
- `plan_only`: sem bridge; gerar plano e artefatos executaveis.
- `blocked`: usuario exigiu direct mode, mas o ambiente nao atende aos
  requisitos.

