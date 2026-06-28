# Decision Rules: Sample Table

- Amostrar tabela somente com consulta read-only e `TOP` explicito.
- Usar limite padrao quando o solicitante nao informar limite.
- Mascarar CPF, CNPJ, email, telefone, nome, endereco, token, senha e segredos.
- Evitar scans amplos sem filtro em tabelas grandes.
- Validar database, schema e tabela antes de montar a query.
- Aplicar timeout de statement/conexao e `LOCK_TIMEOUT`.
- Registrar limite, tabela e possivel vies da amostra.
- Nao usar amostra como prova estatistica sem perfilamento adicional.
- Bloquear qualquer tentativa de mutacao disfarcada na query.
- Nao imprimir connection string, usuario, senha, host completo ou URL completa.
