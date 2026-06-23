# Runtime Externo: presentations skill (@oai/artifact-tool)

## Dependencia

O runner `generate-deck-from-template` depende da **presentations skill** que
fornece o pacote `@oai/artifact-tool` e o ambiente Node.js bundled do Codex.

## Como o runner resolve

1. Variavel de ambiente `PRESENTATIONS_SKILL_DIR` — caminho direto para o
   diretorio da skill (deve conter `artifact_tool/API_QUICK_START.md`).
2. Cache automatico do Codex:
   `~/.codex/plugins/cache/openai-primary-runtime/presentations/*/skills/presentations`
3. Node.js: busca em `~/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node`
   ou no PATH do sistema (`which node`).

## Pre-check

O runner executa o pre-check **antes** de qualquer processamento. Se a skill nao
for encontrada, ele imprime uma mensagem de erro acionavel e retorna exit code 1
sem simular geracao.

## Fallback

Nao ha fallback Python-puro implementado. Sem a skill, o runner nao gera o deck.
Para ambientes sem o runtime do Codex, configure `PRESENTATIONS_SKILL_DIR`
manualmente ou use um container com o `@oai/artifact-tool` instalado.

## Variavel de ambiente

```
PRESENTATIONS_SKILL_DIR=/caminho/para/presentations/skills/presentations
```

## Testes

O teste `test_generate_deck_from_template_creates_pptx` e marcado com
`@unittest.skipUnless` quando a skill nao esta disponivel no ambiente (skip limpo,
sem falha de ambiente mascarada como falha de codigo).
