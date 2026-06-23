# Database Write Permissions

- Target database: <database name>
- Dry run: yes | no
- Write permissions: - | yes | no
- Rolled back: - | yes
- Message: <present only in dry-run — describes what the real test would do>

## Checks

- create_temp_table
- insert
- update
- delete

> All checks run inside a transaction that is always rolled back — nothing is persisted.
> Facts (runner): dry_run, write_permissions, rolled_back, checks
> Inferences (agent): whether the connection is ready for write operations; recommend this before first write
