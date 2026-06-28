# Decision Rules: Explain Query Plan

- Aceitar apenas `EXPLAIN` ou query read-only transformada em plano seguro.
- Bloquear `EXPLAIN ANALYZE` quando puder executar carga excessiva sem confirmacao explicita do contrato.
- Bloquear comandos de escrita, DDL, procedures e administrativos dentro do plano.
- Aplicar `statement_timeout` antes de solicitar plano.
- Destacar scans sequenciais, joins caros, filtros tardios, sorts e ausencia de indice.
- Nao recomendar criar indice como acao executavel; apenas registrar hipotese.
- Mascarar literais pessoais presentes na query antes de renderizar.
- Separar custo estimado de evidencia real de performance.
