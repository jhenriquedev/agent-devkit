# Prompt: Generate Operation Report

## Objetivo
Gerar `operation-report.md` consolidando os artefatos de uma operacao ja executada
ou planejada (le operation-dry-run.json e operation-result.json se existir).

## Entradas esperadas
operation_dir (req): diretorio com os artefatos da operacao. Opcional: output_dir.

## Passos de raciocinio
1. Ler operation-dry-run.json (sempre) e operation-result.json (se executou).
2. Renderizar o relatorio com: operacao, recurso, ambiente, conta validada,
   preflight, post-check e resultado (returncode/stdout resumido/lambda_response).
3. Capability read-only: nao executa nenhuma mutacao nem chama AWS.

## Regras de decisao
- Se operation-result.json ausente => relatorio de uma operacao apenas planejada.
- Nunca incluir payload bruto; apenas hashes ja presentes nos artefatos.

## Formato de saida
Caminho do operation-report.md gerado e um resumo de 3-5 linhas do que a operacao fez.

## NAO fazer
- Nao re-executar a operacao. Nao expor secrets/payloads.
