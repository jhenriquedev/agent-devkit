# Decision Rules - request-more-info

- `request-more-info` exige incidente explicito ou fixture.
- Rode analise de insuficiencia antes de montar mensagem.
- Nunca enviar campo `request` no update.
- Usar nota ou acao adicional para preservar a solicitacao original.
- Dry-run e obrigatorio por padrao.
- Escrita real exige `--execute`.
- Nao pedir dados ja presentes no chamado.
- Se nao houver lacunas, nao enviar pedido.
