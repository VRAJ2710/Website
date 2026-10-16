#!/usr/bin/env python3
"""patch_rt43e.py: chat41 -> chat42 (client). Stacks on rt43b output (app.js 76d74522).
1/2 secondary line (futures leg / pre-market / after hours / computed DXY) on every markets-table row and phone card
2   pre-market poll covers every US stock (60 per request, up to 3 requests a minute)
3   strip badge shows the same label as the table (e.g. "spot proxy", "delayed 10m")
4   one warm-up gate: counts read "Syncing…" until the priced count settles
Usage: python3 patch_rt43e.py [--check] <dir containing app.js and index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt43e ──' in s: die('rt43e already applied')
if '// ── rt43b ──' not in s: die('base is not rt43b output')
if 'app.js?v=chat41' not in h: die('index.html is not chat41')
for need in ['function _rt43SubText(', 'function _rtTapeBadge(', 'function _rt42Ready(', 'function quoteStatusSummary(', 'function _rt43ExtOpen(']:
    if need not in s: die('missing ' + need)
BLOCK = r'''// ── rt43e ──
// 1/2: the secondary line (futures leg for spot commodities, US pre-market / after-hours, computed DXY) on every
//      markets-table row and phone card, not only in the detail view
setInterval(() => { try {
  document.querySelectorAll('td[data-fl], .gc[data-price-card]').forEach(host => {
    const tk = host.dataset.fl || host.dataset.priceCard; if (!tk) return;
    let txt = ""; try { txt = _rt43SubText(tk); } catch (e) {}
    let el = host.querySelector(":scope > .rt43e-sub");
    if (!txt) { if (el) el.remove(); return; }
    if (!el) { el = document.createElement("div"); el.className = "rt43e-sub"; el.style.cssText = "font-family:var(--mn);font-size:10px;line-height:1.3;color:var(--t2);font-weight:500;margin-top:3px;white-space:normal"; host.appendChild(el); }
    if (el.textContent !== txt) el.textContent = txt;
  });
} catch (e) {} }, 2000);
// 2: pre-market / after-hours for every US stock row (the rt43b poll covered the first 60), batched 60 per request
async function _rt43eExtPoll() {
  if (document.hidden || !_rt43ExtOpen() || _usRegularOpen()) return;
  try {
    const us = a => a && a.cat === "Stock" && !a._rt43 && /^[A-Z][A-Z.\-]{0,6}$/.test(YAHOO_SYMBOLS[a.tk] || a.tk);
    const vis = new Set([...(_rt.visible || [])]);
    const list = A.filter(us).map(a => a.tk).sort((x, y) => (vis.has(y) ? 1 : 0) - (vis.has(x) ? 1 : 0));
    for (let i = 0; i < list.length && i < 180; i += 60) {
      const part = list.slice(i, i + 60);
      const r = await fetch("/api/ext-hours?symbols=" + encodeURIComponent(part.map(t => YAHOO_SYMBOLS[t] || t).join(",")), { signal: AbortSignal.timeout(9000) });
      if (!r.ok) continue; const j = await r.json(); if (!j || !j.quotes) continue;
      part.forEach(tk => { const q = j.quotes[YAHOO_SYMBOLS[tk] || tk]; if (!q) return;
        if (/^PRE/.test(q.state) && q.pre > 0) _rt43Ext[tk] = { p: q.pre, ts: _rt43Ms(q.preTs), lbl: "Pre-market", at: Date.now() };
        else if (/^POST/.test(q.state) && q.post > 0) _rt43Ext[tk] = { p: q.post, ts: _rt43Ms(q.postTs), lbl: "After hours", at: Date.now() }; });
    }
  } catch (e) {}
}
setTimeout(_rt43eExtPoll, 3000);
setInterval(_rt43eExtPoll, 60_000);
// 3: the strip badge says exactly what the table says (same fp() label), not a generic word
{
  const _tb0 = _rtTapeBadge;
  _rtTapeBadge = function (d) {
    try { if (d && d.status !== "live" && d.status !== "unavailable" && d.label) {
      const cls = d.status === "delayed" || d.status === "extended" ? "tape-del" : d.status === "stale" ? "tape-stale" : "tape-cache";
      return `<span class="tape-badge ${cls}" title="${_escAttr(d.detail || d.label)}">${_escHtml(String(d.label).toLowerCase())}</span>`; } } catch (e) {}
    return _tb0.apply(this, arguments);
  };
}
// 4: one warm-up gate for every count: "Syncing…" until the count settles (all priced, or unchanged for 5 s, or 30 s)
let _rt43eReadyAt = 0, _rt43eLast = -1, _rt43eSince = 0;
function _rt43eReady() {
  if (_rt43eReadyAt) return true;
  try { let n = 0; A.forEach(a => { if (hasSyncedQuote(a.tk)) n++; });
    if (n !== _rt43eLast) { _rt43eLast = n; _rt43eSince = Date.now(); }
    if (n >= A.length || (n >= A.length * 0.9 && Date.now() - _rt43eSince >= 5000) || performance.now() > 30000) { _rt43eReadyAt = Date.now(); return true; } } catch (e) {}
  return false;
}
{
  const _qs0 = quoteStatusSummary, _s0 = _rt37Sum, _r0 = _rt42Ready;
  quoteStatusSummary = function () { return _rt43eReady() ? _qs0.apply(this, arguments) : "Syncing…"; };
  _rt37Sum = function () { return _rt43eReady() ? _s0.apply(this, arguments) : "Syncing…"; };
  _rt42Ready = function () { return _rt43eReady() && _r0.apply(this, arguments); };
}
'''
s = s.rstrip('\n') + '\n' + BLOCK
if h.count('app.js?v=chat41') != 1: die('index bust anchor')
h = h.replace('app.js?v=chat41', 'app.js?v=chat42')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print('OK rt43e block appended + index chat41->chat42; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
