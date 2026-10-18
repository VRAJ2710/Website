#!/usr/bin/env python3
"""patch_rt48c.py: server.js. Replaces the rt48bs /api/academy-daily block with rt48c (stacks on rt48bs; works with or without rt50console).
Why: on prod every AI explainer was being rejected and only one template matched, so the Academy showed one item.
- validator: wider direction/hedge vocabulary ("spike", "increase", "generally" ...), asset names like "S&P 500"/"10-year" no longer count
  as invented numbers, asset aliases from the model ("GBP", "S&P 500", "Up") are normalised, reasons are recorded;
- headlines get textbook knock-on assets ("dollar slips" -> gold, EUR/USD, pound; "yields fall" -> gold; "Bitcoin dips" -> Ether), and an item
  whose answer the headline already states is rejected for every asset;
- 14 more template rules (safe-haven, sanctions/hurricanes, recession, tariffs, US jobs, hawkish/dovish Fed, knock-ons); templates are spread
  across different assets and top up to 3 items;
- provider reply parsing: raw JSON, markdown fences, prose, bare arrays, truncated replies (complete items salvaged); maxTokens 700 -> 1600;
- auto rebuild (max 3 a day, 2h apart) while fewer than 3 items or no AI item; new cache file (v3) so today's template-only cache is rebuilt;
- admin-only diagnostic in ?refresh=1 (max 6 a day) or ?diag=1 (no rebuild): AI status/model/parse mode, counts received/accepted,
  rejections by reason with up to 8 samples, templates used. No secrets, no new tables, no Stripe. ACADEMY_AI=off still works.
Usage: python3 patch_rt48c.py [--check] server.js"""
import sys, subprocess, tempfile, os
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
P = args[0] if args else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
def die(m): print('ABORT:', m); sys.exit(1)
if '// ── rt48c:' in s: die('rt48c already applied')
START = '// ── rt48bs: /api/academy-daily ──'
LAST = '  try { return send(); } catch (e) { try { res.end(); } catch (x) {} } }\n'
ROUTE = '  if (p === "/api/academy-daily") return academyDaily(req, res);'
if s.count(START) != 1 or s.count(ROUTE) != 1:
    print('SKIPPED: rt48bs block/route not found exactly once (start %d, route %d); nothing changed' % (s.count(START), s.count(ROUTE))); sys.exit(0)
i = s.index(START); j = s.find(LAST, i)
if j < 0 or s.find('async function academyDaily(', i) > j: print('SKIPPED: end of rt48bs block not found; nothing changed'); sys.exit(0)
j += len(LAST)
OLD = r'''// ── rt48bs: /api/academy-daily ── auto-generated Academy explainers from the site's own RSS headlines (replaces rt48s).
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
NEW = r'''// ── rt48c: /api/academy-daily ── (replaces rt48bs) auto-generated Academy explainers from the site's own RSS headlines.
// Only headlines about an asset the site covers (gold, oil, US dollar, US yields, S&P 500, Nasdaq, Bitcoin, Ether, EUR/USD, pound),
// or with a textbook knock-on effect for one (e.g. "dollar slips" -> gold, EUR/USD). The AI picks a headline, one allowed asset and
// a direction (up / down / little change) and writes a short explanation; the server writes the question and the fixed answers.
// Every item (fresh or cached) must pass _rt48bWhy (empty = valid): allowed asset, no stablecoin topics, no invented numbers,
// wording consistent with the direction, known-wrong reactions rejected, no item whose answer the headline already states.
// AI items first, topped up to 3 with deterministic templates (spread across assets). Cache: memory + os.tmpdir() file per
// London day; up to 3 automatic builds a day, 2h apart, while fewer than 3 items or no AI item; admins can force a rebuild with
// ?refresh=1 (max 6 a day) and see a diagnostic (?refresh=1 or ?diag=1: counts and reasons, no secrets). Always 200 JSON.
// ACADEMY_AI=off disables the AI call (templates only). No database, no Stripe.
const RT48B_ASSETS = {
  gold: ["the gold price", /\b(gold|bullion)\b/i], oil: ["oil prices", /\b(oil|crude|brent|wti|opec\+?)\b/i],
  usd: ["the US dollar", /\b(us dollar|u\.s\. dollar|dollar|greenback|dxy)\b/i], yields: ["US Treasury yields", /\b(treasur(y|ies)|bond yields?|yields?)\b/i],
  spx: ["the S&P 500", /(s&p( 500)?|wall street|us stocks|u\.s\. stocks|dow jones|\bthe dow\b)/i], nasdaq: ["the Nasdaq", /\bnasdaq\b/i],
  btc: ["Bitcoin", /\b(bitcoin|btc)\b/i], eth: ["Ether", /\b(ether|ethereum)\b/i],
  eurusd: ["EUR/USD", /\b(euro|eur\/usd|ecb|lagarde)\b/i], gbp: ["the British pound", /\b(pound|sterling|gbp|bank of england|boe)\b/i] };
