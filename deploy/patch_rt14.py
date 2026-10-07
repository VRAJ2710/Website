#!/usr/bin/env python3
"""
patch_rt14.py — The Dispatch Markets: rt14 (chat13 -> chat14). CLIENT ONLY (server.js untouched).

Usage (from the Replit workspace root, next to app.js and index.html):
    python3 patch_rt14.py --check          # dry run: verify every anchor (+ node --check if available), write nothing
    python3 patch_rt14.py                  # apply app.js + index.html
    python3 patch_rt14.py --dir PATH       # files live elsewhere

What it changes (UI polish; the realtime price layer logic is untouched):
  1. Gold desk (/gold/, and the shared hero on /playbook/):
     - plain kicker "Gold spot (reference) · updated HH:MM:SS" (provider detail moved to the tooltip);
     - hero % uses the tape's XAU basis (spot vs prior close); the desk payload's 0 is never shown as +0.00%;
     - session / prior-day highs & lows, ATR(14), 20-day realised vol, support / resistance (swing pivots) and the
       market-structure text are computed from COMEX gold futures (GC=F) daily bars through the EXISTING cached
       /api/yahoo-chart proxy: one request per visit, 10-minute client cache, one retry, no polling;
     - cards with no data (volume profile, empty gamma, AI zero-input volatility/levels) are hidden, never "$—"/"$0";
     - "xAI" source text -> "AI scenario analysis"; dev "Build sequence" card removed; card top gap fixed;
       header Refresh + stray accent bar tidied (Refresh moved into the hero footer); event rows no longer overlap.
  2. Home: "Pick up where you left off" / "Start here" chips hidden on phones (< 768px; the bottom bar covers them),
     even grid on desktop. Footer disclaimer rewritten in plain English with an "Updated HH:MM:SS" line.
  3. Signed-in bottom bar: Home / Brief / Playbook / Gold / More (Dashboard moves into More); Dashboard gets its own
     grid icon (it used to reuse the house icon).
  4. Copy: "· N dynamic" removed from the Markets header; regime chip reads RISK-ON / MIXED / RISK-OFF on phones
     (score in the tooltip); data-trust pills in plain English.
  5. Phone tap targets: status-bar focus/sync buttons and watchlist-glance buttons get a 44px hit area.
     Desktop: the command bar's duplicate feed summary is hidden below 1440px so Sign in / clock no longer overflow.
Applies only on top of the live chat13 files (rt13 layer present). Every edit is an exact-string replacement
that must match exactly once; if any anchor fails, nothing is written. Refuses to run twice (rt14 marker /
chat14). CRLF safe. Writes go to *.rt14.tmp first and are renamed into place only after every check passed.
No new endpoint, no new server background work, no long-lived connection.
"""
import argparse, os, shutil, subprocess, sys, tempfile

MARKER = "REALTIME PRICE LAYER (rt14)"
PREV_MARKER = "REALTIME PRICE LAYER (rt13)"

