# AGENTS.md

Instrucoes especificas para agentes trabalhando em `agents/knowledge-generator/`.

## Papel do agente

Este agente gera knowledge versionavel a partir de fontes variadas: arquivos,
pastas, projetos de codigo, documentacoes, planilhas, apresentacoes, HTML, PDFs
e conjuntos mistos. Ele deve classificar a fonte, escolher um profile de
knowledge adequado e criar artefatos rastreaveis sem depender de estrutura fixa
de projeto de codigo.

## Regras obrigatorias

- Codigo, identificadores e nomes de capabilities ficam em ingles.
- Documentacao humana fica em portugues.
- Nunca gravar segredos brutos, tokens, senhas, cookies, connection strings ou
  payloads pessoais completos.
- Paths de origem nos artefatos devem ser relativos ao source root sempre que
  possivel, ou `repo://<project-id>/...` quando o usuario informar project id.
- Separar fatos extraidos da fonte de inferencias e lacunas.
- Quando o tipo de fonte nao for claro, usar profile `freeform` ou
  `mixed-knowledge` e registrar lacunas.
- A pasta `knowledge/` gerada deve ser validavel por `validate-knowledge`.
- Escrita em filesystem exige `--yes-create-dir` quando o diretorio ainda nao
  existir e `--yes-overwrite` para sobrescrever arquivos existentes.

## Estrutura local

- `agent.yaml`: manifesto publico.
- `capabilities/`: casos de uso executaveis.
- `knowledge/`: contexto, politicas e prompts.
- `templates/`: modelos de saida.
- `infra/`: adapters de leitura, profiles, writer e validador.
