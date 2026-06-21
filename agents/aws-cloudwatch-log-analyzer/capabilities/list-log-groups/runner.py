#!/usr/bin/env python3
"""Runner for list-log-groups."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import get_repository, load_fixture, print_error, value_or_dash, write_output  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run aws-cloudwatch-log-analyzer/list-log-groups")
    parser.add_argument("--region")
    parser.add_argument("--log-group-prefix")
    parser.add_argument("--service")
    parser.add_argument("--environment")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        payload = load_payload(args)
        write_output(render(payload, args), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def load_payload(args: argparse.Namespace) -> dict:
    if args.fixture:
        return load_fixture(args.fixture)
    if not args.region:
        raise ValueError("--region is required when --fixture is not provided")
    return get_repository().list_log_groups(
        region=args.region,
        log_group_prefix=args.log_group_prefix,
        limit=args.limit,
    )


def render(payload: dict, args: argparse.Namespace) -> str:
    groups = payload.get("log_groups") or payload.get("logGroups") or []
    lines = [
        "# Log Groups",
        "",
        "## Consulta",
        "",
        f"- Regiao: {value_or_dash(payload.get('region') or args.region)}",
        f"- Prefixo: {value_or_dash(args.log_group_prefix)}",
        f"- Servico: {value_or_dash(args.service)}",
        f"- Ambiente: {value_or_dash(args.environment)}",
        f"- Limite: {value_or_dash(args.limit)}",
        f"- Total retornado: {len(groups)}",
        "",
        "## Resultados",
        "",
        "| Log group | Retention | Stored bytes |",
        "|---|---|---|",
    ]
    for group in groups:
        lines.append(
            "| "
            + " | ".join(
                [
                    value_or_dash(group.get("log_group_name") or group.get("logGroupName")),
                    value_or_dash(group.get("retention_in_days") or group.get("retentionInDays")),
                    value_or_dash(group.get("stored_bytes") or group.get("storedBytes")),
                ]
            )
            + " |"
        )
    if not groups:
        lines.append("| - | - | - |")
    if not args.log_group_prefix:
        lines.extend(["", "## Avisos", "", "- Nenhum prefixo informado; a consulta pode ser ampla."])
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
