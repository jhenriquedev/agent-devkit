# Decision Rules

- Decidir apenas a partir de entidades, rota de sintoma, checks e lacunas registradas.
- Nunca inventar causa quando os checks minimos estiverem ausentes.
- Usar `needs_more_info` quando faltarem CPF, proposta, contrato ou identificador tecnico indispensavel.
- Usar `pending_n1_checks` quando houver entidades suficientes, mas checks obrigatorios ainda estiverem `unavailable` ou nao executados.
- Usar escalonamento N2 somente com evidencia tecnica, divergencia entre fontes ou bloqueio fora da alçada N1.
- Separar regra de negocio, falha tecnica, pendencia operacional e lacuna de diagnostico.
- Se restritiva estiver `hit`, refletir bloqueio operacional antes de apontar problema de app.
- Se BPO indicar pendencia documental, formalizacao ou CCB, manter recomendacao alinhada com BPO.
- O quality gate so passa quando os checks minimos da rota foram executados ou suas lacunas foram justificadas.
- A decisao deve preservar CPF mascarado e nunca expor segredos, tokens ou credenciais.
