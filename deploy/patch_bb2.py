#!/usr/bin/env python3
"""patch_bb2.py — Ask/Expert on the post-rt52 client (chatNN -> chatNN+1, NN >= 57).

First streamed tokens under 3s, inline citations for sources that were actually
fed in, and server-side peer comparisons (the MU 11.8x vs WDC 12.3x bug).

Streaming trade-off: the first SSE event is the deterministic comparison block,
written after auth and at most a 900ms stale-while-revalidate read, before the
model is called. Model text is flushed as it arrives unless the unflushed buffer
contains a comparison word (higher/lower/above/below/cheaper/richer/premium/
discount/...). That buffer is held to the next sentence, checked against the
precomputed direction, and replaced with the templated sentence when it
contradicts the data. A replacement that repeats the block already shown is not
flushed, so a wrong "higher" never appears. Holding the whole answer until the
model finished would miss the 3s goal; holding only comparison sentences delays
that one sentence, not the first token.

Peer valuations refresh lazily from Yahoo's keyless quote endpoint when the
in-memory snapshot is older than 24h or older than the latest US cash close.
No cron, no background worker, no new table. The as-of time is the quote's
market time and is printed in the citation. Trailing P/E (TTM) and forward P/E
are labelled and never compared with each other.

xAI is not on the streaming path. During a non-stream chat the xAI proxy timeout
is capped at 800ms so an out-of-credits provider is skipped quickly. OpenAI
gpt-4o-mini is tried first, then Gemini 2.5 Flash. If neither key is configured,
the request falls through to the existing JSON handler.

Streaming allows the same people as the JSON handler: currentUser, then
hasPremiumAccess (premium tier or admin). It does not re-check tier itself.

Stacks on rt52 + rt52s. rt53 (home freeze and the macro grid) may already
have run and bumped the cache buster; this patch does not require its marker.
Refuses unless these are present:
  app.js      // ── rt52 ──
  app.js      function _rt52Render13f(
  server.js   // ── rt52s: 13F v2 ──
  server.js   async function institutional13fV2(
  index.html  app.js?v=chatNN with NN >= 57, exactly once
Then the index bust becomes chatNN+1. On rt52 alone that is chat57 -> chat58.
On rt52 then rt53 (PR #25, which takes chat57 -> chat58) it is chat58 -> chat59.
Already-applied (// ── bb2 ──) exits 0. A missing rt52 marker, or a bust below
chat57, exits 1 and writes nothing.

Usage: python3 patch_bb2.py [--check] <dir containing app.js, index.html, server.js>
CRLF-safe. node --check runs before anything is written; a later failure restores backups.
Prints md5 and line count of each file before and after. EXPECTED_MD5 is a warning only.
"""
import hashlib, os, re, sys, subprocess, tempfile

# Live no-rt53 base (post rt52, rt52s, and rt52ops). Paste a newer set here if
# the files move. A blank value skips the warning for that file. Mismatch warns
# and does not abort, so an rt53 base (chat58) still applies and becomes chat59.
EXPECTED_MD5 = {
    "app.js": "45107b5b78039f675ffd94646ce4d309",
    "index.html": "87ee1667f8e6deef4c449ff9a61cce8d",
    "server.js": "4e8c340439b57d202b6c13711cc7a338",
}

CHECK = "--check" in sys.argv
args = [a for a in sys.argv[1:] if a != "--check"]
D = args[0] if args else "."
APP, IDX, SRV = os.path.join(D, "app.js"), os.path.join(D, "index.html"), os.path.join(D, "server.js")

def load(p):
    b = open(p, "rb").read()
    return b.decode("utf-8").replace("\r\n", "\n"), b"\r\n" in b

def die(m):
    print("ABORT (nothing written):", m)
    sys.exit(1)

