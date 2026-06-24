#!/usr/bin/env python3
"""Tests for agent manifest contracts."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class AgentManifestTest(unittest.TestCase):
    def test_excel_workbook_builder_declares_all_capabilities(self) -> None:
        agent_dir = ROOT / "agents" / "excel-workbook-builder"
        manifest = yaml.safe_load((agent_dir / "agent.yaml").read_text(encoding="utf-8")) or {}
        declared = manifest.get("capabilities")
        on_disk = sorted(path.parent.name for path in (agent_dir / "capabilities").glob("*/capability.yaml"))

        self.assertIsInstance(declared, list)
        self.assertEqual(sorted(declared), on_disk)


if __name__ == "__main__":
    unittest.main()
