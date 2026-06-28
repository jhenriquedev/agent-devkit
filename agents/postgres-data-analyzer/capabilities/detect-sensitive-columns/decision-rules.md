# Decision Rules: Detect Sensitive Columns

- Detectar sensibilidade por heuristica de nome, tipo e contexto de tabela.
- Classificar CPF, CNPJ, documento, e-mail, telefone, nome, endereco, token e senha com severidade apropriada.
- Confirmar com regras de negocio antes de assumir classificacao definitiva.
- Nao consultar valores brutos para provar sensibilidade quando metadados forem suficientes.
- Quando amostra for inevitavel, mascarar ou omitir valores.
- Diferenciar coluna sensivel direta, identificador tecnico e campo operacional nao pessoal.
- Registrar falsos positivos possiveis e baixa confianca.
- A saida deve orientar mascaramento em queries e relatorios posteriores.
