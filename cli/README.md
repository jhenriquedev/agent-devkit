# CLI

Interface de linha de comando do Agent DevKit.

## Objetivo

Fornecer comandos curtos e unificados para descobrir agentes, listar
capabilities e inspecionar contratos sem navegar manualmente pela estrutura de
arquivos.

O executavel publico fica na raiz do repositorio:

```bash
agent <comando>
python agent <comando>
```

`agent` e o comando canonico. `ai-devkit` e `aikit` continuam aceitos apenas
como aliases legados de compatibilidade.

## Comandos MVP

```bash
agent --help
agent --version
agent agents list
agent capabilities list
agent capabilities list --agent azure-devops-orchestrator
agent doctor
agent commands list
agent llm list
agent llm configure openai --api-key-env OPENAI_API_KEY --model gpt-5 --set-default
agent llm doctor
agent install project --target . --host all
agent install project --target . --host all --profiles sustentacao,infra
agent install global --host codex
agent doctor --project .
agent providers list
agent provider status aws
agent credential resolve topdesk --env-file ./topdesk.env
agent "analise esse incidente"
agent run azure-devops-orchestrator read-card --project "Projeto" --id 123 --include-comments
```

`agent run`, `agent doctor`, `agent agents list`, `agent capabilities list`,
`agent commands list` e `agent install` sao deterministicos e nao exigem LLM.
`agent llm` tambem e deterministico: ele apenas lista, configura e diagnostica
backends. `agent providers` e `agent provider` leem o registry local de
providers e diagnosticam metadados disponiveis no processo atual. `agent
credential` resolve referencias de credenciais sem imprimir valores. `agent`
e a entrada em linguagem natural: ele cria um `execution_plan` multiagente,
seleciona coordenador, especialistas, configurador de provider e revisor, e usa
capabilities deterministicas quando a rota estiver pronta. Backend LLM so e
necessario quando a tarefa nao puder ser resolvida por rota/capability local; se
nao houver backend disponivel, retorna uma mensagem instrutiva para usar
`agent run` ou configurar um backend.

Em `--json`, respostas de `agent "<prompt>"` incluem:

- `execution_plan`: contrato `ai-devkit.agentic-plan/v1`;
- `specialist_tasks`: capabilities escolhidas por agente;
- `configuration_tasks`: providers/fontes que precisam de opt-in;
- `review_task`: revisao final exigida pelo runtime;
- `orchestration_trace`: trilha resumida de coordenacao.

Os papeis de runtime tambem sao agentes reais versionados em `agents/`:
`task-orchestrator`, `provider-configurator`, `local-llm-operator` e
`execution-reviewer`. Eles aparecem em `agent agents list` e suas capabilities
podem ser inspecionadas como qualquer outro agente.

Quando o plano identifica uma tarefa operacional repetitiva e ha Ollama
configurado, o runtime delega essa parte ao `local-llm-operator` e injeta o
resultado como contexto para o coordenador principal. Essa delegacao nunca faz
escrita externa, aprovacao, decisao de permissao ou revisao final.

Quando `review_gate.required = true`, a conclusao passa pelo
`execution-reviewer` usando um reviewer independente, preferindo `claude-code`
ou `codex-cli`. Sem reviewer configurado, quando o reviewer retorna
`REVIEW BLOCKED`, ou quando nao retorna `REVIEW OK`, a execucao termina como
`needs-review` e nao como `ok`.

## Instalacao global e por projeto

O comando `install` instala apenas artefatos de descoberta do Agent DevKit para
hosts locais. Ele nao pede credenciais, nao cria `.env` e nao persiste segredos.

Instalacao por projeto:

```bash
agent install project --target . --host all
agent install project --target . --host codex
agent install project --target . --host claude-code
agent install project --target . --host claude-desktop
agent install project --target . --host claude-ai
```

Instalacao global:

```bash
agent install global --host all
agent install global --host codex
agent install global --host claude-code
agent install global --host claude-desktop
agent install global --host claude-ai
```

Use `--dry-run` para revisar os caminhos antes de gravar:

```bash
agent install project --target . --host all --dry-run --json
```

Destinos criados:

