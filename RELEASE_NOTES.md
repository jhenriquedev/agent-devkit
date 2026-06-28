# v0.1.5

Runtime agentic hardening release.

## Highlights

- Replaces missing-provider/source dead ends with a global agentic setup wizard
  owned by `provider-configurator`, covering prompt-routed sources and
  capability provider requirements.
- Adds persistent local decisions for tools, integrations, skills and LLMs,
  including enable/disable commands and prompt-routed control actions.
- Adds Ollama status, model listing, model pull and update planning commands,
  and includes Ollama in the plan-first toolchain registry.
- Adds model routing metadata so local LLMs are treated as operational workers
  while Claude/Codex remain preferred coordinators and reviewers.
- Adds review-gate metadata for routed work, documents, code, automations and
  local-LLM delegated work.
- Strengthens identity enforcement so backend responses that claim to be
  Claude, Codex or ChatGPT are rewritten to the configured local agent
  identity.

## Validation

- v0.1.5 contract tests pass locally.
- Full repository validation and release verification must pass before tag.

# v0.1.0

Runtime agentic release.

## Highlights

- Adds local Agent DevKit home with memory, personality, aliases, sessions,
  task state, policies, audit trail and cache directories.
- Makes `agent` the canonical CLI entrypoint with natural-language prompt
  routing, configurable personality and custom local aliases.
- Adds persistent conversation sessions with project-scoped active session
  reuse, session listing/resume and token estimates.
- Adds LLM backend preference and fallback across Codex CLI, Claude Code,
  OpenAI, Anthropic, OpenRouter and Ollama.
- Adds plan-first toolchain/setup helpers for Codex, Claude, GitHub CLI and
  supporting external tools.
- Adds local tasks, scheduler, calendar ICS integration and GitHub PR reviewer
  automation in report-only mode by default.
- Adds permission policies, global dry-run behavior and local JSON/Markdown
  audit logs with secret redaction.
- Adds the `github-pr-reviewer` specialist agent and providers for GitHub,
  calendar, local scheduler and local notification.

## Validation

- Repository strict validation passes.
- Release gate quick check passes.
- Full Python unittest suite passes locally.

# v0.0.4

Documentation-only patch release.

## Highlights

- Expanded the GitHub README with a complete first-run configuration tutorial.
- Documented host-authenticated CLI usage through `codex-cli` and
  `claude-code`.
- Documented API-key setup for `openai`, `anthropic` and `openrouter`.
- Documented local Ollama setup, backend switching and per-run backend
  overrides.
- Aligned the npm package README and CLI reference with the same authentication
  and LLM backend guidance.

# v0.0.3

Patch release.

## Highlights

- Adds `-v` as an alias for `--version` on the `agent`, `aikit` and
  `ai-devkit` entrypoints.
- Keeps npm README and CLI documentation aligned with the new version alias.

# v0.0.2

Documentation-only patch release.

## Highlights

- Expanded the GitHub README with installation, first-use, LLM, provider,
  deterministic `agent run`, memory and host-adapter setup examples.
- Expanded the npm package README so npmjs.com shows setup commands and basic
  tutorials for new users.
- No CLI behavior changes from v0.0.1.

## Install

```bash
npm install -g agent-devkit
agent --version
agent doctor
```

# v0.0.1

Initial public release of Agent DevKit.

## Highlights

- Canonical `agent` CLI with deterministic capability execution.
- Specialist agent library with 22 agents and 308 capabilities.
- Provider, credential, LLM, source and local memory management commands.
- Project/global install support for Codex App, Claude Code and Claude Desktop/Claude.ai adapters.
- npm package distribution with the `agent` binary.

## Install

```bash
npm install -g agent-devkit
agent --version
agent doctor
```
