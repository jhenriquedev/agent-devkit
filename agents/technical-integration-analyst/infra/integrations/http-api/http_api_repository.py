#!/usr/bin/env python3
"""Controlled HTTP execution for technical integration tests."""

from __future__ import annotations

import ipaddress
import json
import os
import socket
import urllib.error
import urllib.parse
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
        allowed_hosts: list[str] | None = None,
    ) -> dict[str, Any]:
        resolved_base_url = base_url or contract.get("base_url") or os.environ.get("TECH_INTEGRATION_DEFAULT_BASE_URL")
        operations = [operation for operation in contract.get("operations") or [] if operation.get("method")]
        has_mutations = any(operation.get("method") not in SAFE_METHODS for operation in operations)
        if execute and not resolved_base_url:
            raise HttpApiRepositoryError("base_url is required for real execution")
        if execute and has_mutations and not confirm_mutations:
            raise HttpApiRepositoryError("--confirm-mutations is required to execute mutations")
        if execute:
            validate_base_url(resolved_base_url or "", resolve_allowed_hosts(allowed_hosts))

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


def resolve_allowed_hosts(allowed_hosts: list[str] | None) -> list[str]:
    values = list(allowed_hosts or [])
    env_value = os.environ.get("TECH_INTEGRATION_ALLOWED_HOSTS", "")
    values.extend(item.strip() for item in env_value.split(",") if item.strip())
    return [item.lower() for item in values if item.strip()]


def validate_base_url(base_url: str, allowed_hosts: list[str]) -> None:
    if not allowed_hosts:
        raise HttpApiRepositoryError("--allow-host or TECH_INTEGRATION_ALLOWED_HOSTS is required for real execution")

    parsed = urllib.parse.urlparse(base_url)
    if parsed.scheme not in allowed_schemes():
        raise HttpApiRepositoryError(f"URL scheme not allowed: {parsed.scheme or '<empty>'}")

    host = (parsed.hostname or "").lower()
    if not host:
        raise HttpApiRepositoryError("base_url host is required for real execution")
    if not host_allowed(host, allowed_hosts):
        raise HttpApiRepositoryError(f"base_url host is not allowlisted: {host}")
    if is_blocked_host(host):
        raise HttpApiRepositoryError(f"base_url host is not allowed: {host}")

    for address in resolve_host_addresses(host, parsed.port):
        if is_blocked_ip(address):
            raise HttpApiRepositoryError(f"base_url resolved to blocked address: {address}")


def allowed_schemes() -> set[str]:
    schemes = {"https"}
    if os.environ.get("TECH_INTEGRATION_ALLOW_HTTP", "").strip().lower() in {"1", "true", "yes", "on"}:
        schemes.add("http")
    return schemes


def host_allowed(host: str, allowed_hosts: list[str]) -> bool:
    for allowed in allowed_hosts:
        if allowed.startswith("*.") and host.endswith(allowed[1:]) and host != allowed[2:]:
            return True
        if host == allowed:
            return True
    return False


def is_blocked_host(host: str) -> bool:
    if host in {"localhost", "metadata.google.internal"}:
        return True
    try:
        return is_blocked_ip(ipaddress.ip_address(host))
    except ValueError:
        return False


def resolve_host_addresses(host: str, port: int | None) -> list[ipaddress._BaseAddress]:
    addresses = []
    try:
        infos = socket.getaddrinfo(host, port or 443, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return addresses
    for info in infos:
        sockaddr = info[4]
        if not sockaddr:
            continue
        try:
            addresses.append(ipaddress.ip_address(sockaddr[0]))
        except ValueError:
            continue
    return addresses


def is_blocked_ip(address: ipaddress._BaseAddress) -> bool:
    metadata = ipaddress.ip_address("169.254.169.254")
    return (
        address == metadata
        or address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def label(operation: dict[str, Any]) -> str:
    return f"{operation.get('method')} {operation.get('path')}"
