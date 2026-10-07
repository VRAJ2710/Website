#!/usr/bin/env python3
"""
patch_rt15.py — The Dispatch Markets: rt15 gold-desk server fix. SERVER ONLY (server.js; client untouched).

Usage (from the Replit workspace root, next to server.js):
    python3 patch_rt15.py --check          # dry run: verify every anchor (+ node --check if available), write nothing
    python3 patch_rt15.py                  # apply to server.js
    python3 patch_rt15.py --dir PATH       # server.js lives elsewhere

What it changes (/api/gold-desk only):
  1. The AI prompt gets real COMEX gold futures (GC=F) figures computed from the existing cached Yahoo chart
     fetch (fetchYahooChart "GC=F" 6mo/1d, 30s cache, in-flight de-dupe): price, prior close, % change, session and
     prior-day high/low, ATR(14), 20-day realised vol, 20/50-day averages, swing support/resistance with touches.
     The spot reference (gold-api.com) is labelled as having no daily change instead of sending changePct 0.
     The response's sessions / volatility / levels come from those computed figures (not AI guesses), and the
     playbook disclaimer states that levels and targets are futures prices with the spot basis.
  2. The generated desk is cached in memory for 10 minutes and shared by all premium readers; concurrent first
     requests share one generation; a forced Refresh inside the window is served from cache (no AI call).
     TTL is checked on read; no timers, no pollers. Failures are not cached.
  3. Source text: "Yahoo Finance market snapshot + xAI scenario analysis" -> "Spot: gold-api.com reference ·
     Levels and volatility: COMEX gold futures (GC=F) daily bars, Yahoo Finance, delayed · AI scenario analysis".
Applies only to the rt11b production server.js (the gold-desk handler it ships). Every edit is an exact-string
replacement with an expected match count; if any anchor fails, nothing is written. Refuses to run twice (rt15
marker). CRLF safe. Writes go to server.js.rt15.tmp first and are renamed into place only after every check passed.
"""
import argparse, os, shutil, subprocess, sys, tempfile

MARKER = "rt15: gold desk"
PREV_SIGNATURE = 'dataSource: "Yahoo Finance market snapshot + xAI scenario analysis",'

