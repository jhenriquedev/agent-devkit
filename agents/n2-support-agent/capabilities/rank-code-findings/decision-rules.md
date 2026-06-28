# Decision Rules

- Rankear achados depois de `analyze-code-root-cause`.
- Priorizar arquivos source sobre migrations, migrations sobre testes, e testes sobre suporte.
- Usar score de relevancia como desempate dentro do mesmo tipo de arquivo.
- Nao colocar teste como arquivo primario de patch quando houver implementacao candidata.
- Destacar arquivos que conectam sintoma, regra de negocio e evidencia runtime.
- Rebaixar arquivos gerados, configuracoes distantes e matches apenas nominais.
- Preservar justificativa de ranking para cada item.
- Se nao houver achados, retornar lista vazia e blocker para patch seguro.
- Nao alterar arquivos nem criar plano de patch nesta capability.
- Manter paths relativos ao `codebase_path` para facilitar implementacao futura.
