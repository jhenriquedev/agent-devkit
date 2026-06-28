# Regras

- Em producao, priorizar situacao `INT`; aceitar `APR` como fallback analitico.
- Se nenhuma proposta tiver data de ultimo vencimento, retornar sem selecao.
- Nao consultar documentos automaticamente nesta capability.
- CPF deve ser mascarado em saida humana.
- Nao chamar alvos configurados em `BPO_FORBIDDEN_URL_PATTERNS` nem imprimir
  payload SOAP bruto.
