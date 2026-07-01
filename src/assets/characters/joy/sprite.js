// Joy — round gamepad-bot mascot (CSS shapes). Inspired by a handheld-console robot.
// Signature: round body, dark console screen face (eyes+smile), D-pad + buttons, antenna loop,
// stubby arms, little thrusters. `palette.body` recolors the body (default warm yellow).
// Requires @keyframes rb-float, rb-pulse, rb-spin in the host page's <helmet>.

export function joyElement(React, mood, size, blink, palette) {
  const h = React.createElement;
  mood = mood || "idle";
  const S = Number(size) || 120;
  palette = palette || {};
  const body = palette.body || "#FFCB3A";
  const bodyDk = palette.dark || "#E0A21E";
  const screen = "#15151E",
    screenGlow = palette.glow || "#FFE08A";
  const dark = "#2A2A33",
    red = "#E8584E",
    teal = "#3FC8C0";
  const W = S * 1.55,
    H = S * 1.6,
    cx = W / 2;
  const bw = S * 1.12,
    bh = S * 1.06,
    bl = cx - bw / 2,
    bt = S * 0.34;
  const px = (n) => n + "px";
  const abs = (st) => Object.assign({ position: "absolute" }, st);
  const D = (st, kids) => h("div", { style: st }, kids);
  const dim = mood === "sleeping",
    closed = blink || mood === "sleeping";
  const kids = [];

  kids.push(
    D(
      abs({
        left: px(cx - S * 0.42),
        top: px(H - S * 0.08),
        width: px(S * 0.84),
        height: px(S * 0.12),
        background: "radial-gradient(50% 50% at 50% 50%, rgba(0,0,0,.28), transparent 70%)",
      }),
    ),
  );
  // antenna (triangle loop)
  kids.push(
    D(
      abs({
        left: px(cx - S * 0.09),
        top: px(bt - S * 0.24),
        width: px(S * 0.18),
        height: px(S * 0.2),
        border: px(Math.max(2, S * 0.022)) + " solid " + bodyDk,
        clipPath: "polygon(50% 0,100% 100%,0 100%)",
        background: "transparent",
        transform: "rotate(6deg)",
      }),
    ),
  );
  // arms
  kids.push(
    D(
      abs({
        left: px(bl - S * 0.16),
        top: px(bt + bh * 0.4),
        width: px(S * 0.26),
        height: px(S * 0.16),
        borderRadius: px(S * 0.09),
        background: "linear-gradient(180deg," + dark + ",#1a1a22)",
        transform: "rotate(-12deg)",
      }),
    ),
  );
  kids.push(
    D(
      abs({
        left: px(bl + bw - S * 0.1),
        top: px(bt + bh * 0.4),
        width: px(S * 0.26),
        height: px(S * 0.16),
        borderRadius: px(S * 0.09),
        background: "linear-gradient(180deg," + dark + ",#1a1a22)",
        transform: "rotate(12deg)",
      }),
    ),
  );
  // thrusters/feet
  [-0.2, 0.2].forEach((o) =>
    kids.push(
      D(
        abs({
          left: px(cx + S * o - S * 0.06),
          top: px(bt + bh - S * 0.02),
          width: px(S * 0.12),
          height: px(S * 0.14),
          borderRadius: "40% 40% 50% 50%",
          background: "linear-gradient(180deg,#C0C8D2,#7E8794)",
        }),
      ),
    ),
  );
  // body sphere
  kids.push(
    D(
      abs({
        left: px(bl),
        top: px(bt),
        width: px(bw),
        height: px(bh),
        borderRadius: "50%",
        background:
          "radial-gradient(120% 120% at 32% 26%, #FFFFFF 2%, " + body + " 34%, " + bodyDk + ")",
        boxShadow:
          "inset 0 " +
          px(-S * 0.08) +
          " " +
          px(S * 0.1) +
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
  // console screen
  const swW = bw * 0.62,
    swH = bh * 0.42,
    swL = cx - swW / 2,
    swT = bt + bh * 0.16;
  kids.push(
    D(
      abs({
        left: px(swL),
        top: px(swT),
        width: px(swW),
        height: px(swH),
        borderRadius: px(S * 0.08),
        background: screen,
        border: px(Math.max(2, S * 0.02)) + " solid #C7CCD6",
        boxShadow: "inset 0 0 " + px(S * 0.05) + " #000",
      }),
    ),
  );
  // face on screen
  const eL = swL + swW * 0.34,
    eR = swL + swW * 0.66,
    eY = swT + swH * 0.42;
  const gsh = dim ? "none" : "0 0 " + px(S * 0.05) + " " + screenGlow;
  const eye = (c) => {
    if (closed || mood === "happy")
      return D(
        abs({
          left: px(c - S * 0.05),
          top: px(eY - S * 0.005),
          width: px(S * 0.1),
          height: px(S * 0.05),
          borderTop: px(S * 0.022) + " solid " + screenGlow,
          borderRadius: px(S * 0.06) + " " + px(S * 0.06) + " 0 0",
          boxShadow: gsh,
        }),
      );
    const dy = mood === "thinking" ? -S * 0.03 : 0;
    const d = mood === "concerned" ? S * 0.09 : S * 0.06;
    return D(
      abs({
        left: px(c - d / 2),
        top: px(eY - d / 2 + dy),
        width: px(d),
        height: px(d),
        borderRadius: "50%",
        background: screenGlow,
        boxShadow: gsh,
      }),
    );
  };
  kids.push(eye(eL));
  kids.push(eye(eR));
  const mY = swT + swH * 0.72;
  if (!closed) {
    const mw = mood === "happy" ? S * 0.18 : S * 0.12;
    kids.push(
      D(
        abs({
          left: px(cx - mw / 2),
          top: px(mY - S * 0.04),
          width: px(mw),
          height: px(S * 0.07),
          borderBottom: px(S * 0.02) + " solid " + screenGlow,
          borderRadius: "0 0 " + px(S * 0.1) + " " + px(S * 0.1),
          opacity: 0.9,
        }),
      ),
    );
  }
  // D-pad
  const dpx = swL + S * 0.02,
    dpy = swT + swH + S * 0.06;
  kids.push(
    D(
      abs({
        left: px(dpx),
        top: px(dpy + S * 0.04),
        width: px(S * 0.18),
        height: px(S * 0.06),
        borderRadius: "2px",
        background: dark,
      }),
    ),
  );
  kids.push(
    D(
      abs({
        left: px(dpx + S * 0.06),
        top: px(dpy - S * 0.02),
        width: px(S * 0.06),
        height: px(S * 0.18),
        borderRadius: "2px",
        background: dark,
      }),
    ),
  );
  // buttons
  kids.push(
    D(
      abs({
        left: px(swL + swW - S * 0.04),
        top: px(dpy + S * 0.01),
        width: px(S * 0.075),
        height: px(S * 0.075),
        borderRadius: "50%",
        background: red,
      }),
    ),
  );
  kids.push(
    D(
      abs({
        left: px(swL + swW - S * 0.13),
        top: px(dpy + S * 0.08),
        width: px(S * 0.075),
        height: px(S * 0.075),
        borderRadius: "50%",
        background: teal,
      }),
    ),
  );

  const badges = {
    thinking: ["?", screenGlow],
    concerned: ["!", "#E8B45F"],
    sleeping: ["z", screenGlow],
    working: ["\u25cc", screenGlow],
  };
  const b = badges[mood];
  if (b)
    kids.push(
      D(
        abs({
          top: px(bt - S * 0.02),
          right: px(S * 0.05),
          fontFamily: "'JetBrains Mono',monospace",
          fontWeight: 700,
          fontSize: px(S * 0.22),
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
        animation: "rb-float 2.8s ease-in-out infinite",
      },
    },
    kids.map((c, i) => React.cloneElement(c, { key: i })),
  );
}

function joyTermGrid(mood, blink) {
  const base = [
    "........YbY........",
    ".......YYbYY.......",
    ".....YYYYYYYYY.....",
    "...DDYYYYYYYYYDD...",
    "..DDYYYYYYYYYYYDD..",
    "..bYYCCCCCCCCCYYb..",
    "..bYYCEECCEECCYYb..",
    "..bYYCCCCCCCCCYYb..",
    "..bYYCCmmmmmCCYYb..",
    "...YYYYYYYYYYYYY...",
    "...YYPYYYYYYRYYY...",
    "...YPPPYYYYRRRYY...",
    "...YYPYYYYYYTYYY...",
    "....YYYYYYYYYYY....",
    ".....GG.....GG.....",
  ].map((s) => s.split(""));
  const set = (r, c, ch) => {
    if (base[r] && base[r][c] !== undefined) base[r][c] = ch;
  };
  const closed = blink || mood === "sleeping";
  if (closed || mood === "happy") {
    for (const c of [5, 6, 9, 10]) {
      set(6, c, "C");
      set(7, c, c === 5 || c === 9 ? "C" : "E");
    }
  }
  return base;
}

export function joyTerminalElement(React, mood, cell, palette, blink) {
  const h = React.createElement;
  cell = Number(cell) || 10;
  palette = palette || {};
  const body = palette.body || "#FFCB3A";
  const dim = mood === "sleeping";
  const glow = palette.glow || "#FFE08A";
  const COL = {
    Y: body,
    b: "#C9961C",
    D: "#2A2A33",
    C: "#15151E",
    E: dim ? "#8a7a3a" : glow,
    m: dim ? "#8a7a3a" : glow,
    P: "#2A2A33",
    R: "#E8584E",
    T: "#3FC8C0",
    G: "#9AA3AF",
  };
  const grid = joyTermGrid(mood, blink);
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
        const isE = ch === "E" || ch === "m";
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
          right: -cell * 1.3,
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
