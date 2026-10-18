#!/usr/bin/env python3
"""patch_rt34.py — chat30 -> chat31. Stacks on rt33 output (app.js fa8a959f). Client + index.html cache bust.
Playbook load repaint, admin checkout -> billing, XAU change from GC=F chart basis, empty calendar hidden,
sector rotation lazy-load, research date label, mobile tab/table/overflow layout, alert undo, tab title.
Usage: python3 patch_rt34.py [--check] <dir containing app.js + index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt34)' in s: die('rt34 already applied')
if 'REALTIME PRICE LAYER (rt33)' not in s: die('base is not rt33 output')
if 'app.js?v=chat30' not in h: die('index.html is not chat30')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt33)', '// REALTIME PRICE LAYER (rt34)')
R('playbook repaint', '  _goldDeskLoad = false;\n  if (pg === "gold") _refreshGoldView();', '  _goldDeskLoad = false;\n  if (pg === "gold" || pg === "playbook") _refreshGoldView();')
R('playbook start', '  _goldDeskErr = null;\n  if (pg === "gold") _refreshGoldView();', '  _goldDeskErr = null;\n  if (pg === "gold" || pg === "playbook") _refreshGoldView();')
R('premium checkout', '  if(checkout==="1"){\n    history.replaceState({}, "", location.pathname);\n', '  if(checkout==="1"&&_isPremium()){\n    history.replaceState({}, "", location.pathname);\n    if(_userBilling){showToast("You already have Premium. Opening billing…","var(--gd)");_openBillingPortal();}\n    else showToast("Premium is already active on this account (no Stripe billing to manage)","var(--gd)");\n    return;\n  }\n  if(checkout==="1"){\n    history.replaceState({}, "", location.pathname);\n')
R('gc basis', '        _rt.goldChecked = Date.now();\n', '        _rt.goldChecked = Date.now();\n        _rt34Gc();\n')
R('calendar empty', '  h += `<div style="padding:4px 16px 6px;background:var(--b1);border-bottom:1px solid var(--gb);border-top:1px solid var(--gb);margin-top:4px">\n    <div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.15em;padding-top:8px">ECONOMIC CALENDAR</div>',
  '  if (upcoming.length) h += `<div style="padding:4px 16px 6px;background:var(--b1);border-bottom:1px solid var(--gb);border-top:1px solid var(--gb);margin-top:4px">\n    <div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.15em;padding-top:8px">ECONOMIC CALENDAR</div>')
R('sector lazy', "  if (!cN || !dN) return { label: '—', col: 'var(--t3)', desc: 'Sector data not loaded on this page' };",
  "  if (!cN || !dN) { _rt34Sec(); return { label: '—', col: 'var(--t3)', desc: 'Loading sector returns…' }; }")
R('research date', '<span>Apr 26, 2026 · 8 min</span>', '<span>Published Apr 26, 2026 · levels as of publication · 8 min</span>')
R('alert undo', 'function removeAlert(idx){\n  if(!isFinite(idx)||idx<0||idx>=alerts.length)return;\n  alerts.splice(idx,1);',
  'function removeAlert(idx){\n  if(!isFinite(idx)||idx<0||idx>=alerts.length)return;\n  const _rm=alerts.splice(idx,1)[0];_rt34Undo(_rm,idx);')
R('title', 'function _rt33Ensure(tk, wait) {', 'function _rt33Ensure(tk, wait) {\n  try { if (tk) document.title = `${tk} · ${(A.find(a => a.tk === tk) || {}).nm || "Markets"} | The Dispatch Markets`; } catch (e) {}')
BLOCK = r"""// ── rt34: playbook repaint, GC=F basis for XAU, sector lazy-load, alert undo, mobile layout ──
function _rt34Gc() {
  try {
    if (_rt.gcPct && Date.now() - _rt.gcPct.at < 6 * 3600_000) return;
    const m = _rt33Meta["GC=F"], px = m && m.regularMarketPrice, pv = m && (m.chartPreviousClose || m.previousClose);
    if (px > 0 && pv > 0) { _rt.gcPct = { c: (px / pv - 1) * 100, at: Date.now() }; return; }
    if (!window.__rt34GcF) { window.__rt34GcF = 1; fetchYahooIntraday("GC=F").catch(() => {}); }
  } catch (e) {}
}
function _rt34Sec() {
  if (window.__rt34Sec) return; window.__rt34Sec = 1;
  setTimeout(() => { try { Promise.resolve(fetchSectorData()).then(() => { try { renderMain(); } catch (e) {} }).catch(() => {}); } catch (e) {} }, 0);
}
function _rt34Undo(a, idx) {
  try {
    localStorage.setItem("td_alerts", JSON.stringify(alerts));
    document.querySelectorAll(".toast,#toast,.rt34-undo").forEach(t => { if (/Alert set/.test(t.textContent || "")) t.remove(); });
    const d = document.createElement("div");
    d.className = "rt34-undo"; d.setAttribute("role", "status");
    d.innerHTML = `<span>Alert removed: ${a.tk} ${a.dir === "above" ? "≥" : "≤"} $${a.targetPrice}</span><button type="button">Undo</button>`;
    d.querySelector("button").onclick = () => { alerts.splice(Math.min(idx, alerts.length), 0, a); localStorage.setItem("td_alerts", JSON.stringify(alerts)); d.remove(); try { if (IS_DESKTOP() && termSelTk) renderP2(); else _refreshView(); } catch (e) {} };
    document.body.appendChild(d); setTimeout(() => d.remove(), 6000);
  } catch (e) {}
}
(() => { try {
  const st = document.createElement("style"); st.id = "rt34-css";
  st.textContent = `.rt34-undo{position:fixed;left:50%;bottom:calc(84px + env(safe-area-inset-bottom));transform:translateX(-50%);z-index:9999;display:flex;gap:12px;align-items:center;background:var(--b2);border:1px solid var(--gb);color:var(--tx);padding:10px 14px;border-radius:8px;font:12px var(--sn)}
.rt34-undo button{background:none;border:0;color:var(--gd);font-weight:800;cursor:pointer}
@media (max-width:767px){
 #main{overflow-x:hidden;padding-bottom:calc(96px + env(safe-area-inset-bottom))}
 #main img,#main svg,#main canvas,#main pre{max-width:100%}
 #main .gc,#main table{max-width:100%}
 [data-rt34t] td,[data-rt34t] th{padding:6px 4px!important;font-size:10px!important;white-space:normal;word-break:break-word}
}`;
  document.head.appendChild(st);
} catch (e) {} })();
"""
R('inst tbl', 'min-width:330px"', 'min-width:0;table-layout:auto" data-rt34t')
R('fin tbl', 'min-width:320px"', 'min-width:0;table-layout:auto" data-rt34t', 2)
R('rt34 block', 'const _rt23Ch = {};', BLOCK + 'const _rt23Ch = {};')

for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
h = h.replace('app.js?v=chat30', 'app.js?v=chat31')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + index; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
