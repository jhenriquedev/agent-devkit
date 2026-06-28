# Decision Rules: Sample Table

- Amostrar tabela somente com query read-only e limite explicito.
- Usar limite padrao de amostra quando o solicitante nao informar limite.
- Mascarar CPF, CNPJ, e-mail, telefone, token, senha e campos pessoais.
- Nao usar `ORDER BY random()` em tabelas grandes sem criterio seguro.
- Validar schema e tabela antes de montar a query.
- Registrar limite, schema, tabela e possivel vies da amostra.
- Nao usar amostra como prova estatistica sem perfilamento adicional.
- Bloquear qualquer tentativa de mutacao disfarcada na query de amostra.
