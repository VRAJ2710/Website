"use strict";

const path = require("path");

/**
 * Canonical public site. Live currently serves both apex and www; session
 * cookies were host-only, so Stripe return URLs on the other host looked
 * signed out. Pin Stripe and cookie domain to the apex registrable site.
 */
const CANONICAL_ORIGIN = "https://thedispatch.uk";
const CANONICAL_HOST = "thedispatch.uk";
const REPLIT_PRODUCTION_HOST = "the-dispatch.replit.app";
const PUBLIC_HOSTS = new Set(["thedispatch.uk", "www.thedispatch.uk"]);

const PUBLIC_STATIC_PATHS = new Set([
  "/index.html",
  "/app.js",
  "/styles.css",
  "/logo-mark.svg",
  "/og-card.svg",
  "/manifest.json",
  "/robots.txt",
  "/sitemap.xml",
]);

const BLOCKED_BASENAMES = new Set([
  "server.js",
  "stripeclient.js",
  "marketproxy.js",
  "rssfeeds.js",
  "billingorigin.js",
  "startcheckout.js",
  "package.json",
  "package-lock.json",
  "pnpm-lock.yaml",
  ".replit",
  "replit.md",
  "zipfile.zip",
  "tsconfig.story.json",
]);

function headerFirst(value) {
  return String(value || "").split(",")[0].trim();
}

function requestHost(req) {
  const headers = req?.headers || {};
  return headerFirst(headers["x-forwarded-host"]) || headerFirst(headers.host);
}

function requestProtocol(req) {
  const forwarded = headerFirst(req?.headers?.["x-forwarded-proto"]);
  if (forwarded === "https" || forwarded === "http") return forwarded;
  return "http";
}

function hostnameOf(host) {
  return String(host || "").split(":")[0].toLowerCase();
}

function isPublicDispatchHost(host) {
  return PUBLIC_HOSTS.has(hostnameOf(host));
}

function isPublicDispatchOrigin(value) {
  try {
    return isPublicDispatchHost(new URL(String(value || "").trim()).hostname);
  } catch {
    return false;
  }
}

/**
 * DISPATCH_PUBLIC_ORIGIN wins over REPLIT_DOMAINS, but www is always
 * rewritten to apex so a mis-set production secret cannot split sessions.
 */
function configuredPublicOrigin(env = process.env) {
  const raw = String(env.DISPATCH_PUBLIC_ORIGIN || "").trim().replace(/\/$/, "");
  if (!raw) return "";
  if (isPublicDispatchOrigin(raw)) return CANONICAL_ORIGIN;
  return raw;
}

function publicUrl(req, options = {}) {
  const env = options.env || process.env;
  const port = options.port || env.PORT || 5000;
  const host = requestHost(req);
  const configured = configuredPublicOrigin(env);

  if (isPublicDispatchHost(host) || isPublicDispatchOrigin(configured)) {
    return CANONICAL_ORIGIN;
  }
  if (configured) return configured;

  const protocol = requestProtocol(req) === "https" ? "https" : "http";
  if (host) return `${protocol}://${host}`;

  const previewDomain = String(env.REPLIT_DOMAINS || "").split(",")[0].trim();
  if (previewDomain) return `https://${previewDomain}`;
  return `${protocol}://localhost:${port}`;
}

function webhookBaseUrl(env = process.env) {
  const configured = configuredPublicOrigin(env);
  if (configured) return configured;
  const domain = String(env.REPLIT_DOMAINS || "").split(",")[0].trim();
  if (domain) return `https://${domain}`;
  return "";
}

function canonicalRedirectLocation(req, publicOrigin = CANONICAL_ORIGIN) {
  const host = hostnameOf(requestHost(req));
  // www and the production Replit alias both 308 to apex. Preview hosts stay put.
  if (host !== "www.thedispatch.uk" && host !== REPLIT_PRODUCTION_HOST) return null;
  const origin = String(publicOrigin || CANONICAL_ORIGIN).replace(/\/$/, "");
  try {
    const url = new URL(req.url || "/", origin);
    return `${origin}${url.pathname}${url.search}`;
  } catch {
    return `${origin}/`;
  }
}

function writeCanonicalRedirect(req, res, publicOrigin = CANONICAL_ORIGIN) {
  const location = canonicalRedirectLocation(req, publicOrigin);
  if (!location) return false;
  res.writeHead(308, { Location: location, "Cache-Control": "no-store" });
  res.end();
  return true;
}

function useSecureCookie(req) {
  const host = hostnameOf(requestHost(req));
  return requestProtocol(req) === "https" || isPublicDispatchHost(host) || host === REPLIT_PRODUCTION_HOST;
}

