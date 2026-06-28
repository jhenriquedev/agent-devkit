# Decision Rules

- Gravar `patch_plan.md` no `--output` informado ou preparar entrega para card Azure.
- Sem `--output` e sem card Azure, retornar bloqueio pedindo destino de entrega.
- O plano deve conter causa raiz, plano TDD, atividades, arquivos, criterios de aceite, riscos, rollback e migrations quando aplicavel.
- `readyForImplementation` depende de handoff/card suficiente, arquivo candidato, categoria valida e confianca minima.
- Nao implementar codigo, migrations ou testes nesta capability.
- Incluir perguntas bloqueantes quando a causa raiz ou reproduccao ainda nao for segura.
- Mascarar CPF e remover e-mail pessoal, tokens, credenciais e payloads sensiveis.
- Priorizar arquivos de implementacao e testes relacionados, evitando mudanças amplas sem evidencia.
- Diferenciar correção de bug, ajuste de dados, dependência externa e ação pendente do cliente.
- O plano deve ser detalhado o bastante para outro agente implementar com TDD.
