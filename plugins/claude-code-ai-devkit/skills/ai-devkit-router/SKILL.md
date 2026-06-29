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

Use the plugin subagents in `plugins/claude-code-ai-devkit/agents/` when the
task benefits from isolated context:

- `agent-devkit-repo-explorer` for repository exploration and agent/capability
  inventory.
- `agent-devkit-db-analyst` for SQL Server, Postgres, or Supabase read-only
  analysis.
- `agent-devkit-pr-reviewer` for GitHub PR review in report-only mode.
- `agent-devkit-support-triage` for N1/N2 support triage.
- `agent-devkit-execution-reviewer` for final plan/result review.

Subagents must prefer Agent DevKit MCP tools when available. If MCP is not
available, they must call the thin plugin runtime script instead of duplicating
domain logic. They must preserve `write_policy`, `providers`, `risks`,
`fallback_applied`, and `next_steps` in their summaries.

If a provider is missing, ask for the minimum provider reference with
`agent provider configure`. If the user ignores the request, preserve the
runtime fallback result from `requires.providers`.

Never expose raw secrets. The runtime stores references only.
