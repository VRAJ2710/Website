const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const {
  CANONICAL_ORIGIN,
  canonicalRedirectLocation,
  clearSessionCookieHeader,
  configuredPublicOrigin,
  isServableStaticPath,
  isStripeWebhookPath,
  publicUrl,
  resolveStaticFile,
  sessionCookieHeader,
  webhookBaseUrl,
  writeCanonicalRedirect,
} = require("../billingOrigin");
const { startCheckout } = require("../startCheckout");

function req(host, url = "/", extraHeaders = {}) {
  return { headers: { host, ...extraHeaders }, url };
}

test("pins Stripe return URLs to apex even when DISPATCH_PUBLIC_ORIGIN is www", () => {
  const env = {
    DISPATCH_PUBLIC_ORIGIN: "https://www.thedispatch.uk",
    REPLIT_DOMAINS: "example.replit.app",
  };
  assert.equal(configuredPublicOrigin(env), CANONICAL_ORIGIN);
  assert.equal(publicUrl(req("thedispatch.uk"), { env }), CANONICAL_ORIGIN);
  assert.equal(publicUrl(req("www.thedispatch.uk"), { env }), CANONICAL_ORIGIN);
  assert.equal(publicUrl(req("example.replit.app"), { env }), CANONICAL_ORIGIN);
  assert.equal(webhookBaseUrl(env), CANONICAL_ORIGIN);
});

test("does not let REPLIT_DOMAINS win on a Dispatch host", () => {
  const env = { REPLIT_DOMAINS: "example.replit.app" };
  assert.equal(publicUrl(req("thedispatch.uk", "/", { "x-forwarded-proto": "https" }), { env }), CANONICAL_ORIGIN);
  assert.equal(
    publicUrl(req("preview.replit.dev"), { env }),
    "http://preview.replit.dev",
  );
  assert.equal(
    publicUrl({ headers: {} }, { env, port: 5000 }),
    "https://example.replit.app",
  );
});

test("308s www to apex while preserving path and query", () => {
  assert.equal(
    canonicalRedirectLocation(req("www.thedispatch.uk", "/?checkout=1")),
    "https://thedispatch.uk/?checkout=1",
  );
  assert.equal(canonicalRedirectLocation(req("thedispatch.uk", "/?checkout=1")), null);
  assert.equal(canonicalRedirectLocation(req("localhost:5000", "/")), null);

  const headers = {};
  let status;
  let ended = false;
  const res = {
    writeHead(code, next) { status = code; Object.assign(headers, next); },
    end() { ended = true; },
  };
  assert.equal(writeCanonicalRedirect(req("www.thedispatch.uk", "/__auth/subscribe"), res), true);
  assert.equal(status, 308);
  assert.equal(headers.Location, "https://thedispatch.uk/__auth/subscribe");
  assert.equal(ended, true);
  assert.equal(writeCanonicalRedirect(req("thedispatch.uk", "/"), {
    writeHead() { throw new Error("apex must not redirect"); },
    end() {},
  }), false);
});

test("sets Secure and Domain cookies on production hosts only", () => {
  const prod = sessionCookieHeader("abc", req("thedispatch.uk", "/", { "x-forwarded-proto": "https" }));
  assert.match(prod, /dispatch_session=abc/);
  assert.match(prod, /Secure/);
  assert.match(prod, /Domain=thedispatch.uk/);
  assert.match(prod, /HttpOnly/);
  assert.match(prod, /SameSite=Lax/);

  const www = sessionCookieHeader("abc", req("www.thedispatch.uk"));
  assert.match(www, /Secure/);
  assert.match(www, /Domain=thedispatch.uk/);

  const local = sessionCookieHeader("abc", req("127.0.0.1:5000"));
  assert.equal(local.includes("Secure"), false);
  assert.equal(local.includes("Domain="), false);

  const cleared = clearSessionCookieHeader(req("thedispatch.uk", "/", { "x-forwarded-proto": "https" }));
  assert.match(cleared, /Max-Age=0/);
  assert.match(cleared, /Domain=thedispatch.uk/);
  assert.match(cleared, /Secure/);
});

