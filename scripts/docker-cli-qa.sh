#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${AGENT_DEVKIT_DOCKER_IMAGE:-node:20-bookworm}"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required for destructive CLI QA" >&2
  exit 1
fi

cd "$ROOT_DIR"
npm run package:build
npm pack ./tooling/agent-devkit --pack-destination "$TMP_DIR" --silent >/dev/null
TARBALL="$(find "$TMP_DIR" -maxdepth 1 -name 'agent-devkit-*.tgz' -print -quit)"
if [[ -z "$TARBALL" ]]; then
  echo "agent-devkit package tarball was not created" >&2
  exit 1
fi

docker run --rm \
  -v "$TARBALL:/tmp/agent-devkit.tgz:ro" \
  "$IMAGE" \
  bash -lc '
    set -euo pipefail
    export DEBIAN_FRONTEND=noninteractive
    if ! command -v python3 >/dev/null 2>&1; then
      apt-get update >/dev/null
      apt-get install -y --no-install-recommends python3 ca-certificates >/dev/null
      rm -rf /var/lib/apt/lists/*
    fi

    npm install -g /tmp/agent-devkit.tgz >/dev/null

    export HOME=/tmp/agent-devkit-user
    export AGENT_DEVKIT_BACKUP_PASSPHRASE=docker-smoke-passphrase
    mkdir -p "$HOME"
    cd /tmp

    agent --version

    commands="$(agent commands list --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      const agent = (payload.llm || []).find((item) => item.command === "agent");
      if (!agent) throw new Error("commands list did not include agent command");
      if (agent.requires_llm !== false) throw new Error("agent command should advertise local/no-LLM flows");
      if (agent.mode !== "adaptive") throw new Error("agent command should be adaptive");
      if (!(agent.local_without_llm || []).includes("onboarding")) throw new Error("agent command did not advertise onboarding without LLM");
    '"'"' "$commands"

    onboarding="$(agent --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.kind !== "onboarding") throw new Error("agent without args did not enter onboarding");
      if (!payload.specialists || payload.specialists.agents_with_provider_requirements < 1) {
        throw new Error("onboarding did not surface specialist provider readiness");
      }
      if (!(payload.specialists.missing_providers || []).some((item) => item.id === "azure-devops")) {
        throw new Error("onboarding specialist readiness did not surface missing Azure DevOps provider");
      }
    '"'"' "$onboarding"

    renamed="$(agent --rename IanotaDocker --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.agent_name !== "IanotaDocker") throw new Error("agent --rename did not persist identity");
    '"'"' "$renamed"

    identity="$(agent --json qual seu nome?)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (!String(payload.response || "").includes("IanotaDocker")) throw new Error("renamed identity was not used");
    '"'"' "$identity"
    trailing_json_rename="$(agent mude seu nome para ianota10 --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.action !== "rename") throw new Error("trailing --json natural rename did not execute rename");
      if (payload.identity?.name !== "ianota10") throw new Error("trailing --json natural rename persisted wrong name");
      if (String(process.argv[1]).includes("ianota10 --json")) throw new Error("trailing --json leaked into natural prompt text");
    '"'"' "$trailing_json_rename"
    trailing_json_identity="$(agent qual seu nome? --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (!String(payload.response || "").includes("ianota10")) throw new Error("trailing --json identity prompt did not use renamed identity");
    '"'"' "$trailing_json_identity"
    trailing_json_plan="$(agent plan analise o card 9900 --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.kind !== "agentic-plan") throw new Error("trailing --json agentic plan did not return JSON plan");
      if (String(payload.execution_plan?.prompt || "").includes("--json")) throw new Error("trailing --json leaked into agentic plan prompt");
    '"'"' "$trailing_json_plan"
    trailing_json_execute="$(agent execute analise o card 9900 --dry-run --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.kind !== "agentic-plan") throw new Error("trailing --json execute dry-run did not return JSON plan");
      if (payload.command_mode !== "execute") throw new Error("execute dry-run did not keep command_mode");
      if (String(payload.execution_plan?.prompt || "").includes("--dry-run")) throw new Error("trailing --dry-run leaked into execute prompt");
    '"'"' "$trailing_json_execute"
    local_orchestrate="$(agent orchestrate o que voce consegue fazer aqui --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.command_mode !== "orchestrate") throw new Error("orchestrate did not keep command_mode");
      if (payload.execution_plan?.model_plan?.strategy !== "deterministic-local") throw new Error("local orchestrate did not expose deterministic local plan");
      if (payload.agentic_summary?.model_strategy !== "deterministic-local") throw new Error("local orchestrate did not expose agentic summary");
    '"'"' "$local_orchestrate"
    alias_added="$(agent alias add jarvis --json)"
    alias_path="$(node -e '"'"'console.log(JSON.parse(process.argv[1]).path)'"'"' "$alias_added")"
    alias_identity="$("$alias_path" --json qual seu nome?)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (!String(payload.response || "").includes("Jarvis")) throw new Error("alias identity was not used");
    '"'"' "$alias_identity"
    help_prompt="$(agent --json o que voce consegue fazer aqui)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.mode !== "local-capabilities-help") throw new Error("capability help was not answered locally");
      if (payload.requires_llm !== false) throw new Error("capability help should not require LLM");
    '"'"' "$help_prompt"
    task_create="$(agent task create docker-manual --title DockerManual --prompt "o que voce consegue fazer aqui" --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "created") throw new Error("manual task was not created");
    '"'"' "$task_create"
    onboarding_with_task="$(agent --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      const commands = new Set((payload.suggested_actions || []).map((item) => item.command));
      if (!commands.has("agent task run docker-manual --dry-run")) throw new Error("pending task action was not suggested");
    '"'"' "$onboarding_with_task"
    task_run="$(agent task run docker-manual --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "ok") throw new Error("manual task run did not finish ok");
      if (payload.task.run_count !== 1) throw new Error("manual task run count was not updated");
      if (payload.result?.mode !== "local-capabilities-help") throw new Error("manual task did not return prompt result");
      if (!payload.response) throw new Error("manual task response missing");
    '"'"' "$task_run"

    skill_create="$(agent skill create docker-skill --description "Docker QA skill" --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "created") throw new Error("local skill was not created");
    '"'"' "$skill_create"
    skill_catalog="$(agent catalog search docker-skill --type skill --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (!(payload.items || []).some((item) => item.id === "docker-skill")) throw new Error("local skill was not cataloged");
    '"'"' "$skill_catalog"
    script_create="$(agent script create docker-script --command "echo docker-script-ok" --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "created") throw new Error("local script was not created");
    '"'"' "$script_create"
    script_dry_run="$(agent script run docker-script --dry-run --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "planned") throw new Error("local script dry-run did not plan");
    '"'"' "$script_dry_run"
    if agent script run docker-script --json >/tmp/docker-script-blocked.json; then
      echo "local script run without --yes should have failed" >&2
      exit 1
    fi
    node -e '"'"'
      const payload = JSON.parse(require("fs").readFileSync("/tmp/docker-script-blocked.json", "utf8"));
      if (payload.status !== "needs-confirmation") throw new Error("local script run without --yes did not require confirmation");
      if (payload.exit_code !== 2) throw new Error("local script run without --yes did not return exit_code 2");
    '"'"'
    script_run="$(agent script run docker-script --yes --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "ok") throw new Error("local script run failed");
      if (!String(payload.stdout || "").includes("docker-script-ok")) throw new Error("local script stdout missing");
    '"'"' "$script_run"
    agent_create="$(agent agents create docker-agent --description "Docker QA agent" --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "created") throw new Error("local agent was not created");
    '"'"' "$agent_create"
    agent_validate="$(agent agents validate docker-agent --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "passed") throw new Error("local agent validation failed");
    '"'"' "$agent_validate"
    agent_catalog="$(agent catalog search docker-agent --type agent --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (!(payload.items || []).some((item) => item.id === "docker-agent" && item.type === "agent" && item.origin === "local")) {
        throw new Error("local agent was not cataloged as an agent");
      }
    '"'"' "$agent_catalog"

    backup="$(agent memory backup create --title DockerQA --json)"
    backup_id="$(node -e '"'"'console.log(JSON.parse(process.argv[1]).backup.id)'"'"' "$backup")"
    restore_plan="$(agent memory backup restore "$backup_id" --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "planned" || payload.executed !== false) throw new Error("restore did not require confirmation");
    '"'"' "$restore_plan"
    encrypted_backup="$(agent memory backup create --title DockerEncrypted --encrypted --passphrase-env AGENT_DEVKIT_BACKUP_PASSPHRASE --json)"
    encrypted_package="$(node -e '"'"'console.log(JSON.parse(process.argv[1]).backup.package)'"'"' "$encrypted_backup")"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "created") throw new Error("encrypted backup was not created");
      if (payload.backup.encrypted !== true) throw new Error("encrypted backup flag missing");
      if (payload.backup.sensitive_local_copy !== false) throw new Error("encrypted backup kept sensitive local copy");
      if (!payload.backup.package) throw new Error("encrypted backup package path missing");
      const fs = require("fs");
      const path = require("path");
      if (!fs.existsSync(payload.backup.package)) throw new Error("encrypted backup package file does not exist");
      if (fs.existsSync(path.join(payload.backup.path, "memory"))) throw new Error("encrypted backup kept plaintext memory directory");
    '"'"' "$encrypted_backup"
    encrypted_restore="$(agent memory backup restore --file "$encrypted_package" --passphrase-env AGENT_DEVKIT_BACKUP_PASSPHRASE --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "planned" || payload.executed !== false) throw new Error("encrypted restore did not plan safely");
    '"'"' "$encrypted_restore"

    mkdir -p /tmp/kb-project
    cd /tmp/kb-project
    kb="$(agent knowledge-base create --provider github --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.kb.storage.provider !== "knowledge-github") throw new Error("knowledge provider alias was not canonicalized");
      if (payload.stored_values !== false) throw new Error("knowledge tokens should not store raw values");
      if (payload.kb.cache?.local_ttl_minutes !== 1440) throw new Error("knowledge cache local ttl missing");
      if (payload.kb.cache?.remote_ttl_minutes !== 240) throw new Error("knowledge cache remote ttl missing");
    '"'"' "$kb"
    test -f knowledge-base/indexes/semantic.json
    test -f knowledge-base/indexes/chunks.jsonl
    tokens="$(agent knowledge-base tokens --json)"
    node -e '"'"'
      const raw = process.argv[1];
      const payload = JSON.parse(raw);
      if (payload.stored_values !== false) throw new Error("knowledge tokens returned stored values");
      if (raw.includes("token_")) throw new Error("knowledge tokens exposed a raw token-looking value");
    '"'"' "$tokens"
    sensitive_snapshot="$(agent knowledge snapshot create --title DockerSensitive --content "api_key=abc123 user test@example.com cpf 123.456.789-00" --json)"
    node -e '"'"'
      const fs = require("fs");
      const payload = JSON.parse(process.argv[1]);
      const text = fs.readFileSync(payload.path, "utf8");
      if (!text.includes("[REDACTED_SECRET]")) throw new Error("sensitive snapshot did not redact secret");
      if (!text.includes("[REDACTED_PII]")) throw new Error("sensitive snapshot did not redact PII");
      if (text.includes("abc123") || text.includes("test@example.com") || text.includes("123.456.789-00")) {
        throw new Error("sensitive snapshot stored raw sensitive material");
      }
    '"'"' "$sensitive_snapshot"
    sensitive_snapshot_id="$(node -e '"'"'console.log(JSON.parse(process.argv[1]).snapshot_id)'"'"' "$sensitive_snapshot")"
    sensitive_review="$(agent knowledge review "$sensitive_snapshot_id" --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "rejected") throw new Error("sensitive knowledge snapshot review should reject");
    '"'"' "$sensitive_review"
    sensitive_publish="$(agent knowledge publish "$sensitive_snapshot_id" --yes --owner-agent knowledge-owner --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "blocked") throw new Error("sensitive knowledge snapshot publish should block");
    '"'"' "$sensitive_publish"
    snapshot="$(agent knowledge snapshot create --title DockerSnapshot --content "# DockerSnapshot\n\nReusable Docker QA knowledge." --json)"
    snapshot_id="$(node -e '"'"'console.log(JSON.parse(process.argv[1]).snapshot_id)'"'"' "$snapshot")"
    snapshot_list="$(agent knowledge snapshot list --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.count < 1) throw new Error("knowledge snapshot list did not return created snapshot");
    '"'"' "$snapshot_list"
    snapshot_score="$(agent knowledge snapshot score "$snapshot_id" --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (!["submit", "review"].includes(payload.decision)) throw new Error("unexpected knowledge snapshot score decision");
    '"'"' "$snapshot_score"
    snapshot_submit="$(agent knowledge snapshot submit "$snapshot_id" --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "pending-review" || payload.remote_connected !== false) throw new Error("knowledge snapshot submit did not stay local pending review");
    '"'"' "$snapshot_submit"
    planned_publish="$(agent knowledge publish "$snapshot_id" --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "planned") throw new Error("knowledge publish without --yes should be planned");
      if (payload.review?.persisted !== false) throw new Error("knowledge publish plan persisted review state");
    '"'"' "$planned_publish"
    test ! -e "knowledge-base/reviews/approved/$snapshot_id.json"
    test ! -e "knowledge-base/snapshots/accepted/$snapshot_id.md"
    if agent knowledge publish "$snapshot_id" --yes --json >/tmp/knowledge-publish-without-owner.json; then
      echo "knowledge publish without owner should have failed" >&2
      exit 1
    fi
    node -e '"'"'
      const payload = JSON.parse(require("fs").readFileSync("/tmp/knowledge-publish-without-owner.json", "utf8"));
      if (payload.status !== "blocked" || payload.reason !== "owner_agent_required") throw new Error("knowledge publish without owner did not block correctly");
    '"'"'
    published="$(agent knowledge publish "$snapshot_id" --yes --owner-agent knowledge-owner --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "published") throw new Error("knowledge publish --yes did not publish");
      if (payload.review?.persisted !== true) throw new Error("knowledge publish --yes did not persist review");
    '"'"' "$published"
    node -e '"'"'
      const fs = require("fs");
      const path = require("path");
      const auditDir = path.join(process.cwd(), "knowledge-base", "audit");
      const events = fs.readdirSync(auditDir)
        .filter((item) => item.endsWith(".json"))
        .map((item) => JSON.parse(fs.readFileSync(path.join(auditDir, item), "utf8")));
      const snapshotEvents = events.filter((item) => item.snapshot_id === process.argv[1]);
      const names = new Set(snapshotEvents.map((item) => item.event));
      if (!names.has("review")) throw new Error("knowledge audit missing review event");
      if (!names.has("publish")) throw new Error("knowledge audit missing publish event");
      if (!snapshotEvents.every((item) => item.content_sha256)) {
        throw new Error("knowledge audit missing snapshot id or content hash");
      }
    '"'"' "$snapshot_id"
    knowledge_search="$(agent knowledge search docker --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.count < 1) throw new Error("published knowledge was not searchable");
    '"'"' "$knowledge_search"
    conversational_snapshot="$(agent knowledge snapshot create --title DockerConversational --content "ok obrigado" --json)"
    conversational_snapshot_id="$(node -e '"'"'console.log(JSON.parse(process.argv[1]).snapshot_id)'"'"' "$conversational_snapshot")"
    conversational_score="$(agent knowledge snapshot score "$conversational_snapshot_id" --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      const reasons = new Set((payload.findings || []).map((item) => item.reason));
      if (payload.decision !== "blocked") throw new Error("conversational knowledge snapshot should be blocked");
      if (!reasons.has("purely-conversational-content")) throw new Error("conversational knowledge snapshot missing policy finding");
    '"'"' "$conversational_score"
    personal_snapshot="$(agent knowledge snapshot create --title DockerPersonalMemory --content "Meu nome e Ianota e prefiro respostas curtas." --json)"
    personal_snapshot_id="$(node -e '"'"'console.log(JSON.parse(process.argv[1]).snapshot_id)'"'"' "$personal_snapshot")"
    personal_score="$(agent knowledge snapshot score "$personal_snapshot_id" --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      const reasons = new Set((payload.findings || []).map((item) => item.reason));
      if (payload.decision !== "blocked") throw new Error("personal-memory knowledge snapshot should be blocked");
      if (!reasons.has("personal-memory-content")) throw new Error("personal-memory knowledge snapshot missing policy finding");
    '"'"' "$personal_score"
    review_list="$(agent knowledge review list --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.kind !== "knowledge-reviews") throw new Error("knowledge review list failed");
    '"'"' "$review_list"
    curate="$(agent knowledge curate --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.kind !== "knowledge-curation") throw new Error("knowledge curate failed");
    '"'"' "$curate"
    sync="$(agent knowledge sync --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "planned") throw new Error("remote knowledge sync should be planned only");
    '"'"' "$sync"

    mcp="$(agent mcp tools --json)"
    node -e '"'"'
      const names = new Set(JSON.parse(process.argv[1]).tools.map((tool) => tool.name));
      for (const name of [
        "agent_devkit_onboarding_status",
        "agent_devkit_memory_backup_create",
        "agent_devkit_knowledge_base_create",
        "agent_devkit_shared_memory_create",
      ]) {
        if (!names.has(name)) throw new Error(`missing MCP tool ${name}`);
      }
    '"'"' "$mcp"

    shared="$(agent shared-memory create --title DockerQA --json)"
    shared_id="$(node -e '"'"'console.log(JSON.parse(process.argv[1]).memory.id)'"'"' "$shared")"
    shared_key="$(node -e '"'"'console.log(JSON.parse(process.argv[1]).contributor_access.key)'"'"' "$shared")"
    shared_owner_key="$(node -e '"'"'console.log(JSON.parse(process.argv[1]).owner_access.key)'"'"' "$shared")"
    if [[ -z "$shared_owner_key" || "$shared_owner_key" == "undefined" ]]; then
      echo "shared-memory create did not return owner access" >&2
      exit 1
    fi
    if [[ "$shared" == *owner_key* ]]; then
      echo "shared-memory create leaked internal owner_key field" >&2
      exit 1
    fi
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "created" || !payload.contributor_access?.key) throw new Error("shared memory was not created");
      if (JSON.stringify(payload).includes("owner_key")) throw new Error("owner key leaked in shared memory payload");
    '"'"' "$shared"
    sensitive_shared="$(agent shared-memory submit "$shared_id" --title DockerSensitiveShared --content "api_key=abc123 user test@example.com cpf 123.456.789-00" --key "$shared_key" --json)"
    node -e '"'"'
      const fs = require("fs");
      const payload = JSON.parse(process.argv[1]);
      const text = fs.readFileSync(payload.path, "utf8");
      if (!text.includes("[REDACTED_SECRET]")) throw new Error("sensitive shared memory did not redact secret");
      if (!text.includes("[REDACTED_PII]")) throw new Error("sensitive shared memory did not redact PII");
      if (text.includes("abc123") || text.includes("test@example.com") || text.includes("123.456.789-00")) {
        throw new Error("sensitive shared memory stored raw sensitive material");
      }
    '"'"' "$sensitive_shared"
    sensitive_shared_id="$(node -e '"'"'console.log(JSON.parse(process.argv[1]).submission_id)'"'"' "$sensitive_shared")"
    sensitive_shared_review="$(agent shared-memory review "$shared_id" "$sensitive_shared_id" --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "rejected") throw new Error("sensitive shared memory review should reject");
    '"'"' "$sensitive_shared_review"
    sensitive_shared_publish="$(agent shared-memory publish "$shared_id" "$sensitive_shared_id" --yes --owner-key "$shared_owner_key" --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "blocked") throw new Error("sensitive shared memory publish should block");
    '"'"' "$sensitive_shared_publish"
    shared_submit="$(agent shared-memory submit "$shared_id" --title DockerRunbook --content "Reusable Docker shared memory knowledge." --key "$shared_key" --json)"
    shared_submission_id="$(node -e '"'"'console.log(JSON.parse(process.argv[1]).submission_id)'"'"' "$shared_submit")"
    shared_plan="$(agent shared-memory publish "$shared_id" "$shared_submission_id" --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "planned") throw new Error("shared-memory publish without --yes should be planned");
      if (payload.review?.persisted !== false) throw new Error("shared-memory publish plan persisted review state");
    '"'"' "$shared_plan"
    test ! -e "$HOME/.agent-devkit/shared-memory/$shared_id/reviews/$shared_submission_id.json"
    test ! -e "$HOME/.agent-devkit/shared-memory/$shared_id/accepted/$shared_submission_id.md"
    if agent shared-memory publish "$shared_id" "$shared_submission_id" --yes --json >/tmp/shared-publish-without-owner.json; then
      echo "shared-memory publish --yes without owner key should have failed" >&2
      exit 1
    fi
    node -e '"'"'
      const payload = JSON.parse(require("fs").readFileSync("/tmp/shared-publish-without-owner.json", "utf8"));
      if (payload.status !== "blocked") throw new Error("shared-memory publish without owner key should block");
      if (payload.reason !== "owner_key_required") throw new Error("shared-memory publish without owner key reported wrong reason");
      if (payload.exit_code !== 2) throw new Error("shared-memory publish without owner key did not return exit_code 2");
    '"'"'
    test ! -e "$HOME/.agent-devkit/shared-memory/$shared_id/reviews/$shared_submission_id.json"
    test ! -e "$HOME/.agent-devkit/shared-memory/$shared_id/accepted/$shared_submission_id.md"
    shared_publish="$(agent shared-memory publish "$shared_id" "$shared_submission_id" --yes --owner-key "$shared_owner_key" --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "published") throw new Error("shared-memory publish --yes did not publish");
      if (payload.review?.persisted !== true) throw new Error("shared-memory publish --yes did not persist review");
    '"'"' "$shared_publish"
    shared_read="$(agent shared-memory read "$shared_id" "$shared_submission_id" --key "$shared_key" --json)"
    node -e '"'"'
      const payload = JSON.parse(process.argv[1]);
      if (payload.status !== "ok") throw new Error("shared-memory read failed");
      if (payload.entry_id !== process.argv[2]) throw new Error("shared-memory read returned wrong entry");
      if (!String(payload.content || "").includes("Reusable Docker shared memory knowledge.")) throw new Error("shared-memory read content missing");
    '"'"' "$shared_read" "$shared_submission_id"

    test -d "$HOME/.agent-devkit"
    npm uninstall -g agent-devkit >/dev/null
    rm -rf "$HOME/.agent-devkit"
    test ! -e "$HOME/.agent-devkit"
  '

echo "Docker destructive CLI QA passed."
