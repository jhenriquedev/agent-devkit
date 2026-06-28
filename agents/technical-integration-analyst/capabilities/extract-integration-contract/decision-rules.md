# Decision Rules: Extract Integration Contract

- Preservar evidencia por operacao sempre que possivel.
- Classificar mutation quando metodo ou protocolo indicar efeito colateral.
- Marcar lacunas como perguntas, nao como valores assumidos.
- Detectar protocolo principal e protocolos secundarios: REST, SOAP, MCP, SFTP, SMTP, GraphQL, file, queue ou unknown.
- Separar dados documentados de inferencias e manter origem/localizacao de cada operacao.
- Extrair ambientes, auth, endpoints, payloads, parametros, respostas, erros e efeitos colaterais.
- Nao inventar `base_url`, token, ID dinamico, fila, path SFTP ou mailbox ausente.
- Mascarar secrets em exemplos e previews antes de renderizar.
- Limitar preview de fonte conforme `knowledge/policies.yaml`.
- Classificar operacoes sem informacao suficiente como incompletas, nao executaveis.
- A saida JSON/Markdown deve alimentar artifacts, testes e documentacao sem releitura da fonte bruta.
