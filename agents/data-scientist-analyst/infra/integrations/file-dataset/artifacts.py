#!/usr/bin/env python3
"""Artifact helpers for generated data-scientist outputs."""

from __future__ import annotations

from pathlib import Path


def write_artifact(content: str, output: str | None) -> str | None:
    if not output:
        return None
    path = Path(output).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return str(path)
