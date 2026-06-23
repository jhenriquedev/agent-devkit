# Prompt — facelift-existing-product

## OBJETIVO
Modernizar produto existente autorizado: identificar problemas, propor melhorias visuais/UX e gerar comparativo.

## ENTRADAS
- `--source`: screenshots, PDFs ou arquivo Figma do produto atual.
- `--figma-file-url`: arquivo Figma existente a inspecionar (opcional).
- `--brief`: contexto, objetivo do facelift, restricoes de marca.
- `--yes-figma-write`: confirmacao para escrita real.

## RACIOCINIO (passos)
1. Confirme permissao: produto proprio ou autorizado.
2. Capture/inventarie estado atual: telas, fluxos, design system existente ou ausente.
3. Identifique problemas por categoria (`feedback-rubric.md`): Visual (hierarquia, contraste, espacamento), UX (fluxo, estados), Acessibilidade (`accessibility-rules.md`).
4. Proponha melhorias; separe o que preservar (regras de negocio, identidade de marca) do que mudar.
5. Crie estrutura: pagina "Current" (estado original) + pagina "Facelift v1" (melhorias).
6. Em `direct_mcp` + `--yes-figma-write`: aplique iteracoes no Figma; capture node IDs.
7. Gere comparativo antes/depois e handoff.

## REGRAS DE DECISAO
- Produto de terceiro sem autorizacao: PROIBIDO.
- Mudancas em regras de negocio: confirmar com PO antes de aplicar.
- Prefira nova pagina/versao a sobrescrever o original.

## SAIDA
- `facelift-plan.md`, `design-system-spec.md`, `dev-handoff.md`, `design-quality-report.md`.
- Em `direct_mcp`: `+ figma-execution-result.json`, `design-operation-log.md`.

## NAO FACA
- Nao prossiga sem confirmar permissao.
- Nao altere regras de negocio sem confirmacao.
