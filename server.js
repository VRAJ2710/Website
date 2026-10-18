/*
 * APPROXIMATE production server.js. UNVERIFIED against prod.
 * thedispatch.uk build chat56 does not serve server.js, so this file was not
 * compared to the live process. It is the rt9-patch copy of server.js after
 * the deploy/patch_rt*.py server patches were applied in git introduction
 * order (see FOLD.md). Patches whose anchors were missing were left unapplied.
 * Do not deploy this file on the strength of this reconstruction.
 */
const http = require("http");
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
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { neon } = require("@neondatabase/serverless");
const { ReplitConnectors } = require("@replit/connectors-sdk");
const { runMigrations } = require("stripe-replit-sync");
const {
  BoundedTtlCache,
  FixedWindowRateLimiter,
  normalizeCoinGeckoPath,
  normalizeTwelveDataSymbols,
  normalizeTwelveDataQuotes,
} = require("./marketProxy");
const { approvedRssFeedUrl } = require("./rssFeeds");
const {
  ensureDispatchPremiumPrice,
  getStripeMode,
  getStripeSync,
  getUncachableStripeClient,
} = require("./stripeClient");

const root = __dirname;
const checkoutLocks = new Map();
const PORT = Number(process.env.PORT || 5000);
const AI_TIMEOUT_MS = Number(process.env.AI_TIMEOUT_MS || 25000);
const AI_MODEL_CACHE_MS = 10 * 60 * 1000;
let aiModelCache = { id: null, expiresAt: 0 };
let stripeState = { ready: false, mode: null, error: "Stripe is starting." };
const sql = process.env.DATABASE_URL ? neon(process.env.DATABASE_URL) : null;
let databaseReady = false;
const coinGeckoCache = new BoundedTtlCache({ maxEntries: 48, maxBytes: 1024 * 1024 });
const coinGeckoRateLimiter = new FixedWindowRateLimiter({ limit: 30, windowMs: 60_000, maxKeys: 256 });
const rssFeedCache = new BoundedTtlCache({ maxEntries: 30, maxBytes: 2 * 1024 * 1024 });
const rssFeedRateLimiter = new FixedWindowRateLimiter({ limit: 30, windowMs: 60_000, maxKeys: 256 });
const twelveDataCache = new BoundedTtlCache({ maxEntries: 8, maxBytes: 128 * 1024 });
const TWELVE_DATA_CACHE_MS = 15 * 60 * 1000;
// The Basic plan permits eight credits/minute and 800/day. Our eight-symbol
// allowlist plus a 15-minute shared cache caps normal refreshes at 768 credits/day.
const twelveDataDailyRateLimiter = new FixedWindowRateLimiter({ limit: 90, windowMs: 24 * 60 * 60 * 1000, maxKeys: 1 });

class AiRequestError extends Error {
  constructor(status, message, code) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

function json(res, status, body, extraHeaders = {}) {
  const data = JSON.stringify(body);
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": "*",
    ...extraHeaders,
  });
  res.end(data);
}
function text(res, status, body, contentType = "text/plain; charset=utf-8") {
  res.writeHead(status, {
    "Content-Type": contentType,
    "Cache-Control": "no-store",
  });
  res.end(body);
}
function cookieValue(req, name) {
  const raw = req.headers.cookie || "";
  const found = raw.split(";").map(v => v.trim()).find(v => v.startsWith(name + "="));
  return found ? decodeURIComponent(found.slice(name.length + 1)) : null;
}
function tokenHash(token) {
  return crypto.createHash("sha256").update(String(token || "")).digest("hex");
}
async function currentUser(req) {
  const token = cookieValue(req, "dispatch_session");
  if (!databaseReady || !token) return null;
  const result = await sql`SELECT COALESCE(json_agg(row_to_json(uq)), '[]'::json) AS data FROM (SELECT u.id, u.email, u.password_hash AS "passwordHash", u.tier,
    u.billing_portal AS "billingPortal", u.stripe_customer_id AS "stripeCustomerId",
    u.stripe_subscription_id AS "stripeSubscriptionId", u.checkout_session AS "checkoutSession",
    u.checkout_attempt_id AS "checkoutAttemptId"
    FROM dispatch_sessions s JOIN dispatch_users u ON u.id = s.user_id
    WHERE s.token_hash=${tokenHash(token)} AND s.expires_at > NOW() LIMIT 1) uq`;
  return result[0]?.data?.[0] || null;
}
async function setSession(res, user, oldToken = null) {
  const token = crypto.randomBytes(32).toString("hex");
  await sql`INSERT INTO dispatch_sessions (token_hash, user_id, expires_at)
    VALUES (${tokenHash(token)}, ${user.id}, NOW() + INTERVAL '30 days')`;
  if (oldToken) await sql`DELETE FROM dispatch_sessions WHERE token_hash=${tokenHash(oldToken)}`;
  res.setHeader("Set-Cookie", `dispatch_session=${token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000`);
}
function passwordHash(password, salt = crypto.randomBytes(16).toString("hex")) {
  const hash = crypto.scryptSync(String(password), salt, 64).toString("hex");
  return `${salt}:${hash}`;
}
function validPassword(password, storedHash) {
  if (!storedHash || typeof password !== "string") return false;
  const [salt, expected] = String(storedHash).split(":");
  if (!salt || !expected) return false;
  const actual = crypto.scryptSync(password, salt, 64).toString("hex");
  return actual.length === expected.length
    && crypto.timingSafeEqual(Buffer.from(actual, "hex"), Buffer.from(expected, "hex"));
}
function validAccountInput(email, password) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) && typeof password === "string" && password.length >= 8;
}
async function initializeAuthDatabase() {
  if (!sql) throw new Error("DATABASE_URL is required for persistent member accounts.");
  await sql`CREATE TABLE IF NOT EXISTS dispatch_users (
    id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
    tier TEXT NOT NULL DEFAULT 'free', billing_portal BOOLEAN NOT NULL DEFAULT FALSE,
    stripe_customer_id TEXT, stripe_subscription_id TEXT, checkout_session JSONB,
    checkout_attempt_id TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  )`;
  await sql`CREATE TABLE IF NOT EXISTS dispatch_sessions (
    token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES dispatch_users(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  )`;
  await sql`CREATE INDEX IF NOT EXISTS dispatch_sessions_expiry_idx ON dispatch_sessions (expires_at)`;
  await sql`CREATE TABLE IF NOT EXISTS dispatch_password_resets (
    token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES dispatch_users(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL, used_at TIMESTAMPTZ
  )`;
  await sql`DELETE FROM dispatch_sessions WHERE expires_at <= NOW()`;
  await sql`DELETE FROM dispatch_password_resets WHERE expires_at <= NOW() OR used_at IS NOT NULL`;
  databaseReady = true;
}
async function findUserByEmail(email) {
  const result = await sql`SELECT COALESCE(json_agg(row_to_json(uq)), '[]'::json) AS data FROM (SELECT id, email, password_hash AS "passwordHash", tier,
    billing_portal AS "billingPortal", stripe_customer_id AS "stripeCustomerId",
    stripe_subscription_id AS "stripeSubscriptionId", checkout_session AS "checkoutSession",
    checkout_attempt_id AS "checkoutAttemptId"
    FROM dispatch_users WHERE email=${email} LIMIT 1) uq`;
  return result[0]?.data?.[0] || null;
}
async function saveUser(user) {
  await sql`UPDATE dispatch_users SET tier=${user.tier}, billing_portal=${Boolean(user.billingPortal)},
    stripe_customer_id=${user.stripeCustomerId || null}, stripe_subscription_id=${user.stripeSubscriptionId || null},
    checkout_session=${user.checkoutSession ? JSON.stringify(user.checkoutSession) : null},
    checkout_attempt_id=${user.checkoutAttemptId || null} WHERE id=${user.id}`;
}
function publicUser(user) {
  if (!user) return { tier: "free", billingPortal: false };
  const { passwordHash, ...safeUser } = user;
  return safeUser;
}
function withCheckoutLock(userId, work) {
  const previous = checkoutLocks.get(userId) || Promise.resolve();
  const run = previous.catch(() => undefined).then(work);
  checkoutLocks.set(userId, run);
  return run.finally(() => {
    if (checkoutLocks.get(userId) === run) checkoutLocks.delete(userId);
  });
}
function page(res, title, content) {
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" });
  res.end(`<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title}</title>
  <style>body{margin:0;background:#0b1018;color:#e8edf3;font:16px system-ui;display:grid;place-items:center;min-height:100vh}
  main{width:min(420px,calc(100% - 40px));background:#111a26;border:1px solid #293849;border-radius:14px;padding:28px;box-sizing:border-box}
  h1{font-size:22px;margin:0 0 8px;color:#f5a623}p{color:#9baabb;line-height:1.5}label{display:block;color:#b8c4d2;font-size:13px;margin:16px 0 6px}
  input{width:100%;box-sizing:border-box;padding:11px;background:#0b1018;color:#fff;border:1px solid #3a4a5d;border-radius:7px}
  button,a{display:inline-block;margin-top:20px;padding:11px 16px;border:0;border-radius:7px;background:#f5a623;color:#111;font-weight:700;text-decoration:none;cursor:pointer}
  .muted{font-size:12px;color:#718096}</style></head><body><main>${content}<p class="muted rt34s-legal" style="margin:22px 0 0;text-align:center"><a href="/terms" style="display:inline;margin:0;padding:0;background:none;color:#9baabb;font-weight:400;text-decoration:underline">Terms</a> · <a href="/privacy" style="display:inline;margin:0;padding:0;background:none;color:#9baabb;font-weight:400;text-decoration:underline">Privacy</a></p></main></body></html>`);
}
async function readBody(req) {
  let text = "";
  for await (const chunk of req) text += chunk;
  try { return text ? JSON.parse(text) : {}; } catch { return {}; }
}
async function readRawBody(req, maxBytes = 2 * 1024 * 1024) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > maxBytes) throw new Error("Request body is too large.");
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
}
async function upstream(url, options = {}) {
  const response = await fetch(url, { ...options, headers: { "User-Agent": "DispatchMarkets/1.0", ...(options.headers || {}) } });
  if (!response.ok) throw new Error(`upstream ${response.status}`);
  return response;
}
async function coinGecko(req, res, rawPath) {
  // Only expose the small public market-data surface the terminal uses; this
  // is deliberately not a general-purpose fetch proxy.
  const normalizedPath = normalizeCoinGeckoPath(rawPath);
  if (!normalizedPath) {
    return json(res, 400, { error: "Unsupported crypto data request." });
  }
  const clientAddress = req.socket?.remoteAddress || "unknown";
  if (!coinGeckoRateLimiter.allow(clientAddress)) {
    return json(res, 200, { unavailable: true }, { "X-Dispatch-Data-Status": "rate_limited" });
  }
  const cached = coinGeckoCache.get(normalizedPath);
  if (cached) return json(res, 200, cached);
  try {
    const response = await fetch(`https://api.coingecko.com/api/v3${normalizedPath}`, {
      headers: { "User-Agent": "DispatchMarkets/1.0" },
      signal: AbortSignal.timeout(8_000),
    });
    if (!response.ok) throw new Error(`CoinGecko ${response.status}`);
    const data = await response.json();
    coinGeckoCache.set(normalizedPath, data, 30_000);
    return json(res, 200, data);
  } catch {
    // Optional public data must not produce client-side 429/CORS failures.
    return json(res, 200, { unavailable: true }, { "X-Dispatch-Data-Status": "unavailable" });
  }
}
async function readTextCapped(response, maxBytes) {
  if (!response.body) return "";
  const reader = response.body.getReader();
  const chunks = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > maxBytes) throw new Error("RSS feed exceeds the response limit.");
      chunks.push(Buffer.from(value));
    }
  } finally {
    reader.cancel().catch(() => {});
  }
  return Buffer.concat(chunks).toString("utf8");
}
async function rssFeed(req, res, feedId) {
  const feedUrl = approvedRssFeedUrl(feedId);
  if (!feedUrl) return json(res, 400, { error: "Unknown RSS feed." });
  const cached = rssFeedCache.get(feedId);
  if (cached) return text(res, 200, cached, "application/xml; charset=utf-8");
  const clientAddress = req.socket?.remoteAddress || "unknown";
  if (!rssFeedRateLimiter.allow(clientAddress)) return text(res, 200, "", "application/xml; charset=utf-8");
  try {
    const response = await fetch(feedUrl, {
      headers: { "User-Agent": "DispatchMarkets/1.0" },
      redirect: "error",
      signal: AbortSignal.timeout(8_000),
    });
    if (!response.ok) throw new Error(`RSS ${response.status}`);
    const body = await readTextCapped(response, 512 * 1024);
    rssFeedCache.set(feedId, body, 60_000);
    return text(res, 200, body, "application/xml; charset=utf-8");
  } catch {
    // Public feeds are optional. Preserve a quiet, honest empty-state response.
    return text(res, 200, "", "application/xml; charset=utf-8");
  }
}
function clipped(value, max) {
  return String(value || "").trim().slice(0, max);
}
function rt24sWordClip(value, max) {
  const t = String(value || "").trim();
  if (!(max > 1) || t.length <= max) return t;
  const cut = t.slice(0, max - 1), sp = cut.lastIndexOf(" ");
  return (sp > max * 0.6 ? cut.slice(0, sp) : cut).replace(/[\s,;:·–—-]+$/, "") + "…";
}
function safeText(value, max) {
  return rt24sWordClip(value, max).replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[char]));
}
function safeGeneratedValue(value, depth = 0) {
  if (depth > 6) return null;
  if (typeof value === "string") return safeText(value, 3000);
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  if (typeof value === "boolean" || value === null) return value;
  if (Array.isArray(value)) return value.slice(0, 20).map(item => safeGeneratedValue(item, depth + 1));
  if (typeof value === "object") {
    return Object.fromEntries(Object.entries(value)
      .filter(([key]) => !["__proto__", "constructor", "prototype"].includes(key))
      .slice(0, 40)
      .map(([key, item]) => [key, safeGeneratedValue(item, depth + 1)]));
  }
  return null;
}
function jsonFromText(text) {
  const clean = String(text || "").replace(/```json|```/gi, "").trim();
  try { return JSON.parse(clean); } catch {}
  const start = clean.indexOf("{");
  const end = clean.lastIndexOf("}");
  if (start >= 0 && end > start) return JSON.parse(clean.slice(start, end + 1));
  throw new AiRequestError(502, "The AI returned an unreadable response. Please try again.", "INVALID_RESPONSE");
}
function asAiMessages(messages, limit = 16) {
  if (!Array.isArray(messages)) return [];
  return messages.slice(-limit).map(message => ({
    role: message?.role === "assistant" ? "assistant" : "user",
    content: clipped(message?.content, 6000),
  })).filter(message => message.content);
}
function withTimeout(promise, timeoutMs, message = "The AI request timed out. Please try again.") {
  let timeout;
  const deadline = new Promise((_, reject) => {
    timeout = setTimeout(() => reject(new AiRequestError(504, message, "TIMEOUT")), timeoutMs);
  });
  return Promise.race([promise, deadline]).finally(() => clearTimeout(timeout));
}
async function xaiProxy(pathname, options, timeoutMs = AI_TIMEOUT_MS) {
  // Create a fresh client for every request so connector credentials can refresh.
  const connectors = new ReplitConnectors();
  return withTimeout(connectors.proxy("xai", pathname, options), timeoutMs);
}
async function discoverAiModel() {
  if (aiModelCache.id && aiModelCache.expiresAt > Date.now()) return aiModelCache.id;

  let models = [];
  let providerStatus = null;
  try {
    const response = await xaiProxy("/v1/language-models", { method: "GET" }, 8000);
    providerStatus = response.status;
    if (response.ok) {
      const data = await response.json();
      models = data.models || data.data || [];
    }
  } catch {}
  if (!models.length) {
    try {
      const response = await xaiProxy("/v1/models", { method: "GET" }, 8000);
      providerStatus = response.status;
      if (response.ok) {
        const data = await response.json();
        models = data.data || data.models || [];
      }
    } catch {}
  }

  const candidates = models.filter(model => {
    const id = typeof model?.id === "string" ? model.id : "";
    const modalities = Array.isArray(model?.input_modalities) ? model.input_modalities : [];
    return id && /grok/i.test(id) && (!modalities.length || modalities.includes("text"));
  });
  const selected = candidates.find(model => /grok-(4|3)/i.test(model.id)) || candidates[0];
  if (!selected?.id) {
    if (providerStatus === 402 || providerStatus === 403) {
      throw new AiRequestError(503, "The connected xAI team has no available credits. Add credits, then try again.", "PROVIDER_CREDITS");
    }
    throw new AiRequestError(503, "The AI provider is not ready. Please try again shortly.", "PROVIDER_UNAVAILABLE");
  }
  aiModelCache = { id: selected.id, expiresAt: Date.now() + AI_MODEL_CACHE_MS };
  return selected.id;
}
async function generateAi({ system, messages, maxTokens = 1000, temperature = 0.2 }) {
  return withTimeout((async () => {
    const model = await discoverAiModel();
    const response = await xaiProxy("/v1/chat/completions", {
      method: "POST",
      body: {
        model,
        messages: [{ role: "system", content: clipped(system, 5000) }, ...asAiMessages(messages)],
        max_completion_tokens: Math.max(300, Math.min(Number(maxTokens) || 1000, 2400)),
        temperature,
      },
    });

    if (!response.ok) {
      if (response.status === 429) {
        throw new AiRequestError(429, "AI generation is temporarily rate limited. Please try again shortly.", "RATE_LIMIT");
      }
      if (response.status === 402 || response.status === 403) {
        throw new AiRequestError(503, "The connected xAI team has no available credits. Add credits, then try again.", "PROVIDER_CREDITS");
      }
      if (response.status === 401) {
        throw new AiRequestError(503, "The AI provider connection needs attention. Please try again shortly.", "PROVIDER_AUTH");
      }
      throw new AiRequestError(502, "AI generation is unavailable right now. Please try again shortly.", "UPSTREAM_ERROR");
    }
    const data = await response.json();
    const text = data?.choices?.[0]?.message?.content;
    if (!text) throw new AiRequestError(502, "The AI returned an empty response. Please try again.", "EMPTY_RESPONSE");
    return { text: String(text), model };
  })(), AI_TIMEOUT_MS);
}
function sendAiError(res, error) {
  const status = error instanceof AiRequestError ? error.status : 502;
  const message = error instanceof AiRequestError ? error.message : "AI generation is unavailable right now. Please try again shortly.";
  console.error("AI generation failed:", error?.code || error?.message || error);
  return json(res, status, { error: message, code: error?.code, limitReached: error?.code === "RATE_LIMIT" });
}
// ── rt48c: /api/academy-daily ── (replaces rt48bs) auto-generated Academy explainers from the site's own RSS headlines.
// Only headlines about an asset the site covers (gold, oil, US dollar, US yields, S&P 500, Nasdaq, Bitcoin, Ether, EUR/USD, pound),
// or with a textbook knock-on effect for one (e.g. "dollar slips" -> gold, EUR/USD). The AI picks a headline, one allowed asset and
// a direction (up / down / little change) and writes a short explanation; the server writes the question and the fixed answers.
// Every item (fresh or cached) must pass _rt48bWhy (empty = valid): allowed asset, no stablecoin topics, no invented numbers,
// wording consistent with the direction, known-wrong reactions rejected, no item whose answer the headline already states.
// AI items first, topped up to 3 with deterministic templates (spread across assets). Cache: memory + os.tmpdir() file per
// London day; up to 3 automatic builds a day, 2h apart, while fewer than 3 items or no AI item; admins can force a rebuild with
// ?refresh=1 (max 6 a day) and see a diagnostic (?refresh=1 or ?diag=1: counts and reasons, no secrets). Always 200 JSON.
// ACADEMY_AI=off disables the AI call (templates only). No database, no Stripe.
const RT48B_ASSETS = {
  gold: ["the gold price", /\b(gold|bullion)\b/i], oil: ["oil prices", /\b(oil|crude|brent|wti|opec\+?)\b/i],
  usd: ["the US dollar", /\b(us dollar|u\.s\. dollar|dollar|greenback|dxy)\b/i], yields: ["US Treasury yields", /\b(treasur(y|ies)|bond yields?|yields?)\b/i],
  spx: ["the S&P 500", /(s&p( 500)?|wall street|us stocks|u\.s\. stocks|dow jones|\bthe dow\b)/i], nasdaq: ["the Nasdaq", /\bnasdaq\b/i],
  btc: ["Bitcoin", /\b(bitcoin|btc)\b/i], eth: ["Ether", /\b(ether|ethereum)\b/i],
  eurusd: ["EUR/USD", /\b(euro|eur\/usd|ecb|lagarde)\b/i], gbp: ["the British pound", /\b(pound|sterling|gbp|bank of england|boe)\b/i] };
