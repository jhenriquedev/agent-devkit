# Decision Rules: Test Connection

- Validar conectividade com consulta read-only minima.
- Nunca imprimir connection string, usuario, senha, host completo ou URL completa.
- Aplicar timeout de conexao, timeout de statement e `LOCK_TIMEOUT`.
- Nao listar tabelas, schemas extensos ou dados de negocio nesta capability.
- Tratar falha de credencial, rede e permissao como categorias distintas quando possivel.
- Nao tentar credenciais alternativas automaticamente.
- Validar override de database apenas como nome, nunca como SQL/path/URL.
- Nao executar `EXEC`, `DBCC`, DDL, DML ou comandos administrativos.
- A saida deve indicar se as demais capabilities read-only podem rodar.
- Reportar contexto minimo: database atual, versao resumida e schema atual quando seguro.
