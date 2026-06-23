# Prompt: Run Integration Tests

## OBJETIVO
Planejar e (sob autorização explícita) executar testes contra endpoints reais,
com relatório de resultado por operação.

## ENTRADAS
- Mesmas flags de origem (`--url`, `--file`, `--directory`, `--text`)
- `--execute` (flag — habilita execução real; padrão: dry-run)
- `--confirm-mutations` (flag — obrigatório para mutations reais)
- `--fixture <path>` (JSON de resultado pré-gravado para reprodução sem rede)
- `--output` (opcional)

## RACIOCÍNIO
1. Extraia contrato e monte plano por operação.
2. Padrão = dry-run: liste operação e se é mutation, sem chamar nada.
3. Execução real só com `--execute` E base URL/ambiente seguro definidos.
4. Mutations reais exigem `--confirm-mutations`.
5. Aceite `--fixture` para reproduzir resultado sem rede.

## RUBRICA / REGRAS DE DECISÃO
- Sem base URL → bloquear execução real com mensagem de erro clara.
- Sem `--confirm-mutations` com mutations presentes → bloquear e informar.
- Mascarar secrets em request (Authorization) e body_preview de response.
- Apresentar plano de operações antes de executar.

## SAÍDA
Markdown seguindo `run-integration-tests-output.md`:
execução real (bool), base URL mascarada, status por operação (dry-run | HTTP status).

## NÃO FAÇA
- Executar mutation sem `--confirm-mutations` e ambiente explícito.
- Logar headers de Authorization ou tokens completos no relatório.
