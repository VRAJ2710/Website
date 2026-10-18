#!/usr/bin/env python3
"""
patch_rt12.py — The Dispatch Markets: rt12 follow-up (chat11 -> chat12). CLIENT ONLY (server.js untouched).

Usage (from the Replit workspace root, next to app.js and index.html):
    python3 patch_rt12.py --check          # dry run: verify every anchor (+ node --check if available), write nothing
    python3 patch_rt12.py                  # apply app.js + index.html
    python3 patch_rt12.py --dir PATH       # files live elsewhere

Applies only on top of the live chat11 files (rt11 layer present). Every edit is an exact-string
replacement that must match exactly the stated number of times (1 unless noted); if any anchor fails,
nothing is written. Refuses to run twice (rt12 marker / chat12). CRLF safe. Writes go to *.rt12.tmp
first and are renamed into place only after every check passed.
No new endpoint, no new upstream request, no new background work; chart fetches are fewer, not more.
"""
import argparse, os, shutil, subprocess, sys, tempfile

MARKER = "REALTIME PRICE LAYER (rt12)"
PREV_MARKER = "REALTIME PRICE LAYER (rt11)"

RT11_MODULE = r'''// ═══════════════════════════════════════════════════════════
// REALTIME PRICE LAYER (rt11) — browser-direct, free, keyless.
// No server connection is held open: every socket below goes straight from
// the visitor's browser to a public market-data stream, so Replit compute is
// untouched. Sources (measured from a browser on thedispatch.uk origin):
//   • Coinbase Exchange WS ticker (USD crypto + PAXG) — trade-by-trade
//   • Kraken WS v2 ticker — automatic fallback for crypto if Coinbase fails
//   • Yahoo Finance public stream — FX ~1s; US stocks/ETFs during the
//     regular session; indices/futures arrive with the exchange's delay and
//     are labelled DELAYED Nm from the tick's own timestamp
//   • gold-api.com XAU (CORS *, keyless, no rate limit) — spot proxy that
//     updates every ~30s; polled just after each expected update
// Ticks set P[tk] immediately; the DOM is repainted at most once a second,
// in place, for the tickers that actually changed. Hidden tab = everything
// closed. Kill switch: localStorage td_rt_off = "1".
// rt10: one 24h change basis for crypto (rolling 24h: stream > CoinGecko),
// an older print never replaces a newer one, honest crypto-page header,
// consistent crypto decimals, gold "checked" time, chart placeholders resolve.
// rt11: crypto 24h basis ranked stream > Yahoo rolling-24h > CoinGecko (unknown bases show "—"),
// /crypto/ table + strip + card read the desk quote, no fake 0.00% on basis-less proxies,
// live status-line recount, phone name column, spark hide also while a fetch is queued.
// ═══════════════════════════════════════════════════════════
const RT_CB_URL = "wss://ws-feed.exchange.coinbase.com";
const RT_KR_URL = "wss://ws.kraken.com/v2";
const RT_YS_URL = "wss://streamer.finance.yahoo.com/?version=2";
const RT_GOLD_URL = "https://api.gold-api.com/price/XAU";
// Per-source switches (flip to false and re-publish to drop a source; the 60s loop still covers it).
const RT_USE = Object.freeze({ crypto: true, yahoo: true, gold: true });
// internal ticker -> [Coinbase product, Kraken v2 symbol]
const RT_CRYPTO = Object.freeze({
  BTC: ["BTC-USD", "BTC/USD"], ETH: ["ETH-USD", "ETH/USD"], SOL: ["SOL-USD", "SOL/USD"],
  XRP: ["XRP-USD", "XRP/USD"], DOGE: ["DOGE-USD", "DOGE/USD"], ADA: ["ADA-USD", "ADA/USD"],
  AVAX: ["AVAX-USD", "AVAX/USD"], LINK: ["LINK-USD", "LINK/USD"], DOT: ["DOT-USD", "DOT/USD"],
  LTC: ["LTC-USD", "LTC/USD"], UNI: ["UNI-USD", "UNI/USD"], NEAR: ["NEAR-USD", "NEAR/USD"],
  ALGO: ["ALGO-USD", "ALGO/USD"], HBAR: ["HBAR-USD", "HBAR/USD"], BCH: ["BCH-USD", "BCH/USD"],
  XLM: ["XLM-USD", "XLM/USD"], FIL: ["FIL-USD", "FIL/USD"], APT: ["APT-USD", "APT/USD"],
  SUI: ["SUI-USD", "SUI/USD"], ATOM: ["ATOM-USD", "ATOM/USD"], INJ: ["INJ-USD", "INJ/USD"],
  SHIB: ["SHIB-USD", "SHIB/USD"], PEPE: ["PEPE-USD", "PEPE/USD"], MATIC: ["POL-USD", "POL/USD"],
  TON: [null, "TON/USD"],
  PAXG: ["PAXG-USD", "PAXG/USD"], // secondary gold line only — never written into P.XAU
});
const RT_SRC = new Set(["coinbase-ws", "kraken-ws", "yahoo-stream", "gold-api-spot-proxy-browser"]);
const RT_HOLD_MS = 90_000;     // a polled value may not overwrite a stream tick younger than this
const RT_PAINT_MS = 1000;      // DOM repaint cadence (max once per second)
const RT_SCAN_MS = 3000;       // re-derive the visible symbol set
const RT_FAST_POLL_MS = 15_000;// visible, non-streaming symbols via the cached server proxy
const RT_YS_CAP_DESK = 150, RT_YS_CAP_PHONE = 40;
const RT_ROLL_RANK = Object.freeze({ stream: 3, y24: 2, cg: 1 });
const _rt = {
  running: false, booted: false, dirty: new Set(), dir: {}, lastRecv: {}, lag: {}, goodPrev: {},
  sock: {}, attempts: {}, gotData: {}, lastMsg: {}, reconnectT: {}, timers: [],
  want: new Set(), visible: new Set(), subd: { cb: new Set(), kr: new Set(), ys: new Set() },
  cryptoProv: 0, provFails: 0, paxg: null, goldT: null, ysRev: null, emptySince: {},
  roll: {}, cgAt: 0, goldChecked: 0, cryptoSet: null, sparkTk: {}, sparkFail: {}, hdrAt: 0, cgRefetchAt: 0,
  stats: { msgs: { cb: 0, kr: 0, ys: 0 }, ticks: 0, paints: 0, cells: 0, goldPolls: 0, fastPolls: 0,
    connects: { cb: 0, kr: 0, ys: 0 }, closes: 0, pauses: 0, resumes: 0, errors: 0 },
};
window._rtStats = () => ({
  running: _rt.running, hidden: document.hidden, provider: _rt.cryptoProv ? "kraken" : "coinbase",
  sockets: Object.fromEntries(Object.entries(_rt.sock).map(([k, s]) => [k, s ? s.readyState : null])),
  subscribed: { cb: [..._rt.subd.cb], kr: [..._rt.subd.kr], ys: [..._rt.subd.ys] },
  want: [..._rt.want], paxg: _rt.paxg, ..._rt.stats,
});

function _rtDisabled() {
  try { if (localStorage.getItem("td_rt_off") === "1") return true; } catch (e) {}
  return (typeof updatePaused !== "undefined" && updatePaused) || (typeof updateFreq !== "undefined" && updateFreq === 0);
}
function _rtLagMs(tk) { return _rt.lag[tk] || 0; }
function _rtIsCrypto(tk) {
  if (!_rt.cryptoSet) {
    const s = new Set(Object.keys(RT_CRYPTO)); s.delete("PAXG");
    try { Object.values(CG_MAP).forEach(t => s.add(t)); } catch (e) {}
    _rt.cryptoSet = s;
  }
  return _rt.cryptoSet.has(tk) || (typeof TICKER_CATS !== "undefined" && TICKER_CATS[tk] === "cry");
}
/** One crypto price format everywhere: 2 dp at $1 and above, at least 4 dp (≈4 significant figures) below $1. */
function _rtStreamable(tk) {
  if (tk === "XAU" || _rtIsCrypto(tk)) return true;
  const yh = typeof YAHOO_SYMBOLS !== "undefined" && YAHOO_SYMBOLS[tk];
  return !!(yh && _rtYahooRev()[yh] && !_rtIsUsEquitySym(yh));
}
function _rtCryptoPx(v) {
  if (typeof v !== "number" || !isFinite(v) || v <= 0) return "—";
  if (v >= 1) return v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return v.toFixed(Math.min(10, Math.max(4, Math.ceil(-Math.log10(v)) + 3)));
}
function _rtIsUsEquitySym(yh) { return /^[A-Z][A-Z.\-]{0,6}$/.test(yh || ""); }
function _rtWeekend() {
  try {
    const p = Object.fromEntries(new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", weekday: "short", hour: "2-digit", hour12: false }).formatToParts(new Date()).map(x => [x.type, x.value]));
    const h = Number(p.hour) % 24;
    return p.weekday === "Sat" || (p.weekday === "Sun" && h < 17) || (p.weekday === "Fri" && h >= 17);
  } catch (e) { return false; }
}
function _rtYahooRev() {
  if (_rt.ysRev) return _rt.ysRev;
  const rev = {};
  Object.entries(YAHOO_SYMBOLS).forEach(([tk, yh]) => {
    if (!yh || tk === "XAU" || RT_CRYPTO[tk] || /-USD$/.test(yh)) return; // gold spot & crypto have their own feeds
    (rev[yh] = rev[yh] || []).push(tk);
  });
  return (_rt.ysRev = rev);
}

/** Lightweight apply for streamed ticks: price, change vs prior close, source, provider time. */
function _rtApply(tk, p, o) {
  if (!tk || typeof p !== "number" || !isFinite(p) || p <= 0) return false;
  const now = Date.now();
  let ts = Number(o.ts);
  if (!(ts > 0) || ts > now + 60_000) ts = now;
  if (RT_SRC.has(liveQuoteSrc[tk]) && liveQuoteTs[tk] && ts < liveQuoteTs[tk]) return false; // never step back in time
  let prev = (typeof o.prev === "number" && isFinite(o.prev) && o.prev > 0) ? o.prev : null;
  if (prev == null && !o.noBasePrev && _rt.goodPrev[tk] > 0) prev = _rt.goodPrev[tk];
  const oldP = P[tk] && liveSymbols.has(tk) ? P[tk].p : null;
  P[tk] = { p, c: prev ? +(((p - prev) / prev) * 100).toFixed(2) : 0 };
  if (prev) BASE[tk] = { p: prev, c: 0 };
  if (prev && (o.src === "coinbase-ws" || o.src === "kraken-ws")) _rt.roll[tk] = { prev, at: now, kind: "stream" };
  liveSymbols.add(tk);
  liveQuoteTs[tk] = ts;
  liveQuoteSrc[tk] = o.src;
  if (o.name) liveQuoteName[tk] = o.name;
  else if (liveQuoteProxy[tk] && !o.proxy) liveQuoteName[tk] = ""; // don't keep a proxy's name on a real print
  liveQuoteCached[tk] = false;
  liveQuoteChangeAvailable[tk] = prev != null;
  liveQuoteProxy[tk] = !!o.proxy;
  liveQuoteMarketClosed[tk] = false;
  liveQuoteSession[tk] = null;
  _rt.lastRecv[tk] = now;
  _rt.lag[tk] = Math.max(0, now - ts);
  _rt.stats.ticks++;
  if (oldP !== p) { _rt.dirty.add(tk); _rt.dir[tk] = oldP == null ? 0 : (p > oldP ? 1 : -1); }
  else if (o.repaint) { _rt.dirty.add(tk); _rt.dir[tk] = 0; } // same value, new as-of: repaint without a flash
  return true;
}
/** Called from _applyLiveQuote (every polled/server quote). Returning true = keep what we have. */
function _rtGuard(tk, q, source) {
  const src = String(q.source || source || "");
  const now = Date.now();
  const proxyish = !!q.proxy || src.startsWith("gold-api-spot-proxy") || src === "frankfurter-ecb" || src === "open-exchange-rate-api";
  const fin = v => typeof v === "number" && isFinite(v);
  // 0) A quote whose server says it has no real prior close carries no change at all ("—", never a fake 0.00%).
  if (q.basis === "none") { delete q.c; delete q.prev; delete q.change; }
  // Basis-less spot proxies (gold-api returns prev = price, c = 0): use the session's spot prior close if one is
  // known (Twelve Data XAU/USD), otherwise show no change.
  if (src.startsWith("gold-api-spot-proxy") && !(fin(q.prev) && q.prev > 0 && Math.abs(q.prev - q.p) > 1e-9 && q.c !== 0)) {
    const gp = _rt.goodPrev[tk];
    if (gp > 0) { q.prev = gp; q.c = ((q.p - gp) / gp) * 100; } else { delete q.c; delete q.prev; delete q.change; }
  }
  // 1) Crypto: ONE 24h basis per ticker. Ranked: exchange stream (Coinbase open_24h / Kraken) > Yahoo rolling 24h
  //    (server basis "rolling_24h") > CoinGecko 24h. A lower-ranked source is re-based onto the best basis seen in
  //    the last 30 min; a source with an unknown basis (old Yahoo 5-day prev close, Twelve Data/Finnhub day basis)
  //    shows its price but no change until a 24h basis is known.
  if (_rtIsCrypto(tk) && !RT_SRC.has(src) && fin(q.p) && q.p > 0) {
    const r = _rt.roll[tk], rOk = r && r.prev > 0 && now - r.at < 30 * 60_000;
    const c = Number(q.c);
    let kind = null, own = null;
    if (src === "coingecko" && isFinite(c) && c > -100) { kind = "cg"; own = q.p / (1 + c / 100); }
    else if (src.startsWith("yahoo") && q.basis === "rolling_24h" && fin(q.prev) && q.prev > 0) { kind = "y24"; own = q.prev; }
    if (kind && (!rOk || RT_ROLL_RANK[kind] >= (RT_ROLL_RANK[r.kind] || 0))) {
      // A server-cached quote may still set the basis when its own timestamp is recent (short response cache);
      // an old cached print (stale fallback) never does.
      const qr = Number(q.ts ?? q.fetchedAt), qMs = qr > 0 && qr < 10_000_000_000 ? qr * 1000 : qr;
      if (!q.cached || (qMs > 0 && now - qMs < 5 * 60_000)) _rt.roll[tk] = { prev: own, at: now, kind };
      q.prev = own; q.c = ((q.p - own) / own) * 100;
    } else if (rOk) {
      q.prev = r.prev; q.c = ((q.p - r.prev) / r.prev) * 100;
    } else if (!kind) {
      delete q.c; delete q.prev; delete q.change;
    }
  }
  const hasPrev = typeof q.prev === "number" && isFinite(q.prev) && q.prev > 0;
  // Spot gold's prior close only from a spot feed (Yahoo XAU maps to futures, a different basis).
  if (hasPrev && !proxyish && !RT_SRC.has(src) && !_rtIsCrypto(tk) && (tk !== "XAU" || src === "twelve-data")) _rt.goodPrev[tk] = q.prev;
  if (RT_SRC.has(src)) return false;
  const adoptPrev = () => {
    // Keep the fresher price, but adopt a missing prior close.
    if (hasPrev && !proxyish && liveQuoteChangeAvailable[tk] === false && P[tk]?.p > 0) {
      BASE[tk] = { p: q.prev, c: 0 };
      P[tk].c = +(((P[tk].p - q.prev) / q.prev) * 100).toFixed(2);
      liveQuoteChangeAvailable[tk] = true;
      _rt.dirty.add(tk);
    }
    return true;
  };
  // 2) A live stream tick younger than RT_HOLD_MS is never overwritten by a poll.
  if (RT_SRC.has(liveQuoteSrc[tk]) && now - (_rt.lastRecv[tk] || 0) <= RT_HOLD_MS) return adoptPrev();
  // 3) Tickers a stream covers (crypto, gold, FX/indices/futures): an older print never replaces a newer one
  //    (stale server cache, delayed fallback, …). US stocks keep the existing last-poll-wins behaviour because
  //    Yahoo stamps trade time while Twelve Data stamps fetch time, so their clocks are not comparable.
  if (!_rtStreamable(tk)) return false;
  const raw = Number(q.ts ?? q.fetchedAt);
  const inTs = raw > 0 && raw < 10_000_000_000 ? raw * 1000 : raw;
  const curTs = Number(liveQuoteTs[tk]);
  if (liveSymbols.has(tk) && P[tk]?.p > 0 && curTs > 0 && inTs > 0 && inTs < curTs - 5000) return adoptPrev();
  return false;
}

// ── Yahoo stream protobuf (PricingData) — tiny decoder, no dependency ──
function _rtDecodeYs(b64) {
  const bin = atob(b64), n = bin.length, b = new Uint8Array(n);
  for (let i = 0; i < n; i++) b[i] = bin.charCodeAt(i);
  const dv = new DataView(b.buffer);
  let i = 0; const o = {};
  const varint = () => { let r = 0, m = 1, x; do { x = b[i++]; r += (x & 0x7f) * m; m *= 128; } while (x & 0x80 && i < n); return r; };
  const zz = v => (v % 2 === 1 ? -(v + 1) / 2 : v / 2);
  while (i < n) {
    const key = varint(), f = Math.floor(key / 8), wt = key & 7;
    if (wt === 0) o[f] = varint();
    else if (wt === 5) { o[f] = dv.getFloat32(i, true); i += 4; }
    else if (wt === 1) { o[f] = dv.getFloat64(i, true); i += 8; }
    else if (wt === 2) { const len = varint(); if (f === 1) o[f] = new TextDecoder().decode(b.subarray(i, i + len)); i += len; }
    else break;
  }
  const hint = o[27] != null ? zz(o[27]) : null;
  const round = v => (typeof v === "number" && isFinite(v)) ? (hint != null && hint >= 0 && hint <= 8 ? +v.toFixed(hint) : +v.toPrecision(7)) : null;
  return { id: o[1], price: round(o[2]), time: o[3] != null ? zz(o[3]) : null, mh: o[7], change: round(o[12]) };
}
function _rtOnYs(ev) {
  _rt.stats.msgs.ys++;
  let m; try { m = JSON.parse(ev.data); } catch (e) { return; }
  if (!m || m.type !== "pricing" || !m.message) return;
  let d; try { d = _rtDecodeYs(m.message); } catch (e) { return; }
  if (!d.id || !(d.price > 0)) return;
  const tks = _rtYahooRev()[d.id];
  if (!tks) return;
  if (_rtIsUsEquitySym(d.id)) {
    // Stocks/ETFs: regular session only — extended-hours prints keep the existing RTH CLOSE handling.
    if (!_usRegularOpen()) return;
  }
  const prev = d.change != null ? d.price - d.change : null;
  tks.forEach(tk => _rtApply(tk, d.price, { src: "yahoo-stream", ts: d.time, prev: prev > 0 ? prev : null, name: tk === "DXY" ? "US Dollar Index" : undefined }));
}
function _rtOnCb(ev) {
  _rt.stats.msgs.cb++;
  let m; try { m = JSON.parse(ev.data); } catch (e) { return; }
  if (!m || m.type !== "ticker" || !m.product_id) return;
  const p = Number(m.price), open = Number(m.open_24h), ts = Date.parse(m.time) || Date.now();
  if (m.product_id === "PAXG-USD") { _rtPaxg(p, ts, "Coinbase"); return; }
  const tk = _rtCbRev()[m.product_id];
  if (tk) _rtApply(tk, p, { src: "coinbase-ws", ts, prev: open > 0 ? open : null, noBasePrev: true });
}
function _rtOnKr(ev) {
  _rt.stats.msgs.kr++;
  let m; try { m = JSON.parse(ev.data); } catch (e) { return; }
  if (!m || m.channel !== "ticker" || !Array.isArray(m.data)) return;
  m.data.forEach(row => {
    const p = Number(row.last), ch = Number(row.change);
    if (row.symbol === "PAXG/USD") { _rtPaxg(p, Date.now(), "Kraken"); return; }
    const tk = _rtKrRev()[row.symbol];
    if (tk) _rtApply(tk, p, { src: "kraken-ws", ts: Date.now(), prev: isFinite(ch) && p - ch > 0 ? p - ch : null, noBasePrev: true });
  });
}
function _rtCbRev() { return _rt.cbRev || (_rt.cbRev = Object.fromEntries(Object.entries(RT_CRYPTO).filter(([, v]) => v[0]).map(([tk, v]) => [v[0], tk]))); }
function _rtKrRev() { return _rt.krRev || (_rt.krRev = Object.fromEntries(Object.entries(RT_CRYPTO).filter(([, v]) => v[1]).map(([tk, v]) => [v[1], tk]))); }
function _rtPaxg(p, ts, venue) {
  if (!(p > 0)) return;
  const old = _rt.paxg?.p;
  _rt.paxg = { p, ts, venue, recv: Date.now() };
  if (old !== p || !_rt.paxgPainted) _rt.dirty.add("PAXG");
}
/** Secondary gold line for the XAU tile — clearly a tokenised-gold proxy, never the spot headline. */
function _rtPaxgLine() {
  const x = _rt.paxg;
  if (!x || Date.now() - x.recv > 10 * 60_000) return "";
  const px = x.p.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const age = _fmtAge(x.ts);
  return `<div class="front-door-quote-paxg" title="PAX Gold (PAXG) trading on ${_escAttr(x.venue)} — a tokenised-gold proxy that can sit at a premium or discount to spot. Not the XAU spot price.">PAXG ≈ $${_escHtml(px)} · ${_escHtml(x.venue)} stream · tokenised-gold proxy · last trade ${_escHtml(age)} ago</div>`;
}
function _rtCryptoNote() {
  return Object.keys(RT_CRYPTO).some(tk => liveQuoteSrc[tk] === "coinbase-ws" || liveQuoteSrc[tk] === "kraken-ws")
    ? " \u00b7 \u25cf price = live exchange stream (Coinbase/Kraken)" : "";
}
function _rtCoinTk(sym) { sym = String(sym || "").toUpperCase(); return sym === "POL" ? "MATIC" : sym; }
function _rtTableStale() { try { return !!(_cryptoAsOf && !isNaN(_cryptoAsOf)); } catch (e) { return false; } }
function _rtCgTableTs() {
  try { if (_cryptoAsOf && !isNaN(_cryptoAsOf)) return _cryptoAsOf.getTime(); } catch (e) {}
  return _rt.cgAt || 0;
}
/** Crypto rankings row values: the exchange stream when it is the freshest print, else the CoinGecko table row. */
function _rtCoinView(coin) {
  const tk = _rtCoinTk(coin && coin.symbol);
  const tc = coin ? (coin.price_change_percentage_24h_in_currency ?? coin.price_change_percentage_24h) : null;
  const out = { tk, p: coin ? coin.current_price : null, c24: typeof tc === "number" && isFinite(tc) ? tc : null, live: false, stream: false, desk: false, fresher: false, src: "coingecko", ts: _rtCgTableTs() };
  const now = Date.now(), r = _rt.roll[tk], rOk = r && r.prev > 0 && now - r.at < 30 * 60_000;
  const src = liveQuoteSrc[tk];
  if (src && liveSymbols.has(tk) && P[tk] && P[tk].p > 0) {
    const ts = Number(liveQuoteTs[tk]) || 0, age = now - ts;
    if ((src === "coinbase-ws" || src === "kraken-ws") && age < 10 * 60_000 && ts >= out.ts - 60_000) {
      out.stream = true; out.live = now - (_rt.lastRecv[tk] || 0) <= RT_HOLD_MS;
    } else if (!liveQuoteCached[tk] && age < 30 * 60_000 && ts >= out.ts - 3 * 60_000) {
      // The desk quote is (about) as new as the rankings snapshot: show the desk value so the table, watchlist
      // strip, tape and summary card read one value on one 24h basis.
      out.desk = true; out.fresher = src !== "coingecko";
    }
    if (out.stream || out.desk) {
      out.p = P[tk].p; out.src = src; out.ts = ts;
      const ch = liveChg(tk);
      out.c24 = ch != null ? ch : (rOk ? ((out.p - r.prev) / r.prev) * 100 : null);
      return out;
    }
  }
  // Rankings row: put its change on the ticker's best-known 24h basis (stream / Yahoo rolling 24h).
  if (rOk && r.kind !== "cg" && out.p > 0) out.c24 = ((out.p - r.prev) / r.prev) * 100;
  return out;
}
function _rtChgTxt(v) { return v == null || !isFinite(v) ? "—" : `${v > 0 ? "+" : ""}${Number(v).toFixed(2)}%`; }
/** /crypto/ status line: live with the latest tick time while streaming, honest fallback otherwise. */
function _rtCryptoHeaderText() {
  let data = null; try { data = _cryptoMktData; } catch (e) {}
  if (!Array.isArray(data) || !data.length) return "";
  let last = 0, src = "", n = 0, f = 0;
  data.forEach(c => { const v = _rtCoinView(c); if (v.fresher) f++; if (v.live) { n++; if (v.ts > last) { last = v.ts; src = v.src; } } });
  let stale = false, asOf = null; try { stale = !!(_cryptoAsOf && !isNaN(_cryptoAsOf)); asOf = stale ? _cryptoAsOf : null; } catch (e) {}
  const cg = stale
    ? `CoinGecko table delayed \u00b7 as of ${asOf.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
    : (_rt.cgAt ? `CoinGecko table \u00b7 fetched ${_fmtAsOf(_rt.cgAt)}` : "CoinGecko table");
  const fr = f ? ` \u00b7 ${f} row${f === 1 ? "" : "s"} from desk quotes (hover for source)` : "";
  return last
    ? `\u25cf Live \u00b7 ${_quoteSourceLabel(src)} \u00b7 last tick ${_fmtAsOf(last)} \u00b7 ${n} streamed row${n === 1 ? "" : "s"} marked \u25cf \u00b7 other values: ${cg}${fr}`
    : `Delayed \u00b7 ${cg}${fr}`;
}
function _rtCryptoHeader() {
  const t = _rtCryptoHeaderText();
  if (!t) return "";
  return `<div data-rt-crypto-hdr class="${t.startsWith("\u25cf") ? "rt-hdr-live" : ""}" style="font-family:var(--mn);font-size:10px;color:var(--t3);padding:2px 0 6px">${_escHtml(t)}</div>`;
}
/** Price + 24h cells for one rankings row (used by the renderer and the 1s painter). */
function _rtCoinCells(coin) {
  const v = _rtCoinView(coin);
  const staleTbl = !v.stream && !v.desk && _rtTableStale();
  const cls = `${v.live ? "rt-live" : ""}${staleTbl ? " rt-stale-cell" : ""}`.trim();
  const title = (v.stream || v.desk) ? `${_quoteSourceLabel(v.src)} \u00b7 ${_quoteMeta(v.tk).label} \u00b7 as of ${_fmtAsOf(v.ts)}` : staleTbl ? `CoinGecko \u00b7 delayed \u00b7 as of ${_fmtAsOf(v.ts)}` : `CoinGecko \u00b7 fetched ${_fmtAsOf(v.ts)}`;
  return { v, cls, title, px: v.p > 0 ? `$${_rtCryptoPx(v.p)}` : "—", chg: _rtChgTxt(v.c24),
    col: v.c24 == null ? "var(--t3)" : v.c24 > 0 ? "var(--gn)" : v.c24 < 0 ? "var(--rd)" : "var(--t3)" };
}
function _rtGoldChecked() {
  if (liveQuoteSrc.XAU !== "gold-api-spot-proxy-browser" || !_rt.goldChecked || Date.now() - _rt.goldChecked > 3 * 60_000) return "";
  return ` \u00b7 checked ${_fmtAsOf(_rt.goldChecked)}`;
}

// ── sockets: open / subscribe diff / reconnect with backoff / watchdog ──
function _rtOpen(key) {
  if (_rt.sock[key] || !_rt.running) return;
  const url = key === "cb" ? RT_CB_URL : key === "kr" ? RT_KR_URL : RT_YS_URL;
  let ws;
  try { ws = new WebSocket(url); } catch (e) { _rt.stats.errors++; _rtScheduleReconnect(key); return; }
  _rt.sock[key] = ws; _rt.subd[key] = new Set(); _rt.gotData[key] = false;
  _rt.stats.connects[key]++;
  ws.onopen = () => { _rt.lastMsg[key] = Date.now(); _rtSync(key); };
  ws.onmessage = ev => {
    _rt.lastMsg[key] = Date.now();
    if (!_rt.gotData[key]) { _rt.gotData[key] = true; _rt.attempts[key] = 0; if (key !== "ys") _rt.provFails = 0; }
    if (key === "cb") _rtOnCb(ev); else if (key === "kr") _rtOnKr(ev); else _rtOnYs(ev);
  };
  ws.onerror = () => { _rt.stats.errors++; };
  ws.onclose = () => {
    if (_rt.sock[key] !== ws) return;
    _rt.sock[key] = null; _rt.subd[key] = new Set(); _rt.stats.closes++;
    if (!_rt.running) return;
    if (key !== "ys" && !_rt.gotData[key] && ++_rt.provFails >= 3) { _rt.cryptoProv = 1 - _rt.cryptoProv; _rt.provFails = 0; }
    _rtScheduleReconnect(key);
  };
}
function _rtClose(key) {
  clearTimeout(_rt.reconnectT[key]); _rt.reconnectT[key] = null;
  const ws = _rt.sock[key];
  _rt.sock[key] = null; _rt.subd[key] = new Set();
  if (ws) { try { ws.onclose = null; ws.close(1000); } catch (e) {} }
}
function _rtScheduleReconnect(key) {
  if (!_rt.running || _rt.reconnectT[key]) return;
  const n = _rt.attempts[key] = (_rt.attempts[key] || 0) + 1;
  const delay = Math.min(60_000, 1000 * 2 ** Math.min(n - 1, 6)) * (0.8 + Math.random() * 0.4);
  _rt.reconnectT[key] = setTimeout(() => { _rt.reconnectT[key] = null; _rtSyncAll(); }, delay);
}
function _rtWanted(key) {
  const out = new Set();
  if (key === "ys" ? !RT_USE.yahoo : !RT_USE.crypto) return out;
  if (key === "ys") {
    const rev = _rtYahooRev(), cap = IS_DESKTOP() ? RT_YS_CAP_DESK : RT_YS_CAP_PHONE;
    const usOpen = _usRegularOpen();
    for (const tk of _rt.want) {
      const yh = YAHOO_SYMBOLS[tk];
      if (!yh || !rev[yh]) continue;
      if (_rtIsUsEquitySym(yh) && !usOpen) continue; // nothing to stream outside the regular session
      out.add(yh);
      if (out.size >= cap) break;
    }
    return out;
  }
  const col = key === "cb" ? 0 : 1;
  for (const tk of _rt.want) { const v = RT_CRYPTO[tk]; if (v && v[col]) out.add(v[col]); }
  if (_rt.want.has("XAU") && RT_CRYPTO.PAXG[col]) out.add(RT_CRYPTO.PAXG[col]);
  return out;
}
function _rtSend(key, ws, add, del) {
  const msgs = [];
  if (key === "cb") {
    if (del.length) msgs.push({ type: "unsubscribe", product_ids: del, channels: ["ticker"] });
    if (add.length) msgs.push({ type: "subscribe", product_ids: add, channels: ["ticker"] });
  } else if (key === "kr") {
    if (del.length) msgs.push({ method: "unsubscribe", params: { channel: "ticker", symbol: del } });
    if (add.length) msgs.push({ method: "subscribe", params: { channel: "ticker", symbol: add } });
  } else {
    if (del.length) msgs.push({ unsubscribe: del });
    if (add.length) msgs.push({ subscribe: add });
  }
  msgs.forEach(m => { try { ws.send(JSON.stringify(m)); } catch (e) {} });
}
function _rtSync(key) {
  const ws = _rt.sock[key];
  if (!ws || ws.readyState !== 1) return;
  const want = _rtWanted(key), have = _rt.subd[key];
  const add = [...want].filter(s => !have.has(s)), del = [...have].filter(s => !want.has(s));
  if (!add.length && !del.length) return;
  if (add.length) _rt.lastMsg[key] = Date.now(); // fresh subscription restarts the silence watchdog
  _rtSend(key, ws, add, del);
  _rt.subd[key] = want;
}
function _rtSyncAll() {
  if (!_rt.running) return;
  const cryptoKey = _rt.cryptoProv ? "kr" : "cb", otherKey = _rt.cryptoProv ? "cb" : "kr";
  _rtClose(otherKey);
  [cryptoKey, "ys"].forEach(key => {
    const want = _rtWanted(key);
    if (!want.size) {
      // Nothing on screen needs this feed: unsubscribe now, close after 60s idle (avoids reconnect churn while scrolling).
      _rt.emptySince[key] = _rt.emptySince[key] || Date.now();
      if (Date.now() - _rt.emptySince[key] > 60_000) _rtClose(key); else _rtSync(key);
      return;
    }
    _rt.emptySince[key] = 0;
    if (!_rt.sock[key]) { if (!_rt.reconnectT[key]) _rtOpen(key); return; }
    _rtSync(key);
    // Watchdog: a silent socket during an open market is treated as dead.
    const silentMs = Date.now() - (_rt.lastMsg[key] || Date.now());
    const limit = key === "ys" ? (_rtWeekend() ? Infinity : 120_000) : 45_000;
    if (_rt.sock[key]?.readyState === 1 && silentMs > limit) { try { _rt.sock[key].close(); } catch (e) {} }
  });
}

// ── which symbols matter right now: what is on screen (+ the desk tape) ──
function _rtScan() {
  const vh = window.innerHeight, vw = window.innerWidth, vis = new Set();
  const inView = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.bottom > 0 && r.top < vh && r.right > 0 && r.left < vw; };
  document.querySelectorAll("#tape .ti[data-tk],td[data-fl],[data-price-card],[data-live-price],.data-card[data-tk],[data-rt-px],.wl-glance-chip").forEach(el => {
    if (!inView(el)) return;
    let tk = el.dataset.tk || el.dataset.fl || el.dataset.priceCard || el.getAttribute("data-live-price") || el.dataset.rtPx;
    if (!tk && el.classList.contains("wl-glance-chip")) tk = ((el.getAttribute("onclick") || "").match(/openA\('([^']+)'\)/) || [])[1];
    if (tk) vis.add(tk);
  });
  if (pg === "home" || pg === "gold" || pg === "playbook") { vis.add("XAU"); vis.add("DXY"); }
  if (typeof termSelTk !== "undefined" && termSelTk) vis.add(termSelTk);
  _rt.visible = vis;
  const want = new Set(vis);
  // Desktop tape scrolls the whole TAPE_ORDER through view — keep it warm.
  const tape = document.getElementById("tape");
  if (IS_DESKTOP() && tape && tape.getBoundingClientRect().height > 0) TAPE_ORDER.forEach(tk => want.add(tk));
  _rt.want = want;
}
function _rtTick() {
  if (_rtDisabled()) { if (_rt.running) _rtPause("disabled"); return; }
  if (!_rt.running) { if (!document.hidden) _rtResume(); return; }
  _rtScan();
  _rtSyncAll();
  if (_rt.want.has("XAU") && !_rt.goldT) _rtGoldPoll();
}

// ── gold-api.com XAU spot proxy: poll just after each expected 30s update ──
async function _rtGoldPoll() {
  clearTimeout(_rt.goldT); _rt.goldT = null;
  if (!_rt.running || !_rt.want.has("XAU") || !RT_USE.gold) return;
  let next = 10_000;
  try {
    _rt.stats.goldPolls++;
    const r = await fetch(RT_GOLD_URL, { cache: "no-store", credentials: "omit", signal: AbortSignal.timeout(8000) });
    if (r.ok) {
      const j = await r.json();
      const p = Number(j?.price), ts = Date.parse(j?.updatedAt);
      if (p > 0 && ts > 0) {
        _rt.goldChecked = Date.now();
        _rtApply("XAU", p, { src: "gold-api-spot-proxy-browser", ts, proxy: true, name: "Spot Gold (proxy)", repaint: true });
        // upstream refreshes about every 30s: aim 2s after the next refresh
        const due = ts + 32_000 - Date.now();
        next = due > 3000 && due < 31_000 ? due : 5000;
      }
    }
  } catch (e) { next = 30_000; }
  if (_rt.running) _rt.goldT = setTimeout(_rtGoldPoll, next);
}

// ── visible symbols with no live stream: faster refresh via the cached proxy ──
async function _rtFastPoll() {
  if (!_rt.running || _rtDisabled() || document.hidden) return;
  const now = Date.now(), usOpen = _usRegularOpen(), weekend = _rtWeekend();
  const list = [..._rt.visible].filter(tk => {
    const yh = typeof YAHOO_SYMBOLS !== "undefined" && YAHOO_SYMBOLS[tk];
    if (!yh || tk === "XAU" || RT_CRYPTO[tk] || /-USD$/.test(yh)) return false;
    if (now - (_rt.lastRecv[tk] || 0) < 30_000) return false;   // already streaming
    if (_rtIsUsEquitySym(yh) && !usOpen) return false;          // closed session — nothing new to fetch
    if (weekend) return false;
    // Last print >30 min old (even allowing for a 15m delay) = that market is shut; the 60s loop covers reopen.
    if (liveQuoteTs[tk] && now - liveQuoteTs[tk] > 30 * 60_000) return false;
    return true;
  }).slice(0, 30);
  if (!list.length) return;
  _rt.stats.fastPolls++;
  try {
    const syms = [...new Set(list.map(tk => YAHOO_SYMBOLS[tk]))];
    const res = await fetch(`/api/yahoo-quote?symbols=${encodeURIComponent(syms.join(","))}`, { signal: AbortSignal.timeout(10_000) });
    if (!res.ok) return;
    const data = await res.json();
    list.forEach(tk => {
      const q = data && data[YAHOO_SYMBOLS[tk]];
      if (!q || !(q.p > 0)) return;
      const before = P[tk]?.p, hist = HIST[tk] ? HIST[tk].slice() : null;
      if (_applyLiveQuote(tk, q, "yahoo")) {
        if (hist) HIST[tk] = hist; else delete HIST[tk]; // keep sparklines on their own cadence
        if (P[tk]?.p !== before) { _rt.dirty.add(tk); _rt.dir[tk] = before == null ? 0 : (P[tk].p > before ? 1 : -1); }
      }
    });
  } catch (e) {}
}

// ── in-place painter: only changed tickers, at most once per second ──
function _rtFlash(el, tk) {
  const d = _rt.dir[tk];
  if (!el || !d || _rt.reduceMotion) return;
  el.classList.remove("rt-up", "rt-dn"); void el.offsetWidth; el.classList.add(d > 0 ? "rt-up" : "rt-dn");
}
function _rtTapeBadge(d) {
  return d.status === "live" ? '<span class="htec-live-dot" title="Near real-time"></span>'
    : d.status === "delayed" ? '<span class="tape-badge tape-del" title="Delayed free feed">D</span>'
    : d.status === "stale" ? '<span class="tape-badge tape-stale" title="Stale tick">S</span>'
    : d.status === "cached" ? '<span class="tape-badge tape-cache" title="Session cache">C</span>'
    : d.status === "closed" ? '<span class="tape-badge tape-cache" title="Provider reports market closed">CLOSED</span>'
    : '<span style="opacity:0.35;font-size:7px">○</span>';
}
/** Watchlist strip chip: on /crypto/ a coin in the rankings shows exactly the table's value; elsewhere the desk quote. */
function _rtChipVals(tk) {
  let row = null;
  try { if (pg === "crypto" && Array.isArray(_cryptoMktData)) row = _cryptoMktData.find(c => _rtCoinTk(c.symbol) === tk) || null; } catch (e) {}
  if (row) {
    const v = _rtCoinView(row);
    if (v.p > 0) {
      const c = v.c24, abs = c == null ? null : v.p - v.p / (1 + c / 100);
      const meta = v.stream || v.desk ? _quoteMeta(tk) : null;
      return { p: `${_rtCryptoPx(v.p)}`, c, abs, src: v.src, asOf: v.ts, label: meta ? meta.label : (_rtTableStale() ? "DELAYED" : "CoinGecko") };
    }
  }
  if (!hasSyncedQuote(tk)) return null;
  const d = fp(tk), ch = liveChg(tk);
  return { p: d.p, c: ch, abs: ch == null ? null : d.raw, src: d.src, asOf: d.asOf, label: d.label };
}
function _rtPaintChip(el, tk) {
  const x = _rtChipVals(tk); if (!x) return false;
  const pe = el.querySelector(".wl-g-p"), ce = el.querySelector(".wl-g-c");
  let moved = false;
  if (pe && pe.textContent !== x.p) { pe.textContent = x.p; moved = true; }
  if (ce) {
    const col = x.c == null ? "var(--t3)" : x.c > 0 ? "var(--gn)" : x.c < 0 ? "var(--rd)" : "var(--t3)";
    const sign = x.c != null && x.c >= 0 ? "+" : "";
    const a = Math.abs(x.abs || 0), absTxt = x.abs == null ? "" : `${x.abs >= 0 ? "+" : "-"}${a >= 1000 ? Math.round(a).toLocaleString() : a.toFixed(2)}`;
    const txt = x.c == null ? "—" : `${x.c > 0 ? "▲" : x.c < 0 ? "▼" : "•"} ${sign}${Number(x.c).toFixed(2)}% · ${absTxt}`;
    if (ce.textContent !== txt) ce.textContent = txt;
    ce.style.color = col;
  }
  const srcTxt = `${_quoteSourceLabel(x.src)} · as of ${_fmtAsOf(x.asOf)}`;
  el.title = srcTxt;
  const se = el.querySelector(':scope > span[style*="display:block"]'); if (se && se.textContent !== srcTxt) se.textContent = srcTxt;
  return moved;
}
/** Status lines are rendered once per page build; recount them in place (cheap: one pass over the desk list). */
function _rtRecountStatus() {
  if (typeof quoteStatusSummary !== "function") return;
  try {
    if (pg === "mkt") {
      const sub = document.querySelector('.pg-hdr[data-page-title="Markets"] .pg-hdr-sub');
      if (sub) {
        const dyn = typeof _dynMarkets !== "undefined" ? Object.keys(_dynMarkets).length : 0;
        const t = `${quoteStatusSummary(undefined, { includeUnavailable: true })} · ${dyn} dynamic`;
        if (sub.textContent !== t) sub.textContent = t;
      }
    }
    const p1 = document.getElementById("p1sub");
    if (p1 && typeof A !== "undefined") {
      const m = /^(\d+) of (\d+) · /.exec(p1.textContent || "");
      if (m && +m[1] === A.length && +m[2] === A.length) { // unfiltered desk list only
        const t = `${A.length} of ${A.length} · ${quoteStatusSummary(A.map(a => a.tk), { includeUnavailable: true })}`;
        if (p1.textContent !== t) p1.textContent = t;
      }
    }
  } catch (e) {}
}
/** Every 5s, independent of the stream switch: placeholders, status lines, /crypto/ strip + header freshness. */
function _rtHousekeep() {
  if (document.hidden) return;
  _rtSparkSweep();
  _rtRecountStatus();
  try {
    if (pg === "crypto") {
      document.querySelectorAll(".wl-glance-chip").forEach(el => {
        const tk = ((el.getAttribute("onclick") || "").match(/openA\('([^']+)'\)/) || [])[1];
        if (tk) _rtPaintChip(el, tk);
      });
      const h = document.querySelector("[data-rt-crypto-hdr]");
      if (h) { const t = _rtCryptoHeaderText(); if (t && h.textContent !== t) { h.textContent = t; h.classList.toggle("rt-hdr-live", t.startsWith("\u25cf")); } }
    }
  } catch (e) {}
}
/** fetchCrypto saw fresh CoinGecko data while the rankings table is a stale server copy: refresh the table once
 *  (at most once a minute; no blind polling — only on evidence that fresh data exists). */
function _rtCgFresh() {
  try {
    if (pg !== "crypto" || !_rtTableStale() || _cryptoMktLoading || Date.now() - _rt.cgRefetchAt < 60_000) return;
    _rt.cgRefetchAt = Date.now();
    fetchCryptoMarket();
  } catch (e) {}
}
function _rtPaint() {
  if (!_rt.dirty.size || document.hidden) return;
  const dirty = new Set(_rt.dirty); _rt.dirty.clear();
  let n = 0;
  const info = {};
  const get = tk => info[tk] || (info[tk] = (() => {
    const d = fp(tk), ch = liveChg(tk);
    return { d, ch, col: ch == null ? "var(--t3)" : ch > 0 ? "var(--gn)" : ch < 0 ? "var(--rd)" : "var(--t3)", sign: ch != null && ch >= 0 ? "+" : "" };
  })());
  const setText = (el, txt) => { if (el && el.textContent !== txt) { el.textContent = txt; n++; return true; } return false; };
  document.querySelectorAll("#tape .ti[data-tk],td[data-fl],[data-price-card],[data-live-price],.data-card[data-tk],[data-rt-px],[data-rt-c24],.wl-glance-chip").forEach(el => {
    let tk = el.dataset.tk || el.dataset.fl || el.dataset.priceCard || el.getAttribute("data-live-price") || el.dataset.rtPx || el.dataset.rtC24;
    if (!tk && el.classList.contains("wl-glance-chip")) tk = ((el.getAttribute("onclick") || "").match(/openA\('([^']+)'\)/) || [])[1];
    if (!tk || !dirty.has(tk) || !hasSyncedQuote(tk)) return;
    const { d, ch, col, sign } = get(tk);
    if (el.matches("#tape .ti")) {
      const k = el.children; if (k.length < 3) return;
      if (setText(k[1], d.p)) _rtFlash(el, tk);
      setText(k[2], ch == null ? "—" : sign + d.c + "%"); k[2].style.color = col;
      if (el.dataset.rtSt !== d.status) { el.dataset.rtSt = d.status; k[0].innerHTML = `${_escHtml(tk)}${_rtTapeBadge(d)}`; }
      el.title = `${tk} · ${d.label || "NO SYNC"}${d.asOf ? ` · as of ${_fmtAsOf(d.asOf)}` : ""}`;
      if (typeof _tapePrev !== "undefined") _tapePrev[tk] = d.p;
    } else if (el.matches("td[data-fl]")) {
      const meta = el.querySelector(".price-row-meta");
      let txt = [...el.childNodes].find(x => x.nodeType === 3 && x.textContent.trim());
      const a = typeof A !== "undefined" ? A.find(x => x.tk === tk) : null;
      const money = txt ? txt.textContent.trim().startsWith("$") : (meta ? !!a && ["Stock", "Crypto", "Commodity"].includes(a.cat) : !!el.closest("#wl-table"));
      const val = (money ? "$" : "") + d.p;
      if (!txt) { el.querySelectorAll(":scope > span").forEach(s => s.remove()); txt = document.createTextNode(""); el.insertBefore(txt, el.firstChild); }
      if (txt.textContent !== val) { txt.textContent = val; n++; _rtFlash(el, tk); }
      if (meta) meta.innerHTML = `${stat(tk)} ${asOfTag(tk)}`;
      const next = el.nextElementSibling;
      if (next && /%$/.test(next.textContent.trim()) || next && next.textContent.trim() === "—") {
        const arrow = ch == null || ch === 0 ? "" : (ch > 0 ? "↑" : "↓");
        const keepArrow = /^[↑↓]/.test(next.textContent.trim()) || !!meta || !!el.closest("#wl-table");
        setText(next, ch == null ? "—" : `${keepArrow ? arrow : ""}${sign}${d.c}%`); next.style.color = col;
      }
    } else if (el.matches("[data-price-card]")) {
      const showDollar = el.dataset.priceDollar === "1", pctOnly = el.dataset.priceChg === "pct";
      const pe = el.querySelector(".asset-price"), ce = el.querySelector(".asset-chg");
      if (pe && setText(pe, (showDollar ? "$" : "") + d.p)) _rtFlash(pe, tk);
      if (ce) {
        ce.style.color = col;
        setText(ce, ch == null ? "—" : (pctOnly ? `${sign}${d.c}%` : `${sign}${d.chg} (${sign}${d.c}%)`));
        ce.classList.remove("px-up", "px-dn", "px-flat");
        ce.classList.add(ch == null || ch === 0 ? "px-flat" : ch > 0 ? "px-up" : "px-dn");
      }
      const st = el.querySelector(".trust-stat");
      if (st && st.dataset.rtSt !== d.status + d.label) { const t = document.createElement("span"); t.innerHTML = stat(tk); const nn = t.firstElementChild; if (nn) { nn.dataset.rtSt = d.status + d.label; st.replaceWith(nn); } }
      const ao = el.querySelector(".asof-tag");
      if (ao) { const t = document.createElement("span"); t.innerHTML = asOfTag(tk); if (t.firstElementChild) ao.replaceWith(t.firstElementChild); }
    } else if (el.matches("[data-live-price]")) {
      if (setText(el, d.p)) _rtFlash(el, tk);
    } else if (el.matches(".data-card[data-tk]")) {
      const v = el.querySelector(".value"), c = el.querySelector(".change");
      if (v && setText(v, d.p)) _rtFlash(v, tk);
      if (c) { setText(c, ch == null ? "—" : `${sign}${d.chg} (${sign}${d.c}%)`); c.style.color = col; }
    } else if (el.matches(".wl-glance-chip")) {
      if (_rtPaintChip(el, tk)) _rtFlash(el.querySelector(".wl-g-p"), tk);
    } else if (el.matches("[data-rt-px],[data-rt-c24]")) {
      // Crypto rankings table: same row values as the renderer (the desk quote when it is current).
      const cells = _rtCoinCells({ symbol: tk });
      if (!cells.v.stream && !cells.v.desk) return;
      if (el.dataset.rtPx) {
        if (setText(el, cells.px)) _rtFlash(el, tk);
        el.classList.toggle("rt-live", cells.v.live); el.classList.remove("rt-stale-cell");
        el.title = cells.title;
      } else {
        setText(el, cells.chg); el.style.color = cells.col; el.classList.remove("rt-stale-cell");
      }
    }
  });
  const ch = document.querySelector("[data-rt-crypto-hdr]");
  if (ch) { const t = _rtCryptoHeaderText(); if (t && ch.textContent !== t) { ch.textContent = t; ch.classList.toggle("rt-hdr-live", t.startsWith("\u25cf")); } }
  // Analysis header, front door, gold dashboard
  try { if (typeof termSelTk !== "undefined" && termSelTk && dirty.has(termSelTk)) _patchP2LiveHeader(); } catch (e) {}
  if (pg === "home" && (dirty.has("XAU") || dirty.has("DXY") || dirty.has("PAXG"))) {
    try {
      if (_paintFrontDoorQuotes()) {
        _rt.paxgPainted = true;
        document.querySelectorAll(".front-door-quotes").forEach(box => {
          const tiles = box.querySelectorAll(".front-door-quote-value");
          if (dirty.has("XAU")) _rtFlash(tiles[0], "XAU");
          if (dirty.has("DXY")) _rtFlash(tiles[1], "DXY");
        });
      }
    } catch (e) {}
  }
  if (dirty.has("XAU") && (pg === "gold" || pg === "playbook")) {
    const px = livePx("XAU"), gd = document.querySelector(".gd-px");
    if (gd && px != null && typeof _gdPx === "function") {
      const t = gd.firstChild;
      if (t && t.nodeType === 3) { const val = `$${_gdPx(px)} `; if (t.textContent !== val) { t.textContent = val; n++; _rtFlash(gd, "XAU"); } }
      const k = document.querySelector(".gd-kicker"); if (k) setText(k, _rtGoldKicker());
    }
  }
  _rt.stats.paints++; _rt.stats.cells += n;
}
function _rtGoldKicker() {
  if (typeof livePx === "function" && livePx("XAU") != null && liveQuoteSrc.XAU) {
    const m = _quoteMeta("XAU");
    return `XAU · ${_quoteSourceLabel(liveQuoteSrc.XAU)} · ${m.label}${m.asOf ? ` · as of ${_fmtAsOf(m.asOf)}` : ""}${_rtGoldChecked()}`;
  }
  return "XAU · COMEX proxy GC=F · delayed";
}

// ── chart placeholders: resolve or hide instead of a permanent faint "loading" ──
const RT_SPARK_GIVEUP_MS = 20_000, RT_SPARK_RETRY_MS = 10 * 60_000;
function _rtSparkGaveUp(tk) {
  try {
    const t = _rt.sparkFail[tk];
    if (!t) return false;
    if (Date.now() - t > RT_SPARK_RETRY_MS) { delete _rt.sparkFail[tk]; delete _rt.sparkTk[tk]; return false; }
    return true;
  } catch (e) { return false; }
}
function _rtSparkHiddenHtml(tk, w, h) {
  return `<div data-spark-tk="${tk}" data-spark-w="${w}" data-spark-h="${h}" data-rt-no-chart="1" role="img" aria-label="Intraday chart unavailable right now" title="Intraday chart unavailable right now" style="width:${w}px;height:${h}px;opacity:0"></div>`;
}
function _rtSparkHide(el) {
  if (el.dataset.rtNoChart) return;
  el.dataset.rtNoChart = "1";
  el.textContent = ""; el.style.border = "none"; el.style.opacity = "0";
  el.setAttribute("aria-label", "Intraday chart unavailable right now"); el.title = "Intraday chart unavailable right now";
}
// Tracked per ticker (not per element): pages re-render their cards, which would otherwise restart the clock.
function _rtSparkSweep() {
  if (document.hidden || typeof _ensureSparkline !== "function") return;
  const now = Date.now(), vh = window.innerHeight;
  document.querySelectorAll("[data-spark-tk]").forEach(el => {
    const tk = el.dataset.sparkTk;
    if (!tk) return;
    if (el.querySelector("svg")) { if (el.style.border) { el.style.border = "none"; el.style.opacity = "1"; el.style.display = "block"; } return; }
    const n = (HIST[tk] || []).filter(v => typeof v === "number" && isFinite(v) && v > 0).length;
    if (n >= 5 && typeof _patchSparkline === "function") { delete _rt.sparkFail[tk]; delete _rt.sparkTk[tk]; _patchSparkline(tk); return; }
    if (_rtSparkGaveUp(tk)) { _rtSparkHide(el); return; }
    if (el.dataset.rtNoChart) return;
    const r = el.getBoundingClientRect();
    if (!(r.width > 0) || r.bottom < 0 || r.top > vh) return;
    const st = _rt.sparkTk[tk] || (_rt.sparkTk[tk] = { seen: now, retried: false });
    if (!st.retried && now - st.seen > 8000) { st.retried = true; try { _ensureSparkline(tk); } catch (e) {} return; }
    // Hide even while a fetch is still queued (phones queue ~200 chart requests behind the CoinGecko gate):
    // when it lands, _ensureSparkline -> _patchSparkline draws it and restores the frame.
    if (now - st.seen > RT_SPARK_GIVEUP_MS) { _rt.sparkFail[tk] = now; _rtSparkHide(el); }
  });
}

// ── lifecycle ──
function _rtResume() {
  if (_rt.running || _rtDisabled() || document.hidden) return;
  _rt.running = true; _rt.stats.resumes++;
  _rt.reduceMotion = !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  _rt.timers = [
    setInterval(_rtTick, RT_SCAN_MS),
    setInterval(_rtPaint, RT_PAINT_MS),
    setInterval(_rtFastPoll, RT_FAST_POLL_MS),
  ];
  _rtScan(); _rtSyncAll(); _rtGoldPoll();
  // Back after longer than one normal loop interval: refresh everything else once (no extra cadence).
  const loopMs = Math.max(60, MOBILE() ? Math.max(updateFreq || 60, MOBILE_PRICE_FREQ) : (updateFreq || 60)) * 1000;
  if (_rt.booted && typeof priceLastFetch !== "undefined" && (!priceLastFetch || Date.now() - priceLastFetch.getTime() > loopMs)) {
    try { fetchLivePrices(); } catch (e) {}
  }
}
function _rtPause(why) {
  if (!_rt.running) return;
  _rt.running = false; _rt.stats.pauses++; _rt.lastPause = why;
  _rt.timers.forEach(clearInterval); _rt.timers = [];
  clearTimeout(_rt.goldT); _rt.goldT = null;
  ["cb", "kr", "ys"].forEach(_rtClose);
}
function _rtInit() {
  if (_rt.booted) return;
  _rt.booted = true;
  try {
    const css = document.createElement("style");
    css.id = "rt-layer-css";
    css.textContent = `@keyframes rtUp{0%{background-color:rgba(34,197,94,.30)}100%{background-color:transparent}}
@keyframes rtDn{0%{background-color:rgba(239,68,68,.30)}100%{background-color:transparent}}
.rt-up{animation:rtUp .9s ease-out;border-radius:3px}.rt-dn{animation:rtDn .9s ease-out;border-radius:3px}
.front-door-quote-paxg{margin-top:4px;font-family:var(--mn,monospace);font-size:10px;letter-spacing:.02em;color:var(--t3,#8a8f98)}
.rt-live::before{content:"\\25CF  ";color:var(--gn,#22c55e);font-size:7px;vertical-align:middle}
.rt-stale-cell{opacity:.7}
.rt-hdr-live{color:var(--gn,#22c55e)!important}
.rt-cg-table td,.rt-cg-table th{font-variant-numeric:tabular-nums}
.rt-cg-table td:nth-child(n+3),.rt-cg-table th{white-space:nowrap}
.rt-cg-table .cg-sym-in{display:none}
@media (max-width:420px){
.rt-cg-table{min-width:0!important;font-size:10px!important}
.rt-cg-table th,.rt-cg-table td{padding:7px 4px!important}
.rt-cg-table th:nth-child(4),.rt-cg-table td:nth-child(4),.rt-cg-table th:nth-child(8),.rt-cg-table td:nth-child(8){display:none}
.rt-cg-table td:nth-child(2) img{width:16px;height:16px}
.rt-cg-table td:nth-child(2){min-width:52px;white-space:nowrap}
.rt-cg-table td:nth-child(2) > div{gap:5px!important}
.rt-cg-table .cg-nm,.rt-cg-table .cg-sym{display:none!important}
.rt-cg-table .cg-sym-in{display:inline-block!important;max-width:44px;overflow:hidden;text-overflow:ellipsis;vertical-align:middle;font-size:10.5px;white-space:nowrap;word-break:keep-all;overflow-wrap:normal}
.rt-live::before{font-size:6px}
}
@media (prefers-reduced-motion: reduce){.rt-up,.rt-dn{animation:none}}`;
    document.head.appendChild(css);
  } catch (e) {}
  document.addEventListener("visibilitychange", () => { if (document.hidden) _rtPause("hidden"); else _rtResume(); });
  window.addEventListener("pagehide", () => _rtPause("pagehide"));
  window.addEventListener("pageshow", () => { if (!document.hidden) _rtResume(); });
  let st;
  window.addEventListener("scroll", () => { clearTimeout(st); st = setTimeout(() => { if (_rt.running) { _rtScan(); _rtSyncAll(); } }, 400); }, { passive: true, capture: true });
  setInterval(_rtHousekeep, 5000); // independent of the stream switch: placeholders, status lines, /crypto/ strip
  // A dormant check also notices pause/resume and manual-update settings.
  setInterval(() => { if (!_rt.running && !document.hidden && !_rtDisabled()) _rtResume(); }, 5000);
  _rtResume();
}
'''
RT12_MODULE = r'''// ═══════════════════════════════════════════════════════════
// REALTIME PRICE LAYER (rt12) — browser-direct, free, keyless.
// No server connection is held open: every socket below goes straight from
// the visitor's browser to a public market-data stream, so Replit compute is
// untouched. Sources (measured from a browser on thedispatch.uk origin):
//   • Coinbase Exchange WS ticker (USD crypto + PAXG) — trade-by-trade
//   • Kraken WS v2 ticker — automatic fallback for crypto if Coinbase fails
//   • Yahoo Finance public stream — FX ~1s; US stocks/ETFs during the
//     regular session; indices/futures arrive with the exchange's delay and
//     are labelled DELAYED Nm from the tick's own timestamp
//   • gold-api.com XAU (CORS *, keyless, no rate limit) — spot proxy that
//     updates every ~30s; polled just after each expected update
// Ticks set P[tk] immediately; the DOM is repainted at most once a second,
// in place, for the tickers that actually changed. Hidden tab = everything
// closed. Kill switch: localStorage td_rt_off = "1".
// rt10: one 24h change basis for crypto (rolling 24h: stream > CoinGecko),
// an older print never replaces a newer one, honest crypto-page header,
// consistent crypto decimals, gold "checked" time, chart placeholders resolve.
// rt11: crypto 24h basis ranked stream > Yahoo rolling-24h > CoinGecko (unknown bases show "—"),
// /crypto/ table + strip + card read the desk quote, no fake 0.00% on basis-less proxies,
// live status-line recount, phone name column, spark hide also while a fetch is queued.
// rt12: charts fetched only near the viewport and resolved (drawn or hidden) within ~20s; stale /crypto/
// table re-asked (server SWR) then at most once a minute; no polled 24h % for a streamed coin while its
// socket connects; summary card + status chip tick; closed-market stocks keep the newer quote.
// ═══════════════════════════════════════════════════════════
const RT_CB_URL = "wss://ws-feed.exchange.coinbase.com";
const RT_KR_URL = "wss://ws.kraken.com/v2";
const RT_YS_URL = "wss://streamer.finance.yahoo.com/?version=2";
const RT_GOLD_URL = "https://api.gold-api.com/price/XAU";
// Per-source switches (flip to false and re-publish to drop a source; the 60s loop still covers it).
const RT_USE = Object.freeze({ crypto: true, yahoo: true, gold: true });
// internal ticker -> [Coinbase product, Kraken v2 symbol]
const RT_CRYPTO = Object.freeze({
  BTC: ["BTC-USD", "BTC/USD"], ETH: ["ETH-USD", "ETH/USD"], SOL: ["SOL-USD", "SOL/USD"],
  XRP: ["XRP-USD", "XRP/USD"], DOGE: ["DOGE-USD", "DOGE/USD"], ADA: ["ADA-USD", "ADA/USD"],
  AVAX: ["AVAX-USD", "AVAX/USD"], LINK: ["LINK-USD", "LINK/USD"], DOT: ["DOT-USD", "DOT/USD"],
  LTC: ["LTC-USD", "LTC/USD"], UNI: ["UNI-USD", "UNI/USD"], NEAR: ["NEAR-USD", "NEAR/USD"],
  ALGO: ["ALGO-USD", "ALGO/USD"], HBAR: ["HBAR-USD", "HBAR/USD"], BCH: ["BCH-USD", "BCH/USD"],
  XLM: ["XLM-USD", "XLM/USD"], FIL: ["FIL-USD", "FIL/USD"], APT: ["APT-USD", "APT/USD"],
  SUI: ["SUI-USD", "SUI/USD"], ATOM: ["ATOM-USD", "ATOM/USD"], INJ: ["INJ-USD", "INJ/USD"],
  SHIB: ["SHIB-USD", "SHIB/USD"], PEPE: ["PEPE-USD", "PEPE/USD"], MATIC: ["POL-USD", "POL/USD"],
  TON: [null, "TON/USD"],
  PAXG: ["PAXG-USD", "PAXG/USD"], // secondary gold line only — never written into P.XAU
});
const RT_SRC = new Set(["coinbase-ws", "kraken-ws", "yahoo-stream", "gold-api-spot-proxy-browser"]);
const RT_HOLD_MS = 90_000;     // a polled value may not overwrite a stream tick younger than this
const RT_PAINT_MS = 1000;      // DOM repaint cadence (max once per second)
const RT_SCAN_MS = 3000;       // re-derive the visible symbol set
const RT_FAST_POLL_MS = 15_000;// visible, non-streaming symbols via the cached server proxy
const RT_YS_CAP_DESK = 150, RT_YS_CAP_PHONE = 40;
const RT_ROLL_RANK = Object.freeze({ stream: 3, y24: 2, cg: 1 });
const RT_CHG_HOLD_MS = 3000;   // a streamed coin's polled 24h % waits this long for the exchange's own basis
const _rt = {
  running: false, booted: false, dirty: new Set(), dir: {}, lastRecv: {}, lag: {}, goodPrev: {},
  sock: {}, attempts: {}, gotData: {}, lastMsg: {}, reconnectT: {}, timers: [],
  want: new Set(), visible: new Set(), subd: { cb: new Set(), kr: new Set(), ys: new Set() },
  cryptoProv: 0, provFails: 0, paxg: null, goldT: null, ysRev: null, emptySince: {},
  roll: {}, cgAt: 0, goldChecked: 0, cryptoSet: null, sparkTk: {}, sparkFail: {}, hdrAt: 0, cgRefetchAt: 0,
  holdUntil: {}, heldPrev: {}, lastSt: {}, recountAt: 0, recountT: 0, lazyT: 0, cgSwrT: 0,
  stats: { msgs: { cb: 0, kr: 0, ys: 0 }, ticks: 0, paints: 0, cells: 0, goldPolls: 0, fastPolls: 0,
    connects: { cb: 0, kr: 0, ys: 0 }, closes: 0, pauses: 0, resumes: 0, errors: 0 },
};
window._rtStats = () => ({
  running: _rt.running, hidden: document.hidden, provider: _rt.cryptoProv ? "kraken" : "coinbase",
  sockets: Object.fromEntries(Object.entries(_rt.sock).map(([k, s]) => [k, s ? s.readyState : null])),
  subscribed: { cb: [..._rt.subd.cb], kr: [..._rt.subd.kr], ys: [..._rt.subd.ys] },
  want: [..._rt.want], paxg: _rt.paxg, ..._rt.stats,
});

function _rtDisabled() {
  try { if (localStorage.getItem("td_rt_off") === "1") return true; } catch (e) {}
  return (typeof updatePaused !== "undefined" && updatePaused) || (typeof updateFreq !== "undefined" && updateFreq === 0);
}
function _rtLagMs(tk) { return _rt.lag[tk] || 0; }
function _rtIsCrypto(tk) {
  if (!_rt.cryptoSet) {
    const s = new Set(Object.keys(RT_CRYPTO)); s.delete("PAXG");
    try { Object.values(CG_MAP).forEach(t => s.add(t)); } catch (e) {}
    _rt.cryptoSet = s;
  }
  return _rt.cryptoSet.has(tk) || (typeof TICKER_CATS !== "undefined" && TICKER_CATS[tk] === "cry");
}
/** One crypto price format everywhere: 2 dp at $1 and above, at least 4 dp (≈4 significant figures) below $1. */
function _rtStreamable(tk) {
  if (tk === "XAU" || _rtIsCrypto(tk)) return true;
  const yh = typeof YAHOO_SYMBOLS !== "undefined" && YAHOO_SYMBOLS[tk];
  return !!(yh && _rtYahooRev()[yh] && !_rtIsUsEquitySym(yh));
}
function _rtCryptoPx(v) {
  if (typeof v !== "number" || !isFinite(v) || v <= 0) return "—";
  if (v >= 1) return v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return v.toFixed(Math.min(10, Math.max(4, Math.ceil(-Math.log10(v)) + 3)));
}
function _rtIsUsEquitySym(yh) { return /^[A-Z][A-Z.\-]{0,6}$/.test(yh || ""); }
function _rtWeekend() {
  try {
    const p = Object.fromEntries(new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", weekday: "short", hour: "2-digit", hour12: false }).formatToParts(new Date()).map(x => [x.type, x.value]));
    const h = Number(p.hour) % 24;
    return p.weekday === "Sat" || (p.weekday === "Sun" && h < 17) || (p.weekday === "Fri" && h >= 17);
  } catch (e) { return false; }
}
function _rtYahooRev() {
  if (_rt.ysRev) return _rt.ysRev;
  const rev = {};
  Object.entries(YAHOO_SYMBOLS).forEach(([tk, yh]) => {
    if (!yh || tk === "XAU" || RT_CRYPTO[tk] || /-USD$/.test(yh)) return; // gold spot & crypto have their own feeds
    (rev[yh] = rev[yh] || []).push(tk);
  });
  return (_rt.ysRev = rev);
}

/** Lightweight apply for streamed ticks: price, change vs prior close, source, provider time. */
function _rtApply(tk, p, o) {
  if (!tk || typeof p !== "number" || !isFinite(p) || p <= 0) return false;
  const now = Date.now();
  let ts = Number(o.ts);
  if (!(ts > 0) || ts > now + 60_000) ts = now;
  if (RT_SRC.has(liveQuoteSrc[tk]) && liveQuoteTs[tk] && ts < liveQuoteTs[tk]) return false; // never step back in time
  let prev = (typeof o.prev === "number" && isFinite(o.prev) && o.prev > 0) ? o.prev : null;
  if (prev == null && !o.noBasePrev && _rt.goodPrev[tk] > 0) prev = _rt.goodPrev[tk];
  const oldP = P[tk] && liveSymbols.has(tk) ? P[tk].p : null;
  P[tk] = { p, c: prev ? +(((p - prev) / prev) * 100).toFixed(2) : 0 };
  if (prev) BASE[tk] = { p: prev, c: 0 };
  if (prev && (o.src === "coinbase-ws" || o.src === "kraken-ws")) _rt.roll[tk] = { prev, at: now, kind: "stream" };
  liveSymbols.add(tk);
  liveQuoteTs[tk] = ts;
  liveQuoteSrc[tk] = o.src;
  if (o.name) liveQuoteName[tk] = o.name;
  else if (liveQuoteProxy[tk] && !o.proxy) liveQuoteName[tk] = ""; // don't keep a proxy's name on a real print
  liveQuoteCached[tk] = false;
  liveQuoteChangeAvailable[tk] = prev != null;
  liveQuoteProxy[tk] = !!o.proxy;
  liveQuoteMarketClosed[tk] = false;
  liveQuoteSession[tk] = null;
  _rt.lastRecv[tk] = now;
  _rt.lag[tk] = Math.max(0, now - ts);
  _rt.stats.ticks++;
  if (oldP !== p) { _rt.dirty.add(tk); _rt.dir[tk] = oldP == null ? 0 : (p > oldP ? 1 : -1); }
  else if (o.repaint) { _rt.dirty.add(tk); _rt.dir[tk] = 0; } // same value, new as-of: repaint without a flash
  return true;
}
/** Called from _applyLiveQuote (every polled/server quote). Returning true = keep what we have. */
function _rtGuard(tk, q, source) {
  const src = String(q.source || source || "");
  const now = Date.now();
  const proxyish = !!q.proxy || src.startsWith("gold-api-spot-proxy") || src === "frankfurter-ecb" || src === "open-exchange-rate-api";
  const fin = v => typeof v === "number" && isFinite(v);
  // 0) A quote whose server says it has no real prior close carries no change at all ("—", never a fake 0.00%).
  if (q.basis === "none") { delete q.c; delete q.prev; delete q.change; }
  // Basis-less spot proxies (gold-api returns prev = price, c = 0): use the session's spot prior close if one is
  // known (Twelve Data XAU/USD), otherwise show no change.
  if (src.startsWith("gold-api-spot-proxy") && !(fin(q.prev) && q.prev > 0 && Math.abs(q.prev - q.p) > 1e-9 && q.c !== 0)) {
    const gp = _rt.goodPrev[tk];
    if (gp > 0) { q.prev = gp; q.c = ((q.p - gp) / gp) * 100; } else { delete q.c; delete q.prev; delete q.change; }
  }
  // 1) Crypto: ONE 24h basis per ticker. Ranked: exchange stream (Coinbase open_24h / Kraken) > Yahoo rolling 24h
  //    (server basis "rolling_24h") > CoinGecko 24h. A lower-ranked source is re-based onto the best basis seen in
  //    the last 30 min; a source with an unknown basis (old Yahoo 5-day prev close, Twelve Data/Finnhub day basis)
  //    shows its price but no change until a 24h basis is known.
  if (_rtIsCrypto(tk) && !RT_SRC.has(src) && fin(q.p) && q.p > 0) {
    const r = _rt.roll[tk], rOk = r && r.prev > 0 && now - r.at < 30 * 60_000;
    const c = Number(q.c);
    let kind = null, own = null;
    if (src === "coingecko" && isFinite(c) && c > -100) { kind = "cg"; own = q.p / (1 + c / 100); }
    else if (src.startsWith("yahoo") && q.basis === "rolling_24h" && fin(q.prev) && q.prev > 0) { kind = "y24"; own = q.prev; }
    if (kind && (!rOk || RT_ROLL_RANK[kind] >= (RT_ROLL_RANK[r.kind] || 0))) {
      // A server-cached quote may still set the basis when its own timestamp is recent (short response cache);
      // an old cached print (stale fallback) never does.
      const qr = Number(q.ts ?? q.fetchedAt), qMs = qr > 0 && qr < 10_000_000_000 ? qr * 1000 : qr;
      if (!q.cached || (qMs > 0 && now - qMs < 5 * 60_000)) _rt.roll[tk] = { prev: own, at: now, kind };
      q.prev = own; q.c = ((q.p - own) / own) * 100;
    } else if (rOk) {
      q.prev = r.prev; q.c = ((q.p - r.prev) / r.prev) * 100;
    } else if (!kind) {
      delete q.c; delete q.prev; delete q.change;
    }
    // While the exchange socket connects, a streamed coin shows no polled 24h % (its basis differs slightly
    // from the exchange's own 24h open); after RT_CHG_HOLD_MS without a stream basis the polled basis is used.
    const cur = _rt.roll[tk];
    if (fin(q.prev) && q.prev > 0 && RT_USE.crypto && RT_CRYPTO[tk] && _rt.booted && !_rtDisabled() && !(_rt.want.size && !_rt.want.has(tk)) && !(cur && cur.kind === "stream" && now - cur.at < 30 * 60_000)) {
      const hu = _rt.holdUntil[tk] || (_rt.holdUntil[tk] = now + RT_CHG_HOLD_MS);
      if (now < hu) {
        _rt.heldPrev[tk] = q.prev;
        delete q.c; delete q.prev; delete q.change;
        setTimeout(() => _rtReleaseHold(tk), hu - now + 30);
      }
    }
  }
  const hasPrev = typeof q.prev === "number" && isFinite(q.prev) && q.prev > 0;
  // Spot gold's prior close only from a spot feed (Yahoo XAU maps to futures, a different basis).
  if (hasPrev && !proxyish && !RT_SRC.has(src) && !_rtIsCrypto(tk) && (tk !== "XAU" || src === "twelve-data")) _rt.goodPrev[tk] = q.prev;
  if (RT_SRC.has(src)) return false;
  const adoptPrev = () => {
    // Keep the fresher price, but adopt a missing prior close.
    if (hasPrev && !proxyish && liveQuoteChangeAvailable[tk] === false && P[tk]?.p > 0) {
      BASE[tk] = { p: q.prev, c: 0 };
      P[tk].c = +(((P[tk].p - q.prev) / q.prev) * 100).toFixed(2);
      liveQuoteChangeAvailable[tk] = true;
      _rt.dirty.add(tk);
    }
    return true;
  };
  // 2) A live stream tick younger than RT_HOLD_MS is never overwritten by a poll.
  if (RT_SRC.has(liveQuoteSrc[tk]) && now - (_rt.lastRecv[tk] || 0) <= RT_HOLD_MS) return adoptPrev();
  // 3) Tickers a stream covers (crypto, gold, FX/indices/futures): an older print never replaces a newer one
  //    (stale server cache, delayed fallback, …). US stocks keep the existing last-poll-wins behaviour because
  //    Yahoo stamps trade time while Twelve Data stamps fetch time, so their clocks are not comparable.
  const raw = Number(q.ts ?? q.fetchedAt);
  const inTs = raw > 0 && raw < 10_000_000_000 ? raw * 1000 : raw;
  const curTs = Number(liveQuoteTs[tk]);
  if (!_rtStreamable(tk)) {
    // Closed US cash session: Twelve Data and Yahoo print the same close with different clocks; keep the
    // quote with the newer provider timestamp instead of alternating sources on every refresh.
    let closed = !!liveQuoteMarketClosed[tk];
    try { if (!closed && typeof _usRegularOpen === "function") closed = !_usRegularOpen(); } catch (e) {}
    const curSrc = liveQuoteSrc[tk];
    if (closed && curSrc && curSrc !== src && liveSymbols.has(tk) && P[tk]?.p > 0 && curTs > 0 && !(inTs > curTs)) return adoptPrev();
    return false;
  }
  if (liveSymbols.has(tk) && P[tk]?.p > 0 && curTs > 0 && inTs > 0 && inTs < curTs - 5000) return adoptPrev();
  return false;
}

/** End of the connect-time hold: no stream basis arrived, so show the polled 24h basis after all. */
function _rtReleaseHold(tk) {
  try {
    const prev = _rt.heldPrev[tk];
    if (!(prev > 0) || RT_SRC.has(liveQuoteSrc[tk]) || liveQuoteChangeAvailable[tk] !== false || !(P[tk]?.p > 0)) return;
    if (Date.now() < (_rt.holdUntil[tk] || 0)) return;
    const r = _rt.roll[tk], base = r && r.prev > 0 && Date.now() - r.at < 30 * 60_000 ? r.prev : prev;
    BASE[tk] = { p: base, c: 0 };
    P[tk].c = +(((P[tk].p - base) / base) * 100).toFixed(2);
    liveQuoteChangeAvailable[tk] = true;
    delete _rt.heldPrev[tk];
    _rt.dirty.add(tk);
  } catch (e) {}
}

// ── Yahoo stream protobuf (PricingData) — tiny decoder, no dependency ──
function _rtDecodeYs(b64) {
  const bin = atob(b64), n = bin.length, b = new Uint8Array(n);
  for (let i = 0; i < n; i++) b[i] = bin.charCodeAt(i);
  const dv = new DataView(b.buffer);
  let i = 0; const o = {};
  const varint = () => { let r = 0, m = 1, x; do { x = b[i++]; r += (x & 0x7f) * m; m *= 128; } while (x & 0x80 && i < n); return r; };
  const zz = v => (v % 2 === 1 ? -(v + 1) / 2 : v / 2);
  while (i < n) {
    const key = varint(), f = Math.floor(key / 8), wt = key & 7;
    if (wt === 0) o[f] = varint();
    else if (wt === 5) { o[f] = dv.getFloat32(i, true); i += 4; }
    else if (wt === 1) { o[f] = dv.getFloat64(i, true); i += 8; }
    else if (wt === 2) { const len = varint(); if (f === 1) o[f] = new TextDecoder().decode(b.subarray(i, i + len)); i += len; }
    else break;
  }
  const hint = o[27] != null ? zz(o[27]) : null;
  const round = v => (typeof v === "number" && isFinite(v)) ? (hint != null && hint >= 0 && hint <= 8 ? +v.toFixed(hint) : +v.toPrecision(7)) : null;
  return { id: o[1], price: round(o[2]), time: o[3] != null ? zz(o[3]) : null, mh: o[7], change: round(o[12]) };
}
function _rtOnYs(ev) {
  _rt.stats.msgs.ys++;
  let m; try { m = JSON.parse(ev.data); } catch (e) { return; }
  if (!m || m.type !== "pricing" || !m.message) return;
  let d; try { d = _rtDecodeYs(m.message); } catch (e) { return; }
  if (!d.id || !(d.price > 0)) return;
  const tks = _rtYahooRev()[d.id];
  if (!tks) return;
  if (_rtIsUsEquitySym(d.id)) {
    // Stocks/ETFs: regular session only — extended-hours prints keep the existing RTH CLOSE handling.
    if (!_usRegularOpen()) return;
  }
  const prev = d.change != null ? d.price - d.change : null;
  tks.forEach(tk => _rtApply(tk, d.price, { src: "yahoo-stream", ts: d.time, prev: prev > 0 ? prev : null, name: tk === "DXY" ? "US Dollar Index" : undefined }));
}
function _rtOnCb(ev) {
  _rt.stats.msgs.cb++;
  let m; try { m = JSON.parse(ev.data); } catch (e) { return; }
  if (!m || m.type !== "ticker" || !m.product_id) return;
  const p = Number(m.price), open = Number(m.open_24h), ts = Date.parse(m.time) || Date.now();
  if (m.product_id === "PAXG-USD") { _rtPaxg(p, ts, "Coinbase"); return; }
  const tk = _rtCbRev()[m.product_id];
  if (tk) _rtApply(tk, p, { src: "coinbase-ws", ts, prev: open > 0 ? open : null, noBasePrev: true });
}
function _rtOnKr(ev) {
  _rt.stats.msgs.kr++;
  let m; try { m = JSON.parse(ev.data); } catch (e) { return; }
  if (!m || m.channel !== "ticker" || !Array.isArray(m.data)) return;
  m.data.forEach(row => {
    const p = Number(row.last), ch = Number(row.change);
    if (row.symbol === "PAXG/USD") { _rtPaxg(p, Date.now(), "Kraken"); return; }
    const tk = _rtKrRev()[row.symbol];
    if (tk) _rtApply(tk, p, { src: "kraken-ws", ts: Date.now(), prev: isFinite(ch) && p - ch > 0 ? p - ch : null, noBasePrev: true });
  });
}
function _rtCbRev() { return _rt.cbRev || (_rt.cbRev = Object.fromEntries(Object.entries(RT_CRYPTO).filter(([, v]) => v[0]).map(([tk, v]) => [v[0], tk]))); }
function _rtKrRev() { return _rt.krRev || (_rt.krRev = Object.fromEntries(Object.entries(RT_CRYPTO).filter(([, v]) => v[1]).map(([tk, v]) => [v[1], tk]))); }
function _rtPaxg(p, ts, venue) {
  if (!(p > 0)) return;
  const old = _rt.paxg?.p;
  _rt.paxg = { p, ts, venue, recv: Date.now() };
  if (old !== p || !_rt.paxgPainted) _rt.dirty.add("PAXG");
}
/** Secondary gold line for the XAU tile — clearly a tokenised-gold proxy, never the spot headline. */
function _rtPaxgLine() {
  const x = _rt.paxg;
  if (!x || Date.now() - x.recv > 10 * 60_000) return "";
  const px = x.p.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const age = _fmtAge(x.ts);
  return `<div class="front-door-quote-paxg" title="PAX Gold (PAXG) trading on ${_escAttr(x.venue)} — a tokenised-gold proxy that can sit at a premium or discount to spot. Not the XAU spot price.">PAXG ≈ $${_escHtml(px)} · ${_escHtml(x.venue)} stream · tokenised-gold proxy · last trade ${_escHtml(age)} ago</div>`;
}
function _rtCryptoNote() {
  return Object.keys(RT_CRYPTO).some(tk => liveQuoteSrc[tk] === "coinbase-ws" || liveQuoteSrc[tk] === "kraken-ws")
    ? " \u00b7 \u25cf price = live exchange stream (Coinbase/Kraken)" : "";
}
function _rtCoinTk(sym) { sym = String(sym || "").toUpperCase(); return sym === "POL" ? "MATIC" : sym; }
function _rtTableStale() { try { return !!(_cryptoAsOf && !isNaN(_cryptoAsOf)); } catch (e) { return false; } }
function _rtCgTableTs() {
  try { if (_cryptoAsOf && !isNaN(_cryptoAsOf)) return _cryptoAsOf.getTime(); } catch (e) {}
  return _rt.cgAt || 0;
}
/** Crypto rankings row values: the exchange stream when it is the freshest print, else the CoinGecko table row. */
function _rtCoinView(coin) {
  const tk = _rtCoinTk(coin && coin.symbol);
  const tc = coin ? (coin.price_change_percentage_24h_in_currency ?? coin.price_change_percentage_24h) : null;
  const out = { tk, p: coin ? coin.current_price : null, c24: typeof tc === "number" && isFinite(tc) ? tc : null, live: false, stream: false, desk: false, fresher: false, src: "coingecko", ts: _rtCgTableTs() };
  const now = Date.now(), r = _rt.roll[tk], rOk = r && r.prev > 0 && now - r.at < 30 * 60_000;
  const src = liveQuoteSrc[tk];
  if (src && liveSymbols.has(tk) && P[tk] && P[tk].p > 0) {
    const ts = Number(liveQuoteTs[tk]) || 0, age = now - ts;
    if ((src === "coinbase-ws" || src === "kraken-ws") && age < 10 * 60_000 && ts >= out.ts - 60_000) {
      out.stream = true; out.live = now - (_rt.lastRecv[tk] || 0) <= RT_HOLD_MS;
    } else if (!liveQuoteCached[tk] && age < 30 * 60_000 && ts >= out.ts - 3 * 60_000) {
      // The desk quote is (about) as new as the rankings snapshot: show the desk value so the table, watchlist
      // strip, tape and summary card read one value on one 24h basis.
      out.desk = true; out.fresher = src !== "coingecko";
    }
    if (out.stream || out.desk) {
      out.p = P[tk].p; out.src = src; out.ts = ts;
      const ch = liveChg(tk);
      out.c24 = ch != null ? ch : (rOk ? ((out.p - r.prev) / r.prev) * 100 : null);
      return out;
    }
  }
  // Rankings row: put its change on the ticker's best-known 24h basis (stream / Yahoo rolling 24h).
  if (rOk && r.kind !== "cg" && out.p > 0) out.c24 = ((out.p - r.prev) / r.prev) * 100;
  return out;
}
function _rtChgTxt(v) { return v == null || !isFinite(v) ? "—" : `${v > 0 ? "+" : ""}${Number(v).toFixed(2)}%`; }
/** /crypto/ status line: live with the latest tick time while streaming, honest fallback otherwise. */
function _rtCryptoHeaderText() {
  let data = null; try { data = _cryptoMktData; } catch (e) {}
  if (!Array.isArray(data) || !data.length) return "";
  let last = 0, src = "", n = 0, f = 0;
  data.forEach(c => { const v = _rtCoinView(c); if (v.fresher) f++; if (v.live) { n++; if (v.ts > last) { last = v.ts; src = v.src; } } });
  let stale = false, asOf = null; try { stale = !!(_cryptoAsOf && !isNaN(_cryptoAsOf)); asOf = stale ? _cryptoAsOf : null; } catch (e) {}
  const cg = stale
    ? `CoinGecko table delayed \u00b7 as of ${asOf.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
    : (_rt.cgAt ? `CoinGecko table \u00b7 fetched ${_fmtAsOf(_rt.cgAt)}` : "CoinGecko table");
  const fr = f ? ` \u00b7 ${f} row${f === 1 ? "" : "s"} from desk quotes (hover for source)` : "";
  return last
    ? `\u25cf Live \u00b7 ${_quoteSourceLabel(src)} \u00b7 last tick ${_fmtAsOf(last)} \u00b7 ${n} streamed row${n === 1 ? "" : "s"} marked \u25cf \u00b7 other values: ${cg}${fr}`
    : `Delayed \u00b7 ${cg}${fr}`;
}
function _rtCryptoHeader() {
  const t = _rtCryptoHeaderText();
  if (!t) return "";
  return `<div data-rt-crypto-hdr class="${t.startsWith("\u25cf") ? "rt-hdr-live" : ""}" style="font-family:var(--mn);font-size:10px;color:var(--t3);padding:2px 0 6px">${_escHtml(t)}</div>`;
}
/** Price + 24h cells for one rankings row (used by the renderer and the 1s painter). */
function _rtCoinCells(coin) {
  const v = _rtCoinView(coin);
  const staleTbl = !v.stream && !v.desk && _rtTableStale();
  const cls = `${v.live ? "rt-live" : ""}${staleTbl ? " rt-stale-cell" : ""}`.trim();
  const title = (v.stream || v.desk) ? `${_quoteSourceLabel(v.src)} \u00b7 ${_quoteMeta(v.tk).label} \u00b7 as of ${_fmtAsOf(v.ts)}` : staleTbl ? `CoinGecko \u00b7 delayed \u00b7 as of ${_fmtAsOf(v.ts)}` : `CoinGecko \u00b7 fetched ${_fmtAsOf(v.ts)}`;
  return { v, cls, title, px: v.p > 0 ? `$${_rtCryptoPx(v.p)}` : "—", chg: _rtChgTxt(v.c24),
    col: v.c24 == null ? "var(--t3)" : v.c24 > 0 ? "var(--gn)" : v.c24 < 0 ? "var(--rd)" : "var(--t3)" };
}
function _rtGoldChecked() {
  if (liveQuoteSrc.XAU !== "gold-api-spot-proxy-browser" || !_rt.goldChecked || Date.now() - _rt.goldChecked > 3 * 60_000) return "";
  return ` \u00b7 checked ${_fmtAsOf(_rt.goldChecked)}`;
}

// ── sockets: open / subscribe diff / reconnect with backoff / watchdog ──
function _rtOpen(key) {
  if (_rt.sock[key] || !_rt.running) return;
  const url = key === "cb" ? RT_CB_URL : key === "kr" ? RT_KR_URL : RT_YS_URL;
  let ws;
  try { ws = new WebSocket(url); } catch (e) { _rt.stats.errors++; _rtScheduleReconnect(key); return; }
  _rt.sock[key] = ws; _rt.subd[key] = new Set(); _rt.gotData[key] = false;
  _rt.stats.connects[key]++;
  ws.onopen = () => { _rt.lastMsg[key] = Date.now(); _rtSync(key); };
  ws.onmessage = ev => {
    _rt.lastMsg[key] = Date.now();
    if (!_rt.gotData[key]) { _rt.gotData[key] = true; _rt.attempts[key] = 0; if (key !== "ys") _rt.provFails = 0; }
    if (key === "cb") _rtOnCb(ev); else if (key === "kr") _rtOnKr(ev); else _rtOnYs(ev);
  };
  ws.onerror = () => { _rt.stats.errors++; };
  ws.onclose = () => {
    if (_rt.sock[key] !== ws) return;
    _rt.sock[key] = null; _rt.subd[key] = new Set(); _rt.stats.closes++;
    if (!_rt.running) return;
    if (key !== "ys" && !_rt.gotData[key] && ++_rt.provFails >= 3) { _rt.cryptoProv = 1 - _rt.cryptoProv; _rt.provFails = 0; }
    _rtScheduleReconnect(key);
  };
}
function _rtClose(key) {
  clearTimeout(_rt.reconnectT[key]); _rt.reconnectT[key] = null;
  const ws = _rt.sock[key];
  _rt.sock[key] = null; _rt.subd[key] = new Set();
  if (ws) { try { ws.onclose = null; ws.close(1000); } catch (e) {} }
}
function _rtScheduleReconnect(key) {
  if (!_rt.running || _rt.reconnectT[key]) return;
  const n = _rt.attempts[key] = (_rt.attempts[key] || 0) + 1;
  const delay = Math.min(60_000, 1000 * 2 ** Math.min(n - 1, 6)) * (0.8 + Math.random() * 0.4);
  _rt.reconnectT[key] = setTimeout(() => { _rt.reconnectT[key] = null; _rtSyncAll(); }, delay);
}
function _rtWanted(key) {
  const out = new Set();
  if (key === "ys" ? !RT_USE.yahoo : !RT_USE.crypto) return out;
  if (key === "ys") {
    const rev = _rtYahooRev(), cap = IS_DESKTOP() ? RT_YS_CAP_DESK : RT_YS_CAP_PHONE;
    const usOpen = _usRegularOpen();
    for (const tk of _rt.want) {
      const yh = YAHOO_SYMBOLS[tk];
      if (!yh || !rev[yh]) continue;
      if (_rtIsUsEquitySym(yh) && !usOpen) continue; // nothing to stream outside the regular session
      out.add(yh);
      if (out.size >= cap) break;
    }
    return out;
  }
  const col = key === "cb" ? 0 : 1;
  for (const tk of _rt.want) { const v = RT_CRYPTO[tk]; if (v && v[col]) out.add(v[col]); }
  if (_rt.want.has("XAU") && RT_CRYPTO.PAXG[col]) out.add(RT_CRYPTO.PAXG[col]);
  return out;
}
function _rtSend(key, ws, add, del) {
  const msgs = [];
  if (key === "cb") {
    if (del.length) msgs.push({ type: "unsubscribe", product_ids: del, channels: ["ticker"] });
    if (add.length) msgs.push({ type: "subscribe", product_ids: add, channels: ["ticker"] });
  } else if (key === "kr") {
    if (del.length) msgs.push({ method: "unsubscribe", params: { channel: "ticker", symbol: del } });
    if (add.length) msgs.push({ method: "subscribe", params: { channel: "ticker", symbol: add } });
  } else {
    if (del.length) msgs.push({ unsubscribe: del });
    if (add.length) msgs.push({ subscribe: add });
  }
  msgs.forEach(m => { try { ws.send(JSON.stringify(m)); } catch (e) {} });
}
function _rtSync(key) {
  const ws = _rt.sock[key];
  if (!ws || ws.readyState !== 1) return;
  const want = _rtWanted(key), have = _rt.subd[key];
  const add = [...want].filter(s => !have.has(s)), del = [...have].filter(s => !want.has(s));
  if (!add.length && !del.length) return;
  if (add.length) _rt.lastMsg[key] = Date.now(); // fresh subscription restarts the silence watchdog
  _rtSend(key, ws, add, del);
  _rt.subd[key] = want;
}
function _rtSyncAll() {
  if (!_rt.running) return;
  const cryptoKey = _rt.cryptoProv ? "kr" : "cb", otherKey = _rt.cryptoProv ? "cb" : "kr";
  _rtClose(otherKey);
  [cryptoKey, "ys"].forEach(key => {
    const want = _rtWanted(key);
    if (!want.size) {
      // Nothing on screen needs this feed: unsubscribe now, close after 60s idle (avoids reconnect churn while scrolling).
      _rt.emptySince[key] = _rt.emptySince[key] || Date.now();
      if (Date.now() - _rt.emptySince[key] > 60_000) _rtClose(key); else _rtSync(key);
      return;
    }
    _rt.emptySince[key] = 0;
    if (!_rt.sock[key]) { if (!_rt.reconnectT[key]) _rtOpen(key); return; }
    _rtSync(key);
    // Watchdog: a silent socket during an open market is treated as dead.
    const silentMs = Date.now() - (_rt.lastMsg[key] || Date.now());
    const limit = key === "ys" ? (_rtWeekend() ? Infinity : 120_000) : 45_000;
    if (_rt.sock[key]?.readyState === 1 && silentMs > limit) { try { _rt.sock[key].close(); } catch (e) {} }
  });
}

// ── which symbols matter right now: what is on screen (+ the desk tape) ──
function _rtScan() {
  const vh = window.innerHeight, vw = window.innerWidth, vis = new Set();
  const inView = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.bottom > 0 && r.top < vh && r.right > 0 && r.left < vw; };
  document.querySelectorAll("#tape .ti[data-tk],td[data-fl],[data-price-card],[data-live-price],.data-card[data-tk],[data-rt-px],.wl-glance-chip").forEach(el => {
    if (!inView(el)) return;
    let tk = el.dataset.tk || el.dataset.fl || el.dataset.priceCard || el.getAttribute("data-live-price") || el.dataset.rtPx;
    if (!tk && el.classList.contains("wl-glance-chip")) tk = ((el.getAttribute("onclick") || "").match(/openA\('([^']+)'\)/) || [])[1];
    if (tk) vis.add(tk);
  });
  if (pg === "home" || pg === "gold" || pg === "playbook") { vis.add("XAU"); vis.add("DXY"); }
  if (typeof termSelTk !== "undefined" && termSelTk) vis.add(termSelTk);
  _rt.visible = vis;
  const want = new Set(vis);
  // Desktop tape scrolls the whole TAPE_ORDER through view — keep it warm.
  const tape = document.getElementById("tape");
  if (IS_DESKTOP() && tape && tape.getBoundingClientRect().height > 0) TAPE_ORDER.forEach(tk => want.add(tk));
  _rt.want = want;
}
function _rtTick() {
  if (_rtDisabled()) { if (_rt.running) _rtPause("disabled"); return; }
  if (!_rt.running) { if (!document.hidden) _rtResume(); return; }
  _rtScan();
  _rtSyncAll();
  if (_rt.want.has("XAU") && !_rt.goldT) _rtGoldPoll();
}

// ── gold-api.com XAU spot proxy: poll just after each expected 30s update ──
async function _rtGoldPoll() {
  clearTimeout(_rt.goldT); _rt.goldT = null;
  if (!_rt.running || !_rt.want.has("XAU") || !RT_USE.gold) return;
  let next = 10_000;
  try {
    _rt.stats.goldPolls++;
    const r = await fetch(RT_GOLD_URL, { cache: "no-store", credentials: "omit", signal: AbortSignal.timeout(8000) });
    if (r.ok) {
      const j = await r.json();
      const p = Number(j?.price), ts = Date.parse(j?.updatedAt);
      if (p > 0 && ts > 0) {
        _rt.goldChecked = Date.now();
        _rtApply("XAU", p, { src: "gold-api-spot-proxy-browser", ts, proxy: true, name: "Spot Gold (proxy)", repaint: true });
        // upstream refreshes about every 30s: aim 2s after the next refresh
        const due = ts + 32_000 - Date.now();
        next = due > 3000 && due < 31_000 ? due : 5000;
      }
    }
  } catch (e) { next = 30_000; }
  if (_rt.running) _rt.goldT = setTimeout(_rtGoldPoll, next);
}

// ── visible symbols with no live stream: faster refresh via the cached proxy ──
async function _rtFastPoll() {
  if (!_rt.running || _rtDisabled() || document.hidden) return;
  const now = Date.now(), usOpen = _usRegularOpen(), weekend = _rtWeekend();
  const list = [..._rt.visible].filter(tk => {
    const yh = typeof YAHOO_SYMBOLS !== "undefined" && YAHOO_SYMBOLS[tk];
    if (!yh || tk === "XAU" || RT_CRYPTO[tk] || /-USD$/.test(yh)) return false;
    if (now - (_rt.lastRecv[tk] || 0) < 30_000) return false;   // already streaming
    if (_rtIsUsEquitySym(yh) && !usOpen) return false;          // closed session — nothing new to fetch
    if (weekend) return false;
    // Last print >30 min old (even allowing for a 15m delay) = that market is shut; the 60s loop covers reopen.
    if (liveQuoteTs[tk] && now - liveQuoteTs[tk] > 30 * 60_000) return false;
    return true;
  }).slice(0, 30);
  if (!list.length) return;
  _rt.stats.fastPolls++;
  try {
    const syms = [...new Set(list.map(tk => YAHOO_SYMBOLS[tk]))];
    const res = await fetch(`/api/yahoo-quote?symbols=${encodeURIComponent(syms.join(","))}`, { signal: AbortSignal.timeout(10_000) });
    if (!res.ok) return;
    const data = await res.json();
    list.forEach(tk => {
      const q = data && data[YAHOO_SYMBOLS[tk]];
      if (!q || !(q.p > 0)) return;
      const before = P[tk]?.p, hist = HIST[tk] ? HIST[tk].slice() : null;
      if (_applyLiveQuote(tk, q, "yahoo")) {
        if (hist) HIST[tk] = hist; else delete HIST[tk]; // keep sparklines on their own cadence
        if (P[tk]?.p !== before) { _rt.dirty.add(tk); _rt.dir[tk] = before == null ? 0 : (P[tk].p > before ? 1 : -1); }
      }
    });
  } catch (e) {}
}

// ── in-place painter: only changed tickers, at most once per second ──
function _rtFlash(el, tk) {
  const d = _rt.dir[tk];
  if (!el || !d || _rt.reduceMotion) return;
  el.classList.remove("rt-up", "rt-dn"); void el.offsetWidth; el.classList.add(d > 0 ? "rt-up" : "rt-dn");
}
function _rtTapeBadge(d) {
  return d.status === "live" ? '<span class="htec-live-dot" title="Near real-time"></span>'
    : d.status === "delayed" ? '<span class="tape-badge tape-del" title="Delayed free feed">D</span>'
    : d.status === "stale" ? '<span class="tape-badge tape-stale" title="Stale tick">S</span>'
    : d.status === "cached" ? '<span class="tape-badge tape-cache" title="Session cache">C</span>'
    : d.status === "closed" || d.status === "rth-close" ? '<span class="tape-badge tape-cache" title="Market closed — last regular-session print">CLOSED</span>'
    : d.status === "extended" ? '<span class="tape-badge tape-del" title="Extended-hours print (delayed)">D</span>'
    : '<span style="opacity:0.35;font-size:7px">○</span>';
}
/** Watchlist strip chip: on /crypto/ a coin in the rankings shows exactly the table's value; elsewhere the desk quote. */
function _rtChipVals(tk) {
  let row = null;
  try { if (pg === "crypto" && Array.isArray(_cryptoMktData)) row = _cryptoMktData.find(c => _rtCoinTk(c.symbol) === tk) || null; } catch (e) {}
  if (row) {
    const v = _rtCoinView(row);
    if (v.p > 0) {
      const c = v.c24, abs = c == null ? null : v.p - v.p / (1 + c / 100);
      const meta = v.stream || v.desk ? _quoteMeta(tk) : null;
      return { p: `${_rtCryptoPx(v.p)}`, c, abs, src: v.src, asOf: v.ts, label: meta ? meta.label : (_rtTableStale() ? "DELAYED" : "CoinGecko") };
    }
  }
  if (!hasSyncedQuote(tk)) return null;
  const d = fp(tk), ch = liveChg(tk);
  return { p: d.p, c: ch, abs: ch == null ? null : d.raw, src: d.src, asOf: d.asOf, label: d.label };
}
function _rtPaintChip(el, tk) {
  const x = _rtChipVals(tk); if (!x) return false;
  const pe = el.querySelector(".wl-g-p"), ce = el.querySelector(".wl-g-c");
  let moved = false;
  if (pe && pe.textContent !== x.p) { pe.textContent = x.p; moved = true; }
  if (ce) {
    const col = x.c == null ? "var(--t3)" : x.c > 0 ? "var(--gn)" : x.c < 0 ? "var(--rd)" : "var(--t3)";
    const sign = x.c != null && x.c >= 0 ? "+" : "";
    const a = Math.abs(x.abs || 0), absTxt = x.abs == null ? "" : `${x.abs >= 0 ? "+" : "-"}${a >= 1000 ? Math.round(a).toLocaleString() : a.toFixed(2)}`;
    const txt = x.c == null ? "—" : `${x.c > 0 ? "▲" : x.c < 0 ? "▼" : "•"} ${sign}${Number(x.c).toFixed(2)}% · ${absTxt}`;
    if (ce.textContent !== txt) ce.textContent = txt;
    ce.style.color = col;
  }
  const srcTxt = `${_quoteSourceLabel(x.src)} · as of ${_fmtAsOf(x.asOf)}`;
  el.title = srcTxt;
  const se = el.querySelector(':scope > span[style*="display:block"]'); if (se && se.textContent !== srcTxt) se.textContent = srcTxt;
  return moved;
}
/** Status lines are rendered once per page build; recount them in place (cheap: one pass over the desk list). */
function _rtRecountStatus() {
  if (typeof quoteStatusSummary !== "function") return;
  try {
    if (pg === "mkt") {
      const sub = document.querySelector('.pg-hdr[data-page-title="Markets"] .pg-hdr-sub');
      if (sub) {
        const dyn = typeof _dynMarkets !== "undefined" ? Object.keys(_dynMarkets).length : 0;
        const t = `${quoteStatusSummary(undefined, { includeUnavailable: true })} · ${dyn} dynamic`;
        if (sub.textContent !== t) sub.textContent = t;
      }
    }
    const p1 = document.getElementById("p1sub");
    if (p1 && typeof A !== "undefined") {
      const m = /^(\d+) of (\d+) · /.exec(p1.textContent || "");
      if (m && +m[1] === A.length && +m[2] === A.length) { // unfiltered desk list only
        const t = `${A.length} of ${A.length} · ${quoteStatusSummary(A.map(a => a.tk), { includeUnavailable: true })}`;
        if (p1.textContent !== t) p1.textContent = t;
      }
    }
    if (typeof renderStatus === "function") renderStatus(); // status chip (signature-guarded: no-op if unchanged)
    const cl = document.getElementById("cmdLive");
    if (cl && typeof quoteStatusCounts === "function" && !(typeof updatePaused !== "undefined" && updatePaused)) {
      const fc = quoteStatusCounts();
      if (fc.live || fc.closed || fc.cached || fc.delayed || fc.stale || fc.proxy) {
        const t = (typeof _usRegularOpen === "function" && !_usRegularOpen() ? "US MARKETS CLOSED · " : "") + quoteStatusSummary(undefined, { includeUnavailable: true });
        if (cl.textContent !== t) cl.textContent = t;
      }
    }
  } catch (e) {}
  _rt.recountAt = Date.now();
}
/** A ticker changed status (e.g. first stream tick turns CACHED into LIVE): recount within ~1.5s. */
function _rtRecountSoon() {
  const wait = 1500 - (Date.now() - _rt.recountAt);
  if (wait <= 0) { _rtRecountStatus(); return; }
  if (!_rt.recountT) _rt.recountT = setTimeout(() => { _rt.recountT = 0; _rtRecountStatus(); }, wait);
}
/** /crypto/ summary card: the "Top:" line reads the same row values as the table, ticking with the painter. */
function _rtPaintCryptoTop() {
  try {
    if (pg !== "crypto" || !Array.isArray(_cryptoMktData) || !_cryptoMktData.length) return;
    const el = document.querySelector("#siteIntelCard .si-insight");
    if (!el) return;
    const t = el.textContent, i = t.lastIndexOf(" Top: ");
    if (i < 0) return;
    const m = /^ Top: [^,]*?(?:[+\-]?\d+\.\d+%|\u2014)(?:, [^,]*?(?:[+\-]?\d+\.\d+%|\u2014))*\./.exec(t.slice(i));
    if (!m) return;
    const top = " Top: " + _cryptoMktData.slice(0, 3).map(c => String(c.symbol || "").toUpperCase() + " " + _rtChgTxt(_rtCoinView(c).c24)).join(", ") + ".";
    const nt = t.slice(0, i) + top + t.slice(i + m[0].length);
    if (nt !== t) el.textContent = nt;
  } catch (e) {}
}
/** Rankings table came back as a stale server copy (server SWR): the server revalidates in the background, so
 *  ask once more shortly; after that at most once a minute while it stays stale (only on /crypto/). */
function _rtCgTableLoaded() {
  try {
    if (!_rtTableStale() || Date.now() - _rt.cgRefetchAt < 60_000) return;
    _rt.cgRefetchAt = Date.now();
    clearTimeout(_rt.cgSwrT);
    _rt.cgSwrT = setTimeout(() => { if (pg === "crypto" && _rtTableStale() && !_cryptoMktLoading) fetchCryptoMarket(); }, 8000);
  } catch (e) {}
}
function _rtCgStaleTick() {
  try {
    if (pg !== "crypto" || !_rtTableStale() || _cryptoMktLoading || Date.now() - _rt.cgRefetchAt < 60_000) return;
    _rt.cgRefetchAt = Date.now();
    fetchCryptoMarket();
  } catch (e) {}
}
/** Every 5s, independent of the stream switch: placeholders, status lines, /crypto/ strip + header freshness. */
function _rtHousekeep() {
  if (document.hidden) return;
  _rtSparkScan();
  _rtRecountStatus();
  try {
    if (pg === "crypto") {
      _rtCgStaleTick();
      _rtPaintCryptoTop();
      document.querySelectorAll(".wl-glance-chip").forEach(el => {
        const tk = ((el.getAttribute("onclick") || "").match(/openA\('([^']+)'\)/) || [])[1];
        if (tk) _rtPaintChip(el, tk);
      });
      const h = document.querySelector("[data-rt-crypto-hdr]");
      if (h) { const t = _rtCryptoHeaderText(); if (t && h.textContent !== t) { h.textContent = t; h.classList.toggle("rt-hdr-live", t.startsWith("\u25cf")); } }
    }
  } catch (e) {}
}
/** fetchCrypto saw fresh CoinGecko data while the rankings table is a stale server copy: refresh the table once
 *  (at most once a minute; no blind polling — only on evidence that fresh data exists). */
function _rtCgFresh() {
  try {
    if (pg !== "crypto" || !_rtTableStale() || _cryptoMktLoading || Date.now() - _rt.cgRefetchAt < 60_000) return;
    _rt.cgRefetchAt = Date.now();
    fetchCryptoMarket();
  } catch (e) {}
}
function _rtPaint() {
  if (!_rt.dirty.size || document.hidden) return;
  const dirty = new Set(_rt.dirty); _rt.dirty.clear();
  let n = 0;
  const info = {};
  let stChanged = false;
  const get = tk => info[tk] || (info[tk] = (() => {
    const d = fp(tk), ch = liveChg(tk);
    if (_rt.lastSt[tk] !== d.status) { _rt.lastSt[tk] = d.status; stChanged = true; }
    return { d, ch, col: ch == null ? "var(--t3)" : ch > 0 ? "var(--gn)" : ch < 0 ? "var(--rd)" : "var(--t3)", sign: ch != null && ch >= 0 ? "+" : "" };
  })());
  const setText = (el, txt) => { if (el && el.textContent !== txt) { el.textContent = txt; n++; return true; } return false; };
  document.querySelectorAll("#tape .ti[data-tk],td[data-fl],[data-price-card],[data-live-price],.data-card[data-tk],[data-rt-px],[data-rt-c24],.wl-glance-chip").forEach(el => {
    let tk = el.dataset.tk || el.dataset.fl || el.dataset.priceCard || el.getAttribute("data-live-price") || el.dataset.rtPx || el.dataset.rtC24;
    if (!tk && el.classList.contains("wl-glance-chip")) tk = ((el.getAttribute("onclick") || "").match(/openA\('([^']+)'\)/) || [])[1];
    if (!tk || !dirty.has(tk) || !hasSyncedQuote(tk)) return;
    const { d, ch, col, sign } = get(tk);
    if (el.matches("#tape .ti")) {
      const k = el.children; if (k.length < 3) return;
      if (setText(k[1], d.p)) _rtFlash(el, tk);
      setText(k[2], ch == null ? "—" : sign + d.c + "%"); k[2].style.color = col;
      if (el.dataset.rtSt !== d.status) { el.dataset.rtSt = d.status; k[0].innerHTML = `${_escHtml(tk)}${_rtTapeBadge(d)}`; }
      el.title = `${tk} · ${d.label || "NO SYNC"}${d.asOf ? ` · as of ${_fmtAsOf(d.asOf)}` : ""}`;
      if (typeof _tapePrev !== "undefined") _tapePrev[tk] = d.p;
    } else if (el.matches("td[data-fl]")) {
      const meta = el.querySelector(".price-row-meta");
      let txt = [...el.childNodes].find(x => x.nodeType === 3 && x.textContent.trim());
      const a = typeof A !== "undefined" ? A.find(x => x.tk === tk) : null;
      const money = txt ? txt.textContent.trim().startsWith("$") : (meta ? !!a && ["Stock", "Crypto", "Commodity"].includes(a.cat) : !!el.closest("#wl-table"));
      const val = (money ? "$" : "") + d.p;
      if (!txt) { el.querySelectorAll(":scope > span").forEach(s => s.remove()); txt = document.createTextNode(""); el.insertBefore(txt, el.firstChild); }
      if (txt.textContent !== val) { txt.textContent = val; n++; _rtFlash(el, tk); }
      if (meta) meta.innerHTML = `${stat(tk)} ${asOfTag(tk)}`;
      const next = el.nextElementSibling;
      if (next && /%$/.test(next.textContent.trim()) || next && next.textContent.trim() === "—") {
        const arrow = ch == null || ch === 0 ? "" : (ch > 0 ? "↑" : "↓");
        const keepArrow = /^[↑↓]/.test(next.textContent.trim()) || !!meta || !!el.closest("#wl-table");
        setText(next, ch == null ? "—" : `${keepArrow ? arrow : ""}${sign}${d.c}%`); next.style.color = col;
      }
    } else if (el.matches("[data-price-card]")) {
      const showDollar = el.dataset.priceDollar === "1", pctOnly = el.dataset.priceChg === "pct";
      const pe = el.querySelector(".asset-price"), ce = el.querySelector(".asset-chg");
      if (pe && setText(pe, (showDollar ? "$" : "") + d.p)) _rtFlash(pe, tk);
      if (ce) {
        ce.style.color = col;
        setText(ce, ch == null ? "—" : (pctOnly ? `${sign}${d.c}%` : `${sign}${d.chg} (${sign}${d.c}%)`));
        ce.classList.remove("px-up", "px-dn", "px-flat");
        ce.classList.add(ch == null || ch === 0 ? "px-flat" : ch > 0 ? "px-up" : "px-dn");
      }
      const st = el.querySelector(".trust-stat");
      if (st && st.dataset.rtSt !== d.status + d.label) { const t = document.createElement("span"); t.innerHTML = stat(tk); const nn = t.firstElementChild; if (nn) { nn.dataset.rtSt = d.status + d.label; st.replaceWith(nn); } }
      const ao = el.querySelector(".asof-tag");
      if (ao) { const t = document.createElement("span"); t.innerHTML = asOfTag(tk); if (t.firstElementChild) ao.replaceWith(t.firstElementChild); }
    } else if (el.matches("[data-live-price]")) {
      if (setText(el, d.p)) _rtFlash(el, tk);
    } else if (el.matches(".data-card[data-tk]")) {
      const v = el.querySelector(".value"), c = el.querySelector(".change");
      if (v && setText(v, d.p)) _rtFlash(v, tk);
      if (c) { setText(c, ch == null ? "—" : `${sign}${d.chg} (${sign}${d.c}%)`); c.style.color = col; }
    } else if (el.matches(".wl-glance-chip")) {
      if (_rtPaintChip(el, tk)) _rtFlash(el.querySelector(".wl-g-p"), tk);
    } else if (el.matches("[data-rt-px],[data-rt-c24]")) {
      // Crypto rankings table: same row values as the renderer (the desk quote when it is current).
      const cells = _rtCoinCells({ symbol: tk });
      if (!cells.v.stream && !cells.v.desk) return;
      if (el.dataset.rtPx) {
        if (setText(el, cells.px)) _rtFlash(el, tk);
        el.classList.toggle("rt-live", cells.v.live); el.classList.remove("rt-stale-cell");
        el.title = cells.title;
      } else {
        setText(el, cells.chg); el.style.color = cells.col; el.classList.remove("rt-stale-cell");
      }
    }
  });
  const ch = document.querySelector("[data-rt-crypto-hdr]");
  if (ch) { const t = _rtCryptoHeaderText(); if (t && ch.textContent !== t) { ch.textContent = t; ch.classList.toggle("rt-hdr-live", t.startsWith("\u25cf")); } }
  if (pg === "crypto") _rtPaintCryptoTop();
  if (stChanged) _rtRecountSoon();
  // Analysis header, front door, gold dashboard
  try { if (typeof termSelTk !== "undefined" && termSelTk && dirty.has(termSelTk)) _patchP2LiveHeader(); } catch (e) {}
  if (pg === "home" && (dirty.has("XAU") || dirty.has("DXY") || dirty.has("PAXG"))) {
    try {
      if (_paintFrontDoorQuotes()) {
        _rt.paxgPainted = true;
        document.querySelectorAll(".front-door-quotes").forEach(box => {
          const tiles = box.querySelectorAll(".front-door-quote-value");
          if (dirty.has("XAU")) _rtFlash(tiles[0], "XAU");
          if (dirty.has("DXY")) _rtFlash(tiles[1], "DXY");
        });
      }
    } catch (e) {}
  }
  if (dirty.has("XAU") && (pg === "gold" || pg === "playbook")) {
    const px = livePx("XAU"), gd = document.querySelector(".gd-px");
    if (gd && px != null && typeof _gdPx === "function") {
      const t = gd.firstChild;
      if (t && t.nodeType === 3) { const val = `$${_gdPx(px)} `; if (t.textContent !== val) { t.textContent = val; n++; _rtFlash(gd, "XAU"); } }
      const k = document.querySelector(".gd-kicker"); if (k) setText(k, _rtGoldKicker());
    }
  }
  _rt.stats.paints++; _rt.stats.cells += n;
}
function _rtGoldKicker() {
  if (typeof livePx === "function" && livePx("XAU") != null && liveQuoteSrc.XAU) {
    const m = _quoteMeta("XAU");
    return `XAU · ${_quoteSourceLabel(liveQuoteSrc.XAU)} · ${m.label}${m.asOf ? ` · as of ${_fmtAsOf(m.asOf)}` : ""}${_rtGoldChecked()}`;
  }
  return "XAU · COMEX proxy GC=F · delayed";
}

// ── chart placeholders: fetched only near the viewport; drawn, or hidden cleanly, within ~20s ──
// spark() no longer fetches every card's intraday series at render time (a phone /markets/ load fired ~390
// chart requests, most of them rate-limited by the server and left as permanent "— loading —"). Instead:
//   • a placeholder far from the viewport is a blank frame and costs nothing;
//   • near the viewport, the existing _ensureSparkline() fetch starts and the frame says "— loading —";
//   • a fetch that ends without data hides the frame at once (retry after RT_SPARK_RETRY_MS, when visible);
//   • a fetch still pending after RT_SPARK_GIVEUP_MS hides the frame; if it lands later it still draws.
const RT_SPARK_GIVEUP_MS = 15_000, RT_SPARK_RETRY_MS = 5 * 60_000;
function _rtSparkGaveUp(tk) {
  try {
    const t = _rt.sparkFail[tk];
    if (!t) return false;
    if (Date.now() - t > RT_SPARK_RETRY_MS) { delete _rt.sparkFail[tk]; delete _rt.sparkTk[tk]; return false; }
    return true;
  } catch (e) { return false; }
}
function _rtSparkHiddenHtml(tk, w, h) {
  return `<div data-spark-tk="${tk}" data-spark-w="${w}" data-spark-h="${h}" data-rt-no-chart="1" role="img" aria-label="Intraday chart unavailable right now" title="Intraday chart unavailable right now" style="width:${w}px;height:${h}px;opacity:0"></div>`;
}
function _rtSparkHide(el) {
  if (el.dataset.rtNoChart) return;
  el.dataset.rtNoChart = "1";
  el.textContent = ""; el.style.border = "none"; el.style.opacity = "0";
  el.setAttribute("aria-label", "Intraday chart unavailable right now"); el.title = "Intraday chart unavailable right now";
}
function _rtSparkValid(tk) { return (HIST[tk] || []).filter(v => typeof v === "number" && isFinite(v) && v > 0).length; }
/** Placeholder text used by spark(): only a chart actually being fetched says "loading". */
function _rtSparkPhTxt(tk) { try { return _sparkPending.has(tk) ? "\u2014 loading \u2014" : ""; } catch (e) { return ""; } }
/** spark() rendered a placeholder: decide (just after the DOM update) whether it is near enough to fetch. */
function _rtSparkLazy(tk) {
  if (!_rt.lazyT) _rt.lazyT = setTimeout(() => { _rt.lazyT = 0; _rtSparkScan(); }, 60);
}
/** _ensureSparkline() finished (its finally): no data -> hide every frame for this ticker now. */
function _rtSparkDone(tk) {
  try {
    if (_rtSparkValid(tk) >= 5) { delete _rt.sparkFail[tk]; delete _rt.sparkTk[tk]; return; }
    let at = Date.now();
    // Failed only because the CoinGecko gate is backing off: allow a retry right after the back-off ends.
    try { if (typeof _cgBackoffUntil !== "undefined" && _cgBackoffUntil > at && _cgIdForTicker(tk)) at = at - RT_SPARK_RETRY_MS + (_cgBackoffUntil - at) + 5000; } catch (e) {}
    _rt.sparkFail[tk] = at; delete _rt.sparkTk[tk];
    document.querySelectorAll(`[data-spark-tk="${tk}"]`).forEach(el => { if (!el.querySelector("svg")) _rtSparkHide(el); });
  } catch (e) {}
}
function _rtSparkScan() {
  if (document.hidden || typeof _ensureSparkline !== "function") return;
  const now = Date.now(), vh = window.innerHeight || 800;
  document.querySelectorAll("[data-spark-tk]").forEach(el => {
    const tk = el.dataset.sparkTk;
    if (!tk) return;
    if (el.querySelector("svg")) {
      if (el.style.border || el.dataset.rtNoChart) { el.style.border = "none"; el.style.opacity = "1"; el.style.display = "block"; delete el.dataset.rtNoChart; el.removeAttribute("title"); el.setAttribute("aria-label", `${tk} intraday chart`); }
      return;
    }
    if (_rtSparkValid(tk) >= 5 && typeof _patchSparkline === "function") { delete _rt.sparkFail[tk]; delete _rt.sparkTk[tk]; _patchSparkline(tk); return; }
    if (_rtSparkGaveUp(tk)) { _rtSparkHide(el); return; }
    const st = _rt.sparkTk[tk];
    if (st && now - st.seen > RT_SPARK_GIVEUP_MS) { _rt.sparkFail[tk] = now; _rtSparkHide(el); return; }
    if (_sparkPending.has(tk)) {
      if (!st) _rt.sparkTk[tk] = { seen: now };
      if (!el.textContent && !el.dataset.rtNoChart) el.textContent = "\u2014 loading \u2014";
      return;
    }
    const r = el.getBoundingClientRect();
    if (!(r.width > 0) || r.bottom < -vh * 0.5 || r.top > vh * 1.5) { if (el.textContent) el.textContent = ""; return; }
    _rt.sparkTk[tk] = { seen: now };
    if (!el.dataset.rtNoChart) el.textContent = "\u2014 loading \u2014";
    try { _ensureSparkline(tk); } catch (e) {}
  });
}

// ── lifecycle ──
function _rtResume() {
  if (_rt.running || _rtDisabled() || document.hidden) return;
  _rt.running = true; _rt.stats.resumes++;
  _rt.reduceMotion = !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  _rt.timers = [
    setInterval(_rtTick, RT_SCAN_MS),
    setInterval(_rtPaint, RT_PAINT_MS),
    setInterval(_rtFastPoll, RT_FAST_POLL_MS),
  ];
  _rtScan(); _rtSyncAll(); _rtGoldPoll();
  // Back after longer than one normal loop interval: refresh everything else once (no extra cadence).
  const loopMs = Math.max(60, MOBILE() ? Math.max(updateFreq || 60, MOBILE_PRICE_FREQ) : (updateFreq || 60)) * 1000;
  if (_rt.booted && typeof priceLastFetch !== "undefined" && (!priceLastFetch || Date.now() - priceLastFetch.getTime() > loopMs)) {
    try { fetchLivePrices(); } catch (e) {}
  }
}
function _rtPause(why) {
  if (!_rt.running) return;
  _rt.running = false; _rt.stats.pauses++; _rt.lastPause = why;
  _rt.timers.forEach(clearInterval); _rt.timers = [];
  clearTimeout(_rt.goldT); _rt.goldT = null;
  ["cb", "kr", "ys"].forEach(_rtClose);
}
function _rtInit() {
  if (_rt.booted) return;
  _rt.booted = true;
  try {
    const css = document.createElement("style");
    css.id = "rt-layer-css";
    css.textContent = `@keyframes rtUp{0%{background-color:rgba(34,197,94,.30)}100%{background-color:transparent}}
@keyframes rtDn{0%{background-color:rgba(239,68,68,.30)}100%{background-color:transparent}}
.rt-up{animation:rtUp .9s ease-out;border-radius:3px}.rt-dn{animation:rtDn .9s ease-out;border-radius:3px}
.front-door-quote-paxg{margin-top:4px;font-family:var(--mn,monospace);font-size:10px;letter-spacing:.02em;color:var(--t3,#8a8f98)}
.rt-live::before{content:"\\25CF  ";color:var(--gn,#22c55e);font-size:7px;vertical-align:middle}
.rt-stale-cell{opacity:.7}
.rt-hdr-live{color:var(--gn,#22c55e)!important}
.rt-cg-table td,.rt-cg-table th{font-variant-numeric:tabular-nums}
.rt-cg-table td:nth-child(n+3),.rt-cg-table th{white-space:nowrap}
.rt-cg-table .cg-sym-in{display:none}
@media (max-width:420px){
.rt-cg-table{min-width:0!important;font-size:10px!important}
.rt-cg-table th,.rt-cg-table td{padding:7px 4px!important}
.rt-cg-table th:nth-child(4),.rt-cg-table td:nth-child(4),.rt-cg-table th:nth-child(8),.rt-cg-table td:nth-child(8){display:none}
.rt-cg-table td:nth-child(2) img{width:16px;height:16px}
.rt-cg-table td:nth-child(2){min-width:52px;white-space:nowrap}
.rt-cg-table td:nth-child(2) > div{gap:5px!important}
.rt-cg-table .cg-nm,.rt-cg-table .cg-sym{display:none!important}
.rt-cg-table .cg-sym-in{display:inline-block!important;max-width:44px;overflow:hidden;text-overflow:ellipsis;vertical-align:middle;font-size:10.5px;white-space:nowrap;word-break:keep-all;overflow-wrap:normal}
.rt-live::before{font-size:6px}
}
@media (prefers-reduced-motion: reduce){.rt-up,.rt-dn{animation:none}}`;
    document.head.appendChild(css);
  } catch (e) {}
  document.addEventListener("visibilitychange", () => { if (document.hidden) _rtPause("hidden"); else _rtResume(); });
  window.addEventListener("pagehide", () => _rtPause("pagehide"));
  window.addEventListener("pageshow", () => { if (!document.hidden) _rtResume(); });
  let st;
  window.addEventListener("scroll", () => { clearTimeout(st); st = setTimeout(() => { _rtSparkScan(); if (_rt.running) { _rtScan(); _rtSyncAll(); } }, 250); }, { passive: true, capture: true });
  setInterval(_rtHousekeep, 5000); // independent of the stream switch: placeholders, status lines, /crypto/ strip
  // A dormant check also notices pause/resume and manual-update settings.
  setInterval(() => { if (!_rt.running && !document.hidden && !_rtDisabled()) _rtResume(); }, 5000);
  _rtResume();
}
'''

