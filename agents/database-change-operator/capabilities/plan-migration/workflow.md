# Workflow

1. Ler o arquivo SQL informado em `--path`.
2. Remover comentarios e dividir comandos por statement.
3. Calcular checksum SHA-256 do SQL normalizado.
4. Classificar operacoes, risco destrutivo, bloqueios e suporte transacional.
5. Detectar rollback `.down.sql` quando o arquivo for `.up.sql`.
6. Emitir plano em Markdown.
