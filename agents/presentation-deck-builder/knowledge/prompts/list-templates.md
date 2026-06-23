# Prompt: list-templates

## OBJETIVO
Listar todos os templates registrados com `current_version`, status e nome.

## ENTRADAS
- `--templates-root` (opcional): diretorio raiz dos templates.

## RACIOCINIO (passos)
1. Varrer `<templates_root>/*/template.yaml`.
2. Para cada template, extrair: `id`, `current_version`, `name`, `status`.
3. Imprimir como lista Markdown.
4. Se nenhum template encontrado: "Nenhum template registrado."

## RUBRICA / REGRAS DE DECISAO
- E read-only: nunca abre arquivos .pptx.
- Ordenar por `id` alfabeticamente.

## SAIDA
Lista Markdown:
```
# Templates
- <id>  current=<version>  <name>
```
Ou: "- Nenhum template registrado."

## NAO FACA
- Nao abra arquivos .pptx.
- Nao modifique nenhum arquivo.
