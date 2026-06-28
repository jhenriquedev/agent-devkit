# Draw.io mxfile Format

Use uncompressed XML for versionable output:

```xml
<mxfile host="Agent DevKit">
  <diagram id="diagram-1" name="Page-1">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

Nodes are `mxCell` elements with `vertex="1"` and `mxGeometry`.

Connectors are `mxCell` elements with `edge="1"`, `source`, `target`, and
relative geometry.

Use stable IDs:

- `node-<source-id>` for diagram elements.
- `edge-<n>` for connectors.
- `group-<name>` for swimlanes/groups.
- `diagram-title` and `diagram-legend` for common utility cells.
