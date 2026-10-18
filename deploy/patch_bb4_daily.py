#!/usr/bin/env python3
"""patch_bb4_daily.py — make /api/academy-daily resilient. server.js only.

Stacks on the live rt48c handler (the block patch_rt48c.py installed) and on rt52s.
No new tables, no cron, no background worker, no Stripe, no secrets.

What changes, with the same small anchors on the plain live files and after bb2 (PR #23):
- a saved lesson is returned immediately. A fresh one is source cache. An older or previous-day
  lesson is source stale. A refresh, when one is due, keeps running after the response
  (stale-while-revalidate). There is no timer and no new process;
- a cold request, with nothing saved, waits at most 900ms. The build may finish in that
  window (source live) or keep going after the response. The user still gets a last-good
  lesson or the deterministic fallback;
- the background build does not call generateAi. That helper tries xAI first for 25s.
  This build tries gpt-4o-mini, then Gemini 2.5 Flash, each with a 2.5s cap, and
  never starts a second build while one promise is in flight;
- the last good lesson is kept in memory and in the temp dir, including across the London day;
- the handler always answers users with JSON. A thrown error becomes that fallback, not a 500;
- ?diag=1 stays admin-only and is 403 for everyone else. ?refresh=1 still does not rebuild for non-admins;
- every user response carries asOf and source (live, cache, stale, fallback).

Version: this file does not edit app.js or index.html, so it does not change ?v=chatNN.
patch_bb4_academy.py detects the current chatNN (live is chat59) and adds one.
Requires the rt52s marker, the bb2 marker, and function hasPremiumAccess(.
It does not compare tier strings. Diag stays admin-only via isAdminUser.
The marker is bb4daily, so the home-freeze server patch is not treated as this one.
This file does not edit generateAi (its provider order stays for the coming
Ask patch), the Ask stream, the rt52s 13F block, or the prefs schema.

Usage:
    python3 patch_bb4_daily.py --check server.js
    python3 patch_bb4_daily.py server.js
A second run prints REFUSE and exits 0. CRLF-safe. node --check before the write;
a failed write restores the backup. Prints md5 and line count before and after.
Prints no secrets.
"""
import hashlib, os, subprocess, sys, tempfile

CHECK = "--check" in sys.argv
args = [a for a in sys.argv[1:] if a != "--check"]
P = args[0] if args else "server.js"

def die(m):
    print("ABORT (nothing written):", m)
    sys.exit(1)

def load(path):
    b = open(path, "rb").read()
    return b.decode("utf-8").replace("\r\n", "\n"), b"\r\n" in b

def stats(text, crlf):
    raw = (text.replace("\n", "\r\n") if crlf else text).encode("utf-8")
    return hashlib.md5(raw).hexdigest(), len(text.splitlines()), len(raw)

def show(label, text, crlf):
    md5, lines, nbytes = stats(text, crlf)
    print("%s md5=%s lines=%d bytes=%d" % (label, md5, lines, nbytes))

def nodecheck(text, label):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as t:
        t.write(text)
        tmp = t.name
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    os.unlink(tmp)
    if r.returncode:
        die("node --check failed for %s: %s" % (label, (r.stderr or "")[:500]))

if not os.path.isfile(P):
    die("not found: " + P)
s, crlf = load(P)
if "// ── bb4daily ──" in s:
    print("REFUSE: bb4daily already applied")
    sys.exit(0)
show("bb4daily before server.js", s, crlf)
digest = stats(s, crlf)[0]
LIVE = "6972fdeb0fc892f370ef63fe21b80b55"
if digest != LIVE:
    print("WARN md5 server.js: have %s expected live %s (anchors still decide)" % (digest, LIVE))
errors = []
for need in ("// ── rt52s", "// ── bb2 ──", "function hasPremiumAccess(", "// ── rt48c:", "async function academyDaily(req, res) {", "function _rt48bValid(", "async function _rt48sBuild(", "const _rt48sFile"):
    if need not in s:
        errors.append("missing %r" % need)
