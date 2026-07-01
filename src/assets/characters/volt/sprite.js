// Volt — chibi robot-pup mascot built from CSS shapes (no pixels, no SVG file).
// Signature: glowing orange TV-screen face with dark vertical-bar eyes + cheeky smirk,
// teal metal chassis, two tall pointy ears, headphone disc, power-plug tail.
// `palette` recolors the CHASSIS (metal); the orange screen is Volt's fixed identity.
// Requires @keyframes rb-float, rb-pulse, rb-spin in the host page's <helmet>.

export function voltElement(React, mood, size, blink, palette) {
  const h = React.createElement;
  mood = mood || "idle";
  const S = Number(size) || 120;
  palette = palette || {};
  const metal = palette.body || "#92B7B0";
  const metalDk = palette.dark || "#5E7E78";
  const accent = palette.glow || "#9FE8DE";
  // fixed orange screen identity
  const oL = "#FFD56B",
    oM = "#FF9A3C",
    oD = "#FF6B2C",
    oGlow = "#FF8A3D";
  const face = "#46220F",
    tongue = "#E0553C";

  const W = S * 1.5,
    H = S * 1.46,
    cx = W / 2;
  const headW = S,
    headH = S * 0.84,
    headLeft = cx - headW / 2,
    headTop = S * 0.36;
  const px = (n) => n + "px";
  const abs = (st) => Object.assign({ position: "absolute" }, st);
  const D = (st, kids) => h("div", { style: st }, kids);

  const dim = mood === "sleeping";
  const closed = blink || mood === "sleeping";
  const kids = [];

  kids.push(
    D(
      abs({
        left: px(cx - S * 0.42),
        top: px(H - S * 0.1),
        width: px(S * 0.84),
        height: px(S * 0.12),
        background: "radial-gradient(50% 50% at 50% 50%, rgba(0,0,0,.4), transparent 70%)",
      }),
    ),
  );

  // ears (pointy cones)
  const earClip = "polygon(50% 0%, 72% 52%, 63% 100%, 37% 100%, 28% 52%)";
  kids.push(
    D(
      abs({
        left: px(headLeft - S * 0.02),
        top: px(headTop - S * 0.4),
        width: px(S * 0.2),
        height: px(S * 0.56),
        background: "linear-gradient(180deg," + accent + "," + metal + " 42%," + metalDk + ")",
        clipPath: earClip,
        transform: "rotate(-27deg)",
        transformOrigin: "50% 100%",
      }),
    ),
  );
  kids.push(
    D(
      abs({
        left: px(headLeft + headW - S * 0.18),
        top: px(headTop - S * 0.46),
        width: px(S * 0.2),
        height: px(S * 0.62),
        background: "linear-gradient(180deg," + accent + "," + metal + " 42%," + metalDk + ")",
        clipPath: earClip,
        transform: "rotate(15deg)",
        transformOrigin: "50% 100%",
      }),
    ),
  );

  // feet (behind head bottom)
  kids.push(
    D(
      abs({
        left: px(cx - S * 0.22),
        top: px(headTop + headH - S * 0.03),
        width: px(S * 0.15),
        height: px(S * 0.11),
        borderRadius: px(S * 0.05),
        background: metalDk,
      }),
    ),
  );
  kids.push(
    D(
      abs({
        left: px(cx + S * 0.07),
        top: px(headTop + headH - S * 0.03),
        width: px(S * 0.15),
        height: px(S * 0.11),
        borderRadius: px(S * 0.05),
        background: metalDk,
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
        borderRadius: px(S * 0.27),
        background:
          "linear-gradient(158deg, rgba(255,255,255,.32), rgba(255,255,255,0) 46%), " + metal,
        boxShadow:
          "inset 0 " +
          px(S * 0.05) +
          " " +
          px(S * 0.05) +
          " rgba(255,255,255,.3), inset 0 " +
          px(-S * 0.05) +
          " " +
          px(S * 0.07) +
          " " +
          metalDk +
          ", 0 " +
          px(S * 0.12) +
          " " +
          px(S * 0.2) +
          " rgba(0,0,0,.3)",
      }),
    ),
  );

  // headphone disc (right)
  kids.push(
    D(
      abs({
        left: px(headLeft + headW - S * 0.11),
        top: px(headTop + headH * 0.3),
        width: px(S * 0.24),
        height: px(S * 0.24),
        borderRadius: "50%",
        background: "radial-gradient(circle at 38% 32%, " + metal + ", " + metalDk + ")",
        boxShadow: "0 " + px(S * 0.02) + " " + px(S * 0.04) + " rgba(0,0,0,.3)",
      }),
      [
        D({
          position: "absolute",
          left: "32%",
          top: "32%",
          width: "36%",
          height: "36%",
          borderRadius: "50%",
          background: metalDk,
        }),
      ],
    ),
  );

  // screen
  const scW = S * 0.82,
    scH = S * 0.6,
    scLeft = cx - scW / 2,
    scTop = headTop + S * 0.1;
  kids.push(
    D(
      abs({
        left: px(scLeft),
        top: px(scTop),
        width: px(scW),
        height: px(scH),
        borderRadius: px(S * 0.15),
        overflow: "hidden",
        opacity: dim ? 0.5 : 1,
        background: "radial-gradient(120% 130% at 50% 28%, " + oL + ", " + oM + " 55%, " + oD + ")",
        boxShadow:
          "inset 0 0 " +
          px(S * 0.06) +
          " rgba(255,170,70,.6), 0 0 " +
          px(S * 0.16) +
          " " +
          (dim ? "transparent" : oGlow) +
          ", inset 0 0 0 " +
          px(Math.max(1, S * 0.012)) +
          " rgba(120,50,10,.4)",
      }),
      [
        D(
          abs({
            left: px(-S * 0.05),
            top: px(-S * 0.1),
            width: px(scW * 0.5),
            height: px(scH + S * 0.2),
            background: "linear-gradient(105deg, rgba(255,255,255,.42), rgba(255,255,255,0) 60%)",
            transform: "skewX(-12deg)",
          }),
        ),
      ],
    ),
  );

  // ---- face features (on top of screen) ----
  const eyeCxL = cx - S * 0.15,
    eyeCxR = cx + S * 0.15,
    eyeCy = scTop + scH * 0.42;
  if (closed) {
    [eyeCxL, eyeCxR].forEach((c) =>
      kids.push(
        D(
          abs({
            left: px(c - S * 0.07),
            top: px(eyeCy - S * 0.014),
            width: px(S * 0.14),
            height: px(S * 0.028),
            background: face,
            borderRadius: px(S * 0.02),
          }),
        ),
      ),
    );
  } else if (mood === "concerned") {
    [eyeCxL, eyeCxR].forEach((c) =>
      kids.push(
        D(
          abs({
            left: px(c - S * 0.06),
            top: px(eyeCy - S * 0.1),
            width: px(S * 0.12),
            height: px(S * 0.2),
            borderRadius: "50%",
            background: face,
          }),
        ),
      ),
    );
  } else {
    const dy = mood === "thinking" ? -S * 0.03 : 0;
    [eyeCxL, eyeCxR].forEach((c) =>
      kids.push(
        D(
          abs({
            left: px(c - S * 0.035),
            top: px(eyeCy - S * 0.13 + dy),
            width: px(S * 0.07),
            height: px(S * 0.26),
            background: face,
            borderRadius: px(S * 0.035),
          }),
        ),
      ),
    );
  }
  const mCy = scTop + scH * 0.78;
  if (mood === "happy") {
    kids.push(
      D(
        abs({
          left: px(cx - S * 0.15),
          top: px(mCy - S * 0.05),
          width: px(S * 0.3),
          height: px(S * 0.15),
          borderBottom: px(S * 0.04) + " solid " + face,
          borderRadius: "0 0 " + px(S * 0.22) + " " + px(S * 0.22),
        }),
      ),
    );
    kids.push(
      D(
        abs({
          left: px(cx + S * 0.02),
          top: px(mCy + S * 0.05),
          width: px(S * 0.08),
          height: px(S * 0.07),
          background: tongue,
          borderRadius: px(S * 0.03),
        }),
      ),
    );
  } else if (mood === "concerned") {
    kids.push(
      D(
        abs({
          left: px(cx - S * 0.05),
          top: px(mCy - S * 0.01),
          width: px(S * 0.1),
          height: px(S * 0.09),
          border: px(S * 0.025) + " solid " + face,
          borderRadius: "50%",
        }),
      ),
    );
  } else if (!closed) {
    kids.push(
      D(
        abs({
          left: px(cx - S * 0.13),
          top: px(mCy - S * 0.03),
          width: px(S * 0.24),
          height: px(S * 0.1),
          borderBottom: px(S * 0.035) + " solid " + face,
          borderRadius: "0 0 " + px(S * 0.18) + " " + px(S * 0.05),
          transform: "rotate(-4deg)",
        }),
      ),
    );
    kids.push(
      D(
        abs({
          left: px(cx + S * 0.08),
          top: px(mCy + S * 0.03),
          width: px(S * 0.06),
          height: px(S * 0.06),
          background: tongue,
          borderRadius: px(S * 0.02),
        }),
      ),
    );
  } else {
    kids.push(
      D(
        abs({
          left: px(cx - S * 0.06),
          top: px(mCy),
          width: px(S * 0.12),
          height: px(S * 0.022),
          background: face,
          borderRadius: px(S * 0.02),
        }),
      ),
    );
  }
  if (mood === "working")
    kids.push(
      D(
        abs({
          left: px(scLeft + S * 0.05),
          top: px(scTop + scH * 0.52),
          width: px(scW - S * 0.1),
          height: px(S * 0.022),
          background: "rgba(70,34,15,.45)",
        }),
      ),
    );

  // badge
  const badges = {
    thinking: ["?", oGlow],
    concerned: ["!", "#E8B45F"],
    sleeping: ["z", accent],
    working: ["\u25cc", oGlow],
  };
  const b = badges[mood];
  if (b) {
    const isSpin = mood === "working";
    kids.push(
      D(
        abs({
          top: px(headTop - S * 0.16),
          right: px(S * 0.04),
          fontFamily: "'JetBrains Mono',monospace",
          fontWeight: 700,
          fontSize: px(S * 0.24),
          color: b[1],
          textShadow: "0 0 " + px(S * 0.08) + " " + b[1],
          animation: isSpin ? "rb-spin .9s linear infinite" : "rb-pulse 1.8s ease-in-out infinite",
        }),
        b[0],
      ),
    );
  }

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

// ---- Terminal version: Volt as Unicode block art + truecolor ----
function voltTermGrid(mood, blink) {
  const base = [
    "....DD........DD....",
    "....BB........BB....",
    "...BBBB......BBBB...",
    "..BBBBBBBBBBBBBBBB..",
    ".BBBBBBBBBBBBBBBBBB.",
    ".BOOOOOOOOOOOOOOOOB.",
    ".BOOOOEEOOOOEEOOOOB.",
    ".BOOOOEEOOOOEEOOOOB.",
    ".BOOOOEEOOOOEEOOOOB.",
    ".BOOOOOOOOOOOOOOOOB.",
    ".BOOOOOMMMMMMOOOOOB.",
    ".BOOOOOOOOOOOOOOOOB.",
    ".BBOOOOOOOOOOOOOOBB.",
    "..BBBBBBBBBBBBBBBB..",
    "...BBBBBBBBBBBBBB...",
    ".....DD......DD.....",
  ].map((s) => s.split(""));
  const set = (r, c, ch) => {
    if (base[r] && base[r][c] !== undefined) base[r][c] = ch;
  };
  const eyeCols = [6, 7, 12, 13];
  const closed = blink || mood === "sleeping";
  if (closed) {
    eyeCols.forEach((c) => {
      set(6, c, "O");
      set(8, c, "O");
    });
  } else if (mood === "thinking") {
    eyeCols.forEach((c) => {
      set(8, c, "O");
      set(5, c, "E");
    });
  } else if (mood === "concerned") {
    [8, 11].forEach((c) => set(10, c, "M"));
    [7, 9, 10, 12].forEach((c) => set(10, c, "O"));
  } else if (mood === "happy") {
    [6, 7, 8, 9, 10, 11, 12, 13].forEach((c) => set(10, c, "M"));
    set(11, 9, "M");
    set(11, 10, "M");
  } else if (mood === "working") {
    for (let c = 2; c <= 17; c++) if (base[9][c] === "O") set(9, c, "M");
  }
  return base;
}

export function voltTerminalElement(React, mood, cell, palette, blink) {
  const h = React.createElement;
  cell = Number(cell) || 11;
  palette = palette || {};
  const metal = palette.body || "#92B7B0",
    metalDk = palette.dark || "#5E7E78";
  const dim = mood === "sleeping";
  const O = dim ? "#B5662E" : "#FF9A3C",
    glow = "#FF8A3D",
    face = "#3A1E0E";
  const COL = { B: metal, D: metalDk, O: O, E: face, M: face };
  const grid = voltTermGrid(mood, blink);
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
        const isO = ch === "O";
        spans.push(
          h(
            "span",
            {
              key: i,
              style: {
                color: COL[ch],
                textShadow: isO && !dim ? "0 0 " + cell * 0.45 + "px " + glow : "none",
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
    sleeping: ["z", "#9FE8DE"],
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
