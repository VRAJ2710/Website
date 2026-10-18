#!/usr/bin/env python3
"""
patch_rt17.py — The Dispatch Markets: rt17 CLIENT (chat15 -> chat16). Settings rebuild + per-account prefs.
Pair with patch_rt17s.py (server: /api/prefs, /api/account/export|delete, admin-only /api/ai-status, Ask hints).
The client degrades safely if the server patch is not live yet (prefs stay on the device).

Usage:  python3 patch_rt17.py --check | python3 patch_rt17.py | --dir PATH

Changes:
  - Settings overlay rebuilt: Account, Layout, Markets & prices, Alerts, Display, Ask/Expert, Newsletter, Privacy,
    and (admins only) AI providers. Collapsible sections, 44px targets, bottom sheet on phones.
  - Price-frequency picker removed: td_freq ignored and deleted; fixed safe cadence; polls skip hidden tabs.
  - Prefs: localStorage td_prefs_v1 (guests) + GET/PUT /api/prefs (signed in, debounced).
  - Timestamps: 24h, in the chosen timezone (default Europe/London).
  - In-app price alerts + daily brief reminder (5s check while the tab is visible; browser Notification if allowed).
  - Ask hints (length, focus) sent with /api/chat.
Exact anchors with counts; refuses to run twice; CRLF safe; node --check; tmp-then-rename.
"""
import argparse, os, shutil, subprocess, sys, tempfile

MARKER = "REALTIME PRICE LAYER (rt17)"
PREV_MARKER = "REALTIME PRICE LAYER (rt16)"

