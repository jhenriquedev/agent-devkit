# Decision Rules - list-incidents

- `list-incidents` e somente leitura.
- Respeitar `limit`; nao paginar automaticamente.
- Filtros ausentes significam consulta ampla, nao erro.
- Nao inferir que a amostra representa todo o backlog.
- Marcar incidentes sem grupo ou prioridade como candidatos a triagem.
- Nao alterar chamados nesta capability.
- Nao expor payload raw.
- Separar contagens de interpretacoes operacionais.
