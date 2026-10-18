#!/usr/bin/env python3
"""patch_bb3b.py — stream crash, empty numbered list, first paint.

Root of `bb2 stream error Cannot read properties of undefined (reading 'length')`.
The same statement, two live bases:

  chat61 server d01df387 line 8895  (bb3FilterSources calls it at 8901;
      fit's function bb3Tickers() at 9155 overwrites ask's at 8874)
  chat59 server 6972fdeb line 8546  (filter at 8552; fit's bb3Tickers at 8806
      overwrites ask's at 8525)

  for (var i = 0; i < tickers.length; i++)

info.tickers is undefined because the later function returns an array.
The throw is before the inner try, headers are already sent, and the bb2
wrapper only does res.end(), so the client falls back to the legacy JSON
path (~rt42s chat ms).

This patch never calls bb3Tickers. Every array read in the new stream path
uses Array.isArray. Missing P/E numbers stay on the existing bb2One path
(no throw). A restated numbered list is dropped whole, including the
"differences:" intro and a dangling Summary. The SSE response flushes a
~2KB comment pad before the peer block. Failures log `bb3b stream error`
plus a redacted stack and, once headers are out, an error event and a done
event.

Legacy generateAi order, from the live names (there is no provider id
"openai1" in AI_PROVIDER_IDS):

  xai-key  -> XAI_API_KEY via completeWithXaiKey
  openai   -> OPENAI_API_KEY (aiProviderKey), only if OPENAI_MANUAL_OPT_IN
  openai1  -> AI_INTEGRATIONS_OPENAI_API_KEY (bb2OpenAiCfg prefers this
              over OPENAI_API_KEY; the legacy loop never tried it)
  google   -> GEMINI_API_KEY or GOOGLE_API_KEY

When the integration key is set it is tried first and OPENAI_API_KEY is
tried immediately after it. xAI (the key path and the connector id) is
skipped for 30 minutes after PROVIDER_CREDITS. The cooldown is a process
variable. No new keys, no persistence, and key values are never printed.

bb4daily (chat61) already builds academy lessons through _bb4dGen /
_bb4dOne and skips provider "xai" there. This patch does not edit that
block, BB4D_AI, or _rt48sBuild. Academy never enters the reordered
generateAi loop.

Requires the bb3 and bb3fit markers and chatNN >= 59. Expected md5s are
the chat61 trio; a mismatch (including plain chat59) warns and does not
abort. Already applied exits 0. app.js and index.html change, so
app.js?v=chatN bumps one step (chat61 -> chat62, chat59 -> chat60).

Usage: python3 patch_bb3b.py [--check] <dir with app.js, index.html, server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "33ed3185be567ca7e6011991a002546c",
    "index.html": "c4f77a9a7c4af0826724b5b2c9e4f274",
    "server.js": "d01df3871aa1bc57085932288ccff93b",
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
    print("bb3b %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
    return digest

def encode(text, use_crlf):
    return (text.replace("\n", "\r\n") if use_crlf else text).encode("utf-8")

s, crlf = load(APP)
h, hcrlf = load(IDX)
v, vcrlf = load(SRV)

for path in (APP, IDX, SRV):
    digest = show("before", path)
    expect = EXPECTED_MD5.get(os.path.basename(path)) or ""
    if expect and digest != expect:
        print("WARN md5 %s: have %s expected %s (anchors still decide)" % (os.path.basename(path), digest, expect))

if "// \u2500\u2500 bb3b \u2500\u2500" in v:
    print("REFUSE: bb3b already applied")
    sys.exit(0)

miss = []
if "// \u2500\u2500 bb3 \u2500\u2500" not in v:
    miss.append("server.js marker missing: // ── bb3 ──")
if "// \u2500\u2500 bb3fit \u2500\u2500" not in v:
    miss.append("server.js marker missing: // ── bb3fit ──")
chat_hits = re.findall(r'app\.js\?v=chat(\d+)"', h)
chat_n = None
if len(chat_hits) != 1:
    miss.append('index.html marker missing: app.js?v=chatNN" (found %d)' % len(chat_hits))
else:
    chat_n = int(chat_hits[0])
    if chat_n < 59:
        miss.append("index.html is chat%d; need chat59 or later" % chat_n)

anchors = [
    ("server.js", v, "async function generateAi(options) {"),
    ("server.js", v, "function sendAiError(res, error) {"),
    ("server.js", v, "function bb3Mentions(source, tickers) {"),
    ("server.js", v, "for (var i = 0; i < tickers.length; i++) {"),
    ("server.js", v, 'console.warn("bb2 stream error", e && e.message);'),
    ("app.js", s, "function _chatMd(text) {"),
    ("app.js", s, "if (!streamed && (broken || !final)) {"),
    ("app.js", s, 'if (ev.error && !acc) broken = true;'),
]
for label, src, anchor in anchors:
    if src.count(anchor) != 1:
        miss.append("%s anchor %r matched %d times" % (label, anchor, src.count(anchor)))
# bb4daily owns the academy lesson build. Present on chat61, absent on chat59.
# Record the skip so a later edit cannot rewrite it. Never required.
BB4_KEEP = []
if "// \u2500\u2500 bb4daily \u2500\u2500" in v:
    BB4_KEEP = [
        'if (provider === "xai" || typeof generateWithAiProvider !== "function")',
        'const BB4D_AI = [["openai", "gpt-4o-mini"], ["google", "gemini-2.5-flash"]];',
        "const r = await _bb4dGen(",
    ]
    for anchor in BB4_KEEP:
        if v.count(anchor) != 1:
            miss.append("bb4daily anchor %r matched %d times" % (anchor, v.count(anchor)))
if miss:
    print("ABORT (nothing written):")
    for item in miss:
        print("ABORT:", item)
    sys.exit(1)

g0 = v.find("async function generateAi(options) {")
g1 = v.find("\nfunction sendAiError(res, error) {")
if g0 < 0 or g1 < 0 or g1 < g0:
    die("server.js generateAi span missing")
v = v[:g0] + "async function generateAi(options) {\n  return bb3bGenerateAi(options);\n}\n" + v[g1 + 1:]

OLD_MD = """function _chatMd(text) {
  if (!text) return "";
  let s = String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  s = s.replace(/^## (.+)$/gm, '<div class="chat-h2">$1</div>');
  s = s.replace(/^### (.+)$/gm, '<div class="chat-h3">$1</div>');
  s = s.replace(/\\*\\*(.+?)\\*\\*/g, "<strong>$1</strong>");
  s = s.replace(/`([^`]+)`/g, '<code class="chat-code">$1</code>');
  s = s.replace(/^[-•] (.+)$/gm, '<div class="chat-li"><span class="chat-li-dot">▸</span>$1</div>');
  s = s.replace(/\\n\\n/g, "</p><p>");
  return `<p>${s}</p>`;
}"""

NEW_MD = """function _chatMd(text) {
  // ── bb3b ── a numbered marker with no text is never an item
  if (!text) return "";
  var rawLines = String(text).split("\\n");
  var keptLines = [];
  for (var ci = 0; ci < rawLines.length; ci++) {
    var line = rawLines[ci];
    if (/^\\s*\\d+\\.\\s*$/.test(line)) continue;
    var numbered = /^\\s*\\d+\\.\\s+(\\S[\\s\\S]*)$/.exec(line);
    if (numbered && !String(numbered[1] || "").trim()) continue;
    keptLines.push(line);
  }
  let s = keptLines.join("\\n").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  s = s.replace(/^## (.+)$/gm, '<div class="chat-h2">$1</div>');
  s = s.replace(/^### (.+)$/gm, '<div class="chat-h3">$1</div>');
  s = s.replace(/\\*\\*(.+?)\\*\\*/g, "<strong>$1</strong>");
  s = s.replace(/`([^`]+)`/g, '<code class="chat-code">$1</code>');
  s = s.replace(/^(\\d+\\.\\s+\\S.*)$/gm, '<div class="chat-li"><span class="chat-li-dot">▸</span>$1</div>');
  s = s.replace(/^[-•] (.+)$/gm, '<div class="chat-li"><span class="chat-li-dot">▸</span>$1</div>');
  s = s.replace(/<div class="chat-li"><span class="chat-li-dot">▸<\\/span>\\s*<\\/div>/g, "");
  s = s.replace(/<li>\\s*<\\/li>/gi, "");
  s = s.replace(/\\n\\n/g, "</p><p>");
  return `<p>${s}</p>`;
}"""

if s.count(OLD_MD) != 1:
    die("app.js _chatMd anchor matched %d times" % s.count(OLD_MD))
s = s.replace(OLD_MD, NEW_MD, 1)

OLD_EV = """          if (ev.t) note(ev.t);
          if (ev.done) final = ev;
          if (ev.error && !acc) broken = true;"""
NEW_EV = """          // bb3b: ':' padding is not a data event. The first data event paints now.
          if (ev.t) note(ev.t);
          else if (ev.status) note(String(ev.status));
          if (ev.done) final = ev;
          if (ev.error) broken = true;"""
if s.count(OLD_EV) != 1:
    die("app.js SSE reader anchor matched %d times" % s.count(OLD_EV))
s = s.replace(OLD_EV, NEW_EV, 1)
OLD_FALL = "    if (!streamed && (broken || !final)) {"
NEW_FALL = "    if (!streamed && !final) { // bb3b: a done event is the answer; do not fall back"
if s.count(OLD_FALL) != 1:
    die("app.js fallback anchor matched %d times" % s.count(OLD_FALL))
s = s.replace(OLD_FALL, NEW_FALL, 1)

BLOCK = r'''
// ── bb3b ── Guard the stream crash, drop empty numbered lists, flush the first byte.
// BB3B_JS
var bb3bXaiCoolUntil = 0;
function bb3bArr(x) { return Array.isArray(x) ? x : []; }
function bb3bEnv(name) { return String((process.env && process.env[name]) || "").trim(); }
function bb3bStack(err) {
  var s = err && err.stack ? String(err.stack) : String(err && err.message || err || "");
  s = s.replace(/Bearer\s+\S+/gi, "Bearer [redacted]");
  s = s.replace(/\bsk-[A-Za-z0-9_\-]{6,}\b/g, "[redacted]");
  s = s.replace(/(api[_-]?key|authorization|cookie|crumb)=([^&\s]+)/gi, "$1=[redacted]");
  return s.slice(0, 4000);
}
function bb3bNoteCredits(error, id) {
  var code = error && error.code;
  var status = error && error.status;
  if ((id === "xai-key" || id === "xai") && (code === "PROVIDER_CREDITS" || status === 402 || status === 403)) {
    bb3bXaiCoolUntil = Date.now() + 30 * 60 * 1000;
  }
}
function bb3bXaiCooling() { return Date.now() < bb3bXaiCoolUntil; }
function bb3bOpenAiOptIn() {
  if (typeof openAiOwnerOptIn === "function") return !!openAiOwnerOptIn(process.env);
  return String(process.env.OPENAI_MANUAL_OPT_IN || "").trim().toLowerCase() === "true";
}
function bb3bAttempts() {
  var out = [];
  if (bb3bEnv("XAI_API_KEY") && !bb3bXaiCooling()) out.push({ kind: "xai-key", id: "xai-key" });
  var integration = !!bb3bEnv("AI_INTEGRATIONS_OPENAI_API_KEY");
  if (integration) out.push({ kind: "openai-slot", id: "openai1", env: "AI_INTEGRATIONS_OPENAI_API_KEY", baseEnv: "AI_INTEGRATIONS_OPENAI_BASE_URL" });
  var manual = !!bb3bEnv("OPENAI_API_KEY") && bb3bOpenAiOptIn();
  if (integration && manual) out.push({ kind: "openai-slot", id: "openai", env: "OPENAI_API_KEY", baseEnv: "OPENAI_BASE_URL" });
  var status = typeof aiProviderStatus === "function" ? aiProviderStatus() : { fallbackOrder: [] };
  var order = bb3bArr(status && status.fallbackOrder);
  for (var i = 0; i < order.length; i++) {
    var id = order[i];
    if (id === "xai" && bb3bXaiCooling()) continue;
    if (id === "openai" && integration) continue;
    out.push({ kind: "provider", id: id });
  }
  return out;
}
async function bb3bRunXaiKey(options) {
  var xaiKey = bb3bEnv("XAI_API_KEY");
  if (!xaiKey || bb3bXaiCooling()) return null;
  var completeWithXaiKey, xaiBaseUrl, xaiModel;
  if (typeof globalThis.bb3bXaiTest === "function") {
    var api = globalThis.bb3bXaiTest() || {};
    completeWithXaiKey = api.completeWithXaiKey;
    xaiBaseUrl = api.xaiBaseUrl || function () { return "https://api.x.ai"; };
    xaiModel = api.xaiModel || function () { return "grok"; };
  } else {
    var mod = require("./dispatchXai");
    completeWithXaiKey = mod.completeWithXaiKey;
    xaiBaseUrl = mod.xaiBaseUrl;
    xaiModel = mod.xaiModel;
  }
  var result = await completeWithXaiKey({
    apiKey: xaiKey,
    model: xaiModel(),
    baseUrl: xaiBaseUrl(),
    system: options && options.system,
    messages: options && options.messages,
    maxTokens: options && options.maxTokens,
    temperature: options && options.temperature,
    timeoutMs: 25000
  });
  if (typeof options.validate === "function") {
    var validated = options.validate(result && result.text);
    if (validated !== undefined) return Object.assign({}, result, { validated: validated });
  }
  return result;
}
async function bb3bRunOpenAiSlot(attempt, options) {
  var key = bb3bEnv(attempt.env);
  if (!key) {
    if (typeof AiRequestError === "function") throw new AiRequestError(503, "OpenAI is not configured.", "PROVIDER_NOT_CONFIGURED");
    throw new Error("openai");
  }
  var base = bb3bEnv(attempt.baseEnv) || (attempt.id === "openai" ? bb3bEnv("OPENAI_BASE_URL") : "") || "https://api.openai.com";
  base = String(base).replace(/\/+$/, "").replace(/\/v1$/i, "");
  var model = bb3bEnv("DISPATCH_AI_OPENAI_MODEL") || "gpt-4o-mini";
  var messages = typeof asAiMessages === "function" ? asAiMessages(options && options.messages) : bb3bArr(options && options.messages);
  var system = typeof clipped === "function" ? clipped(options && options.system, 5000) : String((options && options.system) || "");
  var tokens = Math.max(300, Math.min(Number(options && options.maxTokens) || 1000, 2400));
  var controller = new AbortController();
  var timeoutMs = typeof AI_TIMEOUT_MS === "number" ? AI_TIMEOUT_MS : 25000;
  var response = await withTimeout(fetch(base + "/v1/chat/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json", "Authorization": "Bearer " + key },
    body: JSON.stringify({
      model: model,
      messages: [{ role: "system", content: system }].concat(messages),
      max_completion_tokens: tokens,
      temperature: options && options.temperature
    }),
    signal: controller.signal
  }), timeoutMs, undefined, function () { try { controller.abort(); } catch (e) {} });
  if (!response || !response.ok) {
    if (typeof aiProviderError === "function") throw aiProviderError("openai", response && response.status);
    throw new Error("openai");
  }
  var data;
  try { data = await response.json(); }
  catch (e) {
    if (typeof AiRequestError === "function") throw new AiRequestError(502, "The AI returned an unreadable response. Please try again.", "INVALID_RESPONSE");
    throw e;
  }
  var generated = data && data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content;
  if (typeof generated !== "string" || !generated.trim()) {
    if (typeof AiRequestError === "function") throw new AiRequestError(502, "The AI returned an empty response. Please try again.", "EMPTY_RESPONSE");
    throw new Error("empty");
  }
  var result = { text: String(generated), model: model, provider: "OpenAI" };
  if (typeof options.validate === "function") {
    var validated = options.validate(result.text);
    return Object.assign({}, result, { validated: validated });
  }
  return result;
}
async function bb3bGenerateAi(options) {
  var lastError = null;
  var seen = {};
  while (true) {
    var attempts = bb3bAttempts().filter(function (a) { return a && !seen[a.kind + ":" + a.id]; });
    if (!attempts.length) break;
    var attempt = attempts[0];
    seen[attempt.kind + ":" + attempt.id] = true;
    try {
      if (attempt.kind === "xai-key") {
        var xaiResult = await bb3bRunXaiKey(options);
        if (!xaiResult) continue;
        console.warn("AI provider answered: xai-key");
        return xaiResult;
      }
      if (attempt.kind === "openai-slot") {
        var slotResult = await bb3bRunOpenAiSlot(attempt, options);
        console.warn("AI provider answered:", attempt.id);
        return slotResult;
      }
      var provider = attempt.id;
      var model = await discoverAiModel(provider);
      var controller = new AbortController();
      var result = await withTimeout(
        generateWithAiProvider(provider, Object.assign({}, options, { model: model, signal: controller.signal })),
        typeof AI_TIMEOUT_MS === "number" ? AI_TIMEOUT_MS : 25000,
        undefined,
        function () { try { controller.abort(); } catch (e) {} }
      );
      var validated = typeof options.validate === "function" ? options.validate(result.text) : undefined;
      console.warn("AI provider answered:", provider);
      return validated === undefined ? result : Object.assign({}, result, { validated: validated });
    } catch (error) {
      lastError = error;
      bb3bNoteCredits(error, attempt.id);
      var code = (typeof isAiTimeoutError === "function" && isAiTimeoutError(error)) ? "TIMEOUT" : ((error && error.code) || "UPSTREAM_ERROR");
      if (attempt.id === "xai-key") console.warn("AI provider attempt failed: xai-key", code);
      else console.warn("AI provider attempt failed:", attempt.id, code);
    }
  }
  if (lastError && typeof AiRequestError === "function" && lastError instanceof AiRequestError) throw lastError;
  if (typeof AiRequestError === "function") throw new AiRequestError(503, "No configured AI provider is ready.", "PROVIDER_UNAVAILABLE");
  throw lastError || new Error("no provider");
}
function bb3bListDot(buf, i) {
  if (!buf || buf.charAt(i) !== ".") return false;
  var next = i + 1 < buf.length ? buf.charAt(i + 1) : "";
  if (next && !/\s/.test(next)) return false;
  var k = i - 1;
  if (k < 0 || !/\d/.test(buf.charAt(k))) return false;
  while (k >= 0 && /\d/.test(buf.charAt(k))) k--;
  var p = k;
  while (p >= 0 && (buf.charAt(p) === " " || buf.charAt(p) === "\t")) p--;
  if (p >= 0 && buf.charAt(p) !== "\n") return false;
  return true;
}
function bb3bNext(buf, force) {
  buf = String(buf || "");
  var lead = 0;
  while (lead < buf.length && /\s/.test(buf.charAt(lead))) lead++;
  var i = lead;
  while (i < buf.length) {
    var c = buf.charAt(i);
    if ((c === "." || c === "!" || c === "?") && !(c === "." && bb3bListDot(buf, i))) {
      var prev = i > 0 ? buf.charAt(i - 1) : "";
      var next = i + 1 < buf.length ? buf.charAt(i + 1) : "";
      var decimal = c === "." && /\d/.test(prev) && (/\d/.test(next) || (next === "" && !force));
      if (!decimal) {
        if (next === "" && !force) return null;
        if (next !== "" && !/\s/.test(next)) { i++; continue; }
        var j = i + 1;
        while (j < buf.length && /\s/.test(buf.charAt(j))) j++;
        return { prefix: buf.slice(0, lead), sentence: buf.slice(lead, i + 1), sep: buf.slice(i + 1, j), rest: buf.slice(j) };
      }
    }
    i++;
  }
  if (force && buf.length) return { prefix: "", sentence: buf, sep: "", rest: "" };
  return null;
}
function bb3bMarkerOnly(line) { return /^\s*\d+\.\s*$/.test(String(line || "")); }
function bb3bItem(line) { return /^\s*\d+\.\s+\S/.test(String(line || "")); }
function bb3bIntro(line) { return /differences:\s*$/i.test(String(line || "").trim()); }
function bb3bHeading(line) {
  var t = String(line || "").trim();
  if (!t) return false;
  if (/^summary\s*$/i.test(t)) return true;
  if (/^#{1,6}\s+\S/.test(t)) return true;
  if (/^\*\*[^*]+\*\*$/.test(t)) return true;
  return false;
}
function bb3bRestates(sentence, facts) {
  var s = String(sentence || "");
  var list = bb3bArr(facts);
  if (!list.length) return false;
  for (var n = 0; n < list.length; n++) {
    var f = list[n];
    if (!f || !f.a || !f.b) continue;
    var hasA = new RegExp("\\b" + f.a + "\\b").test(s);
    var hasB = new RegExp("\\b" + f.b + "\\b").test(s);
    if (hasA && hasB && (/\b(higher|lower|above|below|cheaper|richer|premium|discount)\b/i.test(s) || /p\/e|multiple/i.test(s))) return true;
    if (f.dir === "missing" && (hasA || hasB) && /not reported/i.test(s)) return true;
  }
  return false;
}
function bb3bFixProse(line, facts, drop) {
  var buf = String(line || ""), out = "";
  var list = bb3bArr(facts);
  function take(force) {
    var part = bb3bNext(buf, force);
    if (!part) return false;
    if (part.rest === buf && !force) return false;
    if (drop && bb3bRestates(part.sentence, list)) {
      var pre = part.prefix + part.sep;
      if (pre.trim() && !bb3bMarkerOnly(pre)) out += pre;
    } else {
      var fixed = typeof bb3Fix === "function" ? bb3Fix(part.sentence, list) : part.sentence;
      var piece = part.prefix + fixed + part.sep;
      if (!bb3bMarkerOnly(piece) && String(piece || "").trim()) out += piece;
    }
    buf = part.rest;
    return true;
  }
  var guard = 0;
  while (buf && take(false)) { if (++guard > 1000) break; }
  if (buf) take(true);
  return out;
}
function bb3bRewrite(text, facts, drop) {
  var lines = String(text || "").replace(/\r\n/g, "\n").split("\n");
  var out = [];
  var i = 0;
  while (i < lines.length) {
    if (bb3bIntro(lines[i]) || bb3bItem(lines[i]) || bb3bMarkerOnly(lines[i])) {
      var intro = bb3bIntro(lines[i]) ? lines[i] : null;
      if (intro != null) i++;
      var items = [];
      while (i < lines.length && (bb3bItem(lines[i]) || bb3bMarkerOnly(lines[i]))) {
        items.push(lines[i]);
        i++;
      }
      if (!items.length && intro != null) { out.push(intro); continue; }
      var kept = [];
      for (var n = 0; n < items.length; n++) {
        if (bb3bMarkerOnly(items[n])) continue;
        if (drop && bb3bRestates(items[n], facts)) continue;
        kept.push(items[n]);
      }
      if (kept.length) {
        if (intro != null) out.push(intro);
        for (var k = 0; k < kept.length; k++) out.push(kept[k]);
      }
      continue;
    }
    var prose = drop ? bb3bFixProse(lines[i], facts, true) : lines[i];
    if (prose && !bb3bMarkerOnly(prose)) out.push(prose);
    i++;
  }
  var cleaned = [];
  for (var p = 0; p < out.length; p++) {
    if (bb3bHeading(out[p])) {
      var q = p + 1;
      while (q < out.length && !String(out[q]).trim()) q++;
      if (q >= out.length || bb3bHeading(out[q])) continue;
    }
    cleaned.push(out[p]);
  }
  return cleaned.join("\n").replace(/\n{3,}/g, "\n\n");
}
function bb3bAskInfo(body) {
  var q = typeof bb2Question === "function" ? bb2Question(body) : "";
  var peer = typeof bb2PeerAsk === "function" ? !!bb2PeerAsk(q) : false;
  var list = [];
  function add(t) {
    t = String(t || "").toUpperCase();
    if (!t || !/^[A-Z][A-Z0-9.\-]{0,9}$/.test(t) || list.indexOf(t) >= 0) return;
    list.push(t);
  }
  var base = typeof bb2Base === "function" ? bb2Base(q) : null;
  if (base) {
    add(base);
    bb3bArr(typeof BB2_PEERS !== "undefined" && BB2_PEERS ? BB2_PEERS[base] : []).forEach(add);
  }
  if (body && Array.isArray(body.tickers)) body.tickers.forEach(add);
  return { q: q, peer: peer, base: base, tickers: list };
}
function bb3bMentions(source, tickers) {
  var list = bb3bArr(tickers);
  var blob = ((source && source.name) || "") + " " + ((source && source.detail) || "") + " " + ((source && source.link) || "");
  blob = blob.toUpperCase();
  for (var i = 0; i < list.length; i++) {
    var tk = String(list[i] || "");
    if (!tk) continue;
    if (new RegExp("\\b" + tk.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\b").test(blob)) return true;
  }
  return false;
}
function bb3bRawSources(body) {
  var arr = bb3bArr(body && body.sources);
  var out = [];
  arr.slice(0, 8).forEach(function (src) {
    if (!src || typeof src !== "object") return;
    var name = String(src.name || src.src || "").trim();
    if (!name) return;
    var link = typeof src.link === "string" && /^https?:\/\//i.test(src.link) ? src.link.slice(0, 300) : "";
    out.push({ name: name.slice(0, 80), link: link, asOf: src.asOf ? String(src.asOf).slice(0, 48) : "", detail: src.detail ? String(src.detail).slice(0, 140) : "" });
  });
  return out;
}
function bb3bFilterSources(sources, body) {
  var info = bb3bAskInfo(body);
  var out = [];
  bb3bArr(sources).forEach(function (src) {
    if (!src) return;
    if (bb3bMentions(src, info.tickers)) out.push(src);
    else if (!info.peer) out.push(src);
  });
  return out;
}
function bb3bTrimBody(body) {
  var info = bb3bAskInfo(body);
  if (!info.peer || !body || typeof body.context !== "string" || !body.context) return body;
  var tickers = bb3bArr(info.tickers);
  var lines = String(body.context).split("\n");
  var kept = [], inHeads = false, keepFollow = false;
  lines.forEach(function (line) {
    var t = String(line || "").trim();
    if (/^Latest headlines:/i.test(t)) { inHeads = true; keepFollow = false; return; }
    if (inHeads) {
      if (!t) { inHeads = false; return; }
      if (/^[•\-] /.test(t) || /^\[[^\]]+\]/.test(t)) {
        if (bb3bMentions({ name: t, detail: t, link: "" }, tickers)) kept.push(t);
        return;
      }
      inHeads = false;
    }
    if (!t) { keepFollow = false; return; }
    var mention = bb3bMentions({ name: t, detail: "", link: "" }, tickers);
    var peerHead = /peer valuation/i.test(t);
    var follow = keepFollow && /^(Financials:|Earnings:|Live price:)/i.test(t);
    if (mention || peerHead || follow) {
      kept.push(line);
      keepFollow = /^(Active ticker:|Peer valuations)/i.test(t);
    } else keepFollow = false;
  });
  var ctx = kept.join("\n").replace(/\n{3,}/g, "\n\n").trim().slice(0, 1600);
  var next = {};
  Object.keys(body).forEach(function (k) { next[k] = body[k]; });
  next.context = ctx;
  return next;
}
function bb3bReadCache(syms) {
  var out = {}, any = false;
  bb3bArr(syms).forEach(function (sym) {
    var hit = bb2Mem && bb2Mem.vals && typeof bb2Mem.vals.get === "function" && bb2Mem.vals.get(sym);
    if (hit && hit.v) { out[sym] = hit.v; any = true; }
  });
  return any ? out : null;
}
function bb3bCompose(reply, built, cite) {
  var facts = bb3bArr(built && built.facts);
  var text = bb3bRewrite(String(reply || "").replace(/\n+Sources:[\s\S]*$/i, ""), facts, true);
  text = text.replace(/Peer comparisons as of [^\n]*\n/g, "").replace(/^Peer comparisons:\n/gm, "");
  text = text.replace(/Fetching latest valuations\.\n*/g, "");
  text = text.replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
  if (/^summary\s*$/i.test(text)) text = "";
  if (facts.length) {
    var lead = (typeof bb3LeadText === "function" ? bb3LeadText(built, cite) : "").trim();
    return (lead + (text ? "\n\n" + text : "")).trim();
  }
  return text.trim();
}
function bb3bHold(text, facts) {
  var s = String(text || "");
  if (!s) return false;
  if (bb3bMarkerOnly(s) || bb3bItem(s) || bb3bIntro(s)) return true;
  if (/p\/e|multiple|trailing|forward|\bttm\b|not reported/i.test(s)) return true;
  if (/\b(higher|lower|above|below|cheaper|richer|premium|discount)\b/i.test(s)) return true;
  if (/\b[A-Z]{2,5}\b/.test(s) && /\d/.test(s)) return true;
  if (/\d\.$/.test(s) && !bb3bListDot(s, s.length - 1)) return true;
  var list = bb3bArr(facts);
  for (var n = 0; n < list.length; n++) {
    var f = list[n];
    if (!f) continue;
    if ((f.a && new RegExp("\\b" + f.a + "\\b").test(s)) || (f.b && new RegExp("\\b" + f.b + "\\b").test(s))) return true;
  }
  return false;
}
async function bb3bStreamInner(req, res) {
  var t0 = Date.now();
  var acc = "";
  var headersSent = false;
  var meta = { provider: "Dispatch", model: "comparison" };
  var firstAt = 0, modelAt = 0;
  function send(obj, kind) {
    res.write("data: " + JSON.stringify(obj) + "\n\n");
    if (typeof res.flush === "function") { try { res.flush(); } catch (e) {} }
    if (!firstAt && obj && obj.t) firstAt = Date.now();
    if (kind === "model" && obj && obj.t && !modelAt) modelAt = Date.now();
  }
  function fail(err) {
    console.warn("bb3b stream error", bb3bStack(err));
    if (!(headersSent || (res && res.headersSent))) {
      try { return json(res, 500, { error: "unavailable" }); } catch (e2) { return; }
    }
    try {
      res.write("data: " + JSON.stringify({ error: "unavailable" }) + "\n\n");
      res.write("data: " + JSON.stringify({ done: true, reply: acc || "", meta: { provider: (meta && meta.provider) || "Dispatch", model: (meta && meta.model) || "comparison", streamed: false }, sources: [] }) + "\n\n");
      res.end();
    } catch (e3) {}
  }
  try {
    var user = await currentUser(req);
    if (!user || !hasPremiumAccess(user)) return json(res, 401, { error: "Premium membership required" });
    var body = typeof bb2Read0 === "function" ? await bb2Read0(req) : {};
    res.writeHead(200, {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      "X-Accel-Buffering": "no",
      "Connection": "keep-alive"
    });
    headersSent = true;
    if (typeof res.flushHeaders === "function") { try { res.flushHeaders(); } catch (e) {} }
    if (res.socket && typeof res.socket.setNoDelay === "function") { try { res.socket.setNoDelay(true); } catch (e2) {} }
    var padLine = ":" + new Array(65).join(" ") + "\n";
    var pad = "";
    while (pad.length < 2048) pad += padLine;
    res.write(pad);
    var info = bb3bAskInfo(body);
    var base = info.peer ? info.base : null;
    var peers = bb3bArr(typeof BB2_PEERS !== "undefined" && BB2_PEERS ? BB2_PEERS[base] : []);
    var syms = base ? [base].concat(peers).slice(0, 6) : [];
    var built = null;
    var vals = syms.length ? bb3bReadCache(syms) : null;
    if (vals && typeof bb2BuildFacts === "function") {
      try { built = bb2BuildFacts(base, vals); } catch (e4) { built = null; }
    }
    var sources = bb3bFilterSources(bb3bRawSources(body), body);
    function addYahoo() {
      var factsNow = bb3bArr(built && built.facts);
      if (!factsNow.length || typeof bb2PeerSource !== "function") return 0;
      if (!sources.some(function (src) { return src && src.name === "Yahoo Finance"; })) sources.push(bb2PeerSource(base, built));
      return sources.length;
    }
    var cite = addYahoo();
    var facts = bb3bArr(built && built.facts);
    var lead = typeof bb3LeadText === "function" ? bb3LeadText(built, cite) : "";
    if (lead) { acc += lead; send({ t: lead }, "lead"); }
    else if (base) { var note = "Fetching latest valuations.\n\n"; acc += note; send({ t: note }, "status"); }
    var pendingLead = null;
    if (syms.length && typeof bb2Refresh === "function") {
      var job = null;
      try { job = bb2Refresh(syms); } catch (e5) { job = null; }
      if (job && typeof job.then === "function") {
        if (!built) {
          pendingLead = Promise.race([
            job.then(function () { return "up"; }).catch(function () { return "up"; }),
            new Promise(function (r) { setTimeout(function () { r("slow"); }, 800); })
          ]).then(function (up) {
            if (up !== "up") { if (job && typeof job.catch === "function") job.catch(function () {}); return; }
            vals = bb3bReadCache(syms);
            if (!(vals && typeof bb2BuildFacts === "function")) return;
            try { built = bb2BuildFacts(base, vals); } catch (e6) { return; }
            facts = bb3bArr(built && built.facts);
            cite = addYahoo();
            if (store) {
              store.facts = facts;
              store.bb3Built = built || { facts: facts, asOf: "" };
              store.clientSources = sources.filter(function (src) { return !(src && src.name === "Yahoo Finance"); });
              var late = sources.length ? sources[sources.length - 1] : null;
              store.peerSource = (late && late.name === "Yahoo Finance") ? late : null;
            }
            lead = typeof bb3LeadText === "function" ? bb3LeadText(built, cite) : "";
            if (lead) { acc += lead; send({ t: lead }, "lead"); }
          });
        } else if (typeof job.catch === "function") job.catch(function () {});
      }
    }
    var store = (typeof bb2Als !== "undefined" && bb2Als && bb2Als.getStore) ? bb2Als.getStore() : null;
    if (store) {
      store.facts = facts;
      store.bb3Built = built || { facts: facts, asOf: built && built.asOf || "" };
      store.clientSources = sources.filter(function (src) { return !(src && src.name === "Yahoo Finance"); });
      var lastSrc = sources.length ? sources[sources.length - 1] : null;
      store.peerSource = (lastSrc && lastSrc.name === "Yahoo Finance") ? lastSrc : null;
      store.body = body;
    }
    var buf = "";
    function emitModel(text) {
      var s = String(text || "");
      if (!s.trim() || bb3bMarkerOnly(s)) return;
      if (acc && !/\n$/.test(acc) && !/^\n/.test(s)) s = "\n" + s;
      acc += s;
      send({ t: s }, "model");
    }
    function pump(force) {
      var pending = "";
      var lines = String(buf || "").split("\n");
      if (!force && buf && buf.charAt(buf.length - 1) !== "\n") pending = lines.pop();
      var emitLines = [], holdLines = [], holding = false;
      for (var n = 0; n < lines.length; n++) {
        var line = lines[n];
        if (bb3bIntro(line) || bb3bItem(line) || bb3bMarkerOnly(line)) holding = true;
        if (holding) holdLines.push(line);
        else emitLines.push(line);
      }
      if (holding && !force) {
        buf = holdLines.join("\n") + (holdLines.length ? "\n" : "") + pending;
        if (emitLines.length) emitModel(bb3bRewrite(emitLines.join("\n") + "\n", facts, true));
        return;
      }
      var all = emitLines.concat(holdLines);
      if (pending && !force) buf = pending;
      else { if (pending) all.push(pending); buf = ""; }
      if (all.length) emitModel(bb3bRewrite(all.join("\n") + (buf ? "\n" : ""), facts, true));
      if (buf && !force && !bb3bHold(buf, facts)) { var open = buf; buf = ""; emitModel(open); }
    }
    try {
      var askBody = bb3bTrimBody(body);
      var system = typeof bb2System === "function" ? bb2System(askBody, built, sources) : "";
      if (typeof bb2Complete === "function") meta = await bb2Complete(system, askBody && askBody.messages, function (d) { buf += d; pump(false); }) || meta;
    } catch (e7) {
      if (!acc.trim()) { send({ error: "unavailable" }); send({ done: true, reply: "", meta: { provider: "Dispatch", model: "comparison", streamed: false }, sources: [] }); res.end(); console.warn("bb3b stream error", bb3bStack(e7)); return; }
    }
    if (pendingLead) { try { await pendingLead; } catch (e8) {} }
    pump(true);
    if (store) store.facts = facts;
    var clientSources = bb3bArr(store && store.clientSources);
    var citeN = store && store.peerSource ? (clientSources.length + 1) : 0;
    var reply = bb3bCompose(acc, store && store.bb3Built, citeN);
    var footSources = clientSources.slice();
    if (store && store.peerSource) footSources.push(store.peerSource);
    reply += typeof bb2Footer === "function" ? bb2Footer(footSources) : "";
    var srcAt = reply.indexOf("\n\nSources:");
    if (srcAt < 0) srcAt = reply.indexOf("\nSources:");
    if (srcAt >= 0 && acc.indexOf("Sources:") < 0) send({ t: reply.slice(srcAt) });
    send({ done: true, reply: reply, meta: { provider: meta.provider, model: meta.model, streamed: true }, sources: footSources });
    res.end();
    console.warn("bb3b chat model_ttft_ms", modelAt ? modelAt - t0 : -1, "total_ms", Date.now() - t0, "provider", meta && meta.provider || "Dispatch");
  } catch (err) {
    return fail(err);
  }
}
try {
  if (typeof rt20sWrapResponse === "function" && !rt20sWrapResponse.__bb3b) {
    var bb3bWrap0 = rt20sWrapResponse;
    rt20sWrapResponse = function (req, res) {
      try {
        var headers = (req && req.headers) || {};
        var accept = String(headers.accept || headers.Accept || "");
        var flag = String(headers["x-dispatch-stream"] || headers["X-Dispatch-Stream"] || "");
        var host = headers.host || headers.Host || "localhost";
        var url = new URL((req && req.url) || "/", "http://" + host);
        if (req && req.method === "POST" && url.pathname === "/api/chat" && (/text\/event-stream/i.test(accept) || flag === "1")) return;
      } catch (e) {}
      return bb3bWrap0.apply(this, arguments);
    };
    rt20sWrapResponse.__bb3b = true;
  }
  bb2ClientSources = function (body) { return bb3bFilterSources(bb3bRawSources(body), body); };
  bb2Rewrite = function (text, facts) { return bb3bRewrite(text, bb3bArr(facts), false); };
  bb2Lead = function (built, cite) { return typeof bb3LeadText === "function" ? bb3LeadText(built, cite) : ""; };
  bb2Finish = function (reply, store) {
    var facts = bb3bArr(store && store.facts);
    var built = (store && store.bb3Built) || { facts: facts, asOf: "" };
    var cite = store && store.peerSource ? (bb3bArr(store.clientSources).length + 1) : 0;
    var text = bb3bCompose(reply, built.facts ? built : { facts: facts, asOf: built.asOf || "" }, cite);
    var sources = bb3bArr(store && store.clientSources).slice();
    if (store && store.peerSource) sources.push(store.peerSource);
    return text + (typeof bb2Footer === "function" ? bb2Footer(sources) : "");
  };
  if (typeof bb2System === "function") {
    var bb3bSystem0 = bb2System;
    bb2System = function (body, built, sources) {
      return bb3bSystem0.call(this, bb3bTrimBody(body), built, bb3bArr(sources)) + "\n\nThe peer comparison lines are already on screen. Do not repeat them as a paragraph, a numbered list, or bullets. Do not restate a peer P/E. Add only other context.";
    };
  }
  bb2StreamInner = bb3bStreamInner;
} catch (e) { console.warn("bb3b hooks skipped", e && e.message); }
// BB3B_JS_END
'''

v = v.rstrip("\n") + "\n" + BLOCK
for anchor in BB4_KEEP:
    if v.count(anchor) != 1:
        die("bb4daily xAI skip was modified: %r" % anchor)
if "_bb4d" in BLOCK or "BB4D_AI" in BLOCK or "academy-daily" in BLOCK:
    die("bb3b block mentions academy-daily")

old_bust = 'app.js?v=chat%d"' % chat_n
new_bust = 'app.js?v=chat%d"' % (chat_n + 1)
if s != load(APP)[0] or h != load(IDX)[0]:
    if h.count(old_bust) != 1:
        die("index.html cache buster %s matched %d times" % (old_bust, h.count(old_bust)))
    h = h.replace(old_bust, new_bust, 1)
    print("index chat%d -> chat%d" % (chat_n, chat_n + 1))
else:
    print("index chat%d unchanged" % chat_n)

def nodecheck(src, label):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as t:
        t.write(src)
        tmp = t.name
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    os.unlink(tmp)
    if r.returncode:
        die("node --check failed for %s: %s" % (label, r.stderr[:500]))

nodecheck(v, "server.js")
nodecheck(s, "app.js")
print("node --check passed" + (" (dry run)" if CHECK else ""))
after_app = encode(s, crlf)
after_idx = encode(h, hcrlf)
after_srv = encode(v, vcrlf)
show("after", APP, after_app)
show("after", IDX, after_idx)
show("after", SRV, after_srv)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

baks = [(APP, after_app), (IDX, after_idx), (SRV, after_srv)]
written = []
try:
    for path, data in baks:
        bak = path + ".bb3bbak"
        open(bak, "wb").write(open(path, "rb").read())
        open(path, "wb").write(data)
        written.append((path, bak))
    r = subprocess.run(["node", "--check", SRV], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("node --check failed after write: " + r.stderr[:400])
    r2 = subprocess.run(["node", "--check", APP], capture_output=True, text=True)
    if r2.returncode:
        raise RuntimeError("node --check failed after write for app.js: " + r2.stderr[:400])
    for path, bak in written:
        os.unlink(bak)
except Exception as e:
    for path, bak in written:
        if os.path.exists(bak):
            open(path, "wb").write(open(bak, "rb").read())
            os.unlink(bak)
    print("ABORT: write failed; backup restored:", e)
    sys.exit(1)
print("APPLY bb3b stream guard, list drop, flush, provider order")
