#!/usr/bin/env python3
"""patch_rt53s.py — make /api/academy-daily resilient. server.js only.

Stacks on the live rt48c handler (the block patch_rt48c.py installed) and on rt52s.
No new tables, no cron, no background worker, no Stripe, no secrets.

What changes, with the same small anchors whether or not bb2 (PR #23) is applied:
- each RSS fetch and the AI call have a hard timeout (bb2 may wrap generateAi; this calls it at request time);
- the last good lesson is kept in memory and in the temp dir, including across the London day, and is served when a refresh fails;
- if there is no last good lesson, one deterministic fallback lesson is returned;
- the handler always answers users with JSON. A thrown error becomes that fallback, not a 500;
- ?diag=1 stays admin-only and is now 403 for everyone else. ?refresh=1 still does not rebuild for non-admins;
- every user response carries asOf and source (live, cache, stale, fallback).

Refresh happens only when a request finds the saved lesson missing, older than two hours, or an admin asks.
The in-flight build is the one that request started. There is no timer and no new process.

Version: this file does not edit app.js or index.html, so it does not change ?v=chatNN.
patch_rt53.py detects the current chatNN (live is chat58 after bb2) and adds one.
bb3 may land beside this file; it is not an anchor and this file does not edit regime fit.
Requires the rt52s marker, the bb2 marker, and function hasPremiumAccess(. It does not
compare tier strings. Diag stays admin-only via the existing isAdminUser helper.
This file does not edit the rt52s 13F block, Ask/Expert, or the prefs schema.

Usage:
    python3 patch_rt53s.py --check server.js
    python3 patch_rt53s.py server.js
Refuses a second run. CRLF-safe. node --check before the write; a failed write restores the backup.
Prints md5 and line count before and after. Prints no secrets.
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
show("rt53s before server.js", s, crlf)
digest = stats(s, crlf)[0]
LIVE = "2e04b3c16f8400dc5ea211e676831b23"
if digest != LIVE:
    print("WARN md5 server.js: have %s expected live bb2+hotfix %s (anchors still decide)" % (digest, LIVE))
if "// ── rt53s:" in s:
    die("REFUSE: rt53s already applied")
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

FETCH_NEW = '    const xml = await _rt53Get(u, 4500); if (!xml) return; all.push(..._rt48sParse(xml, src)); } catch (e) {} }));'
GEN_NEW = "        const r = await _rt53Gen({ maxTokens: 1600, temperature: 0.2,"

HELPERS = r'''// ── rt53s: academy-daily ── timeouts, last-good cache, deterministic fallback. No cron. ?diag=1 is admin-only.
const _rt53LastFile = require("path").join(require("os").tmpdir(), "dispatch-academy-daily-last.json");
let _rt53Last = null;
async function _rt53Gen(opts) {
  if (typeof generateAi !== "function") { const e = new Error("no generateAi"); e.code = "NO_AI"; throw e; }
  let timer;
  const hung = new Promise((_, rej) => { timer = setTimeout(() => { const e = new Error("academy-daily AI timed out"); e.code = "TIMEOUT"; rej(e); }, 8000); });
  try { return await Promise.race([Promise.resolve().then(() => generateAi(opts)), hung]); }
  finally { clearTimeout(timer); }
}
async function _rt53Get(url, ms) {
  let timer;
  const ctrl = typeof AbortSignal !== "undefined" && typeof AbortSignal.timeout === "function" ? AbortSignal.timeout(ms) : null;
  const r = await fetch(url, { headers: { "User-Agent": "DispatchMarkets/1.0" }, redirect: "follow", signal: ctrl || undefined });
  if (!r || !r.ok) return "";
  const body = Promise.resolve().then(() => r.text());
  const cap = new Promise((_, rej) => { timer = setTimeout(() => rej(new Error("body timeout")), ms); });
  try { return String(await Promise.race([body, cap]) || "").slice(0, 600000); }
  finally { clearTimeout(timer); }
}
function _rt53Remember(items, generatedAt, kind, day) {
  try {
    const good = (items || []).filter(_rt48bValid).slice(0, 3);
    if (!good.length || kind === "fallback") return;
    _rt53Last = { v: 1, at: Date.now(), day: day || "", generatedAt: generatedAt || new Date().toISOString(), items: good, kind: kind || "template" };
    require("fs").writeFileSync(_rt53LastFile, JSON.stringify(_rt53Last));
  } catch (e) {}
}
function _rt53ReadFile(file) {
  try { return JSON.parse(require("fs").readFileSync(file, "utf8")); } catch (e) { return null; }
}
function _rt53Recall() {
  const take = (o, at) => {
    if (!o || !Array.isArray(o.items)) return null;
    const items = o.items.filter(_rt48bValid).slice(0, 3);
    if (!items.length || (o.kind === "fallback")) return null;
    const when = at || Date.parse(o.generatedAt) || Date.now();
    if (Date.now() - when > 14 * 864e5) return null;
    return { v: 1, at: when, day: o.day || "", generatedAt: o.generatedAt || new Date(when).toISOString(), items, kind: o.kind || "template" };
  };
  if (_rt53Last && _rt53Last.items && _rt53Last.items.length) return _rt53Last;
  const saved = take(_rt53ReadFile(_rt53LastFile), null);
  if (saved) { _rt53Last = saved; return saved; }
  const v3 = take(_rt53ReadFile(_rt48sFile), null);
  if (v3) { _rt53Last = v3; return v3; }
  return null;
}
function _rt53ValidState() {
  try {
    const st = _rt48sState;
    if (!st || !Array.isArray(st.items) || st.kind === "fallback") return null;
    const items = st.items.filter(_rt48bValid).slice(0, 3);
    if (!items.length) return null;
    return { day: st.day || "", generatedAt: st.generatedAt || "", kind: st.kind || "template", items };
  } catch (e) { return null; }
}
function _rt53FallbackItems() {
  try {
    const H = { h: "The Federal Reserve cuts rates in a surprise move", src: "Dispatch Academy", link: "" };
    const e = "Gold often rises on a surprise Fed cut: lower rates reduce the cost of holding a metal that pays no interest, and the dollar tends to weaken.";
    const it = _rt48bItem(H, "gold", "up", e, "template");
    if (_rt48bValid(it)) return [it];
  } catch (e) {}
  return [{ h: "The Federal Reserve cuts rates in a surprise move", src: "Dispatch Academy", link: "", asset: "gold", dir: "up", q: "If this news is a surprise to markets, what is the typical first reaction in the gold price?", o: ["Up", "Down", "Little change"], a: 0, e: "Gold often rises on a surprise Fed cut: lower rates reduce the cost of holding a metal that pays no interest, and the dollar tends to weaken.", kind: "template" }];
}
async function _rt53Who(req) {
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
          const fb = _rt53FallbackItems();
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
      const u = await _rt53Who(req);
      try { admin = !!(u && typeof isAdminUser === "function" && isAdminUser(u)); } catch (e) { admin = false; }
      if (diag && !admin) return send(403, { error: "Administrator access required." }, "no-store");
      if (admin && refresh && (_rt48sState.forced || 0) < 6) forced = true;
    }
    try { _rt48sLoad(); } catch (e) {}
    const day = _rt48sDay();
    const seed = _rt53ValidState();
    if (seed && seed.items.length) _rt53Remember(seed.items, seed.generatedAt, seed.kind, seed.day);
    const freshMs = 2 * 60 * 60 * 1000;
    const ageOf = (st) => { const t = Date.parse(st && st.generatedAt || ""); return isFinite(t) ? Date.now() - t : Infinity; };
    const fresh = !!(seed && seed.day === day && seed.items.length && ageOf(seed) < freshMs);
    let builtNow = false;
    if (forced || !fresh) {
      try {
        if (!_rt48sState.busy) {
          if (forced) { _rt48sState.forced = (_rt48sState.forced || 0) + 1; _rt48sState.busy = _rt48sBuild("admin-refresh").finally(() => { _rt48sState.busy = null; }); }
          else {
            const weak = !seed || seed.day !== day || seed.items.length < 3 || !seed.items.some(x => x.kind === "ai");
            const due = (_rt48sState.tries || 0) < 3 && Date.now() - (_rt48sState.last || 0) > 2 * 36e5;
            if (weak && due) _rt48sState.busy = _rt48sBuild(seed && seed.items.length ? "auto-retry" : "auto").finally(() => { _rt48sState.busy = null; });
          }
        }
        if (_rt48sState.busy) {
          let finished = false;
          const waited = _rt48sState.busy.then(() => { finished = true; }, () => { finished = true; });
          await Promise.race([waited, new Promise(r => setTimeout(r, forced ? 12000 : 6000))]);
          builtNow = finished;
        }
      } catch (e) {}
      const built = _rt53ValidState();
      if (built && built.items.length) _rt53Remember(built.items, built.generatedAt, built.kind, built.day);
    }
    const nowState = _rt53ValidState();
    const last = _rt53Recall();
    let source = "fallback", items = [], asOf = "", kind = "template", contentDay = day;
    if (nowState && nowState.day === day && nowState.items.length && nowState.kind !== "fallback") {
      source = builtNow ? "live" : (ageOf(nowState) < freshMs ? "cache" : "stale");
      items = nowState.items; asOf = nowState.generatedAt || new Date().toISOString();
      kind = nowState.items.some(x => x.kind === "ai") ? "ai" : "template"; contentDay = nowState.day || day;
    } else if (last && last.items && last.items.length) {
      source = "stale"; items = last.items; asOf = last.generatedAt || new Date(last.at || Date.now()).toISOString();
      kind = last.items.some(x => x.kind === "ai") ? "ai" : "template"; contentDay = last.day || day;
    } else {
      items = _rt53FallbackItems(); source = "fallback"; asOf = new Date().toISOString(); kind = "template"; contentDay = day;
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
    return send(200, { date: day, generatedAt: now, asOf: now, source: "fallback", stale: false, kind: "template", items: _rt53FallbackItems(), v: 3 }, "no-store");
  }
}
'''

out = s[:i] + HELPERS + NEW + s[j:]
out = out.replace(FETCH, FETCH_NEW, 1).replace(GEN, GEN_NEW, 1)
# The start index was computed on the original string. The two earlier replaces are before academyDaily,
# but only if both needles sit before START. Confirm the function was not duplicated and the old end is gone.
if out.count("async function academyDaily(req, res) {") != 1:
    die("academyDaily count after edit is %d" % out.count("async function academyDaily(req, res) {"))
if FETCH in out:
    die("rss fetch anchor still present after edit")
if out.count("// ── rt53s:") != 1:
    die("rt53s marker count is %d" % out.count("// ── rt53s:"))
nodecheck(out, "server.js")
show("rt53s after server.js", out, crlf)
print("OK rt53s: academy-daily timeouts, last-good cache, fallback lesson, diag 403; index bump skipped (server-only); node --check passed" + (" (dry run, nothing written)" if CHECK else ""))
if CHECK:
    sys.exit(0)

bak = P + ".rt53sbak"
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