- `.ai-devkit/config.yaml`: configuracao minima da instalacao, sem segredos.
- `.ai-devkit/ai-devkit.lock`: lock por projeto com runtime, commit e perfis.
- `~/.agent-devkit/runtime.lock`: lock global com runtime, commit e canal local.
- `.codex/plugins/ai-devkit`: bundle local do plugin Codex.
- `.codex/skills/ai-devkit-router`: skill de roteamento para Codex.
- `.claude/plugins/ai-devkit`: bundle local do plugin Claude Code.
- `.claude/skills/ai-devkit-router`: skill de roteamento para Claude Code.
- `.claude/commands`: comandos `devkit-*` para Claude Code.
- `.claude/plugins/ai-devkit-skill`: bundle do skill Claude Desktop/Claude.ai.
- `.claude/skills/ai-devkit`: skill Agent DevKit para Claude Desktop/Claude.ai.

Para testes ou automacao, `AIKIT_INSTALL_HOME` ou `--home` redirecionam o alvo
de instalacao global sem tocar no home real.

## Release gate

Antes de publicar ou entregar uma versao, rode o gate completo:

```bash
python3 scripts/release-gate.py --json
```

Para uma verificacao rapida sem a suite completa de `unittest`:

```bash
python3 scripts/release-gate.py --quick --json
```

## Lock e versionamento

O instalador grava um lock para registrar a versao efetivamente instalada:

```bash
agent install global --host all
agent install project --target . --host all --profiles sustentacao,infra
```

Arquivos gerados:

- global: `~/.agent-devkit/runtime.lock`
- projeto: `<project>/.ai-devkit/ai-devkit.lock`

O lock registra `source`, `repository`, `ref`, `commit`, `git_ref`, `dirty`,
`version`, `installed_at` e `channel`. Em instalacoes por projeto, tambem grava
`profiles` e a politica `providers.policy: project-overrides-global`.

Use o doctor com projeto para detectar divergencia entre lock global e lock do
projeto:

```bash
agent doctor --project .
agent doctor --project . --json
agent doctor --project . --home /tmp/agent-devkit-home --json
```

Uma divergencia de lock gera warning, nao erro: o objetivo e avisar que o
projeto esta fixado em runtime diferente do global sem bloquear diagnosticos
basicos. Use `--home` ou `AIKIT_INSTALL_HOME` quando o lock global foi criado
em um home alternativo.

## Doctor expandido

`agent doctor` valida a saude local sem chamar sistemas externos e sem exigir
credenciais. Providers e LLMs ausentes sao tratados como diagnostico parcial,
nao como falha estrutural.

```bash
agent doctor
agent doctor --json
agent doctor --project .
agent doctor --project . --home /tmp/agent-devkit-home --json
```

A saida JSON inclui:

- `diagnostics.runtime`: raiz, configs e checks locais do runtime.
- `diagnostics.locks`: lock global, lock do projeto e divergencias.
- `diagnostics.plugins`: plugins fonte e plugins instalados por host.
- `diagnostics.providers`: resumo de providers configurados, ausentes e com
  erro, sem valores de segredo.
- `diagnostics.llm`: resumo de backends LLM, host CLIs e chaves por referencia,
  sem valores de segredo.

O comando retorna erro apenas para problemas estruturais do runtime, como raiz
inexistente. Provider opcional ausente, LLM sem chave ou CLI de host nao
instalada aparecem no bloco de diagnostico e podem ser resolvidos sob demanda.

## Backends LLM

O modo `agent "<prompt>"` exige um backend LLM. O Agent DevKit suporta tres
familias de backend:

- CLIs oficiais autenticadas fora do Agent DevKit (`codex-cli` e
  `claude-code`).
- APIs configuradas por referencia a variavel de ambiente (`openai`,
  `anthropic` e `openrouter`).
- Endpoint local compativel com OpenAI (`ollama`).

O Agent DevKit nao faz login direto no ChatGPT web, Claude.ai ou Claude
Desktop. Para usar login/assinatura de usuario, autentique primeiro a CLI
oficial e depois configure o Agent DevKit para chama-la.

### Codex CLI