function shouldPinSessionDomain(req) {
  const host = hostnameOf(requestHost(req));
  // Apex and www share one cookie. The production Replit hostname must not mint
  // another host-only dispatch_session. Browsers drop Domain=thedispatch.uk on
  // that host; the 308 sends login to apex before a session cookie is set.
  // Localhost and other preview hosts stay host-only so a Domain attribute is
  // not written onto a host that cannot store it.
  return PUBLIC_HOSTS.has(host) || host === REPLIT_PRODUCTION_HOST;
}

function cookieFlags(req, { maxAge, clear = false, domain } = {}) {
  const parts = ["Path=/", "HttpOnly", "SameSite=Lax"];
  parts.push(clear ? "Max-Age=0" : `Max-Age=${maxAge ?? 2592000}`);
  if (useSecureCookie(req)) parts.push("Secure");
  const pinDomain = domain === undefined ? shouldPinSessionDomain(req) : Boolean(domain);
  if (pinDomain) parts.push(`Domain=${CANONICAL_HOST}`);
  return parts;
}

function dispatchSessionTokens(cookieHeader) {
  const raw = Array.isArray(cookieHeader) ? cookieHeader.join("; ") : String(cookieHeader || "");
  const prefix = "dispatch_session=";
  const values = [];
  for (const part of raw.split(";")) {
    const trimmed = part.trim();
    if (!trimmed.startsWith(prefix)) continue;
    const encoded = trimmed.slice(prefix.length);
    if (!encoded) continue;
    try {
      values.push(decodeURIComponent(encoded));
    } catch {
      values.push(encoded);
    }
    if (values.length >= 8) break;
  }
  return values;
}

function clearSessionCookieHeader(req) {
  const hostOnly = ["dispatch_session=", ...cookieFlags(req, { clear: true, domain: false })].join("; ");
  const domainScoped = ["dispatch_session=", ...cookieFlags(req, { clear: true, domain: true })].join("; ");
  return [hostOnly, domainScoped];
}

function sessionCookieHeader(token, req) {
  const established = [`dispatch_session=${token}`, ...cookieFlags(req)].join("; ");
  // Expire a host-only ghost and any previous Domain cookie, then set the new one.
  // The later Domain (or host-only) Set-Cookie wins for that cookie's identity.
  return [...clearSessionCookieHeader(req), established];
}

function isStripeWebhookPath(pathname) {
  return pathname === "/api/stripe/webhook" || pathname === "/api/stripe-webhook";
}

function normalizedPathname(pathname) {
  const raw = String(pathname || "/");
  const noQuery = raw.split("?")[0];
  try {
    return decodeURIComponent(noQuery);
  } catch {
    return noQuery;
  }
}

function isBlockedSourcePath(pathname) {
  const rel = normalizedPathname(pathname);
  const base = path.posix.basename(rel).toLowerCase();
  if (BLOCKED_BASENAMES.has(base)) return true;
  if (base.endsWith(".map")) return true;
  if (rel.startsWith("/test/") || rel.startsWith("/scripts/") || rel.startsWith("/story/") || rel.startsWith("/artifacts/") || rel.startsWith("/.agents/")) {
    return true;
  }
  if (rel.startsWith("/.") && rel !== "/") return true;
  return false;
}

function isServableStaticPath(pathname) {
  const rel = normalizedPathname(pathname);
  if (rel === "/" || rel === "/index.html") return true;
  if (isBlockedSourcePath(rel)) return false;
  return PUBLIC_STATIC_PATHS.has(rel);
}

function resolveStaticFile(root, pathname) {
  const rel = normalizedPathname(pathname);
  const requested = rel === "/" ? "/index.html" : rel;
  if (!isServableStaticPath(requested)) return null;
  const file = path.normalize(path.join(root, requested));
  const rootDir = path.normalize(root);
  const prefix = rootDir.endsWith(path.sep) ? rootDir : rootDir + path.sep;
  if (file !== rootDir && !file.startsWith(prefix)) return null;
  return file;
}

module.exports = {
  BLOCKED_BASENAMES,
  CANONICAL_HOST,
  CANONICAL_ORIGIN,
  PUBLIC_HOSTS,
  PUBLIC_STATIC_PATHS,
  REPLIT_PRODUCTION_HOST,
  canonicalRedirectLocation,
  clearSessionCookieHeader,
  configuredPublicOrigin,
  cookieFlags,
  dispatchSessionTokens,
  isBlockedSourcePath,
  isPublicDispatchHost,
  isPublicDispatchOrigin,
  isServableStaticPath,
  isStripeWebhookPath,
  publicUrl,
  requestHost,
  requestProtocol,
  resolveStaticFile,
  sessionCookieHeader,
  shouldPinSessionDomain,
  useSecureCookie,
  webhookBaseUrl,
  writeCanonicalRedirect,
};
