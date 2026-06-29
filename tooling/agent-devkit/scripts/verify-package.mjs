#!/usr/bin/env node

import { mkdtemp, rm, readdir, readFile, stat } from "node:fs/promises";
import { spawn } from "node:child_process";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const packageRoot = path.resolve(__dirname, "..");
const runtimeRoot = path.join(packageRoot, "runtime");
const agentBin = path.join(packageRoot, "bin", "agent.mjs");
const forbiddenNames = new Set([".git", "docs", "node_modules", "__pycache__", ".pytest_cache"]);

function run(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: packageRoot,
      shell: false,
      text: true,
      stdio: ["ignore", "pipe", "pipe"],
      ...options,
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) {
        resolve({ stdout, stderr });
        return;
      }
      reject(new Error(`${command} ${args.join(" ")} failed with ${code}\n${stdout}\n${stderr}`));
    });
  });
}

function runMcpSmoke(env) {
  return new Promise((resolve, reject) => {
    const child = spawn("node", [agentBin, "mcp", "serve"], {
      cwd: packageRoot,
      shell: false,
      text: true,
      stdio: ["pipe", "pipe", "pipe"],
      env,
    });
    const pending = new Map();
    let stdoutBuffer = "";
    let stderr = "";
    let settled = false;
    const timeout = setTimeout(() => {
      fail(new Error(`Packaged MCP stdio smoke timed out\n${stderr}`));
    }, 15000);

    function fail(error) {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      child.kill();
      reject(error);
    }

    function finish() {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      child.kill();
      resolve();
    }

    function send(payload) {
      child.stdin.write(`${JSON.stringify(payload)}\n`);
    }

    function rpc(payload) {
      return new Promise((resolveRpc, rejectRpc) => {
        pending.set(payload.id, { resolve: resolveRpc, reject: rejectRpc });
        send(payload);
      });
    }

    child.stdout.on("data", (chunk) => {
      stdoutBuffer += chunk;
      let newline = stdoutBuffer.indexOf("\n");
      while (newline >= 0) {
        const line = stdoutBuffer.slice(0, newline).trim();
        stdoutBuffer = stdoutBuffer.slice(newline + 1);
        newline = stdoutBuffer.indexOf("\n");
        if (!line) continue;
        let message;
        try {
          message = JSON.parse(line);
        } catch (error) {
          fail(new Error(`Packaged MCP stdio returned invalid JSON: ${line}`));
          return;
        }
        const waiter = pending.get(message.id);
        if (waiter) {
          pending.delete(message.id);
          waiter.resolve(message);
        }
      }
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.on("error", fail);
    child.on("close", (code) => {
      if (!settled && code !== 0) {
        fail(new Error(`Packaged MCP stdio exited with ${code}\n${stderr}`));
      }
    });

    (async () => {
      try {
        const initialize = await rpc({
          jsonrpc: "2.0",
          id: 1,
          method: "initialize",
          params: {
            protocolVersion: "2025-11-25",
            capabilities: {},
            clientInfo: { name: "package-smoke", version: "0" },
          },
        });
        if (initialize.result?.serverInfo?.name !== "agent-devkit") {
          throw new Error(`Packaged MCP stdio did not initialize correctly: ${JSON.stringify(initialize)}`);
        }
        send({ jsonrpc: "2.0", method: "notifications/initialized" });
        const tools = await rpc({ jsonrpc: "2.0", id: 2, method: "tools/list" });
        if (!tools.result?.tools?.some((tool) => tool.name === "agent_devkit_onboarding_status")) {
          throw new Error(`Packaged MCP stdio did not list onboarding tool: ${JSON.stringify(tools)}`);
        }
        const call = await rpc({
          jsonrpc: "2.0",
          id: 3,
          method: "tools/call",
          params: { name: "agent_devkit_onboarding_status", arguments: {} },
        });
        if (call.result?.isError || call.result?.structuredContent?.kind !== "onboarding") {
          throw new Error(`Packaged MCP stdio onboarding call failed: ${JSON.stringify(call)}`);
        }
        finish();
      } catch (error) {
        fail(error);
      }
    })();
  });
}

async function assertExists(relativePath) {
  await stat(path.join(runtimeRoot, relativePath));
}

async function pathExists(targetPath) {
  try {
    await stat(targetPath);
    return true;
  } catch (error) {
    if (error && error.code === "ENOENT") return false;
    throw error;
  }
}

async function assertNoJsonFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      await assertNoJsonFiles(fullPath);
      continue;
    }
    if (entry.name.endsWith(".json")) {
      throw new Error(`Unexpected JSON file found: ${fullPath}`);
    }
  }
}

async function assertNoForbiddenFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(directory, entry.name);
    if (forbiddenNames.has(entry.name)) {
      throw new Error(`Forbidden path found in npm runtime: ${fullPath}`);
    }
    if (entry.name === ".env" || (entry.name.startsWith(".env.") && entry.name !== ".env.example")) {
      throw new Error(`Forbidden env file found in npm runtime: ${fullPath}`);
    }
    if (entry.name.endsWith(".pyc") || entry.name.endsWith(".pyo")) {
      throw new Error(`Forbidden Python cache found in npm runtime: ${fullPath}`);
    }
    if (entry.isDirectory()) {
      await assertNoForbiddenFiles(fullPath);
    }
  }
}

