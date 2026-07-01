import type { DesignSemantics } from "../../../infra/bases/design";
import type { ThemeDefinition } from "../../../infra/bases/theme";

export type ThemeColorName = keyof ThemeDefinition["colors"];
export type StatusName = keyof DesignSemantics["status"];
export type RiskName = keyof DesignSemantics["risk"];
export type GlyphName = keyof DesignSemantics["glyphs"];

export type Tokens = {
  theme: ThemeDefinition;
  semantics: DesignSemantics;
  glyphs: DesignSemantics["glyphs"];
  color(name: ThemeColorName): string;
  statusColor(status: StatusName): string;
  riskColor(risk: RiskName): string;
};

export function resolveTokens(theme: ThemeDefinition, semantics: DesignSemantics): Tokens {
  const colors = theme.colors as Record<string, string>;
  const toColor = (tokenName: string): string => colors[tokenName] ?? theme.colors.textMuted;

  return {
    theme,
    semantics,
    glyphs: semantics.glyphs,
    color: (name) => theme.colors[name],
    statusColor: (status) => toColor(semantics.status[status]),
    riskColor: (risk) => toColor(semantics.risk[risk]),
  };
}
