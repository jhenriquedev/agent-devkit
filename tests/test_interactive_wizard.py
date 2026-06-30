#!/usr/bin/env python3
"""Focused tests for interactive CLI wizard helpers."""

from __future__ import annotations

import contextlib
import io
import unittest
from unittest import mock

from cli.aikit import interactive_wizard


class InteractiveWizardTest(unittest.TestCase):
    def test_onboarding_mode_menu_marks_minimal_as_recommended(self) -> None:
        option = interactive_wizard.ONBOARDING_MODE_OPTIONS[0]

        line = interactive_wizard.format_onboarding_option(option, selected=False, include_selector=False)

        self.assertEqual(line, "1. minimo: identidade, mini-cerebro local embarcado e memoria (Recomendado)")

    def test_onboarding_mode_fallback_prompt_has_no_visible_default(self) -> None:
        captured = io.StringIO()
        ask_text = mock.Mock(return_value="")
        with (
            mock.patch.object(interactive_wizard, "choose_onboarding_mode_with_arrows", return_value=None),
            mock.patch.object(interactive_wizard, "ask_text", ask_text),
            contextlib.redirect_stdout(captured),
        ):
            selected = interactive_wizard.choose_onboarding_mode()

        self.assertEqual(selected, "minimal")
        ask_text.assert_called_once_with("Escolha o modo:")
        output = captured.getvalue()
        self.assertIn("1. minimo: identidade, mini-cerebro local embarcado e memoria (Recomendado)", output)
        self.assertIn("2. completo: minimo + toolchain, sources, notificacoes, knowledge e memorias", output)
        self.assertIn("3. pular", output)

    def test_onboarding_mode_arrow_selection_moves_to_complete(self) -> None:
        captured = io.StringIO()
        with (
            mock.patch.object(interactive_wizard, "read_key", side_effect=["\x1b[B", "\r"]),
            contextlib.redirect_stdout(captured),
        ):
            selected = interactive_wizard.read_onboarding_mode_selection()

        self.assertEqual(selected, "complete")

    def test_onboarding_mode_numeric_selection_still_works(self) -> None:
        captured = io.StringIO()
        with (
            mock.patch.object(interactive_wizard, "read_key", return_value="3"),
            contextlib.redirect_stdout(captured),
        ):
            selected = interactive_wizard.read_onboarding_mode_selection()

        self.assertEqual(selected, "skip")

    def test_onboarding_mode_text_selection_still_works(self) -> None:
        captured = io.StringIO()
        with (
            mock.patch.object(interactive_wizard, "read_key", side_effect=["c", "o", "m", "p", "l", "e", "t", "o", "\r"]),
            contextlib.redirect_stdout(captured),
        ):
            selected = interactive_wizard.read_onboarding_mode_selection()

        self.assertEqual(selected, "complete")


if __name__ == "__main__":
    unittest.main()