Instale o Codex CLI oficial:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

Execute `codex` uma vez e conclua o login:

```bash
codex
codex --version
agent llm configure codex-cli --set-default
agent llm doctor codex-cli
```

Quando este backend e usado, o runtime chama:

```bash
codex exec --skip-git-repo-check --ephemeral "<prompt>"
```

### Claude Code

Instale o Claude Code oficial:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Execute `claude` uma vez e conclua o login:

```bash
claude
claude --version
agent llm configure claude-code --set-default
agent llm doctor claude-code
```

Quando este backend e usado, o runtime chama:

```bash
claude --print --permission-mode plan "<prompt>"
```

### APIs por chave

O Agent DevKit nao grava chaves em claro. Backends de API sao configurados por
referencia a variaveis de ambiente:

```bash
export OPENAI_API_KEY="..."
agent llm configure openai --api-key-env OPENAI_API_KEY --model gpt-5 --set-default
agent llm doctor openai
```

Anthropic:

```bash
export ANTHROPIC_API_KEY="..."
agent llm configure anthropic --api-key-env ANTHROPIC_API_KEY --model claude-sonnet-4-5 --set-default
agent llm doctor anthropic
```

OpenRouter:

```bash
export OPENROUTER_API_KEY="..."
agent llm configure openrouter --api-key-env OPENROUTER_API_KEY --model openai/gpt-5 --set-default
agent llm doctor openrouter
```

### Ollama local

```bash
agent ollama status
agent ollama models
agent ollama pull qwen2.5-coder --dry-run
agent ollama pull qwen2.5-coder --yes
ollama serve
agent llm configure ollama --base-url http://localhost:11434/v1 --model qwen2.5-coder --set-default
agent llm doctor ollama
```

Ollama e tratado como executor operacional local. Codex e Claude continuam como
coordenadores/revisores preferenciais para decisao, especificacao, codigo,
documentos, automacoes e fechamento de entrega.

Backends suportados no MVP:

- `openai`: API OpenAI ou endpoint OpenAI-compatible.
- `anthropic`: API Anthropic.
- `openrouter`: API OpenRouter.
- `ollama`: servidor local compativel com OpenAI em `http://localhost:11434/v1`.
- `codex-cli`: CLI oficial do Codex, autenticada fora do Agent DevKit.
- `claude-code`: CLI oficial do Claude Code, autenticada fora do Agent DevKit.

Comandos disponiveis:

```bash
agent llm list
agent llm configure openai --api-key-env OPENAI_API_KEY --set-default
agent llm configure anthropic --api-key-env ANTHROPIC_API_KEY --set-default
agent llm configure openrouter --api-key-env OPENROUTER_API_KEY --set-default
agent llm configure ollama --base-url http://localhost:11434/v1 --model qwen2.5-coder --set-default
agent llm configure codex-cli --set-default
agent llm configure claude-code --set-default
agent llm set-default codex-cli
agent llm disable ollama
agent llm enable ollama
agent llm doctor
agent llm doctor openai
```

Tambem e possivel escolher um backend para uma unica execucao:

```bash
agent --llm claude-code "analise este incidente"
agent --llm openai "crie um plano de testes"
```

A configuracao padrao fica em `~/.agent-devkit/config.json`. Para automacao e
testes, use `AGENT_DEVKIT_HOME`, `AI_DEVKIT_CONFIG_HOME` ou `AIKIT_CONFIG_HOME`
para apontar outro diretorio. `~/.ai-devkit` continua aceito como home legado
quando ja existir.

Para migrar explicitamente o home legado para o caminho canonico:

```bash
agent config migrate-home --dry-run
agent config migrate-home
```

## Providers

O registry central fica em `providers/*.yaml`. Ele declara providers remotos,
locais, ferramentas e bridges entre agentes. Nesta etapa, o CLI apenas lista e
diagnostica providers; configuracao persistente de credenciais fica para o
fluxo lazy.

Comandos disponiveis:

