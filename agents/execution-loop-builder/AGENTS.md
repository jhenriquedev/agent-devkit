# Execution Loop Builder

Instrucoes locais para trabalhar no agente `execution-loop-builder`.

## Responsabilidade

Este agente planeja, gera e revisa loops de execucao controlados: ciclos de
planejar, executar, observar, revisar e parar por criterios claros.

## Fora De Escopo

- Executar capabilities reais dentro do loop gerado no MVP.
- Criar orquestrador distribuido, fila cloud ou UI de monitoramento.
- Permitir loop sem budget de tempo e iteracao.
- Registrar loops de escrita externa como permissivos por padrao.

## Guardrails

- Todo loop deve ter `max_iterations`, `max_runtime_seconds` e `stop_when`.
- Side effects externos exigem dry-run, idempotencia e permissao explicita.
- Runner gerado deve persistir estado e auditoria por iteracao.
- Notificacao deve ser limitada para evitar spam.
- Registro no scheduler local so ocorre com `--execute`.
- Loops destrutivos ficam bloqueados por padrao.
