# Regras

- Proposta elegivel segue a politica operacional configurada por
  `BPO_ELIGIBLE_SITUATIONS`, `BPO_ELIGIBLE_PROPOSAL_TYPES` e
  `BPO_REQUIRE_POSITIVE_WITHDRAW_LIMIT`.
- Propostas `CAD`, `PEN` ou `AND` indicam analise em andamento.
- Propostas `REP` indicam reprova.
- CPF deve ser mascarado em saida humana.
- Nao chamar alvos configurados em `BPO_FORBIDDEN_URL_PATTERNS` nem imprimir
  payload SOAP bruto.
