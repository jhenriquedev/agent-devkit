"""GitHub PR reviewer MVP using the GitHub CLI."""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

from cli.aikit.memory import redact_secrets
from cli.aikit.permissions import permission_check
from cli.aikit.tasks import create_task


GH_TIMEOUT_SECONDS = 120


def pr_list_review_requests() -> dict[str, Any]:
    check = gh_check()
    if check["status"] != "ok":
        return check
    result = run_gh(["pr", "list", "--review-requested", "@me", "--json", "number,title,url,author,headRefName,baseRefName,isDraft"])
    if result["status"] != "ok":
        return result
    prs = parse_json_list(result["stdout"])
    return {"kind": "pr", "status": "ok", "mode": "report-only", "items": prs, "count": len(prs), "provider": "github"}


def pr_inspect(pr_ref: str) -> dict[str, Any]:
    check = gh_check()
    if check["status"] != "ok":
        return check
    result = run_gh(["pr", "view", pr_ref, "--json", "number,title,url,author,body,headRefName,baseRefName,state,isDraft,reviewDecision,mergeable"])
    if result["status"] != "ok":
        return result
    return {"kind": "pr", "status": "ok", "mode": "report-only", "item": parse_json_object(result["stdout"]), "provider": "github"}


def pr_review(
    pr_ref: str,
    *,
    approve: bool = False,
    request_changes: bool = False,
    comment: str | None = None,
    allow_write: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    action = pr_write_action(approve=approve, request_changes=request_changes, comment=comment)
    if (approve or request_changes or comment) and not allow_write:
        return {
            "kind": "pr-review",
            "status": "blocked",
            "ok": False,
            "mode": "report-only",
            "requires_permission": True,
            "message": "PR write actions require explicit opt-in with --allow-write.",
            "exit_code": 2,
        }
    permission = None
    if action:
        permission = permission_check(agent="github-pr-reviewer", provider="github", action=action)
        if dry_run:
            return {
                "kind": "pr-review",
                "status": "planned",
                "ok": True,
                "dry_run": True,
                "mode": "write-plan" if allow_write else "report-only",
                "provider": "github",
                "pr_ref": pr_ref,
                "permission": permission,
                "external_action": pr_external_action(pr_ref, approve=approve, request_changes=request_changes, comment=comment),
                "summary": "Dry-run only. No PR comments, approvals or request-changes were submitted.",
            }
        if not permission["ok"]:
            return {
                "kind": "pr-review",
                "status": "blocked",
                "ok": False,
                "mode": "write-opt-in",
                "requires_permission": True,
                "permission": permission,
                "message": "PR write action is above the configured permission level.",
                "exit_code": 2,
            }
    elif dry_run:
        return {
            "kind": "pr-review",
            "status": "planned",
            "ok": True,
            "dry_run": True,
            "mode": "report-only",
            "provider": "github",
            "pr_ref": pr_ref,
            "summary": "Dry-run only. PR diff would be loaded for report-only review.",
        }
    if action and not allow_write:
        return {
            "kind": "pr-review",
            "status": "blocked",
            "ok": False,
            "mode": "write-opt-in",
            "requires_permission": True,
            "message": "PR write execution is reserved for the permissions layer. No comments, approvals or request-changes were submitted.",
            "exit_code": 2,
        }
    check = gh_check()
    if check["status"] != "ok":
        return check
    if action:
        review_result = run_gh(pr_review_args(pr_ref, approve=approve, request_changes=request_changes, comment=comment))
        if review_result["status"] != "ok":
            return review_result
        return {
            "kind": "pr-review",
            "status": "ok",
            "ok": True,
            "mode": "write-opt-in",
            "provider": "github",
            "pr_ref": pr_ref,
            "permission": permission,
            "external_action": pr_external_action(pr_ref, approve=approve, request_changes=request_changes, comment=comment),
            "summary": "PR review action submitted through gh.",
        }
    view = pr_inspect(pr_ref)
    if view.get("status") != "ok":
        return view
    diff_result = run_gh(["pr", "diff", pr_ref])
    if diff_result["status"] != "ok":
        return diff_result
    return {
        "kind": "pr-review",
        "status": "ok",
        "ok": True,
        "mode": "report-only" if not allow_write else "write-opt-in",
        "provider": "github",
        "pr": view.get("item"),
        "diff_available": bool(diff_result.get("stdout")),
        "summary": "PR diff loaded for report-only review. No comments, approvals or request-changes were submitted.",
    }


def pr_write_action(*, approve: bool, request_changes: bool, comment: str | None) -> str | None:
    if approve or request_changes:
        return "approve" if approve else "request-changes"
    if comment:
        return "comment"
    return None


def pr_review_args(pr_ref: str, *, approve: bool, request_changes: bool, comment: str | None) -> list[str]:
    args = ["pr", "review", pr_ref]
    if approve:
        args.append("--approve")
    elif request_changes:
        args.append("--request-changes")
    else:
        args.append("--comment")
    if comment:
        args.extend(["--body", comment])
    return args


def pr_external_action(pr_ref: str, *, approve: bool, request_changes: bool, comment: str | None) -> dict[str, Any]:
    return {
        "provider": "github",
        "agent": "github-pr-reviewer",
        "pr_ref": pr_ref,
        "action": pr_write_action(approve=approve, request_changes=request_changes, comment=comment),
        "comment": bool(comment),
        "approve": approve,
        "request_changes": request_changes,
    }


def pr_create_automation(*, task_id: str | None = None, title: str | None = None, time: str = "09:00") -> dict[str, Any]:
    task = create_task(
        task_id=task_id or "daily-pr-review",
        title=title or "Revisar PRs pendentes diariamente",
        prompt="revise todas as prs que recebo diariamente",
        schedule={"type": "daily", "time": time},
        action={"type": "capability", "agent": "github-pr-reviewer", "capability": "list-review-requests", "external_writes": False},
        permissions={"mode": "report-only", "comment": False, "approve": False, "request_changes": False},
        notifications=[{"type": "terminal"}],
    )
    task["kind"] = "pr-automation"
    task["mode"] = "report-only"
    return task


def gh_check() -> dict[str, Any]:
    binary = shutil.which("gh")
    if not binary:
        return {
            "kind": "pr",
            "status": "needs-setup",
            "ok": False,
            "provider": "github",
            "message": "GitHub CLI `gh` was not found in PATH.",
            "next_steps": ["Run `agent toolchain install gh-cli --dry-run`.", "Authenticate with `gh auth login`."],
            "exit_code": 2,
        }
    return {"kind": "pr", "status": "ok", "binary": binary}


def run_gh(args: list[str]) -> dict[str, Any]:
    try:
        process = subprocess.run(
            ["gh", *args],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=GH_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "kind": "pr",
            "status": "failed",
            "ok": False,
            "provider": "github",
            "command": ["gh", *args],
            "message": redact_secrets((stderr or stdout or f"gh command timed out after {GH_TIMEOUT_SECONDS}s").strip()),
            "exit_code": 124,
        }
    if process.returncode != 0:
        return {
            "kind": "pr",
            "status": "failed",
            "ok": False,
            "provider": "github",
            "command": ["gh", *args],
            "message": redact_secrets((process.stderr or process.stdout or "gh command failed").strip()),
            "exit_code": process.returncode,
        }
    return {"kind": "pr", "status": "ok", "stdout": process.stdout}


def parse_json_list(value: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []


def parse_json_object(value: str) -> dict[str, Any]:
    try:
        payload = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}
