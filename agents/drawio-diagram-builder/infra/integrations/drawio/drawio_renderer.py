"""Deterministic Draw.io XML renderer."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any
from xml.dom import minidom
from xml.etree import ElementTree

# layout_engine provides layout recommendations used by render_drawio
try:
    from layout_engine import recommend_layout  # type: ignore  # pylint: disable=import-error
    _LAYOUT_ENGINE_AVAILABLE = True
except ImportError:
    _LAYOUT_ENGINE_AVAILABLE = False

    def recommend_layout(diagram_type: str | None, node_count: int) -> dict:  # type: ignore
        direction = "top-to-bottom" if diagram_type in {"erd", "data_lineage"} else "left-to-right"
        return {"direction": direction, "split_recommended": node_count > 12}

try:
    import yaml as _yaml  # type: ignore
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

# Paths to template YAMLs (relative to this file: ../../templates/)
_TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "templates"
_SHAPE_LIBRARY_PATH = _TEMPLATES_DIR / "shape-library.yaml"
_STYLE_PRESETS_PATH = _TEMPLATES_DIR / "style-presets.yaml"


def _load_yaml_safe(path: Path) -> dict[str, Any]:
    """Load a YAML file safely; return empty dict on any failure."""
    if not path.exists():
        return {}
    try:
        if _YAML_AVAILABLE:
            import yaml as _yaml_mod  # type: ignore
            return _yaml_mod.safe_load(path.read_text(encoding="utf-8")) or {}
        # Fallback: very minimal YAML parser for simple key: "value" maps
        result: dict[str, Any] = {}
        current: dict[str, Any] = result
        parent_key: str | None = None
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.strip().startswith("#"):
                continue
            indent = len(line) - len(line.lstrip())
            stripped = line.strip()
            if ":" in stripped:
                key, _, value = stripped.partition(":")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if indent == 0:
                    result[key] = {}
                    current = result[key]
                    parent_key = key
                elif indent > 0 and parent_key:
                    current[key] = value
        return result
    except Exception:  # pylint: disable=broad-except
        return {}


def _get_shape_library() -> dict[str, str]:
    """Return shape style strings keyed by kind from shape-library.yaml."""
    data = _load_yaml_safe(_SHAPE_LIBRARY_PATH)
    shapes = data.get("shapes", {})
    if isinstance(shapes, dict):
        return {str(k): str(v) for k, v in shapes.items()}
    return {}


def _get_style_preset(family: str | None) -> dict[str, str]:
    """Return color/stroke preset dict for a diagram family from style-presets.yaml."""
    data = _load_yaml_safe(_STYLE_PRESETS_PATH)
    presets = data.get("presets", {})
    if not isinstance(presets, dict):
        return {}
    # Try exact family match, fallback to 'default'
    preset = presets.get(str(family)) if family else None
    if not preset:
        preset = presets.get("default", {})
    if isinstance(preset, dict):
        return {str(k): str(v) for k, v in preset.items()}
    return {}


# Determine diagram family from diagram_type
_FAMILY_MAP: dict[str, str] = {
    "architecture": "architecture",
    "cloud_architecture": "architecture",
    "c4_context": "architecture",
    "c4_container": "architecture",
    "c4_component": "architecture",
    "integration_architecture": "architecture",
    "erd": "data",
    "data_lineage": "data",
    "etl_flow": "data",
    "domain_relationships": "data",
    "flowchart": "product",
    "user_journey": "product",
    "service_blueprint": "product",
    "approval_flow": "product",
    "runbook": "product",
    "incident_flow": "product",
    "onboarding_flow": "product",
}


def _diagram_family(diagram_type: str | None) -> str | None:
    return _FAMILY_MAP.get(str(diagram_type).lower()) if diagram_type else None


DEFAULT_STYLE = {
    "node_fill": "#dae8fc",
    "node_stroke": "#6c8ebf",
    "group_fill": "#f5f5f5",
    "group_stroke": "#666666",
    "edge_stroke": "#555555",
}


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_spec_from_text(
    text: str,
    title: str | None = None,
    diagram_type: str | None = None,
    audience: str | None = None,
    detail_level: str | None = None,
) -> dict[str, Any]:
    statements = split_statements(text)
    selected = statements[:8] or ["Contexto nao informado"]
    nodes = []
    for index, statement in enumerate(selected, start=1):
        nodes.append(
            {
                "id": f"step-{index}",
                "label": compact_label(statement),
                "group": infer_group(statement, diagram_type),
                "kind": infer_kind(statement, diagram_type),
                "description": statement,
            }
        )
    edges = []
    for index in range(len(nodes) - 1):
        edges.append(
            {
                "source": nodes[index]["id"],
                "target": nodes[index + 1]["id"],
                "label": infer_edge_label(nodes[index]["label"], diagram_type),
            }
        )
    return {
        "title": title or infer_title(text, diagram_type),
        "diagram_type": diagram_type or "flowchart",
        "audience": audience or "tecnica e negocio",
        "detail_level": detail_level or "medium",
        "facts": selected,
        "assumptions": ["Fluxo inferido pela ordem em que os fatos aparecem nas fontes."],
        "open_questions": infer_open_questions(text),
        "nodes": nodes,
        "edges": edges,
    }


def render_drawio(spec: dict[str, Any]) -> str:
    _GROUP_ORIGINS.clear()
    title = str(spec.get("title") or "Diagram")
    nodes = list(spec.get("nodes") or [])
    edges = list(spec.get("edges") or [])
    # Resolve style preset from family — overrides DEFAULT_STYLE when available
    family = _diagram_family(spec.get("diagram_type"))
    preset = _get_style_preset(family) or DEFAULT_STYLE
    if not nodes:
        nodes = [{"id": "empty", "label": "Sem elementos mapeados", "group": "Lacunas"}]

    mxfile = ElementTree.Element(
        "mxfile",
        {
            "host": "AI DevKit",
            "agent": "drawio-diagram-builder",
            "version": "0.1.0",
            "modified": datetime.now(timezone.utc).isoformat(),
        },
    )
    diagram = ElementTree.SubElement(mxfile, "diagram", {"id": "diagram-1", "name": title[:60]})
    model = ElementTree.SubElement(
        diagram,
        "mxGraphModel",
        {
            "dx": "1200",
            "dy": "800",
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": "1600",
            "pageHeight": "1000",
            "math": "0",
            "shadow": "0",
        },
    )
    root = ElementTree.SubElement(model, "root")
    ElementTree.SubElement(root, "mxCell", {"id": "0"})
    ElementTree.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

    shape_library = _get_shape_library()
    layout = recommend_layout(spec.get("diagram_type"), len(nodes))
    add_title(root, title)
    groups = group_nodes(nodes)
    positions = layout_positions(nodes)
    group_bounds = compute_group_bounds(nodes, positions)
    for group, bounds in group_bounds.items():
        add_group(root, group, bounds, preset=preset)
    for node in nodes:
        add_node(root, node, positions[node["id"]], group=node.get("group"), preset=preset, shape_library=shape_library)
    for index, edge in enumerate(edges, start=1):
        add_edge(root, edge, index, preset=preset)
    if len(groups) > 1 or spec.get("open_questions") or layout.get("split_recommended"):
        add_legend(root, spec, group_bounds, split_recommended=layout.get("split_recommended", False))

    return pretty_xml(mxfile)


def add_title(root: ElementTree.Element, title: str) -> None:
    cell = ElementTree.SubElement(
        root,
        "mxCell",
        {
            "id": "diagram-title",
            "value": title,
            "style": "text;html=1;strokeColor=none;fillColor=none;fontSize=22;fontStyle=1;align=left;",
            "vertex": "1",
            "parent": "1",
        },
    )
    ElementTree.SubElement(cell, "mxGeometry", {"x": "40", "y": "20", "width": "760", "height": "40", "as": "geometry"})


def add_group(root: ElementTree.Element, group: str, bounds: tuple[int, int, int, int], preset: dict[str, str] | None = None) -> None:
    x, y, width, height = bounds
    style = preset or DEFAULT_STYLE
    cell = ElementTree.SubElement(
        root,
        "mxCell",
        {
            "id": f"group-{slug(group)}",
            "value": group,
            "style": f"swimlane;html=1;rounded=1;fillColor={style.get('group_fill', DEFAULT_STYLE['group_fill'])};strokeColor={style.get('group_stroke', DEFAULT_STYLE['group_stroke'])};fontStyle=1;",
            "vertex": "1",
            "parent": "1",
        },
    )
    ElementTree.SubElement(cell, "mxGeometry", {"x": str(x), "y": str(y), "width": str(width), "height": str(height), "as": "geometry"})


def add_node(root: ElementTree.Element, node: dict[str, Any], position: tuple[int, int], group: str | None = None, preset: dict[str, str] | None = None, shape_library: dict[str, str] | None = None) -> None:
    x, y = position
    parent = f"group-{slug(group)}" if group else "1"
    kind = str(node.get("kind") or "process")
    # Use shape from shape_library.yaml when available, fallback to hardcoded
    shape_style = (shape_library or {}).get(kind) or shape_for_kind(kind)
    if shape_style and not shape_style.endswith(";"):
        shape_style += ";"
    style = preset or DEFAULT_STYLE
    cell = ElementTree.SubElement(
        root,
        "mxCell",
        {
            "id": f"node-{slug(node.get('id'))}",
            "value": node_value(node),
            "style": f"{shape_style}fillColor={style.get('node_fill', DEFAULT_STYLE['node_fill'])};strokeColor={style.get('node_stroke', DEFAULT_STYLE['node_stroke'])};",
            "vertex": "1",
            "parent": parent,
        },
    )
    local_x = x
    local_y = y
    if group:
        gx, gy, _, _ = group_origin(group)
        local_x = x - gx
        local_y = y - gy
    ElementTree.SubElement(cell, "mxGeometry", {"x": str(local_x), "y": str(local_y), "width": "180", "height": "70", "as": "geometry"})


def add_edge(root: ElementTree.Element, edge: dict[str, Any], index: int, preset: dict[str, str] | None = None) -> None:
    style = preset or DEFAULT_STYLE
    cell = ElementTree.SubElement(
        root,
        "mxCell",
        {
            "id": f"edge-{index}",
            "value": str(edge.get("label") or ""),
            "style": f"endArrow=block;html=1;rounded=0;strokeWidth=2;strokeColor={style.get('edge_stroke', DEFAULT_STYLE['edge_stroke'])};",
            "edge": "1",
            "parent": "1",
            "source": f"node-{slug(edge.get('source'))}",
            "target": f"node-{slug(edge.get('target'))}",
        },
    )
    ElementTree.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})


def add_legend(root: ElementTree.Element, spec: dict[str, Any], group_bounds: dict[str, tuple[int, int, int, int]], split_recommended: bool = False) -> None:
    max_x = max((x + width for x, _, width, _ in group_bounds.values()), default=940)
    questions = spec.get("open_questions") or []
    value = "Legenda: caixas = etapas/componentes; setas = relacoes/fluxo"
    if questions:
        value += f"\nPerguntas abertas: {len(questions)}"
    if split_recommended:
        value += "\nAviso: diagrama denso — considere dividir em paginas."
    cell = ElementTree.SubElement(
        root,
        "mxCell",
        {
            "id": "diagram-legend",
            "value": value,
            "style": "shape=note;whiteSpace=wrap;html=1;backgroundOutline=1;fillColor=#fff2cc;strokeColor=#d6b656;",
            "vertex": "1",
            "parent": "1",
        },
    )
    ElementTree.SubElement(cell, "mxGeometry", {"x": str(max_x + 40), "y": "90", "width": "260", "height": "110", "as": "geometry"})


def layout_positions(nodes: list[dict[str, Any]]) -> dict[str, tuple[int, int]]:
    positions: dict[str, tuple[int, int]] = {}
    groups = group_nodes(nodes)
    for group_index, group in enumerate(groups):
        group_nodes_list = [node for node in nodes if (node.get("group") or "Fluxo") == group]
        base_x = 80
        base_y = 100 + group_index * 190
        for index, node in enumerate(group_nodes_list):
            positions[str(node["id"])] = (base_x + index * 240, base_y + 50)
    return positions


def compute_group_bounds(nodes: list[dict[str, Any]], positions: dict[str, tuple[int, int]]) -> dict[str, tuple[int, int, int, int]]:
    bounds: dict[str, tuple[int, int, int, int]] = {}
    for group in group_nodes(nodes):
        selected = [node for node in nodes if (node.get("group") or "Fluxo") == group]
        points = [positions[str(node["id"])] for node in selected]
        min_x = min(x for x, _ in points) - 30
        min_y = min(y for _, y in points) - 40
        max_x = max(x for x, _ in points) + 220
        max_y = max(y for _, y in points) + 100
        bounds[group] = (min_x, min_y, max_x - min_x, max_y - min_y)
        remember_group_origin(group, bounds[group])
    return bounds


_GROUP_ORIGINS: dict[str, tuple[int, int, int, int]] = {}


def remember_group_origin(group: str, bounds: tuple[int, int, int, int]) -> None:
    _GROUP_ORIGINS[group] = bounds


def group_origin(group: str) -> tuple[int, int, int, int]:
    return _GROUP_ORIGINS.get(group, (0, 0, 0, 0))


def group_nodes(nodes: list[dict[str, Any]]) -> list[str]:
    groups: list[str] = []
    for node in nodes:
        group = str(node.get("group") or "Fluxo")
        if group not in groups:
            groups.append(group)
    return groups


def shape_for_kind(kind: str) -> str:
    if kind in {"database", "data", "table", "entity"}:
        return "shape=cylinder3d;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;"
    if kind in {"decision", "rule"}:
        return "rhombus;whiteSpace=wrap;html=1;"
    if kind in {"actor", "user"}:
        return "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;"
    return "rounded=1;whiteSpace=wrap;html=1;"


def node_value(node: dict[str, Any]) -> str:
    label = str(node.get("label") or node.get("id") or "Node")
    attributes = node.get("attributes") or []
    if attributes:
        return label + "<br/><hr/>" + "<br/>".join(str(attribute) for attribute in attributes)
    return label


def add_refinement_note(xml_text: str, feedback: str) -> str:
    root = ElementTree.fromstring(xml_text)
    graph_root = root.find(".//root")
    if graph_root is None:
        raise ValueError("invalid drawio: missing mxGraphModel/root")
    cell = ElementTree.SubElement(
        graph_root,
        "mxCell",
        {
            "id": "refinement-note",
            "value": f"Refinamento solicitado: {feedback}",
            "style": "shape=note;whiteSpace=wrap;html=1;backgroundOutline=1;fillColor=#fff2cc;strokeColor=#d6b656;",
            "vertex": "1",
            "parent": "1",
        },
    )
    ElementTree.SubElement(cell, "mxGeometry", {"x": "40", "y": "850", "width": "520", "height": "100", "as": "geometry"})
    return pretty_xml(root)


def pretty_xml(element: ElementTree.Element) -> str:
    rough = ElementTree.tostring(element, encoding="utf-8")
    return minidom.parseString(rough).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


def split_statements(text: str) -> list[str]:
    cleaned = re.sub(r"[#*_`>\[\]{}]", " ", text or "")
    parts = re.split(r"(?:\n+|(?<=[.!?;])\s+)", cleaned)
    return [" ".join(part.split()) for part in parts if len(" ".join(part.split())) > 3]


def compact_label(text: str, max_len: int = 48) -> str:
    words = text.split()
    label = " ".join(words[:8])
    if len(label) > max_len:
        label = label[: max_len - 1].rstrip() + "..."
    return label


def infer_title(text: str, diagram_type: str | None) -> str:
    first = split_statements(text)[:1]
    if first:
        return compact_label(first[0], 60)
    return f"Diagrama {diagram_type or 'Draw.io'}"


def infer_group(statement: str, diagram_type: str | None) -> str:
    lowered = statement.lower()
    if diagram_type in {"architecture", "cloud_architecture", "c4_container"}:
        if any(term in lowered for term in ["usuario", "cliente", "user"]):
            return "Atores"
        if any(term in lowered for term in ["banco", "database", "dados", "data"]):
            return "Dados"
        return "Sistemas"
    if any(term in lowered for term in ["usuario", "cliente", "operador"]):
        return "Usuario"
    if any(term in lowered for term in ["sistema", "api", "servico", "serviço"]):
        return "Sistema"
    return "Fluxo"


def infer_kind(statement: str, diagram_type: str | None) -> str:
    lowered = statement.lower()
    if diagram_type == "erd" or any(term in lowered for term in ["tabela", "entidade", "banco"]):
        return "entity"
    if any(term in lowered for term in ["decide", "se ", "caso", "quando"]):
        return "decision"
    if any(term in lowered for term in ["usuario", "cliente", "ator"]):
        return "actor"
    return "process"


def infer_edge_label(_label: str, diagram_type: str | None) -> str:
    if diagram_type == "architecture":
        return "integra"
    if diagram_type == "erd":
        return "relaciona"
    return "proximo"


def infer_open_questions(text: str) -> list[str]:
    lowered = (text or "").lower()
    questions: list[str] = []
    if "audiencia" not in lowered and "público" not in lowered and "publico" not in lowered:
        questions.append("Quem e a audiencia principal do diagrama?")
    if "escopo" not in lowered:
        questions.append("Qual e o escopo e o fora de escopo?")
    return questions


def slug(value: Any) -> str:
    slugged = re.sub(r"[^A-Za-z0-9_-]+", "-", str(value or "item")).strip("-")
    return slugged or "item"
