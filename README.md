# AI DevKit

Biblioteca de agentes especialistas, capabilities, prompts, repositories e
conhecimento operacional para desenvolvimento, sustentacao e especificacao de
software com IA.

> Objetivo: substituir o uso ad-hoc de prompts por agentes pre-criados,
> versionados e prontos para uso, com baixo consumo de contexto, decisoes mais
> consistentes e artefatos padronizados.

## O que e

O AI DevKit e um repositorio agent-native. Seu produto principal nao e uma pasta
de prompts soltos: e uma biblioteca de **agentes especialistas** que podem ser
acionados por Codex, Claude, Cursor ou outro agente compativel.

Cada agente encapsula um dominio de atuacao, como Azure DevOps, AWS CloudWatch
ou criacao de PowerPoint. Dentro do proprio agente ficam sua superficie externa
de capabilities, seu conhecimento de dominio e sua infraestrutura especializada.

## Principios

1. **Agentes fortes, raiz minima.** A raiz deve conter apenas o que e global ao
   repositorio. O detalhe tecnico vive dentro de cada agente.
2. **Capability como unidade executavel.** Cada caso de uso deve ser uma
   capability com contrato, workflow, entradas, saidas e quality gates.
3. **Infra executavel.** Integracoes externas ficam em repositories dentro de
   `infra/integrations/<provider>/`, usando `.env` da raiz.
4. **Contexto sob demanda.** O agente consumidor deve carregar primeiro o
   manifesto e o contexto minimo, e so depois os detalhes da capability.
5. **Padronizacao por contrato.** Agentes e capabilities declaram sua superficie
   publica em manifests versionados.

## Estrutura raiz

```text
ai-devkit/
├─ AGENTS.md          # contrato raiz para agentes
├─ README.md          # visao humana do projeto
├─ .env.example       # variaveis de ambiente esperadas
├─ .github/           # governanca GitHub do repositorio
├─ agents/            # agentes especialistas e suas capabilities
├─ cli/               # documentacao da CLI do DevKit
├─ vendor/            # skills, plugins e bundles externos/importados
└─ scripts/           # automacoes operacionais globais do repositorio
```

A pasta `docs/` e local, usada para desenvolvimento do projeto e artefatos
gerados. Ela e ignorada pelo Git e nao faz parte do projeto versionado final.
Specs versionadas devem ficar nos manifests, READMEs, workflows, policies e
contratos dentro do agente dono.

## Estrutura de um agente

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

- `AGENTS.md`: regras especificas para qualquer agente trabalhando naquele
  especialista.
- `agent.yaml`: manifesto publico com identidade, versao, owner, status,
  contexto padrao e superficie exportada.
- `capabilities/`: front externo do agente; casos de uso acionaveis.
- `knowledge/`: contexto, politicas, linguagem e regras necessarias para o
  agente decidir bem.
- `templates/`: modelos de arquivos, respostas e artefatos gerados pelas
  capabilities.
- `infra/`: suporte executavel do agente, como repositories, models e CLIs de
  integracao externa.

## Estrutura de uma capability

```text
agents/<agent-id>/capabilities/<capability-id>/
├─ capability.yaml
├─ workflow.md
├─ decision-rules.md
└─ runner.py          # opcional, quando a capability for executavel pela CLI
```

Uma capability deve declarar entradas, saidas, artefatos gerados, methods
necessarios e criterios de qualidade. Quando houver `entrypoint.runner`, ela
pode ser executada por `./ai-devkit run`. Prompts ficam em `knowledge/prompts/`;
templates ficam em `templates/` na raiz do agente.

## Papel de `scripts/`

`scripts/` na raiz existe apenas para operacao global do repositorio: validar
todos os manifests, gerar catalogos, rodar checagens cross-agent ou empacotar
releases. Scripts especializados de integracao pertencem ao repository dentro
de `infra/integrations/<provider>/`.

## Configuracao local

Copie `.env.example` para `.env` e preencha apenas valores locais. O `.env` real
e ignorado pelo Git. Para Azure DevOps, `AZURE_DEVOPS_ORG` e
`AZURE_DEVOPS_PAT` sao globais; o projeto deve ser informado por comando com
`--project` para permitir trabalhar em multiplos projetos da mesma organizacao.
`AZURE_DEVOPS_PROJECT` existe apenas como fallback local.

## Agentes disponiveis

- [`azure-devops-orchestrator`](agents/azure-devops-orchestrator/): especialista
  em Azure DevOps Boards, work items, comentarios, tags, atribuicoes e
  movimentacao de estado.
- [`aws-cloudwatch-log-analyzer`](agents/aws-cloudwatch-log-analyzer/):
  especialista em AWS CloudWatch Logs para busca de eventos, rastreio de
  requests, padroes de erro e relatorios operacionais.

## CLI

Use o executavel da raiz para descobrir agentes e capabilities:

```bash
./ai-devkit agents
./ai-devkit capabilities azure-devops-orchestrator
./ai-devkit inspect azure-devops-orchestrator ler-card
./ai-devkit run azure-devops-orchestrator ler-card --project "Projeto" --id 123 --include-comments
```

No estado atual, as 7 capabilities do `azure-devops-orchestrator` possuem
`runner.py` e podem ser executadas por `run`: `listar-cards`, `ler-card`,
`comentar-card`, `alterar-tags-card`, `atribuir-card`, `mover-card`,
`preparar-analise-card` e `gerar-relatorio-cards`.

## Por onde comecar

Leia primeiro o [`AGENTS.md`](AGENTS.md). Para criar uma nova automacao ou fluxo
especializado, comece por `agents/<agent-id>/` e modele suas capabilities antes
de criar repositories ou infraestrutura.
