# Workflow: Scale Auto Scaling Group

## Passos
1. Verificar que `--auto-scaling-group`, `--desired-capacity` e `--environment`
   foram fornecidos. Se faltar, parar e perguntar.
2. resource_id = auto_scaling_group.
3. Dry-run: mostrar a capacidade alvo e o comando `autoscaling set-desired-capacity
   --honor-cooldown`. Ler preflight (describe-auto-scaling-groups) para comparar
   capacidade atual vs solicitada, e verificar min/max do grupo.
4. ALERTAR se desired_capacity = 0 (scale-to-zero = servico fora do ar).
   Em prd/hml, exigir confirmacao adicional antes de aceitar execucao com 0.
5. Para executar: exigir `--execute` + `--confirm-resource <asg_name>` + ambiente.
   Em prd, destacar impacto e cooldown.
6. Comparar capacidade preflight vs post-check.

## Regras de decisao
- desired_capacity = 0 em prd/hml => confirmar impacto de indisponibilidade.
- Conta fora da allowlist => abortar.
- Sem confirm-resource => nao executar.

## Criterio de parada
Abortar se: falta input, conta invalida, confirm-resource incorreto.
