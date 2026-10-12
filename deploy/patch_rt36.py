#!/usr/bin/env python3
"""patch_rt36.py — chat32 -> chat33. Stacks on rt35 output (app.js 7251c6ba). Client + index.html cache bust.
Closing round of the chat29 audit: ticker-news relevance, one regime-fit source, consistent counts, Ask chips and focus,
lens verdict labels, brief/regime overweight contradictions, Financials loader watchdog, crypto mcap from CoinGecko,
unique alert input ids, Playbook sidebar link, plain timestamps, More sheet consistency.
Usage: python3 patch_rt36.py [--check] <dir>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt36)' in s: die('rt36 already applied')
if 'REALTIME PRICE LAYER (rt35)' not in s: die('base is not rt35 output')
if 'app.js?v=chat32' not in h: die('index.html is not chat32')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt35)', '// REALTIME PRICE LAYER (rt36)')
R('tk news', 'return tags.includes(sym)||(n.x||"").toUpperCase().includes(sym);', 'return _rt36TkHit(n,sym);')
R('fit one source', 'fit: (ai.fit?.length ? ai.fit : local.fit),', 'fit: local.fit,')
R('dash count', 'const primaryLiveCount = [...liveSymbols].filter(hasSyncedQuote).length;', 'const primaryLiveCount = A.filter(a => hasSyncedQuote(a.tk)).length;')
R('dash badge', 'bd(primaryLiveCount + " synced", "var(--gn)")', 'bd(primaryLiveCount + " of " + A.length + " priced", "var(--gn)")')
R('book synced', '${book.length?` · ${liveN} synced`:""}', '${book.length?` · ${liveN} priced`:""}')
R('news book n', 'const bookN=_newsBookTickers().length;', 'const bookN=(typeof _rt26BookDesk==="function"?_rt26BookDesk():_newsBookTickers()).length;')
R('strip live', '<span class="ns-lbl">LIVE</span><span class="ns-val ns-live">${quoteStatusCounts().live}</span>', '<span class="ns-lbl">PRICED</span><span class="ns-val ns-live">${A.length - quoteStatusCounts().unavailable}</span>')
R('loading chip', 'const liveChip = !_userTierReady\n    ? `<span class="htec-chip htec-chip-muted">Loading prices…</span>`', 'const liveChip = (!_userTierReady && !liveSymbols.size)\n    ? `<span class="htec-chip htec-chip-muted">Loading prices…</span>`')
R('just now', 'return s < 60 ? `${s}s ago`', 'return s < 60 ? "just now"')
R('al id m1', '\n        <input id="al-price" class=', '\n        <input id="al-price-m" class=')
R('al id m2', '\n          <button onclick="addAlert(\'${a.tk}\',document.getElementById(\'al-price\').value,\'above\')"', '\n          <button onclick="addAlert(\'${a.tk}\',document.getElementById(\'al-price-m\').value,\'above\')"')
R('al id m3', '\n          <button onclick="addAlert(\'${a.tk}\',document.getElementById(\'al-price\').value,\'below\')"', '\n          <button onclick="addAlert(\'${a.tk}\',document.getElementById(\'al-price-m\').value,\'below\')"')
R('chips dedupe', 'if (last?.structured?.followUps?.length) {', 'if (last?.structured?.followUps?.length && !document.querySelector(".chat-fu")) {')
R('chat focus', 'messages: _chatMsgs.map(m => ({ role: m.role, content: m.content })),', 'messages: _rt36Msgs(_chatMsgs.map(m => ({ role: m.role, content: m.content })), tickers),')
R('lens lbl1', '⬢ LENS ENGINE INTELLIGENCE', '⬢ AI SYNTHESIS VERDICT')
R('lens lbl2', 'REGIME-WEIGHTED VIEW</div>', 'REGIME-WEIGHTED LENS VOTE</div>')
R('brief ow', 'const b = _rt31Brief(_brief);', 'const b = _rt36Ow(_rt31Brief(_brief));')
R('btc th', 'th:"ETF inflows $471M single day. MSBT launched at 0.14%. Exchange reserves at 9-year low. Range-bound $68-72K despite macro stress."', 'th:"Largest crypto asset by market cap. Spot ETF flows, exchange reserves and real yields drive the medium-term trend; check the live price and flows above before acting."')
BLOCK = r"""// ── rt36: closing round of the chat29 audit ──
function _rt36TkHit(n, sym) {
  try {
    const x = String((n.x || "") + " " + (n.desc || ""));
    if (_rt33Has(x.toUpperCase(), sym) && (sym.length > 2 || /\$[A-Z]/.test(x) || /\([A-Z]{1,5}\)/.test(x) || new RegExp("\\b" + sym + "\\b").test(x))) return true;
    const a = A.find(q => q.tk === sym), nm = a && a.nm ? String(a.nm).split(/[ ,(]/)[0] : "";
    return nm.length >= 4 && new RegExp("\\b" + nm.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\b", "i").test(x);
  } catch (e) { return false; }
}
function _rt36Msgs(ms, tks) {
  try {
    if (!tks || !tks.length || !ms.length) return ms;
    const out = ms.slice(), i = out.length - 1;
    if (out[i].role === "user") out[i] = { ...out[i], content: out[i].content + `\n\n[Answer about ${tks.slice(0, 3).join(", ")} first. Leave out gold or macro lines unless they bear directly on it. Quote valuation only from the live figures supplied, and name real peers with their figures or none.]` };
    return out;
  } catch (e) { return ms; }
}
function _rt36Ow(b) {
  try {
    if (!b) return b;
    const re = _computeRegimeEngine(), lc = v => String(v || "").toLowerCase();
    const hit = (x, list) => (list || []).some(y => lc(x).includes(lc(y).split(/[ /(]/)[0]) || lc(y).includes(lc(x).split(/[ /(]/)[0]));
    return { ...b, overweight: (b.overweight || []).filter(x => !hit(x, re.underweight)), underweight: (b.underweight || []).filter(x => !hit(x, re.overweight)) };
  } catch (e) { return b; }
}
// crypto market cap comes from CoinGecko only (one source across Compare, lens and /crypto/)
(() => { try { A.forEach(a => { if (a.cat === "Crypto") { a._mc0 = a._mc0 || a.mc; a.mc = "—"; } }); } catch (e) {} })();
function _rt36CgMc() {
  try {
    (_cryptoMktData || []).forEach(c => {
      const tk = (typeof resolveInternalTicker === "function" && resolveInternalTicker(String(c.symbol || "").toUpperCase())) || String(c.symbol || "").toUpperCase();
      const a = A.find(x => x.tk === tk && x.cat === "Crypto");
      if (a && c.market_cap > 0) a.mc = c.market_cap >= 1e12 ? "$" + (c.market_cap / 1e12).toFixed(2) + "T" : c.market_cap >= 1e9 ? "$" + (c.market_cap / 1e9).toFixed(1) + "B" : "$" + (c.market_cap / 1e6).toFixed(0) + "M";
    });
  } catch (e) {}
}
setInterval(_rt36CgMc, 5000);
// headlines: show the full line (CSS wraps) instead of a hard '…' cut at 120 chars
try { const _rt36Clip0 = _rt16Clip; _rt16Clip = function (s, n) { return _rt36Clip0(s, Math.max(Number(n) || 0, 240)); }; } catch (e) {}
// Playbook sidebar link: in-app route instead of a full reload (first click was swallowed mid-boot)
document.addEventListener("click", e => {
  const b = e.target && e.target.closest && e.target.closest("#sbi-playbook,.sbi-playbook");
  if (b && typeof nav === "function" && !_isVisitor()) { e.preventDefault(); e.stopImmediatePropagation(); try { nav("playbook"); history.pushState(history.state, "", "/playbook/"); } catch (x) {} }
}, true);
// Financials loader watchdog: never leave 'LOADING FINANCIALS…' up for more than 15s
setInterval(() => {
  try {
    document.querySelectorAll("#term-fin-root,#anlz-fin-root").forEach(el => {
      if (!/LOADING FINANCIALS/i.test(el.innerText || "")) { delete el.dataset.rt36; return; }
      const t = +el.dataset.rt36 || 0, now = Date.now();
      if (!t) { el.dataset.rt36 = String(now); return; }
      if (now - t < 15000) return;
      const tk = (IS_DESKTOP() ? termSelTk : selTk) || "";
      if (_finCache[tk]) { el.innerHTML = renderFinancials(tk, _finCache[tk]); return; }
      el.innerHTML = `<div style="padding:16px;text-align:center;font-size:12px;color:var(--t3)">Financials did not load. <button type="button" class="news-act" onclick="delete _finCache['${tk}'];loadFinancials('${tk}','${el.id}')">Retry</button></div>`;
    });
  } catch (e) {}
}, 3000);
(() => { try { const st = document.createElement("style"); st.textContent = `.more-nav-item em{display:none}`; document.head.appendChild(st); } catch (e) {} })();
"""
R('rt36 block', 'const _rt23Ch = {};', BLOCK + 'const _rt23Ch = {};')

for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
h = h.replace('app.js?v=chat32', 'app.js?v=chat33')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + index; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
