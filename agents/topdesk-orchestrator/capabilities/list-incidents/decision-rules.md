# Decision Rules - list-incidents

- `list-incidents` e somente leitura.
- Respeitar `limit`; nao paginar automaticamente.
- Filtros ausentes significam consulta ampla, nao erro.
- Nao inferir que a amostra representa todo o backlog.
- Marcar incidentes sem grupo ou prioridade como candidatos a triagem.
- Nao alterar chamados nesta capability.
- Nao expor payload raw.
- Separar contagens de interpretacoes operacionais.
- Declarar filtros efetivos usados na consulta.
- Preferir ID, numero, resumo, status, prioridade e grupo operador em tabela resumida.
- Nao incluir request completo, progress trail ou anexos na listagem.
- Mascarar dados sensiveis quando aparecerem em resumo ou caller.
- Usar `read-incident` para qualquer analise detalhada antes de escrita.
- Resultado vazio deve ser tratado como amostra vazia para os filtros, nao como inexistencia definitiva.