FETCH = '    const r = await fetch(u, { headers: { "User-Agent": "DispatchMarkets/1.0" }, signal: AbortSignal.timeout(8000) }); if (!r.ok) return; all.push(..._rt48sParse((await r.text()).slice(0, 600000), src)); } catch (e) {} }));'
GEN = "        const r = await generateAi({ maxTokens: 1600, temperature: 0.2,"
END = "  try { return send(); } catch (e) { try { res.end(); } catch (x) {} } }\n"
START = "async function academyDaily(req, res) {"
for name, needle in (("rss fetch", FETCH), ("generateAi call", GEN), ("academyDaily start", START), ("academyDaily end", END)):
    n = s.count(needle)
    if n != 1:
        errors.append("anchor %s matched %d times (need 1)" % (name, n))
if errors:
    die("; ".join(errors))
i = s.find(START)
j = s.find(END, i)
if j < 0:
    die("academyDaily end anchor is not after the function start")
j += len(END)
if s.find(START, i + len(START), j) >= 0:
    die("a second academyDaily start sits inside the function")
if not (0 <= s.find(FETCH) < i and 0 <= s.find(GEN) < i):
    die("rss fetch and generateAi anchors must sit before academyDaily")

FETCH_NEW = '    const xml = await _bb4dGet(u, 1500); if (!xml) return; all.push(..._rt48sParse(xml, src)); } catch (e) {} }));'
GEN_NEW = "        const r = await _bb4dGen({ maxTokens: 1600, temperature: 0.2,"

