#!/usr/bin/env python3
"""Technical integration contract extraction and artifact generation."""

from __future__ import annotations

import json
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
POSTMAN_SCHEMA = "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"


@dataclass(frozen=True)
class Operation:
    name: str
    protocol: str
    method: str | None
    path: str
    summary: str
    mutation: bool
    evidence: str
    body_example: Any | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "protocol": self.protocol,
            "method": self.method,
            "path": self.path,
            "summary": self.summary,
            "mutation": self.mutation,
            "evidence": self.evidence,
            "body_example": self.body_example,
        }


class TechnicalIntegrationRepository:
    """Extract integration contracts and generate derived artifacts."""

    def extract_contract(self, *, sources: list[dict[str, Any]], base_url: str | None = None) -> dict[str, Any]:
        operations: list[Operation] = []
        protocols: set[str] = set()
        auth: set[str] = set()
        errors: set[str] = set()
        detected_base_url = base_url or os.environ.get("TECH_INTEGRATION_DEFAULT_BASE_URL")

        for source in sources:
            text = source.get("text") or ""
            raw = source.get("raw") or text
            source_type = source.get("source_type") or "text"
            protocols.update(detect_protocols(text, source_type))
            auth.update(detect_auth(text))
            errors.update(detect_errors(text))
            detected_base_url = detected_base_url or detect_base_url(text)
            operations.extend(extract_structured_operations(raw, source_type, source.get("location") or "source"))
            operations.extend(extract_text_operations(text, source.get("location") or "source"))

        deduped = dedupe_operations(operations)
        if deduped and not protocols:
            protocols.add("rest")
        if not protocols:
            protocols.add("unknown")

        contract = {
            "protocols": sorted(protocols),
            "primary_protocol": primary_protocol(protocols),
            "base_url": detected_base_url,
            "auth": sorted(auth),
            "operations": [operation.as_dict() for operation in deduped],
            "errors": sorted(errors),
        }
        contract["missing_information"] = identify_missing_information(contract)
        contract["flow"] = analyze_flow(contract)
        return contract

    def render_contract_markdown(self, contract: dict[str, Any]) -> str:
        lines = [
            "# Contrato de Integracao",
            "",
            "## Resumo",
            "",
            f"- Protocolo: {contract.get('primary_protocol') or '-'}",
            f"- Protocolos detectados: {', '.join(contract.get('protocols') or []) or '-'}",
            f"- Base URL: {contract.get('base_url') or '{{base_url}}'}",
            f"- Auth: {', '.join(contract.get('auth') or []) or 'nao documentado'}",
            "",
            "## Operacoes",
            "",
        ]
        operations = contract.get("operations") or []
        if not operations:
            lines.append("- Nenhuma operacao detectada.")
        for operation in operations:
            label = operation_label(operation)
            lines.extend(
                [
                    f"### {label}",
                    "",
                    f"- Protocolo: {operation.get('protocol') or '-'}",
                    f"- Mutation: {operation.get('mutation')}",
                    f"- Evidencia: {operation.get('evidence') or '-'}",
                    "",
                ]
            )
        lines.extend(render_missing_section(contract))
        return "\n".join(lines).rstrip() + "\n"

    def render_ingestion_markdown(self, loaded: dict[str, Any]) -> str:
        lines = [
            "# Ingestao de Documentacao Tecnica",
            "",
            f"- Fontes carregadas: {loaded.get('count', 0)}",
            f"- Fontes ignoradas: {len(loaded.get('ignored') or [])}",
            "",
            "## Fontes",
            "",
        ]
        for source in loaded.get("sources") or []:
            preview = compact(source.get("text") or "")[:500]
            lines.extend(
                [
                    f"### {source.get('source_id')}",
                    "",
                    f"- Local: {source.get('location')}",
                    f"- Tipo: {source.get('source_type')}",
                    f"- Tamanho: {len(source.get('text') or '')}",
                    "",
                    "```text",
                    preview,
                    "```",
                    "",
                ]
            )
        return "\n".join(lines).rstrip() + "\n"

    def render_missing_information(self, contract: dict[str, Any]) -> str:
        lines = ["# Informacoes Ausentes", "", "## Perguntas", ""]
        missing = contract.get("missing_information") or []
        if not missing:
            lines.append("- Nenhuma lacuna bloqueante detectada.")
        for item in missing:
            lines.append(f"- {item}")
        return "\n".join(lines).rstrip() + "\n"

    def render_flow(self, contract: dict[str, Any]) -> str:
        lines = ["# Fluxo de Uso da Integracao", "", "## Ordem recomendada", ""]
        for index, step in enumerate(contract.get("flow") or [], start=1):
            lines.append(f"{index}. {step}")
        return "\n".join(lines).rstrip() + "\n"

    def generate_test_data(self, contract: dict[str, Any]) -> dict[str, Any]:
        cases: list[dict[str, Any]] = []
        for operation in contract.get("operations") or []:
            label = operation_label(operation)
            cases.append(
                {
                    "operation": label,
                    "valid": operation.get("body_example") or {"id": "{{resource_id}}", "name": "valid-test"},
                    "invalid": {"missing_required_field": True},
                    "boundary": {"max_length_text": "x" * 255, "zero_amount": 0},
                }
            )
        return {"cases": cases}

    def render_test_data(self, test_data: dict[str, Any]) -> str:
        lines = ["# Massa de Testes", ""]
        for case in test_data.get("cases") or []:
            lines.extend(
                [
                    f"## {case['operation']}",
                    "",
                    "### Valida",
                    "",
                    "```json",
                    json.dumps(case["valid"], ensure_ascii=False, indent=2),
                    "```",
                    "",
                    "### Invalida",
                    "",
                    "```json",
                    json.dumps(case["invalid"], ensure_ascii=False, indent=2),
                    "```",
                    "",
                ]
            )
        if not test_data.get("cases"):
            lines.append("- Nenhuma operacao detectada para gerar massa.")
        return "\n".join(lines).rstrip() + "\n"

    def build_postman_collection(self, contract: dict[str, Any]) -> dict[str, Any]:
        base_url = contract.get("base_url") or "{{base_url}}"
        items = []
        for operation in http_operations(contract):
            method = operation.get("method") or "POST"
            path = operation.get("path") or "/"
            headers = [{"key": "Accept", "value": "application/json"}]
            body = {}
            if method not in SAFE_METHODS:
                headers.append({"key": "Content-Type", "value": "application/json"})
                body = {
                    "mode": "raw",
                    "raw": json.dumps(operation.get("body_example") or {"example": "value"}, indent=2),
                    "options": {"raw": {"language": "json"}},
                }
            request: dict[str, Any] = {
                "method": method,
                "header": headers,
                "url": {
                    "raw": "{{base_url}}" + path,
                    "host": ["{{base_url}}"],
                    "path": [part for part in path.strip("/").split("/") if part],
                },
                "auth": {"type": "bearer", "bearer": [{"key": "token", "value": "{{token}}", "type": "string"}]},
            }
            if body:
                request["body"] = body
            items.append({"name": operation_label(operation), "request": request, "response": []})
        return {
            "info": {
                "name": "Technical Integration Analyst Collection",
                "schema": POSTMAN_SCHEMA,
            },
            "variable": [
                {"key": "base_url", "value": base_url},
                {"key": "token", "value": ""},
                {"key": "resource_id", "value": ""},
            ],
            "item": items,
        }

    def render_http_artifacts(self, contract: dict[str, Any]) -> str:
        lines = ["# Artefatos HTTP", "", "## Curl", ""]
        operations = http_operations(contract)
        if not operations:
            lines.append("- Nenhuma operacao HTTP detectada.")
        for operation in operations:
            lines.extend(["```bash", build_curl(contract, operation), "```", ""])
        return "\n".join(lines).rstrip() + "\n"

    def render_protocol_artifacts(self, contract: dict[str, Any]) -> str:
        lines = ["# Artefatos de Protocolo", ""]
        protocols = [protocol for protocol in contract.get("protocols") or [] if protocol not in {"rest", "soap", "mcp"}]
        if not protocols:
            lines.append("- Nenhum protocolo nao HTTP detectado. Use `generate-http-artifacts` para REST/SOAP/MCP-over-HTTP.")
        for protocol in protocols:
            lines.extend(
                [
                    f"## {protocol}",
                    "",
                    "- Preparar credenciais em variaveis de ambiente.",
                    "- Executar transferencia/envio em ambiente sandbox.",
                    "- Validar arquivo, mensagem ou resposta de confirmacao.",
                    "- Executar cleanup quando a integracao criar estado.",
                    "",
                ]
            )
        return "\n".join(lines).rstrip() + "\n"

    def render_technical_docs(self, contract: dict[str, Any]) -> str:
        test_data = self.generate_test_data(contract)
        return "\n".join(
            [
                "# Documentacao Tecnica de Integracao",
                "",
                self.render_contract_markdown(contract).rstrip(),
                "",
                self.render_flow(contract).rstrip(),
                "",
                self.render_missing_information(contract).rstrip(),
                "",
                self.render_test_data(test_data).rstrip(),
            ]
        ).rstrip() + "\n"

    def write_pdf(self, markdown: str, output: str) -> None:
        try:
            from reportlab.lib.pagesizes import letter  # type: ignore
            from reportlab.pdfgen import canvas  # type: ignore
        except ImportError as exc:
            raise RuntimeError("reportlab is required to generate PDF files") from exc
        c = canvas.Canvas(output, pagesize=letter)
        width, height = letter
        y = height - 48
        for raw_line in markdown.splitlines():
            line = raw_line[:110]
            if y < 48:
                c.showPage()
                y = height - 48
            c.drawString(48, y, line)
            y -= 14
        c.save()


