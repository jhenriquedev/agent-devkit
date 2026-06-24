#!/usr/bin/env python3
"""TOPdesk repository using Python stdlib and curl."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class TopdeskRepositoryError(RuntimeError):
    """Raised when TOPdesk returns an error or env config is missing."""


@dataclass(frozen=True)
class TopdeskConfig:
    base_url: str
    username: str
    app_password: str

    @classmethod
    def from_env(cls) -> "TopdeskConfig":
        load_dotenv()
        password = os.environ.get("TOPDESK_APP_PASSWORD") or os.environ.get("TOPDESK_PASSWORD")
        missing = [
            name
            for name, value in (
                ("TOPDESK_BASE_URL", os.environ.get("TOPDESK_BASE_URL")),
                ("TOPDESK_USERNAME", os.environ.get("TOPDESK_USERNAME")),
                ("TOPDESK_APP_PASSWORD", password),
            )
            if not value
        ]
        if missing:
            raise TopdeskRepositoryError(f"Missing env vars: {', '.join(missing)}")
        return cls(
            base_url=os.environ["TOPDESK_BASE_URL"].rstrip("/"),
            username=os.environ["TOPDESK_USERNAME"],
            app_password=password or "",
        )


class TopdeskRepository:
    """Small TOPdesk incident repository for local execution."""

    def __init__(self, config: TopdeskConfig | None = None) -> None:
        self.config = config or TopdeskConfig.from_env()

    def list_incidents(
        self,
        *,
        query: str | None = None,
        status: str | None = None,
        operator_group: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        params: dict[str, str] = {"page_size": str(limit)}
        if query:
            params["query"] = query
        if status:
            params["status"] = status
        if operator_group:
            params["operatorGroup"] = operator_group
        result = self._request("GET", "/incidents", query=params)
        items = result if isinstance(result, list) else result.get("data", [])
        return {
            "count": len(items),
            "items": [self._normalize_incident(item) for item in items[:limit]],
            "query": params,
        }

    def get_incident(
        self,
        *,
        incident_id: str | None = None,
        number: str | None = None,
    ) -> dict[str, Any]:
        if incident_id:
            result = self._request("GET", f"/incidents/id/{urllib.parse.quote(incident_id)}")
        elif number:
            result = self._request("GET", f"/incidents/number/{urllib.parse.quote(number)}")
        else:
            raise TopdeskRepositoryError("incident_id or number is required")
        return self._normalize_incident(result)

    def get_progress_trail(
        self,
        *,
        incident_id: str | None = None,
        number: str | None = None,
    ) -> dict[str, Any]:
        if incident_id:
            path = f"/incidents/id/{urllib.parse.quote(incident_id)}/progresstrail"
        elif number:
            path = f"/incidents/number/{urllib.parse.quote(number)}/progresstrail"
        else:
            raise TopdeskRepositoryError("incident_id or number is required")
        result = self._request("GET", path)
        entries = result if isinstance(result, list) else result.get("data", [])
        return {"count": len(entries), "entries": entries}

    def create_incident(self, fields: dict[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
        if dry_run:
            return {"dry_run": True, "operation": "create_incident", "fields": fields}
        result = self._request("POST", "/incidents", body=fields)
        return {"dry_run": False, "incident": self._normalize_incident(result)}

    def update_incident(
        self,
        fields: dict[str, Any],
        *,
        incident_id: str | None = None,
        number: str | None = None,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        if not incident_id and not number:
            raise TopdeskRepositoryError("incident_id or number is required")
        path = (
            f"/incidents/id/{urllib.parse.quote(incident_id)}"
            if incident_id
            else f"/incidents/number/{urllib.parse.quote(number or '')}"
        )
        if dry_run:
            return {
                "dry_run": True,
                "operation": "update_incident",
                "target": incident_id or number,
                "fields": fields,
            }
        result = self._request("PATCH", path, body=fields)
        return {"dry_run": False, "incident": self._normalize_incident(result)}

    def get_catalog(self, catalog: str) -> dict[str, Any]:
        allowed = {"categories", "subcategories", "impacts", "urgencies", "priorities", "statuses"}
        if catalog not in allowed:
            raise TopdeskRepositoryError(f"unsupported catalog: {catalog}")
        result = self._request("GET", f"/incidents/{catalog}")
        items = result if isinstance(result, list) else result.get("data", [])
        return {"catalog": catalog, "count": len(items), "items": items}

    def search_persons(self, query: str | None = None, *, limit: int = 20) -> dict[str, Any]:
        params = {"page_size": str(limit)}
        if query:
            params["query"] = query
        result = self._request("GET", "/persons", query=params)
        items = result if isinstance(result, list) else result.get("data", [])
        return {"count": len(items), "items": items[:limit]}

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, str] | None = None,
        body: Any | None = None,
    ) -> Any:
        url = self._url(path, query)
        timeout_seconds = request_timeout_seconds("TOPDESK_REQUEST_TIMEOUT_SECONDS")
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as curl_config, tempfile.NamedTemporaryFile("w+b") as response_file:
            curl_config.write(f'user = "{curl_config_value(self.config.username + ":" + self.config.app_password)}"\n')
            curl_config.flush()
            command = [
                "curl",
                "-sS",
                "--config",
                curl_config.name,
                "--max-time",
                str(timeout_seconds),
                "-X",
                method,
                "-H",
                "Accept: application/json",
                "-o",
                response_file.name,
                "-w",
                "%{http_code}",
            ]
            if body is not None:
                command.extend(["-H", "Content-Type: application/json", "--data", json.dumps(body)])
            command.append(url)
            try:
                result = subprocess.run(
                    command,
                    check=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout_seconds + 5,
                )
            except subprocess.TimeoutExpired as exc:
                raise TopdeskRepositoryError(f"TOPdesk curl timed out after {timeout_seconds}s") from exc
            raw = response_file.read().decode("utf-8-sig", errors="replace")
        if result.returncode != 0:
            raise TopdeskRepositoryError(f"TOPdesk curl failed: {result.stderr.strip()}")
        status_text = result.stdout.strip()
        status = int(status_text) if status_text.isdigit() else 0
        if status >= 400 or status == 0:
            raise TopdeskRepositoryError(f"TOPdesk HTTP {status}: {raw}")
        return json.loads(raw) if raw.strip() else {}

    def _url(self, path: str, query: dict[str, str] | None = None) -> str:
        normalized_path = path if path.startswith("/") else f"/{path}"
        url = f"{self.config.base_url}/tas/api{normalized_path}"
        if query:
            clean = {key: value for key, value in query.items() if value not in (None, "")}
            if clean:
                url = f"{url}?{urllib.parse.urlencode(clean)}"
        return url

    @staticmethod
    def _normalize_incident(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item.get("id"),
            "number": item.get("number") or item.get("incidentNumber"),
            "brief_description": item.get("briefDescription") or item.get("brief_description"),
            "request": item.get("request"),
            "status": lookup_name(item.get("status")) or item.get("statusName") or item.get("status"),
            "category": lookup_name(item.get("category")) or item.get("categoryName"),
            "subcategory": lookup_name(item.get("subcategory")) or item.get("subcategoryName"),
            "priority": lookup_name(item.get("priority")) or item.get("priorityName"),
            "operator": lookup_name(item.get("operator")) or item.get("operatorName"),
            "operator_group": lookup_name(item.get("operatorGroup")) or item.get("operatorGroupName"),
            "caller": lookup_name(item.get("caller")) or item.get("callerName"),
            "creation_date": item.get("creationDate") or item.get("creation_date"),
            "modification_date": item.get("modificationDate") or item.get("modification_date"),
            "raw": item,
        }


def lookup_name(value: Any) -> str:
    if isinstance(value, dict):
        name = value.get("name")
        return name if isinstance(name, str) else ""
    return value if isinstance(value, str) else ""


def request_timeout_seconds(env_name: str) -> int:
    raw = os.environ.get(env_name, "30")
    return int(raw) if raw.isdigit() and int(raw) > 0 else 30


def curl_config_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def load_dotenv() -> None:
    for candidate in _dotenv_candidates():
        if not candidate.exists():
            continue
        for raw_line in candidate.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
        return


def _dotenv_candidates() -> list[Path]:
    paths = []
    for start in (Path.cwd(), Path(__file__).resolve()):
        current = start if start.is_dir() else start.parent
        paths.extend(parent / ".env" for parent in [current, *current.parents])
    seen = set()
    unique = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique
