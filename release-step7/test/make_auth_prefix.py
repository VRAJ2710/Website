# TEST ONLY: builds an auth harness from the REAL lineage auth code (c101g base, ancestor of live r6n) - verbatim functions and
# handler bodies - plus small stubs for things that are not under test. Output: test/auth_prefix.js
import sys
L = open("/workspace/c101g/base/server.js").read().split("\n")
def rng(a, b): return "\n".join(L[a-1:b])
def fn(start):  # verbatim function starting at line `start` up to the closing "}" at column 0
    i = start - 1; out = []
    while True:
        out.append(L[i])
        if L[i] == "}" : break
        i += 1
    return "\n".join(out)
def block(start):  # verbatim route block "  if (...) {" ... "  }"
    i = start - 1; out = [L[i]]; i += 1
    while L[i] != "  }": out.append(L[i]); i += 1
    out.append(L[i]); return "\n".join(out)
find = lambda s: next(i + 1 for i, l in enumerate(L) if l.startswith(s))
parts = []
parts.append('''// ---- TEST-ONLY auth harness: verbatim c101g auth code over PGlite ----
const crypto = require("crypto");
const { neon, testSchema, testUsers, testRoute } = require("/workspace/c113/release-step7/test/neon_pglite.js");
process.env.DATABASE_URL = process.env.DATABASE_URL || "pglite://memory";
const ACCOUNT_EMAIL_MAX_LENGTH = 254, ACCOUNT_PASSWORD_MIN_LENGTH = 8, ACCOUNT_PASSWORD_MAX_LENGTH = 128, AUTH_FORM_MAX_BYTES = 8192;
const CANONICAL_HOST = "thedispatch.uk";
const PUBLIC_ORIGIN = "https://thedispatch.uk";
function reportRecoveryDeliveryFailure() { throw new Error("not under test"); } function withTimeout() { throw new Error("not under test"); }
let databaseReady = false;
function useSecureCookie() { return false; } function shouldPinSessionDomain() { return false; }
function allowAuthRequest() { return true; } async function c96SaveName() {} function isAdminUser() { return false; }
function publicUser(u) { return { guest: false, id: u.id, email: u.email, tier: u.tier, billingPortal: Boolean(u.billingPortal), isAdmin: false }; }
function text(res, s, b) { res.writeHead(s, { "Content-Type": "text/plain; charset=utf-8" }); res.end(b); }
function json(res, s, b) { res.writeHead(s, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" }); res.end(JSON.stringify(b)); }
async function readAuthForm(req) { const c = []; for await (const x of req) c.push(x); return Buffer.concat(c).toString("utf8"); }''')
parts.append(L[find('const { ReplitConnectors } = require("@replit/connectors-sdk");') - 1])  # verbatim (mocked module in tests)
parts.append(rng(find("const ACCOUNT_PUBLIC_ORIGIN = "), find("const RECOVERY_SENDER_PREFLIGHT = ")))  # verbatim recovery/Resend settings
parts.append(rng(366, 366))  # const sql = ... neon(...)
for s in ("function cookieValue(", "function tokenHash(", "function dispatchSessionTokens(", "function cookieFlags(",
          "async function currentUser(", "async function currentUserForToken(", "function sessionCookieHeader(",
          "function clearSessionCookieHeader(", "async function deletePresentedSessions(", "async function setSession(",
          "function passwordHash(", "function validPassword(", "function validAccountInput(", "async function initializeAuthDatabase(",
          "async function findUserByEmail(", "async function findUserById(", "function sameOriginMutation(",
          "function page(", "async function deliverRecoveryWithResend("):
    parts.append(fn(find(s)))
# initializeAuthDatabase may reference later tables; we only need the first two CREATEs -> run its verbatim body but tolerate the rest
reg = block(find('  if (p === "/__auth/register" && req.method === "POST") {'))
log = block(find('  if (p === "/__auth/login" && req.method === "POST") {'))
sub = block(find('  if (p === "/__auth/subscribe" && req.method === "POST") {'))
me = L[find('  if (p === "/api/me" && req.method === "GET") {') - 1]
parts.append('''const authDbReady = (async function () {
  try { await initializeAuthDatabase(); } catch (e) { if (!/does not exist|relation/.test(String(e.message))) console.log("init note: " + e.message); }
  await testSchema(sql);  // TEST DB SETUP ONLY: adds the production column (lives in neon_pglite.js)
  await sql`INSERT INTO dispatch_users (id, email, password_hash, tier, created_at) VALUES ('00000000-0000-4000-8000-000000000001', 'old@example.com', ${passwordHash("oldpassword1")}, 'free', NOW() - INTERVAL '30 days') ON CONFLICT DO NOTHING`;
  databaseReady = true;
})();
async function authHarnessRoute(req, res, p) {
  await authDbReady;
  if (p === "/__testdb/users") return json(res, 200, await testUsers(sql));
  if (p.startsWith("/__testdb/")) return json(res, 200, await testRoute(sql, p, new URL(req.url, "http://x").searchParams, tokenHash));
''' + reg + "\n" + log + "\n" + sub + "\n" + me + '''
  if (p === "/api/me") return "fallthrough";
}
function authHarness(req, res) {
  const p = req.url.split("?")[0];
  const signed = /dispatch_session=/.test(req.headers.cookie || "");
  if (req.method === "POST" && (p === "/__auth/register" || p === "/__auth/login" || p === "/__auth/subscribe")) { authHarnessRoute(req, res, p).catch(e => { res.statusCode = 500; res.end(String(e)); }); return true; }
  if (p.startsWith("/__testdb/") || (p === "/api/me" && signed)) { authHarnessRoute(req, res, p).catch(e => { res.statusCode = 500; res.end(String(e)); }); return true; }
  return false;
}
// ---- end harness ----''')
open(sys.argv[1], "w").write("\n".join(parts) + "\n")
