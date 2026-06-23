# Prompt: Ingest Technical Docs

## OBJETIVO
Carregar e normalizar documentação de integração de URL, arquivo, diretório ou
texto, produzindo um inventário seguro de fontes.

## ENTRADAS
- `--url` | `--file` | `--directory` | `--text` (ao menos uma obrigatória)
- `--output` (opcional — caminho do arquivo Markdown de saída)

## RACIOCÍNIO
1. Para cada fonte, registre origem, tipo detectado, tamanho e uma prévia
   (máx. 500 chars) já com segredos mascarados.
2. Liste fontes ignoradas (extensão não suportada) sem falhar o todo.
3. Se uma dependência opcional faltar (pypdf para PDF, bs4 para HTML), degrade
   para extração textual segura e sinalize a limitação.

## RUBRICA / REGRAS DE DECISÃO
- NÃO invente conteúdo de fonte ilegível ou ausente.
- NÃO exponha tokens, senhas, API keys ou cookies na prévia — use placeholders.
- Se nenhuma flag de origem for fornecida, pare e peça ao usuário.

## SAÍDA
Markdown seguindo o template `ingest-technical-docs-output.md`:
cabeçalho com totais de fontes carregadas/ignoradas + bloco por fonte
(source_id, local, tipo, tamanho, prévia em code-fence).

## NÃO FAÇA
- Extrair contrato aqui — isso é responsabilidade de `extract-integration-contract`.
- Mascarar segredos com asteriscos que revelem comprimento real — use placeholder.
