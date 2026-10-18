#!/usr/bin/env python3
"""patch_rt48bs.py: server.js. Replaces the rt48s /api/academy-daily block with rt48bs:
- explainers only for headlines mapped to gold, oil, USD, US yields, S&P 500, Nasdaq, BTC, ETH, EUR/USD or GBP; the question is the
  asset's typical first move with answers Up / Down / Little change; stablecoin headlines banned; entities decoded;
- a validator rejects wrong directions for known patterns (e.g. oil supply disruption -> down), invented numbers, advice wording,
  circular items and unknown assets; if no AI item passes, deterministic templates are used;
- cached items that fail the validator are discarded on load (new cache file); admins can force a rebuild with ?refresh=1 (max 4/day).
Keeps the existing route line. Works with or without rt50console. ACADEMY_AI=off still disables AI calls.
Usage: python3 patch_rt48bs.py [--check] server.js"""
import sys, subprocess, tempfile, os
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
P = args[0] if args else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
def die(m): print('ABORT:', m); sys.exit(1)
if '// ── rt48bs' in s: die('rt48bs already applied')
START = '// ── rt48s: /api/academy-daily ──'
LAST = '  try { return send(); } catch (e) { try { res.end(); } catch (x) {} } }\n'
ROUTE = '  if (p === "/api/academy-daily") return academyDaily(req, res);'
if s.count(START) != 1 or s.count(ROUTE) != 1 or 'async function academyDaily(' not in s:
    print('SKIPPED: rt48s block/route not found exactly once (start %d, route %d); nothing changed' % (s.count(START), s.count(ROUTE))); sys.exit(0)
