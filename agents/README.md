# Agents

Esta pasta contem os agentes especialistas do AI DevKit. Cada agente representa
uma inteligencia pre-criada, versionada e pronta para uso por Codex, Claude,
Cursor ou outro agente compativel.

## Objetivo

Organizar o projeto por especialistas autocontidos em tres camadas: superficie
externa, conhecimento e infraestrutura especializada.

## Estrutura esperada

```text
agents/<agent-id>/
├─ AGENTS.md
├─ README.md
├─ agent.yaml
├─ capabilities/
├─ knowledge/
├─ templates/
└─ infra/
```

## Regras

- Use nomes em `kebab-case`.
- Cada agente deve ter um `agent.yaml` com identidade, owner, status, versao,
  contexto minimo e superficie publica.
- Cada caso de uso executavel deve viver em `capabilities/<capability-id>/`.
- `capabilities/` e o front externo do agente e descreve casos de uso
  acionaveis.
- `knowledge/` guarda contexto, politicas, linguagem e regras de decisao.
- `templates/` guarda modelos de arquivos, respostas e artefatos gerados pelas
  capabilities.
- `infra/` guarda repositories, models e CLIs para acesso a sistemas externos.

## Agentes atuais

- `azure-devops-orchestrator`: especialista em Azure DevOps Boards.
- `aws-cloudwatch-log-analyzer`: especialista em AWS CloudWatch Logs.
- `elasticsearch-log-analyzer`: especialista em logs no Elasticsearch.
- `database-change-operator`: especialista em mudancas controladas em Postgres.
- `postgres-data-analyzer`: especialista em analise read-only de dados Postgres.
- `sqlserver-data-analyzer`: especialista em analise read-only de dados SQL
  Server.
- `sqlserver-change-operator`: especialista em mudancas controladas em SQL
  Server.
- `software-specification-analyst`: especialista em analise de requisitos,
  entrevistas, analise de projetos e especificacoes completas de software.
- `technical-integration-analyst`: especialista em documentacoes tecnicas de
  integracoes e artefatos de teste.
- `topdesk-orchestrator`: especialista em TOPdesk para incidentes e triagem.
