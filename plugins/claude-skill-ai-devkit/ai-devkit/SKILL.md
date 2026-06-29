---
name: ai-devkit
description: Route software support, infrastructure, data, documentation, integration, and development tasks through Agent DevKit practices in Claude Desktop or Claude.ai. Use when the user asks about incidents, N1/N2 triage, AWS, Azure DevOps, TOPdesk, BPO, SQL Server, Postgres, Elasticsearch, Figma, Draw.io, Excel, presentations, technical integration, specifications, providers, credentials, fallbacks, or Agent DevKit agent selection.
---

# Agent DevKit

Use this skill as a thin analytical adapter. Prefer Agent DevKit's deterministic
runtime when local tools are available; otherwise produce plans, commands,
queries, runbooks, and manual steps without pretending local execution happened.

## Workflow

1. Classify the request by domain and select the most specific Agent DevKit agent.
2. If local execution is available, prefer `agent run <agent> <capability>`.
3. If local execution is unavailable, use the same capability contract to
   produce `plan_only`, `manual_steps`, or `use_user_supplied_context`.
4. Ask only for the provider credential needed for the current task.
5. Never ask the user to configure every provider upfront.
6. Never print or persist raw secrets.

## References

- For routing rules, read `references/routing.md`.
- For provider and credential behavior, read `references/providers.md`.
- For support workflows, read `references/sustentacao.md`.
- For infrastructure workflows, read `references/infra.md`.
- For development/specification workflows, read `references/desenvolvimento.md`.
- For Claude Code subagent patterns, read `references/subagents.md`.
