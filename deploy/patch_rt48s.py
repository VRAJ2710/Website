#!/usr/bin/env python3
"""patch_rt48s.py (server only, optional): adds GET /api/academy-daily for Dispatch Academy auto-content.
Builds up to 3 explainer questions a day from the site's approved RSS feeds (f0 BBC Business, f1 CNBC, f4 MarketWatch, f12 CoinDesk)
with ONE call to the site's existing generateAi() provider; output is strictly validated (headline index, lengths, no URLs/HTML,
no numbers that are not in the headline). Cached in memory + os.tmpdir()/dispatch-academy-daily.json for the London day;
at most 2 build attempts a day, 2h apart. Always answers 200 JSON; failures are silent (the client keeps its template cards).
ACADEMY_AI=off disables the AI call. No database, no new tables, no Stripe.
Two anchored inserts; SKIPS (changes nothing) unless both anchors match exactly once. Refuses twice.
Usage: python3 patch_rt48s.py [--check] server.js"""
import sys, subprocess, tempfile, os
args = [a for a in sys.argv[1:] if a != "--check"]; check = "--check" in sys.argv
p = args[0] if args else "server.js"
raw = open(p, "rb").read().decode("utf-8"); crlf = "\r\n" in raw; s = raw.replace("\r\n", "\n")
if "// ── rt48s:" in s or '"/api/academy-daily"' in s: sys.exit("REFUSE: rt48s already applied")
A1 = "const MARKET_SYSTEM = `"
A2 = '  if (p === "/api/yahoo-chart") {'
for a in (A1, A2):
    if s.count(a) != 1: print("SKIPPED: anchor matched %d times (%s); nothing changed" % (s.count(a), a[:40])); sys.exit(0)
for need in ("approvedRssFeedUrl", "async function generateAi("):
    if need not in s: print("NOTE: %s not found; the route will still answer 200 with no AI items" % need)
BLOCK = r'''// ── rt48s: /api/academy-daily ── auto-generated Academy explainers from the site's own RSS headlines.
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
s = s.replace(A1, BLOCK + A1, 1)
s = s.replace(A2, '  if (p === "/api/academy-daily") return academyDaily(req, res);\n' + A2, 1)
with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: sys.exit("ABORT: node --check failed: " + r.stderr[:400])
print("OK rt48s: /api/academy-daily added (2 anchored inserts); node --check passed" + (" (dry run)" if check else ""))
if not check:
    open(p, "wb").write((s.replace("\n", "\r\n") if crlf else s).encode("utf-8")); print("written", p)