HELPERS = r'''// ── bb4daily ── timeouts, last-good cache, deterministic fallback. No cron. ?diag=1 is admin-only.
const _bb4dLastFile = require("path").join(require("os").tmpdir(), "dispatch-academy-daily-last.json");
let _bb4dLast = null;
const BB4D_AI = [["openai", "gpt-4o-mini"], ["google", "gemini-2.5-flash"]];
async function _bb4dOne(provider, model, opts, ms) {
  if (provider === "xai" || typeof generateWithAiProvider !== "function") {
    const e = new Error("provider skipped"); e.code = "NO_AI"; throw e;
  }
  const ctrl = typeof AbortController === "function" ? new AbortController() : null;
  let timer;
  const run = generateWithAiProvider(provider, {
    system: opts && opts.system, messages: opts && opts.messages, maxTokens: opts && opts.maxTokens,
    temperature: opts && opts.temperature, model: model, signal: ctrl ? ctrl.signal : undefined
  });
  const cap = new Promise((_, rej) => { timer = setTimeout(() => { try { if (ctrl) ctrl.abort(); } catch (x) {} const e = new Error("academy-daily AI timed out"); e.code = "TIMEOUT"; rej(e); }, ms); });
  try { return await Promise.race([Promise.resolve(run), cap]); }
  finally { clearTimeout(timer); }
}
async function _bb4dGen(opts) {
  let last;
  for (let i = 0; i < BB4D_AI.length; i++) {
    try { return await _bb4dOne(BB4D_AI[i][0], BB4D_AI[i][1], opts, 2500); }
    catch (e) { last = e; }
  }
  if (!last) { last = new Error("no provider"); last.code = "NO_AI"; }
  throw last;
}
function _bb4dStart(why) {
  if (_rt48sState.busy) return _rt48sState.busy;
  let release;
  const gate = new Promise(r => { release = r; });
  _rt48sState.busy = gate;
  if (why === "admin-refresh") _rt48sState.forced = (_rt48sState.forced || 0) + 1;
  const job = _rt48sBuild(why).finally(() => {
    if (_rt48sState.busy === job || _rt48sState.busy === gate) _rt48sState.busy = null;
    release();
  });
  _rt48sState.busy = job;
  job.then(() => {
    try {
      const built = _bb4dState();
      if (built && built.items.length) _bb4dRemember(built.items, built.generatedAt, built.kind, built.day);
    } catch (e) {}
  }, () => {});
  return job;
}
async function _bb4dGet(url, ms) {
  let timer;
  const ctrl = typeof AbortSignal !== "undefined" && typeof AbortSignal.timeout === "function" ? AbortSignal.timeout(ms) : null;
  const r = await fetch(url, { headers: { "User-Agent": "DispatchMarkets/1.0" }, redirect: "follow", signal: ctrl || undefined });
  if (!r || !r.ok) return "";
  const body = Promise.resolve().then(() => r.text());
  const cap = new Promise((_, rej) => { timer = setTimeout(() => rej(new Error("body timeout")), ms); });
  try { return String(await Promise.race([body, cap]) || "").slice(0, 600000); }
  finally { clearTimeout(timer); }
}
function _bb4dRemember(items, generatedAt, kind, day) {
  try {
    const good = (items || []).filter(_rt48bValid).slice(0, 3);
    if (!good.length || kind === "fallback") return;
    _bb4dLast = { v: 1, at: Date.now(), day: day || "", generatedAt: generatedAt || new Date().toISOString(), items: good, kind: kind || "template" };
    require("fs").writeFileSync(_bb4dLastFile, JSON.stringify(_bb4dLast));
  } catch (e) {}
}
function _bb4dRead(file) {
  try { return JSON.parse(require("fs").readFileSync(file, "utf8")); } catch (e) { return null; }
}
function _bb4dRecall() {
  const take = (o, at) => {
    if (!o || !Array.isArray(o.items)) return null;
    const items = o.items.filter(_rt48bValid).slice(0, 3);
    if (!items.length || (o.kind === "fallback")) return null;
    const when = at || Date.parse(o.generatedAt) || Date.now();
    if (Date.now() - when > 14 * 864e5) return null;
    return { v: 1, at: when, day: o.day || "", generatedAt: o.generatedAt || new Date(when).toISOString(), items, kind: o.kind || "template" };
  };
  if (_bb4dLast && _bb4dLast.items && _bb4dLast.items.length) return _bb4dLast;
  const saved = take(_bb4dRead(_bb4dLastFile), null);
  if (saved) { _bb4dLast = saved; return saved; }
  const v3 = take(_bb4dRead(_rt48sFile), null);
  if (v3) { _bb4dLast = v3; return v3; }
  return null;
}
function _bb4dState() {
  try {
    const st = _rt48sState;
    if (!st || !Array.isArray(st.items) || st.kind === "fallback") return null;
    const items = st.items.filter(_rt48bValid).slice(0, 3);
    if (!items.length) return null;
    return { day: st.day || "", generatedAt: st.generatedAt || "", kind: st.kind || "template", items };
  } catch (e) { return null; }
}
function _bb4dFallback() {
  try {
    const H = { h: "The Federal Reserve cuts rates in a surprise move", src: "Dispatch Academy", link: "" };
    const e = "Gold often rises on a surprise Fed cut: lower rates reduce the cost of holding a metal that pays no interest, and the dollar tends to weaken.";
    const it = _rt48bItem(H, "gold", "up", e, "template");
    if (_rt48bValid(it)) return [it];
  } catch (e) {}
  return [{ h: "The Federal Reserve cuts rates in a surprise move", src: "Dispatch Academy", link: "", asset: "gold", dir: "up", q: "If this news is a surprise to markets, what is the typical first reaction in the gold price?", o: ["Up", "Down", "Little change"], a: 0, e: "Gold often rises on a surprise Fed cut: lower rates reduce the cost of holding a metal that pays no interest, and the dollar tends to weaken.", kind: "template" }];
}
async function _bb4dWho(req) {
  if (typeof currentUser !== "function") return null;
  let timer;
  try {
    return await Promise.race([
      Promise.resolve(currentUser(req)),
      new Promise((_, rej) => { timer = setTimeout(() => rej(new Error("timeout")), 2500); })
    ]);
  } catch (e) { return null; }
  finally { clearTimeout(timer); }
}

'''

