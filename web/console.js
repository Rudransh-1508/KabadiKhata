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
  function apiDown(msg) { return `<p class="err">Can't reach the API (${esc(msg)}). Start it with <code>make api</code>, then reload.</p>`; }

  async function loadNames() {
    if (Object.keys(names).length) return;
    const r = await api("/actors", AUDITOR);
    if (r.ok) r.data.forEach((a) => { names[a.actor_id] = a.name; });
  }

  // ---------- flag wording (plain language, from the Flag's own fields) ----------
  function describe(f) {
    if (f.rule === "R1_mass_balance") {
      const [, rec, mat, month] = f.flag_id.split(":");
      return { sev: "critical", t: `${nameOf(rec)} certified ${fmt(f.score, 1)} times what it collected`,
               s: `${MATERIAL[mat] || mat} · ${month} · ${f.evidence_ids.length} certificates`, score: `${fmt(f.score, 1)}×` };
    }
    if (f.rule === "R3_broken_chain") {
      const m = /#(\d+)/.exec(f.explanation_en || "");
      return { sev: "chain", t: `${nameOf(f.subject_id)}'s receipt chain is broken`,
               s: m ? `Receipt No. ${m[1]} was changed after it was written` : "A receipt was changed after it was written", score: m ? `No. ${m[1]}` : "" };
    }
    const who = f.subject_id.split(",").map(nameOf);
    return { sev: "warn", t: `The same scale photo on ${fmt(f.score)} receipts`, s: who.join(", "), score: "" };
  }
  const SEV_ORDER = { critical: 0, chain: 1, warn: 2 };
  const statusText = { open: "Open", inspection_requested: "Inspection requested", dismissed: "Dismissed" };

  const today = new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  const stampFor = { open: ["grey", "Open"], inspection_requested: ["", "Inspect"], dismissed: ["grey", "Dismissed"] };
  const stamp = (status) => { const [c, t] = stampFor[status] || ["grey", status]; return `<span class="stamp ${c}">${esc(t)}</span>`; };

  // ---------- HOME: a front page ----------
  async function home() {
    const tok = nav;
    setWho("");
    view.replaceChildren(h(`
      <section class="sheet rise">
        <div class="dateline"><span>${esc(today)}</span><span>Synthetic demo edition</span></div>
        <p class="kicker">The console</p>
        <h1 class="headline">Who is reading today?</h1>
        <p class="dek">Pick a desk. Each one sees only what Cedar allows it to see.</p>
        <div class="front" style="margin-top:30px">
          <a href="#auditor"><p class="kicker">Auditor desk · au-1</p><h2>The fraud radar</h2><span class="fig red" id="h-flags">–</span>
            <p id="h-flags-s">Check every recycler's certificates against verified receipts.</p><span class="link big">Open the radar →</span></a>
          <a href="#ledger"><p class="kicker">Kabadiwala ledger</p><h2>Receipt chains</h2><span class="fig" id="h-kw">–</span>
            <p id="h-kw-s">Verify any kabadiwala's chain of receipts.</p><span class="link big">Open the ledger →</span></a>
          <a href="#brand"><p class="kicker">Brand desk · br-1</p><h2>My certificates</h2><span class="fig" id="h-risk">–</span>
            <p id="h-risk-s">See how much of each certificate real collections back.</p><span class="link big">Open certificates →</span></a>
        </div>
      </section>`));
    try {
      const [flags, kws, certs] = await Promise.all([api("/flags", AUDITOR), api("/actors?role=kabadiwala", AUDITOR), api("/certificates?brand_id=br-1", "br-1")]);
      if (tok !== nav) return;
      if (certs.ok) {
        const risky = certs.data.filter((c) => c.verified_backed_pct < THRESHOLD).length;
        countUp(document.getElementById("h-risk"), risky);
        document.getElementById("h-risk-s").textContent = `of ${certs.data.length} certificates fall below ${THRESHOLD}% verified-backed.`;
      }
      const open = (flags.data || []).filter((f) => f.status === "open").length;
      if (flags.ok && flags.data.length) { countUp(document.getElementById("h-flags"), open); document.getElementById("h-flags-s").textContent = "open flags waiting for a person to decide."; }
      else { document.getElementById("h-flags").textContent = "0"; document.getElementById("h-flags-s").textContent = "flags so far. Run the radar to check every recycler."; }
      if (kws.ok) {
        countUp(document.getElementById("h-kw"), kws.data.length);
        const checks = await Promise.all(kws.data.map((k) => api(`/verify/${encodeURIComponent(k.actor_id)}`, AUDITOR)));
        if (tok !== nav) return;
        const broken = checks.filter((c) => c.ok && !c.data.ok).length;
        document.getElementById("h-kw-s").textContent = broken ? `kabadiwalas on record. ${broken} chain has been tampered with.` : "kabadiwalas on record. Every chain is intact.";
      }
    } catch (e) { if (tok === nav) view.append(h(`<section class="sheet">${apiDown(e.message)}</section>`)); }
  }

  // ---------- AUDITOR ----------
  async function auditor(openId) {
    setWho("auditor au-1");
    view.replaceChildren(h(`
      <section class="sheet rise">
        <div class="head-row"><div><p class="kicker">Auditor desk · au-1</p><h1 class="headline">The fraud radar</h1>
          <p class="dek">Code decides what gets flagged. The language model only explains it. You decide what happens next.</p></div>
          <button class="btn btn-primary btn-lg" id="run">Run the radar</button></div>
        <div class="tally" id="summary"></div>
        <div class="flags" id="flags"><p class="empty">Loading…</p></div>
      </section>`));
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
    btn.disabled = true; btn.textContent = "Checking…";
    const list = document.getElementById("flags");
    list.prepend(h(`<div class="scanline"></div>`));
    const [r] = await Promise.all([api("/radar/run", AUDITOR, { method: "POST", body: {} }), new Promise((ok) => setTimeout(ok, reduce ? 0 : 1100))]);
    btn.disabled = false; btn.textContent = "Run the radar again";
    if (!r.ok) { list.innerHTML = apiDown(`HTTP ${r.status}`); return; }
    flagsCache = r.data;
    renderFlags(true);
  }

  function renderFlags(animate) {
    const list = document.getElementById("flags"), sum = document.getElementById("summary");
    if (!list) return;
    if (!flagsCache.length) {
      list.innerHTML = `<p class="empty">Nothing flagged yet. Run the radar to check every recycler's certificates against verified receipts.</p>`;
      sum.innerHTML = ""; return;
    }
    const rows = flagsCache.map((f) => ({ f, d: describe(f) })).sort((a, b) => SEV_ORDER[a.d.sev] - SEV_ORDER[b.d.sev] || b.f.score - a.f.score);
    const count = (s) => rows.filter((x) => x.d.sev === s).length;
    sum.innerHTML = `<span><b>${count("critical")}</b>recycler over-claiming</span><span><b>${count("chain")}</b>chain tampered with</span><span><b>${count("warn")}</b>photos reused</span>`;
    list.replaceChildren(...rows.map(({ f, d }) => {
      const el = h(`<button class="flag sev-${d.sev} ${animate ? "rise" : ""}" data-id="${esc(f.flag_id)}">
        <span class="bar"></span>
        <span><span class="t">${esc(d.t)}</span><span class="s">${esc(d.s)}</span></span>
        <span class="side"><span class="score">${esc(d.score)}</span>${stamp(f.status)}</span></button>`).firstChild;
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
    const rule = { R1_mass_balance: "Mass balance", R2_duplicate_photo: "Duplicate photo", R3_broken_chain: "Broken chain" }[f.rule] || f.rule;
    pbody.replaceChildren(h(`<p class="kicker">${esc(rule)} · ${esc(f.flag_id)}</p><h2 class="ptitle">${esc(d.t)}</h2><div id="pmain"></div>
      <div class="explain"><div class="lang"><span class="section-label" style="margin:0">Why it was flagged</span>
        <button data-l="en" class="on">English</button><button data-l="hi">हिंदी</button>
        <span class="fine" style="margin-left:auto">${f.explanation_source ? "written by: " + esc(f.explanation_source) : ""}</span></div>
        <p id="ptext"></p></div>
      <div><p class="section-label">Evidence</p><div class="evid">${f.evidence_ids.map((e) => `<span>${esc(e)}</span>`).join("")}</div></div>
      <div class="decide" id="decide"></div>`));
    const setText = () => { document.getElementById("ptext").textContent = (lang === "hi" ? f.explanation_hi : f.explanation_en) || "—"; };
    pbody.querySelectorAll(".lang button").forEach((b) => b.addEventListener("click", () => {
      lang = b.dataset.l; pbody.querySelectorAll(".lang button").forEach((x) => x.classList.toggle("on", x === b)); setText(); }));
    setText();
    renderDecision(f);
    showPanel();

    const main = document.getElementById("pmain");
    if (f.rule === "R1_mass_balance") {
      const p = await api(`/provenance/${encodeURIComponent(f.evidence_ids[0])}`, AUDITOR);
      if (!p.ok) return;
      const cert = p.data.recycler_certified_t, coll = p.data.verified_inflow_t;
      main.replaceChildren(h(`<div style="display:grid;gap:18px">
        <div class="figs"><div><b class="red" id="k1">0</b><span>tonnes certified</span></div><div><b class="green" id="k2">0</b><span>tonnes actually collected, on receipts</span></div></div>
        <div class="inkbars"><div class="inkbar">Certified<div class="track"><div class="fill" id="f1"></div></div><span class="v">${fmt(cert, 2)} t</span></div>
          <div class="inkbar">Collected<div class="track"><div class="fill green" id="f2"></div></div><span class="v">${fmt(coll, 2)} t</span></div></div>
        <div><p class="verdict-line">${fmt(f.score, 1)}× over-claim</p><p class="fine">Certified ÷ (collected × 0.85 recycling yield). Flagged above 1.17×. Synthetic data.</p></div></div>`));
      countUp(document.getElementById("k1"), cert, 2); countUp(document.getElementById("k2"), coll, 2);
      requestAnimationFrame(() => { document.getElementById("f1").style.width = "100%"; document.getElementById("f2").style.width = `${Math.max(1.5, (coll / cert) * 100)}%`; });
    } else if (f.rule === "R3_broken_chain") {
      const v = await api(`/verify/${encodeURIComponent(f.subject_id)}`, AUDITOR);
      if (!v.ok) return;
      main.replaceChildren(h(`<div style="display:grid;gap:16px">
        <div class="figs"><div><b class="red">#${esc(v.data.broken_at_seq)}</b><span>first receipt that doesn't hold</span></div><div><b>${esc(v.data.length)}</b><span>receipts checked</span></div></div>
        <p style="margin:0;font-size:17px">${esc(v.data.reason)}. Receipts from #${esc(v.data.broken_at_seq)} on stop counting as verified inflow for any recycler.</p>
        <a class="link" href="#ledger/${encodeURIComponent(f.subject_id)}">See ${esc(nameOf(f.subject_id))}'s receipts</a></div>`));
    } else {
      const who = f.subject_id.split(",");
      main.replaceChildren(h(`<div class="figs"><div><b>${fmt(f.score)}</b><span>receipts with near-identical photos</span></div>
        <div><b>${who.length}</b><span>kabadiwalas: ${esc(who.map(nameOf).join(", "))}</span></div></div>`));
    }
  }

  function renderDecision(f) {
    const box = document.getElementById("decide");
    if (!box) return;
    if (f.status !== "open") {
      const when = f.decided_ts ? new Date(f.decided_ts).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" }) : "";
      box.innerHTML = `<span class="stamp big ${f.status === "dismissed" ? "grey" : ""} thunk">${f.status === "dismissed" ? "Dismissed" : "Inspection requested"}</span>
        <span class="fine">by ${esc(f.decided_by || "")}${when ? ", " + esc(when) : ""}</span>`;
      return;
    }
    box.innerHTML = `<button class="btn btn-primary btn-lg" data-d="inspect">Request an inspection</button><button class="btn btn-ghost" data-d="dismiss">Dismiss</button>
      <span class="fine">Only a person decides. The rule and the explanation never do.</span>`;
    box.querySelectorAll("button").forEach((b) => b.addEventListener("click", async () => {
      box.querySelectorAll("button").forEach((x) => { x.disabled = true; });
      const r = await api(`/flags/${encodeURIComponent(f.flag_id)}/decision`, AUDITOR, { method: "POST", body: { decision: b.dataset.d } });
      if (!r.ok) { box.innerHTML = `<span class="err">Couldn't record the decision (HTTP ${r.status}).</span>`; return; }
      Object.assign(f, r.data);
      renderDecision(f); renderFlags(false);
    }));
  }

  // ---------- LEDGER ----------
  async function ledger(kwId) {
    view.replaceChildren(h(`
      <section class="sheet rise">
        <p class="kicker">Kabadiwala ledger</p><h1 class="headline">Every receipt, chained to the one before</h1>
        <p class="dek">Each receipt carries the fingerprint of the last. Change one, and the chain breaks at that receipt.</p>
        <div class="people" id="people"></div>
        <div id="pass"></div>
      </section>
      <div id="kw"></div>`));
    try {
      await loadNames();
      const kws = await api("/actors?role=kabadiwala", AUDITOR);
      if (!kws.ok) throw new Error(`HTTP ${kws.status}`);
      const id = kwId || "kw-raju";
      const ppl = document.getElementById("people");
      kws.data.forEach((k) => {
        const b = h(`<button class="person ${k.actor_id === id ? "on" : ""}" data-id="${esc(k.actor_id)}">${esc(k.name)}<i></i></button>`).firstChild;
        b.addEventListener("click", () => { location.hash = "#ledger/" + encodeURIComponent(k.actor_id); });
        ppl.appendChild(b);
      });
      showChain(id, kws.data.find((k) => k.actor_id === id));
      kws.data.forEach(async (k) => {
        const v = await api(`/verify/${encodeURIComponent(k.actor_id)}`, AUDITOR);
        const mark = ppl.querySelector(`[data-id="${CSS.escape(k.actor_id)}"] i`);
        if (mark && v.ok) { mark.className = v.data.ok ? "ok" : "bad"; mark.textContent = v.data.ok ? "✓" : "✗"; }
      });
    } catch (e) { view.append(h(`<section class="sheet">${apiDown(e.message)}</section>`)); }
  }

  async function showChain(id, actor) {
    setWho(`kabadiwala ${id}`);
    const tok = nav;
    const r = await api(`/receipts?collector_id=${encodeURIComponent(id)}`, id);   // the kabadiwala reads his own chain
    const pass = document.getElementById("pass"), box = document.getElementById("kw");
    if (tok !== nav || !box) return;
    if (!r.ok) { pass.innerHTML = apiDown(`HTTP ${r.status}`); return; }
    const { receipts, monthly } = r.data;
    const kg = monthly.reduce((s, m) => s + m.weight_kg, 0), inr = monthly.reduce((s, m) => s + m.total_inr, 0);
    pass.replaceChildren(h(`<div class="passbook">
        <div><p class="kicker">मेरा हिसाब · ${esc(monthly.map((m) => m.month).join(", ") || "—")}</p><h2>${esc(actor ? actor.name : id)}</h2>
          <p class="fine" style="margin-top:6px">${esc(actor && actor.locality ? actor.locality : "")}</p>
          <div id="cstamp" style="margin-top:16px"><span class="stamp grey">Not verified yet</span></div></div>
        <dl class="leaders"><div><dt>Receipts</dt><dd id="i1">0</dd></div><div><dt>Kilos collected</dt><dd id="i2">0</dd></div>
          <div><dt>Earned (indicative rates)</dt><dd>₹<span id="i3">0</span></dd></div></dl>
      </div>`));
    countUp(document.getElementById("i1"), receipts.length); countUp(document.getElementById("i2"), kg, 1); countUp(document.getElementById("i3"), inr);
    box.replaceChildren(h(`<div style="display:grid;gap:8px">
      <div class="desk-row"><button class="btn btn-primary btn-lg" id="verify">Verify the chain</button>
        <span class="desk-note">Recomputes every fingerprint from what the receipt says.</span></div>
      <div class="chain-scroll" id="cscroll"><div class="chain" id="chain"></div></div></div>
      <div id="after"></div>`));
    const chain = document.getElementById("chain");
    receipts.forEach((x) => {
      const day = new Date(x.ts).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
      const b = h(`<button class="slip" data-seq="${x.seq}"><span class="n">No. ${x.seq} · ${esc(day)}</span><b>${fmt(x.weight_kg, 1)} kg</b>
        <span class="m">${esc(MATERIAL[x.material] || x.material)}</span><span class="h">${esc(x.hash.slice(0, 10))}</span><span class="mark"></span></button>`).firstChild;
      b.addEventListener("click", () => detail(x, b));
      chain.appendChild(b);
    });
    document.getElementById("verify").addEventListener("click", () => verify(id, receipts.length));
  }

  function afterSheet() {
    let s = document.getElementById("aftersheet");
    if (!s) { document.getElementById("after").replaceChildren(h(`<section class="sheet rise" id="aftersheet"><div id="verdict"></div><div id="rdetail"></div></section>`)); s = document.getElementById("aftersheet"); }
    return s;
  }

  function detail(x, el) {
    document.querySelectorAll(".slip.sel").forEach((b) => b.classList.remove("sel"));
    el.classList.add("sel");
    afterSheet();
    document.getElementById("rdetail").replaceChildren(h(`<div class="rdetail" style="margin-top:18px">
      <div><span>Receipt</span><b>${esc(x.receipt_id)} · No. ${x.seq}</b></div>
      <div><span>When</span><b>${esc(new Date(x.ts).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" }))}</b></div>
      <div><span>What</span><b>${fmt(x.weight_kg, 1)} kg ${esc(MATERIAL[x.material] || x.material)}</b></div>
      <div><span>Where</span><b>${esc(x.locality)}</b></div>
      <div><span>Rate (indicative)</span><b>₹${fmt(x.price_inr_per_kg)} a kilo</b></div>
      <div><span>Data</span><b>${x.synthetic ? "synthetic" : "real"}</b></div>
      <div class="hash">fingerprint of the receipt before&nbsp; ${esc(x.prev_hash)}<br>fingerprint of this receipt&nbsp;&nbsp;&nbsp;&nbsp; ${esc(x.hash)}</div></div>`));
  }

  async function verify(id, total) {
    const btn = document.getElementById("verify");
    btn.disabled = true;
    const v = await api(`/verify/${encodeURIComponent(id)}`, id);
    if (!v.ok) { btn.disabled = false; afterSheet(); document.getElementById("verdict").innerHTML = apiDown(`HTTP ${v.status}`); return; }
    const slips = [...document.querySelectorAll(".slip")];
    slips.forEach((b) => { b.classList.remove("void"); b.querySelector(".mark").innerHTML = ""; });
    const stop = v.data.ok ? slips.length : v.data.broken_at_seq;
    const scroller = document.getElementById("cscroll");
    const tick = reduce ? 0 : Math.max(18, Math.min(60, 1600 / Math.max(1, stop)));
    for (let i = 0; i < slips.length; i++) {
      if (i < stop) slips[i].querySelector(".mark").innerHTML = `<span class="stamp green">OK</span>`;
      else if (i === stop) slips[i].querySelector(".mark").innerHTML = `<span class="stamp thunk">Edited</span>`;
      else slips[i].classList.add("void");
      if (i <= stop && tick) {
        scroller.scrollLeft = Math.max(0, slips[i].offsetLeft - scroller.clientWidth / 2);
        await new Promise((ok) => setTimeout(ok, i === stop ? 350 : tick));
      }
    }
    afterSheet();
    if (v.data.ok) {
      document.getElementById("cstamp").innerHTML = `<span class="stamp big green thunk">Chain verified</span>`;
      document.getElementById("verdict").innerHTML = `<div class="verdict"><p>All ${total} receipts check out. Nothing has changed since it was written.</p></div>`;
    } else {
      document.getElementById("cstamp").innerHTML = `<span class="stamp big thunk">Broken at No. ${esc(v.data.broken_at_seq)}</span>`;
      document.getElementById("verdict").innerHTML = `<div class="verdict"><span class="stamp big thunk">Tampered</span>
        <p><b>Receipt No. ${esc(v.data.broken_at_seq)}</b>: ${esc(v.data.reason)}. Every receipt from here on stops counting as verified inflow, and the auditor sees a broken-chain flag.</p></div>`;
      const bad = slips[v.data.broken_at_seq];
      if (bad) bad.click();
    }
    btn.disabled = false; btn.textContent = "Verify again";
  }

  // ---------- BRAND ----------
  const pctClass = (p) => (p < 50 ? "red" : p < THRESHOLD ? "amber" : "green");
  async function brand(brandId) {
    const id = brandId || "br-1";
    setWho(`brand ${id}`);
    view.replaceChildren(h(`
      <section class="sheet rise">
        <div class="head-row"><div><p class="kicker">Brand desk · ${esc(id)}</p><h1 class="headline" id="bsum">My certificates</h1>
          <p class="dek">How much of each recycling certificate is backed by receipts we can verify. We trust a certificate at ${THRESHOLD}% or more.</p></div>
          <div class="switch">${BRANDS.map(([b, n]) => `<a class="${b === id ? "on" : ""}" href="#brand/${b}">${esc(n)}</a>`).join("")}</div></div>
        <div class="table-wrap"><table class="ledger"><thead><tr><th>Recycler</th><th>Material</th><th>Tonnes</th><th>Backed by receipts</th><th></th></tr></thead>
          <tbody id="certs"><tr><td colspan="5" class="empty">Checking every certificate against verified receipts…</td></tr></tbody></table></div>
      </section>`));
    const tok = nav;
    const r = await api(`/certificates?brand_id=${encodeURIComponent(id)}`, id);
    if (tok !== nav) return;
    const body = document.getElementById("certs");
    if (!r.ok) { body.innerHTML = `<tr><td colspan="5">${apiDown(`HTTP ${r.status}`)}</td></tr>`; return; }
    const certs = r.data.slice().sort((a, b) => a.verified_backed_pct - b.verified_backed_pct);
    const good = certs.filter((c) => c.verified_backed_pct >= THRESHOLD).length;
    document.getElementById("bsum").textContent = `${good} of ${certs.length} certificates hold up`;
    body.replaceChildren(...certs.map((c) => {
      const tr = h(`<table><tbody><tr class="row" tabindex="0">
        <td><span class="rec">${esc(nameOf(c.recycler_id))}</span><span class="id">${esc(c.certificate_id)} · ${esc(c.month)}</span></td>
        <td>${esc(MATERIAL[c.material] || c.material)}</td><td class="num">${fmt(c.tonnes, 2)}</td>
        <td><div class="pct"><span class="num" style="font-family:var(--font-display);font-weight:700;font-size:18px">${fmt(c.verified_backed_pct, 1)}%</span>
          <div class="track"><div class="fill ${pctClass(c.verified_backed_pct)}" data-w="${c.verified_backed_pct}"></div></div></div></td>
        <td>${c.verified_backed_pct < THRESHOLD ? `<span class="stamp">Review</span>` : ""}</td></tr></tbody></table>`).querySelector("tr");
      const go = () => { location.hash = `#cert/${encodeURIComponent(id)}/${encodeURIComponent(c.certificate_id)}`; };
      tr.addEventListener("click", go); tr.addEventListener("keydown", (e) => { if (e.key === "Enter") go(); });
      return tr;
    }));
    requestAnimationFrame(() => setTimeout(() => body.querySelectorAll(".fill[data-w]").forEach((f) => { f.style.width = `${f.dataset.w}%`; }), 80));
  }

  async function cert(brandId, certId) {
    setWho(`brand ${brandId}`);
    const tok = nav;
    view.replaceChildren(h(`<section class="sheet"><p class="empty">Loading the certificate…</p></section>`));
    const r = await api(`/provenance/${encodeURIComponent(certId)}`, brandId);
    if (tok !== nav) return;
    if (!r.ok) { view.innerHTML = `<section class="sheet">${r.status === 403 ? deniedHtml(r.data) : apiDown(`HTTP ${r.status}`)}</section>`; return; }
    const p = r.data, c = p.certificate, pct = p.verified_backed_pct;
    const maxT = Math.max(...p.by_locality.map((l) => l.tonnes), 0.001);
    view.replaceChildren(h(`
      <a class="back" href="#brand/${encodeURIComponent(brandId)}">Back to all certificates</a>
      <section class="sheet rise">
        <div class="dateline"><span>Certificate ${esc(c.certificate_id)}</span><span>${esc(c.month)} · ${esc(nameOf(c.recycler_id))}</span></div>
        <div class="doc-head"><span class="doc-pct ${pctClass(pct)}" id="dpct">0%</span>
          <div><h1 class="headline" style="font-size:clamp(28px,3.6vw,46px)">${pct < THRESHOLD ? `Only ${fmt(pct, 1)}% of this certificate is backed by real receipts` : `${fmt(pct, 1)}% of this certificate is backed by real receipts`}</h1>
            <p class="dek">${esc(MATERIAL[c.material] || c.material)}, ${fmt(c.tonnes, 2)} tonnes on this certificate.</p></div></div>
        <div class="figs" style="margin-top:28px;grid-template-columns:repeat(3,1fr)">
          <div><b id="c1">0</b><span>t on this certificate</span></div>
          <div><b class="${pct < THRESHOLD ? "red" : ""}" id="c2">0</b><span>t ${esc(nameOf(c.recycler_id))} certified this month</span></div>
          <div><b class="green" id="c3">0</b><span>t verified by receipts</span></div></div>
        <div style="margin-top:28px"><p class="section-label">Where the scrap came from (totals by area, no names)</p>
          <div class="inkbars">${p.by_locality.map((l) => `<div class="inkbar">${esc(l.locality)}<div class="track"><div class="fill green" data-w="${(l.tonnes / maxT) * 100}"></div></div><span class="v">${fmt(l.tonnes, 3)} t</span></div>`).join("")
            || `<p class="fine">No verified receipts behind this certificate.</p>`}</div></div>
        <div class="redacted" style="margin-top:30px" id="redacted"><p class="section-label" style="margin:0">Kabadiwalas behind these tonnes, by area</p>
          <ol>${p.by_locality.map((l) => `<li><span class="bar" style="width:${6 + (l.locality.length % 6)}em"></span>, ${esc(l.locality)} · ${fmt(l.receipts)} receipt${l.receipts === 1 ? "" : "s"}</li>`).join("")
            || `<li>No verified receipts behind this certificate.</li>`}</ol>
          <div><button class="btn btn-primary btn-lg" id="ask">Request their names</button></div>
          <div id="denial"></div></div>
      </section>`));
    countUp(document.getElementById("dpct"), pct, 1, "%");
    countUp(document.getElementById("c1"), c.tonnes, 2); countUp(document.getElementById("c2"), p.recycler_certified_t, 2); countUp(document.getElementById("c3"), p.verified_inflow_t, 2);
    requestAnimationFrame(() => setTimeout(() => view.querySelectorAll(".fill[data-w]").forEach((f) => { f.style.width = `${f.dataset.w}%`; }), 150));
    document.getElementById("ask").addEventListener("click", async () => {
      const a = await api("/actors?role=kabadiwala", brandId);      // the real call; Cedar answers
      if (a.status === 403) document.getElementById("redacted").append(h(`<span class="stamp big thunk overstamp">Denied</span>`));
      document.getElementById("denial").replaceChildren(h(a.status === 403 ? deniedHtml(a.data) : `<p class="err">Expected Cedar to refuse, but got HTTP ${a.status}.</p>`));
      document.getElementById("ask").disabled = true;
    });
  }

  function deniedHtml(d) {
    return `<div class="denial"><p><b>Refused by Cedar policy.</b> Action <code>${esc(d && d.action)}</code>: ${esc(d && d.reason)}.</p>
      <pre>// Kabadi Khata policies. Default deny: anything not permitted below is denied,
// and \`forbid\` always beats \`permit\`.
...
// 2. Brand: provenance of its own Certificates only (aggregate view, never a Kabadiwala identity).
@id("brand-own-certificates")
permit (
  principal is Actor in Role::"brand",
  action == Action::<em>"read_provenance"</em>,
  resource is Certificate
) when { resource has buyer && resource.buyer == principal };</pre><p class="fine">Quoted from src/policy/policies.cedar.</p></div>`;
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
