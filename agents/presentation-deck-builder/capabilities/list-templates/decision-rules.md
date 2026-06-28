# Decision Rules

- Listar templates registrados lendo manifests, nao varrendo arquivos avulsos como fonte definitiva.
- Nao alterar catalogo, manifests ou status.
- Exibir template id, nome, current version, status e caminho relativo.
- Indicar templates com manifest ausente, current version invalida ou estrutura incompleta.
- Nao exibir conteudo interno de decks nesta capability.
- Ordenar resultados de forma estavel para automacoes.
- Respeitar `templates_root` quando informado.
- Preservar compatibilidade de paths em macOS, Windows e Linux.
- Diferenciar template draft, validated, deprecated e archived.
- A saida deve orientar selecao de template antes de gerar deck.
