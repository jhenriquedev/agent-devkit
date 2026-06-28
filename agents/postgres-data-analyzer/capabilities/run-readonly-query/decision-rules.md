# Decision Rules: Run Readonly Query

- Permitir apenas queries iniciadas por `SELECT`, `WITH` ou `EXPLAIN`.
- Bloquear keywords de escrita, DDL, privilege changes, procedures, `COPY`, `DO` e comandos administrativos.
- Validar a query antes de executar e aplicar `statement_timeout`.
- Aplicar `LIMIT` automatico em consultas exploratorias sem limite.
- Nao executar multiplas statements em uma unica chamada.
- Mascarar CPF, CNPJ, e-mail, telefone, token, senha e campos pessoais na saida.
- Nao imprimir connection string, usuario, senha ou URL completa.
- Retornar row count, limite aplicado e aviso quando o resultado for truncado.
