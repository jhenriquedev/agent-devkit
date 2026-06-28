# Agent DevKit

Biblioteca de agentes especialistas, capabilities, prompts, repositories e
conhecimento operacional para desenvolvimento, sustentacao e especificacao de
software com IA.

Nome publico do projeto no GitHub: `agent-devkit`. Nome do produto:
**Agent DevKit**. Comando canonico da CLI: `agent`.

> Objetivo: substituir o uso ad-hoc de prompts por agentes pre-criados,
> versionados e prontos para uso, com baixo consumo de contexto, decisoes mais
> consistentes e artefatos padronizados.

## O que e

O Agent DevKit e um repositorio agent-native. Seu produto principal nao e uma pasta
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
agent-devkit/
├─ AGENTS.md          # contrato raiz para agentes
├─ README.md          # visao humana do projeto
├─ .env.example       # variaveis de ambiente esperadas
├─ .github/           # governanca GitHub do repositorio
├─ agent              # entrypoint publico e canonico da CLI
├─ aikit              # entrypoint de compatibilidade
├─ ai-devkit          # entrypoint legado de compatibilidade
├─ agents/            # agentes especialistas e suas capabilities
├─ cli/               # documentacao da CLI do DevKit
├─ providers/         # registry global de providers
├─ plugins/           # adaptadores nativos Codex/Claude Code/Claude Desktop
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
├─ decision-rules.md  # exigido para fluxos com risco operacional
└─ runner.py          # opcional, quando a capability for executavel pela CLI
```

Uma capability deve declarar entradas, saidas, artefatos gerados, methods
necessarios e criterios de qualidade. Quando houver `entrypoint.runner`, ela
pode ser executada por `agent run`. Prompts ficam em `knowledge/prompts/`;
templates ficam em `templates/` na raiz do agente.

`decision-rules.md` e obrigatorio para capabilities com escrita, integracao
externa, orquestracao, risco operacional ou regras de decisao que nao caibam no
manifesto. Capabilities puramente declarativas podem omitir o arquivo enquanto a
ausencia estiver visivel na validacao global e nao houver ambiguidade de
execucao.

Statuses aceitos para agentes e capabilities:

- `draft`: contrato existe, mas ainda pode estar incompleto.
- `mvp`: runner ou fluxo minimo executa com testes basicos.
- `validated`: passou por validacao estrutural, testes e fixtures.
- `operational`: possui guardrails de uso real e documentacao atualizada.
- `deprecated`: mantido apenas por compatibilidade.

## Papel de `scripts/`

`scripts/` na raiz existe apenas para operacao global do repositorio: validar
todos os manifests, gerar catalogos, rodar checagens cross-agent ou empacotar
releases. Scripts especializados de integracao pertencem ao repository dentro
de `infra/integrations/<provider>/`.

Validacao estrutural principal:

```bash
python3 scripts/validate-repo.py
python3 scripts/validate-repo.py --json
python3 scripts/validate-repo.py --strict
```

E2E de instalacao limpa:

```bash
python3 -m unittest tests.test_aikit_e2e
```

Gate de readiness do MVP local:

```bash
python3 scripts/mvp-readiness.py
python3 scripts/mvp-readiness.py --json
```

## Plugins nativos

`plugins/` contem adaptadores finos para hosts de IA. Eles nao duplicam logica
dos agentes; apenas instalam skill/commands e delegam para o runtime `agent`.

- `plugins/codex-ai-devkit`: plugin local para Codex App.
- `plugins/claude-code-ai-devkit`: plugin local para Claude Code.
- `plugins/claude-skill-ai-devkit`: skill para Claude Desktop/Claude.ai.

Os nomes de pastas dos plugins ainda preservam `ai-devkit` por
compatibilidade. O nome publico do projeto no GitHub e `agent-devkit`, e o
comando canonico da CLI e `agent`.

Credenciais e providers continuam sendo configurados pelo runtime com
`agent provider configure`, sempre por referencia.

Instalacao local dos adaptadores:

```bash
agent install project --target . --host all
agent install global --host all
```

O instalador cria `.ai-devkit/config.yaml` e os artefatos `.codex/` e/ou
`.claude/` necessarios para descoberta pelo host. Ele nao grava `.env`, nao
solicita provider e nao persiste segredos. Use `--dry-run --json` para revisar
os caminhos antes de escrever. O host `all` inclui Codex App, Claude Code e
Claude Desktop/Claude.ai.

Instalacoes globais gravam `~/.ai-devkit/runtime.lock`; instalacoes por projeto
gravam `.ai-devkit/ai-devkit.lock`. Use `agent doctor --project .` para
verificar se o projeto esta fixado em runtime diferente do global.

`agent doctor --json` tambem resume runtime, locks, plugins, providers e
backends LLM. Ausencia de provider opcional ou LLM nao configurada nao bloqueia
o doctor; esses itens aparecem como diagnostico parcial.

Antes de publicar uma versao, rode:

```bash
python3 scripts/release-gate.py --json
```

Execucoes reais de capabilities com escrita exigem confirmacao dupla no runtime:
`--confirm-execute` mais o flag de execucao da capability (`--execute`,
`--yes-confirm`, `--yes-save` ou equivalente). Capabilities marcadas como
`blocked_by_default` tambem exigem `--allow-dangerous`, alem das validacoes
internas da capability.

Saidas JSON de `agent run` usam contrato `ai-devkit.run/v1`, com `status`
parseavel (`ok`, `partial`, `blocked`, `failed`), `agent_id`, `capability_id`,
`providers`, `fallback_applied`, `evidence`, `risks`, `next_steps` e
`artifacts` sempre presentes.

O modo padrao falha para erros estruturais e reporta avisos de higiene local. O
modo `--strict` tambem trata avisos como falhas.

## Configuracao local

Copie `.env.example` para `.env` e preencha apenas valores locais. O `.env` real
e ignorado pelo Git. Para Azure DevOps, `AZURE_DEVOPS_ORG` e
`AZURE_DEVOPS_PAT` sao globais; o projeto deve ser informado por comando com
`--project` para permitir trabalhar em multiplos projetos da mesma organizacao.
`AZURE_DEVOPS_PROJECT` existe apenas como fallback local.

## Agentes disponiveis

- [`aws-architecture-analyst`](agents/aws-architecture-analyst/): especialista
  em analise arquitetural AWS read-only, inventario, dependencias, resiliencia,
  observabilidade, rede e blast radius.
- [`azure-devops-orchestrator`](agents/azure-devops-orchestrator/): especialista
  em Azure DevOps Boards, work items, comentarios, tags, atribuicoes e
  movimentacao de estado.
- [`aws-cloudwatch-log-analyzer`](agents/aws-cloudwatch-log-analyzer/):
  especialista em AWS CloudWatch Logs para busca de eventos, rastreio de
  requests, padroes de erro e relatorios operacionais.
- [`aws-operations-operator`](agents/aws-operations-operator/): especialista em
  operacoes AWS controladas com dry-run por padrao, confirmacao explicita e
  relatorio operacional.
- [`aws-security-governance-auditor`](agents/aws-security-governance-auditor/):
  especialista em auditoria AWS read-only para IAM, exposicao publica, security
  groups, S3, secrets, encryption, CloudTrail e AWS Config.
- [`bpo-analyser`](agents/bpo-analyser/): especialista em consulta direta a
  BPO para analisar propostas por CPF ou numero, status, situacao,
  observacoes e documentos anexados, sem usar APIs intermediarias de produto.
- [`data-scientist-analyst`](agents/data-scientist-analyst/): especialista em
  analise de dados tabulares, profiling, deteccao de dados sensiveis,
  conciliacoes, relatorios tecnicos e artefatos reproduziveis.
- [`database-change-operator`](agents/database-change-operator/):
  especialista em mudancas controladas em PostgreSQL, incluindo migrations,
  rollback, scripts de escrita, upserts e updates com dry-run por padrao.
- [`drawio-diagram-builder`](agents/drawio-diagram-builder/): especialista em
  criar, revisar e refinar diagramas Draw.io editaveis a partir de briefings,
  documentos, pastas, cards Azure, especificacoes, inventarios tecnicos e
  feedback iterativo.
- [`elasticsearch-log-analyzer`](agents/elasticsearch-log-analyzer/):
  especialista em Elasticsearch para descoberta de fontes, busca de eventos,
  rastreio de requests, padroes de erro e relatorios de logs.
- [`excel-workbook-builder`](agents/excel-workbook-builder/): especialista em
  templates, preenchimento, conciliacao, revisao e exportacao de planilhas
  Excel.
- [`figma-ui-ux-product-designer`](agents/figma-ui-ux-product-designer/):
  especialista UI/UX para analisar contexto de produto e criar, recriar,
  evoluir e revisar designs mobile e web com Figma quando disponivel.
- [`knowledge-generator`](agents/knowledge-generator/): especialista em gerar
  knowledge versionavel a partir de arquivos, pastas, projetos e documentacoes.
- [`n1-support-agent`](agents/n1-support-agent/): especialista N1 para executar
  runbooks operacionais a partir de cards Azure DevOps, orquestrando Azure,
  SQL Server, logs e TOPdesk.
- [`n2-support-agent`](agents/n2-support-agent/): especialista N2 para validar
  handoff N1, investigar causa raiz em codigo/evidencias e gerar `patch_plan.md`.
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
agent agents
agent capabilities azure-devops-orchestrator
agent inspect azure-devops-orchestrator read-card
agent run azure-devops-orchestrator read-card --project "Projeto" --id 123 --include-comments
agent run database-change-operator plan-migration --path migrations/202606211200_create_table.up.sql
agent run n1-support-agent execute-n1-card-runbook --project "SupportProject" --card 7710
agent run bpo-analyser analyze-cpf-proposals --cpf 12345678901
agent run bpo-analyser analyze-proposal --proposal-number 123456
agent run presentation-deck-builder register-template --template status.pptx --template-id status-report --version 0.1.0 --yes-save --confirm-execute
agent run postgres-data-analyzer list-tables --database outro_banco --schema public
agent run sqlserver-data-analyzer list-tables --schema dbo
agent run sqlserver-change-operator plan-migration --path migrations/001_create_table.up.sql
agent run software-specification-analyst analyze-project-context --project . --output-dir specifications/contexto --yes-create-dir
agent run software-specification-analyst conduct-requirements-interview --input demanda.md --analysis-dir specifications/contexto --output-dir specifications/entrevista --yes-create-dir
agent run software-specification-analyst create-final-spec-from-analysis --analysis-dir specifications/refinada --output-dir specifications/final --yes-create-dir
agent run software-specification-analyst create-complete-spec --input demanda.md
agent run drawio-diagram-builder execute-diagram-delivery --file specifications/final/software-specification.md --diagram-type user_journey --output-dir diagrams --yes-create-dir
agent run technical-integration-analyst extract-integration-contract --file api.md
agent run topdesk-orchestrator read-incident --number "I 2606 001"
```

No estado atual, as 9 capabilities do `azure-devops-orchestrator` possuem
`runner.py` e podem ser executadas por `run`: `list-cards`, `read-card`,
`comment-card`, `update-card-tags`, `assign-card`, `move-card`,
`prepare-card-analysis`, `generate-cards-report` e `attach-file`.

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
