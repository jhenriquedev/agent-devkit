# Migration Report

- Target database: <database name>
- Count: <n>

## Migrations

| id | name | status | applied_at | rollback |
|---|---|---|---|---|
| <migration_id> | <filename> | applied \| rolled_back | <ISO timestamp> | yes \| no |

> Status values: applied, rolled_back
> Facts (runner): count, migrations[].id, name, status, applied_at, rollback_available
> Inferences (agent): whether expected migrations are present, drift detection
