#!/usr/bin/env python3
"""Tests for canonical write policy normalization."""

from __future__ import annotations

import unittest

from cli.aikit.write_policy import (
    canonical_write_policies,
    coerce_write_policy_metadata,
    is_autonomous_safe_write_policy,
    is_blocked_by_default,
    is_known_write_policy,
    legacy_write_policy_aliases,
    normalize_write_policy,
    requires_runtime_confirmation,
    write_policy_metadata,
    write_policy_public_fields,
)


class WritePolicyTest(unittest.TestCase):
    def test_normalizes_legacy_aliases(self) -> None:
        self.assertEqual(normalize_write_policy("read-only"), "read_only")
        self.assertEqual(normalize_write_policy("ask_before_write"), "confirm")
        self.assertEqual(normalize_write_policy("local-config-write"), "local_config_write")
        self.assertEqual(normalize_write_policy("template_version_write"), "local_write")

    def test_autonomous_safe_policies_are_read_only_or_dry_run(self) -> None:
        self.assertTrue(is_autonomous_safe_write_policy("read_only"))
        self.assertTrue(is_autonomous_safe_write_policy("read-only"))
        self.assertTrue(is_autonomous_safe_write_policy("dry_run"))
        self.assertFalse(is_autonomous_safe_write_policy("output_only"))
        self.assertFalse(is_autonomous_safe_write_policy("confirm"))

    def test_confirmation_and_blocked_policies(self) -> None:
        self.assertTrue(requires_runtime_confirmation("ask_before_write"))
        self.assertTrue(requires_runtime_confirmation("local_write"))
        self.assertTrue(requires_runtime_confirmation("local_config_write"))
        self.assertFalse(requires_runtime_confirmation("output_only"))
        self.assertTrue(is_blocked_by_default("blocked_by_default"))

    def test_metadata_exposes_raw_and_canonical_values(self) -> None:
        metadata = write_policy_metadata("read-only")

        self.assertEqual(metadata["raw"], "read-only")
        self.assertEqual(metadata["canonical"], "read_only")
        self.assertTrue(metadata["known"])
        self.assertTrue(metadata["legacy"])
        self.assertTrue(metadata["autonomous_safe"])

    def test_unknown_policy_is_not_known(self) -> None:
        self.assertFalse(is_known_write_policy("write_whenever"))

    def test_policy_vocabulary_helpers_expose_copies(self) -> None:
        policies = canonical_write_policies()
        aliases = legacy_write_policy_aliases()

        self.assertIn("read_only", policies)
        self.assertEqual(aliases["read-only"], "read_only")
        policies.add("mutated")
        aliases["mutated"] = "read_only"
        self.assertNotIn("mutated", canonical_write_policies())
        self.assertNotIn("mutated", legacy_write_policy_aliases())

    def test_public_fields_coerce_metadata_payloads(self) -> None:
        fields = write_policy_public_fields("ask_before_write")

        self.assertEqual(fields["write_policy"], "confirm")
        self.assertEqual(fields["write_policy_raw"], "ask_before_write")
        self.assertTrue(fields["write_policy_metadata"]["legacy"])

        coerced = coerce_write_policy_metadata(fields["write_policy_metadata"])
        self.assertEqual(coerced["canonical"], "confirm")
        self.assertTrue(coerced["requires_confirmation"])


if __name__ == "__main__":
    unittest.main()