```bash
agent providers list
agent providers list --json
agent provider status
agent provider status elasticsearch
agent provider doctor aws
agent provider configure topdesk --env-file ./topdesk.env
agent provider configure azure-devops --env AZURE_DEVOPS_ORG --env AZURE_DEVOPS_PAT
agent provider configure topdesk --env-file ./topdesk.env --session-only
agent provider unset topdesk
```

`provider configure` grava apenas referencias seguras, como `env:VAR` e
`env-file:/caminho#VAR`; valores de segredos nunca sao persistidos nem exibidos.
Use `--session-only` para validar uma configuracao sem escrever em
`~/.agent-devkit/config.json`. Arquivos passados com `--env-file` precisam conter
ao menos um campo reconhecido pelo provider selecionado.

Quando um prompt ou capability exige uma source/provider ausente, o runtime
aciona o configurador global `provider-configurator` e retorna um wizard
agentico com opt-in e perguntas progressivas em vez de sugerir um comando
hardcoded:

```bash
agent --json "analise o card 7914 do projeto sustentacao no azure"
agent --json run topdesk-orchestrator read-incident --number "I 2606 001"
```

Fluxo de continuidade:

```bash
agent wizard list
agent wizard show <wizard-id>
agent wizard answer <wizard-id> sim
agent wizard answer <wizard-id> <resposta>
agent wizard cancel <wizard-id>
```

Quando a ultima resposta valida e recebida, o wizard salva uma source
reutilizavel em `~/.agent-devkit/config.json`, sem segredos em claro, e retoma o
prompt original. Use `agent wizard answer <wizard-id> <resposta> --no-run` para
salvar a configuracao sem retomar a execucao.

Em terminal interativo, `agent "<prompt>"` conduz essas perguntas diretamente.
Com `--json`, pipes ou automacao, ele retorna `needs-input` com `wizard_id` para
que o fluxo seja continuado de forma explicita e nao bloqueante.

## Decisoes, ferramentas e integracoes

Opt-ins e opt-outs ficam em `~/.agent-devkit/config/decisions.json` e podem ser
gerenciados por comando ou prompt. O roteamento por prompt usa os catalogos de
toolchain, providers, skills e backends LLM; nao depende de uma lista fixa de
alvos.

```bash
agent decisions list
agent tools list
agent tools disable azure-devops
agent tools enable azure-devops
agent integrations list
agent skills list
agent "mostre minhas decisoes"
agent "desative o azure devops por enquanto"
agent "desative topdesk"
agent "habilite gh-cli"
agent "desative a skill security-review"
agent "desative openrouter"
agent "reative o ollama"
agent "liste llms"
agent "esqueca minha decisao sobre anthropic"
```

Quando um nome e ambiguo entre categorias, o retorno fica `needs-input` e inclui
`matches` para o usuario informar a categoria ou o id exato.

## Credential Resolver

O resolver de credenciais opera por referencias e origens, sem retornar valores
sensíveis. Backends reconhecidos nesta etapa:

- `explicit`
- `env`
- `env-file`
- `os-keychain`
- `aws-default-chain`
- `plain-session-only`

Comandos:

```bash
agent credential backends
agent credential resolve topdesk --env-file ./topdesk.env
agent provider status topdesk --env-file ./topdesk.env
```

Arquivos aceitos por `--env-file`:

- `.env`: `CHAVE=valor`
- `.json`: objeto plano `{ "CHAVE": "valor" }`
- `.yaml`/`.yml`: mapeamento plano

## Fallback controlado em `run`

Capabilities podem declarar dependencias em `requires.providers`. Antes de
executar o runner, `agent run` verifica se os providers exigidos estao
configurados. Se um provider estiver ausente e a capability declarar fallback,
o runtime retorna um resultado padronizado com `status: partial` ou
`status: blocked`, sem chamar o provider real e sem imprimir segredos.

Exemplo de retorno parcial em JSON:

```json
{
  "kind": "run",
  "status": "partial",
  "providers": {
    "used": [],
    "missing": ["elasticsearch"],
    "skipped": ["elasticsearch"]
  },
  "fallback_applied": "plan_only"
}
```

Quando o provider esta pronto, o runner executa normalmente e o retorno inclui
`status: ok`, `providers.used` e `fallback_applied: null`.