BLOCK = r'''// ── rt17: Settings rebuild + per-account prefs ─────────────
// Prices: no frequency picker. Streams stay live; polls run at the fixed safe cadence and skip hidden tabs.
const RT17_PREFS_KEY = "td_prefs_v1";
const RT17_TZS = ["Europe/London", "Europe/Paris", "America/New_York", "America/Chicago", "America/Los_Angeles", "Asia/Dubai", "Asia/Kolkata", "Asia/Singapore", "Asia/Tokyo", "Australia/Sydney", "UTC"];
function _rt17Default() {
  return { v: 1, layout: { order: ["p1", "p2", "p3", "p4"], vis: { p1: true, p2: true, p3: true, p4: true }, density: "comfortable" },
    markets: { tz: "Europe/London" }, alerts: { price: [], dailyBrief: false },
    display: { theme: "dark", fontSize: "m", reduceMotion: false }, ask: { length: "detailed", focus: "macro" }, newsletter: { daily: false, weekly: false } };
}
function _rt17Clean(p) {
  const d = _rt17Default(); p = p && typeof p === "object" ? p : {};
  const pick = (v, list, def) => list.includes(v) ? v : def;
  const tkOk = t => { t = String(t || "").trim().toUpperCase(); return /^[A-Z0-9.=^\-]{1,15}$/.test(t) ? t : null; };
  const L = p.layout || {}, M = p.markets || {}, Al = p.alerts || {}, Di = p.display || {}, Ak = p.ask || {}, N = p.newsletter || {};
  const order = [...new Set([...(Array.isArray(L.order) ? L.order.filter(x => d.layout.order.includes(x)) : []), ...d.layout.order])];
  let tz = typeof M.tz === "string" ? M.tz : d.markets.tz;
  try { new Intl.DateTimeFormat("en-GB", { timeZone: tz }); } catch (e) { tz = d.markets.tz; }
  const out = {
    v: 1,
    layout: { order, vis: Object.fromEntries(d.layout.order.map(id => [id, typeof (L.vis || {})[id] === "boolean" ? L.vis[id] : true])), density: pick(L.density, ["comfortable", "compact"], "comfortable") },
    markets: { tz },
    alerts: { price: (Array.isArray(Al.price) ? Al.price : []).slice(0, 20).map(a => { const tk = tkOk(a && a.tk), px = Number(a && a.px); if (!tk || !(px > 0)) return null; return { tk, op: a.op === "below" ? "below" : "above", px, on: a.on !== false, ...(a.firedAt ? { firedAt: Number(a.firedAt) } : {}) }; }).filter(Boolean), dailyBrief: Al.dailyBrief === true },
    display: { theme: "dark", fontSize: pick(Di.fontSize, ["s", "m", "l"], "m"), reduceMotion: Di.reduceMotion === true },
    ask: { length: pick(Ak.length, ["brief", "detailed"], "detailed"), focus: pick(Ak.focus, ["gold", "macro", "crypto", "em"], "macro") },
    newsletter: { daily: N.daily === true, weekly: N.weekly === true },
  };
  if (Array.isArray(M.watchlist)) out.markets.watchlist = [...new Set(M.watchlist.map(tkOk).filter(Boolean))].slice(0, 50);
  return out;
}
let _rt17Prefs = (() => { try { return _rt17Clean(JSON.parse(localStorage.getItem(RT17_PREFS_KEY) || "null")); } catch (e) { return _rt17Default(); } })();
try { if (typeof panelVis === "object" && panelVis && !localStorage.getItem(RT17_PREFS_KEY)) _rt17Prefs.layout.vis = { ..._rt17Prefs.layout.vis, ...panelVis }; } catch (e) {}
let _rt17SaveT = 0, _rt17SaveState = "", _rt17ServerOk = null;
function _rt17Tz() { try { return (_rt17Prefs && _rt17Prefs.markets && _rt17Prefs.markets.tz) || "Europe/London"; } catch (e) { return "Europe/London"; } }
function _rt17Signed() { return typeof _userSignedIn !== "undefined" && _userSignedIn === true; }
function _rt17SaveLocal() { try { localStorage.setItem(RT17_PREFS_KEY, JSON.stringify(_rt17Prefs)); } catch (e) {} }
function _rt17Save() {
  _rt17Prefs = _rt17Clean(_rt17Prefs);
  _rt17SaveLocal(); _rt17Apply();
  if (!_rt17Signed()) { _rt17Status("Saved on this device"); return; }
  _rt17Status("Saving…");
  clearTimeout(_rt17SaveT);
  _rt17SaveT = setTimeout(async () => {
    try {
      const r = await fetch("/api/prefs", { method: "PUT", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prefs: _rt17Prefs }) });
      if (!r.ok) throw new Error(String(r.status));
      _rt17ServerOk = true; _rt17Status("Saved to your account");
    } catch (e) { _rt17ServerOk = false; _rt17Status("Couldn't reach your account — saved on this device"); }
  }, 600);
}
function _rt17Status(t) { _rt17SaveState = t; const el = document.getElementById("rt17-save"); if (el) el.textContent = t; }
async function _rt17LoadServer() {
  if (!_rt17Signed()) return;
  try {
    const r = await fetch("/api/prefs", { credentials: "include" });
    if (!r.ok) { _rt17ServerOk = false; return; }
    const d = await r.json();
    _rt17ServerOk = true;
    if (d && d.prefs) {
      _rt17Prefs = _rt17Clean(d.prefs); _rt17SaveLocal();
      if (Array.isArray(_rt17Prefs.markets.watchlist) && typeof getActiveWl === "function") {
        const wl = getActiveWl(); wl.tickers = _rt17Prefs.markets.watchlist.slice(); if (typeof saveWatchlists === "function") saveWatchlists();
      }
      _rt17Apply();
      try { if (typeof renderMain === "function") renderMain(); } catch (e) {}
    }
  } catch (e) { _rt17ServerOk = false; }
}
function _rt17Apply() {
  const P = _rt17Prefs, b = document.body, de = document.documentElement;
  if (!b) return;
  b.classList.toggle("td-compact", P.layout.density === "compact");
  b.classList.toggle("td-reduce-motion", !!P.display.reduceMotion);
  de.style.setProperty("--td-zoom", P.display.fontSize === "s" ? "0.92" : P.display.fontSize === "l" ? "1.1" : "1");
  b.classList.toggle("td-zoomed", P.display.fontSize !== "m");
  try {
    if (typeof panelVis === "object") { Object.assign(panelVis, P.layout.vis); if (typeof savePanelVis === "function") savePanelVis(); }
    P.layout.order.forEach((id, i) => { const el = document.getElementById(id); if (el) { el.style.order = String(i); if (P.layout.vis[id] === false) el.style.display = "none"; } });
  } catch (e) {}
}
function _rt17AskHints() { return { length: _rt17Prefs.ask.length, focus: _rt17Prefs.ask.focus }; }

// ── Alerts (in-app only: checked while the site is open) ──
function _rt17Px(tk) {
  try { const v = typeof livePx === "function" ? livePx(tk) : null; if (Number.isFinite(v)) return v; } catch (e) {}
  try { const q = P[tk]; const v = Number(q && (q.p ?? q.price)); return Number.isFinite(v) && v > 0 ? v : null; } catch (e) { return null; }
}
function _rt17Notify(title, body) {
  try { if (typeof showToast === "function") showToast(`${title} — ${body}`, "var(--gd)"); } catch (e) {}
  try { if ("Notification" in window && Notification.permission === "granted") new Notification(title, { body, tag: "td-" + title }); } catch (e) {}
}
function _rt17CheckAlerts() {
  if (document.hidden) return;
  let changed = false;
  (_rt17Prefs.alerts.price || []).forEach(a => {
    if (!a.on) return;
    const px = _rt17Px(a.tk); if (px == null) return;
    if ((a.op === "above" && px >= a.px) || (a.op === "below" && px <= a.px)) {
      a.on = false; a.firedAt = Date.now(); changed = true;
      _rt17Notify(`${a.tk} ${a.op} ${a.px}`, `now ${px.toLocaleString("en-GB", { maximumFractionDigits: 4 })}`);
    }
  });
  if (_rt17Prefs.alerts.dailyBrief) {
    const now = new Date();
    const day = now.toLocaleDateString("en-CA", { timeZone: "Europe/London" });
    const hr = Number(now.toLocaleString("en-GB", { timeZone: "Europe/London", hour: "2-digit", hour12: false }));
    let seen = ""; try { seen = localStorage.getItem("td_brief_notified") || ""; } catch (e) {}
    if (hr >= 7 && seen !== day) {
      try { localStorage.setItem("td_brief_notified", day); } catch (e) {}
      _rt17Notify("Today's Dispatch Brief", "Open the Brief for today's house view.");
    }
  }
  if (changed) { _rt17Save(); if (document.getElementById("settingsOv")) _rt17Render(); }
}
setInterval(_rt17CheckAlerts, 5000);

// ── Settings UI ──
function _rt17Esc(s) { return typeof _escHtml === "function" ? _escHtml(s) : String(s); }
function _rt17Sec(id, title, body, open) {
  return `<details class="rt17-sec" id="rt17-${id}" ${open ? "open" : ""}><summary>${title}</summary><div class="rt17-body">${body}</div></details>`;
}
function _rt17Seg(name, cur, opts, onchange) {
  return `<div class="rt17-seg" role="radiogroup" aria-label="${name}">${opts.map(([v, l]) => `<button type="button" role="radio" aria-checked="${cur === v}" class="${cur === v ? "on" : ""}" onclick="${onchange}('${v}')">${l}</button>`).join("")}</div>`;
}
function _rt17Tog(label, on, onchange, sub) {
  return `<label class="rt17-row rt17-tog"><span><span class="rt17-l">${label}</span>${sub ? `<span class="rt17-sub">${sub}</span>` : ""}</span><input type="checkbox" ${on ? "checked" : ""} onchange="${onchange}"><span class="rt17-sw" aria-hidden="true"></span></label>`;
}
function _rt17Soon(label, note) { return `<div class="rt17-row rt17-soon"><span class="rt17-l">${label}</span><span class="rt17-badge">Coming soon</span>${note ? `<span class="rt17-sub">${note}</span>` : ""}</div>`; }
function _rt17Html() {
  const P = _rt17Prefs, admin = typeof _userAdmin !== "undefined" && _userAdmin === true, prem = typeof _isPremium === "function" && _isPremium(), signed = _rt17Signed();
  const email = window._tdMeEmail || "";
  const plan = admin ? "Admin · full access" : prem ? "Premium" : signed ? "Free account" : "Not signed in";
  const acct = signed
    ? `<div class="rt17-row"><span class="rt17-l">Plan</span><span class="rt17-v">${plan}</span></div>
       ${email ? `<div class="rt17-row"><span class="rt17-l">Email</span><span class="rt17-v">${_rt17Esc(email)}</span></div>` : ""}
       ${(typeof _userBilling !== "undefined" && _userBilling && !admin) ? `<button type="button" class="rt17-btn" onclick="_openBillingPortal()">Manage billing (Stripe)</button>` : (!prem ? `<a class="rt17-btn rt17-btn-gold" href="/__auth/subscribe">Upgrade to Premium · £15/month</a>` : "")}
       ${admin ? `<a class="rt17-btn" href="/__admin">Admin console</a>` : ""}
       <a class="rt17-btn" href="/__auth/logout">Sign out</a>`
    : `<div class="rt17-row"><span class="rt17-l">Plan</span><span class="rt17-v">${plan}</span></div>
       <div class="rt17-note">Settings are saved on this device. Sign in to keep them on every device.</div>
       <a class="rt17-btn rt17-btn-gold" href="/__auth/login">Sign in</a><a class="rt17-btn" href="/__auth/register">Create free account</a>`;
  const names = { p1: "Markets", p2: "News / analysis", p3: "Signals & calendar", p4: "Indices & watchlist" };
  const layout = `<div class="rt17-h">Desktop panels</div>
    ${P.layout.order.map((id, i) => `<div class="rt17-row rt17-order">
      <label class="rt17-tog-inline"><input type="checkbox" ${P.layout.vis[id] !== false ? "checked" : ""} onchange="_rt17SetVis('${id}',this.checked)"> <span>${names[id]}</span></label>
      <span class="rt17-ud"><button type="button" aria-label="Move ${names[id]} up" ${i === 0 ? "disabled" : ""} onclick="_rt17Move('${id}',-1)">▲</button><button type="button" aria-label="Move ${names[id]} down" ${i === P.layout.order.length - 1 ? "disabled" : ""} onclick="_rt17Move('${id}',1)">▼</button></span></div>`).join("")}
    <div class="rt17-h">Density</div>${_rt17Seg("Density", P.layout.density, [["comfortable", "Comfortable"], ["compact", "Compact"]], "_rt17SetDensity")}
    <button type="button" class="rt17-btn" onclick="_rt17ResetLayout()">Reset layout</button>`;
  const wl = typeof getActiveWl === "function" ? getActiveWl() : { name: "Watchlist", tickers: [] };
  const markets = `<div class="rt17-note">Prices stream live where a free live feed exists (crypto, FX, US stocks in market hours). Everything else refreshes about every minute while this tab is open and pauses when it's hidden. Each price shows its source and its own "as of" time; delayed feeds say so.</div>
    <div class="rt17-h">Default watchlist · ${_rt17Esc(wl.name || "Watchlist")}</div>
    ${(wl.tickers || []).map((tk, i, arr) => `<div class="rt17-row rt17-order"><span class="rt17-l">${_rt17Esc(tk)}</span><span class="rt17-ud">
      <button type="button" aria-label="Move ${_rt17Esc(tk)} up" ${i === 0 ? "disabled" : ""} onclick="_rt17WlMove(${i},-1)">▲</button><button type="button" aria-label="Move ${_rt17Esc(tk)} down" ${i === arr.length - 1 ? "disabled" : ""} onclick="_rt17WlMove(${i},1)">▼</button><button type="button" aria-label="Remove ${_rt17Esc(tk)}" onclick="_rt17WlDel(${i})">✕</button></span></div>`).join("") || `<div class="rt17-note">No symbols yet.</div>`}
    <form class="rt17-add" onsubmit="event.preventDefault();_rt17WlAdd(this.sym.value);this.sym.value=''"><input name="sym" maxlength="15" autocapitalize="characters" placeholder="Add symbol, e.g. NVDA" aria-label="Add symbol"><button type="submit" class="rt17-btn">Add</button></form>
    <div class="rt17-h">Timezone for timestamps</div>
    <select class="rt17-sel" aria-label="Timezone" onchange="_rt17SetTz(this.value)">${[...new Set([P.markets.tz, ...RT17_TZS])].map(z => `<option value="${_rt17Esc(z)}" ${z === P.markets.tz ? "selected" : ""}>${_rt17Esc(z.replace(/_/g, " "))}</option>`).join("")}</select>
    ${_rt17Soon("Default chart range & interval")}${_rt17Soon("Number format & decimals")}${_rt17Soon("Display currency (USD / GBP / EUR)", "Prices are shown in their native currency for now.")}`;
  const perm = "Notification" in window ? Notification.permission : "unsupported";
  const alerts = `<div class="rt17-note">Alerts work in this browser while The Dispatch is open. Email alerts aren't available yet.</div>
    ${(P.alerts.price || []).map((a, i) => `<div class="rt17-row"><span class="rt17-l">${_rt17Esc(a.tk)} ${a.op} ${a.px}</span><span class="rt17-ud">${a.on ? `<span class="rt17-sub">armed</span>` : `<span class="rt17-sub">${a.firedAt ? "triggered" : "off"}</span><button type="button" onclick="_rt17AlertRearm(${i})">Re-arm</button>`}<button type="button" aria-label="Delete alert" onclick="_rt17AlertDel(${i})">✕</button></span></div>`).join("")}
    <form class="rt17-add rt17-add-alert" onsubmit="event.preventDefault();_rt17AlertAdd(this)">
      <select name="tk" aria-label="Symbol">${(wl.tickers || []).map(t => `<option>${_rt17Esc(t)}</option>`).join("")}</select>
      <select name="op" aria-label="Direction"><option value="above">above</option><option value="below">below</option></select>
      <input name="px" inputmode="decimal" placeholder="Price" aria-label="Price level"><button type="submit" class="rt17-btn">Add</button></form>
    ${_rt17Tog("Daily brief reminder", P.alerts.dailyBrief, "_rt17SetBriefNote(this.checked)", "Once a day after 07:00 UK time, when you open the site")}
    ${perm === "default" ? `<button type="button" class="rt17-btn" onclick="Notification.requestPermission().then(()=>_rt17Render())">Allow browser notifications</button>` : perm === "denied" ? `<div class="rt17-note">Browser notifications are blocked; alerts show inside the page.</div>` : ""}`;
  const display = `${_rt17Soon("Theme: Light", "Terminal dark is the only theme for now.")}
    <div class="rt17-h">Text size</div>${_rt17Seg("Text size", P.display.fontSize, [["s", "Small"], ["m", "Standard"], ["l", "Large"]], "_rt17SetFont")}
    ${_rt17Tog("Reduce motion", P.display.reduceMotion, "_rt17SetMotion(this.checked)", "Turns off price flashes and animations")}`;
  const ask = `<div class="rt17-h">Answer length</div>${_rt17Seg("Answer length", P.ask.length, [["brief", "Brief"], ["detailed", "Detailed"]], "_rt17SetAskLen")}
    <div class="rt17-h">Default focus</div>${_rt17Seg("Default focus", P.ask.focus, [["gold", "Gold"], ["macro", "Macro"], ["crypto", "Crypto"], ["em", "EM"]], "_rt17SetAskFocus")}`;
  const news = `${_rt17Tog("Daily newsletter", P.newsletter.daily, "_rt17SetNews('daily',this.checked)", P.newsletter.daily ? "Saved — sending starts soon" : "")}
    ${_rt17Tog("Weekly newsletter", P.newsletter.weekly, "_rt17SetNews('weekly',this.checked)", P.newsletter.weekly ? "Saved — sending starts soon" : "")}
    <div class="rt17-note">We'll save your choice now. Newsletter emails haven't started yet.</div>`;
  const privacy = `<button type="button" class="rt17-btn" onclick="_rt17Export()">Export my data (JSON)</button>
    ${signed && !admin ? `<div class="rt17-h rt17-danger">Delete account</div>
      <div class="rt17-note">This permanently deletes your account, sessions and saved settings. Paying members must cancel billing first.</div>
      <input class="rt17-sel" id="rt17-del-in" autocomplete="off" placeholder="Type DELETE to confirm" aria-label="Type DELETE to confirm" oninput="document.getElementById('rt17-del-btn').disabled=this.value!=='DELETE'">
      <button type="button" class="rt17-btn rt17-btn-danger" id="rt17-del-btn" disabled onclick="_rt17Delete()">Delete my account</button><div class="rt17-note" id="rt17-del-msg" role="status"></div>`
    : signed ? `<div class="rt17-note">Administrator accounts can't be deleted from Settings.</div>` : `<button type="button" class="rt17-btn" onclick="_rt17ClearLocal()">Clear settings on this device</button>`}`;
  const byok = admin ? _rt17Sec("byok", "AI providers (admin)", `<div id="ai-provider-status" class="rt17-note">Checking owner-managed providers…</div><div class="rt17-note">Keys are configured in Replit Secrets, never on this page. Only administrators see this section.</div>`) : "";
  return `<div class="rt17-panel" role="document">
    <div class="rt17-top"><h2 id="settings-title" tabindex="-1">Settings</h2><button type="button" class="rt17-x" onclick="_rt17Close()" aria-label="Close settings">×</button></div>
    <div class="rt17-scroll">
      ${_rt17Sec("account", "Account", acct, true)}
      ${_rt17Sec("layout", "Layout", layout)}
      ${_rt17Sec("markets", "Markets & prices", markets)}
      ${_rt17Sec("alerts", "Alerts", alerts)}
      ${_rt17Sec("display", "Display", display)}
      ${_rt17Sec("ask", "Ask / Expert", ask)}
      ${_rt17Sec("newsletter", "Newsletter", news)}
      ${_rt17Sec("privacy", "Privacy", privacy)}
      ${byok}
      <div class="rt17-foot">Research only · Not investment advice · <span id="rt17-save" role="status">${_rt17Esc(_rt17SaveState || (signed ? "Saved to your account" : "Saved on this device"))}</span></div>
    </div></div>`;
}
function _rt17Render() {
  const el = document.getElementById("settingsOv"); if (!el) return;
  const open = [...el.querySelectorAll("details[open]")].map(d => d.id);
  const sc = el.querySelector(".rt17-scroll")?.scrollTop || 0;
  el.innerHTML = _rt17Html();
  el.querySelectorAll("details").forEach(d => { d.open = open.includes(d.id); });
  const s = el.querySelector(".rt17-scroll"); if (s) s.scrollTop = sc;
  if (el.querySelector("#ai-provider-status") && typeof _loadAiProviderStatus === "function") _loadAiProviderStatus();
}
function _rt17Close() { const el = document.getElementById("settingsOv"); if (el) { if (typeof _closeA11yDialog === "function") _closeA11yDialog(el); else el.remove(); } settingsOpen = false; }
function openSettings() {
  let el = document.getElementById("settingsOv");
  if (el) { _rt17Close(); return; }
  settingsOpen = true;
  el = document.createElement("div");
  el.id = "settingsOv"; el.className = "rt17-ov";
  el.setAttribute("role", "dialog"); el.setAttribute("aria-modal", "true"); el.setAttribute("aria-labelledby", "settings-title");
  el.innerHTML = _rt17Html();
  document.body.appendChild(el);
  if (el.querySelector("#ai-provider-status") && typeof _loadAiProviderStatus === "function") _loadAiProviderStatus();
  if (typeof _openA11yDialog === "function") _openA11yDialog(el, () => _rt17Close(), "button[aria-label='Close settings']");
  el.addEventListener("click", e => { if (e.target === el) _rt17Close(); });
  if (_rt17Signed() && _rt17ServerOk === null) _rt17LoadServer().then(() => _rt17Render());
}
function _rt17SetVis(id, on) { _rt17Prefs.layout.vis[id] = !!on; if (typeof togglePanelVis === "function") togglePanelVis(id, !!on); _rt17Save(); }
function _rt17Move(id, d) { const o = _rt17Prefs.layout.order, i = o.indexOf(id), j = i + d; if (i < 0 || j < 0 || j >= o.length) return; [o[i], o[j]] = [o[j], o[i]]; _rt17Save(); _rt17Render(); }
function _rt17SetDensity(v) { _rt17Prefs.layout.density = v; _rt17Save(); _rt17Render(); }
function _rt17ResetLayout() { const d = _rt17Default().layout; _rt17Prefs.layout = d; if (typeof resetPanelLayout === "function") { try { panelVis = { ...d.vis }; savePanelVis(); ["p1", "p2", "p3", "p4"].forEach(id => { const p = document.getElementById(id); if (p) { p.style.display = "flex"; p.style.order = ""; } }); } catch (e) {} } _rt17Save(); _rt17Render(); if (typeof showToast === "function") showToast("Layout reset", "var(--gn)"); }
function _rt17WlSync() { const wl = getActiveWl(); if (typeof saveWatchlists === "function") saveWatchlists(); _rt17Prefs.markets.watchlist = wl.tickers.slice(0, 50); _rt17Save(); try { if (typeof _paintWlGlance === "function") _paintWlGlance(); } catch (e) {} _rt17Render(); }
function _rt17WlMove(i, d) { const t = getActiveWl().tickers, j = i + d; if (j < 0 || j >= t.length) return; [t[i], t[j]] = [t[j], t[i]]; _rt17WlSync(); }
function _rt17WlDel(i) { getActiveWl().tickers.splice(i, 1); _rt17WlSync(); }
function _rt17WlAdd(v) {
  const t = String(v || "").trim().toUpperCase();
  if (!/^[A-Z0-9.=^\-]{1,15}$/.test(t)) { if (typeof showToast === "function") showToast("Enter a ticker like NVDA or BTC", "var(--gd)"); return; }
  const wl = getActiveWl(); if (!wl.tickers.includes(t)) { if (wl.tickers.length >= 50) return; wl.tickers.push(t); } _rt17WlSync();
}
function _rt17SetTz(z) { _rt17Prefs.markets.tz = z; _rt17Save(); try { if (typeof renderMain === "function") renderMain(); } catch (e) {} }
function _rt17AlertAdd(f) {
  const px = Number(String(f.px.value || "").replace(/[, ]/g, ""));
  if (!(px > 0) || !f.tk.value) { if (typeof showToast === "function") showToast("Pick a symbol and a price above 0", "var(--gd)"); return; }
  if (_rt17Prefs.alerts.price.length >= 20) return;
  _rt17Prefs.alerts.price.push({ tk: f.tk.value, op: f.op.value === "below" ? "below" : "above", px, on: true }); _rt17Save(); _rt17Render();
}
function _rt17AlertDel(i) { _rt17Prefs.alerts.price.splice(i, 1); _rt17Save(); _rt17Render(); }
function _rt17AlertRearm(i) { const a = _rt17Prefs.alerts.price[i]; if (a) { a.on = true; delete a.firedAt; } _rt17Save(); _rt17Render(); }
function _rt17SetBriefNote(on) { _rt17Prefs.alerts.dailyBrief = !!on; _rt17Save(); }
function _rt17SetFont(v) { _rt17Prefs.display.fontSize = v; _rt17Save(); _rt17Render(); }
function _rt17SetMotion(on) { _rt17Prefs.display.reduceMotion = !!on; _rt17Save(); }
function _rt17SetAskLen(v) { _rt17Prefs.ask.length = v; _rt17Save(); _rt17Render(); }
function _rt17SetAskFocus(v) { _rt17Prefs.ask.focus = v; _rt17Save(); _rt17Render(); }
function _rt17SetNews(k, on) { _rt17Prefs.newsletter[k] = !!on; _rt17Save(); _rt17Render(); }
function _rt17Download(name, obj) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(obj, null, 2)], { type: "application/json" }));
  a.download = name; document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
}
async function _rt17Export() {
  const local = { prefs: _rt17Prefs, watchlists: typeof watchlists !== "undefined" ? watchlists : [] };
  if (_rt17Signed()) {
    try { const r = await fetch("/api/account/export", { credentials: "include" }); if (!r.ok) throw new Error(String(r.status)); const d = await r.json(); _rt17Download("dispatch-my-data.json", { ...d, device: local }); return; }
    catch (e) { if (typeof showToast === "function") showToast("Couldn't reach your account; exported this device's data", "var(--gd)"); }
  }
  _rt17Download("dispatch-my-data.json", { exportedAt: new Date().toISOString(), account: null, device: local });
}
async function _rt17Delete() {
  const inp = document.getElementById("rt17-del-in"), msg = document.getElementById("rt17-del-msg");
  if (!inp || inp.value !== "DELETE") return;
  if (msg) msg.textContent = "Deleting…";
  try {
    const r = await fetch("/api/account/delete", { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ confirm: "DELETE" }) });
    const d = await r.json().catch(() => ({}));
    if (r.ok) { try { localStorage.removeItem(RT17_PREFS_KEY); } catch (e) {} location.href = "/"; return; }
    if (msg) msg.innerHTML = _rt17Esc(d.error || "Couldn't delete the account.") + (d.code === "BILLING_ACTIVE" && typeof _userBilling !== "undefined" && _userBilling ? ` <button type="button" class="rt17-btn" onclick="_openBillingPortal()">Manage billing</button>` : "");
  } catch (e) { if (msg) msg.textContent = "Couldn't reach the server. Nothing was deleted."; }
}
function _rt17ClearLocal() { try { localStorage.removeItem(RT17_PREFS_KEY); } catch (e) {} _rt17Prefs = _rt17Default(); _rt17Apply(); _rt17Render(); if (typeof showToast === "function") showToast("Settings cleared on this device", "var(--gn)"); }
(function _rt17Css() {
  try {
    if (document.getElementById("ui17-css")) return;
    const s = document.createElement("style"); s.id = "ui17-css";
    s.textContent = `.rt17-ov{position:fixed;inset:0;background:rgba(0,0,0,.8);z-index:700;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(6px)}
.rt17-panel{background:var(--b2);border:1px solid var(--b3);border-radius:14px;width:92%;max-width:560px;max-height:88vh;display:flex;flex-direction:column;box-shadow:var(--shadow-lg);overflow:hidden}
.rt17-top{display:flex;justify-content:space-between;align-items:center;padding:14px 18px;border-bottom:1px solid var(--gb)}
.rt17-top h2{margin:0;font:800 18px var(--sn)}
.rt17-x{background:var(--b3);border:0;color:var(--t2);border-radius:50%;width:44px;height:44px;font-size:20px;cursor:pointer}
.rt17-scroll{overflow-y:auto;padding:6px 18px 18px;-webkit-overflow-scrolling:touch}
.rt17-sec{border-bottom:1px solid var(--gb)}
.rt17-sec>summary{list-style:none;cursor:pointer;min-height:48px;display:flex;align-items:center;justify-content:space-between;font:700 12px var(--mn);letter-spacing:.14em;text-transform:uppercase;color:var(--gd)}
.rt17-sec>summary::-webkit-details-marker{display:none}
.rt17-sec>summary::after{content:"▾";color:var(--t3)}.rt17-sec[open]>summary::after{content:"▴"}
.rt17-body{padding:0 0 14px;display:flex;flex-direction:column;gap:8px}
.rt17-row{display:flex;align-items:center;justify-content:space-between;gap:10px;min-height:44px;border-bottom:1px solid rgba(255,255,255,.04);flex-wrap:wrap}
.rt17-l{font:600 14px var(--sn);color:var(--tx)}.rt17-v{font:500 13px var(--mn);color:var(--t2);overflow-wrap:anywhere}
.rt17-sub{display:block;font:500 11px var(--mn);color:var(--t3)}
.rt17-h{font:700 11px var(--mn);color:var(--t2);letter-spacing:.1em;text-transform:uppercase;margin-top:8px}
.rt17-note{font:500 12px/1.5 var(--sn);color:var(--t3)}
.rt17-btn{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 14px;background:var(--b3);border:1px solid var(--gb);border-radius:8px;color:var(--tx);font:700 12px var(--mn);text-decoration:none;cursor:pointer;box-sizing:border-box}
.rt17-btn-gold{background:var(--gd);color:var(--bg);border-color:var(--gd)}
.rt17-btn-danger{background:transparent;border-color:var(--rd);color:var(--rd)}.rt17-btn[disabled]{opacity:.45;cursor:not-allowed}
.rt17-danger{color:var(--rd)}
.rt17-seg{display:flex;gap:6px;flex-wrap:wrap}.rt17-seg button{min-height:44px;min-width:64px;padding:0 12px;border-radius:8px;border:1px solid var(--b4);background:transparent;color:var(--t2);font:700 12px var(--mn);cursor:pointer}
.rt17-seg button.on{border-color:var(--gd);background:var(--gdG);color:var(--gd)}
.rt17-ud{display:inline-flex;gap:6px;align-items:center}.rt17-ud button{min-width:44px;min-height:44px;border-radius:8px;border:1px solid var(--b4);background:transparent;color:var(--t2);font-size:14px;cursor:pointer}.rt17-ud button[disabled]{opacity:.3}
.rt17-tog{cursor:pointer;position:relative}.rt17-tog input{position:absolute;opacity:0;width:1px;height:1px}
.rt17-sw{width:44px;height:26px;border-radius:26px;background:var(--b4);position:relative;flex-shrink:0;transition:.2s}.rt17-sw::after{content:"";position:absolute;top:3px;left:3px;width:20px;height:20px;border-radius:50%;background:#fff;transition:.2s}
.rt17-tog input:checked+.rt17-sw{background:var(--gn)}.rt17-tog input:checked+.rt17-sw::after{left:21px}.rt17-tog input:focus-visible+.rt17-sw{outline:2px solid var(--gd)}
.rt17-tog-inline{display:inline-flex;align-items:center;gap:10px;min-height:44px;font:600 14px var(--sn);color:var(--tx)}.rt17-tog-inline input{width:20px;height:20px;accent-color:var(--gd)}
.rt17-add{display:flex;gap:8px;flex-wrap:wrap}.rt17-add input,.rt17-add select,.rt17-sel{min-height:44px;flex:1 1 120px;background:var(--b1);color:var(--tx);border:1px solid var(--b4);border-radius:8px;padding:0 10px;font:600 14px var(--mn);box-sizing:border-box;min-width:0}
.rt17-body>.rt17-sel{width:100%;flex:none;height:44px}
.rt17-soon{opacity:.75}.rt17-badge{font:700 10px var(--mn);letter-spacing:.08em;color:var(--t3);border:1px dashed var(--b4);border-radius:5px;padding:3px 7px}
.rt17-soon .rt17-sub{flex-basis:100%}
.rt17-foot{font:500 11px var(--mn);color:var(--t3);padding-top:14px;text-align:center}
@media (max-width:600px){.rt17-ov{align-items:flex-end}.rt17-panel{width:100%;max-width:none;max-height:92vh;border-radius:14px 14px 0 0}.rt17-scroll{padding-bottom:calc(18px + env(safe-area-inset-bottom))}}
body.td-compact .gc,body.td-compact .panel-body,body.td-compact .tt td{padding-top:4px!important;padding-bottom:4px!important}
body.td-compact .home-sec,body.td-compact .gd-card{margin-bottom:8px!important}
body.td-zoomed #app,body.td-zoomed #main{zoom:var(--td-zoom,1)}
body.td-reduce-motion *,body.td-reduce-motion *::before,body.td-reduce-motion *::after{animation:none!important;transition:none!important}`;
    document.head.appendChild(s);
  } catch (e) {}
})();
try { if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", _rt17Apply); else _rt17Apply(); } catch (e) {}

'''

