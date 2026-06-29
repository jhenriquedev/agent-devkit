# Agent DevKit

Agent DevKit is a CLI runtime for specialist AI agents, capabilities,
provider-aware automations and local host adapters for Codex and Claude.
On first run, the npm wrapper creates a local Python environment under
`~/.agent-devkit/python` (or `AGENT_DEVKIT_HOME`) and installs the bundled
`requirements.txt` dependencies.

The npm package installs the canonical command:

```bash
agent
```

## Install

```bash
npm install -g agent-devkit
```

Validate the installation:

```bash
agent
agent --version
agent -v
agent doctor
```

Expected version for this release:

```text
agent 0.3.0
```

## Quick Start

List available agents and capabilities:

```bash
agent agents list
agent capabilities list
agent providers list
agent llm list
agent commands list
```

Agent DevKit `v0.3.0` also includes deterministic runtime discovery and
integration commands:

```bash
agent roadmap
agent catalog search pr
agent plan "review this Azure card"
agent route explain "review the PRs waiting for me"
agent eval run routing
agent secrets doctor
agent mcp tools
```

Install project-local host artifacts for Codex, Claude Code and Claude
Desktop/Claude.ai:

```bash
cd /path/to/your/project
agent install project --target . --host all
agent doctor --project .
```

Run a natural-language task:

```bash
agent "analise o problema relatado no card 9900"
```

Natural-language mode requires an LLM backend. Deterministic commands such as
`agent agents list`, `agent capabilities list`, `agent doctor`, `agent provider`
and `agent run` do not require an LLM.

Running `agent` without arguments starts the local onboarding status and wizard:
memory, personality, LLM backends, Ollama, toolchain, sources and next actions.
Use `agent onboard minimal` for identity, coordinator LLM, Qwen3-0.6B via
Ollama and local memory. Use `agent onboard complete` to include toolchain,
providers/sources, specialist catalog, local automations, tasks, notifications,
knowledge and shared memory. Both commands return plans; external installs
still require explicit opt-in.

The canonical executable remains `agent`, but the local public agent name can be
changed during onboarding, with `agent --rename <name>`, with
`agent personality edit --rename <name>`, or through a natural-language prompt
such as `agent "mude seu nome para ianota10"`. To expose an executable alias,
use `agent alias add <name>`.

Useful operational commands:

```bash
agent plan "analyze Azure card 7914"
agent execute --dry-run "summarize these logs"
agent workflow install daily-pr-review --dry-run
agent local-llm doctor
agent local-llm install qwen3:0.6b --dry-run
agent skill create my-skill --description "Local skill"
agent script create hello --command "echo hello"
agent team init
agent team doctor
agent knowledge init
agent knowledge search "runbook procedure"
agent shared-memory create --title "Support runbooks"
agent shared-memory submit <memory-id> --title "New runbook" --content "..." --key <contributor-key>
agent shared-memory review <memory-id> <submission-id>
agent shared-memory publish <memory-id> <submission-id> --yes --owner-key <owner-key>
agent contribute pr my-extension --dry-run
agent mcp manifest
agent mcp serve
```

## Complete Configuration Tutorial

There are three practical ways to use agents from the CLI:

1. Use an official authenticated host CLI, such as Codex CLI or Claude Code.
2. Use API keys for OpenAI, Anthropic or OpenRouter.
3. Use a local OpenAI-compatible backend, such as Ollama.

Agent DevKit does not log in directly to ChatGPT web, Claude.ai or Claude
Desktop. To reuse a user subscription/login, it delegates to the official host
CLI already installed and authenticated on your machine. For CI, automation or
non-interactive servers, prefer API-key backends.

### Option A: GPT through Codex CLI

Install the official Codex CLI:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

Run Codex once and complete the browser login with your ChatGPT account or API
key:

```bash
codex
```

Verify that the binary is available:

```bash
codex --version
```

Configure Agent DevKit to use Codex CLI as the default LLM backend:

```bash
agent llm configure codex-cli --set-default
agent llm doctor codex-cli
```

Run a prompt:

```bash
agent "analyze this repository and identify stabilization risks"
```

### Option B: Claude through Claude Code

Install the official Claude Code CLI:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Run Claude Code once and complete the browser login:

```bash
claude
```

Verify that the binary is available:

```bash
claude --version
```

Configure Agent DevKit to use Claude Code as the default LLM backend:

```bash
agent llm configure claude-code --set-default
agent llm doctor claude-code
```

Run a prompt:

```bash
agent "plan the investigation for this production incident"
```

To switch Claude accounts later, open `claude` and use `/login` inside the
interactive session.

### Option C: OpenAI API key

Agent DevKit stores credential references, not secret values. Keep the API key
in your shell environment:

```bash
export OPENAI_API_KEY="..."
agent llm configure openai --api-key-env OPENAI_API_KEY --model gpt-5 --set-default
agent llm doctor openai
```

### Option D: Anthropic API key

```bash
export ANTHROPIC_API_KEY="..."
agent llm configure anthropic --api-key-env ANTHROPIC_API_KEY --model claude-sonnet-4-5 --set-default
agent llm doctor anthropic
```

### Option E: OpenRouter API key

