# Decision Rules: Correlate Azure Card Logs

- Separar dados do card e fatos CloudWatch em secoes distintas.
- Esta capability nao le Azure DevOps diretamente; ela usa entrada fornecida, fixture ou argumentos do usuario.
- Nao escrever comentarios, tags, status ou campos no Azure DevOps; nenhuma escrita deve ser executada.
- Comentario sugerido deve ser texto para revisao humana, nao acao automatica.
- Se nao houver log group informado ou extraido com evidencia, solicitar entrada explicita.
- Nao tratar fixture como consulta live nem concluir causa raiz sem validacao complementar.
