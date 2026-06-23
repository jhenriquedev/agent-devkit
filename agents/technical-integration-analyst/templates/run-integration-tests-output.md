# Plano de Testes de Integracao

- Execucao real: {true|false}
- Base URL: {base_url | {{base_url}}}

## Operacoes

- {METHOD} {/path}: {dry-run | HTTP_STATUS_CODE}
- {METHOD} {/mutation_path}: {dry-run | HTTP_STATUS_CODE}

<!-- Uma linha por operacao detectada no contrato.
     Status "dry-run" quando execute=false; status HTTP (200, 404, 500, etc.) quando execute=true.
     Sem operacoes = "Nenhuma operacao executavel detectada."
     Authorization e secrets NUNCA aparecem neste relatorio. -->
