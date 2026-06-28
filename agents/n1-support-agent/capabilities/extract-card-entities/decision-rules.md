# Decision Rules

- Extrair entidades do titulo, descricao, comentarios e fixture consolidada sem alterar o texto de origem.
- Normalizar CPF, proposta, contrato, TOPdesk, request id, correlation id, telefone e e-mail quando presentes.
- Sempre expor CPF apenas mascarado no contrato de saida.
- Se houver multiplos CPFs ou propostas, registrar todos mascarados e marcar ambiguidade.
- Distinguir identificadores tecnicos de numeros comuns para reduzir falsos positivos.
- Preservar request id e correlation id quando forem necessarios para busca de logs.
- Nao criar entidades por inferencia fraca; registrar `missing` ou `ambiguous`.
- Remover tokens, senhas e segredos do texto normalizado.
- Quando nenhuma entidade operacional for encontrada, retornar gap objetivo para `needs_more_info`.
- A saida deve ser consumivel pelas demais capabilities sem exigir releitura do card bruto.
