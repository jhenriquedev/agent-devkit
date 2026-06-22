# Figma MCP Setup

## Objetivo

Permitir que o `figma-ui-ux-product-designer` execute criacao, edicao,
inspecao e revisao real no Figma a partir do CLI local.

## Requisitos

- Um runtime com acesso ao Figma MCP.
- Um comando bridge configurado em `FIGMA_MCP_BRIDGE_COMMAND`.
- `FIGMA_MCP_ENABLED=true` ou `FIGMA_DIRECT_MODE=true`.
- Confirmacao explicita no comando da capability com `--yes-figma-write` para
  operacoes que criam ou alteram Figma.

## Contrato Do Bridge

O bridge recebe JSON em stdin:

```json
{
  "kind": "figma_mcp_operation",
  "version": "1.0",
  "operation": {
    "capability": "create-web-app-design",
    "action": "create_file_with_screens",
    "file_name": "Portal",
    "page_name": "AI DevKit Design",
    "screens": ["Dashboard"],
    "components": ["Button", "Card"]
  }
}
```

E retorna JSON em stdout:

```json
{
  "status": "executed",
  "file_key": "ABC123",
  "file_url": "https://figma.com/design/ABC123/Portal",
  "page_name": "AI DevKit Design",
  "created_node_ids": ["10:1"],
  "mutated_node_ids": [],
  "screenshot_refs": ["dashboard.png"]
}
```

Sem `file_key`, `file_url`, `created_node_ids`, `mutated_node_ids` ou
`inspected_node_ids`, o agente deve tratar a execucao como invalida.

## Exemplo

Primeiro configure o bridge:

```bash
./ai-devkit run figma-ui-ux-product-designer setup-figma-mcp-bridge \
  --install-bridge \
  --write-env \
  --login \
  --validate-live \
  --output-dir docs/figma-setup \
  --yes-create-dir
```

Depois execute uma capability de design:

```bash
FIGMA_MCP_ENABLED=true \
FIGMA_DIRECT_MODE=true \
FIGMA_MCP_BRIDGE_COMMAND="figma-mcp-bridge" \
./ai-devkit run figma-ui-ux-product-designer create-web-app-design \
  --brief demanda.md \
  --figma-file-name "Portal" \
  --require-direct \
  --yes-figma-write \
  --output-dir docs/design/portal \
  --yes-create-dir
```
