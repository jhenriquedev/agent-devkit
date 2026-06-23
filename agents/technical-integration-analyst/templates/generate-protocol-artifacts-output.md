# Artefatos de Protocolo

## {protocol}

<!-- Repita esta secao para cada protocolo nao-HTTP detectado (sftp, smtp, file, queue, etc.) -->

### Setup

- Preparar credenciais em variaveis de ambiente (`SFTP_HOST`, `SFTP_USER`, `SFTP_KEY`, etc.).
- Configurar cliente adequado para o protocolo.

### Transferencia / Envio

- Executar operacao principal com variaveis de ambiente (sem expor credenciais em texto).
- Exemplo orientativo:
  ```bash
  sftp -i $SFTP_KEY $SFTP_USER@$SFTP_HOST
  ```

### Validacao

- Verificar arquivo recebido / confirmacao de entrega / log de resposta.
- Registrar evidencia do resultado.

### Cleanup

- Remover arquivos temporarios.
- Fechar sessao e reverter estado criado, quando aplicavel.

---
<!-- Sem protocolos nao-HTTP = "Nenhum protocolo nao HTTP detectado. Use generate-http-artifacts para REST/SOAP/MCP-over-HTTP." -->
