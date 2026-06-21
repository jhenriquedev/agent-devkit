# Decision Rules: Analyze Integration Flow

- Auth e obtencao de token precedem chamadas protegidas.
- Criacao/setup precede consulta, atualizacao, cancelamento ou exclusao.
- Operacoes destrutivas devem ficar no final e exigir ambiente seguro.
