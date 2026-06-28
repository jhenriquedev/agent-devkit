# Decision Rules

- Executar a ordem operacional definida em `knowledge/policies.yaml`.
- Carregar N1, fixture ou card antes de analisar codigo.
- Nao repetir triagem N1 quando o handoff ja for suficiente; validar e partir dele.
- Exigir `--output` ou card Azure para entregar `patch_plan.md`.
- Gerar plano de patch, comentario e acoes Azure sem mutacoes externas por padrao.
- Executar mutacoes Azure somente com `--execute`.
- Nao implementar o patch; a entrega central e o `patch_plan.md`.
- Se faltar evidencia para patch seguro, manter perguntas bloqueantes e `readyForImplementation=false`.
- Mascarar CPF, e-mail e segredos em todos os artefatos.
- Registrar quais agentes especialistas foram planejados, executados ou pulados.
