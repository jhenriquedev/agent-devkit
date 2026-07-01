import { Box, Text } from "ink";
import { progressCells } from "../layout";
import { useTokens } from "../TokensContext";

export type ProgressBarProps = {
  value: number;
  total: number;
  width?: number;
  showCount?: boolean;
};

export function ProgressBar({ value, total, width = 7, showCount = true }: ProgressBarProps) {
  const tokens = useTokens();
  const { filled, empty } = progressCells(value, total, width);

  return (
    <Box gap={1}>
      <Text color={tokens.color("primary")}>
        {tokens.glyphs.progressFull.repeat(filled)}
        {tokens.glyphs.progressEmpty.repeat(empty)}
      </Text>
      {showCount ? (
        <Text color={tokens.color("textDim")}>
          {value}/{total}
        </Text>
      ) : null}
    </Box>
  );
}
