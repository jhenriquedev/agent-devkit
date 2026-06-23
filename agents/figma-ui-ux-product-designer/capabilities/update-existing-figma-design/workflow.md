# Prompt — update-existing-figma-design

## OBJETIVO
Evoluir arquivo Figma existente sem destruir o design validado.

## ENTRADAS
- `--figma-file-url`: arquivo Figma a evoluir (obrigatorio).
- `--brief`: descricao das mudancas desejadas.
- `--source`: fontes de referencia das mudancas.
- `--yes-figma-write`: confirmacao para escrita.

## RACIOCINIO (passos)
1. Inspecione o arquivo (`analyze-existing-figma-project`): paginas, frames, componentes, versao atual.
2. Defina o plano de mudancas: o que alterar, o que preservar, nova pagina/frame ou edicao inline.
3. Prefira criar nova versao/pagina/frame em vez de sobrescrever design validado.
4. Em `direct_mcp` + `--yes-figma-write`:
   - Use `update_screen` via bridge; aplique mudancas incrementalmente.
   - Capture `mutated_node_ids` retornados.
5. Atualize `dev-handoff.md` com as mudancas e razoes.
6. Execute checklist de qualidade pos-edicao.

## REGRAS DE DECISAO
- Inspecionar ANTES de alterar: obrigatorio.
- Mudancas destrutivas (deletar frames validados): PROIBIDAS por padrao.
- Confirmar escrita antes de qualquer mutacao.
- Sem `mutated_node_ids` retornados: NAO afirme que o arquivo foi alterado.

## SAIDA
- `dev-handoff.md` atualizado, `design-quality-report.md`.
- Em `direct_mcp`: `+ figma-execution-result.json`, `design-operation-log.md`.

## NAO FACA
- Nao altere sem inspecionar o estado atual primeiro.
- Nao sobrescreva artefatos validados sem criar versao anterior.
