# Workflow

1. Carregar o dataset local com os controles de leitura solicitados.
2. Gerar ingestao, profile, analise exploratoria e relatorio markdown.
3. Persistir `profile.json`, `exploratory.json`, `data-report.md` e `manifest.json` no diretorio de saida.
4. Retornar o manifesto com `cache_key`, caminhos dos artifacts e resumo operacional.
