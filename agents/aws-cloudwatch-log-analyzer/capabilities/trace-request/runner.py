#!/usr/bin/env python3
"""Runner for trace-request."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import (  # noqa: E402
    event_message,
    get_events,
    is_error_event,
    load_events_payload,
    print_error,
    render_events_table,
    sort_events,
    value_or_dash,
    write_output,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run aws-cloudwatch-log-analyzer/trace-request")
    parser.add_argument("--region")
    parser.add_argument("--log-group")
    parser.add_argument("--start-time")
    parser.add_argument("--end-time")
    parser.add_argument("--identifier", required=False)
    parser.add_argument("--identifier-type", default="identifier")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        if args.identifier and is_sensitive_identifier(args.identifier):
            raise ValueError("sensitive identifier must be replaced by a technical request id, correlation id or masked value")
        if not args.identifier and not args.fixture:
            raise ValueError("--identifier is required when --fixture is not provided")
        payload = load_events_payload(args)
        write_output(render(payload, args), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def render(payload: dict, args: argparse.Namespace) -> str:
    identifier = args.identifier or payload.get("identifier")
    events = [
        event
        for event in get_events(payload)
        if not identifier or identifier in event_message(event)
    ]
    events = sort_events(events)
    rendered_events = [mask_event(event) for event in events]
    error_count = sum(1 for event in events if is_error_event(event))
    lines = [
        "# Request Trace",
        "",
        "## Identificador",
        "",
        f"- Tipo: {value_or_dash(args.identifier_type or payload.get('identifier_type'))}",
        f"- Valor: {value_or_dash(mask_sensitive_text(identifier))}",
        f"- Eventos encontrados: {len(events)}",
        f"- Eventos com erro: {error_count}",
        "",
        "## Timeline",
        "",
        *render_events_table(rendered_events, limit=args.limit),
        "",
        "## Lacunas",
        "",
        "- Validar se outros log groups tambem participam do fluxo.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def mask_event(event: dict) -> dict:
    masked = dict(event)
    masked["message"] = mask_sensitive_text(event.get("message"))
    return masked


def is_sensitive_identifier(value: str) -> bool:
    text = value.strip()
    return any(
        [
            bool(EMAIL_RE.search(text)),
            bool(CPF_RE.search(text)),
            bool(JWT_RE.search(text)),
            bool(SECRET_RE.search(text)),
            len(text) > 80,
        ]
    )


def mask_sensitive_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = EMAIL_RE.sub(mask_email_match, text)
    text = CPF_RE.sub("***.***.***-**", text)
    text = JWT_RE.sub("<jwt-masked>", text)
    text = SECRET_RE.sub(r"\1=<masked>", text)
    return text


def mask_email_match(match: re.Match[str]) -> str:
    local = match.group("local")
    domain = match.group("domain")
    prefix = local[:1] if local else "*"
    return f"{prefix}***@{domain}"


EMAIL_RE = re.compile(r"(?P<local>[A-Za-z0-9._%+-]+)@(?P<domain>[A-Za-z0-9.-]+\.[A-Za-z]{2,})")
CPF_RE = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
SECRET_RE = re.compile(r"\b(token|secret|password|authorization)\s*[:=]\s*[^,\s;]+", re.IGNORECASE)


if __name__ == "__main__":
    raise SystemExit(main())
