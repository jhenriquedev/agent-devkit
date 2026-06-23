# Update Records

- Target database: <database name>
- Dry run: yes | no
- Status: - | updated
- Affected rows (preview): <count> [shown in dry-run; count(*) with same WHERE]
- Where: <where clause>

## Execution

- Re-run with `--execute` to update these records.
  (only present in dry-run output)

## Plan

- Path: <schema.table>
- Checksum: <sha256>
- Statements: <n>
- Blocked: no | yes — <reason>
- Destructive: no | yes — requires --confirm-destructive
- Transactional: yes | no
- Rollback path: - | <path>

### Operations

| command | preview |
|---|---|
| <verb> | <first 180 chars of statement> |

> Facts (runner): dry_run, affected_rows_preview, where_sql, plan.checksum, plan.blocked, plan.destructive
> Inferences (agent): risk assessment, recommendation to use migration for DDL changes
