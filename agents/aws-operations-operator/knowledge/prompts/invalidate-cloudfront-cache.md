# Prompt: Invalidate CloudFront Cache

## Objetivo
Criar uma invalidation de cache CloudFront (`cloudfront create-invalidation`) para um
ou mais paths.

## Entradas esperadas
distribution_id, paths (string separada por espaco), environment (req). Opcionais:
execute, confirm_resource (= distribution_id), profile.

## Passos de raciocinio
1. resource_id = distribution_id. Os paths sao split por espaco.
2. Dry-run: mostrar o comando e os paths. CloudFront e global — o region nao e
   anexado ao comando (comportamento do repository).
3. Executar so com `--execute` + `--confirm-resource <distribution_id>` + ambiente.
4. Lembrar: invalidation nao pode ser desfeita; aguardar propagacao.

## Regras de decisao
- Evitar `/*` amplo sem necessidade (custo + thundering herd no origin); se o usuario
  pedir `/*`, confirmar a intencao.
- Conta fora da allowlist => abortar.

## Formato de saida
Distribuicao, paths, ambiente, status da invalidation. Caminho dos artefatos.

## NAO fazer
- Nao prometer reversao. Nao invalidar `/*` por padrao.
