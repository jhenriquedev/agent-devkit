#!/usr/bin/env python3
"""Runner for excel-workbook-builder/ingest-workbook-data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from workbook_support import read_xlsx_dataset  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest data from an Excel workbook")
    parser.add_argument("--workbook", required=True)
    parser.add_argument("--sheet")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        workbook = Path(args.workbook).expanduser().resolve()
        if not workbook.exists():
            raise ValueError(f"workbook not found: {workbook}")
        payload = read_xlsx_dataset(workbook, args.sheet)
        output = (
            Path(args.output).expanduser().resolve()
            if args.output
            else workbook.with_suffix(".extracted.json")
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Dados extraidos: {output}")
        print(f"Linhas: {payload['row_count']}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