i = s.index(START); j = s.find(LAST, i)
if j < 0 or s.find('async function academyDaily(', i) > j: print('SKIPPED: end of rt48s block not found; nothing changed'); sys.exit(0)
j += len(LAST)
OLD = r'''// ── rt48s: /api/academy-daily ── auto-generated Academy explainers from the site's own RSS headlines.
// No database: memory + one small JSON file in the OS temp dir, keyed by London date. At most one AI call per build,
// at most 2 builds a day, 2h apart. Never surfaces errors: always 200 with items (possibly empty). Set ACADEMY_AI=off to disable AI.
const _rt48sState = { day: "", generatedAt: "", items: [], kind: "template", tries: 0, last: 0, busy: null };
const _rt48sFile = require("path").join(require("os").tmpdir(), "dispatch-academy-daily.json");
function _rt48sDay() { try { return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/London" }).format(new Date()); } catch (e) { return new Date().toISOString().slice(0, 10); } }
function _rt48sLoad() { try { const o = JSON.parse(require("fs").readFileSync(_rt48sFile, "utf8")); if (o && o.day === _rt48sDay() && Array.isArray(o.items)) Object.assign(_rt48sState, { day: o.day, generatedAt: o.generatedAt || "", items: o.items, kind: o.kind || "template", tries: o.tries || 0, last: o.last || 0 }); } catch (e) {} }
function _rt48sSave() { try { const { day, generatedAt, items, kind, tries, last } = _rt48sState; require("fs").writeFileSync(_rt48sFile, JSON.stringify({ day, generatedAt, items, kind, tries, last })); } catch (e) {} }
function _rt48sTxt(s) { return String(s || "").replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1").replace(/<[^>]*>/g, " ").replace(/&amp;/g, "&").replace(/&quot;/g, '"').replace(/&#0?39;|&apos;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&#(\d+);/g, (m, n) => String.fromCharCode(Number(n))).replace(/\s+/g, " ").trim(); }
function _rt48sParse(xml, src) { const out = [], re = /<item[\s>][\s\S]*?<\/item>/gi; let m; while ((m = re.exec(xml)) && out.length < 25) { const it = m[0], g = t => { const r = new RegExp("<" + t + "[^>]*>([\\s\\S]*?)</" + t + ">", "i").exec(it); return r ? _rt48sTxt(r[1]) : ""; };
  const h = g("title"), link = g("link"), t = Date.parse(g("pubDate") || g("dc:date") || ""); if (h.length < 20 || h.length > 240) continue; out.push({ h, link: /^https:\/\/[^\s"'<>]{5,300}$/.test(link) ? link : "", src, t: isFinite(t) ? t : 0 }); } return out; }
async function _rt48sHeads() { const feeds = [["f0", "BBC Business"], ["f1", "CNBC"], ["f4", "MarketWatch"], ["f12", "CoinDesk"]], all = [];
  await Promise.all(feeds.map(async ([id, src]) => { try { const u = typeof approvedRssFeedUrl === "function" ? approvedRssFeedUrl(id) : null; if (!u) return;
    const r = await fetch(u, { headers: { "User-Agent": "DispatchMarkets/1.0" }, signal: AbortSignal.timeout(8000) }); if (!r.ok) return; all.push(..._rt48sParse((await r.text()).slice(0, 600000), src)); } catch (e) {} }));
  const now = Date.now(), seen = new Set(); return all.filter(x => (!x.t || now - x.t < 72 * 36e5) && !seen.has(x.h.toLowerCase()) && seen.add(x.h.toLowerCase())).sort((a, b) => b.t - a.t).slice(0, 18); }
function _rt48sOk(it, heads) { if (!it || typeof it !== "object") return null; const i = Number(it.i); if (!Number.isInteger(i) || i < 0 || i >= heads.length) return null; const H = heads[i];
  const S = (v, n, m) => typeof v === "string" && v.trim().length >= (m || 3) && v.length <= n && !/[<>]|https?:|www\./i.test(v) ? v.trim() : null;
  const q = S(it.q, 220), e = S(it.e, 420), o = Array.isArray(it.o) && it.o.length === 3 ? it.o.map(x => S(x, 90, 2)) : null, a = Number(it.a);
  if (!q || !e || !o || o.some(x => !x) || new Set(o).size !== 3 || !Number.isInteger(a) || a < 0 || a > 2) return null;
  // no invented figures: every number used must appear in the headline itself
  const nums = s => (s.match(/\d+(?:[.,]\d+)?/g) || []); const hn = new Set(nums(H.h)); if ([q, e, ...o].some(s => nums(s).some(n => !hn.has(n)))) return null;
  return { h: H.h, src: H.src, link: H.link, q, o, a, e }; }
async function _rt48sBuild() { const day = _rt48sDay(); _rt48sState.tries++; _rt48sState.last = Date.now(); _rt48sSave();
  try { const heads = await _rt48sHeads(); if (heads.length < 3) return;
    if (String(process.env.ACADEMY_AI || "").toLowerCase() === "off" || typeof generateAi !== "function") return;
    const list = heads.map((x, k) => `${k}. ${x.h}`).join("\n");
    const r = await generateAi({ maxTokens: 900, temperature: 0.2,
      system: "You write short educational multiple-choice questions for a free beginner markets course. Use ONLY the numbered headlines provided. Never invent facts, figures, prices or quotes that are not in the headline. Each question asks about the typical first market reaction or the concept behind a headline (for example why oil supply news can lift oil prices), framed as a typical first reaction, never as a prediction or advice. Plain British English. Reply with JSON only, no prose.",
      messages: [{ role: "user", content: `Headlines:\n${list}\n\nPick the 3 headlines with the clearest market lesson. Return exactly: {"items":[{"i":<headline number>,"q":"<question, max 200 chars>","o":["<option>","<option>","<option>"],"a":<index 0-2 of the correct option>,"e":"<explanation, max 380 chars, says this is a typical first reaction, not a rule>"}]}` }] });
    let j = null; try { const t = String(r && r.text || ""), s0 = t.indexOf("{"), s1 = t.lastIndexOf("}"); j = s0 >= 0 && s1 > s0 ? JSON.parse(t.slice(s0, s1 + 1)) : null; } catch (e) { j = null; }
    const used = new Set(), items = (j && Array.isArray(j.items) ? j.items : []).map(x => _rt48sOk(x, heads)).filter(x => x && !used.has(x.h) && used.add(x.h)).slice(0, 3);
    if (items.length && _rt48sDay() === day) { Object.assign(_rt48sState, { day, generatedAt: new Date().toISOString(), items, kind: "ai" }); _rt48sSave(); }
  } catch (e) { try { console.warn("academy-daily: build skipped", (e && (e.code || e.message)) || e); } catch (x) {} } }
async function academyDaily(req, res) {
  const send = () => { const s = _rt48sState, body = JSON.stringify({ date: _rt48sDay(), generatedAt: s.day === _rt48sDay() ? s.generatedAt : "", kind: s.day === _rt48sDay() && s.items.length ? s.kind : "template", items: s.day === _rt48sDay() ? s.items : [] });
    res.writeHead(200, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "public, max-age=900", "X-Content-Type-Options": "nosniff" }); res.end(body); };
  try { const day = _rt48sDay(); if (_rt48sState.day !== day) { _rt48sLoad(); if (_rt48sState.day !== day) Object.assign(_rt48sState, { day, generatedAt: "", items: [], kind: "template", tries: 0, last: 0 }); }
    if (!_rt48sState.items.length && !_rt48sState.busy && _rt48sState.tries < 2 && Date.now() - _rt48sState.last > 2 * 36e5) _rt48sState.busy = _rt48sBuild().finally(() => { _rt48sState.busy = null; });
    if (_rt48sState.busy) await Promise.race([_rt48sState.busy, new Promise(r => setTimeout(r, 6000))]);
  } catch (e) {}
  try { return send(); } catch (e) { try { res.end(); } catch (x) {} } }
'''
NEW = r'''// ── rt48bs: /api/academy-daily ── auto-generated Academy explainers from the site's own RSS headlines (replaces rt48s).
// Only headlines about an asset the site covers (gold, oil, US dollar, US yields, S&P 500, Nasdaq, Bitcoin, Ether, EUR/USD, pound).
// The AI only picks a headline, one allowed asset and a direction (up / down / little change) and writes a short explanation;
// the server writes the question and the fixed answers itself. Every item (fresh or cached) must pass _rt48bValid: allowed asset
// named in the headline, no stablecoin topics, no invented numbers, wording consistent with the direction, and known-wrong
// reactions rejected. With no valid AI item, deterministic templates are used. Cache: memory + os.tmpdir() file per London day;
// at most 2 automatic builds a day, 2h apart; admins can force a rebuild with ?refresh=1 (max 4 a day). Always 200 JSON.
// ACADEMY_AI=off disables the AI call (templates only). No database, no Stripe.
const RT48B_ASSETS = {
  gold: ["the gold price", /\b(gold|bullion)\b/i], oil: ["oil prices", /\b(oil|crude|brent|wti|opec\+?)\b/i],
  usd: ["the US dollar", /\b(us dollar|u\.s\. dollar|dollar|greenback|dxy)\b/i], yields: ["US Treasury yields", /\b(treasur(y|ies)|bond yields?|yields?)\b/i],
  spx: ["the S&P 500", /(s&p( 500)?|wall street|us stocks|u\.s\. stocks|dow jones|\bthe dow\b)/i], nasdaq: ["the Nasdaq", /\bnasdaq\b/i],
  btc: ["Bitcoin", /\b(bitcoin|btc)\b/i], eth: ["Ether", /\b(ether|ethereum)\b/i],
  eurusd: ["EUR/USD", /\b(euro|eur\/usd|ecb|lagarde)\b/i], gbp: ["the British pound", /\b(pound|sterling|gbp|bank of england|boe)\b/i] };
const RT48B_OPTS = ["Up", "Down", "Little change"], RT48B_DIRS = ["up", "down", "flat"];
const RT48B_BAN = /stablecoin|tether|\busdc\b|\busdt\b|\b(australian|canadian|new zealand|hong kong|singapore|taiwan|zimbabwe) dollar\b/i;
// headline pattern + asset → the usual first direction (also the deterministic template set)
const RT48B_RULES = [
  [/\b(fed|federal reserve|fomc|powell)\b.*\b(cuts?|cutting|lowers?)\b.*\brates?\b|\brate cuts?\b.*\b(fed|federal reserve)\b/i, { usd: ["down", "A surprise Fed rate cut usually weakens the US dollar first, because lower US rates make holding dollars less rewarding."], yields: ["down", "Treasury yields typically fall first when the Fed cuts by more than expected, led by shorter maturities."], gold: ["up", "Gold often rises on a surprise Fed cut: lower rates reduce the cost of holding a metal that pays no interest, and the dollar tends to weaken."] }],
  [/\b(fed|federal reserve|fomc|powell)\b.*\b(raises?|hikes?|hiking|lifts?)\b.*\brates?\b/i, { usd: ["up", "A surprise Fed hike usually lifts the US dollar first, because higher US rates attract money into dollars."], yields: ["up", "Treasury yields typically rise first on a surprise hike, especially shorter maturities."], gold: ["down", "Gold often falls on a surprise hike: higher rates raise the cost of holding a metal that pays no interest."] }],
  [/\b(us|u\.s\.|american)\b.*\b(inflation|cpi|consumer prices)\b.*\b(hot|hotter|accelerat\w*|jump\w*|surg\w*|higher than expected|tops?)\b/i, { yields: ["up", "Hotter US inflation usually pushes Treasury yields higher first, as traders expect rates to stay high for longer."], usd: ["up", "A hot US inflation print often lifts the dollar first on expectations of tighter Fed policy."] }],
  [/\b(us|u\.s\.|american)\b.*\b(inflation|cpi|consumer prices)\b.*\b(cool\w*|slow\w*|eas(es|ed|ing)|lower than expected|soft\w*)\b/i, { yields: ["down", "Cooler US inflation usually pulls Treasury yields lower first, as traders price in earlier or bigger rate cuts."], usd: ["down", "Softer US inflation often weakens the dollar first, because rate-cut expectations rise."] }],
  [/\b(oil|crude|refiner(y|ies)|pipeline|tankers?|energy (sites|facilities|infrastructure)|oil terminals?|strait)\b.*\b(attack\w*|strikes?|struck|hit|outage|disrupt\w*|shut\w*|blockade|halt\w*)\b|\b(attack\w*|strikes?|struck|hits?|outage|disrupt\w*|shut\w*|halt\w*)\b.*\b(oil|crude|refiner(y|ies)|pipeline|tankers?|energy (sites|facilities|infrastructure)|oil terminals?)\b/i, { oil: ["up", "A disruption to oil supply usually lifts oil prices first, as traders price in less supply. The move often fades if output recovers quickly."] }],
  [/\bopec\+?\b.*\b(cut\w*|reduc\w*)\b.*\b(output|production|supply)\b/i, { oil: ["up", "A surprise OPEC+ output cut usually lifts oil prices first, because fewer barrels are expected to reach the market."] }],
  [/\b(oil|crude)\b.*\b(glut|surplus|oversuppl\w*)\b|\bopec\+?\b.*\b(raise|boost|increase|hike)\w*\b.*\b(output|production)\b/i, { oil: ["down", "Signs of too much oil supply usually push prices lower first, as more barrels compete for buyers."] }],
  [/\b(bitcoin|ether|ethereum|crypto)\b.*\betfs?\b.*\b(inflows?|record)\b/i, { btc: ["up", "Strong inflows into crypto funds usually support Bitcoin first, because funds must buy the coin to back new shares."], eth: ["up", "Strong inflows into Ether funds usually support the price first, because funds must buy Ether to back new shares."] }],
  [/\b(bitcoin|ether|ethereum|crypto)\b.*\betfs?\b.*\boutflows?\b/i, { btc: ["down", "Outflows from crypto funds usually weigh on Bitcoin first, because funds sell coins as investors redeem shares."], eth: ["down", "Outflows from Ether funds usually weigh on the price first, as funds sell to meet redemptions."] }],
  [/\b(war|missiles?|airstrikes?|invasion|invad\w*|military strikes?|escalat\w*)\b/i, { gold: ["up", "Escalating conflict often lifts gold first, as investors look for a traditional safe haven. Such moves can fade if tensions ease."] }],
  [/\b(ecb|lagarde)\b.*\b(cuts?|lowers?)\b.*\brates?\b/i, { eurusd: ["down", "A surprise ECB cut usually weakens the euro first, so EUR/USD tends to fall."] }],
  [/\b(ecb|lagarde)\b.*\b(raises?|hikes?)\b.*\brates?\b/i, { eurusd: ["up", "A surprise ECB hike usually strengthens the euro first, so EUR/USD tends to rise."] }],
  [/\b(bank of england|boe|bailey)\b.*\b(cuts?|lowers?)\b.*\brates?\b/i, { gbp: ["down", "A surprise Bank of England cut usually weakens the pound first, because lower UK rates make sterling less rewarding to hold."] }],
  [/\b(bank of england|boe|bailey)\b.*\b(raises?|hikes?)\b.*\brates?\b/i, { gbp: ["up", "A surprise Bank of England hike usually lifts the pound first, as higher UK rates attract money into sterling."] }] ];
const RT48B_DIRW = { up: /\b(rise|rises|rising|rose|higher|lift\w*|gain\w*|climb\w*|rall\w*|strengthen\w*|up|support\w*|jump\w*)\b/i, down: /\b(fall|falls|falling|fell|lower|drop\w*|declin\w*|weaken\w*|slip\w*|down|weigh\w*|sell\w*)\b/i, flat: /\b(little|limited|muted|unchanged|flat|small|modest)\b/i };
const _rt48sState = { day: "", generatedAt: "", items: [], kind: "template", tries: 0, last: 0, forced: 0, busy: null };
const _rt48sFile = require("path").join(require("os").tmpdir(), "dispatch-academy-daily-v2.json");
function _rt48sDay() { try { return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/London" }).format(new Date()); } catch (e) { return new Date().toISOString().slice(0, 10); } }
function _rt48bQ(asset) { return `If this news is a surprise to markets, what is the typical first reaction in ${RT48B_ASSETS[asset][0]}?`; }
function _rt48bRule(h, asset) { for (const [re, m] of RT48B_RULES) if (re.test(h) && m[asset]) return m[asset]; return null; }
function _rt48bValid(x) { try { if (!x || typeof x !== "object") return false; const A = RT48B_ASSETS[x.asset], h = String(x.h || ""), e = String(x.e || "");
  if (!A || !(A[1].test(h) || _rt48bRule(h, x.asset)) || RT48B_BAN.test(h) || RT48B_BAN.test(e) || h.length < 20 || h.length > 240 || /[<>]|&#?\w+;/.test(h)) return false;
  const k = RT48B_DIRS.indexOf(x.dir); if (k < 0 || x.a !== k || !Array.isArray(x.o) || x.o.join("|") !== RT48B_OPTS.join("|") || x.q !== _rt48bQ(x.asset)) return false;
  if (e.length < 40 || e.length > 380 || /[<>]|https?:|www\./i.test(e) || /\b(you should|buy now|sell now|guarantee\w*|definitely|certain to)\b/i.test(e)) return false;
  if (!/\b(typical\w*|usual\w*|often|tend\w*)\b/i.test(e) || !RT48B_DIRW[x.dir].test(e)) return false;
  const nums = s => (s.match(/\d+(?:[.,]\d+)?/g) || []), hn = new Set(nums(h)); if (nums(e).some(n => !hn.has(n))) return false;
  const r = _rt48bRule(h, x.asset); if (r && r[0] !== x.dir) return false;
  // circular: the headline already reports this asset's own move ("Bitcoin dips to ...", "yields fall for the week")
  if (!r && new RegExp("(" + A[1].source + ")[^.,;:]{0,30}\\b(rise|rises|rose|rising|jump\\w*|surg\\w*|fall|falls|fell|falling|drop\\w*|dip\\w*|slid\\w*|slide\\w*|slump\\w*|snap\\w*|rall\\w*|gain\\w*|climb\\w*|soar\\w*|sink\\w*|tumbl\\w*|plung\\w*|halt\\w*|steady|flat|record)\\b", "i").test(h)) return false;
  if (x.link && !/^https:\/\/[^\s"'<>]{5,300}$/.test(x.link)) return false; return true; } catch (e) { return false; } }
function _rt48sLoad() { try { const o = JSON.parse(require("fs").readFileSync(_rt48sFile, "utf8")); if (o && o.day === _rt48sDay() && Array.isArray(o.items)) Object.assign(_rt48sState, { day: o.day, generatedAt: o.generatedAt || "", items: o.items, kind: o.kind || "template", tries: o.tries || 0, last: o.last || 0, forced: o.forced || 0 }); } catch (e) {} }
function _rt48sSave() { try { const { day, generatedAt, items, kind, tries, last, forced } = _rt48sState; require("fs").writeFileSync(_rt48sFile, JSON.stringify({ day, generatedAt, items, kind, tries, last, forced })); } catch (e) {} }
function _rt48sTxt(s) { let t = String(s || "").replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1").replace(/<[^>]*>/g, " ");
  const N = { amp: "&", quot: '"', apos: "'", lt: "<", gt: ">", nbsp: " ", rsquo: "\u2019", lsquo: "\u2018", ldquo: "\u201c", rdquo: "\u201d", ndash: "\u2013", mdash: "\u2014", hellip: "\u2026", pound: "\u00a3", euro: "\u20ac", eacute: "\u00e9", middot: "\u00b7" };
  for (let k = 0; k < 3 && /&(#x?[0-9a-f]+|[a-z]+);/i.test(t); k++) t = t.replace(/&#x([0-9a-f]+);/gi, (m, h) => { const c = parseInt(h, 16); return c > 0 && c < 0x110000 ? String.fromCodePoint(c) : ""; })
    .replace(/&#(\d+);/g, (m, d) => { const c = Number(d); return c > 0 && c < 0x110000 ? String.fromCodePoint(c) : ""; }).replace(/&([a-z]+);/gi, (m, n) => N[n.toLowerCase()] != null ? N[n.toLowerCase()] : m);
  return t.replace(/[<>]/g, "").replace(/&[a-z]+;/gi, "").replace(/\s+/g, " ").trim(); }
function _rt48sParse(xml, src) { const out = [], re = /<item[\s>][\s\S]*?<\/item>/gi; let m; while ((m = re.exec(xml)) && out.length < 25) { const it = m[0], g = t => { const r = new RegExp("<" + t + "[^>]*>([\\s\\S]*?)</" + t + ">", "i").exec(it); return r ? _rt48sTxt(r[1]) : ""; };
  const h = g("title"), link = g("link"), t = Date.parse(g("pubDate") || g("dc:date") || ""); if (h.length < 20 || h.length > 240) continue; out.push({ h, link: /^https:\/\/[^\s"'<>]{5,300}$/.test(link) ? link : "", src, t: isFinite(t) ? t : 0 }); } return out; }
function _rt48bAssets(h) { if (RT48B_BAN.test(h)) return []; return Object.keys(RT48B_ASSETS).filter(k => RT48B_ASSETS[k][1].test(h) || _rt48bRule(h, k)); }
async function _rt48sHeads() { const feeds = [["f0", "BBC Business"], ["f1", "CNBC"], ["f4", "MarketWatch"], ["f12", "CoinDesk"], ["f9", "Investing.com"], ["f14", "BBC World"]], all = [];
  await Promise.all(feeds.map(async ([id, src]) => { try { const u = typeof approvedRssFeedUrl === "function" ? approvedRssFeedUrl(id) : null; if (!u) return;
    const r = await fetch(u, { headers: { "User-Agent": "DispatchMarkets/1.0" }, signal: AbortSignal.timeout(8000) }); if (!r.ok) return; all.push(..._rt48sParse((await r.text()).slice(0, 600000), src)); } catch (e) {} }));
  const now = Date.now(), seen = new Set();
  return all.filter(x => !/^live( updates)?:|\blive\b:/i.test(x.h) && (!x.t || now - x.t < 72 * 36e5) && !seen.has(x.h.toLowerCase()) && seen.add(x.h.toLowerCase())).map(x => ({ ...x, as: _rt48bAssets(x.h) })).filter(x => x.as.length).sort((a, b) => b.t - a.t).slice(0, 16); }
function _rt48bItem(H, asset, dir, e, kind) { const a = RT48B_DIRS.indexOf(dir); return { h: H.h, src: H.src, link: H.link, asset, dir, q: _rt48bQ(asset), o: RT48B_OPTS.slice(), a, e: String(e || "").trim(), kind }; }
function _rt48bTemplates(heads, skip) { const out = []; for (const H of heads) { if (out.length >= 3) break; if (skip.has(H.h)) continue;
  for (const as of H.as) { const r = _rt48bRule(H.h, as); if (r) { const it = _rt48bItem(H, as, r[0], r[1], "template"); if (_rt48bValid(it)) { out.push(it); break; } } } } return out; }
async function _rt48sBuild() { const day = _rt48sDay(); _rt48sState.tries++; _rt48sState.last = Date.now(); _rt48sSave();
  try { const heads = await _rt48sHeads(); let items = [];
    if (heads.length && String(process.env.ACADEMY_AI || "").toLowerCase() !== "off" && typeof generateAi === "function") {
      try { const list = heads.map((x, k) => `${k}. ${x.h} [assets: ${x.as.join(", ")}]`).join("\n");
        const r = await generateAi({ maxTokens: 700, temperature: 0.1,
          system: "You help write a free beginner markets course. For each chosen headline, name ONE asset from that headline's allowed list and the usual FIRST market reaction in that asset's price if the news were a surprise: up, down or flat. Asset ids: gold, oil, usd (US dollar), yields (US Treasury yields), spx (S&P 500), nasdaq, btc, eth, eurusd, gbp. Never pick a stablecoin. Only choose headlines where the usual reaction is well established in finance textbooks; skip anything ambiguous. The explanation (max 300 characters, plain British English) must say this is the typical or usual first reaction, must not predict or advise, and must not include any number that is not in the headline. Reply with JSON only.",
          messages: [{ role: "user", content: `Headlines:\n${list}\n\nReturn up to 3 items as {"items":[{"i":<headline number>,"asset":"<asset id from that headline's list>","dir":"up|down|flat","e":"<explanation>"}]}` }] });
        let j = null; try { const t = String(r && r.text || ""), s0 = t.indexOf("{"), s1 = t.lastIndexOf("}"); j = s0 >= 0 && s1 > s0 ? JSON.parse(t.slice(s0, s1 + 1)) : null; } catch (e) { j = null; }
        const used = new Set(); (j && Array.isArray(j.items) ? j.items : []).forEach(x => { const i = Number(x && x.i), H = Number.isInteger(i) ? heads[i] : null; if (!H || used.has(H.h) || !H.as.includes(x.asset)) return;
          const it = _rt48bItem(H, x.asset, String(x.dir || "").toLowerCase(), x.e, "ai"); if (_rt48bValid(it) && items.length < 3) { items.push(it); used.add(H.h); } });
      } catch (e) { try { console.warn("academy-daily: AI skipped", (e && (e.code || e.message)) || e); } catch (x) {} } }
    items = items.concat(_rt48bTemplates(heads, new Set(items.map(x => x.h)))).slice(0, 3);
    if (_rt48sDay() === day && (items.length || !_rt48sState.items.length)) { Object.assign(_rt48sState, { day, generatedAt: new Date().toISOString(), items, kind: items.some(x => x.kind === "ai") ? "ai" : "template" }); _rt48sSave(); }
  } catch (e) { try { console.warn("academy-daily: build skipped", (e && (e.code || e.message)) || e); } catch (x) {} } }
async function academyDaily(req, res) {
  let forced = false;
  const send = () => { const s = _rt48sState, today = s.day === _rt48sDay(), items = today ? s.items.filter(_rt48bValid) : [], body = JSON.stringify({ date: _rt48sDay(), generatedAt: today && items.length ? s.generatedAt : "", kind: items.some(x => x.kind === "ai") ? "ai" : "template", items, v: 2 });
    res.writeHead(200, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": forced ? "no-store" : "private, max-age=300", "X-Content-Type-Options": "nosniff" }); res.end(body); };
  try { const day = _rt48sDay(); if (_rt48sState.day !== day) { _rt48sLoad(); if (_rt48sState.day !== day) Object.assign(_rt48sState, { day, generatedAt: "", items: [], kind: "template", tries: 0, last: 0, forced: 0 }); }
    const n0 = _rt48sState.items.length; _rt48sState.items = _rt48sState.items.filter(_rt48bValid); // drop cached items that fail the current rules
    if (n0 && !_rt48sState.items.length) { _rt48sState.tries = 0; _rt48sState.last = 0; _rt48sSave(); }
    try { const q = new URL(req.url || "/", "http://x").searchParams; if (q.get("refresh") === "1" && typeof currentUser === "function" && typeof isAdminUser === "function") { const u = await currentUser(req); if (u && isAdminUser(u) && (_rt48sState.forced || 0) < 4) forced = true; } } catch (e) {}
    if (forced && !_rt48sState.busy) { _rt48sState.forced = (_rt48sState.forced || 0) + 1; _rt48sState.busy = _rt48sBuild().finally(() => { _rt48sState.busy = null; }); }
    else if (!_rt48sState.items.length && !_rt48sState.busy && _rt48sState.tries < 2 && Date.now() - _rt48sState.last > 2 * 36e5) _rt48sState.busy = _rt48sBuild().finally(() => { _rt48sState.busy = null; });
    if (_rt48sState.busy) await Promise.race([_rt48sState.busy, new Promise(r => setTimeout(r, forced ? 30000 : 6000))]);
  } catch (e) {}
  try { return send(); } catch (e) { try { res.end(); } catch (x) {} } }
'''
cur = s[i:j]
print('old block:', 'matches rt48s exactly' if cur.strip() == OLD.strip() else 'differs from rt48s (%d chars), replacing anyway' % len(cur))
s = s[:i] + NEW.rstrip('\n') + '\n' + s[j:]
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print('OK rt48bs: academy-daily block replaced; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('written', P)
