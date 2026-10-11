// Scroll story: the stage is pinned (position: sticky) inside a tall section; scroll progress drives each scene.
(function () {
  const story = document.querySelector(".story");
  if (!story) return;
  const scenes = [...story.querySelectorAll(".scene")];
  const dots = [...story.querySelectorAll(".story-dots li")];
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (id) => document.getElementById(id);
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const ease = (t) => 1 - Math.pow(1 - t, 3);

  // receipt blocks for the chain scene (synthetic)
  const track = $("track");
  const N = 18, BROKEN = 11;
  for (let i = 0; i < N; i++) {
    const b = document.createElement("div");
    b.className = "rblock";
    const kg = [7.4, 12, 9.5, 21, 5.2, 14, 8.8, 11.6, 6, 18.4, 10, 12.5, 7, 16, 9, 13.2, 6.6, 20][i];
    b.innerHTML = `<span class="seq">#${i}</span><b>${kg} kg</b><span class="h">${(0x9f3a + i * 7919).toString(16).slice(-4)}…</span>`;
    track.appendChild(b);
  }
  const blocks = [...track.children];

  // scene windows on overall progress [start, end]
  const W = [[0, 0.2], [0.2, 0.44], [0.44, 0.68], [0.68, 0.88], [0.88, 1.01]];

  function render(p) {
    scenes.forEach((s, i) => {
      const [a, b] = W[i];
      const t = clamp((p - a) / (b - a));
      const fadeIn = clamp(t / 0.12), fadeOut = i === scenes.length - 1 ? 1 : clamp((1 - t) / 0.12);
      const on = p >= a && p < b;
      s.style.opacity = on ? Math.min(fadeIn, fadeOut) : 0;
      s.style.transform = `translateY(${(1 - fadeIn) * 30 - (1 - fadeOut) * 30}px)`;
      s.style.visibility = on ? "visible" : "hidden";
      if (on) update(i, t);
    });
    dots.forEach((d, i) => d.classList.toggle("on", p >= W[i][0] && p < W[i][1]));
  }

  function update(i, t) {
    if (i === 0) {
      const k = ease(clamp(t / 0.6));
      $("lakh").textContent = Math.round(600000 * k).toLocaleString("en-IN");
      $("lakh").parentElement.style.transform = `scale(${0.55 + 0.45 * k})`;
    } else if (i === 1) {
      const k = ease(clamp(t / 0.5));
      $("bar-cert").style.width = `${100 * k}%`;
      $("bar-coll").style.width = `${(0.243 / 8.543) * 100 * k}%`;
      $("num-cert").textContent = `${(8.54 * k).toFixed(2)} t`;
      $("num-coll").textContent = `${(0.24 * k).toFixed(2)} t`;
      const z = ease(clamp((t - 0.45) / 0.35));
      $("ratio").style.opacity = z;
      $("ratio").style.transform = `scale(${0.4 + 0.6 * z})`;
    } else if (i === 2) {
      // the chain slides sideways while you scroll down; blocks verify one by one and break at #BROKEN
      const k = clamp(t / 0.85);
      const reached = Math.floor(k * (N + 1));
      // keep the block being checked in the middle; after the break, hold the broken one in the middle
      const focus = Math.min(reached, BROKEN), win = track.parentElement.clientWidth;
      const fb = blocks[Math.max(0, Math.min(N - 1, focus))];
      const target = Math.max(0, fb.offsetLeft + fb.offsetWidth / 2 - win / 2);
      track._x = track._x == null ? target : track._x + (target - track._x) * 0.35;
      track.style.transform = `translateX(${-track._x}px)`;
      blocks.forEach((b, j) => {
        b.classList.toggle("ok", j < Math.min(reached, BROKEN));
        b.classList.toggle("bad", j === BROKEN && reached > BROKEN);
        b.classList.toggle("void", j > BROKEN && reached > BROKEN);
      });
      $("chain-note").textContent = reached > BROKEN
        ? `Receipt #${BROKEN} was edited after it was written. The chain breaks there, and everything after it stops counting.`
        : "Each receipt carries the fingerprint of the one before it.";
    } else if (i === 3) {
      const k = ease(clamp((t - 0.15) / 0.4));
      $("lock").style.transform = `scale(${0.6 + 0.4 * k})`;
      $("lock").style.opacity = k;
      $("shackle").setAttribute("d", `M10 22 V${14 - 8 * (1 - k)} a10 10 0 0 1 20 0 V${22 - 8 * (1 - k)}`);
      story.querySelector(".names").style.filter = `blur(${5 * k}px)`;
    }
  }

  if (reduce) {          // no pinning: every scene shows its final state, stacked
    story.classList.add("static");
    scenes.forEach((s, i) => { s.style.opacity = 1; s.style.visibility = "visible"; update(i, 1); });
    return;
  }
  let ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      const r = story.getBoundingClientRect();
      const total = story.offsetHeight - window.innerHeight;
      render(clamp(-r.top / Math.max(1, total)));
      ticking = false;
    });
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll);
  onScroll();
})();
