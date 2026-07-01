// Drift — floating-bot mascot (CSS shapes). Calm hovering robot: big domed visor head with
// soft glowing eyes + UI glints, tapered teardrop body, no legs (floats above its shadow).
// `palette.body` recolors the body (default deep blue). Requires rb-float, rb-pulse, rb-spin.

export function driftElement(React, mood, size, blink, palette) {
  const h = React.createElement;
  mood = mood || "idle";
  const S = Number(size) || 120;
  palette = palette || {};
  const body = palette.body || "#3E8FD0";
  const bodyDk = palette.dark || "#225E96";
  const bodyLt = "#7FC0F0",
    visor = "#0F1B2A",
    glow = palette.glow || "#9FE0FF";
  const W = S * 1.4,
    H = S * 1.7,
    cx = W / 2;
  const hw = S * 1.02,
    hh = S * 0.9,
    hl = cx - hw / 2,
    ht = S * 0.16;
  const px = (n) => n + "px";
  const abs = (st) => Object.assign({ position: "absolute" }, st);
  const D = (st, kids) => h("div", { style: st }, kids);
  const dim = mood === "sleeping",
    closed = blink || mood === "sleeping";
  const kids = [];

  // floating shadow (far below)
  kids.push(
    D(
      abs({
        left: px(cx - S * 0.3),
        top: px(H - S * 0.04),
        width: px(S * 0.6),
        height: px(S * 0.08),
        background: "radial-gradient(50% 50% at 50% 50%, rgba(0,0,0,.24), transparent 70%)",
      }),
    ),
  );
  // tapered body (teardrop) below head
  kids.push(
    D(
      abs({
        left: px(cx - S * 0.28),
        top: px(ht + hh * 0.66),
        width: px(S * 0.56),
        height: px(S * 0.66),
        borderRadius: "46% 46% 50% 50% / 30% 30% 78% 78%",
        background: "linear-gradient(160deg," + bodyLt + " 4%," + body + " 44%," + bodyDk + ")",
        boxShadow: "inset 0 " + px(-S * 0.06) + " " + px(S * 0.08) + " " + bodyDk,
      }),
    ),
  );
  // belly seam + light
  kids.push(
    D(
      abs({
        left: px(cx - S * 0.05),
        top: px(ht + hh * 0.82),
        width: px(S * 0.1),
        height: px(S * 0.1),
        borderRadius: "50%",
        background: "radial-gradient(circle," + glow + "," + bodyDk + ")",
        opacity: dim ? 0.4 : 0.85,
        boxShadow: dim ? "none" : "0 0 " + px(S * 0.08) + " " + glow,
      }),
    ),
  );
  // arms (little, hanging)
  [-1, 1].forEach((s) =>
    kids.push(
      D(
        abs({
          left: px(cx + s * S * 0.26 - S * 0.05),
          top: px(ht + hh * 0.7),
          width: px(S * 0.1),
          height: px(S * 0.28),
          borderRadius: px(S * 0.05),
          background: "linear-gradient(180deg," + body + "," + bodyDk + ")",
          transform: "rotate(" + s * 8 + "deg)",
        }),
      ),
    ),
  );
  // head dome
  kids.push(
    D(
      abs({
        left: px(hl),
        top: px(ht),
        width: px(hw),
        height: px(hh),
        borderRadius: "50% 50% 48% 48% / 56% 56% 44% 44%",
        background: "linear-gradient(155deg," + bodyLt + " 4%," + body + " 46%," + bodyDk + ")",
        boxShadow:
          "inset 0 " +
          px(S * 0.05) +
          " " +
          px(S * 0.06) +
          " rgba(255,255,255,.4), inset 0 " +
          px(-S * 0.06) +
          " " +
          px(S * 0.09) +
          " " +
          bodyDk +
          ", 0 " +
          px(S * 0.1) +
          " " +
          px(S * 0.16) +
          " rgba(0,0,0,.22)",
      }),
    ),
  );
  // visor
  const vw = hw * 0.78,
    vh = hh * 0.6,
    vl = cx - vw / 2,
    vt = ht + hh * 0.16;
  kids.push(
    D(
      abs({
        left: px(vl),
        top: px(vt),
        width: px(vw),
        height: px(vh),
        borderRadius: "46% 46% 48% 48% / 52% 52% 48% 48%",
        overflow: "hidden",
        background: "radial-gradient(120% 120% at 40% 26%, #1C3047, " + visor + ")",
        border: px(Math.max(2, S * 0.018)) + " solid " + bodyLt,
        boxShadow: "inset 0 0 " + px(S * 0.06) + " #000",
      }),
      [
        D(
          abs({
            left: px(-S * 0.05),
            top: px(-S * 0.08),
            width: px(vw * 0.5),
            height: px(vh + S * 0.16),
            background: "linear-gradient(105deg, rgba(255,255,255,.16), rgba(255,255,255,0) 60%)",
            transform: "skewX(-12deg)",
          }),
        ),
      ],
    ),
  );
  // eyes + UI glints
  const eL = vl + vw * 0.34,
    eR = vl + vw * 0.66,
    eY = vt + vh * 0.46;
  const gsh = dim ? "none" : "0 0 " + px(S * 0.06) + " " + glow;
  const eye = (c) => {
    if (closed)
      return D(
        abs({
          left: px(c - S * 0.06),
          top: px(eY - S * 0.008),
          width: px(S * 0.12),
          height: px(S * 0.022),
          borderRadius: px(S * 0.02),
          background: glow,
          opacity: dim ? 0.5 : 0.9,
          boxShadow: gsh,
        }),
      );
    if (mood === "happy")
      return D(
        abs({
          left: px(c - S * 0.06),
          top: px(eY - S * 0.05),
          width: px(S * 0.12),
          height: px(S * 0.09),
          borderBottom: px(S * 0.03) + " solid " + glow,
          borderRadius: "0 0 " + px(S * 0.1) + " " + px(S * 0.1),
          boxShadow: gsh,
        }),
      );
    const d = mood === "concerned" ? S * 0.12 : S * 0.09;
    const dy = mood === "thinking" ? -S * 0.03 : 0;
    return D(
      abs({
        left: px(c - d / 2),
        top: px(eY - d / 2 + dy),
        width: px(d),
        height: px(d),
        borderRadius: "50%",
        background: "radial-gradient(circle at 40% 32%, #fff, " + glow + " 75%)",
        boxShadow: gsh,
      }),
    );
  };
  kids.push(eye(eL));
  kids.push(eye(eR));

  const badges = {
    thinking: ["?", glow],
    concerned: ["!", "#E8B45F"],
    sleeping: ["z", glow],
    working: ["\u25cc", glow],
  };
  const b = badges[mood];
  if (b)
    kids.push(
      D(
        abs({
          top: px(ht - S * 0.02),
          right: px(S * 0.04),
          fontFamily: "'JetBrains Mono',monospace",
          fontWeight: 700,
          fontSize: px(S * 0.2),
          color: b[1],
          textShadow: "0 0 " + px(S * 0.08) + " " + b[1],
          animation:
            mood === "working"
              ? "rb-spin .9s linear infinite"
              : "rb-pulse 1.8s ease-in-out infinite",
        }),
        b[0],
      ),
    );

  return h(
    "div",
    {
      style: {
        position: "relative",
        width: px(W),
        height: px(H),
        animation: "rb-float " + (dim ? "4.5s" : "3.4s") + " ease-in-out infinite",
      },
    },
    kids.map((c, i) => React.cloneElement(c, { key: i })),
  );
}

