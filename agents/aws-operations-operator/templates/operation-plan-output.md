# AWS Operation Plan

> Gerado dinamicamente por `report_renderer.render_operation_plan(payload)`.
> Este template documenta o contrato de saida do artefato `operation-plan.md`.

## Campos

- **Operation**: id da operacao (ex.: `force-ecs-deployment`)
- **Resource**: resource_id alvo (ex.: `orders/orders-api`)
- **Environment**: ambiente (dev | hml | prd)
- **Region**: regiao AWS resolvida (ou `-` se nao aplicavel)
- **Profile**: perfil AWS (ou `-` se padrao)
- **Status**: `planned` | `blocked-plan-only` | `executed`
- **Execute**: `False` (dry-run) ou `True` (executado)
- **Destructive**: `True` para purge/redrive; `False` para demais

## Secao AWS Command

```bash
aws <servico> <acao> [--args...] [--region <r>] [--output json]
```

Payloads de Lambda aparecem como `<redacted sha256=... bytes=...>`.
Operacoes destrutivas exibem o comando mas nao permitem execucao no MVP.

## Artefatos relacionados

- `operation-dry-run.json` — payload estruturado completo
- `rollback-notes.md` — orientacao de reversao
- `operation-result.json` — presente apenas quando `execute: True`
- `operation-report.md` — gerado por `generate-operation-report`
