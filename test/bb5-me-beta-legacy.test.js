const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const PATCH = path.join(__dirname, "..", "deploy", "patch_bb5.py");
const LEAK = /cs_(live|test)_|cus_|sub_/;
const SENTENCE = "MU 11.8x is slightly higher than WDC's 12.3x.";
const FACTS = [{
  a: "MU",
  b: "WDC",
  basis: "trailing",
  dir: "lower",
  va: 11.8,
  vb: 12.3,
  sentence: "MU trailing P/E (TTM) 11.8x is lower than WDC trailing P/E (TTM) 12.3x by 0.5x (4.1%)."
}];

function extractJs() {
  const src = fs.readFileSync(PATCH, "utf8");
  const m = src.match(/\/\/ BB5_JS\n([\s\S]*?)\n\/\/ BB5_JS_END/);
  assert.ok(m, "BB5_JS block missing");
  const js = m[1];
  assert.equal(/CREATE TABLE|setInterval\(|node-cron|stripe\.webhooks|function bb3Tickers/.test(js), false);
  assert.equal(js.includes('tier === "premium"'), false);
  assert.equal(js.includes("tier === 'premium'"), false);
  const names = [...js.matchAll(/(?:^|\n)\s*(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(/g)].map(x => x[1]);
  assert.ok(names.length > 0);
  names.forEach(name => assert.equal(name.startsWith("bb5"), true, name));
  const seen = new Set();
  names.forEach(name => {
    assert.equal(seen.has(name), false, name);
    seen.add(name);
  });
  return js;
}

function load(extra) {
  const context = {
    console,
    Date,
    Math,
    Number,
    String,
    Object,
    Array,
    isFinite,
    globalThis: {},
    isAdminUser: user => !!(user && user._admin === true),
    hasPremiumAccess: user => Boolean(user && (user.tier === "premium" || (user && user._admin === true))),
    ...(extra || {})
  };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(extractJs(), context, { filename: "bb5.js" });
  return context;
}

function leaked(value) {
  return LEAK.test(JSON.stringify(value));
}

const SECRET = {
  passwordHash: "hash",
  stripeCustomerId: "cus_live_abc123",
  stripeSubscriptionId: "sub_live_def456",
  checkoutSession: { url: "https://checkout.stripe.com/c/pay/cs_live_secret", expiresAt: 1 },
  checkoutAttemptId: "cs_test_attempt"
};

test("each role gets only allowlisted keys and admin keeps premium access", () => {
  const s = load();
  const guest = s.bb5PublicUser(null);
  assert.deepEqual(Object.keys(guest).sort(), ["billingPortal", "guest", "isAdmin", "tier"]);
  assert.equal(leaked(guest), false);
  assert.equal(s.hasPremiumAccess(null), false);

  const freeUser = { id: "free-1", email: "free@example.com", tier: "free", billingPortal: false, _admin: false, ...SECRET };
  const free = s.bb5PublicUser(freeUser);
  assert.equal(JSON.stringify(Object.keys(free).sort()), JSON.stringify(["billingPortal", "email", "id", "isAdmin", "tier"]));
  assert.equal(free.email, "free@example.com");
  assert.equal(free.isAdmin, false);
  assert.equal(s.hasPremiumAccess(freeUser), false);
  assert.equal(leaked(free), false);

  const premUser = { id: "prem-1", email: "prem@example.com", tier: "premium", billingPortal: true, _admin: false, ...SECRET };
  const prem = s.bb5PublicUser(premUser);
  assert.equal(JSON.stringify(Object.keys(prem).sort()), JSON.stringify(["billingPortal", "email", "id", "isAdmin", "tier"]));
  assert.equal(prem.tier, "premium");
  assert.equal(prem.billingPortal, true);
  assert.equal(s.hasPremiumAccess(premUser), true);
  assert.equal(leaked(prem), false);

  const adminUser = { id: "admin-1", email: "admin@example.com", tier: "free", billingPortal: false, _admin: true, ...SECRET };
  const admin = s.bb5PublicUser(adminUser);
  assert.equal(JSON.stringify(Object.keys(admin).sort()), JSON.stringify(["billingPortal", "email", "id", "isAdmin", "tier"]));
  assert.equal(admin.isAdmin, true);
  assert.equal(admin.tier, "free");
  assert.equal(s.hasPremiumAccess(adminUser), true);
  assert.equal(leaked(admin), false);
  assert.equal(JSON.stringify(admin).includes("passwordHash"), false);
});

test("Yahoo summaryDetail.beta replaces the desk 1.62 and MU's score stays put", async () => {
  const s = load();
  assert.equal(s.bb5PublishedBeta({ summaryDetail: { beta: { raw: 2.23 } }, defaultKeyStatistics: { beta: { raw: 9.9 } } }), 2.23);
  assert.equal(s.bb5PublishedBeta({ defaultKeyStatistics: { beta: { raw: 2.23 } } }), null);
  assert.equal(s.bb5Sens(1.62, true), -12);
  assert.equal(s.bb5Sens(2.23, true), -12);
  assert.equal(s.bb5Sens(1.62, false), 0);
  assert.equal(s.bb5Sens(2.23, false), 0);
  s.globalThis.bb5BetaTest = { MU: { beta: 2.23, asOf: "2026-10-18T20:00:00.000Z" } };
  const hit = await s.bb5LoadBeta("MU");
  assert.equal(hit.beta, 2.23);
  const profile = s.bb5ApplyProfile({ stance: "positive", cat: "other", beta: 1.62, known: true }, hit);
  assert.equal(profile.beta, 2.23);
  assert.equal(profile.bb5Yahoo, true);
  const fit = s.bb5TagBeta({
    score: 56,
    inputs: [{ key: "sensitivity", label: "How sharply this name moves when the market falls", value: 1.62, unit: "times the market", source: "Dispatch desk reference", asOf: "desk", contribution: -12 }]
  }, profile);
  const row = fit.inputs[0];
  assert.equal(row.value, 2.23);
  assert.equal(row.source, "5y monthly beta, Yahoo");
  assert.equal(row.asOf, "2026-10-18T20:00:00.000Z");
  assert.equal(row.unit, "times the market");
  assert.equal(fit.score, 56);
});

test("legacy reply corrects or removes the wrong MU vs WDC direction", async () => {
  const dropping = load({
    bb3bRewrite: (text, facts, drop) => {
      assert.equal(drop, true);
      const hit = facts.some(f => f && f.a === "MU" && f.b === "WDC");
      return hit && /slightly higher/i.test(text) ? "" : text;
    }
  });
  const removed = dropping.bb5RewriteReply(SENTENCE, FACTS);
  assert.equal(/slightly higher/i.test(removed), false);
  assert.equal(removed.includes(SENTENCE), false);

  const correcting = load({
    bb2FixSentence: (text, facts) => {
      const fact = facts.find(f => f && f.a === "MU" && f.b === "WDC" && f.basis === "trailing");
      if (/slightly higher/i.test(text) && fact && fact.dir === "lower") return fact.sentence;
      if (/trailing/i.test(text) && /forward/i.test(text)) return "Trailing P/E (TTM) and forward P/E are different bases and are not compared.";
      return text;
    }
  });
  const fixed = correcting.bb5RewriteReply(SENTENCE, FACTS);
  assert.equal(/slightly higher/i.test(fixed), false);
  assert.match(fixed, /lower than WDC trailing P\/E \(TTM\) 12\.3x/);
  const mixed = correcting.bb5RewriteReply("MU trailing P/E 11.8x is higher than WDC forward P/E 10.0x.", FACTS);
  assert.match(mixed, /different bases and are not compared/);
  assert.equal(/forward P\/E 10\.0x/.test(mixed), false);

  const wired = load({
    bb2Question: body => body && body.q || "",
    bb2PeerAsk: q => /peer/i.test(q),
    bb2Als: { getStore: () => ({ facts: FACTS.slice() }) },
    bb3bRewrite: (text, facts, drop) => (drop && /slightly higher/i.test(text) ? "" : text)
  });
  const live = await wired.bb5LegacyReply(SENTENCE, { q: "How does MU compare with its peers?" });
  assert.equal(/slightly higher/i.test(live), false);
  const other = await wired.bb5LegacyReply("Gold was firm.", { q: "What did gold do today?" });
  assert.equal(other, "Gold was firm.");
});
