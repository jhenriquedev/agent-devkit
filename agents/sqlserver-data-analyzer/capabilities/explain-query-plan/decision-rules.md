# Decision Rules: Explain Query Plan

- Explicar plano apenas para consulta read-only validada.
- Usar mecanismo logico/seguro do agente; nao executar escrita para obter plano.
- Bloquear comandos de escrita, DDL, `MERGE`, `EXEC`, `DBCC`, `BACKUP` e `RESTORE`.
- Aplicar timeout de statement/conexao e `LOCK_TIMEOUT`.
- Preservar `TOP` ou filtros existentes; nao ampliar a query.
- Destacar scans, joins caros, sort, lookup, falta de indice e filtros tardios quando presentes.
- Separar custo estimado de evidencia real de performance.
- Mascarar literais pessoais e segredos antes de renderizar a query.
- Nao recomendar criar indice como acao executada; apenas apontar hipotese.
- Quando a query for insegura, bloquear e sugerir reescrita read-only.