function driftTermGrid(mood, blink) {
  const base = [
    "....BBBBBBBBBB....",
    "...BBBBBBBBBBBB...",
    "..BBLLLLLLLLLLBB..",
    "..BLVVVVVVVVVVLB..",
    "..BLVVEEVVEEVVLB..",
    "..BLVVEEVVEEVVLB..",
    "..BLVVVVVVVVVVLB..",
    "..BLVVVmmmmVVVLB..",
    "...BBLLLLLLLLBB...",
    "....BBBBBBBBBB....",
    ".....BBBBBBBB.....",
    "......BBBBBB......",
    ".....BBBGGBBB.....",
    "......BBBBBB......",
    ".......BBBB.......",
  ].map((s) => s.split(""));
  const set = (r, c, ch) => {
    if (base[r] && base[r][c] !== undefined) base[r][c] = ch;
  };
  const closed = blink || mood === "sleeping";
  if (closed) {
    for (const c of [6, 7, 10, 11]) {
      set(4, c, "V");
      set(5, c, "E");
    }
  }
  return base;
}

export function driftTerminalElement(React, mood, cell, palette, blink) {
  const h = React.createElement;
  cell = Number(cell) || 9;
  palette = palette || {};
  const body = palette.body || "#3E8FD0";
  const dim = mood === "sleeping";
  const glow = palette.glow || "#9FE0FF";
  const COL = {
    B: body,
    L: "#7FC0F0",
    V: "#0F1B2A",
    E: dim ? "#4E7CA0" : glow,
    m: dim ? "#4E7CA0" : glow,
    G: dim ? "#4E7CA0" : glow,
  };
  const grid = driftTermGrid(mood, blink);
  const block = "\u2588\u2588";
  const rows = grid.map((row, ri) => {
    const spans = [];
    let i = 0;
    while (i < row.length) {
      const ch = row[i];
      let j = i;
      while (j < row.length && row[j] === ch) j++;
      const run = j - i;
      if (ch === ".")
        spans.push(h("span", { key: i, style: { color: "transparent" } }, block.repeat(run)));
      else {
        const isE = ch === "E" || ch === "m" || ch === "G";
        spans.push(
          h(
            "span",
            {
              key: i,
              style: {
                color: COL[ch] || "#888",
                textShadow: isE && !dim ? "0 0 " + cell * 0.5 + "px " + glow : "none",
              },
            },
            block.repeat(run),
          ),
        );
      }
      i = j;
    }
    return h("div", { key: ri, style: { height: cell + "px", lineHeight: cell + "px" } }, spans);
  });
  const badges = {
    thinking: ["?", glow],
    concerned: ["!", "#E8B45F"],
    sleeping: ["z", glow],
    working: ["\u25cc", glow],
  };
  const b = badges[mood];
  let badge = null;
  if (b)
    badge = h(
      "div",
      {
        style: {
          position: "absolute",
          top: cell * 0.2,
          right: -cell * 1.2,
          fontSize: cell * 1.8,
          fontWeight: 700,
          color: b[1],
          textShadow: "0 0 " + cell * 0.6 + "px " + b[1],
          animation:
            mood === "working"
              ? "rb-spin .9s linear infinite"
              : "rb-pulse 1.8s ease-in-out infinite",
        },
      },
      b[0],
    );
  return h(
    "div",
    {
      style: {
        position: "relative",
        display: "inline-block",
        fontFamily: "'JetBrains Mono',monospace",
        fontSize: cell + "px",
        letterSpacing: "-0.5px",
        whiteSpace: "pre",
      },
    },
    rows,
    badge,
  );
}
