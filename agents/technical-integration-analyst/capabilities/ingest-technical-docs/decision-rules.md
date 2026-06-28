# Decision Rules: Ingest Technical Docs

- Nao inventar conteudo quando a fonte nao puder ser lida.
- Mascarar segredos nas previas.
- Preferir extracao textual segura a falha total quando uma dependencia opcional nao estiver instalada.
- Aceitar URL, arquivo, diretorio ou texto como fonte.
- Respeitar limites de bytes, quantidade de fontes e profundidade de diretorio.
- Registrar origem, tipo, tamanho e preview seguro de cada fonte.
- Preservar texto bruto apenas internamente quando necessario; previews devem ser mascarados.
- Ignorar ou reportar formatos nao suportados sem tratar como contrato inexistente.
- Nao seguir links recursivamente alem do escopo solicitado.
- Mascarar `Authorization`, cookies, tokens, API keys, senhas e secrets.
- Quando uma fonte falhar, continuar com as demais e listar lacunas de ingestao.
