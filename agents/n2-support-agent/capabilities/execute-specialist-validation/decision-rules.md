# Decision Rules

- Sem `--execute`, retornar apenas validacoes planejadas com `commandPreview`.
- Com `--execute`, chamar agente especialista somente quando houver contrato seguro e completo.
- Executar BPO diretamente apenas quando houver numero de proposta nao mascarado.
- Nao enviar CPF mascarado como parametro de busca para agente especialista.
- Logs Elasticsearch exigem `source`, `from_time` e `to_time`; `query` e opcional e pertence a logs.
- Logs CloudWatch exigem `region`, `log_group`, `start_time` e `end_time`.
- Banco exige query read-only explicita em campo SQL especifico; nao reutilizar `query` de log como SQL.
- SQL Server e Postgres sao mutuamente direcionados pelo provider ou campo de query recebido.
- Mutacoes de banco, AWS, Azure ou provider externo ficam fora desta capability.
- Quando faltar entrada obrigatoria, retornar `skipped` com `missingInputs` e resumo acionavel.