APP_EDITS = [
    # 1. Real-time layer rt11 -> rt12 (lazy chart fetch + resolve/hide, crypto connect-time hold, stale /crypto/
    #    table re-ask, summary card + status chip tick, closed-market source stay-put, phone MKT CAP CSS).
    ("rt11 module -> rt12", RT11_MODULE, RT12_MODULE),
    # 2. Sparklines: fetch only near the viewport (decided by the rt layer just after render); a frame that is not
    #    being fetched is blank instead of a permanent "— loading —".
    ("spark(): lazy fetch + honest placeholder",
     r'''    if(!_skipLazy)_ensureSparkline(tk);
    return `<div data-spark-tk="${tk}" data-spark-w="${w}" data-spark-h="${h}" role="img" aria-label="Chart loading" style="width:${w}px;height:${h}px;display:flex;align-items:center;justify-content:center;font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.08em;border:1px dashed var(--gb);border-radius:4px;opacity:0.55">— loading —</div>`;''',
     r'''    if(!_skipLazy){if(typeof _rtSparkLazy==="function")_rtSparkLazy(tk);else _ensureSparkline(tk);}
    return `<div data-spark-tk="${tk}" data-spark-w="${w}" data-spark-h="${h}" role="img" aria-label="Chart loading" style="width:${w}px;height:${h}px;display:flex;align-items:center;justify-content:center;font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.08em;border:1px dashed var(--gb);border-radius:4px;opacity:0.55">${typeof _rtSparkPhTxt==="function"?_rtSparkPhTxt(tk):"— loading —"}</div>`;'''),
    # 3. A chart fetch that ends without data resolves its placeholders immediately (hidden, retried later).
    ("_ensureSparkline: report completion",
     r'''  finally{_sparkPending.delete(tk);}''',
     r'''  finally{_sparkPending.delete(tk);if(typeof _rtSparkDone==="function")_rtSparkDone(tk);}'''),
    # 4. Status pill: a shown price is labelled by its real status (RTH CLOSE / AH / PRE …), never UNAVAILABLE.
    ("stat(): label retained statuses",
     r'''  return `<span class="bd trust-stat trust-stat-na" title="${title}" style="background:var(--b3);color:var(--t3);font-size:7.5px">UNAVAILABLE</span>`;''',
     r'''  if(s!=="unavailable"&&d.label&&hasSyncedQuote(tk))return s==="extended"
    ?`<span class="bd trust-stat trust-stat-delayed" title="${title}" style="background:var(--blG);color:var(--bl);font-size:7.5px">${_escHtml(d.label)}</span>`
    :`<span class="bd trust-stat trust-stat-cached" title="${title}" style="background:var(--puG);color:var(--pu);font-size:7.5px">${_escHtml(d.label)}</span>`;
  return `<span class="bd trust-stat trust-stat-na" title="${title}" style="background:var(--b3);color:var(--t3);font-size:7.5px">UNAVAILABLE</span>`;'''),
    # 5. CoinGecko simple/price: no fake 0.00% when there is no 24h change, and a basis-less duplicate id
    #    (matic-network, dead since the POL migration) never overwrites the live POL row for MATIC.
    ("fetchCrypto: no fake 0% / dead duplicate id",
     r'''      if (row?.usd && row.usd > 0) out[tk] = { p: row.usd, c: typeof row.usd_24h_change === "number" ? row.usd_24h_change : 0, ...(cgStaleTs > 0 ? { ts: cgStaleTs, cached: true } : {}) };''',
     r'''      const hasChg = typeof row?.usd_24h_change === "number" && isFinite(row.usd_24h_change);
      if (!hasChg && out[tk]) return; // e.g. empty matic-network must not overwrite the POL row (keeps price-only fallback)
      if (row?.usd && row.usd > 0) out[tk] = { p: row.usd, ...(hasChg ? { c: row.usd_24h_change } : {}), ...(cgStaleTs > 0 ? { ts: cgStaleTs, cached: true } : {}) };'''),
    ("price loop: CoinGecko row without change has no basis",
     r'''if (_applyLiveQuote(tk, { p: row.p, c: row.c, prev: row.p / (1 + (row.c || 0) / 100), ...(row.ts ? { ts: row.ts, cached: true } : {}) }, "coingecko")) successCount++;''',
     r'''if (_applyLiveQuote(tk, { p: row.p, ...(typeof row.c === "number" && isFinite(row.c) ? { c: row.c, prev: row.p / (1 + row.c / 100) } : {}), ...(row.ts ? { ts: row.ts, cached: true } : {}) }, "coingecko")) successCount++;'''),
    # 6. Rankings table: no fake 0% either; a stale (SWR) server copy is re-asked shortly, then <= 1/min.
    ("fetchCryptoMarket: no fake 0%",
     r'''c:typeof chg==="number"&&isFinite(chg)?chg:0,''',
     r'''...(typeof chg==="number"&&isFinite(chg)?{c:chg}:{}),'''),
    ("fetchCryptoMarket: stale table -> re-ask",
     r'''      if(typeof _rt!=="undefined")_rt.cgAt=Date.now();''',
     r'''      if(typeof _rt!=="undefined")_rt.cgAt=Date.now();
      if(typeof _rtCgTableLoaded==="function")_rtCgTableLoaded();'''),
    # 7. Rankings MKT CAP / VOL: compact ($314.9B) so the phone column fits.
    ("crypto table compact market cap",
     r'''return n>=1e12?`$${(n/1e12).toFixed(2)}T`:n>=1e9?`$${(n/1e9).toFixed(2)}B`:n>=1e6?`$${(n/1e6).toFixed(1)}M`:'$'+n.toLocaleString();''',
     r'''return n>=1e12?`$${(n/1e12).toFixed(2)}T`:n>=1e9?`$${(n/1e9).toFixed(1)}B`:n>=1e6?`$${(n/1e6).toFixed(1)}M`:'$'+Math.round(n).toLocaleString();'''),
]

