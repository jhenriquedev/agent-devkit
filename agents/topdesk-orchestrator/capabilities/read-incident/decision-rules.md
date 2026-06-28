# Decision Rules - read-incident

- `read-incident` exige ID, numero ou fixture.
- Sem identificador, pare e peca o alvo.
- Progress trail so e carregado quando solicitado.
- Solicitacao original e fato TOPdesk.
- Historico nao deve ser usado para escrever automaticamente.
- Nao classificar prioridade aqui.
- Nao expor payload raw.
- Usar esta capability antes de qualquer escrita sensivel.
- Preferir ID ou numero explicito; nao buscar por texto livre nesta capability.
- Separar solicitacao original, campos normalizados e progress trail.
- Preservar `request` como fato TOPdesk, sem editar ou resumir como se fosse campo novo.
- Limitar progress trail para evitar despejo sensivel e excesso de contexto.
- Mascarar credenciais, tokens, senhas e dados pessoais desnecessarios.
- A saida deve orientar triagem, insuficiencia ou pedido de informacao sem executar update.
