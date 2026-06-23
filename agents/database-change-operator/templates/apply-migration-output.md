# Apply Migration

- Target database: <database name>
- Dry run: yes | no
- Migration ID: <id derived from filename without .up.sql>
- Status: - | applied | already_applied
- Already applied: - | yes

## Execution

- Re-run with `--execute` to apply this migration.
  (only present in dry-run output)

## Plan

- Path: <path to .up.sql>
- Checksum: <sha256>
- Statements: <n>
- Blocked: no | yes — <reason>
- Destructive: no | yes — requires .down.sql
- Transactional: yes | no
- Rollback path: - | <path to .down.sql>

### Operations

| command | preview |
|---|---|
| <verb> | <first 180 chars of statement> |

> Facts (runner): dry_run, migration_id, status, already_applied, plan.checksum, plan.blocked, plan.destructive, plan.rollback_path
> Inferences (agent): whether to proceed, risk assessment, drift detection
