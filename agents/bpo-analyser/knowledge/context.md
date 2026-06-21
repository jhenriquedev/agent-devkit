# Contexto

O `bpo-analyser` consulta a BPO diretamente para apoiar analise operacional de
propostas. O projeto de referencia para os contratos e
`/Users/jhss/dev/meucashcard/mcc.api`, modulo `SelfHire`.

Contratos usados como referencia:

- `ServicoAPI.consultarPropostaPorNumeroProposta`: consulta status, situacao,
  atividade, dados financeiros e observacoes.
- `ServicoAPI.listarPropostasPorCpf`: lista propostas vinculadas a um CPF.
- `WsProposta.ConsultaDocumentosAnexados`: lista documentos anexados a proposta.

O agente nao deve usar endpoints `api/v1/self-hire`.
