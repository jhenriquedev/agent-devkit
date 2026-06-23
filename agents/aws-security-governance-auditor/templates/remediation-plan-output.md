# AWS Security Remediation Plan — Contrato de Saída

> Este plano NÃO executa correções. É um roteiro manual/revisável.
> Inferências (agente): agrupamento e ordenação por severidade.

## Formato real emitido por `render_remediation_plan` (report_renderer.py)

```
# AWS Security Remediation Plan

Este plano nao executa correcoes. Use como roteiro manual/revisavel.

## Critical

- <title> em `<resource_id>`
  - Ação proposta: <recommendation>
  - Validação: executar nova auditoria read-only após remediação.

## High

...
```

## Artefatos gerados

- `remediation-plan.md` — plano agrupado por severidade (critical → info)

## Quality gates esperados

- `remediation_is_plan_only`: execution=unsupported, sem automação
- `secrets_redacted`: nenhum material sensível impresso
