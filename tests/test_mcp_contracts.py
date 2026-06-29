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
            },
        )
        self.assertEqual(tools_payload["kind"], "mcp-tools")
        self.assertEqual({tool["name"] for tool in tools_payload["tools"]}, tool_names)

    def test_mcp_tool_calls_use_core_and_block_unsafe_writes(self) -> None:
        from cli.aikit.mcp_tools import call_mcp_tool

        with tempfile.TemporaryDirectory() as config_home:
            env = {"AI_DEVKIT_CONFIG_HOME": config_home}
            with self.patch_env(env):
                listed = call_mcp_tool("agent_devkit_agents_list", {})
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
