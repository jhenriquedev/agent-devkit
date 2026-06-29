# Context

Automacoes Python no Agent DevKit existem para poupar contexto de LLM em tarefas
conhecidas e repetitivas. Elas devem ser pequenas, auditaveis e facilmente
convertidas em capabilities quando se tornam parte do produto.

Classificacao de idempotencia:

- `safe-repeat`: pode rodar varias vezes sem novo efeito colateral.
- `creates-artifact`: cria arquivo novo ou versionado.
- `updates-local`: altera estado local.
- `external-write`: altera sistema externo.
- `destructive`: apaga ou sobrescreve dados.

Essa classificacao orienta dry-run, confirmacao e `write_policy`.
