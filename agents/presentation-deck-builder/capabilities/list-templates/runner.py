#!/usr/bin/env python3
"""Runner for presentation-deck-builder/list-templates."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from template_support import parse_template_manifest, resolve_templates_root  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="List registered templates")
    parser.add_argument("--templates-root")
    args = parser.parse_args()
    try:
        root = resolve_templates_root(args.templates_root)
        print("# Templates")
        print("")
        if not root.exists():
            print("- Nenhum template registrado.")
            return 0
        for manifest_path in sorted(root.glob("*/template.yaml")):
            manifest = parse_template_manifest(manifest_path)
            print(f"- {manifest.get('id')}  current={manifest.get('current_version') or '-'}  {manifest.get('name')}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
