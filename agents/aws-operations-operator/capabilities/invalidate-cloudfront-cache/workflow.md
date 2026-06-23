# Workflow: Invalidate CloudFront Cache

## Passos
1. Verificar que `--distribution-id`, `--paths` e `--environment` foram fornecidos.
   Se faltar, parar e perguntar.
2. resource_id = distribution_id. Paths sao split por espaco.
3. Dry-run: mostrar o comando exato. CloudFront e global — region nao e anexado
   (comportamento correto do repository).
4. Se paths == `/*`, confirmar intencao do usuario (custo elevado e thundering herd).
5. Para executar: exigir `--execute` + `--confirm-resource <distribution_id>` + ambiente.
   Lembrar que invalidation nao pode ser desfeita; aguardar propagacao.
6. Conta fora da allowlist => abortar antes de qualquer mutacao.

## Regras de decisao
- `/*` sem confirmacao explicita => perguntar antes de aceitar.
- Sem confirm-resource => nao executar.
- Conta fora da allowlist => abortar.

## Criterio de parada
Abortar se: falta input, conta invalida, confirm-resource incorreto.
