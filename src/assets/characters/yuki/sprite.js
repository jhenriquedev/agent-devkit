// Yuki — robot-kitten mascot built from CSS shapes (original design, winter/ice vibe).
// Signature: white robo-cat head, pointy ears, dark visor with two big GLOWING round eyes,
// tiny nose, blush cheeks, little scarf. `palette.body` recolors the EYE GLOW (Yuki's identity).
// Requires @keyframes rb-float, rb-pulse, rb-spin in the host page's <helmet>.

export function yukiElement(React, mood, size, blink, palette) {
  const h = React.createElement;
  mood = mood || "idle";
  const S = Number(size) || 120;
  palette = palette || {};
  const eyeGlow = palette.body || "#7CC4FF";
  const eyeDk = palette.dark || "#3E6E9E";
  const shell = "#EEF3F9",
    shellDk = "#C3D0DE";
  const visor = "#1E2533",
    visorEdge = "#10151F";
  const earIn = "#2A3342";
  const nose = "#F2A8C0";

  const W = S * 1.5,
    H = S * 1.52,
    cx = W / 2;
  const headW = S,
    headH = S * 0.94,
    headLeft = cx - headW / 2,
    headTop = S * 0.38;
  const px = (n) => n + "px";
  const abs = (st) => Object.assign({ position: "absolute" }, st);
  const D = (st, kids) => h("div", { style: st }, kids);
  const dim = mood === "sleeping";
  const closed = blink || mood === "sleeping";
  const kids = [];

  // shadow
  kids.push(
    D(
      abs({
        left: px(cx - S * 0.4),
        top: px(H - S * 0.1),
        width: px(S * 0.8),
        height: px(S * 0.12),
        background: "radial-gradient(50% 50% at 50% 50%, rgba(0,0,0,.34), transparent 70%)",
      }),
    ),
  );

  // ears (cones) — white shell with inner tint
  const earClip = "polygon(50% 0%, 78% 70%, 66% 100%, 34% 100%, 22% 70%)";
  const earInClip = "polygon(50% 18%, 70% 72%, 30% 72%)";
  const mkEar = (left, top, rot) =>
    D(
      abs({
        left: px(left),
        top: px(top),
        width: px(S * 0.34),
        height: px(S * 0.4),
        transform: "rotate(" + rot + "deg)",
        transformOrigin: "50% 100%",
      }),
      [
        D({
          position: "absolute",
          inset: 0,
          background: "linear-gradient(165deg," + shell + "," + shellDk + ")",
          clipPath: earClip,
        }),
        D({ position: "absolute", inset: 0, background: earIn, clipPath: earInClip }),
      ],
    );
  kids.push(mkEar(headLeft - S * 0.04, headTop - S * 0.26, -16));
  kids.push(mkEar(headLeft + headW - S * 0.3, headTop - S * 0.26, 16));

  // feet
  kids.push(
    D(
      abs({
        left: px(cx - S * 0.22),
        top: px(headTop + headH - S * 0.04),
        width: px(S * 0.15),
        height: px(S * 0.11),
        borderRadius: px(S * 0.05),
        background: shellDk,
      }),
    ),
  );
  kids.push(
    D(
      abs({
        left: px(cx + S * 0.07),
        top: px(headTop + headH - S * 0.04),
        width: px(S * 0.15),
        height: px(S * 0.11),
        borderRadius: px(S * 0.05),
        background: shellDk,
      }),
    ),
  );

  // scarf (winter nod)
  kids.push(
    D(
      abs({
        left: px(cx - S * 0.34),
        top: px(headTop + headH - S * 0.16),
        width: px(S * 0.68),
        height: px(S * 0.16),
        borderRadius: px(S * 0.09),
        background: "linear-gradient(180deg," + eyeGlow + "," + eyeDk + ")",
        boxShadow: "0 " + px(S * 0.02) + " " + px(S * 0.04) + " rgba(0,0,0,.25)",
      }),
    ),
  );

  // head
  kids.push(
    D(
      abs({
        left: px(headLeft),
        top: px(headTop),
        width: px(headW),
        height: px(headH),
        borderRadius: px(S * 0.42),
        background: "linear-gradient(160deg, #FFFFFF, " + shell + " 50%, " + shellDk + ")",
        boxShadow:
          "inset 0 " +
          px(S * 0.05) +
          " " +
          px(S * 0.06) +
          " rgba(255,255,255,.9), inset 0 " +
          px(-S * 0.06) +
          " " +
          px(S * 0.08) +
          " " +
          shellDk +
          ", 0 " +
          px(S * 0.12) +
          " " +
          px(S * 0.2) +
          " rgba(0,0,0,.28)",
      }),
    ),
  );

  // visor (dark face)
  const vW = S * 0.8,
    vH = S * 0.5,
    vLeft = cx - vW / 2,
    vTop = headTop + S * 0.18;
  kids.push(
    D(
      abs({
        left: px(vLeft),
        top: px(vTop),
        width: px(vW),
        height: px(vH),
        borderRadius: px(S * 0.24),
        overflow: "hidden",
        background: "radial-gradient(120% 120% at 50% 25%, #2A3242, " + visor + ")",
        border: px(Math.max(1, S * 0.012)) + " solid " + visorEdge,
        boxShadow: "inset 0 0 " + px(S * 0.06) + " rgba(0,0,0,.6)",
      }),
      [
        D(
          abs({
            left: px(-S * 0.05),
            top: px(-S * 0.08),
            width: px(vW * 0.5),
            height: px(vH + S * 0.16),
            background: "linear-gradient(105deg, rgba(255,255,255,.12), rgba(255,255,255,0) 60%)",
            transform: "skewX(-12deg)",
          }),
        ),
      ],
    ),
  );

  // cheeks
  if (!dim) {
    [cx - S * 0.34, cx + S * 0.34].forEach((c) =>
      kids.push(
        D(
          abs({
            left: px(c - S * 0.06),
            top: px(vTop + vH * 0.62),
            width: px(S * 0.12),
            height: px(S * 0.07),
            borderRadius: "50%",
            background: eyeGlow,
            opacity: 0.35,
          }),
        ),
      ),
    );
  }

  // eyes (the glowing lenses)
  const eyeD = S * 0.3,
    eyeCy = vTop + vH * 0.46;
  const eyeCxL = cx - S * 0.17,
    eyeCxR = cx + S * 0.17;
  const glowShadow = dim ? "none" : "0 0 " + px(eyeD * 0.5) + " " + eyeGlow;
  const drawEye = (c) => {
    if (closed) {
      return D(
        abs({
          left: px(c - eyeD / 2),
          top: px(eyeCy - eyeD * 0.08),
          width: px(eyeD),
          height: px(eyeD * 0.16),
          borderRadius: px(eyeD),
          background: eyeGlow,
          opacity: dim ? 0.5 : 1,
          boxShadow: glowShadow,
        }),
      );
    }
    if (mood === "happy") {
      return D(
        abs({
          left: px(c - eyeD / 2),
          top: px(eyeCy - eyeD * 0.3),
          width: px(eyeD),
          height: px(eyeD * 0.62),
          borderBottom: px(eyeD * 0.18) + " solid " + eyeGlow,
          borderRadius: "0 0 " + px(eyeD) + " " + px(eyeD),
          boxShadow: glowShadow,
        }),
      );
    }
    const big = mood === "concerned";
    const d = big ? eyeD * 1.12 : eyeD;
    const ring = D(
      abs({
        left: px(c - d / 2),
        top: px(eyeCy - d / 2),
        width: px(d),
        height: px(d),
        borderRadius: "50%",
        background: "radial-gradient(circle at 38% 32%, #3a4658, #10151f)",
        border: px(d * 0.15) + " solid " + eyeGlow,
        boxShadow: glowShadow + ", inset 0 0 " + px(d * 0.2) + " " + eyeGlow,
      }),
      [
        D({
          position: "absolute",
          left: "26%",
          top: mood === "thinking" ? "14%" : "30%",
          width: "26%",
          height: "26%",
          borderRadius: "50%",
          background: "#EAF6FF",
          opacity: 0.95,
        }),
      ],
    );
    return ring;
  };
  kids.push(drawEye(eyeCxL));
  kids.push(drawEye(eyeCxR));

  // nose
  kids.push(
    D(
      abs({
        left: px(cx - S * 0.04),
        top: px(vTop + vH - S * 0.02),
        width: px(S * 0.08),
        height: px(S * 0.06),
        background: nose,
        borderRadius: "50% 50% 50% 50% / 30% 30% 80% 80%",
      }),
    ),
  );

  // mouth
  if (mood === "happy") {
    kids.push(
      D(
        abs({
          left: px(cx - S * 0.07),
          top: px(vTop + vH + S * 0.03),
          width: px(S * 0.14),
          height: px(S * 0.07),
          borderBottom: px(S * 0.025) + " solid " + shellDk,
          borderRadius: "0 0 " + px(S * 0.1) + " " + px(S * 0.1),
        }),
      ),
    );
  } else if (mood === "concerned") {
    kids.push(
      D(
        abs({
          left: px(cx - S * 0.03),
          top: px(vTop + vH + S * 0.03),
          width: px(S * 0.06),
          height: px(S * 0.05),
          border: px(S * 0.02) + " solid " + shellDk,
          borderRadius: "50%",
        }),
      ),
    );
  }

  // whiskers
  if (!closed) {
    [-1, 1].forEach((sgn) => {
      [-8, 6].forEach((rot, i) =>
        kids.push(
          D(
            abs({
              left: px(sgn > 0 ? cx + S * 0.12 : cx - S * 0.34),
              top: px(vTop + vH + S * 0.02 + i * S * 0.06),
              width: px(S * 0.22),
              height: px(Math.max(1.2, S * 0.012)),
              background: shellDk,
              opacity: 0.6,
              borderRadius: "2px",
              transform: "rotate(" + sgn * rot + "deg)",
            }),
          ),
        ),
      );
    });
  }

  // badge
  const badges = {
    thinking: ["?", eyeGlow],
    concerned: ["!", "#E8B45F"],
    sleeping: ["z", eyeGlow],
    working: ["\u25cc", eyeGlow],
  };
  const b = badges[mood];
  if (b)
    kids.push(
      D(
        abs({
          top: px(headTop - S * 0.04),
          right: px(S * 0.06),
          fontFamily: "'JetBrains Mono',monospace",
          fontWeight: 700,
          fontSize: px(S * 0.24),
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
        animation: "rb-float 3s ease-in-out infinite",
      },
    },
    kids.map((c, i) => React.cloneElement(c, { key: i })),
  );
}

// ---- Terminal version: Yuki as Unicode block art ----
function yukiTermGrid(mood, blink) {
  const base = [
    "...K..........K....",
    "..WKW........WKW...",
    "..WWW........WWW...",
    ".WWWWWWWWWWWWWWWWW..",
    "WWWWWWWWWWWWWWWWWWW.",
    "WWWFFFFFFFFFFFFFWWW.",
    "WWFFEEEEFFFFEEEEFFW.",
    "WWFEEPPEEFFEEPPEEFW.",
    "WWFEEPPEEFFEEPPEEFW.",
    "WWFFEEEEFFFFEEEEFFW.",
    "WWWFFFFFNNFFFFFFWWW.",
    ".WWWFFFFFFFFFFFWWW..",
    ".WWWWWWWWWWWWWWWWW..",
    "..WWWWWWWWWWWWWWW...",
    "....WWWWWWWWWWW.....",
  ].map((s) => s.split(""));
  const set = (r, c, ch) => {
    if (base[r] && base[r][c] !== undefined) base[r][c] = ch;
  };
  const eyeBlocks = [
    [4, 7],
    [12, 15],
  ]; // col ranges of the two eyes
  const closed = blink || mood === "sleeping";
  if (closed) {
    for (const [a, b] of eyeBlocks)
      for (let c = a; c <= b; c++) {
        set(6, c, "F");
        set(9, c, "F");
        set(7, c, c === a || c === b ? "F" : "E");
        set(8, c, c === a || c === b ? "F" : "E");
      }
  } else if (mood === "thinking") {
    for (const [a, b] of eyeBlocks)
      for (let c = a; c <= b; c++) {
        set(9, c, "F");
        set(5, c, c === a || c === b ? "F" : "E");
      }
  }
  return base;
}

export function yukiTerminalElement(React, mood, cell, palette, blink) {
  const h = React.createElement;
  cell = Number(cell) || 11;
  palette = palette || {};
  const eyeGlow = palette.body || "#7CC4FF";
  const dim = mood === "sleeping";
  const W = "#E7EEF6",
    F = "#1C2331",
    K = "#2A3342",
    P = "#0E1320";
  const COL = { W: W, F: F, K: K, E: dim ? "#4E7CA0" : eyeGlow, P: P, N: "#F2A8C0" };
  const grid = yukiTermGrid(mood, blink);
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
        const isE = ch === "E";
        spans.push(
          h(
            "span",
            {
              key: i,
              style: {
                color: COL[ch],
                textShadow: isE && !dim ? "0 0 " + cell * 0.5 + "px " + eyeGlow : "none",
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
    thinking: ["?", eyeGlow],
    concerned: ["!", "#E8B45F"],
    sleeping: ["z", eyeGlow],
    working: ["\u25cc", eyeGlow],
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