def show(phase, path, data=None):
    raw = open(path, "rb").read() if data is None else data
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    name = os.path.basename(path)
    digest = hashlib.md5(raw).hexdigest()
    print("bb2 %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
    return digest

def encode(text, use_crlf):
    return (text.replace("\n", "\r\n") if use_crlf else text).encode("utf-8")

def nodecheck(src, label):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as t:
        t.write(src)
        tmp = t.name
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    os.unlink(tmp)
    if r.returncode:
        die("node --check failed for %s: %s" % (label, r.stderr[:500]))

EN, EL = "\u2013", "\u2026"
s, crlf = load(APP)
h, hcrlf = load(IDX)
v, vcrlf = load(SRV)

for path in (APP, IDX, SRV):
    digest = show("before", path)
    expect = EXPECTED_MD5.get(os.path.basename(path)) or ""
    if expect and digest != expect:
        print("WARN md5 %s: have %s expected %s (anchors still decide)" % (os.path.basename(path), digest, expect))

if "// \u2500\u2500 bb2 \u2500\u2500" in s or "// \u2500\u2500 bb2 \u2500\u2500" in v:
    print("REFUSE: bb2 already applied")
    sys.exit(0)

rt52_miss = []
if "// \u2500\u2500 rt52 \u2500\u2500" not in s:
    rt52_miss.append("app.js marker missing: // ── rt52 ──")
if "function _rt52Render13f(" not in s:
    rt52_miss.append("app.js marker missing: function _rt52Render13f(")
if "// \u2500\u2500 rt52s: 13F v2 \u2500\u2500" not in v:
    rt52_miss.append("server.js marker missing: // ── rt52s: 13F v2 ──")
if "async function institutional13fV2(" not in v:
    rt52_miss.append("server.js marker missing: async function institutional13fV2(")
chat_n = None
chat_hits = re.findall(r'app\.js\?v=chat(\d+)"', h)
if len(chat_hits) != 1:
    rt52_miss.append('index.html marker missing: app.js?v=chatNN" (found %d)' % len(chat_hits))
else:
    chat_n = int(chat_hits[0])
    if chat_n < 57:
        rt52_miss.append("index.html is chat%d; need chat57 or later" % chat_n)
if rt52_miss:
    print("REFUSE: rt52/rt52s base not detected (nothing written)")
    for item in rt52_miss:
        print("REFUSE:", item)
    sys.exit(1)

OLD_SEND = r'''async function sendChatMessage(retryText = null) {
  if (_chatLoad) return;
  if (!_isPremium()) { _showLoginGate("Dispatch Expert"); return; }
  const inp = document.getElementById("chatInp");
  const text = (retryText ?? inp?.value ?? "").trim();
  if (!text) return;
  if (retryText === null) {
    inp.value = "";
    _chatMsgs.push({ role: "user", content: text });
  }
  _chatLoad = true;
  _chatStartStatus();
  _renderChatMsgs();
  const btn = document.getElementById("chatSend");
  if (btn) btn.disabled = true;
  const tickers = _rt40Tks(text);
  try {
    await Promise.race([Promise.all(_rt38Peers(tickers, text).map(tk => _rt40Fin(tk))), new Promise(r => setTimeout(r, 3000))]);
    await Promise.race([Promise.all(tickers.slice(0, 3).map(tk => _prefetchLensData(tk))), new Promise(r => setTimeout(r, 4000))]);
    const res = await fetch("/api/chat", {
      signal: AbortSignal.timeout(75000),
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: _rt36Msgs(_chatMsgs.map(m => ({ role: m.role, content: m.content })), tickers),
        context: (_rt38PeerCtx(tickers, text).trim() ? _rt38PeerCtx(tickers, text).trim() + "\n\n" : "") + _buildChatContext(),
        tickers,
        knownTickers: _chatKnownTickers(),
        hints: _rt37Hints(tickers)
      })
    });
    const data = await res.json().catch(() => ({}));
    if (res.status === 401) {
      if (retryText === null) _chatMsgs.pop();
      _showLoginGate("Dispatch Expert");
      return;
    }
    if (!res.ok) {
      _chatMsgs.push({ role: "assistant", kind: "ai-unavailable", content: CHAT_AI_UNAVAILABLE, retryable: true });
      return;
    }
    if (typeof data.reply !== "string" || !data.reply.trim()) {
      _chatMsgs.push({ role: "assistant", kind: "empty-answer", content: CHAT_EMPTY_ANSWER, retryable: true });
      return;
    }
    _chatMsgs.push({
      role: "assistant",
      content: _rt37Reply(data.reply, tickers),
      structured: _rt38St(data.structured, tickers),
      meta: data.meta || null
    });
    _persistChat();
  } catch (e) {
    _chatMsgs.push({ role: "assistant", kind: "ai-unavailable", content: CHAT_AI_UNAVAILABLE, retryable: true });
  } finally {
    _chatLoad = false;
    _chatStopStatus();
    if (btn) btn.disabled = false;
    _renderChatMsgs();
  }
}'''

NEW_SEND = r'''async function sendChatMessage(retryText = null) {
  if (_chatLoad) return;
  if (!_isPremium()) { _showLoginGate("Dispatch Expert"); return; }
  const inp = document.getElementById("chatInp");
  const text = (retryText ?? inp?.value ?? "").trim();
  if (!text) return;
  if (retryText === null) {
    inp.value = "";
    _chatMsgs.push({ role: "user", content: text });
  }
  _chatLoad = true;
  _chatStartStatus();
  _renderChatMsgs();
  const btn = document.getElementById("chatSend");
  if (btn) btn.disabled = true;
  const tickers = _rt40Tks(text);
  let acc = "";
  let streamed = false;
  const payload = () => ({
    messages: _rt36Msgs(_chatMsgs.filter(m => !m._bb2).map(m => ({ role: m.role, content: m.content })), tickers),
    context: (_rt38PeerCtx(tickers, text).trim() ? _rt38PeerCtx(tickers, text).trim() + "\n\n" : "") + _buildChatContext(),
    tickers,
    knownTickers: _chatKnownTickers(),
    hints: _rt37Hints(tickers),
    sources: (typeof _bb2Sources === "function" ? _bb2Sources(tickers) : [])
  });
  const note = (chunk) => {
    if (!chunk) return;
    acc += chunk;
    streamed = true;
    const last = _chatMsgs[_chatMsgs.length - 1];
    if (!last || last.role !== "assistant" || !last._bb2) _chatMsgs.push({ role: "assistant", content: acc, _bb2: true });
    else last.content = acc;
    _renderChatMsgs();
  };
  try {
    try {
      const peers = typeof _rt38Peers === "function" ? _rt38Peers(tickers, text) : [];
      const jobs = [];
      if (typeof _rt40Fin === "function") peers.forEach(tk => jobs.push(_rt40Fin(tk)));
      if (typeof _prefetchLensData === "function") tickers.slice(0, 3).forEach(tk => jobs.push(_prefetchLensData(tk)));
      if (jobs.length) await Promise.race([Promise.all(jobs), new Promise(r => setTimeout(r, 200))]);
    } catch (e) {}
    const body = payload();
    let res = await fetch("/api/chat", {
      signal: AbortSignal.timeout(75000),
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "text/event-stream", "X-Dispatch-Stream": "1" },
      body: JSON.stringify(body)
    });
    if (res.status === 401) {
      if (retryText === null && _chatMsgs.length && _chatMsgs[_chatMsgs.length - 1].role === "user") _chatMsgs.pop();
      _showLoginGate("Dispatch Expert");
      return;
    }
    const ctype = (res.headers.get("content-type") || "");
    const canStream = res.ok && ctype.indexOf("text/event-stream") >= 0 && res.body && typeof res.body.getReader === "function";
    if (!res.ok) {
      _chatMsgs.push({ role: "assistant", kind: "ai-unavailable", content: CHAT_AI_UNAVAILABLE, retryable: true });
      return;
    }
    if (!canStream) {
      const data = await res.json().catch(() => ({}));
      _bb2CommitJson(data, tickers);
      return;
    }
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = "", final = null, broken = false;
    try {
      while (true) {
        const step = await reader.read();
        if (step.done) break;
        buf += dec.decode(step.value, { stream: true });
        const parts = buf.split("\n\n");
        buf = parts.pop();
        parts.forEach(part => {
          const data = part.split("\n").filter(l => l.indexOf("data:") === 0).map(l => l.slice(5).trim()).join("\n");
          if (!data) return;
          let ev; try { ev = JSON.parse(data); } catch (e) { return; }
          if (ev.t) note(ev.t);
          if (ev.done) final = ev;
          if (ev.error && !acc) broken = true;
        });
      }
    } catch (e) { broken = !streamed; }
    if (!streamed && (broken || !final)) {
      const res2 = await fetch("/api/chat", {
        signal: AbortSignal.timeout(75000),
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      if (res2.status === 401) {
        if (retryText === null && _chatMsgs.length && _chatMsgs[_chatMsgs.length - 1].role === "user") _chatMsgs.pop();
        _showLoginGate("Dispatch Expert");
        return;
      }
      const data = await res2.json().catch(() => ({}));
      if (!res2.ok) {
        _chatMsgs.push({ role: "assistant", kind: "ai-unavailable", content: CHAT_AI_UNAVAILABLE, retryable: true });
        return;
      }
      _bb2CommitJson(data, tickers);
      return;
    }
    const reply = final && typeof final.reply === "string" && final.reply.trim() ? final.reply : acc;
    if (!String(reply || "").trim()) {
      if (_chatMsgs.length && _chatMsgs[_chatMsgs.length - 1]._bb2) _chatMsgs.pop();
      _chatMsgs.push({ role: "assistant", kind: "empty-answer", content: CHAT_EMPTY_ANSWER, retryable: true });
      return;
    }
    if (_chatMsgs.length && _chatMsgs[_chatMsgs.length - 1]._bb2) _chatMsgs.pop();
    _chatMsgs.push({
      role: "assistant",
      content: _rt37Reply(reply, tickers),
      structured: _rt38St(final && final.structured, tickers),
      meta: (final && final.meta) || null
    });
    _persistChat();
  } catch (e) {
    if (!streamed) _chatMsgs.push({ role: "assistant", kind: "ai-unavailable", content: CHAT_AI_UNAVAILABLE, retryable: true });
  } finally {
    _chatLoad = false;
    _chatStopStatus();
    if (btn) btn.disabled = false;
    _renderChatMsgs();
  }
}'''

OLD_ROW = r"return v ? `${t}: P/E ${f(v.pe)} · forward P/E ${f(v.forwardPe)} · market cap ${_rt33Mc(v.marketCap)}` : `${t}: valuation not available`;"
NEW_ROW = r"return v ? `${t}: trailing P/E (TTM) ${f(v.pe)} · forward P/E ${f(v.forwardPe)} · market cap ${_rt33Mc(v.marketCap)}` : `${t}: valuation not available`;"
OLD_ROW2 = r"return v ? `${t} P/E ${f(v.pe)} · fwd P/E ${f(v.forwardPe)} · mkt cap ${_rt33Mc(v.marketCap)}` : `${t} valuation unavailable`;"
NEW_ROW2 = r"return v ? `${t}: trailing P/E (TTM) ${f(v.pe)} · forward P/E ${f(v.forwardPe)} · mkt cap ${_rt33Mc(v.marketCap)}` : `${t}: valuation unavailable`;"
OLD_PEER_NOTE = "Use these figures when comparing valuation; do not substitute an index or ETF for a peer:"
NEW_PEER_NOTE = "Trailing P/E (TTM) and forward P/E are different bases and are not compared with each other. Use these figures when comparing valuation; do not substitute an index or ETF for a peer:"
copies = [
    ("Synthesising view (usually 20" + EN + "60 seconds)" + EL, "Synthesising view" + EL),
    ("Typical response: 20" + EN + "60 seconds.", "Typical response: first words within a few seconds."),
    ("typically 20" + EN + "60s", "streams as it writes"),
]
# Small signatures checked on the live server (4e8c3404, post rt52s and rt52ops).
# Checked before any edit so a miss names every anchor and leaves the tree untouched.
SERVER_ANCHORS = [
    "async function generateAi(",
    "async function handle(",
    "function json(",
    "async function currentUser(",
    "function hasPremiumAccess(",
    "async function readBody(",
    '"/api/chat"',
    "return json(res, 200, await institutional13fV2());",
]
miss = []
def need_one(hay, needle, label):
    n = hay.count(needle)
    if n != 1:
        miss.append("%s matched %d times" % (label, n))
need_one(s, OLD_SEND, "app.js anchor sendChatMessage")
need_one(s, OLD_ROW, "app.js anchor live peer row")
need_one(s, OLD_ROW2, "app.js anchor earlier peer row")
need_one(s, OLD_PEER_NOTE, "app.js anchor peer note")
for old, _new in copies:
    need_one(s, old, "app.js anchor %r" % old)
for anchor in SERVER_ANCHORS:
    if anchor not in v:
        miss.append("server.js anchor missing: %s" % anchor)
if miss:
    print("ABORT (nothing written):")
    for item in miss:
        print("ABORT:", item)
    sys.exit(1)

s = s.replace(OLD_SEND, NEW_SEND, 1)
print("APPLY sendChatMessage stream + 200ms prefetch cap")
s = s.replace(OLD_ROW, NEW_ROW, 1)
s = s.replace(OLD_ROW2, NEW_ROW2, 1)
s = s.replace(OLD_PEER_NOTE, NEW_PEER_NOTE, 1)
print("APPLY trailing P/E (TTM) labels in peer context")
for old, new in copies:
    s = s.replace(old, new, 1)
print("APPLY chat timing copy")

CLIENT = r'''
// ── bb2 ── Ask streams its answer. Citations link to the sources that were actually supplied.
function _bb2Sources(tickers) {
  const out = [];
  try {
    (typeof NEWS !== "undefined" ? NEWS : []).slice(0, 6).forEach(n => {
      if (!n || !(n.src || n.x)) return;
      out.push({ name: String(n.src || "News").slice(0, 80), link: typeof n.link === "string" ? n.link : "", asOf: n.ts ? new Date(n.ts).toISOString() : "", detail: String(n.x || "").slice(0, 140) });
    });
    (tickers || []).slice(0, 6).forEach(tk => {
      const px = typeof livePx === "function" ? livePx(tk) : null;
      if (px == null) return;
      let name = "Price feed";
      try { if (typeof liveQuoteName !== "undefined" && liveQuoteName[tk]) name = liveQuoteName[tk]; } catch (e) {}
      const ts = (typeof liveQuoteTs !== "undefined" && liveQuoteTs[tk]) || (typeof priceLastFetch !== "undefined" && priceLastFetch ? priceLastFetch.getTime() : 0);
      out.push({ name: String(name).slice(0, 80), link: "", asOf: ts ? new Date(ts).toISOString() : "", detail: tk + " price" });
    });
  } catch (e) {}
  return out.slice(0, 8);
}
function _bb2CommitJson(data, tickers) {
  if (_chatMsgs.length && _chatMsgs[_chatMsgs.length - 1]._bb2) _chatMsgs.pop();
  if (!data || typeof data.reply !== "string" || !data.reply.trim()) {
    _chatMsgs.push({ role: "assistant", kind: "empty-answer", content: CHAT_EMPTY_ANSWER, retryable: true });
    return;
  }
  _chatMsgs.push({ role: "assistant", content: _rt37Reply(data.reply, tickers), structured: _rt38St(data.structured, tickers), meta: data.meta || null });
  _persistChat();
}
{
  const _bb2Md = _chatMd;
  _chatMd = function (text) {
    let html = _bb2Md.apply(this, arguments);
    try {
      html = html.replace(/(https?:\/\/[^\s<]+)/g, function (u) {
        const core = u.replace(/[),.;]+$/g, "");
        return '<a class="bb2-src" href="' + core + '" target="_blank" rel="noopener noreferrer">' + core + "</a>" + u.slice(core.length);
      });
      html = html.replace(/\[(\d+)\]/g, '<sup class="bb2-cite">[$1]</sup>');
    } catch (e) {}
    return html;
  };
  const _bb2Rc = _renderChatMsgs;
  _renderChatMsgs = function () {
    const was = _chatLoad;
    try {
      const last = _chatMsgs[_chatMsgs.length - 1];
      if (was && last && last._bb2 && last.content) _chatLoad = false;
      return _bb2Rc.apply(this, arguments);
    } finally { _chatLoad = was; }
  };
}
(() => { try { const st = document.createElement("style"); st.textContent = ".bb2-src{color:inherit;text-decoration:underline;text-underline-offset:2px}.bb2-cite{font-size:.75em;opacity:.85}"; document.head.appendChild(st); } catch (e) {} })();
'''
s = s.rstrip("\n") + "\n" + CLIENT
print("APPLY client citation helpers")

bust_from, bust_to = "chat%d" % chat_n, "chat%d" % (chat_n + 1)
h = h.replace('app.js?v=%s"' % bust_from, 'app.js?v=%s"' % bust_to, 1)
print("APPLY index %s -> %s" % (bust_from, bust_to))

SERVER = r'''
// ── bb2 ── Ask: stream a precomputed peer comparison first, then validate comparison words per sentence.
// Yahoo valuations refresh on request (24h or older than the latest US cash close). In-memory only. No cron.
// BB2_JS
var bb2Als;
try { bb2Als = new (require("async_hooks").AsyncLocalStorage)(); }
catch (e) { bb2Als = { run: function (_s, fn) { return fn(); }, getStore: function () { return null; } }; }
var bb2Mem = { crumb: "", cookie: "", crumbAt: 0, vals: new Map(), inflight: null };
var BB2_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36";
var BB2_PEERS = {
  MU: ["NVDA", "AVGO", "AMD", "WDC", "INTC"], NVDA: ["AMD", "AVGO", "INTC", "MU", "TSM"], AMD: ["NVDA", "INTC", "AVGO", "MU", "QCOM"],
  AVGO: ["NVDA", "AMD", "QCOM", "MRVL", "MU"], INTC: ["AMD", "NVDA", "TSM", "MU", "QCOM"], TSM: ["NVDA", "INTC", "AMD", "AVGO"], QCOM: ["AVGO", "AMD", "INTC", "NVDA"],
  AAPL: ["MSFT", "GOOGL", "AMZN", "META"], MSFT: ["AAPL", "GOOGL", "AMZN", "ORCL"], GOOGL: ["META", "MSFT", "AMZN", "AAPL"], META: ["GOOGL", "SNAP", "PINS", "MSFT"],
  AMZN: ["WMT", "MSFT", "GOOGL", "COST"], TSLA: ["GM", "F", "RIVN", "TM"], T: ["VZ", "TMUS", "CMCSA"], VZ: ["T", "TMUS", "CMCSA"],
  XOM: ["CVX", "COP", "SHEL", "BP"], CVX: ["XOM", "COP", "SHEL", "BP"], JPM: ["BAC", "WFC", "C", "GS"], BAC: ["JPM", "WFC", "C"], UNH: ["CVS", "CI", "ELV", "HUM"]
};
var BB2_CMP = /\b(higher|lower|above|below|cheaper|richer|premium|discount|more expensive|less expensive)\b/i;
function bb2Clip(s, n) { s = String(s || ""); return s.length > n ? s.slice(0, n) : s; }
function bb2Rnd(n) { return Math.round(Number(n) * 10) / 10; }
function bb2Esc(s) { return String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
function bb2Num(x) {
  if (x == null || x === "") return null;
  if (typeof x === "number") return Number.isFinite(x) ? x : null;
  if (typeof x === "object") return bb2Num(x.raw != null ? x.raw : x.fmt);
  const n = Number(x);
  return Number.isFinite(n) ? n : null;
}
function bb2NyParts(ms) {
  const fmt = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23", weekday: "short" });
  const o = {};
  fmt.formatToParts(new Date(ms)).forEach(p => { o[p.type] = p.value; });
  return o;
}
function bb2NyTime(year, month, day, hour, minute) {
  let utc = Date.UTC(+year, +month - 1, +day, +hour + 5, +minute);
  for (let i = 0; i < 4; i++) {
    const p = bb2NyParts(utc);
    const got = Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour, +p.minute);
    const want = Date.UTC(+year, +month - 1, +day, +hour, +minute);
    if (got === want) return utc;
    utc += want - got;
  }
  return utc;
}
function bb2LastCloseMs(nowMs) {
  const now = nowMs || Date.now();
  const wdMap = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };
  for (let back = 0; back < 8; back++) {
    const p = bb2NyParts(now - back * 864e5);
    const close = bb2NyTime(p.year, p.month, p.day, 16, 0);
    if (close <= now && wdMap[bb2NyParts(close).weekday] >= 1 && wdMap[bb2NyParts(close).weekday] <= 5) return close;
  }
  return now - 864e5;
}
function bb2AsOf(ms) {
  if (!ms) return "";
  return new Date(ms).toISOString().slice(0, 16).replace("T", " ") + " UTC";
}
function bb2Fresh(hit, now) {
  if (!hit || !hit.at || !hit.v) return false;
  const t = now || Date.now();
  if (t - hit.at > 24 * 3600e3) return false;
  const close = bb2LastCloseMs(t);
  if (hit.at < close) return false;
  if (hit.v.marketMs && hit.v.marketMs + 5 * 60e3 < close) return false;
  return true;
}
function bb2Hdr(cookie) {
  const h = { "User-Agent": BB2_UA };
  if (cookie) h.Cookie = cookie;
  return h;
}
function bb2Fetch(url, opts) {
  const f = globalThis.fetch;
  if (typeof f !== "function") return Promise.reject(new Error("no fetch"));
  return f(url, opts);
}
function bb2IsXai(url) {
  try {
    const u = new URL(String(url && url.url ? url.url : url), "http://localhost");
    return /(^|\.)x\.ai$/i.test(u.hostname);
  } catch (e) { return /api\.x\.ai|\/\/x\.ai/i.test(String(url)); }
}
async function bb2Crumb() {
  if (bb2Mem.crumb && Date.now() - bb2Mem.crumbAt < 30 * 60e3) return bb2Mem;
  const first = await bb2Fetch("https://fc.yahoo.com", { headers: { "User-Agent": BB2_UA }, redirect: "manual" });
  let cookie = "";
  try {
    if (first && first.headers && typeof first.headers.getSetCookie === "function") cookie = first.headers.getSetCookie().map(x => String(x).split(";")[0]).filter(Boolean).join("; ");
    else if (first && first.headers && first.headers.get) {
      const m = String(first.headers.get("set-cookie") || "").match(/A3=[^;]+/);
      if (m) cookie = m[0];
    }
  } catch (e) {}
  const cr = await bb2Fetch("https://query1.finance.yahoo.com/v1/test/getcrumb", { headers: bb2Hdr(cookie) });
  const crumb = cr && cr.ok ? String(await cr.text()).trim() : "";
  if (!crumb || crumb.length > 64 || /[<\s]/.test(crumb)) throw new Error("yahoo crumb");
  bb2Mem.crumb = crumb; bb2Mem.cookie = cookie; bb2Mem.crumbAt = Date.now();
  return bb2Mem;
}
function bb2StoreQuote(row, at) {
  if (!row || !row.symbol) return;
  const t = bb2Num(row.regularMarketTime);
  const marketMs = t ? (t > 1e12 ? t : t * 1000) : 0;
  bb2Mem.vals.set(String(row.symbol).toUpperCase(), { at: at || Date.now(), v: {
    trailing: bb2Num(row.trailingPE), forward: bb2Num(row.forwardPE), price: bb2Num(row.regularMarketPrice), mcap: bb2Num(row.marketCap),
    marketMs: marketMs, asOf: marketMs ? bb2AsOf(marketMs) : ""
  } });
}
async function bb2Summary(sym) {
  const gate = await bb2Crumb();
  const url = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/" + encodeURIComponent(sym) + "?modules=price,summaryDetail,defaultKeyStatistics&crumb=" + encodeURIComponent(gate.crumb);
  const res = await bb2Fetch(url, { headers: bb2Hdr(gate.cookie), signal: AbortSignal.timeout(2500) });
  if (!res || !res.ok) return null;
  const j = await res.json();
  const r = j && j.quoteSummary && j.quoteSummary.result && j.quoteSummary.result[0];
  if (!r) return null;
  const t = bb2Num(r.price && r.price.regularMarketTime);
  const marketMs = t ? (t > 1e12 ? t : t * 1000) : 0;
  return {
    trailing: bb2Num(r.summaryDetail && r.summaryDetail.trailingPE) != null ? bb2Num(r.summaryDetail && r.summaryDetail.trailingPE) : bb2Num(r.defaultKeyStatistics && r.defaultKeyStatistics.trailingPE),
    forward: bb2Num(r.defaultKeyStatistics && r.defaultKeyStatistics.forwardPE) != null ? bb2Num(r.defaultKeyStatistics && r.defaultKeyStatistics.forwardPE) : bb2Num(r.summaryDetail && r.summaryDetail.forwardPE),
    price: bb2Num(r.price && r.price.regularMarketPrice), mcap: bb2Num(r.price && r.price.marketCap), marketMs: marketMs, asOf: marketMs ? bb2AsOf(marketMs) : ""
  };
}
async function bb2Refresh(syms) {
  const list = [...new Set((syms || []).map(s => String(s || "").toUpperCase()).filter(Boolean))];
  if (!list.length) return;
  try {
    const gate = await bb2Crumb();
    const url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=" + encodeURIComponent(list.join(",")) + "&crumb=" + encodeURIComponent(gate.crumb);
    const res = await bb2Fetch(url, { headers: bb2Hdr(gate.cookie), signal: AbortSignal.timeout(2500) });
    if (res && res.ok) {
      const j = await res.json();
      const rows = (j && j.quoteResponse && j.quoteResponse.result) || [];
      const at = Date.now();
      rows.forEach(row => bb2StoreQuote(row, at));
    }
  } catch (e) {}
  for (const sym of list) {
    const hit = bb2Mem.vals.get(sym);
    if (hit && hit.v && (hit.v.trailing > 0 || hit.v.forward > 0)) continue;
    try { const v = await bb2Summary(sym); if (v) bb2Mem.vals.set(sym, { at: Date.now(), v: v }); } catch (e) {}
  }
}
async function bb2EnsureVals(syms) {
  const now = Date.now();
  const missing = (syms || []).filter(s => !bb2Fresh(bb2Mem.vals.get(s), now));
  if (missing.length) {
    const job = bb2Refresh(missing);
    job.catch(() => {});
    await Promise.race([job, new Promise(r => setTimeout(r, 900))]);
  }
  const out = {};
  (syms || []).forEach(s => { const hit = bb2Mem.vals.get(s); if (hit && hit.v) out[s] = hit.v; });
  return out;
}
function bb2One(aSym, bSym, aVal, bVal, basis) {
  const label = basis === "trailing" ? "trailing P/E (TTM)" : "forward P/E";
  const key = basis === "trailing" ? "trailing" : "forward";
  const av = aVal && aVal[key], bv = bVal && bVal[key];
  if (!(av > 0) || !(bv > 0)) {
    if ((av > 0) || (bv > 0)) {
      const who = av > 0 ? bSym : aSym;
      return { a: aSym, b: bSym, basis: basis, dir: "missing", sentence: who + " " + label + " was not reported, so " + aSym + " and " + bSym + " are not compared on " + label + "." };
    }
    return null;
  }
  const ra = bb2Rnd(av), rb = bb2Rnd(bv);
  const delta = bb2Rnd(Math.abs(ra - rb));
  const pct = rb ? Math.round((Math.abs(ra - rb) / rb) * 1000) / 10 : 0;
  const dir = Math.abs(ra - rb) < 0.05 ? "in line" : (ra < rb ? "lower" : "higher");
  const sentence = dir === "in line"
    ? (aSym + " " + label + " " + ra.toFixed(1) + "x is in line with " + bSym + " " + label + " " + rb.toFixed(1) + "x.")
    : (aSym + " " + label + " " + ra.toFixed(1) + "x is " + dir + " than " + bSym + " " + label + " " + rb.toFixed(1) + "x by " + delta.toFixed(1) + "x (" + pct.toFixed(1) + "%).");
  return { a: aSym, b: bSym, basis: basis, dir: dir, va: ra, vb: rb, abs: delta, pct: pct, label: label, sentence: sentence };
}
function bb2BuildFacts(base, vals) {
  const peers = [base].concat(BB2_PEERS[base] || []).slice(0, 6);
  const rows = peers.map(sym => {
    const v = vals && vals[sym];
    if (!v) return sym + ": trailing P/E (TTM) not reported | forward P/E not reported";
    const t = v.trailing > 0 ? bb2Rnd(v.trailing).toFixed(1) + "x" : "not reported";
    const f = v.forward > 0 ? bb2Rnd(v.forward).toFixed(1) + "x" : "not reported";
    const px = v.price > 0 ? " | price $" + Number(v.price).toFixed(2) : "";
    const asOf = v.asOf ? " | as of " + v.asOf : "";
    return sym + ": trailing P/E (TTM) " + t + " | forward P/E " + f + px + asOf;
  });
  const facts = [];
  const a = vals && vals[base];
  if (a) peers.slice(1).forEach(sym => {
    ["trailing", "forward"].forEach(basis => { const one = bb2One(base, sym, a, vals[sym], basis); if (one) facts.push(one); });
  });
  let marketMs = 0, asOf = "";
  peers.forEach(sym => { const v = vals && vals[sym]; if (v && v.marketMs > marketMs) { marketMs = v.marketMs; asOf = v.asOf || bb2AsOf(marketMs); } });
  const block = [
    "AUTHORITATIVE PEER COMPARISONS" + (asOf ? " as of " + asOf : "") + " (Yahoo Finance). Directions below are precomputed. Do not compare raw numbers yourself. Never compare a trailing P/E (TTM) with a forward P/E.",
    rows.join("\n"),
    facts.map(f => "FACT: " + f.sentence).join("\n")
  ].filter(Boolean).join("\n");
  return { base: base, peers: peers, rows: rows, facts: facts, block: block, asOf: asOf, marketMs: marketMs };
}
function bb2WordDir(word) {
  const w = String(word || "").toLowerCase();
  if (/higher|above|richer|premium|more expensive/.test(w)) return "higher";
  if (/lower|below|cheaper|discount|less expensive/.test(w)) return "lower";
  return null;
}
function bb2Claim(sentence, fact) {
  const a = bb2Esc(fact.a), b = bb2Esc(fact.b);
  const word = "more expensive|less expensive|higher|lower|above|below|cheaper|richer|premium|discount";
  const reA = new RegExp("\\b" + a + "\\b[\\s\\S]{0,90}?\\b(" + word + ")\\b(?:[\\s\\S]{0,20}?\\b(?:than|to)\\b)?[\\s\\S]{0,40}?\\b" + b + "\\b", "i");
  const ma = String(sentence).match(reA);
  if (ma) return bb2WordDir(ma[1]);
  const reB = new RegExp("\\b" + b + "\\b[\\s\\S]{0,90}?\\b(" + word + ")\\b(?:[\\s\\S]{0,20}?\\b(?:than|to)\\b)?[\\s\\S]{0,40}?\\b" + a + "\\b", "i");
  const mb = String(sentence).match(reB);
  if (!mb) return null;
  const d = bb2WordDir(mb[1]);
  return d === "higher" ? "lower" : d === "lower" ? "higher" : null;
}
function bb2FixSentence(sentence, facts) {
  const s = String(sentence || "");
  if (!facts || !facts.length || !BB2_CMP.test(s)) return s;
  if (/trailing|\bttm\b/i.test(s) && /forward/i.test(s) && !/not compared|do not compare|never compare|different bases/i.test(s)) {
    return "Trailing P/E (TTM) and forward P/E are different bases and are not compared.";
  }
  const sentFwd = /forward/i.test(s), sentTtm = /trailing|\bttm\b/i.test(s);
  const nums = [];
  const reN = /(\d+(?:\.\d+)?)\s*x/gi;
  let m; while ((m = reN.exec(s))) nums.push(Number(m[1]));
  const near = (n, v) => Number.isFinite(n) && Number.isFinite(v) && Math.abs(n - v) <= 0.2;
  for (const f of facts) {
    if (!f || f.dir === "missing" || !f.a || !f.b) continue;
    if (!new RegExp("\\b" + bb2Esc(f.a) + "\\b", "i").test(s) || !new RegExp("\\b" + bb2Esc(f.b) + "\\b", "i").test(s)) continue;
    if (f.basis === "trailing" && sentFwd && !sentTtm) continue;
    if (f.basis === "forward" && !sentFwd) continue;
    if (!nums.length && !sentTtm && !sentFwd && f.basis !== "trailing") continue;
    if (nums.length && !nums.some(n => near(n, f.va) || near(n, f.vb))) continue;
    const claim = bb2Claim(s, f);
    if (!claim) continue;
    if (f.dir === "in line" || claim !== f.dir) return f.sentence;
    return s;
  }
  return s;
}
function bb2Scrub(text) {
  return String(text || "")
    .replace(/\bprice targets?\s+(?:of\s+|at\s+|is\s+)?\$?\d[\d,]*(?:\.\d+)?(?:\s*(?:per share|a share))?/gi, "no price target (research only)")
    .replace(/\b(?:you should|i recommend(?: that)? you|we recommend(?: that)? you|i would|i'd)\s+(?:buy|sell)\b/gi, "no trade recommendation (research only)")
    .replace(/\b(?:buy|sell)\s+recommendation\b/gi, "research view");
}
function bb2Rewrite(text, facts) {
  let buf = String(text || ""), out = "";
  while (buf) {
    if (!BB2_CMP.test(buf)) { out += bb2Scrub(buf); buf = ""; break; }
    const m = buf.match(/^[\s\S]*?[.!?](?=\s|$)/);
    if (!m) break;
    out += bb2Scrub(bb2FixSentence(m[0], facts));
    buf = buf.slice(m[0].length);
  }
  if (buf) out += bb2Scrub(bb2FixSentence(buf, facts));
  return out;
}
function bb2ClientSources(body) {
  const arr = Array.isArray(body && body.sources) ? body.sources : [];
  const out = [];
  arr.slice(0, 8).forEach(s => {
    if (!s || typeof s !== "object") return;
    const name = String(s.name || s.src || "").trim();
    if (!name) return;
    const link = typeof s.link === "string" && /^https?:\/\//i.test(s.link) ? s.link.slice(0, 300) : "";
    out.push({ name: name.slice(0, 80), link: link, asOf: s.asOf ? String(s.asOf).slice(0, 48) : "", detail: s.detail ? String(s.detail).slice(0, 140) : "" });
  });
  return out;
}
function bb2PeerSource(base, built) {
  return {
    name: "Yahoo Finance",
    link: "https://finance.yahoo.com/quote/" + encodeURIComponent(base) + "/key-statistics/",
    asOf: built && built.asOf ? built.asOf : "",
    detail: "trailing P/E (TTM) and forward P/E, refreshed on request"
  };
}
function bb2Footer(sources) {
  if (!sources || !sources.length) return "\n\nSources: No news or price sources were supplied for this answer.";
  const lines = sources.map((s, i) => {
    const bits = ["[" + (i + 1) + "] " + s.name];
    if (s.link) bits.push(s.link);
    if (s.asOf) bits.push("as of " + s.asOf);
    if (s.detail) bits.push(s.detail);
    return bits.join(" | ");
  });
  return "\n\nSources:\n" + lines.join("\n");
}
function bb2Finish(reply, store) {
  const facts = (store && store.facts) || [];
  let text = bb2Rewrite(reply, facts).replace(/\n+Sources:[\s\S]*$/i, "").trim();
  const sources = [];
  if (store && Array.isArray(store.clientSources)) sources.push.apply(sources, store.clientSources);
  if (store && store.peerSource) sources.push(store.peerSource);
  return text + bb2Footer(sources);
}
function bb2Base(q) {
  const text = String(q || "");
  const tagged = text.match(/\[Answer this question as asked, about ([A-Z][A-Z0-9.\-]{0,9})\b/);
  if (tagged && BB2_PEERS[tagged[1]]) return tagged[1];
  const found = [];
  const re = /\$?\b([A-Z]{1,5})\b/g;
  let m; while ((m = re.exec(text))) { if (BB2_PEERS[m[1]] && found.indexOf(m[1]) < 0) found.push(m[1]); }
  return found[0] || null;
}
function bb2PeerAsk(q) { return /peer|compar|versus|\bvs\.?\b|valuation|p\/e|multiple|cheap|expensive|premium|discount/i.test(String(q || "")); }
function bb2Question(body) {
  const msgs = Array.isArray(body && body.messages) ? body.messages : [];
  for (let i = msgs.length - 1; i >= 0; i--) if (msgs[i] && msgs[i].role === "user") return String(msgs[i].content || "");
  return "";
}
function bb2Msgs(messages) {
  if (!Array.isArray(messages)) return [];
  return messages.slice(-12).map(m => ({ role: m && m.role === "assistant" ? "assistant" : "user", content: bb2Clip(m && m.content, 6000) })).filter(m => m.content);
}
function bb2System(body, built, sources) {
  const ctx = bb2Clip(typeof (body && body.context) === "string" ? body.context : JSON.stringify((body && body.context) || {}), 8000);
  const cites = (sources || []).map((s, i) => "[" + (i + 1) + "] " + s.name + (s.asOf ? " as of " + s.asOf : "") + (s.link ? " " + s.link : "") + (s.detail ? " - " + s.detail : "")).join("\n");
  return [
    built && built.block,
    "You are Dispatch Expert, a market-research assistant. Comparison directions were already shown to the reader and are precomputed. Do not recompute higher or lower. Never compare a trailing P/E (TTM) with a forward P/E. No buy or sell recommendation and no price target.",
    cites ? "CITABLE SOURCES (use these [n] markers only; do not invent sources):\n" + cites : "No news or price sources were supplied. Do not invent any.",
    "TERMINAL CONTEXT:\n" + ctx
  ].filter(Boolean).join("\n\n");
}
function bb2HasProvider() {
  return !!(process.env.AI_INTEGRATIONS_OPENAI_API_KEY || process.env.OPENAI_API_KEY || process.env.AI_INTEGRATIONS_OPENAI_BASE_URL || process.env.OPENAI_BASE_URL || process.env.AI_INTEGRATIONS_GEMINI_BASE_URL || process.env.AI_INTEGRATIONS_GEMINI_API_KEY || process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY);
}
function bb2WantsStream(req) {
  const headers = (req && req.headers) || {};
  const accept = String(headers.accept || headers.Accept || "");
  const flag = String(headers["x-dispatch-stream"] || headers["X-Dispatch-Stream"] || "");
  return /text\/event-stream/i.test(accept) || flag === "1";
}
function bb2OpenAiCfg() {
  const base = process.env.AI_INTEGRATIONS_OPENAI_BASE_URL || process.env.OPENAI_BASE_URL || "";
  const key = process.env.AI_INTEGRATIONS_OPENAI_API_KEY || process.env.OPENAI_API_KEY || "";
  if (!base && !key) return null;
  return { base: String(base || "https://api.openai.com/v1").replace(/\/$/, ""), key: key || "dummy" };
}
function bb2GemCfg() {
  const base = process.env.AI_INTEGRATIONS_GEMINI_BASE_URL || "";
  const key = process.env.AI_INTEGRATIONS_GEMINI_API_KEY || process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY || "";
  if (!base && !key) return null;
  return { base: String(base || "https://generativelanguage.googleapis.com").replace(/\/$/, ""), key: key || "dummy" };
}
async function bb2ReadSse(res, onLine) {
  if (!res || !res.body || typeof res.body.getReader !== "function") {
    const text = res && typeof res.text === "function" ? await res.text() : "";
    String(text).split(/\n/).forEach(onLine);
    return;
  }
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  while (true) {
    const step = await reader.read();
    if (step.done) break;
    buf += dec.decode(step.value, { stream: true });
    let i; while ((i = buf.indexOf("\n")) >= 0) { onLine(buf.slice(0, i).replace(/\r$/, "")); buf = buf.slice(i + 1); }
  }
  if (buf) onLine(buf);
}
async function bb2OpenAi(cfg, system, messages, onDelta) {
  const res = await bb2Fetch(cfg.base + "/chat/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json", "Authorization": "Bearer " + cfg.key },
    body: JSON.stringify({ model: "gpt-4o-mini", stream: true, temperature: 0.2, max_tokens: 900, messages: [{ role: "system", content: bb2Clip(system, 14000) }].concat(bb2Msgs(messages)) }),
    signal: AbortSignal.timeout(20000)
  });
  if (!res || !res.ok) throw new Error("openai " + (res && res.status));
  await bb2ReadSse(res, line => {
    const t = String(line || "").trim();
    if (t.indexOf("data:") !== 0) return;
    const p = t.slice(5).trim();
    if (!p || p === "[DONE]") return;
    try {
      const j = JSON.parse(p);
      const d = j.choices && j.choices[0] && j.choices[0].delta && j.choices[0].delta.content;
      if (d) onDelta(String(d));
    } catch (e) {}
  });
}
async function bb2Gemini(cfg, system, messages, onDelta) {
  const root = cfg.base.replace(/\/v1beta\/models\/.*$/, "").replace(/\/$/, "");
  let url = root + "/v1beta/models/gemini-2.5-flash:streamGenerateContent?alt=sse";
  if (cfg.key && cfg.key !== "dummy") url += "&key=" + encodeURIComponent(cfg.key);
  const contents = bb2Msgs(messages).map(m => ({ role: m.role === "assistant" ? "model" : "user", parts: [{ text: m.content }] }));
  const res = await bb2Fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ systemInstruction: { parts: [{ text: bb2Clip(system, 14000) }] }, contents: contents, generationConfig: { temperature: 0.2, maxOutputTokens: 900 } }),
    signal: AbortSignal.timeout(20000)
  });
  if (!res || !res.ok) throw new Error("gemini " + (res && res.status));
  await bb2ReadSse(res, line => {
    const t = String(line || "").trim();
    const p = t.indexOf("data:") === 0 ? t.slice(5).trim() : (t.charAt(0) === "{" ? t : "");
    if (!p) return;
    try {
      const j = JSON.parse(p);
      const parts = j.candidates && j.candidates[0] && j.candidates[0].content && j.candidates[0].content.parts;
      (parts || []).forEach(part => { if (part && part.text) onDelta(String(part.text)); });
    } catch (e) {}
  });
}
async function bb2Complete(system, messages, onDelta) {
  const errs = [];
  const oai = bb2OpenAiCfg();
  if (oai) { try { await bb2OpenAi(oai, system, messages, onDelta); return { provider: "OpenAI", model: "gpt-4o-mini" }; } catch (e) { errs.push(e && e.message); } }
  const gem = bb2GemCfg();
  if (gem) { try { await bb2Gemini(gem, system, messages, onDelta); return { provider: "Gemini", model: "gemini-2.5-flash" }; } catch (e) { errs.push(e && e.message); } }
  throw new Error(errs.filter(Boolean).join("; ") || "no provider");
}
function bb2Lead(built, cite) {
  const lines = ((built && built.facts) || []).map(f => f.sentence).filter(Boolean);
  if (!lines.length) return "";
  return lines.join(" ") + (cite ? " [" + cite + "]" : "") + "\n\n";
}
async function bb2StreamInner(req, res) {
  const t0 = Date.now();
  const user = await currentUser(req);
  if (!user || !hasPremiumAccess(user)) return json(res, 401, { error: "Premium membership required" });
  const body = await bb2Read0(req);
  const q = bb2Question(body);
  const base = bb2PeerAsk(q) ? bb2Base(q) : null;
  let built = null, vals = null;
  if (base) {
    const syms = [base].concat(BB2_PEERS[base] || []).slice(0, 6);
    vals = await bb2EnsureVals(syms);
    built = bb2BuildFacts(base, vals);
  }
  const sources = bb2ClientSources(body);
  let cite = 0;
  if (built && built.facts.length) { sources.push(bb2PeerSource(base, built)); cite = sources.length; }
  const store = bb2Als.getStore();
  if (store) { store.facts = built ? built.facts : []; store.clientSources = sources.slice(); store.peerSource = cite ? sources[sources.length - 1] : null; store.body = body; }
  res.writeHead(200, {
    "Content-Type": "text/event-stream; charset=utf-8",
    "Cache-Control": "no-store",
    "X-Accel-Buffering": "no",
    "Access-Control-Allow-Origin": "*"
  });
  if (res.socket && res.socket.setNoDelay) { try { res.socket.setNoDelay(true); } catch (e) {} }
  const send = obj => {
    res.write("data: " + JSON.stringify(obj) + "\n\n");
    if (typeof res.flush === "function") { try { res.flush(); } catch (e) {} }
  };
  let acc = "", buf = "", firstAt = 0;
  const facts = built ? built.facts : [];
  const emit = piece => {
    const text = bb2Scrub(piece);
    const trimmed = text.trim();
    if (trimmed && facts.some(f => f.sentence && trimmed === f.sentence && acc.indexOf(f.sentence) >= 0)) return;
    acc += text;
    if (!firstAt) firstAt = Date.now();
    send({ t: text });
  };
  const pump = force => {
    while (buf) {
      if (!BB2_CMP.test(buf)) { emit(buf); buf = ""; break; }
      const m = buf.match(/^[\s\S]*?[.!?](?=\s|$)/);
      if (!m) break;
      emit(bb2FixSentence(m[0], facts));
      buf = buf.slice(m[0].length);
    }
    if (force && buf) { emit(bb2FixSentence(buf, facts)); buf = ""; }
  };
  const lead = bb2Lead(built, cite);
  if (lead) emit(lead);
  let meta = { provider: "Dispatch", model: "comparison" };
  try {
    meta = await bb2Complete(bb2System(body, built, sources), body && body.messages, d => { buf += d; pump(false); });
  } catch (e) {
    if (!acc.trim()) { send({ error: "unavailable" }); res.end(); console.warn("bb2 chat provider miss", Date.now() - t0); return; }
  }
  pump(true);
  const reply = bb2Finish(acc, { facts: facts, clientSources: bb2ClientSources(body), peerSource: cite ? sources[sources.length - 1] : null });
  const srcAt = reply.indexOf("\n\nSources:");
  if (srcAt >= 0 && acc.indexOf("Sources:") < 0) emit(reply.slice(srcAt));
  send({ done: true, reply: reply, meta: { provider: meta.provider, model: meta.model, streamed: true }, sources: sources });
  res.end();
  console.warn("bb2 chat ttft_ms", (firstAt || Date.now()) - t0, "total_ms", Date.now() - t0);
}
function bb2StreamChat(req, res) {
  return bb2Als.run({ chat: true, facts: [], clientSources: [], peerSource: null }, function () { return bb2StreamInner(req, res); });
}
var bb2Read0 = typeof readBody === "function" ? readBody : async function () { return {}; };
try {
  if (!globalThis.__bb2FetchWrapped) {
    globalThis.__bb2FetchWrapped = true;
    const bb2Fetch0 = globalThis.fetch;
    globalThis.fetch = async function (url, opts) {
      try {
        const store = bb2Als.getStore();
        if (store && store.chat && bb2IsXai(url)) return { ok: false, status: 402, json: async () => ({}), text: async () => "", body: null };
      } catch (e) {}
      return bb2Fetch0.apply(this, arguments);
    };
  }
  if (typeof xaiProxy === "function") {
    const bb2Xp = xaiProxy;
    xaiProxy = async function (pathname, options, timeoutMs) {
      const store = bb2Als.getStore();
      const cap = store && store.chat ? Math.min(Number(timeoutMs) || 800, 800) : timeoutMs;
      return bb2Xp.call(this, pathname, options, cap);
    };
  }
  const bb2Gen0 = generateAi;
  generateAi = async function (options) {
    const rest = Array.prototype.slice.call(arguments, 1);
    const store = bb2Als.getStore();
    const sys = options && typeof options.system === "string" ? options.system : "";
    const isChat = !!(store && store.chat) || sys.indexOf('{"reply":"string"') >= 0;
    if (!isChat) return bb2Gen0.apply(this, arguments);
    let next = options;
    try {
      if (store && store.body && !store.clientSources) store.clientSources = bb2ClientSources(store.body);
      const q = bb2Question(store && store.body) || bb2Question({ messages: options && options.messages });
      if (bb2PeerAsk(q)) {
        const base = bb2Base(q);
        if (base) {
          const syms = [base].concat(BB2_PEERS[base] || []).slice(0, 6);
          const vals = await bb2EnsureVals(syms);
          const built = bb2BuildFacts(base, vals);
          if (store) {
            store.facts = built.facts;
            if (built.facts.length) store.peerSource = bb2PeerSource(base, built);
          }
          next = Object.assign({}, options, { system: built.block + "\n\nUse the FACT lines verbatim for any comparison. Do not invent a direction. Never compare trailing P/E (TTM) with forward P/E.\n\n" + sys });
        }
      }
    } catch (e) {}
    return bb2Gen0.call(this, next, ...rest);
  };
  readBody = async function (req) {
    const body = await bb2Read0.apply(this, arguments);
    try { const store = bb2Als.getStore(); if (store) store.body = body; } catch (e) {}
    return body;
  };
  const bb2Handle0 = handle;
  handle = async function (req, res) {
    const self = this;
    let stream = false;
    try {
      const host = (req.headers && (req.headers.host || req.headers.Host)) || "localhost";
      const url = new URL(req.url || "/", "http://" + host);
      stream = req.method === "POST" && url.pathname === "/api/chat" && bb2WantsStream(req) && bb2HasProvider();
    } catch (e) {}
    if (stream) {
      try { return await bb2StreamChat(req, res); }
      catch (e) {
        console.warn("bb2 stream error", e && e.message);
        if (res && (res.headersSent || res.writableEnded)) { try { res.end(); } catch (e2) {} return; }
      }
    }
    return bb2Als.run({ chat: false, facts: [], clientSources: [], peerSource: null }, async function () {
      let isChat = false;
      try {
        const host = (req.headers && (req.headers.host || req.headers.Host)) || "localhost";
        const url = new URL(req.url || "/", "http://" + host);
        isChat = req.method === "POST" && url.pathname === "/api/chat";
      } catch (e) {}
      const store = bb2Als.getStore();
      if (store) store.chat = isChat;
      if (isChat && res && typeof res.end === "function" && !res.__bb2End) {
        const end0 = res.end;
        res.__bb2End = true;
        res.end = function (chunk, enc, cb) {
          try {
            const st = bb2Als.getStore();
            if (st && st.chat && chunk && typeof chunk !== "function") {
              const text = Buffer.isBuffer(chunk) ? chunk.toString("utf8") : typeof chunk === "string" ? chunk : "";
              if (text && text.charCodeAt(0) === 123) {
                const body = JSON.parse(text);
                if (body && typeof body.reply === "string") {
                  body.reply = bb2Finish(body.reply, st);
                  const next = JSON.stringify(body);
                  if (typeof res.setHeader === "function") { try { res.setHeader("Content-Length", Buffer.byteLength(next)); } catch (e) {} }
                  return end0.call(this, next, typeof enc === "function" ? undefined : enc, typeof enc === "function" ? enc : cb);
                }
              }
            }
          } catch (e) {}
          return end0.apply(this, arguments);
        };
      }
      return bb2Handle0.call(self, req, res);
    });
  };
} catch (e) { console.warn("bb2 hooks skipped", e && e.message); }
// BB2_JS_END
'''

v = v.rstrip("\n") + "\n" + SERVER
print("APPLY server comparison stream")

nodecheck(s, "app.js")
nodecheck(v, "server.js")
print("node --check passed" + (" (dry run)" if CHECK else ""))
after = {
    APP: encode(s, crlf),
    IDX: encode(h, hcrlf),
    SRV: encode(v, vcrlf),
}
for path in (APP, IDX, SRV):
    show("after", path, after[path])
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

def restore(baks):
    for path, bak in baks:
        if os.path.exists(bak):
            open(path, "wb").write(open(bak, "rb").read())
            os.unlink(bak)

pairs = [(APP, after[APP]), (IDX, after[IDX]), (SRV, after[SRV])]
baks = []
try:
    for path, data in pairs:
        bak = path + ".bb2bak"
        open(bak, "wb").write(open(path, "rb").read())
        baks.append((path, bak))
        open(path, "wb").write(data)
    for path in (APP, SRV):
        r = subprocess.run(["node", "--check", path], capture_output=True, text=True)
        if r.returncode:
            restore(baks)
            print("ABORT: node --check failed after write; backups restored:", r.stderr[:400])
            sys.exit(1)
    for path, bak in baks:
        os.unlink(bak)
except Exception as e:
    restore(baks)
    print("ABORT: write failed; backups restored:", e)
    sys.exit(1)
print("written", APP, IDX, SRV)
