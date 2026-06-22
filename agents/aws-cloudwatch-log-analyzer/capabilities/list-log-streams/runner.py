#!/usr/bin/env python3
"""Runner for list-log-streams."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import get_repository, load_fixture, print_error, value_or_dash, write_output  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run aws-cloudwatch-log-analyzer/list-log-streams")
    parser.add_argument("--region")
    parser.add_argument("--log-group")
    parser.add_argument("--log-stream-prefix")
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
    if not args.log_group:
        raise ValueError("--log-group is required when --fixture is not provided")
    return get_repository().describe_log_streams(
        region=args.region,
        log_group=args.log_group,
        log_stream_prefix=args.log_stream_prefix,
        limit=args.limit,
    )


def render(payload: dict, args: argparse.Namespace) -> str:
    streams = payload.get("log_streams") or payload.get("logStreams") or []
    lines = [
        "# Log Streams",
        "",
        "## Consulta",
        "",
        f"- Regiao: {value_or_dash(payload.get('region') or args.region)}",
        f"- Log group: {value_or_dash(payload.get('log_group') or args.log_group)}",
        f"- Prefixo do stream: {value_or_dash(args.log_stream_prefix)}",
        f"- Limite: {value_or_dash(args.limit)}",
        f"- Total retornado: {len(streams)}",
        "",
        "## Resultados",
        "",
        "| Log stream | Last event | Stored bytes |",
        "|---|---|---|",
    ]
    for stream in streams:
        lines.append(
            "| "
            + " | ".join(
                [
                    value_or_dash(stream.get("log_stream_name") or stream.get("logStreamName")),
                    value_or_dash(stream.get("last_event_timestamp") or stream.get("lastEventTimestamp")),
                    value_or_dash(stream.get("stored_bytes") or stream.get("storedBytes")),
                ]
            )
            + " |"
        )
    if not streams:
        lines.append("| - | - | - |")
    if not args.log_stream_prefix:
        lines.extend(["", "## Avisos", "", "- Nenhum prefixo informado; a listagem pode retornar streams de fluxos distintos."])
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
