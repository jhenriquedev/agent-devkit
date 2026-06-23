# Prompt: generate-template-input-file

## OBJETIVO
(Re)gerar o arquivo de entrada preenchivel (`input-schema.xlsx` e `input-schema.md`)
de uma versao de template a partir do `slide-map.yaml`.

## ENTRADAS
- `--template-id` (obrigatorio): identificador do template.
- `--template-version` (opcional): versao alvo; default = `current_version`.
- `--templates-root` (opcional): diretorio raiz.

## RACIOCINIO (passos)
1. Resolver versao (default = `current_version`).
2. Verificar que o diretorio da versao existe.
3. Ler `slide-map.yaml` para obter colunas/campos por slide.
4. Escrever `input-schema.xlsx` (XLSX raw sem dependencia externa).
5. Escrever `input-schema.md` (tabela Markdown equivalente).
6. Reportar os caminhos gerados.

## RUBRICA / REGRAS DE DECISAO
- Versao inexistente: erro imediato.
- Regerar e idempotente (sobrescreve sem perguntar: write_policy template_version_write).

## SAIDA
- "Input schema gerado: <path>/input-schema.xlsx"
- "Input schema Markdown: <path>/input-schema.md"

## NAO FACA
- Nao preencha `user_content`; o usuario e responsavel pelo preenchimento.
- Nao altere outros artefatos da versao.
