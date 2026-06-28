# Decision Rules

- Consultar Cognito por CPF, e-mail ou telefone somente quando a integracao estiver disponivel para o ambiente.
- Se a integracao nao estiver disponivel, retornar `unavailable` com `diagnosticGaps`; nao referenciar agentes futuros ou inexistentes.
- Mascarar CPF e evitar expor atributos sensiveis de usuario.
- Diferenciar usuario nao encontrado, usuario desabilitado, usuario nao confirmado e atributo nao verificado.
- Nao concluir falha de login ou cadastro apenas por ausencia de usuario sem checar o contexto do sintoma.
- Quando `enabled=false` ou confirmacao pendente explicar o sintoma, recomendar acao operacional N1/N2 correspondente.
- Quando houver multiplos identificadores conflitantes, registrar ambiguidade e pedir dado objetivo minimo.
- Preservar o runbook mesmo se Cognito falhar, marcando a lacuna no quality gate.
- Nunca alterar usuario Cognito nesta capability; ela e estritamente read-only.
