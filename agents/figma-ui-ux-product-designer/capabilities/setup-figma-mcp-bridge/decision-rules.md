# Regras

- Tratar `FIGMA_ACCESS_TOKEN` sozinho como insuficiente para edicao completa de canvas.
- Validar `FIGMA_MCP_BRIDGE_COMMAND` e `FIGMA_MCP_ENABLED=true` ou `FIGMA_DIRECT_MODE=true` antes de declarar direct mode.
- Nunca gravar credenciais reais em arquivos versionados.
- Gerar `figma-env.generated` apenas como artefato local revisavel.
- `write_env` exige confirmacao explicita e deve respeitar o arquivo alvo informado.
- `validate_live` deve retornar evidencia objetiva ou classificar o modo como `blocked`/`plan_only`.
