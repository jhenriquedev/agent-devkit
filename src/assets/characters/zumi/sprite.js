// Zumi — flying robot-bug mascot built from CSS shapes (original design, hovering drone vibe).
// Signature: glossy chrome ovoid body, two big dark wrap-around eyes with glowing pupils,
// antenna, fluttering translucent wings, dangling limbs, floats above its shadow.
// `palette.body` recolors the EYE GLOW / antenna tip (Zumi's identity stays chrome).
// Requires @keyframes rb-float, rb-pulse, rb-spin, zm-flutter in the host page's <helmet>.

export function zumiElement(React, mood, size, blink, palette) {
  const h = React.createElement;
  mood = mood || "idle";
  const S = Number(size) || 120;
  palette = palette || {};
  const glow = palette.body || "#8FE3FF";
  const shell = "#F4F7FB",
    shellMid = "#D7E0EA",
    shellDk = "#AEBBCB";
  const eyeDk = "#1A1F2A",
    eyeMid = "#39414F";

  const W = S * 1.7,
    H = S * 1.85,
    cx = W / 2;
  const bodyW = S * 1.12,
    bodyH = S * 0.82,
    bodyLeft = cx - bodyW / 2,
    bodyTop = S * 0.56;
  const px = (n) => n + "px";
  const abs = (st) => Object.assign({ position: "absolute" }, st);
  const D = (st, kids) => h("div", { style: st }, kids);
  const dim = mood === "sleeping";
  const closed = blink || mood === "sleeping";
  const kids = [];

  // ground shadow (it's airborne — shadow sits far below)
  kids.push(
    D(
      abs({
        left: px(cx - S * 0.3),
        top: px(H - S * 0.06),
        width: px(S * 0.6),
        height: px(S * 0.09),
        background: "radial-gradient(50% 50% at 50% 50%, rgba(0,0,0,.28), transparent 70%)",
      }),
    ),
  );

  // wings (wrapper sets base angle; inner flutters)
  const wing = (baseRot, len, wide, delay) =>
    D(
      abs({
        left: px(cx - wide / 2),
        top: px(bodyTop - S * 0.02),
        width: px(wide),
        height: px(len),
        transform: "rotate(" + baseRot + "deg)",
        transformOrigin: "50% 100%",
      }),
      [
        D(
          {
            position: "absolute",
            inset: 0,
            transformOrigin: "50% 100%",
            animation: "zm-flutter .16s ease-in-out " + delay + "ms infinite alternate",
          },
          [
            D({
              position: "absolute",
              inset: 0,
              borderRadius: "50% 50% 48% 48% / 70% 70% 30% 30%",
              background: "linear-gradient(180deg, rgba(255,255,255,.55), rgba(180,210,235,.18))",
              border: "1px solid rgba(255,255,255,.6)",
              boxShadow: "inset 0 0 " + px(S * 0.06) + " rgba(255,255,255,.5)",
            }),
          ],
        ),
      ],
    );
  kids.push(wing(-36, S * 0.86, S * 0.26, 0));
  kids.push(wing(-20, S * 0.62, S * 0.2, 40));
  kids.push(wing(36, S * 0.86, S * 0.26, 20));
  kids.push(wing(20, S * 0.62, S * 0.2, 60));

  // antenna
  kids.push(
    D(
      abs({
        left: px(cx - S * 0.018),
        top: px(bodyTop - S * 0.22),
        width: px(S * 0.036),
        height: px(S * 0.26),
        background: shellDk,
        borderRadius: px(S * 0.02),
        transform: "rotate(-8deg)",
        transformOrigin: "50% 100%",
      }),
    ),
  );
  kids.push(
    D(
      abs({
        left: px(cx - S * 0.05),
        top: px(bodyTop - S * 0.28),
        width: px(S * 0.1),
        height: px(S * 0.1),
        borderRadius: "50%",
        background: glow,
        boxShadow: "0 0 " + px(S * 0.1) + " " + glow,
        animation: "rb-pulse 1.8s ease-in-out infinite",
      }),
    ),
  );

  // dangling limbs
  const limb = (lx, rot) =>
    D(
      abs({
        left: px(lx),
        top: px(bodyTop + bodyH * 0.78),
        width: px(S * 0.09),
        height: px(S * 0.42),
        transform: "rotate(" + rot + "deg)",
        transformOrigin: "50% 0%",
      }),
      [
        D({
          position: "absolute",
          left: 0,
          top: 0,
          width: "100%",
          height: "52%",
          borderRadius: px(S * 0.05),
          background: "linear-gradient(180deg," + shell + "," + shellDk + ")",
        }),
        D({
          position: "absolute",
          left: "8%",
          top: "50%",
          width: "84%",
          height: "54%",
          borderRadius: px(S * 0.05),
          background: "linear-gradient(180deg," + shellMid + "," + shellDk + ")",
        }),
      ],
    );
  kids.push(limb(cx - S * 0.16, 6));
  kids.push(limb(cx + S * 0.07, -6));

  // body (chrome ovoid)
  kids.push(
    D(
      abs({
        left: px(bodyLeft),
        top: px(bodyTop),
        width: px(bodyW),
        height: px(bodyH),
        borderRadius: "50%",
        background:
          "linear-gradient(150deg, #FFFFFF, " +
          shell +
          " 45%, " +
          shellMid +
          " 78%, " +
          shellDk +
          ")",
        boxShadow:
          "inset 0 " +
          px(S * 0.06) +
          " " +
          px(S * 0.07) +
          " rgba(255,255,255,.95), inset 0 " +
          px(-S * 0.06) +
          " " +
          px(S * 0.09) +
          " " +
          shellDk +
          ", 0 " +
          px(S * 0.1) +
          " " +
          px(S * 0.18) +
          " rgba(0,0,0,.22)",
      }),
    ),
  );

  // eyes (two big dark wrap shapes)
  const eW = bodyW * 0.42,
    eH = bodyH * 0.8,
    eTop = bodyTop + bodyH * 0.1;
  const mkEye = (left, flip) => {
    const inner = [
      // glossy highlight
      D(
        abs({
          left: flip ? "16%" : "44%",
          top: "16%",
          width: "34%",
          height: "30%",
          borderRadius: "50%",
          background: "rgba(255,255,255,.85)",
        }),
      ),
      D(
        abs({
          left: flip ? "30%" : "20%",
          top: "54%",
          width: "16%",
          height: "14%",
          borderRadius: "50%",
          background: "rgba(255,255,255,.5)",
        }),
      ),
    ];
    return D(
      abs({
        left: px(left),
        top: px(eTop),
        width: px(eW),
        height: px(eH),
        borderRadius: flip
          ? "42% 56% 50% 50% / 58% 58% 44% 44%"
          : "56% 42% 50% 50% / 58% 58% 44% 44%",
        background:
          "radial-gradient(120% 120% at " +
          (flip ? "70%" : "30%") +
          " 28%, " +
          eyeMid +
          ", " +
          eyeDk +
          ")",
        overflow: "hidden",
        boxShadow: "inset 0 0 " + px(S * 0.05) + " #000",
      }),
      inner,
    );
  };
  kids.push(mkEye(bodyLeft + bodyW * 0.04, false));
  kids.push(mkEye(bodyLeft + bodyW * 0.54, true));

  // glowing pupils / expression (over the eyes)
  const pCxL = bodyLeft + bodyW * 0.25,
    pCxR = bodyLeft + bodyW * 0.75,
    pCy = eTop + eH * 0.5;
  const glowSh = dim ? "none" : "0 0 " + px(S * 0.08) + " " + glow;
  const drawPupil = (c) => {
    if (closed)
      return D(
        abs({
          left: px(c - S * 0.09),
          top: px(pCy - S * 0.01),
          width: px(S * 0.18),
          height: px(S * 0.025),
          borderRadius: px(S * 0.02),
          background: glow,
          opacity: dim ? 0.5 : 0.9,
          boxShadow: glowSh,
        }),
      );
    if (mood === "happy")
      return D(
        abs({
          left: px(c - S * 0.09),
          top: px(pCy - S * 0.06),
          width: px(S * 0.18),
          height: px(S * 0.12),
          borderBottom: px(S * 0.04) + " solid " + glow,
          borderRadius: "0 0 " + px(S * 0.12) + " " + px(S * 0.12),
          boxShadow: glowSh,
        }),
      );
    const d = mood === "concerned" ? S * 0.16 : S * 0.11;
    const dy = mood === "thinking" ? -S * 0.05 : 0;
    return D(
      abs({
        left: px(c - d / 2),
        top: px(pCy - d / 2 + dy),
        width: px(d),
        height: px(d),
        borderRadius: "50%",
        background: glow,
        boxShadow: glowSh + ", inset 0 0 " + px(S * 0.03) + " #fff",
      }),
    );
  };
  kids.push(drawPupil(pCxL));
  kids.push(drawPupil(pCxR));

  // badge
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
          top: px(bodyTop - S * 0.04),
          right: px(S * 0.12),
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
        animation: "rb-float " + (dim ? "4s" : "2.4s") + " ease-in-out infinite",
      },
    },
    kids.map((c, i) => React.cloneElement(c, { key: i })),
  );
}

