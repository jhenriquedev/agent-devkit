# BPO Analyser

Agente especialista para consultar diretamente a BPO e analisar propostas sem
passar por APIs intermediarias de produto.

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
agent run bpo-analyser test-connection
agent run bpo-analyser list-proposals-by-cpf --cpf 12345678901
agent run bpo-analyser analyze-cpf-proposals --cpf 12345678901
agent run bpo-analyser find-latest-proposal-by-cpf --cpf 12345678901
agent run bpo-analyser consult-proposal --proposal-number 123456
agent run bpo-analyser consult-attached-documents --proposal-number 123456
agent run bpo-analyser analyze-proposal --proposal-number 123456
agent run bpo-analyser analyze-proposal --proposal-number 123456 --format json
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
- `BPO_ELIGIBLE_SITUATIONS`
- `BPO_ELIGIBLE_PROPOSAL_TYPES`
- `BPO_REQUIRE_POSITIVE_WITHDRAW_LIMIT`
- `BPO_FORBIDDEN_URL_PATTERNS`
- `BPO_PARTNER_CONTRACT_FIELDS`
- `BPO_ORIGINATOR_CONTRACT_FIELDS`

O agente usa somente as URLs BPO configuradas. Quando houver APIs de produto que
nao devem ser chamadas por este agente, informe seus trechos em
`BPO_FORBIDDEN_URL_PATTERNS`.

`BPO_TLS_VERIFY=false` existe para compatibilidade local com ambientes de
homologacao que apresentam cadeia de certificado incompleta. O padrao recomendado
continua sendo verificar TLS.
