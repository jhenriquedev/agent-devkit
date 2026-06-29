# Napkin Runbook

## Curation Rules
- Re-prioritize on every read.
- Keep recurring, high-value notes only.
- Max 10 items per category.
- Each item includes date + "Do instead".

## Execution & Validation (Highest Priority)
1. **[2026-06-29] Nao paralelizar build e verify do pacote npm**
   Do instead: rode `npm run package:build && npm run package:verify` sequencialmente; o build remove/recria `tooling/agent-devkit/runtime` e quebra verifies simultaneos.
2. **[2026-06-29] QA destrutivo de instalacao roda em Docker**
   Do instead: use `npm run docker:qa` para instalar tarball em container limpo, validar fluxos CLI criticos, desinstalar e remover `.agent-devkit` sem tocar no host.
3. **[2026-06-29] Docker sem espaco causa falsos erros de apt/GPG**
   Do instead: se `npm run docker:qa` falhar com assinatura invalida no `apt`, verificar `docker system df` e liberar artefatos regeneraveis antes de diagnosticar o CLI.
4. **[2026-06-29] Release gate completo precisa de timeout folgado**
   Do instead: manter timeout do `scripts/release-gate.py` acima da duracao real da suite completa; a suite isolada ja passa de 300s e o gate adiciona overhead.
5. **[2026-06-29] Isolar home do Agent DevKit em testes**
   Do instead: use `AGENT_DEVKIT_HOME=$(mktemp -d)` ou `AI_DEVKIT_CONFIG_HOME=$(mktemp -d)`; `AI_DEVKIT_HOME` nao e lido pelo runtime e pode gravar em `~/.agent-devkit`.
6. **[2026-06-20] Validate agent capabilities through `agent`**
   Do instead: when testing a capability, execute it through `agent run <agent> <capability>` before using lower-level integration CLIs.
7. **[2026-06-21] Excel artifact-tool Node scripts may keep handles alive**
   Do instead: guard `run_node_script()` calls with timeouts and make successful JS runners call `process.exit(0)` after awaited saves.
8. **[2026-06-21] `unittest discover` does not find repo tests**
   Do instead: run `python3 -m unittest $(rg --files -g 'test*.py' -g '!vendor/**')` for the project suite.

## Shell & Command Reliability
1. **[2026-06-20] Azure DevOps SSL can fail through Python urllib**
   Do instead: use the repository's curl-backed transport for Azure DevOps API calls in local/serverless execution.
2. **[2026-06-28] Toolchain install deve ser plan-first e idempotente**
   Do instead: diagnosticar PATH antes de planejar instalacao externa; se a ferramenta ja existe, retornar `already-installed` e nao executar reinstalacao.
3. **[2026-06-28] Saida de instaladores externos pode vazar ambiente**
   Do instead: antes de persistir stdout/stderr de comandos de setup/toolchain, redigir valores de variaveis com KEY/TOKEN/SECRET/PASSWORD/PASS/PAT.
4. **[2026-06-27] Runtime `--source` can conflict with capability domain args**
   Do instead: intercept `--source` only for capabilities that explicitly support Agent DevKit source registry injection; otherwise leave it for the runner domain contract.

## Domain Behavior Guardrails
1. **[2026-06-28] `write_policy` usa vocabulário canônico**
   Do instead: usar apenas `read_only`, `dry_run`, `output_only`, `local_write`, `local_config_write`, `confirm`, `blocked_by_default` ou `delegated`; aliases antigos devem ser aceitos só em runtime e rejeitados como warning pelo validator.
2. **[2026-06-28] Exemplos de roteamento nao sao evidencia por alias**
   Do instead: ao usar `routing.examples`, comparar tokens reais ou frase exata; anchors/intents carregam aliases, exemplos nao devem promover matches genericos como apenas "analise".
3. **[2026-06-28] Agentes devem ser agnosticos de cliente/projeto**
   Do instead: mover nomes de produto, cliente, URLs, paths locais, regras de elegibilidade e campos XML especificos para provider/config/env antes de versionar o agente.
4. **[2026-06-28] Sessao ativa nao deve vazar contexto entre projetos**
   Do instead: ao persistir contexto de conversa, reutilizar automaticamente apenas sessoes do mesmo projeto; para outro projeto, criar nova sessao ou exigir retomada explicita.
5. **[2026-06-28] Roteamento de PR deve usar tokens reais**
   Do instead: detectar `pr`, `prs` ou `pull request` como tokens/expressao, nao substring ampla que captura palavras como `problema`.
6. **[2026-06-28] Tasks com escrita externa devem bloquear por padrao**
   Do instead: permitir `dry-run`, mas bloquear execucao real quando `action.external_writes=true` sem permissao explicita de escrita externa.
7. **[2026-06-20] Azure card descriptions may include sensitive production log data**
   Do instead: retrieve the complete card for validation, but summarize PII-heavy log payloads in user-facing responses unless raw content is explicitly required.
8. **[2026-06-21] N1 restrictive-base uses a scoped SQL Server override**
   Do instead: when the N1 agent checks the restrictive base, prefer `DB_RESTRICTIVE_CONN_STRING` only in the subprocess environment for `sqlserver-data-analyzer`, without changing the global SQL Server analyzer default.

## User Directives
1. **[2026-06-28] Rodar testes focados durante patches**
   Do instead: para melhorias intermediarias, executar apenas testes necessarios para validar o patch e no maximo `scripts/release-gate.py --quick`; reservar suite completa e gate completo apenas para fechamento de fase/versao.
2. **[2026-06-29] Manter `.agent-devkit` como home local**
   Do instead: persistir instalacao, memoria local, configs e artefatos locais em `.agent-devkit` quando o runtime ja usar esse caminho; nao migrar para `.ai-devkit`.
3. **[2026-06-29] Comando canonico permanece `agent`**
   Do instead: manter `agent` como comando default e validar que renomeacao/persona altera o nome publico do agente, nao o executavel canonico.
4. **[2026-06-22] Implement agentic specs individually**
   Do instead: process one `docs/agentic/*_plan.md` spec at a time with agent-specific analysis, tests, implementation, and review; do not use broad multi-agent waves or mechanical generation.
5. **[2026-06-22] Use Agent DevKit agents for work**
   Do instead: route every current and future activity through the relevant Agent DevKit agent/capability before doing direct ad-hoc work.
6. **[2026-06-20] Keep generated docs out of final project versioning**
   Do instead: treat `docs/` as local development/generated artifact space and keep it ignored.
