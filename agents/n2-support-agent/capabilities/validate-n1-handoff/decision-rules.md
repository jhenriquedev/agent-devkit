# Decision Rules

- Validar se o contrato N1 contem entidades, checks, decisao e diagnostic gaps.
- Aceitar handoff somente quando as lacunas abertas nao bloquearem a causa raiz N2.
- Marcar `needsN1Rerun` quando N1 estiver ausente, incompleto ou sem checks minimos.
- Copiar diagnostic gaps abertos para `openDiagnosticGaps` sem perder a origem.
- Nao repetir consultas N1 nesta capability; apenas validar suficiencia.
- Preservar entidades mascaradas e nao reintroduzir CPF cru.
- Diferenciar dado ausente, ferramenta indisponivel e evidencia contraditoria.
- Quando N1 indicar apenas `needs_more_info`, bloquear investigacao N2 ate haver informacao minima.
- Registrar perguntas objetivas para completar o handoff.
- A saida deve orientar `select-specialist-checks` e `generate-patch-plan`.
