#!/usr/bin/env python3
"""bb9a: Academy daily - day rollover of the build counter, 04:00 UK run hour (lazy, first request), AI through the
site's own provider slots (no xAI) with a bounded in-call retry, 15-min in-memory backoff after a failed build,
headline/link/src/asset integrity, plain edition labels. Server-only. No timers, no tables, no secrets.
Usage: python3 patch_bb9a.py <folder> [--check]"""
import sys, os, hashlib, subprocess
BASE_MD5 = "b75978b70054c3c2befd6711e14a56ae"
MARK = "// ── bb9a:"
NL = b"\n"  # py<3.12 portability: no backslash inside f-string braces
def md5(b): return hashlib.md5(b).hexdigest()

HELPERS = r'''// ── bb9a: Academy daily. (1) the build counter resets when the London day changes (it never did, so after 3 builds on 23 Oct no
// 24 Oct build could start until a restart); (2) a new day's set is built on the first request at or after BB9A_RUN_HOUR_UK
// (lazy, no timer); before that yesterday's set is served with a plain label; (3) the AI call uses the same provider slots as
// Ask (bb3bAttempts, minus xAI, as bb4daily intended) with realistic timeouts and one bounded retry round; (4) a failed build
// may retry on the next request after BB9A_FAIL_BACKOFF_MS (in-memory, max BB9A_MAX_TRIES a day); (5) headline, link, src and
// asset must belong to the same news item. No setInterval/setTimeout/cron added, no tables, no secrets.
const BB9A_RUN_HOUR_UK = 4;
const BB9A_FAIL_BACKOFF_MS = 15 * 60 * 1000;
const BB9A_MAX_TRIES = 6;
const BB9A_SRC_HOST = { "Investing.com": /(^|\.)investing\.com$/i, "CoinDesk": /(^|\.)coindesk\.com$/i, "CNBC": /(^|\.)cnbc\.com$/i, "MarketWatch": /(^|\.)marketwatch\.com$/i, "BBC Business": /(^|\.)bbc\.(co\.uk|com)$/i, "BBC World": /(^|\.)bbc\.(co\.uk|com)$/i };
const BB9A_STOP = new Set("the a an and or of to in on at for as by with from is are be its it this that after amid over into than while new says said how what why who will can could may has have was were not but out off per via".split(" "));
// a headline that already states the asset's move with words rt48b does not list ("yields crater", "one-month low")
const BB9A_MOVEW = "crater\\w*|plummet\\w*|collaps\\w*|nosediv\\w*|skyrocket\\w*|tank\\w*|spik\\w*|(?:\\w+-)?(?:day|week|month|year) (?:low|high)s?|lows?|highs?";
function bb9aUk(ms) {
  const d = new Date(ms == null ? Date.now() : ms);
  try { const p = {}; new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(d).forEach(x => { p[x.type] = x.value; });
    return { day: `${p.year}-${p.month}-${p.day}`, hour: Number(p.hour), minute: Number(p.minute), hm: `${p.hour}:${p.minute}` }; }
  catch (e) { const i = d.toISOString(); return { day: i.slice(0, 10), hour: d.getUTCHours(), minute: d.getUTCMinutes(), hm: i.slice(11, 16) }; } }
function bb9aRunText() { const h = BB9A_RUN_HOUR_UK; return `${h % 12 || 12}${h < 12 ? "am" : "pm"} UK`; }
function bb9aDayLabel(day) { try { return new Intl.DateTimeFormat("en-GB", { timeZone: "UTC", weekday: "short", day: "numeric", month: "short" }).format(new Date(day + "T12:00:00Z")).replace(/,/g, ""); } catch (e) { return day || ""; } }
function bb9aPrevDay(day) { try { return new Date(Date.parse(day + "T12:00:00Z") - 864e5).toISOString().slice(0, 10); } catch (e) { return ""; } }
function bb9aRoll(day) { const st = _rt48sState; if (st.bb9aTriesDay === day) return;
  Object.assign(st, { tries: 0, last: 0, forced: 0, bb9aFailed: false, bb9aFailWhy: "", bb9aTriesDay: day }); }
function bb9aWords(s) { return (String(s || "").toLowerCase().match(/[a-z0-9]+/g) || []).filter(w => w.length >= 3 && !BB9A_STOP.has(w) && !/^\d{4,}$/.test(w)).map(w => w.replace(/(ies)$/, "y").replace(/(?<=\w{3})s$/, "")); }
// "" when the link plausibly belongs to the headline. Links whose path is an opaque id (BBC /news/articles/c6ly...) cannot be
// checked and are accepted; a descriptive slug must share words with the headline (60% for Investing.com, see below).
function bb9aLinkWhy(x) { try { const link = String(x && x.link || ""); if (!link) return "";
  let u; try { u = new URL(link); } catch (e) { return "bad-link"; }
  const hostRe = BB9A_SRC_HOST[String(x.src || "")]; if (hostRe && !hostRe.test(u.hostname)) return "src-link-mismatch";
  const slug = bb9aWords(decodeURIComponent(u.pathname).replace(/\.(html?|php)$/i, "").replace(/\/(news|articles?|markets?|story|policy|forex-news|economy-news|stock-market-news|commodities-news|cryptocurrency-news|\d{4}|\d{2})(?=\/)/gi, " "));
  if (slug.length < 4) return "";
  const hw = bb9aWords(x.h), S = new Set(slug), H = new Set(hw); if (!hw.length) return "link-headline-mismatch";
  const hcov = hw.filter(w => S.has(w)).length / hw.length, scov = slug.filter(w => H.has(w)).length / slug.length;
  // Investing.com slugs are the article's own title, so a true pair overlaps almost fully, and its RSS is where titles were
  // paired with other articles' links (23-24 Oct). CNBC/CoinDesk/MarketWatch slugs are SEO rewrites: only reject no overlap.
  const need = /investing\.com$/i.test(u.hostname) ? 0.6 : 0.01;
  return Math.max(hcov, scov) >= need ? "" : "link-headline-mismatch"; } catch (e) { return "link-check-error"; } }
// the asset the headline itself is about: the allowed asset named earliest in it ("" for event headlines such as a Fed decision)
function bb9aPrimary(h) { let best = "", at = Infinity; for (const k of Object.keys(RT48B_ASSETS)) { const m = new RegExp(RT48B_ASSETS[k][1].source, "i").exec(String(h || "")); if (m && m.index < at) { at = m.index; best = k; } } return best; }
function bb9aAssets(h) { const all = _rt48bAssets(h), p = bb9aPrimary(h); return p ? all.filter(k => k === p) : all; }
function bb9aStates(h, asset) { const nm = RT48B_NM[asset]; if (!nm) return false;
  return new RegExp("\\b(?:" + nm + ")\\b(?:(?!\\b(?:as|after|while|but|and|than|with|amid|helping|despite|vs)\\b)[^.;:?!,]){0,40}?\\b(?:" + BB9A_MOVEW + ")\\b", "i").test(String(h || "")); }
// extra checks, run from _rt48bWhy so fresh, cached and saved items all pass them
function bb9aWhy(x) { const p = bb9aPrimary(x.h);
  if (p && x.asset !== p) return "asset-not-headline-subject";
  if (bb9aStates(x.h, x.asset)) return "headline-states-move";
  return bb9aLinkWhy(x); }
// AI: same provider slots as Ask (bb3bAttempts), minus xAI; falls back to the bb4daily provider list. Round 2 retries only
// attempts that failed on a timeout or a transient upstream error.
function bb9aAiAttempts() { let list = [];
  try { if (typeof bb3bAttempts === "function") list = bb3bAttempts().filter(a => a && a.kind !== "xai-key" && a.id !== "xai"); } catch (e) { list = []; }
  for (const [id, model] of BB4D_AI) if (!list.some(a => a.kind === "provider" && a.id === id)) list.push({ kind: "provider", id, model, bb9aFallback: true });
  return list.map(a => a.kind === "provider" && !a.model ? Object.assign({}, a, { model: (BB4D_AI.find(z => z[0] === a.id) || [])[1] }) : a); }
async function bb9aGen(D, opts) { const atts = bb9aAiAttempts(), log = []; let last = null, retry = atts;
  for (let round = 0; round < 2 && retry.length; round++) { const again = [];
    for (const a of retry) { const t0 = Date.now();
      try { const r = a.kind === "openai-slot" ? await bb3bRunOpenAiSlot(a, opts) : await _bb4dOne(a.id, a.model, opts, round ? 20000 : 12000);
        log.push(`${a.id}:ok:${Date.now() - t0}ms`); if (D) D.bb9aAi = log; return r; }
      catch (e) { last = e; const code = String((e && (e.code || e.name)) || "error").slice(0, 30); log.push(`${a.id}:${code}`);
        if (/TIMEOUT|Abort|UPSTREAM|RATE|EMPTY|INVALID|5\d\d|ECONN|fetch/i.test(code + " " + String(e && e.message || ""))) again.push(a); } }
    retry = again; }
  if (D) D.bb9aAi = log; if (!last) { last = new Error("no provider"); last.code = "NO_AI"; } throw last; }
function bb9aMark(day, items, D) { const st = _rt48sState; if (_rt48sDay() !== day) return;
  const got = !!(st.day === day && st.items && st.items.length);
  const why = !got ? (D && !D.heads ? "no-headlines" : "no-items") : (D && /^error/.test(String(D.ai || "")) ? "ai-" + String(D.ai).slice(7) : "");
  st.bb9aFailed = !!why; st.bb9aFailWhy = why; }
// is an automatic build due on this request? (lazy: only a request can start one)
function bb9aDue(seed, day, haveServable) { const st = _rt48sState, P = bb9aUk(), haveToday = !!(seed && seed.day === day && seed.items.length);
  if (!haveToday && haveServable && P.hour < BB9A_RUN_HOUR_UK) return false;
  if ((st.tries || 0) >= BB9A_MAX_TRIES) return false;
  const since = Date.now() - (st.last || 0);
  if (st.bb9aFailed || !haveToday) return since > BB9A_FAIL_BACKOFF_MS;
  return (st.tries || 0) < 3 && since > 2 * 36e5; }
// plain labels: what this set is and when the next one comes
function bb9aLabel(contentDay, day, source) { const st = _rt48sState, P = bb9aUk(), run = bb9aRunText(), dl = bb9aDayLabel(contentDay);
  const base = { dateLabel: dl, nextRunUk: String(BB9A_RUN_HOUR_UK).padStart(2, "0") + ":00" };
  if (source === "fallback") return Object.assign(base, { edition: "sample", stale: false, label: `Sample question while today's set is prepared. A new set arrives around ${run}.` });
  if (contentDay === day) return Object.assign(base, { edition: "today", stale: false, label: `Today's set (${dl}).` });
  if (contentDay === bb9aPrevDay(day)) {
    if (P.hour < BB9A_RUN_HOUR_UK) return Object.assign(base, { edition: "yesterday", stale: false, label: `Yesterday's set, today's arrives around ${run}.` });
    if (st.busy || !(st.tries || 0)) return Object.assign(base, { edition: "yesterday", stale: false, label: `Yesterday's set, today's is being prepared now.` });
    const next = (st.tries || 0) < BB9A_MAX_TRIES ? `We'll try again after ${bb9aUk((st.last || Date.now()) + BB9A_FAIL_BACKOFF_MS).hm} UK.` : `The next try is tomorrow around ${run}.`;
    return Object.assign(base, { edition: "yesterday", stale: true, label: `Today's set didn't generate, so this is yesterday's (${dl}). ${next}` }); }
  return Object.assign(base, { edition: "older", stale: true, label: `Saved set from ${dl}. A newer set hasn't generated since. A new set is due around ${run}.` }); }

'''