A prioridade inicial de resolucao e: valores explicitos internos, ambiente do
processo, depois `--env-file`. O CLI informa apenas nomes de campos encontrados,
origem e lacunas; valores nunca sao exibidos.

Quando um provider e configurado com `--env-file`, `agent provider status
<provider>` passa a usar esse arquivo automaticamente enquanto a configuracao
existir. Use `agent provider unset <provider>` para remover a referencia.

## Guardrails de execucao

`agent run` aplica guardrails antes de chamar o runner da capability.
Capabilities com `write_policy: confirm` continuam podendo produzir plano ou
dry-run sem confirmacao. Para execucao real, o runtime exige uma flag de
execucao da capability (`--execute`, `--yes-confirm`, `--yes-save` ou
equivalente) e uma confirmacao propria:

```bash
agent run azure-devops-orchestrator comment-card --fixture card.json --comment "..."
agent run azure-devops-orchestrator comment-card --fixture card.json --comment "..." --execute --confirm-execute
```

`--confirm-execute` e uma flag do runtime: ela e removida antes de chamar o
runner da capability. As flags de dominio, como `--execute`, `--yes-confirm` e
`--yes-save`, continuam sendo repassadas ao runner. Isso permite manter os
runners focados no dominio.

Capabilities marcadas com `write_policy: blocked_by_default` permanecem
bloqueadas mesmo com `--execute --confirm-execute`. Para liberar uma execucao
perigosa em fluxo controlado, e necessario declarar tambem `--allow-dangerous`:

```bash
agent run aws-operations-operator purge-sqs-queue-plan ... --execute --confirm-execute --allow-dangerous
```

Esse desbloqueio apenas passa pelo guardrail central. A capability ainda deve
validar alvo, permissao, plano, evidencia e rollback.

## Saida padronizada de `run`

Com `--json`, `agent run` sempre retorna um payload parseavel para execucoes de
capability. Os estados possiveis sao `ok`, `partial`, `blocked` e `failed`.

Campos estaveis:

- `schema_version`: versao do contrato, hoje `ai-devkit.run/v1`.
- `status` e `ok`: resultado operacional.
- `agent_id` e `capability_id`: identificadores curtos para automacao.
- `providers`: listas `used`, `missing` e `skipped`.
- `fallback_applied`: fallback usado ou `null`.
- `evidence`, `risks`, `next_steps` e `artifacts`: listas sempre presentes.
- `stdout`, `stderr`, `returncode` e `runner`: diagnostico do runner quando
  aplicavel.

Quando o runner falha em modo JSON, o runtime retorna `status: failed`. Isso
inclui codigo diferente de zero, runner declarado mas ausente e timeout. Em modo
humano, o comportamento legado e preservado para nao ocultar a saida direta do
runner.

Os comandos legados continuam aceitos:

```bash
agent agents
agent capabilities azure-devops-orchestrator
agent inspect azure-devops-orchestrator read-card
agent run azure-devops-orchestrator read-card --project "Projeto" --id 123 --include-comments
agent run database-change-operator plan-migration --path migrations/202606211200_create_table.up.sql
agent run bpo-analyser analyze-cpf-proposals --cpf 12345678901
agent run bpo-analyser analyze-proposal --proposal-number 123456
agent run presentation-deck-builder register-template --template status.pptx --template-id status-report --version 0.1.0 --yes-save --confirm-execute
agent run postgres-data-analyzer list-tables --database outro_banco --schema public
agent run sqlserver-data-analyzer list-tables --schema dbo
agent run sqlserver-change-operator plan-migration --path migrations/001_create_table.up.sql
agent run software-specification-analyst analyze-project-context --project . --output-dir specifications/contexto --yes-create-dir
agent run software-specification-analyst conduct-requirements-interview --input demanda.md --analysis-dir specifications/contexto --output-dir specifications/entrevista --yes-create-dir
agent run software-specification-analyst refine-analysis-with-feedback --analysis-dir specifications/contexto --feedback respostas.md --output-dir specifications/refinada --yes-create-dir
agent run software-specification-analyst create-final-spec-from-analysis --analysis-dir specifications/refinada --output-dir specifications/final --yes-create-dir
agent run software-specification-analyst create-complete-spec --input demanda.md
agent run topdesk-orchestrator read-incident --number "I 2606 001"
```

