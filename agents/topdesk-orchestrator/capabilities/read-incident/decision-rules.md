# Decision Rules - read-incident

- `read-incident` exige ID, numero ou fixture.
- Sem identificador, pare e peca o alvo.
- Progress trail so e carregado quando solicitado.
- Solicitacao original e fato TOPdesk.
- Historico nao deve ser usado para escrever automaticamente.
- Nao classificar prioridade aqui.
- Nao expor payload raw.
- Usar esta capability antes de qualquer escrita sensivel.