// "X <falls|rises> ..." where X is an asset name: used for knock-on rules and to spot headlines that already state an answer
const RT48B_UPV = "rises?|rose|rising|jump\\w*|surg\\w*|soar\\w*|climb\\w*|rall\\w*|gains?|gained|strengthen\\w*|firm\\w*|spik\\w*|advanc\\w*|rebound\\w*|hits? (?:a )?record|record high|snaps? (?:a |its )?(?:\\w+[- ])*(?:losing|down) (?:streak|run)";
const RT48B_DNV = "falls?|fell|falling|drop\\w*|dips?|dipped|slips?|slipped|slid\\w*|slides?|slump\\w*|sink\\w*|sank|tumbl\\w*|plung\\w*|weaken\\w*|retreat\\w*|declin\\w*|eases?|eased|los(?:es|t|ing) ground|snaps? (?:a |its )?(?:\\w+[- ])*(?:win|winning) (?:streak|run)";
const RT48B_NM = { gold: "gold|bullion", oil: "oil|crude|brent|wti|opec", usd: "dollar|greenback|dxy", yields: "yields?|treasur(?:y|ies)", spx: "s&p(?: 500)?|wall street|stocks|dow(?: jones)?", nasdaq: "nasdaq", btc: "bitcoin|btc", eth: "ether|ethereum", eurusd: "euro|eur/usd", gbp: "pound|sterling|gbp" };
function RT48B_MV(names, dir) { return new RegExp("\\b(?:" + names + ")\\b(?:(?!\\b(?:as|after|while|but|and|than|with|amid|helping|despite|vs)\\b)[^.;:?!,]){0,30}?\\b(?:" + (dir === "up" ? RT48B_UPV : RT48B_DNV) + ")\\b", "i"); }
const RT48B_OPTS = ["Up", "Down", "Little change"], RT48B_DIRS = ["up", "down", "flat"];
const RT48B_BAN = /stablecoin|tether|\busdc\b|\busdt\b|\b(australian|canadian|new zealand|hong kong|singapore|taiwan|zimbabwe) dollar\b/i;
// headline pattern + asset → the usual first direction (also the deterministic template set)
const RT48B_RULES = [
  [/\b(fed|federal reserve|fomc|powell)\b.*\b(cuts?|cutting|lowers?)\b.*\brates?\b|\brate cuts?\b.*\b(fed|federal reserve)\b/i, { usd: ["down", "A surprise Fed rate cut usually weakens the US dollar first, because lower US rates make holding dollars less rewarding."], yields: ["down", "Treasury yields typically fall first when the Fed cuts by more than expected, led by shorter maturities."], gold: ["up", "Gold often rises on a surprise Fed cut: lower rates reduce the cost of holding a metal that pays no interest, and the dollar tends to weaken."] }],
  [/\b(fed|federal reserve|fomc|powell)\b.*\b(raises?|hikes?|hiking|lifts?)\b.*\brates?\b/i, { usd: ["up", "A surprise Fed hike usually lifts the US dollar first, because higher US rates attract money into dollars."], yields: ["up", "Treasury yields typically rise first on a surprise hike, especially shorter maturities."], gold: ["down", "Gold often falls on a surprise hike: higher rates raise the cost of holding a metal that pays no interest."] }],
  [/\b(us|u\.s\.|american)\b.*\b(inflation|cpi|consumer prices)\b.*\b(hot|hotter|accelerat\w*|jump\w*|surg\w*|higher than expected|tops?)\b/i, { yields: ["up", "Hotter US inflation usually pushes Treasury yields higher first, as traders expect rates to stay high for longer."], usd: ["up", "A hot US inflation print often lifts the dollar first on expectations of tighter Fed policy."] }],
  [/\b(us|u\.s\.|american)\b.*\b(inflation|cpi|consumer prices)\b.*\b(cool\w*|slow\w*|eas(es|ed|ing)|lower than expected|soft\w*)\b/i, { yields: ["down", "Cooler US inflation usually pulls Treasury yields lower first, as traders price in earlier or bigger rate cuts."], usd: ["down", "Softer US inflation often weakens the dollar first, because rate-cut expectations rise."] }],
  [/\b(oil|crude|refiner(y|ies)|pipeline|tankers?|energy (sites|facilities|infrastructure)|oil terminals?|strait)\b.*\b(attack\w*|strikes?|struck|hit|outage|disrupt\w*|shut\w*|blockade|halt\w*)\b|\b(attack\w*|strikes?|struck|hits?|outage|disrupt\w*|shut\w*|halt\w*)\b.*\b(oil|crude|refiner(y|ies)|pipeline|tankers?|energy (sites|facilities|infrastructure)|oil terminals?)\b/i, { oil: ["up", "A disruption to oil supply usually lifts oil prices first, as traders price in less supply. The move often fades if output recovers quickly."] }],
  [/\bopec\+?\b.*\b(cut\w*|reduc\w*)\b.*\b(output|production|supply)\b/i, { oil: ["up", "A surprise OPEC+ output cut usually lifts oil prices first, because fewer barrels are expected to reach the market."] }],
  [/\b(oil|crude)\b.*\b(glut|surplus|oversuppl\w*)\b|\bopec\+?\b.*\b(raise|boost|increase|hike)\w*\b.*\b(output|production)\b/i, { oil: ["down", "Signs of too much oil supply usually push prices lower first, as more barrels compete for buyers."] }],
  [/\b(bitcoin|ether|ethereum|crypto)\b.*\betfs?\b.*\b(inflows?|record)\b/i, { btc: ["up", "Strong inflows into crypto funds usually support Bitcoin first, because funds must buy the coin to back new shares."], eth: ["up", "Strong inflows into Ether funds usually support the price first, because funds must buy Ether to back new shares."] }],
  [/\b(bitcoin|ether|ethereum|crypto)\b.*\betfs?\b.*\boutflows?\b/i, { btc: ["down", "Outflows from crypto funds usually weigh on Bitcoin first, because funds sell coins as investors redeem shares."], eth: ["down", "Outflows from Ether funds usually weigh on the price first, as funds sell to meet redemptions."] }],
  [/\b(war|missiles?|airstrikes?|invasion|invad\w*|military strikes?|escalat\w*)\b/i, { gold: ["up", "Escalating conflict often lifts gold first, as investors look for a traditional safe haven. Such moves can fade if tensions ease."] }],
  [/\b(ecb|lagarde)\b.*\b(cuts?|lowers?)\b.*\brates?\b/i, { eurusd: ["down", "A surprise ECB cut usually weakens the euro first, so EUR/USD tends to fall."] }],
  [/\b(ecb|lagarde)\b.*\b(raises?|hikes?)\b.*\brates?\b/i, { eurusd: ["up", "A surprise ECB hike usually strengthens the euro first, so EUR/USD tends to rise."] }],
  [/\b(bank of england|boe|bailey)\b.*\b(cuts?|lowers?)\b.*\brates?\b/i, { gbp: ["down", "A surprise Bank of England cut usually weakens the pound first, because lower UK rates make sterling less rewarding to hold."] }],
  [/\b(bank of england|boe|bailey)\b.*\b(raises?|hikes?)\b.*\brates?\b/i, { gbp: ["up", "A surprise Bank of England hike usually lifts the pound first, as higher UK rates attract money into sterling."] }],
  // knock-on effects of a move the headline reports (the question is then about a different asset, so the answer is not given away)
  [RT48B_MV("dollar|greenback|dxy", "down"), { gold: ["up", "Gold is priced in dollars, so a weaker dollar usually supports the gold price: it becomes cheaper for buyers using other currencies."], eurusd: ["up", "EUR/USD is the price of one euro in dollars, so when the dollar weakens broadly, EUR/USD usually rises."], gbp: ["up", "The pound is usually quoted against the dollar, so a broadly weaker dollar tends to lift the pound."] }],
  [RT48B_MV("dollar|greenback|dxy", "up"), { gold: ["down", "Gold is priced in dollars, so a stronger dollar often weighs on the gold price: it becomes dearer for buyers using other currencies."], eurusd: ["down", "EUR/USD is the price of one euro in dollars, so when the dollar strengthens broadly, EUR/USD usually falls."], gbp: ["down", "The pound is usually quoted against the dollar, so a broadly stronger dollar tends to push the pound lower."] }],
  [RT48B_MV("(?:treasury|bond|u\\.?s\\.? |us |10-year )yields?|yields", "down"), { gold: ["up", "Lower bond yields usually support gold, because the interest given up by holding a metal that pays none becomes smaller."] }],
  [RT48B_MV("(?:treasury|bond|u\\.?s\\.? |us |10-year )yields?|yields", "up"), { gold: ["down", "Rising bond yields often weigh on gold, because holding a metal that pays no interest becomes more costly."] }],
  [RT48B_MV("bitcoin|btc", "down"), { eth: ["down", "Ether usually moves in the same direction as Bitcoin, the largest crypto asset, so a falling Bitcoin tends to drag it lower."] }],
  [RT48B_MV("bitcoin|btc", "up"), { eth: ["up", "Ether usually moves in the same direction as Bitcoin, the largest crypto asset, so a rising Bitcoin tends to lift it."] }],
  [/\bsafe[- ]havens?\b|\bflight to safety\b|\brisk[- ]off\b/i, { gold: ["up", "When investors rush for safety, gold usually benefits first, as a traditional safe-haven asset."], yields: ["down", "A rush for safety usually pushes money into Treasuries, which lifts bond prices and so tends to lower yields."] }],
  [/\b(sanction\w*|embargo\w*)\b.*\b(oil|crude|russia\w*|iran\w*|venezuela\w*)\b|\b(oil|crude)\b.*\b(sanction\w*|embargo\w*)\b|\bhurricane\b.*\b(gulf|oil|refiner\w*)\b/i, { oil: ["up", "Anything that may cut oil supply, such as sanctions or storms near production sites, usually lifts oil prices first."] }],
  [/\brecession (fears?|worries|risks?|warnings?)\b|\b(fears?|worries) of (a )?recession\b/i, { yields: ["down", "Recession worries usually pull Treasury yields lower first, as investors buy safer bonds and expect lower interest rates."], oil: ["down", "Recession worries often push oil prices lower first, because a weaker economy is expected to use less fuel."] }],
  [/\b(new|higher|sweeping|steep|more) tariffs?\b|\btariffs?\b.*\b(impos\w*|rais\w*|hik\w*|threat\w*|escalat\w*)\b|\btrade war\b/i, { spx: ["down", "Surprise tariffs or an escalating trade war usually weigh on US stocks first, as investors expect higher costs and slower trade."] }],
  [/\b(payrolls?|jobs report|hiring|job growth)\b.*\b(beat\w*|strong\w*|surg\w*|jump\w*|blows? past|tops?)\b/i, { usd: ["up", "A stronger US jobs report than expected usually lifts the dollar first, because the Fed is seen keeping rates higher for longer."], yields: ["up", "Strong US jobs data usually pushes Treasury yields higher first, as rate-cut expectations fade."] }],
  [/\b(payrolls?|jobs report|hiring|job growth)\b.*\b(miss\w*|weak\w*|slow\w*|stall\w*|disappoint\w*)\b/i, { usd: ["down", "A weaker US jobs report than expected usually weakens the dollar first, because rate cuts look more likely."], yields: ["down", "Weak US jobs data usually pulls Treasury yields lower first, as traders expect earlier rate cuts."] }],
  [/\b(fed|federal reserve|powell|fomc)\b.*\bhawkish\b|\bhawkish\b.*\b(fed|federal reserve|powell|fomc)\b/i, { usd: ["up", "A more hawkish Fed than expected usually lifts the dollar first, because US rates are seen staying higher."], yields: ["up", "A hawkish Fed surprise usually pushes Treasury yields higher first."] }],
  [/\b(fed|federal reserve|powell|fomc)\b.*\bdovish\b|\bdovish\b.*\b(fed|federal reserve|powell|fomc)\b/i, { usd: ["down", "A more dovish Fed than expected usually weakens the dollar first, because US rates are seen falling sooner."], gold: ["up", "A dovish Fed surprise often lifts gold first, as lower expected rates reduce the cost of holding it."] }] ];
