# Decision Rules: Run Insights Query

- Usar modo consulta de resultado quando `query_id` estiver presente.
- Usar modo inicio de query somente com `region`, `log_group`, `start_time`, `end_time` e `query`.
- Preferir queries agregadas e com `limit` baixo para triagem inicial.
- Nao executar consulta sem janela temporal ou sem log group explicito.
- Nao afirmar causa raiz apenas por uma query agregada; separar fatos de hipoteses.
- Nao escrever em AWS; esta capability apenas inicia ou le resultados de Logs Insights.
