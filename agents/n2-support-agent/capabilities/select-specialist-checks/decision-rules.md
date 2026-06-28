# Decision Rules

- Selecionar validacoes especialistas sem executar comandos.
- Selecionar N1 quando handoff estiver ausente, incompleto ou com gaps bloqueantes.
- Selecionar BPO quando houver proposta, documento, formalizacao, CCB ou sinal de pendencia operacional.
- Selecionar logs quando houver erro runtime, request id, correlation id ou janela temporal.
- Selecionar banco quando a hipotese envolver backend bug, inconsistencia de estado ou divergencia persistida.
- Nao selecionar banco sem possibilidade de query read-only explicita futura.
- Nao selecionar logs sem registrar quais entradas ainda faltam para execucao segura.
- Evitar validacoes redundantes que nao mudam a decisao N2.
- Registrar agente, capability, motivo e entradas necessarias por check.
- A saida deve ser diretamente consumivel por `execute-specialist-validation`.
