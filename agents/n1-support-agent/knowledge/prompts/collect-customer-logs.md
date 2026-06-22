# Collect Customer Logs

## Papel

Voce coleta ou declara a lacuna de logs necessarios para explicar o sintoma.

## Entradas

- CPF mascaravel.
- Request id ou correlation id.
- Janela temporal do erro.
- Rota de sintoma e sistema provavel.
- Fonte de logs configurada.

## Procedimento

1. Prefira request id ou correlation id quando houver.
2. Use CPF apenas como apoio e nunca exponha CPF completo.
3. Exija janela temporal para sintomas de erro em tempo de execucao.
4. Escolha fonte CloudWatch ou Elasticsearch somente se configurada.
5. Busque eventos relevantes, nao dumps completos.
6. Separe erro de API, erro de job, timeout e ausencia de evento.
7. Se fonte, query ou janela nao existirem, declare lacuna.

## Saida

Retorne JSON com:

- `capability`
- `status`
- `checkStatus`
- `facts.cpfMasked`
- `facts.requestId`
- `facts.fromTime`
- `facts.toTime`
- `reason`
- `diagnosticGaps`
- `errors`

## Insuficiencia

Sem fonte de logs ou janela temporal, use `unavailable`. Nao conclua que nao
houve erro sem consulta de logs.
