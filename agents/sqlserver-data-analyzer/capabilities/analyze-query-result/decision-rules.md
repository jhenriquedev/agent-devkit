# Decision Rules: Analyze Query Result

- Analisar somente resultados ja retornados por consultas read-only ou fixtures.
- Nao executar SQL de escrita, DDL, `MERGE`, `EXEC`, `DBCC`, `BACKUP` ou `RESTORE`.
- Mascarar CPF, CNPJ, email, telefone, nome, endereco, token, senha e segredos.
- Descrever colunas, nulidade, cardinalidade, outliers simples e sinais de sensibilidade.
- Nao inferir regra de negocio definitiva apenas por padrao nos dados.
- Registrar limite aplicado, row count e possivel truncamento.
- Preferir agregados e estatisticas a dumps de linhas.
- Separar fato medido, inferencia e recomendacao de proximo passo.
- Quando resultado tiver dados pessoais demais, reduzir amostras e explicar a limitacao.
- A saida deve orientar perfilamento, data quality ou query mais especifica.
