const assert = require("node:assert/strict");
const Module = require("node:module");
const test = require("node:test");

delete process.env.DATABASE_URL;
const originalRequire = Module.prototype.require;
Module.prototype.require = function patchedRequire(id) {
  if (id === "@neondatabase/serverless") return { neon() { throw new Error("database is not used by these tests"); } };
  if (id === "@replit/connectors-sdk") return { ReplitConnectors: class { proxy() { throw new Error("connector is not used by these tests"); } } };
  if (id === "stripe-replit-sync") return { runMigrations: async () => {}, StripeSync: class {} };
  if (id === "stripe") return class Stripe {};
  return originalRequire.apply(this, arguments);
};
const { handle } = require("../server");
Module.prototype.require = originalRequire;
const {
  AiRequestError,
  MISSING_KEY_MESSAGE,
  XAI_API_KEY_ENV,
  completeWithXaiKey,
  generateDispatchReply,
  guestUser,
  publicUser,
  resolvePublicUser,
  sessionTokens,
  xaiBaseUrl,
} = require("../aiProvider");

const GUEST = { guest: true, tier: "free", billingPortal: false, isAdmin: false };

test("logged-out session shape has no id", () => {
  const guest = guestUser();
  assert.deepEqual(guest, GUEST);
  assert.equal(Object.hasOwn(guest, "id"), false);
  assert.equal(publicUser(null).id, undefined);
  assert.equal(publicUser({ tier: "premium" }).id, undefined);
  assert.deepEqual(publicUser(undefined), GUEST);
});

test("public user drops the password hash", () => {
  const body = publicUser({
    id: "user-1",
    email: "member@example.com",
    passwordHash: "salt:hash",
    password_hash: "also-secret",
    tier: "premium",
    billingPortal: true,
  });
  assert.equal(body.id, "user-1");
  assert.equal(body.guest, false);
  assert.equal(body.isAdmin, false);
  assert.equal("passwordHash" in body, false);
  assert.equal("password_hash" in body, false);
  assert.equal(JSON.stringify(body).includes("salt:hash"), false);
});

test("session token parsing never throws on a broken cookie", () => {
  assert.deepEqual(sessionTokens(""), []);
  assert.deepEqual(sessionTokens("dispatch_session="), []);
  assert.deepEqual(sessionTokens("dispatch_session=%E0%A4%A"), ["%E0%A4%A"]);
  assert.deepEqual(sessionTokens(["other=1", "dispatch_session=abc%32"]), ["abc2"]);
});

test("GET /api/me resolution stays a guest when lookup throws", async () => {
  let calls = 0;
  const anonymous = await resolvePublicUser("", async () => {
    calls += 1;
    throw new Error("database exploded");
  });
  assert.equal(calls, 0);
  assert.deepEqual(anonymous, GUEST);

  const broken = await resolvePublicUser("dispatch_session=%", async () => {
    throw new Error("neon decoder failed");
  });
  assert.deepEqual(broken, GUEST);
  assert.equal(Object.hasOwn(broken, "id"), false);

  const missing = await resolvePublicUser("dispatch_session=stale", async () => null);
  assert.deepEqual(missing, GUEST);
});

test("XAI_API_KEY chat returns the model reply", async () => {
  let seen;
  const result = await completeWithXaiKey({
    apiKey: "xai-test-key",
    model: "grok-4",
    baseUrl: "https://api.x.ai/v1",
    system: "Be brief",
    messages: [{ role: "user", content: "What is gold doing?" }],
    fetchImpl: async (url, options) => {
      seen = { url, options };
      return {
        ok: true,
        status: 200,
        json: async () => ({ model: "grok-4", choices: [{ message: { content: "Gold is range-bound." } }] }),
      };
    },
  });
  assert.equal(result.text, "Gold is range-bound.");
  assert.equal(result.model, "grok-4");
  assert.equal(seen.url, "https://api.x.ai/v1/chat/completions");
  assert.equal(seen.options.headers.Authorization, "Bearer xai-test-key");
  const payload = JSON.parse(seen.options.body);
  assert.equal(payload.model, "grok-4");
  assert.equal(payload.messages[1].content, "What is gold doing?");
  assert.equal(JSON.stringify(seen).includes("xai-test-key"), true);
  assert.equal(result.text.includes("xai-test-key"), false);
});

