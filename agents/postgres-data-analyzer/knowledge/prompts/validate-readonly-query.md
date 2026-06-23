# Prompt: validate-readonly-query

> Operação read-only. Não execute — apenas valide. Nunca relaxe os bloqueios.

## Objetivo
Validar se uma query é segura para execução read-only (sem keywords de escrita,
começando com SELECT/WITH/EXPLAIN) e reportar a query final após enforce_limit,
antes de qualquer execução real.

## Entradas esperadas
- `query` (obrigatório): a query a validar.
- `limit` (default 100): limite a aplicar via enforce_limit.

## Passos de raciocínio
1. Execute `validate-readonly-query` com a query e o limit.
2. Se válida: exiba `Valid: sim`, a query final (com LIMIT aplicado) e o limite usado.
3. Se inválida (contém keyword bloqueada ou não inicia com SELECT/WITH/EXPLAIN):
   - Explique o motivo da recusa.
   - Identifique a keyword bloqueada.
   - Proponha reescrita read-only se possível.

## Regras de decisão
- Keywords bloqueadas: INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, GRANT,
  REVOKE, VACUUM, CALL, DO, COPY — bloquear sempre, sem exceção.
- Query válida deve iniciar com SELECT, WITH ou EXPLAIN.
- Nunca aprove query de escrita, mesmo que "apenas para teste".

## Saída
- **Se válida:**
  ```
  - Valid: sim
  - Limite aplicado: N
  ```
  ```sql
  <query final após enforce_limit>
  ```
- **Se inválida:**
  ```
  - Valid: não
  - Motivo: keyword bloqueada '<keyword>' / não inicia com SELECT/WITH/EXPLAIN
  ```
  Reescrita sugerida (se aplicável).

## NÃO faça
- Não execute a query no banco.
- Não aprove queries com keywords de escrita sob nenhuma justificativa.
- Não remova o LIMIT da query validada.