EDITS = [
  # load/save keep the build counter only for the London day it belongs to
  ('tries: o.tries || 0, last: o.last || 0, forced: o.forced || 0, diag: o.diag || null });',
   'tries: o.bb9aTriesDay === o.day ? (o.tries || 0) : 0, last: o.bb9aTriesDay === o.day ? (o.last || 0) : 0, forced: o.bb9aTriesDay === o.day ? (o.forced || 0) : 0, diag: o.diag || null, bb9aTriesDay: o.bb9aTriesDay === o.day ? o.day : _rt48sState.bb9aTriesDay });'),
  ('JSON.stringify({ day, generatedAt, items, kind, tries, last, forced, diag })',
   'JSON.stringify({ day, generatedAt, items, kind, tries, last, forced, diag, bb9aTriesDay: _rt48sState.bb9aTriesDay || "" })'),
  # integrity check on every item path
  ('return "bad-link"; return ""; } catch (e) { return "error"; } }',
   'return "bad-link"; return bb9aWhy(x); } catch (e) { return "error"; } }'),
  # headlines: slower second fetch on retry; drop link/headline mismatches; only the headline's own asset
  ('async function _rt48sHeads() {', 'async function _rt48sHeads(bb9aMs) {'),
  ('const xml = await _bb4dGet(u, 1500);', 'const xml = await _bb4dGet(u, bb9aMs || 1500);'),
  ('.map(x => ({ ...x, as: _rt48bAssets(x.h) })).filter(x => x.as.length)',
   '.filter(x => !bb9aLinkWhy(x)).map(x => ({ ...x, as: bb9aAssets(x.h) })).filter(x => x.as.length)'),
  # build: in-call retry of the headline fetch, AI through bb9aGen, failure mark
  ('try { const heads = await _rt48sHeads(); let items = []; D.heads = heads.length;',
   'try { let heads = await _rt48sHeads(); if (!heads.length) { D.bb9aRetry = "headlines"; heads = await _rt48sHeads(4000); } let items = []; D.heads = heads.length;'),
  ('const r = await _bb4dGen({ maxTokens: 1600,', 'const r = await bb9aGen(D, { maxTokens: 1600,'),
  ('    if (_rt48sDay() === day) { _rt48sState.diag = D; _rt48sSave(); }\n  } catch (e) { try { console.warn("academy-daily: build skipped", (e && (e.code || e.message)) || e); } catch (x) {} } }',
   '    bb9aMark(day, items, D);\n    if (_rt48sDay() === day) { _rt48sState.diag = D; _rt48sSave(); }\n  } catch (e) { try { bb9aMark(day, [], null); console.warn("academy-daily: build skipped", (e && (e.code || e.message)) || e); } catch (x) {} } }'),
  # helpers before the route
  ('\nasync function academyDaily(req, res) {', '\n' + HELPERS + 'async function academyDaily(req, res) {'),
  # route: day rollover, due rule, labels
  ('    try { _rt48sLoad(); } catch (e) {}\n    const day = _rt48sDay();',
   '    try { _rt48sLoad(); } catch (e) {}\n    const day = _rt48sDay();\n    bb9aRoll(day);'),
  ('    const due = (_rt48sState.tries || 0) < 3 && Date.now() - (_rt48sState.last || 0) > 2 * 36e5;',
   '    const due = bb9aDue(seed, day, haveServable);'),
  ('    const out = { date: contentDay, generatedAt: asOf, asOf: asOf, source: source, stale: source === "stale", kind: kind, items: items, v: 3 };',
   '    const bb9aL = bb9aLabel(contentDay, day, source);\n    if (source === "stale" && !bb9aL.stale) source = "cache";\n    const out = { date: contentDay, dateLabel: bb9aL.dateLabel, generatedAt: asOf, asOf: asOf, source: source, stale: bb9aL.stale, edition: bb9aL.edition, label: bb9aL.label, nextRunUk: bb9aL.nextRunUk, kind: kind, items: items, v: 3 };'),
  ('      out.diag = Object.assign({ tries: _rt48sState.tries || 0,',
   '      out.diag = Object.assign({ bb9aFailed: !!_rt48sState.bb9aFailed, bb9aFailWhy: _rt48sState.bb9aFailWhy || "", bb9aTriesDay: _rt48sState.bb9aTriesDay || "", tries: _rt48sState.tries || 0,'),
]

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]; check = "--check" in sys.argv
    if not args: print("usage: patch_bb9a.py <folder> [--check]"); return 0
    f = os.path.join(args[0], "server.js"); raw = open(f, "rb").read(); m0 = md5(raw)
    print(f"bb9a: {f} md5 {m0} lines {raw.count(NL)}")
    if m0 != BASE_MD5: print(f"WARN: md5 {m0} != expected base {BASE_MD5} (bb8r); continuing on anchors")
    crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n")
    if MARK in s: print("REFUSE: bb9a already applied"); return 0
    for a, b in EDITS:
        n = s.count(a)
        if n != 1: print(f"REFUSE: anchor found {n}x: {a[:90]!r}"); return 0
        s = s.replace(a, b, 1)
    out = s.replace("\n", "\r\n") if crlf else s
    data = out.encode("utf-8"); tmp = f + ".bb9a.tmp.js"; open(tmp, "wb").write(data)
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    if r.returncode != 0: os.remove(tmp); print("REFUSE: node --check failed\n" + r.stderr); return 0
    print("node --check: ok")
    if check: os.remove(tmp); print(f"--check: dry run ok, would write md5 {md5(data)} lines {data.count(NL)}"); return 0
    os.replace(tmp, f); print(f"bb9a: wrote {f} md5 {md5(data)} lines {data.count(NL)}"); return 0
sys.exit(main())
