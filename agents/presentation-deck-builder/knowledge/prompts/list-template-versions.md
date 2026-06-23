# Prompt: list-template-versions

## OBJETIVO
Listar todas as versoes registradas de um template com status, current_version e
caminhos dos artefatos.

## ENTRADAS
- `--template-id` (obrigatorio): identificador do template.
- `--templates-root` (opcional): diretorio raiz dos templates.

## RACIOCINIO (passos)
1. Ler `template.yaml` do template informado.
2. Imprimir: nome do template, `current_version`, e para cada versao:
   `version`, `status`, `path`, `input_schema`, `created_at`.
3. Indicar qual versao e a `current_version`.

## RUBRICA / REGRAS DE DECISAO
- Template inexistente: erro com mensagem clara.
- E read-only.

## SAIDA
Lista Markdown:
```
# <name>
- current_version: <version>

## Versoes
- <version>  status=<status>  path=<path>
```

## NAO FACA
- Nao modifique nenhum arquivo.
- Nao abra arquivos .pptx.
