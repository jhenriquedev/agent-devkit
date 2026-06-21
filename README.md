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

Cada agente encapsula um dominio de atuacao, como Azure DevOps, AWS CloudWatch,
TOPdesk ou criacao de PowerPoint. Dentro do proprio agente ficam sua superficie
externa de capabilities, seu conhecimento de dominio e sua infraestrutura
especializada.

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
- [`bpo-analyser`](agents/bpo-analyser/): especialista em consulta direta a
  BPO para analisar propostas por CPF ou numero, status, situacao,
  observacoes e documentos anexados, sem usar a API SelfHire.
- [`elasticsearch-log-analyzer`](agents/elasticsearch-log-analyzer/):
  especialista em Elasticsearch para descoberta de fontes, busca de eventos,
  rastreio de requests, padroes de erro e relatorios de logs.
- [`n1-support-agent`](agents/n1-support-agent/): especialista N1 para executar
  runbooks operacionais a partir de cards Azure DevOps, orquestrando Azure,
  SQL Server, logs e TOPdesk.
- [`database-change-operator`](agents/database-change-operator/):
  especialista em mudancas controladas em PostgreSQL, incluindo migrations,
  rollback, scripts de escrita, upserts e updates com dry-run por padrao.
- [`drawio-diagram-builder`](agents/drawio-diagram-builder/): especialista em
  criar, revisar e refinar diagramas Draw.io editaveis a partir de briefings,
  documentos, pastas, cards Azure, especificacoes, inventarios tecnicos e
  feedback iterativo.
- [`postgres-data-analyzer`](agents/postgres-data-analyzer/):
  especialista em PostgreSQL read-only para descoberta de databases, schemas,
  tabelas, relacionamentos, joins, queries assistidas, perfilamento, qualidade
  de dados e relatorios analiticos.
- [`presentation-deck-builder`](agents/presentation-deck-builder/):
  especialista em templates versionados de PowerPoint, arquivos de entrada para
  preenchimento e geracao de decks a partir de conteudo estruturado.
- [`sqlserver-data-analyzer`](agents/sqlserver-data-analyzer/):
  especialista em SQL Server read-only para descoberta de databases, schemas,
  tabelas, relacionamentos, joins, queries assistidas, perfilamento, qualidade
  de dados e relatorios analiticos.
- [`sqlserver-change-operator`](agents/sqlserver-change-operator/):
  especialista em mudancas controladas em SQL Server, incluindo migrations,
  rollback, scripts de escrita, criacao de objetos, updates, deletes e upserts
  com dry-run por padrao.
- [`software-specification-analyst`](agents/software-specification-analyst/):
  especialista em analise de requisitos, entrevistas, analise de projetos,
  documentacao funcional/tecnica, user stories, fluxos de jornada e
  rastreabilidade.
- [`technical-integration-analyst`](agents/technical-integration-analyst/):
  especialista em analise de documentacoes tecnicas de integracoes, com suporte
  a REST, SOAP, MCP, SFTP, SMTP e outros protocolos, gerando contratos, fluxos,
  massa de testes, curls, Postman Collections e documentacao tecnica.
- [`topdesk-orchestrator`](agents/topdesk-orchestrator/): especialista em
  TOPdesk para incidentes, triagem, enriquecimento, pedidos de informacao e
  relatorios operacionais.

## CLI

Use o executavel da raiz para descobrir agentes e capabilities:

