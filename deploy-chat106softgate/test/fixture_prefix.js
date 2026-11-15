const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)
// Test fixture: reconstruction of the dev auth code (Claude Code commits d757562/e60934a, per server.diff.txt)
// with in-memory stand-ins for the database and email transport. Not the real server.js.
const crypto = require("crypto");
const INDEX_TEMPLATE = "<!DOCTYPE html><html><head><title>x</title></head><body><main id=\"main\">app</main><script defer src=\"/app.js?v=__DISPATCH_ASSET_VERSION__\"></script></body>\n</html>";
const DISPATCH_ASSET_VERSION = "0123456789abcdef";
function withAssetVersion(html) {
  return html
    .replaceAll("/styles.css?v=dispatch-terminal-1", `/styles.css?v=${DISPATCH_ASSET_VERSION}`)
    .replaceAll("DISPATCH_ASSET_VERSION", DISPATCH_ASSET_VERSION);
}
const ACCOUNT_PASSWORD_MIN_LENGTH = 8;
const ACCOUNT_PASSWORD_MAX_LENGTH = 128;
const PASSWORD_RESET_TTL_MINUTES = 30;
const EMAIL_VERIFICATION_TTL_HOURS = 24;
const EMAIL_VERIFICATION_TTL_SECONDS = EMAIL_VERIFICATION_TTL_HOURS * 60 * 60;
const RECOVERY_REQUEST_LIMIT = 3;
// ---- in-memory DB stand-in -------------------------------------------------------------
const DB = { users: new Map(), sessions: new Map(), verifications: new Map(), queries: [] };
let databaseReady = true;
function tokenHash(t) { return crypto.createHash("sha256").update(String(t)).digest("hex"); }
async function sql(strings, ...values) {
  const q = strings.join("$?");
  DB.queries.push({ q, values });
  if (/FROM dispatch_sessions s JOIN dispatch_users u/.test(q)) {
    const s = DB.sessions.get(values[0]);
    if (!s) return [{ data: [] }];
    const u = DB.users.get(s.userId);
    if (!u) return [{ data: [] }];
    let ok = true;
    if (/AND u\.email_verified=TRUE LIMIT 1/.test(q)) ok = u.email_verified === true;
    else if (/AND \(u\.email_verified=TRUE OR \$\?=1\) LIMIT 1/.test(q)) ok = u.email_verified === true || Number(values[1]) === 1;
    else if (/email_verified/.test(q.split("WHERE")[1] || "")) throw new Error("unexpected session filter: " + q);
    return [{ data: ok ? [{ id: u.id, email: u.email, passwordHash: u.password_hash, tier: u.tier, billingPortal: false, emailVerified: u.email_verified }] : [] }];
  }
  if (/^INSERT INTO dispatch_users/.test(q.trim())) {
    if ([...DB.users.values()].some(u => u.email === values[1])) throw new Error("duplicate");
    const verified = values.length >= 4 ? values[values.length - 1] : true;
    DB.users.set(values[0], { id: values[0], email: values[1], password_hash: values[2], tier: "free", email_verified: verified });
    return [];
  }
  if (/FROM dispatch_users WHERE email=/.test(q)) {
    const u = [...DB.users.values()].find(x => x.email === values[0]);
    return [{ data: u ? [{ id: u.id, email: u.email, passwordHash: u.password_hash, tier: u.tier, billingPortal: false, emailVerified: u.email_verified }] : [] }];
  }
  if (/FROM dispatch_users WHERE id=/.test(q)) {
    const u = DB.users.get(values[0]);
    return [{ data: u ? [{ id: u.id, email: u.email, passwordHash: u.password_hash, tier: u.tier, billingPortal: false, emailVerified: u.email_verified }] : [] }];
  }
  if (/dispatch_email_verifications/.test(q)) {
    if (MAIL.throwOnInsert && /^INSERT/.test(q.trim())) throw new Error("db down");
    return [];
  }
  return [];
}
// ---- email stand-in --------------------------------------------------------------------
const MAIL = { sent: [], fail: false, throwOnInsert: false, failLogs: 0 };
async function reportRecoveryDeliveryFailure(reason) { MAIL.failLogs++; console.error(JSON.stringify({ event: "recovery_delivery_failed", reason })); }
async function deliverVerificationEmail({ email, verifyUrl }) {
  if (MAIL.fail) { await reportRecoveryDeliveryFailure("provider_rejection"); return false; }
  MAIL.sent.push({ email, verifyUrl });
  return true;
}
function recoveryOrigin() { return "https://example.test"; }
async function issueEmailVerification(user) {
  if (!user || user.emailVerified) return false;
  const origin = recoveryOrigin();
  if (!origin) {
    await reportRecoveryDeliveryFailure("invalid_configuration");
    return false;
  }
  const token = crypto.randomBytes(32).toString("hex");
  const tokenDigest = tokenHash(token);
  await sql`DELETE FROM dispatch_email_verifications WHERE user_id=${user.id}`;
  await sql`INSERT INTO dispatch_email_verifications (token_hash, user_id, expires_at)
    VALUES (${tokenDigest}, ${user.id}, NOW() + INTERVAL '24 hours')`;
  let delivered = false;
  try {
    delivered = await deliverVerificationEmail({
      email: user.email,
      verifyUrl: `${origin}/__auth/verify?token=${encodeURIComponent(token)}`,
    });
  } catch {
    delivered = false;
  }
  return delivered;
}
function emailVerificationRequired() {
  return process.env.NODE_ENV !== "test" || process.env.DISPATCH_TEST_REQUIRE_EMAIL_VERIFICATION === "1";
}
// ---- helpers ---------------------------------------------------------------------------
async function currentUserForToken(token) {
  if (!token) return null;
  const result = await sql`SELECT COALESCE(json_agg(row_to_json(uq)), '[]'::json) AS data FROM (SELECT u.id, u.email, u.password_hash AS "passwordHash", u.tier,
    u.checkout_attempt_id AS "checkoutAttemptId", u.email_verified AS "emailVerified"
    FROM dispatch_sessions s JOIN dispatch_users u ON u.id = s.user_id
    WHERE s.token_hash=${tokenHash(token)} AND s.expires_at > NOW() AND u.email_verified=TRUE LIMIT 1) uq`;
  return result[0]?.data?.[0] || null;
}
function cookieValue(req, name) {
  const m = new RegExp("(?:^|;\\s*)" + name + "=([^;]*)").exec(String(req.headers.cookie || ""));
  return m ? decodeURIComponent(m[1]) : "";
}
async function currentUser(req) {
  if (!databaseReady) return null;
  return currentUserForToken(cookieValue(req, "dispatch_session"));
}
async function findUserByEmail(email) {
  const r = await sql`SELECT COALESCE(json_agg(row_to_json(uq)), '[]'::json) AS data FROM (SELECT id, email_verified AS "emailVerified"
    FROM dispatch_users WHERE email=${email} LIMIT 1) uq`;
  return r[0]?.data?.[0] || null;
}
function passwordHash(p) { return "h:" + p; }
function validPassword(p, h) { return h === "h:" + p; }
function validAccountInput(e, p) { return /@/.test(e) && p.length >= 8 && p.length <= 128; }
async function c96SaveName() {}
function sameOriginMutation(req) { return !req.headers.origin || req.headers.origin === "https://" + req.headers.host; }
function allowAuthRequest() { return true; }
async function readAuthForm(req) { return req.body || ""; }
async function setSession(req, res, user) {
  const token = crypto.randomBytes(16).toString("hex");
  DB.sessions.set(tokenHash(token), { userId: user.id });
  res.setHeader("Set-Cookie", `dispatch_session=${token}; Path=/; HttpOnly`);
}
function isAdminUser() { return false; }
function page(res, title, content) {
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" });
  res.end(`<!doctype html><html><head><title>${title}</title></head><body><main>${content}</main></body></html>`);
}
function text(res, status, body, type = "text/plain; charset=utf-8") { res.writeHead(status, { "Content-Type": type }); res.end(body); }
function json(res, status, obj) { res.writeHead(status, { "Content-Type": "application/json" }); res.end(JSON.stringify(obj)); }
const STRIPE = { sessions: [] };
async function createStripeCheckout(user) { STRIPE.sessions.push(user.id); return "https://checkout.stripe.com/c/test"; }
// ---- request handler (auth routes as in the dev diff) -----------------------------------
async function handle(req, res) {
  const url = new URL(req.url, "http://" + req.headers.host);
  const p = url.pathname;
  if (p === "/__auth/verify" && req.method === "GET") {
    return page(res, "Verify your email · The Dispatch Market", "<h1>Verify your email</h1>");
  }
  if (p === "/__auth/register" && req.method === "POST") {
    if (!sameOriginMutation(req)) return text(res, 403, "Cross-site account registration is not allowed.");
    if (!allowAuthRequest(req, res)) return;
    const raw = await readAuthForm(req, res); if (raw === null) return;
    const form = new URLSearchParams(raw);
    const email = (form.get("email") || "").trim().toLowerCase();
    const password = form.get("password") || "";
    if (!validAccountInput(email, password)) {
      return page(res, "Registration failed", "<h1>Unable to create account</h1>");
    }
    const verificationRequired = emailVerificationRequired();
    const existing = await findUserByEmail(email);
    if (existing) {
      if (!existing.emailVerified && validPassword(password, existing.passwordHash)) {
        const delivered = await issueEmailVerification(existing);
        return page(res, "Check your email · The Dispatch Market", delivered
          ? "<h1>Check your email</h1><p>If this account is awaiting verification, a fresh confirmation link has been sent. It expires in 24 hours.</p><a href='/__auth/login'>Return to sign in</a>"
          : "<h1>We couldn't send a confirmation email yet.</h1><p>Your account remains inactive. Sign in with your password later to request another link.</p><a href='/__auth/login'>Return to sign in</a>");
      }
      return page(res, "Registration failed", "<h1>Unable to create account</h1><p>We could not create that account. Check your details and try again.</p><a href='/__auth/register'>Try again</a>");
    }
    const user = {
      id: crypto.randomUUID(),
      email,
      passwordHash: passwordHash(password),
      tier: "free",
      billingPortal: false,
      emailVerified: !verificationRequired,
    };
    try {
      await sql`INSERT INTO dispatch_users (id, email, password_hash, tier, email_verified)
        VALUES (${user.id}, ${user.email}, ${user.passwordHash}, 'free', ${user.emailVerified})`;
      try { await c96SaveName(user.id, form.get("name")); } catch (c96e) {} // chat96: optional name, stored with the account
    } catch {
      return page(res, "Registration failed", "<h1>Unable to create account</h1>");
    }
    if (verificationRequired) {
      const delivered = await issueEmailVerification(user);
      return page(res, "Verify your email · The Dispatch Market", delivered
        ? "<h1>Check your email</h1><p>We sent a one-time confirmation link. It expires in 24 hours. Your account becomes active after you confirm your address.</p><a href='/__auth/login'>Return to sign in</a>"
        : "<h1>Your account is waiting for email confirmation.</h1><p>We couldn't send the confirmation email right now. Sign in with your password to request another link later.</p><a href='/__auth/login'>Return to sign in</a>");
    }
    await setSession(req, res, user, cookieValue(req, "dispatch_session"));
    res.writeHead(302, { Location: "/" });
    return res.end();
  }
  if (p === "/__auth/login" && req.method === "POST") {
    const raw = await readAuthForm(req, res); if (raw === null) return;
    const form = new URLSearchParams(raw);
    const email = (form.get("email") || "").trim().toLowerCase();
    const password = form.get("password") || "";
    const user = await findUserByEmail(email);
    if (!user || !validAccountInput(email, password) || !validPassword(password, user.passwordHash)) {
      return page(res, "Sign in", "<h1>Sign in failed</h1>");
    }
    if (!user.emailVerified) {
      const delivered = await issueEmailVerification(user);
      return page(res, "Verify your email · The Dispatch Market", delivered
        ? "<h1>Verify your email</h1><p>Your account is not active yet. We sent a fresh one-time confirmation link; it expires in 24 hours.</p><a href='/__auth/login'>Return to sign in</a>"
        : "<h1>Your account is waiting for email confirmation.</h1><p>We couldn't send the confirmation email right now. Try signing in again later to request a new link.</p><a href='/__auth/login'>Return to sign in</a>");
    }
    await setSession(req, res, user, cookieValue(req, "dispatch_session")); res.writeHead(302, { Location: "/" }); return res.end();
  }
  if (p === "/__auth/subscribe" && req.method === "GET") {
    const user = await currentUser(req);
    if (user && (user.tier === "premium" || isAdminUser(user))) return page(res, "Premium active · The Dispatch Market", `<h1>PREMIUM ACTIVE</h1>`);
    if (user) return page(res, "Premium · The Dispatch Market", `<h1>PREMIUM ACCESS</h1><p>Continue to Stripe Checkout to unlock the weekly Gold Playbook. <a href="/pricing">Compare plans</a>.</p><form method="post"><button>Continue to secure checkout</button></form><p class="muted">£15/month · Cancel anytime in the Stripe billing portal.</p>`);
    return page(res, "Premium · The Dispatch Market", `<h1>PREMIUM ACCESS</h1><p>Create your Dispatch sign-in, then continue to secure Stripe Checkout.</p><form method="post"><label for="subscribe-email">Email</label><input id="subscribe-email" name="email" type="email" autocomplete="email" required><label for="subscribe-password">Password</label><input id="subscribe-password" name="password" type="password" minlength="${ACCOUNT_PASSWORD_MIN_LENGTH}" maxlength="${ACCOUNT_PASSWORD_MAX_LENGTH}" autocomplete="new-password" required><button>Continue to secure checkout</button></form>`);
  }
  if (p === "/__auth/subscribe" && req.method === "POST") {
    if (!sameOriginMutation(req)) return text(res, 403, "Cross-site checkout is not allowed.");
    if (!allowAuthRequest(req, res)) return;
    const raw = await readAuthForm(req, res); if (raw === null) return;
    const form = new URLSearchParams(raw);
    let user = await currentUser(req);
    let accountCreated = false;
    if (!user) {
      const email = (form.get("email") || "").trim().toLowerCase();
      const password = form.get("password") || "";
      if (!validAccountInput(email, password)) return page(res, "Subscribe", "<h1>Use a valid email and a password of at least 8 characters.</h1><a href='/__auth/subscribe'>Try again</a>");
      user = await findUserByEmail(email);
      if (user && !validPassword(password, user.passwordHash)) {
        return page(res, "Sign in failed", "<h1>Sign in failed</h1>");
      }
      if (!user) {
        accountCreated = true;
        user = {
          id: crypto.randomUUID(),
          email,
          passwordHash: passwordHash(password),
          tier: "free",
          billingPortal: false,
          emailVerified: !emailVerificationRequired(),
        };
        await sql`INSERT INTO dispatch_users (id, email, password_hash, email_verified)
          VALUES (${user.id}, ${user.email}, ${user.passwordHash}, ${user.emailVerified})`;
      }
      if (!user.emailVerified) {
        const delivered = await issueEmailVerification(user);
        return page(res, "Verify your email · The Dispatch Market", delivered
          ? "<h1>Verify your email before checkout</h1><p>We sent a one-time confirmation link. It expires in 24 hours. Stripe Checkout will remain locked until your address is confirmed.</p><a href='/__auth/login'>Return to sign in</a>"
          : "<h1>Your account is waiting for email confirmation.</h1><p>We couldn't send the confirmation email right now. Sign in later to request another link. Checkout remains unavailable until confirmation.</p><a href='/__auth/login'>Return to sign in</a>");
      }
      await setSession(req, res, user, cookieValue(req, "dispatch_session"));
    }
    res.writeHead(302, { Location: "/?checkout=1" }); return res.end();
  }
  if (p === "/api/checkout" && req.method === "POST") {
    const user = await currentUser(req);
    if (!user) return json(res, 401, { error: "Sign in first." });
    return json(res, 200, { url: await createStripeCheckout(user) });
  }
  if (p === "/app" && req.method === "GET") return text(res, 200, withAssetVersion(INDEX_TEMPLATE), "text/html; charset=utf-8");
  return text(res, 404, "not found");
}
module.exports = { handle, DB, MAIL, STRIPE, withAssetVersion: (h) => withAssetVersion(h) };
