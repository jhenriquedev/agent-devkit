# Knowledge

Conhecimento operacional do agente Database Change Operator.

Esta pasta concentra o contexto que um agente consumidor deve carregar antes de
executar mudancas em banco:

- `context.md`: premissas e modelo mental da operacao.
- `policies.yaml`: guardrails de escrita, bloqueios e timeouts.
- `prompts/`: prompts por capability para uso por agentes externos.

O conhecimento aqui nao guarda credenciais, strings de conexao ou payloads reais
de banco.
