# Setup Figma MCP Bridge Workflow

1. Verificar se o comando `codex` existe.
2. Verificar se o MCP `figma` esta configurado no Codex com `codex mcp get figma`.
3. Se `--login` for informado, iniciar `codex mcp login figma`.
4. Instalar wrappers locais do bridge quando solicitado.
5. Gerar variaveis de ambiente necessarias.
6. Atualizar `.env` local apenas quando `--write-env` for informado.
7. Opcionalmente validar o bridge com uma chamada diagnostica.
8. Gerar relatorio de setup com comandos de uso e pendencias.
