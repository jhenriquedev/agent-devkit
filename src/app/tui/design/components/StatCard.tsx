import { Box, Text } from "ink";
import type { ReactNode } from "react";
import { useTokens } from "../TokensContext";

export type StatCardProps = {
  label: string;
  value?: string;
  children?: ReactNode;
};

export function StatCard({ label, value, children }: StatCardProps) {
  const tokens = useTokens();

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor={tokens.color("border")}
      paddingX={1}
    >
      <Text color={tokens.color("textDim")}>{label}</Text>
      {value !== undefined ? <Text color={tokens.color("text")}>{value}</Text> : children}
    </Box>
  );
}
