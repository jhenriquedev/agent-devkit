import { describe, expect, it } from "vitest";
import { DesignSemanticsSchema } from "../../../infra/bases/design";
import { ThemeDefinitionSchema } from "../../../infra/bases/theme";
import { resolveTokens } from "./tokens";

const theme = ThemeDefinitionSchema.parse({
  schema: "agent-devkit.theme/v1",
  id: "test",
  name: "Test",
  description: "Test theme.",
  appearance: "dark",
  colors: {
    background: "#000000",
    panel: "#111111",
    elevated: "#222222",
    border: "#333333",
    borderStrong: "#444444",
    text: "#EEEEEE",
    textMuted: "#999999",
    textDim: "#666666",
    primary: "#8B7AE6",
    primaryStrong: "#A99CF0",
    success: "#5FD0C8",
    warning: "#E8B45F",
    danger: "#E87A8E",
    accent: "#E7A6CB",
  },
  fonts: { heading: "Space Grotesk", mono: "JetBrains Mono", body: "JetBrains Mono" },
});

const semantics = DesignSemanticsSchema.parse({
  schema: "agent-devkit.design-semantics/v1",
  status: {
    ok: "success",
    attention: "warning",
    blocked: "danger",
    "needs-setup": "primary",
    pending: "textDim",
  },
  risk: {
    destructive: "danger",
    "external-write": "warning",
    "read-only": "success",
    "writes-global-state": "warning",
    "writes-project-state": "primary",
  },
  glyphs: {
    prompt: "❯",
    check: "✓",
    bulletActive: "●",
    bulletIdle: "○",
    progressFull: "▰",
    progressEmpty: "▱",
  },
});

describe("resolveTokens", () => {
  it("resolves theme colors and glyphs", () => {
    const tokens = resolveTokens(theme, semantics);
    expect(tokens.color("primary")).toBe("#8B7AE6");
    expect(tokens.glyphs.prompt).toBe("❯");
  });

  it("maps status and risk names onto theme colors", () => {
    const tokens = resolveTokens(theme, semantics);
    expect(tokens.statusColor("ok")).toBe("#5FD0C8");
    expect(tokens.statusColor("blocked")).toBe("#E87A8E");
    expect(tokens.riskColor("destructive")).toBe("#E87A8E");
    expect(tokens.riskColor("writes-project-state")).toBe("#8B7AE6");
  });
});
