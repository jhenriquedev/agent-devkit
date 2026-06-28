# Decision Rules: Alterar Tags Card

- Preservar tags existentes por padrao.
- Remover apenas tags explicitamente informadas.
- Comparar tags de forma case-insensitive.
- Apresentar tags atuais e tags finais antes de escrita real.
- Se nao houver mudanca, retornar no-op.
- Usar dry-run por padrao e exigir confirmacao explicita antes de aplicar com `--execute`.
