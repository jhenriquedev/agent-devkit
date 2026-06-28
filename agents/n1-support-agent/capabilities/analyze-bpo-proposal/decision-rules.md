# Decision Rules

- Consultar BPO somente por meio do `bpo-analyser`; nao chamar endpoints ou bancos BPO diretamente.
- Se houver numero de proposta, priorizar `analyze-proposal` e usar CPF apenas como contexto de validacao.
- Se houver apenas CPF, consultar propostas por CPF e destacar a proposta mais recente ou registrar ambiguidade.
- Classificar proposta pendente, rejeitada, nao encontrada, indisponivel ou ignorada com base em fatos da BPO, documentos e observacoes.
- Tratar erro da BPO como `unavailable`, nunca como ausencia de pendencia.
- Nao imprimir CPF cru, nome completo desnecessario ou conteudo `base64` de documentos.
- Registrar documentos relevantes por tipo, contagem e existencia, sem expor anexos.
- Separar fatos da BPO de inferencias N1 e pontos de atencao.
- Quando houver bloqueio documental, formalizacao ou CCB ausente, manter a decisao como pendencia operacional ate haver evidencia contraria.
- Incluir origem, capability orquestrada e lacunas no `evidenceLedger` quando a consulta nao puder ser concluida.
