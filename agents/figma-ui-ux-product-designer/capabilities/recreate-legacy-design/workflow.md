# Prompt — recreate-legacy-design

## OBJETIVO
Recriar design legado autorizado no Figma com comparativo antes/depois e rastreabilidade.

## ENTRADAS
- `--source`: screenshots, PDFs, arquivos do design legado.
- `--brief`: contexto e objetivo da recriacao.
- `--figma-file-name`: nome do arquivo Figma a criar.
- `--yes-figma-write`: confirmacao para escrita real.

## RACIOCINIO (passos)
1. Confirme permissao e escopo do material legado (proprio ou autorizado).
2. Inventarie o design legado: telas, fluxos, componentes, fontes, cores.
3. Identifique o que recriar fielmente versus o que modernizar (decida com o usuario se ambiguo).
4. Crie estrutura de paginas: "Legacy" (estado original) e "Recreation" (recriado).
5. Em `direct_mcp` + `--yes-figma-write`: acione bridge incrementalmente; capture node IDs.
6. Em `plan_only`: gere `figma-action-plan.md` com instrucoes passo a passo.
7. Gere comparativo e source-traceability.md.

## REGRAS DE DECISAO
- Clone de produto de terceiro sem permissao: PROIBIDO.
- Material legado proprio ou autorizado: permitido com confirmacao de escrita.
- Ambiguidade sobre o que preservar vs modernizar → pergunte antes de agir.

## SAIDA
- `facelift-plan.md`, `design-system-spec.md`, `dev-handoff.md`, `design-quality-report.md`.
- Em `direct_mcp`: `+ figma-execution-result.json`, `design-operation-log.md`.

## NAO FACA
- Nao prossiga sem confirmar permissao do material de origem.
- Nao decida modernizacoes sem alinhamento com o usuario.
