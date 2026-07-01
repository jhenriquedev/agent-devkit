// Kit — shared pixel-sprite builder for Agent DevKit TUI journeys.
// Returns a React element tree (no custom elements), so it renders reliably
// inside dynamically-created content. Canonical animated component lives in Kit.dc.html.

export function kitGrid(mood, blink) {
  const base = [
    ".....A....A.....",
    ".....B....B.....",
    "....BBB..BBB....",
    "...BBBBBBBBBB...",
    "..BBBBBBBBBBBB..",
    ".BBBBBBBBBBBBBB.",
    ".BBWWWBBBBWWWBB.",
    ".BBWEWBBBBWEWBB.",
    ".BBWWWBBBBWWWBB.",
    ".BBBBBBBBBBBBBB.",
    ".BBBCBBBBBBCBBB.",
    ".BBBBBBMMBBBBBB.",
    "..BBBBBBBBBBBB..",
    "...BBBBBBBBBB...",
    "....DD....DD....",
    "................",
  ].map((s) => s.split(""));
  const set = (r, c, ch) => {
    base[r][c] = ch;
  };
  const eyeCols = { left: [3, 4, 5], right: [10, 11, 12] };
  const clearWhite = () => {
    for (const side of ["left", "right"])
      for (const c of eyeCols[side]) for (const r of [6, 7, 8]) set(r, c, "W");
  };
  const closeEyes = () => {
    for (const side of ["left", "right"])
      for (const c of eyeCols[side]) {
        set(6, c, "B");
        set(8, c, "B");
        set(7, c, "M");
      }
  };
  if (blink) {
    closeEyes();
  } else if (mood === "thinking") {
    clearWhite();
    set(7, 4, "W");
    set(7, 11, "W");
    set(6, 4, "E");
    set(6, 11, "E");
  } else if (mood === "concerned") {
    clearWhite();
    set(6, 4, "E");
    set(7, 4, "E");
    set(6, 11, "E");
    set(7, 11, "E");
  } else if (mood === "sleeping") {
    closeEyes();
  }
  if (mood === "happy") {
    set(11, 7, "B");
    set(11, 8, "B");
    set(11, 6, "M");
    set(11, 9, "M");
    set(12, 7, "M");
    set(12, 8, "M");
  } else if (mood === "sleeping") {
    set(11, 7, "B");
    set(11, 8, "M");
  } else if (mood === "concerned") {
    set(11, 6, "M");
    set(11, 9, "M");
  }
  if (mood === "sleeping" || mood === "concerned") {
    set(10, 4, "B");
    set(10, 11, "B");
  }
  return base;
}

export function kitElement(React, mood, scale, blink, opts) {
  opts = opts || {};
  mood = mood || "idle";
  scale = Number(scale) || 8;
  let body = "#8B7AE6",
    dark = "#6354C4";
  if (mood === "sleeping") {
    body = "#7C77A6";
    dark = "#5B567E";
  }
  if (mood === "concerned") {
    body = "#A88AE8";
  }
  if (opts.body) body = opts.body;
  if (opts.dark) dark = opts.dark;
  const antenna = opts.antenna || "#5FD0C8";
  const cheek = opts.cheek || "#E7A6CB";
  const COL = {
    ".": "transparent",
    B: body,
    D: dark,
    W: "#F4F3FB",
    E: "#211D33",
    M: "#2E2742",
    C: cheek,
    A: antenna,
  };
  const grid = kitGrid(mood, blink);
  const cells = [];
  grid.forEach((row, r) =>
    row.forEach((ch, c) => {
      cells.push(
        React.createElement("div", {
          key: r + "-" + c,
          style: { width: scale, height: scale, background: COL[ch] },
        }),
      );
    }),
  );
  const gridEl = React.createElement(
    "div",
    {
      style: {
        display: "grid",
        gridTemplateColumns: "repeat(16, " + scale + "px)",
        gridTemplateRows: "repeat(16, " + scale + "px)",
      },
    },
    cells,
  );

  const badges = {
    thinking: { t: "?", color: "#A99CF0" },
    working: { t: "", color: "#5FD0C8", spin: true },
    sleeping: { t: "z", color: "#8B7AE6" },
    concerned: { t: "!", color: "#E8B45F" },
    happy: { t: "\u2726", color: "#5FD0C8" },
  };
  const b = badges[mood];
  let badgeEl = null;
  if (b && b.spin) {
    badgeEl = React.createElement("div", {
      style: {
        position: "absolute",
        top: -scale * 1.2,
        right: -scale * 1.4,
        width: scale * 2,
        height: scale * 2,
        borderRadius: "50%",
        border: "3px solid rgba(95,208,200,.25)",
        borderTopColor: b.color,
        animation: "kit-spin .9s linear infinite",
      },
    });
  } else if (b && b.t) {
    badgeEl = React.createElement(
      "div",
      {
        style: {
          position: "absolute",
          top: -scale * 2,
          right: -scale * 1.6,
          fontFamily: "'JetBrains Mono',monospace",
          fontWeight: 700,
          fontSize: scale * 1.8,
          color: b.color,
          animation: "kit-badge 1.8s ease-in-out infinite",
        },
      },
      b.t,
    );
  }
  return React.createElement(
    "div",
    {
      style: {
        position: "relative",
        display: "inline-block",
        animation: "kit-bob 2.6s ease-in-out infinite",
        lineHeight: 0,
      },
    },
    gridEl,
    badgeEl,
  );
}
