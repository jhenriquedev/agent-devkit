# BPO Analyser

Agente especialista para consultar diretamente a BPO e analisar propostas sem
passar pela API SelfHire.

## Escopo inicial

- validar configuracao local dos endpoints BPO;
- listar propostas por CPF via `ServicoAPI`;
- analisar propostas por CPF com classificacao operacional;
- encontrar proposta mais recente/elegivel por CPF;
- consultar proposta por numero via `ServicoAPI`;
- consultar documentos anexados via `WsProposta`;
- consolidar uma analise operacional da proposta com status, situacao,
  observacoes e anexos.

## Como usar

```bash
./ai-devkit run bpo-analyser test-connection
./ai-devkit run bpo-analyser list-proposals-by-cpf --cpf 12345678901
./ai-devkit run bpo-analyser analyze-cpf-proposals --cpf 12345678901
./ai-devkit run bpo-analyser find-latest-proposal-by-cpf --cpf 12345678901
./ai-devkit run bpo-analyser consult-proposal --proposal-number 123456
./ai-devkit run bpo-analyser consult-attached-documents --proposal-number 123456
./ai-devkit run bpo-analyser analyze-proposal --proposal-number 123456
./ai-devkit run bpo-analyser analyze-proposal --proposal-number 123456 --format json
```

As capabilities principais aceitam `--format json` para consumo por outros
agentes. A saida estruturada mascara CPF e remove conteudo base64 de documentos.

## Configuracao

Credenciais devem vir do `.env` da raiz ou do ambiente:

- `BPO_SERVICO_API_URL`
- `BPO_WS_PROPOSTA_URL`
- `BPO_CARTAO_USER`
- `BPO_CARTAO_PASSWORD`

Variaveis opcionais:

- `BPO_WS_ESTEIRA_URL`
- `BPO_WS_FORMALIZACAO_URL`
- `BPO_CONSIGNACAO_URL`
- `BPO_HTTP_TIMEOUT`
- `BPO_DEFAULT_DOCUMENT_TYPE`
- `BPO_TLS_VERIFY`

O agente nao usa a API SelfHire; as URLs acima apontam para os servicos BPO.

`BPO_TLS_VERIFY=false` existe para compatibilidade local com ambientes de
homologacao que apresentam cadeia de certificado incompleta. O padrao recomendado
continua sendo verificar TLS.
