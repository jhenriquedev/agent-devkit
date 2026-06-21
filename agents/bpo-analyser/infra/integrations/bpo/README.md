# Integracao BPO

Repository Python para chamadas SOAP diretas aos servicos BPO usados como
referencia pelo modulo SelfHire do MCC.

## Endpoints usados

- `BPO_SERVICO_API_URL`: endpoint SOAP `ServicoAPI`.
- `BPO_WS_PROPOSTA_URL`: endpoint SOAP `WsProposta`.

## Operacoes read-only

- `ServicoAPI.listarPropostasPorCpf`
- `ServicoAPI.consultarPropostaPorNumeroProposta`
- `WsProposta.ConsultaDocumentosAnexados`

## Guardrails

- Nao chamar API SelfHire.
- Nao logar credenciais.
- Nao renderizar conteudo base64 de documentos por padrao.
- Manter `BPO_TLS_VERIFY=true` salvo necessidade local explicita para
  homologacao com certificado incompleto.
