# Prompt: Scale Auto Scaling Group

## Objetivo
Ajustar a desired capacity de um Auto Scaling Group
(`autoscaling set-desired-capacity --honor-cooldown`).

## Entradas esperadas
auto_scaling_group, desired_capacity (int), environment (req). Opcionais: execute,
confirm_resource (= auto_scaling_group).

## Passos de raciocinio
1. resource_id = auto_scaling_group.
2. Dry-run: mostrar a capacidade alvo. Ler preflight (describe-auto-scaling-groups)
   para conhecer a capacidade atual e min/max.
3. ALERTAR se desired_capacity = 0 (scale-to-zero = derruba o servico) ou se exceder
   o max do grupo.
4. Executar so com `--execute` + `--confirm-resource` + ambiente. Em prd, destacar
   impacto de capacidade e o cooldown honrado.

## Regras de decisao
- desired_capacity = 0 em prd/hml => exigir confirmacao reforcada e explicar o
  impacto (indisponibilidade).
- Conta fora da allowlist => abortar.

## Formato de saida
ASG, capacidade atual->alvo, ambiente, status. Diff preflight->post-check. Caminho
dos artefatos.

## NAO fazer
- Nao escalar para 0 silenciosamente. Nao ignorar min/max do grupo.
