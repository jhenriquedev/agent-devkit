# Visual Quality Gates

Before delivery, verify:

- XML parses and root is `mxfile`.
- Diagram has a title.
- Content nodes have labels.
- Connectors reference existing source and target IDs.
- Important connectors have labels when they represent business actions,
  payloads, protocols, events, or decisions.
- Layout positions nodes intentionally; not all nodes share the same x/y.
- Nodes in the same parent are not geometrically overlapping.
- Review output reports each gate as `ok`, `warning`, or `fail`.
- Legend exists when colors, groups, or line styles have semantic meaning.
- Open questions are explicit when source context is incomplete.
