# Decision Rules: Search Log Events

- Exigir `region`, `log_group`, `start_time` e `end_time` quando nao houver `fixture`.
- Aplicar `filter_pattern` e `log_stream_prefix` quando informados.
- Limitar volume com `limit` e resumir mensagens grandes.
- Renderizar `next_token` quando existir para explicitar paginacao.
- Tratar eventos como fatos observados, nao como causa raiz automatica.
- Nao executar consultas sem janela temporal ou log group explicito.