```bash
./ai-devkit agents
./ai-devkit capabilities azure-devops-orchestrator
./ai-devkit inspect azure-devops-orchestrator read-card
./ai-devkit run azure-devops-orchestrator read-card --project "Projeto" --id 123 --include-comments
./ai-devkit run database-change-operator plan-migration --path migrations/202606211200_create_table.up.sql
./ai-devkit run n1-support-agent execute-n1-card-runbook --project "Sustentacao" --card 7710
./ai-devkit run bpo-analyser analyze-cpf-proposals --cpf 12345678901
./ai-devkit run bpo-analyser analyze-proposal --proposal-number 123456
./ai-devkit run presentation-deck-builder register-template --template status.pptx --template-id status-report --version 0.1.0 --yes-save
./ai-devkit run postgres-data-analyzer list-tables --database outro_banco --schema public
./ai-devkit run sqlserver-data-analyzer list-tables --schema dbo
./ai-devkit run sqlserver-change-operator plan-migration --path migrations/001_create_table.up.sql
./ai-devkit run software-specification-analyst analyze-project-context --project . --output-dir specifications/contexto --yes-create-dir
./ai-devkit run software-specification-analyst conduct-requirements-interview --input demanda.md --analysis-dir specifications/contexto --output-dir specifications/entrevista --yes-create-dir
./ai-devkit run software-specification-analyst create-final-spec-from-analysis --analysis-dir specifications/refinada --output-dir specifications/final --yes-create-dir
./ai-devkit run software-specification-analyst create-complete-spec --input demanda.md
./ai-devkit run drawio-diagram-builder execute-diagram-delivery --file specifications/final/software-specification.md --diagram-type user_journey --output-dir diagrams --yes-create-dir
./ai-devkit run technical-integration-analyst extract-integration-contract --file api.md
./ai-devkit run topdesk-orchestrator read-incident --number "I 2606 001"
```

No estado atual, as 8 capabilities do `azure-devops-orchestrator` possuem
`runner.py` e podem ser executadas por `run`: `list-cards`, `read-card`,
`comment-card`, `update-card-tags`, `assign-card`, `move-card`,
`prepare-card-analysis` e `generate-cards-report`.

O `topdesk-orchestrator` tambem possui runners para `list-incidents`,
`read-incident`, `create-incident`, `update-incident`,
`analyze-incident-insufficiency`, `request-more-info` e `incident-report`.

O `database-change-operator` possui runners para `test-write-permissions`,
`plan-migration`, `apply-migration`, `rollback-migration`, `run-write-script`,
`upsert-records`, `update-records` e `migration-report`. Operacoes de escrita
rodam em dry-run por padrao e exigem `--execute`.

O `n1-support-agent` possui runners para executar runbook de card Azure,
extrair entidades, planejar checks N1, gerar artefatos e atualizar card Azure
por orquestracao. Escritas em Azure DevOps exigem `--execute`.

Nos agentes Postgres, `POSTGRES_DB_CONN_STRING` e a conexao base. Use
`--database <nome>` para trocar apenas o database da URL quando a mesma
credencial tiver acesso a mais de um banco no mesmo host.

O `postgres-data-analyzer` possui runners read-only para descoberta de schema,
relacionamentos, sugestao de joins, validacao e execucao de queries limitadas,
perfilamento, qualidade de dados, rastreio de registros e relatorios.

O `sqlserver-data-analyzer` possui runners read-only para descoberta de schema,
relacionamentos, sugestao de joins, validacao e execucao de queries limitadas,
perfilamento, qualidade de dados, rastreio de registros e relatorios.

O `sqlserver-change-operator` possui runners para `test-write-permissions`,
`plan-migration`, `apply-migration`, `rollback-migration`, `run-write-script`,
`create-object`, `update-records`, `delete-records`, `upsert-records`,
`backup-records` e `change-report`. Escritas reais exigem `--execute`, e
deletes reais tambem exigem `--confirm-delete`.

O `technical-integration-analyst` possui runners para ingerir documentacoes,
extrair contratos, identificar informacoes ausentes, analisar ordem de uso,
gerar massa de testes, gerar curls/Postman Collections, gerar artefatos de
protocolo, executar testes controlados e gerar documentacao tecnica.

O `software-specification-analyst` possui runners para `analyze-project-context`,
`conduct-requirements-interview`, `refine-analysis-with-feedback`,
`create-final-spec-from-analysis` e `create-complete-spec`. Ele cria documentos
intermediarios, conduz perguntas, incorpora feedback e gera especificacao final
a partir de analise refinada.

O `presentation-deck-builder` possui runners iniciais para registrar templates
versionados, listar templates/versoes e gerar arquivos de entrada
`input-schema.xlsx` e `input-schema.md`.

O `drawio-diagram-builder` possui runners para entrevista, ingestao de fontes,
leitura delegada de cards Azure, analise de contexto, planejamento, geracao,
revisao, refinamento e entrega orquestrada de diagramas `.drawio`.

## Por onde comecar

Leia primeiro o [`AGENTS.md`](AGENTS.md). Para criar uma nova automacao ou fluxo
especializado, comece por `agents/<agent-id>/` e modele suas capabilities antes
de criar repositories ou infraestrutura.
