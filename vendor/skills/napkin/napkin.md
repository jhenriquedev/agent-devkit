# Napkin Runbook

## Curation Rules
- Re-prioritize on every read.
- Keep recurring, high-value notes only.
- Max 10 items per category.
- Each item includes date + "Do instead".

## Execution & Validation (Highest Priority)
1. **[2026-06-20] Validate agent capabilities through `agent`**
   Do instead: when testing a capability, execute it through `agent run <agent> <capability>` before using lower-level integration CLIs.
2. **[2026-06-21] Excel artifact-tool Node scripts may keep handles alive**
   Do instead: guard `run_node_script()` calls with timeouts and make successful JS runners call `process.exit(0)` after awaited saves.
3. **[2026-06-21] `unittest discover` does not find repo tests**
   Do instead: run `python3 -m unittest $(rg --files -g 'test*.py' -g '!vendor/**')` for the project suite.

## Shell & Command Reliability
1. **[2026-06-20] Azure DevOps SSL can fail through Python urllib**
   Do instead: use the repository's curl-backed transport for Azure DevOps API calls in local/serverless execution.
2. **[2026-06-27] Runtime `--source` can conflict with capability domain args**
   Do instead: intercept `--source` only for capabilities that explicitly support Agent DevKit source registry injection; otherwise leave it for the runner domain contract.

## Domain Behavior Guardrails
1. **[2026-06-28] Agentes devem ser agnosticos de cliente/projeto**
   Do instead: mover nomes de produto, cliente, URLs, paths locais, regras de elegibilidade e campos XML especificos para provider/config/env antes de versionar o agente.
2. **[2026-06-20] Azure card descriptions may include sensitive production log data**
   Do instead: retrieve the complete card for validation, but summarize PII-heavy log payloads in user-facing responses unless raw content is explicitly required.
3. **[2026-06-21] N1 restrictive-base uses a scoped SQL Server override**
   Do instead: when the N1 agent checks the restrictive base, prefer `DB_RESTRICTIVE_CONN_STRING` only in the subprocess environment for `sqlserver-data-analyzer`, without changing the global SQL Server analyzer default.

## User Directives
1. **[2026-06-22] Implement agentic specs individually**
   Do instead: process one `docs/agentic/*_plan.md` spec at a time with agent-specific analysis, tests, implementation, and review; do not use broad multi-agent waves or mechanical generation.
2. **[2026-06-22] Use Agent DevKit agents for work**
   Do instead: route every current and future activity through the relevant Agent DevKit agent/capability before doing direct ad-hoc work.
3. **[2026-06-20] Keep generated docs out of final project versioning**
   Do instead: treat `docs/` as local development/generated artifact space and keep it ignored.
