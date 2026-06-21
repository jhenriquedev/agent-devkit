#!/usr/bin/env python3
"""Runner for excel-workbook-builder/generate-workbook-from-data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from workbook_support import generate_workbook_from_dataset, normalize_dataset  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Excel workbook from normalized data")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    parser.add_argument("--title", default="Workbook")
    args = parser.parse_args()

    try:
        input_path = Path(args.input).expanduser().resolve()
        if not input_path.exists():
            raise ValueError(f"input not found: {input_path}")
        data = json.loads(input_path.read_text(encoding="utf-8"))
        dataset = normalize_dataset(data, source=data.get("source") or str(input_path))
        output = (
            Path(args.output).expanduser().resolve()
            if args.output
            else Path.cwd() / "docs" / "generated" / "excel-workbook-builder" / "workbook.xlsx"
        )
        generate_workbook_from_dataset(dataset, output, title=args.title)
        print(f"Workbook gerado: {output}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

