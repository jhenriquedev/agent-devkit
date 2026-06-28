#!/usr/bin/env python3
"""Bridge Figma operations from ai-devkit to a Codex runtime with Figma MCP."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[6]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Figma operation through codex exec and Figma MCP")
    parser.add_argument("--codex-command", default="codex")
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    try:
        request = json.loads(sys.stdin.read() or "{}")
        prompt = build_prompt(request)
        schema = build_schema()
        payload = run_codex(args.codex_command, prompt, schema, args.timeout)
        validate_payload(payload)
        print(json.dumps(payload, ensure_ascii=False))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def run_codex(codex_command: str, prompt: str, schema: dict[str, Any], timeout: int) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="figma-codex-bridge-") as tmpdir:
        tmp = Path(tmpdir)
        schema_path = tmp / "schema.json"
        output_path = tmp / "last-message.json"
        schema_path.write_text(json.dumps(schema, ensure_ascii=False), encoding="utf-8")
        command = [
            *shlex.split(codex_command),
            "--ask-for-approval",
            "never",
            "--sandbox",
            "danger-full-access",
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            "--json",
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(output_path),
            "-C",
            str(ROOT),
            prompt,
        ]
        result = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
            raise RuntimeError(f"codex exec falhou: {detail}")
        if not output_path.exists():
            raise RuntimeError("codex exec nao gerou --output-last-message")
        raw = output_path.read_text(encoding="utf-8").strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                raise RuntimeError("resposta do codex nao contem JSON")
            return json.loads(match.group(0))


def build_prompt(request: dict[str, Any]) -> str:
    operation = request.get("operation") or {}
    explicit_script = build_use_figma_script(operation)
    return f"""You are the Figma MCP execution bridge for ai-devkit.

Use the available Figma MCP tools to execute the requested operation.
Return only JSON matching the provided output schema.

Rules:
- The Figma MCP tools are deferred in many Codex exec runtimes.
- Always call tool_search first with query "figma" before any Figma operation.
- After discovery, use any exposed Figma tool matching these names:
  mcp__figma.whoami, mcp__figma.create_new_file, mcp__figma.use_figma,
  mcp__codex_apps__figma._whoami, mcp__codex_apps__figma._create_new_file,
  mcp__codex_apps__figma._use_figma, plus metadata/screenshot/library/search tools.
- Treat either create_new_file or _create_new_file as valid. Treat either use_figma or _use_figma as valid.
- For diagnostics, call whoami and return status \"inspected\" with inspected_node_ids [\"whoami\"].
- For new files, call whoami if plan_key is missing. If multiple plans exist and no plan_key is provided, return status \"blocked\" with a clear message.
- For create/update screen operations, prefer create_new_file when no figma_file_key is provided, then use use_figma.
- When create_new_file succeeds, continue with use_figma in the created file. Do not stop after file creation unless the requested action is exactly \"create_file\".
- Before use_figma writes, follow figma-use rules: top-level await, return created/mutated node IDs, load fonts before text edits, use auto-layout containers, and avoid figma.notify.
- For existing files, inspect metadata before mutating.
- Do not invent a file_url or node IDs. If the tool did not return evidence, return status \"blocked\".
- Return every schema field. Use null for unknown scalar fields and [] for empty arrays.

For screen creation actions, use this exact JavaScript with use_figma after resolving the file key:
```js
{explicit_script}
```

The use_figma result returns createdNodeIds/mutatedNodeIds. Map them to created_node_ids/mutated_node_ids in the final JSON.

Request JSON:
```json
{json.dumps(request, ensure_ascii=False, indent=2)}
```
"""


def build_use_figma_script(operation: dict[str, Any]) -> str:
    title = json.dumps(str(operation.get("file_name") or "AI DevKit Design"))
    page_name = json.dumps(str(operation.get("page_name") or "AI DevKit Design"))
    screens = operation.get("screens") or ["Dashboard"]
    components = operation.get("components") or ["Button", "Card", "Navigation"]
    brief = json.dumps((operation.get("brief") or "Design generated by AI DevKit.")[:500])
    screen_labels = json.dumps([str(item) for item in screens[:6]])
    component_labels = json.dumps([str(item) for item in components[:10]])
    return f"""const page = figma.currentPage;
