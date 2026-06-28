# Regras

- Delegar acesso SQL somente a agentes especializados declarados.
- Permitir apenas operacoes read-only e limites explicitos de linhas.
- Nao reimplementar conexao SQL dentro deste agente.
- Registrar agente, capability, database, schema, table ou query usada.
- Mascarar dados pessoais retornados em amostras e relatorios.
- Tratar resultado SQL como fonte analitica derivada, preservando premissas e lacunas.
