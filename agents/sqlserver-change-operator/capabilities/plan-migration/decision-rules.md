# Decision Rules: Plan Migration

- Planejar migration sem executar escrita.
- Ler script ou entrada e classificar risco: baixo, medio, alto, destrutivo ou bloqueado.
- Detectar rollback correspondente e marcar lacuna quando ausente.
- Bloquear comandos proibidos por politica, incluindo servidor, login, grant/revoke, backup/restore e linked servers.
- Identificar se o script e transacional ou exige execucao fora de transacao.
- Exigir rollback para mudancas destrutivas antes de permitir apply.
- Estimar objetos afetados, pre-checks, historico e limites de linhas quando possivel.
- Recomendar `XACT_ABORT ON`, `LOCK_TIMEOUT` e timeout de statement.
- Nunca imprimir connection string, senha, host completo ou URL completa.
- A saida deve ser suficiente para decidir se `apply-migration` pode rodar.
