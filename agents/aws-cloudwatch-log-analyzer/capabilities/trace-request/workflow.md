# Workflow: Trace Request

## Objetivo

Rastrear um request por identificador tecnico nos logs.

## Passos

1. Validar identificador e escopo.
2. Buscar eventos contendo o identificador.
3. Ordenar por timestamp.
4. Destacar erros e lacunas.

## Guardrails

- Nao usar dado pessoal como identificador sem justificativa.
- Manter janela restrita.
- Nao inferir eventos ausentes.
