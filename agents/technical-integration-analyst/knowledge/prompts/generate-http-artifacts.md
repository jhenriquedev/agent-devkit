# Prompt: Generate HTTP Artifacts

## OBJETIVO
Gerar curls e Postman Collection v2.1 importável para operações HTTP (REST,
SOAP-over-HTTP, MCP-over-HTTP), com variáveis funcionais e sem segredos.

## ENTRADAS
- Mesmas flags de origem (`--url`, `--file`, `--directory`, `--text`)
- `--postman-output` (opcional — salva JSON da collection)
- `--output` (opcional — salva Markdown)

## RACIOCÍNIO
1. Filtre operações representáveis por HTTP (método em GET/POST/PUT/PATCH/DELETE
   ou protocolo rest/soap/mcp).
2. Gere curl por operação com variáveis ({{base_url}}, {{token}}); inclua
   Content-Type e body apenas para métodos não-seguros (POST/PUT/PATCH/DELETE).
3. Gere Postman Collection v2.1 com variables (base_url, token, resource_id)
   e auth bearer por request.

## RUBRICA / REGRAS DE DECISÃO
- NÃO insira segredos reais — use sempre variáveis/placeholders.
- Operação sem endpoint HTTP (SFTP, SMTP, file, queue) não entra aqui.
- Se não houver operações HTTP, emita mensagem indicando usar `generate-protocol-artifacts`.

## SAÍDA
- Markdown seguindo `generate-http-artifacts-output.md` (seção Curl com code-fences bash)
- JSON em `--postman-output` com schema v2.1 importável no Postman

## NÃO FAÇA
- Forçar protocolos não-HTTP (SFTP, SMTP, file, queue) para dentro do Postman.
- Omitr variáveis de ambiente — toda URL e credencial deve ser parametrizada.
