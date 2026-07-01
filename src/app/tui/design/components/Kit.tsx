import { Box, Text } from "ink";
import { useState } from "react";
import { kitCells } from "../kit_cells";
import { useTokens } from "../TokensContext";
import { useBlink, useInterval } from "../useTimers";

const spinnerFrames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

export type KitProps = {
  mood?: string;
  animate?: boolean;
};

export function Kit({ mood = "idle", animate = true }: KitProps) {
  const tokens = useTokens();
  const blink = useBlink();
  const [frame, setFrame] = useState(0);

  const badge = tokens.kit.moods[mood]?.badge;
  const isSpinner = badge === "spinner";

  useInterval(
    () => setFrame((current) => (current + 1) % spinnerFrames.length),
    animate && isSpinner ? 90 : null,
  );

  const rows = kitCells(tokens.kit, mood, animate && blink, tokens.color("background"));
  const keyedRows = rows.map((cells) => ({
    cells: cells.map((cell, colIndex) => ({
      ...cell,
      key: `${cell.top}-${cell.bottom}-${colIndex}`,
    })),
    key: cells.map((cell) => `${cell.top}/${cell.bottom}`).join("|"),
  }));
  const badgeText = isSpinner ? (spinnerFrames[frame] ?? "") : badge;

  return (
    <Box flexDirection="column">
      {keyedRows.map((row, rowIndex) => (
        <Box key={row.key}>
          {row.cells.map((cell) => (
            <Text key={cell.key} color={cell.top} backgroundColor={cell.bottom}>
              ▀
            </Text>
          ))}
          {rowIndex === 0 && badgeText !== undefined && badgeText.length > 0 ? (
            <Text color={tokens.color("primaryStrong")}> {badgeText}</Text>
          ) : null}
        </Box>
      ))}
    </Box>
  );
}
