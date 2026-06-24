#!/usr/bin/env python3
"""Azure DevOps repository using only Python stdlib."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


class AzureRepositoryError(RuntimeError):
    """Raised when Azure DevOps returns an error or env config is missing."""


@dataclass(frozen=True)
class AzureConfig:
    org: str
    pat: str
    default_project: str | None = None
    api_version: str = "7.1"

    @classmethod
    def from_env(cls) -> "AzureConfig":
        load_dotenv()
        missing = [
            name
            for name in ("AZURE_DEVOPS_ORG", "AZURE_DEVOPS_PAT")
            if not os.environ.get(name)
        ]
        if missing:
            raise AzureRepositoryError(f"Missing env vars: {', '.join(missing)}")

        return cls(
            org=normalize_org(os.environ["AZURE_DEVOPS_ORG"]),
            pat=os.environ["AZURE_DEVOPS_PAT"],
            default_project=os.environ.get("AZURE_DEVOPS_PROJECT") or None,
            api_version=os.environ.get("AZURE_DEVOPS_API_VERSION", "7.1"),
        )


class AzureRepository:
    """Small Azure DevOps Boards repository for local, serverless execution."""

    def __init__(self, config: AzureConfig | None = None) -> None:
        self.config = config or AzureConfig.from_env()

    def list_work_items(
        self,
        *,
        project: str | None = None,
        wiql: str | None = None,
        state: str | None = None,
        assigned_to: str | None = None,
        tags: list[str] | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        resolved_project = self._resolve_project(project)
        query = wiql or self._build_wiql(
            project=resolved_project,
            state=state,
            assigned_to=assigned_to,
            tags=tags,
        )
        result = self._request(
            "POST",
            resolved_project,
            "_apis/wit/wiql",
            body={"query": query},
        )
        ids = [item["id"] for item in result.get("workItems", [])[:limit]]
        if not ids:
            return {"count": 0, "items": [], "wiql": query}

        fields = [
            "System.Id",
            "System.WorkItemType",
            "System.Title",
            "System.State",
            "System.AssignedTo",
            "System.Tags",
        ]
        work_items = self._request(
            "GET",
            resolved_project,
            "_apis/wit/workitems",
            query={
                "ids": ",".join(str(item_id) for item_id in ids),
                "fields": ",".join(fields),
            },
        )
        return {
            "count": len(work_items.get("value", [])),
            "items": [self._normalize_work_item(item) for item in work_items.get("value", [])],
            "wiql": query,
        }

    def get_work_item(
        self,
        work_item_id: int,
        *,
        project: str | None = None,
        fields: list[str] | None = None,
        expand_relations: bool = False,
    ) -> dict[str, Any]:
        query: dict[str, str] = {}
        if fields:
            query["fields"] = ",".join(fields)
        if expand_relations:
            query["$expand"] = "Relations"

        result = self._request(
            "GET",
            self._resolve_project(project),
            f"_apis/wit/workitems/{work_item_id}",
            query=query,
        )
        return self._normalize_work_item(result)

    def get_work_item_comments(
        self,
        work_item_id: int,
        *,
        project: str | None = None,
        limit: int = 50,
        order: str = "asc",
    ) -> dict[str, Any]:
        result = self._request(
            "GET",
            self._resolve_project(project),
            f"_apis/wit/workItems/{work_item_id}/comments",
            query={"api-version": "7.1-preview.4", "$top": str(limit), "order": order},
        )
        comments = result.get("comments", [])
        return {
            "work_item_id": work_item_id,
            "count": len(comments),
            "comments": [self._normalize_comment(comment) for comment in comments],
        }

    def add_comment(
        self,
        work_item_id: int,
        comment: str,
        *,
        project: str | None = None,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        if dry_run:
            return {
                "dry_run": True,
                "work_item_id": work_item_id,
                "project": self._resolve_project(project),
                "comment": comment,
                "operation": "add_comment",
            }

        result = self._request(
            "POST",
            self._resolve_project(project),
            f"_apis/wit/workItems/{work_item_id}/comments",
            body={"text": comment},
            query={"api-version": "7.1-preview.4"},
        )
        return {
            "dry_run": False,
            "work_item_id": work_item_id,
            "comment_id": result.get("id"),
            "url": result.get("url"),
            "created_at": result.get("createdDate"),
        }

    def attach_file(
        self,
        work_item_id: int,
        file_path: str,
        *,
        project: str | None = None,
        comment: str | None = None,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        resolved_project = self._resolve_project(project)
        file_name = os.path.basename(file_path)
        if dry_run:
            return {
                "dry_run": True,
                "work_item_id": work_item_id,
                "project": resolved_project,
                "file_path": file_path,
                "file_name": file_name,
                "operation": "attach_file",
            }

        attachment = self._upload_attachment(resolved_project, file_path, file_name)
        operations = [
            {
                "op": "add",
                "path": "/relations/-",
                "value": {
                    "rel": "AttachedFile",
                    "url": attachment["url"],
                    "attributes": {"comment": comment or file_name},
                },
            }
        ]
        updated = self.update_work_item(
            work_item_id,
            operations,
            project=resolved_project,
            dry_run=False,
            reason=comment,
        )
        return {
            "dry_run": False,
            "work_item_id": work_item_id,
            "file_name": file_name,
            "attachment_url": attachment["url"],
            "new_rev": updated.get("new_rev"),
        }

    def update_work_item(
        self,
        work_item_id: int,
        operations: list[dict[str, Any]],
        *,
        project: str | None = None,
        dry_run: bool = True,
        reason: str | None = None,
    ) -> dict[str, Any]:
        if dry_run:
            return {
                "dry_run": True,
                "work_item_id": work_item_id,
                "project": self._resolve_project(project),
                "operations": operations,
                "reason": reason,
            }

        result = self._request(
            "PATCH",
            self._resolve_project(project),
            f"_apis/wit/workitems/{work_item_id}",
            body=operations,
            content_type="application/json-patch+json",
        )
        return {
            "dry_run": False,
            "work_item_id": work_item_id,
            "new_rev": result.get("rev"),
            "changed_fields": [op.get("path", "") for op in operations],
            "url": result.get("url"),
        }

    def find_users(self, query: str, *, project: str | None = None, limit: int = 20) -> dict[str, Any]:
        # Azure identity search varies by tenant. This endpoint is available for
        # many Azure DevOps Services orgs and keeps the repository stdlib-only.
        result = self._request(
            "GET",
            self._resolve_project(project),
            "_apis/identities",
            query={"searchFilter": "General", "filterValue": query, "$top": str(limit)},
        )
        values = result.get("value", [])
        return {
            "count": len(values),
            "users": [self._normalize_identity(item) for item in values],
        }

    def _request(
        self,
        method: str,
        project: str,
        path: str,
        *,
        query: dict[str, str] | None = None,
        body: Any | None = None,
        content_type: str = "application/json",
    ) -> dict[str, Any]:
        query_params = {"api-version": self.config.api_version}
        if query:
            query_params.update(query)
        url = f"{self._project_base_url(project)}/{path}?{urllib.parse.urlencode(query_params)}"

        return self._curl_request(method, url, body=body, content_type=content_type)

    def _auth_header(self) -> str:
        token = base64.b64encode(f":{self.config.pat}".encode("utf-8")).decode("ascii")
        return f"Basic {token}"

    def _curl_request(
        self,
        method: str,
        url: str,
        *,
        body: Any | None,
        content_type: str,
    ) -> dict[str, Any]:
        timeout_seconds = request_timeout_seconds("AZURE_DEVOPS_REQUEST_TIMEOUT_SECONDS")
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as curl_config, tempfile.NamedTemporaryFile("w+b") as response_file:
            curl_config.write(f'user = "{curl_config_value(":" + self.config.pat)}"\n')
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
                "-H",
                f"Content-Type: {content_type}",
                "-o",
                response_file.name,
                "-w",
                "%{http_code}",
            ]
            if body is not None:
                command.extend(["--data", json.dumps(body)])
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
                raise AzureRepositoryError(f"Azure DevOps curl timed out after {timeout_seconds}s") from exc
            raw = response_file.read().decode("utf-8-sig", errors="replace")

        if result.returncode != 0:
            raise AzureRepositoryError(f"Azure DevOps curl failed: {result.stderr.strip()}")

        status_text = result.stdout.strip()
        status = int(status_text) if status_text.isdigit() else 0
        if status >= 400 or status == 0:
            raise AzureRepositoryError(f"Azure DevOps HTTP {status}: {raw}")

        return json.loads(raw) if raw.strip() else {}

    def _upload_attachment(self, project: str, file_path: str, file_name: str) -> dict[str, Any]:
        url = (
            f"{self._project_base_url(project)}/_apis/wit/attachments?"
            f"{urllib.parse.urlencode({'fileName': file_name, 'api-version': self.config.api_version})}"
        )
        timeout_seconds = request_timeout_seconds("AZURE_DEVOPS_REQUEST_TIMEOUT_SECONDS")
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as curl_config:
            curl_config.write(f'user = "{curl_config_value(":" + self.config.pat)}"\n')
            curl_config.flush()
            command = [
                "curl",
                "-sS",
                "--config",
                curl_config.name,
                "--max-time",
                str(timeout_seconds),
                "-X",
                "POST",
                "-H",
                "Accept: application/json",
                "-H",
                "Content-Type: application/octet-stream",
                "--data-binary",
                f"@{file_path}",
                url,
            ]
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
                raise AzureRepositoryError(f"Azure DevOps attachment upload timed out after {timeout_seconds}s") from exc
        if result.returncode != 0:
            raise AzureRepositoryError(f"Azure DevOps attachment upload failed: {result.stderr.strip()}")
        payload = json.loads(result.stdout) if result.stdout.strip() else {}
        if not payload.get("url"):
            raise AzureRepositoryError(f"Azure DevOps attachment upload returned no URL: {result.stdout}")
        return payload

    def _build_wiql(
        self,
        *,
        project: str,
        state: str | None,
        assigned_to: str | None,
        tags: list[str] | None,
    ) -> str:
        clauses = [f"[System.TeamProject] = '{project}'"]
        if state:
            clauses.append(f"[System.State] = '{self._escape_wiql(state)}'")
        if assigned_to:
            clauses.append(f"[System.AssignedTo] = '{self._escape_wiql(assigned_to)}'")
        for tag in tags or []:
            clauses.append(f"[System.Tags] CONTAINS '{self._escape_wiql(tag)}'")
        where = " AND ".join(clauses)
        return (
            "SELECT [System.Id], [System.Title], [System.State] "
            f"FROM WorkItems WHERE {where} ORDER BY [System.ChangedDate] DESC"
        )

    @staticmethod
    def _escape_wiql(value: str) -> str:
        return value.replace("'", "''")

    def _resolve_project(self, project: str | None) -> str:
        resolved = project or self.config.default_project
        if not resolved:
            raise AzureRepositoryError(
                "Azure DevOps project is required. Pass --project or set AZURE_DEVOPS_PROJECT."
            )
        return resolved

    def _project_base_url(self, project: str) -> str:
        return (
            f"https://dev.azure.com/{urllib.parse.quote(self.config.org)}/"
            f"{project}"
        )

    def _url(self, project: str, path: str) -> str:
        return f"{self._project_base_url(project)}/{path}"

    @staticmethod
    def _normalize_work_item(item: dict[str, Any]) -> dict[str, Any]:
        fields = item.get("fields", {})
        assigned = fields.get("System.AssignedTo")
        if isinstance(assigned, dict):
            assigned_to = assigned.get("uniqueName") or assigned.get("displayName")
        else:
            assigned_to = assigned

        tags_raw = fields.get("System.Tags") or ""
        tags = [tag.strip() for tag in tags_raw.split(";") if tag.strip()]
        return {
            "id": item.get("id"),
            "rev": item.get("rev"),
            "work_item_type": fields.get("System.WorkItemType"),
            "title": fields.get("System.Title"),
            "state": fields.get("System.State"),
            "created_date": fields.get("System.CreatedDate"),
            "changed_date": fields.get("System.ChangedDate"),
            "board_column": fields.get("System.BoardColumn")
            or fields.get("WEF_22B684E163F0463B99498D97346D19F5_Kanban.Column"),
            "board_column_done": fields.get("System.BoardColumnDone")
            if "System.BoardColumnDone" in fields
            else fields.get("WEF_22B684E163F0463B99498D97346D19F5_Kanban.Column.Done"),
            "assigned_to": assigned_to,
            "tags": tags,
            "description": fields.get("System.Description"),
            "acceptance_criteria": fields.get("Microsoft.VSTS.Common.AcceptanceCriteria"),
            "relations": item.get("relations", []),
            "url": item.get("url"),
        }

    @staticmethod
    def _normalize_comment(comment: dict[str, Any]) -> dict[str, Any]:
        author = comment.get("createdBy") or {}
        return {
            "id": comment.get("id"),
            "author": author.get("uniqueName") or author.get("displayName"),
            "created_at": comment.get("createdDate"),
            "modified_at": comment.get("modifiedDate"),
            "text": comment.get("text"),
        }

    @staticmethod
    def _normalize_identity(identity: dict[str, Any]) -> dict[str, Any]:
        return {
            "display_name": identity.get("displayName") or identity.get("providerDisplayName"),
            "unique_name": identity.get("uniqueName"),
            "descriptor": identity.get("descriptor") or identity.get("id"),
            "email": identity.get("properties", {}).get("Mail", {}).get("$value"),
        }


def load_dotenv() -> None:
    """Load the nearest .env file without overriding existing environment vars."""
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


def _dotenv_candidates() -> list[Any]:
    from pathlib import Path

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


def normalize_org(value: str) -> str:
    cleaned = value.strip().strip('"').strip("'").rstrip("/")
    marker = "dev.azure.com/"
    if marker in cleaned:
        return cleaned.split(marker, 1)[1].split("/", 1)[0]
    return cleaned


def request_timeout_seconds(env_name: str) -> int:
    raw = os.environ.get(env_name, "30")
    return int(raw) if raw.isdigit() and int(raw) > 0 else 30


def curl_config_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
