# Decision Rules

- Executar apenas consultas read-only via `sqlserver-data-analyzer`.
- Normalizar CPF para 11 digitos antes da busca e mascarar CPF em toda saida.
- Se `schema`, `table` e `cpf-column` forem informados juntos, consultar somente a fonte explicita.
- Sem fonte explicita, descobrir colunas candidatas antes de consultar valores.
- Classificar como `hit` apenas quando houver registro ativo ou evidencia objetiva de restricao.
- Classificar como `clear` somente quando todas as fontes candidatas relevantes responderem sem ocorrencias.
- Se qualquer fonte critica falhar, retornar `unavailable` ou registrar clear parcial com lacuna explicita.
- Nao expor connection string, SQL sensivel, credenciais ou linhas completas com dados pessoais.
- Preservar erros por origem sem abortar o runbook N1.
- Um `hit` na restritiva deve bloquear conclusoes de onboarding livre ate validacao operacional.
