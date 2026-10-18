#!/usr/bin/env python3
"""patch_rt43b.py: chat40 -> chat41 (client). Stacks on rt43 output (app.js 98beb518).
1 metals/energy futures leg polled directly ('Futures ... delayed 10 min' line; change % after reload)
2 one status function for strip, table, phone rows (status/label changes repaint every surface)
3 DXY row in the markets table (computed from live FX)
4 home-listing stocks (TSE/HKEX/KRX/LSE/XETRA/EURONEXT) show their own venue's last close
5 US pre-market / after-hours line for every US stock row (needs rt43bs /api/ext-hours)
6 Settings: Manage billing for every Premium subscriber; admin sees why it is absent
7 one count everywhere (header, desk list, chip recount on the same 2 s tick)
9 MATIC -> POL (Polygon), with saved watchlists migrated
Usage: python3 patch_rt43b.py [--check] <dir containing app.js and index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt43b)' in s or '// ── rt43b ──' in s: die('rt43b already applied')
if 'REALTIME PRICE LAYER (rt43)' not in s or '// ── rt43 ──' not in s: die('base is not rt43 output')
if 'app.js?v=chat40' not in h: die('index.html is not chat40')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
BLOCK = r'''// ── rt43b ──
// one status for every surface: strip, markets table, phone rows and the term chip all read fp(tk) (= _quoteMeta);
// when a ticker's status/label changes we mark it dirty so the shared painter repaints every place it appears
function _rt43bStatus(tk) { const d = fp(tk); return { status: d.status, label: d.label }; }
const _rt43bSig = {};
// 3: DXY gets a markets-table row (computed from live FX in the browser; never the ECB fix)
try { if (!A.some(a => a.tk === "DXY")) A.push({ tk: "DXY", nm: "US Dollar Index", cat: "FX", ex: "ICE (computed)", sc: 55, se: "Neutral", ra: "Neutral", beta: null, pe: "-", mc: "-",
  th: "US dollar against six major currencies (EUR, JPY, GBP, CAD, SEK, CHF) with the ICE weights, computed in your browser from live FX quotes. A weaker dollar is usually a tailwind for gold and commodities." }); } catch (e) {}
// 4: home-listing stocks use their own venue's last close (the shared stock cache keyed on the US session)
{
  const _lc0 = _rt20LastClose, cache = {};
  _rt20LastClose = function (tk) {
    try { const k = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk; const a = A.find(x => x.tk === k);
      if (a && a._rt43) { const q = 15 * 60000, now = Math.floor(Date.now() / q) * q; const c = cache[k]; if (c && c.b === now) return c.v;
        let v = null; if (!_rt18MarketOpenAt(k, new Date(now))) { for (let t = now; t > now - 5 * 86400000; t -= q) { if (_rt18MarketOpenAt(k, new Date(t - q))) { v = t; break; } } }
        cache[k] = { b: now, v }; return v; } } catch (e) {}
    return _lc0.apply(this, arguments);
  };
}
// 1: futures leg for the spot commodities is polled directly (it no longer arrives once spot holds the row),
//    and a spot price that came up without a change is re-applied with the futures' daily %
async function _rt43bFutPoll() {
  if (document.hidden) return;
  const tks = [...Object.keys(RT43_METAL), ...Object.keys(RT43_ENERGY)].filter(t => /=F$/.test(YAHOO_SYMBOLS[t] || ""));
  try { const r = await fetch("/api/yahoo-quote?symbols=" + encodeURIComponent(tks.map(t => YAHOO_SYMBOLS[t]).join(",")), { signal: AbortSignal.timeout(9000) }); if (!r.ok) return; const j = await r.json();
    tks.forEach(tk => { const q = j && j[YAHOO_SYMBOLS[tk]]; if (!q || !(q.p > 0)) return;
      const c = isFinite(Number(q.c)) ? Number(q.c) : q.prev > 0 ? (q.p - q.prev) / q.prev * 100 : NaN; _rt43KeepFut(tk, q.p, c, q.ts);
      if (_rt43SpotFresh(tk) && liveChg(tk) == null && isFinite(c) && P[tk] && P[tk].p > 0) _rt43ApplySpot(tk, P[tk].p, liveQuoteTs[tk], liveQuoteSrc[tk], (A.find(a => a.tk === tk) || {}).nm || tk, c); });
  } catch (e) {}
}
// 5: US pre-market / after-hours prints for every US stock row (Twelve Data rows included) from the server's Yahoo quote
async function _rt43bExtPoll() {
  if (document.hidden || !_rt43ExtOpen() || _usRegularOpen()) return;
  try {
    const sel = IS_DESKTOP() ? (typeof termSelTk !== "undefined" && termSelTk) : (typeof selTk !== "undefined" && selTk);
    const us = tk => { const a = A.find(x => x.tk === tk); return a && a.cat === "Stock" && !a._rt43 && /^[A-Z][A-Z.\-]{0,6}$/.test(YAHOO_SYMBOLS[tk] || tk); };
    const list = [...new Set([sel, ...(_rt.visible || []), ...A.map(a => a.tk)].filter(t => t && us(t)))].slice(0, 60);
    if (!list.length) return;
    const r = await fetch("/api/ext-hours?symbols=" + encodeURIComponent(list.map(t => YAHOO_SYMBOLS[t] || t).join(",")), { signal: AbortSignal.timeout(9000) }); if (!r.ok) return; const j = await r.json();
    if (!j || !j.available || !j.quotes) return;
    list.forEach(tk => { const q = j.quotes[YAHOO_SYMBOLS[tk] || tk]; if (!q) return;
      if (/^PRE/.test(q.state) && q.pre > 0) _rt43Ext[tk] = { p: q.pre, ts: _rt43Ms(q.preTs), lbl: "Pre-market", at: Date.now() };
      else if (/^POST/.test(q.state) && q.post > 0) _rt43Ext[tk] = { p: q.post, ts: _rt43Ms(q.postTs), lbl: "After hours", at: Date.now() }; });
  } catch (e) {}
}
setInterval(() => { try {
  let changed = false;
  const tks = new Set(A.map(a => a.tk)); document.querySelectorAll("#tape .ti[data-tk]").forEach(el => tks.add(el.dataset.tk));
  tks.forEach(tk => { if (!hasSyncedQuote(tk)) return; const s = _rt43bStatus(tk), sig = s.status + "|" + s.label; if (_rt43bSig[tk] !== sig) { _rt43bSig[tk] = sig; _rt.dirty.add(tk); changed = true; } });
  document.querySelectorAll("#tape .ti[data-tk]").forEach(el => { if (el.dataset.rtSt === undefined && hasSyncedQuote(el.dataset.tk)) { _rt.dirty.add(el.dataset.tk); changed = true; } });
  if (changed) { try { _rtPaint(); } catch (e) {} }
  // 7: every count line (header, desk list, chip) recounts from the same function on the same tick
  _rtRecountStatus();
} catch (e) {} }, 2000);
setTimeout(() => { _rt43bFutPoll().then(() => _rt43MetalPoll()); _rt43bExtPoll(); }, 2000);
setInterval(_rt43bFutPoll, 60_000);
setInterval(_rt43bExtPoll, 60_000);
try { const _rit0 = resolveInternalTicker; resolveInternalTicker = function (raw) { return String(raw || "").trim().toUpperCase() === "MATIC" ? "POL" : _rit0.apply(this, arguments); }; } catch (e) {}
try { const u = new URL(location.href); if ((u.searchParams.get("t") || "").toUpperCase() === "MATIC") { u.searchParams.set("t", "POL"); history.replaceState(history.state, "", u.pathname + u.search + u.hash); try { if (IS_DESKTOP()) termSelect("POL"); else openA("POL"); } catch (e) {} } } catch (e) {}
'''
R('marker', '// REALTIME PRICE LAYER (rt43)', '// REALTIME PRICE LAYER (rt43b)')
R('6 settings billing', '${(typeof _userBilling !== "undefined" && _userBilling && !admin) ? `<button type="button" class="rt17-btn" onclick="_openBillingPortal()">Manage billing</button>` : (!prem ?',
  '${(((typeof _userBilling !== "undefined" && _userBilling) || prem) && !admin) ? `<button type="button" class="rt17-btn" onclick="_openBillingPortal()">Manage billing</button>` : admin ? `<span style="font-size:12px;color:var(--t3)">Admin account: Premium is included and there is no Stripe subscription, so there is no billing to manage.</span>` : (!prem ?')
R('9 BASE', 'MATIC:{p:0.22,c:0}', 'POL:{p:0.22,c:0}')
R('9 A', '{tk:"MATIC",nm:"Polygon"', '{tk:"POL",nm:"Polygon (POL)"')
R('9 CG_MAP', '"polygon-ecosystem-token":"MATIC","matic-network":"MATIC"', '"polygon-ecosystem-token":"POL","matic-network":"POL"')
R('9 yahoo ok', '"UNI","MATIC","APT"', '"UNI","POL","APT"')
R('9 stream map', 'MATIC: ["POL-USD", "POL/USD"]', 'POL: ["POL-USD", "POL/USD"]')
R('9 coin tk', 'return sym === "POL" ? "MATIC" : sym;', 'return sym === "MATIC" ? "POL" : sym;')
R('9 crypto cells', '${sym==="POL"?"MATIC":sym}', '${sym==="MATIC"?"POL":sym}', 2)
R('9 yahoo symbols', 'MATIC:"POL28321-USD"', 'POL:"POL28321-USD"')
R('9 yahoo fix', 'MATIC: "POL28321-USD"', 'POL: "POL28321-USD"')
R('9 cats', "MATIC:'cry'", "POL:'cry'")
R('9 watchlist migrate', 'let watch=_lsJson(', 'try{["td_w","qe_w","td_wls"].forEach(k=>{const v=localStorage.getItem(k);if(v&&v.indexOf(\'"MATIC"\')>=0)localStorage.setItem(k,v.split(\'"MATIC"\').join(\'"POL"\'));});}catch(e){} // rt43b: MATIC -> POL\nlet watch=_lsJson(')
R('rt43b block', 'enhanceCommandPalette();\n', 'enhanceCommandPalette();\n' + BLOCK)
for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
import re as _re
left = [m.start() for m in _re.finditer(r'MATIC"?\s*:', s)]
if left: die('MATIC key left over at %r' % left[:3])
HX = [('index bust', 'app.js?v=chat40', 'app.js?v=chat41')]
for name, old, new in HX:
    if h.count(old) != 1: die(f"'{name}' anchor matched {h.count(old)} times in index.html")
    h = h.replace(old, new)
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} app.js edits + {len(HX)} index.html edits; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
