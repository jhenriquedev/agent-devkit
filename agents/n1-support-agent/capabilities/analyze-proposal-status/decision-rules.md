# Decision Rules

- Consultar proposta ou contrato quando houver identificador direto; com apenas CPF, registrar que pode haver multiplas propostas.
- Separar status da proposta, status do contrato, pendencias operacionais e bloqueios de regra de negocio.
- Nao inferir contrato aprovado apenas pela existencia de proposta.
- Se proposta estiver pendente, rejeitada, cancelada ou sem documento obrigatorio, refletir isso como fato operacional.
- Correlacionar status de proposta com BPO quando houver formalizacao, CCB, margem ou documento envolvido.
- Tratar fonte indisponivel como `unavailable`, nao como `not_found`.
- Mascarar CPF e nao expor dados bancarios, margem detalhada ou documentos sensiveis.
- Registrar origem, data da situacao e identificadores usados para auditoria.
- Nao executar alteracao de proposta, contrato ou esteira comercial nesta capability.
- Se houver divergencia entre fontes, manter decisao pendente e listar a divergencia no quality gate.