INDEX_EDITS = [
    ("cache-bust app.js chat11 -> chat12",
     '/app.js?v=chat11"',
     '/app.js?v=chat12"'),
]


def load(path):
    with open(path, "rb") as f:
        raw = f.read().decode("utf-8")
    crlf = "\r\n" in raw
    return raw.replace("\r\n", "\n"), crlf


def apply(text, edits, label, errors):
    for e in edits:
        name, old, new = e[0], e[1], e[2]
        want = e[3] if len(e) > 3 else 1
        n = text.count(old)
        if n != want:
            errors.append(f"{label}: '{name}' anchor matched {n} times (need exactly {want})")
            continue
        text = text.replace(old, new)
    return text


def node_check(js_text, label, errors, required):
    node = shutil.which("node")
    if not node:
        if required:
            errors.append(f"{label}: node not found on PATH for `node --check` (use --skip-node-check to override)")
        else:
            print(f"WARN: node not found; {label} not syntax-checked")
        return
    fd, tmp = tempfile.mkstemp(suffix=".js")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(js_text.encode("utf-8"))
        r = subprocess.run([node, "--check", tmp], capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            errors.append(f"{label}: node --check failed: {(r.stderr or r.stdout).strip()[:400]}")
    finally:
        try: os.remove(tmp)
        except OSError: pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="dry run; write nothing")
    ap.add_argument("--dir", default=".", help="folder containing app.js and index.html")
    a = ap.parse_args()
    app_p, idx_p = (os.path.join(a.dir, n) for n in ("app.js", "index.html"))
    for p in (app_p, idx_p):
        if not os.path.isfile(p):
            sys.exit(f"ABORT: {p} not found — nothing written")
    app, app_crlf = load(app_p)
    idx, idx_crlf = load(idx_p)
    if MARKER in app or 'app.js?v=chat12"' in idx:
        sys.exit("ABORT: rt12 already applied (marker / chat12 found) — refusing to run twice; nothing written")
    if PREV_MARKER not in app or 'app.js?v=chat11"' not in idx:
        sys.exit("ABORT: these are not the chat11 (rt11) files — nothing written")
    errors = []
    new_app = apply(app, APP_EDITS, "app.js", errors)
    new_idx = apply(idx, INDEX_EDITS, "index.html", errors)
    if not errors:
        if (new_app.count(MARKER) != 1 or PREV_MARKER in new_app or "function _rtSparkScan()" not in new_app
                or "_rtSparkSweep" in new_app or new_idx.count('app.js?v=chat12"') != 1):
            errors.append("post-edit sanity check failed")
        node_check(new_app, "app.js", errors, required=False)
    if errors:
        print("ABORT — no files written:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print(f"OK: {len(APP_EDITS)} app.js edits, {len(INDEX_EDITS)} index.html edit verified"
          f" (app.js {len(new_app) - len(app):+d} chars); server.js not touched")
    if a.check:
        print("--check: dry run, nothing written")
        return
    outs = [(app_p, new_app, app_crlf), (idx_p, new_idx, idx_crlf)]
    tmps = []
    try:
        for p, text, crlf in outs:
            if crlf:
                text = text.replace("\n", "\r\n")
            tmp = p + ".rt12.tmp"
            with open(tmp, "wb") as f:
                f.write(text.encode("utf-8"))
            tmps.append((tmp, p))
    except Exception as e:
        for tmp, _ in tmps:
            try: os.remove(tmp)
            except OSError: pass
        sys.exit(f"ABORT: could not stage output ({e}) — no files written")
    for tmp, p in tmps:
        os.replace(tmp, p)
    print("Written: app.js, index.html (app.js?v=chat12)")


if __name__ == "__main__":
    main()
