# Decision Rules: Plan Operational Action

## Objetivo de decisao

Gerar um plano operacional AWS sem executar mutacao. Esta capability e a porta
de entrada segura para discutir impacto, recurso alvo, rollback e proximos
passos antes de usar uma capability especifica.

## Entradas minimas

- `--operation` deve estar na allowlist de planejamento.
- `--resource-id` deve identificar exatamente o alvo.
- `--environment` e obrigatorio e deve ser explicito.
- `--output-dir` deve existir, ou a execucao deve receber `--yes-create-dir`.

## Quando executar

Execute quando:

- o usuario ainda esta avaliando uma acao AWS;
- a operacao precisa ser revisada antes de qualquer `--execute`;
- a operacao desejada esta entre as capabilities conhecidas.

Nao execute quando:

- `operation` estiver fora da allowlist;
- o usuario pedir mutacao imediata sem plano;
- `resource_id` ou `environment` estiverem ausentes;
- o pedido for destrutivo e o usuario espera execucao real.

## Regras de decisao

1. Esta capability nunca chama AWS.
2. Operacao fora da allowlist deve falhar, nao gerar plano generico.
3. `redrive-sqs-dlq` e `purge-sqs-queue-plan` devem sair como
   `blocked-plan-only`.
4. O plano deve declarar `execute: false`, `destructive` e `rollback_hint`.
5. O plano deve orientar a capability especifica a ser usada se o usuario
   decidir executar uma operacao permitida.
6. Nao aceitar aliases de ambiente que mascarem producao.

## Criterios de qualidade

- `operation-plan.md`, `operation-dry-run.json` e `rollback-notes.md` existem.
- `operation-dry-run.json` contem `operation`, `resource_id`, `environment`,
  `execute`, `status`, `destructive` e comando planejado.
- Nenhum artefato contem segredo, token ou payload bruto.

## Escalacao

Pedir confirmacao humana quando:

- o plano sera usado em `prd` ou `hml`;
- a operacao afeta capacidade, cache, schedule ou processamento de mensagens;
- o rollback depende de estado anterior que ainda nao foi coletado.