NEW = r'''async function academyDaily(req, res) {
  const send = (status, obj, cache) => {
    try {
      if (!res || res.headersSent || res.writableEnded) return;
      res.writeHead(status, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": cache || "no-store", "X-Content-Type-Options": "nosniff" });
      res.end(JSON.stringify(obj));
    } catch (e) {
      try {
        if (res && !res.headersSent) {
          const fb = _bb4dFallback();
          const now = new Date().toISOString();
          res.writeHead(200, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" });
          res.end(JSON.stringify({ date: "", generatedAt: now, asOf: now, source: "fallback", stale: false, kind: "template", items: fb, v: 3 }));
        }
      } catch (x) {}
    }
  };
  try {
    let admin = false, wantDiag = false, forced = false;
    let q;
    try { q = new URL(req.url || "/", "http://x").searchParams; } catch (e) { q = new URLSearchParams(); }
    const diag = q.get("diag") === "1", refresh = q.get("refresh") === "1";
    wantDiag = diag || refresh;
    if (wantDiag) {
      const u = await _bb4dWho(req);
      try { admin = !!(u && typeof isAdminUser === "function" && isAdminUser(u)); } catch (e) { admin = false; }
      if (diag && !admin) return send(403, { error: "Administrator access required." }, "no-store");
      if (admin && refresh && (_rt48sState.forced || 0) < 6) forced = true;
    }
    try { _rt48sLoad(); } catch (e) {}
    const day = _rt48sDay();
    const seed = _bb4dState();
    if (seed && seed.items.length) _bb4dRemember(seed.items, seed.generatedAt, seed.kind, seed.day);
    const last = _bb4dRecall();
    const freshMs = 2 * 60 * 60 * 1000;
    const ageOf = (st) => { const t = Date.parse(st && st.generatedAt || ""); return isFinite(t) ? Date.now() - t : Infinity; };
    const todayGood = !!(seed && seed.day === day && seed.items.length);
    const fresh = !!(todayGood && ageOf(seed) < freshMs);
    const haveServable = todayGood || !!(last && last.items && last.items.length);
    const weak = !todayGood || seed.items.length < 3 || !seed.items.some(x => x.kind === "ai");
    const due = (_rt48sState.tries || 0) < 3 && Date.now() - (_rt48sState.last || 0) > 2 * 36e5;
    let builtNow = false;
    if (forced || ((weak || !fresh) && due)) {
      try {
        const already = !!_rt48sState.busy;
        const why = forced ? "admin-refresh" : (todayGood ? "auto-retry" : "auto");
        const job = _bb4dStart(why);
        // Anything already saved is sent now. Only the request that starts a cold build waits, and only briefly.
        if (!haveServable && !already && job) {
          let finished = false;
          const waited = job.then(() => { finished = true; }, () => { finished = true; });
          await Promise.race([waited, new Promise(r => setTimeout(r, 900))]);
          builtNow = finished;
        }
      } catch (e) {}
    }
    const nowState = _bb4dState();
    let source = "fallback", items = [], asOf = "", kind = "template", contentDay = day;
    if (nowState && nowState.day === day && nowState.items.length && nowState.kind !== "fallback") {
      source = builtNow ? "live" : (ageOf(nowState) < freshMs ? "cache" : "stale");
      items = nowState.items; asOf = nowState.generatedAt || new Date().toISOString();
      kind = nowState.items.some(x => x.kind === "ai") ? "ai" : "template"; contentDay = nowState.day || day;
    } else if (last && last.items && last.items.length) {
      source = "stale"; items = last.items; asOf = last.generatedAt || new Date(last.at || Date.now()).toISOString();
      kind = last.items.some(x => x.kind === "ai") ? "ai" : "template"; contentDay = last.day || day;
    } else {
      items = _bb4dFallback(); source = "fallback"; asOf = new Date().toISOString(); kind = "template"; contentDay = day;
    }
    const out = { date: contentDay, generatedAt: asOf, asOf: asOf, source: source, stale: source === "stale", kind: kind, items: items, v: 3 };
    if (admin && wantDiag) {
      let diagBody = { note: "no build yet today" };
      try { if (_rt48sState.diag) diagBody = _rt48sState.diag; } catch (e) {}
      out.diag = Object.assign({ tries: _rt48sState.tries || 0, forced: _rt48sState.forced || 0, busy: !!_rt48sState.busy, aiSwitch: String(process.env.ACADEMY_AI || "").toLowerCase() === "off" ? "off" : "on", source: source }, diagBody);
      return send(200, out, "no-store");
    }
    const cache = source === "live" || source === "cache" ? "private, max-age=60" : "no-store";
    return send(200, out, cache);
  } catch (e) {
    const now = new Date().toISOString();
    let day = "";
    try { day = _rt48sDay(); } catch (x) {}
    return send(200, { date: day, generatedAt: now, asOf: now, source: "fallback", stale: false, kind: "template", items: _bb4dFallback(), v: 3 }, "no-store");
  }
}
'''

