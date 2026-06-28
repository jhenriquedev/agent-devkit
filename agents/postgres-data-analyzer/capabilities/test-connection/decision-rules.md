# Decision Rules: Test Connection

- Nunca imprimir connection string, usuario, senha, host completo ou URL.
- Apenas validar conectividade e metadados basicos do banco atual.
- Executar consulta read-only minima com `statement_timeout`.
- Nao listar tabelas, schemas extensos ou dados de negocio nesta capability.
- Tratar falha de credencial, rede e permissao como categorias distintas quando possivel.
- Nao tentar reconectar com credenciais alternativas automaticamente.
- Respeitar override de database apenas como nome de banco.
- A saida deve ser suficiente para decidir se as demais capabilities podem rodar.
