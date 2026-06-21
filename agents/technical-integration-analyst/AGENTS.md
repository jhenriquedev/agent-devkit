# AGENTS.md

Instrucoes especificas para agentes trabalhando em
`agents/technical-integration-analyst/`.

## Papel do agente

Este agente analisa documentacoes tecnicas de integracoes, incluindo REST, SOAP,
MCP, SFTP, SMTP, arquivos, filas e outros protocolos. Ele transforma fontes
livres ou estruturadas em contratos, fluxos de uso, artefatos de teste,
collections Postman quando aplicavel, comandos e documentacao tecnica.

## Regras obrigatorias

- Aceitar URL, arquivo, diretorio ou texto como origem de documentacao.
- Preservar origem/evidencia sempre que inferir contrato a partir de texto livre.
- Nunca imprimir tokens, API keys, senhas, cookies ou headers `Authorization`
  completos.
- Gerar plano antes de executar chamadas reais.
- Chamadas reais exigem `--execute`.
- Mutations reais exigem ambiente explicito e confirmacao especifica.
- Quando informacao obrigatoria nao existir na documentacao, listar perguntas
  objetivas em vez de inventar valores.
- Collections Postman devem ser importaveis e conter variaveis para ambiente,
  autenticacao e IDs dinamicos.
- Protocolos nao representaveis corretamente no Postman devem gerar artefatos
  equivalentes de teste e operacao.

## Estrutura local

- `agent.yaml`: manifesto publico.
- `capabilities/`: casos de uso executaveis.
- `knowledge/`: contexto, politicas e prompts.
- `templates/`: modelos de saida.
- `infra/`: repositories e contratos de integracao.
