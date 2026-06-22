# Decision Rules - create-incident

- `create-incident` exige resumo e request.
- Dry-run e obrigatorio por padrao.
- Escrita real exige `--execute`.
- Categoria, prioridade e grupo precisam de evidencia ou catalogo.
- Caller exige ID explicito ou resolucao confiavel por pessoa.
- Nao criar quando o request for insuficiente.
- Nao preencher campos de fechamento ou resolucao.
- Suspeita de duplicidade deve bloquear criacao automatica.
