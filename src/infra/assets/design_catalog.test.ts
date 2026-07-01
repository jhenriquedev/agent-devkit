import { describe, expect, it } from "vitest";
import { DesignCatalog } from "./design_catalog";

describe("DesignCatalog", () => {
  it("loads and validates design semantics against the theme tokens", async () => {
    const catalog = new DesignCatalog();
    const result = await catalog.semantics();

    expect(result.isOk()).toBe(true);
    const semantics = result.unwrap();
    expect(semantics.schema).toBe("agent-devkit.design-semantics/v1");
    expect(semantics.status.ok).toBe("success");
    expect(semantics.risk.destructive).toBe("danger");
    expect(semantics.glyphs.prompt).toBe("❯");
  });

  it("loads and validates the Kit sprite", async () => {
    const catalog = new DesignCatalog();
    const result = await catalog.kit();

    expect(result.isOk()).toBe(true);
    const kit = result.unwrap();
    expect(kit.schema).toBe("agent-devkit.kit/v1");
    expect(kit.base).toHaveLength(kit.size.rows);
    expect(kit.palette.B).toBe("#8B7AE6");
    expect(kit.moods.happy).toBeDefined();
    expect(kit.moods.sleeping?.body).toBe("#7C77A6");
  });

  it("caches the parsed tokens across calls", async () => {
    const catalog = new DesignCatalog();
    const first = await catalog.semantics();
    const second = await catalog.semantics();

    expect(first.isOk()).toBe(true);
    expect(second.unwrap()).toBe(first.unwrap());
  });
});
