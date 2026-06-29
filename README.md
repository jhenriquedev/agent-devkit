# Agent DevKit

Biblioteca de agentes especialistas, capabilities, prompts, repositories e
conhecimento operacional para desenvolvimento, sustentacao e especificacao de
software com IA.

Nome publico do projeto no GitHub: `agent-devkit`. Nome do produto:
**Agent DevKit**. Comando canonico da CLI: `agent`.

> Objetivo: substituir o uso ad-hoc de prompts por agentes pre-criados,
> versionados e prontos para uso, com baixo consumo de contexto, decisoes mais
> consistentes e artefatos padronizados.

## Instalacao rapida

Instale o CLI publicado no npm:

```bash
npm install -g agent-devkit
```

Valide a instalacao:

```bash
agent
agent --version
agent -v
agent doctor
```

O pacote instala o comando canonico `agent`. O nome do pacote npm e
`agent-devkit`. Na primeira execucao, o wrapper npm prepara um ambiente Python
local em `~/.agent-devkit/python` (ou no `AGENT_DEVKIT_HOME`) e instala as
dependencias de `requirements.txt`, para evitar setup manual de bibliotecas
Python. Ao executar apenas `agent`, o CLI entra no onboarding local: verifica
memoria, personalidade, backends LLM, Ollama, toolchain, sources, tasks e
proximas acoes sem exigir prompt manual.

## Primeiro uso

Comandos deterministicos nao precisam de LLM configurada. Use estes comandos
para validar se o runtime esta saudavel e quais agentes existem:

```bash
agent agents list
agent capabilities list
agent providers list
agent llm list
agent commands list
agent doctor
```

Na `v0.3.0`, o runtime tambem expoe superficies deterministicas para
descoberta, avaliacao e integracao por hosts:

```bash
agent onboard minimal
agent onboard complete
agent roadmap
agent catalog search pr
agent plan "analise o card 7914 do azure"
agent route explain "revise as prs que recebi hoje"
agent eval run routing
agent secrets doctor
agent mcp tools
```

`agent onboard minimal` planeja o setup essencial: identidade, coordenador LLM
opcional, mini-cerebro Qwen2.5-0.5B embarcado e memoria local. `agent onboard complete`
inclui tambem toolchain, providers/sources, catalogo de agentes, automacoes
locais, tarefas, notificacoes, knowledge e memoria compartilhada. Ambos
retornam plano deterministico; instalacoes externas continuam exigindo opt-in.

Instale os artefatos locais do Agent DevKit no projeto em que voce trabalha:

```bash
cd /caminho/do/projeto
agent install project --target . --host all
agent doctor --project .
```

Esse comando cria apenas arquivos de descoberta para hosts como Codex e Claude.
Ele nao grava `.env`, nao solicita credenciais e nao persiste segredos.

Depois de configurar uma LLM, voce pode usar prompt livre direto no comando
canonico:

```bash
agent "analise o problema relatado no card 9900"
```

Esse modo usa backend LLM. Se nenhum backend estiver configurado, a CLI informa
como configurar uma LLM ou como executar uma capability deterministica com
`agent run`.

O nome publico do agente e configuravel localmente sem mudar o comando
canonico. O comando continua sendo `agent`, mas a identidade pode ser alterada
no onboarding, por flag ou por linguagem natural:

```bash
agent --rename Ianota
agent personality edit --rename Ianota
agent "mude seu nome para ianota10"
agent "qual seu nome?"
```

Se voce quiser tambem chamar o executavel por outro nome, crie um alias local:

```bash
agent alias add jarvis
~/.agent-devkit/bin/jarvis "qual seu nome?"
```

## Tutorial completo de configuracao

Existem tres formas principais de usar agentes pelo CLI:

1. Usar uma CLI oficial ja autenticada, como Codex CLI ou Claude Code.
2. Usar API key de OpenAI, Anthropic ou OpenRouter.
3. Usar um modelo local compativel, como Ollama.

O Agent DevKit nao faz login direto no ChatGPT web, Claude.ai ou Claude
Desktop. Para reaproveitar assinatura/login de usuario, ele chama as CLIs
oficiais instaladas na maquina. Para automacao, CI ou ambientes sem login
interativo, prefira API key.

### Opcao A: usar GPT pelo Codex CLI

Instale o Codex CLI oficial:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

Abra o Codex CLI e conclua o login com sua conta ChatGPT ou API key:

