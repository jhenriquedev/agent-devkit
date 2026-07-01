// Robo — clean, modern, friendly robot mascot built from CSS shapes (no pixels, no SVG).
// Returns a React element tree so it renders inside dynamically-created content.
// Drives expression by `mood` and `blink`; recolors by `palette`.
// Requires these @keyframes in the host page's <helmet>:
//   rb-float, rb-pulse, rb-blink, rb-spin

export function robotElement(React, mood, size, blink, palette) {
  const h = React.createElement;
  mood = mood || "idle";
  const S = Number(size) || 120;
  palette = palette || {};
  const body = palette.body || "#8B7AE6";
  const dark = palette.dark || "#6354C4";
  const glow = palette.glow || palette.antenna || "#7DEFE6";
  const screen = palette.screen || "#141124";

  const W = S * 1.2,
    H = S * 1.42;
  const headTop = S * 0.27,
    headLeft = (W - S) / 2;
  const screenW = S * 0.74,
    screenH = S * 0.5;
  const screenLeft = (W - screenW) / 2,
    screenTop = headTop + S * 0.15;
  const eyeCy = screenTop + screenH * 0.46;
  const eyeCxL = W / 2 - S * 0.15,
    eyeCxR = W / 2 + S * 0.15;
  const mouthCy = screenTop + screenH * 0.78;

  const abs = (st) => Object.assign({ position: "absolute" }, st);
  const D = (st, kids) => h("div", { style: st }, kids);

  // ---- expression on the screen ----
  const eyeEls = [];
  const px = (n) => n + "px";
  const closed = blink || mood === "sleeping";

  function eyeAt(cx, st) {
    const w = st.width,
      hh = st.height;
    return D(
      abs(
        Object.assign(
          {
            left: px(cx - w / 2),
            top: px(eyeCy - hh / 2),
            background: glow,
            boxShadow: "0 0 " + px(S * 0.07) + " " + glow,
          },
          st,
        ),
      ),
    );
  }

  if (closed) {
    [eyeCxL, eyeCxR].forEach((cx, i) =>
      eyeEls.push(
        h("div", {
          key: "e" + i,
          style: abs({
            left: px(cx - S * 0.07),
            top: px(eyeCy - S * 0.012),
            width: px(S * 0.14),
            height: px(S * 0.028),
            borderRadius: px(S * 0.02),
            background: glow,
            boxShadow: "0 0 " + px(S * 0.05) + " " + glow,
          }),
        }),
      ),
    );
  } else if (mood === "happy") {
    // upward domes ∩
    [eyeCxL, eyeCxR].forEach((cx, i) =>
      eyeEls.push(
        h("div", {
          key: "e" + i,
          style: abs({
            left: px(cx - S * 0.07),
            top: px(eyeCy - S * 0.045),
            width: px(S * 0.14),
            height: px(S * 0.1),
            borderRadius: px(S * 0.07) + " " + px(S * 0.07) + " 0 0",
            background: glow,
            boxShadow: "0 0 " + px(S * 0.07) + " " + glow,
          }),
        }),
      ),
    );
  } else if (mood === "concerned") {
    [eyeCxL, eyeCxR].forEach((cx, i) =>
      eyeEls.push(
        h("div", {
          key: "e" + i,
          style: abs({
            left: px(cx - S * 0.085),
            top: px(eyeCy - S * 0.085),
            width: px(S * 0.17),
            height: px(S * 0.17),
            borderRadius: "50%",
            background: glow,
            boxShadow: "0 0 " + px(S * 0.08) + " " + glow,
          }),
        }),
      ),
    );
  } else {
    // idle / thinking / working — pill eyes (thinking shifts up)
    const dy = mood === "thinking" ? -S * 0.05 : 0;
    [eyeCxL, eyeCxR].forEach((cx, i) =>
      eyeEls.push(
        h("div", {
          key: "e" + i,
          style: abs({
            left: px(cx - S * 0.05),
            top: px(eyeCy - S * 0.1 + dy),
            width: px(S * 0.1),
            height: px(S * 0.2),
            borderRadius: px(S * 0.05),
            background: glow,
            boxShadow: "0 0 " + px(S * 0.07) + " " + glow,
          }),
        }),
      ),
    );
  }

  // mouth
  let mouthEl = null;
  if (mood === "happy") {
    mouthEl = h("div", {
      key: "m",
      style: abs({
        left: px(W / 2 - S * 0.12),
        top: px(mouthCy - S * 0.02),
        width: px(S * 0.24),
        height: px(S * 0.12),
        borderBottom: px(S * 0.035) + " solid " + glow,
        borderRadius: "0 0 " + px(S * 0.2) + " " + px(S * 0.2),
        opacity: 0.85,
      }),
    });
  } else if (mood === "concerned") {
    mouthEl = h("div", {
      key: "m",
      style: abs({
        left: px(W / 2 - S * 0.05),
        top: px(mouthCy),
        width: px(S * 0.1),
        height: px(S * 0.06),
        border: px(S * 0.025) + " solid " + glow,
        borderRadius: "50%",
        opacity: 0.7,
      }),
    });
  } else if (!closed) {
    mouthEl = h("div", {
      key: "m",
      style: abs({
        left: px(W / 2 - S * 0.06),
        top: px(mouthCy + S * 0.01),
        width: px(S * 0.12),
        height: px(S * 0.02),
        borderRadius: px(S * 0.02),
        background: glow,
        opacity: 0.45,
      }),
    });
  }

  // scan line for working
  let scanEl = null;
  if (mood === "working") {
    scanEl = h("div", {
      key: "scan",
      style: abs({
        left: px(screenLeft + S * 0.06),
        top: px(screenTop + screenH * 0.5),
        width: px(screenW - S * 0.12),
        height: px(S * 0.02),
        background: glow,
        opacity: 0.5,
        boxShadow: "0 0 " + px(S * 0.05) + " " + glow,
      }),
    });
  }

  // ---- floating badge (zzz / ? / ! / spinner) ----
  let badgeEl = null;
  const badgeBase = abs({
    right: px(-S * 0.06),
    top: px(headTop - S * 0.06),
    fontFamily: "'JetBrains Mono',monospace",
    fontWeight: 700,
    fontSize: px(S * 0.22),
    color: glow,
    animation: "rb-pulse 1.8s ease-in-out infinite",
    textShadow: "0 0 " + px(S * 0.08) + " " + glow,
  });
  if (mood === "thinking") badgeEl = h("div", { key: "b", style: badgeBase }, "?");
  else if (mood === "concerned")
    badgeEl = h(
      "div",
      {
        key: "b",
        style: Object.assign({}, badgeBase, {
          color: "#E8B45F",
          textShadow: "0 0 " + px(S * 0.08) + " #E8B45F",
        }),
      },
      "!",
    );
  else if (mood === "sleeping")
    badgeEl = h(
      "div",
      { key: "b", style: Object.assign({}, badgeBase, { fontSize: px(S * 0.18) }) },
      "z",
    );
  else if (mood === "working")
    badgeEl = h("div", {
      key: "b",
      style: abs({
        right: px(-S * 0.04),
        top: px(headTop - S * 0.04),
        width: px(S * 0.18),
        height: px(S * 0.18),
        borderRadius: "50%",
        border: px(S * 0.035) + " solid " + glow + "44",
        borderTopColor: glow,
        animation: "rb-spin .9s linear infinite",
      }),
    });

  // ---- structural parts ----
  const shadow = D(
    abs({
      left: px(W / 2 - S * 0.36),
      top: px(H - S * 0.12),
      width: px(S * 0.72),
      height: px(S * 0.12),
      background: "radial-gradient(50% 50% at 50% 50%, rgba(0,0,0,.45), transparent 70%)",
    }),
  );

  const antTip = D(
    abs({
      left: px(W / 2 - S * 0.07),
      top: 0,
      width: px(S * 0.14),
      height: px(S * 0.14),
      borderRadius: "50%",
      background: glow,
      boxShadow: "0 0 " + px(S * 0.12) + " " + glow,
      animation: "rb-pulse 1.8s ease-in-out infinite",
    }),
  );
  const antStalk = D(
    abs({
      left: px(W / 2 - S * 0.022),
      top: px(S * 0.1),
      width: px(S * 0.044),
      height: px(headTop - S * 0.08),
      background: dark,
      borderRadius: px(S * 0.03),
    }),
  );

  const earL = D(
    abs({
      left: px(headLeft - S * 0.05),
      top: px(headTop + S * 0.3),
      width: px(S * 0.1),
      height: px(S * 0.26),
      borderRadius: px(S * 0.05),
      background: dark,
    }),
  );
  const earR = D(
    abs({
      left: px(headLeft + S - S * 0.05),
      top: px(headTop + S * 0.3),
      width: px(S * 0.1),
      height: px(S * 0.26),
      borderRadius: px(S * 0.05),
      background: dark,
    }),
  );

  const head = D(
    abs({
      left: px(headLeft),
      top: px(headTop),
      width: px(S),
      height: px(S * 0.9),
      borderRadius: px(S * 0.3),
      background:
        "linear-gradient(165deg, rgba(255,255,255,.28), rgba(255,255,255,0) 52%), " + body,
      boxShadow:
        "inset 0 " +
        px(S * 0.05) +
        " " +
        px(S * 0.06) +
        " rgba(255,255,255,.25), inset 0 " +
        px(-S * 0.06) +
        " " +
        px(S * 0.08) +
        " " +
        dark +
        ", 0 " +
        px(S * 0.12) +
        " " +
        px(S * 0.22) +
        " rgba(0,0,0,.35)",
    }),
  );

  const screenEl = D(
    abs({
      left: px(screenLeft),
      top: px(screenTop),
      width: px(screenW),
      height: px(screenH),
      borderRadius: px(S * 0.16),
      background: "radial-gradient(120% 100% at 50% 0%, #2b2742, " + screen + ")",
      boxShadow:
        "inset 0 0 " +
        px(S * 0.06) +
        " rgba(0,0,0,.6), inset 0 " +
        px(S * 0.02) +
        " " +
        px(S * 0.03) +
        " rgba(255,255,255,.05)",
      border: px(Math.max(1, S * 0.012)) + " solid rgba(0,0,0,.35)",
      overflow: "hidden",
    }),
    [
      // visor shine
      D(
        abs({
          left: px(-S * 0.1),
          top: px(-S * 0.1),
          width: px(S * 0.5),
          height: px(screenH + S * 0.2),
          background: "linear-gradient(105deg, rgba(255,255,255,.10), rgba(255,255,255,0) 70%)",
          transform: "skewX(-12deg)",
        }),
      ),
    ],
  );

  return D(
    {
      position: "relative",
      width: px(W),
      height: px(H),
      animation: "rb-float 3s ease-in-out infinite",
    },
    [
      h("div", { key: "shadow", style: shadow.props.style }, shadow.props.children),
      earL,
      earR,
      antStalk,
      antTip,
      head,
      screenEl,
      ...eyeEls,
      mouthEl,
      scanEl,
      badgeEl,
    ],
  );
}

