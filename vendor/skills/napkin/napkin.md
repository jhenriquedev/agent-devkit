# Napkin Runbook

## Curation Rules
- Re-prioritize on every read.
- Keep recurring, high-value notes only.
- Max 10 items per category.
- Each item includes date + "Do instead".

## Execution & Validation (Highest Priority)
1. **[2026-06-20] Validate agent capabilities through `ai-devkit`**
   Do instead: when testing a capability, execute it through `./ai-devkit run <agent> <capability>` before using lower-level integration CLIs.
2. **[2026-06-21] `unittest discover` does not find repo tests**
   Do instead: run `python3 -m unittest $(rg --files -g 'test*.py' -g '!vendor/**')` for the project suite.

## Shell & Command Reliability
1. **[2026-06-20] Azure DevOps SSL can fail through Python urllib**
   Do instead: use the repository's curl-backed transport for Azure DevOps API calls in local/serverless execution.

## Domain Behavior Guardrails
1. **[2026-06-20] Azure card descriptions may include sensitive production log data**
   Do instead: retrieve the complete card for validation, but summarize PII-heavy log payloads in user-facing responses unless raw content is explicitly required.

## User Directives
1. **[2026-06-20] Keep generated docs out of final project versioning**
   Do instead: treat `docs/` as local development/generated artifact space and keep it ignored.
