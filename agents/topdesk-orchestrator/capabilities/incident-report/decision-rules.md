# Decision Rules - incident-report

- `incident-report` e somente leitura.
- Relatorio opera sobre a amostra retornada.
- Agregar por status e prioridade.
- Destacar chamados sem grupo operador.
- Riscos sao inferencias, nao fatos TOPdesk.
- Nao alterar chamados.
- Nao extrapolar alem de `limit`.
- Proxima acao deve apontar leitura ou triagem, nao escrita direta.
- Separar fatos agregados de inferencias sobre risco operacional.
- Declarar filtros efetivos e tamanho da amostra.
- Destacar chamados sem grupo, prioridade ou categoria como candidatos a triagem.
- Nao incluir request completo nem payload bruto no relatorio agregado.
- Nao recomendar fechamento, resolucao, arquivamento ou escalonamento automatico.
- Quando a amostra estiver vazia, indicar ausencia na consulta, nao ausencia no backlog inteiro.
