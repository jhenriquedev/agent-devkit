# Decision Rules: Generate HTTP Artifacts

- Usar variaveis Postman para base URL, token e IDs dinamicos.
- Nao inserir segredos reais nos artefatos.
- SOAP e MCP-over-HTTP podem ser representados como HTTP quando houver endpoint.
- Gerar Postman Collection v2.1 importavel quando houver operacoes HTTP representaveis.
- Usar variaveis para ambiente, autenticacao, base URL, tenant, IDs dinamicos e valores mutaveis.
- Separar requests de setup, leitura, mutation, cleanup e validacao.
- Nao hardcodar host produtivo como unico destino; preferir `{{base_url}}`.
- Incluir exemplos de payload apenas quando documentados ou marcados como exemplo sintético seguro.
- Marcar mutations com aviso e prerequisitos de ambiente.
- Mascarar `Authorization`, cookies, tokens, API keys e senhas em curl/Postman.
- Se protocolo nao for corretamente representavel em HTTP, delegar para artefatos de protocolo.