```bash
codex
```

Valide se o binario esta no `PATH`:

```bash
codex --version
```

Configure o Agent DevKit para usar o Codex CLI como backend padrao:

```bash
agent llm configure codex-cli --set-default
agent llm doctor codex-cli
```

Execute um prompt livre:

```bash
agent "analise este repositorio e indique riscos de estabilizacao"
```

Quando este backend e usado, o Agent DevKit chama:

```bash
codex exec --skip-git-repo-check --ephemeral "<prompt>"
```

### Opcao B: usar Claude pelo Claude Code

Instale o Claude Code oficial:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Abra o Claude Code e conclua o login com sua conta Claude:

```bash
claude
```

Valide se o binario esta no `PATH`:

```bash
claude --version
```

Configure o Agent DevKit para usar Claude Code como backend padrao:

```bash
agent llm configure claude-code --set-default
agent llm doctor claude-code
```

Execute um prompt livre:

```bash
agent "planeje a investigacao do incidente informado pelo suporte"
```

Quando este backend e usado, o Agent DevKit chama:

```bash
claude --print --permission-mode plan "<prompt>"
```

### Opcao C: usar OpenAI por API key

Defina a chave no ambiente. O Agent DevKit salva apenas a referencia para a
variavel, nao o valor da chave:

```bash
export OPENAI_API_KEY="..."
agent llm configure openai --api-key-env OPENAI_API_KEY --model gpt-5 --set-default
agent llm doctor openai
```

Uso:

```bash
agent "gere um plano de rollback para esta mudanca"
```

### Opcao D: usar Anthropic por API key

```bash
export ANTHROPIC_API_KEY="..."
agent llm configure anthropic --api-key-env ANTHROPIC_API_KEY --model claude-sonnet-4-5 --set-default
agent llm doctor anthropic
```

Uso:

```bash
agent "revise este plano tecnico e aponte lacunas"
```

### Opcao E: usar OpenRouter por API key

```bash
export OPENROUTER_API_KEY="..."
agent llm configure openrouter --api-key-env OPENROUTER_API_KEY --model openai/gpt-5 --set-default
agent llm doctor openrouter
```

Uso:

```bash
agent "roteie este pedido para o agente especialista adequado"
```

### Mini cerebro embarcado e Ollama local

O Agent DevKit vem com um mini cerebro local embarcado baseado no contrato
`Qwen/Qwen2.5-0.5B-Instruct` para conversa inicial, onboarding, setup e tarefas
simples sem depender de Claude, Codex, API externa ou Ollama.

Ollama continua suportado como pool opcional de workers locais. O Agent DevKit
consegue diagnosticar Ollama, listar modelos, planejar pull e usar o backend
local como trabalhador operacional quando ele estiver configurado ou tiver
modelos instalados. Claude/Codex continuam sendo os coordenadores e revisores
preferenciais para decisao, especificacao e entrega final.

```bash
agent setup mini-brain --yes
agent local-llm doctor
agent ollama status
agent ollama models
agent ollama pull qwen3:0.6b --dry-run
agent ollama pull qwen3:0.6b --yes
ollama serve
agent llm configure ollama --base-url http://localhost:11434/v1 --model qwen3:0.6b --set-default
agent llm doctor ollama
```

Uso:

```bash
agent "explique quais capabilities podem ajudar nesta demanda"
```

### Alternar backend padrao

```bash
agent llm list
agent llm set-default codex-cli
agent llm set-default claude-code
agent llm set-default openai
agent llm disable ollama
agent llm enable ollama
agent llm doctor
```

Tambem e possivel escolher um backend apenas para uma execucao:

```bash
agent --llm claude-code "analise este incidente"
agent --llm openai "crie um plano de testes"
```

Referencias oficiais:

- Codex CLI: https://developers.openai.com/codex/cli
- Codex authentication: https://developers.openai.com/codex/auth
- Claude Code quickstart: https://code.claude.com/docs/en/quickstart
- Claude Code setup: https://code.claude.com/docs/en/setup

## Usar agentes por CLI

Existem dois modos de execucao:

- `agent "<prompt>"`: entrada em linguagem natural; monta um plano multiagente,
  usa capabilities deterministicas quando possivel e exige backend LLM apenas
  quando nenhuma rota local atende a tarefa.
- `agent plan "<prompt>"`: gera o plano multiagente explicito sem executar LLM,
  automacao ou escrita externa.
