#!/usr/bin/env python3
"""patch_rt25s.py — server.js, on production c2ecfade (rt24s rolled back). Three independent parts;
each one applies only if its exact anchor matches once, else prints SKIP for that part. Nothing at startup is awaited.
  A. rt24s: safeText() clips at a word boundary with '…' (same code as patch_rt24s.py).
  B. Recovery sender preflight is non-fatal: runs in the background, logs a warning, never blocks listen().
  C. CoinGecko 429: process-wide backoff for api.coingecko.com (15s doubling to 8 min, honours Retry-After);
     during backoff it answers a synthetic 429 locally without hitting the network. Logs once per backoff episode.
Usage: python3 patch_rt25s.py [--check] path/to/server.js
NEVER start server.js in the Replit workspace (Stripe init deletes webhooks)."""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
P = args[0] if args else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
applied, skipped = [], []
def part(name, done_marker, anchor, new):
    global s
    if done_marker in s: skipped.append(f'{name} (already applied)'); return
    n = s.count(anchor)
    if n != 1: skipped.append(f'{name} (anchor matched {n} times)'); return
    s = s.replace(anchor, new); applied.append(name)

part('A safeText word clip', 'function rt24sWordClip(',
 'function safeText(value, max) {\n  return clipped(value, max).replace(',
 '''function rt24sWordClip(value, max) {
  const t = String(value || "").trim();
  if (!(max > 1) || t.length <= max) return t;
  const cut = t.slice(0, max - 1), sp = cut.lastIndexOf(" ");
  return (sp > max * 0.6 ? cut.slice(0, sp) : cut).replace(/[\\s,;:·–—-]+$/, "") + "…";
}
function safeText(value, max) {
  return rt24sWordClip(value, max).replace(''')

part('B preflight non-fatal', 'rt25s: preflight is advisory',
 '  if (RECOVERY_SENDER_PREFLIGHT) await runRecoverySenderPreflight();\n',
 '''  // rt25s: preflight is advisory — a provider/identity outage must not stop the site from starting.
  if (RECOVERY_SENDER_PREFLIGHT) {
    void Promise.resolve().then(() => runRecoverySenderPreflight()).catch(error => {
      console.warn(JSON.stringify({ event: "recovery_sender_preflight_warning", message: String((error && error.message) || error) }));
    });
  }
''')

part('C CoinGecko 429 backoff', '__rt25sCg',
 'const http = require("http");\n',
 '''const http = require("http");
// rt25s: process-wide CoinGecko backoff. During a 429 episode, answer locally instead of re-hitting the API.
(() => {
  const orig = globalThis.fetch;
  if (typeof orig !== "function" || orig.__rt25sCg) return;
  let until = 0, step = 0;
  const wrapped = async function (input, init) {
    let u = "";
    try { u = typeof input === "string" ? input : (input && input.url) || String(input); } catch (e) {}
    if (!u.startsWith("https://api.coingecko.com/")) return orig.call(this, input, init);
    if (Date.now() < until) {
      return new Response(JSON.stringify({ status: { error_code: 429, error_message: "local backoff" } }),
        { status: 429, headers: { "content-type": "application/json", "x-dispatch-backoff": "1" } });
    }
    const r = await orig.call(this, input, init);
    if (r.status === 429) {
      step = Math.min(step + 1, 6);
      const ra = Number(r.headers.get("retry-after")) || 0;
      const ms = Math.max(ra * 1000, 15000 * 2 ** (step - 1));
      until = Date.now() + ms;
      if (step === 1) console.warn(`[rt25s] CoinGecko 429: backing off ${Math.round(ms / 1000)}s (doubling to 480s while it persists)`);
    } else if (r.ok && step) {
      console.log("[rt25s] CoinGecko recovered"); step = 0;
    }
    return r;
  };
  wrapped.__rt25sCg = true;
  globalThis.fetch = wrapped;
})();
''')

for a in applied: print('APPLY', a)
for k in skipped: print('SKIP ', k)
if not applied: print('Nothing to change; server.js left as is.'); sys.exit(0)
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: print('ABORT: node --check failed, nothing written:', r.stderr[:300]); sys.exit(1)
if any(x.startswith('B ') for x in skipped if 'already' not in x):
    print('WARNING: preflight part skipped — startup can still fail the same way. Send: grep -n -B2 -A2 "runRecoverySenderPreflight" server.js')
print('node --check passed' + (' (dry run, nothing written)' if CHECK else ''))
if not CHECK:
    open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('written', P)
