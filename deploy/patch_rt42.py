#!/usr/bin/env python3
"""patch_rt42.py: chat38 -> chat39. Stacks on rt41 output (app.js a415e509). Client + index.html cache bust.
Ask text guard keeps peer lines intact + honest latency copy + 75s timeout; one shared count with 'Syncing…' until the
first full snapshot; plain feed badges instead of D/C/S/P; Pulse title and insight from the same fit score; guest
Gold/Dollar never older than 24h; regime computed from available inputs with a 15s hide fallback; watchlist repaint on
quotes, XAU change from previous close, SPY beta; plain RSI/MA labels, SCORE header, no BYOK jargon.
Usage: python3 patch_rt42.py [--check] <dir>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt42)' in s: die('rt42 already applied')
if 'REALTIME PRICE LAYER (rt41)' not in s: die('base is not rt41 output')
if 'app.js?v=chat38' not in h: die('index.html is not chat38')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt41)', '// REALTIME PRICE LAYER (rt42)')
# 1 Ask
R('ask copy 1', 'Synthesising view (usually under 30 seconds)…', 'Synthesising view (usually 20–60 seconds)…')
R('ask copy 2', 'Typical response: under 30 seconds.', 'Typical response: 20–60 seconds.')
R('ask copy 3', 'latest quotes, newsroom & regime · typically under 30s', 'latest quotes, newsroom & regime · typically 20–60s')
R('ask timeout', '    const res = await fetch("/api/chat", {\n      method: "POST",', '    const res = await fetch("/api/chat", {\n      signal: AbortSignal.timeout(75000),\n      method: "POST",')
# 3 badges
for code, word in [('title="Delayed free feed">D</span>', 'title="Delayed free feed">delayed</span>'), ('title="Stale tick">S</span>', 'title="Stale tick">stale</span>'),
                   ('title="Session cache">C</span>', 'title="Session cache">cached</span>'), ('title="Proxy reference price">P</span>', 'title="Proxy reference price">ref</span>')]:
    R('badge ' + word[-12:], code, word, 2)
R('badge ext', 'title="Extended-hours print (delayed)">D</span>', 'title="Extended-hours print (delayed)">ext</span>')
# 4 pulse
R('pulse insight', 'insight = `${a.nm}: ${a.se} · score ${a.sc}/100 · ${dayLbl} · ${rsLbl}.', 'insight = `${a.nm}: ${f.label} · regime fit ${f.score}/100 · ${dayLbl} · ${rsLbl}.')
R('pulse note', 'return { tk, score, label, note: `${label} · ${a?.se || "—"} · ${chgLbl}` };', 'return { tk, score, label, note: `${label} · regime fit ${score}/100 · ${chgLbl}` };')
# 5 guest gold/dollar
R('fd snap age', '  const r = _fdSnapRow(tk);\n  if (!r) return "";', '  const r = _fdSnapRow(tk);\n  if (!r || !(Date.now() - r.ts < 24 * 3600e3)) return "";')
R('fd inline age', '      if (!q || liveSymbols.has(tk)) return;', '      if (!q || liveSymbols.has(tk)) return;\n      { const qt = Number(q.ts ?? q.fetchedAt); const qms = qt > 0 && qt < 1e10 ? qt * 1000 : qt; if (!(Date.now() - qms < 24 * 3600e3)) return; }')
# 6 regime
R('regime inputs', '  if (r && (!ok(r.vix) || !ok(r.spxChg))) {\n    return { ...r, loading: true, label: "Regime: loading…", narrative: "Regime: loading…" };',
  '  if (r && (!ok(r.vix) || !(ok(r.spxChg) || ok(r.spx)))) {\n    if (performance.now() > 15000) return { ...r, loading: true, _hide: true, label: "", narrative: "" };\n    return { ...r, loading: true, label: "Regime: loading…", narrative: "Regime: loading…" };')
R('regime chip', 'const regimeChip=re.loading?`<span', 'const regimeChip=re.loading&&re._hide?"":re.loading?`<span')
R('regime chip m', 'const regimeChipMob=re.loading?`<span', 'const regimeChipMob=re.loading&&re._hide?"":re.loading?`<span')
R('regime home', '${re && re.loading ? " · Regime: loading…"', '${re && re.loading ? (re._hide ? "" : " · Regime: loading…")')
R('regime text', 're.loading ? "Regime: loading…" : `${re.label} · ${re.score}/100`', 're.loading ? (re._hide ? "" : "Regime: loading…") : `${re.label} · ${re.score}/100`')
# 2 counts
R('strip sync', '${_c.priced?`${_c.priced} prices · ${_c.live} live · ${_rt37Upd(priceLastFetch&&priceLastFetch.getTime())}`:"Prices loading"}', '${_rt42Ready()?`${_c.priced} prices · ${_c.live} live · ${_rt37Upd(priceLastFetch&&priceLastFetch.getTime())}`:"Syncing…"}')
R('brief cells', '<span class="ns-val ns-live">${_rt37Count().priced}</span></div>\n    <div class="ns-cell"><span class="ns-lbl">LIVE</span><span class="ns-val ns-live">${_rt37Count().live}</span>',
  '<span class="ns-val ns-live">${_rt42Ready()?_rt37Count().priced:"…"}</span></div>\n    <div class="ns-cell"><span class="ns-lbl">LIVE</span><span class="ns-val ns-live">${_rt42Ready()?_rt37Count().live:"…"}</span>')
R('markets live', '${tickers.filter(a => hasSyncedQuote(a.tk)).length} prices · ${_rt37Count().live} live`;', '${_rt42Ready() ? `${tickers.filter(a => hasSyncedQuote(a.tk)).length} prices · ${_rt37Count().live} live` : "syncing…"}`;')
# 9 jargon
R('rsi label', '<span style="color:var(--pu)">RSI(14) ${curRsi.toFixed(1)}</span><span style="color:var(--rd)">─ 70 OB</span><span style="color:var(--gn)">─ 30 OS</span>',
  '<span style="color:var(--pu)" title="Relative Strength Index, 14 days: above 70 = stretched higher, below 30 = stretched lower">Momentum (RSI) ${curRsi.toFixed(1)}</span><span style="color:var(--rd)" title="Above 70: stretched higher">─ 70 stretched</span><span style="color:var(--gn)" title="Below 30: stretched lower">─ 30 washed-out</span>')
R('chart legend', '<span style="color:var(--gd)">─ MA20</span><span style="color:var(--bl)">─ MA50</span><span style="color:var(--t3)">Vol bars</span>',
  '<span style="color:var(--gd)" title="Average closing price over the last 20 trading days">─ 20-day average</span><span style="color:var(--bl)" title="Average closing price over the last 50 trading days">─ 50-day average</span><span style="color:var(--t3)">Volume</span>')
R('chart hdr', '>MA20 MA50 RSI(14) Vol</span>', ' title="Moving averages, momentum (RSI) and volume">20/50-day averages · momentum · volume</span>')
R('sc header', '<th>SC</th>', '<th title="Dispatch conviction score, 0–100">SCORE</th>', 2)
R('byok 1', '<li><strong>BYOK AI</strong> — connect your keys; you control token cost (next)</li>', '<li><strong>Your own AI key</strong> — connect your AI provider and control the cost (coming soon)</li>')
R('byok 2', 'Premium adds the weekly Gold Playbook and BYOK AI for £15/month.', 'Premium adds the weekly Gold Playbook and the AI research assistant for £15/month.')
BLOCK = r'''// ── rt42 ──
// one shared count: neutral "Syncing…" until the first full snapshot
let _rt42ReadyAt = 0;
function _rt42Ready() {
  if (_rt42ReadyAt) return true;
  try { const c = _rt37Count(); if (c.priced && (c.priced >= c.total * 0.9 || performance.now() > 20000)) { _rt42ReadyAt = Date.now(); return true; } } catch (e) {}
  return false;
}
{
  const _sum0 = _rt37Sum; _rt37Sum = function () { return _rt42Ready() ? _sum0.apply(this, arguments) : "Syncing…"; };
  const _hero0 = _rt37Hero; _rt37Hero = function () { return _rt42Ready() ? _hero0.apply(this, arguments) : "Syncing…"; };
  try { const _qs0 = quoteStatusSummary; quoteStatusSummary = function () { return _rt42Ready() ? _qs0.apply(this, arguments) : "syncing…"; }; } catch (e) {}
}
// Ask/intel text: drop "not provided" sentences by SENTENCE (never across a decimal point), and only when they carry no figures
{
  const _tx0 = _rt32Txt;
  _rt32Txt = function (t, tk) {
    if (typeof t !== "string") return _tx0.apply(this, arguments);
    const parts = _rt28Split(t);
    const kept = parts.filter(p => !(/\b(?:not\s+(?:provided|available|supplied|specified))\b/i.test(p) && !/\d/.test(p)));
    const cleaned = kept.length === parts.length ? t : kept.join(" ");
    // bypass the rt38 regex remover (it could cut "50.3x"): call the original rt32 chain without it
    return _rt42TxtBase ? _rt42TxtBase(cleaned, tk) : cleaned;
  };
}
// watchlist repaints when its quotes arrive; XAU change from the previous close everywhere
{
  const _lc0 = liveChg;
  liveChg = function (tk) { const r = _lc0.apply(this, arguments); return r == null && tk === "XAU" ? _rt39Chg("XAU") : r; };
  let sig = "";
  setInterval(() => { try {
    if (pg !== "watch" || IS_DESKTOP()) return;
    const ae = document.activeElement; if (ae && /^(INPUT|TEXTAREA|SELECT)$/.test(ae.tagName)) return;
    const s2 = (getActiveWl().tickers || []).map(t => t + ":" + (hasSyncedQuote(t) ? 1 : 0) + ":" + liveChg(t)).join("|");
    if (s2 !== sig) { const first = !sig; sig = s2; if (!first) renderMain(); }
  } catch (e) {} }, 2500);
}
// P/E guard: judge a sentence only against the tickers it names; figures for a peer we hold no client data for
// (the server injects those) are kept rather than dropped
{
  const _nm = tk => { const a = A.find(x => x.tk === tk); return a && a.nm ? String(a.nm).split(/[\s(,]/)[0] : ""; };
  const _names = s => { const out = new Set(); try { (s.match(/\b[A-Z]{1,5}\b/g) || []).forEach(t => { if (A.some(a => a.tk === t) || _finCache[t]) out.add(t); });
    A.forEach(a => { const n = _nm(a.tk); if (n.length > 3 && new RegExp("\\b" + n.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\b").test(s)) out.add(a.tk); }); } catch (e) {} return [...out]; };
  const _g0 = _rt33Guard;
  _rt33Guard = function (s, tk) {
    if (typeof s !== "string" || !/P\/E|market cap/i.test(s)) return s;
    const parts = _rt28Split(s);
    const out = parts.filter(p => {
      if (!/P\/E|market cap/i.test(p)) return true;
      const named = _names(p);
      if (named.length && named.some(t => !(_finCache[t] && _rt33Val(t)))) return true;
      return _g0(p, tk) === p;
    });
    return out.length === parts.length ? s : out.join(" ");
  };
}
try { const spy = A.find(a => a.tk === "SPY"); if (spy) spy.beta = 1.0; } catch (e) {}
'''
R('rt42 block', 'const _rt23Ch = {};', BLOCK + 'const _rt23Ch = {};')
# capture the pre-rt38 _rt32Txt so the decimal-unsafe regex remover is bypassed
R('txt base', '  const _cl0 = _rt32Txt;\n  _rt32Txt = function () {', '  const _cl0 = _rt32Txt; _rt42TxtBase = _cl0;\n  _rt32Txt = function () {')
R('txt base decl', '// ── rt38 ──\n', '// ── rt38 ──\nvar _rt42TxtBase = null;\n')
for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
h = h.replace('app.js?v=chat38', 'app.js?v=chat39')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + index; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