test("hides server source and serves only public assets", () => {
  const root = path.join(__dirname, "..");
  assert.equal(isServableStaticPath("/"), true);
  assert.equal(isServableStaticPath("/app.js"), true);
  assert.equal(isServableStaticPath("/styles.css"), true);
  assert.equal(isServableStaticPath("/server.js"), false);
  assert.equal(isServableStaticPath("/stripeClient.js"), false);
  assert.equal(isServableStaticPath("/package.json"), false);
  assert.equal(isServableStaticPath("/.replit"), false);
  assert.equal(isServableStaticPath("/billingOrigin.js"), false);
  assert.equal(resolveStaticFile(root, "/server.js"), null);
  assert.equal(resolveStaticFile(root, "/app.js"), path.normalize(path.join(root, "app.js")));
  assert.equal(resolveStaticFile(root, "/"), path.normalize(path.join(root, "index.html")));
});

test("documents the Stripe webhook path and accepts the common alias", () => {
  assert.equal(isStripeWebhookPath("/api/stripe/webhook"), true);
  assert.equal(isStripeWebhookPath("/api/stripe-webhook"), true);
  assert.equal(isStripeWebhookPath("/api/stripe_webhook"), false);
});

test("startCheckout always includes credentials and reuses /api/me.checkoutSession", async () => {
  const calls = [];
  const assigned = [];
  const fetchImpl = async (url, options = {}) => {
    calls.push({ url, options });
    if (url === "/api/create-checkout") {
      assert.equal(options.credentials, "include");
      return {
        status: 401,
        json: async () => ({ error: "Sign in before starting checkout." }),
      };
    }
    if (url === "/api/me") {
      assert.equal(options.credentials, "include");
      return {
        ok: true,
        json: async () => ({ id: "user-1", checkoutSession: { url: "https://checkout.stripe.com/reuse" } }),
      };
    }
    throw new Error(`unexpected fetch ${url}`);
  };

  const result = await startCheckout({
    fetchImpl,
    locationAssign: url => assigned.push(url),
  });
  assert.equal(result.ok, true);
  assert.equal(result.reused, true);
  assert.deepEqual(assigned, ["https://checkout.stripe.com/reuse"]);
  assert.equal(calls.length, 2);
});

test("startCheckout does not bounce a signed-in member to subscribe", async () => {
  const assigned = [];
  const result = await startCheckout({
    fetchImpl: async url => {
      if (url === "/api/create-checkout") {
        return { status: 401, json: async () => ({ error: "Sign in before starting checkout." }) };
      }
      return { ok: true, json: async () => ({ id: "user-1", tier: "free" }) };
    },
    locationAssign: url => assigned.push(url),
  });
  assert.equal(result.ok, false);
  assert.equal(result.signedIn, true);
  assert.deepEqual(assigned, []);
});

test("app.js _startCheckout includes credentials and reuses /api/me.checkoutSession", () => {
  const src = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
  const start = src.indexOf("async function _startCheckout");
  const end = src.indexOf("async function runPortfolioAI");
  assert.ok(start >= 0 && end > start, "expected _startCheckout in app.js");
  const fn = src.slice(start, end);
  assert.match(fn, /credentials:\s*['"]include['"]/);
  assert.match(fn, /\/api\/me/);
  assert.match(fn, /checkoutSession/);
  assert.match(fn, /me\?\.id/);
});

test("startCheckout sends guests to subscribe only when /api/me has no account", async () => {
  const assigned = [];
  const result = await startCheckout({
    fetchImpl: async url => {
      if (url === "/api/create-checkout") {
        return { status: 401, json: async () => ({ error: "Sign in before starting checkout." }) };
      }
      return { ok: true, json: async () => ({ tier: "free", billingPortal: false }) };
    },
    locationAssign: url => assigned.push(url),
  });
  assert.equal(result.redirect, "/__auth/subscribe");
  assert.deepEqual(assigned, ["/__auth/subscribe"]);
});
