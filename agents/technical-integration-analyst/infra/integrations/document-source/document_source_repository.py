#!/usr/bin/env python3
"""Documentation source loader for technical integration analysis."""

from __future__ import annotations

import html
import json
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class DocumentSourceError(RuntimeError):
    """Raised when documentation sources cannot be loaded."""


SUPPORTED_EXTENSIONS = {
    ".json",
    ".yaml",
    ".yml",
    ".md",
    ".markdown",
    ".txt",
    ".html",
    ".htm",
    ".xml",
    ".wsdl",
    ".pdf",
}


@dataclass(frozen=True)
class DocumentSource:
    source_id: str
    location: str
    source_type: str
    text: str
    raw: str | None = None
    metadata: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "location": self.location,
            "source_type": self.source_type,
            "text": self.text,
            "raw": self.raw,
            "metadata": self.metadata or {},
        }


class DocumentSourceRepository:
    """Load documentation from local files, directories, URLs, or inline text."""

    def load_sources(
        self,
        *,
        url: str | None = None,
        file: str | None = None,
        directory: str | None = None,
        text: str | None = None,
    ) -> dict[str, Any]:
        sources: list[DocumentSource] = []
        ignored: list[str] = []

        if text:
            sources.append(DocumentSource("inline-1", "inline-text", "text", mask_secrets(text), text))
        if url:
            sources.append(self._load_url(url, len(sources) + 1))
        if file:
            sources.append(self._load_file(Path(file), len(sources) + 1))
        if directory:
            base = Path(directory)
            if not base.exists() or not base.is_dir():
                raise DocumentSourceError(f"directory not found: {directory}")
            for path in sorted(item for item in base.rglob("*") if item.is_file()):
                if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                    ignored.append(str(path))
                    continue
                sources.append(self._load_file(path, len(sources) + 1))

        if not sources:
            raise DocumentSourceError("--url, --file, --directory, or --text is required")

        return {
            "count": len(sources),
            "ignored": ignored,
            "sources": [source.as_dict() for source in sources],
        }

    def _load_url(self, url: str, index: int) -> DocumentSource:
        with urllib.request.urlopen(url, timeout=30) as response:  # nosec - user supplied docs URL.
            raw_bytes = response.read()
            content_type = response.headers.get("content-type", "")
        raw = raw_bytes.decode("utf-8-sig", errors="replace")
        source_type = detect_source_type(url, content_type, raw)
        return DocumentSource(
            f"source-{index}",
            url,
            source_type,
            normalize_text(raw, source_type),
            raw,
            {"content_type": content_type},
        )

    def _load_file(self, path: Path, index: int) -> DocumentSource:
        if not path.exists() or not path.is_file():
            raise DocumentSourceError(f"file not found: {path}")
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            text = extract_pdf_text(path)
            return DocumentSource(f"source-{index}", str(path), "pdf", mask_secrets(text), None)
        raw = path.read_text(encoding="utf-8-sig", errors="replace")
        source_type = detect_source_type(str(path), "", raw)
        return DocumentSource(f"source-{index}", str(path), source_type, normalize_text(raw, source_type), raw)


def detect_source_type(location: str, content_type: str, raw: str) -> str:
    lowered = f"{location} {content_type}".lower()
    stripped = raw.lstrip()
    if lowered.endswith(".pdf") or "application/pdf" in lowered:
        return "pdf"
    if lowered.endswith((".yaml", ".yml")):
        return "yaml"
    if lowered.endswith(".json") or stripped.startswith("{"):
        return "json"
    if lowered.endswith((".xml", ".wsdl")) or stripped.startswith("<?xml"):
        return "xml"
    if "html" in lowered or re.search(r"<html|<body|<pre", raw, re.I):
        return "html"
    if lowered.endswith((".md", ".markdown")):
        return "markdown"
    return "text"


def normalize_text(raw: str, source_type: str) -> str:
    if source_type == "html":
        return mask_secrets(html_to_text(raw))
    return mask_secrets(raw)


def html_to_text(raw: str) -> str:
    try:
        from bs4 import BeautifulSoup  # type: ignore
    except ImportError:
        text = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw, flags=re.I | re.S)
        text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        return html.unescape(compact(text))
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return compact(soup.get_text("\n"))


def extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as exc:
        raise DocumentSourceError("pypdf is required to read PDF files") from exc
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def mask_secrets(value: str) -> str:
    text = value
    patterns = [
        (r"(?i)(authorization\s*:\s*bearer\s+)[^\s,;]+", r"\1{{token}}"),
        (r"(?i)(api[_-]?key\s*[:=]\s*)[^\s,;]+", r"\1{{api_key}}"),
        (r"(?i)(password\s*[:=]\s*)[^\s,;]+", r"\1{{password}}"),
        (r"(?i)(secret\s*[:=]\s*)[^\s,;]+", r"\1{{secret}}"),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text


def compact(value: str) -> str:
    return "\n".join(line.strip() for line in value.splitlines() if line.strip())


def load_json_if_possible(raw: str | None) -> Any | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None
