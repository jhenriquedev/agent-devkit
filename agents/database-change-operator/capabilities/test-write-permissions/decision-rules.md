# Decision Rules

- Use esta capability antes de qualquer operacao de escrita real.
- Sem `--execute`, retornar apenas dry-run com os checks planejados.
- Nao inferir permissao de escrita apenas pelo sucesso de conexao.
- Se o teste falhar, nao tentar aplicar migration ou update.
- A execucao real deve sempre ser transacional e encerrada com rollback.
- Aplicar `statement_timeout` e `lock_timeout` tambem no teste real.
