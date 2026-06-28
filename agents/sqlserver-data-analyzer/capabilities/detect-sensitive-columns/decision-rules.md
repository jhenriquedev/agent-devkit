# Decision Rules: Detect Sensitive Columns

- Detectar sensibilidade por heuristica de nome, tipo e contexto de tabela.
- Classificar CPF, CNPJ, documento, email, telefone, nome, endereco, token, senha e segredos.
- Nao consultar valores brutos quando metadados forem suficientes.
- Quando amostra for inevitavel, aplicar `TOP`, timeout, `LOCK_TIMEOUT` e mascaramento.
- Diferenciar coluna sensivel direta, identificador tecnico e campo operacional nao pessoal.
- Registrar falsos positivos possiveis e baixa confianca.
- Nao expor connection string, usuario, host completo ou URL completa.
- Nao alterar classificacao no banco; a saida e analitica.
- A saida deve orientar mascaramento em queries e relatorios.
- Bloquear escrita, `EXEC` livre e comandos administrativos.
