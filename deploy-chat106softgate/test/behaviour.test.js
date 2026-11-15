// Behaviour tests for the patched fixture prefix. Usage: node behaviour.test.js <patched_prefix.js> <off|on>
process.env.NODE_ENV = "test";
process.env.DISPATCH_TEST_REQUIRE_EMAIL_VERIFICATION = "1";
const assert = require("assert");
const path = require("path");
const mod = require(path.resolve(process.argv[2]));
const MODE = process.argv[3];
let pass = 0;
const errLines = [];
const origErr = console.error;
console.error = (...a) => { errLines.push(a.join(" ")); };
function req(method, url, { body = "", cookie = "", accept = "", origin = "" } = {}) {
  const headers = { host: "dev.test", cookie, accept };
  if (origin) headers.origin = origin;
  return { method, url, headers, body, socket: {} };
}
function res() {
  const r = { status: 0, headers: {}, body: "" };
  r.setHeader = (k, v) => { r.headers[k.toLowerCase()] = v; };
  r.getHeader = k => r.headers[k.toLowerCase()];
  r.writeHead = (s, h = {}) => { r.status = s; for (const k of Object.keys(h)) r.headers[k.toLowerCase()] = h[k]; };
  r.end = b => { if (b !== undefined) r.body += String(b); r.ended = true; };
  return r;
}
async function call(method, url, opts) { const r = res(); await mod.handle(req(method, url, opts), r); return r; }
function sessionCookie(r) { const c = [].concat(r.headers["set-cookie"] || []).find(x => /^dispatch_session=/.test(x)); return c ? c.split(";")[0] : ""; }
async function t(name, fn) { await fn(); pass++; console.log("ok -", name); }
(async () => {
  const OFF = MODE === "off";
  await t("attach line printed once at load", async () => {});
  // 1. Sign-up of a new account.
  const reg = await call("POST", "/__auth/register", { body: "email=a%40x.test&password=password1" });
  const regUser = [...mod.DB.users.values()].find(u => u.email === "a@x.test");
  await t("new account is stored with email_verified=false (column kept)", async () => assert.strictEqual(regUser.email_verified, false));
  await t("verification email sent on sign-up", async () => assert.strictEqual(mod.MAIL.sent.filter(m => m.email === "a@x.test").length, 1));
  if (OFF) {
    await t("flag off: sign-up continues (302 + session)", async () => { assert.strictEqual(reg.status, 302); assert.ok(sessionCookie(reg)); });
  } else {
    await t("flag on: sign-up shows verify-first page, no session", async () => { assert.strictEqual(reg.status, 200); assert.ok(/Check your email/.test(reg.body)); assert.ok(!sessionCookie(reg)); });
  }
  // 2. Sign-in of the unverified account.
  const login = await call("POST", "/__auth/login", { body: "email=a%40x.test&password=password1" });
  const ck = sessionCookie(login) || sessionCookie(reg);
  if (OFF) await t("flag off: sign-in of unverified account succeeds", async () => { assert.strictEqual(login.status, 302); assert.ok(sessionCookie(login)); });
  else await t("flag on: sign-in of unverified account is blocked", async () => { assert.strictEqual(login.status, 200); assert.ok(/not active yet/.test(login.body)); assert.ok(!sessionCookie(login)); });
  // 3. Checkout page + checkout route for the signed-in unverified reader.
  const before = mod.STRIPE.sessions.length;
  const page = await call("GET", "/__auth/subscribe", { cookie: ck });
  const co = await call("POST", "/__auth/subscribe", { cookie: ck, body: "" });
  const api = await call("POST", "/api/checkout", { cookie: ck });
  if (OFF) {
    await t("flag off: checkout page shows the reminder and resend button", async () => {
      assert.ok(/PREMIUM ACCESS/.test(page.body) && /Continue to Stripe Checkout/.test(page.body));
      assert.ok(/Please verify your email\./.test(page.body));
      assert.ok(/action="\/__auth\/verify\/resend"/.test(page.body));
      assert.ok(/a@x\.test/.test(page.body));
    });
    await t("flag off: checkout POST proceeds to /?checkout=1", async () => { assert.strictEqual(co.status, 302); assert.strictEqual(co.headers.location, "/?checkout=1"); });
    await t("flag off: checkout session is created for the unverified reader", async () => { assert.strictEqual(api.status, 200); assert.strictEqual(mod.STRIPE.sessions.length, before + 1); });
  } else {
    await t("flag on: no signed-in session, checkout page is the guest form, no reminder", async () => { assert.ok(/Create your Dispatch sign-in/.test(page.body)); assert.ok(!/Please verify your email/.test(page.body)); });
    await t("flag on: checkout API refuses (401)", async () => { assert.strictEqual(api.status, 401); assert.strictEqual(mod.STRIPE.sessions.length, before); });
  }
  // 4. Guest checkout form creating a new account.
  const sentBefore = mod.MAIL.sent.length;
  const g = await call("POST", "/__auth/subscribe", { body: "email=b%40x.test&password=password2" });
  await t("guest checkout: verification email sent for the new account", async () => assert.strictEqual(mod.MAIL.sent.length, sentBefore + 1));
  if (OFF) await t("flag off: guest checkout continues to /?checkout=1 with a session", async () => { assert.strictEqual(g.status, 302); assert.strictEqual(g.headers.location, "/?checkout=1"); assert.ok(sessionCookie(g)); });
  else await t("flag on: guest checkout is blocked with the verify-first page", async () => { assert.strictEqual(g.status, 200); assert.ok(/before checkout/.test(g.body)); assert.ok(!sessionCookie(g)); });
  // 5. Resend failure: sign-up and checkout still continue, failure logged once.
  mod.MAIL.fail = true;
  const logs0 = errLines.length;
  const r2 = await call("POST", "/__auth/register", { body: "email=c%40x.test&password=password3" });
  const g2 = await call("POST", "/__auth/subscribe", { body: "email=d%40x.test&password=password4" });
  if (OFF) {
    await t("flag off: Resend failure, sign-up still continues", async () => { assert.strictEqual(r2.status, 302); assert.ok(sessionCookie(r2)); });
    await t("flag off: Resend failure, checkout still continues", async () => { assert.strictEqual(g2.status, 302); assert.strictEqual(g2.headers.location, "/?checkout=1"); });
  }
  await t("Resend failure: exactly one log line per failed send", async () => assert.strictEqual(errLines.length - logs0, 2));
  mod.MAIL.fail = false;
  // 5b. A throw inside the send path (token insert) is caught and logged once.
  if (OFF) {
    // (flag on keeps the original enforced path exactly as it is, so it is not exercised here)
    mod.MAIL.throwOnInsert = true;
    const logs1 = errLines.length;
    const r3 = await call("POST", "/__auth/register", { body: "email=e%40x.test&password=password5" });
    mod.MAIL.throwOnInsert = false;
    await t("flag off: send path throws, sign-up still continues", async () => assert.strictEqual(r3.status, 302));
    await t("send path throws: one chat106softgate log line", async () => { assert.strictEqual(errLines.length - logs1, 1); assert.ok(/verification_email_failed/.test(errLines[errLines.length - 1])); assert.ok(!/e@x\.test/.test(errLines[errLines.length - 1])); });
  }
  if (OFF) {
    // 6. Resend endpoint and status endpoint.
    const st = await call("GET", "/__auth/verify/status", { cookie: ck });
    await t("status says reminder=true for the unverified reader", async () => assert.deepStrictEqual(JSON.parse(st.body), { reminder: true }));
    const stg = await call("GET", "/__auth/verify/status");
    await t("status says reminder=false for a guest", async () => assert.deepStrictEqual(JSON.parse(stg.body), { reminder: false }));
    const n0 = mod.MAIL.sent.length;
    const rs = await call("POST", "/__auth/verify/resend", { cookie: ck, accept: "application/json", origin: "https://dev.test" });
    await t("resend (JSON) sends a new email", async () => { assert.deepStrictEqual(JSON.parse(rs.body), { state: "sent" }); assert.strictEqual(mod.MAIL.sent.length, n0 + 1); });
    const rs2 = await call("POST", "/__auth/verify/resend", { cookie: ck });
    await t("resend again within a minute is throttled (HTML page)", async () => { assert.ok(/wait a minute/.test(rs2.body)); assert.strictEqual(mod.MAIL.sent.length, n0 + 1); });
    const rsx = await call("POST", "/__auth/verify/resend", { cookie: ck, origin: "https://evil.test" });
    await t("cross-site resend refused", async () => assert.strictEqual(rsx.status, 403));
    const rsg = await call("GET", "/__auth/verify/resend");
    await t("GET resend is 405", async () => assert.strictEqual(rsg.status, 405));
    const js = await call("GET", "/__auth/verify/reminder.js");
    await t("reminder.js is served and parses", async () => { assert.strictEqual(js.status, 200); new Function(js.body); assert.ok(/Please verify your email\./.test(js.body)); });
    const app = await call("GET", "/app");
    await t("app pages carry the reminder script exactly once", async () => { assert.strictEqual(app.body.split("/__auth/verify/reminder.js").length - 1, 1); assert.ok(/reminder\.js\?v=chat106softgate"><\/script><\/body>/.test(app.body)); });
    // 7. Verified reader: no reminder.
    const v = [...mod.DB.users.values()].find(u => u.email === "a@x.test"); v.email_verified = true;
    const page2 = await call("GET", "/__auth/subscribe", { cookie: ck });
    await t("verified reader: checkout page has no reminder", async () => { assert.ok(/PREMIUM ACCESS/.test(page2.body)); assert.ok(!/c106sg-reminder/.test(page2.body)); });
    const st2 = await call("GET", "/__auth/verify/status", { cookie: ck });
    await t("verified reader: status reminder=false", async () => assert.deepStrictEqual(JSON.parse(st2.body), { reminder: false }));
    // 8. Re-register an unverified address with the right password: signed in, fresh link.
    const n1 = mod.MAIL.sent.length;
    const rr = await call("POST", "/__auth/register", { body: "email=b%40x.test&password=password2" });
    await t("re-register unverified with right password signs in and resends", async () => { assert.strictEqual(rr.status, 302); assert.ok(sessionCookie(rr)); assert.strictEqual(mod.MAIL.sent.length, n1 + 1); });
    const rw = await call("POST", "/__auth/register", { body: "email=b%40x.test&password=wrongpass9" });
    await t("re-register with wrong password still fails", async () => { assert.ok(/Unable to create account/.test(rw.body)); assert.ok(!sessionCookie(rw)); });
  }
  console.error = origErr;
  console.log(`# ${MODE}: ${pass} passed`);
})().catch(e => { console.error = origErr; console.error("FAIL:", e && e.stack || e); process.exit(1); });
