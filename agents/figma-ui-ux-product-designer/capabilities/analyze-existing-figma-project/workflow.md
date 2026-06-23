# Prompt — analyze-existing-figma-project

## OBJETIVO
Inspecionar projeto Figma existente e mapear reuso de design system antes de criar ou alterar.

## ENTRADAS
- `--figma-file-url`: URL do arquivo Figma (obrigatorio).
- `--output-dir`: pasta de saida.

## RACIOCINIO (passos)
1. Extraia o fileKey da URL fornecida; se invalido, solicite URL correta.
2. Detecte o modo Figma (`figma_mode.detect_mode`).
3. Em `direct_mcp`: acione o bridge com operacao `inspect_file`; execute:
   - `get_metadata`: paginas, nome do arquivo, data de modificacao.
   - `get_screenshot`: thumbnail visual do arquivo.
   - `get_libraries`: design systems vinculados.
   - `search_design_system`: tokens, componentes e estilos disponiveis.
4. Em `plan_only`: gere roteiro de inspecao para execucao manual no Figma.
5. Mapeie: paginas, frames principais, componentes reusaveis, variaveis/tokens, estilos de texto e cor.
6. Identifique oportunidades de reuso e gaps a preencher.

## REGRAS DE DECISAO
- Esta capability e read_only: NUNCA mutate o arquivo nesta operacao.
- Se nao houver fileKey valido na URL, solicite a URL correta antes de continuar.
- Registre somente node IDs retornados pelo bridge; nunca invente IDs.

## SAIDA
- `screen-inventory.md`: paginas e frames mapeados.
- `design-system-spec.md`: tokens, componentes e estilos encontrados (mapeado).
- `figma-action-plan.md`: proximos passos recomendados com base na analise.

## NAO FACA
- Nao invente node IDs ou nomes de componentes; cite somente o que o bridge retornou.
- Nao altere o arquivo Figma nesta capability.
