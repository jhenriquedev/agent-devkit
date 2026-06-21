#!/usr/bin/env python3
"""Read-only Elasticsearch repository using Python stdlib and curl."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ElasticsearchRepositoryError(RuntimeError):
    """Raised when Elasticsearch calls fail or required scope is missing."""


@dataclass(frozen=True)
class ElasticsearchConfig:
    base_url: str | None = None
    api_key: str | None = None
    default_time_field: str = "@timestamp"

    @classmethod
    def from_env(cls) -> "ElasticsearchConfig":
        load_dotenv()
        return cls(
            base_url=first_env("ELASTICSEARCH_URL", "ELASTIC_URL", "ES_URL"),
            api_key=first_env("ELASTICSEARCH_API_KEY", "ELASTIC_API_KEY", "EC_API_KEY"),
            default_time_field=os.environ.get("ELASTICSEARCH_DEFAULT_TIME_FIELD", "@timestamp"),
        )


class ElasticsearchRepository:
    """Small read-only repository for Elasticsearch log analysis."""

    def __init__(self, config: ElasticsearchConfig | None = None) -> None:
        self.config = config or ElasticsearchConfig.from_env()

    def list_sources(self, *, pattern: str | None = None, limit: int = 100) -> dict[str, Any]:
        indices = self._request("GET", "/_cat/indices", query={"format": "json", "h": "index,status,health,docs.count,store.size"})
        streams = self._request("GET", "/_data_stream", query={})
        aliases = self._request("GET", "/_cat/aliases", query={"format": "json", "h": "alias,index"})
        source_pattern = pattern or "*"
        return {
            "pattern": source_pattern,
            "indices": filter_sources(indices if isinstance(indices, list) else [], "index", source_pattern, limit),
            "data_streams": filter_sources((streams.get("data_streams") or []), "name", source_pattern, limit),
            "aliases": filter_sources(aliases if isinstance(aliases, list) else [], "alias", source_pattern, limit),
        }

    def describe_source(self, *, source: str) -> dict[str, Any]:
        require_source(source)
        mapping = self._request("GET", f"/{quote_source(source)}/_mapping")
        fields = sorted(extract_mapping_fields(mapping))
        return {
            "source": source,
            "time_fields": [field for field in fields if field.endswith("timestamp") or field in {"@timestamp", "timestamp"}],
            "service_fields": [field for field in fields if field in {"service.name", "service", "serviceName", "app.name"}],
            "level_fields": [field for field in fields if field in {"log.level", "level", "severity"}],
            "trace_fields": [field for field in fields if field in {"trace.id", "trace_id", "correlation.id", "correlation_id", "request.id", "request_id"}],
            "fields": fields[:250],
        }

    def render_query(
        self,
        *,
        source: str,
        start_time: str,
        end_time: str,
        query_text: str | None = None,
        service: str | None = None,
        environment: str | None = None,
        level: str | None = None,
        filters: dict[str, Any] | None = None,
        time_field: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        require_source(source)
        resolved_time_field = time_field or self.config.default_time_field
        body = build_search_body(
            start_time=start_time,
            end_time=end_time,
            time_field=resolved_time_field,
            query_text=query_text,
            service=service,
            environment=environment,
            level=level,
            filters=filters,
            limit=limit,
        )
        return {"source": source, "body": body}

    def search_events(
        self,
        *,
        source: str,
        start_time: str,
        end_time: str,
        query_text: str | None = None,
        service: str | None = None,
        environment: str | None = None,
        level: str | None = None,
        filters: dict[str, Any] | None = None,
        time_field: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        query = self.render_query(
            source=source,
            start_time=start_time,
            end_time=end_time,
            query_text=query_text,
            service=service,
            environment=environment,
            level=level,
            filters=filters,
            time_field=time_field,
            limit=limit,
        )
        result = self._request("POST", f"/{quote_source(source)}/_search", body=query["body"])
        hits = result.get("hits", {})
        items = hits.get("hits", [])
        return {
            "source": source,
            "start_time": start_time,
            "end_time": end_time,
            "query": query["body"],
            "total": normalize_total(hits.get("total")),
            "events": [normalize_event(item) for item in items],
        }

    def count_events(self, **kwargs: Any) -> dict[str, Any]:
        source = kwargs["source"]
        query = self.render_query(**{**kwargs, "limit": 0})
        result = self._request("POST", f"/{quote_source(source)}/_count", body={"query": query["body"]["query"]})
        return {"source": source, "count": result.get("count", 0), "query": query["body"]["query"]}

    def aggregate_terms(
        self,
        *,
        source: str,
        field: str,
        start_time: str,
        end_time: str,
        size: int = 10,
        **kwargs: Any,
    ) -> dict[str, Any]:
        query = self.render_query(
            source=source,
            start_time=start_time,
            end_time=end_time,
            query_text=kwargs.get("query_text"),
            service=kwargs.get("service"),
            environment=kwargs.get("environment"),
            level=kwargs.get("level"),
            filters=kwargs.get("filters"),
            time_field=kwargs.get("time_field"),
            limit=0,
        )
        body = {
            "size": 0,
            "query": query["body"]["query"],
            "aggs": {"items": {"terms": {"field": field, "size": size, "missing": "__missing__"}}},
        }
        result = self._request("POST", f"/{quote_source(source)}/_search", body=body)
        buckets = (((result.get("aggregations") or {}).get("items") or {}).get("buckets") or [])
        return {"source": source, "field": field, "buckets": buckets}

    def aggregate_timeline(
        self,
        *,
        source: str,
        start_time: str,
        end_time: str,
        interval: str = "5m",
        **kwargs: Any,
    ) -> dict[str, Any]:
        time_field = kwargs.get("time_field") or self.config.default_time_field
        query = self.render_query(
            source=source,
            start_time=start_time,
            end_time=end_time,
            query_text=kwargs.get("query_text"),
            service=kwargs.get("service"),
            environment=kwargs.get("environment"),
            level=kwargs.get("level"),
            filters=kwargs.get("filters"),
            time_field=time_field,
            limit=0,
        )
        body = {
            "size": 0,
            "query": query["body"]["query"],
            "aggs": {"timeline": {"date_histogram": {"field": time_field, "fixed_interval": interval}}},
        }
        result = self._request("POST", f"/{quote_source(source)}/_search", body=body)
        buckets = (((result.get("aggregations") or {}).get("timeline") or {}).get("buckets") or [])
        return {"source": source, "time_field": time_field, "interval": interval, "buckets": buckets}

    def get_event(self, *, source: str, event_id: str) -> dict[str, Any]:
        require_source(source)
        if not event_id:
            raise ElasticsearchRepositoryError("event_id is required")
        result = self._request("GET", f"/{quote_source(source)}/_doc/{urllib.parse.quote(event_id, safe='')}")
        return {"source": source, "event": normalize_event(result)}

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, str] | None = None,
        body: Any | None = None,
    ) -> Any:
        if not self.config.base_url:
            raise ElasticsearchRepositoryError("ELASTICSEARCH_URL is required for real Elasticsearch calls")
        if not self.config.api_key:
            raise ElasticsearchRepositoryError("ELASTICSEARCH_API_KEY, ELASTIC_API_KEY, or EC_API_KEY is required")
        url = build_url(self.config.base_url, path, query)
        with tempfile.NamedTemporaryFile("w+b") as response_file:
            command = [
                "curl",
                "-sS",
                "-X",
                method,
                "-H",
                "Accept: application/json",
                "-H",
                f"Authorization: ApiKey {self.config.api_key}",
                "-o",
                response_file.name,
                "-w",
                "%{http_code}",
            ]
            if body is not None:
                command.extend(["-H", "Content-Type: application/json", "--data", json.dumps(body)])
            command.append(url)
            result = subprocess.run(command, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            raw = response_file.read().decode("utf-8-sig", errors="replace")
        if result.returncode != 0:
            raise ElasticsearchRepositoryError(f"Elasticsearch curl failed: {result.stderr.strip()}")
        status_text = result.stdout.strip()
        status = int(status_text) if status_text.isdigit() else 0
        if status >= 400 or status == 0:
            raise ElasticsearchRepositoryError(f"Elasticsearch HTTP {status}: {raw}")
        return json.loads(raw) if raw.strip() else {}


def build_search_body(
    *,
    start_time: str,
    end_time: str,
    time_field: str,
    query_text: str | None = None,
    service: str | None = None,
    environment: str | None = None,
    level: str | None = None,
    filters: dict[str, Any] | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    clauses: list[dict[str, Any]] = [{"range": {time_field: {"gte": start_time, "lte": end_time}}}]
    if query_text:
        clauses.append({"query_string": {"query": query_text, "default_operator": "AND"}})
    add_field_match(clauses, ["service.name", "service", "serviceName", "app.name"], service)
    add_field_match(clauses, ["environment", "env", "labels.environment", "service.environment"], environment)
    add_field_match(clauses, ["log.level", "level", "severity"], level)
    for key, value in (filters or {}).items():
        if value not in (None, ""):
            clauses.append({"term": {key: value}})
    return {
        "size": max(0, min(int(limit), 1000)),
        "sort": [{time_field: {"order": "desc", "unmapped_type": "date"}}],
        "query": {"bool": {"filter": clauses}},
    }


def add_field_match(clauses: list[dict[str, Any]], fields: list[str], value: str | None) -> None:
    if value:
        clauses.append({"bool": {"should": [{"term": {field: value}} for field in fields], "minimum_should_match": 1}})


def normalize_event(item: dict[str, Any]) -> dict[str, Any]:
    source = item.get("_source", item)
    return {
        "id": item.get("_id") or source.get("_id"),
        "index": item.get("_index"),
        "timestamp": pick(source, "@timestamp", "timestamp", "time"),
        "service": pick(source, "service.name", "service", "serviceName", "app.name"),
        "environment": pick(source, "environment", "env", "labels.environment", "service.environment"),
        "level": pick(source, "log.level", "level", "severity"),
        "message": pick(source, "message", "log.message", "msg", "error.message"),
        "trace_id": pick(source, "trace.id", "trace_id", "correlation.id", "correlation_id", "request.id", "request_id"),
        "error_type": pick(source, "error.type", "exception.type", "error.kind"),
        "raw": source,
    }


def pick(data: dict[str, Any], *paths: str) -> Any:
    for path in paths:
        current: Any = data
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                current = None
                break
            current = current[part]
        if current not in (None, ""):
            return current
        if path in data and data[path] not in (None, ""):
            return data[path]
    return None


def normalize_total(value: Any) -> int:
    if isinstance(value, dict):
        return int(value.get("value") or 0)
    return int(value or 0)


def extract_mapping_fields(mapping: dict[str, Any]) -> set[str]:
    fields: set[str] = set()
    for index_data in mapping.values():
        properties = ((index_data.get("mappings") or {}).get("properties") or {})
        walk_properties(properties, "", fields)
    return fields


def walk_properties(properties: dict[str, Any], prefix: str, fields: set[str]) -> None:
    for name, value in properties.items():
        full = f"{prefix}.{name}" if prefix else name
        fields.add(full)
        nested = value.get("properties") if isinstance(value, dict) else None
        if isinstance(nested, dict):
            walk_properties(nested, full, fields)


def filter_sources(items: list[dict[str, Any]], key: str, pattern: str, limit: int) -> list[dict[str, Any]]:
    regex = re.compile("^" + re.escape(pattern).replace("\\*", ".*") + "$")
    return [item for item in items if regex.match(str(item.get(key) or ""))][:limit]


def require_source(source: str | None) -> None:
    if not source:
        raise ElasticsearchRepositoryError("source is required")


def quote_source(source: str) -> str:
    return urllib.parse.quote(source, safe="*,._-:")


def build_url(base_url: str, path: str, query: dict[str, str] | None = None) -> str:
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    if query:
        clean = {key: value for key, value in query.items() if value not in (None, "")}
        if clean:
            url = f"{url}?{urllib.parse.urlencode(clean)}"
    return url


def first_env(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


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
