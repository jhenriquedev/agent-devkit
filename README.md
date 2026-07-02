# Agent DevKit

Agent DevKit is a TypeScript/Node rewrite of the `agent-devkit` package.

The public npm package is `agent-devkit`; the canonical command is `agent`.
Version `0.3.4` starts a new implementation focused on a maintainable CLI/TUI
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
npm run --silent docker:agent -- install node --verify --json
npm run --silent docker:agent -- reset --dry-run
npm run --silent docker:agent -- update --latest --dry-run
npm run --silent docker:agent -- tools --json
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
- `app` must execute capabilities through the shared tool runtime when exposing generic tools.
- `modules` owns product capabilities as isolated vertical slices.
- A module groups capabilities from the same functional domain; it is not an agent.
- A module surface is the canonical agentic interface for that domain.
- Surface capability metadata is derived from capability configs to avoid drift.
- The tool runtime is the canonical execution socket for CLI, MCP, TUI and future agent loops.
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
Standalone binaries are outside the initial `0.3.4` scope.

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
Runtime data uses a canonical local store layout:

```txt
~/.agent-devkit/
  data/
    preferences/
    personalization/
    logs/
    secrets/
    context/
  keys/
```

`data/` contains generated runtime data. `keys/` contains local key material and
is intentionally kept outside `data/`.

Maintenance commands:

```bash
agent reset --dry-run
agent reset --yes
agent reset -g --dry-run
agent update --latest --dry-run
agent update 0.3.4 --dry-run
agent update 0.3.4 --yes
agent preferences
agent preferences --json
agent preferences themes
agent preferences set-theme forest-teal
agent preferences update --theme ocean-blue
agent projects
agent projects create --name "Agent DevKit" --path .
agent sessions
agent sessions create --title "Planning"
agent sessions search "memory"
agent sessions resume <session-id>
agent tools
agent tools --json
agent install node --dry-run
agent install node --verify
agent run project.doctor --input '{}' --json
agent run environment.dependencies --input '{"action":"verify","dependency":"node"}' --json
agent run project.reset --input '{"confirmed":true,"dryRun":false,"homeDirectory":"/tmp/home","projectRoot":"/tmp/project","scope":"project"}' --approve --json
agent mcp
agent mcp stdio
agent mcp http --port 3333 --origin http://localhost:3333
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

## Tool Runtime

The generic tool runtime lets any interface discover and invoke capabilities
without importing command-specific code.

```bash
agent tools --json
agent run <capabilityId> --input '<json>' --json
```

`agent tools --json` returns each capability id, module, risk, approval rule,
input JSON Schema and output JSON Schema. `agent run` validates the JSON input,
checks approval requirements, executes the capability and returns a structured
runtime envelope:

```json
{
  "status": "succeeded",
  "capabilityId": "project.doctor",
  "risk": "read-only",
  "input": {},
  "output": {}
}
```

Risky capabilities return `approval_required` unless `--approve` is passed. MCP
uses the same runtime contract, so future TUI and agent-loop execution should
also plug into this layer instead of calling capabilities directly.

## MCP Server

Agent DevKit exposes its runtime tools through a real MCP server.

For local MCP hosts that launch a subprocess, use stdio:

```bash
agent mcp
agent mcp stdio
```

Add Agent DevKit to a stdio MCP host such as Claude Desktop by pointing its
`claude_desktop_config.json` at the installed `agent` binary:

```json
{
  "mcpServers": {
    "agent-devkit": {
      "command": "agent",
      "args": ["mcp", "stdio"]
    }
  }
}
```

For local HTTP clients, use Streamable HTTP on the single `/mcp` endpoint:

```bash
agent mcp http --host 127.0.0.1 --port 3333
```

HTTP binds to `127.0.0.1` by default. If the client sends an `Origin` header,
that origin must be explicitly allowed:

```bash
agent mcp http --port 3333 --origin http://localhost:3333
```

MCP tools are derived from `ToolRuntime.listTools()`. Calls execute through
`ToolRuntime.execute()` and return the same structured runtime envelope in a
text JSON MCP result.

Risky tools require explicit approval. MCP callers can pass control metadata
that is removed before capability validation:

```json
{
  "_agent": {
    "approved": true
  },
  "confirmed": true,
  "dryRun": true,
  "homeDirectory": "/tmp/home",
  "projectRoot": "/tmp/project",
  "scope": "project"
}
```

CLI and MCP logging must not persist raw tool inputs. Sensitive CLI flags such
as `agent run --input` are redacted before usage and technical logs are written.

## Environment Dependencies

Agent DevKit has a provider-based dependency lifecycle module exposed as the
`environment.dependencies` capability.

```bash
agent install node --dry-run
agent install node --verify --json
agent install --node --verify
```

The first provider is `node`. It is read-only: it checks the current Node.js
runtime, compatibility and environment, but does not install, upgrade,
downgrade or uninstall Node.js. Mutating lifecycle actions currently return
planned or unsupported results without side effects.

Future providers such as `aws-cli`, `docker`, `gh-cli` and `ollama` should
implement the same provider contract instead of adding one-off installer logic
to CLI, TUI, MCP or agent loops.

## Internal Docs

The local `docs/` folder is intentionally ignored by Git. Public documentation
belongs in root files such as this README, `AGENT.md`, and `.github/`.
