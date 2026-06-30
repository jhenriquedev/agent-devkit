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
npm run test:architecture
npm run test:infra
npm run test:app
npm run test:modules
npm run test:modules -- project
npm run test:module -- self
npm run test:modules:changed
npm run check:fast
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
npm run --silent docker:agent -- init --dry-run
npm run --silent docker:agent -- reset --dry-run
npm run --silent docker:agent -- update --latest --dry-run
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

  modules/
    <module>/
      <module>.index.ts
      <module>.config.ts
      <module>.bind.ts
      <module>.surface.ts
      surface/
        capabilities.json
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

  infra/
    assets/
    bases/
    clients/
    files/
    helpers/

  assets/
    fonts/
    i18n/
    images/
    themes/
```

Rules:

- `app` owns entrypoints and presentation adapters: CLI, TUI and MCP.
- `modules` owns product capabilities as isolated vertical slices.
- A module groups capabilities from the same functional domain; it is not an agent.
- A module surface is the canonical agentic interface for that domain.
- A capability owns its entities, service, repository implementation, view model and tests.
- `infra` contains only global low-level bases and reusable helpers.
- Capability services must return `Result<left, right>` from `infra/bases/result.ts`.
- Module configs must bind their test suites through `infra/bases/module.ts`.
- Module binders must return `Result` through `infra/bases/bind.ts`.
- Capabilities and repositories must implement the contracts from `infra/bases/capability.ts`.
- Module surface files must pass the minimum schemas defined by `infra/bases/surface.ts`.
- Concrete clients live in `infra/clients`; database contracts stay in `infra/bases/database.ts`.
- Postgres and Redis clients must use injected executors.
- File serialization lives in `infra/files` and supports JSON, TXT, MD and PDF/binary payloads.
- Asset loading lives in `infra/assets` and reads from the canonical `src/assets` folders.
- `app` calls module bindings instead of reaching into filesystem, npm or process details directly.

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

Maintenance commands:

```bash
agent reset --dry-run
agent reset --yes
agent reset -g --dry-run
agent update --latest --dry-run
agent update 0.4.0 --dry-run
agent update 0.4.0 --yes
agent preferences
agent preferences --json
agent preferences themes
agent preferences set-theme forest-teal
agent preferences update --theme ocean-blue
```

Initial themes:

- `default-purple`
- `forest-teal`
- `ocean-blue`
- `ember-amber`
- `rose-pink`
- `slate-neutral`
- `high-contrast`

`reset` removes only Agent DevKit state folders and executes destructive work
only with `--yes`. `update` plans an npm global install by default and executes
it only with `--yes`.

## Internal Docs

The local `docs/` folder is intentionally ignored by Git. Public documentation
belongs in root files such as this README, `AGENT.md`, and `.github/`.
