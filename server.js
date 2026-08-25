const http = require("http");
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
const { moderateInput, moderateOutput } = require("./moderation");
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
  .muted{font-size:12px;color:#718096}</style></head><body><main>${content}</main></body></html>`);
}
async function readBody(req, maxBytes = 2 * 1024 * 1024) {
  let text = "";
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > maxBytes) throw new AiRequestError(413, "Request body is too large.", "BODY_TOO_LARGE");
    text += chunk;
  }
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
function safeText(value, max) {
  return clipped(value, max).replace(/[&<>"']/g, char => ({
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
// Collect the free-form, user-authored text an AI endpoint received, so it can be
// screened before reaching the AI provider. Machine-generated fields (terminal
// context, market snapshots) are intentionally excluded.
function userSubmittedText(pathname, body) {
  const parts = [];
  if (pathname === "/api/chat" || pathname === "/api/committee") {
    // Screen only the newest user turn. The client resends prior turns for
    // context, and each was already moderated when it was first submitted;
    // rescanning the whole history would let one earlier flagged message wrongly
    // block every later message in the conversation.
    const userMessages = asAiMessages(body?.messages, 16).filter(message => message.role === "user");
    if (userMessages.length) parts.push(userMessages[userMessages.length - 1].content);
    if (typeof body?.system === "string") parts.push(body.system);
  }
  if (pathname === "/api/lenses") {
    if (typeof body?.userThesis === "string") parts.push(body.userThesis);
  }
  return parts;
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
  await updateUserMembership({ customerId: String(customerId || subscription.customer), subscription });
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
  if (p === "/__auth/reset" && req.method === "GET") return page(res, "Reset password", `<h1>RESET PASSWORD</h1><form method="post"><input type="hidden" name="token" value="${safeText(url.searchParams.get("token"), 256)}"><label>New password</label><input name="password" type="password" minlength="8" required><button>Set password</button></form>`);
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
    if (user) return page(res, "Premium · The Dispatch", `<h1>PREMIUM ACCESS</h1><p>Continue to Stripe Checkout to unlock AI briefs, lenses, portfolio analysis, and Dispatch Expert.</p><form method="post"><button>Continue to secure checkout</button></form><p class="muted">£15/month · Cancel anytime in the Stripe billing portal.</p>`);
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
  if (["/api/financials", "/api/earnings", "/api/statements", "/api/holders"].includes(p)) return json(res, 200, { symbol: url.searchParams.get("symbol"), data: [], earnings: [], holders: [] });
  if (["/api/brief", "/api/intelligence", "/api/lenses", "/api/committee", "/api/chat", "/api/gold-desk"].includes(p)) {
    const user = await currentUser(req);
    if (!user || user.tier !== "premium") return json(res, 401, { error: "Premium membership required" });
    try {
      const body = req.method === "POST" ? await readBody(req) : {};
      // Auto-moderate inbound user text before it reaches the AI provider.
      const submitted = userSubmittedText(p, body);
      if (submitted.length) {
        const verdict = moderateInput(submitted);
        if (!verdict.allowed) {
          console.warn("Moderation blocked user input:", verdict.categories.join(", ") || "policy");
          return json(res, 400, {
            error: verdict.message,
            code: "MODERATION_BLOCKED",
            moderation: { blocked: true, categories: verdict.categories },
          });
        }
      }
      if (p === "/api/chat") {
        const context = clipped(JSON.stringify(body.context || {}), 12000);
        const result = await generateAi({
          system: `${MARKET_SYSTEM}\nAnswer the user's market question using the terminal context below. Use short paragraphs and bullets where useful.\nTERMINAL CONTEXT:\n${context}`,
          messages: asAiMessages(body.messages, 12),
          maxTokens: 1200,
          temperature: 0.25,
        });
        return json(res, 200, { reply: safeText(moderateOutput(result.text).text, 9000), meta: { provider: "xAI", model: result.model } });
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
        const moderatedText = moderateOutput(result.text).text;
        let content = safeText(moderatedText, 12000);
        try { content = JSON.stringify(safeGeneratedValue(jsonFromText(moderatedText))); } catch {}
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