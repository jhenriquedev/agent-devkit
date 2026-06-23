# Prompt — setup-figma-mcp-bridge

## OBJETIVO
Configurar e validar o bridge local (Codex + Figma MCP) para habilitar escrita real no Figma.

## ENTRADAS
- `--validate-live`: executar chamada diagnostica de validacao.
- `--login`: iniciar fluxo de login OAuth do Figma MCP.
- `--write-env`: gravar variaveis no arquivo `.env` local.
- `--output-dir`: pasta de saida para o relatorio.

## RACIOCINIO (passos)
1. Checar se o comando `codex` existe no PATH; se nao, instruir instalacao.
2. Checar se o MCP `figma` esta configurado: `codex mcp get figma`; se nao, instruir `codex mcp add figma`.
3. Se `--login`: iniciar `codex mcp login figma` e aguardar autenticacao OAuth.
4. Instalar wrapper `bin/figma-codex-bridge` quando solicitado.
5. Identificar variaveis necessarias: `FIGMA_MCP_BRIDGE_COMMAND`, `FIGMA_MCP_ENABLED`, `FIGMA_DEFAULT_PLAN_KEY` (opcional).
6. Se `--write-env`: gravar variaveis no `.env` (nunca gravar token direto; usar referencia ao keychain/env).
7. Se `--validate-live`: executar chamada diagnostica via bridge e verificar se `status` == `inspected` com evidencia (`file_url` ou `inspected_node_ids`).
8. Gerar relatorio com: status de cada requisito, comandos de uso, pendencias.

## REGRAS DE DECISAO
- Nunca gravar token/credencial em arquivo versionado.
- Habilitar modo `direct_mcp` somente quando a validacao retornar evidencia real.
- Se bridge nao puder ser instalado: documentar o bloqueio e manter modo `plan_only`.

## SAIDA
- `figma-mcp-setup-report.md`: status de cada requisito, comandos, pendencias.
- `figma-env.generated`: variaveis de ambiente geradas (NAO versionado se contiver segredos).

## NAO FACA
- Nao gravar token em arquivo de texto versionado.
- Nao declarar modo `direct_mcp` sem validacao bem-sucedida.
