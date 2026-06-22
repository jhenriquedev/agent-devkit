# Decision Rules: List Log Streams

- Exigir `region` e `log_group` quando nao houver `fixture`.
- Usar `log_stream_prefix` sempre que o usuario indicar servico, instancia, task ou data.
- Tratar ausencia de streams como resultado valido, nao como erro de execucao.
- Nao buscar eventos nem inferir saude do servico apenas pela existencia de streams.
- Mostrar limite, prefixo e total retornado para deixar claro o escopo da descoberta.
- Recomendar `search-log-events` somente quando o usuario precisar analisar mensagens.
