# Decision Rules

- Consultar onboarding quando houver CPF ou proposta; sem ambos, registrar gap objetivo.
- Separar estado atual, ultima evolucao, etapa travada e integracao externa envolvida.
- Diferenciar fluxo em andamento, finalizado, expirado, bloqueado, nao encontrado e indisponivel.
- Se a base restritiva estiver `hit` ou `unavailable`, nao concluir onboarding livre sem evidencias adicionais.
- Para onboarding travado em documentos, margem, convenio ou formalizacao, correlacionar com BPO antes de apontar bug de app.
- Nao alterar registros de onboarding nem reprocessar filas nesta capability.
- Mascarar CPF e reduzir dados pessoais ao minimo necessario.
- Registrar timestamps relevantes para permitir correlacao com logs.
- Quando a consulta nao estiver disponivel, manter `unavailable` e adicionar `diagnosticGaps`.
- A saida deve alimentar `checks`, `evidenceLedger` e `qualityGate` do contrato N1.
