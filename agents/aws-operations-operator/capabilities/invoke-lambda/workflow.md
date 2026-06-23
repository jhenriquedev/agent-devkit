# Workflow: Invoke Lambda

## Passos
1. Verificar que `--function-name` e `--environment` foram fornecidos.
   Se faltar, parar e perguntar.
2. resource_id = function_name.
3. Dry-run: verificar que o payload (se fornecido) aparece APENAS como
   "<redacted sha256=... bytes=...>" nos artefatos — nunca o conteudo bruto.
4. Para executar: exigir `--execute` + `--confirm-resource <function_name>` + ambiente.
   Antes de executar em prd, alertar sobre efeitos colaterais irreversiveis do handler.
5. Pos-execucao: ler post_check (StatusCode, FunctionError, ExecutedVersion,
   response_payload_hash). Se FunctionError != null, reportar falha do handler.

## Regras de decisao
- NUNCA imprimir payload de entrada ou saida — somente hash + bytes.
- Sem confirm-resource => nao executar.
- Conta fora da allowlist => abortar.
- FunctionError presente => falha explicita, mesmo com returncode 200.

## Criterio de parada
Abortar se: falta input, conta invalida, confirm-resource incorreto. Reportar erro
se FunctionError != null.
