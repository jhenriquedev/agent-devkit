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


def set_current_version(root: Path, template_id: str, new_current: str) -> None:
    """Update current_version in template.yaml."""
    directory = template_dir(root, template_id)
    manifest_path = directory / "template.yaml"
    manifest = parse_template_manifest_raw(manifest_path)

    lines = manifest_path.read_text(encoding="utf-8").splitlines()
    updated = []
    for line in lines:
        if line.startswith("current_version:"):
            updated.append(f"current_version: {new_current}")
        else:
            updated.append(line)
    manifest_path.write_text("\n".join(updated) + "\n", encoding="utf-8")


def set_version_status(root: Path, template_id: str, version: str, status: str) -> None:
    """Update the status of a specific version entry in template.yaml."""
    directory = template_dir(root, template_id)
    manifest_path = directory / "template.yaml"

    lines = manifest_path.read_text(encoding="utf-8").splitlines()
    updated = []
    in_target_version = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- version:") and stripped.split(":", 1)[1].strip() == version:
            in_target_version = True
        elif stripped.startswith("- version:"):
            in_target_version = False
        if in_target_version and stripped.startswith("status:"):
            indent = len(line) - len(line.lstrip())
            updated.append(" " * indent + f"status: {status}")
            continue
        updated.append(line)
    manifest_path.write_text("\n".join(updated) + "\n", encoding="utf-8")


def add_version_to_manifest(
    root: Path,
    template_id: str,
    version: str,
    status: str,
) -> None:
    """Append a new version entry to template.yaml."""
    directory = template_dir(root, template_id)
    manifest_path = directory / "template.yaml"
    existing = manifest_path.read_text(encoding="utf-8").rstrip()
    new_entry = (
        f"  - version: {version}\n"
        f"    status: {status}\n"
        f"    path: versions/{version}/template.pptx\n"
        f"    input_schema: versions/{version}/input-schema.xlsx\n"
        f"    created_at: {date.today().isoformat()}\n"
        "    notes: versao criada pelo agente"
    )
    manifest_path.write_text(existing + "\n" + new_entry + "\n", encoding="utf-8")


def copy_version(
    root: Path,
    template_id: str,
    base_version: str,
    new_version: str,
    source_template: Path | None = None,
) -> None:
    """Create a new version directory by copying a base version."""
    base_dir = version_dir(root, template_id, base_version)
    new_dir = version_dir(root, template_id, new_version)
    new_dir.mkdir(parents=True, exist_ok=False)

    for item in base_dir.iterdir():
        target = new_dir / item.name
        if item.is_file():
            shutil.copyfile(item, target)

    if source_template is not None:
        shutil.copyfile(source_template, new_dir / "template.pptx")


def parse_template_manifest_raw(path: Path) -> dict:
    return parse_template_manifest(path)


def update_template_catalog(catalog_path: Path, template_id: str, name: str, version: str, status: str) -> None:
    """Upsert an entry in template-catalog.yaml."""
    if not catalog_path.exists():
        return  # catalog is optional

    text = catalog_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    new_entry_lines = [
        f"  - id: {template_id}",
        f"    name: {name}",
        f"    current_version: {version if status == 'validated' else ''}",
        f"    status: {status}",
    ]

    # Check if template already in catalog
    in_templates = False
    templates_start = -1
    entry_start = -1
    entry_end = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "templates:":
            in_templates = True
            templates_start = i
            continue
        if in_templates:
            if stripped.startswith("- id:") and stripped.split(":", 1)[1].strip() == template_id:
                entry_start = i
                continue
            if entry_start >= 0 and stripped.startswith("- id:"):
                entry_end = i
                break

    if entry_start >= 0:
        # Replace existing entry
        if entry_end < 0:
            entry_end = len(lines)
        # Find end of this entry block
        end = entry_start + 1
        while end < len(lines) and (not lines[end].strip().startswith("- id:") or end == entry_start):
            if lines[end].strip().startswith("- id:") and end != entry_start:
                break
            end += 1
        updated = lines[:entry_start] + new_entry_lines + lines[end:]
    else:
        # Append new entry
        if templates_start >= 0:
            # Find end of templates block
            insert_at = len(lines)
            for i in range(templates_start + 1, len(lines)):
                stripped = lines[i].strip()
                if stripped and not stripped.startswith("-") and not stripped.startswith(" "):
                    insert_at = i
                    break
            updated = lines[:insert_at] + new_entry_lines + lines[insert_at:]
        else:
            updated = lines + ["templates:"] + new_entry_lines

    catalog_path.write_text("\n".join(updated) + "\n", encoding="utf-8")


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
