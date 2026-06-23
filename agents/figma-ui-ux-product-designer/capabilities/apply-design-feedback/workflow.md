# Prompt — apply-design-feedback

## OBJETIVO
Aplicar feedback de design classificado em arquivo Figma existente, sem destruir versao validada.

## ENTRADAS
- `--source`: feedback em texto ou triagem existente.
- `--figma-file-url`: arquivo Figma a atualizar.
- `--yes-figma-write`: confirmacao para escrita.

## RACIOCINIO (passos)
1. Se nao houver triagem previa, execute `triage-design-feedback` primeiro.
2. Inspecione o arquivo Figma: paginas, frames, estado atual (`analyze-existing-figma-project`).
3. Filtre itens aplicaveis: Visual, UX, Acessibilidade, Handoff (prioridade critico e alto primeiro).
4. Para itens Negocio: NAO aplique; registre pergunta e aguarde confirmacao.
5. Crie nova pagina/frame "Feedback v[N]" em vez de sobrescrever.
6. Em `direct_mcp` + `--yes-figma-write`:
   - Aplique mudancas com `update_screen` via bridge; capture `mutated_node_ids`.
7. Execute checklist de qualidade pos-aplicacao.

## REGRAS DE DECISAO
- Inspecionar ANTES de alterar: obrigatorio.
- Mudancas destrutivas: PROIBIDAS.
- Itens Negocio: aguardar confirmacao antes de aplicar.
- Confirmar escrita antes de qualquer mutacao.

## SAIDA
- `dev-handoff.md` atualizado, `design-quality-report.md`, `feedback-triage.md` (status atualizado).
- Em `direct_mcp`: `+ figma-execution-result.json`, `design-operation-log.md`.

## NAO FACA
- Nao aplique mudanca de regra de negocio sem confirmacao.
- Nao sobrescreva o original sem versionar.
