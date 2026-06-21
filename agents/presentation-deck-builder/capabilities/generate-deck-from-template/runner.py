#!/usr/bin/env python3
"""Runner for presentation-deck-builder/generate-deck-from-template."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from template_support import (  # noqa: E402
    parse_template_manifest,
    resolve_templates_root,
    slugify,
    template_dir,
    version_dir,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a PowerPoint deck from template input")
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--template-version")
    parser.add_argument("--templates-root")
    parser.add_argument("--output")
    parser.add_argument("--title")
    parser.add_argument("--subtitle")
    args = parser.parse_args()

    try:
        template_id = slugify(args.template_id)
        input_path = Path(args.input).expanduser().resolve()
        if not input_path.exists():
            raise ValueError(f"input not found: {input_path}")

        root = resolve_templates_root(args.templates_root)
        manifest_path = template_dir(root, template_id) / "template.yaml"
        template_version = resolve_template_version(manifest_path, args.template_version)
        if manifest_path.exists() and template_version:
            expected_version_dir = version_dir(root, template_id, template_version)
            if not expected_version_dir.exists():
                raise ValueError(f"template version not found: {template_id} {template_version}")

        deck = load_deck_input(input_path)
        if args.title:
            deck["title"] = args.title
        if args.subtitle:
            deck["subtitle"] = args.subtitle
        deck.setdefault("title", "KPIs do Projeto")
        deck.setdefault("subtitle", "Resumo executivo")
        deck["template_id"] = template_id
        deck["template_version"] = template_version or "generated"

        output_path = resolve_output_path(args.output, template_id)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="presentation-deck-builder-") as tmpdir:
            workspace = Path(tmpdir)
            input_json = workspace / "deck-input.json"
            script_path = workspace / "generate-deck.mjs"
            preview_path = output_path.with_suffix(".png")
            layout_path = output_path.with_suffix(".layout.json")
            input_json.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
            script_path.write_text(render_js(), encoding="utf-8")
            setup_artifact_workspace(workspace)
            run_node(script_path, input_json, output_path, preview_path, layout_path)

        print(f"Deck gerado: {output_path}")
        print(f"Preview: {preview_path}")
        print(f"Layout: {layout_path}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def resolve_template_version(manifest_path: Path, requested: str | None) -> str:
    if requested:
        return requested
    if not manifest_path.exists():
        return ""
    manifest = parse_template_manifest(manifest_path)
    current = str(manifest.get("current_version") or "")
    if current:
        return current
    versions = manifest.get("versions", [])
    if versions:
        return str(versions[-1].get("version") or "")
    return ""


def load_deck_input(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("json input must be an object")
        return normalize_deck_data(data)
    return parse_markdown_report(path.read_text(encoding="utf-8"))


def normalize_deck_data(data: dict[str, Any]) -> dict[str, Any]:
    metrics = data.get("metrics") or []
    normalized_metrics = []
    for item in metrics:
        if isinstance(item, dict):
            normalized_metrics.append(
                {
                    "label": str(item.get("label") or ""),
                    "value": str(item.get("value") or ""),
                }
            )
    states = data.get("state_breakdown") or {}
    normalized_states = {
        str(key): int(value)
        for key, value in states.items()
        if isinstance(value, int) or str(value).isdigit()
    }
    highlights = [str(item) for item in data.get("highlights") or [] if str(item).strip()]
    return {
        "title": str(data.get("title") or ""),
        "subtitle": str(data.get("subtitle") or ""),
        "metrics": normalized_metrics,
        "state_breakdown": normalized_states,
        "highlights": highlights,
        "footer": str(data.get("footer") or ""),
    }


def parse_markdown_report(text: str) -> dict[str, Any]:
    summary: dict[str, str] = {}
    states: dict[str, int] = {}
    section = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## Executive Summary"):
            section = "summary"
            continue
        if line.startswith("### By State"):
            section = "state"
            continue
        if line.startswith("### ") or line.startswith("## "):
            section = ""
            continue
        match = re.match(r"^- ([^:]+):\s*(.+)$", line)
        if not match:
            continue
        key = match.group(1).strip()
        value = match.group(2).strip()
        if section == "summary":
            summary[key] = value
        elif section == "state" and value.isdigit():
            states[key] = int(value)

    metrics = [
        {"label": "Cards analisados", "value": summary.get("Total de cards", "0")},
        {"label": "Sem responsável", "value": summary.get("Without assignee", "0")},
        {
            "label": "Sem critérios de aceite",
            "value": summary.get("Without acceptance criteria", "0"),
        },
        {"label": "Com anexos", "value": summary.get("With attachments", "0")},
    ]
    highlights = []
    if summary.get("Query reached limit", "").lower() == "true":
        highlights.append("Consulta atingiu o limite configurado; há mais cards no projeto.")
    if summary.get("Without description") not in {"", None, "0"}:
        highlights.append(f"Cards sem descrição: {summary.get('Without description')}.")
    return {
        "title": "KPIs Sustentação - Azure DevOps",
        "subtitle": "Amostra dos cards retornados pelo agente Azure DevOps",
        "metrics": metrics,
        "state_breakdown": states,
        "highlights": highlights,
        "footer": "Fonte: azure-devops-orchestrator/generate-cards-report.",
    }


def resolve_output_path(value: str | None, template_id: str) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    return (
        Path.cwd()
        / "docs"
        / "generated"
        / "presentation-deck-builder"
        / f"{template_id}-deck.pptx"
    ).resolve()


def setup_artifact_workspace(workspace: Path) -> None:
    skill_dir = resolve_presentations_skill_dir()
    setup_script = skill_dir / "container_tools" / "setup_artifact_tool_workspace.mjs"
    node = resolve_node()
    subprocess.run(
        [str(node), str(setup_script), "--workspace", str(workspace)],
        cwd=workspace,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def resolve_presentations_skill_dir() -> Path:
    env_value = os.environ.get("PRESENTATIONS_SKILL_DIR")
    candidates = []
    if env_value:
        candidates.append(Path(env_value).expanduser())
    base = Path.home() / ".codex" / "plugins" / "cache" / "openai-primary-runtime" / "presentations"
    candidates.extend(sorted(base.glob("*/skills/presentations"), reverse=True))
    for candidate in candidates:
        if (candidate / "artifact_tool" / "API_QUICK_START.md").exists():
            return candidate.resolve()
    raise ValueError("presentations skill with artifact_tool was not found")


def resolve_node() -> Path:
    executable = "node.exe" if os.name == "nt" else "node"
    bundled = (
        Path.home()
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "node"
        / "bin"
        / executable
    )
    if bundled.exists():
        return bundled
    found = shutil.which("node")
    if found:
        return Path(found)
    raise ValueError("node executable was not found")


def run_node(
    script_path: Path,
    input_path: Path,
    output_path: Path,
    preview_path: Path,
    layout_path: Path,
) -> None:
    node = resolve_node()
    result = subprocess.run(
        [
            str(node),
            str(script_path),
            str(input_path),
            str(output_path),
            str(preview_path),
            str(layout_path),
        ],
        cwd=script_path.parent,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or f"node failed: {result.returncode}")


def render_js() -> str:
    return r'''
import fs from "node:fs/promises";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

async function writeBlob(path, blob) {
  await fs.writeFile(path, new Uint8Array(await blob.arrayBuffer()));
}

function asText(value, fallback = "") {
  if (value === undefined || value === null) return fallback;
  return String(value);
}

function metricItems(input) {
  const items = Array.isArray(input.metrics) ? input.metrics : [];
  if (items.length > 0) return items.slice(0, 4);
  return [
    { label: "Cards analisados", value: "0" },
    { label: "Em andamento", value: "0" },
    { label: "Sem responsável", value: "0" },
    { label: "Com anexos", value: "0" },
  ];
}

function stateEntries(input) {
  const entries = Object.entries(input.state_breakdown || {});
  return entries.length > 0 ? entries : [["Sem dados", 0]];
}

function addText(slide, name, text, position, style) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name,
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = style;
  return shape;
}

async function main() {
  const [inputPath, outputPath, previewPath, layoutPath] = process.argv.slice(2);
  const input = JSON.parse(await fs.readFile(inputPath, "utf8"));

  const presentation = Presentation.create({
    slideSize: { width: 1280, height: 720 },
  });
  const slide = presentation.slides.add();
  slide.background.fill = "slate-50";

  addText(
    slide,
    "eyebrow",
    "AZURE DEVOPS | SUSTENTAÇÃO",
    { left: 72, top: 42, width: 380, height: 28 },
    { fontSize: 12, bold: true, color: "slate-500" },
  );
  addText(
    slide,
    "title",
    asText(input.title, "KPIs Sustentação - Azure DevOps"),
    { left: 72, top: 82, width: 760, height: 58 },
    { fontSize: 36, bold: true, color: "slate-950" },
  );
  addText(
    slide,
    "subtitle",
    asText(input.subtitle, "Resumo executivo"),
    { left: 72, top: 145, width: 880, height: 36 },
    { fontSize: 18, color: "slate-600" },
  );

  const metrics = metricItems(input);
  const metricWidth = 250;
  metrics.forEach((metric, index) => {
    const left = 72 + index * 286;
    slide.shapes.add({
      geometry: "roundRect",
      name: `metric-frame-${index + 1}`,
      position: { left, top: 212, width: metricWidth, height: 116 },
      fill: "white",
      line: { style: "solid", fill: "slate-200", width: 1 },
      borderRadius: "rounded-xl",
      shadow: "shadow-sm",
    });
    addText(
      slide,
      `metric-value-${index + 1}`,
      asText(metric.value, "-"),
      { left: left + 22, top: 232, width: metricWidth - 44, height: 42 },
      { fontSize: 34, bold: true, color: index === 0 ? "blue-700" : "slate-950" },
    );
    addText(
      slide,
      `metric-label-${index + 1}`,
      asText(metric.label, "Indicador"),
      { left: left + 22, top: 282, width: metricWidth - 44, height: 30 },
      { fontSize: 15, color: "slate-600" },
    );
  });

  const chartFrame = slide.shapes.add({
    geometry: "roundRect",
    name: "state-chart-frame",
    position: { left: 72, top: 372, width: 560, height: 248 },
    fill: "white",
    line: { style: "solid", fill: "slate-200", width: 1 },
    borderRadius: "rounded-xl",
    shadow: "shadow-sm",
  });
  addText(
    slide,
    "state-chart-title",
    "Distribuição por estado",
    { left: 100, top: 394, width: 360, height: 30 },
    { fontSize: 19, bold: true, color: "slate-900" },
  );
  const states = stateEntries(input);
  slide.charts.add("bar", {
    position: {
      left: chartFrame.position.left + 34,
      top: chartFrame.position.top + 68,
      width: chartFrame.position.width - 68,
      height: 145,
    },
    categories: states.map(([name]) => name),
    series: [{ name: "Cards", values: states.map(([, value]) => Number(value) || 0), fill: "blue-600" }],
    hasLegend: false,
    dataLabels: { showValue: true, position: "outEnd" },
    yAxis: {
      majorGridlines: { style: "solid", fill: "slate-200", width: 1 },
    },
  });

  slide.shapes.add({
    geometry: "roundRect",
    name: "highlights-frame",
    position: { left: 672, top: 372, width: 536, height: 248 },
    fill: "white",
    line: { style: "solid", fill: "slate-200", width: 1 },
    borderRadius: "rounded-xl",
    shadow: "shadow-sm",
  });
  addText(
    slide,
    "highlights-title",
    "Pontos de atenção",
    { left: 700, top: 394, width: 380, height: 30 },
    { fontSize: 19, bold: true, color: "slate-900" },
  );
  const highlights = Array.isArray(input.highlights) && input.highlights.length > 0
    ? input.highlights.slice(0, 4)
    : ["Sem alertas adicionais no insumo recebido."];
  addText(
    slide,
    "highlights-body",
    highlights.map((item) => `- ${item}`).join("\n"),
    { left: 700, top: 442, width: 468, height: 128 },
    { fontSize: 16, color: "slate-700" },
  );
  addText(
    slide,
    "footer",
    asText(input.footer, `Template: ${input.template_id || "-"} ${input.template_version || ""}`),
    { left: 72, top: 660, width: 1000, height: 22 },
    { fontSize: 11, color: "slate-500" },
  );

  const preview = await presentation.export({ slide, format: "png", scale: 1 });
  await writeBlob(previewPath, preview);
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(layoutPath, await layout.text(), "utf8");
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(outputPath);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
'''


if __name__ == "__main__":
    raise SystemExit(main())
