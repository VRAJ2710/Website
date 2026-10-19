#!/usr/bin/env python3
"""patch_bb5.py — /api/me allowlist, one Yahoo beta, legacy comparison rewrite.

Chat62 is chat61 plus bb3b. Expected md5s are that trio; a mismatch warns
and does not abort. Already applied exits 0. app.js changes, so
app.js?v=chatN bumps one step (chat62 -> chat63).

/api/me was publicUser(), which spread every column except the password
hash. That included checkoutSession.url (cs_live_…), stripeCustomerId and
stripeSubscriptionId. The client reads id, email, tier, billingPortal and
isAdmin. Email stays because Settings prints it (account row and the
newsletter "Send to" line) from window._tdMeEmail. Upgrade already POSTs
/api/create-checkout; the client no longer reads a checkout URL from /api/me.

Fit sensitivity used BB3_ROWS (MU 1.62, "times the market", "Dispatch desk
reference"). The stock page shows valuation.beta from GET /api/financials,
which is quoteSummary.summaryDetail.beta (Yahoo's 5y monthly beta). Both
now use that field. The fit input source is "5y monthly beta, Yahoo" with
the fetch asOf. The score formula is unchanged: beta above 1.5 takes 12
points when the mood is below 60. 1.62 and 2.23 are both above 1.5, so
MU's score does not change.

The legacy JSON /api/chat reply is passed through bb3bRewrite (the stream
rewriter) with peer facts before it is returned. A wrong-direction
comparison is dropped or replaced. Trailing and forward P/E stay separate.

Every new top-level name starts with bb5. This patch does not declare
function bb3Tickers or any other existing function. No new tables, no
cron, no Stripe product, price or webhook edits.

Usage: python3 patch_bb5.py [--check] <dir with app.js, index.html, server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "99e60c7a6b9ddfc9ed2bf0bc090c95f7",
    "index.html": "cb0d4fc6e9f337f879a17478693dbf44",
    "server.js": "3f547a578132675b217229c332bf7754",
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
    print("bb5 %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
    return digest

def encode(text, use_crlf):
    return (text.replace("\n", "\r\n") if use_crlf else text).encode("utf-8")

s, crlf = load(APP)
h, hcrlf = load(IDX)
v, vcrlf = load(SRV)
orig_s, orig_h = s, h

for path in (APP, IDX, SRV):
    digest = show("before", path)
    expect = EXPECTED_MD5.get(os.path.basename(path)) or ""
    if expect and digest != expect:
        print("WARN md5 %s: have %s expected %s (anchors still decide)" % (os.path.basename(path), digest, expect))

if "// \u2500\u2500 bb5 \u2500\u2500" in v:
    print("REFUSE: bb5 already applied")
    sys.exit(0)

miss = []
if "// \u2500\u2500 bb3b \u2500\u2500" not in v:
    miss.append("server.js marker missing: // ── bb3b ──")
if "// \u2500\u2500 bb3fit \u2500\u2500" not in v:
    miss.append("server.js marker missing: // ── bb3fit ──")
chat_hits = re.findall(r'app\.js\?v=chat(\d+)"', h)
chat_n = None
if len(chat_hits) != 1:
    miss.append('index.html marker missing: app.js?v=chatNN" (found %d)' % len(chat_hits))
else:
    chat_n = int(chat_hits[0])
    if chat_n < 62:
        miss.append("index.html is chat%d; need chat62 or later" % chat_n)

anchors = [
    ("server.js", v, "function publicUser(user) {"),
    ("server.js", v, "async function bb3Compute(ticker, now) {"),
    ("server.js", v, "function bb3Profile(ticker) {"),
    ("server.js", v, "function bb3Assemble(ticker, profile, mood, session, spy, nowMs, sessionAsOfMs, spyAsOfMs) {"),
    ("server.js", v, "reply: answer.reply,"),
    ("app.js", s, "if(me?.checkoutSession?.url){window.location.href=me.checkoutSession.url;return;}"),
]
for label, src, anchor in anchors:
    if src.count(anchor) != 1:
        miss.append("%s anchor %r matched %d times" % (label, anchor, src.count(anchor)))
if miss:
    print("ABORT (nothing written):")
    for item in miss:
        print("ABORT:", item)
    sys.exit(1)

OLD_PUBLIC = """function publicUser(user) {
  if (!user) return { tier: "free", billingPortal: false };
  const { passwordHash, ...safeUser } = user;
  return { ...safeUser, isAdmin: isAdminUser(user) };
}"""
NEW_PUBLIC = """function publicUser(user) {
  return bb5PublicUser(user);
}"""
if v.count(OLD_PUBLIC) != 1:
    die("server.js publicUser body matched %d times" % v.count(OLD_PUBLIC))
v = v.replace(OLD_PUBLIC, NEW_PUBLIC, 1)

OLD_REPLY = "          reply: answer.reply,"
NEW_REPLY = "          reply: await bb5LegacyReply(answer.reply, body),"
if v.count(OLD_REPLY) != 1:
    die("server.js legacy reply anchor matched %d times" % v.count(OLD_REPLY))
v = v.replace(OLD_REPLY, NEW_REPLY, 1)

OLD_CHECKOUT = "        if(me?.checkoutSession?.url){window.location.href=me.checkoutSession.url;return;}\n"
NEW_CHECKOUT = "        // bb5: the upgrade click already POSTed /api/create-checkout. Do not read a session URL from /api/me.\n"
if s.count(OLD_CHECKOUT) != 1:
    die("app.js checkout URL anchor matched %d times" % s.count(OLD_CHECKOUT))
s = s.replace(OLD_CHECKOUT, NEW_CHECKOUT, 1)

BLOCK = r'''
// ── bb5 ── Allowlist /api/me, one Yahoo 5y monthly beta, legacy comparison rewrite.
// BB5_JS
var bb5BetaMem = {};
var bb5MeKeys = ["id", "email", "tier", "billingPortal", "isAdmin"];
function bb5PublicUser(user) {
  if (!user || !user.id) return { guest: true, tier: "free", billingPortal: false, isAdmin: false };
  var admin = typeof isAdminUser === "function" ? isAdminUser(user) === true : false;
  var out = {
    id: String(user.id),
    email: typeof user.email === "string" ? user.email : "",
    tier: typeof user.tier === "string" ? user.tier : "free",
    billingPortal: user.billingPortal === true,
    isAdmin: admin
  };
  return out;
}
function bb5BetaRaw(v) {
  if (v && typeof v === "object") return bb5BetaRaw(v.raw != null ? v.raw : v.fmt);
  var n = Number(v);
  return isFinite(n) ? Math.round(n * 100) / 100 : null;
}
function bb5PublishedBeta(quote) {
  var sd = quote && quote.summaryDetail;
  return bb5BetaRaw(sd && sd.beta);
}
function bb5Sens(beta, wary) {
  var n = Number(beta);
  if (!isFinite(n)) return 0;
  return wary && n > 1.5 ? -12 : 0;
}
async function bb5LoadBeta(ticker) {
  var key = String(ticker || "").toUpperCase();
  if (!key) return null;
  var hit = bb5BetaMem[key];
  if (hit && hit.beta != null && Date.now() - hit.at < 3600000) return hit;
  var box = typeof globalThis !== "undefined" ? globalThis.bb5BetaTest : null;
  if (box && Object.prototype.hasOwnProperty.call(box, key)) {
    var forced = box[key];
    var trial = { beta: bb5BetaRaw(forced && forced.beta != null ? forced.beta : forced), asOf: (forced && forced.asOf) || "", at: Date.now() };
    if (trial.beta == null) return null;
    bb5BetaMem[key] = trial;
    return trial;
  }
  var quote = null;
  try {
    if (typeof rt32Yahoo === "function") quote = await rt32Yahoo(key.replace(/\./g, "-"));
  } catch (e) { quote = null; }
  var beta = bb5PublishedBeta(quote);
  if (beta == null) return null;
  var saved = { beta: beta, asOf: new Date().toISOString(), at: Date.now() };
  bb5BetaMem[key] = saved;
  return saved;
}
function bb5ApplyProfile(row, hit) {
  row = row || { stance: "none", cat: "other", beta: null, known: false };
  if (!hit || hit.beta == null || !isFinite(Number(hit.beta))) return row;
  return { stance: row.stance, cat: row.cat, beta: hit.beta, known: row.known === true, bb5Yahoo: true, bb5AsOf: hit.asOf || "" };
}
function bb5TagBeta(fit, profile) {
  if (!fit || !profile || profile.bb5Yahoo !== true || !fit.inputs) return fit;
  var rows = fit.inputs;
  for (var i = 0; i < rows.length; i++) {
    var row = rows[i];
    if (!row || row.key !== "sensitivity") continue;
    row.value = profile.beta;
    row.unit = "times the market";
    row.source = "5y monthly beta, Yahoo";
    if (profile.bb5AsOf) row.asOf = profile.bb5AsOf;
  }
  return fit;
}
function bb5RewriteReply(text, facts) {
  var list = Array.isArray(facts) ? facts : [];
  var out = String(text == null ? "" : text);
  if (typeof bb3bRewrite === "function") out = bb3bRewrite(out, list, true);
  else if (typeof bb3Rewrite === "function") out = bb3Rewrite(out, list, true);
  else if (typeof bb2Rewrite === "function") out = bb2Rewrite(out, list);
  if (typeof bb3Fix === "function") {
    var fixed = bb3Fix(out, list);
    if (typeof fixed === "string") out = fixed;
  } else if (typeof bb2FixSentence === "function") {
    var fixed2 = bb2FixSentence(out, list);
    if (typeof fixed2 === "string") out = fixed2;
  }
  return out;
}
async function bb5LegacyFacts(body, q) {
  var store = null;
  try { store = (typeof bb2Als !== "undefined" && bb2Als && bb2Als.getStore) ? bb2Als.getStore() : null; } catch (e) { store = null; }
  if (store && Array.isArray(store.facts) && store.facts.length) return store.facts;
  var base = typeof bb2Base === "function" ? bb2Base(q) : null;
  if (!base || typeof bb2BuildFacts !== "function" || typeof BB2_PEERS === "undefined" || !BB2_PEERS) return [];
  var peers = BB2_PEERS[base] || [];
  var syms = [base].concat(peers).slice(0, 6);
  if (typeof bb2Refresh === "function") { try { await bb2Refresh(syms); } catch (e2) {} }
  var vals = {};
  if (typeof bb3bReadCache === "function") {
    var cached = bb3bReadCache(syms);
    if (cached && typeof cached === "object") vals = cached;
  } else if (typeof bb2Mem !== "undefined" && bb2Mem && bb2Mem.vals && typeof bb2Mem.vals.get === "function") {
    for (var n = 0; n < syms.length; n++) {
      var hit = bb2Mem.vals.get(syms[n]);
      if (hit && hit.v) vals[syms[n]] = hit.v;
    }
  }
  var built = null;
  try { built = bb2BuildFacts(base, vals); } catch (e3) { built = null; }
  var facts = (built && built.facts) || [];
  if (store) {
    store.facts = facts;
    store.bb3Built = built || { facts: facts, asOf: "" };
    if (facts.length && !store.peerSource && typeof bb2PeerSource === "function") store.peerSource = bb2PeerSource(base, built);
  }
  return facts;
}
async function bb5LegacyReply(reply, body) {
  var text = String(reply == null ? "" : reply);
  try {
    var q = typeof bb2Question === "function" ? bb2Question(body) : "";
    if (typeof bb2PeerAsk === "function" && !bb2PeerAsk(q)) return text;
    var facts = await bb5LegacyFacts(body, q);
    text = bb5RewriteReply(text, facts);
  } catch (e) {}
  return text;
}
try {
  if (typeof bb3Compute === "function") {
    var bb5Compute0 = bb3Compute;
    bb3Compute = async function (ticker, now) {
      try { await bb5LoadBeta(ticker); } catch (e) {}
      return bb5Compute0.apply(this, arguments);
    };
  }
  if (typeof bb3Profile === "function") {
    var bb5Profile0 = bb3Profile;
    bb3Profile = function (ticker) {
      var row = bb5Profile0.apply(this, arguments);
      var hit = bb5BetaMem[String(ticker || "").toUpperCase()];
      return bb5ApplyProfile(row, hit);
    };
  }
  if (typeof bb3Assemble === "function") {
    var bb5Assemble0 = bb3Assemble;
    bb3Assemble = function (ticker, profile) {
      var fit = bb5Assemble0.apply(this, arguments);
      return bb5TagBeta(fit, profile);
    };
  }
} catch (e) { console.warn("bb5 fit hook skipped"); }
// BB5_JS_END
'''

declared = re.findall(r'(?:^|\n)\s*(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(', BLOCK)
bad = [name for name in declared if not name.startswith("bb5")]
if bad:
    die("bb5 block declares a non-bb5 function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb5 block repeats a function: %s" % ", ".join(dupes))
if "function bb3Tickers" in BLOCK or "stripe.webhooks" in BLOCK or "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK:
    die("bb5 block has a forbidden declaration")

v = v.rstrip("\n") + "\n" + BLOCK

client_changed = s != orig_s or h != orig_h
if client_changed:
    old_bust = 'app.js?v=chat%d"' % chat_n
    new_bust = 'app.js?v=chat%d"' % (chat_n + 1)
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

written = []
try:
    for path, data in ((APP, after_app), (IDX, after_idx), (SRV, after_srv)):
        bak = path + ".bb5bak"
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
print("APPLY bb5 me allowlist, yahoo beta, legacy comparison")
