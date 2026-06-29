# Docker Container Builder

Instrucoes locais para trabalhar no agente `docker-container-builder`.

## Responsabilidade

Este agente planeja, gera e revisa artefatos Docker locais, incluindo
`Dockerfile`, `.dockerignore`, `docker-compose.yml` e `README.docker.md`.
O objetivo e containerizar projetos de forma revisavel, segura e portavel sem
executar build, push ou deploy real.

## Fora De Escopo

- Executar `docker build`, `docker compose up`, `docker push` ou deploy real.
- Criar infraestrutura cloud, Kubernetes, Helm ou registry remoto.
- Persistir segredos em imagens, compose ou logs.
- Fazer supply-chain hardening avancado fora do checklist inicial.

## Guardrails

- Gerar `.dockerignore` sempre que gerar `Dockerfile`.
- Nao copiar `.env`, `.ssh`, chaves, caches, `.git`, `node_modules` ou `.venv`.
- Preferir usuario nao-root.
- Evitar `latest` em alvo `prod`.
- Nao gerar `privileged`, `network_mode: host` ou bind mount de `/`.
- Build, push e deploy devem aparecer apenas como plano dry-run.
- Escrita local deve ficar restrita a `target_project`.
