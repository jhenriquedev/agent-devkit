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
