# Decision Rules

- Gerar comentario interno curto para Azure DevOps a partir da causa raiz e do plano de patch.
- Incluir categoria, confianca, resumo tecnico, referencia ao `patch_plan.md` e proximas acoes.
- Nao incluir detalhes extensos que pertencem ao `patch_plan.md`.
- Quando o plano nao estiver pronto, destacar blockers e perguntas objetivas.
- Nao expor CPF cru, e-mail pessoal, tokens, connection strings ou dumps de log.
- Diferenciar causa confirmada, hipotese provavel e evidencia insuficiente.
- Mencionar validacoes especialistas planejadas ou executadas quando elas sustentarem a conclusao.
- Nao prometer implementacao, prazo ou deploy sem evidencias no contrato de entrada.
- Manter a mensagem adequada para comentario interno, nao para resposta ao cliente.
- A saida deve poder ser usada por `update-azure-workflow` sem reprocessar diagnostico.
