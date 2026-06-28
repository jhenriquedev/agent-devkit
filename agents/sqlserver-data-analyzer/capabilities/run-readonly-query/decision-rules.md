# Decision Rules: run-readonly-query

## Rubrica de quando validar antes de executar

| Origem da query | Ação |
|---|---|
| Digitada pelo usuário em texto livre | Rodar `validate-readonly-query` antes |
| Gerada por `build-analysis-query` | Pode ir direto |
| Copiada de fonte confiável e revisada | Pode ir direto (baixo risco) |
| Contém subquery complexa ou joins de múltiplas tabelas | Recomendar `validate-readonly-query` |

## Regras de decisão

1. `row_count == limit` → avisar que pode haver mais linhas; sugerir WHERE mais
   específico.
2. Colunas com `sensitive_kind` no resultado → mascarar na saída; nunca exibir
   CPF, CNPJ, email, telefone, nome, endereço, token ou senha brutos.
3. Se `SqlServerRepositoryError` (keyword bloqueada) → parar, reportar keyword
   sem executar, sugerir reformulação.
4. Timeout → reportar sem revelar credenciais; sugerir simplificar query.
5. Não remover TOP nem desabilitar timeouts em nenhuma circunstância.
6. Aplicar `LOCK_TIMEOUT` e timeout de statement/conexao em todas as execucoes.
7. Bloquear `EXEC` livre, `DBCC`, `MERGE`, `BACKUP`, `RESTORE` e qualquer DDL/DML.
8. Nao executar multiplas statements em uma unica chamada.

## Quando pedir info

- `query` ausente → pedir ao usuário.
- Query suspeita (palavras bloqueadas) → bloquear; não pedir "confirmação".
