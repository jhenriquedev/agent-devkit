# Run Write Script

- Target database: <database name>
- Dry run: yes | no
- Status: - | executed

## Execution

- Re-run with `--execute` to run this script.
  (only present in dry-run output)
- Add `--confirm-destructive` if the script contains DROP/TRUNCATE/DELETE.

## Plan

- Path: <path to .sql>
- Checksum: <sha256>
- Statements: <n>
- Blocked: no | yes — blocks execution
- Destructive: no | yes — requires --confirm-destructive
- Transactional: yes | no

### Operations

| command | preview |
|---|---|
| <verb> | <first 180 chars of statement> |

> Facts (runner): dry_run, status, plan.checksum, plan.blocked, plan.destructive
> Inferences (agent): whether to recommend migration instead, risk narrative
