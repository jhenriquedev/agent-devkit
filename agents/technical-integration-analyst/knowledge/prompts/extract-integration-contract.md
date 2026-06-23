# Prompt: Extract Integration Contract

## OBJETIVO
Extrair contrato normalizado a partir das fontes ingeridas, cobrindo protocolos,
autenticação, operações, payloads, erros e lacunas, com evidência por operação.

## ENTRADAS
- Mesmas flags de origem (`--url`, `--file`, `--directory`, `--text`)
- `--base-url` (opcional)
- `--contract-output` (opcional — salva JSON do contrato)
- `--output` (opcional — salva Markdown)

## RACIOCÍNIO
1. Detecte protocolo(s), auth, base URL, operações, payloads, códigos de erro.
2. Use parsers estruturados quando houver OpenAPI/Swagger, Postman ou WSDL/SOAP;
   complemente com extração por texto livre (método+path), preservando evidência.
3. Para cada operação, registre: protocolo, método/path, mutation (true/false),
   evidência (origem), exemplo de corpo quando disponível.
4. Separe explicitamente fatos documentados de inferências.

## RUBRICA / REGRAS DE DECISÃO
- `mutation = true` quando método não é GET/HEAD/OPTIONS OU protocolo tem efeito colateral.
- Se nenhuma operação e nenhum protocolo detectado: marque protocolo "unknown".
- Campos `missing_information` e `flow` são sempre incluídos no contrato de saída.

## SAÍDA
- Markdown seguindo `extract-integration-contract-output.md` (Resumo + Operações + Informações Ausentes)
- JSON em `--contract-output` quando solicitado (campos: protocols, primary_protocol,
  base_url, auth, operations, errors, missing_information, flow)

## NÃO FAÇA
- Assumir base URL ou credenciais ausentes — transforme em pergunta em `missing_information`.
- Inventar operações não documentadas na fonte.