def extract_structured_operations(raw: str, source_type: str, location: str) -> list[Operation]:
    if source_type == "json":
        data = parse_json(raw)
        if isinstance(data, dict):
            if "openapi" in data or "swagger" in data:
                return openapi_operations(data, location)
            if "item" in data and "info" in data:
                return postman_operations(data, location)
    if source_type == "yaml":
        data = parse_yaml(raw)
        if isinstance(data, dict) and ("openapi" in data or "swagger" in data):
            return openapi_operations(data, location)
    if source_type == "xml" and ("wsdl" in raw.lower() or "soap" in raw.lower()):
        return wsdl_operations(raw, location)
    return []


def parse_json(raw: str) -> Any | None:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def parse_yaml(raw: str) -> Any | None:
    try:
        import yaml  # type: ignore
    except ImportError:
        return None
    try:
        return yaml.safe_load(raw)
    except Exception:
        return None


def openapi_operations(data: dict[str, Any], location: str) -> list[Operation]:
    operations: list[Operation] = []
    for path, path_item in (data.get("paths") or {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            upper = method.upper()
            if upper not in HTTP_METHODS:
                continue
            summary = operation.get("summary") or operation.get("operationId") or f"{upper} {path}"
            operations.append(
                Operation(
                    name=f"{upper} {path}",
                    protocol="rest",
                    method=upper,
                    path=path,
                    summary=summary,
                    mutation=upper not in SAFE_METHODS,
                    evidence=location,
                    body_example=extract_openapi_example(operation),
                )
            )
    return operations


def extract_openapi_example(operation: dict[str, Any]) -> Any | None:
    content = (((operation.get("requestBody") or {}).get("content")) or {}).get("application/json") or {}
    if "example" in content:
        return content["example"]
    examples = content.get("examples") or {}
    if examples:
        first = next(iter(examples.values()))
        if isinstance(first, dict):
            return first.get("value")
    return None


def postman_operations(data: dict[str, Any], location: str) -> list[Operation]:
    operations: list[Operation] = []
    for item in flatten_postman_items(data.get("item") or []):
        request = item.get("request") or {}
        method = (request.get("method") or "GET").upper()
        url = request.get("url") or {}
        raw_url = url.get("raw") if isinstance(url, dict) else str(url)
        path = re.sub(r"^https?://[^/]+", "", raw_url or "") or "/"
        operations.append(
            Operation(
                name=item.get("name") or f"{method} {path}",
                protocol="rest",
                method=method,
                path=path,
                summary=item.get("name") or "",
                mutation=method not in SAFE_METHODS,
                evidence=location,
            )
        )
    return operations


def flatten_postman_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flat: list[dict[str, Any]] = []
    for item in items:
        if "request" in item:
            flat.append(item)
        flat.extend(flatten_postman_items(item.get("item") or []))
    return flat


def wsdl_operations(raw: str, location: str) -> list[Operation]:
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return []
    operations = []
    for node in root.findall(".//{*}operation"):
        name = node.attrib.get("name")
        if not name:
            continue
        operations.append(Operation(name, "soap", "POST", f"soap:{name}", name, True, location))
    return dedupe_operations(operations)


def extract_text_operations(text: str, location: str) -> list[Operation]:
    operations: list[Operation] = []
    pattern = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(/[A-Za-z0-9_./{}:-]+)", re.I)
    for match in pattern.finditer(text):
        method = match.group(1).upper()
        path = normalize_path(match.group(2))
        operations.append(
            Operation(
                name=f"{method} {path}",
                protocol="rest",
                method=method,
                path=path,
                summary=f"{method} {path}",
                mutation=method not in SAFE_METHODS,
                evidence=location,
                body_example=extract_inline_json_after(text, match.end()),
            )
        )
    return operations


def extract_inline_json_after(text: str, start: int) -> Any | None:
    snippet = text[start : start + 500]
    match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", snippet)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def detect_protocols(text: str, source_type: str) -> set[str]:
    lowered = text.lower()
    protocols: set[str] = set()
    if source_type == "xml" and ("wsdl" in lowered or "soap" in lowered):
        protocols.add("soap")
    if "openapi" in lowered or re.search(r"\b(get|post|put|patch|delete)\s+/", lowered):
        protocols.add("rest")
    if "soap" in lowered or "wsdl" in lowered:
        protocols.add("soap")
    if "mcp" in lowered or "model context protocol" in lowered:
        protocols.add("mcp")
    if "sftp" in lowered or "ssh file transfer" in lowered:
        protocols.add("sftp")
    if "smtp" in lowered or "email server" in lowered:
        protocols.add("smtp")
    if "graphql" in lowered:
        protocols.add("graphql")
    if "csv" in lowered or "fixed-width" in lowered or "arquivo" in lowered:
        protocols.add("file")
    return protocols


def detect_auth(text: str) -> set[str]:
    lowered = text.lower()
    auth = set()
    if "bearer" in lowered:
        auth.add("bearer_token")
    if "oauth" in lowered:
        auth.add("oauth2")
    if "api key" in lowered or "apikey" in lowered:
        auth.add("api_key")
    if "basic auth" in lowered or "basic authentication" in lowered:
        auth.add("basic")
    if "username" in lowered and "password" in lowered:
        auth.add("user_password")
    return auth


def detect_errors(text: str) -> set[str]:
    errors = set()
    for match in re.finditer(r"\b(4\d\d|5\d\d)\b(?:\s+([A-Za-z0-9_.-]+))?", text):
        code = match.group(1)
        name = match.group(2) or ""
        errors.add(f"{code} {name}".strip())
    return errors


def detect_base_url(text: str) -> str | None:
    match = re.search(r"(?i)base\s+url\s*[:=-]\s*(https?://[^\s)]+)", text)
    if match:
        return match.group(1).rstrip(".")
    match = re.search(r"https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+", text)
    if match:
        return match.group(0).rstrip(".")
    return None


def primary_protocol(protocols: set[str]) -> str:
    for candidate in ("rest", "soap", "mcp", "sftp", "smtp", "graphql", "file", "queue"):
        if candidate in protocols:
            return candidate
    return "unknown"


def dedupe_operations(operations: list[Operation]) -> list[Operation]:
    seen = set()
    deduped = []
    for operation in operations:
        key = (operation.protocol, operation.method, operation.path)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(operation)
    return deduped


def identify_missing_information(contract: dict[str, Any]) -> list[str]:
    missing = []
    if not contract.get("base_url") and any(op.get("method") for op in contract.get("operations") or []):
        missing.append("Qual e a base URL do ambiente sandbox/homologacao?")
    if not contract.get("auth"):
        missing.append("Qual mecanismo de autenticacao deve ser usado e quais variaveis armazenam as credenciais?")
    if any(op.get("mutation") for op in contract.get("operations") or []):
        missing.append("Qual ambiente e seguro para executar mutations e qual criterio confirma cleanup?")
    if not contract.get("operations"):
        missing.append("Quais operacoes, comandos ou endpoints fazem parte da integracao?")
    return missing


def analyze_flow(contract: dict[str, Any]) -> list[str]:
    steps = []
    if contract.get("auth"):
        steps.append("Configurar autenticacao e obter token/credencial valida.")
    operations = contract.get("operations") or []
    for operation in sorted(operations, key=flow_sort_key):
        suffix = " (mutation)" if operation.get("mutation") else ""
        steps.append(f"Executar {operation_label(operation)}{suffix}.")
    if any(op.get("mutation") for op in operations):
        steps.append("Validar efeitos colaterais e executar cleanup quando aplicavel.")
    if not steps:
        steps.append("Completar informacoes faltantes antes de definir fluxo executavel.")
    return steps


def flow_sort_key(operation: dict[str, Any]) -> tuple[int, str]:
    method = operation.get("method") or ""
    if method == "POST":
        rank = 1
    elif method in {"GET", "HEAD", "OPTIONS"}:
        rank = 2
    elif method in {"PUT", "PATCH"}:
        rank = 3
    elif method == "DELETE":
        rank = 4
    else:
        rank = 5
    return rank, operation.get("path") or ""


def http_operations(contract: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        operation
        for operation in contract.get("operations") or []
        if operation.get("method") in HTTP_METHODS or operation.get("protocol") in {"rest", "soap", "mcp"}
    ]


def build_curl(contract: dict[str, Any], operation: dict[str, Any]) -> str:
    method = operation.get("method") or "POST"
    path = operation.get("path") or "/"
    parts = [
        "curl --request",
        method,
        f"'{{{{base_url}}}}{path}'",
        "--header 'Accept: application/json'",
        "--header 'Authorization: Bearer {{token}}'",
    ]
    if method not in SAFE_METHODS:
        body = json.dumps(operation.get("body_example") or {"example": "value"})
        parts.extend(["--header 'Content-Type: application/json'", f"--data '{body}'"])
    return " \\\n  ".join(parts)


def operation_label(operation: dict[str, Any]) -> str:
    method = operation.get("method")
    path = operation.get("path")
    if method and path:
        return f"{method} {path}"
    return operation.get("name") or path or "-"


def render_missing_section(contract: dict[str, Any]) -> list[str]:
    lines = ["## Informacoes Ausentes", ""]
    missing = contract.get("missing_information") or []
    if not missing:
        lines.append("- Nenhuma lacuna bloqueante detectada.")
    else:
        for item in missing:
            lines.append(f"- {item}")
    return lines


def normalize_path(path: str) -> str:
    return path.rstrip(".,);") or "/"


def compact(value: str) -> str:
    return " ".join(value.replace("\r", " ").split())


def write_json(path: str, payload: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
