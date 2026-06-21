# Execute N2 Investigation

## Fluxo

1. Carregar contrato N1, fixture ou card Azure.
2. Analisar codigo quando `--codebase-path` existir.
3. Correlacionar evidencias e codigo.
4. Classificar causa raiz.
5. Gerar `patch_plan.md`.
6. Preparar comentario, tag e anexo no Azure.
7. Executar mutacoes apenas com `--execute`.
