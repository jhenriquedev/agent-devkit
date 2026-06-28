# Integracao BPO

Repository Python para chamadas SOAP diretas aos servicos BPO usados como
fonte operacional configurada pelo usuario.

## Endpoints usados

- `BPO_SERVICO_API_URL`: endpoint SOAP `ServicoAPI`.
- `BPO_WS_PROPOSTA_URL`: endpoint SOAP `WsProposta`.
- `BPO_ELIGIBLE_SITUATIONS`: situacoes que podem ser elegiveis.
- `BPO_ELIGIBLE_PROPOSAL_TYPES`: tipos de proposta aceitos pela politica.
- `BPO_REQUIRE_POSITIVE_WITHDRAW_LIMIT`: exige limite de saque positivo.
- `BPO_FORBIDDEN_URL_PATTERNS`: trechos de URL que este agente nao pode chamar.
- `BPO_PARTNER_CONTRACT_FIELDS`: campos XML que representam contrato do parceiro.
- `BPO_ORIGINATOR_CONTRACT_FIELDS`: campos XML que representam contrato do originador.

## Operacoes read-only

- `ServicoAPI.listarPropostasPorCpf`
- `ServicoAPI.consultarPropostaPorNumeroProposta`
- `WsProposta.ConsultaDocumentosAnexados`

## Guardrails

- Nao chamar alvos configurados em `BPO_FORBIDDEN_URL_PATTERNS`.
- Nao logar credenciais.
- Nao renderizar conteudo base64 de documentos por padrao.
- Manter `BPO_TLS_VERIFY=true` salvo necessidade local explicita para
  homologacao com certificado incompleto.