SERVER_EDITS = [
    ('gold desk cache constants + state',
     r'''const YAHOO_CHART_CACHE_MS = 30_000;''',
     r'''const YAHOO_CHART_CACHE_MS = 30_000;
// rt15: gold desk — one shared AI generation per 10 minutes (in memory, TTL checked on read, no pollers).
const GOLD_DESK_CACHE_MS = 10 * 60_000;
let goldDeskCache = null;      // { at, body }
let goldDeskInFlight = null;   // concurrent first requests share one generation''',
     1),
    ('gold futures stats + generator + cache (before normaliseGoldDesk)',
     r'''function normaliseGoldDesk(value, quotes) {''',
     r'''// ── rt15: gold desk grounded in COMEX gold futures (GC=F) daily bars + shared 10-minute result cache ──
// The figures come from the same cached /api/yahoo-chart fetch the browser uses (fetchYahooChart, 30s cache,
// in-flight de-dupe), so the server makes at most one extra Yahoo request per gold-desk generation.
function computeGoldFuturesStats(res) {
  const q = res?.indicators?.quote?.[0];
  const ts = res?.timestamp;
  if (!q || !Array.isArray(ts)) return null;
  const ok = v => typeof v === "number" && Number.isFinite(v) && v > 0;
  const bars = [];
  for (let i = 0; i < ts.length; i++) {
    const o = q.open?.[i], hi = q.high?.[i], lo = q.low?.[i], c = q.close?.[i];
    if (ok(o) && ok(hi) && ok(lo) && ok(c) && hi >= lo) bars.push({ t: ts[i] * 1000, h: hi, l: lo, c });
  }
  if (bars.length < 30) return null;
  const meta = res.meta || {};
  const last = bars[bars.length - 1];
  const prev = bars[bars.length - 2];
  const price = ok(meta.regularMarketPrice) ? meta.regularMarketPrice : last.c;
  const done = bars.slice(0, -1); // the latest bar may still be trading
  const trueRanges = [];
  for (let i = 1; i < done.length; i++) {
    const b = done[i], pc = done[i - 1].c;
    trueRanges.push(Math.max(b.h - b.l, Math.abs(b.h - pc), Math.abs(b.l - pc)));
  }
  const atr14 = trueRanges.length >= 14 ? trueRanges.slice(-14).reduce((a, b) => a + b, 0) / 14 : null;
  const closes = done.map(b => b.c);
  const rets = [];
  for (let i = Math.max(1, closes.length - 20); i < closes.length; i++) rets.push(Math.log(closes[i] / closes[i - 1]));
  let realizedVol20dPct = null;
  if (rets.length >= 19) {
    const mean = rets.reduce((a, b) => a + b, 0) / rets.length;
    realizedVol20dPct = Math.sqrt(rets.reduce((a, b) => a + (b - mean) ** 2, 0) / (rets.length - 1) * 252) * 100;
  }
  const sma = n => closes.length >= n ? closes.slice(-n).reduce((a, b) => a + b, 0) / n : null;
  const sma20 = sma(20), sma50 = sma(50);
  // Swing pivots: a session whose high (low) is above (below) the two sessions either side; last 90 sessions.
  const win = done.slice(-90), highs = [], lows = [];
  for (let i = 2; i < win.length - 2; i++) {
    const b = win[i], around = [win[i - 2], win[i - 1], win[i + 1], win[i + 2]];
    if (around.every(x => b.h > x.h)) highs.push(b.h);
    if (around.every(x => b.l < x.l)) lows.push(b.l);
  }
  const near = 0.003;
  const touches = (level, key) => win.filter(b => Math.abs(b[key] - level) / level <= near).length;
  const distinct = arr => arr.reduce((out, v) => (out.some(x => Math.abs(x - v) / v <= near) ? out : [...out, v]), []);
  const r2 = v => (v == null ? null : Math.round(v * 100) / 100);
  const resistance = distinct(highs.filter(v => v > price * 1.001).sort((a, b) => a - b)).slice(0, 2)
    .map(v => ({ level: r2(v), touches: touches(v, "h") }));
  const support = distinct(lows.filter(v => v < price * 0.999).sort((a, b) => b - a)).slice(0, 2)
    .map(v => ({ level: r2(v), touches: touches(v, "l") }));
  let trend = "mixed";
  if (sma20 && sma50) {
    if (price > sma20 && sma20 > sma50) trend = "uptrend";
    else if (price < sma20 && sma20 < sma50) trend = "downtrend";
  }
  const atrPct = atr14 ? (atr14 / price) * 100 : null;
  const day = t => new Date(t).toISOString().slice(0, 10);
  const asOfMs = Number(meta.regularMarketTime) > 0 ? Number(meta.regularMarketTime) * 1000 : last.t;
  return {
    instrument: "COMEX gold futures (GC=F), Yahoo Finance daily bars, delayed",
    asOf: new Date(asOfMs).toISOString(),
    price: r2(price),
    priorClose: r2(prev.c),
    changePct: prev.c ? r2((price / prev.c - 1) * 100) : null,
    session: {
      date: day(last.t),
      high: r2(ok(meta.regularMarketDayHigh) ? Math.max(meta.regularMarketDayHigh, last.h) : last.h),
      low: r2(ok(meta.regularMarketDayLow) ? Math.min(meta.regularMarketDayLow, last.l) : last.l),
    },
    priorDay: { date: day(prev.t), high: r2(prev.h), low: r2(prev.l) },
    atr14: r2(atr14),
    atr14PctOfPrice: r2(atrPct),
    realizedVol20dPct: r2(realizedVol20dPct),
    volatilityCondition: atrPct == null ? null : atrPct < 0.9 ? "low" : atrPct <= 1.8 ? "normal" : "elevated",
    sma20: r2(sma20),
    sma50: r2(sma50),
    trend,
    swingSupport: support,
    swingResistance: resistance,
    method: "ATR(14) = mean true range of the last 14 completed sessions; realised vol = annualised stdev of 20 daily log returns; swing levels = daily highs/lows above/below the two sessions either side within the last 90 sessions, touches = sessions within 0.3%.",
  };
}
async function goldFuturesStats() {
  const chart = await fetchYahooChart("GC=F", "6mo", "1d");
  if (chart?.unavailable) return null;
  return computeGoldFuturesStats(chart?.data?.chart?.result?.[0]);
}
function applyGoldFutures(desk, futures, spotPrice) {
  if (!futures) return desk;
  const basis = Number.isFinite(spotPrice) ? Math.round(futures.price - spotPrice) : null;
  const basisText = basis == null ? "" : ` Spot trades about $${Math.abs(basis)} ${basis >= 0 ? "below" : "above"} futures.`;
  const src = "COMEX gold futures (GC=F) daily bars, Yahoo Finance, delayed";
  return {
    ...desk,
    dataSource: `Spot: gold-api.com reference · Levels and volatility: ${src} · AI scenario analysis`,
    gold: { ...desk.gold, futures: { price: futures.price, priorClose: futures.priorClose, changePct: futures.changePct, asOf: futures.asOf } },
    levels: {
      support: futures.swingSupport.map(s => ({ level: s.level, strength: `Swing low · ${s.touches} touches · COMEX futures daily`, hits: s.touches })),
      resistance: futures.swingResistance.map(s => ({ level: s.level, strength: `Swing high · ${s.touches} touches · COMEX futures daily`, hits: s.touches })),
    },
    sessions: {
      sessionHigh: futures.session.high, sessionLow: futures.session.low,
      priorDayHigh: futures.priorDay.high, priorDayLow: futures.priorDay.low,
      source: src,
    },
    volatility: {
      condition: futures.volatilityCondition || desk.volatility?.condition || "Monitor",
      atr14: futures.atr14,
      realizedVol20dPct: futures.realizedVol20dPct,
    },
    playbook: {
      ...desk.playbook,
      disclaimer: `Conditional research scenario — not investment advice. Levels and targets are COMEX gold futures (GC=F) prices.${basisText}`,
    },
  };
}
async function generateGoldDesk() {
  const [references, quotes, futures] = await Promise.all([
    withTimeout(marketReferenceQuotes(), 8000, "Reference market data timed out."),
    withTimeout(yahooQuote(["^TNX", "^VIX"]), 8000, "Gold market data timed out. Please try again."),
    withTimeout(goldFuturesStats(), 8000, "Gold futures data timed out.").catch(() => null),
  ]);
  const spot = references.XAU;
  const spotHasChange = Boolean(spot && !spot.proxy && Number.isFinite(Number(spot.c)));
  const snapshot = {
    goldSpot: spot ? {
      price: spot.p,
      source: spot.name || "Spot gold reference",
      asOf: spot.ts ? new Date(spot.ts * 1000).toISOString() : null,
      ...(spotHasChange ? { changePct: spot.c } : { changePct: "not available from this spot source - use goldFutures for the daily change" }),
    } : "unavailable",
    goldFutures: futures || "unavailable",
    dollarIndex: references.DXY, treasury10Year: quotes["^TNX"], vix: quotes["^VIX"],
    asOf: new Date().toISOString(),
  };
  const grounding = futures
    ? "Gold levels: base the daily change, session ranges, volatility (ATR, realised vol) and support/resistance on goldFutures and say they are COMEX futures prices; express all levels and targets in futures prices. Do not describe price action as flat unless goldFutures.changePct is near zero."
    : "Gold futures figures are unavailable: do not state a daily change, ATR or support/resistance levels; describe them as unavailable.";
  const result = await generateAi({
    system: `${MARKET_SYSTEM}\nCreate a conditional weekly gold research playbook from this market snapshot. Return ONLY valid JSON: {"structure":{"regime":"string","bias":"bullish|bearish|range","summary":"string"},"levels":{"support":[{"level":0,"strength":"string"}],"resistance":[{"level":0,"strength":"string"}]},"volatility":{"condition":"string","atr14":0,"realizedVol20dPct":0},"events":[{"date":"string","event":"string","impact":"low|medium|high","cat":"string","goldNote":"string"}],"playbook":{"weekId":"string","weekLabel":"string","regime":{"bias":"bullish|bearish|range","summary":"string"},"macroContext":["string"],"scenarios":{"bullish":{"title":"string","thesis":"string","entry":"string","invalidation":"string","targets":[0]},"bearish":{"title":"string","thesis":"string","entry":"string","invalidation":"string","targets":[0]},"range":{"title":"string","thesis":"string","entry":"string","invalidation":"string","targets":[0]}},"checklist":["string"]}}. Use the supplied snapshot only; state uncertainty rather than inventing events or prices. ${grounding} The snapshot is in the user message.`,
    // Snapshot goes in the user turn: provider calls clip the system prompt at 5000 chars, user turns at 6000.
    messages: [{ role: "user", content: `Generate the weekly gold desk playbook from this market snapshot.\nSNAPSHOT:\n${clipped(JSON.stringify(snapshot), 5800)}` }],
    maxTokens: 1800,
    validate: text => validateGoldDeskResponse(text, { ...quotes, "GC=F": references.XAU, "DX-Y.NYB": references.DXY }),
  });
  const desk = result.validated || validateGoldDeskResponse(result.text, { ...quotes, "GC=F": references.XAU, "DX-Y.NYB": references.DXY });
  return { ...applyGoldFutures(desk, futures, Number(spot?.p)), meta: { provider: result.provider, model: result.model } };
}
async function goldDeskPayload() {
  const stamp = (at, hit) => ({ hit, generatedAt: new Date(at).toISOString(), expiresAt: new Date(at + GOLD_DESK_CACHE_MS).toISOString() });
  if (goldDeskCache && Date.now() - goldDeskCache.at < GOLD_DESK_CACHE_MS) {
    return { hit: true, body: { ...goldDeskCache.body, cache: stamp(goldDeskCache.at, true) } };
  }
  if (goldDeskInFlight) return goldDeskInFlight; // concurrent requests share one generation
  const pending = (async () => {
    const body = await generateGoldDesk();
    const at = Date.now();
    goldDeskCache = { at, body };
    return { hit: false, body: { ...body, cache: stamp(at, false) } };
  })();
  goldDeskInFlight = pending;
  try {
    return await pending;
  } finally {
    if (goldDeskInFlight === pending) goldDeskInFlight = null;
  }
}
function normaliseGoldDesk(value, quotes) {''',
     1),
    ("source text: no 'xAI'",
     r'''    dataSource: "Yahoo Finance market snapshot + xAI scenario analysis",''',
     r'''    dataSource: "Spot: gold-api.com reference · AI scenario analysis",''',
     1),
    ('spot proxy carries no change: null, not 0',
     r'''    gold: { price, changePct: asNumber(gold?.c), spark: [] },''',
     r'''    gold: { price, changePct: gold?.proxy && !asNumber(gold?.c) ? null : asNumber(gold?.c), spark: [] }, // rt15: a proxy without a prior close has no change''',
     1),
    ('sessions source default',
     r'''    sessions: { source: "Yahoo Finance snapshot" },''',
     r'''    sessions: { source: "Unavailable without futures data" },''',
     1),
    ('/api/gold-desk handler -> cached generator',
     r'''      if (p === "/api/gold-desk") {
        const [references, quotes] = await Promise.all([
          withTimeout(marketReferenceQuotes(), 8000, "Reference market data timed out."),
          withTimeout(yahooQuote(["^TNX", "^VIX"]), 8000, "Gold market data timed out. Please try again."),
        ]);
        const snapshot = {
          gold: references.XAU, dollarIndex: references.DXY, treasury10Year: quotes["^TNX"], vix: quotes["^VIX"],
          asOf: new Date().toISOString(),
        };
        const result = await generateAi({
          system: `${MARKET_SYSTEM}\nCreate a conditional weekly gold research playbook from this market snapshot. Return ONLY valid JSON: {"structure":{"regime":"string","bias":"bullish|bearish|range","summary":"string"},"levels":{"support":[{"level":0,"strength":"string"}],"resistance":[{"level":0,"strength":"string"}]},"volatility":{"condition":"string","atr14":0,"realizedVol20dPct":0},"events":[{"date":"string","event":"string","impact":"low|medium|high","cat":"string","goldNote":"string"}],"playbook":{"weekId":"string","weekLabel":"string","regime":{"bias":"bullish|bearish|range","summary":"string"},"macroContext":["string"],"scenarios":{"bullish":{"title":"string","thesis":"string","entry":"string","invalidation":"string","targets":[0]},"bearish":{"title":"string","thesis":"string","entry":"string","invalidation":"string","targets":[0]},"range":{"title":"string","thesis":"string","entry":"string","invalidation":"string","targets":[0]}},"checklist":["string"]}}. Use the supplied snapshot only; state uncertainty rather than inventing events or prices.\nSNAPSHOT:\n${clipped(JSON.stringify(snapshot), 6000)}`,
          messages: [{ role: "user", content: "Generate the weekly gold desk playbook." }],
          maxTokens: 1800,
            validate: text => validateGoldDeskResponse(text, {
              ...quotes,
              "GC=F": references.XAU,
              "DX-Y.NYB": references.DXY,
            }),
        });
        return json(res, 200, { ...(result.validated || validateGoldDeskResponse(result.text, {
          ...quotes,
          "GC=F": references.XAU,
          "DX-Y.NYB": references.DXY,
        })), meta: { provider: result.provider, model: result.model } });
      }''',
     r'''      if (p === "/api/gold-desk") {
        // rt15: served from the shared 10-minute cache; a forced client Refresh inside the window does not call the AI.
        const desk = await goldDeskPayload();
        return json(res, 200, desk.body, { "X-Dispatch-Data-Status": desk.hit ? "cached" : "fresh" });
      }''',
     1),
    ('exports for tests',
     r'''  validateGoldDeskResponse,
  normaliseGoldDesk,
''',
     r'''  validateGoldDeskResponse,
  normaliseGoldDesk,
  computeGoldFuturesStats,
  applyGoldFutures,
  goldDeskPayload,
''',
     1),
]

