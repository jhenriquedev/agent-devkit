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

The project uses capability-first modules, not DDD layers.

Keep boundaries strict:

- `src/app`: entrypoints and presentation adapters. CLI, TUI and MCP live here.
- `src/modules`: product modules and isolated capabilities.
- `src/infra`: global low-level bases only, such as `Result`, error codes, logger, HTTP client and helpers.
- `src/assets`: shared UI/runtime assets.
- The shared tool runtime is the canonical socket for generic capability discovery and execution.
- External dependency lifecycle belongs to the `environment.dependencies`
  capability and provider contract, not to one-off CLI code.

Each module must follow this shape:

```txt
src/modules/<module>/
  <module>.index.ts
  <module>.config.ts
  <module>.bind.ts
  <module>.surface.ts
  surface/
    knowledge.json
    loop.json
    prompt.json
    skill.json
  capabilities/
    <capability>/
      <capability>.entities.ts
      <capability>.repository.ts
      <capability>.service.ts
      <capability>.viewmodel.ts
      <capability>.readme.md
      <capability>.test.ts
```

Repository interfaces and concrete implementations stay together inside the
capability. This is intentional: capabilities are isolated vertical slices.

All capability service methods must return `Result<left, right>` from
`src/infra/bases/result.ts`. Error codes belong in
`src/infra/bases/errors.ts`.

Infra adapters must also return `Result`. Concrete clients live in
`src/infra/clients`; database contracts stay in `src/infra/bases/database.ts`.
Postgres and Redis clients receive injected driver-compatible executors. File
serialization lives in `src/infra/files` for JSON, TXT, MD and PDF/binary
payloads. Asset loading lives in `src/infra/assets` and must guard against path
traversal outside `src/assets`.

Theme assets live in `src/assets/themes`. The default theme is
`default-purple`, based on the TUI design system in `docs/ai-devkit-ui`.
User preferences live under `~/.agent-devkit/preferences.json` and must be
changed through the `user.preferences` capability.

Capabilities must extend the canonical base from
`src/infra/bases/capability.ts`; repositories must implement its repository
port. Module composition must happen through binders from
`src/infra/bases/bind.ts`, and binding operations must return `Result`.

Each module config must satisfy `src/infra/bases/module.ts` and bind its module
tests through `tests.include`. `npm run test:modules` must use those bindings;
do not add module tests through package-level glob shortcuts.

Module-level surface files define the canonical agentic interface for skill,
knowledge, prompt and loop behavior. Capability metadata is derived from
capability configs to avoid drift. Surface files must validate against
`src/infra/bases/surface.ts`; do not add ad hoc prompt or knowledge files
directly inside capabilities unless they are explicitly referenced as optional
assets by a module surface.

Do not put capability rules in the TUI or CLI parser. `app` must call module
bindings and remain thin.

Generic tool execution must go through `src/modules/capability_tool_runtime.ts`.
The runtime wraps the central capability registry and returns a stable envelope
with `status`, `capabilityId`, `input`, `output`, `error`, `risk`, approval data
and audit timing. CLI, MCP, TUI and future agent loops should consume that
runtime instead of each interface inventing its own capability invocation path.

## Version Scope

`0.4.0` should become a real publishable package with a minimal CLI/TUI shell
before larger runtime behavior is added.

Initial commands should stay intentionally small:

- `agent`
- `agent "prompt"`
- `agent --help`
- `agent --version`
- `agent doctor`
- `agent init`
- `agent reset`
- `agent update`
- `agent install <dependency>`
- `agent tools`
- `agent run <capabilityId> --input '<json>'`
- `agent mcp`
- `agent mcp stdio`
- `agent mcp http --host 127.0.0.1 --port 3333`

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
- MCP stdio must never write human text to stdout; stdout belongs to the MCP
  protocol. Operational messages belong on stderr or in logs.
- MCP HTTP must default to localhost and validate `Origin` when one is sent.
- MCP approval metadata uses `_agent.approved` and must be removed before
  capability input validation.
- `agent run --input` and MCP tool inputs must never be persisted as raw logs.
- Avoid compatibility hacks from the legacy `0.3.x` implementation unless they
  are explicitly part of the new design.
