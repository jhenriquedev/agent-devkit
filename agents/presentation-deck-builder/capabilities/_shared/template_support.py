"""Shared helpers for presentation-deck-builder runners."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import re
import shutil
import zipfile


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
        f"    path: versions/{version}/template.pptx",
        f"    input_schema: versions/{version}/input-schema.xlsx",
        f"    created_at: {date.today().isoformat()}",
        "    notes: template registrado pelo agente",
        "",
    ]
    (directory / "template.yaml").write_text("\n".join(manifest), encoding="utf-8")


def append_changelog(root: Path, template_id: str, version: str, message: str) -> None:
    directory = template_dir(root, template_id)
    entry = f"## {date.today().isoformat()} - {version}\n\n- {message}\n\n"
    root_log = directory / "changelog.md"
    version_log = version_dir(root, template_id, version) / "changelog.md"
    previous = root_log.read_text(encoding="utf-8") if root_log.exists() else "# Changelog\n\n"
    root_log.write_text(previous.rstrip() + "\n\n" + entry, encoding="utf-8")
    version_log.write_text("# Changelog\n\n" + entry, encoding="utf-8")


def write_slide_map(root: Path, template_id: str, version: str) -> None:
    content = f"""id: {slugify(template_id)}.slide-map
version: {version}
slides:
  - id: cover
    slide: 1
    purpose: abertura
    required_fields: [title, subtitle, date]
  - id: content-01
    slide: 2
    purpose: conteudo
    required_fields: [slide_title, bullets]
  - id: closing
    slide: 3
    purpose: fechamento
    required_fields: [next_steps]
"""
    (version_dir(root, template_id, version) / "slide-map.yaml").write_text(content, encoding="utf-8")


def write_usage_notes(root: Path, template_id: str, version: str) -> None:
    content = f"""# Usage Notes

- Template: `{slugify(template_id)}`
- Version: `{version}`
- Preencha `input-schema.xlsx` ou `input-schema.md`.
- Se campos obrigatorios estiverem vazios, o agente deve perguntar antes de gerar.
"""
    (version_dir(root, template_id, version) / "usage-notes.md").write_text(content, encoding="utf-8")


def input_rows() -> list[list[str]]:
    return [
        ["slide_id", "slide", "slide_title", "section", "content_type", "required", "user_content", "notes"],
        ["cover", "1", "Titulo", "abertura", "text", "yes", "", ""],
        ["content-01", "2", "Conteudo principal", "conteudo", "bullets", "yes", "", ""],
        ["closing", "3", "Proximos passos", "fechamento", "bullets", "yes", "", ""],
    ]


def write_input_schema_md(root: Path, template_id: str, version: str) -> None:
    rows = input_rows()
    lines = [
        "# Input Schema",
        "",
        "| " + " | ".join(rows[0]) + " |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    (version_dir(root, template_id, version) / "input-schema.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_input_schema_xlsx(root: Path, template_id: str, version: str) -> None:
    target = version_dir(root, template_id, version) / "input-schema.xlsx"
    rows = input_rows()
    sheet_data = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            ref = f"{column_name(col_index)}{row_index}"
            cells.append(
                f'<c r="{ref}" t="inlineStr"><is><t>{xml_escape(value)}</t></is></c>'
            )
        sheet_data.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    worksheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_data)}</sheetData>'
        "</worksheet>"
    )
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("_rels/.rels", ROOT_RELS)
        archive.writestr("xl/workbook.xml", WORKBOOK)
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


def parse_template_manifest(path: Path) -> dict:
    data: dict[str, object] = {"versions": []}
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

WORKBOOK = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="slides" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""

WORKBOOK_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""
