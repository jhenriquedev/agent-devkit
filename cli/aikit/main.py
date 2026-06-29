#!/usr/bin/env python3
"""AI DevKit public command line entrypoint."""

from __future__ import annotations

import json
import os
import sys
import traceback

from cli.aikit.cli_dispatch import dispatch, format_audit_warning, is_audit_warning, maybe_record_cli_audit
from cli.aikit.cli_parser import DETERMINISTIC_COMMANDS, LLM_COMMANDS, build_parser
from cli.aikit.errors import DevKitError
from cli.aikit.human_output import print_human
from cli.aikit.interactive_wizard import maybe_run_interactive_wizard


def main(argv: list[str] | None = None, *, prog: str | None = None) -> int:
    parser = build_parser(prog=prog)
    args = parser.parse_args(argv)
    args.prog_name = prog or "aikit"

    try:
        result = dispatch(args)
    except DevKitError as exc:
        audit_result = maybe_record_cli_audit(args, result=None, error=str(exc))
        if is_audit_warning(audit_result):
            print(format_audit_warning(audit_result), file=sys.stderr)
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - CLI boundary must not leak tracebacks by default.
        if os.environ.get("AI_DEVKIT_DEBUG") == "1":
            traceback.print_exc(file=sys.stderr)
        else:
            print(
                f"error: internal error: {type(exc).__name__}. "
                "Run with AI_DEVKIT_DEBUG=1 for traceback.",
                file=sys.stderr,
            )
        audit_result = maybe_record_cli_audit(args, result=None, error=f"{type(exc).__name__}: {exc}")
        if is_audit_warning(audit_result):
            print(format_audit_warning(audit_result), file=sys.stderr)
        return 1

    if result is None:
        return 0
    if not getattr(args, "json", False):
        result = maybe_run_interactive_wizard(result)
    maybe_record_cli_audit(args, result=result, error=None)

    if getattr(args, "json", False):
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human(result)
    if "exit_code" in result:
        return int(result["exit_code"])
    if result.get("kind") == "doctor" and result.get("errors"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