def load(path):
    with open(path, "rb") as f:
        raw = f.read().decode("utf-8")
    crlf = "\r\n" in raw
    return raw.replace("\r\n", "\n"), crlf


def apply(text, edits, label, errors):
    for name, old, new, want in edits:
        n = text.count(old)
        if n != want:
            errors.append(f"{label}: '{name}' anchor matched {n} times (need exactly {want})")
            continue
        text = text.replace(old, new)
    return text


def node_check(js_text, errors, required):
    node = shutil.which("node")
    if not node:
        if required:
            errors.append("node not found on PATH for `node --check`")
        else:
            print("WARN: node not found; server.js not syntax-checked")
        return
    fd, tmp = tempfile.mkstemp(suffix=".js")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(js_text.encode("utf-8"))
        r = subprocess.run([node, "--check", tmp], capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            errors.append(f"server.js: node --check failed: {(r.stderr or r.stdout).strip()[:400]}")
    finally:
        try: os.remove(tmp)
        except OSError: pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="dry run; write nothing")
    ap.add_argument("--dir", default=".", help="folder containing server.js")
    a = ap.parse_args()
    srv_p = os.path.join(a.dir, "server.js")
    if not os.path.isfile(srv_p):
        sys.exit(f"ABORT: {srv_p} not found — nothing written")
    srv, crlf = load(srv_p)
    if MARKER in srv:
        sys.exit("ABORT: rt15 already applied (marker found) — refusing to run twice; nothing written")
    if PREV_SIGNATURE not in srv:
        sys.exit("ABORT: this is not the expected production server.js (gold-desk source signature missing) — nothing written")
    errors = []
    new_srv = apply(srv, SERVER_EDITS, "server.js", errors)
    if not errors:
        tail = new_srv.split('if (p === "/api/gold-desk") {', 1)[-1][:600]
        if (new_srv.count(MARKER) != 2 or "xAI scenario" in new_srv or new_srv.count("async function goldDeskPayload(") != 1
                or new_srv.count("function computeGoldFuturesStats(") != 1 or "goldDeskPayload()" not in tail
                or "generateAi(" in tail):
            errors.append("post-edit sanity check failed")
        node_check(new_srv, errors, required=False)
    if errors:
        print("ABORT — no files written:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print(f"OK: {len(SERVER_EDITS)} server.js edits verified (server.js {len(new_srv) - len(srv):+d} chars); client files not touched")
    if a.check:
        print("--check: dry run, nothing written")
        return
    text = new_srv.replace("\n", "\r\n") if crlf else new_srv
    tmp = srv_p + ".rt15.tmp"
    try:
        with open(tmp, "wb") as f:
            f.write(text.encode("utf-8"))
    except Exception as e:
        try: os.remove(tmp)
        except OSError: pass
        sys.exit(f"ABORT: could not stage output ({e}) — nothing written")
    os.replace(tmp, srv_p)
    print("Written: server.js")


if __name__ == "__main__":
    main()
