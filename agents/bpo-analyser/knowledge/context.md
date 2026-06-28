# Contexto

O `bpo-analyser` consulta a BPO diretamente para apoiar analise operacional de
propostas. Os contratos de servico, endpoints e politicas operacionais devem ser
informados pelo usuario via configuracao do provider BPO.

Contratos usados como referencia:

- `ServicoAPI.consultarPropostaPorNumeroProposta`: consulta status, situacao,
  atividade, dados financeiros e observacoes.
- `ServicoAPI.listarPropostasPorCpf`: lista propostas vinculadas a um CPF.
- `WsProposta.ConsultaDocumentosAnexados`: lista documentos anexados a proposta.

O agente nao deve usar endpoints que o usuario declarar em
`BPO_FORBIDDEN_URL_PATTERNS`.