// ---- Terminal version: the same robot as Unicode block art + truecolor ----
// This is what a capable terminal (truecolor, Unicode) actually renders.
function robotTermGrid(mood, blink) {
  const base = [
    "........AA..........",
    "........DD..........",
    "....BBBBBBBBBBBB....",
    "...BBBBBBBBBBBBBB...",
    "..BBBBBBBBBBBBBBBB..",
    "..BBBBBBBBBBBBBBBB..",
    "DDBBSSSSSSSSSSSSBBDD",
    "DDBBSSSSSSSSSSSSBBDD",
    "DDBBSSEESSSSEESSBBDD",
    "DDBBSSEESSSSEESSBBDD",
    "DDBBSSEESSSSEESSBBDD",
    "DDBBSSSSSSSSSSSSBBDD",
    "DDBBSSSSMMMMSSSSBBDD",
    "..BBBBBBBBBBBBBBBB..",
    "...BBBBBBBBBBBBBB...",
    "....BBBBBBBBBBBB....",
    "......BBBBBBBB......",
  ].map((s) => s.split(""));
  const set = (r, c, ch) => {
    if (base[r] && base[r][c] !== undefined) base[r][c] = ch;
  };
  const eyeCols = [6, 7, 12, 13];
  const closed = blink || mood === "sleeping";
  if (closed) {
    eyeCols.forEach((c) => {
      set(8, c, "S");
      set(10, c, "S");
    });
  } else if (mood === "happy") {
    eyeCols.forEach((c) => set(10, c, "S"));
    [7, 8, 9, 10, 11, 12].forEach((c) => set(12, c, "M"));
  } else if (mood === "thinking") {
    eyeCols.forEach((c) => {
      set(10, c, "S");
      set(7, c, "E");
    });
  } else if (mood === "concerned") {
    [5, 8, 11, 14].forEach((c) => {
      set(8, c, "E");
      set(9, c, "E");
      set(10, c, "E");
    });
    set(12, 8, "S");
    set(12, 11, "S");
  } else if (mood === "working") {
    for (let c = 4; c <= 15; c++) set(11, c, "M");
  }
  return base;
}

export function robotTerminalElement(React, mood, cell, palette, blink) {
  const h = React.createElement;
  cell = Number(cell) || 11;
  palette = palette || {};
  const body = palette.body || "#8B7AE6",
    dark = palette.dark || "#5E4FB8";
  const glow = palette.glow || palette.antenna || "#7DEFE6",
    screen = palette.screen || "#141124";
  const dim = (hex) => (hex.length === 7 ? hex + "88" : hex);
  const COL = { B: body, D: dark, S: screen, E: glow, A: glow, M: dim(glow) };
  const grid = robotTermGrid(mood, blink);
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
        const isGlow = ch === "E" || ch === "A";
        spans.push(
          h(
            "span",
            {
              key: i,
              style: {
                color: COL[ch],
                textShadow: isGlow ? "0 0 " + cell * 0.5 + "px " + glow : "none",
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
          top: cell * 0.4,
          right: -cell * 1.6,
          fontSize: cell * 1.9,
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
