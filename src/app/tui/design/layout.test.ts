import { describe, expect, it } from "vitest";
import { columnWidths, padCell, progressCells } from "./layout";

describe("layout helpers", () => {
  it("computes clamped progress cells", () => {
    expect(progressCells(4, 7, 7)).toEqual({ filled: 4, empty: 3 });
    expect(progressCells(0, 0, 5)).toEqual({ filled: 0, empty: 5 });
    expect(progressCells(10, 5, 4)).toEqual({ filled: 4, empty: 0 });
  });

  it("measures column widths and pads cells", () => {
    expect(
      columnWidths([
        ["a", "bbb"],
        ["cc", "d"],
      ]),
    ).toEqual([2, 3]);
    expect(padCell("a", 3)).toBe("a  ");
    expect(padCell("long", 2)).toBe("long");
  });
});
