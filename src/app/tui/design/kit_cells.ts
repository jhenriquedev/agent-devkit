import type { KitSprite } from "../../../infra/bases/design";

export type KitCell = {
  top: string;
  bottom: string;
};

type KitOverride = [number, number, string];

function applyOverrides(grid: string[][], overrides: readonly KitOverride[]): void {
  for (const [row, col, char] of overrides) {
    const line = grid[row];

    if (line !== undefined && col >= 0 && col < line.length) {
      line[col] = char;
    }
  }
}

/**
 * Resolves the Kit sprite into terminal half-block rows. Each output row packs
 * two vertical pixels into one cell: `top` is the foreground of `▀`, `bottom`
 * is its background. Transparent pixels are flattened onto `background`.
 */
export function kitCells(
  kit: KitSprite,
  mood: string,
  blink: boolean,
  background: string,
): KitCell[][] {
  const grid = kit.base.map((line) => line.split(""));
  const moodDefinition = kit.moods[mood] ?? kit.moods.idle;

  if (moodDefinition !== undefined) {
    applyOverrides(grid, moodDefinition.overrides);
  }

  if (blink) {
    applyOverrides(grid, kit.blink.overrides);
  }

  const palette: Record<string, string> = { ...kit.palette };

  if (moodDefinition?.body !== undefined) {
    palette.B = moodDefinition.body;
  }

  if (moodDefinition?.dark !== undefined) {
    palette.D = moodDefinition.dark;
  }

  const colorFor = (char: string): string => {
    const value = palette[char];
    return value === undefined || value === "transparent" ? background : value;
  };

  const cellAt = (row: number, col: number): string => grid[row]?.[col] ?? ".";

  const rows: KitCell[][] = [];

  for (let row = 0; row + 1 < kit.base.length; row += 2) {
    const cells: KitCell[] = [];

    for (let col = 0; col < kit.size.cols; col += 1) {
      cells.push({ top: colorFor(cellAt(row, col)), bottom: colorFor(cellAt(row + 1, col)) });
    }

    rows.push(cells);
  }

  return rows;
}