APP_EDITS = [
    ("module header rt16 -> rt17",
     "// REALTIME PRICE LAYER (rt16) — browser-direct, free, keyless.",
     "// REALTIME PRICE LAYER (rt17) — browser-direct, free, keyless."),
    ("/api/me: keep email, load account prefs",
     "      _userAdmin=d.isAdmin===true;\n    }\n  }catch(e){}\n  await editorialReady;",
     "      _userAdmin=d.isAdmin===true;\n      window._tdMeEmail=typeof d.email===\"string\"?d.email:\"\";\n    }\n  }catch(e){}\n  try{ if(typeof _rt17LoadServer===\"function\") _rt17LoadServer(); }catch(e){}\n  await editorialReady;"),
    ("frequency: fixed, stored value ignored",
     "let updateFreq=parseInt(localStorage.getItem('td_freq')||'60');",
     "let updateFreq=60; // rt17: no user frequency; streams are live, polls use the fixed safe cadence\ntry{localStorage.removeItem('td_freq')}catch(e){}"),
    ("saveFreq: no-op",
     "function saveFreq(){localStorage.setItem('td_freq',String(updateFreq));}",
     "function saveFreq(){}"),
    ("old settings renamed (replaced by rt17 openSettings)",
     "function openSettings(){\n  let el=document.getElementById('settingsOv');",
     "function _openSettingsLegacy(){\n  let el=document.getElementById('settingsOv');"),
    ("setUpdateFreq: removed",
     "function setUpdateFreq(freq){\n  updateFreq=freq;saveFreq();\n  _restartIntervals();\n  // Single re-open refreshes settings panel (was double-called → flicker)\n  if(typeof openSettings===\"function\")openSettings();\n  showToast(freq===0?'Manual updates only':`Updates every ${freq}s`,'var(--bl)');\n}",
     "function setUpdateFreq(){ /* rt17: removed — prices are as live as each source allows */ }"),
    ("restart: skip hidden tabs",
     "    _priceInterval=setInterval(fetchLivePrices, freq * 1000);",
     "    _priceInterval=setInterval(()=>{ if(!document.hidden) fetchLivePrices(); }, freq * 1000);"),
    ("boot: skip hidden tabs",
     "_priceInterval=setInterval(fetchLivePrices, effectivePriceFreq * 1000);",
     "_priceInterval=setInterval(()=>{ if(!document.hidden) fetchLivePrices(); }, effectivePriceFreq * 1000);"),
    ("chat: Ask hints",
     "        knownTickers: _chatKnownTickers()\n      })",
     "        knownTickers: _chatKnownTickers(),\n        hints: typeof _rt17AskHints === \"function\" ? _rt17AskHints() : undefined\n      })"),
    ("_fmtAsOf: 24h in the chosen timezone",
     '    return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });',
     '    return new Date(ts).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false, timeZone: _rt17Tz() });'),
    ("_rt16Hms follows the chosen timezone",
     'function _rt16Hms(ts) {\n  const d = new Date(ts); if (isNaN(d)) return "—";\n  const p = n => String(n).padStart(2, "0");\n  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;\n}',
     'function _rt16Hms(ts) {\n  const d = new Date(ts); if (isNaN(d)) return "—";\n  return _fmtAsOf(d.getTime());\n}'),
    ("rt17 block before the footer clock",
     "// Footer clock: once a second, text only, paused while the tab is hidden.",
     BLOCK + "// Footer clock: once a second, text only, paused while the tab is hidden."),
]

