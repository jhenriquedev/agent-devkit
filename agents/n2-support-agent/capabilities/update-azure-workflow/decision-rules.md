# Decision Rules

- Planejar tag, comentario, anexo, movimento e atribuicao Azure como apoio ao N2.
- Sem `--execute`, todas as acoes devem permanecer em modo planejado.
- Com `--execute`, aplicar somente acoes com projeto, card e parametros suficientes.
- Nao escrever `patch_plan.md` quando `--output` apontar para arquivo de acoes.
- Anexar `patch_plan.md` somente quando houver arquivo de entrega existente ou gerado pela investigacao.
- Adicionar tag `Analise N2` sem duplicar tag existente.
- Mover card apenas quando `target_state` estiver presente; coluna isolada deve virar lacuna ou skip.
- Atribuir responsavel somente quando `assign_to` estiver informado.
- Usar apenas capabilities do `azure-devops-orchestrator` declaradas no manifesto.
- Nao incluir PII ou segredos em comentario, tag, estado, coluna ou nome de anexo.
