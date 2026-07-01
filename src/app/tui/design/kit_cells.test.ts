import { describe, expect, it } from "vitest";
import { KitSpriteSchema } from "../../../infra/bases/design";
import { kitCells } from "./kit_cells";

const kit = KitSpriteSchema.parse({
  schema: "agent-devkit.kit/v1",
  size: { rows: 2, cols: 2 },
  palette: { ".": "transparent", B: "#8B7AE6" },
  base: ["B.", ".B"],
  blink: { overrides: [] },
  moods: {
    idle: { overrides: [] },
    happy: { overrides: [[0, 1, "B"]], badge: "✦" },
  },
});

describe("kitCells", () => {
  it("packs two pixel rows into one half-block row and flattens transparency", () => {
    const rows = kitCells(kit, "idle", false, "#000000");
    expect(rows).toHaveLength(1);
    expect(rows[0]).toHaveLength(2);
    expect(rows[0]?.[0]).toEqual({ top: "#8B7AE6", bottom: "#000000" });
    expect(rows[0]?.[1]).toEqual({ top: "#000000", bottom: "#8B7AE6" });
  });

  it("applies mood overrides", () => {
    const rows = kitCells(kit, "happy", false, "#000000");
    expect(rows[0]?.[1]?.top).toBe("#8B7AE6");
  });

  it("falls back to idle for unknown moods", () => {
    const rows = kitCells(kit, "does-not-exist", false, "#000000");
    expect(rows[0]?.[0]?.top).toBe("#8B7AE6");
  });
});