// "X <falls|rises> ..." where X is an asset name: used for knock-on rules and to spot headlines that already state an answer
const RT48B_UPV = "rises?|rose|rising|jump\\w*|surg\\w*|soar\\w*|climb\\w*|rall\\w*|gains?|gained|strengthen\\w*|firm\\w*|spik\\w*|advanc\\w*|rebound\\w*|hits? (?:a )?record|record high|snaps? (?:a |its )?(?:\\w+[- ])*(?:losing|down) (?:streak|run)";
const RT48B_DNV = "falls?|fell|falling|drop\\w*|dips?|dipped|slips?|slipped|slid\\w*|slides?|slump\\w*|sink\\w*|sank|tumbl\\w*|plung\\w*|weaken\\w*|retreat\\w*|declin\\w*|eases?|eased|los(?:es|t|ing) ground|snaps? (?:a |its )?(?:\\w+[- ])*(?:win|winning) (?:streak|run)";
const RT48B_NM = { gold: "gold|bullion", oil: "oil|crude|brent|wti|opec", usd: "dollar|greenback|dxy", yields: "yields?|treasur(?:y|ies)", spx: "s&p(?: 500)?|wall street|stocks|dow(?: jones)?", nasdaq: "nasdaq", btc: "bitcoin|btc", eth: "ether|ethereum", eurusd: "euro|eur/usd", gbp: "pound|sterling|gbp" };
function RT48B_MV(names, dir) { return new RegExp("\\b(?:" + names + ")\\b(?:(?!\\b(?:as|after|while|but|and|than|with|amid|helping|despite|vs)\\b)[^.;:?!,]){0,30}?\\b(?:" + (dir === "up" ? RT48B_UPV : RT48B_DNV) + ")\\b", "i"); }
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
  [/\b(bank of england|boe|bailey)\b.*\b(raises?|hikes?)\b.*\brates?\b/i, { gbp: ["up", "A surprise Bank of England hike usually lifts the pound first, as higher UK rates attract money into sterling."] }],
  // knock-on effects of a move the headline reports (the question is then about a different asset, so the answer is not given away)
  [RT48B_MV("dollar|greenback|dxy", "down"), { gold: ["up", "Gold is priced in dollars, so a weaker dollar usually supports the gold price: it becomes cheaper for buyers using other currencies."], eurusd: ["up", "EUR/USD is the price of one euro in dollars, so when the dollar weakens broadly, EUR/USD usually rises."], gbp: ["up", "The pound is usually quoted against the dollar, so a broadly weaker dollar tends to lift the pound."] }],
  [RT48B_MV("dollar|greenback|dxy", "up"), { gold: ["down", "Gold is priced in dollars, so a stronger dollar often weighs on the gold price: it becomes dearer for buyers using other currencies."], eurusd: ["down", "EUR/USD is the price of one euro in dollars, so when the dollar strengthens broadly, EUR/USD usually falls."], gbp: ["down", "The pound is usually quoted against the dollar, so a broadly stronger dollar tends to push the pound lower."] }],
  [RT48B_MV("(?:treasury|bond|u\\.?s\\.? |us |10-year )yields?|yields", "down"), { gold: ["up", "Lower bond yields usually support gold, because the interest given up by holding a metal that pays none becomes smaller."] }],
  [RT48B_MV("(?:treasury|bond|u\\.?s\\.? |us |10-year )yields?|yields", "up"), { gold: ["down", "Rising bond yields often weigh on gold, because holding a metal that pays no interest becomes more costly."] }],
  [RT48B_MV("bitcoin|btc", "down"), { eth: ["down", "Ether usually moves in the same direction as Bitcoin, the largest crypto asset, so a falling Bitcoin tends to drag it lower."] }],
  [RT48B_MV("bitcoin|btc", "up"), { eth: ["up", "Ether usually moves in the same direction as Bitcoin, the largest crypto asset, so a rising Bitcoin tends to lift it."] }],
  [/\bsafe[- ]havens?\b|\bflight to safety\b|\brisk[- ]off\b/i, { gold: ["up", "When investors rush for safety, gold usually benefits first, as a traditional safe-haven asset."], yields: ["down", "A rush for safety usually pushes money into Treasuries, which lifts bond prices and so tends to lower yields."] }],
  [/\b(sanction\w*|embargo\w*)\b.*\b(oil|crude|russia\w*|iran\w*|venezuela\w*)\b|\b(oil|crude)\b.*\b(sanction\w*|embargo\w*)\b|\bhurricane\b.*\b(gulf|oil|refiner\w*)\b/i, { oil: ["up", "Anything that may cut oil supply, such as sanctions or storms near production sites, usually lifts oil prices first."] }],
  [/\brecession (fears?|worries|risks?|warnings?)\b|\b(fears?|worries) of (a )?recession\b/i, { yields: ["down", "Recession worries usually pull Treasury yields lower first, as investors buy safer bonds and expect lower interest rates."], oil: ["down", "Recession worries often push oil prices lower first, because a weaker economy is expected to use less fuel."] }],
  [/\b(new|higher|sweeping|steep|more) tariffs?\b|\btariffs?\b.*\b(impos\w*|rais\w*|hik\w*|threat\w*|escalat\w*)\b|\btrade war\b/i, { spx: ["down", "Surprise tariffs or an escalating trade war usually weigh on US stocks first, as investors expect higher costs and slower trade."] }],
  [/\b(payrolls?|jobs report|hiring|job growth)\b.*\b(beat\w*|strong\w*|surg\w*|jump\w*|blows? past|tops?)\b/i, { usd: ["up", "A stronger US jobs report than expected usually lifts the dollar first, because the Fed is seen keeping rates higher for longer."], yields: ["up", "Strong US jobs data usually pushes Treasury yields higher first, as rate-cut expectations fade."] }],
  [/\b(payrolls?|jobs report|hiring|job growth)\b.*\b(miss\w*|weak\w*|slow\w*|stall\w*|disappoint\w*)\b/i, { usd: ["down", "A weaker US jobs report than expected usually weakens the dollar first, because rate cuts look more likely."], yields: ["down", "Weak US jobs data usually pulls Treasury yields lower first, as traders expect earlier rate cuts."] }],
  [/\b(fed|federal reserve|powell|fomc)\b.*\bhawkish\b|\bhawkish\b.*\b(fed|federal reserve|powell|fomc)\b/i, { usd: ["up", "A more hawkish Fed than expected usually lifts the dollar first, because US rates are seen staying higher."], yields: ["up", "A hawkish Fed surprise usually pushes Treasury yields higher first."] }],
  [/\b(fed|federal reserve|powell|fomc)\b.*\bdovish\b|\bdovish\b.*\b(fed|federal reserve|powell|fomc)\b/i, { usd: ["down", "A more dovish Fed than expected usually weakens the dollar first, because US rates are seen falling sooner."], gold: ["up", "A dovish Fed surprise often lifts gold first, as lower expected rates reduce the cost of holding it."] }] ];
