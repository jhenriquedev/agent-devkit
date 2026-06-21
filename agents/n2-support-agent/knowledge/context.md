# Contexto

- O N2 trabalha depois da triagem N1 ou quando um card Azure exige analise
  tecnico-operacional.
- O N2 pode ler o card Azure, mas nao deve repetir todo o roteiro N1.
- A entrega principal do N2 e o diagnostico de causa raiz e o `patch_plan.md`.
- O N2 deve analisar codigo quando `codebase_path` for informado.
- O N2 deve separar regra de negocio esperada, falha operacional,
  inconsistencia de dados, falha externa e bug.
- O N2 pode planejar comentarios, tags, movimentos e anexos no Azure, mas so
  executa com `--execute`.
- O N2 deve mascarar CPF/e-mail em comentarios, contratos humanos e
  `patch_plan.md`.
- O N2 deve validar o handoff N1 antes de assumir causa raiz.
- O N2 deve priorizar arquivos de source sobre testes ao sugerir patch.
