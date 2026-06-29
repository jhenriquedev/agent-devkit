# Agent DevKit Claude Code Plugin

Adaptador fino para o Claude Code descobrir e usar o runtime local do AI
DevKit.

O plugin fornece um router skill, comandos de orientacao e scripts que delegam
para `agent`.

Ele tambem inclui subagentes Claude Code em `agents/` para isolar contexto de
exploracao, banco, PR, suporte e revisao final. Esses subagentes continuam
usando o Agent DevKit como fonte da verdade: preferem MCP quando disponivel e,
como fallback atual, chamam `scripts/run-capability.py`.

## Comandos

```bash
python3 scripts/bootstrap.py
python3 scripts/doctor.py --json
python3 scripts/run-capability.py --json elasticsearch-log-analyzer search-log-events --source app --from 2026-06-27T00:00:00Z --to 2026-06-27T01:00:00Z
```

## Subagentes

- `agent-devkit-repo-explorer`
- `agent-devkit-db-analyst`
- `agent-devkit-pr-reviewer`
- `agent-devkit-support-triage`
- `agent-devkit-execution-reviewer`

Eles sao opcionais e conservadores. Nao devem executar escrita externa sem
confirmacao, nao devem ignorar `write_policy` e nao devem duplicar a logica dos
agentes em `agents/`.

A instalacao recomendada pelo runtime e:

```bash
agent install project --target . --host claude-code
agent install global --host claude-code
```

Credenciais devem ser configuradas progressivamente com
`agent provider configure`.
