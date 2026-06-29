# Docker Container Builder

Agente especialista em gerar e revisar artefatos Docker locais.

## Capabilities

- `analyze-containerization-target`: inspeciona projeto local e detecta sinais
  de linguagem, entrypoint, portas e riscos.
- `generate-dockerfile`: gera conteudo de `Dockerfile` em modo output-only.
- `generate-compose`: gera `docker-compose.yml` para desenvolvimento local em
  modo output-only.
- `generate-container-project-files`: planeja ou escreve arquivos Docker locais
  com `--execute`.
- `review-docker-security`: revisa Dockerfile/compose existentes ou texto.
- `plan-image-build`: gera comandos de build/tag/run sem executar Docker.

## Politica

O agente nao executa Docker CLI. Build, push e deploy reais permanecem
bloqueados por padrao e devem ser tratados por capabilities futuras com policy
propria.
