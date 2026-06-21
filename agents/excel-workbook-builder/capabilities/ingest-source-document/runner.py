#!/usr/bin/env python3
"""Runner for excel-workbook-builder/ingest-source-document."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from workbook_support import load_tabular_file  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest a source document into normalized JSON")
    parser.add_argument("--source", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        source = Path(args.source).expanduser().resolve()
        if not source.exists():
            raise ValueError(f"source not found: {source}")
        payload = load_tabular_file(source)
        output = (
            Path(args.output).expanduser().resolve()
            if args.output
            else source.with_suffix(".extracted.json")
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Dados extraidos: {output}")
        print(f"Linhas: {payload['row_count']}")
        print(f"Colunas: {', '.join(payload['columns']) if payload['columns'] else '-'}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

