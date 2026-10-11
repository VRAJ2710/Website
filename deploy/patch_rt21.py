#!/usr/bin/env python3
"""patch_rt21.py — chat19 -> chat20. Stacks on rt20 output (t20). Client-only (+ one index.html style rule).
Usage: python3 patch_rt21.py [--check] <dir containing app.js + index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt21)' in s: die('rt21 already applied')
if 'REALTIME PRICE LAYER (rt20)' not in s: die('base is not rt20 output')
if 'app.js?v=chat19' not in h: die('index.html is not chat19')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt20)', '// REALTIME PRICE LAYER (rt21)')
# 1. honest wording (LIVE stays only on stream badges/counts)
W = [
 ('"◆ LIVE PULSE · AI UNAVAILABLE"', '"◆ PULSE · AI UNAVAILABLE"'),
 (': "◆ LIVE PULSE";', ': "◆ PULSE";'),
 ('The local LIVE PULSE context remains available.', 'The local PULSE context remains available.'),
 ('<div class="sec-label-v2">Live Detections</div>', '<div class="sec-label-v2">Detections</div>'),
 ('"Free brief uses live free data only — no LLM synthesis"', '"Free brief uses free market data — no LLM synthesis"'),
 ('${nLive}/${s.tks.length} live</div>', '${nLive}/${s.tks.length} updated</div>'),
 ('`VIX live · ${nLive} chg inputs`', '`VIX · ${nLive} chg inputs`'),
 ('`${nLive} live inputs · VIX pending`', '`${nLive} inputs · VIX pending`'),
 ('Background only: live prices come from the feeds above.', 'Background only: prices come from the feeds above.'),
 ('not used for live prices', 'not used for prices'),
 ('"Awaiting live tape. "', '"Awaiting prices. "'),
 ('"Awaiting live tape for heatmap leaders."', '"Awaiting prices for heatmap leaders."'),
 ('stress-test your thesis against live data', 'stress-test your thesis against market data'),
 ('Live prices when feed syncs', 'Prices when the feed syncs'),
 ('all tracked assets with live prices', 'all tracked assets with latest prices'),
 ('Nothing in your book has a live mark yet.', 'Nothing in your book has a current price yet.'),
 ('No live desk names yet this session.', 'No priced desk names yet this session.'),
 ('Session movers · live desk names', 'Session movers · desk names'),
 (' · live regime now ${_escHtml(re.label)}', ' · current regime ${_escHtml(re.label)}'),
 ('⚡ Live Markets${dynCount', '⚡ All markets${dynCount'),
 ('>Live index strips · lead wire', '>Index strips · lead wire'),
 ('aria-label="Live US market strip"', 'aria-label="US market strip"'),
]
for i, (a, b) in enumerate(W): R(f'wording {i}', a, b)
R('awaiting feed (all)', 'awaiting live feed', 'awaiting feed', None)
R('portfolio priced', '${liveN < portfolio.length ? ` (${liveN} live)` : ""}', '${liveN < portfolio.length ? ` (${liveN} priced)` : ""}')
R('stored brief wording', '  out._rt18Day = day;\n  return out;', '  _rt21BriefWords(out);\n  out._rt18Day = day;\n  return out;')
# 2. destructive actions
R('clear confirm', '<button type="button" class="rt17-btn" onclick="_rt17ClearLocal()">Clear settings on this device</button>',
  '<div id="rt21-clr" class="rt21-clr"><button type="button" class="rt17-btn" onclick="_rt21ClearAsk()">Clear settings on this device</button></div>')
R('alert undo', '<button type="button" aria-label="Delete alert" onclick="_rt17AlertDel(${i})">✕</button>', '<button type="button" aria-label="Delete alert" onclick="_rt21AlertDel(${i},this)">✕</button>')
# 3. news-scores unavailable (rt21s)
R('ns unavailable', '    if(res.ok&&Array.isArray(data.scores)){',
  '    if(res.ok&&data&&data.unavailable){\n      _newsScoreState="unavailable";\n      try{sessionStorage.setItem("td_ns_cool",String(Date.now()+5*60*1000));}catch(e){}\n    }else if(res.ok&&Array.isArray(data.scores)){')
# 4. polish
R('tape awaiting', '`<span class="ti" style="color:var(--t3)">Awaiting price feed — tap ⟳ to sync</span>`',
  '(_rt20Booting() ? `<span class="ti" style="color:var(--t3);letter-spacing:0.12em">SYNCING PRICES…</span>` : `<span class="ti" style="color:var(--t3)">No prices yet — tap ⟳ to sync</span>`)')
R('glance status', 'const hasValue = retained && d.p != null && d.p !== "—";',
  'const hasValue = (retained || ["cached", "closed", "delayed", "proxy", "stale"].includes(d.status)) && d.p != null && d.p !== "—";')
R('glance loading state', 'const state = hasValue ? d.p : (retained ? (d.label || "UNAVAILABLE") : "UNAVAILABLE");',
  'const state = hasValue ? d.p : (_rt20Booting() ? "…" : retained ? (d.label || "UNAVAILABLE") : "UNAVAILABLE");')
R('more dup header', '`<div class="more-nav-grp">All sections</div>${PUBLIC_NAV_ITEMS', '`${PUBLIC_NAV_ITEMS')
R('toast x removes node', 'el.querySelector(".rt19-ax").onclick = () => { el.classList.remove("show"); };',
  'el.querySelector(".rt19-ax").onclick = () => { clearTimeout(el._t); el.remove(); };')

BLOCK = r"""// ── rt21: honest wording in stored briefs, confirm/undo for destructive actions ──
function _rt21BriefWords(o) {
  const fix = t => typeof t === "string" ? t.replace(/free desk brief from live tape/gi, "free desk brief from market data").replace(/uses live free data only/gi, "uses free market data").replace(/\blive tape\b/gi, "market data") : t;
  ["headline", "summary", "houseView"].forEach(k => { if (typeof o[k] === "string") o[k] = fix(o[k]); });
  if (Array.isArray(o.risks)) o.risks = o.risks.map(fix);
}
function _rt21ClearAsk() {
  const w = document.getElementById("rt21-clr"); if (!w) return;
  w.innerHTML = `<div class="rt21-confirm" role="group" aria-label="Confirm clearing settings"><span>Clear all settings on this device?</span><button type="button" class="rt17-btn rt17-btn-danger" onclick="_rt21ClearDo()">Confirm</button><button type="button" class="rt17-btn" onclick="_rt21ClearCancel()">Cancel</button></div>`;
  w.querySelector("button")?.focus();
}
function _rt21ClearCancel() {
  const w = document.getElementById("rt21-clr"); if (!w) return;
  w.innerHTML = `<button type="button" class="rt17-btn" onclick="_rt21ClearAsk()">Clear settings on this device</button>`;
}
function _rt21ClearDo() {
  try { localStorage.removeItem(RT17_PREFS_KEY); } catch (e) {}
  _rt17Prefs = _rt17Default(); _rt17Apply(); _rt17Render();
  const w = document.getElementById("rt21-clr");
  if (w) w.innerHTML = `<div class="rt17-note" role="status">Cleared. Settings are back to defaults on this device.</div><button type="button" class="rt17-btn" onclick="_rt21ClearAsk()">Clear settings on this device</button>`;
}
let _rt21Undo = null;
function _rt21AlertDel(i, btn) {
  const a = _rt17Prefs.alerts.price[i]; if (!a) return;
  const row = btn && btn.closest ? btn.closest(".rt17-row") : null;
  const go = () => {
    _rt17Prefs.alerts.price.splice(i, 1); _rt17Save(); _rt17Render();
    _rt21Undo = { a, i };
    _rt21Toast(`Alert removed · ${a.tk} ${a.op} ${a.px}`, "Undo", () => {
      if (!_rt21Undo) return; const u = _rt21Undo; _rt21Undo = null;
      _rt17Prefs.alerts.price.splice(Math.min(u.i, _rt17Prefs.alerts.price.length), 0, u.a); _rt17Save(); _rt17Render();
    }, 6000);
  };
  if (row && !(_rt17Prefs.display && _rt17Prefs.display.reduceMotion)) {
    row.style.overflow = "hidden"; row.style.maxHeight = row.offsetHeight + "px"; row.style.transition = "max-height .18s ease, opacity .18s ease, min-height .18s ease";
    requestAnimationFrame(() => { row.style.maxHeight = "0px"; row.style.minHeight = "0px"; row.style.opacity = "0"; });
    setTimeout(go, 190);
  } else go();
}
function _rt21Toast(msg, actLabel, act, ms) {
  let el = document.getElementById("rt21-toast"); if (el) { clearTimeout(el._t); el.remove(); }
  el = document.createElement("div"); el.id = "rt21-toast"; el.setAttribute("role", "status");
  const esc = typeof _escHtml === "function" ? _escHtml : String;
  el.innerHTML = `<span>${esc(msg)}</span>${act ? `<button type="button" class="rt21-tact">${esc(actLabel)}</button>` : ""}<button type="button" class="rt19-ax" aria-label="Dismiss">×</button>`;
  document.body.appendChild(el);
  const close = () => { clearTimeout(el._t); el.remove(); };
  if (act) el.querySelector(".rt21-tact").onclick = () => { close(); act(); };
  el.querySelector(".rt19-ax").onclick = close;
  el._t = setTimeout(close, ms || 6000);
}
(function _rt21Css() {
  if (document.getElementById("rt21-css")) return;
  const st = document.createElement("style"); st.id = "rt21-css";
  st.textContent = `
.rt21-clr{min-height:76px}
.rt21-confirm{display:flex;flex-wrap:wrap;align-items:center;gap:8px;min-height:48px}.rt21-confirm span{flex:1 1 100%;font-size:13px;color:var(--tx,#eee)}
#rt21-toast{position:fixed;left:0;right:0;margin:0 auto;width:fit-content;bottom:calc(84px + env(safe-area-inset-bottom,0px));z-index:950;display:flex;align-items:center;gap:6px;max-width:min(92vw,460px);background:var(--b2,#151517);border:1px solid var(--b4,#333);border-radius:10px;padding:4px 4px 4px 14px;box-shadow:0 10px 30px rgba(0,0,0,.6);font-size:13px;color:var(--tx,#eee)}
#rt21-toast>span{flex:1 1 auto;min-width:0}
.rt21-tact{min-height:44px;padding:0 12px;border:0;background:transparent;color:var(--gd,#d4a64a);font-weight:700;cursor:pointer}`;
  document.head.appendChild(st);
})();
"""
R('rt21 block', 'function _rt17Default() {', BLOCK + 'function _rt17Default() {')
for name, old, new, count in E:
    n = s.count(old)
    if count is None:
        if n < 1: die(f"'{name}' anchor matched 0 times")
    elif n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
HE = [('cache bust', 'app.js?v=chat19', 'app.js?v=chat20'),
      ('no desktop panels below 768px', '<div class="panel-grid" id="panelGrid">', '<style>@media (max-width:767px){#panelGrid{display:none!important}}</style>\n<div class="panel-grid" id="panelGrid">')]
for name, old, new in HE:
    if h.count(old) != 1: die(f"index '{name}' matched {h.count(old)} times")
    h = h.replace(old, new)
for bad in ['◆ LIVE PULSE', 'local LIVE PULSE', 'Live Detections', '"Free brief uses live free data only', 'VIX live']:
    if bad in s: die('postcondition: still present: ' + bad)
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + {len(HE)} index edits; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
