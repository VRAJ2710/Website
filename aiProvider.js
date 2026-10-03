"use strict";

// Ask/Expert calls xAI. Replit must set this secret; do not commit a key.
// Optional: XAI_MODEL (default grok-4), XAI_BASE_URL (default https://api.x.ai/v1).
const XAI_API_KEY_ENV = "XAI_API_KEY";
const DEFAULT_XAI_MODEL = "grok-4";
const DEFAULT_XAI_BASE_URL = "https://api.x.ai/v1";

const MISSING_KEY_MESSAGE = "AI is not configured. In Replit Secrets, set XAI_API_KEY to an xAI API key from console.x.ai. Ask/Expert cannot publish an answer until that secret is set.";

class AiRequestError extends Error {
  constructor(status, message, code) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

function xaiApiKey() {
  return String(process.env.XAI_API_KEY || "").trim();
}

function xaiModel() {
  return String(process.env.XAI_MODEL || DEFAULT_XAI_MODEL).trim() || DEFAULT_XAI_MODEL;
}

function xaiBaseUrl() {
  const configured = String(process.env.XAI_BASE_URL || "").trim();
  if (!configured) return DEFAULT_XAI_BASE_URL;
  let parsed;
  try { parsed = new URL(configured); } catch {
    throw new AiRequestError(503, "XAI_BASE_URL is not a valid https URL.", "PROVIDER_CONFIG");
  }
  if (parsed.protocol !== "https:") {
    throw new AiRequestError(503, "XAI_BASE_URL must use https.", "PROVIDER_CONFIG");
  }
  return configured.replace(/\/$/, "");
}

function guestUser() {
  return { guest: true, tier: "free", billingPortal: false, isAdmin: false };
}

function publicUser(user) {
  if (!user || typeof user !== "object" || Array.isArray(user) || !user.id) return guestUser();
  const { passwordHash, password_hash, ...safeUser } = user;
  return {
    ...safeUser,
    guest: false,
    isAdmin: user.isAdmin === true || user.is_admin === true,
  };
}

function sessionTokens(cookieHeader) {
  const raw = Array.isArray(cookieHeader) ? cookieHeader.join("; ") : String(cookieHeader || "");
  const prefix = "dispatch_session=";
  const values = [];
  for (const part of raw.split(";")) {
    const trimmed = part.trim();
    if (!trimmed.startsWith(prefix)) continue;
    const encoded = trimmed.slice(prefix.length);
    if (!encoded) continue;
    try { values.push(decodeURIComponent(encoded)); }
    catch { values.push(encoded); }
    if (values.length >= 8) break;
  }
  return values;
}

async function resolvePublicUser(cookieHeader, lookup) {
  try {
    const tokens = sessionTokens(cookieHeader);
    if (!tokens.length) return guestUser();
    const user = typeof lookup === "function" ? await lookup(tokens) : null;
    return publicUser(user);
  } catch (error) {
    const message = error && error.message ? error.message : error;
    console.error("GET /api/me failed closed to guest:", message);
    return guestUser();
  }
}

function clipText(value, max) {
  return String(value || "").trim().slice(0, max);
}

function completionMessages(system, messages) {
  const history = Array.isArray(messages) ? messages : [];
  const clipped = history.slice(-16).map(message => ({
    role: message && message.role === "assistant" ? "assistant" : "user",
    content: clipText(message && message.content, 6000),
  })).filter(message => message.content);
  return [{ role: "system", content: clipText(system, 5000) }, ...clipped];
}

function completionText(data) {
  const content = data && data.choices && data.choices[0] && data.choices[0].message
    ? data.choices[0].message.content
    : "";
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content.map(part => {
      if (typeof part === "string") return part;
      return part && typeof part.text === "string" ? part.text : "";
    }).join("");
  }
  return "";
}

async function completeWithXaiKey({
  apiKey,
  model,
  baseUrl,
  system,
  messages,
  maxTokens = 1000,
  temperature = 0.2,
  timeoutMs = 25000,
  fetchImpl = fetch,
}) {
  const key = String(apiKey || "").trim();
  if (!key) throw new AiRequestError(503, MISSING_KEY_MESSAGE, "AI_KEY_MISSING");
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetchImpl(`${String(baseUrl || DEFAULT_XAI_BASE_URL).replace(/\/$/, "")}/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${key}`,
      },
      body: JSON.stringify({
        model: model || DEFAULT_XAI_MODEL,
        messages: completionMessages(system, messages),
        max_tokens: Math.max(300, Math.min(Number(maxTokens) || 1000, 2400)),
        temperature,
      }),
      signal: controller.signal,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      if (response.status === 401) {
        throw new AiRequestError(503, "The XAI_API_KEY secret was rejected by xAI. Update that Replit secret and try again.", "PROVIDER_AUTH");
      }
      if (response.status === 402 || response.status === 403) {
        throw new AiRequestError(503, "The xAI account has no available credits. Add credits, then try again.", "PROVIDER_CREDITS");
      }
      if (response.status === 429) {
        throw new AiRequestError(429, "AI generation is temporarily rate limited. Please try again shortly.", "RATE_LIMIT");
      }
      throw new AiRequestError(502, "AI generation is unavailable right now. Please try again shortly.", "UPSTREAM_ERROR");
    }
    const text = completionText(data).trim();
    if (!text) throw new AiRequestError(502, "The AI returned an empty response. Please try again.", "EMPTY_RESPONSE");
    return { text, model: (data && data.model) || model || DEFAULT_XAI_MODEL };
  } catch (error) {
    if (error instanceof AiRequestError) throw error;
    if (error && (error.name === "AbortError" || error.code === "ABORT_ERR")) {
      throw new AiRequestError(504, "The AI request timed out. Please try again.", "TIMEOUT");
    }
    throw new AiRequestError(503, "The AI provider could not be reached. Please try again shortly.", "PROVIDER_UNAVAILABLE");
  } finally {
    clearTimeout(timer);
  }
}

async function generateDispatchReply({ apiKey, completeWithKey, completeWithConnector }) {
  const key = String(apiKey || "").trim();
  if (key) return completeWithKey(key);
  try {
    return await completeWithConnector();
  } catch (error) {
    if (error instanceof AiRequestError && ["PROVIDER_CREDITS", "RATE_LIMIT", "UPSTREAM_ERROR", "EMPTY_RESPONSE", "INVALID_RESPONSE", "TIMEOUT", "MARKET_DATA_UNAVAILABLE"].includes(error.code)) {
      throw error;
    }
    const detail = error && (error.code || error.message) ? (error.code || error.message) : error;
    console.error("xAI connector chat failed:", detail);
    throw new AiRequestError(503, MISSING_KEY_MESSAGE, "AI_KEY_MISSING");
  }
}

module.exports = {
  AiRequestError,
  DEFAULT_XAI_BASE_URL,
  DEFAULT_XAI_MODEL,
  MISSING_KEY_MESSAGE,
  XAI_API_KEY_ENV,
  completeWithXaiKey,
  generateDispatchReply,
  guestUser,
  publicUser,
  resolvePublicUser,
  sessionTokens,
  xaiApiKey,
  xaiBaseUrl,
  xaiModel,
};
