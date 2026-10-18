#!/usr/bin/env python3
"""patch_rt23.py — chat21 -> chat22. Stacks on rt22 output (t22). Client + index.html cache bust.
Usage: python3 patch_rt23.py [--check] <dir containing app.js + index.html>"""
import sys, os, re, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt23)' in s: die('rt23 already applied')
if 'REALTIME PRICE LAYER (rt22)' not in s: die('base is not rt22 output')
if 'app.js?v=chat21' not in h: die('index.html is not chat21')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt22)', '// REALTIME PRICE LAYER (rt23)')
# 1. word-boundary clamps on display text (audit of every display .slice on prose)
C = [
 ('${a.th?.slice(0, 140) || ""}', '${_rt16Clip(a.th || "", 140)}'),
 ('${_escAttr(n.note).slice(0, 90)}', '${_escAttr(_rt16Clip(n.note, 90))}'),
 ('${(_brief?.headline || "Playing…").slice(0, 48)}', '${_rt16Clip(_brief?.headline || "Playing…", 48)}'),
 ('${(r.thesis || "").slice(0, 120)}${(r.thesis || "").length > 120 ? "…" : ""}', '${_rt16Clip(r.thesis || "", 120)}'),
 ('${r.thesis.slice(0,120)}...', '${_rt16Clip(r.thesis, 120)}'),
 ('${a.th.slice(0,120)}...', '${_rt16Clip(a.th, 120)}'),
 ('${r.thesis.slice(0,100)}...', '${_rt16Clip(r.thesis, 100)}'),
 ('x:(it.headline||"").slice(0,120),', 'x:_rt16Clip(it.headline||"",120),', 2),
 ('(notes[0].text||notes[0].body||notes[0].note||"").slice(0,90)', '_rt16Clip(notes[0].text||notes[0].body||notes[0].note||"",90)'),
 ('${_escHtml((_brief.headline||"").slice(0,90))}', '${_escHtml(_rt16Clip(_brief.headline||"",90))}'),
 ('${(synth.analysis || "").slice(0, 400)}', '${_rt16Clip(synth.analysis || "", 400)}'),
 ('${t.length > 28 ? t.slice(0, 28) + "…" : t}', '${_rt16Clip(t, 28)}'),
 ("${note.length>65?note.slice(0,65)+'…':note}", '${_rt16Clip(note,65)}'),
]
for i, c in enumerate(C): R(f'clip {i}', c[0], c[1], c[2] if len(c) > 2 else 1)
# (r.thesis || "").slice(0, 90) variant
R('clip 90', '${(r.thesis || "").slice(0, 90)}${(r.thesis || "").length > 90 ? "…" : ""}', '${_rt16Clip(r.thesis || "", 90)}')
# 2. stock chart: never a dead end
R('chart label', 'INTRADAY · UPDATES ON FETCH</div>', '${_rt23ChartLbl(a.tk, (HIST[a.tk]||[]).filter(v=>typeof v==="number"&&isFinite(v)&&v>0).length>=5)}</div>')
R('chart data', '  const hdRaw=HIST[a.tk]||[];const hd=hdRaw.filter(v=>typeof v==="number"&&isFinite(v)&&v>0);',
  '  const hdRaw=HIST[a.tk]||[];let hd=hdRaw.filter(v=>typeof v==="number"&&isFinite(v)&&v>0);\n  if(hd.length<5){const fb=_rt23Ch[a.tk];if(fb&&fb.pts&&fb.pts.length>=5)hd=fb.pts;else _rt23ChartFetch(a.tk);}')
R('chart empty', 'CHART UNAVAILABLE — INSUFFICIENT INTRADAY DATA</text>`;',
  '${_rt23Ch[a.tk]&&_rt23Ch[a.tk].failed?"CHART DATA UNAVAILABLE RIGHT NOW":"LOADING CHART…"}</text>`;')
# 4. phone stock detail: mark the view so the INTEL and watchlist strips get out of the way
R('detail marker', '  let h=`<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;margin-bottom:10px">\n    <div style="display:flex;gap:10px;align-items:center">${ring(a.sc,52)}',
  '  let h=`<div class="rt23-stock" style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;margin-bottom:10px">\n    <div style="display:flex;gap:10px;align-items:center">${ring(a.sc,52)}')
