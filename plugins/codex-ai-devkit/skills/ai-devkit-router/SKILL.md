---
name: ai-devkit-router
description: Route support, infrastructure, data, documentation, integration, and development tasks through the local Agent DevKit runtime.
---

# Agent DevKit Router

Use this skill when a task belongs to software support, N1/N2 triage, AWS,
Azure DevOps, TOPdesk, BPO, SQL Server, Postgres, Elasticsearch, Figma,
Draw.io, Excel, presentations, technical integration, or software
specification.

## Routing

1. Prefer the most specific Agent DevKit agent/capability.
2. Inspect available agents with `agent agents list --json`.
3. Inspect capabilities with `agent capabilities list --agent <agent> --json`.
4. Execute deterministic work with `agent run <agent> <capability>`.
5. Use `agent provider status <provider> --json` before work that needs an
   external provider.

## Providers

Capabilities can declare `requires.providers`. If a provider is not configured,
ask only for the minimum needed credential reference, such as `--env NAME` or
`--env-file PATH`. If the user ignores the request, continue with the fallback
declared by the capability.

Never print or persist raw secret values. Use `agent provider configure` so the
runtime stores references only.

## Fallback

If a provider is missing, preserve the runtime fallback result. Do not retry by
calling external systems directly. Valid fallbacks include `plan_only`,
`dry_run`, `manual_steps`, `use_user_supplied_context`, `skip_provider`, and
`blocked`.

## Commands

- `agent doctor --json`
- `agent providers list --json`
- `agent provider status <provider> --json`
- `agent provider configure <provider> --env-file <path>`
- `agent --json run <agent> <capability> [args...]`
