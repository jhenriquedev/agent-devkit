# SQL Server Update Records

- Target database: <database name or ->
- Dry-run: yes | no
- Where: <where clause>
- Max affected rows: <limit>

Re-run with `--execute` after reviewing affected rows.

## Plan

- Path: <schema.table>
- Checksum: <sha256 hex>
- Statements: 1
- Blocked: yes | no
- Destructive: yes | no
- Transactional: yes | no
- Risk: blocked | high | medium | low
- Rollback path: -

## Operations

1. update: UPDATE [schema].[table] SET [col] = N'val' WHERE <where clause>;
