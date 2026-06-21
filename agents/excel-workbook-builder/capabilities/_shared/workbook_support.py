"""Shared helpers for excel-workbook-builder runners."""

from __future__ import annotations

import csv
from datetime import date
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any
import unicodedata
import zipfile
import xml.etree.ElementTree as ET


AGENT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_TEMPLATES_ROOT = AGENT_DIR / "templates"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug or "template"


def resolve_templates_root(value: str | None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    return DEFAULT_TEMPLATES_ROOT


def template_dir(root: Path, template_id: str) -> Path:
    return root / slugify(template_id)


def version_dir(root: Path, template_id: str, version: str) -> Path:
    return template_dir(root, template_id) / "versions" / version


def ensure_write_allowed(path: Path, yes: bool, label: str) -> None:
    if yes:
        return
    answer = input(f"Posso salvar {label} em {path}? [s/N] ").strip().lower()
    if answer not in {"s", "sim", "y", "yes"}:
        raise ValueError("gravacao nao autorizada")


def copy_template(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def write_template_manifest(
    root: Path,
    template_id: str,
    name: str,
    version: str,
    status: str,
) -> None:
    directory = template_dir(root, template_id)
    current_version = version if status == "validated" else ""
    manifest = [
        f"id: {slugify(template_id)}",
        f"name: {name}",
        f"current_version: {current_version}",
        "versions:",
        f"  - version: {version}",
        f"    status: {status}",
        f"    path: versions/{version}/template.xlsx",
        f"    input_schema: versions/{version}/input-schema.xlsx",
        f"    created_at: {date.today().isoformat()}",
        "    notes: template registrado pelo agente",
        "",
    ]
    (directory / "template.yaml").write_text("\n".join(manifest), encoding="utf-8")


def parse_template_manifest(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {"versions": []}
    current_version: dict[str, str] | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            if key != "versions":
                data[key] = value.strip()
            continue
        if stripped.startswith("- version:"):
            current_version = {"version": stripped.split(":", 1)[1].strip()}
            data["versions"].append(current_version)
            continue
        if current_version is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current_version[key.strip()] = value.strip()
    return data


def append_changelog(root: Path, template_id: str, version: str, message: str) -> None:
    directory = template_dir(root, template_id)
    entry = f"## {date.today().isoformat()} - {version}\n\n- {message}\n\n"
    root_log = directory / "changelog.md"
    version_log = version_dir(root, template_id, version) / "changelog.md"
    previous = root_log.read_text(encoding="utf-8") if root_log.exists() else "# Changelog\n\n"
    root_log.write_text(previous.rstrip() + "\n\n" + entry, encoding="utf-8")
    version_log.write_text("# Changelog\n\n" + entry, encoding="utf-8")


def write_sheet_map(root: Path, template_id: str, version: str) -> None:
    content = f"""id: {slugify(template_id)}.sheet-map
version: {version}
sheets:
  - name: Inputs
    purpose: dados preenchidos pelo usuario
    required_columns: [sheet, range, field, value, notes]
  - name: Data
    purpose: dados normalizados
  - name: Summary
    purpose: resumo executivo e quality gates
"""
    (version_dir(root, template_id, version) / "sheet-map.yaml").write_text(
        content,
        encoding="utf-8",
    )


def write_usage_notes(root: Path, template_id: str, version: str) -> None:
    content = f"""# Usage Notes

- Template: `{slugify(template_id)}`
- Version: `{version}`
- Preencha `input-schema.xlsx` ou `input-schema.md`.
- Se campos obrigatorios estiverem vazios, o agente deve perguntar antes de gerar.
- Campos numericos devem ser preenchidos como numeros, nao texto formatado.
"""
    (version_dir(root, template_id, version) / "usage-notes.md").write_text(
        content,
        encoding="utf-8",
    )


def input_rows() -> list[list[str]]:
    return [
        ["sheet", "range", "field", "content_type", "required", "user_content", "notes"],
        ["Inputs", "A2", "dataset_name", "text", "yes", "", ""],
        ["Inputs", "B2", "source_file", "text", "yes", "", ""],
        ["Inputs", "C2", "refresh_date", "date", "no", "", "yyyy-mm-dd"],
        ["Inputs", "D2", "business_notes", "text", "no", "", ""],
    ]


def write_input_schema_md(root: Path, template_id: str, version: str) -> None:
    rows = input_rows()
    lines = [
        "# Input Schema",
        "",
        "| " + " | ".join(rows[0]) + " |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    (version_dir(root, template_id, version) / "input-schema.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_input_schema_xlsx(root: Path, template_id: str, version: str) -> None:
    target = version_dir(root, template_id, version) / "input-schema.xlsx"
    create_minimal_xlsx(target, input_rows(), "Input")


def create_minimal_xlsx(target: Path, rows: list[list[Any]], sheet_name: str = "Sheet1") -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    sheet_data = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            ref = f"{column_name(col_index)}{row_index}"
            cells.append(
                f'<c r="{ref}" t="inlineStr"><is><t>{xml_escape(str(value))}</t></is></c>'
            )
        sheet_data.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    worksheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_data)}</sheetData>'
        "</worksheet>"
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets><sheet name="{xml_escape(sheet_name)}" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("_rels/.rels", ROOT_RELS)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", WORKBOOK_RELS)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)


def column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def load_tabular_file(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "rows" in data:
            return normalize_dataset(data, source=str(path))
        if isinstance(data, list):
            return normalize_dataset({"rows": data}, source=str(path))
        raise ValueError("json source must contain rows or be a list")
    if suffix in {".csv", ".tsv", ".txt"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        with path.open(encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file, delimiter=delimiter))
        return normalize_dataset({"rows": rows}, source=str(path))
    if suffix in {".md", ".markdown"}:
        rows = parse_markdown_table(path.read_text(encoding="utf-8"))
        return normalize_dataset({"rows": rows}, source=str(path))
    if suffix in {".xlsx", ".xlsm", ".xltx"}:
        return read_xlsx_dataset(path)
    raise ValueError(f"unsupported source format: {suffix}")


def parse_markdown_table(text: str) -> list[dict[str, Any]]:
    table_lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    if len(table_lines) < 2:
        return []
    headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows = []
    for line in table_lines[2:]:
        values = [cell.strip() for cell in line.strip("|").split("|")]
        if len(values) == len(headers):
            rows.append(dict(zip(headers, values, strict=True)))
    return rows


def normalize_dataset(data: dict[str, Any], *, source: str | None = None) -> dict[str, Any]:
    rows = data.get("rows") or []
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    columns = data.get("columns")
    if not columns:
        seen: list[str] = []
        for row in rows:
            if isinstance(row, dict):
                for key in row:
                    if key not in seen:
                        seen.append(str(key))
        columns = seen
    normalized_rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized_rows.append({str(column): infer_value(row.get(column)) for column in columns})
    return {
        "source": source or data.get("source") or "",
        "columns": [str(column) for column in columns],
        "rows": normalized_rows,
        "row_count": len(normalized_rows),
    }


def normalize_column_names(dataset: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_dataset(dataset, source=dataset.get("source"))
    mapping = {column: slug_column_name(column) for column in normalized["columns"]}
    return {
        "source": normalized.get("source", ""),
        "columns": [mapping[column] for column in normalized["columns"]],
        "rows": [
            {mapping[column]: row.get(column) for column in normalized["columns"]}
            for row in normalized["rows"]
        ],
        "row_count": normalized["row_count"],
        "column_mapping": mapping,
    }


def slug_column_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return text or "column"


def infer_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (int, float, bool)):
        return value
    text = str(value).strip()
    if text == "":
        return None
    normalized = text.replace(",", ".")
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if re.fullmatch(r"-?\d+[\.,]\d+", text):
        return float(normalized)
    return text


def read_xlsx_dataset(path: Path, sheet_name: str | None = None) -> dict[str, Any]:
    workbook = read_xlsx_workbook(path)
    sheets = workbook["sheets"]
    if not sheets:
        return {"source": str(path), "columns": [], "rows": [], "row_count": 0}
    selected = None
    for sheet in sheets:
        if sheet_name is None or sheet["name"] == sheet_name:
            selected = sheet
            break
    if selected is None:
        available = ", ".join(sheet["name"] for sheet in sheets)
        raise ValueError(f"sheet not found: {sheet_name}. available: {available}")
    matrix = selected["values"]
    if not matrix:
        return {"source": str(path), "columns": [], "rows": [], "row_count": 0}
    headers = [str(value) if value is not None else f"column_{index + 1}" for index, value in enumerate(matrix[0])]
    rows = []
    for raw_row in matrix[1:]:
        if not any(value is not None for value in raw_row):
            continue
        padded = raw_row + [None] * (len(headers) - len(raw_row))
        rows.append(dict(zip(headers, padded[: len(headers)], strict=True)))
    return normalize_dataset({"source": str(path), "columns": headers, "rows": rows}, source=str(path))


def read_xlsx_workbook(path: Path) -> dict[str, Any]:
    if not zipfile.is_zipfile(path):
        raise ValueError("workbook is not a valid zip-based xlsx file")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        shared_strings = read_shared_strings(archive)
        sheet_infos = read_sheet_infos(archive)
        sheets = []
        for sheet in sheet_infos:
            target = sheet["target"].lstrip("/")
            if not target.startswith("xl/"):
                target = f"xl/{target}"
            if target not in names:
                continue
            sheets.append(
                {
                    "name": sheet["name"],
                    "path": target,
                    "values": read_sheet_values(archive, target, shared_strings),
                }
            )
    return {"file": str(path), "sheets": sheets, "part_count": len(names)}


def read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    values = []
    for item in root.findall(f".//{{{XML_MAIN_NS}}}si"):
        text = "".join(node.text or "" for node in item.findall(f".//{{{XML_MAIN_NS}}}t"))
        values.append(text)
    return values


def read_sheet_infos(archive: zipfile.ZipFile) -> list[dict[str, str]]:
    root = ET.fromstring(archive.read("xl/workbook.xml"))
    rels_root = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    rels = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels_root.findall(f".//{{{XML_REL_NS}}}Relationship")
    }
    sheets = []
    for sheet in root.findall(f".//{{{XML_MAIN_NS}}}sheet"):
        rel_id = sheet.attrib.get(f"{{{XML_DOC_REL_NS}}}id")
        if rel_id and rel_id in rels:
            sheets.append({"name": sheet.attrib.get("name", ""), "target": rels[rel_id]})
    return sheets


def read_sheet_values(
    archive: zipfile.ZipFile,
    sheet_path: str,
    shared_strings: list[str],
) -> list[list[Any]]:
    root = ET.fromstring(archive.read(sheet_path))
    rows: list[list[Any]] = []
    for row in root.findall(f".//{{{XML_MAIN_NS}}}row"):
        values: list[Any] = []
        for cell in row.findall(f"{{{XML_MAIN_NS}}}c"):
            ref = cell.attrib.get("r", "")
            col_index = column_index_from_ref(ref)
            while len(values) < col_index:
                values.append(None)
            values.append(read_cell_value(cell, shared_strings))
        rows.append(values)
    return rows


def read_cell_value(cell: ET.Element, shared_strings: list[str]) -> Any:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(f".//{{{XML_MAIN_NS}}}t")) or None
    value = cell.find(f"{{{XML_MAIN_NS}}}v")
    if value is None or value.text is None:
        return None
    if cell_type == "s":
        index = int(value.text)
        return shared_strings[index] if 0 <= index < len(shared_strings) else None
    if cell_type == "b":
        return value.text == "1"
    return infer_value(value.text)


def column_index_from_ref(ref: str) -> int:
    letters = re.sub(r"[^A-Z]", "", ref.upper())
    index = 0
    for letter in letters:
        index = index * 26 + (ord(letter) - 64)
    return max(index - 1, 0)


def generate_workbook_from_dataset(
    dataset: dict[str, Any],
    output: Path,
    *,
    title: str,
    summary: dict[str, Any] | None = None,
) -> None:
    payload = {
        "title": title,
        "dataset": normalize_dataset(dataset, source=dataset.get("source")),
        "summary": summary or {},
    }
    run_workbook_builder(payload, output)


def run_workbook_builder(payload: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="excel-workbook-builder-") as tmpdir:
        workspace = Path(tmpdir)
        ensure_artifact_workspace(workspace)
        input_path = workspace / "workbook-input.json"
        script_path = workspace / "build-workbook.mjs"
        input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        script_path.write_text(WORKBOOK_BUILDER_JS, encoding="utf-8")
        result = subprocess.run(
            [str(resolve_node()), str(script_path), str(input_path), str(output)],
            cwd=workspace,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            raise ValueError(result.stderr.strip() or f"node failed: {result.returncode}")


def run_node_script(script: str, args: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="excel-workbook-builder-") as tmpdir:
        workspace = Path(tmpdir)
        ensure_artifact_workspace(workspace)
        script_path = workspace / "script.mjs"
        script_path.write_text(script, encoding="utf-8")
        result = subprocess.run(
            [str(resolve_node()), str(script_path), *args],
            cwd=workspace,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            raise ValueError(result.stderr.strip() or f"node failed: {result.returncode}")


def render_workbook_preview(
    workbook: Path,
    output: Path,
    *,
    sheet: str | None = None,
    cell_range: str | None = None,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run_node_script(
        RENDER_WORKBOOK_JS,
        [
            str(workbook),
            str(output),
            sheet or "",
            cell_range or "",
        ],
    )


def apply_formula_plan(workbook: Path, formula_plan: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run_node_script(APPLY_FORMULA_PLAN_JS, [str(workbook), str(formula_plan), str(output)])


def ensure_artifact_workspace(workspace: Path) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    package_json = workspace / "package.json"
    package_json.write_text('{"private":true,"type":"module"}\n', encoding="utf-8")
    node_modules_source = resolve_node_modules()
    node_modules_target = workspace / "node_modules"
    if node_modules_target.exists():
        return
    if os.name == "nt":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(node_modules_target), str(node_modules_source)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    else:
        os.symlink(node_modules_source, node_modules_target, target_is_directory=True)


def resolve_node_modules() -> Path:
    env_value = os.environ.get("CODEX_NODE_MODULES") or os.environ.get("NODE_MODULES")
    candidates = []
    if env_value:
        candidates.append(Path(env_value).expanduser())
    candidates.append(
        Path.home()
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "node"
        / "node_modules"
    )
    for candidate in candidates:
        if (candidate / "@oai" / "artifact-tool").exists():
            return candidate.resolve()
    raise ValueError("@oai/artifact-tool node_modules not found")


def resolve_node() -> Path:
    executable = "node.exe" if os.name == "nt" else "node"
    env_value = os.environ.get("CODEX_NODE")
    candidates = []
    if env_value:
        candidates.append(Path(env_value).expanduser())
    candidates.append(
        Path.home()
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "node"
        / "bin"
        / executable
    )
    found = shutil.which("node")
    if found:
        candidates.append(Path(found))
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    raise ValueError("node executable not found")


def inspect_xlsx(path: Path) -> dict[str, Any]:
    if not zipfile.is_zipfile(path):
        raise ValueError("workbook is not a valid zip-based xlsx file")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        xml_text = "\n".join(
            archive.read(name).decode("utf-8", errors="replace")
            for name in names
            if name.endswith(".xml")
        )
    error_markers = ["#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A"]
    found_errors = [marker for marker in error_markers if marker in xml_text]
    workbook = read_xlsx_workbook(path)
    return {
        "file": str(path),
        "part_count": len(names),
        "worksheet_count": len([name for name in names if name.startswith("xl/worksheets/")]),
        "worksheets": [
            {"name": sheet["name"], "rows": len(sheet["values"])}
            for sheet in workbook["sheets"]
        ],
        "formula_errors": found_errors,
    }


XML_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
XML_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
XML_DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

WORKBOOK_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""

WORKBOOK_BUILDER_JS = r'''
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";
import fs from "node:fs/promises";

function asMatrix(headers, rows) {
  return [
    headers,
    ...rows.map((row) => headers.map((header) => row[header] ?? null)),
  ];
}

async function main() {
  const [inputPath, outputPath] = process.argv.slice(2);
  const payload = JSON.parse(await fs.readFile(inputPath, "utf8"));
  const dataset = payload.dataset || { columns: [], rows: [] };
  const columns = dataset.columns || [];
  const rows = dataset.rows || [];
  const workbook = Workbook.create();

  const summary = workbook.worksheets.add("Summary");
  summary.showGridLines = false;
  summary.getRange("A1:D1").values = [[payload.title || "Workbook"]];
  summary.getRange("A3:B7").values = [
    ["Metric", "Value"],
    ["Rows", rows.length],
    ["Columns", columns.length],
    ["Source", dataset.source || "-"],
    ["Generated by", "excel-workbook-builder"],
  ];
  summary.getRange("A1:D1").format.font = { bold: true, size: 16, color: "#1F2937" };
  summary.getRange("A3:B3").format.font = { bold: true, color: "#FFFFFF" };
  summary.getRange("A3:B3").format.fill = { color: "#2563EB" };
  summary.getRange("A3:B7").format.borders = { preset: "all", style: "thin", color: "#D9D9D9" };
  summary.getRange("A:B").format.autofitColumns();

  const data = workbook.worksheets.add("Data");
  data.showGridLines = false;
  if (columns.length > 0) {
    const matrix = asMatrix(columns, rows);
    const range = data.getRangeByIndexes(0, 0, matrix.length, columns.length);
    range.values = matrix;
    data.getRangeByIndexes(0, 0, 1, columns.length).format.font = { bold: true, color: "#FFFFFF" };
    data.getRangeByIndexes(0, 0, 1, columns.length).format.fill = { color: "#111827" };
    range.format.borders = { preset: "all", style: "thin", color: "#E5E7EB" };
    range.format.autofitColumns();
    data.freezePanes.freezeRows(1);
  } else {
    data.getRange("A1").values = [["No data"]];
  }

  if (payload.summary && Object.keys(payload.summary).length > 0) {
    const quality = workbook.worksheets.add("Quality");
    quality.showGridLines = false;
    const entries = Object.entries(payload.summary);
    quality.getRangeByIndexes(0, 0, entries.length + 1, 2).values = [
      ["Metric", "Value"],
      ...entries.map(([key, value]) => [key, value]),
    ];
    quality.getRange("A1:B1").format.font = { bold: true, color: "#FFFFFF" };
    quality.getRange("A1:B1").format.fill = { color: "#047857" };
    quality.getRange("A:B").format.autofitColumns();
  }

  await fs.mkdir(new URL(".", `file://${outputPath}`).pathname, { recursive: true });
  const xlsx = await SpreadsheetFile.exportXlsx(workbook);
  await xlsx.save(outputPath);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
'''

RENDER_WORKBOOK_JS = r'''
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";
import fs from "node:fs/promises";

async function main() {
  const [workbookPath, outputPath, sheetName, range] = process.argv.slice(2);
  const input = await FileBlob.load(workbookPath);
  const workbook = await SpreadsheetFile.importXlsx(input);
  const options = { format: "png", scale: 1, autoCrop: "all" };
  if (sheetName) options.sheetName = sheetName;
  if (range) options.range = range;
  const preview = await workbook.render(options);
  await fs.writeFile(outputPath, new Uint8Array(await preview.arrayBuffer()));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
'''

APPLY_FORMULA_PLAN_JS = r'''
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";
import fs from "node:fs/promises";

async function main() {
  const [workbookPath, planPath, outputPath] = process.argv.slice(2);
  const input = await FileBlob.load(workbookPath);
  const workbook = await SpreadsheetFile.importXlsx(input);
  const plan = JSON.parse(await fs.readFile(planPath, "utf8"));
  const sheetName = plan.sheet || "Calculations";
  const sheet = workbook.worksheets.getOrAdd(sheetName);
  sheet.showGridLines = false;
  for (const item of plan.cells || []) {
    const range = sheet.getRange(item.cell);
    if (item.formula) {
      range.formulas = [[item.formula]];
    } else {
      range.values = [[item.value ?? item.label ?? ""]];
    }
  }
  if (plan.cells && plan.cells.length > 0) {
    sheet.getRange("A:Z").format.autofitColumns();
  }
  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(outputPath);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
'''
