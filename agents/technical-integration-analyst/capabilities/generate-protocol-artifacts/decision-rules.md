# Decision Rules: Generate Protocol Artifacts

- Nao forcar Postman para protocolos que ele nao representa corretamente.
- Preferir checklist operacional quando execucao automatica nao for segura.
- Separar setup, transferencia/envio, validacao e cleanup.
- Gerar artefatos especificos para SOAP, MCP, SFTP, SMTP, arquivo, fila, GraphQL ou protocolo desconhecido.
- Para SFTP/arquivo, incluir paths, padroes de nome, encoding, schema e criterio de idempotencia quando documentados.
- Para SMTP, incluir envelope, headers, anexos, TLS/auth e mailbox de teste quando documentados.
- Para filas, incluir producer, consumer, topico/fila, payload, retry, DLQ e ordenacao quando documentados.
- Nunca incluir credenciais reais; usar variaveis e placeholders seguros.
- Marcar informacoes ausentes por protocolo como perguntas objetivas.
- Separar comandos orientativos de execucao real.
- Incluir criterios de validacao e rollback/cleanup quando houver efeito colateral.
