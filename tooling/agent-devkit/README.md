# Agent DevKit

Agent DevKit is a CLI runtime for specialist AI agents, capabilities,
provider-aware automations and local host adapters for Codex and Claude.

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
agent --version
agent doctor
```

Expected version for this release:

```text
agent 0.0.2
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
agent llm configure ollama --base-url http://localhost:11434/v1 --model qwen2.5-coder --set-default
agent llm configure codex-cli --set-default
agent llm configure claude-code --set-default
```

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
