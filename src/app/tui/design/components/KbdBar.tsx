import { Box, Text } from "ink";
import { useTokens } from "../TokensContext";

export type KbdBarProps = {
  keys: string[];
};

export function KbdBar({ keys }: KbdBarProps) {
  const tokens = useTokens();

  return (
    <Box gap={2}>
      {keys.map((key) => (
        <Text key={key} color={tokens.color("textDim")}>
          {key}
        </Text>
      ))}
    </Box>
  );
}
