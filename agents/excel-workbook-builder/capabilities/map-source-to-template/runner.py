#!/usr/bin/env python3
"""Runner for excel-workbook-builder/map-source-to-template."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Map source schema to template fields")
    parser.add_argument("--source-schema", required=True)
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--field", action="append", default=[])
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        schema = json.loads(Path(args.source_schema).expanduser().resolve().read_text(encoding="utf-8"))
        columns = schema.get("columns", [])
        mappings = []
        for item in args.field:
            if "=" not in item:
                raise ValueError("--field must use source=target")
            source, target = item.split("=", 1)
            mappings.append({"source": source.strip(), "target": target.strip()})
        mapped_sources = {item["source"] for item in mappings}
        unmapped = [column for column in columns if column not in mapped_sources]
        lines = [
            f"template_id: {args.template_id}",
            "mappings:",
        ]
        for item in mappings:
            lines.append(f"  - source: {item['source']}")
            lines.append(f"    target: {item['target']}")
        lines.append("unmapped_columns:")
        for column in unmapped:
            lines.append(f"  - {column}")
        content = "\n".join(lines) + "\n"
        if args.output:
            output = Path(args.output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(content, encoding="utf-8")
        else:
            print(content)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

