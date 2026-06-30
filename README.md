# Agent DevKit

Agent DevKit is a TypeScript/Node rewrite of the `agent-devkit` package.

The public npm package is `agent-devkit`; the canonical command is `agent`.
Version `0.4.0` starts a new implementation focused on a maintainable CLI/TUI
runtime while preserving the product direction from the legacy `0.3.x` line.

## Status

This branch is the technical foundation for the rewrite. The package setup,
build, checks and release pipeline are prepared before product behavior is
implemented.

## Install

```bash
npm install -g agent-devkit
```

## Development

```bash
npm install
npm run check
npm run dev -- --help
```

Useful scripts:

```bash
npm run build
npm run typecheck
npm run lint
npm run test
npm run package:verify
npm run package:pack
```

## Docker Development

Use Docker when you want to validate the project without installing dependencies
or the `agent` command in the host environment.

```bash
npm run docker:build
npm run docker:check
npm run docker:agent -- --help
npm run --silent docker:agent -- doctor --json
```

Interactive TUI runs are also executed through the container:

```bash
npm run docker:agent
npm run docker:agent -- "analyze this repository"
```

For debugging inside the same development image:

```bash
npm run docker:shell
```

## Architecture

The project is organized around explicit boundaries:

```txt
src/
  app/
    cli/
    mcp/
    tui/
    viewmodels/

  domain/
    entities/
    ports/
    services/
    usecases/

  infra/
    config/
    filesystem/
    process/
    repositories/
```

Rules:

- `app` owns terminal input/output, CLI parsing, TUI screens and view models.
- `app/mcp` owns the future MCP interface for external agents and hosts.
- `domain` owns product rules, entities, ports and use cases.
- `infra` owns concrete adapters such as filesystem, processes and local config.
- Domain code must not import from `app` or `infra`.
- Presenters must call use cases instead of reading files or spawning processes directly.

## Distribution

The package is npm-first and publishes the `agent` binary from `dist/main.js`.
Standalone binaries are outside the initial `0.4.0` scope.

Installing the npm package must not create runtime folders or project files.
State is created only when the user runs the tool:

```txt
npm install -g agent-devkit
  installs the agent command only

agent
  may create ~/.agent-devkit when global state is needed

agent init
agent install project
  may create <project>/.agent-devkit for project-local state
```

When `.agent-devkit/` exists, it should concentrate Agent DevKit state for that
scope instead of spreading generated files across unrelated project paths.

## Internal Docs

The local `docs/` folder is intentionally ignored by Git. Public documentation
belongs in root files such as this README, `AGENT.md`, and `.github/`.
