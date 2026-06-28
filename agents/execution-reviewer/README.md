# Execution Reviewer

Agente de runtime responsavel por revisar plano, execucao e saida final de
atividades multiagente.

No runtime da CLI, este agente e acionado quando `review_gate.required = true`.
A revisao deve ser executada por um backend independente do produtor da resposta,
preferindo `claude-code` ou `codex-cli`.

O reviewer deve responder com `REVIEW OK` para aprovar ou `REVIEW BLOCKED` para
bloquear. Sem reviewer independente configurado, com decisao bloqueada, ou sem
uma decisao explicita `REVIEW OK`, a CLI retorna `needs-review` e nao conclui a
atividade como `ok`.
