// Bottle-pile mosaic for the landing hero.
// A pile of crushed plastic bottles is drawn procedurally (no photo, nothing to license), sampled into blocks,
// and the blocks near the cursor push away and swirl. Some blocks near the cursor turn into receipt tags:
// the picture is made of verified receipts. All tag values are synthetic.
(function () {
  const canvas = document.getElementById("mosaic");
  const tagLayer = document.getElementById("tags");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // seeded RNG so the pile looks the same on every load (and in the video)
  let seed = 20261011;
  const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
  const pick = (a) => a[Math.floor(rnd() * a.length)];

  const BODY = [ // PET clear/blue/green, HDPE white, a few amber
    [176, 214, 224], [120, 186, 214], [52, 128, 190], [38, 98, 160], [70, 160, 110], [44, 120, 84],
    [210, 228, 232], [232, 236, 234], [92, 196, 208], [196, 150, 82],
  ];
  const CAP = [[40, 110, 200], [230, 236, 240], [214, 64, 52], [60, 160, 80], [240, 170, 40]];

  // One bottle, drawn along +x: cap, neck, shoulder, ribbed body, label band. Units are offscreen px.
  function bottle(g, len, wid, body, cap, ink) {
    const [r, gg, b] = body;
    const neck = wid * 0.38, capW = wid * 0.46, capL = len * 0.08, neckL = len * 0.1, shoulder = len * 0.14;
    const x0 = -len / 2, xBody = x0 + len - capL - neckL - shoulder;
    g.beginPath();
    g.moveTo(x0 + wid * 0.25, -wid / 2);
    g.lineTo(xBody, -wid / 2);
    g.quadraticCurveTo(xBody + shoulder * 0.8, -wid / 2, xBody + shoulder, -neck / 2);
    g.lineTo(xBody + shoulder + neckL, -neck / 2);
    g.lineTo(xBody + shoulder + neckL, neck / 2);
    g.lineTo(xBody + shoulder, neck / 2);
    g.quadraticCurveTo(xBody + shoulder * 0.8, wid / 2, xBody, wid / 2);
    g.lineTo(x0 + wid * 0.25, wid / 2);
    g.quadraticCurveTo(x0, wid / 2, x0, wid * 0.25);
    g.lineTo(x0, -wid * 0.25);
    g.quadraticCurveTo(x0, -wid / 2, x0 + wid * 0.25, -wid / 2);
    g.closePath();
    g.fillStyle = ink || `rgb(${r}, ${gg}, ${b})`;
    g.fill();
    if (ink) { g.fillRect(xBody + shoulder + neckL - 1, -capW / 2, capL, capW); return; }
    g.lineWidth = 2.5;
    g.strokeStyle = `rgb(${r * 0.45 | 0}, ${gg * 0.45 | 0}, ${b * 0.45 | 0})`;
    g.stroke();
    // ribs
    g.strokeStyle = `rgba(0,0,0,.18)`; g.lineWidth = 1.5;
    for (let k = 1; k < 4; k++) { const x = x0 + (xBody - x0) * k / 4; g.beginPath(); g.moveTo(x, -wid / 2 + 2); g.lineTo(x, wid / 2 - 2); g.stroke(); }
    // highlight
    g.fillStyle = "rgba(255,255,255,.35)";
    g.fillRect(x0 + wid * 0.3, -wid * 0.3, (xBody - x0) * 0.75, wid * 0.12);
    // label
    g.fillStyle = pick(["rgb(214,58,48)", "rgb(30,90,170)", "rgb(245,245,240)", "rgb(40,150,80)", "rgb(240,170,40)"]);
    g.fillRect(x0 + (xBody - x0) * 0.35, -wid / 2 + 1, (xBody - x0) * 0.3, wid - 2);
    // cap
    const [cr, cg, cb] = cap;
    g.fillStyle = `rgb(${cr}, ${cg}, ${cb})`;
    g.fillRect(xBody + shoulder + neckL - 1, -capW / 2, capL, capW);
  }

  // A bundle of old newspapers (raddi): a few offset sheets, the top one printed, tied with string.
  function bundle(g, s, ink) {
    const w = s * 1.0, h = s * 0.68;
    if (ink) { g.fillStyle = ink; g.fillRect(-w / 2 - 4, -h / 2 - 4, w + 8, h + 8); return; }
    for (let k = 3; k >= 0; k--) {                                   // stacked sheets, slightly offset
      const tone = 196 + k * 7 + (rnd() * 10 | 0);
      g.fillStyle = `rgb(${tone}, ${tone - 4}, ${tone - 16})`;
      g.save(); g.rotate((rnd() - 0.5) * 0.08); g.fillRect(-w / 2 + k * 2, -h / 2 + k * 2, w, h); g.restore();
      g.fillStyle = "rgba(0,0,0,.25)"; g.fillRect(-w / 2 + k * 2, h / 2 + k * 2 - 1.5, w, 1.5);
    }
    g.fillStyle = "rgb(36,36,36)"; g.fillRect(-w / 2 + 6, -h / 2 + 5, w * 0.62, h * 0.12);   // masthead
    g.fillStyle = "rgb(128,126,118)"; g.fillRect(-w / 2 + 6, -h / 2 + h * 0.26, w * 0.34, h * 0.28); // photo
    g.fillStyle = "rgba(60,60,60,.55)";
    for (let k = 0; k < 7; k++) {
      const y = -h / 2 + h * 0.26 + k * h * 0.09;
      g.fillRect(-w / 2 + w * 0.44, y, w * 0.24, 2.5);
      g.fillRect(-w / 2 + w * 0.72, y, w * 0.22, 2.5);
    }
    g.strokeStyle = "rgb(176,128,70)"; g.lineWidth = 3.5;               // string, tied both ways
    g.beginPath(); g.moveTo(-w * 0.08, -h / 2 - 2); g.lineTo(-w * 0.08, h / 2 + 8); g.stroke();
    g.beginPath(); g.moveTo(-w / 2 - 2, h * 0.06); g.lineTo(w / 2 + 8, h * 0.06); g.stroke();
    g.fillStyle = "rgb(150,104,52)"; g.beginPath(); g.arc(-w * 0.08, h * 0.06, 4, 0, Math.PI * 2); g.fill(); // knot
  }

  const TYPES = [
    { draw: bundle, label: "newspaper bundle (raddi)", kg: [5, 25] },
    { draw: null, label: "plastic bottles", kg: [2, 15] },            // bottle(), drawn last so it sits on top
  ];

  function drawPile(w, h) {
    const mk = () => { const c = document.createElement("canvas"); c.width = w; c.height = h; return c.getContext("2d"); };
    const g = mk(), ix = mk();
    g.fillStyle = "rgb(12, 17, 25)"; g.fillRect(0, 0, w, h);
    ix.fillStyle = "rgb(0,0,0)"; ix.fillRect(0, 0, w, h);
    const len0 = Math.max(70, Math.min(w, h) * 0.22);
    const n = Math.round((w * h) / (len0 * len0 * 0.42));
    const items = [];
    for (let i = 0; i < n; i++) {
      items.push({ t: rnd() < 0.32 ? 0 : 1, x: rnd() * w, y: rnd() * h, a: rnd() * Math.PI * 2, k: 0.8 + rnd() * 0.45, seed: (rnd() * 1e9) | 0 });
    }
    items.sort((p, q) => p.t - q.t);            // flat scrap underneath, bottles on top
    for (const it of items) {
      for (const [ctx2, ink] of [[g, null], [ix, `rgb(${(it.t + 1) * 30},0,0)`]]) {
        const save = seed; seed = it.seed;         // same random details in both passes
        ctx2.save(); ctx2.translate(it.x, it.y); ctx2.rotate(it.a);
        const s = len0 * it.k;
        if (TYPES[it.t].draw) TYPES[it.t].draw(ctx2, s, ink);
        else if (ink) { const sv = ctx2.fillStyle; bottle(ctx2, s, s * 0.32, [0, 0, 0], [0, 0, 0], ink); ctx2.fillStyle = sv; }
        else { const shade = 0.8 + rnd() * 0.3; bottle(ctx2, s, s * (0.3 + rnd() * 0.06), pick(BODY).map((v) => Math.min(255, v * shade | 0)), pick(CAP)); }
        ctx2.restore();
        seed = save;
      }
    }
    return { img: g.getImageData(0, 0, w, h), idx: ix.getImageData(0, 0, w, h) };
  }

  const PEOPLE = [["Raju", "Seelampur"], ["Sunita", "Okhla"], ["Imran", "Shahdara"], ["Kamla", "Govindpuri"], ["Ramesh", "Karol Bagh"], ["Shabnam", "Mustafabad"], ["Mohan", "Narela"], ["Rekha", "Lajpat Nagar"]];

  let cells = [], cell = 14, cols = 0, rows = 0, W = 0, H = 0, dpr = 1;
  let mouse = { x: -9999, y: -9999, on: false };

  // a receipt for ~2% of blocks, naming the scrap actually under that block
  function receiptFor(idx, i, j) {
    if (rnd() >= 0.02) return null;
    const p = ((j * 4 + 2) * idx.width + (i * 4 + 2)) * 4;
    const t = Math.round(idx.data[p] / 30) - 1;
    if (t < 0 || t >= TYPES.length) return null;               // empty ground: no receipt
    const [lo, hi] = TYPES[t].kg;
    return { who: pick(PEOPLE), kg: (lo + rnd() * (hi - lo)).toFixed(1).replace(/\.0$/, ""), m: TYPES[t].label };
  }

  function build() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = canvas.clientWidth; H = canvas.clientHeight;
    canvas.width = W * dpr; canvas.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    cell = W < 640 ? 8 : 10;
    cols = Math.ceil(W / cell); rows = Math.ceil(H / cell);
    seed = 20261011;
    const { img, idx } = drawPile(cols * 4, rows * 4);
    cells = [];
    for (let j = 0; j < rows; j++) {
      for (let i = 0; i < cols; i++) {
        let r = 0, g = 0, b = 0;
        for (let dy = 0; dy < 4; dy++) for (let dx = 0; dx < 4; dx++) {
          const p = ((j * 4 + dy) * img.width + (i * 4 + dx)) * 4;
          r += img.data[p]; g += img.data[p + 1]; b += img.data[p + 2];
        }
        cells.push({
          x: i * cell, y: j * cell, ox: 0, oy: 0, rot: 0,
          c: [r / 16 | 0, g / 16 | 0, b / 16 | 0],
          receipt: receiptFor(idx, i, j),
          tagEl: null,
        });
      }
    }
    tagLayer.replaceChildren();
  }

  const R = 170; // influence radius in px
  function frame() {
    ctx.clearRect(0, 0, W, H);
    const shown = [];
    for (const c of cells) {
      let tx = 0, ty = 0, trot = 0;
      if (mouse.on && !reduce) {
        const cx = c.x + cell / 2 - mouse.x, cy = c.y + cell / 2 - mouse.y;
        const d = Math.hypot(cx, cy);
        if (d < R) {
          const f = (1 - d / R) ** 2;
          const ang = Math.atan2(cy, cx) + f * 0.9;      // push out and swirl
          tx = Math.cos(ang) * f * 46 - cx * f * 0.15;
          ty = Math.sin(ang) * f * 46 - cy * f * 0.15;
          trot = f * 1.2;
          if (c.receipt && d < R * 0.8) shown.push([d, c]);
        }
      }
      c.ox += (tx - c.ox) * 0.16; c.oy += (ty - c.oy) * 0.16; c.rot += (trot - c.rot) * 0.16;
      const [r, g, b] = c.c;
      const lift = Math.min(1, Math.hypot(c.ox, c.oy) / 40);
      ctx.fillStyle = `rgb(${Math.min(255, r + lift * 40) | 0}, ${Math.min(255, g + lift * 40) | 0}, ${Math.min(255, b + lift * 40) | 0})`;
      const s = cell - 1.5;
      if (Math.abs(c.rot) > 0.01) {
        ctx.save();
        ctx.translate(c.x + c.ox + cell / 2, c.y + c.oy + cell / 2);
        ctx.rotate(c.rot);
        ctx.fillRect(-s / 2, -s / 2, s, s);
        ctx.restore();
      } else {
        ctx.fillRect(c.x + c.ox, c.y + c.oy, s, s);
      }
    }
    // up to 3 nearest receipt blocks, spaced so their tags never overlap
    shown.sort((a, b) => a[0] - b[0]);
    const keep = new Set();
    for (const [, c] of shown) {
      if (keep.size >= 3) break;
      const far = [...keep].every((k) => Math.abs(k.x + k.ox - c.x - c.ox) > 170 || Math.abs(k.y + k.oy - c.y - c.oy) > 64);
      if (far) keep.add(c);
    }
    for (const c of cells) {
      if (!c.receipt) continue;
      if (keep.has(c)) {
        if (!c.tagEl) {
          c.tagEl = document.createElement("div");
          c.tagEl.className = "tag";
          c.tagEl.innerHTML = `${c.receipt.kg} kg ${c.receipt.m} <span class="ok">✓</span><br><span class="id">${c.receipt.who[0]} · ${c.receipt.who[1]}</span>`;
          tagLayer.appendChild(c.tagEl);
          requestAnimationFrame(() => c.tagEl && c.tagEl.classList.add("on"));
        }
        c.tagEl.style.left = `${c.x + c.ox + cell / 2}px`;
        c.tagEl.style.top = `${c.y + c.oy}px`;
        ctx.strokeStyle = "#f4f1e6"; ctx.lineWidth = 1.5;
        ctx.strokeRect(c.x + c.ox - 1, c.y + c.oy - 1, cell + 0.5, cell + 0.5);
      } else if (c.tagEl) {
        const el = c.tagEl; c.tagEl = null;
        el.classList.remove("on");
        setTimeout(() => el.remove(), 200);
      }
    }
    requestAnimationFrame(frame);
  }

  const hero = canvas.parentElement;
  hero.addEventListener("pointermove", (e) => {
    const r = canvas.getBoundingClientRect();
    mouse = { x: e.clientX - r.left, y: e.clientY - r.top, on: true };
  });
  hero.addEventListener("pointerleave", () => { mouse.on = false; });
  let t;
  window.addEventListener("resize", () => { clearTimeout(t); t = setTimeout(build, 150); });
  build();
  requestAnimationFrame(frame);
})();
