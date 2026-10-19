const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const PATCH = path.join(__dirname, "..", "deploy", "patch_bb5c.py");
const LEAK = /cs_(live|test)_|cus_|sub_/;
const SIGNED = ["billingPortal", "email", "id", "isAdmin", "tier"];

function extractJs() {
  const src = fs.readFileSync(PATCH, "utf8");
  const m = src.match(/\/\/ BB5C_JS\n([\s\S]*?)\n\/\/ BB5C_JS_END/);
  assert.ok(m, "BB5C_JS block missing");
  const js = m[1];
  assert.equal(/CREATE TABLE|setInterval\(|stripe\.webhooks|tier === "premium"|tier === 'premium'/.test(js), false);
  const names = [...js.matchAll(/(?:^|\n)\s*(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(/g)].map(x => x[1]);
  assert.deepEqual(names, ["bb5cPublicUser"]);
  return js;
}

function load() {
  const context = {
    console,
    String,
    Boolean,
    isAdminUser: user => !!(user && user._admin === true),
    hasPremiumAccess: user => Boolean(user && (user.tier === "premium" || (user && user._admin === true)))
  };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(extractJs(), context, { filename: "bb5c.js" });
  return context;
}

const SECRET = {
  passwordHash: "hash",
  stripeCustomerId: "cus_live_abc123",
  stripeSubscriptionId: "sub_live_def456",
  checkoutSession: { url: "https://checkout.stripe.com/c/pay/cs_live_secret", expiresAt: 1 },
  checkoutAttemptId: "cs_test_attempt"
};

function keys(value) {
  return JSON.stringify(Object.keys(value).sort());
}

test("admin with a free database tier is premium on /api/me, and other roles stay put", () => {
  const s = load();
  const guest = s.bb5cPublicUser(null);
  assert.equal(JSON.stringify(guest), JSON.stringify({ guest: true, tier: "free", billingPortal: false, isAdmin: false }));
  assert.equal(LEAK.test(JSON.stringify(guest)), false);

  const admin = s.bb5cPublicUser({ id: "admin-1", email: "owner@example.com", tier: "free", billingPortal: false, _admin: true, ...SECRET });
  assert.equal(admin.tier, "premium");
  assert.equal(admin.isAdmin, true);
  assert.equal(admin.billingPortal, false);
  assert.equal(keys(admin), JSON.stringify(SIGNED));
  assert.equal(LEAK.test(JSON.stringify(admin)), false);

  const premium = s.bb5cPublicUser({ id: "prem-1", email: "paid@example.com", tier: "premium", billingPortal: true, _admin: false, ...SECRET });
  assert.equal(premium.tier, "premium");
  assert.equal(premium.isAdmin, false);
  assert.equal(premium.billingPortal, true);
  assert.equal(keys(premium), JSON.stringify(SIGNED));
  assert.equal(LEAK.test(JSON.stringify(premium)), false);

  const free = s.bb5cPublicUser({ id: "free-1", email: "free@example.com", tier: "free", billingPortal: false, _admin: false, ...SECRET });
  assert.equal(free.tier, "free");
  assert.equal(free.isAdmin, false);
  assert.equal(free.billingPortal, false);
  assert.equal(keys(free), JSON.stringify(SIGNED));
  assert.equal(LEAK.test(JSON.stringify(free)), false);

  const empty = s.bb5cPublicUser({});
  assert.equal(JSON.stringify(empty), JSON.stringify(guest));
});
