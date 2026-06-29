# Claude Code Agents

Este plugin usa o runtime central do Agent DevKit como fonte da verdade. Agentes
nativos do host devem ser pequenos, focados e conservadores. Eles nao duplicam
logica de `agents/`; apenas orientam o Claude Code a chamar o Agent DevKit por
MCP quando disponivel ou pelo script local `run-capability.py`.

## Subagentes incluidos

- `agent-devkit-repo-explorer`: explora repositorios e inventario de agentes.
- `agent-devkit-db-analyst`: analisa perguntas de banco usando capabilities
  read-only.
- `agent-devkit-pr-reviewer`: revisa Pull Requests por contrato do
  `github-pr-reviewer`.
- `agent-devkit-support-triage`: faz triagem N1/N2 sem assumir escrita externa.
- `agent-devkit-execution-reviewer`: revisa plano/resultado antes da resposta
  final.

## Guardrails

- Use o MCP `mcp__agent-devkit__capability_run` se ele existir na sessao.
- Se MCP nao existir, use apenas `python3 plugins/claude-code-ai-devkit/scripts/run-capability.py --json ...`.
- Nao use shell arbitrario para resolver uma tarefa coberta por capability.
- Preserve `write_policy`, `providers`, `fallback_applied`, `risks` e
  `next_steps` na resposta.
- Retorne resumo com evidencias; nao despeje logs completos.
- Reporte `blocked` quando a tarefa exigir permissao, provider ou escrita
  externa nao autorizada.

Observacao: em subagentes fornecidos por plugin, Claude Code ignora frontmatter
como `permissionMode` e `mcpServers`. Por isso estes templates restringem
ferramentas com `tools` e reforcam permissoes no prompt do subagente.