out = s[:i] + HELPERS + NEW + s[j:]
out = out.replace(FETCH, FETCH_NEW, 1).replace(GEN, GEN_NEW, 1)
# The lesson build must not consult generateAi: that helper tries xAI first for 25s.
GATE = 'else if (typeof generateAi !== "function") D.ai = "no-generateAi";'
if out.count(GATE) != 1:
    die("generateAi gate matched %d times (need 1)" % out.count(GATE))
out = out.replace(GATE, 'else if (typeof generateWithAiProvider !== "function") D.ai = "no-provider";', 1)
# The start index was computed on the original string. The two earlier replaces are before academyDaily,
# but only if both needles sit before START. Confirm the function was not duplicated and the old end is gone.
if out.count("async function academyDaily(req, res) {") != 1:
    die("academyDaily count after edit is %d" % out.count("async function academyDaily(req, res) {"))
if FETCH in out or GEN in out:
    die("rss fetch or generateAi anchor still present after edit")
if out.count("// ── bb4daily ──") != 1:
    die("bb4daily marker count is %d" % out.count("// ── bb4daily ──"))
if "generateAi(" in out[out.find("// ── bb4daily ──"):out.find("const MARKET_SYSTEM")]:
    die("lesson build still calls generateAi")
def span(text, start, end, label):
    i = text.find(start)
    j = text.find(end, i + len(start)) if i >= 0 else -1
    if i < 0 or j < 0:
        die("could not bound %s" % label)
    return text[i:j]
# generateAi's provider order and the Ask stream belong to the coming Ask patch.
for label, a, b in (
    ("generateAi", "async function generateAi(options) {", "function sendAiError(res, error) {"),
    ("Ask stream", "async function bb2StreamInner(req, res) {", "function bb2StreamChat(req, res) {"),
):
    if span(s, a, b, label) != span(out, a, b, label):
        die("%s changed; leave it for the Ask patch" % label)
nodecheck(out, "server.js")
show("bb4daily after server.js", out, crlf)
print("OK bb4daily: academy-daily skips xAI, one build at a time, 900ms cold bound, last-good cache, fallback lesson, diag 403; index bump skipped (server-only); node --check passed" + (" (dry run, nothing written)" if CHECK else ""))
if CHECK:
    sys.exit(0)

bak = P + ".bb4daily.bak"
try:
    open(bak, "wb").write(open(P, "rb").read())
    open(P, "wb").write((out.replace("\n", "\r\n") if crlf else out).encode("utf-8"))
    r = subprocess.run(["node", "--check", P], capture_output=True, text=True)
    if r.returncode:
        open(P, "wb").write(open(bak, "rb").read())
        os.unlink(bak)
        print("ABORT: node --check failed after write; backup restored:", (r.stderr or "")[:400])
        sys.exit(1)
    os.unlink(bak)
except Exception as e:
    if os.path.exists(bak):
        open(P, "wb").write(open(bak, "rb").read())
        os.unlink(bak)
    print("ABORT: write failed; backup restored:", e)
    sys.exit(1)
print("written", P)
