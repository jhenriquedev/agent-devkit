import { Box, Text } from "ink";
import type { ReactNode } from "react";
import { useTokens } from "../TokensContext";

export type PanelProps = {
  title?: string;
  children: ReactNode;
};

export function Panel({ title, children }: PanelProps) {
  const tokens = useTokens();

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor={tokens.color("border")}
      paddingX={1}
    >
      {title !== undefined ? <Text color={tokens.color("textDim")}>{title}</Text> : null}
      {children}
    </Box>
  );
}
