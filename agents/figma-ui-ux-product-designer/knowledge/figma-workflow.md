# Figma Workflow

## Direct Mode

Use quando o ambiente expuser ferramentas Figma e o usuario autorizar escrita.

1. Detectar `FIGMA_MCP_ENABLED=true` ou capacidade equivalente no ambiente.
2. Para novo arquivo, usar o fluxo `figma-create-new-file`.
3. Para arquivo existente, extrair `fileKey` e `nodeId` da URL.
4. Inspecionar com metadata/screenshot antes de escrever.
5. Buscar libraries, componentes, variaveis e estilos antes de desenhar do zero.
6. Escrever incrementalmente com `use_figma`.
7. Retornar node IDs criados/alterados.
8. Gerar handoff e quality report.

## Plan Only

Use quando nao houver MCP, token, plano Figma ou permissao de escrita.

1. Gerar `figma-action-plan.md`.
2. Gerar `design-brief.md`, inventario de telas e mapas.
3. Gerar scripts/conteudo que um agente com Figma conectado possa executar.
4. Marcar claramente o que depende de execucao futura no Figma.

## URL Capture

Para URL propria, localhost ou sistema com permissao:

1. Confirmar permissao e escopo.
2. Criar/selecionar arquivo Figma.
3. Capturar URL com `generate_figma_design` quando disponivel.
4. Recriar/editabilizar com `use_figma` e design system.
5. Gerar comparativo antes/depois quando for facelift.