- `agent execute "<prompt>"` e `agent orchestrate "<prompt>"`: executam pelo
  runtime agentico com roteamento, wizard de provider/source, modelo local
  quando permitido e review gate.
- `agent run <agent> <capability>`: execucao deterministica; nao exige LLM.

Exemplo em linguagem natural:

```bash
agent "analise o problema relatado no card 9900"
```

Em `--json`, prompts roteados retornam `execution_plan` com o coordenador
`task-orchestrator`, tarefas especialistas, configuracoes pendentes,
`review_task` e `orchestration_trace`. Se uma fonte ou provider faltar, o plano
fica `needs-input` e inclui o `provider-configurator` com a proxima pergunta do
wizard. Quando a fonte esta configurada e a capability e read-only, o runtime
executa a task primaria pelo runner existente e revisa a conclusao pelo
`review_gate`.

Para tarefas operacionais como resumo, classificacao, extracao e normalizacao,
o runtime pode usar o mini cerebro embarcado para bootstrap/conversa simples ou
delegar uma subtarefa limitada ao `local-llm-operator` usando Ollama quando
disponivel. O resultado local aparece em `local_llm_execution` e e usado apenas
como contexto de apoio pelo coordenador principal.

Quando `review_gate.required = true`, o Agent DevKit exige uma segunda revisao
concreta pelo `execution-reviewer`, preferindo `claude-code` ou `codex-cli`.
Sem reviewer independente configurado, ou sem uma decisao explicita
`REVIEW OK`, a execucao retorna `needs-review` em vez de concluir como `ok`.

Exemplo deterministico:

```bash
agent run azure-devops-orchestrator read-card --project "Projeto" --id 9900 --include-comments
```

Antes de executar uma capability, voce pode inspecionar contrato, entradas e
saidas:

```bash
agent inspect azure-devops-orchestrator read-card
```

Comandos operacionais da `v0.2.1`:

```bash
agent catalog list --type workflow
agent catalog rebuild-index
agent workflow show daily-pr-review
agent workflow install daily-pr-review --dry-run
agent local-llm doctor
agent local-llm install qwen3:0.6b --dry-run
agent skill create minha-skill --description "Skill local"
agent script create hello --command "echo hello"
agent agents create meu-agente --description "Agente local"
agent team init
agent team doctor
agent contribute pr minha-extensao --dry-run
```

O MCP stdio embutido fica disponivel sempre que o CLI esta instalado:

```bash
agent mcp manifest
agent mcp tools
agent mcp serve
```

As ferramentas MCP expõem catalogo, onboarding, doctor, route explain, plano
agentico, evals, workflows, LLM local, artefatos locais, sources, wizards,
memoria local e memoria compartilhada. As operacoes com risco de escrita
externa continuam bloqueadas ou em dry-run por padrao.

## Memoria compartilhada

Memorias compartilhadas sao workspaces locais em `.agent-devkit/shared-memory`.
O criador e o dono da memoria; outros agentes recebem uma URL local e uma chave
de contribuidor, enviam novidades para `incoming`, e o dono revisa antes de
publicar em `accepted`.

```bash
agent shared-memory create --title "Runbooks de suporte"
agent shared-memory submit <memory-id> --title "Novo runbook" --content "..." --key <contributor-key>
agent shared-memory review <memory-id> <submission-id>
agent shared-memory publish <memory-id> <submission-id> --yes --owner-key <owner-key>
```

## Modo equipe

O modo equipe cria uma configuracao versionavel de projeto em
`.agent-devkit/team.yaml`. Esse arquivo pode guardar defaults de providers,
sources, workflows, permissoes, limites de LLM local e politica de prompt
injection, mas nunca valores de credenciais.

```bash
agent team init
agent team status
agent team doctor
agent team onboard
agent team profile list
agent team profile show default
agent team profile export default --path ./team-profile.yaml
agent team profile import ./team-profile.yaml
```

Segredos continuam pessoais, em `~/.agent-devkit`, por referencia segura:

```bash
agent secret set azure-devops pat --env AZURE_DEVOPS_PAT
```

## Knowledge fabric local

A `v0.3.0` introduz uma base de conhecimento compartilhada file-first. A fonte
canonica e um diretorio `knowledge-base/` com Markdown, JSON e YAML; indices
lexicais ou semanticos sao derivados e podem ser recriados.

