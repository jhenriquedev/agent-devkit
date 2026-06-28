# Agent DevKit Claude Code Plugin

Adaptador fino para o Claude Code descobrir e usar o runtime local do AI
DevKit.

O plugin fornece um router skill, comandos de orientacao e scripts que delegam
para `agent`.

## Comandos

```bash
python3 scripts/bootstrap.py
python3 scripts/doctor.py --json
python3 scripts/run-capability.py --json elasticsearch-log-analyzer search-log-events --source app --from 2026-06-27T00:00:00Z --to 2026-06-27T01:00:00Z
```

A instalacao recomendada pelo runtime e:

```bash
agent install project --target . --host claude-code
agent install global --host claude-code
```

Credenciais devem ser configuradas progressivamente com
`agent provider configure`.
