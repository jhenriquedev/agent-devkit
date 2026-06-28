# Decision Rules: Test Write Permissions

- Testar permissao de escrita sem tocar dados de negocio por padrao.
- Sem `--execute`, retornar somente plano e checagens pretendidas.
- Com `--execute`, usar objeto temporario ou schema de auditoria controlado quando possivel.
- Aplicar `XACT_ABORT ON`, `LOCK_TIMEOUT` e timeout para o teste.
- Nao testar com `UPDATE`, `DELETE` ou DDL destrutivo em tabela de negocio.
- Validar disponibilidade do schema de historico configurado.
- Nunca imprimir connection string, senha, host completo ou URL completa.
- Reportar permissoes faltantes de forma objetiva sem recomendar elevar privilegio amplo.
- Bloquear comandos de servidor, login, grant/revoke e configuracao.
- A saida deve indicar se apply, rollback e auditoria podem ser executados com seguranca.
