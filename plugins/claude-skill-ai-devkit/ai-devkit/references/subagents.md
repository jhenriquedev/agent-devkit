# Subagentes Claude

Subagentes sao um recurso do Claude Code. Este skill de Claude Desktop/Claude.ai
permanece `skill-only` e nao tenta criar subagentes dinamicos.

Quando o usuario estiver em Claude Code, use os templates do plugin
`claude-code-ai-devkit/agents/`:

- `agent-devkit-repo-explorer`
- `agent-devkit-db-analyst`
- `agent-devkit-pr-reviewer`
- `agent-devkit-support-triage`
- `agent-devkit-execution-reviewer`

Regras:

- Agent DevKit continua sendo a fonte da verdade.
- Prefira MCP do Agent DevKit quando existir.
- Sem MCP, use `scripts/run-capability.py --json`.
- Preserve `write_policy`, providers, fallbacks, riscos e proximos passos.
- Nao conceda escrita externa por padrao.
