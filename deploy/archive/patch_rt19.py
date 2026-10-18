#!/usr/bin/env python3
"""patch_rt19.py — chat17 -> chat18. Stacks on rt18 output. Client-only.
Usage: python3 patch_rt19.py [--check] <dir containing app.js + index.html>
"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt19)' in s: die('rt19 already applied')
if 'REALTIME PRICE LAYER (rt18)' not in s: die('base is not rt18 output')
if 'app.js?v=chat17' not in h: die('index.html is not chat17')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))

R('marker', '// REALTIME PRICE LAYER (rt18)', '// REALTIME PRICE LAYER (rt19)')
# 1. Settings for guests + /settings/ route
R('guest more settings',
  '          ${_navIco(id)}<span>${lb}</span>\n        </button>`).join("")}`\n    : `${NAV_GROUPS.map(gr => `',
  '          ${_navIco(id)}<span>${lb}</span>\n        </button>`).join("")}\n      <div class="more-nav-grp">Account</div>\n      <button class="more-nav-item" onclick="closeMoreNav();openSettings()">\n        ${_navIco("settings")}<span>Settings</span>\n      </button>`\n    : `${NAV_GROUPS.map(gr => `')
R('settings route after boot', '  _finishAppBoot();\n}\n\nfunction _finishAppBoot(){',
  '  _finishAppBoot();\n  if (window._rt19WantSettings) { window._rt19WantSettings = false; setTimeout(() => { try { if (!document.getElementById("settingsOv")) openSettings(); history.replaceState(history.state, "", "/settings/"); } catch (e) {} }, 0); }\n}\n\nfunction _finishAppBoot(){')
R('settings close restores url', 'function _rt17Close() { const el = document.getElementById("settingsOv"); if (el) {',
  'function _rt17Close() { _rt19AiCache = null; try { if (/^\\/settings\\/?$/.test(location.pathname)) history.replaceState(history.state, "", "/"); } catch (e) {} const el = document.getElementById("settingsOv"); if (el) {')
# 2. Newsletter
R('newsletter',
  '''  const news = `${_rt17Tog("Daily newsletter", P.newsletter.daily, "_rt17SetNews('daily',this.checked)", P.newsletter.daily ? "Saved — sending starts soon" : "")}
    ${_rt17Tog("Weekly newsletter", P.newsletter.weekly, "_rt17SetNews('weekly',this.checked)", P.newsletter.weekly ? "Saved — sending starts soon" : "")}
    <div class="rt17-note">We'll save your choice now. Newsletter emails haven't started yet.</div>`;''',
  '''  const news = signed
    ? `${email ? `<div class="rt17-row"><span class="rt17-l">Send to</span><span class="rt17-v">${_rt17Esc(email)}</span></div>` : ""}
    ${_rt17Tog("Daily newsletter", P.newsletter.daily, "_rt17SetNews('daily',this.checked)")}
    ${_rt17Tog("Weekly newsletter", P.newsletter.weekly, "_rt17SetNews('weekly',this.checked)")}
    <div class="rt17-note" role="status">${(P.newsletter.daily || P.newsletter.weekly) ? "Your choice is saved. Sending starts soon." : "Pick daily, weekly or both. Sending starts soon."}</div>`
    : `<div class="rt17-note">Sign in to subscribe. Newsletters go to your account email.</div>
    <a class="rt17-btn rt17-btn-gold" href="/__auth/login">Sign in</a><a class="rt17-btn" href="/__auth/register">Create free account</a>`;''')
# 3. prefs: after first paint, 5 s timeout, single in-flight request
R('prefs base rename', 'async function _rt17LoadServer() {', 'async function _rt17LoadServerBase_rt19() {')
R('prefs timeout', '    const r = await fetch("/api/prefs", { credentials: "include" });', '    const r = await fetch("/api/prefs", { credentials: "include", signal: AbortSignal.timeout(5000) });')
R('prefs after paint', 'try{ if(typeof _rt17LoadServer==="function") _rt17LoadServer(); }catch(e){}',
  'try{ if(typeof _rt17LoadServer==="function") requestAnimationFrame(()=>setTimeout(()=>_rt17LoadServer(),0)); }catch(e){}')
# 4. ai-status once per open
R('ai once (render)', '  const s = el.querySelector(".rt17-scroll"); if (s) s.scrollTop = sc;\n  if (el.querySelector("#ai-provider-status") && typeof _loadAiProviderStatus === "function") _loadAiProviderStatus();',
  '  const s = el.querySelector(".rt17-scroll"); if (s) s.scrollTop = sc;\n  _rt19AiStatus();')
R('ai once (open)', '  document.body.appendChild(el);\n  if (el.querySelector("#ai-provider-status") && typeof _loadAiProviderStatus === "function") _loadAiProviderStatus();',
  '  document.body.appendChild(el);\n  _rt19AiCache = null; _rt19AiStatus();')
# 5. wording + dead frequency code
W = [
 ('<span>Gold</span><em>Live gold dashboard</em>', '<span>Gold</span><em>Gold dashboard</em>'),
 ('"AI credits empty — free desk brief from live tape (no LLM)"', '"AI credits empty — free desk brief from market data (no LLM)"'),
 ('Finnhub (real-time US equities)', 'Finnhub (US equities, may be delayed)'),
 ("Generate today's house view from live free data", "Generate today's house view from free market data"),
 ('Interactive desk letter · free live data', 'Interactive desk letter · free market data'),
 ('Bloomberg-style desk edition from live free feeds', 'Bloomberg-style desk edition from free market feeds'),
 ('A broadsheet built from <strong>live free feeds</strong>', 'A broadsheet built from <strong>free market feeds</strong>'),
 ("Generate today's desk brief from live tape.", "Generate today's desk brief from market data."),
 ('Book first · live tape · ink ledger desk', 'Book first · market tape · ink ledger desk'),
 ('"Live gold structure · levels, sessions, volatility and macro"', '"Gold structure · levels, sessions, volatility and macro"'),
 ('Built from live Yahoo tape', 'Built from Yahoo market data (may be delayed)'),
 ('Lens Engine fuses live Yahoo quote', 'Lens Engine fuses the latest Yahoo quote'),
 ('Lens Engine fuses live quote ·', 'Lens Engine fuses latest quote ·'),
 ('LENS ENGINE — FUSING LIVE DATA + AI…', 'LENS ENGINE — FUSING MARKET DATA + AI…'),
 ('Lens Engine — fusing live data + AI reasoning…', 'Lens Engine — fusing market data + AI reasoning…'),
 ('Fetching live market data…', 'Fetching market data…'),
 ('Tap to load live market data', 'Tap to load market data'),
 ('SYNCING LIVE PRICES…', 'SYNCING PRICES…'),
 ('uses this terminal’s live quotes', 'uses this terminal’s latest quotes'),
 ('Premium · live quotes, newsroom & regime', 'Premium · latest quotes, newsroom & regime'),
 ("showToast('Live updates paused'", "showToast('Price updates paused'"),
 ('Alerts trigger an in-app notification when live price data matches', 'Alerts trigger an in-app notification when the latest price matches'),
]
for i, (a, b) in enumerate(W): R(f'wording {i}', a, b)
R('wording fetching x2', 'FETCHING LIVE DATA', 'FETCHING MARKET DATA', 2)
R('live dot titles', '\'<span class="htec-live-dot" title="Near real-time"></span>\'', '`<span class="htec-live-dot" title="${_rt19LiveTitle(d)}"></span>`', 2)
R('dead saveFreq', 'function saveFreq(){}\n', '')
R('dead setUpdateFreq', 'function setUpdateFreq(){ /* rt17: removed — prices are as live as each source allows */ }\n', '')
# 6. news-scores: one quiet retry with backoff, then cool down
R('news-scores retry', '    const res=await fetch("/api/news-scores",{method:"POST",credentials:"include",headers:{"Content-Type":"application/json"},body:JSON.stringify({headlines:pending.map(n=>({id:_newsScoreId(n),title:n.x||"",summary:n.desc||"",tickers:_tagNewsHeadline(`${n.x||""} ${n.desc||""}`).slice(0,4)}))})});',
  '    const _rt19Body=JSON.stringify({headlines:pending.map(n=>({id:_newsScoreId(n),title:n.x||"",summary:n.desc||"",tickers:_tagNewsHeadline(`${n.x||""} ${n.desc||""}`).slice(0,4)}))});\n    const res=await _rt19NewsScoresFetch(_rt19Body);')
R('news-scores cooldown gate', '  if(!pending.length||!_isPremium()||_newsScoreLoading){',
  '  if(!pending.length||!_isPremium()||_newsScoreLoading||Date.now()<_rt19NsCool()){')
# 7. polish
R('alert toast', '  try { if (typeof showToast === "function") showToast(`${title} — ${body}`, "var(--gd)"); } catch (e) {}',
  '  try { _rt19AlertToast(title, body); } catch (e) {}')
R('seg aria-pressed', '`<div class="rt17-seg" role="radiogroup" aria-label="${name}">${opts.map(([v, l]) => `<button type="button" role="radio" aria-checked="${cur === v}" class="${cur === v ? "on" : ""}" onclick="${onchange}(\'${v}\')">${l}</button>`).join("")}</div>`',
  '`<div class="rt17-seg" role="group" aria-label="${name}">${opts.map(([v, l]) => `<button type="button" aria-pressed="${cur === v}" class="${cur === v ? "on" : ""}" onclick="${onchange}(\'${v}\')">${l}</button>`).join("")}</div>`')
R('delete cancel', '<button type="button" class="rt17-btn rt17-btn-danger" id="rt17-del-btn" disabled onclick="_rt17Delete()">Delete my account</button>',
  '<button type="button" class="rt17-btn rt17-btn-danger" id="rt17-del-btn" disabled onclick="_rt17Delete()">Delete my account</button><button type="button" class="rt17-btn" onclick="_rt19DelCancel()">Cancel</button>')

BLOCK = r"""// ── rt19: settings route, prefs/ai-status loading, honest live titles, quiet news scores, polish ──
window._rt19WantSettings = /^\/settings\/?$/.test(location.pathname) || /[?&]settings(=|&|$)/.test(location.search);
let _rt19PrefsP = null;
function _rt17LoadServer() {
  if (_rt19PrefsP) return _rt19PrefsP;
  _rt19PrefsP = _rt17LoadServerBase_rt19().finally(() => {
    _rt19PrefsP = null;
    try { if (document.getElementById("settingsOv")) _rt17Render(); } catch (e) {}
  });
  return _rt19PrefsP;
}
let _rt19AiCache = null, _rt19AiP = null;
function _rt19AiHtml(status) {
  const esc = typeof _escHtml === "function" ? _escHtml : String;
  const providers = status.providers || [];
  const configured = providers.filter(p => p.configured);
  const order = (status.fallbackOrder || []).map(id => providers.find(p => p.id === id)?.label || id);
  return `<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px">${providers.map(p => `<span style="font-family:var(--mn);font-size:9px;padding:5px 7px;border:1px solid ${p.configured ? "rgba(34,197,94,.3)" : "var(--b4)"};border-radius:5px;color:${p.configured ? "var(--gn)" : "var(--t3)"}">${esc(p.label)} · ${p.configured ? (p.mode === "connection" ? "CONNECTED" : "CONFIGURED") : "ADD KEY"}</span>`).join("")}</div>
    <div style="font-family:var(--mn);font-size:10px;color:var(--t3);line-height:1.6">${configured.length ? `Automatic fallback: ${order.map(esc).join(" → ")}.` : "No AI provider is configured."} Provider keys stay server-side and are never sent to the browser.</div>`;
}
/** ai-status is fetched once per settings open; re-renders reuse the cached markup. */
function _rt19AiStatus() {
  const t = document.getElementById("ai-provider-status"); if (!t) return;
  if (_rt19AiCache != null) { t.innerHTML = _rt19AiCache; return; }
  if (_rt19AiP) return;
  _rt19AiP = fetch("/api/ai-status", { credentials: "include", signal: AbortSignal.timeout(8000) })
    .then(r => { if (!r.ok) throw new Error(String(r.status)); return r.json(); })
    .then(st => { _rt19AiCache = _rt19AiHtml(st); })
    .catch(() => { _rt19AiCache = '<div style="font-family:var(--mn);font-size:10px;color:var(--rd)">AI provider status is temporarily unavailable.</div>'; })
    .finally(() => { _rt19AiP = null; const t2 = document.getElementById("ai-provider-status"); if (t2 && _rt19AiCache != null) t2.innerHTML = _rt19AiCache; });
}
/** Accurate tooltip for the green dot: streamed vs polled, with source and time. */
function _rt19LiveTitle(d) {
  const src = String((d && d.src) || "");
  const streamed = /-ws$|stream/i.test(src);
  const lbl = typeof _quoteSourceLabel === "function" ? _quoteSourceLabel(src) : src;
  const t = d && d.asOf && typeof _fmtAsOf === "function" ? ` · as of ${_fmtAsOf(d.asOf)}` : "";
  return (streamed ? `Streaming · ${lbl}` : `Recent quote · ${lbl} · refreshed by polling`) + t;
}
/** /api/news-scores: retry once after a short backoff on 5xx/network, then cool down 5 min. No console output. */
function _rt19NsCool() { try { return Number(sessionStorage.getItem("td_ns_cool")) || 0; } catch (e) { return 0; } }
async function _rt19NewsScoresFetch(body) {
  const go = () => fetch("/api/news-scores", { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body, signal: AbortSignal.timeout(30000) });
  let res = null;
  try { res = await go(); } catch (e) { res = null; }
  if (!res || res.status >= 500) {
    await new Promise(r => setTimeout(r, 1500 + Math.random() * 1500));
    try { res = await go(); } catch (e) { res = null; }
  }
  if (!res || res.status >= 500) {
    try { sessionStorage.setItem("td_ns_cool", String(Date.now() + 5 * 60 * 1000)); } catch (e) {}
    return { ok: false, status: res ? res.status : 0, json: async () => ({}) };
  }
  return res;
}
function _rt19AlertToast(title, body) {
  let el = document.getElementById("rt19-alert");
  if (!el) {
    el = document.createElement("div"); el.id = "rt19-alert"; el.setAttribute("role", "alert");
    document.body.appendChild(el);
  }
  const esc = typeof _escHtml === "function" ? _escHtml : String;
  el.innerHTML = `<div class="rt19-at"><strong>${esc(title)}</strong><span>${esc(body)}</span></div><button type="button" class="rt19-ax" aria-label="Dismiss alert">×</button>`;
  el.querySelector(".rt19-ax").onclick = () => { el.classList.remove("show"); };
  el.classList.add("show");
  clearTimeout(el._t); el._t = setTimeout(() => el.classList.remove("show"), 8000);
}
function _rt19DelCancel() {
  const inp = document.getElementById("rt17-del-in"), btn = document.getElementById("rt17-del-btn"), msg = document.getElementById("rt17-del-msg");
  if (inp) inp.value = ""; if (btn) btn.disabled = true; if (msg) msg.textContent = "Cancelled. Nothing was deleted.";
  const sec = document.getElementById("rt17-privacy"); if (sec) sec.open = false;
}
(function _rt19Css() {
  if (document.getElementById("rt19-css")) return;
  const st = document.createElement("style"); st.id = "rt19-css";
  st.textContent = `
.more-nav-hdr{position:sticky;top:0;z-index:5;background:var(--b1,#0E0E10)!important;padding:14px 16px 10px;box-shadow:0 6px 10px -6px rgba(0,0,0,.7)}
.more-nav-item{position:relative;z-index:0}
#rt19-alert{position:fixed;left:50%;bottom:calc(84px + env(safe-area-inset-bottom,0px));transform:translate(-50%,20px);opacity:0;pointer-events:none;z-index:900;display:flex;align-items:center;gap:10px;max-width:min(92vw,460px);background:var(--b2,#151517);border:1px solid var(--gd,#d4a64a);border-radius:10px;padding:8px 6px 8px 14px;box-shadow:0 10px 30px rgba(0,0,0,.6);transition:transform .2s,opacity .2s}
#rt19-alert.show{opacity:1;transform:translate(-50%,0);pointer-events:auto}
.rt19-at{display:flex;flex-direction:column;gap:2px;font-size:13px;color:var(--tx,#eee)}.rt19-at span{color:var(--t2,#bbb);font-size:12px}
.rt19-ax{flex:none;width:44px;height:44px;border:0;border-radius:8px;background:transparent;color:var(--t2,#bbb);font-size:20px;cursor:pointer}`;
  document.head.appendChild(st);
})();
"""
# legacy settings overlay (held the dead PRICE UPDATE FREQUENCY picker) — exact slice, verified
LS = s.find('function _openSettingsLegacy(){')
LE = s.find('\nfunction togglePanelVis(id,show){', LS)
if s.count('function _openSettingsLegacy(){') != 1 or LS < 0 or LE < 0: die('legacy settings slice not found')
legacy = s[LS:LE]
if 'PRICE UPDATE FREQUENCY' not in legacy or legacy.count('\nfunction ') != 0 or len(legacy) > 12000: die('legacy settings slice does not look as expected')
if s.count('_openSettingsLegacy') != 1: die('legacy settings is still referenced')
s = s[:LS] + s[LE + 1:]
R('rt19 block', 'function _rt17Default() {', BLOCK + 'function _rt17Default() {')
for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
# index.html
HE = [('pause title', 'title="Pause/resume live updates"', 'title="Pause/resume price updates"'),
      ('favicon', '<link rel="icon" type="image/svg+xml" href="/logo-mark.svg?v=78d3bf40eeefab58">',
       '<link rel="icon" type="image/svg+xml" href="/logo-mark.svg?v=78d3bf40eeefab58">\n<link rel="shortcut icon" type="image/svg+xml" href="/logo-mark.svg?v=78d3bf40eeefab58">'),
      ('cache bust', 'app.js?v=chat17', 'app.js?v=chat18')]
for name, old, new in HE:
    if h.count(old) != 1: die(f"index '{name}' matched {h.count(old)} times")
    h = h.replace(old, new)
for bad in ['PRICE UPDATE FREQUENCY', 'title="Near real-time"', 'Live gold dashboard', 'real-time US equities']:
    if bad in s: die('postcondition: still present: ' + bad)
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + legacy removal ({len(legacy)} chars) + {len(HE)} index edits; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
