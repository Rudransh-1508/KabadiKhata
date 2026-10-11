// Scroll story. The stage is pinned (position: sticky) inside a tall section; scroll progress p in [0, 1]
// drives every scene: scrap flies in, a newspaper bundle comes untied, two clippings, her photo and the zoom into her eye.
(function () {
  const story = document.querySelector(".story");
  if (!story) return;
  const $ = (id) => document.getElementById(id);
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const ease = (t) => 1 - Math.pow(1 - t, 3);
  const io = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
  const span = (p, a, b) => clamp((p - a) / (b - a));
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // scene windows on overall progress
  const SC = { scrap: [0, 0.17], bundle: [0.17, 0.33], clip1: [0.33, 0.48], clip2: [0.48, 0.58], her: [0.58, 0.9], cta: [0.9, 1.01] };
  const LAYERS = { scrap: $("sc-scrap"), bundle: $("sc-bundle"), clip1: $("sc-clip1"), clip2: $("sc-clip2"), her: $("sc-her"), cta: $("sc-cta") };
  const dots = [...story.querySelectorAll(".story-dots li")];

  // ---------- 1. scrap objects, drawn in code ----------
  let rs = 7;
  const rnd = () => ((rs = (rs * 1664525 + 1013904223) >>> 0) / 4294967296);
  const pick = (a) => a[Math.floor(rnd() * a.length)];
  function canvasFor(w, h, draw) {
    const c = document.createElement("canvas"), d = 2;
    c.width = w * d; c.height = h * d; c.style.width = w + "px"; c.style.height = h + "px";
    const g = c.getContext("2d"); g.scale(d, d); draw(g, w, h); return c;
  }
  const ART = {
    bottle(g, w, h) {
      const col = pick([[120, 186, 214], [52, 128, 190], [70, 160, 110], [200, 225, 232], [92, 196, 208]]);
      const grad = g.createLinearGradient(0, 0, w, 0);
      grad.addColorStop(0, `rgba(${col.map((v) => v * 0.55 | 0)},.95)`); grad.addColorStop(0.35, `rgba(${col},.95)`);
      grad.addColorStop(0.55, `rgba(${col.map((v) => Math.min(255, v + 50))},.95)`); grad.addColorStop(1, `rgba(${col.map((v) => v * 0.6 | 0)},.95)`);
      const bw = w * 0.62, x0 = (w - bw) / 2, neck = w * 0.26;
      g.beginPath();
      g.moveTo(x0, h * 0.32); g.quadraticCurveTo(x0, h * 0.2, w / 2 - neck / 2, h * 0.14); g.lineTo(w / 2 - neck / 2, h * 0.07);
      g.lineTo(w / 2 + neck / 2, h * 0.07); g.lineTo(w / 2 + neck / 2, h * 0.14); g.quadraticCurveTo(x0 + bw, h * 0.2, x0 + bw, h * 0.32);
      g.lineTo(x0 + bw, h * 0.94); g.quadraticCurveTo(w / 2, h * 1.0, x0, h * 0.94); g.closePath();
      g.fillStyle = grad; g.fill();
      g.fillStyle = pick(["#d63a30", "#1e5aaa", "#f5f5f0", "#2a9650"]); g.fillRect(x0, h * 0.45, bw, h * 0.16);       // label
      g.fillStyle = "rgba(255,255,255,.35)"; g.fillRect(x0 + bw * 0.14, h * 0.22, bw * 0.1, h * 0.66);               // shine
      g.fillStyle = pick(["#2a6ec8", "#e9eef0", "#d64034", "#3ca050"]); g.fillRect(w / 2 - neck * 0.6, 0, neck * 1.2, h * 0.08); // cap
    },
    bundle(g, w, h) {
      for (let k = 4; k >= 0; k--) {
        const t = 190 + k * 9;
        g.fillStyle = `rgb(${t},${t - 5},${t - 18})`; g.fillRect(k * 2, h * 0.1 + k * (h * 0.15), w - k * 3, h * 0.22);
        g.fillStyle = "rgba(0,0,0,.18)"; g.fillRect(k * 2, h * 0.1 + k * (h * 0.15) + h * 0.2, w - k * 3, 2);
        g.fillStyle = "rgba(40,40,40,.35)";
        for (let j = 0; j < 4; j++) g.fillRect(k * 2 + 8, h * 0.13 + k * (h * 0.15) + j * 5, (w - 30) * (0.4 + rnd() * 0.5), 2);
      }
      g.strokeStyle = "#a06a32"; g.lineWidth = 4;
      g.beginPath(); g.moveTo(w * 0.4, h * 0.05); g.lineTo(w * 0.42, h * 0.98); g.stroke();
      g.beginPath(); g.moveTo(0, h * 0.5); g.lineTo(w, h * 0.52); g.stroke();
    },
    can(g, w, h) {
      const col = pick(["#c8282a", "#c0c8cc", "#2a8c50", "#1e3c8c", "#e6b41e"]);
      const grad = g.createLinearGradient(0, 0, w, 0);
      grad.addColorStop(0, "rgba(0,0,0,.35)"); grad.addColorStop(0.4, "rgba(255,255,255,.25)"); grad.addColorStop(1, "rgba(0,0,0,.4)");
      g.fillStyle = col; g.beginPath(); g.roundRect ? g.roundRect(0, h * 0.06, w, h * 0.88, 8) : g.rect(0, h * 0.06, w, h * 0.88); g.fill();
      g.fillStyle = grad; g.fillRect(0, h * 0.06, w, h * 0.88);
      g.fillStyle = "#d4d8da"; g.beginPath(); g.ellipse(w / 2, h * 0.07, w / 2, h * 0.07, 0, 0, Math.PI * 2); g.fill();
      g.strokeStyle = "rgba(0,0,0,.3)"; g.lineWidth = 2; g.beginPath(); g.ellipse(w / 2, h * 0.07, w * 0.3, h * 0.04, 0, 0, Math.PI * 2); g.stroke();
    },
    cardboard(g, w, h) {
      g.fillStyle = pick(["#b88a55", "#a87c48", "#c49862"]);
      g.beginPath(); g.moveTo(0, h * 0.1); g.lineTo(w * 0.95, 0); g.lineTo(w, h * 0.85); g.lineTo(w * 0.08, h); g.closePath(); g.fill();
      g.fillStyle = "rgba(255,230,180,.35)"; g.fillRect(w * 0.05, h * 0.42, w * 0.9, h * 0.13);
      g.strokeStyle = "rgba(70,40,15,.5)"; g.lineWidth = 2; g.stroke();
      g.fillStyle = "rgba(60,35,15,.55)"; g.font = `700 ${h * 0.14}px sans-serif`; g.fillText("FRAGILE", w * 0.2, h * 0.32);
    },
    plate(g, w) {
      const r = w / 2, grad = g.createRadialGradient(r * 0.7, r * 0.6, r * 0.1, r, r, r);
      grad.addColorStop(0, "#f2f5f6"); grad.addColorStop(0.55, "#b4bcc0"); grad.addColorStop(1, "#6c767a");
      g.fillStyle = grad; g.beginPath(); g.arc(r, r, r - 1, 0, Math.PI * 2); g.fill();
      g.strokeStyle = "rgba(255,255,255,.7)"; g.lineWidth = 3; g.beginPath(); g.arc(r, r, r * 0.72, 0, Math.PI * 2); g.stroke();
    },
    pipe(g, w, h) {
      const grad = g.createLinearGradient(0, 0, 0, h);
      grad.addColorStop(0, "#e8a070"); grad.addColorStop(0.45, "#b8642e"); grad.addColorStop(1, "#6e3a18");
      g.fillStyle = grad; g.fillRect(0, h * 0.25, w, h * 0.5);
      g.fillStyle = "#8a4a20"; g.fillRect(w * 0.82, h * 0.12, w * 0.18, h * 0.76);
    },
  };
  const KINDS = [["bottle", 70, 170], ["bottle", 60, 150], ["bundle", 200, 120], ["can", 64, 104], ["cardboard", 180, 130],
                 ["plate", 120, 120], ["pipe", 190, 48], ["bottle", 56, 140], ["bundle", 170, 104], ["can", 56, 92]];
  const field = $("field"), items = [];
  function buildScrap() {
    field.replaceChildren(); items.length = 0; rs = 7;
    const W = innerWidth, H = innerHeight;
    for (let i = 0; i < 22; i++) {
      const [kind, w, h] = KINDS[i % KINDS.length];
      const c = canvasFor(w, h, ART[kind]);
      field.appendChild(c);
      // homes sit in the right two thirds, in a loose cloud; starts are far outside the screen
      const hx = W * (0.42 + rnd() * 0.56), hy = H * (0.08 + rnd() * 0.84);
      const ang = rnd() * Math.PI * 2, far = Math.max(W, H) * (0.9 + rnd() * 0.5);
      items.push({ c, w, h, hx, hy, sx: W * 0.7 + Math.cos(ang) * far, sy: H * 0.5 + Math.sin(ang) * far,
                   r0: (rnd() - 0.5) * 6, r1: (rnd() - 0.5) * 0.9, s: 0.75 + rnd() * 0.6, delay: rnd() * 0.25 });
    }
  }

  function scrap(t) {
    const W = innerWidth, H = innerHeight, cx = W * 0.7, cy = H * 0.5;
    const through = io(span(t, 0.72, 1));           // the camera flies through the cloud at the end
    for (const it of items) {
      const k = ease(span(t, it.delay * 0.5, 0.55 + it.delay * 0.5));
      let x = it.sx + (it.hx - it.sx) * k, y = it.sy + (it.hy - it.sy) * k;
      x = cx + (x - cx) * (1 + through * 2.2); y = cy + (y - cy) * (1 + through * 2.2);
      const sc = it.s * (0.55 + 0.45 * k + 0.25 * span(t, 0.4, 0.72)) * (1 + through * 3.5);
      const rot = it.r0 + (it.r1 - it.r0) * k + t * 0.6;
      it.c.style.transform = `translate(${x - it.w / 2}px, ${y - it.h / 2}px) rotate(${rot}rad) scale(${sc})`;
      it.c.style.opacity = 1 - through;
    }
    const copy = story.querySelector(".scrap-copy");
    copy.style.opacity = span(t, 0.15, 0.3) * (1 - span(t, 0.75, 0.9));
    copy.style.transform = `translateY(calc(-50% + ${(1 - span(t, 0.15, 0.3)) * 24}px))`;
  }

  // ---------- 2. bundle of raddi (photo); if img/raddi-untied.jpg exists the rope comes off ----------
  const HEADLINE = { x: 0.395, y: 0.29 };
  function bundle(t) {
    const wrap = $("raddi"), W = wrap.offsetWidth, H = wrap.offsetHeight;
    const settle = ease(span(t, 0, 0.2)), z = io(span(t, 0.45, 1));
    const sc = (1.12 - 0.12 * settle) * (1 + z * 1.6);
    const fx = 0.5 + (HEADLINE.x - 0.5) * z, fy = 0.5 + (HEADLINE.y - 0.5) * z;
    wrap.style.transform = `translate(${-sc * W * fx}px, ${-sc * H * fy}px) scale(${sc})`;
    const untied = $("untied");
    if (untied) untied.style.opacity = io(span(t, 0.22, 0.42));
  }

  // ---------- 3-4. clippings ----------
  // the camera drifts over the paper: a slow push-in with a slight tilt
  const cam = (t, tilt) => `rotateX(${7 - 3 * t}deg) rotateZ(${tilt}deg) scale(${1.0 + 0.07 * t}) translate(${-1.5 * t}vw, ${-1 * t}vh)`;
  function clip1(t) {
    const art = LAYERS.clip1.querySelector(".clipping");
    art.style.transform = cam(t, -1.6);
    $("hl1").style.setProperty("--hl", `${io(span(t, 0.12, 0.45)) * 100}%`);
    const z = io(span(t, 0.5, 0.85));
    art.style.filter = `blur(${z * 4}px) brightness(${1 - z * 0.45})`;
    $("big1").style.opacity = z;
    $("big1").style.transform = `translate(-50%, -50%) scale(${0.3 + 0.7 * z})`;
    $("big1").textContent = Math.round(600000 * z).toLocaleString("en-IN");
  }
  function clip2(t) {
    const art = LAYERS.clip2.querySelector(".clipping");
    const k = ease(span(t, 0, 0.3));
    art.style.transform = `translateX(${(1 - k) * 70}vw) ${cam(t, 1.4 - (1 - k) * 6)}`;
    $("hl2").style.setProperty("--hl", `${io(span(t, 0.3, 0.7)) * 100}%`);
  }

  // ---------- 5. her: zoom into the full photo, crossfade into the close-up lined up on her face, then into the teary eye ----------
  const FULL = { mid: { x: 0.507, y: 0.716 }, eyes: 0.134 };          // eye midpoint and eye distance, as fractions of the full photo
  const CLOSE = { mid: { x: 0.559, y: 0.495 }, eyes: 0.314, eye: { x: 0.405, y: 0.5 } };
  function place(el, s, fx, fy, dx = 0, dy = 0) {
    el.style.transform = `translate(${dx - s * el.offsetWidth * fx}px, ${dy - s * el.offsetHeight * fy}px) scale(${s})`;
  }
  function her(t) {
    const p1 = $("photo"), p2 = $("photo2");
    const appear = ease(span(t, 0, 0.08));
    const zA = io(span(t, 0.18, 0.5));                                   // full photo -> her face
    const sA = 1 + zA * 4.2;
    const shift = (1 - zA) * Math.min(innerWidth * 0.17, 260) * (innerWidth > 760 ? 1 : 0);
    place(p1, sA, 0.5 + (FULL.mid.x - 0.5) * zA, 0.5 + (FULL.mid.y - 0.5) * zA, shift, (1 - appear) * 40);
    // close-up scaled so its eyes sit exactly where the full photo's eyes are on screen
    const match = (sA * FULL.eyes * p1.offsetWidth) / (CLOSE.eyes * p2.offsetWidth);
    const zB = io(span(t, 0.52, 0.82));                                  // close-up -> the teary eye
    const sB = match * (1 + zB * 3.6);
    place(p2, sB, CLOSE.mid.x + (CLOSE.eye.x - CLOSE.mid.x) * zB, CLOSE.mid.y + (CLOSE.eye.y - CLOSE.mid.y) * zB);
    const x = span(t, 0.42, 0.52);
    p1.style.opacity = appear * (1 - x);
    p2.style.opacity = x;
    $("her1").style.opacity = span(t, 0.05, 0.12) * (1 - span(t, 0.2, 0.28));
    $("her2").style.opacity = span(t, 0.82, 0.9);
  }

  function cta(t) {
    const c = LAYERS.cta.querySelector(".cta-copy");
    c.style.opacity = ease(span(t, 0, 0.3));
    c.style.transform = `translateY(${(1 - ease(span(t, 0, 0.3))) * 30}px)`;
  }
  const RUN = { scrap, bundle, clip1, clip2, her, cta };

  function render(p) {
    Object.entries(SC).forEach(([k, [a, b]], i) => {
      const L = LAYERS[k], last = k === "cta";
      const fadeIn = clamp((p - a) / 0.012 + 1), fadeOut = last ? 1 : clamp((b - p) / 0.012 + 1);
      const on = p >= a - 0.012 && (last || p <= b + 0.012);
      L.style.visibility = on ? "visible" : "hidden";
      L.style.opacity = on ? Math.min(fadeIn, fadeOut) : 0;
      if (on) RUN[k](span(p, a, b));
      if (dots[i]) dots[i].classList.toggle("on", p >= a && p < b);
    });
  }

  buildScrap();
  if (reduce) {
    story.classList.add("static");
    Object.entries(RUN).forEach(([k, f]) => { LAYERS[k].style.opacity = 1; LAYERS[k].style.visibility = "visible"; f(k === "her" ? 0.2 : 0.99); });
    return;
  }
  let ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      const r = story.getBoundingClientRect();
      render(clamp(-r.top / Math.max(1, story.offsetHeight - innerHeight)));
      ticking = false;
    });
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", () => { buildScrap(); onScroll(); });
  onScroll();
})();
