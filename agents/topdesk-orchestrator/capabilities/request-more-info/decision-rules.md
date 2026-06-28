# Decision Rules - request-more-info

- `request-more-info` exige incidente explicito ou fixture.
- Rode analise de insuficiencia antes de montar mensagem.
- Nunca enviar campo `request` no update.
- Usar nota ou acao adicional para preservar a solicitacao original.
- Dry-run e obrigatorio por padrao.
- Escrita real exige `--execute`.
- Nao pedir dados ja presentes no chamado.
- Se nao houver lacunas, nao enviar pedido.
- Payload deve usar `action` ou nota adicional, nunca `request`.
- Bloquear qualquer campo de fechamento, resolucao, arquivamento ou escalonamento.
- Perguntas devem ser especificas, curtas e relacionadas a lacunas detectadas.
- Nao pedir segredo bruto; solicitar evidencias, timestamps, mensagens de erro e impacto quando necessario.
- Em dry-run, mostrar mensagem planejada e perguntas sem atualizar TOPdesk.
- Em execucao real, relatar resultado sem expor payload sensivel completo.
