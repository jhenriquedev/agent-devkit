# Rollback Migration

- Target database: <database name>
- Dry run: yes | no
- Migration ID: <id derived from filename without .down.sql>
- Status: - | rolled_back

## Execution

- Re-run with `--execute` to roll back this migration.
  (only present in dry-run output)

## Plan

- Path: <path to .down.sql>
- Checksum: <sha256>
- Statements: <n>
- Blocked: no | yes
- Destructive: no | yes
- Transactional: yes | no
- Rollback path: -

### Operations

| command | preview |
|---|---|
| <verb> | <first 180 chars of statement> |

> Facts (runner): dry_run, migration_id, status, plan.checksum, plan.blocked
> Inferences (agent): confirmation that history was updated to rolled_back
