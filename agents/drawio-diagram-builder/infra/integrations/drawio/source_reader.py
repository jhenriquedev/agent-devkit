"""Source readers for Draw.io diagram generation."""

from __future__ import annotations

import csv
import html
import json
import re
import urllib.request
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


IGNORED_DIRS = {".git", "node_modules", "vendor", "__pycache__", "dist", "build", "target", ".next"}
SUPPORTED_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".csv",
    ".html",
    ".htm",
    ".xml",
    ".pdf",
    ".docx",
    ".xlsx",
    ".pptx",
    ".drawio",
}


def load_sources(
    text: str | None = None,
    files: list[str] | None = None,
    directory: str | None = None,
    url: str | None = None,
) -> dict[str, Any]:
    sources: list[dict[str, Any]] = []
    failed_sources: list[dict[str, str]] = []
    if text:
        sources.append({"kind": "text", "path": "inline", "text": normalize_text(text)})
    for value in files or []:
        append_source_or_failure(sources, failed_sources, Path(value).expanduser())
    if directory:
        root = Path(directory).expanduser()
        try:
            paths = iter_supported_files(root)
        except Exception as exc:
            failed_sources.append({"path": str(root), "error": str(exc)})
            paths = []
        for path in paths:
            append_source_or_failure(sources, failed_sources, path)
    if url:
        try:
            sources.append(read_url(url))
        except Exception as exc:
            failed_sources.append({"path": url, "error": str(exc)})

    combined = "\n\n".join(item["text"] for item in sources if item.get("text"))
    return {
        "source_count": len(sources),
        "failed_sources": failed_sources,
        "sources": sources,
        "combined_text": combined,
        "facts": extract_fact_candidates(combined),
        "open_questions": infer_open_questions(combined),
    }


def append_source_or_failure(sources: list[dict[str, Any]], failed_sources: list[dict[str, str]], path: Path) -> None:
    try:
        source = read_file(path)
    except Exception as exc:
        failed_sources.append({"path": str(path), "error": str(exc)})
        return
    sources.append(source)


def iter_supported_files(root: Path) -> list[Path]:
    if not root.exists():
        raise ValueError(f"directory not found: {root}")
    paths: list[Path] = []
    for path in sorted(root.rglob("*")):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            paths.append(path)
    return paths


def read_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"file not found: {path}")
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        text = read_pdf(path)
    elif suffix == ".docx":
        text = read_docx(path)
    elif suffix == ".xlsx":
        text = read_xlsx(path)
    elif suffix == ".pptx":
        text = read_pptx(path)
    elif suffix == ".json":
        text = read_json(path)
    elif suffix == ".csv":
        text = read_csv(path)
    elif suffix in {".html", ".htm"}:
        text = strip_html(path.read_text(encoding="utf-8", errors="replace"))
    else:
        text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "kind": suffix.lstrip(".") or "file",
        "path": str(path),
        "text": normalize_text(text),
    }


def read_url(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=20) as response:  # nosec B310 - user-requested read-only URL fetch.
        raw = response.read().decode("utf-8", errors="replace")
    return {"kind": "url", "path": url, "text": normalize_text(strip_html(raw))}


def read_json(path: Path) -> str:
    try:
        return json.dumps(json.loads(path.read_text(encoding="utf-8")), ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def read_csv(path: Path) -> str:
    rows: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        for row in csv.reader(handle):
            rows.append(" | ".join(row))
    return "\n".join(rows)


def read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on optional env
        raise ValueError("pypdf is required to read PDF files") from exc
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8", errors="replace")
    return extract_xml_text(xml)


def read_xlsx(path: Path) -> str:
    texts: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            if name == "xl/sharedStrings.xml" or name.startswith("xl/worksheets/"):
                texts.append(extract_xml_text(archive.read(name).decode("utf-8", errors="replace")))
    return "\n".join(text for text in texts if text)


def read_pptx(path: Path) -> str:
    texts: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                texts.append(extract_xml_text(archive.read(name).decode("utf-8", errors="replace")))
    return "\n".join(text for text in texts if text)


def extract_xml_text(xml_text: str) -> str:
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        return re.sub(r"<[^>]+>", " ", xml_text)
    return " ".join(node.strip() for node in root.itertext() if node and node.strip())


def strip_html(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", value))


def normalize_text(value: str) -> str:
    return "\n".join(line.strip() for line in value.replace("\r", "\n").splitlines() if line.strip())


def extract_fact_candidates(text: str, limit: int = 12) -> list[str]:
    sentences = split_statements(text)
    return sentences[:limit]


def infer_open_questions(text: str) -> list[str]:
    questions: list[str] = []
    lowered = text.lower()
    if not lowered.strip():
        questions.append("Qual material deve ser analisado para criar o diagrama?")
    if "audiencia" not in lowered and "público" not in lowered and "publico" not in lowered:
        questions.append("Quem e a audiencia principal do diagrama?")
    if "escopo" not in lowered:
        questions.append("Qual e o escopo e o fora de escopo do diagrama?")
    return questions


def split_statements(text: str) -> list[str]:
    cleaned = re.sub(r"[#*_`>\[\]{}]", " ", text)
    parts = re.split(r"(?:\n+|(?<=[.!?;])\s+)", cleaned)
    statements = [" ".join(part.split()) for part in parts if len(" ".join(part.split())) > 3]
    return statements
