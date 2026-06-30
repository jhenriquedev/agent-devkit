# v0.3.1

Embedded mini-brain patch release.

## Highlights

- Ships the embedded `Qwen/Qwen2.5-0.5B-Instruct` mini-brain contract and
  installs the GGUF on demand into `.agent-devkit/models` with explicit opt-in.
- Replaces the previous deterministic mini-brain stub with real local
  inference through `llama-cpp-python`.
- Keeps Ollama as an optional local worker pool for additional models and
  operational delegation instead of making it a prerequisite for first use.
- Lets low-risk `agent "<prompt>"` setup/onboarding conversations run without
  Claude, Codex, Ollama, OpenAI, Anthropic, OpenRouter or API keys.
- Updates package verification to reject GGUF artifacts in the npm runtime while
  keeping model URL, size and SHA-256 in the manifest.
- Updates onboarding and LLM documentation to describe the embedded mini-brain
  as the default bootstrap path and Ollama as an optional extension.

## Validation

- Focused embedded mini-brain, local LLM, onboarding and Ollama delegation tests
  pass locally.
- Source smoke confirms `agent "<prompt>"` uses `embedded-mini-brain` with
  Ollama and host CLIs absent from `PATH`.
- Packaged npm runtime smoke confirms the manifest-only package can bootstrap
  and that the GGUF is not bundled into `runtime/models`.
- `npm run package:build` passes locally.
- `npm run package:verify` passes locally and validates the on-demand embedded
  model contract.

# v0.3.0

Operational autonomy release.

## Highlights

- Expands the runtime into a more complete autonomous Agent DevKit surface with
  no-argument onboarding, local memory, personality, sessions, tasks,
  workflows, knowledge and MCP tools.
- Adds local-first knowledge base commands, shared memory workspaces,
  owner-reviewed submissions, knowledge snapshot review/curation/publish
  flows and provider manifests for future remote sync.
- Adds local artifact management for user-created agents, skills, scripts and
  automations under the Agent DevKit home.
- Extends MCP stdio to expose catalog, capabilities, memory, shared memory,
  tasks, workflows, knowledge, local artifacts, local LLM diagnostics and
  agentic planning.
- Adds specialist agents for knowledge authoring, review, curation, ownership,
  shared memory, local memory and contribution review.
- Improves package verification so the npm artifact validates onboarding,
  MCP, local artifacts, knowledge, shared memory and release metadata before
  publish.
- Documents remaining v0.3.0 gaps in `docs/v0.3.0_problems.md` for follow-up
  stabilization work.

## Validation

- `npm run package:build` passes locally.
- `npm run package:verify` passes locally.
- `python3 scripts/release-gate.py --quick --json` passes locally.
- Release alignment must pass in CI before npm publish.

# v0.2.0

Runtime consolidation release.

## Highlights

- Adds deterministic runtime discovery with `agent roadmap`, searchable
  `agent catalog`, `agent route explain` and `agent --explain`.
- Adds MVP eval suites for routing, catalog, MCP, prompt injection,
  mini-brain limits and generated-agent contracts, wired into the quick release
  gate.
- Adds safe secret reference diagnostics with `agent secrets`, without storing
  raw secret values.
- Evolves MCP stdio with catalog search, route explain, dry-run planning,
  eval, secrets and roadmap tools while preserving read-only defaults.
- Adds local extension, workflow and contribution MVP commands for future
  operational completion work.
- Adds prompt-injection external-content labeling and focused regression tests
  for v0.2.0 CLI contracts.
- Keeps Slack, WhatsApp and Teams integrations out of scope and filters
  preterido problem items from the active roadmap.

## Validation

- Focused v0.2.0, MCP, CLI and architecture tests pass locally.
- Release gate quick check, package build and package verify pass before tag.
- Full Python unittest suite must pass before the release tag.

# v0.1.7

Runtime foundation and integration expansion release.

