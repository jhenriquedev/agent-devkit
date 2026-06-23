# SQL Server Upsert Records

- Target database: <database name or ->
- Dry-run: yes | no
- Record count: <number of records>

## Plan

- Path: <input file path>
- Checksum: <sha256 hex>
- Statements: <count (one per record)>
- Blocked: yes | no
- Destructive: yes | no
- Transactional: yes | no
- Risk: blocked | high | medium | low
- Rollback path: -

## Operations

1. if: IF EXISTS (SELECT 1 FROM [schema].[table] WHERE [key] = ...) UPDATE ... ELSE INSERT ...
