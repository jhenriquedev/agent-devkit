#!/usr/bin/env python3
"""MCP stdio contracts for Agent DevKit."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from cli.aikit.tasks import create_task


ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "agent"
CLI_TIMEOUT_SECONDS = int(os.environ.get("AI_DEVKIT_TEST_CLI_TIMEOUT_SECONDS", "60"))


class McpContractsTest(unittest.TestCase):
    def run_agent(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(AGENT), *args],
            cwd=ROOT,
            env=os.environ | (env or {}),
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=CLI_TIMEOUT_SECONDS,
        )

    def test_mcp_manifest_and_tools_cli(self) -> None:
        manifest = self.run_agent("mcp", "manifest", "--json")
        tools = self.run_agent("mcp", "tools", "--json")

        self.assertEqual(manifest.returncode, 0, manifest.stderr)
        self.assertEqual(tools.returncode, 0, tools.stderr)
        manifest_payload = json.loads(manifest.stdout)
        tools_payload = json.loads(tools.stdout)
        self.assertEqual(manifest_payload["kind"], "mcp-manifest")
        self.assertEqual(manifest_payload["transport"], "stdio")
        self.assertEqual(manifest_payload["server"]["name"], "agent-devkit")
        tool_names = {tool["name"] for tool in manifest_payload["tools"]}
        self.assertGreaterEqual(
            tool_names,
            {
                "agent_devkit_agents_list",
                "agent_devkit_capabilities_list",
                "agent_devkit_capability_inspect",
                "agent_devkit_capability_run",
                "agent_devkit_doctor",
                "agent_devkit_source_list",
                "agent_devkit_source_status",
                "agent_devkit_wizard_show",
                "agent_devkit_wizard_answer",
                "agent_devkit_knowledge_snapshot_create",
                "agent_devkit_knowledge_snapshot_score",
                "agent_devkit_knowledge_publish",
            },
        )
        self.assertEqual(tools_payload["kind"], "mcp-tools")
        self.assertEqual({tool["name"] for tool in tools_payload["tools"]}, tool_names)

    def test_mcp_tool_calls_use_core_and_block_unsafe_writes(self) -> None:
        from cli.aikit.mcp_tools import call_mcp_tool

        with tempfile.TemporaryDirectory() as config_home:
            env = {
                "AI_DEVKIT_CONFIG_HOME": config_home,
                "AGENT_DEVKIT_BACKUP_PASSPHRASE": "mcp-backup-passphrase",
            }
            with self.patch_env(env):
                listed = call_mcp_tool("agent_devkit_agents_list", {})
                onboarding = call_mcp_tool("agent_devkit_onboarding_status", {})
                memory = call_mcp_tool("agent_devkit_memory_show", {})
                memory_backup = call_mcp_tool("agent_devkit_memory_backup_create", {"title": "MCP Backup"})
                memory_backup_id = memory_backup["structuredContent"]["backup"]["id"]
                encrypted_backup = call_mcp_tool(
                    "agent_devkit_memory_backup_create",
                    {
                        "title": "MCP Encrypted Backup",
                        "encrypted": True,
                        "passphrase_env": "AGENT_DEVKIT_BACKUP_PASSPHRASE",
                    },
                )
                memory_backup_list = call_mcp_tool("agent_devkit_memory_backup_list", {})
                memory_backup_restore = call_mcp_tool("agent_devkit_memory_backup_restore", {"backup_id": memory_backup_id})
                shared = call_mcp_tool("agent_devkit_shared_memory_create", {"title": "MCP Memory"})
                shared_id = shared["structuredContent"]["memory"]["id"]
                shared_key = shared["structuredContent"]["contributor_access"]["key"]
                shared_owner_key = shared["structuredContent"]["owner_access"]["key"]
                shared_audit_text = Path(shared["structuredContent"]["audit"]["json_path"]).read_text(encoding="utf-8")
                shared_submit = call_mcp_tool(
                    "agent_devkit_shared_memory_submit",
                    {
                        "memory_id": shared_id,
                        "title": "Finding",
                        "content": "Conteudo reutilizavel sem segredo.",
                        "key": shared_key,
                    },
                )
                shared_publish = call_mcp_tool(
                    "agent_devkit_shared_memory_publish",
                    {
                        "memory_id": shared_id,
                        "submission_id": shared_submit["structuredContent"]["submission_id"],
                        "yes": True,
                        "owner_key": shared_owner_key,
                    },
                )
                shared_read = call_mcp_tool(
                    "agent_devkit_shared_memory_read",
                    {
                        "memory_id": shared_id,
                        "entry_id": shared_submit["structuredContent"]["submission_id"],
                        "key": shared_key,
                    },
                )
                personality_update = call_mcp_tool("agent_devkit_personality_update", {"agent_name": "Jarvis"})
                personality_show = call_mcp_tool("agent_devkit_personality_show", {})
                create_task(task_id="mcp-daily", title="MCP Daily", prompt="status", schedule={"type": "manual"})
                tasks = call_mcp_tool("agent_devkit_task_list", {})
                task_run = call_mcp_tool("agent_devkit_task_run_dry_run", {"task_id": "mcp-daily"})
                scheduler = call_mcp_tool("agent_devkit_scheduler_run_once_dry_run", {})
                notifications = call_mcp_tool("agent_devkit_notifications_format", {"message": "done", "task_id": "mcp-daily"})
                catalog = call_mcp_tool("agent_devkit_catalog_list", {"type": "workflow"})
                plan = call_mcp_tool("agent_devkit_agentic_plan", {"prompt": "analise o card 7914 do azure"})
                workflow = call_mcp_tool("agent_devkit_workflow_run_dry_run", {"workflow_id": "daily-pr-review"})
                local_llm = call_mcp_tool("agent_devkit_local_llm_doctor", {})
                local_skill = call_mcp_tool(
                    "agent_devkit_local_skill_create",
                    {"id": "mcp-skill", "description": "Skill local para hosts MCP."},
                )
                local_skill_list = call_mcp_tool("agent_devkit_local_skill_list", {})
                local_skill_show = call_mcp_tool("agent_devkit_local_skill_show", {"id": "mcp-skill"})
                local_script = call_mcp_tool(
                    "agent_devkit_local_script_create",
                    {"id": "mcp-script", "command": "echo mcp"},
                )
                local_script_list = call_mcp_tool("agent_devkit_local_script_list", {})
                local_script_run = call_mcp_tool("agent_devkit_local_script_run_dry_run", {"id": "mcp-script"})
                local_agent = call_mcp_tool(
                    "agent_devkit_local_agent_create",
                    {"id": "mcp-agent", "description": "Agente local para hosts MCP."},
                )
                local_agent_list = call_mcp_tool("agent_devkit_local_agent_list", {})
                local_agent_show = call_mcp_tool("agent_devkit_local_agent_show", {"id": "mcp-agent"})
                local_agent_validate = call_mcp_tool("agent_devkit_local_agent_validate", {"id": "mcp-agent"})
                automation = call_mcp_tool(
                    "agent_devkit_local_automation_create",
                    {
                        "id": "mcp-check",
                        "title": "MCP Check",
                        "prompt": "resuma tarefas pendentes",
                        "every": "1d",
                    },
                )
                automation_list = call_mcp_tool("agent_devkit_local_automation_list", {})
                automation_show = call_mcp_tool("agent_devkit_local_automation_show", {"id": "mcp-check"})
                automation_disable = call_mcp_tool("agent_devkit_local_automation_disable", {"id": "mcp-check"})
                automation_validate = call_mcp_tool("agent_devkit_local_automation_validate", {"id": "mcp-check"})
                artifacts = call_mcp_tool("agent_devkit_local_artifacts_list", {})
                with tempfile.TemporaryDirectory() as team_project:
                    team_initial = call_mcp_tool("agent_devkit_team_status", {"project": team_project})
                    team_init = call_mcp_tool("agent_devkit_team_init", {"project": team_project})
                    team = call_mcp_tool("agent_devkit_team_status", {"project": team_project})
                    team_doctor = call_mcp_tool("agent_devkit_team_doctor", {"project": team_project})
                    team_onboard = call_mcp_tool("agent_devkit_team_onboard", {"project": team_project})
                    team_profiles = call_mcp_tool("agent_devkit_team_profile_list", {"project": team_project})
                    team_profile = call_mcp_tool(
                        "agent_devkit_team_profile_show",
                        {"project": team_project, "profile_id": "default"},
                    )
                    team_export = call_mcp_tool(
                        "agent_devkit_team_profile_export",
                        {"project": team_project, "profile_id": "default"},
                    )
                knowledge = call_mcp_tool("agent_devkit_knowledge_doctor", {})
                with tempfile.TemporaryDirectory() as project:
                    kb_init = call_mcp_tool("agent_devkit_knowledge_init", {"project": project})
                    kb_create = call_mcp_tool("agent_devkit_knowledge_base_create", {"project": project, "provider": "github"})
                    kb_semantic_index = Path(project) / "knowledge-base" / "indexes" / "semantic.json"
                    kb_chunks_index = Path(project) / "knowledge-base" / "indexes" / "chunks.jsonl"
                    kb_semantic_index_exists = kb_semantic_index.exists()
                    kb_chunks_index_exists = kb_chunks_index.exists()
                    kb_status = call_mcp_tool("agent_devkit_knowledge_base_status", {"project": project})
                    kb_tokens = call_mcp_tool("agent_devkit_knowledge_base_tokens", {"project": project})
                    kb_rotate = call_mcp_tool("agent_devkit_knowledge_base_rotate_token", {"project": project, "scope": "read"})
                    kb_index = call_mcp_tool("agent_devkit_knowledge_index", {"project": project})
                    kb_snapshot = call_mcp_tool(
                        "agent_devkit_knowledge_snapshot_create",
                        {
                            "project": project,
                            "title": "MCP Snapshot",
                            "content": "# MCP Snapshot\n\nConteudo reutilizavel sem segredo para hosts MCP.",
                        },
                    )
                    kb_snapshot_id = kb_snapshot["structuredContent"]["snapshot_id"]
                    kb_snapshot_list = call_mcp_tool("agent_devkit_knowledge_snapshot_list", {"project": project})
                    kb_snapshot_show = call_mcp_tool(
                        "agent_devkit_knowledge_snapshot_show",
                        {"project": project, "snapshot_id": kb_snapshot_id},
                    )
                    kb_snapshot_score = call_mcp_tool(
                        "agent_devkit_knowledge_snapshot_score",
                        {"project": project, "snapshot_id": kb_snapshot_id},
                    )
                    kb_snapshot_submit = call_mcp_tool(
                        "agent_devkit_knowledge_snapshot_submit",
                        {"project": project, "snapshot_id": kb_snapshot_id},
                    )
                    kb_review = call_mcp_tool(
                        "agent_devkit_knowledge_review",
                        {"project": project, "snapshot_id": kb_snapshot_id},
                    )
                    kb_publish_plan = call_mcp_tool(
                        "agent_devkit_knowledge_publish",
                        {"project": project, "snapshot_id": kb_snapshot_id},
                    )
                    kb_publish_missing_owner = call_mcp_tool(
                        "agent_devkit_knowledge_publish",
                        {"project": project, "snapshot_id": kb_snapshot_id, "yes": True},
                    )
                    kb_publish = call_mcp_tool(
                        "agent_devkit_knowledge_publish",
                        {
                            "project": project,
                            "snapshot_id": kb_snapshot_id,
                            "yes": True,
                            "owner_agent": "knowledge-owner",
                        },
                    )
                    kb_review_list = call_mcp_tool("agent_devkit_knowledge_review_list", {"project": project})
                    kb_curate = call_mcp_tool("agent_devkit_knowledge_curate", {"project": project})
                    kb_sync = call_mcp_tool("agent_devkit_knowledge_sync", {"project": project})
                    kb_search = call_mcp_tool(
                        "agent_devkit_knowledge_search",
                        {"project": project, "query": "mcp snapshot"},
                    )
                read_only = call_mcp_tool(
                    "agent_devkit_capability_run",
                    {
                        "agent_id": "task-orchestrator",
                        "capability_id": "plan-task",
                        "request_id": "req-mcp-1",
                        "inputs": {"prompt": "planeje"},
                    },
                )
                blocked = call_mcp_tool(
                    "agent_devkit_capability_run",
                    {
                        "agent_id": "sqlserver-change-operator",
                        "capability_id": "apply-migration",
                        "args": ["--path", "migration.sql", "--execute"],
                    },
                )

        self.assertFalse(listed["isError"])
        self.assertEqual(listed["structuredContent"]["kind"], "agents")
        self.assertFalse(onboarding["isError"])
        self.assertEqual(onboarding["structuredContent"]["kind"], "onboarding")
        self.assertFalse(memory["isError"])
        self.assertEqual(memory["structuredContent"]["kind"], "memory")
        self.assertFalse(memory_backup["isError"])
        self.assertEqual(memory_backup["structuredContent"]["kind"], "memory-backup")
        self.assertFalse(encrypted_backup["isError"])
        self.assertTrue(encrypted_backup["structuredContent"]["backup"]["encrypted"])
        self.assertFalse(encrypted_backup["structuredContent"]["backup"]["sensitive_local_copy"])
        self.assertFalse(memory_backup_list["isError"])
        self.assertEqual(memory_backup_list["structuredContent"]["kind"], "memory-backups")
        self.assertFalse(memory_backup_restore["isError"])
        self.assertEqual(memory_backup_restore["structuredContent"]["status"], "planned")
        self.assertFalse(shared["isError"])
        self.assertEqual(shared["structuredContent"]["kind"], "shared-memory")
        self.assertNotIn(shared_key, shared_audit_text)
        self.assertNotIn(shared_owner_key, shared_audit_text)
        self.assertFalse(shared_submit["isError"])
        self.assertEqual(shared_submit["structuredContent"]["status"], "pending")
        self.assertFalse(shared_publish["isError"])
        self.assertEqual(shared_publish["structuredContent"]["status"], "published")
        self.assertFalse(shared_read["isError"])
        self.assertEqual(shared_read["structuredContent"]["kind"], "shared-memory-read")
        self.assertIn("Conteudo reutilizavel sem segredo.", shared_read["structuredContent"]["content"])
        self.assertFalse(personality_update["isError"])
        self.assertEqual(personality_update["structuredContent"]["agent_name"], "Jarvis")
        self.assertFalse(personality_show["isError"])
        self.assertEqual(personality_show["structuredContent"]["agent_name"], "Jarvis")
        self.assertFalse(tasks["isError"])
        self.assertEqual(tasks["structuredContent"]["kind"], "tasks")
        self.assertFalse(task_run["isError"])
        self.assertEqual(task_run["structuredContent"]["kind"], "task-run")
        self.assertTrue(task_run["structuredContent"]["dry_run"])
        self.assertFalse(scheduler["isError"])
        self.assertEqual(scheduler["structuredContent"]["kind"], "scheduler")
        self.assertTrue(scheduler["structuredContent"]["dry_run"])
        self.assertFalse(notifications["isError"])
        self.assertEqual(notifications["structuredContent"]["kind"], "notification-event")
        self.assertFalse(catalog["isError"])
        self.assertEqual(catalog["structuredContent"]["kind"], "catalog")
        self.assertTrue(all(item["type"] == "workflow" for item in catalog["structuredContent"]["items"]))
        self.assertFalse(plan["isError"])
        self.assertEqual(plan["structuredContent"]["kind"], "agentic-plan")
        self.assertFalse(workflow["isError"])
        self.assertEqual(workflow["structuredContent"]["kind"], "workflow-run")
        self.assertTrue(workflow["structuredContent"]["dry_run"])
        self.assertFalse(local_llm["isError"])
        self.assertEqual(local_llm["structuredContent"]["kind"], "local-llm-doctor")
        self.assertFalse(local_skill["isError"])
        self.assertEqual(local_skill["structuredContent"]["kind"], "local-skill")
        self.assertTrue(any(item["id"] == "mcp-skill" for item in local_skill_list["structuredContent"]["items"]))
        self.assertFalse(local_skill_show["isError"])
        self.assertIn("Skill local para hosts MCP.", local_skill_show["structuredContent"]["content"])
        self.assertFalse(local_script["isError"])
        self.assertEqual(local_script["structuredContent"]["kind"], "local-script")
        self.assertTrue(any(item["id"] == "mcp-script" for item in local_script_list["structuredContent"]["items"]))
        self.assertFalse(local_script_run["isError"])
        self.assertEqual(local_script_run["structuredContent"]["status"], "planned")
        self.assertFalse(local_agent["isError"])
        self.assertEqual(local_agent["structuredContent"]["kind"], "local-agent")
        self.assertTrue(any(item["id"] == "mcp-agent" for item in local_agent_list["structuredContent"]["items"]))
        self.assertFalse(local_agent_show["isError"])
        self.assertIn("mcp-agent", local_agent_show["structuredContent"]["manifest"])
        self.assertFalse(local_agent_validate["isError"])
        self.assertEqual(local_agent_validate["structuredContent"]["status"], "passed")
        self.assertFalse(automation["isError"])
        self.assertEqual(automation["structuredContent"]["kind"], "local-automation")
        self.assertEqual(automation["structuredContent"]["automation"]["schedule"]["type"], "interval")
        self.assertFalse(automation_list["isError"])
        self.assertTrue(any(item["id"] == "mcp-check" for item in automation_list["structuredContent"]["items"]))
        self.assertFalse(automation_show["isError"])
        self.assertEqual(automation_show["structuredContent"]["automation"]["id"], "mcp-check")
        self.assertFalse(automation_disable["isError"])
        self.assertEqual(automation_disable["structuredContent"]["status"], "disabled")
        self.assertFalse(automation_validate["isError"])
        self.assertEqual(automation_validate["structuredContent"]["status"], "passed")
        self.assertFalse(artifacts["isError"])
        self.assertEqual(artifacts["structuredContent"]["kind"], "local-artifacts")
        self.assertTrue(any(item["id"] == "mcp-check" for item in artifacts["structuredContent"]["automations"]["items"]))
        self.assertFalse(team_initial["isError"])
        self.assertEqual(team_initial["structuredContent"]["status"], "not-configured")
        self.assertFalse(team_init["isError"])
        self.assertEqual(team_init["structuredContent"]["status"], "initialized")
        self.assertFalse(team["isError"])
        self.assertEqual(team["structuredContent"]["kind"], "team")
        self.assertEqual(team["structuredContent"]["status"], "ok")
        self.assertFalse(team_doctor["isError"])
        self.assertEqual(team_doctor["structuredContent"]["status"], "ok")
        self.assertFalse(team_onboard["isError"])
        self.assertEqual(team_onboard["structuredContent"]["status"], "ok")
        self.assertFalse(team_profiles["isError"])
        self.assertEqual(team_profiles["structuredContent"]["kind"], "team-profiles")
        self.assertFalse(team_profile["isError"])
        self.assertEqual(team_profile["structuredContent"]["profile"]["id"], "default")
        self.assertFalse(team_export["isError"])
        self.assertEqual(team_export["structuredContent"]["status"], "planned")
        self.assertEqual(knowledge["structuredContent"]["kind"], "knowledge-doctor")
        self.assertIn(knowledge["structuredContent"]["status"], {"ok", "blocked"})
        self.assertFalse(kb_init["isError"])
        self.assertEqual(kb_init["structuredContent"]["status"], "initialized")
        self.assertFalse(kb_create["isError"])
        self.assertEqual(kb_create["structuredContent"]["kb"]["storage"]["provider"], "knowledge-github")
        self.assertEqual(kb_create["structuredContent"]["kb"]["cache"], {"local_ttl_minutes": 1440, "remote_ttl_minutes": 240})
        self.assertTrue(kb_semantic_index_exists)
        self.assertTrue(kb_chunks_index_exists)
        self.assertFalse(kb_status["isError"])
        self.assertEqual(kb_status["structuredContent"]["kind"], "knowledge-base")
        self.assertFalse(kb_tokens["isError"])
        self.assertFalse(kb_tokens["structuredContent"]["stored_values"])
        self.assertFalse(kb_rotate["isError"])
        self.assertEqual(kb_rotate["structuredContent"]["scope"], "read")
        self.assertFalse(kb_index["isError"])
        self.assertEqual(kb_index["structuredContent"]["kind"], "knowledge-index")
        self.assertFalse(kb_snapshot["isError"])
        self.assertEqual(kb_snapshot["structuredContent"]["status"], "created")
        self.assertFalse(kb_snapshot_list["isError"])
        self.assertGreaterEqual(kb_snapshot_list["structuredContent"]["count"], 1)
        self.assertFalse(kb_snapshot_show["isError"])
        self.assertEqual(kb_snapshot_show["structuredContent"]["kind"], "knowledge-snapshot")
        self.assertFalse(kb_snapshot_score["isError"])
        self.assertIn(kb_snapshot_score["structuredContent"]["decision"], {"submit", "review"})
        self.assertFalse(kb_snapshot_submit["isError"])
        self.assertEqual(kb_snapshot_submit["structuredContent"]["status"], "pending-review")
        self.assertFalse(kb_review["isError"])
        self.assertEqual(kb_review["structuredContent"]["status"], "approved")
        self.assertFalse(kb_publish_plan["isError"])
        self.assertEqual(kb_publish_plan["structuredContent"]["status"], "planned")
        self.assertFalse(kb_publish_plan["structuredContent"]["review"]["persisted"])
        self.assertTrue(kb_publish_missing_owner["isError"])
        self.assertEqual(kb_publish_missing_owner["structuredContent"]["status"], "blocked")
        self.assertEqual(kb_publish_missing_owner["structuredContent"]["reason"], "owner_agent_required")
        self.assertFalse(kb_publish["isError"])
        self.assertEqual(kb_publish["structuredContent"]["status"], "published")
        self.assertFalse(kb_review_list["isError"])
        self.assertEqual(kb_review_list["structuredContent"]["kind"], "knowledge-reviews")
        self.assertFalse(kb_curate["isError"])
        self.assertEqual(kb_curate["structuredContent"]["kind"], "knowledge-curation")
        self.assertFalse(kb_sync["isError"])
        self.assertIn(kb_sync["structuredContent"]["status"], {"local-only", "planned"})
        self.assertFalse(kb_sync["structuredContent"]["executed"])
        self.assertFalse(kb_search["isError"])
        self.assertGreaterEqual(kb_search["structuredContent"]["count"], 1)
        self.assertEqual(read_only["structuredContent"]["origin"], "mcp")
        self.assertEqual(read_only["structuredContent"]["request_id"], "req-mcp-1")
        self.assertTrue(blocked["isError"])
        self.assertEqual(blocked["structuredContent"]["status"], "blocked")
        self.assertEqual(blocked["structuredContent"]["reason"], "mcp_write_policy_blocked")
        self.assertEqual(blocked["structuredContent"]["origin"], "mcp")

    def test_mcp_stdio_initialize_list_and_call(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            process = subprocess.Popen(
                [sys.executable, str(AGENT), "mcp", "serve"],
                cwd=ROOT,
                env=os.environ | {"AI_DEVKIT_CONFIG_HOME": config_home},
                text=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                initialize = self.rpc(
                    process,
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2025-11-25",
                            "capabilities": {},
                            "clientInfo": {"name": "test-client", "version": "0"},
                        },
                    },
                )
                self.notify(process, {"jsonrpc": "2.0", "method": "notifications/initialized"})
                tools = self.rpc(process, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
                doctor = self.rpc(
                    process,
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {"name": "agent_devkit_doctor", "arguments": {}},
                    },
                )
                malformed = self.rpc(
                    process,
                    {
                        "jsonrpc": "2.0",
                        "id": 4,
                        "method": "tools/call",
                        "params": {"name": "agent_devkit_doctor", "arguments": []},
                    },
                )
                unknown = self.rpc(process, {"jsonrpc": "2.0", "id": 5, "method": "unknown/method"})
            finally:
                if process.stdin:
                    process.stdin.close()
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                if process.stdout:
                    process.stdout.close()
                if process.stderr:
                    process.stderr.close()

        self.assertEqual(initialize["result"]["serverInfo"]["name"], "agent-devkit")
        self.assertIn("tools", initialize["result"]["capabilities"])
        self.assertTrue(any(tool["name"] == "agent_devkit_doctor" for tool in tools["result"]["tools"]))
        self.assertFalse(doctor["result"]["isError"])
        self.assertEqual(doctor["result"]["structuredContent"]["kind"], "doctor")
        self.assertIn("content", doctor["result"])
        self.assertEqual(malformed["error"]["code"], -32602)
        self.assertEqual(unknown["error"]["code"], -32601)

    def rpc(self, process: subprocess.Popen[str], payload: dict[str, Any]) -> dict[str, Any]:
        assert process.stdin is not None
        assert process.stdout is not None
        process.stdin.write(json.dumps(payload) + "\n")
        process.stdin.flush()
        line = process.stdout.readline()
        self.assertTrue(line, "MCP server did not return a response")
        return json.loads(line)

    def notify(self, process: subprocess.Popen[str], payload: dict[str, Any]) -> None:
        assert process.stdin is not None
        process.stdin.write(json.dumps(payload) + "\n")
        process.stdin.flush()

    def patch_env(self, values: dict[str, str]):
        class PatchEnv:
            def __enter__(self_inner: object) -> None:
                self._old_env = os.environ.copy()
                os.environ.update(values)

            def __exit__(self_inner: object, *_exc: object) -> None:
                os.environ.clear()
                os.environ.update(self._old_env)

        return PatchEnv()


if __name__ == "__main__":
    unittest.main()
