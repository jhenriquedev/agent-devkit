# Upsert Records

- Target database: <database name>
- Dry run: yes | no
- Status: - | upserted
- Record count: <n>

## Execution

- Re-run with `--execute` to upsert these records.
  (only present in dry-run output)
- Records above max_affected_rows (default 1000) require --max-affected-rows.
- Destructive ops require --confirm-destructive.

## Plan

- Path: <input file>
- Checksum: <sha256>
- Statements: <n>
- Blocked: no | yes
- Destructive: no | yes
- Transactional: yes | no

### Operations

| command | preview |
|---|---|
| insert | INSERT INTO <schema>.<table> (...) VALUES ... ON CONFLICT ... |

> Facts (runner): dry_run, record_count, status, plan.checksum
> Inferences (agent): type casting warnings (all values treated as text), volume check