const RT48B_DIRW = { up: /\b(rise|rises|rising|rose|higher|lift\w*|gain\w*|climb\w*|rall\w*|strengthen\w*|up|upward|support\w*|jump\w*|increas\w*|boost\w*|push\w* (prices )?(up|higher)|spik\w*|surg\w*|soar\w*|advanc\w*|firm\w*|benefit\w*|appreciat\w*|bid up|rebound\w*)\b/i, down: /\b(fall|falls|falling|fell|lower|drop\w*|declin\w*|weaken\w*|slip\w*|down|downward|weigh\w*|sell\w*|decreas\w*|slid\w*|slide\w*|slump\w*|tumbl\w*|plung\w*|sink\w*|retreat\w*|soften\w*|pressure\w*|hurt\w*|depreciat\w*|eas(e|es|ing))\b/i, flat: /\b(little|limited|muted|unchanged|flat|small|modest|steady|stable|contained|minimal)\b/i };
const RT48B_HEDGE = /\b(typical\w*|usual\w*|often|tend\w*|general\w*|common\w*|normal\w*|historical\w*|traditional\w*|frequent\w*|likely)\b/i;
// names whose digits are not "numbers" (S&P 500, Nasdaq 100, FTSE 100, 10-year, 2-year, 2% target, G7, Web3 ...)
const RT48B_NUMOK = /\b(s&p ?500|nasdaq[- ]?100|ftse ?100|dow 30|\d{1,2}-year|\d{1,2}-month|g7|g20|web3|2% (inflation )?target|covid-19|24\/7|q[1-4])\b/gi;
const _rt48sState = { day: "", generatedAt: "", items: [], kind: "template", tries: 0, last: 0, forced: 0, busy: null, diag: null };
const _rt48sFile = require("path").join(require("os").tmpdir(), "dispatch-academy-daily-v3.json");
function _rt48sDay() { try { return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/London" }).format(new Date()); } catch (e) { return new Date().toISOString().slice(0, 10); } }
function _rt48bQ(asset) { return `If this news is a surprise to markets, what is the typical first reaction in ${RT48B_ASSETS[asset][0]}?`; }
function _rt48bRule(h, asset) { for (const [re, m] of RT48B_RULES) if (re.test(h) && m[asset]) return m[asset]; return null; }
function _rt48bWhy(x) { try { if (!x || typeof x !== "object") return "not-object"; const A = RT48B_ASSETS[x.asset], h = String(x.h || ""), e = String(x.e || "");
  if (!A) return "asset-not-allowed"; if (!(A[1].test(h) || _rt48bRule(h, x.asset))) return "asset-not-in-headline";
  if (RT48B_BAN.test(h) || RT48B_BAN.test(e)) return "banned-topic"; if (h.length < 20 || h.length > 240 || /[<>]|&#?\w+;/.test(h)) return "bad-headline";
  const k = RT48B_DIRS.indexOf(x.dir); if (k < 0) return "bad-dir"; if (x.a !== k || !Array.isArray(x.o) || x.o.join("|") !== RT48B_OPTS.join("|") || x.q !== _rt48bQ(x.asset)) return "bad-shape";
  if (e.length < 40) return "e-too-short"; if (e.length > 380) return "e-too-long"; if (/[<>]|https?:|www\./i.test(e)) return "e-link-or-html";
  if (/\b(you should|buy now|sell now|guarantee\w*|definitely|certain to)\b/i.test(e)) return "e-advice";
  if (!RT48B_HEDGE.test(e)) return "e-no-hedge-word"; if (!RT48B_DIRW[x.dir].test(e)) return "e-dir-word-missing";
  const nums = t => (String(t).replace(RT48B_NUMOK, " ").match(/\d+(?:[.,]\d+)*/g) || []).map(n => n.replace(/,/g, "")), hn = new Set(nums(h)); if (nums(e).some(n => !hn.has(n))) return "e-number-not-in-headline";
  const r = _rt48bRule(h, x.asset); if (r && r[0] !== x.dir) return "contradicts-known-reaction";
  // the headline already states this asset's move ("Bitcoin dips to ...", "yields fall for the week"): the answer would be given away
  if ((RT48B_MV(RT48B_NM[x.asset], "up").test(h) || RT48B_MV(RT48B_NM[x.asset], "down").test(h))) return "headline-states-move";
  if (x.link && !/^https:\/\/[^\s"'<>]{5,300}$/.test(x.link)) return "bad-link"; return ""; } catch (e) { return "error"; } }
function _rt48bValid(x) { return !_rt48bWhy(x); }
function _rt48sLoad() { try { const o = JSON.parse(require("fs").readFileSync(_rt48sFile, "utf8")); if (o && o.day === _rt48sDay() && Array.isArray(o.items)) Object.assign(_rt48sState, { day: o.day, generatedAt: o.generatedAt || "", items: o.items, kind: o.kind || "template", tries: o.tries || 0, last: o.last || 0, forced: o.forced || 0, diag: o.diag || null }); } catch (e) {} }
function _rt48sSave() { try { const { day, generatedAt, items, kind, tries, last, forced, diag } = _rt48sState; require("fs").writeFileSync(_rt48sFile, JSON.stringify({ day, generatedAt, items, kind, tries, last, forced, diag })); } catch (e) {} }
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
  return all.filter(x => !/^live( updates)?:|\blive\b:/i.test(x.h) && (!x.t || now - x.t < 72 * 36e5) && !seen.has(x.h.toLowerCase()) && seen.add(x.h.toLowerCase())).map(x => ({ ...x, as: _rt48bAssets(x.h) })).filter(x => x.as.length).sort((a, b) => b.t - a.t).slice(0, 20); }
function _rt48bItem(H, asset, dir, e, kind) { const a = RT48B_DIRS.indexOf(dir); return { h: H.h, src: H.src, link: H.link, asset, dir, q: _rt48bQ(asset), o: RT48B_OPTS.slice(), a, e: String(e || "").trim(), kind }; }
function _rt48bTemplates(heads, skip, usedAs, want) { const out = [], cand = [];
  heads.forEach((H, hi) => { if (skip.has(H.h)) return; H.as.forEach(as => { const r = _rt48bRule(H.h, as); if (!r) return; const it = _rt48bItem(H, as, r[0], r[1], "template"); if (_rt48bValid(it)) cand.push({ it, hi }); }); });
  const usedH = new Set(skip), seenAs = new Set(usedAs || []);
  for (const pass of [0, 1]) for (const c of cand) { if (out.length >= want) break; if (usedH.has(c.it.h) || (pass === 0 && seenAs.has(c.it.asset))) continue; out.push(c.it); usedH.add(c.it.h); seenAs.add(c.it.asset); }
  return out; }
// read the provider reply: plain JSON, markdown-fenced JSON, prose around it, or a truncated reply (complete item objects are kept)
function _rt48bParse(t) { t = String(t || "").replace(/```(?:json|JSON)?/g, "").trim(); const tryJ = v => { try { return JSON.parse(v); } catch (e) { return null; } };
  let j = tryJ(t); if (!j) { const s0 = t.indexOf("{"), s1 = t.lastIndexOf("}"); if (s0 >= 0 && s1 > s0) j = tryJ(t.slice(s0, s1 + 1)); }
  if (!j) { const s0 = t.indexOf("["), s1 = t.lastIndexOf("]"); if (s0 >= 0 && s1 > s0) j = tryJ(t.slice(s0, s1 + 1)); }
  let arr = Array.isArray(j) ? j : j && Array.isArray(j.items) ? j.items : j && typeof j === "object" ? (Object.values(j).find(Array.isArray) || null) : null, how = arr ? "json" : "";
  if (!arr) { arr = (t.match(/\{[^{}]*\}/g) || []).map(tryJ).filter(o => o && typeof o === "object" && ("asset" in o || "i" in o)); how = arr.length ? "salvaged" : "unreadable"; }
  return { arr: arr.slice(0, 12), how }; }
const RT48B_ALIAS = { "s&p 500": "spx", "s&p": "spx", "sp500": "spx", "s&p500": "spx", "spx": "spx", "us stocks": "spx", "stocks": "spx", "wall street": "spx", "dollar": "usd", "us dollar": "usd", "u.s. dollar": "usd", "dxy": "usd", "usd": "usd",
  "treasury yields": "yields", "us yields": "yields", "us treasury yields": "yields", "yield": "yields", "yields": "yields", "bitcoin": "btc", "btc": "btc", "ether": "eth", "ethereum": "eth", "eth": "eth", "euro": "eurusd", "eur/usd": "eurusd", "eurusd": "eurusd", "eur": "eurusd",
  "pound": "gbp", "sterling": "gbp", "gbp": "gbp", "gbp/usd": "gbp", "gbpusd": "gbp", "british pound": "gbp", "gold": "gold", "xau": "gold", "xauusd": "gold", "oil": "oil", "crude": "oil", "crude oil": "oil", "brent": "oil", "wti": "oil", "nasdaq": "nasdaq", "nasdaq 100": "nasdaq" };
function _rt48bAsId(v) { const k = String(v || "").toLowerCase().replace(/[()]/g, "").replace(/\s+/g, " ").trim(); return RT48B_ASSETS[k] ? k : RT48B_ALIAS[k] || ""; }
function _rt48bDirId(v) { const k = String(v || "").toLowerCase().trim(); return /^(up|higher|rise|rises|bullish|positive|increase)$/.test(k) ? "up" : /^(down|lower|fall|falls|bearish|negative|decrease)$/.test(k) ? "down" : /^(flat|little change|unchanged|neutral|sideways|little|none)$/.test(k) ? "flat" : ""; }
async function _rt48sBuild(why) { const day = _rt48sDay(), t0 = Date.now(), D = { at: new Date().toISOString(), why: why || "auto", heads: 0, ai: "not-called", model: "", ms: 0, replyChars: 0, parse: "", received: 0, accepted: 0, rejected: {}, samples: [], templates: 0, served: 0 };
  _rt48sState.tries++; _rt48sState.last = Date.now(); _rt48sSave();
  try { const heads = await _rt48sHeads(); let items = []; D.heads = heads.length;
    if (!heads.length) D.ai = "no-headlines"; else if (String(process.env.ACADEMY_AI || "").toLowerCase() === "off") D.ai = "off (ACADEMY_AI)"; else if (typeof generateAi !== "function") D.ai = "no-generateAi";
    else {
      try { const list = heads.map((x, k) => `${k}. ${x.h} [assets: ${x.as.join(", ")}]`).join("\n");
        const r = await generateAi({ maxTokens: 1600, temperature: 0.2,
          system: "You help write a free beginner markets course. From the numbered headlines, choose up to 4 where the usual FIRST market reaction is well established in finance textbooks, and for each name ONE asset id from that headline's [assets: ...] list and the usual first move in that asset's price if the news were a surprise: up, down or flat. Prefer an asset whose move the headline does NOT already state (e.g. for 'Dollar slips' choose gold or eurusd, not usd). Never pick a stablecoin. The explanation: one or two plain British English sentences, at most 260 characters, saying this is the typical or usual first reaction and why, using the words rise/fall (or little change); no digits at all, no predictions, no advice. Reply with raw JSON only, no markdown.",
          messages: [{ role: "user", content: `Headlines:\n${list}\n\nReturn {"items":[{"i":<headline number>,"asset":"<asset id from that headline's list>","dir":"up|down|flat","e":"<explanation>"}]}` }] });
        const txt = String(r && r.text || ""); D.ai = "ok"; D.model = String(r && r.model || "").slice(0, 60); D.replyChars = txt.length;
        const P = _rt48bParse(txt); D.parse = P.how; D.received = P.arr.length;
        const used = new Set(), rej = (why, x, extra) => { D.rejected[why] = (D.rejected[why] || 0) + 1; if (D.samples.length < 8) D.samples.push(Object.assign({ why, i: x && x.i, asset: String(x && x.asset || "").slice(0, 20), dir: String(x && x.dir || "").slice(0, 16), e: String(x && x.e || "").slice(0, 200) }, extra || {})); };
        P.arr.forEach(x => { if (!x || typeof x !== "object") return rej("not-object", x);
          let i = Number(x.i != null ? x.i : x.index), H = Number.isInteger(i) ? heads[i] : null;
          const ht = String(x.h || x.headline || "").toLowerCase().trim(); if ((!H || (ht && H.h.toLowerCase() !== ht)) && ht) H = heads.find(y => y.h.toLowerCase() === ht) || H;
          if (!H) return rej("bad-headline-index", x); const as = _rt48bAsId(x.asset), dir = _rt48bDirId(x.dir);
          if (!as) return rej("asset-not-allowed", x, { h: H.h.slice(0, 120) }); if (!H.as.includes(as)) return rej("asset-not-in-headline-list", x, { h: H.h.slice(0, 120) });
          if (used.has(H.h)) return rej("duplicate-headline", x); if (items.length >= 3) return rej("over-limit", x);
          const it = _rt48bItem(H, as, dir, x.e, "ai"), w = _rt48bWhy(it); if (w) return rej(w, x, { h: H.h.slice(0, 120) }); items.push(it); used.add(H.h); D.accepted++; });
      } catch (e) { D.ai = "error: " + String((e && (e.code || e.name)) || "unknown").slice(0, 40); try { console.warn("academy-daily: AI skipped", (e && (e.code || e.message)) || e); } catch (x) {} } }
    const tp = _rt48bTemplates(heads, new Set(items.map(x => x.h)), items.map(x => x.asset), 3 - items.length); D.templates = tp.length; items = items.concat(tp).slice(0, 3); D.served = items.length; D.ms = Date.now() - t0;
    if (_rt48sDay() === day && (items.length || !_rt48sState.items.length)) Object.assign(_rt48sState, { day, generatedAt: new Date().toISOString(), items, kind: items.some(x => x.kind === "ai") ? "ai" : "template" });
    if (_rt48sDay() === day) { _rt48sState.diag = D; _rt48sSave(); }
  } catch (e) { try { console.warn("academy-daily: build skipped", (e && (e.code || e.message)) || e); } catch (x) {} } }
async function academyDaily(req, res) {
  let forced = false, admin = false, wantDiag = false;
  const send = () => { const s = _rt48sState, today = s.day === _rt48sDay(), items = today ? s.items.filter(_rt48bValid) : [], out = { date: _rt48sDay(), generatedAt: today && items.length ? s.generatedAt : "", kind: items.some(x => x.kind === "ai") ? "ai" : "template", items, v: 3 };
    if (admin && wantDiag) out.diag = Object.assign({ tries: s.tries, forced: s.forced || 0, busy: !!s.busy, aiSwitch: String(process.env.ACADEMY_AI || "").toLowerCase() === "off" ? "off" : "on" }, today && s.diag ? s.diag : { note: "no build yet today" });
    res.writeHead(200, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": admin && wantDiag ? "no-store" : "private, max-age=300", "X-Content-Type-Options": "nosniff" }); res.end(JSON.stringify(out)); };
  try { const day = _rt48sDay(); if (_rt48sState.day !== day) { _rt48sLoad(); if (_rt48sState.day !== day) Object.assign(_rt48sState, { day, generatedAt: "", items: [], kind: "template", tries: 0, last: 0, forced: 0, diag: null }); }
    const n0 = _rt48sState.items.length; _rt48sState.items = _rt48sState.items.filter(_rt48bValid); // drop cached items that fail the current rules
    if (n0 && !_rt48sState.items.length) { _rt48sState.tries = 0; _rt48sState.last = 0; _rt48sSave(); }
    try { const q = new URL(req.url || "/", "http://x").searchParams; const rf = q.get("refresh") === "1"; wantDiag = rf || q.get("diag") === "1";
      if (wantDiag && typeof currentUser === "function" && typeof isAdminUser === "function") { const u = await currentUser(req); admin = !!(u && isAdminUser(u)); if (admin && rf && (_rt48sState.forced || 0) < 6) forced = true; } } catch (e) {}
    const S = _rt48sState, weak = S.items.length < 3 || !S.items.some(x => x.kind === "ai");
    if (forced && !S.busy) { S.forced = (S.forced || 0) + 1; S.busy = _rt48sBuild("admin-refresh").finally(() => { S.busy = null; }); }
    else if (weak && !S.busy && S.tries < 3 && Date.now() - S.last > 2 * 36e5) S.busy = _rt48sBuild(S.items.length ? "auto-retry" : "auto").finally(() => { S.busy = null; });
    if (S.busy) await Promise.race([S.busy, new Promise(r => setTimeout(r, forced ? 45000 : 6000))]);
  } catch (e) {}
  try { return send(); } catch (e) { try { res.end(); } catch (x) {} } }
'''
print('old block:', 'matches rt48bs exactly' if s[i:j].strip() == OLD.strip() else 'differs from rt48bs (%d chars), replacing anyway' % (j - i))
s = s[:i] + NEW + s[j:]
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print('OK rt48c: academy-daily block replaced; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('written', P)