```bash
agent knowledge init
agent knowledge doctor
agent knowledge snapshot create --title "Runbook" --content "# Runbook..."
agent knowledge review runbook
agent knowledge publish runbook --yes --owner-agent knowledge-owner
agent knowledge snapshot list
agent knowledge snapshot show runbook
agent knowledge snapshot score runbook
agent knowledge snapshot submit runbook
agent knowledge review list
agent knowledge curate
agent knowledge sync
agent knowledge reindex
agent knowledge search "runbook procedimento"
agent knowledge index
agent knowledge-base create --provider github
agent knowledge-base join kb_01JZ... --provider s3
```

Snapshots sao tratados como conteudo externo nao confiavel. A revisao bloqueia
segredos, PII obvia e sinais de prompt injection antes de publicar localmente.

Os providers `knowledge-*` documentam o storage previsto para GitHub, S3,
Supabase Storage, Google Drive, SharePoint, OneDrive, Notion, Obsidian,
filesystem local e indice vetorial derivado. Providers remotos ficam em
`draft`, exigem opt-in e fallback para plano/manual enquanto nao houver
credencial e implementacao ativa.

## QA destrutivo em Docker

Para validar instalacao limpa, bootstrap de dependencias, onboarding, memoria,
knowledge-base, MCP, desinstalacao e remocao da `.agent-devkit` sem tocar no
host:

```bash
npm run docker:qa
```

O script empacota o runtime local, instala o tarball em um container
`node:20-bookworm`, executa os fluxos criticos e remove o home local criado no
container.

## Configurar providers

Providers tambem sao configurados por referencia. Configure apenas o que for
necessario para a tarefa; o agente pode seguir com fallback quando um provider
opcional nao estiver disponivel.

Azure DevOps:

```bash
export AZURE_DEVOPS_ORG="sua-org"
export AZURE_DEVOPS_PAT="..."
agent provider configure azure-devops --env AZURE_DEVOPS_ORG --env AZURE_DEVOPS_PAT
agent provider doctor azure-devops
```

AWS:

```bash
export AWS_PROFILE="default"
export AWS_REGION="us-east-1"
agent provider configure aws --env AWS_PROFILE --env AWS_REGION
agent provider doctor aws
```

TOPdesk:

```bash
export TOPDESK_BASE_URL="https://sua-instancia.topdesk.net"
export TOPDESK_USERNAME="usuario"
export TOPDESK_APP_PASSWORD="..."
agent provider configure topdesk --env TOPDESK_BASE_URL --env TOPDESK_USERNAME --env TOPDESK_APP_PASSWORD
agent provider doctor topdesk
```

Exemplo de uso deterministico com uma capability:

```bash
agent run azure-devops-orchestrator read-card --project "Projeto" --id 9900 --include-comments
```

## Configuracao agentica e decisoes locais

Quando um prompt ou capability exige uma fonte ou provider ainda nao
configurado, o `agent` nao deve mais parar apenas sugerindo um comando manual.
Ele aciona o configurador global `provider-configurator`, retorna um wizard
agentico com opt-in, perguntas progressivas e retomada do prompt original:

```bash
agent --json "analise o card 7914 do projeto sustentacao no azure"
agent --json run topdesk-orchestrator read-incident --number "I 2606 001"
```

O retorno inclui `setup_wizard.wizard_id`. Continue o roteiro uma resposta por
vez; ao concluir, o runtime cria a source reutilizavel e retoma o prompt
original automaticamente:

```bash
agent wizard list
agent wizard show wiz-20260628120000-abc12345
agent wizard answer wiz-20260628120000-abc12345 sim
agent wizard answer wiz-20260628120000-abc12345 "minha-org"
agent wizard answer wiz-20260628120000-abc12345 AZURE_DEVOPS_PAT
agent wizard cancel wiz-20260628120000-abc12345
```

Em terminal interativo, sem `--json`, o proprio `agent` conduz o roteiro
pergunta por pergunta. Em automacoes, pipes e testes, use os subcomandos
`agent wizard ...` para evitar bloqueio de terminal.

Credenciais devem ser informadas por referencia, por exemplo o nome de uma
variavel de ambiente ou o caminho de um arquivo local. O Agent DevKit nao grava
o valor bruto do segredo no estado do wizard nem na configuracao da source.