```bash
export OPENROUTER_API_KEY="..."
agent llm configure openrouter --api-key-env OPENROUTER_API_KEY --model openai/gpt-5 --set-default
agent llm doctor openrouter
```

### Option F: Ollama local backend

```bash
agent ollama status
agent ollama models
agent ollama pull qwen3:0.6b --dry-run
agent ollama pull qwen3:0.6b --yes
ollama serve
agent llm configure ollama --base-url http://localhost:11434/v1 --model qwen3:0.6b --set-default
agent llm doctor ollama
```

Ollama is treated as an operational worker for repetitive local tasks. Codex and
Claude remain the preferred coordinators and reviewers for high-level planning,
software changes, documents, automation decisions and final review.

### Switch or override the backend

```bash
agent llm list
agent llm set-default codex-cli
agent llm set-default claude-code
agent llm set-default openai
agent llm disable ollama
agent llm enable ollama
agent llm doctor
```

Use one backend for a single run:

```bash
agent --llm claude-code "analyze this incident"
agent --llm openai "create a regression test plan"
```

## Use Agents From The CLI

Agent DevKit has two execution modes:

- `agent "<prompt>"`: natural-language routing; requires an LLM backend.
- `agent run <agent> <capability>`: deterministic execution; does not require
  an LLM backend.

Natural-language example:

```bash
agent "analise o problema relatado no card 9900"
```

If a required source or provider is not configured yet, prompt routing and
capability execution return the global `provider-configurator` setup wizard
instead of a hardcoded manual command:

```bash
agent --json "analise o card 7914 do projeto sustentacao no azure"
agent --json run topdesk-orchestrator read-incident --number "I 2606 001"
```

The wizard asks for opt-in and collects one configuration item at a time.

Deterministic example:

```bash
agent run azure-devops-orchestrator read-card --project "Project" --id 9900 --include-comments
```

Inspect a capability contract before running it:

```bash
agent inspect azure-devops-orchestrator read-card
```

## Local Decisions And Tool Control

Agent DevKit persists opt-in and opt-out decisions locally. You can inspect and
change tools, integrations, skills and LLM availability from commands or natural
language prompts:

```bash
agent decisions list
agent tools disable azure-devops
agent tools enable azure-devops
agent integrations list
agent skills list
agent "mostre minhas decisoes"
agent "desative o azure devops por enquanto"
agent "reative o ollama"
```

Decisions are stored under `~/.agent-devkit/config/decisions.json`; secret values
are not stored there.

## Configure LLM Backends

Agent DevKit stores references to credentials, not secret values. API keys stay
in environment variables.

OpenAI:

```bash
export OPENAI_API_KEY="..."
agent llm configure openai --api-key-env OPENAI_API_KEY --model gpt-5 --set-default
agent llm doctor
```

Anthropic:

```bash
export ANTHROPIC_API_KEY="..."
agent llm configure anthropic --api-key-env ANTHROPIC_API_KEY --model claude-sonnet-4-5 --set-default
```

OpenRouter:

```bash
export OPENROUTER_API_KEY="..."
agent llm configure openrouter --api-key-env OPENROUTER_API_KEY --model openai/gpt-5 --set-default
```

Local or host-authenticated backends:

```bash
agent llm configure ollama --base-url http://localhost:11434/v1 --model qwen3:0.6b --set-default
agent llm configure codex-cli --set-default
agent llm configure claude-code --set-default
```

Official references:

- Codex CLI: https://developers.openai.com/codex/cli
- Codex authentication: https://developers.openai.com/codex/auth
- Claude Code quickstart: https://code.claude.com/docs/en/quickstart
- Claude Code setup: https://code.claude.com/docs/en/setup

## Configure Providers

Configure only the provider you need for a task. Missing optional providers are
reported as partial diagnostics and do not break local discovery.

Azure DevOps:

```bash
export AZURE_DEVOPS_ORG="your-org"
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
export TOPDESK_BASE_URL="https://your-instance.topdesk.net"
export TOPDESK_USERNAME="user"
export TOPDESK_APP_PASSWORD="..."
agent provider configure topdesk --env TOPDESK_BASE_URL --env TOPDESK_USERNAME --env TOPDESK_APP_PASSWORD
agent provider doctor topdesk
```

You can also inspect a credentials file without printing secret values:

```bash
agent credential resolve topdesk --env-file ./topdesk.env
```

## Deterministic Capability Runs

Use `agent run` when you want direct execution without natural-language routing:

```bash
agent run azure-devops-orchestrator read-card --project "Project" --id 9900 --include-comments
agent run aws-cloudwatch-log-analyzer search-log-events --help
```

Inspect a capability contract before running it:

```bash
agent inspect azure-devops-orchestrator read-card
```

## Memory

Agent DevKit can keep local usage memory for routines and source preferences:

```bash
agent memory show
agent memory reset --all
```

## Host Installation

Install only one host adapter when needed:

```bash
agent install project --target . --host codex
agent install project --target . --host claude-code
agent install project --target . --host claude-desktop
agent install global --host all
```

Preview writes without touching the filesystem:

```bash
agent install project --target . --host all --dry-run --json
```

## Links

- GitHub: https://github.com/jhenriquedev/agent-devkit
- npm: https://www.npmjs.com/package/agent-devkit
- License: MIT
