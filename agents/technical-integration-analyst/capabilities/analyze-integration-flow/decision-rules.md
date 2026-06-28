# Decision Rules: Analyze Integration Flow

- Auth e obtencao de token precedem chamadas protegidas.
- Criacao/setup precede consulta, atualizacao, cancelamento ou exclusao.
- Operacoes destrutivas devem ficar no final e exigir ambiente seguro.
- Ordenar operacoes por dependencia de IDs dinamicos e pre-condicoes.
- Separar fluxo principal, validacoes, cleanup e rollback quando aplicavel.
- Marcar mutations explicitamente por metodo, protocolo ou efeito colateral documentado.
- Nao assumir endpoint, credencial, ambiente ou payload ausente.
- Preservar evidencia de origem para cada passo inferido.
- Sinalizar lacunas que impedem execucao segura como perguntas objetivas.
- Mascarar tokens, cookies, senhas, API keys e headers `Authorization`.
- Quando protocolo nao for HTTP, gerar fluxo operacional equivalente em vez de forcar Postman.
