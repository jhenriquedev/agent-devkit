# Migration Plan

## Plan

- Path: <path to .up.sql>
- Target database: <database name>
- Checksum: <sha256>
- Statements: <n>
- Blocked: no | yes — <matched pattern>
- Destructive: no | yes
- Transactional: yes | no
- Rollback path: - | <path to .down.sql>

## Operations

| command | preview |
|---|---|
| <verb> | <first 180 chars of statement> |

> Facts (runner): checksum, statement_count, blocked, destructive, transactional, rollback_path
> Inferences (agent): risk narrative, recommendation to add .down.sql if destructive
