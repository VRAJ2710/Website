// Box-only proof: what Node actually emits for the live subscribe Set-Cookie construction
// (verbatim call sites) vs the step-8 flatten, under both harness-like and production flags.
"use strict";
const http = require("http");
const assert = require("assert");

function flags(secure, clear, domain) {
  const parts = ["Path=/", "HttpOnly", "SameSite=Lax", clear ? "Max-Age=0" : "Max-Age=2592000"];
  if (secure) parts.push("Secure");
  if (domain) parts.push("Domain=thedispatch.uk");
  return parts;
}
function sessionCookieHeader(token, secure, pinDomain) {
  const established = [`dispatch_session=${token}`, ...flags(secure, false, pinDomain)].join("; ");
  return [
    ["dispatch_session=", ...flags(secure, true, false)].join("; "),
    ["dispatch_session=", ...flags(secure, true, true)].join("; "),
    established,
  ];
}

function capture(setFn) {
  return new Promise((resolve, reject) => {
    const srv = http.createServer((req, res) => {
      setFn(req, res);
      res.writeHead(302, { Location: "/me" });
      res.end();
    });
    srv.listen(0, "127.0.0.1", () => {
      const port = srv.address().port;
      http.get({ host: "127.0.0.1", port, path: "/" }, (res) => {
        const raw = [];
        const rh = res.rawHeaders;
        for (let i = 0; i < rh.length; i += 2) if (rh[i].toLowerCase() === "set-cookie") raw.push(rh[i + 1]);
        srv.close();
        resolve({ raw, parsed: res.headers["set-cookie"] });
      }).on("error", reject);
    });
  });
}

function sessionCookies(list) {
  return list.filter((c) => c.startsWith("dispatch_session="));
}
function tokenOf(list) {
  const re = /(?:^|,)\s*dispatch_session=([0-9a-f]{64})(?=;|,|$)/;
  for (const c of list) {
    const m = c.match(re);
    if (m) return m[1];
  }
  return null;
}
function hasJoinedSession(list) {
  return sessionCookies(list).some((c) => c.includes(",dispatch_session="));
}

(async () => {
  const tok = "ab".repeat(32);
  const cases = [
    { name: "harness (no Secure, established host-only)", secure: false, pin: false },
    { name: "production (Secure + Domain)", secure: true, pin: true },
  ];
  for (const c of cases) {
    const register = await capture((req, res) => {
      res.setHeader("Set-Cookie", sessionCookieHeader(tok, c.secure, c.pin));
    });
    const bug = await capture((req, res) => {
      res.setHeader("Set-Cookie", sessionCookieHeader(tok, c.secure, c.pin));
      const sessionCookie = res.getHeader("Set-Cookie");
      assert.ok(Array.isArray(sessionCookie), "getHeader after setSession must be an array");
      assert.strictEqual(sessionCookie.length, 3);
      res.setHeader("Set-Cookie", [sessionCookie, "dispatch_account_created=1; Path=/; SameSite=Lax; Max-Age=120"].filter(Boolean));
    });
    const fix = await capture((req, res) => {
      res.setHeader("Set-Cookie", sessionCookieHeader(tok, c.secure, c.pin));
      const sessionCookie = res.getHeader("Set-Cookie");
      res.setHeader("Set-Cookie", [].concat(sessionCookie || [], "dispatch_account_created=1; Path=/; SameSite=Lax; Max-Age=120").filter(Boolean));
    });
    assert.strictEqual(register.raw.length, 3, c.name + " register header count");
    assert.ok(!hasJoinedSession(register.raw), c.name + " register must be flat");
    assert.strictEqual(tokenOf(register.raw), tok);

    assert.strictEqual(bug.raw.length, 2, c.name + " bug header count");
    assert.ok(hasJoinedSession(bug.raw), c.name + " bug must comma-join the three session cookies");
    assert.ok(bug.raw.some((x) => x.startsWith("dispatch_account_created=1")), c.name + " bug still sends account_created");

    assert.strictEqual(fix.raw.length, 4, c.name + " fix header count");
    assert.ok(!hasJoinedSession(fix.raw), c.name + " fix must stay flat");
    assert.strictEqual(sessionCookies(fix.raw).length, 3);
    assert.strictEqual(tokenOf(fix.raw), tok);
    assert.ok(fix.raw.some((x) => x.startsWith("dispatch_account_created=1; Path=/; SameSite=Lax; Max-Age=120")));
    console.log("PASS", c.name, "register=3 flat, bug=2 joined, fix=4 flat");
  }
  console.log("ALLOK cookie_headers.js");
})().catch((e) => { console.error("FAIL", e); process.exit(1); });
