import { Box, Text } from "ink";
import type { ReactNode } from "react";
import { useTokens } from "../TokensContext";

export type TerminalChromeProps = {
  title?: string;
  hint?: string;
  children: ReactNode;
};

export function TerminalChrome({ title, hint, children }: TerminalChromeProps) {
  const tokens = useTokens();

  return (
    <Box flexDirection="column" borderStyle="round" borderColor={tokens.color("border")}>
      <Box paddingX={1} gap={1}>
        <Text color={tokens.color("danger")}>{tokens.glyphs.bulletActive}</Text>
        <Text color={tokens.color("warning")}>{tokens.glyphs.bulletActive}</Text>
        <Text color={tokens.color("success")}>{tokens.glyphs.bulletActive}</Text>
        {title !== undefined ? <Text color={tokens.color("textMuted")}>{title}</Text> : null}
        {hint !== undefined ? (
          <Box flexGrow={1} justifyContent="flex-end">
            <Text color={tokens.color("textDim")}>{hint}</Text>
          </Box>
        ) : null}
      </Box>
      <Box flexDirection="column" paddingX={1}>
        {children}
      </Box>
    </Box>
  );
}
