#!/usr/bin/env python3
"""patch_rt40.py: chat36 -> chat37. Stacks on rt39 output (app.js 8fc00a8a). Client + index.html cache bust.
Ask: the question wins (tickers = what the question names; the open stock is only context), real sector peers with an
explicit PEER VALUATIONS block, verdict pill hidden, sentence-space fix, stored history cleared once and sanitised on
render. Title synced on cold ?t= loads; stock view kept across desktop/phone switches; TNV Back clears ?t= on phone;
Ctrl+K shows 'Compare MU vs NVDA'. Usage: python3 patch_rt40.py [--check] <dir>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt40)' in s: die('rt40 already applied')
if 'REALTIME PRICE LAYER (rt39)' not in s: die('base is not rt39 output')
if 'app.js?v=chat36' not in h: die('index.html is not chat36')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt39)', '// REALTIME PRICE LAYER (rt40)')
R('ask tickers', '  const tickers = _extractChatTickers(text);', '  const tickers = _rt40Tks(text);')
R('history once', 'if (localStorage.getItem("td_chat_v") !== "chat34")', 'if (localStorage.getItem("td_chat_v") !== "chat37")')
R('history ver', 'localStorage.setItem("td_chat_v", "chat34");', 'localStorage.setItem("td_chat_v", "chat37");')
BLOCK = r'''// ── rt40 ──
const RT40_PEERS = {
  MU: ["NVDA", "AVGO", "AMD", "WDC", "INTC"], NVDA: ["AMD", "AVGO", "INTC", "MU", "TSM"], AMD: ["NVDA", "INTC", "AVGO", "MU", "QCOM"],
  AVGO: ["NVDA", "AMD", "QCOM", "MRVL", "MU"], INTC: ["AMD", "NVDA", "TSM", "MU", "QCOM"], TSM: ["NVDA", "INTC", "AMD", "AVGO"], QCOM: ["AVGO", "AMD", "INTC", "NVDA"],
  AAPL: ["MSFT", "GOOGL", "AMZN", "META"], MSFT: ["AAPL", "GOOGL", "AMZN", "ORCL"], GOOGL: ["META", "MSFT", "AMZN", "AAPL"], META: ["GOOGL", "SNAP", "PINS", "MSFT"],
  AMZN: ["WMT", "MSFT", "GOOGL", "COST"], TSLA: ["GM", "F", "RIVN", "TM"], T: ["VZ", "TMUS", "CMCSA"], VZ: ["T", "TMUS", "CMCSA"],
  XOM: ["CVX", "COP", "SHEL", "BP"], CVX: ["XOM", "COP", "SHEL", "BP"], JPM: ["BAC", "WFC", "C", "GS"], BAC: ["JPM", "WFC", "C"], UNH: ["CVS", "CI", "ELV", "HUM"]
};
const RT40_ASSET = [[/\b(gold|bullion|xau)\b/i, "XAU"], [/\bsilver\b/i, "XAG"], [/\b(oil|crude|wti)\b/i, "WTI"], [/\bbrent\b/i, "BRENT"], [/\bbitcoin\b|\bbtc\b/i, "BTC"], [/\bether(eum)?\b|\beth\b/i, "ETH"], [/\b(dollar index|dxy)\b/i, "DXY"], [/\b(s&p|spx|s and p)\b/i, "SPX"], [/\bvix\b/i, "VIX"], [/\b(treasur|10[- ]?y(ea)?r|yields?)\b/i, "TNX"]];
function _rt40Tks(text) {
  const t = String(text || ""), out = [];
  const add = x => { if (x && !out.includes(x)) out.push(x); };
  try {
    (t.match(/\$?\b[A-Z]{1,5}(?:\.[A-Z]{1,2})?\b/g) || []).forEach(m => { const k = m.replace("$", ""); if (A.find(a => a.tk === k)) add(k); });
    A.forEach(a => { const stem = String(a.nm || "").replace(/[,.]?\s+(Inc|Corp(oration)?|Technology|Technologies|Holdings|Group|Company|Co|plc|Ltd|Platforms|Class [A-Z])\b.*$/i, "").trim(); if (stem.length >= 4 && a.cat === "Stock" && new RegExp(`\\b${stem.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i").test(t)) add(a.tk); });
    RT40_ASSET.forEach(([re, tk]) => { if (re.test(t)) add(tk); });
  } catch (e) {}
  // nothing named: a question about "it / this stock / valuation / peers" refers to the open stock
  if (!out.length && typeof selTk !== "undefined" && selTk && /\b(it|its|this|the stock|the company|valuation|peers?|p\/e|earnings|buy|sell|hold|price target|risk)\b/i.test(t)) add(selTk);
  return out.slice(0, 6);
}
_rt36Msgs = function (ms, tks) {
  try {
    if (!ms.length) return ms;
    const out = ms.slice(), i = out.length - 1;
    if (out[i].role !== "user") return out;
    const open = typeof selTk !== "undefined" && selTk ? selTk : "";
    const note = tks && tks.length
      ? `\n\n[Answer this question as asked, about ${tks.slice(0, 3).join(", ")}. Quote valuation only from the live figures supplied, including the PEER VALUATIONS block when comparing.]`
      : `\n\n[Answer this question as asked. ${open ? `The reader has ${open} open; that is background only, do not answer about ${open} unless the question asks.` : ""}]`;
    out[i] = { ...out[i], content: out[i].content + note };
    return out;
  } catch (e) { return ms; }
};
async function _rt40Fin(tk) {
  try {
    if (_finCache[tk]) return;
    if (A.find(a => a.tk === tk && a.cat === "Stock")) return await Promise.race([_rt33Ensure(tk, true), new Promise(r => setTimeout(r, 6000))]);
    const r = await fetch("/api/financials?symbol=" + encodeURIComponent(tk), { signal: AbortSignal.timeout(6000) });
    if (r.ok) { const d = await r.json(); if (d && d.valuation) _finCache[tk] = d; }
  } catch (e) {}
}
_rt38Peers = function (tks, text) {
  try {
    const base = (tks || []).find(t => { const a = A.find(x => x.tk === t); return a && a.cat === "Stock"; });
    if (!base) return [];
    const ask = /peer|compar|versus|\bvs\b|relative|cheap|expensive|valuation|p\/e|multiple|sector/i.test(String(text || ""));
    const set = [base]; (tks || []).forEach(t => { const a = A.find(x => x.tk === t); if (a && a.cat === "Stock" && !set.includes(t)) set.push(t); });
    if (ask) (RT40_PEERS[base] || []).forEach(t => { if (!set.includes(t)) set.push(t); });
    return set.slice(0, 6);
  } catch (e) { return []; }
};
_rt38PeerCtx = function (tks, text) {
  try {
    const peers = _rt38Peers(tks, text);
    if (peers.length < 2) return "";
    const f = x => x == null || !isFinite(x) ? "n/a" : Number(x).toFixed(1) + "x";
    const rows = peers.map(t => { const v = _rt33Val(t); return v ? `${t}: P/E ${f(v.pe)} · forward P/E ${f(v.forwardPe)} · market cap ${_rt33Mc(v.marketCap)}` : `${t}: valuation not available`; });
    return `\n\nPEER VALUATIONS (live, /api/financials; sector peers of ${peers[0]}). Use these figures when comparing valuation; do not substitute an index or ETF for a peer:\n${rows.join("\n")}`;
  } catch (e) { return ""; }
};
{
  const _rp1 = _rt37Reply;
  _rt37Reply = function (t, tks) { let r = _rp1.apply(this, arguments); try { r = String(r || "").replace(/([a-z0-9%)\]])\.([A-Z][a-z])/g, "$1. $2"); } catch (e) {} return r; };
  const _bm0 = _renderBotMsg;
  _renderBotMsg = function (m, idx) {
    try {
      if (m && m.role === "assistant" && typeof m.content === "string") {
        const st = m.structured ? { ...m.structured, verdict: "", dataUsed: (m.structured.dataUsed || []).filter(d => !/\bgold\b|GC=F|XAU|windows?:/i.test(String(d))) } : m.structured;
        m = { ...m, content: _rt37Reply(m.content, ["__any"]), structured: st };
      }
    } catch (e) {}
    return _bm0.call(this, m, idx);
  };
  const _sh0 = _buildLocalSearchHits;
  _buildLocalSearchHits = function (raw) {
    const m = String(raw || "").trim().match(/^compare\s+(.+)$/i);
    if (m) { const tks = m[1].toUpperCase().split(/[\s,]+|\bVS\.?\b/).filter(Boolean).slice(0, 3); if (tks.length) return [{ nm: `Compare ${tks.join(" vs ")}`, sub: "Side-by-side valuation", tp: "Command", act: `lookupTicker('COMPARE ${tks.join(" ").replace(/'/g, "")}');closeSearch()`, priority: 3 }]; }
    return _sh0.apply(this, arguments);
  };
  const _dc0 = _dynClear;
  _dynClear = function () { const r = _dc0.apply(this, arguments); try { const u = new URL(location.href); if (u.searchParams.has("t")) { u.searchParams.delete("t"); history.replaceState(history.state, "", u.pathname + (u.search || "") + u.hash); } } catch (e) {} return r; };
}
let _rt40DynT = 0; const _rt40Bad = {};
{
  const _lt1 = lookupTicker;
  lookupTicker = async function (tk) {
    const k = String(tk || "").trim().toUpperCase();
    if (_rt40Bad[k] && Date.now() - _rt40Bad[k] < 120000) { _dynTk = k; _dynData = null; _dynLoading = false; if (IS_DESKTOP()) renderP2(); else { if (pg !== "anlz") pg = "anlz"; renderMain(); } return; }
    return _lt1.apply(this, arguments);
  };
}
setInterval(() => { try {
  if (!_dynLoading) { _rt40DynT = 0; if (_dynTk && !_dynData) { _rt40Bad[_dynTk] = Date.now(); const root = IS_DESKTOP() ? document.getElementById("p2body") : document.getElementById("main"); if (root && /Loading |FETCHING/i.test(root.innerText.slice(0, 200))) { if (IS_DESKTOP()) renderP2(); else { pg = "anlz"; renderMain(); } } } return; }
  if (!_rt40DynT) { _rt40DynT = Date.now(); return; }
  if (Date.now() - _rt40DynT > 9000) { _rt40DynT = 0; if (_dynTk) _rt40Bad[_dynTk] = Date.now(); _lookupSeq++; _dynLoading = false; _dynData = null; if (IS_DESKTOP()) renderP2(); else renderMain(); }
} catch (e) {} }, 1000);
(() => { try { const st = document.createElement("style"); st.textContent = ".chat-verdict{display:none!important}"; document.head.appendChild(st); } catch (e) {} })();
// title on cold ?t= loads, and keep the stock view across desktop/phone switches
setInterval(() => { try {
  const t = new URL(location.href).searchParams.get("t"); if (!t) return;
  const k = String(t).toUpperCase(), cur = (IS_DESKTOP() ? termSelTk : selTk) || ""; if (cur !== k) return;
  const a = A.find(x => x.tk === k); const want = `${k} · ${a ? a.nm : "Markets"} | The Dispatch Markets`;
  if (document.title !== want) document.title = want;
} catch (e) {} }, 1000);
{
  let wasDesk = IS_DESKTOP(), tmr = 0;
  addEventListener("resize", () => { clearTimeout(tmr); tmr = setTimeout(() => { try {
    const d = IS_DESKTOP(); if (d === wasDesk) return; wasDesk = d;
    const t = (new URL(location.href).searchParams.get("t") || "").toUpperCase(); if (!t || !A.find(x => x.tk === t)) return;
    if (d) { if (termSelTk !== t) termSelect(t); } else if (selTk !== t || pg !== "anlz") openA(t);
  } catch (e) {} }, 350); });
}
'''
R('rt40 block', 'const _rt23Ch = {};', BLOCK + 'const _rt23Ch = {};')
R('ask peers fetch', '..._rt38Peers(tickers, text).map(tk => _rt33Ensure(tk, true))', '..._rt38Peers(tickers, text).map(tk => _rt40Fin(tk))')
for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
h = h.replace('app.js?v=chat36', 'app.js?v=chat37')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + index; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
