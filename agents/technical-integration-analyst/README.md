# Technical Integration Analyst

Agente especialista para analisar documentacoes tecnicas de integracoes e gerar
contratos, fluxos, massa de testes, comandos, collections Postman e
documentacao tecnica.

## Escopo inicial

- ingerir documentacao por URL, arquivo, diretorio ou texto;
- extrair contrato de integracao a partir de OpenAPI, Postman, WSDL/SOAP,
  Markdown, HTML, PDF e texto livre;
- identificar informacoes ausentes e perguntas necessarias;
- analisar ordem de uso da integracao;
- gerar massa de testes;
- gerar curls e Postman Collection para integracoes HTTP;
- gerar artefatos operacionais para SFTP, SMTP, SOAP, MCP e outros protocolos;
- executar testes reais com dry-run por padrao;
- gerar documentacao tecnica em Markdown e PDF.

## Como usar

```bash
./ai-devkit run technical-integration-analyst ingest-technical-docs --file manual.pdf
./ai-devkit run technical-integration-analyst extract-integration-contract --url https://example.com/docs
./ai-devkit run technical-integration-analyst generate-http-artifacts --file api.md --postman-output /tmp/collection.json
./ai-devkit run technical-integration-analyst run-integration-tests --file api.md --base-url https://sandbox.example.com
```

## Configuracao

Use `.env` local para valores padrao. Segredos tambem podem ser informados no
Postman por variaveis depois da importacao.

```env
TECH_INTEGRATION_DEFAULT_BASE_URL=
TECH_INTEGRATION_DEFAULT_AUTH_TOKEN=
TECH_INTEGRATION_HTTP_TIMEOUT=30
```

Chamadas reais exigem `--execute`. Mutations reais tambem exigem confirmacao de
escopo seguro.
