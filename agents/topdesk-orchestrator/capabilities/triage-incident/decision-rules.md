# Decision Rules - triage-incident

- `triage-incident` exige ID, numero ou fixture com incidente explicito.
- Categorias e prioridades sugeridas devem existir no catalogo carregado.
- Prioridade deriva de impacto e urgencia descritos no chamado.
- Solicitante so pode ser preenchido quando `search-persons` resolver uma pessoa.
- Nunca sugerir fechamento, arquivamento, resolucao ou escalonamento.
- Sem evidencia suficiente, deixar o campo fora do plano de update.
- Escrita real exige `--execute`; dry-run e o comportamento padrao.
- A saida deve separar fatos TOPdesk de inferencias do agente.
- Usar `knowledge/triage-rules.md` como rubrica, mas nao inventar campos ausentes.
- Buscar pessoa apenas quando houver nome ou identificador de caller suficiente.
- Payload de update deve conter somente campos com evidencia e valor de catalogo valido.
- Nunca sobrescrever `request` durante triagem.
- Se catalogo estiver ausente ou incompleto, retornar lacuna em vez de valor inventado.
- Em dry-run, mostrar plano minimo e proxima acao de validacao.
