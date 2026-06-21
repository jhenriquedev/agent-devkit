#!/usr/bin/env python3
"""Azure DevOps workflow action builder for the N2 Support Agent."""

from __future__ import annotations

from typing import Any


DEFAULT_N2_TAG = "Analise N2"
DEFAULT_PATCH_FILE = "patch_plan.md"


def build_azure_action_specs(
    *,
    project: str,
    card: int,
    card_comment: str,
    patch_file_name: str | None,
    attachment_path: str | None,
    target_state: str | None,
    target_column: str | None,
    assign_to: str | None,
) -> list[dict[str, Any]]:
    specs = [
        {
            "id": "add-n2-tag",
            "capability": "update-card-tags",
            "commandArgs": [
                "--project",
                project,
                "--id",
                str(card),
                "--add-tag",
                DEFAULT_N2_TAG,
                "--reason",
                "N2 analysis started",
            ],
            "summary": f"Add tag {DEFAULT_N2_TAG}",
        },
        {
            "id": "comment-card",
            "capability": "comment-card",
            "commandArgs": [
                "--project",
                project,
                "--id",
                str(card),
                "--comment",
                card_comment,
            ],
            "summary": card_comment,
        },
    ]
    if target_state:
        command = [
            "--project",
            project,
            "--id",
            str(card),
            "--state",
            target_state,
            "--reason",
            "N2 workflow update",
        ]
        if target_column:
            command.extend(["--board-column", target_column])
        specs.append(
            {
                "id": "move-card",
                "capability": "move-card",
                "commandArgs": command,
                "summary": build_move_summary(target_state, target_column),
            }
        )
    elif target_column:
        specs.append(
            {
                "id": "move-card",
                "capability": "move-card",
                "commandArgs": [],
                "summary": "Target column was provided without target state; move-card requires --target-state.",
                "status": "skipped",
            }
        )
    if assign_to:
        specs.append(
            {
                "id": "assign-card",
                "capability": "assign-card",
                "commandArgs": [
                    "--project",
                    project,
                    "--id",
                    str(card),
                    "--assignee",
                    assign_to,
                    "--reason",
                    "N2 workflow assignment",
                ],
                "summary": f"Assign card {card} to {assign_to}",
            }
        )
    specs.append(build_attach_spec(project, card, patch_file_name, attachment_path))
    return specs


def build_attach_spec(project: str, card: int, patch_file_name: str | None, attachment_path: str | None) -> dict[str, Any]:
    file_name = patch_file_name or DEFAULT_PATCH_FILE
    command = []
    if attachment_path:
        command = [
            "--project",
            project,
            "--id",
            str(card),
            "--file",
            attachment_path,
            "--comment",
            "N2 patch_plan.md",
        ]
    return {
        "id": "attach-patch-plan",
        "capability": "attach-file",
        "commandArgs": command,
        "summary": f"Attach {file_name} to card {card}",
    }


def build_move_summary(target_state: str, target_column: str | None) -> str:
    if target_column:
        return f"Move card to state {target_state} and column {target_column}"
    return f"Move card to state {target_state}"
