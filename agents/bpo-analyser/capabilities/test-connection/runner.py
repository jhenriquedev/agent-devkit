#!/usr/bin/env python3
"""Runner for bpo-analyser/test-connection."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import get_repository, load_fixture, print_error, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run bpo-analyser/test-connection")
    parser.add_argument("--network", action="store_true")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        payload = load_fixture(args.fixture) if args.fixture else get_repository().test_connection(
            network=args.network
        )
        write_output(render(payload), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def render(payload: dict) -> str:
    lines = [
        "# Diagnostico BPO",
        "",
        f"- Configurado: {value_or_dash(payload.get('configured'))}",
        f"- Usuario configurado: {value_or_dash(payload.get('user_configured'))}",
        f"- Senha configurada: {value_or_dash(payload.get('password_configured'))}",
        f"- Timeout: {value_or_dash(payload.get('timeout'))}",
        f"- Tipo de documento padrao: {value_or_dash(payload.get('default_document_type'))}",
        f"- TLS verify: {value_or_dash(payload.get('tls_verify'))}",
        "",
        "## Endpoints",
        "",
        "| Endpoint | Configurado | URL | Rede |",
        "|---|---|---|---|",
    ]
    for name, endpoint in (payload.get("endpoints") or {}).items():
        network = endpoint.get("network")
        if isinstance(network, dict):
            network_text = "ok" if network.get("ok") else value_or_dash(network.get("error"))
        else:
            network_text = "-"
        lines.append(
            f"| {name} | {value_or_dash(endpoint.get('configured'))} | "
            f"{value_or_dash(endpoint.get('url'))} | {network_text} |"
        )
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
