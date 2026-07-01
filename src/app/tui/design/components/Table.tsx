import { Box, Text } from "ink";
import { columnWidths, padCell } from "../layout";
import { useTokens } from "../TokensContext";

export type TableProps = {
  rows: string[][];
  header?: string[];
};

export function Table({ rows, header }: TableProps) {
  const tokens = useTokens();
  const widths = columnWidths(header !== undefined ? [header, ...rows] : rows);

  const renderLine = (cells: string[]): string =>
    cells.map((cell, index) => padCell(cell, widths[index] ?? 0)).join("  ");

  return (
    <Box flexDirection="column">
      {header !== undefined ? (
        <Text color={tokens.color("textDim")}>{renderLine(header)}</Text>
      ) : null}
      {rows.map((row) => (
        <Text key={row.join("\u0000")} color={tokens.color("text")}>
          {renderLine(row)}
        </Text>
      ))}
    </Box>
  );
}
