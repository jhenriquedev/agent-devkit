# Figma Action Plan
<!-- Template de referencia — o runner gera este arquivo em render_figma_action_plan().
     Modo e passos sao preenchidos em runtime. -->

## Modo
<!-- [runtime] direct_mcp | local_mcp_bridge | plan_only | blocked -->

## Execucao Real (somente em direct_mcp)
<!-- [runtime] status, file_url, page_name, created_node_ids, mutated_node_ids, screenshot_refs -->
- Status: <!-- [runtime] -->
- Figma file: <!-- [runtime] -->
- Created node IDs: <!-- [runtime] -->

## Passos

### Em direct_mcp
1. Carregar skill figma-use antes de qualquer escrita.
2. Se novo arquivo necessario: carregar figma-create-new-file e resolver planKey.
3. Inspecionar arquivo existente com metadata/screenshot antes de alterar.
4. Buscar libraries, componentes, variaveis e estilos (get_libraries / search_design_system).
5. Criar ou atualizar frames incrementalmente com use_figma.
6. Capturar node IDs criados/alterados e gerar handoff.

### Em plan_only / local_mcp_bridge
1. Usar este arquivo como roteiro para uma sessao com Figma MCP ativo.
2. Criar arquivo Figma ou abrir o existente indicado.
3. Criar paginas: Discovery, Design System, Flows, Screens, Review, Handoff.
4. Aplicar screen-inventory.md e design-system-spec.md.
5. Validar com design-quality-report.md antes de aprovar.

## Pendencias
<!-- [runtime] itens bloqueados por decisao de negocio ou ambiente -->