# 5. no trailing separator in the INTEL strip (the marquee gap is spacing, not a '·')
R('intel chunk', '  const chunk = `${scrollTxt} · `;', '  const chunk = String(scrollTxt).replace(/[\\s·•|,;–—-]+$/, "");')
R('intel head trim', '  const headRaw = (intel.headline || reLabel()).replace(/</g, "&lt;");', '  const headRaw = String(intel.headline || reLabel()).replace(/[\\s·•|,;–—-]+$/, "").replace(/</g, "&lt;");')
BLOCK = r"""// ── rt23: stock chart fallback (last session / daily 1M), phone detail chrome, separators ──
const _rt23Ch = {};
function _rt23ChartLbl(tk, haveHist) {
  const fb = _rt23Ch[tk];
  if (!haveHist && fb && fb.pts && fb.pts.length >= 5) return fb.label;
  let crypto = false; try { crypto = _rtIsCrypto(tk); } catch (e) {}
  if (crypto) return "INTRADAY · 24H MARKET";
  let open = true; try { open = _usRegularOpen(); } catch (e) {}
  return open ? "INTRADAY · UPDATES ON FETCH" : "LAST SESSION · MARKET CLOSED";
}
async function _rt23ChartFetch(tk) {
  if (_rt23Ch[tk] && (_rt23Ch[tk].busy || _rt23Ch[tk].pts || Date.now() - (_rt23Ch[tk].at || 0) < 60000)) return;
  _rt23Ch[tk] = { busy: true, at: Date.now() };
  const ys = (typeof YAHOO_SYMBOLS !== "undefined" && YAHOO_SYMBOLS[tk]) || tk;
  const get = async (range, interval) => {
    try {
      const r = await chartFetch(`/api/yahoo-chart?symbol=${encodeURIComponent(ys)}&range=${range}&interval=${interval}`, { signal: AbortSignal.timeout(10000) });
      if (!r.ok) return null;
      const res = (await r.json())?.chart?.result?.[0];
      const ts = res?.timestamp || [], cl = res?.indicators?.quote?.[0]?.close || [];
      const pts = [], tss = [];
      cl.forEach((v, i) => { if (typeof v === "number" && isFinite(v) && v > 0) { pts.push(v); tss.push(ts[i]); } });
      return pts.length >= 5 ? { pts, last: tss[tss.length - 1] } : null;
    } catch (e) { return null; }
  };
  let out = null, label = "";
  const day = t => { try { return new Date(t * 1000).toLocaleDateString("en-GB", { weekday: "short", timeZone: (_rt17Prefs && _rt17Prefs.display && _rt17Prefs.display.tz) || "Europe/London" }); } catch (e) { return ""; } };
  const s = await get("1d", "5m");
  if (s) { out = s; label = `LAST SESSION · ${day(s.last).toUpperCase()}`; }
  else { const d = await get("1mo", "1d"); if (d) { out = d; label = "DAILY · 1M"; } }
  _rt23Ch[tk] = out ? { pts: out.pts.slice(-120), label, at: Date.now() } : { failed: true, at: Date.now() };
  try {
    const viewing = (IS_DESKTOP() && typeof termSelTk !== "undefined" && termSelTk === tk) || selTk === tk;
    if (viewing) { if (IS_DESKTOP()) renderP2(); else renderMain(); }
  } catch (e) {}
}
(function _rt23Css() {
  if (document.getElementById("rt23-css")) return;
  const st = document.createElement("style"); st.id = "rt23-css";
  st.textContent = `
@media (max-width:767px){body:has(#main .rt23-stock) #siteIntelBar,body:has(#main .rt23-stock) #wlGlanceBar{display:none!important}}
.si-bar-chunk{padding-right:2.5em}`;
  document.head.appendChild(st);
})();
"""
R('rt23 block', 'function _rt22Name(tk) {', BLOCK + 'function _rt22Name(tk) {')
for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
if h.count('app.js?v=chat21') != 1: die('index cache-bust anchor')
h = h.replace('app.js?v=chat21', 'app.js?v=chat22')
for bad in ['INSUFFICIENT INTRADAY DATA', 'a.th?.slice(0, 140)', '.slice(0,117)+"..."']:
    if bad in s: die('postcondition: still present: ' + bad)
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + index; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
