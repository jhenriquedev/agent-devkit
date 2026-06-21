#!/usr/bin/env python3
"""Runner for excel-workbook-builder/generate-workbook-from-template."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from workbook_support import (  # noqa: E402
    fill_workbook_from_dataset,
    normalize_dataset,
    resolve_templates_root,
    slugify,
)
from template_binding import resolve_template_version  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate workbook from registered template")
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--template-version")
    parser.add_argument("--templates-root")
    parser.add_argument("--output")
    parser.add_argument("--title")
    args = parser.parse_args()

    try:
        root = resolve_templates_root(args.templates_root)
        template_id = slugify(args.template_id)
        version, source_template = resolve_template_version(root, template_id, args.template_version)

        input_path = Path(args.input).expanduser().resolve()
        data = json.loads(input_path.read_text(encoding="utf-8"))
        dataset = normalize_dataset(data, source=data.get("source") or str(input_path))
        output = (
            Path(args.output).expanduser().resolve()
            if args.output
            else Path.cwd() / "docs" / "generated" / "excel-workbook-builder" / f"{template_id}.xlsx"
        )
        fill_workbook_from_dataset(
            source_template,
            dataset,
            output,
            data_sheet="Data",
        )
        print(f"Workbook gerado: {output}")
        print(f"Template: {template_id} {version}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
