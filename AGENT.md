# Agent DevKit Agent Guide

This repository contains the `0.4.0` rewrite of Agent DevKit.

## Product Direction

Agent DevKit is an installable npm package that exposes the command `agent`.
The product should support two interaction styles:

- structured CLI commands for automation and scripting;
- a rich terminal UI for interactive onboarding, prompt sessions, diagnostics and long-running workflows.
- an MCP interface for external agents and compatible hosts.

## Technical Stack

- TypeScript
- Node.js `>=20`
- npm package distribution
- Ink + React for TUI
- Commander for CLI parsing
- Zod for runtime contracts and config validation
- tsup for builds
- Vitest for tests
- Biome for formatting and linting

## Architecture Rules

Keep boundaries strict:

- `src/app`: presenter layer. CLI, TUI, view models and user-facing formatting.
- `src/app/mcp`: presenter layer for external agents. MCP tools/resources must call domain use cases, not CLI commands.
- `src/domain`: product rules. Entities, ports, services and use cases.
- `src/infra`: concrete adapters. Filesystem, config, process execution, local repositories and external integrations.

Dependency direction:

```txt
app -> domain
infra -> domain ports
domain -> no app or infra imports
```

Do not put business rules in the TUI or CLI parser. Do not let domain code
format terminal output, read files directly, or spawn child processes directly.

## Version Scope

`0.4.0` should become a real publishable package with a minimal CLI/TUI shell
before larger runtime behavior is added.

Initial commands should stay intentionally small:

- `agent`
- `agent "prompt"`
- `agent --help`
- `agent --version`
- `agent doctor`
- `agent agents list`

## Repository Notes

- `docs/` is local-only development documentation and must stay ignored.
- Public project documentation belongs in `README.md`, `AGENT.md`, `LICENSE`,
  and `.github/`.
- Installing the npm package must not create `~/.agent-devkit/` or
  `<project>/.agent-devkit/`. Runtime state is created only after the user runs
  the tool and a command needs that scope.
- Global user state belongs under `~/.agent-devkit/`.
- Project-local state belongs under `<project>/.agent-devkit/` and should be
  created only by explicit project flows such as `agent init` or
  `agent install project`.
- `scripts/` is for maintenance automation: build checks, release validation,
  package verification, cleanup and similar project operations.
- Docker is available for local validation without installing the CLI on the
  host. Prefer `npm run docker:check` for isolated gates and
  `npm run docker:agent -- --help` for containerized CLI/TUI execution.
- Avoid compatibility hacks from the legacy `0.3.x` implementation unless they
  are explicitly part of the new design.
