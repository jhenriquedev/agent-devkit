# Decision Rules: Identify Missing Information

- Perguntas devem ser acionaveis e especificas.
- Lacunas que bloqueiam mutations reais devem aparecer antes das demais.
- Nao solicitar segredo bruto quando variavel de ambiente ou placeholder resolve.
- Agrupar lacunas por ambiente, autenticacao, operacoes, dados, seguranca, erros e protocolo.
- Marcar cada lacuna como bloqueante, importante ou opcional.
- Nao inventar `base_url`, escopo OAuth, headers, schema, payload ou ambiente.
- Perguntar por formato esperado e exemplo seguro quando payload estiver incompleto.
- Para execution real, exigir base URL, allowed host, timeout, auth e politica de mutation.
- Para Postman, exigir variaveis de ambiente e IDs dinamicos quando necessario.
- Para protocolos nao HTTP, pedir host/path/fila/mailbox e criterios de validacao seguros.
- A saida deve ser curta o bastante para o operador responder sem reler toda documentacao.
