import { Text } from "ink";
import { useTokens } from "../TokensContext";
import type { GlyphName } from "../tokens";

export type HeadingProps = {
  children: string;
};

/** Space Grotesk from the design system is unavailable in a terminal, so
 * headings degrade to bold in the user's monospace font. */
export function Heading({ children }: HeadingProps) {
  const tokens = useTokens();
  return (
    <Text bold color={tokens.color("text")}>
      {children}
    </Text>
  );
}

export type DividerProps = {
  width?: number;
};

export function Divider({ width = 40 }: DividerProps) {
  const tokens = useTokens();
  return <Text color={tokens.color("border")}>{"─".repeat(width)}</Text>;
}

export type GlyphProps = {
  name: GlyphName;
  color?: string;
};

export function Glyph({ name, color }: GlyphProps) {
  const tokens = useTokens();
  return <Text color={color ?? tokens.color("text")}>{tokens.glyphs[name]}</Text>;
}
