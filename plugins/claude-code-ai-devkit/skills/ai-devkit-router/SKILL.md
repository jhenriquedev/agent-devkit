---
name: ai-devkit-router
description: Route support, infrastructure, data, documentation, integration, and development tasks through the local Agent DevKit runtime.
---

# Agent DevKit Router

Use this skill when a task belongs to software support, N1/N2 triage, AWS,
Azure DevOps, TOPdesk, BPO, SQL Server, Postgres, Elasticsearch, Figma,
Draw.io, Excel, presentations, technical integration, or software
specification.

Prefer `agent run` for deterministic execution. Use `agent` only when the
terminal runtime must route free-form language without host LLM support.

If a provider is missing, ask for the minimum provider reference with
`agent provider configure`. If the user ignores the request, preserve the
runtime fallback result from `requires.providers`.

Never expose raw secrets. The runtime stores references only.