Aliases:

```bash
agent a
agent c --agent azure-devops-orchestrator
agent i azure-devops-orchestrator read-card
agent r azure-devops-orchestrator read-card --project "Projeto" --id 123
agent a
agent c azure-devops-orchestrator
agent i azure-devops-orchestrator read-card
agent r azure-devops-orchestrator read-card --project "Projeto" --id 123
```

Use `--json` para saida estruturada:

```bash
agent inspect azure-devops-orchestrator read-card --json
agent --json inspect azure-devops-orchestrator read-card
```

## Execucao

O comando `run` delega para o `runner.py` declarado no `capability.yaml`.
Apenas capabilities com `entrypoint.runner` sao executaveis pela CLI. As demais
podem ser inspecionadas e usadas por agentes consumidores como contratos
declarativos.

No `azure-devops-orchestrator`, as capabilities executaveis atuais sao:

- `list-cards`
- `read-card`
- `comment-card`
- `update-card-tags`
- `assign-card`
- `move-card`
- `prepare-card-analysis`
- `generate-cards-report`
- `attach-file`

No `aws-cloudwatch-log-analyzer`, as capabilities executaveis atuais sao:

- `list-log-groups`
- `search-log-events`
- `analyze-service-error`
- `trace-request`
- `detect-error-patterns`
- `extract-log-samples`
- `generate-incident-report`
- `correlate-azure-card-logs`

No `elasticsearch-log-analyzer`, as capabilities executaveis atuais sao:

- `list-log-sources`
- `search-log-events`
- `analyze-service-errors`
- `trace-request`
- `detect-error-patterns`
- `extract-log-samples`
- `generate-log-report`
- `correlate-azure-card-logs`

No `bpo-analyser`, as capabilities executaveis atuais sao:

- `test-connection`
- `list-proposals-by-cpf`
- `analyze-cpf-proposals`
- `find-latest-proposal-by-cpf`
- `consult-proposal`
- `consult-attached-documents`
- `analyze-proposal`

No `postgres-data-analyzer`, as capabilities executaveis atuais sao:

- `test-connection`
- `list-databases`
- `list-schemas`
- `list-tables`
- `describe-table`
- `list-relationships`
- `suggest-joins`
- `search-tables`
- `search-columns`
- `explore-database-domain`
- `generate-erd-report`
- `run-readonly-query`
- `validate-readonly-query`
- `build-analysis-query`
- `explain-query-plan`
- `sample-table`
- `profile-table`
- `analyze-query-result`
- `detect-sensitive-columns`
- `detect-data-quality-issues`
- `analyze-cpf-column`
- `estimate-table-size`
- `compare-tables`
- `trace-record`
- `generate-data-report`

No `n1-support-agent`, as capabilities executaveis atuais sao:

- `execute-n1-card-runbook`
- `extract-card-entities`
- `analyze-restrictive-base`
- `analyze-cognito-user`
- `analyze-onboarding-status`
- `analyze-proposal-status`
- `collect-customer-logs`
- `decide-n1-outcome`
- `generate-n1-artifacts`
- `update-azure-card`

No `database-change-operator`, as capabilities executaveis atuais sao:

- `test-write-permissions`
- `plan-migration`
- `apply-migration`
- `rollback-migration`
- `run-write-script`
- `upsert-records`
- `update-records`
- `migration-report`

No `sqlserver-data-analyzer`, as capabilities executaveis atuais sao:

- `test-connection`
- `list-databases`
- `list-schemas`
- `list-tables`
- `describe-table`
- `list-relationships`
- `suggest-joins`
- `search-tables`
- `search-columns`
- `explore-database-domain`
- `generate-erd-report`
- `run-readonly-query`
- `validate-readonly-query`
- `build-analysis-query`
- `explain-query-plan`
- `sample-table`
- `profile-table`
- `analyze-query-result`
- `detect-sensitive-columns`
- `detect-data-quality-issues`
- `analyze-cpf-column`
- `estimate-table-size`
- `compare-tables`
- `trace-record`
- `generate-data-report`

