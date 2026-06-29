# Contexto

Loops podem ser manuais ou registrados no scheduler local existente. O scheduler
local ja existe no runtime como `task`/`scheduler`; este agente apenas gera
contratos e registra tasks quando solicitado.

## Contrato Minimo

- `id`
- `objective`
- `trigger`
- `budget.max_iterations`
- `budget.max_runtime_seconds`
- `side_effects.external_writes`
- `steps`
- `success_when`
- `stop_when`

## Estado Minimo

- ultima execucao;
- status;
- iteracoes;
- erros;
- artefatos;
- motivo de parada.