## Highlights

- Reframes Agent DevKit as the executable agent runtime, with specialist
  agents and capabilities acting as parts of the whole instead of isolated
  folders.
- Splits CLI parsing, dispatch and human rendering from reusable core runtime
  services used by CLI, future hosts and MCP.
- Adds canonical capability execution contracts, normalized write policies,
  safer source handling, observable audit results and stricter quality gates.
- Expands the specialist catalog with agent builders, automation builders,
  Supabase analysis, Docker/Lambda builders, loop engineering, notifications
  and Playwright/Selenium/PyAutoGUI support.
- Adds desktop notifications for macOS, Linux and Windows-compatible local
  channels while keeping remote chat integrations out of this cut.
- Adds the Qwen3-0.6B-oriented mini-brain path for setup, wizard assistance and
  low-risk conversational classification.
- Adds the generic Agent DevKit MCP stdio server surface for hosts such as
  Hermes Agent, OpenClaw and OpenCode without making the base installation
  depend on those hosts.

## Validation

- Full Python unittest suite passes locally.
- Repository validation, release gate and release alignment must pass before
  tag.

# v0.1.6

Runtime agentic stabilization patch.

## Highlights

- Cuts the v0.1.5 hardening work as a patch release after the final delivery
  review.
- Keeps the npm-packaged runtime aligned with the repository runtime before
  publish.
- Strengthens package verification so the npm artifact must include the
  runtime agents, orchestration modules, agentic wizard modules and canonical
  `~/.agent-devkit` home behavior.
- Updates runtime role agent manifests and release metadata to `0.1.6`.

## Validation

- v0.1.5/v0.1.6 focused contract tests pass locally.
- Full repository validation, release alignment and npm package verification
  pass before tag.

# v0.1.5

Runtime agentic hardening release.

## Highlights

- Adds the first real multi-agent orchestration path for `agent "<prompt>"`,
  including `execution_plan`, `specialist_tasks`, `configuration_tasks`,
  `review_task` and `orchestration_trace`.
- Routes configured read-only prompt tasks through the selected specialist
  capability runner instead of treating the plan as metadata only.
- Materializes runtime roles as real agents in `agents/`: `task-orchestrator`,
  `provider-configurator`, `local-llm-operator` and `execution-reviewer`.
- Replaces missing-provider/source dead ends with a global agentic setup wizard
  owned by `provider-configurator`, covering prompt-routed sources and
  capability provider requirements.
- Adds persistent wizard state under `~/.agent-devkit/state/wizards`, `agent
  wizard list/show/answer/cancel`, safe credential references, source creation
  and automatic prompt resume after setup completion.
- Makes `~/.agent-devkit` the canonical global Agent DevKit home, keeps
  `~/.ai-devkit` as legacy fallback when present, and adds `agent config
  migrate-home` for explicit migration.
- Completes the interactive TTY path for setup wizards: without `--json`, the
  agent asks one question at a time, validates answers before persistence and
  never stores raw credential values.
- Adds persistent local decisions for tools, integrations, skills and LLMs,
  including enable/disable commands and prompt-routed control actions.
- Generalizes prompt-routed control actions across catalogued toolchain items,
  providers, vendor skills and LLM backends, with `needs-input` for ambiguous
  targets.
- Adds Ollama status, model listing, model pull and update planning commands,
  and includes Ollama in the plan-first toolchain registry.
- Adds model routing metadata so local LLMs are treated as operational workers
  while Claude/Codex remain preferred coordinators and reviewers.
- Executes selected Ollama delegations through `local-llm-operator` for bounded
  operational work and feeds the result back to the coordinator as supporting
  context.
- Enforces `review_gate` through `execution-reviewer`; required reviews now run
  on an independent reviewer backend and block completion when no reviewer is
  configured, when the reviewer returns `REVIEW BLOCKED`, or when the reviewer
  does not return `REVIEW OK`.
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
