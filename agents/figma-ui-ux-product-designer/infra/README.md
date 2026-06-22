# Infra

Esta pasta guarda contratos e adapters para integracoes externas do
`figma-ui-ux-product-designer`.

Credenciais e ponte MCP devem vir de `.env` local ou do ambiente de execucao.
Nunca grave tokens Figma ou Azure em arquivos versionados.

O CLI local nao chama ferramentas Codex diretamente. Para escrita real no Figma,
configure `FIGMA_MCP_BRIDGE_COMMAND` com um comando que receba JSON em stdin e
retorne JSON com `file_key`, `file_url` ou node IDs criados/alterados.