No `sqlserver-change-operator`, as capabilities executaveis atuais sao:

- `test-write-permissions`
- `plan-migration`
- `apply-migration`
- `rollback-migration`
- `run-write-script`
- `create-object`
- `update-records`
- `delete-records`
- `upsert-records`
- `backup-records`
- `change-report`

No `technical-integration-analyst`, as capabilities executaveis atuais sao:

- `ingest-technical-docs`
- `extract-integration-contract`
- `identify-missing-information`
- `analyze-integration-flow`
- `generate-test-data`
- `generate-http-artifacts`
- `generate-protocol-artifacts`
- `run-integration-tests`
- `generate-technical-docs`

No `software-specification-analyst`, as capabilities executaveis atuais sao:

- `analyze-project-context`
- `conduct-requirements-interview`
- `refine-analysis-with-feedback`
- `create-final-spec-from-analysis`
- `create-complete-spec`

No `presentation-deck-builder`, as capabilities executaveis iniciais sao:

- `register-template`
- `list-templates`
- `list-template-versions`
- `generate-template-input-file`

No `topdesk-orchestrator`, as capabilities executaveis atuais sao:

- `list-incidents`
- `read-incident`
- `create-incident`
- `update-incident`
- `analyze-incident-insufficiency`
- `request-more-info`
- `incident-report`

Exemplo com fixture local:

```bash
agent run azure-devops-orchestrator read-card --fixture /tmp/card.json --include-comments
```

Exemplo com Azure DevOps real, usando `.env` da raiz:

```bash
agent run azure-devops-orchestrator read-card --project "Projeto" --id 123 --include-comments
```

Para Azure DevOps, sempre prefira informar `--project` no comando. Isso evita
fixar o agente a um unico projeto e permite usar a mesma organizacao/token para
varios projetos.

Exemplo com TOPdesk real, usando `.env` da raiz:

```bash
agent run topdesk-orchestrator read-incident --number "I 2606 001" --include-progress-trail
```

Para TOPdesk, escritas como `create-incident`, `update-incident` e
`request-more-info` rodam em dry-run por padrao. Use `--execute` apenas quando a
alteracao estiver revisada.

Exemplo com documentacao tecnica de integracao:

```bash
agent run technical-integration-analyst generate-http-artifacts --file api.md --postman-output /tmp/collection.json
```

Exemplo com Database Change Operator:

```bash
agent run database-change-operator plan-migration --path migrations/202606211200_create_table.up.sql
agent run database-change-operator apply-migration --path migrations/202606211200_create_table.up.sql --execute
```

Para banco de dados, escritas tambem rodam em dry-run por padrao. Use `--execute`
apenas depois de revisar o plano.

Exemplo com Software Specification Analyst:

```bash
agent run software-specification-analyst analyze-project-context --project . --output-dir specifications/contexto --yes-create-dir
agent run software-specification-analyst conduct-requirements-interview --input demanda.md --analysis-dir specifications/contexto --output-dir specifications/entrevista --yes-create-dir
agent run software-specification-analyst refine-analysis-with-feedback --analysis-dir specifications/contexto --feedback respostas.md --output-dir specifications/refinada --yes-create-dir
agent run software-specification-analyst create-final-spec-from-analysis --analysis-dir specifications/refinada --output-dir specifications/final --yes-create-dir
agent run software-specification-analyst create-complete-spec --input demanda.md
```

Os runners propoem criar pastas em `specifications/<slug>/` no projeto atual e
perguntam antes de criar a pasta. O fluxo recomendado e analise, entrevista,
refinamento com feedback e especificacao final. Para automacao revisada, use
`--yes-create-dir`.

Exemplo multibanco com a mesma connection string base:

```bash
agent run postgres-data-analyzer list-tables --database outro_banco --schema public
agent run sqlserver-data-analyzer list-tables --database OutroBanco --schema dbo
```
agent run database-change-operator migration-report --database outro_banco
```

O argumento `--database` troca somente o nome do database na URL Postgres. Host,
porta, usuario, senha e parametros como `sslmode` continuam vindo do `.env`.
