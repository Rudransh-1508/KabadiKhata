// Kabadi Khata console: Home, Auditor (radar + flag panel), Kabadiwala ledger (chain verify), Brand (certificates + Cedar denial).
// Every number comes from the API through /api (web/server.py). Nothing is decided here.
(function () {
  const AUDITOR = "au-1";
  const BRANDS = [["br-1", "Brand One"], ["br-2", "Brand Two"]];
  const THRESHOLD = 80;                 // verified-backed % a Certificate needs to count as trustworthy (CLAUDE.md fix #4)
  const MATERIAL = { PET: "plastic bottles (PET)", HDPE: "hard plastic (HDPE)", LDPE_film: "plastic bags", mixed_plastic: "mixed plastic",
                     cardboard: "cardboard", paper: "newspaper & paper", metal: "metal", ewaste: "e-waste", unknown: "unknown" };
  const view = document.getElementById("view");
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const names = {};                    // actor_id -> name (auditor reads the directory once)
  let flagsCache = [];
  let nav = 0;                         // bumps on every navigation; late async work for an old page stops

  // ---------- helpers ----------
  async function api(path, who, opts = {}) {
    const res = await fetch("/api" + path, {
      method: opts.method || "GET",
      headers: { "X-Principal": who, ...(opts.body ? { "content-type": "application/json" } : {}) },
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    let data = null;
    try { data = await res.json(); } catch (e) { /* empty body */ }
    return { ok: res.ok, status: res.status, data };
  }
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const h = (html) => { const t = document.createElement("template"); t.innerHTML = html.trim(); return t.content; };
  const nameOf = (id) => names[id] || (id && id.startsWith("rc-") ? "Recycler " + id.slice(3).toUpperCase() : id);
  const fmt = (n, d = 0) => Number(n).toLocaleString("en-IN", { minimumFractionDigits: d, maximumFractionDigits: d });
  function countUp(el, to, d = 0, suffix = "", ms = 900) {
    if (!el) return;
    if (reduce) { el.textContent = fmt(to, d) + suffix; return; }
    const t0 = performance.now();
    const step = (t) => { const k = Math.min(1, (t - t0) / ms), e = 1 - Math.pow(1 - k, 3);
      el.textContent = fmt(to * e, d) + suffix; if (k < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  }
  function ringTo(el, pct) {
    if (!el) return;
    const label = el.querySelector("b");
    if (reduce) { el.style.setProperty("--p", pct); label.textContent = fmt(pct, 1) + "%"; return; }
    const t0 = performance.now();
    const step = (t) => { const k = Math.min(1, (t - t0) / 1000), e = 1 - Math.pow(1 - k, 3);
      el.style.setProperty("--p", pct * e); label.textContent = fmt(pct * e, 1) + "%"; if (k < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  }
  const ringClass = (p) => (p < 50 ? "r-bad" : p < THRESHOLD ? "r-warn" : "r-ok");
  function stagger(root) { [...root.querySelectorAll(".rise")].forEach((el, i) => { el.style.animationDelay = `${i * 60}ms`; }); }
  function setWho(text) { document.getElementById("who").innerHTML = text ? `acting as <b>${esc(text)}</b>` : ""; }
  function apiDown(msg) { return `<div class="err">Can't reach the API (${esc(msg)}). Start it with <code>make api</code>, then reload.</div>`; }

  async function loadNames() {
    if (Object.keys(names).length) return;
    const r = await api("/actors", AUDITOR);
    if (r.ok) r.data.forEach((a) => { names[a.actor_id] = a.name; });
  }

  // ---------- flag wording (plain language, from the Flag's own fields) ----------
  function describe(f) {
    if (f.rule === "R1_mass_balance") {
      const [, rec, mat, month] = f.flag_id.split(":");
      return { sev: "critical", t: `${nameOf(rec)} certified ${fmt(f.score, 1)}× what it collected`,
               s: `${MATERIAL[mat] || mat} · ${month} · ${f.evidence_ids.length} certificates`, score: `${fmt(f.score, 1)}×` };
    }
    if (f.rule === "R3_broken_chain") {
      const m = /#(\d+)/.exec(f.explanation_en || "");
      return { sev: "chain", t: `${nameOf(f.subject_id)}'s receipt chain is broken`,
               s: m ? `Edited after writing at receipt #${m[1]}` : "A receipt was changed after it was written", score: m ? `#${m[1]}` : "" };
    }
    const who = f.subject_id.split(",").map(nameOf);
    return { sev: "warn", t: `Same scale photo on ${fmt(f.score)} receipts`, s: who.join(", "), score: `${fmt(f.score)}×` };
  }
  const SEV_ORDER = { critical: 0, chain: 1, warn: 2 };
  const statusText = { open: "Open", inspection_requested: "Inspection requested", dismissed: "Dismissed" };

  // ---------- HOME ----------
  async function home() {
    const tok = nav;
    setWho("");
    view.replaceChildren(h(`
      <div class="page-head rise"><div><span class="eyebrow">Console</span><h1>Who are you today?</h1>
        <p>Pick a role. Each one sees only what Cedar allows it to see.</p></div></div>
      <div class="cards3">
        <a class="rcard rise bad" href="#auditor"><span class="label">Auditor · au-1</span><h2>Fraud radar</h2>
          <div class="big" id="h-flags">–</div><p id="h-flags-s">Run the radar over every recycler's certificates.</p><span class="go">Open radar →</span></a>
        <a class="rcard rise ok" href="#ledger"><span class="label">Kabadiwala ledger</span><h2>Receipt chains</h2>
          <div class="big" id="h-kw">–</div><p id="h-kw-s">Verify any kabadiwala's receipt chain.</p><span class="go">Open ledger →</span></a>
        <a class="rcard rise warn" href="#brand"><span class="label">Brand · br-1</span><h2>My certificates</h2>
          <div class="big" id="h-risk">–</div><p id="h-risk-s">Check how much of each certificate is backed by real collections.</p><span class="go">Open certificates →</span></a>
      </div>`));
    stagger(view);
    try {
      const [flags, kws, certs] = await Promise.all([api("/flags", AUDITOR), api("/actors?role=kabadiwala", AUDITOR), api("/certificates?brand_id=br-1", "br-1")]);
      if (tok !== nav) return;
      if (certs.ok) {
        const risky = certs.data.filter((c) => c.verified_backed_pct < THRESHOLD).length;
        countUp(document.getElementById("h-risk"), risky);
        document.getElementById("h-risk-s").textContent = `of ${certs.data.length} certificates are below ${THRESHOLD}% verified-backed`;
      }
      const open = (flags.data || []).filter((f) => f.status === "open").length;
      if (flags.ok && flags.data.length) { countUp(document.getElementById("h-flags"), open); document.getElementById("h-flags-s").textContent = "open flags waiting for a decision"; }
      else document.getElementById("h-flags").innerHTML = `0<small>run the radar</small>`;
      if (kws.ok) {
        countUp(document.getElementById("h-kw"), kws.data.length);
        const checks = await Promise.all(kws.data.map((k) => api(`/verify/${encodeURIComponent(k.actor_id)}`, AUDITOR)));
        if (tok !== nav) return;
        const broken = checks.filter((c) => c.ok && !c.data.ok).length;
        document.getElementById("h-kw-s").textContent = broken ? `kabadiwalas · ${broken} chain broken` : "kabadiwalas · every chain intact";
      }
    } catch (e) { if (tok === nav) view.append(h(apiDown(e.message))); }
  }

  // ---------- AUDITOR ----------
  async function auditor(openId) {
    setWho("auditor au-1");
    view.replaceChildren(h(`
      <div class="page-head rise"><div><span class="eyebrow">Auditor · au-1</span><h1>Fraud radar</h1>
        <p>Code decides the flag. The LLM only explains it. You decide what happens next.</p></div>
        <button class="btn btn-primary" id="run">▶ Run radar</button></div>
      <div class="summary rise" id="summary"></div>
      <div class="flags" id="flags"><div class="empty">Loading…</div></div>`));
    stagger(view);
    document.getElementById("run").addEventListener("click", runRadar);
    try {
      await loadNames();
      const tok = nav;
      const r = await api("/flags", AUDITOR);
      if (tok !== nav) return;
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      flagsCache = r.data;
      renderFlags(false);
      if (openId) openFlag(openId);
    } catch (e) { document.getElementById("flags").innerHTML = apiDown(e.message); }
  }

  async function runRadar() {
    const btn = document.getElementById("run");
    btn.disabled = true; btn.textContent = "Scanning…";
    const list = document.getElementById("flags");
    list.prepend(h(`<div class="scan"></div>`));
    const [r] = await Promise.all([api("/radar/run", AUDITOR, { method: "POST", body: {} }), new Promise((ok) => setTimeout(ok, reduce ? 0 : 1100))]);
    btn.disabled = false; btn.textContent = "▶ Run radar again";
    if (!r.ok) { list.innerHTML = apiDown(`HTTP ${r.status}`); return; }
    flagsCache = r.data;
    renderFlags(true);
  }

  function renderFlags(animate) {
    const list = document.getElementById("flags"), sum = document.getElementById("summary");
    if (!list) return;
    if (!flagsCache.length) {
      list.innerHTML = `<div class="empty">No flags yet. Run the radar to check every recycler's certificates against verified receipts.</div>`;
      sum.innerHTML = ""; return;
    }
    const rows = flagsCache.map((f) => ({ f, d: describe(f) })).sort((a, b) => SEV_ORDER[a.d.sev] - SEV_ORDER[b.d.sev] || b.f.score - a.f.score);
    const count = (s) => rows.filter((x) => x.d.sev === s).length;
    sum.innerHTML = `<span class="chip sev-critical"><i></i>${count("critical")} over-claiming recycler</span>
      <span class="chip sev-chain"><i></i>${count("chain")} broken chain</span>
      <span class="chip sev-warn"><i></i>${count("warn")} reused photos</span>`;
    list.replaceChildren(...rows.map(({ f, d }) => {
      const el = h(`<button class="flag sev-${d.sev} ${animate ? "rise" : ""}" data-id="${esc(f.flag_id)}">
        <span class="stripe"></span>
        <span class="body"><span class="t">${esc(d.t)}</span><span class="s">${esc(d.s)}</span></span>
        <span class="side"><span class="score">${esc(d.score)}</span><span class="pill ${f.status}">${statusText[f.status] || f.status}</span></span></button>`).firstChild;
      el.addEventListener("click", () => { location.hash = "#auditor/" + encodeURIComponent(f.flag_id); });
      return el;
    }));
    if (animate) stagger(list);
  }

  // ---------- flag panel ----------
  const panel = document.getElementById("panel"), backdrop = document.getElementById("backdrop"), pbody = document.getElementById("panel-body");
  function showPanel() { backdrop.hidden = false; requestAnimationFrame(() => { backdrop.classList.add("on"); panel.classList.add("on"); }); panel.setAttribute("aria-hidden", "false"); }
  function hidePanel() {
    panel.classList.remove("on"); backdrop.classList.remove("on"); panel.setAttribute("aria-hidden", "true");
    setTimeout(() => { backdrop.hidden = true; }, 250);
  }
  const closeToList = () => { if (location.hash.startsWith("#auditor/")) location.hash = "#auditor"; else hidePanel(); };
  document.getElementById("panel-close").addEventListener("click", closeToList);
  backdrop.addEventListener("click", closeToList);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && panel.classList.contains("on")) closeToList(); });

  async function openFlag(id) {
    const f = flagsCache.find((x) => x.flag_id === id);
    if (!f) return;
    const d = describe(f);
    let lang = "en";
    pbody.replaceChildren(h(`<span class="label">${esc(f.rule.replace(/_/g, " "))} · ${esc(f.flag_id)}</span><h2 class="ptitle">${esc(d.t)}</h2><div id="pmain"></div>
      <div class="explain"><div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap"><span class="label">Why</span>
        <span class="seg"><button data-l="en" class="on">English</button><button data-l="hi">हिंदी</button></span>
        <span class="src">${f.explanation_source ? "written by: " + esc(f.explanation_source) : ""}</span></div>
        <p id="ptext"></p></div>
      <div><span class="label">Evidence</span><div class="evid">${f.evidence_ids.map((e) => `<span>${esc(e)}</span>`).join("")}</div></div>
      <div class="decide" id="decide"></div>`));
    const setText = () => { document.getElementById("ptext").textContent = (lang === "hi" ? f.explanation_hi : f.explanation_en) || "—"; };
    pbody.querySelectorAll(".seg button").forEach((b) => b.addEventListener("click", () => {
      lang = b.dataset.l; pbody.querySelectorAll(".seg button").forEach((x) => x.classList.toggle("on", x === b)); setText(); }));
    setText();
    renderDecision(f);
    showPanel();

    const main = document.getElementById("pmain");
    if (f.rule === "R1_mass_balance") {
      const p = await api(`/provenance/${encodeURIComponent(f.evidence_ids[0])}`, AUDITOR);
      if (!p.ok) return;
      const cert = p.data.recycler_certified_t, coll = p.data.verified_inflow_t;
      main.replaceChildren(h(`<div style="display:grid;gap:18px">
        <div class="kpis"><div class="kpi bad"><b id="k1">0</b><span>tonnes certified</span></div><div class="kpi ok"><b id="k2">0</b><span>tonnes actually collected (verified)</span></div></div>
        <div class="hbars"><div class="hbar">Certified<div class="track"><div class="fill" id="f1"></div></div></div>
          <div class="hbar">Collected<div class="track"><div class="fill ok" id="f2"></div></div></div></div>
        <p class="ratio-line">${fmt(f.score, 1)}× over-claim<small>certified ÷ (collected × 0.85 recycling yield) · flagged above 1.17× · synthetic data</small></p></div>`));
      countUp(document.getElementById("k1"), cert, 2); countUp(document.getElementById("k2"), coll, 2);
      requestAnimationFrame(() => { document.getElementById("f1").style.width = "100%"; document.getElementById("f2").style.width = `${Math.max(1.5, (coll / cert) * 100)}%`; });
    } else if (f.rule === "R3_broken_chain") {
      const v = await api(`/verify/${encodeURIComponent(f.subject_id)}`, AUDITOR);
      if (!v.ok) return;
      main.replaceChildren(h(`<div style="display:grid;gap:14px">
        <div class="kpis"><div class="kpi bad"><b>#${esc(v.data.broken_at_seq)}</b><span>first broken receipt</span></div><div class="kpi"><b>${esc(v.data.length)}</b><span>receipts checked</span></div></div>
        <p style="margin:0">${esc(v.data.reason)}. Receipts from #${esc(v.data.broken_at_seq)} on no longer count as verified inflow for any recycler.</p>
        <a class="btn btn-ghost" style="width:fit-content" href="#ledger/${encodeURIComponent(f.subject_id)}">See ${esc(nameOf(f.subject_id))}'s chain →</a></div>`));
    } else {
      const who = f.subject_id.split(",");
      main.replaceChildren(h(`<div style="display:grid;gap:12px"><div class="kpis"><div class="kpi"><b>${fmt(f.score)}</b><span>receipts with near-identical photos</span></div>
        <div class="kpi"><b>${who.length}</b><span>kabadiwalas involved</span></div></div>
        <div class="evid">${who.map((w) => `<span>${esc(nameOf(w))}</span>`).join("")}</div></div>`));
    }
  }

  function renderDecision(f) {
    const box = document.getElementById("decide");
    if (!box) return;
    if (f.status !== "open") {
      const when = f.decided_ts ? new Date(f.decided_ts).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" }) : "";
      box.innerHTML = `<span class="done">✓ ${statusText[f.status]} by ${esc(f.decided_by || "")}${when ? " · " + esc(when) : ""}</span>`;
      return;
    }
    box.innerHTML = `<button class="btn btn-primary" data-d="inspect">Request inspection</button><button class="btn btn-ghost" data-d="dismiss">Dismiss</button>
      <span class="src">Only a person decides. The rule and the explanation never do.</span>`;
    box.querySelectorAll("button").forEach((b) => b.addEventListener("click", async () => {
      box.querySelectorAll("button").forEach((x) => { x.disabled = true; });
      const r = await api(`/flags/${encodeURIComponent(f.flag_id)}/decision`, AUDITOR, { method: "POST", body: { decision: b.dataset.d } });
      if (!r.ok) { box.innerHTML = `<span class="err">Could not record the decision (HTTP ${r.status}).</span>`; return; }
      Object.assign(f, r.data);
      renderDecision(f); renderFlags(false);
    }));
  }

  // ---------- LEDGER ----------
  async function ledger(kwId) {
    view.replaceChildren(h(`
      <div class="page-head rise"><div><span class="eyebrow">Kabadiwala ledger</span><h1>Receipt chain</h1>
        <p>Every receipt carries the fingerprint of the one before it. Edit one, and the chain breaks right there.</p></div></div>
      <div class="people rise" id="people"></div>
      <div id="kw"></div>`));
    stagger(view);
    try {
      await loadNames();
      const kws = await api("/actors?role=kabadiwala", AUDITOR);
      if (!kws.ok) throw new Error(`HTTP ${kws.status}`);
      const id = kwId || "kw-raju";
      const ppl = document.getElementById("people");
      kws.data.forEach((k) => {
        const b = h(`<button class="person ${k.actor_id === id ? "on" : ""}" data-id="${esc(k.actor_id)}"><i></i>${esc(k.name)}</button>`).firstChild;
        b.addEventListener("click", () => { location.hash = "#ledger/" + encodeURIComponent(k.actor_id); });
        ppl.appendChild(b);
      });
      showChain(id, kws.data.find((k) => k.actor_id === id));
      // status dots: verified in the background
      kws.data.forEach(async (k) => {
        const v = await api(`/verify/${encodeURIComponent(k.actor_id)}`, AUDITOR);
        const dot = ppl.querySelector(`[data-id="${CSS.escape(k.actor_id)}"] i`);
        if (dot && v.ok) dot.className = v.data.ok ? "ok" : "bad";
      });
    } catch (e) { view.append(h(apiDown(e.message))); }
  }

  async function showChain(id, actor) {
    setWho(`kabadiwala ${id}`);
    const box = document.getElementById("kw");
    const tok = nav;
    const r = await api(`/receipts?collector_id=${encodeURIComponent(id)}`, id);   // the kabadiwala reads his own chain
    if (tok !== nav || !box) return;
    if (!r.ok) { box.innerHTML = apiDown(`HTTP ${r.status}`); return; }
    const { receipts, monthly } = r.data;
    const kg = monthly.reduce((s, m) => s + m.weight_kg, 0), inr = monthly.reduce((s, m) => s + m.total_inr, 0);
    box.replaceChildren(h(`<div style="display:grid;gap:18px">
      <div class="income rise">
        <div class="who-card"><span class="label">मेरा हिसाब · ${esc(monthly.map((m) => m.month).join(", ") || "—")}</span><h2>${esc(actor ? actor.name : id)}</h2>
          <span style="color:var(--muted)">${esc(actor && actor.locality ? actor.locality : "")}</span><span class="status idle" id="cstatus">Chain not verified yet</span></div>
        <div class="kpi"><b id="i1">0</b><span>receipts</span></div>
        <div class="kpi"><b id="i2">0</b><span>kg collected</span></div>
        <div class="kpi"><b id="i3">0</b><span>₹ earned (indicative)</span></div>
      </div>
      <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap" class="rise"><button class="btn btn-primary" id="verify">Verify chain</button>
        <span class="src">Recomputes every fingerprint from the receipt's contents.</span></div>
      <div class="chain-scroll rise" id="cscroll"><div class="chain" id="chain"></div></div>
      <div id="verdict"></div><div id="rdetail"></div></div>`));
    stagger(box);
    countUp(document.getElementById("i1"), receipts.length); countUp(document.getElementById("i2"), kg, 1); countUp(document.getElementById("i3"), inr);
    const chain = document.getElementById("chain");
    receipts.forEach((x) => {
      const day = new Date(x.ts).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
      const b = h(`<button class="cblock" data-seq="${x.seq}"><span class="seq">#${x.seq}</span><b>${fmt(x.weight_kg, 1)} kg</b>
        <span class="m">${esc(MATERIAL[x.material] || x.material)}</span><span class="d">${esc(day)}</span><span class="h">${esc(x.hash.slice(0, 8))}…</span></button>`).firstChild;
      b.addEventListener("click", () => detail(x, b));
      chain.appendChild(b);
    });
    document.getElementById("verify").addEventListener("click", () => verify(id, receipts.length));
  }

  function detail(x, el) {
    document.querySelectorAll(".cblock.sel").forEach((b) => b.classList.remove("sel"));
    el.classList.add("sel");
    document.getElementById("rdetail").replaceChildren(h(`<div class="rdetail rise">
      <div><span class="label">Receipt</span><b>${esc(x.receipt_id)} · #${x.seq}</b></div>
      <div><span class="label">When</span><b>${esc(new Date(x.ts).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" }))}</b></div>
      <div><span class="label">What</span><b>${fmt(x.weight_kg, 1)} kg ${esc(MATERIAL[x.material] || x.material)}</b></div>
      <div><span class="label">Where</span><b>${esc(x.locality)}</b></div>
      <div><span class="label">Price (indicative)</span><b>₹${fmt(x.price_inr_per_kg)}/kg</b></div>
      <div><span class="label">Data</span><b>${x.synthetic ? "synthetic" : "real"}</b></div>
      <div class="hash">previous fingerprint ${esc(x.prev_hash)}<br>this fingerprint&nbsp;&nbsp;&nbsp;&nbsp; ${esc(x.hash)}</div></div>`));
  }

  async function verify(id, total) {
    const btn = document.getElementById("verify");
    btn.disabled = true;
    const v = await api(`/verify/${encodeURIComponent(id)}`, id);
    if (!v.ok) { btn.disabled = false; document.getElementById("verdict").innerHTML = apiDown(`HTTP ${v.status}`); return; }
    const blocks = [...document.querySelectorAll(".cblock")];
    blocks.forEach((b) => b.classList.remove("ok", "bad", "void"));
    const stop = v.data.ok ? blocks.length : v.data.broken_at_seq;
    const scroller = document.getElementById("cscroll");
    const tick = reduce ? 0 : Math.max(18, Math.min(60, 1600 / Math.max(1, stop)));
    for (let i = 0; i < blocks.length; i++) {
      if (i < stop) blocks[i].classList.add("ok");
      else if (i === stop) blocks[i].classList.add("bad");
      else blocks[i].classList.add("void");
      if (i <= stop && tick) {
        scroller.scrollLeft = Math.max(0, blocks[i].offsetLeft - scroller.clientWidth / 2);
        await new Promise((ok) => setTimeout(ok, i === stop ? 300 : tick));
      }
    }
    const st = document.getElementById("cstatus");
    if (v.data.ok) {
      st.className = "status ok"; st.textContent = "✓ Chain verified";
      document.getElementById("verdict").innerHTML = `<div class="verdict ok">✓ All ${total} receipts verified. Nothing has been changed since it was written.</div>`;
    } else {
      st.className = "status bad"; st.textContent = `✕ Broken at #${v.data.broken_at_seq}`;
      document.getElementById("verdict").innerHTML = `<div class="verdict bad"><b>Chain broken at receipt #${esc(v.data.broken_at_seq)}</b>: ${esc(v.data.reason)}.
        Receipts from #${esc(v.data.broken_at_seq)} on no longer count as verified inflow, and the auditor sees an R3 flag.</div>`;
      const bad = blocks[v.data.broken_at_seq];
      if (bad) bad.click();
    }
    btn.disabled = false; btn.textContent = "Verify again";
  }

  // ---------- BRAND ----------
  async function brand(brandId) {
    const id = brandId || "br-1";
    setWho(`brand ${id}`);
    view.replaceChildren(h(`
      <div class="page-head rise"><div><span class="eyebrow">Brand · ${esc(id)}</span><h1 id="bsum">My certificates</h1>
        <p>How much of each EPR certificate is backed by receipts we can verify. Trustworthy at ${THRESHOLD}% or more.</p></div>
        <div class="people">${BRANDS.map(([b, n]) => `<a class="person ${b === id ? "on" : ""}" href="#brand/${b}" style="text-decoration:none">${esc(n)}</a>`).join("")}</div></div>
      <div class="certs" id="certs"><div class="empty">Checking every certificate against verified receipts…</div></div>`));
    stagger(view);
    const tok = nav;
    const r = await api(`/certificates?brand_id=${encodeURIComponent(id)}`, id);
    if (tok !== nav) return;
    if (!r.ok) { document.getElementById("certs").innerHTML = apiDown(`HTTP ${r.status}`); return; }
    const certs = r.data.slice().sort((a, b) => a.verified_backed_pct - b.verified_backed_pct);
    const good = certs.filter((c) => c.verified_backed_pct >= THRESHOLD).length;
    document.getElementById("bsum").innerHTML = `<span style="color:var(--ok)">${good}</span> of ${certs.length} certificates trustworthy`;
    const grid = document.getElementById("certs");
    grid.replaceChildren();
    certs.forEach((c) => {
      const el = h(`<a class="cert rise ${ringClass(c.verified_backed_pct)}" href="#cert/${encodeURIComponent(id)}/${encodeURIComponent(c.certificate_id)}">
        <div class="ring"><b>0%</b></div><div class="meta"><b>${esc(nameOf(c.recycler_id))}</b>
        <span>${esc(MATERIAL[c.material] || c.material)} · ${fmt(c.tonnes, 2)} t · ${esc(c.month)}</span><span>${esc(c.certificate_id)}</span></div></a>`).firstChild;
      grid.appendChild(el);
      ringTo(el.querySelector(".ring"), c.verified_backed_pct);
    });
    stagger(grid);
  }

  async function cert(brandId, certId) {
    setWho(`brand ${brandId}`);
    const tok = nav;
    view.replaceChildren(h(`<div class="empty">Loading certificate…</div>`));
    const r = await api(`/provenance/${encodeURIComponent(certId)}`, brandId);
    if (tok !== nav) return;
    if (!r.ok) { view.innerHTML = r.status === 403 ? deniedHtml(r.data) : apiDown(`HTTP ${r.status}`); return; }
    const p = r.data, c = p.certificate, pct = p.verified_backed_pct;
    const maxT = Math.max(...p.by_locality.map((l) => l.tonnes), 0.001);
    view.replaceChildren(h(`
      <a class="back rise" href="#brand/${encodeURIComponent(brandId)}">← All certificates</a>
      <div class="cert-hero rise ${ringClass(pct)}"><div class="ring lg"><b>0%</b></div>
        <div style="display:grid;gap:8px"><span class="eyebrow">${esc(c.certificate_id)} · ${esc(c.month)}</span>
          <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,42px);letter-spacing:-.03em;margin:0;line-height:1.05">
            ${pct < THRESHOLD ? `Only ${fmt(pct, 1)}% of this certificate is backed by verified receipts` : `${fmt(pct, 1)}% backed by verified receipts`}</h1>
          <p style="margin:0;color:var(--muted)">${esc(nameOf(c.recycler_id))} · ${esc(MATERIAL[c.material] || c.material)} · ${fmt(c.tonnes, 2)} t on this certificate</p></div></div>
      <div class="kpis rise" style="grid-template-columns:repeat(auto-fit,minmax(200px,1fr))">
        <div class="kpi"><b id="c1">0</b><span>t on this certificate</span></div>
        <div class="kpi ${pct < THRESHOLD ? "bad" : ""}"><b id="c2">0</b><span>t certified by ${esc(nameOf(c.recycler_id))} this month</span></div>
        <div class="kpi ok"><b id="c3">0</b><span>t verified by receipts</span></div></div>
      <div class="rise" style="display:grid;gap:12px"><span class="label">Where the scrap came from (aggregate)</span>
        <div class="hbars">${p.by_locality.map((l) => `<div class="hbar">${esc(l.locality)}<div class="track" title="${l.receipts} receipts"><div class="fill ok" data-w="${(l.tonnes / maxT) * 100}"></div></div></div>`).join("")
          || `<span style="color:var(--muted)">No verified receipts behind this certificate.</span>`}</div></div>
      <div class="lockbox rise"><span class="label">Kabadiwala identities</span>
        <div class="blur" aria-hidden="true"><span>██████ · Seelampur</span><span>█████ · Okhla</span><span>████ · Shahdara</span><span>███████ · Narela</span></div>
        <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center"><button class="btn btn-ghost" id="ask">🔒 Request identities</button>
          <span class="src">Brands see where the scrap came from, never who collected it.</span></div>
        <div id="denial"></div></div>`));
    stagger(view);
    ringTo(view.querySelector(".ring.lg"), pct);
    countUp(document.getElementById("c1"), c.tonnes, 2); countUp(document.getElementById("c2"), p.recycler_certified_t, 2); countUp(document.getElementById("c3"), p.verified_inflow_t, 2);
    requestAnimationFrame(() => setTimeout(() => view.querySelectorAll(".fill[data-w]").forEach((f) => { f.style.width = `${f.dataset.w}%`; }), 150));
    document.getElementById("ask").addEventListener("click", async () => {
      const a = await api("/actors?role=kabadiwala", brandId);      // the real call; Cedar answers
      document.getElementById("denial").replaceChildren(h(a.status === 403 ? deniedHtml(a.data)
        : `<div class="err">Expected a Cedar denial but got HTTP ${a.status}.</div>`));
    });
  }

  function deniedHtml(d) {
    return `<div class="denied"><h3>Denied by Cedar policy</h3>
      <p>Action <code>${esc(d && d.action)}</code>: ${esc(d && d.reason)}.</p>
      <pre>// policies.cedar: the only thing a brand may do
@id("brand-own-certificates")
permit (
  principal is Actor in Role::"brand",
  action == Action::<em>"read_provenance"</em>,
  resource is Certificate
) when { resource.buyer == principal };   <em>// default deny: nothing else</em></pre></div>`;
  }

  // ---------- router ----------
  async function route() {
    nav++;
    const [page, a, b] = location.hash.replace(/^#/, "").split("/").map(decodeURIComponent);
    document.querySelectorAll(".tabs a").forEach((t) => t.classList.toggle("on", t.dataset.tab === (page === "cert" ? "brand" : page || "home")));
    if (page === "auditor") {
      if (!document.getElementById("flags")) await auditor(a);
      else if (a) openFlag(a); else hidePanel();
      return;
    }
    hidePanel();
    if (page === "ledger") await ledger(a);
    else if (page === "brand") await brand(a);
    else if (page === "cert") await cert(a, b);
    else await home();
    view.focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
  }
  window.addEventListener("hashchange", route);
  route();
})();
