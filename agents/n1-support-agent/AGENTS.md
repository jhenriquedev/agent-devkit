# AGENTS.md

Instrucoes especificas para agentes trabalhando em `agents/n1-support-agent/`.

- Codigo, identificadores e nomes de capabilities ficam em ingles.
- Documentacao e runbooks ficam em portugues.
- O N1 deve orquestrar agentes especialistas existentes em vez de reimplementar
  integracoes.
- Escritas no Azure DevOps exigem `--execute`.
- Saidas devem seguir contrato fixo para facilitar consumo por outros agentes.
