#!/usr/bin/env python3
"""patch_rt44.py: chat42 -> chat43 (client). Stacks on rt43e output (app.js fb569eab).
1 EIA official spot reference line under WTI / Brent (from /api/eia-spot; hidden if unavailable)
2 ticker strip shows LIVE for live instruments
3 sub-lines never push prices sideways (phone cards / detail)
4 Beta hidden when missing (source fixes + DOM guard)
Usage: python3 patch_rt44.py [--check] <dir containing app.js and index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt44 ──' in s: die('rt44 already applied')
if '// ── rt43e ──' not in s: die('base is not rt43e output')
if 'app.js?v=chat42' not in h: die('index.html is not chat42')
for need in ['function _rt43SubText(', 'function _rtTapeBadge(', 'function _escAttr(']:
    if need not in s: die('missing ' + need)
# source fixes for Beta (each optional: skipped with a note if the anchor moved)
EDITS = [
 ('Beta: ${a.beta || "—"} | P/E:', '${a.beta != null && a.beta !== "" && a.beta !== "—" ? `Beta: ${a.beta} | ` : ""}P/E:'),
 ('<div style="font-family:var(--mn);font-size:9.5px;color:var(--t2)">Beta: <span style="color:var(--tx)">${a.beta}</span></div>',
  '${a.beta != null && a.beta !== "" && a.beta !== "—" ? `<div style="font-family:var(--mn);font-size:9.5px;color:var(--t2)">Beta: <span style="color:var(--tx)">${a.beta}</span></div>` : ""}'),
]
for old, new in EDITS:
    n = s.count(old)
    if n == 1: s = s.replace(old, new); print('edit ok:', old[:40])
    else: print('edit skipped (%d matches): %s' % (n, old[:40]))
BLOCK = r'''// ── rt44 ──
// 1: official EIA daily spot reference under WTI and Brent ("Official spot (EIA) $X · as of DATE"); hidden if unavailable
let _rt44Eia = null, _rt44EiaAt = 0;
async function _rt44EiaPoll() {
  if (document.hidden && _rt44Eia) return;
  try { const r = await fetch("/api/eia-spot", { signal: AbortSignal.timeout(15000) }); if (!r.ok) return;
    const j = await r.json(); if (j && j.available) { _rt44Eia = j; _rt44EiaAt = Date.now(); } else if (j && j.available === false && Date.now() - _rt44EiaAt > 12 * 3600e3) _rt44Eia = null; } catch (e) {}
}
function _rt44EiaText(tk) {
  try { const q = _rt44Eia && _rt44Eia[tk]; if (!q || !(q.p > 0) || !q.date) return "";
    const d = new Date(q.date + "T12:00:00Z"); if (!isFinite(d) || Date.now() - d.getTime() > 14 * 864e5) return "";
    const dt = d.toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
    return `Official spot (EIA) $${Number(q.p).toFixed(2)} · as of ${dt}`; } catch (e) { return ""; }
}
{
  const _st0 = _rt43SubText;
  _rt43SubText = function (tk) {
    let base = ""; try { base = _st0.apply(this, arguments) || ""; } catch (e) {}
    if (tk !== "WTI" && tk !== "BRENT") return base;
    const ref = _rt44EiaText(tk);
    return base && ref ? base + " · " + ref : (base || ref);
  };
}
setTimeout(_rt44EiaPoll, 2000);
setInterval(_rt44EiaPoll, 30 * 60_000);
// 2: ticker strip says LIVE for every live instrument (DXY, FX, crypto, metals spot), matching the table's LIVE
try { const st = document.createElement("style"); st.textContent = ".tape-live{background:var(--gnG);color:var(--gn)}"; document.head.appendChild(st); } catch (e) {}
{
  const _tb1 = _rtTapeBadge;
  _rtTapeBadge = function (d) {
    try { if (d && d.status === "live") {
      const t = (d.label ? d.label + " · " : "") + (typeof _rt19LiveTitle === "function" ? _rt19LiveTitle(d) : "Live");
      return `<span class="tape-badge tape-live" title="${_escAttr(t)}">LIVE</span>`; } } catch (e) {}
    return _tb1.apply(this, arguments);
  };
}
// 3: secondary lines never push the price sideways: lift a sub-line out of a horizontal flex row; phone cards keep it
//    full-width under the card body and wrap long text
function _rt44RowFlex(e) { try { const cs = getComputedStyle(e); return /flex/.test(cs.display) && !/column/.test(cs.flexDirection) && e.childElementCount > 1; } catch (x) { return false; } }
setInterval(() => { try {
  document.querySelectorAll(".rt43-sub, .rt43e-sub").forEach(el => {
    el.style.maxWidth = "100%"; el.style.overflowWrap = "anywhere"; el.style.minWidth = "0";
    if (el.classList.contains("rt43e-sub")) { el.style.flexBasis = "100%"; el.style.textAlign = "left"; return; }
    if (el.dataset.rt44mv) return;
    const host = el.parentElement; if (!host || host.closest("#tape,.tape-track,header")) return;
    const row = _rt44RowFlex(host) ? host : (host.parentElement && _rt44RowFlex(host.parentElement) ? host.parentElement : null);
    if (!row || row.matches("body,main,#app,td,tr") || row.closest("#tape,.tape-track,header")) return;
    el.dataset.rt44mv = "1"; el.style.textAlign = "left"; el.style.marginTop = "6px"; row.insertAdjacentElement("afterend", el);
  });
} catch (e) {} }, 1000);
// 4: hide Beta wherever the instrument has no beta (indices, FX crosses added later): no "Beta: undefined" / "Beta: —"
const _rt44Miss = /^(undefined|null|nan|—|-|–|n\/a|)$/i;
setInterval(() => { try {
  const root = document.getElementById("app") || document.body;
  root.querySelectorAll("tr").forEach(tr => { const c = tr.children; if (c.length < 2 || !/^beta$/i.test((c[0].textContent || "").trim())) return;
    const miss = [...c].slice(1).every(x => _rt44Miss.test((x.textContent || "").trim())); if (miss && tr.style.display !== "none") tr.style.display = "none"; });
  root.querySelectorAll("div,span,li").forEach(e => { if (e.childElementCount > 2) return; const t = (e.textContent || "").trim();
    if (t.length > 24 || !/^(beta|β)\b/i.test(t)) return;
    const m = t.match(/^(?:beta|β)\s*:?\s*(.*)$/i);
    if (m && e.childElementCount <= 1 && _rt44Miss.test(m[1].trim()) && t !== "Beta" && t !== "BETA") { e.style.display = "none"; return; }
    if (/^(beta|β)$/i.test(t)) { const n = e.nextElementSibling, p = e.parentElement;
      if (n && _rt44Miss.test((n.textContent || "").trim()) && p && p.childElementCount === 2) p.style.display = "none"; }
  });
} catch (e) {} }, 1500);
'''
s = s.rstrip('\n') + '\n' + BLOCK
if h.count('app.js?v=chat42') != 1: die('index bust anchor')
h = h.replace('app.js?v=chat42', 'app.js?v=chat43')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print('OK rt44 block appended + index chat42->chat43; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