const RT48B_DIRW = { up: /\b(rise|rises|rising|rose|higher|lift\w*|gain\w*|climb\w*|rall\w*|strengthen\w*|up|upward|support\w*|jump\w*|increas\w*|boost\w*|push\w* (prices )?(up|higher)|spik\w*|surg\w*|soar\w*|advanc\w*|firm\w*|benefit\w*|appreciat\w*|bid up|rebound\w*)\b/i, down: /\b(fall|falls|falling|fell|lower|drop\w*|declin\w*|weaken\w*|slip\w*|down|downward|weigh\w*|sell\w*|decreas\w*|slid\w*|slide\w*|slump\w*|tumbl\w*|plung\w*|sink\w*|retreat\w*|soften\w*|pressure\w*|hurt\w*|depreciat\w*|eas(e|es|ing))\b/i, flat: /\b(little|limited|muted|unchanged|flat|small|modest|steady|stable|contained|minimal)\b/i };
const RT48B_HEDGE = /\b(typical\w*|usual\w*|often|tend\w*|general\w*|common\w*|normal\w*|historical\w*|traditional\w*|frequent\w*|likely)\b/i;
// names whose digits are not "numbers" (S&P 500, Nasdaq 100, FTSE 100, 10-year, 2-year, 2% target, G7, Web3 ...)
const RT48B_NUMOK = /\b(s&p ?500|nasdaq[- ]?100|ftse ?100|dow 30|\d{1,2}-year|\d{1,2}-month|g7|g20|web3|2% (inflation )?target|covid-19|24\/7|q[1-4])\b/gi;
const _rt48sState = { day: "", generatedAt: "", items: [], kind: "template", tries: 0, last: 0, forced: 0, busy: null, diag: null };
const _rt48sFile = require("path").join(require("os").tmpdir(), "dispatch-academy-daily-v3.json");
function _rt48sDay() { try { return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/London" }).format(new Date()); } catch (e) { return new Date().toISOString().slice(0, 10); } }
function _rt48bQ(asset) { return `If this news is a surprise to markets, what is the typical first reaction in ${RT48B_ASSETS[asset][0]}?`; }
function _rt48bRule(h, asset) { for (const [re, m] of RT48B_RULES) if (re.test(h) && m[asset]) return m[asset]; return null; }
function _rt48bWhy(x) { try { if (!x || typeof x !== "object") return "not-object"; const A = RT48B_ASSETS[x.asset], h = String(x.h || ""), e = String(x.e || "");
  if (!A) return "asset-not-allowed"; if (!(A[1].test(h) || _rt48bRule(h, x.asset))) return "asset-not-in-headline";
  if (RT48B_BAN.test(h) || RT48B_BAN.test(e)) return "banned-topic"; if (h.length < 20 || h.length > 240 || /[<>]|&#?\w+;/.test(h)) return "bad-headline";
  const k = RT48B_DIRS.indexOf(x.dir); if (k < 0) return "bad-dir"; if (x.a !== k || !Array.isArray(x.o) || x.o.join("|") !== RT48B_OPTS.join("|") || x.q !== _rt48bQ(x.asset)) return "bad-shape";
  if (e.length < 40) return "e-too-short"; if (e.length > 380) return "e-too-long"; if (/[<>]|https?:|www\./i.test(e)) return "e-link-or-html";
  if (/\b(you should|buy now|sell now|guarantee\w*|definitely|certain to)\b/i.test(e)) return "e-advice";
  if (!RT48B_HEDGE.test(e)) return "e-no-hedge-word"; if (!RT48B_DIRW[x.dir].test(e)) return "e-dir-word-missing";
  const nums = t => (String(t).replace(RT48B_NUMOK, " ").match(/\d+(?:[.,]\d+)*/g) || []).map(n => n.replace(/,/g, "")), hn = new Set(nums(h)); if (nums(e).some(n => !hn.has(n))) return "e-number-not-in-headline";
  const r = _rt48bRule(h, x.asset); if (r && r[0] !== x.dir) return "contradicts-known-reaction";
  // the headline already states this asset's move ("Bitcoin dips to ...", "yields fall for the week"): the answer would be given away
  if ((RT48B_MV(RT48B_NM[x.asset], "up").test(h) || RT48B_MV(RT48B_NM[x.asset], "down").test(h))) return "headline-states-move";
  if (x.link && !/^https:\/\/[^\s"'<>]{5,300}$/.test(x.link)) return "bad-link"; return ""; } catch (e) { return "error"; } }
function _rt48bValid(x) { return !_rt48bWhy(x); }
function _rt48sLoad() { try { const o = JSON.parse(require("fs").readFileSync(_rt48sFile, "utf8")); if (o && o.day === _rt48sDay() && Array.isArray(o.items)) Object.assign(_rt48sState, { day: o.day, generatedAt: o.generatedAt || "", items: o.items, kind: o.kind || "template", tries: o.tries || 0, last: o.last || 0, forced: o.forced || 0, diag: o.diag || null }); } catch (e) {} }
function _rt48sSave() { try { const { day, generatedAt, items, kind, tries, last, forced, diag } = _rt48sState; require("fs").writeFileSync(_rt48sFile, JSON.stringify({ day, generatedAt, items, kind, tries, last, forced, diag })); } catch (e) {} }
function _rt48sTxt(s) { let t = String(s || "").replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1").replace(/<[^>]*>/g, " ");
  const N = { amp: "&", quot: '"', apos: "'", lt: "<", gt: ">", nbsp: " ", rsquo: "\u2019", lsquo: "\u2018", ldquo: "\u201c", rdquo: "\u201d", ndash: "\u2013", mdash: "\u2014", hellip: "\u2026", pound: "\u00a3", euro: "\u20ac", eacute: "\u00e9", middot: "\u00b7" };
  for (let k = 0; k < 3 && /&(#x?[0-9a-f]+|[a-z]+);/i.test(t); k++) t = t.replace(/&#x([0-9a-f]+);/gi, (m, h) => { const c = parseInt(h, 16); return c > 0 && c < 0x110000 ? String.fromCodePoint(c) : ""; })
    .replace(/&#(\d+);/g, (m, d) => { const c = Number(d); return c > 0 && c < 0x110000 ? String.fromCodePoint(c) : ""; }).replace(/&([a-z]+);/gi, (m, n) => N[n.toLowerCase()] != null ? N[n.toLowerCase()] : m);
  return t.replace(/[<>]/g, "").replace(/&[a-z]+;/gi, "").replace(/\s+/g, " ").trim(); }
function _rt48sParse(xml, src) { const out = [], re = /<item[\s>][\s\S]*?<\/item>/gi; let m; while ((m = re.exec(xml)) && out.length < 25) { const it = m[0], g = t => { const r = new RegExp("<" + t + "[^>]*>([\\s\\S]*?)</" + t + ">", "i").exec(it); return r ? _rt48sTxt(r[1]) : ""; };
  const h = g("title"), link = g("link"), t = Date.parse(g("pubDate") || g("dc:date") || ""); if (h.length < 20 || h.length > 240) continue; out.push({ h, link: /^https:\/\/[^\s"'<>]{5,300}$/.test(link) ? link : "", src, t: isFinite(t) ? t : 0 }); } return out; }
function _rt48bAssets(h) { if (RT48B_BAN.test(h)) return []; return Object.keys(RT48B_ASSETS).filter(k => RT48B_ASSETS[k][1].test(h) || _rt48bRule(h, k)); }
async function _rt48sHeads() { const feeds = [["f0", "BBC Business"], ["f1", "CNBC"], ["f4", "MarketWatch"], ["f12", "CoinDesk"], ["f9", "Investing.com"], ["f14", "BBC World"]], all = [];
  await Promise.all(feeds.map(async ([id, src]) => { try { const u = typeof approvedRssFeedUrl === "function" ? approvedRssFeedUrl(id) : null; if (!u) return;
    const r = await fetch(u, { headers: { "User-Agent": "DispatchMarkets/1.0" }, signal: AbortSignal.timeout(8000) }); if (!r.ok) return; all.push(..._rt48sParse((await r.text()).slice(0, 600000), src)); } catch (e) {} }));
  const now = Date.now(), seen = new Set();
  return all.filter(x => !/^live( updates)?:|\blive\b:/i.test(x.h) && (!x.t || now - x.t < 72 * 36e5) && !seen.has(x.h.toLowerCase()) && seen.add(x.h.toLowerCase())).map(x => ({ ...x, as: _rt48bAssets(x.h) })).filter(x => x.as.length).sort((a, b) => b.t - a.t).slice(0, 20); }
function _rt48bItem(H, asset, dir, e, kind) { const a = RT48B_DIRS.indexOf(dir); return { h: H.h, src: H.src, link: H.link, asset, dir, q: _rt48bQ(asset), o: RT48B_OPTS.slice(), a, e: String(e || "").trim(), kind }; }
function _rt48bTemplates(heads, skip, usedAs, want) { const out = [], cand = [];
  heads.forEach((H, hi) => { if (skip.has(H.h)) return; H.as.forEach(as => { const r = _rt48bRule(H.h, as); if (!r) return; const it = _rt48bItem(H, as, r[0], r[1], "template"); if (_rt48bValid(it)) cand.push({ it, hi }); }); });
  const usedH = new Set(skip), seenAs = new Set(usedAs || []);
  for (const pass of [0, 1]) for (const c of cand) { if (out.length >= want) break; if (usedH.has(c.it.h) || (pass === 0 && seenAs.has(c.it.asset))) continue; out.push(c.it); usedH.add(c.it.h); seenAs.add(c.it.asset); }
  return out; }
// read the provider reply: plain JSON, markdown-fenced JSON, prose around it, or a truncated reply (complete item objects are kept)
function _rt48bParse(t) { t = String(t || "").replace(/```(?:json|JSON)?/g, "").trim(); const tryJ = v => { try { return JSON.parse(v); } catch (e) { return null; } };
  let j = tryJ(t); if (!j) { const s0 = t.indexOf("{"), s1 = t.lastIndexOf("}"); if (s0 >= 0 && s1 > s0) j = tryJ(t.slice(s0, s1 + 1)); }
  if (!j) { const s0 = t.indexOf("["), s1 = t.lastIndexOf("]"); if (s0 >= 0 && s1 > s0) j = tryJ(t.slice(s0, s1 + 1)); }
  let arr = Array.isArray(j) ? j : j && Array.isArray(j.items) ? j.items : j && typeof j === "object" ? (Object.values(j).find(Array.isArray) || null) : null, how = arr ? "json" : "";
  if (!arr) { arr = (t.match(/\{[^{}]*\}/g) || []).map(tryJ).filter(o => o && typeof o === "object" && ("asset" in o || "i" in o)); how = arr.length ? "salvaged" : "unreadable"; }
  return { arr: arr.slice(0, 12), how }; }
const RT48B_ALIAS = { "s&p 500": "spx", "s&p": "spx", "sp500": "spx", "s&p500": "spx", "spx": "spx", "us stocks": "spx", "stocks": "spx", "wall street": "spx", "dollar": "usd", "us dollar": "usd", "u.s. dollar": "usd", "dxy": "usd", "usd": "usd",
  "treasury yields": "yields", "us yields": "yields", "us treasury yields": "yields", "yield": "yields", "yields": "yields", "bitcoin": "btc", "btc": "btc", "ether": "eth", "ethereum": "eth", "eth": "eth", "euro": "eurusd", "eur/usd": "eurusd", "eurusd": "eurusd", "eur": "eurusd",
  "pound": "gbp", "sterling": "gbp", "gbp": "gbp", "gbp/usd": "gbp", "gbpusd": "gbp", "british pound": "gbp", "gold": "gold", "xau": "gold", "xauusd": "gold", "oil": "oil", "crude": "oil", "crude oil": "oil", "brent": "oil", "wti": "oil", "nasdaq": "nasdaq", "nasdaq 100": "nasdaq" };
function _rt48bAsId(v) { const k = String(v || "").toLowerCase().replace(/[()]/g, "").replace(/\s+/g, " ").trim(); return RT48B_ASSETS[k] ? k : RT48B_ALIAS[k] || ""; }
function _rt48bDirId(v) { const k = String(v || "").toLowerCase().trim(); return /^(up|higher|rise|rises|bullish|positive|increase)$/.test(k) ? "up" : /^(down|lower|fall|falls|bearish|negative|decrease)$/.test(k) ? "down" : /^(flat|little change|unchanged|neutral|sideways|little|none)$/.test(k) ? "flat" : ""; }
async function _rt48sBuild(why) { const day = _rt48sDay(), t0 = Date.now(), D = { at: new Date().toISOString(), why: why || "auto", heads: 0, ai: "not-called", model: "", ms: 0, replyChars: 0, parse: "", received: 0, accepted: 0, rejected: {}, samples: [], templates: 0, served: 0 };
  _rt48sState.tries++; _rt48sState.last = Date.now(); _rt48sSave();
  try { const heads = await _rt48sHeads(); let items = []; D.heads = heads.length;
    if (!heads.length) D.ai = "no-headlines"; else if (String(process.env.ACADEMY_AI || "").toLowerCase() === "off") D.ai = "off (ACADEMY_AI)"; else if (typeof generateAi !== "function") D.ai = "no-generateAi";
    else {
      try { const list = heads.map((x, k) => `${k}. ${x.h} [assets: ${x.as.join(", ")}]`).join("\n");
        const r = await generateAi({ maxTokens: 1600, temperature: 0.2,
          system: "You help write a free beginner markets course. From the numbered headlines, choose up to 4 where the usual FIRST market reaction is well established in finance textbooks, and for each name ONE asset id from that headline's [assets: ...] list and the usual first move in that asset's price if the news were a surprise: up, down or flat. Prefer an asset whose move the headline does NOT already state (e.g. for 'Dollar slips' choose gold or eurusd, not usd). Never pick a stablecoin. The explanation: one or two plain British English sentences, at most 260 characters, saying this is the typical or usual first reaction and why, using the words rise/fall (or little change); no digits at all, no predictions, no advice. Reply with raw JSON only, no markdown.",
          messages: [{ role: "user", content: `Headlines:\n${list}\n\nReturn {"items":[{"i":<headline number>,"asset":"<asset id from that headline's list>","dir":"up|down|flat","e":"<explanation>"}]}` }] });
        const txt = String(r && r.text || ""); D.ai = "ok"; D.model = String(r && r.model || "").slice(0, 60); D.replyChars = txt.length;
        const P = _rt48bParse(txt); D.parse = P.how; D.received = P.arr.length;
        const used = new Set(), rej = (why, x, extra) => { D.rejected[why] = (D.rejected[why] || 0) + 1; if (D.samples.length < 8) D.samples.push(Object.assign({ why, i: x && x.i, asset: String(x && x.asset || "").slice(0, 20), dir: String(x && x.dir || "").slice(0, 16), e: String(x && x.e || "").slice(0, 200) }, extra || {})); };
        P.arr.forEach(x => { if (!x || typeof x !== "object") return rej("not-object", x);
          let i = Number(x.i != null ? x.i : x.index), H = Number.isInteger(i) ? heads[i] : null;
          const ht = String(x.h || x.headline || "").toLowerCase().trim(); if ((!H || (ht && H.h.toLowerCase() !== ht)) && ht) H = heads.find(y => y.h.toLowerCase() === ht) || H;
          if (!H) return rej("bad-headline-index", x); const as = _rt48bAsId(x.asset), dir = _rt48bDirId(x.dir);
          if (!as) return rej("asset-not-allowed", x, { h: H.h.slice(0, 120) }); if (!H.as.includes(as)) return rej("asset-not-in-headline-list", x, { h: H.h.slice(0, 120) });
          if (used.has(H.h)) return rej("duplicate-headline", x); if (items.length >= 3) return rej("over-limit", x);
          const it = _rt48bItem(H, as, dir, x.e, "ai"), w = _rt48bWhy(it); if (w) return rej(w, x, { h: H.h.slice(0, 120) }); items.push(it); used.add(H.h); D.accepted++; });
      } catch (e) { D.ai = "error: " + String((e && (e.code || e.name)) || "unknown").slice(0, 40); try { console.warn("academy-daily: AI skipped", (e && (e.code || e.message)) || e); } catch (x) {} } }
    const tp = _rt48bTemplates(heads, new Set(items.map(x => x.h)), items.map(x => x.asset), 3 - items.length); D.templates = tp.length; items = items.concat(tp).slice(0, 3); D.served = items.length; D.ms = Date.now() - t0;
    if (_rt48sDay() === day && (items.length || !_rt48sState.items.length)) Object.assign(_rt48sState, { day, generatedAt: new Date().toISOString(), items, kind: items.some(x => x.kind === "ai") ? "ai" : "template" });
    if (_rt48sDay() === day) { _rt48sState.diag = D; _rt48sSave(); }
  } catch (e) { try { console.warn("academy-daily: build skipped", (e && (e.code || e.message)) || e); } catch (x) {} } }
async function academyDaily(req, res) {
  let forced = false, admin = false, wantDiag = false;
  const send = () => { const s = _rt48sState, today = s.day === _rt48sDay(), items = today ? s.items.filter(_rt48bValid) : [], out = { date: _rt48sDay(), generatedAt: today && items.length ? s.generatedAt : "", kind: items.some(x => x.kind === "ai") ? "ai" : "template", items, v: 3 };
    if (admin && wantDiag) out.diag = Object.assign({ tries: s.tries, forced: s.forced || 0, busy: !!s.busy, aiSwitch: String(process.env.ACADEMY_AI || "").toLowerCase() === "off" ? "off" : "on" }, today && s.diag ? s.diag : { note: "no build yet today" });
    res.writeHead(200, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": admin && wantDiag ? "no-store" : "private, max-age=300", "X-Content-Type-Options": "nosniff" }); res.end(JSON.stringify(out)); };
  try { const day = _rt48sDay(); if (_rt48sState.day !== day) { _rt48sLoad(); if (_rt48sState.day !== day) Object.assign(_rt48sState, { day, generatedAt: "", items: [], kind: "template", tries: 0, last: 0, forced: 0, diag: null }); }
    const n0 = _rt48sState.items.length; _rt48sState.items = _rt48sState.items.filter(_rt48bValid); // drop cached items that fail the current rules
    if (n0 && !_rt48sState.items.length) { _rt48sState.tries = 0; _rt48sState.last = 0; _rt48sSave(); }
    try { const q = new URL(req.url || "/", "http://x").searchParams; const rf = q.get("refresh") === "1"; wantDiag = rf || q.get("diag") === "1";
      if (wantDiag && typeof currentUser === "function" && typeof isAdminUser === "function") { const u = await currentUser(req); admin = !!(u && isAdminUser(u)); if (admin && rf && (_rt48sState.forced || 0) < 6) forced = true; } } catch (e) {}
    const S = _rt48sState, weak = S.items.length < 3 || !S.items.some(x => x.kind === "ai");
    if (forced && !S.busy) { S.forced = (S.forced || 0) + 1; S.busy = _rt48sBuild("admin-refresh").finally(() => { S.busy = null; }); }
    else if (weak && !S.busy && S.tries < 3 && Date.now() - S.last > 2 * 36e5) S.busy = _rt48sBuild(S.items.length ? "auto-retry" : "auto").finally(() => { S.busy = null; });
    if (S.busy) await Promise.race([S.busy, new Promise(r => setTimeout(r, forced ? 45000 : 6000))]);
  } catch (e) {}
  try { return send(); } catch (e) { try { res.end(); } catch (x) {} } }
const MARKET_SYSTEM = `You are Dispatch Expert, a careful market-research assistant. Use only the supplied market context and clearly identify uncertainty. Do not claim real-time facts that were not provided. Do not provide personalized financial advice or guarantees. Keep analysis factual, concise, and useful for independent research.`;
function normaliseBrief(value) {
  const today = new Date().toISOString().slice(0, 10);
  const date = /^\d{4}-\d{2}-\d{2}$/.test(String(value?.date || "")) ? String(value.date) : today;
  return {
    date,
    headline: safeText(value?.headline, 180),
    houseView: safeText(value?.houseView, 80) || "MONITOR",
    summary: safeText(value?.summary, 1400),
    focusTickers: Array.isArray(value?.focusTickers) ? value.focusTickers.slice(0, 8).map(item => safeText(item, 24)).filter(Boolean) : [],
    overweight: Array.isArray(value?.overweight) ? value.overweight.slice(0, 8).map(item => safeText(item, 120)).filter(Boolean) : [],
    risks: Array.isArray(value?.risks) ? value.risks.slice(0, 8).map(item => safeText(item, 220)).filter(Boolean) : [],
    confidence: Math.max(0, Math.min(100, Number(value?.confidence) || 0)),
  };
}
function asNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}
function goldLevels(value, price, direction) {
  const items = Array.isArray(value) ? value : [];
  const levels = items.map((item, index) => ({
    level: asNumber(typeof item === "object" ? item?.level : item),
    strength: safeText(typeof item === "object" ? item?.strength : "", 80),
    hits: Math.max(0, Math.min(99, Number(item?.hits) || 0)),
  })).filter(item => item.level != null).slice(0, 4);
  if (levels.length || !price) return levels;
  return [1, 2].map(step => ({
    level: Number((price * (1 + direction * step * 0.01)).toFixed(2)),
    strength: "Illustrative 1% interval from current price",
    hits: 0,
  }));
}
function goldScenario(value, label, price, direction) {
  const targets = (Array.isArray(value?.targets) ? value.targets : [])
    .map(asNumber).filter(target => target != null).slice(0, 3);
  if (!targets.length && price) targets.push(Number((price * (1 + direction * 0.01)).toFixed(2)));
  return {
    title: safeText(value?.title, 100) || `${label} scenario`,
    thesis: safeText(value?.thesis, 900),
    entry: safeText(value?.entry, 500),
    invalidation: safeText(value?.invalidation, 500),
    targets,
  };
}
function normaliseGoldDesk(value, quotes) {
  const gold = quotes["GC=F"];
  const price = asNumber(gold?.p);
  if (!price) throw new AiRequestError(502, "Live gold market data is unavailable. Please try again shortly.", "MARKET_DATA_UNAVAILABLE");
  const model = value && typeof value === "object" ? value : {};
  const today = new Date().toISOString().slice(0, 10);
  const normaliseMacro = symbol => {
    const quote = quotes[symbol] || {};
    return { px: asNumber(quote.p), chg: asNumber(quote.c) };
  };
  const events = (Array.isArray(model.events) ? model.events : []).slice(0, 8).map(event => ({
    date: safeText(event?.date, 32),
    event: safeText(event?.event, 160),
    impact: ["low", "medium", "high"].includes(event?.impact) ? event.impact : "medium",
    cat: safeText(event?.cat, 80) || "Macro",
    goldNote: safeText(event?.goldNote, 300),
  }));
  const playbook = model.playbook || {};
  return {
    asOf: new Date().toISOString(),
    dataSource: "Yahoo Finance market snapshot + xAI scenario analysis",
    gold: { price, changePct: asNumber(gold?.c), spark: [] },
    structure: {
      regime: safeText(model.structure?.regime, 80) || "Monitor",
      bias: ["bullish", "bearish", "range"].includes(model.structure?.bias) ? model.structure.bias : "range",
      summary: safeText(model.structure?.summary, 1000),
    },
    levels: {
      support: goldLevels(model.levels?.support, price, -1),
      resistance: goldLevels(model.levels?.resistance, price, 1),
    },
    sessions: { source: "Yahoo Finance snapshot" },
    volumeProfile: { bins: [], note: "Volume profile is unavailable from this market snapshot." },
    volatility: {
      condition: safeText(model.volatility?.condition, 80) || "Monitor",
      atr14: asNumber(model.volatility?.atr14),
      realizedVol20dPct: asNumber(model.volatility?.realizedVol20dPct),
    },
    macro: { dxy: normaliseMacro("DX-Y.NYB"), tnx: normaliseMacro("^TNX"), vix: normaliseMacro("^VIX") },
    gamma: {
      disclaimer: "Scenario levels are research aids, not dealer gamma estimates.",
      levels: [],
    },
    events,
    playbook: {
      weekId: safeText(playbook.weekId, 32) || today,
      weekLabel: safeText(playbook.weekLabel, 100) || `Week of ${today}`,
      regime: {
        bias: ["bullish", "bearish", "range"].includes(playbook.regime?.bias) ? playbook.regime.bias : "range",
        summary: safeText(playbook.regime?.summary, 1000) || safeText(model.structure?.summary, 1000),
      },
      disclaimer: "Conditional research scenario — not investment advice.",
      macroContext: (Array.isArray(playbook.macroContext) ? playbook.macroContext : []).slice(0, 6).map(item => safeText(item, 300)),
      scenarios: {
        bullish: goldScenario(playbook.scenarios?.bullish, "Bullish", price, 1),
        bearish: goldScenario(playbook.scenarios?.bearish, "Bearish", price, -1),
        range: goldScenario(playbook.scenarios?.range, "Range", price, 0),
      },
      keyLevels: { gammaLiquidity: [] },
      eventsThatChangeThesis: events.map(event => ({ date: event.date, event: event.event, impact: event.impact, ifThen: event.goldNote })),
      checklist: (Array.isArray(playbook.checklist) ? playbook.checklist : []).slice(0, 8).map(item => safeText(item, 300)),
    },
  };
}
async function yahooQuote(symbols) {
  const out = {};
  await Promise.all(symbols.slice(0, 60).map(async symbol => {
    try {
      const u = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?range=5d&interval=1d`;
      const d = await (await upstream(u)).json();
      const meta = d.chart?.result?.[0]?.meta;
      if (!meta || typeof meta.regularMarketPrice !== "number") return;
      const price = meta.regularMarketPrice;
      const prev = meta.previousClose || meta.chartPreviousClose || price;
      out[symbol] = {
        p: price, c: prev ? ((price - prev) / prev) * 100 : 0, prev,
        change: price - prev, currency: meta.currency, exchange: meta.exchangeName,
        name: meta.longName || meta.shortName || symbol, ts: meta.regularMarketTime
      };
    } catch {}
  }));
  return out;
}
async function twelveDataQuote(symbols) {
  const apiKey = process.env.TWELVE_DATA_API_KEY;
  const requested = normalizeTwelveDataSymbols(symbols);
  if (!apiKey) return { configured: false, quotes: {} };
  if (!requested.length) return { configured: true, quotes: {} };

  const cacheKey = requested.join(",");
  const cached = twelveDataCache.get(cacheKey);
  if (cached) return { configured: true, cached: true, ...cached };
  if (!twelveDataDailyRateLimiter.allow("core-tape")) {
    return { configured: true, unavailable: true, reason: "daily_limit", quotes: {} };
  }

  try {
    const response = await fetch(
      `https://api.twelvedata.com/quote?symbol=${encodeURIComponent(requested.join(","))}`,
      {
        headers: {
          "User-Agent": "DispatchMarkets/1.0",
          Authorization: `apikey ${apiKey}`,
        },
        signal: AbortSignal.timeout(8_000),
      },
    );
    if (!response.ok) throw new Error(`Twelve Data ${response.status}`);
    const quotes = normalizeTwelveDataQuotes(await response.json());
    if (!Object.keys(quotes).length) throw new Error("Twelve Data returned no usable quotes");
    const result = { quotes, fetchedAt: Date.now() };
    twelveDataCache.set(cacheKey, result, TWELVE_DATA_CACHE_MS);
    return { configured: true, ...result };
  } catch {
    // The caller falls back to Yahoo's explicitly delayed feed for this cycle.
    return { configured: true, unavailable: true, quotes: {} };
  }
}
function serveStatic(req, res, pathname) {
  const requested = pathname === "/" ? "/index.html" : pathname;
  const file = path.normalize(path.join(root, requested));
  if (!file.startsWith(root) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) return false;
  const types = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml", ".json": "application/json", ".txt": "text/plain" };
  res.writeHead(200, {
    "Content-Type": types[path.extname(file)] || "application/octet-stream",
    "Cache-Control": "no-store",
  });
  fs.createReadStream(file).pipe(res);
  return true;
}

function publicUrl(req) {
  const domain = process.env.REPLIT_DOMAINS?.split(",")[0];
  if (domain) return `https://${domain}`;
  const forwardedProtocol = String(req.headers["x-forwarded-proto"] || "").split(",")[0];
  const protocol = forwardedProtocol === "https" ? "https" : "http";
  return `${protocol}://${req.headers.host || `localhost:${PORT}`}`;
}
function premiumFromSubscription(subscription) {
  return ["active", "trialing"].includes(subscription?.status);
}
async function updateUserMembership({ customerId, subscription }) {
  const userId = subscription?.metadata?.dispatch_user_id;
  const result = userId
    ? await sql`SELECT COALESCE(json_agg(row_to_json(uq)), '[]'::json) AS data FROM (SELECT id, email, password_hash AS "passwordHash", tier,
        billing_portal AS "billingPortal", stripe_customer_id AS "stripeCustomerId",
        stripe_subscription_id AS "stripeSubscriptionId", checkout_session AS "checkoutSession",
        checkout_attempt_id AS "checkoutAttemptId" FROM dispatch_users WHERE id=${userId} LIMIT 1) uq`
    : await sql`SELECT COALESCE(json_agg(row_to_json(uq)), '[]'::json) AS data FROM (SELECT id, email, password_hash AS "passwordHash", tier,
        billing_portal AS "billingPortal", stripe_customer_id AS "stripeCustomerId",
        stripe_subscription_id AS "stripeSubscriptionId", checkout_session AS "checkoutSession",
        checkout_attempt_id AS "checkoutAttemptId" FROM dispatch_users WHERE stripe_customer_id=${customerId} LIMIT 1) uq`;
  const user = result[0]?.data?.[0];
  if (!user) return;

  user.stripeCustomerId = customerId;
  user.stripeSubscriptionId = subscription?.id || user.stripeSubscriptionId || null;
  user.tier = premiumFromSubscription(subscription) ? "premium" : "free";
  user.billingPortal = Boolean(customerId);
  await saveUser(user);
}
async function syncMembershipFromSubscription(customerId, subscriptionId) {
  if (!subscriptionId) return;
  const stripe = await getUncachableStripeClient();
  const subscription = await stripe.subscriptions.retrieve(subscriptionId);
  updateUserMembership({ customerId: String(customerId || subscription.customer), subscription });
}
async function applyStripeMembershipEvent(event) {
  const object = event?.data?.object;
  if (!object) return;
  if (event.type.startsWith("customer.subscription.")) {
    // Webhooks can arrive out of order. Read Stripe's current subscription
    // before changing access so an old "active" snapshot cannot undo a later
    // cancellation.
    await syncMembershipFromSubscription(object.customer, object.id);
    return;
  }
  if (event.type === "checkout.session.completed") {
    await syncMembershipFromSubscription(object.customer, object.subscription);
    return;
  }
  if (event.type === "invoice.paid" || event.type === "invoice.payment_failed") {
    await syncMembershipFromSubscription(object.customer, object.subscription);
  }
}
async function initializeStripe() {
  try {
    if (!process.env.DATABASE_URL) throw new Error("DATABASE_URL is unavailable.");
    await runMigrations({ databaseUrl: process.env.DATABASE_URL });
    const sync = await getStripeSync();
    const domain = process.env.REPLIT_DOMAINS?.split(",")[0];
    if (!domain) throw new Error("REPLIT_DOMAINS is unavailable for managed Stripe webhooks.");
    await sync.findOrCreateManagedWebhook(`https://${domain}/api/stripe/webhook`, {
      enabled_events: [
        "checkout.session.completed",
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
        "invoice.paid",
        "invoice.payment_failed",
      ],
      description: "The Dispatch membership synchronization",
    });
    await sync.syncBackfill();
    await ensureDispatchPremiumPrice();
    stripeState = { ready: true, mode: await getStripeMode(), error: null };
    console.log(`Stripe membership billing ready (${stripeState.mode} mode).`);
  } catch (error) {
    stripeState = { ready: false, mode: null, error: error.message || "Stripe initialization failed." };
    console.error("Stripe membership billing unavailable:", error);
  }
}
function assertTestDatabaseIsolation() {
  if (process.env.NODE_ENV !== "test") return;
  const testDatabaseUrl = process.env.AUTH_TEST_DATABASE_URL;
  if (!testDatabaseUrl || testDatabaseUrl !== process.env.DATABASE_URL) {
    throw new Error("NODE_ENV=test requires DATABASE_URL to be AUTH_TEST_DATABASE_URL.");
  }
  if (process.env.APPLICATION_DATABASE_URL && testDatabaseUrl === process.env.APPLICATION_DATABASE_URL) {
    throw new Error("NODE_ENV=test refuses to use the application database.");
  }
}

async function handle(req, res) {
  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  const p = url.pathname;
  { // rt43s: pricing page, /upgrade, shared energy spot
    let rp = ""; try { rp = new URL(req.url, "http://localhost").pathname; } catch {}
    if (req.method === "GET" || req.method === "HEAD") {
      if (rp === "/upgrade" || rp === "/upgrade/") { res.writeHead(302, { Location: "/pricing" }); return res.end(); }
      if (rp === "/pricing" || rp === "/pricing/") return rt43sPricing(req, res);
      if (rp === "/api/spot-energy") return rt43sEnergy(res);
      if (rp === "/api/eia-spot") return rt44Eia(res); // rt44: EIA official spot
      if (rp === "/api/ext-hours") return rt43bExt(req, res); // rt43b: extended-hours prints
    }
  }
  { // rt42s: pretty ticker URLs -> the markets deep link
    const m = req.method === "GET" || req.method === "HEAD" ? p.match(/^\/(?:markets|stock|stocks|ticker|quote|symbol)\/([A-Za-z0-9^][A-Za-z0-9.\-=^]{0,14})\/?$/) : null;
    if (m && !/\.(?:html?|js|css|json|xml|txt|png|jpe?g|svg|ico|webp|map|gz|br)$/i.test(m[1])) {
      res.writeHead(301, { Location: "/markets/?t=" + encodeURIComponent(m[1].toUpperCase()), "Cache-Control": "public, max-age=3600" });
      return res.end();
    }
  }
  if (p === "/__auth/login" && req.method === "GET") return page(res, "Sign in · The Dispatch", `<h1>THE DISPATCH</h1><p>Sign in to your market intelligence workspace.</p><form method="post"><label>Email</label><input name="email" type="email" required><label>Password</label><input name="password" type="password" minlength="8" required><button>Sign in</button></form><p class="muted"><a href="/__auth/recover">Forgot your password?</a></p><p class="muted">New here? Start your Premium checkout to create a Dispatch sign-in.</p>`);
  if (p === "/__auth/recover" && req.method === "GET") return page(res, "Recover access", `<h1>RECOVER ACCESS</h1><p>Enter your account email to create a one-time password reset link.</p><form method="post"><label>Email</label><input name="email" type="email" required><button>Create reset link</button></form><p class="muted">Reset links expire after 30 minutes.</p>`);
  if (p === "/__auth/recover" && req.method === "POST") {
    let raw = ""; for await (const c of req) raw += c;
    const email = (new URLSearchParams(raw).get("email") || "").trim().toLowerCase();
    const user = await findUserByEmail(email);
    if (!user) return page(res, "Recover access", "<h1>Check your email</h1><p>If an account exists, a reset link has been created. <a href='/__auth/recover'>Try again</a></p>");
    const token = crypto.randomBytes(32).toString("hex");
    await sql`DELETE FROM dispatch_password_resets WHERE user_id=${user.id}`;
    await sql`INSERT INTO dispatch_password_resets (token_hash, user_id, expires_at) VALUES (${tokenHash(token)}, ${user.id}, NOW() + INTERVAL '30 minutes')`;
    return page(res, "Reset password", `<h1>RESET LINK READY</h1><p class="muted">In production, this link would be emailed to you.</p><a href="/__auth/reset?token=${encodeURIComponent(token)}">Reset password</a>`);
  }
  if (p === "/__auth/reset" && req.method === "GET") return page(res, "Reset password", `<h1>RESET PASSWORD</h1><form method="post"><input type="hidden" name="token" value="${url.searchParams.get("token") || ""}"><label>New password</label><input name="password" type="password" minlength="8" required><button>Set password</button></form>`);
  if (p === "/__auth/reset" && req.method === "POST") {
    let raw = ""; for await (const c of req) raw += c;
    const form = new URLSearchParams(raw); const token = form.get("token") || ""; const password = form.get("password") || "";
    const resetResult = await sql`SELECT COALESCE(json_agg(row_to_json(rq)), '[]'::json) AS data FROM (SELECT user_id FROM dispatch_password_resets WHERE token_hash=${tokenHash(token)} AND used_at IS NULL AND expires_at > NOW() LIMIT 1) rq`;
    const reset = resetResult[0]?.data?.[0];
    if (!reset || !validAccountInput("reset@example.com", password)) return page(res, "Reset failed", "<h1>Reset link expired</h1><p>Request a new password reset link.</p><a href='/__auth/recover'>Recover access</a>");
    const hash = passwordHash(password);
    await sql`UPDATE dispatch_users SET password_hash=${hash} WHERE id=${reset.user_id}`;
    await sql`UPDATE dispatch_password_resets SET used_at=NOW() WHERE token_hash=${tokenHash(token)}`;
    await sql`DELETE FROM dispatch_sessions WHERE user_id=${reset.user_id}`;
    return page(res, "Password reset", "<h1>PASSWORD UPDATED</h1><p>Your old sessions were signed out. You can now sign in.</p><a href='/__auth/login'>Sign in</a>");
  }
  if (p === "/__auth/login" && req.method === "POST") {
    let raw = ""; for await (const c of req) raw += c;
    const form = new URLSearchParams(raw);
    const email = (form.get("email") || "").trim().toLowerCase();
    const password = form.get("password") || "";
    const user = await findUserByEmail(email);
    if (!user || !validAccountInput(email, password) || !validPassword(password, user.passwordHash)) {
      return page(res, "Sign in", "<h1>Sign in failed</h1><p>Check your email and password, or start Premium to create an account.</p><a href='/__auth/login'>Try again</a>");
    }
    await setSession(res, user, cookieValue(req, "dispatch_session")); res.writeHead(302, { Location: "/" }); return res.end();
  }
  if (p === "/__auth/subscribe" && req.method === "GET") {
    const user = await currentUser(req);
    if (user && (user.tier === "premium" || isAdminUser(user))) return page(res, "Premium active · The Dispatch", `<h1>PREMIUM ACTIVE</h1><p>Your account already has Premium. Nothing else to buy.</p>${user.billingPortal ? `<p class="muted">Manage or cancel your subscription from Settings → Manage billing.</p><a href="/settings/">Open Settings</a>` : `<p class="muted">Premium is included with this account, so there is no Stripe billing to manage.</p><a href="/">Back to The Dispatch</a>`}`);
    if (user) return page(res, "Premium · The Dispatch", `<h1>PREMIUM ACCESS</h1><p>Continue to Stripe Checkout to unlock the weekly Gold Playbook, the AI Dispatch Brief, Ask and AI lenses, company statements and institutional holders. <a href="/pricing">Compare plans</a>.</p><form method="post"><button>Continue to secure checkout</button></form><p class="muted">£15/month · Cancel anytime in the Stripe billing portal.</p>`);
    return page(res, "Premium · The Dispatch", `<h1>PREMIUM ACCESS</h1><p>Create your Dispatch sign-in, then continue to secure Stripe Checkout.</p><form method="post"><label>Email</label><input name="email" type="email" required><label>Password</label><input name="password" type="password" minlength="8" required><button>Continue to secure checkout</button></form><p class="muted">£15/month · Cancel anytime in the Stripe billing portal.</p>`);
  }
  if (p === "/__auth/subscribe" && req.method === "POST") {
    let raw = ""; for await (const c of req) raw += c;
    const form = new URLSearchParams(raw);
    let user = await currentUser(req);
    if (!user) {
      const email = (form.get("email") || "").trim().toLowerCase();
      const password = form.get("password") || "";
      if (!validAccountInput(email, password)) return page(res, "Subscribe", "<h1>Use a valid email and a password of at least 8 characters.</h1><a href='/__auth/subscribe'>Try again</a>");
      user = await findUserByEmail(email);
      if (user && !validPassword(password, user.passwordHash)) {
        return page(res, "Subscribe", "<h1>Sign in failed</h1><p>This email already has an account. Use its password to continue.</p><a href='/__auth/login'>Sign in</a>");
      }
      if (!user) {
        user = { id: crypto.randomUUID(), email, passwordHash: passwordHash(password), tier: "free", billingPortal: false };
        await sql`INSERT INTO dispatch_users (id, email, password_hash) VALUES (${user.id}, ${user.email}, ${user.passwordHash})`;
      }
      await setSession(res, user, cookieValue(req, "dispatch_session"));
    }
    res.writeHead(302, { Location: "/?checkout=1" }); return res.end();
  }
  if (p === "/__auth/logout") { const token = cookieValue(req, "dispatch_session"); if (token) await sql`DELETE FROM dispatch_sessions WHERE token_hash=${tokenHash(token)}`; res.setHeader("Set-Cookie", "dispatch_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"); res.writeHead(302, { Location: "/" }); return res.end(); }

  if (p === "/api/me") return json(res, 200, publicUser(await currentUser(req)));
  if (p === "/api/stripe-status") return json(res, 200, {
    active: (await currentUser(req))?.tier === "premium",
    configured: stripeState.ready,
    mode: stripeState.mode,
  });
  if (p === "/api/stripe/webhook" && req.method === "POST") {
    const signature = req.headers["stripe-signature"];
    if (!signature || Array.isArray(signature)) return json(res, 400, { error: "Missing stripe-signature" });
    try {
      const payload = await readRawBody(req);
      const sync = await getStripeSync();
      await sync.processWebhook(payload, signature);
      // The sync engine verifies the signature before this payload is used for
      // the app's in-memory access gate.
      await applyStripeMembershipEvent(JSON.parse(payload.toString("utf8")));
      return json(res, 200, { received: true });
    } catch (error) {
      console.error("Stripe webhook rejected:", error.message || error);
      return json(res, 400, { error: "Webhook processing error" });
    }
  }
  if (p === "/api/yahoo-quote") return json(res, 200, await yahooQuote((url.searchParams.get("symbols") || "").split(",").map(s => s.trim()).filter(Boolean)));
  if (p === "/api/twelve-data-quote") {
    return json(res, 200, await twelveDataQuote((url.searchParams.get("symbols") || "").split(",").map(s => s.trim()).filter(Boolean)));
  }
  if (p === "/api/academy-daily") return academyDaily(req, res);
  if (p === "/api/yahoo-chart") {
    try { const symbol = url.searchParams.get("symbol"); const range = url.searchParams.get("range") || "5d"; const interval = url.searchParams.get("interval") || "15m"; return json(res, 200, await (await upstream(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?range=${encodeURIComponent(range)}&interval=${encodeURIComponent(interval)}`)).json()); }
    // Chart data is decorative/optional. An empty chart response keeps the
    // terminal honest without turning an upstream blip into client-side noise.
    catch { return json(res, 200, { chart: { result: [], error: { description: "Market chart feed unavailable" } } }); }
  }
  if (p === "/api/coingecko") return coinGecko(req, res, url.searchParams.get("path"));
  if (p === "/api/search") {
    try { return json(res, 200, await (await upstream(`https://query1.finance.yahoo.com/v1/finance/search?q=${encodeURIComponent(url.searchParams.get("q") || "")}&quotesCount=8&newsCount=0`)).json()); }
    catch { return json(res, 502, { quotes: [] }); }
  }
  if (p === "/api/finnhub") {
    if (url.searchParams.get("endpoint") === "quote") {
      const symbol = url.searchParams.get("symbol");
      const quotes = await yahooQuote([symbol]);
      return json(res, 200, quotes[symbol] || {});
    }
    return json(res, 200, []);
  }
  if (p === "/api/rss-feed") {
    return rssFeed(req, res, url.searchParams.get("feed"));
  }
  if (p === "/api/geo") {
    try { return json(res, 200, await (await upstream("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson")).json()); } catch { return json(res, 502, { events: [] }); }
  }
  if (p === "/api/economics") return json(res, 200, { data: [] });
  if (p === "/api/ticker-news") return rt37sNews(res, url);
  if (p === "/terms" || p === "/terms/" || p === "/privacy" || p === "/privacy/") return rt33sLegal(res, p);
  if (["/api/financials", "/api/earnings", "/api/statements", "/api/holders"].includes(p)) return rt33sFund(req, res, p, url);
  if (["/api/brief", "/api/intelligence", "/api/lenses", "/api/committee", "/api/chat", "/api/gold-desk"].includes(p)) {
    const user = await currentUser(req);
    if (!user || user.tier !== "premium") return json(res, 401, { error: "Premium membership required" });
    const body = req.method === "POST" ? await readBody(req) : {};
    try {
      if (p === "/api/chat") {
        const context = clipped(JSON.stringify(body.context || {}), 12000);
        const result = await generateAi({
          system: `${MARKET_SYSTEM}\nAnswer the user's market question using the terminal context below. Use short paragraphs and bullets where useful.\nTERMINAL CONTEXT:\n${context}`,
          messages: asAiMessages(body.messages, 12),
          maxTokens: 1200,
          temperature: 0.25,
        });
        return json(res, 200, { reply: safeText(result.text, 9000), meta: { provider: "xAI", model: result.model } });
      }
      if (p === "/api/brief") {
        const context = clipped(JSON.stringify(body.context || {}), 16000);
        const result = await generateAi({
          system: `${MARKET_SYSTEM}\nProduce a daily market brief from the supplied context. Return ONLY valid JSON with this schema: {"date":"YYYY-MM-DD","headline":"string","houseView":"string","summary":"string","focusTickers":["string"],"overweight":["string"],"risks":["string"],"confidence":0}. Do not invent data.\nMARKET CONTEXT:\n${context}`,
          messages: [{ role: "user", content: "Generate the Dispatch market brief." }],
          maxTokens: 1100,
        });
        return json(res, 200, { brief: normaliseBrief(jsonFromText(result.text)), cached: false, trial: false, preview: false, meta: { provider: "xAI", model: result.model } });
      }
      if (p === "/api/lenses") {
        const context = clipped(JSON.stringify({
          ticker: body.ticker, name: body.name, assetCategory: body.assetCategory,
          terminalContext: body.terminalContext, regime: body.regime, userThesis: body.userThesis,
        }), 18000);
        const result = await generateAi({
          system: `${MARKET_SYSTEM}\nAct as a multi-lens investment committee. Return ONLY valid JSON: {"lenses":[{"name":"string","role":"string","analysis":"string","verdict":"BUY|HOLD|SELL|MONITOR|IMPLEMENT"}],"intelligence":{"verdict":"string","confidence":0,"bullCase":"string","bearCase":"string","actionPlan":"string","keyDisagreements":["string"],"catalysts":["string"],"risks":["string"],"positionSizing":"string"}}. Provide 4-7 lenses, include a final risk synthesis, and state uncertainty.\nCONTEXT:\n${context}`,
          messages: [{ role: "user", content: "Generate the lens analysis." }],
          maxTokens: 1800,
        });
        const generated = jsonFromText(result.text);
        const lenses = Array.isArray(generated?.lenses) ? generated.lenses.slice(0, 8).map(lens => ({
          name: safeText(lens?.name, 80), role: safeText(lens?.role, 100), analysis: safeText(lens?.analysis, 1800), verdict: safeText(lens?.verdict, 30) || "MONITOR",
        })).filter(lens => lens.name && lens.analysis) : [];
        if (!lenses.length) throw new AiRequestError(502, "The AI returned no lens analysis. Please try again.", "INVALID_RESPONSE");
        return json(res, 200, { lenses, intelligence: safeGeneratedValue(generated.intelligence) || null, meta: { provider: "xAI", model: result.model } });
      }
      if (p === "/api/intelligence") {
        const context = clipped(JSON.stringify({ surface: body.surface, ticker: body.ticker, context: body.context }), 16000);
        const result = await generateAi({
          system: `${MARKET_SYSTEM}\nReturn ONLY valid JSON: {"headline":"string","insight":"string","anomalies":["string"],"actions":[{"label":"string","type":"chat","value":"string"}],"fit":[{"tk":"string","score":0}],"priority":"normal|high","usedSearch":false}. Base the output only on the supplied context.\nCONTEXT:\n${context}`,
          messages: [{ role: "user", content: "Generate a short site-intelligence update." }],
          maxTokens: 900,
        });
        return json(res, 200, { intel: safeGeneratedValue(jsonFromText(result.text)), meta: { provider: "xAI", model: result.model } });
      }
      if (p === "/api/committee") {
        const requestedSystem = clipped(body.system, 3000);
        const result = await generateAi({
          system: `${MARKET_SYSTEM}${requestedSystem ? `\nRequested output format: ${requestedSystem}` : ""}`,
          messages: asAiMessages(body.messages, 12),
          maxTokens: body.max_tokens || body.maxTokens || 1400,
          temperature: 0.2,
        });
        let content = safeText(result.text, 12000);
        try { content = JSON.stringify(safeGeneratedValue(jsonFromText(result.text))); } catch {}
        return json(res, 200, { content: [{ type: "text", text: content }], meta: { provider: "xAI", model: result.model } });
      }
      if (p === "/api/gold-desk") {
        const quotes = await withTimeout(yahooQuote(["GC=F", "DX-Y.NYB", "^TNX", "^VIX"]), 8000, "Gold market data timed out. Please try again.");
        const snapshot = {
          gold: quotes["GC=F"], dollarIndex: quotes["DX-Y.NYB"], treasury10Year: quotes["^TNX"], vix: quotes["^VIX"],
          asOf: new Date().toISOString(),
        };
        const result = await generateAi({
          system: `${MARKET_SYSTEM}\nCreate a conditional weekly gold research playbook from this market snapshot. Return ONLY valid JSON: {"structure":{"regime":"string","bias":"bullish|bearish|range","summary":"string"},"levels":{"support":[{"level":0,"strength":"string"}],"resistance":[{"level":0,"strength":"string"}]},"volatility":{"condition":"string","atr14":0,"realizedVol20dPct":0},"events":[{"date":"string","event":"string","impact":"low|medium|high","cat":"string","goldNote":"string"}],"playbook":{"weekId":"string","weekLabel":"string","regime":{"bias":"bullish|bearish|range","summary":"string"},"macroContext":["string"],"scenarios":{"bullish":{"title":"string","thesis":"string","entry":"string","invalidation":"string","targets":[0]},"bearish":{"title":"string","thesis":"string","entry":"string","invalidation":"string","targets":[0]},"range":{"title":"string","thesis":"string","entry":"string","invalidation":"string","targets":[0]}},"checklist":["string"]}}. Use the supplied snapshot only; state uncertainty rather than inventing events or prices.\nSNAPSHOT:\n${clipped(JSON.stringify(snapshot), 6000)}`,
          messages: [{ role: "user", content: "Generate the weekly gold desk playbook." }],
          maxTokens: 1800,
        });
        return json(res, 200, { ...normaliseGoldDesk(jsonFromText(result.text), quotes), meta: { provider: "xAI", model: result.model } });
      }
      return json(res, 200, { ok: true });
    } catch (error) {
      return sendAiError(res, error);
    }
  }
  if (p === "/api/screener") return json(res, 200, { data: [] });
  if (p === "/api/create-checkout" && req.method === "POST") {
    const user = await currentUser(req);
    if (!user) return json(res, 401, { error: "Sign in before starting checkout." });
    if (!stripeState.ready) return json(res, 503, { error: "Stripe billing is temporarily unavailable. Please try again shortly." });
    return withCheckoutLock(user.id, async () => {
      try {
        const stripe = await getUncachableStripeClient();
        if (!user.stripeCustomerId) {
          const customer = await stripe.customers.create({
            email: user.email,
            metadata: { dispatch_user_id: user.id },
          });
          user.stripeCustomerId = customer.id;
          user.billingPortal = true;
          await saveUser(user);
        }
        if (user.checkoutSession?.url && user.checkoutSession.expiresAt > Date.now()) {
          return json(res, 200, { url: user.checkoutSession.url });
        }
        user.checkoutSession = null;
        user.checkoutAttemptId = user.checkoutAttemptId || crypto.randomUUID();
        const subscriptions = await stripe.subscriptions.list({
          customer: user.stripeCustomerId,
          status: "all",
          limit: 100,
        });
        const billableSubscription = subscriptions.data.find(subscription =>
          ["active", "trialing", "past_due", "unpaid", "incomplete"].includes(subscription.status),
        );
        if (billableSubscription) {
          await syncMembershipFromSubscription(user.stripeCustomerId, billableSubscription.id);
          return json(res, 409, { error: "This account already has a subscription. Manage it in the billing portal." });
        }
        const price = await ensureDispatchPremiumPrice();
        const baseUrl = publicUrl(req);
        const checkout = await stripe.checkout.sessions.create({
          customer: user.stripeCustomerId,
          client_reference_id: user.id,
          mode: "subscription",
          line_items: [{ price: price.id, quantity: 1 }],
          subscription_data: { metadata: { dispatch_user_id: user.id } },
          success_url: `${baseUrl}/?checkout=success&session_id={CHECKOUT_SESSION_ID}`,
          cancel_url: `${baseUrl}/?checkout=cancelled`,
        }, {
          idempotencyKey: `dispatch-checkout-${user.id}-${user.checkoutAttemptId}`,
        });
        user.checkoutSession = { url: checkout.url, expiresAt: Date.now() + 30 * 60 * 1000 };
        await saveUser(user);
        return json(res, 200, { url: checkout.url });
      } catch (error) {
        console.error("Stripe checkout creation failed:", error.message || error);
        return json(res, 502, { error: "Unable to start Stripe Checkout. Please try again." });
      }
    });
  }
  if (p === "/api/billing-portal" && req.method === "POST") {
    const user = await currentUser(req);
    if (!user?.stripeCustomerId) return json(res, 400, { error: "No Stripe billing account is available for this sign-in." });
    if (!stripeState.ready) return json(res, 503, { error: "Stripe billing is temporarily unavailable. Please try again shortly." });
    try {
      const stripe = await getUncachableStripeClient();
      const portal = await stripe.billingPortal.sessions.create({
        customer: user.stripeCustomerId,
        return_url: publicUrl(req),
      });
      return json(res, 200, { url: portal.url });
    } catch (error) {
      console.error("Stripe portal creation failed:", error.message || error);
      return json(res, 502, { error: "Unable to open the Stripe billing portal." });
    }
  }
  if (serveStatic(req, res, p)) return;
  json(res, 404, { error: "Not found" });
}

const server = http.createServer((req, res) => {
  handle(req, res).catch(err => { console.error(err); if (!res.headersSent) json(res, 500, { error: "Server error" }); });
});
async function start() {
  assertTestDatabaseIsolation();
  await initializeAuthDatabase();
  await initializeStripe();
  server.listen(PORT, "0.0.0.0", () => console.log(`Dispatch Markets preview listening on ${PORT}`));
}
start().catch(error => {
  console.error("Application startup failed:", error);
  process.exitCode = 1;
});

// rt29s: coinGecko stale-while-error (fresh 5 min, family fallback < 24h, never days-old copies)
;(() => {
  try {
    if (typeof coinGecko !== "function" || typeof normalizeCoinGeckoPath !== "function" || typeof json !== "function") {
      console.warn("[rt29s] coinGecko override not installed (missing helper)"); return;
    }
    const FRESH = 5 * 60_000, SWR = 2 * 60_000, MAXSTALE = 24 * 3600_000;
    const fresh = new Map(), fam = new Map(), inflight = new Map();
    const famKey = p => {
      try {
        const u = new URL("https://x" + p);
        ["per_page", "page", "sparkline", "price_change_percentage"].forEach(k => u.searchParams.delete(k));
        return u.pathname + "?" + [...u.searchParams].sort((a, b) => (a[0] > b[0] ? 1 : -1)).map(([k, v]) => k + "=" + v).join("&");
      } catch { return p; }
    };
    const pull = path => {
      if (inflight.has(path)) return inflight.get(path);
      const pr = (async () => {
        const r = await fetch(`https://api.coingecko.com/api/v3${path}`, { headers: { "User-Agent": "DispatchMarkets/1.0" }, signal: AbortSignal.timeout(8_000) });
        if (!r.ok) throw new Error(`CoinGecko ${r.status}`);
        const data = await r.json();
        const at = Date.now(), rec = { data, at };
        fresh.set(path, rec); fam.set(famKey(path), rec);
        if (fresh.size > 64) fresh.delete(fresh.keys().next().value);
        if (fam.size > 64) fam.delete(fam.keys().next().value);
        return rec;
      })();
      inflight.set(path, pr);
      pr.then(() => inflight.delete(path), () => inflight.delete(path));
      return pr;
    };
    const hdr = (st, at) => ({ "X-Dispatch-Data-Status": st, "X-Dispatch-Data-As-Of": new Date(at).toISOString() });
    const fallback = (res, path) => {
      const g = fresh.get(path) || fam.get(famKey(path));
      if (g && Date.now() - g.at < MAXSTALE) return json(res, 200, g.data, hdr("stale", g.at));
      return json(res, 200, { unavailable: true }, { "X-Dispatch-Data-Status": "unavailable" });
    };
    const original = coinGecko;
    coinGecko = async function rt29sCoinGecko(req, res, rawPath) {
      const path = normalizeCoinGeckoPath(rawPath);
      if (!path) return original(req, res, rawPath);
      const f = fresh.get(path);
      if (f && Date.now() - f.at < FRESH) {
        if (Date.now() - f.at > SWR) pull(path).catch(() => {});
        return json(res, 200, f.data, hdr("fresh", f.at));
      }
      try {
        if (typeof coinGeckoRateLimiter !== "undefined" && coinGeckoRateLimiter && !coinGeckoRateLimiter.allow(rt33sIp(req))) return rt33sCgMiss(req, res, rawPath, path, original, fresh, fam, famKey, fallback);
      } catch {}
      try { const rec = await pull(path); return json(res, 200, rec.data, hdr("fresh", rec.at)); }
      catch { return rt33sCgMiss(req, res, rawPath, path, original, fresh, fam, famKey, fallback); }
    };
    console.log("[rt29s] coinGecko stale-while-error installed");
  } catch (e) { console.warn("[rt29s] coinGecko override skipped:", e && e.message); }
})();

// rt32s: free fundamentals (SEC EDGAR companyfacts + Yahoo quoteSummary), 12h cache, inflight dedupe, 8s timeouts
const RT32 = { cache: new Map(), inflight: new Map(), cik: null, cikAt: 0, cikP: null, ck: "", crumb: "", crumbAt: 0, crumbP: null };
const RT32_UA = "TheDispatch support@thedispatch.uk";
const RT32_BUA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36";
function rt32Get(u, headers) { return fetch(u, { headers: headers || {}, signal: AbortSignal.timeout(8000), redirect: "follow" }); }
async function rt32CikMap() {
  if (RT32.cik && Date.now() - RT32.cikAt < 7 * 864e5) return RT32.cik;
  if (!RT32.cikP) RT32.cikP = (async () => {
    const r = await rt32Get("https://www.sec.gov/files/company_tickers.json", { "User-Agent": RT32_UA, Accept: "application/json" });
    if (!r.ok) throw new Error("sec tickers " + r.status);
    const j = await r.json(), m = new Map();
    for (const v of Object.values(j)) if (v && v.ticker) m.set(String(v.ticker).toUpperCase(), { cik: String(v.cik_str).padStart(10, "0"), name: v.title });
    RT32.cik = m; RT32.cikAt = Date.now(); return m;
  })().finally(() => { RT32.cikP = null; });
  return RT32.cikP;
}
async function rt32Crumb(force) {
  if (!force && RT32.crumb && Date.now() - RT32.crumbAt < 6 * 3600e3) return RT32.crumb;
  if (!RT32.crumbP) RT32.crumbP = (async () => {
    const r = await rt32Get("https://fc.yahoo.com/", { "User-Agent": RT32_BUA });
    const sc = (typeof r.headers.getSetCookie === "function" ? r.headers.getSetCookie() : [r.headers.get("set-cookie") || ""]).map(c => String(c).split(";")[0]).filter(Boolean).join("; ");
    const c = await rt32Get("https://query2.finance.yahoo.com/v1/test/getcrumb", { "User-Agent": RT32_BUA, Cookie: sc });
    const t = (await c.text()).trim();
    if (!c.ok || !t || t.length > 40 || /[<{\s]/.test(t)) throw new Error("crumb " + c.status);
    RT32.ck = sc; RT32.crumb = t; RT32.crumbAt = Date.now(); return t;
  })().finally(() => { RT32.crumbP = null; });
  return RT32.crumbP;
}
async function rt32Yahoo(sym) {
  const mods = "summaryDetail,defaultKeyStatistics,financialData,earnings,earningsHistory,calendarEvents,institutionOwnership,majorHoldersBreakdown,price";
  for (let i = 0; i < 2; i++) {
    const crumb = await rt32Crumb(i > 0);
    const r = await rt32Get(`https://query2.finance.yahoo.com/v10/finance/quoteSummary/${encodeURIComponent(sym)}?modules=${mods}&crumb=${encodeURIComponent(crumb)}`, { "User-Agent": RT32_BUA, Cookie: RT32.ck });
    if (r.status === 401 || r.status === 403) continue;
    if (!r.ok) throw new Error("yahoo " + r.status);
    const j = await r.json();
    const res = j && j.quoteSummary && j.quoteSummary.result && j.quoteSummary.result[0];
    if (!res) throw new Error("yahoo empty");
    return res;
  }
  throw new Error("yahoo auth");
}
async function rt32Price(sym) {
  try {
    const r = await rt32Get(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?range=1d&interval=1d`, { "User-Agent": RT32_BUA });
    if (!r.ok) return null;
    const m = (await r.json())?.chart?.result?.[0]?.meta;
    return m && m.regularMarketPrice > 0 ? m.regularMarketPrice : null;
  } catch { return null; }
}
const RT32_C = {
  revenue: ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet", "SalesRevenueGoodsNet"],
  grossProfit: ["GrossProfit"], operatingIncome: ["OperatingIncomeLoss"], netIncome: ["NetIncomeLoss", "ProfitLoss"],
  eps: ["EarningsPerShareDiluted", "EarningsPerShareBasic"], cfo: ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
  capex: ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"],
  cash: ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
  debt: ["LongTermDebtNoncurrent", "LongTermDebt"], debtCur: ["LongTermDebtCurrent", "DebtCurrent"], equity: ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
};
function rt32Days(a, b) { return (Date.parse(b) - Date.parse(a)) / 864e5; }
function rt32Units(facts, names) {
  const g = facts && facts["us-gaap"] || {};
  let best = null;
  for (const n of names) {
    const u = g[n] && g[n].units; if (!u) continue;
    const arr = u.USD || u["USD/shares"] || Object.values(u)[0]; if (!arr || !arr.length) continue;
    const last = arr.reduce((m, x) => x.end > m ? x.end : m, "");
    if (!best || last > best.last) best = { arr, last };
  }
  return best ? best.arr : [];
}
function rt32Flow(arr) {
  const by = new Map();
  for (const x of arr) { if (!x.start || !x.end || x.val == null) continue; const k = x.start + "|" + x.end; const o = by.get(k); if (!o || x.filed > o.filed) by.set(k, x); }
  const L = [...by.values()], ann = new Map(), q = new Map();
  for (const x of L) {
    const d = rt32Days(x.start, x.end);
    if (d > 340 && d < 390) ann.set(x.end, x.val);
    if (d > 75 && d < 105) q.set(x.end, x.val);
  }
  for (const x of L) {
    const d = rt32Days(x.start, x.end); if (d < 105 || d > 390) continue;
    let prev = null;
    for (const y of L) if (y.start === x.start && y.end < x.end && (!prev || y.end > prev.end)) prev = y;
    if (prev) { const g = rt32Days(prev.end, x.end); if (g > 75 && g < 105 && !q.has(x.end)) q.set(x.end, x.val - prev.val); }
  }
  return { ann, q };
}
function rt32Inst(arr) { const m = new Map(); for (const x of arr) if (x.end && x.val != null && !x.start) { const o = m.get(x.end); if (!o || x.filed > o.filed) m.set(x.end, x); } return new Map([...m].map(([k, v]) => [k, v.val])); }
function rt32Sec(facts) {
  const F = {}, I = {};
  for (const k of ["revenue", "grossProfit", "operatingIncome", "netIncome", "eps", "cfo", "capex"]) F[k] = rt32Flow(rt32Units(facts, RT32_C[k]));
  for (const k of ["cash", "debt", "debtCur", "equity"]) I[k] = rt32Inst(rt32Units(facts, RT32_C[k]));
  const build = (key, n) => {
    const ends = new Set([...F.revenue[key].keys(), ...F.netIncome[key].keys()]);
    return [...ends].sort().reverse().slice(0, n).map(end => {
      const g = k => F[k][key].has(end) ? F[k][key].get(end) : null, ins = k => I[k].has(end) ? I[k].get(end) : null;
      const cfo = g("cfo"), cx = g("capex");
      const d = ins("debt"), dc = ins("debtCur");
      return { period: key === "ann" ? "FY" + end.slice(0, 4) : end.slice(0, 7), end, revenue: g("revenue"), grossProfit: g("grossProfit"), operatingIncome: g("operatingIncome"), netIncome: g("netIncome"), eps: g("eps"),
        fcf: cfo != null ? cfo - (cx || 0) : null, cash: ins("cash"), debt: d != null || dc != null ? (d || 0) + (dc || 0) : null, equity: ins("equity") };
    });
  };
  const sh = (facts && facts.dei && facts.dei.EntityCommonStockSharesOutstanding && facts.dei.EntityCommonStockSharesOutstanding.units.shares) || [];
  const shares = sh.length ? sh.reduce((m, x) => x.end > m.end ? x : m).val : null;
  return { annual: build("ann", 5), quarterly: build("q", 5), shares };
}
const rt32R = v => v && typeof v === "object" ? (v.raw != null ? v.raw : null) : (typeof v === "number" ? v : null);
async function rt32Build(sym) {
  const now = new Date().toISOString(), out = { symbol: sym, asOf: now, financials: null, valuation: null, earnings: null, institutions: null };
  const ySym = sym.replace(/\./g, "-");
  const [secR, yR] = await Promise.allSettled([
    (async () => {
      const m = await rt32CikMap(); const e = m.get(sym) || m.get(ySym); if (!e) return null;
      const r = await rt32Get(`https://data.sec.gov/api/xbrl/companyfacts/CIK${e.cik}.json`, { "User-Agent": RT32_UA, Accept: "application/json" });
      if (!r.ok) throw new Error("sec facts " + r.status);
      const j = await r.json(); const s = rt32Sec(j.facts); s.name = e.name; return s;
    })(),
    rt32Yahoo(ySym),
  ]);
  const sec = secR.status === "fulfilled" ? secR.value : null, y = yR.status === "fulfilled" ? yR.value : null;
  if (sec && (sec.annual.length || sec.quarterly.length)) out.financials = { source: "SEC EDGAR (XBRL company facts)", asOf: now, name: sec.name, annual: sec.annual, quarterly: sec.quarterly };
  if (y) {
    const sd = y.summaryDetail || {}, ks = y.defaultKeyStatistics || {}, fd = y.financialData || {}, pr = y.price || {};
    const v = { source: "Yahoo Finance", asOf: now, price: rt32R(fd.currentPrice) || rt32R(pr.regularMarketPrice), pe: rt32R(sd.trailingPE), forwardPe: rt32R(sd.forwardPE) || rt32R(ks.forwardPE), ps: rt32R(sd.priceToSalesTrailing12Months),
      pb: rt32R(ks.priceToBook), evEbitda: rt32R(ks.enterpriseToEbitda), marketCap: rt32R(sd.marketCap) || rt32R(pr.marketCap), divYield: rt32R(sd.dividendYield) != null ? rt32R(sd.dividendYield) : rt32R(sd.yield),
      beta: rt32R(sd.beta), profitMargin: rt32R(fd.profitMargins), revenueGrowth: rt32R(fd.revenueGrowth), targetMean: rt32R(fd.targetMeanPrice), recommendation: fd.recommendationKey || null };
    if (Object.entries(v).some(([k, x]) => !["source", "asOf"].includes(k) && x != null)) out.valuation = v;
    const hist = ((y.earningsHistory || {}).history || []).map(h => {
      const a = rt32R(h.epsActual), e = rt32R(h.epsEstimate), sp = rt32R(h.surprisePercent), qd = h.quarter && h.quarter.fmt;
      return { quarter: qd ? `${qd.slice(0, 7)}` : (h.period || ""), date: qd || null, actual: a, estimate: e, surprisePct: sp != null ? Math.round(sp * 1000) / 10 : null, beat: a != null && e != null ? a >= e : null };
    }).filter(h => h.actual != null).reverse();
    const ce = (y.calendarEvents || {}).earnings || {};
    const nd = (ce.earningsDate || [])[0];
    if (hist.length || nd) out.earnings = { source: "Yahoo Finance", asOf: now, history: hist, next: nd ? { date: nd.fmt, estimate: rt32R(ce.earningsAverage), isEstimate: !!ce.isEarningsDateEstimate } : null };
    const io = (y.institutionOwnership || {}).ownershipList || [], mh = y.majorHoldersBreakdown || {};
    const holders = io.map(h => ({ name: h.organization, pct: rt32R(h.pctHeld), shares: rt32R(h.position), value: rt32R(h.value), date: h.reportDate && h.reportDate.fmt, change: rt32R(h.pctChange) })).filter(h => h.name);
    if (holders.length || rt32R(mh.institutionsPercentHeld) != null) out.institutions = { source: "Yahoo Finance (13F filings)", asOf: now, pctHeld: rt32R(mh.institutionsPercentHeld), insidersPct: rt32R(mh.insidersPercentHeld), count: rt32R(mh.institutionsCount), holders };
  }
  if (!out.valuation && sec) {
    const px = await rt32Price(ySym);
    if (px) {
      const q = sec.quarterly, ttm = k => q.length >= 4 && q.slice(0, 4).every(x => x[k] != null) ? q.slice(0, 4).reduce((s, x) => s + x[k], 0) : (sec.annual[0] ? sec.annual[0][k] : null);
      const eps = ttm("eps"), rev = ttm("revenue"), mc = sec.shares ? px * sec.shares : null, eq = (q[0] || sec.annual[0] || {}).equity;
      out.valuation = { source: "Computed: SEC EDGAR + Yahoo price", asOf: now, price: px, pe: eps > 0 ? px / eps : null, forwardPe: null, ps: mc && rev > 0 ? mc / rev : null, pb: mc && eq > 0 ? mc / eq : null, evEbitda: null, marketCap: mc, divYield: null };
    }
  }
  if (!out.earnings && sec && sec.quarterly.some(x => x.eps != null)) out.earnings = { source: "SEC EDGAR (no estimates)", asOf: now, history: sec.quarterly.filter(x => x.eps != null).slice(0, 4).map(x => ({ quarter: x.end.slice(0, 7), date: x.end, actual: x.eps, estimate: null, surprisePct: null, beat: null })), next: null };
  const v = out.valuation || {}, H = out.earnings && out.earnings.history || [];
  // compat with the existing client loaders
  out.metrics = { peRatio: v.pe, forwardPE: v.forwardPe, psRatio: v.ps, pbRatio: v.pb, evEbitda: v.evEbitda, marketCap: v.marketCap, dividendYield: v.divYield };
  out.history = H; out.nextEarnings = out.earnings && out.earnings.next;
  const bt = H.filter(h => h.beat != null); out.beatRate = bt.length ? Math.round(bt.filter(h => h.beat).length / bt.length * 100) : null;
  const sp = H.filter(h => h.surprisePct != null); out.avgSurprise = sp.length ? Math.round(sp.reduce((s, h) => s + h.surprisePct, 0) / sp.length * 10) / 10 : null;
  out.holders = (out.institutions && out.institutions.holders) || [];
  out.sources = { sec: secR.status === "fulfilled" ? (sec ? "ok" : "no CIK") : String(secR.reason && secR.reason.message), yahoo: yR.status === "fulfilled" ? "ok" : String(yR.reason && yR.reason.message) };
  return out;
}
async function rt32Fundamentals(req, res, p, url) {
  const sym = String(url.searchParams.get("symbol") || "").trim().toUpperCase();
  if (!/^[A-Z0-9][A-Z0-9.\-]{0,9}$/.test(sym)) return json(res, 200, { symbol: sym, unavailable: true, reason: "bad symbol", data: [], earnings: [], holders: [], history: [] });
  const hit = RT32.cache.get(sym);
  if (hit && Date.now() - hit.at < 12 * 3600e3) return json(res, 200, hit.data, { "Cache-Control": "public, max-age=600" });
  try {
    if (!RT32.inflight.has(sym)) RT32.inflight.set(sym, rt32Build(sym).finally(() => RT32.inflight.delete(sym)));
    const data = await RT32.inflight.get(sym);
    const any = data.financials || data.valuation || data.earnings || data.institutions;
    if (any) { RT32.cache.set(sym, { at: Date.now(), data }); if (RT32.cache.size > 300) RT32.cache.delete(RT32.cache.keys().next().value); }
    else if (hit) return json(res, 200, hit.data);
    return json(res, 200, any ? data : { ...data, unavailable: true });
  } catch (e) {
    console.warn("[rt32s] fundamentals", sym, e && e.message);
    if (hit) return json(res, 200, hit.data);
    return json(res, 200, { symbol: sym, unavailable: true, reason: "source error", data: [], earnings: [], holders: [], history: [] });
  }
}

// rt33s: per-client Yahoo limiter key + last-good quote cache
function rt33sIp(req) {
  try {
    const xf = String(req.headers["x-forwarded-for"] || "").split(",").map(x => x.trim()).filter(Boolean);
    return xf.length ? xf[xf.length - 1] : (req.socket?.remoteAddress || "unknown");
  } catch { return req.socket?.remoteAddress || "unknown"; }
}
const rt33sYq = new Map();
function rt33sYqStore(q) {
  try {
    if (!q || typeof q !== "object") return;
    const at = Date.now();
    for (const [k, v] of Object.entries(q)) if (v && typeof v.p === "number" && v.p > 0) rt33sYq.set(k, { v, at });
    while (rt33sYq.size > 2000) rt33sYq.delete(rt33sYq.keys().next().value);
  } catch {}
}
function rt33sYqCached(raw) {
  const out = {};
  try {
    for (const k of String(raw).split(",").map(x => x.trim()).filter(Boolean).slice(0, 200)) {
      const e = rt33sYq.get(k);
      if (e && Date.now() - e.at < 15 * 60_000) out[k] = { ...e.v, cached: true };
    }
  } catch {}
  return out;
}
function rt33sCgMiss(req, res, rawPath, path, original, fresh, fam, famKey, fallback) {
  // rt29s only kept in-memory copies; a fresh instance has none, so a 429 became {unavailable}. Prefer any
  // in-memory copy (< 24h), else let the original handler answer from its own persisted last-good copy.
  try { const g = fresh.get(path) || fam.get(famKey(path)); if (g && Date.now() - g.at < 24 * 3600_000) return fallback(res, path); } catch {}
  return rt38sCgAged(req, res, rawPath, path, original, fallback);
}
const RT33S_CRYPTO = new Set(["BTC","ETH","SOL","XRP","DOGE","ADA","AVAX","DOT","LINK","MATIC","POL","LTC","BCH","XLM","ATOM","NEAR","ALGO","HBAR","FIL","APT","SUI","INJ","SHIB","PEPE","UNI","TON","TRX","BNB","ARB","OP","ETC","XMR","ICP","AAVE","MKR"]);
async function rt33sFund(req, res, p, url) {
  const sym = String(url.searchParams.get("symbol") || "").trim().toUpperCase();
  const empty = reason => ({ symbol: sym, unavailable: true, reason, data: [], earnings: [], holders: [], history: [] });
  if (RT33S_CRYPTO.has(sym) || /-USD$/.test(sym)) return json(res, 200, empty("crypto asset: company fundamentals do not apply"));
  if (p === "/api/financials" || typeof rt32Build !== "function" || typeof RT32 === "undefined") return rt32Fundamentals(req, res, p, url);
  if (!/^[A-Z0-9][A-Z0-9.\-]{0,9}$/.test(sym)) return json(res, 200, empty("bad symbol"));
  let data = null; const hit = RT32.cache.get(sym);
  if (hit && Date.now() - hit.at < 12 * 3600e3) data = hit.data;
  else {
    try {
      if (!RT32.inflight.has(sym)) RT32.inflight.set(sym, rt32Build(sym).finally(() => RT32.inflight.delete(sym)));
      data = await RT32.inflight.get(sym);
      if (data.financials || data.valuation || data.earnings || data.institutions) RT32.cache.set(sym, { at: Date.now(), data });
    } catch (e) { data = hit ? hit.data : null; }
  }
  if (!data) return json(res, 200, empty("source error"));
  const base = { symbol: sym, asOf: data.asOf, sources: data.sources };
  if (p === "/api/earnings") return json(res, 200, { ...base, earnings: data.earnings, history: data.history || [], nextEarnings: data.nextEarnings || null, beatRate: data.beatRate, avgSurprise: data.avgSurprise });
  if (p === "/api/holders") return json(res, 200, { ...base, institutions: data.institutions, holders: data.holders || [] });
  return json(res, 200, { ...base, financials: data.financials, data: [] });
}
function rt33sBriefDate(b) {
  try { if (b && typeof b === "object") b.date = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/London" }).format(new Date()); } catch {}
  return b;
}
function rt33sLegal(res, p) {
  const terms = /terms/.test(p);
  const title = terms ? "Terms of Use" : "Privacy Notice";
  const body = terms
    ? "<p>The Dispatch Markets (thedispatch.uk) publishes market research and data for information only. Nothing on this site is investment advice or a recommendation to buy or sell any security. Prices come from free third-party feeds and may be delayed or incomplete.</p><p>Premium costs £15 per month, billed monthly through Stripe. You can cancel at any time from Manage billing; access continues to the end of the paid period.</p><p>You may not scrape, resell or redistribute site content or data. We may change or withdraw features at any time.</p><p>Questions: <a href=\"mailto:support@thedispatch.uk\">support@thedispatch.uk</a></p>"
    : "<p>We collect only what we need to run the service: your email address and account settings when you register, and your subscription status from Stripe if you subscribe. Card details are handled by Stripe and never reach our servers.</p><p>Watchlists, alerts and display settings are stored in your browser; signed-in settings may also be saved to your account. We use essential cookies for sign-in only, and no advertising trackers.</p><p>You can ask us to export or delete your data at any time.</p><p>Contact: <a href=\"mailto:support@thedispatch.uk\">support@thedispatch.uk</a></p>";
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title} | The Dispatch Markets</title><link rel="canonical" href="https://thedispatch.uk${terms ? "/terms" : "/privacy"}"><style>body{margin:0;background:#0d1016;color:#d8dde6;font:16px/1.65 system-ui,-apple-system,Segoe UI,sans-serif}main{max-width:720px;margin:0 auto;padding:40px 20px}h1{font-size:28px;margin:0 0 6px}a{color:#e5b453}.k{font:12px ui-monospace,monospace;letter-spacing:.12em;color:#8a94a6}</style></head><body><main><div class="k">THE DISPATCH MARKETS</div><h1>${title}</h1>${body}<p><a href="/">← Back to The Dispatch</a></p></main></body></html>`;
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "public, max-age=3600" });
  res.end(html);
}

// rt37s: per-ticker Yahoo Finance RSS headlines
const rt37sNewsCache = new Map();
function rt37sDec(t) { return String(t || "").replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1").replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'").replace(/<[^>]+>/g, "").trim(); }
async function rt37sNews(res, url) {
  const sym = String(url.searchParams.get("symbol") || "").trim().toUpperCase();
  if (!/^[A-Z0-9.^=\-]{1,15}$/.test(sym)) return json(res, 400, { error: "bad symbol", items: [] });
  const hit = rt37sNewsCache.get(sym);
  if (hit && Date.now() - hit.at < 15 * 60_000) return json(res, 200, { symbol: sym, items: hit.items, cached: true }, { "Cache-Control": "public, max-age=300" });
  try {
    const r = await fetch(`https://feeds.finance.yahoo.com/rss/2.0/headline?s=${encodeURIComponent(sym)}&region=US&lang=en-US`, { headers: { "User-Agent": "Mozilla/5.0 (TheDispatch support@thedispatch.uk)" }, signal: AbortSignal.timeout(8000) });
    if (!r.ok) throw new Error("rss " + r.status);
    const xml = await r.text();
    const items = [];
    for (const m of xml.matchAll(/<item>([\s\S]*?)<\/item>/g)) {
      const g = tag => { const x = m[1].match(new RegExp(`<${tag}>([\\s\\S]*?)</${tag}>`)); return x ? rt37sDec(x[1]) : ""; };
      const title = g("title"), link = g("link"), ts = Date.parse(g("pubDate")) || 0;
      if (title && /^https?:\/\//.test(link)) items.push({ title: title.slice(0, 300), link, ts, summary: g("description").slice(0, 400), source: "Yahoo Finance" });
      if (items.length >= 20) break;
    }
    rt37sNewsCache.set(sym, { at: Date.now(), items });
    while (rt37sNewsCache.size > 500) rt37sNewsCache.delete(rt37sNewsCache.keys().next().value);
    return json(res, 200, { symbol: sym, items }, { "Cache-Control": "public, max-age=300" });
  } catch (e) {
    return json(res, 200, { symbol: sym, items: hit ? hit.items : [], unavailable: !hit });
  }
}

// rt38s: pass the original handler's persisted CoinGecko copy through only when it is under 24h old
function rt38sCgAged(req, res, rawPath, path, original, fallback) {
  const hdr = {}; let status = 200, done = false; const chunks = [];
  const o = { setHeader: res.setHeader, writeHead: res.writeHead, write: res.write, end: res.end };
  const restore = () => { res.setHeader = o.setHeader; res.writeHead = o.writeHead; res.write = o.write; res.end = o.end; };
  const bail = () => { if (done) return; done = true; restore(); try { fallback(res, path); } catch {} };
  res.setHeader = (k, v) => { hdr[String(k).toLowerCase()] = v; return res; };
  res.writeHead = (st, a, b2) => { status = st; const h = a && typeof a === "object" ? a : (b2 || {}); for (const [k, v] of Object.entries(h)) hdr[k.toLowerCase()] = v; return res; };
  res.write = c => { if (c) chunks.push(Buffer.isBuffer(c) ? c : Buffer.from(String(c))); return true; };
  res.end = c => {
    if (done) return res; done = true;
    if (c) chunks.push(Buffer.isBuffer(c) ? c : Buffer.from(String(c)));
    restore();
    const ao = Date.parse(hdr["x-dispatch-data-as-of"] || "");
    const ok = status === 200 && (ao ? Date.now() - ao < 24 * 3600_000 : String(hdr["x-dispatch-data-status"] || "") === "fresh");
    if (!ok) { try { fallback(res, path); } catch {} return res; }
    res.writeHead(status, hdr); return res.end(Buffer.concat(chunks));
  };
  setTimeout(bail, 12_000).unref?.();
  try { const r = original(req, res, rawPath); if (r && typeof r.catch === "function") r.catch(bail); return r; } catch { bail(); }
}

// rt41s: server-side PEER VALUATIONS for Ask (prepended to the system prompt; context is clipped)
const RT41S_PEERS = {
  MU: ["NVDA", "AVGO", "AMD", "WDC", "INTC"], NVDA: ["AMD", "AVGO", "INTC", "MU", "TSM"], AMD: ["NVDA", "INTC", "AVGO", "MU", "QCOM"],
  AVGO: ["NVDA", "AMD", "QCOM", "MRVL", "MU"], INTC: ["AMD", "NVDA", "TSM", "MU", "QCOM"], TSM: ["NVDA", "INTC", "AMD", "AVGO"], QCOM: ["AVGO", "AMD", "INTC", "NVDA"],
  AAPL: ["MSFT", "GOOGL", "AMZN", "META"], MSFT: ["AAPL", "GOOGL", "AMZN", "ORCL"], GOOGL: ["META", "MSFT", "AMZN", "AAPL"], META: ["GOOGL", "SNAP", "PINS", "MSFT"],
  AMZN: ["WMT", "MSFT", "GOOGL", "COST"], TSLA: ["GM", "F", "RIVN", "TM"], T: ["VZ", "TMUS", "CMCSA"], VZ: ["T", "TMUS", "CMCSA"],
  XOM: ["CVX", "COP", "SHEL", "BP"], CVX: ["XOM", "COP", "SHEL", "BP"], JPM: ["BAC", "WFC", "C", "GS"], BAC: ["JPM", "WFC", "C"], UNH: ["CVS", "CI", "ELV", "HUM"]
};
function rt41sBase(q) {
  const m = q.match(/\[Answer this question as asked, about ([A-Z][A-Z0-9.\-]{0,9})\b/);
  if (m && RT41S_PEERS[m[1]]) return m[1];
  for (const t of (q.match(/\$?\b[A-Z]{1,5}\b(?:'s)?/g) || [])) { const k = t.replace(/^\$|'s$/g, ""); if (RT41S_PEERS[k]) return k; }
  return null;
}
async function rt41sVal(sym) {
  try {
    const hit = RT32.cache.get(sym);
    const data = hit && Date.now() - hit.at < 12 * 3600e3 ? hit.data : await rt32Build(sym);
    return data && data.valuation ? data.valuation : null;
  } catch { return null; }
}
function rt41sMc(v) { if (!(v > 0)) return "n/a"; return v >= 1e12 ? `$${(v / 1e12).toFixed(2)}T` : v >= 1e9 ? `$${(v / 1e9).toFixed(1)}B` : `$${(v / 1e6).toFixed(0)}M`; }
async function rt41sPeerBlock(base) {
  const syms = [base, ...(RT41S_PEERS[base] || [])].slice(0, 6);
  const vals = await Promise.race([Promise.all(syms.map(rt41sVal)), new Promise(r => setTimeout(() => r(null), 3500))]);
  const got = vals ? vals : syms.map(s => { try { const h = RT32.cache.get(s); return h && h.data && h.data.valuation || null; } catch { return null; } });
  const f = x => x == null || !isFinite(x) ? "n/a" : `${Number(x).toFixed(1)}x`;
  const rows = syms.map((s, i) => { const v = got[i]; return v ? `${s}: P/E ${f(v.pe)} · forward P/E ${f(v.forwardPe)} · market cap ${rt41sMc(v.marketCap)}${v.price ? ` · price $${v.price}` : ""}` : null; }).filter(Boolean);
  if (rows.length < 2) return "";
  return `PEER VALUATIONS (live fundamentals, Yahoo Finance / SEC; sector peers of ${base}). When the question is about valuation or peers, quote these exact figures for each company. Do not say a figure is "not specified" when it is listed here, and do not substitute an index or ETF for a peer:\n${rows.join("\n")}`;
}
try {
  const rt41sGen0 = generateAi;
  generateAi = async function (options, ...rest) {
    try {
      if (options && typeof options.system === "string" && options.system.includes('{"reply":"string"') && Array.isArray(options.messages)) {
        const last = [...options.messages].reverse().find(m => m && m.role === "user");
        const q = String((last && last.content) || "");
        if (/peer|valuation|p\/e|\bpe\b|multiples?|compar|versus|\bvs\.?\b|cheap|expensive/i.test(q)) {
          const base = rt41sBase(q);
          if (base) { const blk = await rt41sPeerBlock(base); if (blk) options = { ...options, system: `${blk}\n\n${options.system}` }; }
        }
      }
    } catch {}
    return rt41sGen0.call(this, options, ...rest);
  };
} catch {}

// rt42s: Ask latency guard (memoised peer block + overall deadline on /api/chat generations)
try {
  if (typeof rt41sPeerBlock === "function") {
    const rt42sPb0 = rt41sPeerBlock, rt42sPbMemo = new Map();
    rt41sPeerBlock = async function (base) {
      const hit = rt42sPbMemo.get(base);
      if (hit && Date.now() - hit.at < 10 * 60e3) return hit.v;
      const v = await rt42sPb0(base);
      if (v) rt42sPbMemo.set(base, { at: Date.now(), v });
      return v;
    };
  }
  const rt42sGen0 = generateAi;
  generateAi = async function (options, ...rest) {
    const isChat = options && typeof options.system === "string" && options.system.includes('{"reply":"string"') && Array.isArray(options.messages);
    if (!isChat) return rt42sGen0.call(this, options, ...rest);
    const t0 = Date.now(); let timer;
    try {
      return await Promise.race([
        rt42sGen0.call(this, options, ...rest),
        new Promise((_, rej) => { timer = setTimeout(() => rej(new AiRequestError(504, "The research assistant took too long to answer. Please try again.", "TIMEOUT")), 55000); }),
      ]);
    } finally { clearTimeout(timer); console.warn("rt42s chat ms", Date.now() - t0); }
  };
} catch (e) { console.warn("rt42s latency guard skipped"); }

// rt43s: pricing, shared energy spot, honest reference/last-good marking, synthetic DXY from live FX
const RT43S_FREE = ["Live and delayed market prices with charts", "Markets, crypto, newsroom and heatmaps", "Regime model and the free desk brief", "Market Lab, Desk Run and the Letter", "Watchlists and price alerts"];
const RT43S_PREM = ["Everything in Free", "Weekly Gold Playbook", "AI Dispatch Brief", "Ask research assistant and AI lenses", "Company statements and institutional holders", "Custom screener and document intelligence", "Cancel any time (Settings → Manage billing)"];
async function rt43sPricing(req, res) {
  let user = null; try { user = await currentUser(req); } catch {}
  const admin = (() => { try { return isAdminUser(user); } catch { return false; } })();
  const prem = !!user && (user.tier === "premium" || admin);
  const li = a => a.map(x => `<li>${x}</li>`).join("");
  const cta = prem
    ? `<p class="muted">${admin ? "Admin · Premium included." : "Premium active."} ${!admin ? `Manage billing from <a href="/settings/">Settings</a>.` : "There is no Stripe subscription on an admin account."}</p>`
    : `${user ? "" : `<a href="/__auth/register">Create free account</a> · `}<a href="/__auth/subscribe">Get Premium · £15/month</a>`;
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" });
  if (req.method === "HEAD") return res.end();
  return res.end(`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Pricing · The Dispatch</title>
<meta name="description" content="The Dispatch Markets: Free and Premium (£15/month) plans.">
<style>body{margin:0;background:#0b1018;color:#e8edf3;font:16px/1.5 system-ui}main{max-width:860px;margin:0 auto;padding:32px 20px}
h1{font-size:28px;margin:0 0 6px}.g{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:22px 0}@media(max-width:640px){.g{grid-template-columns:1fr}}
.c{background:#111a26;border:1px solid #293849;border-radius:14px;padding:22px}.c.p{border-color:#c9a227}h2{margin:0 0 4px;font-size:20px}.pr{font-size:26px;font-weight:800;margin:6px 0 10px}
ul{padding-left:18px;margin:0}li{margin:6px 0}a{color:#e7c35a}.muted{color:#93a1b3;font-size:14px}</style></head><body><main>
<a href="/">← The Dispatch</a><h1>Pricing</h1><p class="muted">One plan upgrade, no token mark-up. Prices in GBP, billed monthly through Stripe.</p>
<div class="g"><section class="c"><h2>Free</h2><div class="pr">£0</div><ul>${li(RT43S_FREE)}</ul></section>
<section class="c p"><h2>Premium</h2><div class="pr">£15/month</div><ul>${li(RT43S_PREM)}</ul></section></div>
<p>${cta}</p><p class="muted">Research and data for information only; not investment advice. See the <a href="/terms">Terms</a> and <a href="/privacy">Privacy notice</a>.</p>
</main></body></html>`);
}
const RT43S_EN = { at: 0, data: null, day: "", used: 0, inflight: null };
async function rt43sEnergyFetch() {
  const key = process.env.TWELVE_DATA_API_KEY;
  if (!key) return null;
  const r = await fetch(`https://api.twelvedata.com/quote?symbol=${encodeURIComponent("WTI/USD,XBR/USD")}&apikey=${encodeURIComponent(key)}`, { signal: AbortSignal.timeout(8000), headers: { accept: "application/json" } });
  if (!r.ok) throw new Error("twelve " + r.status);
  const j = await r.json();
  const one = (q, name) => { const p = Number(q && q.close), prev = Number(q && q.previous_close), ts = Number(q && (q.last_quote_at || q.timestamp));
    return p > 0 ? { p, prev: prev > 0 ? prev : null, c: prev > 0 ? ((p - prev) / prev) * 100 : null, ts: ts > 0 ? ts : Math.floor(Date.now() / 1000), name, source: "twelve-spot", proxy: true } : null; };
  return { WTI: one(j["WTI/USD"], "WTI crude spot"), BRENT: one(j["XBR/USD"], "Brent crude spot") };
}
async function rt43sEnergy(res) {
  const now = Date.now(), day = new Date().toISOString().slice(0, 10);
  if (RT43S_EN.day !== day) { RT43S_EN.day = day; RT43S_EN.used = 0; }
  const budget = Math.max(0, Number(process.env.RT43_TD_ENERGY_DAILY || 300));
  const left = budget - RT43S_EN.used;
  const msLeft = Date.parse(day + "T24:00:00Z") - now;
  const interval = left >= 2 ? Math.max(60_000, Math.floor(msLeft / (left / 2))) : Infinity;
  if (!process.env.TWELVE_DATA_API_KEY) return json(res, 200, { available: false, reason: "no-key" }, { "Cache-Control": "no-store" });
  if ((!RT43S_EN.data || now - RT43S_EN.at >= interval) && !RT43S_EN.inflight && left >= 2) {
    RT43S_EN.inflight = rt43sEnergyFetch().then(d => { RT43S_EN.used += 2; if (d && (d.WTI || d.BRENT)) { RT43S_EN.data = d; RT43S_EN.at = Date.now(); } }).catch(() => { RT43S_EN.used += 2; }).finally(() => { RT43S_EN.inflight = null; });
    await Promise.race([RT43S_EN.inflight, new Promise(r => setTimeout(r, 6000))]);
  }
  const d = RT43S_EN.data;
  if (!d) return json(res, 200, { available: false, reason: left < 2 ? "budget" : "unavailable" }, { "Cache-Control": "no-store" });
  const ageSec = Math.round((Date.now() - RT43S_EN.at) / 1000);
  const stale = ageSec > Math.max(180, (isFinite(interval) ? interval / 1000 : 0) * 3);
  return json(res, 200, { available: true, WTI: d.WTI && { ...d.WTI, stale }, BRENT: d.BRENT && { ...d.BRENT, stale }, fetchedAt: RT43S_EN.at, ageSec, refreshSec: isFinite(interval) ? Math.round(interval / 1000) : null }, { "Cache-Control": "public, max-age=30" });
}
const rt43sAge = ts => { const t = Number(ts); return t > 0 ? Math.max(0, Math.round(Date.now() / 1000 - (t > 1e10 ? t / 1000 : t))) : null; };
try {
  if (typeof fetchGoldProxy === "function") {
    const g = { at: 0, q: null };
    fetchGoldProxy = async function () {
      if (g.q && Date.now() - g.at < 30_000) return { ...g.q, cached: true };
      try {
        const r = await fetch("https://api.gold-api.com/price/XAU", { signal: AbortSignal.timeout(6000), headers: { accept: "application/json" } });
        if (!r.ok) throw new Error("gold " + r.status);
        const d = await r.json(); const price = Number(d && d.price), ts = Date.parse((d && d.updatedAt) || "");
        if (!(price > 0)) throw new Error("gold invalid");
        const q = { p: price, c: 0, prev: price, change: 0, currency: "USD", exchange: "FREE REFERENCE", name: "Spot Gold (proxy)", ts: Number.isFinite(ts) ? Math.floor(ts / 1000) : Math.floor(Date.now() / 1000), source: "gold-api-spot-proxy", proxy: true };
        g.q = q; g.at = Date.now(); try { rememberReferenceQuote("spot-gold-proxy", q); } catch {}
        return q;
      } catch {
        let lg = g.q; try { lg = lg || lastGoodReferenceQuote("spot-gold-proxy"); } catch {}
        return lg ? { ...lg, cached: true, stale: true, staleAgeSec: rt43sAge(lg.ts) } : null;
      }
    };
  }
  if (typeof fetchSyntheticDxy === "function" && typeof fetchYahooQuote === "function") {
    const W = [["EURUSD=X", -0.576, true], ["JPY=X", 0.136, false], ["GBPUSD=X", -0.119, true], ["CAD=X", 0.091, false], ["SEK=X", 0.042, false], ["CHF=X", 0.036, false]];
    const d = { at: 0, q: null };
    fetchSyntheticDxy = async function () {
      if (d.q && Date.now() - d.at < 30_000) return { ...d.q, cached: true };
      try {
        const qs = await Promise.all(W.map(([s]) => fetchYahooQuote(s).catch(() => null)));
        if (qs.some(q => !q || !(q.p > 0) || /last-good/.test(String(q.source || "")))) throw new Error("fx incomplete");
        const idx = k => 50.14348112 * W.reduce((m, [, e], i) => m * (qs[i][k] ** e), 1);
        const p = idx("p"); const prevOk = qs.every(q => q.prev > 0); const prev = prevOk ? 50.14348112 * W.reduce((m, [, e], i) => m * (qs[i].prev ** e), 1) : null;
        const ts = Math.min(...qs.map(q => Number(q.ts) > 1e10 ? Number(q.ts) / 1000 : Number(q.ts) || Date.now() / 1000));
        const q = { p: Number(p.toFixed(3)), prev: prev ? Number(prev.toFixed(3)) : null, c: prev ? ((p - prev) / prev) * 100 : null, change: prev ? p - prev : null, currency: "USD", exchange: "SYNTHETIC", name: "US Dollar Index (computed from live FX)", ts: Math.floor(ts), source: "dxy-fx-computed", proxy: true };
        d.q = q; d.at = Date.now(); try { rememberReferenceQuote("synthetic-dxy-proxy", q); } catch {}
        return q;
      } catch {
        return d.q ? { ...d.q, cached: true, stale: true, staleAgeSec: rt43sAge(d.q.ts) } : null;
      }
    };
  }
  const rt43sMark = out => { try { for (const k of Object.keys(out || {})) { const q = out[k]; if (q && typeof q === "object" && (q.cached || /last-good/.test(String(q.source || ""))) && /last-good/.test(String(q.source || "")) ) { q.stale = true; q.staleAgeSec = rt43sAge(q.ts); } } } catch {} return out; };
  if (typeof yahooQuote === "function") { const yq0 = yahooQuote; yahooQuote = async function (...a) { return rt43sMark(await yq0.apply(this, a)); }; }
  if (typeof rt33sYqCached === "function") { const yc0 = rt33sYqCached; rt33sYqCached = function (...a) { const out = yc0.apply(this, a); try { for (const k of Object.keys(out || {})) { const q = out[k]; if (q && typeof q === "object") { q.stale = true; q.cached = true; q.staleAgeSec = rt43sAge(q.ts); } } } catch {} return out; }; }
  if (typeof rt41sPeerBlock === "function") { const pb0 = rt41sPeerBlock; rt41sPeerBlock = async function (...a) { const v = await pb0.apply(this, a); return v ? v + "\nCompare like with like: trailing P/E with trailing P/E, forward P/E with forward P/E. Never compare one company's trailing P/E with another company's forward P/E; if a figure is n/a, say so for that company only." : v; }; }
} catch (e) { console.warn("rt43s monkeypatch skipped"); }

// rt43b: Twelve Data energy diagnostics (non-secret reason codes)
try { if (typeof rt43sEnergyFetch === "function" && typeof rt43sEnergy === "function" && typeof RT43S_EN === "object") {
  RT43S_EN.err = null;
  const rt43bClean = (m, key) => String(m || "").split(key || "\u0000").join("***").replace(/apikey=[^&\s]+/gi, "apikey=***").replace(/[^\w .,:/'()-]/g, "").slice(0, 140);
  rt43sEnergyFetch = async function () {
    const key = String(process.env.TWELVE_DATA_API_KEY || "").trim();
    if (!key) { RT43S_EN.err = "no-key"; return null; }
    let r, j;
    try { r = await fetch(`https://api.twelvedata.com/quote?symbol=${encodeURIComponent("WTI/USD,XBR/USD")}&apikey=${encodeURIComponent(key)}`, { signal: AbortSignal.timeout(8000), headers: { accept: "application/json" } }); }
    catch (e) { RT43S_EN.err = "td-network-" + (e && e.name === "TimeoutError" ? "timeout" : "error"); return null; }
    if (!r.ok) { RT43S_EN.err = "td-http-" + r.status; return null; }
    try { j = await r.json(); } catch (e) { RT43S_EN.err = "td-bad-json"; return null; }
    if (j && j.status === "error") { RT43S_EN.err = `td-${j.code || "error"}: ${rt43bClean(j.message, key)}`; return null; }
    const errs = [];
    const one = (sym, name) => { const q = j && j[sym];
      if (!q) { errs.push(sym + " missing"); return null; }
      if (q.status === "error") { errs.push(`${sym} td-${q.code || "error"}: ${rt43bClean(q.message, key)}`); return null; }
      const p = Number(q.close), prev = Number(q.previous_close), ts = Number(q.last_quote_at || q.timestamp);
      if (!(p > 0)) { errs.push(sym + " no-price"); return null; }
      return { p, prev: prev > 0 ? prev : null, c: prev > 0 ? ((p - prev) / prev) * 100 : null, ts: ts > 0 ? ts : Math.floor(Date.now() / 1000), name, source: "twelve-spot", proxy: true }; };
    const out = { WTI: one("WTI/USD", "WTI crude spot"), BRENT: one("XBR/USD", "Brent crude spot") };
    RT43S_EN.err = errs.length ? errs.join(" | ") : null;
    return out;
  };
  rt43sEnergy = async function (res) {
    const now = Date.now(), day = new Date().toISOString().slice(0, 10);
    if (RT43S_EN.day !== day) { RT43S_EN.day = day; RT43S_EN.used = 0; }
    const budget = Math.max(0, Number(process.env.RT43_TD_ENERGY_DAILY || 300));
    const left = budget - RT43S_EN.used;
    const msLeft = Date.parse(day + "T24:00:00Z") - now;
    const interval = left >= 2 ? Math.max(60_000, Math.floor(msLeft / (left / 2))) : Infinity;
    if (!String(process.env.TWELVE_DATA_API_KEY || "").trim()) return json(res, 200, { available: false, reason: "no-key" }, { "Cache-Control": "no-store" });
    // after a failure, retry no faster than every 2 min so errors don't burn the shared 8/min, 800/day free limits
    const due = RT43S_EN.data ? now - RT43S_EN.at >= interval : now - (RT43S_EN.failAt || 0) >= 120_000;
    if (due && !RT43S_EN.inflight && left >= 2) {
      RT43S_EN.inflight = rt43sEnergyFetch().then(d => { RT43S_EN.used += 2; if (d && (d.WTI || d.BRENT)) { RT43S_EN.data = d; RT43S_EN.at = Date.now(); } else RT43S_EN.failAt = Date.now(); })
        .catch(e => { RT43S_EN.used += 2; RT43S_EN.failAt = Date.now(); RT43S_EN.err = "td-exception"; }).finally(() => { RT43S_EN.inflight = null; });
      await Promise.race([RT43S_EN.inflight, new Promise(r => setTimeout(r, 6000))]);
    }
    const d = RT43S_EN.data;
    if (!d) return json(res, 200, { available: false, reason: left < 2 ? "budget" : RT43S_EN.inflight ? "pending" : (RT43S_EN.err || "unavailable"), retryInSec: Math.max(0, Math.round((120_000 - (Date.now() - (RT43S_EN.failAt || 0))) / 1000)) }, { "Cache-Control": "no-store" });
    const ageSec = Math.round((Date.now() - RT43S_EN.at) / 1000);
    const stale = ageSec > Math.max(180, (isFinite(interval) ? interval / 1000 : 0) * 3);
    return json(res, 200, { available: true, WTI: d.WTI && { ...d.WTI, stale }, BRENT: d.BRENT && { ...d.BRENT, stale }, fetchedAt: RT43S_EN.at, ageSec, refreshSec: isFinite(interval) ? Math.round(interval / 1000) : null, ...(RT43S_EN.err ? { partial: RT43S_EN.err } : {}) }, { "Cache-Control": "public, max-age=30" });
  };
} } catch (e) { console.warn("rt43b skipped:", e && e.message); }

// rt43b: US pre-market / after-hours prints (Yahoo v7 quote with the rt32 crumb), 60 s shared cache
const RT43B_EXT = new Map(); let RT43B_EXT_P = null;
async function rt43bExtFetch(syms) {
  for (let i = 0; i < 2; i++) {
    const crumb = await rt32Crumb(i > 0);
    const r = await rt32Get(`https://query2.finance.yahoo.com/v7/finance/quote?symbols=${encodeURIComponent(syms.join(","))}&fields=preMarketPrice,preMarketTime,postMarketPrice,postMarketTime,marketState,regularMarketPrice&crumb=${encodeURIComponent(crumb)}`, { "User-Agent": RT32_BUA, Cookie: RT32.ck });
    if (r.status === 401 || r.status === 403) continue;
    if (!r.ok) throw new Error("yahoo " + r.status);
    const j = await r.json(), now = Date.now();
    const rows = (j && j.quoteResponse && j.quoteResponse.result) || [];
    if (RT43B_EXT.size > 3000) RT43B_EXT.clear();
    syms.forEach(s => RT43B_EXT.set(s, { at: now, v: null }));
    rows.forEach(q => { if (!q || !q.symbol) return; RT43B_EXT.set(String(q.symbol).toUpperCase(), { at: now, v: { state: String(q.marketState || ""), pre: Number(q.preMarketPrice) || null, preTs: Number(q.preMarketTime) || null, post: Number(q.postMarketPrice) || null, postTs: Number(q.postMarketTime) || null, reg: Number(q.regularMarketPrice) || null } }); });
    return;
  }
  throw new Error("yahoo auth");
}
async function rt43bExt(req, res) {
  let syms = [];
  try { syms = [...new Set(String(new URL(req.url, "http://localhost").searchParams.get("symbols") || "").toUpperCase().split(",").map(s => s.trim()).filter(s => /^[A-Z][A-Z.\-]{0,6}$/.test(s)))].slice(0, 60); } catch {}
  if (!syms.length) return json(res, 400, { available: false, reason: "symbols" }, { "Cache-Control": "no-store" });
  if (typeof rt32Crumb !== "function" || typeof rt32Get !== "function") return json(res, 200, { available: false, reason: "no-crumb" }, { "Cache-Control": "no-store" });
  const need = syms.filter(s => { const c = RT43B_EXT.get(s); return !c || Date.now() - c.at > 60_000; });
  let reason = null;
  if (need.length) {
    try { if (!RT43B_EXT_P) RT43B_EXT_P = rt43bExtFetch(need).finally(() => { RT43B_EXT_P = null; }); await RT43B_EXT_P; }
    catch (e) { reason = "yahoo-" + String(e && e.message || "error").replace(/[^\w -]/g, "").slice(0, 40); }
  }
  const quotes = {}; syms.forEach(s => { const c = RT43B_EXT.get(s); if (c && c.v) quotes[s] = c.v; });
  return json(res, 200, { available: Object.keys(quotes).length > 0, quotes, ...(reason ? { reason } : {}) }, { "Cache-Control": "public, max-age=30" });
}

// rt43d: Twelve Data energy spot is not on the free plan (td-403 for WTI/USD and XBR/USD): no energy calls at all
// unless RT43D_TD_ENERGY=1, and the core basket exactly as before rt43c (basket restored; no energy credit claims)
try {
  if (typeof RT43C === "object" && RT43C && Array.isArray(RT43C.dropped) && RT43C.dropped.length && typeof twelveDataAllowedSymbols !== "undefined" && !Object.isFrozen(twelveDataAllowedSymbols)) {
    for (const s of RT43C.dropped) if (!twelveDataAllowedSymbols.includes(s)) twelveDataAllowedSymbols.push(s);
    console.log("rt43d: core basket restored to", twelveDataAllowedSymbols.length, "symbols");
    RT43C.dropped = []; RT43C.trimmed = false;
  }
} catch (e) { console.warn("rt43d basket restore skipped:", e && e.message); }
try { if (typeof rt43sEnergy === "function") {
  const _en0 = rt43sEnergy;
  rt43sEnergy = async function (res) {
    if (String(process.env.RT43D_TD_ENERGY || "") === "1") return _en0.apply(this, arguments);
    return json(res, 200, { available: false, reason: "not-on-plan", detail: "WTI and Brent spot are not on the free Twelve Data plan; the 10-minute-delayed NYMEX/ICE futures are shown instead." }, { "Cache-Control": "public, max-age=3600" });
  };
} } catch (e) { console.warn("rt43d energy gate skipped:", e && e.message); }

// rt44: official EIA daily spot reference for WTI (RWTC) and Brent (RBRTE); free sources only, cached ~6 h
// order: EIA API v2 (only if EIA_API_KEY is set; free key) -> EIA public spot table page -> FRED CSV (EIA series)
const RT44_EIA = { at: 0, tryAt: 0, v: null, src: "", reason: "", p: null };
function rt44Row(p, prev, date, series) { p = Number(p); prev = Number(prev); return p > 0 && /^\d{4}-\d{2}-\d{2}$/.test(date) ? { p: Math.round(p * 100) / 100, prev: prev > 0 ? Math.round(prev * 100) / 100 : null, date, series } : null; }
async function rt44Get(url) { const r = await fetch(url, { headers: { "User-Agent": "Mozilla/5.0 (thedispatch.uk reference fetch)", Accept: "*/*" }, signal: AbortSignal.timeout(12000) }); if (!r.ok) throw new Error("http " + r.status); return r.text(); }
async function rt44FromApi() {
  const k = process.env.EIA_API_KEY; if (!k) throw new Error("no-key");
  const out = {};
  for (const [tk, s] of [["WTI", "RWTC"], ["BRENT", "RBRTE"]]) {
    const t = await rt44Get(`https://api.eia.gov/v2/petroleum/pri/spt/data/?api_key=${encodeURIComponent(k)}&frequency=daily&data[0]=value&facets[series][]=${s}&sort[0][column]=period&sort[0][direction]=desc&length=2`);
    const d = (JSON.parse(t).response || {}).data || []; const row = d[0] && rt44Row(d[0].value, d[1] && d[1].value, String(d[0].period), s); if (row) out[tk] = row;
  }
  return out;
}
async function rt44FromPage() {
  const h = await rt44Get("https://www.eia.gov/dnav/pet/pet_pri_spt_s1_d.htm");
  const dates = [...h.matchAll(/class="Series5"[^>]*>\s*(\d{2})\/(\d{2})\/(\d{2})\s*</g)].map(m => `20${m[3]}-${m[1]}-${m[2]}`);
  const out = {};
  for (const [tk, s] of [["WTI", "RWTC"], ["BRENT", "RBRTE"]]) {
    const i = h.indexOf("s=" + s + "&"); if (i < 0) continue;
    const seg = h.slice(Math.max(0, h.lastIndexOf('class="DataRow"', i)), i);
    const vals = [...seg.matchAll(/<td[^>]*class="(?:DataB|Current2)"[^>]*>\s*([\d.,]*)\s*</g)].map(m => m[1].replace(/,/g, ""));
    if (!dates.length || vals.length !== dates.length) continue;
    let j = vals.length - 1; while (j >= 0 && !(Number(vals[j]) > 0)) j--;
    let k = j - 1; while (k >= 0 && !(Number(vals[k]) > 0)) k--;
    const row = j >= 0 && rt44Row(vals[j], k >= 0 ? vals[k] : null, dates[j], s); if (row) out[tk] = row;
  }
  return out;
}
async function rt44FromFred() {
  const out = {}, from = new Date(Date.now() - 30 * 864e5).toISOString().slice(0, 10);
  for (const [tk, id, s] of [["WTI", "DCOILWTICO", "RWTC"], ["BRENT", "DCOILBRENTEU", "RBRTE"]]) {
    const rows = (await rt44Get(`https://fred.stlouisfed.org/graph/fredgraph.csv?id=${id}&cosd=${from}`)).trim().split(/\r?\n/).slice(1).map(l => l.split(",")).filter(r => Number(r[1]) > 0);
    const a = rows[rows.length - 1], b = rows[rows.length - 2]; const row = a && rt44Row(a[1], b && b[1], a[0], s); if (row) out[tk] = row;
  }
  return out;
}
async function rt44Refresh() {
  const errs = [];
  for (const [name, fn] of [["eia-api", rt44FromApi], ["eia", rt44FromPage], ["fred", rt44FromFred]]) {
    try { const v = await fn(); if (v.WTI || v.BRENT) { RT44_EIA.v = v; RT44_EIA.src = name; RT44_EIA.at = Date.now(); RT44_EIA.reason = ""; return; } errs.push(name + "-empty"); }
    catch (e) { errs.push(name + "-" + String(e && e.message || "error").replace(/[^\w -]/g, "").slice(0, 30)); }
  }
  RT44_EIA.reason = errs.join(",");
}
async function rt44Eia(res) {
  const now = Date.now();
  if ((!RT44_EIA.v || now - RT44_EIA.at > 6 * 3600e3) && now - RT44_EIA.tryAt > 15 * 60e3) {
    RT44_EIA.tryAt = now;
    if (!RT44_EIA.p) RT44_EIA.p = rt44Refresh().finally(() => { RT44_EIA.p = null; });
  }
  if (RT44_EIA.p && !RT44_EIA.v) { try { await RT44_EIA.p; } catch {} }
  const v = RT44_EIA.v;
  if (!v) return json(res, 200, { available: false, reason: RT44_EIA.reason || "pending" }, { "Cache-Control": "no-store" });
  return json(res, 200, { available: true, source: RT44_EIA.src === "fred" ? "EIA via FRED" : "EIA", ...v, fetchedAt: new Date(RT44_EIA.at).toISOString(), ageSec: Math.round((now - RT44_EIA.at) / 1000) }, { "Cache-Control": "public, max-age=900" });
}