O usuario tambem pode controlar ferramentas, integracoes, skills e LLMs sem
editar arquivos diretamente. Os alvos sao resolvidos pelos catalogos locais:
`tooling/toolchain.yaml`, `providers/*.yaml`, `vendor/skills/CATALOG.md` e
backends LLM registrados.

```bash
agent decisions list
agent tools list
agent tools disable azure-devops
agent tools enable azure-devops
agent integrations list
agent skills list
agent llm list
```

As mesmas operacoes podem ser feitas por prompt:

```bash
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

Se um nome existir em mais de uma categoria, o agente retorna `needs-input` com
as opcoes encontradas em vez de escolher silenciosamente. Use a categoria no
prompt para resolver, por exemplo `desative a integracao figma` ou `desative a
ferramenta figma-mcp`.

Se o usuario negar ou desativar uma ferramenta, a decisao fica persistida em
`~/.agent-devkit/config/decisions.json` e o agente segue sem usar essa ferramenta
nas proximas sessoes ate reativacao explicita.

O home global canonico e `~/.agent-devkit`. Instancias antigas em `~/.ai-devkit`
continuam funcionando como legado; use `agent config migrate-home --dry-run` e
depois `agent config migrate-home` para migrar explicitamente.

Comandos uteis:

```bash
agent commands list
agent inspect azure-devops-orchestrator read-card
agent memory show
agent memory backup create --title "Antes da migracao"
export AGENT_DEVKIT_BACKUP_PASSPHRASE="frase longa"
agent memory backup create --title "Antes da migracao" --encrypted --passphrase-env AGENT_DEVKIT_BACKUP_PASSPHRASE
agent memory backup restore <backup-id> --yes
agent memory reset --all
```

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
- `plugins/claude-code-ai-devkit`: plugin local para Claude Code, incluindo
  skill, comandos e subagentes opcionais para usar capabilities do Agent DevKit
  em contextos isolados.
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

Instalacoes globais gravam `~/.agent-devkit/runtime.lock`; instalacoes por projeto
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

Saidas JSON de `agent "<prompt>"` usam o contrato de orquestracao
`ai-devkit.agentic-plan/v1` dentro de `execution_plan`. Os estados principais
sao `planned`, `needs-input`, `ok`, `partial` e `blocked`. Saidas JSON de
`agent run` usam contrato `ai-devkit.run/v1`, com `status`
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

- [`agent-devkit-agent-builder`](agents/agent-devkit-agent-builder/):
  especialista interno para planejar, criar scaffold e validar novos agentes do
  proprio Agent DevKit.
- [`automation-architect`](agents/automation-architect/): especialista em
  classificar pedidos de automacao, escolher tecnologia adequada, planejar a
  solucao e delegar por contrato para builders especificos.
- [`generic-agent-builder`](agents/generic-agent-builder/): especialista em
  planejar, gerar e revisar agentes genericos portaveis para projetos e hosts
  externos.
- [`python-automation-builder`](agents/python-automation-builder/):
  especialista em planejar, gerar, revisar e empacotar automacoes Python
  seguras para tarefas repetitivas.
- [`selenium-automation-builder`](agents/selenium-automation-builder/):
  especialista em planejar, gerar e revisar automacoes Selenium/WebDriver quando
  houver requisito tecnico para Selenium.
- [`pyautogui-automation-builder`](agents/pyautogui-automation-builder/):
  especialista em planejar, gerar e revisar automacoes desktop visuais com
  PyAutoGUI como ultimo recurso.
- [`playwright-automation-builder`](agents/playwright-automation-builder/):
  especialista em planejar, gerar, revisar e executar checks controlados de
  automacoes web modernas com Playwright.
- [`aws-lambda-builder`](agents/aws-lambda-builder/): especialista em
  planejar, gerar, revisar e empacotar projetos AWS Lambda locais sem executar
  deploy real.
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
- [`docker-container-builder`](agents/docker-container-builder/): especialista
  em planejar, gerar e revisar artefatos Docker locais, incluindo Dockerfile,
  .dockerignore, docker-compose.yml, README.docker.md e planos de build sem
  executar build, push ou deploy real.
- [`execution-loop-builder`](agents/execution-loop-builder/): especialista em
  planejar, gerar, revisar e registrar loops de execucao controlados com
  budgets, criterios de parada, estado minimo e auditoria por iteracao.
- [`drawio-diagram-builder`](agents/drawio-diagram-builder/): especialista em
  criar, revisar e refinar diagramas Draw.io editaveis a partir de briefings,
  documentos, pastas, cards Azure, especificacoes, inventarios tecnicos e
  feedback iterativo.
- [`elasticsearch-log-analyzer`](agents/elasticsearch-log-analyzer/):
  especialista em Elasticsearch para descoberta de fontes, busca de eventos,
  rastreio de requests, padroes de erro e relatorios de logs.
- [`execution-reviewer`](agents/execution-reviewer/): agente runtime de
  revisao final, revisao de planos e revisao de resultados antes da conclusao.
- [`contribution-reviewer`](agents/contribution-reviewer/): agente runtime para
  validar extensoes locais, revisar riscos de contribuicao upstream e planejar
  PRs em modo report-only.
- [`excel-workbook-builder`](agents/excel-workbook-builder/): especialista em
  templates, preenchimento, conciliacao, revisao e exportacao de planilhas
  Excel.
- [`figma-ui-ux-product-designer`](agents/figma-ui-ux-product-designer/):
  especialista UI/UX para analisar contexto de produto e criar, recriar,
  evoluir e revisar designs mobile e web com Figma quando disponivel.
- [`github-pr-reviewer`](agents/github-pr-reviewer/): especialista em Pull
  Requests GitHub para listar revisoes pendentes, inspecionar PRs, revisar diffs
  em modo report-only e criar automacoes locais conservadoras.
- [`knowledge-infra-builder`](agents/knowledge-infra-builder/): especialista em
  criar e diagnosticar a infraestrutura file-first da knowledge base
  compartilhada.
- [`knowledge-author`](agents/knowledge-author/): especialista em criar
  snapshots de conhecimento reutilizavel, sanitizado e revisavel.
- [`knowledge-generator`](agents/knowledge-generator/): especialista em gerar
  knowledge versionavel a partir de arquivos, pastas, projetos e documentacoes.
- [`knowledge-reviewer`](agents/knowledge-reviewer/): especialista em revisar
  snapshots, bloqueando segredo, PII indevida, duplicidade e prompt injection.
- [`knowledge-curator`](agents/knowledge-curator/): especialista em curadoria
  continua, deduplicacao, arquivamento e reindexacao derivada da knowledge base.
- [`knowledge-owner`](agents/knowledge-owner/): autoridade de publicacao
  controlada da knowledge base principal apos revisao.
- [`local-llm-operator`](agents/local-llm-operator/): agente runtime para
  diagnosticar, selecionar e delegar tarefas operacionais a LLMs locais.
- [`local-memory-manager`](agents/local-memory-manager/): agente runtime para
  inspecionar e curar memoria local, preferencias, sessoes e identidade sem
  expor segredos.
- [`memory-sync-manager`](agents/memory-sync-manager/): especialista em
  planejar backup, restore e sincronizacao seletiva da memoria local e
  personalidade.
- [`notification-operator`](agents/notification-operator/): agente runtime para
  formatar, enviar e configurar notificacoes locais de tarefas com payload
  canonico.
- [`n1-support-agent`](agents/n1-support-agent/): especialista N1 para executar
  runbooks operacionais a partir de cards Azure DevOps, orquestrando Azure,
  SQL Server, logs e TOPdesk.
- [`n2-support-agent`](agents/n2-support-agent/): especialista N2 para validar
  handoff N1, investigar causa raiz em codigo/evidencias e gerar `patch_plan.md`.
- [`postgres-data-analyzer`](agents/postgres-data-analyzer/):
  especialista em PostgreSQL read-only para descoberta de databases, schemas,
  tabelas, relacionamentos, joins, queries assistidas, perfilamento, qualidade
  de dados e relatorios analiticos.
- [`supabase-project-analyst`](agents/supabase-project-analyst/):
  especialista em inspecao local e auditoria report-only de projetos Supabase,
  cobrindo RLS, Auth, Storage, migrations, Edge Functions e planos de correcao
  sem aplicar mudancas reais.
- [`shared-memory-curator`](agents/shared-memory-curator/): agente runtime para
  criar memorias compartilhadas, revisar contribuicoes externas e publicar
  apenas conteudo aprovado pelo dono.
- [`provider-configurator`](agents/provider-configurator/): agente runtime que
  conduz wizard de providers, sources e referencias seguras de credenciais.
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
- [`task-orchestrator`](agents/task-orchestrator/): agente runtime que planeja
  prompts livres, seleciona especialistas, coordena execucao e aciona revisao.
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
