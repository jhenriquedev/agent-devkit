# Prompt: Invoke Lambda

## Objetivo
Invocar uma funcao Lambda (opcionalmente com payload), capturando StatusCode,
FunctionError e um HASH do payload de resposta — nunca o conteudo bruto.

## Entradas esperadas
- function_name, environment (req). Opcionais: payload (string), region, profile,
  execute, confirm_resource (= function_name).

## Passos de raciocinio
1. resource_id = function_name.
2. Dry-run: o payload aparece nos artefatos APENAS como "<redacted sha256=... bytes=...>".
   Confirmar que nenhum segredo aparece em plano/json.
3. Executar so com `--execute` + `--confirm-resource <function_name>` + ambiente.
4. Pos-execucao: ler post_check (StatusCode, FunctionError, ExecutedVersion,
   response_payload_hash). Se FunctionError != null, sinalizar falha do handler.

## Regras de decisao
- NUNCA imprimir o payload (entrada ou saida) bruto. So hash + bytes.
- Invoke nao tem rollback automatico: alertar sobre efeitos colaterais do handler
   antes de executar (especialmente em prd).
- Conta fora da allowlist => abortar.

## Formato de saida
Funcao, ambiente, StatusCode, FunctionError (se houver), hash do payload de resposta.
Caminho dos artefatos. Sem nenhum trecho de payload.

## NAO fazer
- Nao logar payload. Nao reexecutar "para testar" sem nova confirmacao.
