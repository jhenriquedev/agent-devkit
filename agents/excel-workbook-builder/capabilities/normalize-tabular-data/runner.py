#!/usr/bin/env python3
"""Runner for excel-workbook-builder/normalize-tabular-data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from workbook_support import load_tabular_file, normalize_column_names, normalize_dataset  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize tabular data")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    parser.add_argument("--slug-columns", action="store_true")
    args = parser.parse_args()

    try:
        source = Path(args.input).expanduser().resolve()
        if not source.exists():
            raise ValueError(f"input not found: {source}")
        dataset = load_tabular_file(source)
        payload = normalize_column_names(dataset) if args.slug_columns else normalize_dataset(dataset)
        output = (
            Path(args.output).expanduser().resolve()
            if args.output
            else source.with_suffix(".normalized.json")
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Dados normalizados: {output}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

