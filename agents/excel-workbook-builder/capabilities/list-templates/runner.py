#!/usr/bin/env python3
"""Runner for excel-workbook-builder/list-templates."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from workbook_support import parse_template_manifest, resolve_templates_root  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="List registered Excel templates")
    parser.add_argument("--templates-root")
    args = parser.parse_args()

    root = resolve_templates_root(args.templates_root)
    lines = ["# Excel Templates", ""]
    if not root.exists():
        lines.append("- No template registered.")
    else:
        found = False
        for manifest in sorted(root.glob("*/template.yaml")):
            found = True
            data = parse_template_manifest(manifest)
            lines.append(
                f"- {data.get('id') or manifest.parent.name}  "
                f"current={data.get('current_version') or '-'}  "
                f"{data.get('name') or '-'}"
            )
        if not found:
            lines.append("- No template registered.")
    print("\n".join(lines).rstrip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