page.name = {page_name};
await figma.loadFontAsync({{ family: 'Inter', style: 'Regular' }});
await figma.loadFontAsync({{ family: 'Inter', style: 'Semi Bold' }});
const created = [];
const mutated = [page.id];
const frame = figma.createAutoLayout('VERTICAL', {{
  name: {title},
  itemSpacing: 20,
  paddingTop: 32,
  paddingRight: 32,
  paddingBottom: 32,
  paddingLeft: 32,
  cornerRadius: 12,
  fills: [{{ type: 'SOLID', color: {{ r: 0.96, g: 0.97, b: 0.98 }} }}],
}});
frame.resize(960, 100);
frame.x = 120;
frame.y = 120;
created.push(frame.id);
const title = figma.createText();
title.name = 'Screen title';
title.fontName = {{ family: 'Inter', style: 'Semi Bold' }};
title.fontSize = 30;
title.characters = {title};
title.fills = [{{ type: 'SOLID', color: {{ r: 0.08, g: 0.09, b: 0.11 }} }}];
frame.appendChild(title);
created.push(title.id);
const summary = figma.createText();
summary.name = 'Brief summary';
summary.fontName = {{ family: 'Inter', style: 'Regular' }};
summary.fontSize = 16;
summary.characters = {brief};
summary.resize(840, summary.height);
summary.fills = [{{ type: 'SOLID', color: {{ r: 0.28, g: 0.31, b: 0.36 }} }}];
frame.appendChild(summary);
created.push(summary.id);
const screenLabels = {screen_labels};
const cards = figma.createAutoLayout('HORIZONTAL', {{ name: 'Screen cards', itemSpacing: 12 }});
frame.appendChild(cards);
cards.layoutSizingHorizontal = 'FILL';
created.push(cards.id);
for (const label of screenLabels.slice(0, 4)) {{
  const card = figma.createAutoLayout('VERTICAL', {{
    name: `Card - ${{label}}`,
    itemSpacing: 8,
    paddingTop: 16,
    paddingRight: 16,
    paddingBottom: 16,
    paddingLeft: 16,
    cornerRadius: 8,
    fills: [{{ type: 'SOLID', color: {{ r: 1, g: 1, b: 1 }} }}],
    strokes: [{{ type: 'SOLID', color: {{ r: 0.86, g: 0.88, b: 0.91 }} }}],
    strokeWeight: 1,
  }});
  card.resize(204, 120);
  const cardTitle = figma.createText();
  cardTitle.fontName = {{ family: 'Inter', style: 'Semi Bold' }};
  cardTitle.fontSize = 14;
  cardTitle.characters = label;
  const cardBody = figma.createText();
  cardBody.fontName = {{ family: 'Inter', style: 'Regular' }};
  cardBody.fontSize = 12;
  cardBody.characters = 'Estado: success, loading, empty, error';
  cardBody.resize(170, cardBody.height);
  card.appendChild(cardTitle);
  card.appendChild(cardBody);
  cards.appendChild(card);
  created.push(card.id, cardTitle.id, cardBody.id);
}}
const componentText = figma.createText();
componentText.name = 'Component inventory';
componentText.fontName = {{ family: 'Inter', style: 'Regular' }};
componentText.fontSize = 13;
componentText.characters = 'Componentes previstos: ' + {component_labels}.join(', ');
componentText.resize(840, componentText.height);
frame.appendChild(componentText);
created.push(componentText.id);
page.appendChild(frame);
return {{ createdNodeIds: created, mutatedNodeIds: mutated, pageName: page.name }};"""


def build_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "status",
            "message",
            "file_key",
            "file_url",
            "page_name",
            "created_node_ids",
            "mutated_node_ids",
            "inspected_node_ids",
            "screenshot_refs",
        ],
        "properties": {
            "status": {
                "type": "string",
                "enum": ["executed", "updated", "created", "inspected", "blocked"],
            },
            "message": {"type": ["string", "null"]},
            "file_key": {"type": ["string", "null"]},
            "file_url": {"type": ["string", "null"]},
            "page_name": {"type": ["string", "null"]},
            "created_node_ids": {"type": "array", "items": {"type": "string"}},
            "mutated_node_ids": {"type": "array", "items": {"type": "string"}},
            "inspected_node_ids": {"type": "array", "items": {"type": "string"}},
            "screenshot_refs": {"type": "array", "items": {"type": "string"}},
        },
    }


def validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("status") == "blocked":
        raise RuntimeError(payload.get("message") or "Figma bridge blocked")
    evidence = [
        payload.get("file_key"),
        payload.get("file_url"),
        payload.get("created_node_ids"),
        payload.get("mutated_node_ids"),
        payload.get("inspected_node_ids"),
    ]
    if not any(evidence):
        raise RuntimeError("Figma bridge nao retornou evidencia real")


if __name__ == "__main__":
    raise SystemExit(main())
