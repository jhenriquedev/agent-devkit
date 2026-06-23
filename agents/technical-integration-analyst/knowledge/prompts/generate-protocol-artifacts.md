# Prompt: Generate Protocol Artifacts

## OBJETIVO
Gerar artefatos de teste e operação para protocolos não-HTTP (SFTP, SMTP, file,
queue, etc.), na forma de checklists operacionais e comandos orientativos.

## ENTRADAS
- Mesmas flags de origem (`--url`, `--file`, `--directory`, `--text`)
- `--output` (opcional)

## RACIOCÍNIO
Por protocolo detectado (sftp, smtp, file, queue e similares), produza:
1. **Setup**: preparar credenciais em variáveis de ambiente, configurar cliente.
2. **Transferência/Envio**: comandos orientativos para executar a operação.
3. **Validação**: verificar arquivo recebido, confirmação de entrega, log de resposta.
4. **Cleanup**: remover arquivos temporários, fechar sessão, reverter estado criado.

## RUBRICA / REGRAS DE DECISÃO
- NÃO force Postman — protocolos não-HTTP não são representáveis em collection HTTP.
- Prefira checklist operacional quando execução automática não for segura.
- Sinalize informações ausentes específicas do protocolo (ex.: host SFTP, porta SMTP).

## SAÍDA
Markdown seguindo `generate-protocol-artifacts-output.md`:
por protocolo → seções Setup / Transferência-Envio / Validação / Cleanup.

## NÃO FAÇA
- Misturar REST/SOAP/MCP aqui — esses vão em `generate-http-artifacts`.
- Inserir credenciais reais nos comandos — use variáveis de ambiente.
