# Decision Rules

- Analisar codigo somente quando `codebase_path` existir e apontar para um projeto legivel.
- Partir do handoff N1, card e evidencias runtime; nao repetir triagem N1 como fonte primaria.
- Ignorar diretorios de build, cache, vendor, dependencias e artefatos gerados.
- Priorizar arquivos de implementacao sobre testes, migrations e arquivos auxiliares.
- Extrair classes, metodos, handlers, queries e regras de negocio relacionados ao sintoma.
- Nao marcar causa raiz como confirmada apenas por match textual em nome de arquivo.
- Registrar arquivos inspecionados, tokens usados, achados tecnicos e lacunas de leitura.
- Quando nao houver arquivo candidato, retornar evidencia insuficiente para patch seguro.
- Mascarar CPF e remover segredos encontrados em comentarios, fixtures ou logs locais.
- A saida deve alimentar ranking, classificacao de causa raiz e `patch_plan.md`.
