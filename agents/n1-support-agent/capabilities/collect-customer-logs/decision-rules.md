# Decision Rules

- Buscar logs quando houver request id, correlation id, CPF, proposta, contrato ou janela temporal objetiva.
- Priorizar request id e correlation id sobre CPF por reduzirem ruido e exposicao de dados pessoais.
- Usar `aws-cloudwatch-log-analyzer` e `elasticsearch-log-analyzer`; nao consultar provedores diretamente nesta capability.
- Se nao houver janela temporal, registrar baixa confianca e limitar a busca para evitar excesso de dados.
- Mascarar CPF, tokens, senhas, headers sensiveis e payloads pessoais.
- Diferenciar erro tecnico confirmado, ausencia de evento na janela, fonte indisponivel e busca inconclusiva.
- Nao concluir ausencia de erro quando CloudWatch ou Elasticsearch estiver indisponivel.
- Registrar fonte, query resumida, janela, quantidade de eventos e ids correlacionados no `evidenceLedger`.
- Quando logs confirmarem erro tecnico, preparar evidencias suficientes para agrupamento N2.
- Nao incluir dumps completos de log na resposta ao cliente.
