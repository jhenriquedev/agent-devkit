# Decision Rules - create-incident

- `create-incident` exige resumo e request.
- Dry-run e obrigatorio por padrao.
- Escrita real exige `--execute`.
- Categoria, prioridade e grupo precisam de evidencia ou catalogo.
- Caller exige ID explicito ou resolucao confiavel por pessoa.
- Nao criar quando o request for insuficiente.
- Nao preencher campos de fechamento ou resolucao.
- Suspeita de duplicidade deve bloquear criacao automatica.
- `fields_json` nao pode sobrescrever resumo/request obrigatorios com valores vazios.
- Payload deve ser minimo, revisavel e sem credenciais ou dados sensiveis desnecessarios.
- Nao escalar, arquivar, fechar ou resolver chamado durante criacao.
- Quando houver caller, categoria, prioridade ou grupo sem evidencia confiavel, deixar fora do payload.
- Em dry-run, renderizar o plano e o payload planejado sem chamar escrita real.
- Em execucao real, relatar ID/numero retornado sem despejar resposta bruta sensivel.