// ---- Terminal version: Zumi as Unicode block art ----
function zumiTermGrid(mood, blink) {
  const base = [
    "..G..............G..",
    "...G....AA....G.....",
    "....G...BB...G......",
    ".....G..BB..G.......",
    "......BBBBBBBB......",
    "....BBBBBBBBBBBB....",
    "...BBSSSSBBSSSSBB...",
    "..BBSSPPSSSSPPSSBB..",
    "..BBSSPPSSSSPPSSBB..",
    "..BBSSSSBBSSSSSSBB..",
    "...BBBBBBBBBBBBBB...",
    "....BBBBBBBBBBBB....",
    ".......B....B.......",
    ".......B....B.......",
    "......BB....BB......",
  ].map((s) => s.split(""));
  const set = (r, c, ch) => {
    if (base[r] && base[r][c] !== undefined) base[r][c] = ch;
  };
  const pcols = [
    [6, 7],
    [12, 13],
  ];
  const closed = blink || mood === "sleeping";
  if (closed) {
    for (const [a, b] of pcols)
      for (let c = a; c <= b; c++) {
        set(7, c, "S");
        set(8, c, "S");
      }
  } else if (mood === "thinking") {
    for (const [a, b] of pcols)
      for (let c = a; c <= b; c++) {
        set(8, c, "S");
        set(7, c, "P");
      }
  }
  return base;
}

export function zumiTerminalElement(React, mood, cell, palette, blink) {
  const h = React.createElement;
  cell = Number(cell) || 11;
  palette = palette || {};
  const glow = palette.body || "#8FE3FF";
  const dim = mood === "sleeping";
  const COL = {
    B: "#E7EEF6",
    S: "#1A1F2A",
    P: dim ? "#4E7CA0" : glow,
    A: "#AEBBCB",
    G: "rgba(180,210,235,.45)",
  };
  const grid = zumiTermGrid(mood, blink);
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
        const isP = ch === "P";
        spans.push(
          h(
            "span",
            {
              key: i,
              style: {
                color: COL[ch],
                textShadow: isP && !dim ? "0 0 " + cell * 0.5 + "px " + glow : "none",
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
          right: -cell * 1.4,
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
