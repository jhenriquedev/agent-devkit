# Agents

Esta pasta contem os agentes especialistas do Agent DevKit. Cada agente representa
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

- `agent-devkit-agent-builder`: especialista interno para planejar, criar
  scaffold e validar novos agentes do proprio Agent DevKit.
- `automation-architect`: especialista em classificar pedidos de automacao,
  escolher tecnologia adequada e delegar por contrato para builders
  especializados.
- `generic-agent-builder`: especialista em planejar, gerar e revisar agentes
  genericos portaveis para projetos e hosts externos.
- `python-automation-builder`: especialista em planejar, gerar, revisar e
  empacotar automacoes Python seguras para tarefas repetitivas.
- `selenium-automation-builder`: especialista em planejar, gerar e revisar
  automacoes Selenium/WebDriver quando houver requisito tecnico para Selenium.
- `pyautogui-automation-builder`: especialista em planejar, gerar e revisar
  automacoes desktop visuais com PyAutoGUI como ultimo recurso.
- `playwright-automation-builder`: especialista em planejar, gerar, revisar e
  executar checks controlados de automacoes web modernas com Playwright.
- `aws-lambda-builder`: especialista em planejar, gerar, revisar e empacotar
  projetos AWS Lambda locais sem executar deploy real.
- `aws-architecture-analyst`: especialista em analise arquitetural AWS
  read-only.
- `aws-cloudwatch-log-analyzer`: especialista em AWS CloudWatch Logs.
- `aws-operations-operator`: especialista em operacoes AWS controladas com
  dry-run por padrao.
- `aws-security-governance-auditor`: especialista em auditoria AWS read-only de
  seguranca e governanca.
- `azure-devops-orchestrator`: especialista em Azure DevOps Boards.
- `bpo-analyser`: especialista em consulta direta a BPO para analisar propostas
  por CPF ou numero e documentos anexados sem usar APIs intermediarias de produto.
- `data-scientist-analyst`: especialista em analise de dados tabulares,
  profiling, conciliacao e relatorios tecnicos.
- `database-change-operator`: especialista em mudancas controladas em Postgres.
- `docker-container-builder`: especialista em planejar, gerar e revisar
  artefatos Docker locais sem executar build, push ou deploy real.
- `execution-loop-builder`: especialista em planejar, gerar, revisar e
  registrar loops de execucao controlados com budgets e criterios de parada.
- `contribution-reviewer`: agente runtime para validar extensoes locais,
  revisar riscos de contribuicao upstream e planejar PRs em modo report-only.
- `drawio-diagram-builder`: especialista em diagramas Draw.io editaveis a
  partir de fontes reais, entrevista, geracao, revisao e refinamento.
- `elasticsearch-log-analyzer`: especialista em logs no Elasticsearch.
- `execution-reviewer`: agente runtime de revisao final, revisao de planos e
  revisao de resultados de agentes especialistas.
- `excel-workbook-builder`: especialista em templates, preenchimento,
  conciliacao, revisao e exportacao de planilhas Excel.
- `figma-ui-ux-product-designer`: especialista UI/UX para criar, recriar,
  evoluir e revisar designs mobile e web.
- `github-pr-reviewer`: especialista em Pull Requests GitHub, revisao
  report-only, permissao explicita para comentarios/aprovacoes e automacoes
  locais conservadoras.
- `knowledge-infra-builder`: especialista em criar e diagnosticar a
  infraestrutura file-first da knowledge base compartilhada.
- `knowledge-author`: especialista em criar snapshots de conhecimento
  reutilizavel, sanitizado e revisavel.
- `knowledge-generator`: especialista em gerar knowledge versionavel a partir de
  fontes locais e documentacoes.
- `knowledge-reviewer`: especialista em revisar snapshots, bloqueando segredo,
  PII indevida, duplicidade e prompt injection.
- `knowledge-curator`: especialista em curadoria continua, deduplicacao,
  arquivamento e reindexacao derivada da knowledge base.
- `knowledge-owner`: autoridade de publicacao controlada da knowledge base
  principal apos revisao.
- `local-llm-operator`: agente runtime para diagnosticar, selecionar e delegar
  tarefas operacionais a LLMs locais como Ollama.
- `local-memory-manager`: agente runtime para inspecionar e curar memoria local,
  preferencias, sessoes e identidade sem expor segredos.
- `memory-sync-manager`: especialista em planejar backup, restore e
  sincronizacao seletiva da memoria local e personalidade.
- `n1-support-agent`: especialista N1 para runbooks operacionais a partir de
  cards Azure DevOps.
- `n2-support-agent`: especialista N2 para investigacao de causa raiz e geracao
  de `patch_plan.md`.
- `presentation-deck-builder`: especialista em templates versionados e geracao
  de apresentacoes PowerPoint.
- `postgres-data-analyzer`: especialista em analise read-only forte de dados
  Postgres.
- `supabase-project-analyst`: especialista em inspecao local e auditoria
  report-only de projetos Supabase, RLS, Auth, Storage, migrations e planos de
  correcao sem aplicar mudancas reais.
- `notification-operator`: agente runtime para formatar, enviar e configurar
  notificacoes locais de tarefas com payload canonico.
- `provider-configurator`: agente runtime para conduzir wizard de configuracao
  de providers, sources e referencias seguras de credenciais.
- `sqlserver-data-analyzer`: especialista em analise read-only de dados SQL
  Server.
- `sqlserver-change-operator`: especialista em mudancas controladas em SQL
  Server.
- `shared-memory-curator`: agente runtime para criar memorias compartilhadas,
  revisar contribuicoes externas e publicar apenas conteudo aprovado pelo dono.
- `software-specification-analyst`: especialista em analise de requisitos,
  entrevistas, analise de projetos e especificacoes completas de software.
- `task-orchestrator`: agente runtime que planeja prompts livres, seleciona
  especialistas, coordena execucao e aciona revisao.
- `technical-integration-analyst`: especialista em documentacoes tecnicas de
  integracoes e artefatos de teste.
- `topdesk-orchestrator`: especialista em TOPdesk para incidentes e triagem.
