# Workflow: Toggle EventBridge Rule

## Passos
1. Verificar que `--rule-name`, `--action` (enable|disable) e `--environment`
   foram fornecidos. Se faltar, parar e perguntar.
2. resource_id = rule_name. Validar action em {enable, disable}.
3. Dry-run: ler preflight (describe-rule) para conhecer o estado atual da rule.
4. Explicar consequencia: disable pausa agendamentos/triggers; enable os reativa.
   O rollback e a action oposta.
5. Em prd, ao desabilitar rule critica (cobranca, limpeza, compliance), alertar
   sobre o efeito de pausar o agendamento.
6. Para executar: exigir `--execute` + `--confirm-resource <rule_name>` + ambiente.

## Regras de decisao
- action fora de {enable, disable} => recusar (repository tambem valida).
- Sem confirm-resource => nao executar.
- Conta fora da allowlist => abortar.

## Criterio de parada
Abortar se: action invalida, falta input, conta invalida, confirm-resource incorreto.
