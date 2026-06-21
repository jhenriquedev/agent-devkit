#!/usr/bin/env python3
"""Controlled HTTP execution for technical integration tests."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class HttpApiRepositoryError(RuntimeError):
    """Raised when HTTP integration execution is unsafe or fails."""


SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class HttpApiRepository:
    """Execute HTTP operations with explicit dry-run and mutation controls."""

    def run_tests(
        self,
        *,
        contract: dict[str, Any],
        base_url: str | None = None,
        execute: bool = False,
        confirm_mutations: bool = False,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        resolved_base_url = base_url or contract.get("base_url") or os.environ.get("TECH_INTEGRATION_DEFAULT_BASE_URL")
        operations = [operation for operation in contract.get("operations") or [] if operation.get("method")]
        has_mutations = any(operation.get("method") not in SAFE_METHODS for operation in operations)
        if execute and not resolved_base_url:
            raise HttpApiRepositoryError("base_url is required for real execution")
        if execute and has_mutations and not confirm_mutations:
            raise HttpApiRepositoryError("--confirm-mutations is required to execute mutations")

        results = []
        for operation in operations:
            if not execute:
                results.append({"operation": label(operation), "status": "dry-run", "mutation": operation.get("method") not in SAFE_METHODS})
                continue
            results.append(self._execute_operation(operation, resolved_base_url or "", timeout or default_timeout()))
        return {"execute": execute, "base_url": resolved_base_url, "results": results}

    def _execute_operation(self, operation: dict[str, Any], base_url: str, timeout: int) -> dict[str, Any]:
        method = operation.get("method") or "GET"
        url = base_url.rstrip("/") + "/" + str(operation.get("path") or "/").lstrip("/")
        data = None
        headers = {"Accept": "application/json"}
        token = os.environ.get("TECH_INTEGRATION_DEFAULT_AUTH_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if method not in SAFE_METHODS:
            headers["Content-Type"] = "application/json"
            data = json.dumps(operation.get("body_example") or {}).encode("utf-8")
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec - explicit user execution.
                body = response.read().decode("utf-8-sig", errors="replace")
                return {"operation": label(operation), "status": response.status, "body_preview": body[:500]}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8-sig", errors="replace")
            return {"operation": label(operation), "status": exc.code, "body_preview": body[:500]}


def default_timeout() -> int:
    raw = os.environ.get("TECH_INTEGRATION_HTTP_TIMEOUT", "30")
    return int(raw) if raw.isdigit() else 30


def label(operation: dict[str, Any]) -> str:
    return f"{operation.get('method')} {operation.get('path')}"
