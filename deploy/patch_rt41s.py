#!/usr/bin/env python3
"""patch_rt41s.py: server, end-of-file only (no inner anchors). Wraps generateAi: for the /api/chat call (identified by
its system prompt's {"reply":"string" JSON contract), when the latest user message asks about peers / valuation / P/E /
multiples / compare and names one covered stock, builds a PEER VALUATIONS block on the server from the rt32 fundamentals
cache/helper (sector-peer map, 3.5s budget) and PREPENDS it to the system prompt, which is not clipped.
Safe: if generateAi is not reassignable, or rt32 helpers are missing, nothing changes. Never runs server.js.
Usage: python3 patch_rt41s.py [--check] <server.js>"""
import sys, subprocess, tempfile, os
CHECK = '--check' in sys.argv
P = [a for a in sys.argv[1:] if a != '--check'][0] if len(sys.argv) > 1 else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
if 'rt41sPeerBlock' in s: print('SKIP rt41s already applied'); sys.exit(0)
if 'async function generateAi(' not in s: print('SKIP generateAi is not a function declaration here; server.js left as is'); sys.exit(0)
if 'async function rt32Build(' not in s: print('SKIP rt32 fundamentals helper not found; server.js left as is'); sys.exit(0)
s = s.rstrip('\n') + r'''

// rt41s: server-side PEER VALUATIONS for Ask (prepended to the system prompt; context is clipped)
const RT41S_PEERS = {
  MU: ["NVDA", "AVGO", "AMD", "WDC", "INTC"], NVDA: ["AMD", "AVGO", "INTC", "MU", "TSM"], AMD: ["NVDA", "INTC", "AVGO", "MU", "QCOM"],
  AVGO: ["NVDA", "AMD", "QCOM", "MRVL", "MU"], INTC: ["AMD", "NVDA", "TSM", "MU", "QCOM"], TSM: ["NVDA", "INTC", "AMD", "AVGO"], QCOM: ["AVGO", "AMD", "INTC", "NVDA"],
  AAPL: ["MSFT", "GOOGL", "AMZN", "META"], MSFT: ["AAPL", "GOOGL", "AMZN", "ORCL"], GOOGL: ["META", "MSFT", "AMZN", "AAPL"], META: ["GOOGL", "SNAP", "PINS", "MSFT"],
  AMZN: ["WMT", "MSFT", "GOOGL", "COST"], TSLA: ["GM", "F", "RIVN", "TM"], T: ["VZ", "TMUS", "CMCSA"], VZ: ["T", "TMUS", "CMCSA"],
  XOM: ["CVX", "COP", "SHEL", "BP"], CVX: ["XOM", "COP", "SHEL", "BP"], JPM: ["BAC", "WFC", "C", "GS"], BAC: ["JPM", "WFC", "C"], UNH: ["CVS", "CI", "ELV", "HUM"]
};
function rt41sBase(q) {
  const m = q.match(/\[Answer this question as asked, about ([A-Z][A-Z0-9.\-]{0,9})\b/);
  if (m && RT41S_PEERS[m[1]]) return m[1];
  for (const t of (q.match(/\$?\b[A-Z]{1,5}\b(?:'s)?/g) || [])) { const k = t.replace(/^\$|'s$/g, ""); if (RT41S_PEERS[k]) return k; }
  return null;
}
async function rt41sVal(sym) {
  try {
    const hit = RT32.cache.get(sym);
    const data = hit && Date.now() - hit.at < 12 * 3600e3 ? hit.data : await rt32Build(sym);
    return data && data.valuation ? data.valuation : null;
  } catch { return null; }
}
function rt41sMc(v) { if (!(v > 0)) return "n/a"; return v >= 1e12 ? `$${(v / 1e12).toFixed(2)}T` : v >= 1e9 ? `$${(v / 1e9).toFixed(1)}B` : `$${(v / 1e6).toFixed(0)}M`; }
async function rt41sPeerBlock(base) {
  const syms = [base, ...(RT41S_PEERS[base] || [])].slice(0, 6);
  const vals = await Promise.race([Promise.all(syms.map(rt41sVal)), new Promise(r => setTimeout(() => r(null), 3500))]);
  const got = vals ? vals : syms.map(s => { try { const h = RT32.cache.get(s); return h && h.data && h.data.valuation || null; } catch { return null; } });
  const f = x => x == null || !isFinite(x) ? "n/a" : `${Number(x).toFixed(1)}x`;
  const rows = syms.map((s, i) => { const v = got[i]; return v ? `${s}: P/E ${f(v.pe)} · forward P/E ${f(v.forwardPe)} · market cap ${rt41sMc(v.marketCap)}${v.price ? ` · price $${v.price}` : ""}` : null; }).filter(Boolean);
  if (rows.length < 2) return "";
  return `PEER VALUATIONS (live fundamentals, Yahoo Finance / SEC; sector peers of ${base}). When the question is about valuation or peers, quote these exact figures for each company. Do not say a figure is "not specified" when it is listed here, and do not substitute an index or ETF for a peer:\n${rows.join("\n")}`;
}
try {
  const rt41sGen0 = generateAi;
  generateAi = async function (options, ...rest) {
    try {
      if (options && typeof options.system === "string" && options.system.includes('{"reply":"string"') && Array.isArray(options.messages)) {
        const last = [...options.messages].reverse().find(m => m && m.role === "user");
        const q = String((last && last.content) || "");
        if (/peer|valuation|p\/e|\bpe\b|multiples?|compar|versus|\bvs\.?\b|cheap|expensive/i.test(q)) {
          const base = rt41sBase(q);
          if (base) { const blk = await rt41sPeerBlock(base); if (blk) options = { ...options, system: `${blk}\n\n${options.system}` }; }
        }
      }
    } catch {}
    return rt41sGen0.call(this, options, ...rest);
  };
} catch {}
'''
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s)
r = subprocess.run(['node', '--check', t.name], capture_output=True, text=True); os.unlink(t.name)
if r.returncode: print('ABORT node --check failed', r.stderr[:400]); sys.exit(1)
print('APPLY server-side peer valuations for Ask')
if CHECK: print('node --check passed (dry run, nothing written)'); sys.exit(0)
open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('node --check passed\nwritten', P)