APP_EDITS = [
    ('module header rt13 -> rt14',
     r'''// REALTIME PRICE LAYER (rt13) — browser-direct, free, keyless.''',
     r'''// REALTIME PRICE LAYER (rt14) — browser-direct, free, keyless.'''),
    ('module notes',
     r'''// a stream label / LIVE count needs a tick in the last 30s; batched flashes; proxy tape badge "P".
''',
     r'''// a stream label / LIVE count needs a tick in the last 30s; batched flashes; proxy tape badge "P".
// rt14 (UI only): plain gold kicker + hero % from the tape basis; no "N dynamic" suffix in the Markets status.
'''),
    ("Markets status recount: no 'N dynamic'",
     r'''        const dyn = typeof _dynMarkets !== "undefined" ? Object.keys(_dynMarkets).length : 0;
        const t = `${quoteStatusSummary(undefined, { includeUnavailable: true })} · ${dyn} dynamic`;''',
     r'''        const t = quoteStatusSummary(undefined, { includeUnavailable: true });'''),
    ("renderMkt header: no 'N dynamic'",
     r'''let h = _renderPgHdr("Markets", `${feedSummary} · ${dynCount} dynamic`, `<span class="live-dot"></span>`);''',
     r'''let h = _renderPgHdr("Markets", feedSummary, `<span class="live-dot"></span>`);'''),
    ('painter: gold hero % follows the tape basis',
     r'''      const k = document.querySelector(".gd-kicker"); if (k) setText(k, _rtGoldKicker());
    }''',
     r'''      const k = document.querySelector(".gd-kicker"); if (k) setText(k, _rtGoldKicker());
      const c = document.querySelector(".gd-chg"), cv = typeof liveChg === "function" ? liveChg("XAU") : null;
      if (c && cv != null && cv !== 0) { const ct = _gdChg(cv); if (c.textContent !== ct) { c.textContent = ct; c.className = `gd-chg ${cv >= 0 ? "px-up" : "px-dn"}`; } }
    }'''),
    ('_rtGoldKicker: plain label (+ title helper)',
     r'''function _rtGoldKicker() {
  if (typeof livePx === "function" && livePx("XAU") != null && liveQuoteSrc.XAU) {
    const m = _quoteMeta("XAU");
    return `XAU · ${_quoteSourceLabel(liveQuoteSrc.XAU)} · ${m.label}${m.asOf ? ` · as of ${_fmtAsOf(m.asOf)}` : ""}${_rtGoldChecked()}`;
  }
  return "XAU · COMEX proxy GC=F · delayed";
}''',
     r'''function _rtGoldKicker() {
  // rt14: plain words up front; the provider / status / checked detail moves to the tooltip (_rtGoldKickerTitle).
  if (typeof livePx === "function" && livePx("XAU") != null && liveQuoteSrc.XAU) {
    const m = _quoteMeta("XAU");
    const src = String(liveQuoteSrc.XAU || "");
    const kind = /gold-api|proxy/i.test(src) || m.status === "proxy" ? "Gold spot (reference)" : "Gold spot";
    const lag = /delayed|stale|cached|closed|close/i.test(`${m.status || ""} ${m.label || ""}`) ? ` · ${String(m.label || m.status).toLowerCase()}` : "";
    return `${kind}${lag}${m.asOf ? ` · updated ${_fmtAsOf(m.asOf)}` : ""}`;
  }
  return "Gold · COMEX futures (GC=F) · delayed";
}
function _rtGoldKickerTitle() {
  try {
    if (typeof livePx === "function" && livePx("XAU") != null && liveQuoteSrc.XAU) {
      const m = _quoteMeta("XAU");
      return `${_quoteSourceLabel(liveQuoteSrc.XAU)} · ${m.label}${m.asOf ? ` · as of ${_fmtAsOf(m.asOf)}` : ""}${_rtGoldChecked()}`;
    }
  } catch (e) {}
  return "COMEX gold futures (GC=F), delayed";
}'''),
    ('loadGoldDesk: cached path also loads GC=F bars',
     r'''  if (!force && _goldDesk && Date.now() - _goldDeskFetchedAt < 120000) {
    if (pg === "gold") _refreshGoldView();''',
     r'''  if (!force && _goldDesk && Date.now() - _goldDeskFetchedAt < 120000) {
    try { if (_isPremium()) _gdLoadHist(); } catch (_) {}
    if (pg === "gold") _refreshGoldView();'''),
    ('loadGoldDesk: GC=F bars alongside the desk',
     r'''  _goldDeskLoad = true;
  _goldDeskErr = null;''',
     r'''  try { _gdLoadHist(force); } catch (_) {}
  _goldDeskLoad = true;
  _goldDeskErr = null;'''),
    ('GC=F daily-bar helpers',
     r'''function _gdVpBars(bins) {''',
     r'''// rt14: the desk's levels, sessions and volatility come from COMEX gold futures (GC=F) daily bars through the
// existing cached /api/yahoo-chart proxy: one request per gold visit (10-min client cache, one retry), never polled.
let _gdHist = null, _gdHistAt = 0, _gdHistLoad = false, _gdHistErrAt = 0;
async function _gdLoadHist(force) {
  if (_gdHistLoad) return;
  const age = Date.now() - _gdHistAt;
  if (_gdHist && age < (force ? 60_000 : 600_000)) return;
  if (!force && _gdHistErrAt && Date.now() - _gdHistErrAt < 60_000) return;
  _gdHistLoad = true;
  let st = null;
  try {
    for (let i = 0; i < 2 && !st; i++) {
      if (i) await new Promise(r => setTimeout(r, 5000));
      try {
        const r = await fetch("/api/yahoo-chart?symbol=GC%3DF&range=6mo&interval=1d");
        const j = r.ok ? await r.json() : null;
        st = _gdStats(j?.chart?.result?.[0]);
      } catch (_) {}
    }
  } finally { _gdHistLoad = false; }
  if (st) { _gdHist = st; _gdHistAt = Date.now(); _gdHistErrAt = 0; } else _gdHistErrAt = Date.now();
  if (pg === "gold" || pg === "playbook") _refreshGoldView();
}
function _gdStats(res) {
  const q = res?.indicators?.quote?.[0], ts = res?.timestamp;
  if (!q || !Array.isArray(ts)) return null;
  const ok = v => typeof v === "number" && isFinite(v) && v > 0;
  const bars = [];
  for (let i = 0; i < ts.length; i++) {
    const o = q.open?.[i], hi = q.high?.[i], lo = q.low?.[i], c = q.close?.[i];
    if (ok(o) && ok(hi) && ok(lo) && ok(c) && hi >= lo) bars.push({ t: ts[i] * 1000, h: hi, l: lo, c });
  }
  if (bars.length < 30) return null;
  const meta = res.meta || {};
  const last = bars[bars.length - 1], prev = bars[bars.length - 2];
  const px = ok(meta.regularMarketPrice) ? meta.regularMarketPrice : last.c;
  const done = bars.slice(0, -1); // the latest bar may still be trading
  const tr = [];
  for (let i = 1; i < done.length; i++) { const b = done[i], pc = done[i - 1].c; tr.push(Math.max(b.h - b.l, Math.abs(b.h - pc), Math.abs(b.l - pc))); }
  const atr = tr.length >= 14 ? tr.slice(-14).reduce((a, b) => a + b, 0) / 14 : null;
  const closes = done.map(b => b.c);
  const rets = [];
  for (let i = Math.max(1, closes.length - 20); i < closes.length; i++) rets.push(Math.log(closes[i] / closes[i - 1]));
  let rv = null;
  if (rets.length >= 19) { const m = rets.reduce((a, b) => a + b, 0) / rets.length; rv = Math.sqrt(rets.reduce((a, b) => a + (b - m) ** 2, 0) / (rets.length - 1) * 252) * 100; }
  const sma = n => closes.length >= n ? closes.slice(-n).reduce((a, b) => a + b, 0) / n : null;
  const sma20 = sma(20), sma50 = sma(50);
  // Swing pivots: a session whose high (low) is above (below) the two sessions either side; last 90 sessions.
  const win = done.slice(-90), hiP = [], loP = [];
  for (let i = 2; i < win.length - 2; i++) {
    const b = win[i], nb = [win[i - 2], win[i - 1], win[i + 1], win[i + 2]];
    if (nb.every(x => b.h > x.h)) hiP.push(b.h);
    if (nb.every(x => b.l < x.l)) loP.push(b.l);
  }
  const near = 0.003;
  const touches = (L, k) => win.filter(b => Math.abs(b[k] - L) / L <= near).length;
  const uniq = arr => { const out = []; arr.forEach(v => { if (!out.some(x => Math.abs(x - v) / v <= near)) out.push(v); }); return out; };
  const resL = uniq(hiP.filter(v => v > px * 1.001).sort((a, b) => a - b)).slice(0, 2).map(v => ({ level: v, hits: touches(v, "h") }));
  const supL = uniq(loP.filter(v => v < px * 0.999).sort((a, b) => b - a)).slice(0, 2).map(v => ({ level: v, hits: touches(v, "l") }));
  let trend = "mixed trend";
  if (sma20 && sma50) {
    if (px > sma20 && sma20 > sma50) trend = "uptrend";
    else if (px < sma20 && sma20 < sma50) trend = "downtrend";
  }
  const atrPct = atr ? atr / px * 100 : null;
  const cond = atrPct == null ? null : atrPct < 0.9 ? "low" : atrPct <= 1.8 ? "normal" : "elevated";
  const sessHigh = ok(meta.regularMarketDayHigh) ? Math.max(meta.regularMarketDayHigh, last.h) : last.h;
  const sessLow = ok(meta.regularMarketDayLow) ? Math.min(meta.regularMarketDayLow, last.l) : last.l;
  const mt = Number(meta.regularMarketTime) > 0 ? Number(meta.regularMarketTime) * 1000 : last.t;
  return { px, prevClose: prev.c, chgPct: prev.c ? (px / prev.c - 1) * 100 : null,
    sessDate: last.t, sessHigh, sessLow, prevDate: prev.t, prevHigh: prev.h, prevLow: prev.l,
    atr, atrPct, rv, sma20, sma50, trend, cond, sup: supL, res: resL, asOf: mt };
}
function _gdStructText(s) {
  const f = v => `$${_gdPx(Math.round(v * 10) / 10)}`;
  const out = [];
  if (s.chgPct != null) out.push(`COMEX gold futures are ${s.chgPct >= 0 ? "up" : "down"} ${Math.abs(s.chgPct).toFixed(2)}% on the session (${f(s.px)} vs ${f(s.prevClose)} prior close).`);
  if (s.sma20 && s.sma50) out.push(`Price is ${s.px >= s.sma20 ? "above" : "below"} its 20-day average (${f(s.sma20)}) and ${s.px >= s.sma50 ? "above" : "below"} its 50-day average (${f(s.sma50)}).`);
  if (s.atr) out.push(`Daily ranges are ${s.cond}: ATR(14) ${f(s.atr)}, ${s.atrPct.toFixed(1)}% of price.`);
  return out.join(" ");
}
function _gdVpBars(bins) {'''),
    ('gold header: Refresh leaves the page header',
     r'''  const hdrActions = `<div class="pg-hdr-actions">
    <button type="button" class="btn btn-ghost btn-sm" onclick="loadGoldDesk(true)">${_goldDeskLoad ? "Loading…" : "⟳ Refresh"}</button>
  </div>`;''',
     r'''  const hdrActions = ""; // rt14: Refresh lives in the hero footer (the header button + accent bar looked orphaned on phones)'''),
    ('gold gate copy',
     r'''      <div class="empty-title">Gold desk unavailable</div>
      ${premiumGate''',
     r'''      <div class="empty-title">${premiumGate ? "The Gold Dashboard is part of Premium" : "Gold desk unavailable"}</div>
      ${premiumGate ? `<div class="empty-sub" style="margin-bottom:12px">Sign in or subscribe to see gold levels, sessions and volatility.</div>` : ""}
      ${premiumGate'''),
    ('gold hero',
     r'''  const d = _goldDesk;
  const g = d.gold || {};
  const px = livePxN != null ? livePxN : g.price;
  const chg = g.changePct;
  const chgCls = chg == null ? "px-flat" : chg >= 0 ? "px-up" : "px-dn";

  h += `<div class="gd-hero gc">
    <div class="gd-hero-top">
      <div>
        <div class="gd-kicker">${_escHtml(typeof _rtGoldKicker === "function" ? _rtGoldKicker() : "XAU · COMEX proxy GC=F · delayed")}</div>
        <div class="gd-px">$${_gdPx(px)} <span class="gd-chg ${chgCls}">${_gdChg(chg)}</span></div>
        <div class="gd-sub">${_escHtml(d.structure?.regime || "—")} · vol ${d.volatility?.condition || "—"} (ATR $${_gdPx(d.volatility?.atr14)})</div>
      </div>
      <div class="gd-hero-right">
        ${_gdSpark(g.spark)}
        <div class="gd-macro-mini">
          <span>DXY <b>${d.macro?.dxy?.px != null ? d.macro.dxy.px : "—"}</b></span>
          <span>10Y <b>${d.macro?.tnx?.px != null ? d.macro.tnx.px + "%" : "—"}</b></span>
          <span>VIX <b>${d.macro?.vix?.px != null ? d.macro.vix.px : "—"}</b></span>
        </div>
      </div>
    </div>
    <div class="gd-asof">As of ${d.asOf ? new Date(d.asOf).toLocaleString() : "—"} · ${_escHtml(d.dataSource || "")}</div>
  </div>`;''',
     r'''  const d = _goldDesk;
  const g = d.gold || {};
  const gs = _gdHist; // rt14: COMEX GC=F daily-bar stats (null until loaded)
  const px = livePxN != null ? livePxN : g.price;
  // rt14: the hero % uses the tape's XAU basis (spot vs prior close). The desk payload's changePct comes from a
  // spot reference that carries no change, so a 0 there is "unknown", never "+0.00%".
  const lcN = typeof liveChg === "function" ? liveChg("XAU") : null;
  const aiBlind = !(Number.isFinite(g.changePct) && g.changePct !== 0); // the AI saw no price change at all
  const chg = lcN != null && lcN !== 0 ? lcN : (!aiBlind ? g.changePct : null);
  const chgCls = chg == null ? "px-flat" : chg >= 0 ? "px-up" : "px-dn";
  const aiAtr = !aiBlind && d.volatility?.atr14 > 0 ? d.volatility.atr14 : null;
  const heroSub = gs
    ? `${gs.trend} · daily range ${gs.cond || "—"}${gs.atr ? ` (ATR $${_gdPx(Math.round(gs.atr * 10) / 10)}, futures)` : ""}`
    : aiAtr ? `${d.structure?.regime || "—"} · vol ${d.volatility?.condition || "—"} (ATR $${_gdPx(aiAtr)})` : "";
  const dxyPx = d.macro?.dxy?.px, dxyTxt = Number.isFinite(dxyPx) ? Number(dxyPx).toFixed(2) : "—";
  const aiAt = d.asOf ? _fmtAsOf(new Date(d.asOf).getTime()) : "";

  h += `<div class="gd-hero gc">
    <div class="gd-hero-top">
      <div>
        <div class="gd-kicker" title="${_escHtml(typeof _rtGoldKickerTitle === "function" ? _rtGoldKickerTitle() : "")}">${_escHtml(typeof _rtGoldKicker === "function" ? _rtGoldKicker() : "Gold · COMEX futures (GC=F) · delayed")}</div>
        <div class="gd-px">$${_gdPx(px)} <span class="gd-chg ${chgCls}">${chg != null ? _gdChg(chg) : ""}</span></div>
        ${heroSub ? `<div class="gd-sub">${_escHtml(heroSub)}</div>` : ""}
      </div>
      <div class="gd-hero-right">
        ${_gdSpark(g.spark)}
        <div class="gd-macro-mini">
          <span>DXY <b>${dxyTxt}</b></span>
          <span>10Y <b>${d.macro?.tnx?.px != null ? d.macro.tnx.px + "%" : "—"}</b></span>
          <span>VIX <b>${d.macro?.vix?.px != null ? d.macro.vix.px : "—"}</b></span>
        </div>
      </div>
    </div>
    <div class="gd-hero-foot">
      <div class="gd-asof">Spot: reference feed · Levels &amp; volatility: COMEX gold futures (GC=F) daily bars, Yahoo Finance, delayed${gs ? ` · as of ${_escHtml(_fmtAsOf(gs.asOf))}` : ""} · AI scenario analysis${aiAt ? ` ${_escHtml(aiAt)}` : ""}</div>
      <button type="button" class="gd-refresh" onclick="loadGoldDesk(true)"${_goldDeskLoad ? " disabled" : ""}>${_goldDeskLoad ? "Refreshing…" : "↻ Refresh"}</button>
    </div>
  </div>`;'''),
    ('playbook: gamma card only when it has levels',
     r'''    const kl = pb.keyLevels || {};
    h += `<div class="gd-card gc">
      <div class="gd-sec-h">Gamma & liquidity zones</div>
      <p class="gd-disclaimer">${_escHtml(d.gamma?.disclaimer || "Proxy levels — not dealer GEX.")}</p>
      <div class="gd-levels">${(kl.gammaLiquidity || d.gamma?.levels || []).slice(0, 8).map(L =>
        `<span class="gd-chip" title="${_escHtml(L.label || "")}">$${_gdPx(L.level)} · ${_escHtml(L.label || L.kind || "")}</span>`
      ).join("")}</div>
    </div>`;''',
     r'''    const kl = pb.keyLevels || {};
    const gl = (kl.gammaLiquidity && kl.gammaLiquidity.length ? kl.gammaLiquidity : d.gamma?.levels || []).slice(0, 8);
    if (gl.length) h += `<div class="gd-card gc">
      <div class="gd-sec-h">Gamma & liquidity zones</div>
      <p class="gd-disclaimer">${_escHtml(d.gamma?.disclaimer || "Proxy levels — not dealer GEX.")}</p>
      <div class="gd-levels">${gl.map(L =>
        `<span class="gd-chip" title="${_escHtml(L.label || "")}">$${_gdPx(L.level)} · ${_escHtml(L.label || L.kind || "")}</span>`
      ).join("")}</div>
    </div>`;'''),
    ('gold desk cards + no dev roadmap',
     r'''  } else {
    // Dashboard tab
    h += `<div class="gd-grid">
      <div class="gd-card gc">
        <div class="gd-sec-h">Market structure</div>
        <div class="gd-body">${_escHtml(d.structure?.summary || "")}</div>
        <div class="gd-badge-row" style="margin-top:10px">${bd(d.structure?.bias || "range", "var(--gd)")}${bd(d.volatility?.condition || "vol", "var(--bl)")}</div>
      </div>
      <div class="gd-card gc">
        <div class="gd-sec-h">Session highs & lows</div>
        <div class="gd-kv"><span>Session high</span><b>$${_gdPx(d.sessions?.sessionHigh)}</b></div>
        <div class="gd-kv"><span>Session low</span><b>$${_gdPx(d.sessions?.sessionLow)}</b></div>
        <div class="gd-kv"><span>Prior day high</span><b>$${_gdPx(d.sessions?.priorDayHigh)}</b></div>
        <div class="gd-kv"><span>Prior day low</span><b>$${_gdPx(d.sessions?.priorDayLow)}</b></div>
        <div class="gd-muted" style="margin-top:8px">Source: ${_escHtml(d.sessions?.source || "—")}</div>
      </div>
    </div>`;

    h += `<div class="gd-grid">
      <div class="gd-card gc">
        <div class="gd-sec-h">Support</div>
        ${(d.levels?.support || []).map(s => `<div class="gd-kv"><span>S · ${s.hits || 0} touches</span><b>$${_gdPx(s.level)}</b></div>`).join("") || '<div class="gd-muted">—</div>'}
      </div>
      <div class="gd-card gc">
        <div class="gd-sec-h">Resistance</div>
        ${(d.levels?.resistance || []).map(s => `<div class="gd-kv"><span>R · ${s.hits || 0} touches</span><b>$${_gdPx(s.level)}</b></div>`).join("") || '<div class="gd-muted">—</div>'}
      </div>
    </div>`;

    h += `<div class="gd-card gc">
      <div class="gd-sec-h">Volume profile</div>
      <div class="gd-kv"><span>POC</span><b>$${_gdPx(d.volumeProfile?.poc)}</b></div>
      <div class="gd-kv"><span>Value area</span><b>$${_gdPx(d.volumeProfile?.val)} – $${_gdPx(d.volumeProfile?.vah)}</b></div>
      <div class="gd-muted" style="margin:8px 0">${_escHtml(d.volumeProfile?.note || "")}</div>
      ${_gdVpBars(d.volumeProfile?.bins)}
    </div>`;

    h += `<div class="gd-card gc">
      <div class="gd-sec-h">Volatility</div>
      <div class="gd-kv"><span>ATR(14)</span><b>$${_gdPx(d.volatility?.atr14)}</b></div>
      <div class="gd-kv"><span>Realized vol 20d</span><b>${d.volatility?.realizedVol20dPct != null ? d.volatility.realizedVol20dPct + "%" : "—"}</b></div>
      <div class="gd-kv"><span>Condition</span><b>${_escHtml(d.volatility?.condition || "—")}</b></div>
    </div>`;

    h += `<div class="gd-card gc">
      <div class="gd-sec-h">Dollar & yields</div>
      <div class="gd-kv"><span>DXY</span><b>${d.macro?.dxy?.px != null ? d.macro.dxy.px : "—"} <span class="${(d.macro?.dxy?.chg||0)>=0?"px-up":"px-dn"}">${d.macro?.dxy?.chg != null ? _gdChg(d.macro.dxy.chg) : ""}</span></b></div>
      <div class="gd-kv"><span>US 10Y</span><b>${d.macro?.tnx?.px != null ? d.macro.tnx.px + "%" : "—"}</b></div>
      <div class="gd-kv"><span>VIX</span><b>${d.macro?.vix?.px != null ? d.macro.vix.px : "—"}</b></div>
    </div>`;

    h += `<div class="gd-card gc">
      <div class="gd-sec-h">Gamma / liquidity proxies</div>
      <p class="gd-disclaimer">${_escHtml(d.gamma?.disclaimer || "")}</p>
      <div class="gd-levels">${(d.gamma?.levels || []).map(L =>
        `<span class="gd-chip">$${_gdPx(L.level)} · ${_escHtml(L.label || "")}</span>`
      ).join("")}</div>
    </div>`;

    h += `<div class="gd-card gc"><div class="gd-sec-h">Upcoming macro events</div>`;
    (d.events || []).forEach(e => {
      h += `<div class="gd-event">
        <div class="gd-event-d">${_escHtml(e.date)} · ${bd(e.impact || "medium", e.impact === "high" ? "var(--rd)" : "var(--gd)")} ${bd(e.cat || "Macro", "var(--bl)")}</div>
        <div class="gd-event-t">${_escHtml(e.event)}</div>
        <div class="gd-sm">${_escHtml(e.goldNote || "")}</div>
      </div>`;
    });
    if (!(d.events || []).length) h += `<div class="gd-muted">No model events in window</div>`;
    h += `</div>`;
  }

  h += `<div class="gd-roadmap gc">
    <div class="gd-sec-h">Build sequence</div>
    <div class="gd-roadmap-row"><span class="gd-done">✓</span> Gold dashboard (delayed data)</div>
    <div class="gd-roadmap-row"><span class="gd-done">✓</span> Weekly playbook engine</div>
    <div class="gd-roadmap-row"><span class="gd-todo">○</span> BYOK AI (OpenAI / Anthropic / Grok / Perplexity)</div>
    <div class="gd-roadmap-row"><span class="gd-todo">○</span> Alerts + personal trading journal</div>
  </div>`;

  return h;
}''',
     r'''  } else {
    // Dashboard tab — rt14: structure, sessions, levels and volatility are computed from COMEX GC=F daily bars.
    // A card with nothing real to show is left out instead of printing "$—", "$0" or "0 touches".
    const f1 = v => `$${_gdPx(Math.round(v * 10) / 10)}`;
    const dayLbl = t => { try { return new Date(t).toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short", timeZone: "America/New_York" }); } catch (_) { return ""; } };
    const futNote = gs ? `COMEX gold futures (GC=F) · Yahoo Finance daily bars, delayed · last ${f1(gs.px)}${livePxN != null ? ` · spot is about $${Math.abs(Math.round(gs.px - livePxN))} ${gs.px >= livePxN ? "below" : "above"} futures` : ""}` : "";
    const aiTxt = !aiBlind ? (d.structure?.summary || "") : "";
    const structTxt = gs ? _gdStructText(gs) : aiTxt;
    let grid1 = "";
    if (structTxt) {
      grid1 += `<div class="gd-card gc">
        <div class="gd-sec-h">Market structure</div>
        <div class="gd-body">${_escHtml(structTxt)}</div>
        <div class="gd-badge-row" style="margin-top:10px">${gs ? bd(gs.trend, "var(--gd)") + (gs.cond ? bd(`vol ${gs.cond}`, "var(--bl)") : "") : bd(d.structure?.bias || "range", "var(--gd)")}</div>
        ${gs ? `<div class="gd-note">Computed from COMEX futures daily bars (20/50-day averages, ATR 14).</div>` : `<div class="gd-note">AI scenario analysis</div>`}
      </div>`;
    }
    if (gs) {
      grid1 += `<div class="gd-card gc">
        <div class="gd-sec-h">Session highs & lows</div>
        <div class="gd-kv"><span>Session high · ${dayLbl(gs.sessDate)}</span><b>${f1(gs.sessHigh)}</b></div>
        <div class="gd-kv"><span>Session low</span><b>${f1(gs.sessLow)}</b></div>
        <div class="gd-kv"><span>Prior day high · ${dayLbl(gs.prevDate)}</span><b>${f1(gs.prevHigh)}</b></div>
        <div class="gd-kv"><span>Prior day low</span><b>${f1(gs.prevLow)}</b></div>
        <div class="gd-note">${_escHtml(futNote)}</div>
      </div>`;
    } else if (_gdHistLoad) {
      grid1 += `<div class="gd-card gc"><div class="gd-sec-h">Session highs & lows</div><div class="gd-muted">Loading COMEX futures bars…</div></div>`;
    } else if (_gdHistErrAt) {
      grid1 += `<div class="gd-card gc"><div class="gd-sec-h">Levels &amp; volatility</div><div class="gd-muted">Futures data did not load just now. Tap Refresh to try again.</div></div>`;
    }
    if (grid1) h += `<div class="gd-grid">${grid1}</div>`;

    if (gs && (gs.sup.length || gs.res.length)) {
      const lvRows = (arr, tag) => arr.map((s, i) => `<div class="gd-kv"><span>${tag}${i + 1} · ${s.hits} touch${s.hits === 1 ? "" : "es"}</span><b>${f1(s.level)}</b></div>`).join("");
      h += `<div class="gd-grid">
      <div class="gd-card gc">
        <div class="gd-sec-h">Support</div>
        ${lvRows(gs.sup, "S") || '<div class="gd-muted">No swing low below price in the last 90 sessions.</div>'}
      </div>
      <div class="gd-card gc">
        <div class="gd-sec-h">Resistance</div>
        ${lvRows(gs.res, "R") || '<div class="gd-muted">No swing high above price in the last 90 sessions.</div>'}
      </div>
    </div>
    <div class="gd-note" style="margin:-4px 2px 12px">Support/resistance: swing lows/highs on COMEX futures daily bars (last 90 sessions), in futures prices. Touches = sessions that came within 0.3%.</div>`;
    }

    if (d.volumeProfile?.bins?.length) {
      h += `<div class="gd-card gc">
      <div class="gd-sec-h">Volume profile</div>
      <div class="gd-kv"><span>POC</span><b>$${_gdPx(d.volumeProfile?.poc)}</b></div>
      <div class="gd-kv"><span>Value area</span><b>$${_gdPx(d.volumeProfile?.val)} – $${_gdPx(d.volumeProfile?.vah)}</b></div>
      ${_gdVpBars(d.volumeProfile?.bins)}
    </div>`;
    }

    if (gs && gs.atr) {
      h += `<div class="gd-card gc">
      <div class="gd-sec-h">Volatility</div>
      <div class="gd-kv"><span>ATR(14) · daily</span><b>${f1(gs.atr)} (${gs.atrPct.toFixed(1)}%)</b></div>
      <div class="gd-kv"><span>Realised vol · 20 days</span><b>${gs.rv != null ? gs.rv.toFixed(1) + "%" : "—"}</b></div>
      <div class="gd-kv"><span>Condition</span><b>${_escHtml(gs.cond || "—")}</b></div>
      <div class="gd-note">COMEX gold futures daily bars. Condition: ATR under 0.9% of price = low, 0.9–1.8% = normal, above 1.8% = elevated.</div>
    </div>`;
    } else if (aiAtr) {
      h += `<div class="gd-card gc">
      <div class="gd-sec-h">Volatility</div>
      <div class="gd-kv"><span>ATR(14)</span><b>$${_gdPx(aiAtr)}</b></div>
      <div class="gd-kv"><span>Condition</span><b>${_escHtml(d.volatility?.condition || "—")}</b></div>
      <div class="gd-note">AI scenario analysis</div>
    </div>`;
    }

    const dxyLc = typeof liveChg === "function" ? liveChg("DXY") : null;
    const dxyChg = dxyLc != null && dxyLc !== 0 ? dxyLc : (Number.isFinite(d.macro?.dxy?.chg) && d.macro.dxy.chg !== 0 ? d.macro.dxy.chg : null);
    h += `<div class="gd-card gc">
      <div class="gd-sec-h">Dollar & yields</div>
      <div class="gd-kv"><span>DXY</span><b>${dxyTxt}${dxyChg != null ? ` <span class="${dxyChg >= 0 ? "px-up" : "px-dn"}">${_gdChg(dxyChg)}</span>` : ""}</b></div>
      <div class="gd-kv"><span>US 10Y</span><b>${d.macro?.tnx?.px != null ? d.macro.tnx.px + "%" : "—"}</b></div>
      <div class="gd-kv"><span>VIX</span><b>${d.macro?.vix?.px != null ? d.macro.vix.px : "—"}</b></div>
    </div>`;

    if ((d.gamma?.levels || []).length) {
      h += `<div class="gd-card gc">
      <div class="gd-sec-h">Gamma / liquidity proxies</div>
      <p class="gd-disclaimer">${_escHtml(d.gamma?.disclaimer || "")}</p>
      <div class="gd-levels">${d.gamma.levels.map(L =>
        `<span class="gd-chip">$${_gdPx(L.level)} · ${_escHtml(L.label || "")}</span>`
      ).join("")}</div>
    </div>`;
    }

    if ((d.events || []).length) {
      h += `<div class="gd-card gc"><div class="gd-sec-h">Upcoming macro events</div>`;
      d.events.forEach(e => {
        h += `<div class="gd-event">
        <div class="gd-event-d">${_escHtml(e.date)} · ${bd(e.impact || "medium", e.impact === "high" ? "var(--rd)" : "var(--gd)")} ${bd(e.cat || "Macro", "var(--bl)")}</div>
        <div class="gd-event-t">${_escHtml(e.event)}</div>
        <div class="gd-sm">${_escHtml(e.goldNote || "")}</div>
      </div>`;
      });
      h += `<div class="gd-note">AI scenario analysis</div></div>`;
    }
  }

  return h;
}'''),
    ('home: pick-up chips (hidden on phone, even grid on desktop)',
     r'''    h += `<section class="home-sec">
      <div class="home-sec-h">Pick up where you left off</div>
      <div class="home-chips">''',
     r'''    h += `<section class="home-sec home-pickup">
      <div class="home-sec-h">Pick up where you left off</div>
      <div class="home-chips" style="--n:${recent.length}">'''),
    ('home: start-here chips (same treatment)',
     r'''    h += `<section class="home-sec">
      <div class="home-sec-h">Start here</div>
      <div class="home-chips">''',
     r'''    h += `<section class="home-sec home-pickup">
      <div class="home-sec-h">Start here</div>
      <div class="home-chips" style="--n:4">'''),
    ('nav: Dashboard gets its own grid icon',
     r'''  dash: '<path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0h4" stroke="currentColor" stroke-width="2" fill="none"/>',''',
     r'''  // rt14: Dashboard = panel layout (it used to reuse the house outline, so it looked like a second Home).
  dash: '<rect x="3.5" y="3.5" width="7" height="9" rx="1.6" stroke="currentColor" stroke-width="1.9" fill="none"/><rect x="13.5" y="3.5" width="7" height="5" rx="1.6" stroke="currentColor" stroke-width="1.9" fill="none"/><rect x="13.5" y="11.5" width="7" height="9" rx="1.6" stroke="currentColor" stroke-width="1.9" fill="none"/><rect x="3.5" y="15.5" width="7" height="5" rx="1.6" stroke="currentColor" stroke-width="1.9" fill="none"/>','''),
    ('nav: signed-in bottom bar = 4 tabs + More',
     r'''const NAV_PRIMARY = [["home","Home"],["brief","Brief"],["playbook","Playbook"],["gold","Gold"],["dash","Dash"]];''',
     r'''// rt14: four tabs + More. Dashboard lives in More (Desk group) with every other destination.
const NAV_PRIMARY = [["home","Home"],["brief","Brief"],["playbook","Playbook"],["gold","Gold"]];'''),
    ('footer: plain-English disclaimer + Updated line',
     r'''function _siteFooter(){
  const feedAsOf = priceLastFetch ? `${_fmtAsOf(priceLastFetch.getTime())} (${_fmtAge(priceLastFetch.getTime())})` : "no feed yet";
  return `<footer class="site-trust-footer" style="margin-top:28px;padding:16px 0 6px;border-top:1px solid var(--gb);text-align:center">
    <div style="font-family:var(--mn);font-size:9px;color:var(--t3);line-height:1.65;max-width:420px;margin:0 auto">
      <strong style="color:var(--t2)">Research only · Not investment advice</strong><br>
      Quotes: free Yahoo / CoinGecko / proxies — delayed, can gap · Seed prices never shown as market · Regime, Lab impulse, free brief, conviction scores = educational models<br>
      Feed as of ${feedAsOf} · <span style="color:var(--gd)">thedispatch.uk</span>
    </div>
  </footer>`;
}''',
     r'''function _siteFooter(){
  // rt14: plain English; the time is the last successful price refresh.
  const upd = priceLastFetch ? `Updated ${_fmtAsOf(priceLastFetch.getTime())}` : "";
  return `<footer class="site-trust-footer" style="margin-top:28px;padding:16px 0 6px;border-top:1px solid var(--gb);text-align:center">
    <div class="stf-body">
      <strong>Research only · Not investment advice</strong><br>
      Prices from free market feeds; some may be delayed. Scores and signals are educational models.
      ${upd ? `<div class="stf-upd">${upd} · <span style="color:var(--gd)">thedispatch.uk</span></div>` : `<div class="stf-upd"><span style="color:var(--gd)">thedispatch.uk</span></div>`}
    </div>
  </footer>`;
}
(function _uiCss14() {
  try {
    if (document.getElementById("ui14-css")) return;
    const s = document.createElement("style");
    s.id = "ui14-css";
    s.textContent = `.gd-card>.gd-sec-h:first-child,.gd-roadmap>.gd-sec-h:first-child,.gd-ladder-sec>.gd-sec-h:first-child{margin-top:0}
.gd-event{display:block}
.gd-event-t{white-space:normal;color:var(--ink,#EDEDE8);font-size:13px;line-height:1.4;margin:2px 0 3px}
.gd-hero-foot{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-top:8px}
.gd-hero-foot .gd-asof{flex:1 1 320px;min-width:0}
.gd-refresh{flex:0 0 auto;background:none;border:1px solid var(--rule-strong,rgba(237,237,232,.3));border-radius:6px;color:var(--ink-2,#A8ADB6);font:600 12px/1 var(--ui,system-ui);padding:0 12px;min-height:36px;cursor:pointer}
.gd-refresh:hover{border-color:var(--gold,#D9AE52);color:var(--gold,#D9AE52)}
.gd-refresh[disabled]{opacity:.6;cursor:default}
.gd-note{margin-top:8px;font-size:11px;line-height:1.45;color:var(--ink-3,#8A8F98)}
.site-trust-footer .stf-body{font-family:var(--ui,system-ui);font-size:11px;line-height:1.6;color:var(--ink-3,#8A8F98);max-width:440px;margin:0 auto}
.site-trust-footer .stf-body strong{color:var(--ink-2,#A8ADB6);font-weight:600}
.site-trust-footer .stf-upd{font-family:var(--data,monospace);font-size:10.5px;margin-top:2px}
.auth-btn{white-space:nowrap}
.more-nav{position:fixed;inset:0;z-index:200}
.more-nav:not(.on){pointer-events:none}
.more-nav.on .more-nav-scrim{opacity:1}
.more-nav.on .more-nav-panel{opacity:1;transform:none}
.more-nav-x{min-width:44px;min-height:44px}
.more-nav-sub{min-height:44px}
@media (min-width:768px){.home-pickup .home-chips{display:grid;grid-template-columns:repeat(var(--n,4),minmax(0,1fr))}.home-pickup .home-chip{justify-content:center}}
@media (min-width:768px) and (max-width:1439px){#cmdLive{display:none}}
@media (max-width:767px){
.home-pickup{display:none!important}
.pg-hdr-accent{top:0;bottom:auto}
.gd-refresh{min-height:44px}
.gd-hero-foot{flex-wrap:nowrap;align-items:flex-end}
.gd-hero-foot .gd-asof{flex:1 1 auto}
.htec-status-r .htec-act{min-width:44px;min-height:44px;margin:-6px 0;display:inline-flex;align-items:center;justify-content:center}
.wl-glance-mini{min-width:44px}
}`;
    document.head.appendChild(s);
  } catch (e) {}
})();'''),
    ('trust pills: plain English',
     r'''      ${hasTwelveData ? `<span class="trust-pill trust-ok">TWELVE DATA · CROSS-ASSET + INDEX TRACKERS · SHARED 15M CACHE</span>` : ""}
      <span class="trust-pill">YAHOO DELAYED · NOT BLOOMBERG</span>
      <span class="trust-pill">FEED ONLY - NO SEED PRICES</span>
      <span class="trust-pill trust-model">REGIME / LAB = MODEL</span>''',
     r'''      ${hasTwelveData ? `<span class="trust-pill trust-ok">FX, METALS &amp; INDEX TRACKERS: TWELVE DATA, UP TO 15 MIN OLD</span>` : ""}
      <span class="trust-pill">STOCKS: YAHOO FINANCE, MAY BE DELAYED</span>
      <span class="trust-pill trust-model">REGIME &amp; LAB SCORES ARE MODELS</span>'''),
    ('regime chip: plain words on phones',
     r'''  const m = { "Risk-On (Strong)": "RISK+", "Risk-On (Fragile)": "RISK", "Transition": "TRANS", "Risk-Off": "RISK-" };''',
     r'''  const m = { "Risk-On (Strong)": "RISK-ON", "Risk-On (Fragile)": "RISK-ON", "Transition": "MIXED", "Risk-Off": "RISK-OFF" };'''),
    ('regime chips: score as /100, detail in tooltip',
     r'''  const regimeChip=`<span class="htec-chip htec-chip-regime" title="Educational model">${re.label} ${re.score}</span>`;
  const regimeChipMob=`<span class="htec-chip htec-chip-regime" title="${re.label}">${_mobShortRegime(re.label)} ${re.score}</span>`;''',
     r'''  const regimeChip=`<span class="htec-chip htec-chip-regime" title="Market regime model (educational)">${re.label} · ${re.score}/100</span>`;
  const regimeChipMob=`<span class="htec-chip htec-chip-regime" title="Market regime model (educational): ${re.label} · ${re.score}/100">${_mobShortRegime(re.label)}</span>`;'''),
    ('home greeting: singular/plural',
     r'''      ? `${liveN} symbols live · VIX ${re.vix}''',
     r'''      ? `${liveN} symbol${liveN === 1 ? "" : "s"} live · VIX ${re.vix}'''),
    ('More sheet: Gold described correctly + Playbook listed',
     r'''      <button class="more-nav-item ${pg==='gold'?'on':''}" onclick="_moreNavGo('gold')">
        ${_navIco('gold')}<span>Gold</span><em>Weekly gold playbook</em>
      </button>''',
     r'''      ${publicOnly ? "" : `<button class="more-nav-item ${pg==='playbook'?'on':''}" onclick="_moreNavGo('playbook')">
        ${_navIco('playbook')}<span>Playbook</span><em>Weekly gold playbook</em>
      </button>`}
      <button class="more-nav-item ${pg==='gold'?'on':''}" onclick="_moreNavGo('gold')">
        ${_navIco('gold')}<span>Gold</span><em>Live gold dashboard</em>
      </button>'''),
    ('playbook ladder: not drawn from zero-input AI levels',
     r'''    const ladder = _renderLadder(d);''',
     r'''    // rt14: when the AI saw no price change (spot reference only), its levels are guesses around spot - not drawn.
    const ladder = aiBlind ? "" : _renderLadder(d);'''),
]
INDEX_EDITS = [
    ("cache-bust app.js chat13 -> chat14",
     '/app.js?v=chat13"',
     '/app.js?v=chat14"'),
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
    if MARKER in app or 'app.js?v=chat14"' in idx:
        sys.exit("ABORT: rt14 already applied (marker / chat14 found) — refusing to run twice; nothing written")
    if PREV_MARKER not in app or 'app.js?v=chat13"' not in idx:
        sys.exit("ABORT: these are not the chat13 (rt13) files — nothing written")
    errors = []
    new_app = apply(app, APP_EDITS, "app.js", errors)
    new_idx = apply(idx, INDEX_EDITS, "index.html", errors)
    if not errors:
        if (new_app.count(MARKER) != 1 or PREV_MARKER in new_app or "function _rtTickFresh(" not in new_app
                or new_app.count("function _gdStats(") != 1 or new_app.count('s.id = "ui14-css"') != 1
                or " dynamic`" in new_app or "Build sequence" in new_app or "xAI" in new_app.split("function _renderGoldSurface", 1)[1][:20000]
                or new_idx.count('app.js?v=chat14"') != 1):
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
            tmp = p + ".rt14.tmp"
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
    print("Written: app.js, index.html (app.js?v=chat14)")


if __name__ == "__main__":
    main()