INDEX_EDITS = [
    ("cache-bust app.js chat15 -> chat16", '/app.js?v=chat15"', '/app.js?v=chat16"'),
]

def load(path):
    with open(path, "rb") as f:
        raw = f.read().decode("utf-8")
    crlf = "\r\n" in raw
    return raw.replace("\r\n", "\n"), crlf


def apply(text, edits, label, errors):
    for e in edits:
        name, old, new = e[0], e[1], e[2]
        want = e[3] if len(e) > 3 else 1
        n = text.count(old)
        if n != want:
            errors.append(f"{label}: '{name}' anchor matched {n} times (need exactly {want})")
            continue
        text = text.replace(old, new)
    return text


def node_check(js_text, label, errors, required):
    node = shutil.which("node")
    if not node:
        if required:
            errors.append(f"{label}: node not found on PATH for `node --check` (use --skip-node-check to override)")
        else:
            print(f"WARN: node not found; {label} not syntax-checked")
        return
    fd, tmp = tempfile.mkstemp(suffix=".js")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(js_text.encode("utf-8"))
        r = subprocess.run([node, "--check", tmp], capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            errors.append(f"{label}: node --check failed: {(r.stderr or r.stdout).strip()[:400]}")
    finally:
        try: os.remove(tmp)
        except OSError: pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dir", default=".")
    a = ap.parse_args()
    app_p, idx_p = (os.path.join(a.dir, n) for n in ("app.js", "index.html"))
    for p in (app_p, idx_p):
        if not os.path.isfile(p):
            sys.exit(f"ABORT: {p} not found — nothing written")
    app, app_crlf = load(app_p)
    idx, idx_crlf = load(idx_p)
    if MARKER in app or 'app.js?v=chat16"' in idx:
        sys.exit("ABORT: rt17 already applied (marker / chat16 found) — refusing to run twice; nothing written")
    if PREV_MARKER not in app or 'app.js?v=chat15"' not in idx:
        sys.exit("ABORT: these are not the chat15 (rt16) files — nothing written")
    errors = []
    new_app = apply(app, APP_EDITS, "app.js", errors)
    new_idx = apply(idx, INDEX_EDITS, "index.html", errors)
    if not errors:
        if (new_app.count(MARKER) != 1 or PREV_MARKER in new_app or new_app.count("function openSettings(") != 1
                or "td_freq')||" in new_app or "PRICE UPDATE FREQUENCY" in new_app.split("function _openSettingsLegacy", 1)[0]
                or new_idx.count('app.js?v=chat16"') != 1):
            errors.append("post-edit sanity check failed")
        node_check(new_app, "app.js", errors, required=False)
    if errors:
        print("ABORT — no files written:")
        for e in errors: print("  -", e)
        sys.exit(1)
    print(f"OK: {len(APP_EDITS)} app.js edits, {len(INDEX_EDITS)} index.html edit verified (app.js {len(new_app)-len(app):+d} chars); server.js not touched")
    if a.check:
        print("--check: dry run, nothing written"); return
    tmps = []
    try:
        for p, text, crlf in ((app_p, new_app, app_crlf), (idx_p, new_idx, idx_crlf)):
            if crlf: text = text.replace("\n", "\r\n")
            tmp = p + ".rt17.tmp"
            with open(tmp, "wb") as f: f.write(text.encode("utf-8"))
            tmps.append((tmp, p))
    except Exception as e:
        for tmp, _ in tmps:
            try: os.remove(tmp)
            except OSError: pass
        sys.exit(f"ABORT: could not stage output ({e}) — no files written")
    for tmp, p in tmps: os.replace(tmp, p)
    print("Written: app.js, index.html (app.js?v=chat16)")


if __name__ == "__main__":
    main()
