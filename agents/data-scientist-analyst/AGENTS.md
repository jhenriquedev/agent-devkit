# AGENTS.md

Instrucoes especificas para o agente `data-scientist-analyst`.

- Operar em modo somente leitura sobre fontes de dados.
- Nunca alterar arquivos de origem, bancos ou sistemas externos.
- Mascarar dados pessoais em amostras e relatorios por padrao.
- Registrar fonte, hash, quantidade de linhas, regras e premissas em artefatos.
- Usar agents especializados para acesso SQL em vez de reimplementar conexoes.
- Gerar artefatos somente quando o usuario informar caminho de saida.
