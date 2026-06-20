# Catálogo de Plugins

> Bundles completos (skills + commands + subagents + scripts). Ative/instale via a marketplace do seu agente; os skills internos carregam sob demanda.

**Total: 37 plugins**


## open-design (2)

| Plugin | Descrição | Skills | Commands | Caminho |
|---|---|---|---|---|
| `community-import-smoke-test` | A portable community plugin for validating Open Design plugin import flows. | 0 | 0 | `vendor/plugins/open-design/community/import-smoke-test` |
| `open-design` | Local-first design app · 139 skills + 150 DESIGN.md systems · exposes projects/files/preview tools to your coding agent over stdio MCP. R... | 0 | 0 | `vendor/plugins/open-design/open-design` |

## ruflo (35)

| Plugin | Descrição | Skills | Commands | Caminho |
|---|---|---|---|---|
| `ruflo-adr` | ADR lifecycle management — create, index, supersede, check compliance, and link Architecture Decision Records to code via AgentDB hierarc... | 4 | 1 | `vendor/plugins/ruflo/ruflo-adr` |
| `ruflo-agent` | Agent runtimes for ruflo — local WASM-sandboxed agents (rvagent: 10 wasm_agent_*/wasm_gallery_* MCP tools, built on @ruvector/rvagent-was... | 4 | 2 | `vendor/plugins/ruflo/ruflo-agent` |
| `ruflo-agentdb` | Substrate plugin for Ruflo memory: AgentDB controller bridge (15 agentdb_* MCP tools), RuVector ONNX embeddings (10 embeddings_* tools in... | 2 | 2 | `vendor/plugins/ruflo/ruflo-agentdb` |
| `ruflo-aidefence` | AI safety scanning, PII detection, prompt injection defense, and adaptive threat learning | 2 | 1 | `vendor/plugins/ruflo/ruflo-aidefence` |
| `ruflo-arena` | Competitive ruliology for Ruflo swarms — arenas, tournaments, and adaptive co-evolution of program strategies (ADR-147/148). Strategies-a... | 0 | 1 | `vendor/plugins/ruflo/ruflo-arena` |
| `ruflo-autopilot` | Autonomous /loop-driven task completion with learning, prediction, and progress tracking — wraps 10 autopilot_* MCP tools (status/enable/... | 2 | 2 | `vendor/plugins/ruflo/ruflo-autopilot` |
| `ruflo-browser` | Session-as-skill browser automation: Playwright + RVF cognitive containers + ruvector trajectories + AgentDB selector memory + AIDefence ... | 9 | 1 | `vendor/plugins/ruflo/ruflo-browser` |
| `ruflo-core` | Foundation plugin — registers the ruflo MCP server (300+ tools across memory/agentdb/embeddings/hooks/aidefence/neural/autopilot/browser/... | 4 | 2 | `vendor/plugins/ruflo/ruflo-core` |
| `ruflo-cost-tracker` | Token usage tracking, model cost attribution per agent, budget alerts, and optimization recommendations — uses memory_* (namespace-routed... | 20 | 1 | `vendor/plugins/ruflo/ruflo-cost-tracker` |
| `ruflo-daa` | Dynamic Agentic Architecture — 8 daa_* MCP tools for adaptive agents (create/adapt), cognitive patterns, workflows (create/execute), know... | 2 | 1 | `vendor/plugins/ruflo/ruflo-daa` |
| `ruflo-ddd` | Domain-Driven Design scaffolding — bounded contexts, aggregate roots, domain events, value objects, repositories, and anti-corruption lay... | 3 | 1 | `vendor/plugins/ruflo/ruflo-ddd` |
| `ruflo-docs` | Documentation generation, API docs (JSDoc/TSDoc/OpenAPI), and drift detection — drives the `document` background worker via hooks_worker-... | 2 | 1 | `vendor/plugins/ruflo/ruflo-docs` |
| `ruflo-federation` | Cross-installation agent federation with zero-trust security, peer discovery, consensus-based task routing, and per-call budget circuit b... | 3 | 1 | `vendor/plugins/ruflo/ruflo-federation` |
| `ruflo-goals` | Long-horizon goal planning, deep research orchestration, and adaptive replanning using GOAP algorithms | 5 | 1 | `vendor/plugins/ruflo/ruflo-goals` |
| `ruflo-graph-intelligence` | RuFlo Graph Intelligence Engine — real-time relationship intelligence with complexity-aware execution. Single-entry personalized PageRank... | 0 | 0 | `vendor/plugins/ruflo/ruflo-graph-intelligence` |
| `ruflo-intelligence` | User-facing surface for Ruflo's self-learning system: 6 neural_* + 10 hooks_intelligence_* + 9 routing/meta hooks + 4 SONA/MicroLoRA tool... | 3 | 2 | `vendor/plugins/ruflo/ruflo-intelligence` |
| `ruflo-iot-cognitum` | IoT device lifecycle, telemetry anomaly detection, fleet management, and witness chain verification for Cognitum Seed hardware | 5 | 1 | `vendor/plugins/ruflo/ruflo-iot-cognitum` |
| `ruflo-jujutsu` | Advanced git workflows with diff analysis, risk scoring, change classification (feature/bugfix/refactor/...), and reviewer recommendation... | 2 | 1 | `vendor/plugins/ruflo/ruflo-jujutsu` |
| `ruflo-knowledge-graph` | Knowledge graph construction — entity extraction, relation mapping, and pathfinder graph traversal | 2 | 1 | `vendor/plugins/ruflo/ruflo-knowledge-graph` |
| `ruflo-loop-workers` | Cache-aware /loop workers and CronCreate background automation — wraps 5 hooks_worker-* MCP tools (list/dispatch/status/detect/cancel) an... | 2 | 2 | `vendor/plugins/ruflo/ruflo-loop-workers` |
| `ruflo-market-data` | Market data ingestion — feed normalization, OHLCV vectorization, and HNSW-indexed pattern matching | 2 | 1 | `vendor/plugins/ruflo/ruflo-market-data` |
| `ruflo-metaharness` | MetaHarness integration for ruflo — surfaces score/genome/mint/mcp-scan/threat-model via skills; pairs with @metaharness/router (ADR-148/... | 8 | 1 | `vendor/plugins/ruflo/ruflo-metaharness` |
| `ruflo-migrations` | Schema migration management — generate, validate, dry-run, and rollback database migrations | 2 | 1 | `vendor/plugins/ruflo/ruflo-migrations` |
| `ruflo-neural-trader` | Neural trading via npx neural-trader — self-learning strategies, Rust/NAPI backtesting, 112+ MCP tools, swarm coordination, and portfolio... | 9 | 1 | `vendor/plugins/ruflo/ruflo-neural-trader` |
| `ruflo-observability` | Structured logging, distributed tracing, and metrics — correlate agent swarm activity with application telemetry | 2 | 1 | `vendor/plugins/ruflo/ruflo-observability` |
| `ruflo-plugin-creator` | Scaffold, validate, and publish new Claude Code plugins with the canonical plugin contract — ADR + smoke + Compatibility + namespace coor... | 2 | 1 | `vendor/plugins/ruflo/ruflo-plugin-creator` |
| `ruflo-rag-memory` | RuVector memory with HNSW search, AgentDB, and semantic retrieval | 2 | 2 | `vendor/plugins/ruflo/ruflo-rag-memory` |
| `ruflo-ruvector` | Self-learning vector database via npx ruvector@0.2.25 — HNSW, adaptive LoRA embeddings, code-graph clustering, hooks routing, brain/SONA,... | 4 | 1 | `vendor/plugins/ruflo/ruflo-ruvector` |
| `ruflo-ruvllm` | RuVLLM local inference with chat formatting (Claude/GPT/Gemini/Ollama/Cohere), model configuration, MicroLoRA fine-tuning, and SONA real-... | 2 | 1 | `vendor/plugins/ruflo/ruflo-ruvllm` |
| `ruflo-rvf` | RVF format for portable agent memory, session persistence, and cross-platform transfer | 2 | 1 | `vendor/plugins/ruflo/ruflo-rvf` |
| `ruflo-security-audit` | Security review, dependency scanning, policy gates, and CVE monitoring | 2 | 1 | `vendor/plugins/ruflo/ruflo-security-audit` |
| `ruflo-sparc` | SPARC methodology — Specification, Pseudocode, Architecture, Refinement, Completion phases with gate checks | 3 | 1 | `vendor/plugins/ruflo/ruflo-sparc` |
| `ruflo-swarm` | Agent teams, swarm coordination, Monitor streams, and worktree isolation — wraps 4 swarm_* + 8 agent_* MCP tools (12 total) plus 6 topolo... | 2 | 2 | `vendor/plugins/ruflo/ruflo-swarm` |
| `ruflo-testgen` | Test gap detection, coverage analysis, and automated test generation — drives the testgaps background worker via hooks_worker-dispatch; S... | 2 | 1 | `vendor/plugins/ruflo/ruflo-testgen` |
| `ruflo-workflows` | Workflow automation across two surfaces: the 10 workflow_* MCP tools (create/run/execute/status/list/pause/resume/cancel/delete/template)... | 5 | 8 | `vendor/plugins/ruflo/ruflo-workflows` |
