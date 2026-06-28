# Azure DevOps Orchestrator

Agente especialista para operar Azure DevOps Boards com foco em work items,
cards, comentarios, tags, atribuicoes e movimentacao de estado.

## Objetivo

Servir como uma camada especializada para agentes como Codex. O Codex continua
conduzindo a conversa, mas carrega este agente quando a tarefa envolve Azure
DevOps. Este pacote define contexto, politicas, capabilities e methods que
reduzem inferencia improvisada e padronizam artefatos.

## Escopo inicial

O MVP e read-first:

- Listar cards de um projeto ou query.
- Ler um card especifico por ID e projeto explicito.
- Ler comentarios, anexos, tags, coluna, status e metadados principais.
- Preparar comentario com confirmacao antes de escrita.

Tambem existem capabilities de escrita controlada para alterar tags, atribuir
responsavel, mover estado/coluna e anexar arquivos. Todas executam dry-run por
padrao e exigem `--execute` para escrita real.

## Estrutura

```text
azure-devops-orchestrator/
├─ AGENTS.md
├─ README.md
├─ agent.yaml
├─ capabilities/
├─ knowledge/
├─ templates/
└─ infra/
```

## Camadas

- `capabilities/`: front externo do agente. Cada capability representa um caso
  de uso acionavel.
- `knowledge/`: conhecimento necessario para o agente decidir bem, incluindo
  contexto, politicas, prompts e regras do dominio.
- `templates/`: modelos de arquivos, respostas e artefatos gerados pelas
  capabilities.
- `infra/`: suporte executavel do agente, incluindo repositories, models e CLI
  para integracoes externas.

## Como usar

1. Carregue `agent.yaml` para descobrir capabilities e superficie publica.
2. Carregue `knowledge/context.md` para obter as regras minimas do dominio.
3. Escolha a capability em `capabilities/`.
4. Use apenas methods declarados pelo agente ou pela capability.
5. Para qualquer escrita, siga `knowledge/policies.yaml`.

## Execucao local

Use a CLI raiz quando quiser validar uma capability completa:

```bash
agent run azure-devops-orchestrator read-card --project "Projeto" --id 123 --include-comments
```

Capabilities executaveis atuais:

```bash
agent run azure-devops-orchestrator list-cards --project "Projeto" --limit 20
agent run azure-devops-orchestrator read-card --project "Projeto" --id 123 --include-comments
agent run azure-devops-orchestrator comment-card --project "Projeto" --id 123 --comment "Atualizacao."
agent run azure-devops-orchestrator update-card-tags --project "Projeto" --id 123 --add-tag Bugfix
agent run azure-devops-orchestrator assign-card --project "Projeto" --id 123 --assignee pessoa@example.com
agent run azure-devops-orchestrator move-card --project "Projeto" --id 123 --state Active
agent run azure-devops-orchestrator prepare-card-analysis --project "Projeto" --id 123 --include-comment-draft
agent run azure-devops-orchestrator generate-cards-report --project "Projeto" --state "To Do" --limit 50 --include-comments
agent run azure-devops-orchestrator attach-file --project "Projeto" --id 123 --file evidencia.txt --comment "Evidencia operacional."
```

Use a CLI da integracao apenas quando precisar testar diretamente o repository:

```bash
python agents/azure-devops-orchestrator/infra/integrations/azure/cli.py get-work-item --project "Projeto" --id 123 --expand-relations
```

O projeto Azure DevOps deve ser informado em cada chamada com `--project`. O
token e a organizacao sao globais e vêm do `.env` da raiz ou do ambiente.