async function main() {
  const packageJson = JSON.parse(await readFile(path.join(packageRoot, "package.json"), "utf8"));
  const expectedVersion = `agent ${packageJson.version}`;

  await assertExists("agent");
  await assertExists("cli/aikit/main.py");
  await assertExists("cli/aikit/app_home.py");
  await assertExists("cli/aikit/control_router.py");
  await assertExists("cli/aikit/execution_reviewer.py");
  await assertExists("cli/aikit/catalog.py");
  await assertExists("cli/aikit/router_explain.py");
  await assertExists("cli/aikit/roadmap_cli.py");
  await assertExists("cli/aikit/eval.py");
  await assertExists("cli/aikit/secrets.py");
  await assertExists("cli/aikit/extensions.py");
  await assertExists("cli/aikit/workflows.py");
  await assertExists("cli/aikit/contribution.py");
  await assertExists("cli/aikit/local_llm_operator.py");
  await assertExists("cli/aikit/orchestrator.py");
  await assertExists("cli/aikit/wizard_state.py");
  await assertExists("agents");
  await assertExists("agents/task-orchestrator/agent.yaml");
    await assertExists("agents/provider-configurator/agent.yaml");
    await assertExists("agents/local-llm-operator/agent.yaml");
    await assertExists("agents/execution-reviewer/agent.yaml");
    await assertExists("agents/knowledge-owner/agent.yaml");
    await assertExists("agents/memory-sync-manager/agent.yaml");
    await assertExists("requirements.txt");
    await assertExists("providers");
    await assertExists("providers/knowledge-local.yaml");
    await assertExists("providers/knowledge-github.yaml");
    await assertExists("providers/knowledge-vector.yaml");
    await assertExists("plugins");
    await assertNoForbiddenFiles(runtimeRoot);

  const configHome = await mkdtemp(path.join(os.tmpdir(), "agent-devkit-package-"));
  const fakeHome = await mkdtemp(path.join(os.tmpdir(), "agent-devkit-home-"));
  try {
    const env = {
      ...process.env,
      AIKIT_CONFIG_HOME: configHome,
      AI_DEVKIT_CONFIG_HOME: configHome,
      AGENT_DEVKIT_BACKUP_PASSPHRASE: "package-smoke-passphrase",
      PACKAGE_A_TOKEN: "package-a-secret",
      PACKAGE_Z_TOKEN: "package-z-secret",
      PYTHONDONTWRITEBYTECODE: "1",
    };
    const version = await run("node", [agentBin, "--version"], { env });
    if (version.stdout.trim() !== expectedVersion) {
      throw new Error(`Unexpected version output: ${version.stdout}`);
    }
    const commands = await run("node", [agentBin, "commands", "list", "--json"], { env });
    const payload = JSON.parse(commands.stdout);
    const deterministic = new Set(payload.deterministic.map((item) => item.command));
    for (const command of [
      "agents",
      "capabilities",
      "run",
      "doctor",
      "install",
      "source",
      "memory",
      "roadmap",
      "catalog",
      "route",
      "eval",
      "secrets",
      "local",
      "workflow",
      "contribution",
      "team",
      "knowledge",
      "knowledge-base",
      "shared-memory",
    ]) {
      if (!deterministic.has(command)) {
        throw new Error(`Missing deterministic command in package smoke: ${command}`);
      }
    }
    const agentCommandMode = payload.llm?.find((item) => item.command === "agent");
    if (
      !agentCommandMode ||
      agentCommandMode.requires_llm !== false ||
      agentCommandMode.mode !== "adaptive" ||
      !agentCommandMode.local_without_llm?.includes("onboarding")
    ) {
      throw new Error(`Packaged runtime did not advertise agent as adaptive/no-LLM-capable: ${commands.stdout}`);
    }
    await run("node", [agentBin, "secret", "set", "zeta", "token", "--env", "PACKAGE_Z_TOKEN", "--json"], { env });
    const packageSecret = await run("node", [agentBin, "secret", "set", "alpha", "token", "--env", "PACKAGE_A_TOKEN", "--json"], { env });
    const packageSecretPayload = JSON.parse(packageSecret.stdout);
    if (
      packageSecretPayload.reference?.provider !== "alpha" ||
      packageSecretPayload.reference?.env !== "PACKAGE_A_TOKEN" ||
      packageSecret.stdout.includes("package-a-secret")
    ) {
      throw new Error(`Packaged runtime did not return the newly saved secret reference safely: ${packageSecret.stdout}`);
    }
    const packageSecrets = await run("node", [agentBin, "secret", "list", "--json"], { env });
    const packageSecretProviders = JSON.parse(packageSecrets.stdout).references?.map((item) => item.provider).join(",");
    if (packageSecretProviders !== "alpha,zeta" || packageSecrets.stdout.includes("package-z-secret")) {
      throw new Error(`Packaged runtime did not list secret refs safely and deterministically: ${packageSecrets.stdout}`);
    }
    const workflowRunPlan = await run("node", [agentBin, "workflow", "run", "daily-pr-review", "--dry-run", "--json"], { env });
    const workflowRunPlanPayload = JSON.parse(workflowRunPlan.stdout);
    if (
      workflowRunPlanPayload.kind !== "workflow-run" ||
      workflowRunPlanPayload.status !== "planned" ||
      workflowRunPlanPayload.plan?.task?.id !== "daily-pr-review"
    ) {
      throw new Error(`Packaged runtime did not plan declarative workflow run: ${workflowRunPlan.stdout}`);
    }
    const onboarding = await run("node", [agentBin, "--json"], { env });
    const onboardingPayload = JSON.parse(onboarding.stdout);
    if (onboardingPayload.kind !== "onboarding") {
      throw new Error(`Packaged runtime did not start onboarding without args: ${onboarding.stdout}`);
    }
    const rename = await run("node", [agentBin, "--rename", "Ianota", "--json"], { env });
    const renamePayload = JSON.parse(rename.stdout);
    if (renamePayload.agent_name !== "Ianota") {
      throw new Error(`Packaged runtime did not support agent --rename: ${rename.stdout}`);
    }
    const identity = await run("node", [agentBin, "--json", "qual", "seu", "nome?"], { env });
    if (!String(JSON.parse(identity.stdout).response || "").includes("Ianota")) {
      throw new Error(`Packaged runtime did not persist renamed identity: ${identity.stdout}`);
    }
    const trailingJsonRename = await run("node", [agentBin, "mude", "seu", "nome", "para", "ianota10", "--json"], { env });
    const trailingJsonRenamePayload = JSON.parse(trailingJsonRename.stdout);
    if (
      trailingJsonRenamePayload.action !== "rename" ||
      trailingJsonRenamePayload.identity?.name !== "ianota10" ||
      String(trailingJsonRename.stdout).includes("ianota10 --json")
    ) {
      throw new Error(`Packaged runtime treated trailing --json as prompt text: ${trailingJsonRename.stdout}`);
    }
    const trailingJsonIdentity = await run("node", [agentBin, "qual", "seu", "nome?", "--json"], { env });
    if (!String(JSON.parse(trailingJsonIdentity.stdout).response || "").includes("ianota10")) {
      throw new Error(`Packaged runtime did not support trailing --json on natural prompt: ${trailingJsonIdentity.stdout}`);
    }
    const trailingJsonPlan = await run("node", [agentBin, "plan", "analise", "o", "card", "9900", "--json"], { env });
    const trailingJsonPlanPayload = JSON.parse(trailingJsonPlan.stdout);
    if (
      trailingJsonPlanPayload.kind !== "agentic-plan" ||
      trailingJsonPlanPayload.execution_plan?.prompt?.includes("--json")
    ) {
      throw new Error(`Packaged runtime treated trailing --json as agentic prompt text: ${trailingJsonPlan.stdout}`);
    }
    const aliasAdd = await run("node", [agentBin, "alias", "add", "jarvis", "--json"], { env });
    const aliasPayload = JSON.parse(aliasAdd.stdout);
    await stat(aliasPayload.path);
    const aliasIdentity = await run(aliasPayload.path, ["--json", "qual", "seu", "nome?"], { env });
    if (!String(JSON.parse(aliasIdentity.stdout).response || "").includes("Jarvis")) {
      throw new Error(`Packaged runtime alias did not preserve invoked name: ${aliasIdentity.stdout}`);
    }
    const helpPrompt = await run("node", [agentBin, "--json", "o", "que", "voce", "consegue", "fazer", "aqui"], { env });
    const helpPayload = JSON.parse(helpPrompt.stdout);
    if (helpPayload.mode !== "local-capabilities-help" || helpPayload.requires_llm !== false) {
      throw new Error(`Packaged runtime did not answer capability help locally: ${helpPrompt.stdout}`);
    }
    const taskCreate = await run(
      "node",
      [
        agentBin,
        "task",
        "create",
        "package-manual",
        "--title",
        "Package Manual",
        "--prompt",
        "o que voce consegue fazer aqui",
        "--json",
      ],
      { env },
    );
    if (JSON.parse(taskCreate.stdout).status !== "created") {
      throw new Error(`Packaged runtime did not create a manual task: ${taskCreate.stdout}`);
    }
    const onboardingWithTask = await run("node", [agentBin, "--json"], { env });
    const onboardingWithTaskPayload = JSON.parse(onboardingWithTask.stdout);
    const suggestedCommands = new Set((onboardingWithTaskPayload.suggested_actions || []).map((item) => item.command));
    if (!suggestedCommands.has("agent task run package-manual --dry-run")) {
      throw new Error(`Packaged runtime did not surface pending task action: ${onboardingWithTask.stdout}`);
    }
    const taskRun = await run("node", [agentBin, "task", "run", "package-manual", "--json"], { env });
    const taskRunPayload = JSON.parse(taskRun.stdout);
    if (
      taskRunPayload.status !== "ok" ||
      taskRunPayload.task?.run_count !== 1 ||
      taskRunPayload.result?.mode !== "local-capabilities-help" ||
      !taskRunPayload.response
    ) {
      throw new Error(`Packaged runtime task run did not return prompt result: ${taskRun.stdout}`);
    }
    const skillCreate = await run("node", [agentBin, "skill", "create", "package-skill", "--description", "Package QA skill", "--json"], {
      env,
    });
    if (JSON.parse(skillCreate.stdout).status !== "created") {
      throw new Error(`Packaged runtime did not create a local skill: ${skillCreate.stdout}`);
    }
    const skillCatalog = await run("node", [agentBin, "catalog", "search", "package-skill", "--type", "skill", "--json"], { env });
    if (!JSON.parse(skillCatalog.stdout).items?.some((item) => item.id === "package-skill")) {
      throw new Error(`Packaged runtime did not index local skill in catalog: ${skillCatalog.stdout}`);
    }
    const scriptCreate = await run(
      "node",
      [agentBin, "script", "create", "package-script", "--command", "echo package-script-ok", "--json"],
      { env },
    );
    if (JSON.parse(scriptCreate.stdout).status !== "created") {
      throw new Error(`Packaged runtime did not create a local script: ${scriptCreate.stdout}`);
    }
    const scriptDryRun = await run("node", [agentBin, "script", "run", "package-script", "--dry-run", "--json"], { env });
    if (JSON.parse(scriptDryRun.stdout).status !== "planned") {
      throw new Error(`Packaged runtime did not dry-run a local script: ${scriptDryRun.stdout}`);
    }
    const scriptBlocked = await run("node", [agentBin, "script", "run", "package-script", "--json"], { env }).catch((error) => error);
    if (
      !String(scriptBlocked.message || "").includes("needs-confirmation") ||
      !String(scriptBlocked.message || "").includes("exit_code")
    ) {
      throw new Error(`Packaged runtime did not require confirmation for local script run: ${scriptBlocked.message || scriptBlocked.stdout}`);
    }
    const scriptRun = await run("node", [agentBin, "script", "run", "package-script", "--yes", "--json"], { env });
    const scriptRunPayload = JSON.parse(scriptRun.stdout);
    if (scriptRunPayload.status !== "ok" || !String(scriptRunPayload.stdout || "").includes("package-script-ok")) {
      throw new Error(`Packaged runtime did not run a confirmed local script: ${scriptRun.stdout}`);
    }
    const agentCreate = await run("node", [agentBin, "agents", "create", "package-agent", "--description", "Package QA agent", "--json"], {
      env,
    });
    if (JSON.parse(agentCreate.stdout).status !== "created") {
      throw new Error(`Packaged runtime did not create a local agent: ${agentCreate.stdout}`);
    }
    const agentValidate = await run("node", [agentBin, "agents", "validate", "package-agent", "--json"], { env });
    if (JSON.parse(agentValidate.stdout).status !== "passed") {
      throw new Error(`Packaged runtime did not validate a local agent: ${agentValidate.stdout}`);
    }
    const agentCatalog = await run("node", [agentBin, "catalog", "search", "package-agent", "--type", "agent", "--json"], { env });
    const agentCatalogPayload = JSON.parse(agentCatalog.stdout);
    if (!agentCatalogPayload.items?.some((item) => item.id === "package-agent" && item.type === "agent" && item.origin === "local")) {
      throw new Error(`Packaged runtime did not index local agent as an agent catalog item: ${agentCatalog.stdout}`);
    }
    const mcpTools = await run("node", [agentBin, "mcp", "tools", "--json"], { env });
    const mcpPayload = JSON.parse(mcpTools.stdout);
    const mcpNames = new Set(mcpPayload.tools.map((tool) => tool.name));
    for (const tool of [
      "agent_devkit_onboarding_status",
      "agent_devkit_memory_show",
      "agent_devkit_personality_show",
      "agent_devkit_task_list",
      "agent_devkit_notifications_doctor",
      "agent_devkit_team_status",
      "agent_devkit_team_init",
      "agent_devkit_team_profile_list",
      "agent_devkit_knowledge_doctor",
      "agent_devkit_knowledge_init",
      "agent_devkit_knowledge_index",
      "agent_devkit_knowledge_curate",
      "agent_devkit_knowledge_sync",
      "agent_devkit_knowledge_snapshot_create",
      "agent_devkit_knowledge_snapshot_score",
      "agent_devkit_knowledge_publish",
      "agent_devkit_knowledge_base_create",
      "agent_devkit_knowledge_base_tokens",
      "agent_devkit_memory_backup_create",
      "agent_devkit_memory_backup_restore",
      "agent_devkit_shared_memory_create",
      "agent_devkit_shared_memory_read",
      "agent_devkit_shared_memory_publish",
      "agent_devkit_local_skill_create",
      "agent_devkit_local_script_run_dry_run",
      "agent_devkit_local_agent_validate",
    ]) {
      if (!mcpNames.has(tool)) {
        throw new Error(`Missing MCP tool in package smoke: ${tool}`);
      }
    }
    await runMcpSmoke(env);
    const shared = await run("node", [agentBin, "shared-memory", "create", "--title", "Package Smoke", "--json"], { env });
    const sharedPayload = JSON.parse(shared.stdout);
    if (sharedPayload.status !== "created" || !sharedPayload.contributor_access?.key) {
      throw new Error(`Packaged runtime did not create shared memory: ${shared.stdout}`);
    }
    if (shared.stdout.includes("owner_key")) {
      throw new Error(`Packaged runtime leaked owner key metadata in shared memory payload: ${shared.stdout}`);
    }
    const sharedId = sharedPayload.memory?.id;
    const sharedKey = sharedPayload.contributor_access?.key;
    const sharedOwnerKey = sharedPayload.owner_access?.key;
    if (!sharedOwnerKey) {
      throw new Error(`Packaged runtime did not return owner access for shared memory creator: ${shared.stdout}`);
    }
    const sensitiveShared = await run(
      "node",
      [
        agentBin,
        "shared-memory",
        "submit",
        sharedId,
        "--title",
        "Package Sensitive Shared",
        "--content",
        "api_key=abc123 user test@example.com cpf 123.456.789-00",
        "--key",
        sharedKey,
        "--json",
      ],
      { env },
    );
    const sensitiveSharedPayload = JSON.parse(sensitiveShared.stdout);
    const sensitiveSharedText = await readFile(sensitiveSharedPayload.path, "utf8");
    if (
      !sensitiveSharedText.includes("[REDACTED_SECRET]") ||
      !sensitiveSharedText.includes("[REDACTED_PII]") ||
      sensitiveSharedText.includes("abc123") ||
      sensitiveSharedText.includes("test@example.com") ||
      sensitiveSharedText.includes("123.456.789-00")
    ) {
      throw new Error(`Packaged runtime stored sensitive shared-memory material: ${sensitiveSharedText}`);
    }
    const sensitiveSharedReview = await run(
      "node",
      [
        agentBin,
        "shared-memory",
        "review",
        sharedId,
        sensitiveSharedPayload.submission_id,
        "--json",
      ],
      { env },
    );
    if (JSON.parse(sensitiveSharedReview.stdout).status !== "rejected") {
      throw new Error(`Packaged runtime approved sensitive shared-memory submission: ${sensitiveSharedReview.stdout}`);
    }
    const sensitiveSharedPublish = await run(
      "node",
      [
        agentBin,
        "shared-memory",
        "publish",
        sharedId,
        sensitiveSharedPayload.submission_id,
        "--yes",
        "--owner-key",
        sharedOwnerKey,
        "--json",
      ],
      { env },
    );
    if (JSON.parse(sensitiveSharedPublish.stdout).status !== "blocked") {
      throw new Error(`Packaged runtime published sensitive shared-memory submission: ${sensitiveSharedPublish.stdout}`);
    }
    const sharedSubmit = await run(
      "node",
      [
        agentBin,
        "shared-memory",
        "submit",
        sharedId,
        "--title",
        "Package Runbook",
        "--content",
        "Reusable package shared memory knowledge.",
        "--key",
        sharedKey,
        "--json",
      ],
      { env },
    );
    const sharedSubmissionId = JSON.parse(sharedSubmit.stdout).submission_id;
    const sharedPlan = await run("node", [agentBin, "shared-memory", "publish", sharedId, sharedSubmissionId, "--json"], { env });
    const sharedPlanPayload = JSON.parse(sharedPlan.stdout);
    if (sharedPlanPayload.status !== "planned" || sharedPlanPayload.review?.persisted !== false) {
      throw new Error(`Packaged runtime shared-memory publish plan mutated review state: ${sharedPlan.stdout}`);
    }
    const sharedRoot = path.join(configHome, "shared-memory", sharedId);
    if (await pathExists(path.join(sharedRoot, "reviews", `${sharedSubmissionId}.json`))) {
      throw new Error("Packaged runtime shared-memory publish plan persisted review for clean submission without --yes");
    }
    if (await pathExists(path.join(sharedRoot, "accepted", `${sharedSubmissionId}.md`))) {
      throw new Error("Packaged runtime shared-memory publish plan accepted a submission without --yes");
    }
    const sharedMissingOwner = await run("node", [agentBin, "shared-memory", "publish", sharedId, sharedSubmissionId, "--yes", "--json"], { env }).catch((error) => error);
    if (
      !String(sharedMissingOwner.message || "").includes("owner_key_required") ||
      !String(sharedMissingOwner.message || "").includes("exit_code")
    ) {
      throw new Error(`Packaged runtime did not require owner key for shared-memory publish: ${sharedMissingOwner.message || sharedMissingOwner.stdout}`);
    }
    const sharedPublish = await run(
      "node",
      [agentBin, "shared-memory", "publish", sharedId, sharedSubmissionId, "--yes", "--owner-key", sharedOwnerKey, "--json"],
      { env },
    );
    const sharedPublishPayload = JSON.parse(sharedPublish.stdout);
    if (sharedPublishPayload.status !== "published" || sharedPublishPayload.review?.persisted !== true) {
      throw new Error(`Packaged runtime did not publish confirmed shared-memory submission: ${sharedPublish.stdout}`);
    }
    const sharedRead = await run(
      "node",
      [agentBin, "shared-memory", "read", sharedId, sharedSubmissionId, "--key", sharedKey, "--json"],
      { env },
    );
    const sharedReadPayload = JSON.parse(sharedRead.stdout);
    if (
      sharedReadPayload.status !== "ok" ||
      sharedReadPayload.entry_id !== sharedSubmissionId ||
      !String(sharedReadPayload.content || "").includes("Reusable package shared memory knowledge.")
    ) {
      throw new Error(`Packaged runtime did not read accepted shared-memory entry: ${sharedRead.stdout}`);
    }
    const backup = await run("node", [agentBin, "memory", "backup", "create", "--title", "Package Smoke", "--json"], { env });
    const backupPayload = JSON.parse(backup.stdout);
    if (backupPayload.status !== "created" || backupPayload.backup?.remote_upload !== false) {
      throw new Error(`Packaged runtime did not create a local memory backup: ${backup.stdout}`);
    }
    const restorePlan = await run("node", [agentBin, "memory", "backup", "restore", backupPayload.backup.id, "--json"], { env });
    const restorePlanPayload = JSON.parse(restorePlan.stdout);
    if (restorePlanPayload.status !== "planned" || restorePlanPayload.executed !== false) {
      throw new Error(`Packaged runtime did not require confirmation for memory restore: ${restorePlan.stdout}`);
    }
    const encryptedBackup = await run(
      "node",
      [
        agentBin,
        "memory",
        "backup",
        "create",
        "--title",
        "Package Encrypted",
        "--encrypted",
        "--passphrase-env",
        "AGENT_DEVKIT_BACKUP_PASSPHRASE",
        "--json",
      ],
      { env },
    );
    const encryptedPayload = JSON.parse(encryptedBackup.stdout);
    if (
      encryptedPayload.status !== "created" ||
      encryptedPayload.backup?.encrypted !== true ||
      encryptedPayload.backup?.sensitive_local_copy !== false ||
      !encryptedPayload.backup?.package
    ) {
      throw new Error(`Packaged runtime did not create an encrypted memory backup: ${encryptedBackup.stdout}`);
    }
    await stat(encryptedPayload.backup.package);
    const encryptedRestorePlan = await run(
      "node",
      [
        agentBin,
        "memory",
        "backup",
        "restore",
        encryptedPayload.backup.id,
        "--passphrase-env",
        "AGENT_DEVKIT_BACKUP_PASSPHRASE",
        "--json",
      ],
      { env },
    );
    const encryptedRestorePayload = JSON.parse(encryptedRestorePlan.stdout);
    if (encryptedRestorePayload.status !== "planned" || encryptedRestorePayload.executed !== false) {
      throw new Error(`Packaged runtime did not plan encrypted memory restore safely: ${encryptedRestorePlan.stdout}`);
    }
    const knowledgeProject = await mkdtemp(path.join(os.tmpdir(), "agent-devkit-kb-"));
    try {
      const knowledge = await run("node", [agentBin, "knowledge-base", "create", "--provider", "github", "--json"], {
        env,
        cwd: knowledgeProject,
      });
      const knowledgePayload = JSON.parse(knowledge.stdout);
      if (knowledgePayload.kb?.storage?.provider !== "knowledge-github" || knowledgePayload.stored_values !== false) {
        throw new Error(`Packaged runtime did not create canonical knowledge base: ${knowledge.stdout}`);
      }
      if (
        knowledgePayload.kb?.cache?.local_ttl_minutes !== 1440 ||
        knowledgePayload.kb?.cache?.remote_ttl_minutes !== 240
      ) {
        throw new Error(`Packaged runtime did not expose knowledge cache policy: ${knowledge.stdout}`);
      }
      await stat(path.join(knowledgeProject, "knowledge-base", "indexes", "semantic.json"));
      await stat(path.join(knowledgeProject, "knowledge-base", "indexes", "chunks.jsonl"));
      const tokens = await run("node", [agentBin, "knowledge-base", "tokens", "--json"], { env, cwd: knowledgeProject });
      const tokensPayload = JSON.parse(tokens.stdout);
      if (tokensPayload.stored_values !== false || String(tokens.stdout).includes("token_")) {
        throw new Error(`Packaged runtime exposed raw knowledge tokens: ${tokens.stdout}`);
      }
      const sensitiveSnapshot = await run(
        "node",
        [
          agentBin,
          "knowledge",
          "snapshot",
          "create",
          "--title",
          "Package Sensitive",
          "--content",
          "api_key=abc123 user test@example.com cpf 123.456.789-00",
          "--json",
        ],
        { env, cwd: knowledgeProject },
      );
      const sensitivePayload = JSON.parse(sensitiveSnapshot.stdout);
      const sensitiveText = await readFile(sensitivePayload.path, "utf8");
      if (
        !sensitiveText.includes("[REDACTED_SECRET]") ||
        !sensitiveText.includes("[REDACTED_PII]") ||
        sensitiveText.includes("abc123") ||
        sensitiveText.includes("test@example.com") ||
        sensitiveText.includes("123.456.789-00")
      ) {
        throw new Error(`Packaged runtime stored sensitive knowledge snapshot material: ${sensitiveText}`);
      }
      const sensitiveReview = await run("node", [agentBin, "knowledge", "review", sensitivePayload.snapshot_id, "--json"], {
        env,
        cwd: knowledgeProject,
      });
      if (JSON.parse(sensitiveReview.stdout).status !== "rejected") {
        throw new Error(`Packaged runtime approved sensitive knowledge snapshot: ${sensitiveReview.stdout}`);
      }
      const sensitivePublish = await run("node", [agentBin, "knowledge", "publish", sensitivePayload.snapshot_id, "--yes", "--owner-agent", "knowledge-owner", "--json"], {
        env,
        cwd: knowledgeProject,
      });
      if (JSON.parse(sensitivePublish.stdout).status !== "blocked") {
        throw new Error(`Packaged runtime published sensitive knowledge snapshot: ${sensitivePublish.stdout}`);
      }
      const snapshot = await run("node", [
        agentBin,
        "knowledge",
        "snapshot",
        "create",
        "--title",
        "Package Snapshot",
        "--content",
        "# Package Snapshot\n\nReusable package QA knowledge.",
        "--json",
      ], { env, cwd: knowledgeProject });
      const snapshotPayload = JSON.parse(snapshot.stdout);
      const snapshotId = snapshotPayload.snapshot_id;
      const snapshotList = await run("node", [agentBin, "knowledge", "snapshot", "list", "--json"], { env, cwd: knowledgeProject });
      if (JSON.parse(snapshotList.stdout).count < 1) {
        throw new Error(`Packaged runtime did not list knowledge snapshots: ${snapshotList.stdout}`);
      }
      const snapshotScore = await run("node", [agentBin, "knowledge", "snapshot", "score", snapshotId, "--json"], { env, cwd: knowledgeProject });
      const scorePayload = JSON.parse(snapshotScore.stdout);
      if (!["submit", "review"].includes(scorePayload.decision)) {
        throw new Error(`Packaged runtime returned unexpected snapshot score: ${snapshotScore.stdout}`);
      }
      const snapshotSubmit = await run("node", [agentBin, "knowledge", "snapshot", "submit", snapshotId, "--json"], { env, cwd: knowledgeProject });
      if (JSON.parse(snapshotSubmit.stdout).status !== "pending-review") {
        throw new Error(`Packaged runtime did not submit snapshot for review: ${snapshotSubmit.stdout}`);
      }
      const plannedPublish = await run("node", [agentBin, "knowledge", "publish", snapshotId, "--json"], { env, cwd: knowledgeProject });
      const plannedPublishPayload = JSON.parse(plannedPublish.stdout);
      if (plannedPublishPayload.status !== "planned" || plannedPublishPayload.review?.persisted !== false) {
        throw new Error(`Packaged runtime knowledge publish plan mutated review state: ${plannedPublish.stdout}`);
      }
      if (await pathExists(path.join(knowledgeProject, "knowledge-base", "reviews", "approved", `${snapshotId}.json`))) {
        throw new Error("Packaged runtime knowledge publish plan persisted review for clean snapshot without --yes");
      }
      if (await pathExists(path.join(knowledgeProject, "knowledge-base", "snapshots", "accepted", `${snapshotId}.md`))) {
        throw new Error("Packaged runtime knowledge publish plan moved snapshot without --yes");
      }
      const missingOwnerPublish = await run("node", [agentBin, "knowledge", "publish", snapshotId, "--yes", "--json"], { env, cwd: knowledgeProject }).catch((error) => error);
      if (!String(missingOwnerPublish.message || "").includes("owner_agent_required")) {
        throw new Error(`Packaged runtime did not require knowledge-owner for publish: ${missingOwnerPublish.message || missingOwnerPublish.stdout}`);
      }
      const published = await run("node", [agentBin, "knowledge", "publish", snapshotId, "--yes", "--owner-agent", "knowledge-owner", "--json"], { env, cwd: knowledgeProject });
      const publishedPayload = JSON.parse(published.stdout);
      if (publishedPayload.status !== "published" || publishedPayload.review?.persisted !== true) {
        throw new Error(`Packaged runtime did not publish confirmed knowledge snapshot: ${published.stdout}`);
      }
      const auditDir = path.join(knowledgeProject, "knowledge-base", "audit");
      const auditFiles = (await readdir(auditDir)).filter((item) => item.endsWith(".json"));
      const auditEvents = [];
      for (const file of auditFiles) {
        auditEvents.push(JSON.parse(await readFile(path.join(auditDir, file), "utf8")));
      }
      const snapshotAuditEvents = auditEvents.filter((item) => item.snapshot_id === snapshotId);
      const auditEventNames = new Set(snapshotAuditEvents.map((item) => item.event));
      if (
        !auditEventNames.has("review") ||
        !auditEventNames.has("publish") ||
        !snapshotAuditEvents.every((item) => item.content_sha256)
      ) {
        throw new Error(`Packaged runtime did not write knowledge audit events: ${JSON.stringify(auditEvents)}`);
      }
      const search = await run("node", [agentBin, "knowledge", "search", "package", "--json"], { env, cwd: knowledgeProject });
      if (JSON.parse(search.stdout).count < 1) {
        throw new Error(`Packaged runtime did not index published knowledge snapshot: ${search.stdout}`);
      }
      const duplicateSnapshot = await run("node", [
        agentBin,
        "knowledge",
        "snapshot",
        "create",
        "--title",
        "Package Snapshot Duplicate",
        "--content",
        "# Package Snapshot\n\nReusable package QA knowledge.",
        "--json",
      ], { env, cwd: knowledgeProject });
      const duplicatePayload = JSON.parse(duplicateSnapshot.stdout);
      const duplicateScore = await run("node", [agentBin, "knowledge", "snapshot", "score", duplicatePayload.snapshot_id, "--json"], { env, cwd: knowledgeProject });
      const duplicateScorePayload = JSON.parse(duplicateScore.stdout);
      if (
        duplicateScorePayload.decision !== "blocked" ||
        !(duplicateScorePayload.findings || []).some((item) => item.reason === "duplicate-content")
      ) {
        throw new Error(`Packaged runtime did not block duplicate knowledge snapshot: ${duplicateScore.stdout}`);
      }
      const conversationalSnapshot = await run("node", [
        agentBin,
        "knowledge",
        "snapshot",
        "create",
        "--title",
        "Package Conversational",
        "--content",
        "ok obrigado",
        "--json",
      ], { env, cwd: knowledgeProject });
      const conversationalPayload = JSON.parse(conversationalSnapshot.stdout);
      const conversationalScore = await run(
        "node",
        [agentBin, "knowledge", "snapshot", "score", conversationalPayload.snapshot_id, "--json"],
        { env, cwd: knowledgeProject },
      );
      const conversationalScorePayload = JSON.parse(conversationalScore.stdout);
      if (
        conversationalScorePayload.decision !== "blocked" ||
        !(conversationalScorePayload.findings || []).some((item) => item.reason === "purely-conversational-content")
      ) {
        throw new Error(`Packaged runtime did not block conversational knowledge snapshot: ${conversationalScore.stdout}`);
      }
      const personalSnapshot = await run("node", [
        agentBin,
        "knowledge",
        "snapshot",
        "create",
        "--title",
        "Package Personal Memory",
        "--content",
        "Meu nome e Ianota e prefiro respostas curtas.",
        "--json",
      ], { env, cwd: knowledgeProject });
      const personalPayload = JSON.parse(personalSnapshot.stdout);
      const personalScore = await run(
        "node",
        [agentBin, "knowledge", "snapshot", "score", personalPayload.snapshot_id, "--json"],
        { env, cwd: knowledgeProject },
      );
      const personalScorePayload = JSON.parse(personalScore.stdout);
      if (
        personalScorePayload.decision !== "blocked" ||
        !(personalScorePayload.findings || []).some((item) => item.reason === "personal-memory-content")
      ) {
        throw new Error(`Packaged runtime did not block personal-memory knowledge snapshot: ${personalScore.stdout}`);
      }
      const reviewList = await run("node", [agentBin, "knowledge", "review", "list", "--json"], { env, cwd: knowledgeProject });
      if (JSON.parse(reviewList.stdout).kind !== "knowledge-reviews") {
        throw new Error(`Packaged runtime did not list knowledge reviews: ${reviewList.stdout}`);
      }
      const curate = await run("node", [agentBin, "knowledge", "curate", "--json"], { env, cwd: knowledgeProject });
      if (JSON.parse(curate.stdout).kind !== "knowledge-curation") {
        throw new Error(`Packaged runtime did not run knowledge curate: ${curate.stdout}`);
      }
      const sync = await run("node", [agentBin, "knowledge", "sync", "--json"], { env, cwd: knowledgeProject });
      if (JSON.parse(sync.stdout).status !== "planned") {
        throw new Error(`Packaged runtime did not plan remote knowledge sync: ${sync.stdout}`);
      }
    } finally {
      await rm(knowledgeProject, { recursive: true, force: true });
    }
    const roadmap = await run("node", [agentBin, "roadmap", "--json"], { env });
    const roadmapPayload = JSON.parse(roadmap.stdout);
    if (!Array.isArray(roadmapPayload.preteridos) || !roadmapPayload.preteridos.includes(25) || !roadmapPayload.preteridos.includes(26)) {
      throw new Error(`Packaged runtime roadmap did not filter preteridos: ${roadmap.stdout}`);
    }
    const doctor = await run("node", [agentBin, "doctor", "--json"], { env });
    const doctorPayload = JSON.parse(doctor.stdout);
    if (doctorPayload.status !== "ok") {
      throw new Error(`Packaged runtime doctor failed: ${doctor.stdout}`);
    }

    const canonicalEnv = {
      ...process.env,
      HOME: fakeHome,
      PYTHONDONTWRITEBYTECODE: "1",
    };
    delete canonicalEnv.AGENT_DEVKIT_HOME;
    delete canonicalEnv.AI_DEVKIT_CONFIG_HOME;
    delete canonicalEnv.AIKIT_CONFIG_HOME;
    const config = await run("node", [agentBin, "config", "show", "--json"], { env: canonicalEnv });
    const configPayload = JSON.parse(config.stdout);
    const home = configPayload.home || {};
    if (!String(home.home || "").endsWith(".agent-devkit")) {
      throw new Error(`Packaged runtime did not use canonical .agent-devkit home: ${config.stdout}`);
    }
    if (home.migration_command !== "agent config migrate-home") {
      throw new Error(`Packaged runtime is missing home migration command: ${config.stdout}`);
    }
    await assertNoForbiddenFiles(runtimeRoot);
  } finally {
    await rm(configHome, { recursive: true, force: true });
    await rm(fakeHome, { recursive: true, force: true });
  }

  console.log("Agent DevKit npm package verified.");
}

try {
  await main();
} catch (error) {
  console.error(error instanceof Error ? error.message : "Agent DevKit package verification failed.");
  process.exit(1);
}
