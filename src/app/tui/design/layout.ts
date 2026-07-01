export type ProgressCells = {
  filled: number;
  empty: number;
};

export function progressCells(value: number, total: number, width: number): ProgressCells {
  const safeTotal = total > 0 ? total : 1;
  const ratio = Math.max(0, Math.min(1, value / safeTotal));
  const filled = Math.max(0, Math.min(width, Math.round(ratio * width)));

  return { filled, empty: width - filled };
}

export function columnWidths(rows: readonly string[][]): number[] {
  const widths: number[] = [];

  for (const row of rows) {
    row.forEach((cell, index) => {
      widths[index] = Math.max(widths[index] ?? 0, cell.length);
    });
  }

  return widths;
}

export function padCell(value: string, width: number): string {
  return value.length >= width ? value : value + " ".repeat(width - value.length);
}
