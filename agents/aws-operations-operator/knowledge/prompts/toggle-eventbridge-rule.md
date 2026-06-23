# Prompt: Toggle EventBridge Rule

## Objetivo
Habilitar ou desabilitar uma rule do EventBridge (`events enable-rule` /
`events disable-rule`).

## Entradas esperadas
rule_name, action (enable|disable), environment (req). Opcionais: execute,
confirm_resource (= rule_name).

## Passos de raciocinio
1. resource_id = rule_name. Validar action em {enable, disable} (o repository tambem valida).
2. Dry-run: ler preflight (describe-rule) para conhecer o estado atual.
3. Explicar consequencia: disable de uma rule de schedule pausa o job; enable o
   reativa. O rollback e simplesmente a action oposta.
4. Executar so com `--execute` + `--confirm-resource` + ambiente.

## Regras de decisao
- Em prd, ao desabilitar uma rule critica (ex.: jobs de cobranca/limpeza), alertar
  sobre o efeito de pausar o agendamento.
- Conta fora da allowlist => abortar.

## Formato de saida
Rule, action, ambiente, estado antes->depois, e como reverter (action oposta).
Caminho dos artefatos.

## NAO fazer
- Nao aceitar action diferente de enable/disable. Nao executar sem confirmacao.
