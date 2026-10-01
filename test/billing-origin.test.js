const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const {
  CANONICAL_ORIGIN,
  canonicalRedirectLocation,
  clearSessionCookieHeader,
  configuredPublicOrigin,
  dispatchSessionTokens,
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
  assert.equal(
    canonicalRedirectLocation(req("the-dispatch.replit.app", "/__auth/login")),
    "https://thedispatch.uk/__auth/login",
  );
  assert.equal(
    canonicalRedirectLocation(req("the-dispatch.replit.app", "/markets/?x=1")),
    "https://thedispatch.uk/markets/?x=1",
  );
  assert.equal(canonicalRedirectLocation(req("preview.replit.dev", "/")), null);

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

  const replitHeaders = {};
  let replitStatus;
  assert.equal(writeCanonicalRedirect(req("the-dispatch.replit.app", "/markets/"), {
    writeHead(code, next) { replitStatus = code; Object.assign(replitHeaders, next); },
    end() {},
  }), true);
  assert.equal(replitStatus, 308);
  assert.equal(replitHeaders.Location, "https://thedispatch.uk/markets/");
});

test("clears host-only and Domain session cookies, then sets one Domain cookie", () => {
  const prod = sessionCookieHeader("abc", req("thedispatch.uk", "/", { "x-forwarded-proto": "https" }));
  assert.ok(Array.isArray(prod));
  assert.equal(prod.length, 3);
  assert.match(prod[0], /Max-Age=0/);
  assert.equal(prod[0].includes("Domain="), false);
  assert.match(prod[0], /Secure/);
  assert.match(prod[0], /HttpOnly/);
  assert.match(prod[0], /SameSite=Lax/);
  assert.match(prod[1], /Max-Age=0/);
  assert.match(prod[1], /Domain=thedispatch.uk/);
  assert.match(prod[1], /Secure/);
  assert.match(prod[2], /dispatch_session=abc/);
  assert.match(prod[2], /Domain=thedispatch.uk/);
  assert.match(prod[2], /Secure/);
  assert.equal(/Max-Age=0/.test(prod[2]), false);

  const www = sessionCookieHeader("abc", req("www.thedispatch.uk"));
  assert.match(www.at(-1), /Secure/);
  assert.match(www.at(-1), /Domain=thedispatch.uk/);

  const local = sessionCookieHeader("abc", req("127.0.0.1:5000"));
  assert.equal(local.at(-1).includes("Secure"), false);
  assert.equal(local.at(-1).includes("Domain="), false);
  assert.equal(local[0].includes("Domain="), false);
  assert.match(local[1], /Domain=thedispatch.uk/);
  assert.match(local[1], /Max-Age=0/);

  const cleared = clearSessionCookieHeader(req("thedispatch.uk", "/", { "x-forwarded-proto": "https" }));
  assert.ok(Array.isArray(cleared));
  assert.equal(cleared.length, 2);
  assert.match(cleared[0], /Max-Age=0/);
  assert.equal(cleared[0].includes("Domain="), false);
  assert.match(cleared[1], /Max-Age=0/);
  assert.match(cleared[1], /Domain=thedispatch.uk/);
  assert.match(cleared[1], /Secure/);

  const replit = sessionCookieHeader("abc", req("the-dispatch.replit.app", "/", { "x-forwarded-proto": "https" }));
  assert.match(replit.at(-1), /Domain=thedispatch.uk/);
  assert.equal(replit.at(-1).includes("Max-Age=0"), false);
});

test("dispatchSessionTokens keeps every dispatch_session in header order", () => {
  assert.deepEqual(
    dispatchSessionTokens("theme=dark; dispatch_session=dead; dispatch_session=valid"),
    ["dead", "valid"],
  );
  assert.deepEqual(dispatchSessionTokens(""), []);
  assert.deepEqual(dispatchSessionTokens("dispatch_session="), []);
});

test("server.js resolves every presented session and clears both cookie shapes", () => {
  const src = fs.readFileSync(path.join(__dirname, "..", "server.js"), "utf8");
  assert.match(src, /dispatchSessionTokens/);
  assert.match(src, /currentUserForToken/);
  assert.match(src, /deletePresentedSessions/);
  assert.match(src, /await deletePresentedSessions\(req, oldToken\)/);
  assert.match(src, /await deletePresentedSessions\(req\)/);
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

test("apply_pricefix12 self-test", () => {
  const result = spawnSync(
    "python3",
    [path.join(__dirname, "..", "scripts", "apply_pricefix12.py"), "--self-test"],
    { encoding: "utf8" },
  );
  assert.equal(result.status, 0, `${result.stdout || ""}\n${result.stderr || ""}`);
});
