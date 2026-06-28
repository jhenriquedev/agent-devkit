---
name: drawio-diagramming
description: Create, inspect, validate, and refine editable Draw.io/diagrams.net `.drawio` files from source material, diagram specs, architecture notes, product journeys, ERDs, process flows, Azure card context, and other Agent DevKit artifacts. Use when work involves Draw.io XML, mxfile structure, visual quality gates, diagram layout, or converting requirements/specs into editable diagrams.
---

# Draw.io Diagramming

Use this skill when generating or reviewing editable `.drawio` diagrams.

## Core Workflow

1. Separate facts, assumptions, inferences, and open questions.
2. Convert source material into a small `diagram-spec.json`; keep this spec as
   the source of truth for generation and refinement.
3. Render uncompressed Draw.io XML (`mxfile`) for diffable output.
4. Validate XML, connector references, labels, geometry, title, and legend.
5. Refine iteratively by updating the spec, re-rendering the `.drawio`, and
   recording a changelog until acceptance.

## References

- Read `references/mxfile-format.md` before writing or patching `.drawio` XML.
- Read `references/layout-patterns.md` when deciding layout or diagram split.
- Read `references/visual-quality-gates.md` before claiming a diagram is ready.
- Read `references/diagram-types.md` when selecting the diagram type.

## Scripts

- Run `scripts/validate_drawio.py <diagram.drawio>` to validate a diagram.
- Run `scripts/inspect_drawio.py <diagram.drawio>` to summarize nodes, edges,
  warnings, and basic structure.

Prefer local deterministic XML generation over screenshots or external design
services. If the source is ambiguous, ask targeted interview questions before
rendering.
