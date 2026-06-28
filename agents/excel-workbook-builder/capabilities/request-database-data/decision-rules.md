# Regras

- Delegar acesso a banco apenas para agentes permitidos: `sqlserver-data-analyzer` ou `postgres-data-analyzer`.
- Usar `azure-devops-orchestrator` somente para contexto de cards, nao para consulta SQL.
- Montar pedido com schema esperado, filtros, limite e justificativa de uso.
- Executar agente delegado somente quando `execute` for explicitamente solicitado.
- Nao reimplementar conexao de banco neste agente.
- Registrar resultado como fonte derivada para workbook.
