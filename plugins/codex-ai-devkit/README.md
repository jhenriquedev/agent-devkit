# Agent DevKit Codex Plugin

Adaptador fino para o Codex App descobrir e usar o runtime local do Agent DevKit.

O plugin nao implementa logica de dominio. Ele instala um router skill e scripts
que delegam para `agent`.

## Comandos

```bash
python3 scripts/bootstrap.py
python3 scripts/install-runtime.py project --target . --dry-run --json
python3 scripts/doctor.py --json
python3 scripts/resolve-capability.py --agent n1-support-agent
python3 scripts/run-capability.py --json elasticsearch-log-analyzer search-log-events --source app --from 2026-06-27T00:00:00Z --to 2026-06-27T01:00:00Z
```

A instalacao recomendada pelo runtime e:

```bash
agent install project --target . --host codex
agent install global --host codex
```

Credenciais continuam sob responsabilidade do runtime via
`agent provider configure`.