test("a missing XAI_API_KEY becomes a clear 503 and a rejected key does not crash", async () => {
  assert.equal(XAI_API_KEY_ENV, "XAI_API_KEY");
  await assert.rejects(
    () => completeWithXaiKey({ apiKey: "  ", fetchImpl: async () => { throw new Error("should not fetch"); } }),
    error => error instanceof AiRequestError && error.status === 503 && error.code === "AI_KEY_MISSING" && error.message === MISSING_KEY_MESSAGE,
  );

  const connectorOnly = await generateDispatchReply({
    apiKey: "",
    completeWithKey: async () => { throw new Error("key path should not run"); },
    completeWithConnector: async () => ({ text: "connector reply", model: "grok-3" }),
  });
  assert.equal(connectorOnly.text, "connector reply");

  await assert.rejects(
    () => generateDispatchReply({
      apiKey: "",
      completeWithKey: async () => { throw new Error("key path should not run"); },
      completeWithConnector: async () => { throw new Error("ReplitConnectors is unavailable"); },
    }),
    error => error instanceof AiRequestError && error.status === 503 && error.code === "AI_KEY_MISSING" && error.message.includes("XAI_API_KEY"),
  );

  await assert.rejects(
    () => generateDispatchReply({
      apiKey: "xai-test-key",
      completeWithKey: async () => { throw new AiRequestError(503, "The XAI_API_KEY secret was rejected by xAI.", "PROVIDER_AUTH"); },
      completeWithConnector: async () => { throw new Error("connector should not run when a key is set"); },
    }),
    error => error instanceof AiRequestError && error.code === "PROVIDER_AUTH" && error.status === 503,
  );

  const rejected = await completeWithXaiKey({
    apiKey: "xai-test-key",
    fetchImpl: async () => ({ ok: false, status: 401, json: async () => ({ error: "bad key" }) }),
  }).catch(error => error);
  assert.ok(rejected instanceof AiRequestError);
  assert.equal(rejected.status, 503);
  assert.equal(rejected.code, "PROVIDER_AUTH");
  assert.equal(String(rejected.message).includes("xai-test-key"), false);

  const offline = await completeWithXaiKey({
    apiKey: "xai-test-key",
    fetchImpl: async () => { throw new Error("getaddrinfo EAI_AGAIN api.x.ai"); },
  }).catch(error => error);
  assert.ok(offline instanceof AiRequestError);
  assert.equal(offline.status, 503);
  assert.equal(offline.code, "PROVIDER_UNAVAILABLE");
});

function callRoute(path, headers = {}) {
  const req = {
    method: "GET",
    url: path,
    headers: { host: "127.0.0.1", ...headers },
    socket: { remoteAddress: "127.0.0.1" },
  };
  const res = {
    statusCode: 0,
    body: "",
    headersSent: false,
    setHeader() {},
    writeHead(status) { this.statusCode = status; this.headersSent = true; },
    end(data) { this.body = data || ""; },
  };
  return handle(req, res).then(() => ({ status: res.statusCode, body: res.body ? JSON.parse(res.body) : null }));
}

test("GET /api/me is a guest 200 when logged out or the cookie read throws", async () => {
  const anonymous = await callRoute("/api/me");
  assert.equal(anonymous.status, 200);
  assert.deepEqual(anonymous.body, GUEST);
  assert.equal(Object.hasOwn(anonymous.body, "id"), false);

  const stale = await callRoute("/api/me", { cookie: "dispatch_session=%E0%A4%A" });
  assert.equal(stale.status, 200);
  assert.deepEqual(stale.body, GUEST);

  const exploding = {
    method: "GET",
    url: "/api/me",
    headers: new Proxy({ host: "127.0.0.1" }, {
      get(target, prop) {
        if (prop === "cookie") throw new Error("cookie header exploded");
        return target[prop];
      },
    }),
    socket: { remoteAddress: "127.0.0.1" },
  };
  const res = {
    statusCode: 0,
    body: "",
    headersSent: false,
    setHeader() {},
    writeHead(status) { this.statusCode = status; this.headersSent = true; },
    end(data) { this.body = data || ""; },
  };
  await handle(exploding, res);
  assert.equal(res.statusCode, 200);
  assert.deepEqual(JSON.parse(res.body), GUEST);
});

test("POST /api/chat without a session is rejected before the model call", async () => {
  const req = {
    method: "POST",
    url: "/api/chat",
    headers: { host: "127.0.0.1", "content-type": "application/json" },
    socket: { remoteAddress: "127.0.0.1" },
    async *[Symbol.asyncIterator]() {
      yield Buffer.from(JSON.stringify({ messages: [{ role: "user", content: "Hello" }] }));
    },
  };
  const res = {
    statusCode: 0,
    body: "",
    headersSent: false,
    setHeader() {},
    writeHead(status) { this.statusCode = status; this.headersSent = true; },
    end(data) { this.body = data || ""; },
  };
  await handle(req, res);
  assert.equal(res.statusCode, 401);
  assert.equal(JSON.parse(res.body).error, "Premium membership required");
});

test("XAI_BASE_URL must stay https", () => {
  const previous = process.env.XAI_BASE_URL;
  try {
    delete process.env.XAI_BASE_URL;
    assert.equal(xaiBaseUrl(), "https://api.x.ai/v1");
    process.env.XAI_BASE_URL = "http://127.0.0.1/v1";
    assert.throws(() => xaiBaseUrl(), error => error instanceof AiRequestError && error.status === 503);
  } finally {
    if (previous === undefined) delete process.env.XAI_BASE_URL;
    else process.env.XAI_BASE_URL = previous;
  }
});
