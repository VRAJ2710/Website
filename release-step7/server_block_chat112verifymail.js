// ===== chat112verifymail (release step 7, 27 Nov 2026): verification emails, ENFORCEMENT OFF. Replaces chat111verify. =====
// Sign-up hook (after the response has gone out, never delaying it): a NEW account from POST /__auth/register or
// /__auth/subscribe is set email_verified=FALSE (same rule as step 6) and, only when that UPDATE actually flips it, gets ONE
// verification email through the server's existing Resend wiring (Replit Resend connector, the same path and settings as
// password recovery: DISPATCH_RECOVERY_DELIVERY_PROVIDER=resend, DISPATCH_RECOVERY_EMAIL_FROM, DISPATCH_RECOVERY_DELIVERY_TIMEOUT_MS).
// Sending is fire-and-forget with a hard timeout; a failure or timeout writes one log line and nothing else.
// Routes (only these four exact paths; everything else falls through unchanged):
//   GET  /__auth/verify?token=...      one-time link (24 h): sets email_verified=TRUE, shows "Email confirmed" or a friendly page
//   POST /__auth/verify/resend         signed-in unverified users; same-origin; 1 per 5 min and 5 per 24 h per user
//   GET  /__auth/verify/status         {"show":true|false} for the reminder banner (guests and verified users: false)
//   GET  /__auth/verify/reminder.js    the small dismissible banner script
// Pages: for requests that carry a dispatch_session cookie only, HTML pages get one <script src="/__auth/verify/reminder.js">
// tag before </body>; the banner appears only if /status says the signed-in user is unverified. Guests get byte-identical pages.
// VERIFY_ENFORCE is false: nothing reads email_verified to block sign-in, /api/me, checkout or content.
// No schema change, no new env var or secret, no alert email, no other email. Uses existing tables only.
;(function () {
  var TAG = "chat112verifymail";
  var VERIFY_ENFORCE = false;
  var SIGNUP_PATHS = { "/__auth/register": 1, "/__auth/subscribe": 1 };
  var RESEND_GAP_MS = 5 * 60 * 1000, RESEND_DAY_MAX = 5, DAY_MS = 24 * 60 * 60 * 1000;
  var SKIP = /^\/(?:api|__auth|__v3p|__navy|admin|signin|signup|login|logout|register|account|checkout|billing|webhook|webhooks|stripe|auth|reset|verify)(?:[\/?#.]|$)/i;
  var crypto = require("crypto");
  var seen = {}, sends = new Map();
  function line(msg) { try { console.log("[" + TAG + "] " + msg); } catch (e) {} }
  function logOnce(key, msg) { if (seen[key]) return; seen[key] = 1; line(msg); }
  function errCode(e) { return String((e && (e.code || e.name)) || "error").replace(/[^A-Za-z0-9_]/g, "").slice(0, 32) || "error"; }
  function db() { try { return (typeof sql === "function" && sql && typeof tokenHash === "function") ? sql : null; } catch (e) { return null; } }
  // ---- sending (existing Resend connector wiring; off unless the server is configured exactly like production) ----
  function sender() {
    try {
      var prov = typeof RECOVERY_DELIVERY_PROVIDER === "string" ? RECOVERY_DELIVERY_PROVIDER : "";
      var from = typeof RECOVERY_EMAIL_FROM === "string" ? RECOVERY_EMAIL_FROM : "";
      var addr = from.replace(/^.*</, "").replace(/>.*$/, "").trim().toLowerCase();
      if (prov !== "resend" || !/^[^@\s<>]+@thedispatch\.uk$/.test(addr) || typeof ReplitConnectors !== "function") return null;
      var ms = Number(typeof RECOVERY_DELIVERY_TIMEOUT_MS === "number" ? RECOVERY_DELIVERY_TIMEOUT_MS : 5000);
      if (!(ms >= 500 && ms <= 15000)) ms = 5000;
      return { from: from, ms: ms };
    } catch (e) { return null; }
  }
  function publicOrigin() {
    try { var u = new URL(typeof ACCOUNT_PUBLIC_ORIGIN === "string" ? ACCOUNT_PUBLIC_ORIGIN : ""); if (u.protocol === "https:") return u.origin; } catch (e) {}
    return "https://thedispatch.uk";
  }
  function emailText(url) {
    return "Welcome to The Dispatch.\n\n" +
      "Please confirm your email address by opening this link:\n" + url + "\n\n" +
      "The link works once and expires in 24 hours. Your account already works; confirming simply tells us this address is yours.\n\n" +
      "If you did not create an account, you can ignore this email and nothing will happen.\n\n" +
      "The Dispatch\nhttps://thedispatch.uk";
  }
  function sendVerification(email, token, why) {
    var s = sender();
    if (!s) { logOnce("off", "email delivery is not configured on this server; verification email not sent"); return Promise.resolve(false); }
    var url = publicOrigin() + "/__auth/verify?token=" + token, timer = null;
    var call = Promise.resolve().then(function () {
      var connectors = new ReplitConnectors();
      return connectors.proxy("resend", "/emails", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: { from: s.from, to: [email], subject: "Confirm your email for The Dispatch", text: emailText(url) },
      });
    });
    var deadline = new Promise(function (_, reject) {
      timer = setTimeout(function () { reject({ code: "TIMEOUT" }); }, s.ms);
      if (timer && timer.unref) timer.unref();
    });
    return Promise.race([call, deadline]).then(function (r) {
      clearTimeout(timer);
      if (!r || !r.ok) { line("verification email not sent (" + why + "): provider status " + ((r && r.status) || "unknown")); return false; }
      return true;
    }, function (e) {
      clearTimeout(timer);
      line("verification email not sent (" + why + "): " + (e && e.code === "TIMEOUT" ? "timeout" : "transport_error"));
      return false;
    });
  }
  // ---- tokens and limits ----
  function issueToken(q, userId) {
    var token = crypto.randomBytes(32).toString("hex");
    return Promise.resolve(q`DELETE FROM dispatch_email_verifications WHERE user_id = ${userId}`).then(function () {
      return q`INSERT INTO dispatch_email_verifications (token_hash, user_id, expires_at) VALUES (${tokenHash(token)}, ${userId}, NOW() + INTERVAL '24 hours')`;
    }).then(function () { return token; });
  }
  function recent(userId, now) {
    var list = (sends.get(userId) || []).filter(function (t) { return now - t < DAY_MS; });
    if (list.length) sends.set(userId, list); else sends.delete(userId);
    return list;
  }
  function noteSend(userId) {
    var now = Date.now(), list = recent(userId, now); list.push(now); sends.set(userId, list);
    if (sends.size > 20000) { var first = sends.keys().next().value; sends.delete(first); }
  }
  function limited(userId) {
    var now = Date.now(), list = recent(userId, now);
    if (list.length >= RESEND_DAY_MAX) return Math.ceil((list[0] + DAY_MS - now) / 1000);
    if (list.length && now - list[list.length - 1] < RESEND_GAP_MS) return Math.ceil((list[list.length - 1] + RESEND_GAP_MS - now) / 1000);
    return 0;
  }
  // ---- sign-up hook ----
  function freshSessionToken(res) {
    var sc; try { sc = res.getHeader("set-cookie"); } catch (e) { return null; }
    var list = Array.isArray(sc) ? sc : (sc ? [sc] : []), tok = null, re = /(?:^|,)\s*dispatch_session=([0-9a-f]{64})(?=;|,|$)/g, m;
    for (var i = 0; i < list.length; i++) { var v = String(list[i] || ""); re.lastIndex = 0; while ((m = re.exec(v))) tok = m[1]; }
    return tok;
  }
  function onNewSignup(sessionToken) {
    var q = db();
    if (!q) return logOnce("nodb", "database helpers unavailable; sign-up left as is");
    Promise.resolve().then(function () {
      return q`UPDATE dispatch_users u SET email_verified = FALSE FROM dispatch_sessions s
        WHERE s.token_hash = ${tokenHash(sessionToken)} AND s.user_id = u.id AND u.email_verified = TRUE
          AND u.created_at > NOW() - INTERVAL '10 minutes' RETURNING u.id, u.email`;
    }).then(function (rows) {
      var r = rows && rows[0];
      if (!r || !r.id || !r.email) return;
      return issueToken(q, r.id).then(function (token) { noteSend(r.id); return sendVerification(r.email, token, "sign-up"); });
    }).catch(function (e) { line("verification step skipped after sign-up (" + errCode(e) + "); account unaffected"); });
  }
  // ---- helpers for the routes ----
  function signedInCookie(req) { return /(?:^|;\s*)dispatch_session=[^;\s]/.test(String((req.headers && req.headers.cookie) || "")); }
  function sendJson(res, status, obj) {
    var b = Buffer.from(JSON.stringify(obj), "utf8");
    res.writeHead(status, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", "Content-Length": b.length });
    res.end(b);
  }
  function sendPage(res, title, html) {
    try { res.setHeader("Referrer-Policy", "no-referrer"); res.setHeader("X-Robots-Tag", "noindex"); } catch (e) {}
    if (typeof page === "function") return page(res, title, html);
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" });
    res.end("<!doctype html><html><head><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>" + title + "</title></head><body><main>" + html + "</main></body></html>");
  }
  function userState(req) {  // -> Promise<{user, verified}|null>; any failure counts as "verified" so nothing is shown
    var q = db();
    if (!q || typeof currentUser !== "function" || !signedInCookie(req)) return Promise.resolve(null);
    return Promise.resolve(currentUser(req)).then(function (user) {
      if (!user || !user.id) return null;
      return Promise.resolve(q`SELECT email_verified FROM dispatch_users WHERE id = ${user.id} LIMIT 1`).then(function (rows) {
        return { user: user, verified: !(rows && rows[0] && rows[0].email_verified === false) };
      });
    }).catch(function (e) { logOnce("state:" + errCode(e), "status lookup failed (" + errCode(e) + "); showing nothing"); return null; });
  }
  var P_OK = "<h1>Email confirmed</h1><p>Thanks. Your email address is confirmed and your Dispatch account is all set.</p><a href='/'>Continue to The Dispatch</a>";
  var P_BAD = "<h1>This link has expired or was already used</h1><p>Your account works as normal. If you still need to confirm your email, sign in and use the reminder at the top of any page to get a new link.</p><a href='/'>Go to The Dispatch</a>";
  var P_ERR = "<h1>We couldn't confirm your email just now</h1><p>Your account works as normal. Please open the link again in a few minutes.</p><a href='/'>Go to The Dispatch</a>";
  function handleVerify(req, res, url) {
    var m = String(req.method || "GET").toUpperCase();
    if (m === "HEAD") { res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" }); return res.end(); }  // link scanners: never consume
    var token = String(url.searchParams.get("token") || "").trim().toLowerCase(), q = db();
    if (!/^[0-9a-f]{64}$/.test(token)) return sendPage(res, "Link expired · The Dispatch Market", P_BAD);
    if (!q) return sendPage(res, "Please try again · The Dispatch Market", P_ERR);
    var h = tokenHash(token);
    Promise.resolve(q`WITH claimed AS (DELETE FROM dispatch_email_verifications WHERE token_hash = ${h} AND expires_at > NOW() RETURNING user_id)
        UPDATE dispatch_users u SET email_verified = TRUE FROM claimed WHERE u.id = claimed.user_id RETURNING u.id`).then(function (rows) {
      if (rows && rows[0] && rows[0].id) { sends.delete(rows[0].id); return sendPage(res, "Email confirmed · The Dispatch Market", P_OK); }
      return Promise.resolve(q`DELETE FROM dispatch_email_verifications WHERE token_hash = ${h} AND expires_at <= NOW()`).catch(function () {}).then(function () {
        sendPage(res, "Link expired · The Dispatch Market", P_BAD);
      });
    }).catch(function (e) { line("verify link failed (" + errCode(e) + ")"); if (!res.headersSent) sendPage(res, "Please try again · The Dispatch Market", P_ERR); });
  }
  function handleResend(req, res) {
    try { req.resume(); } catch (e) {}
    var same = false; try { same = typeof sameOriginMutation === "function" && sameOriginMutation(req); } catch (e) { same = false; }
    if (!same) return sendJson(res, 403, { ok: false, status: "forbidden" });
    userState(req).then(function (st) {
      if (!st) return sendJson(res, 401, { ok: false, status: "signin" });
      if (st.verified) return sendJson(res, 200, { ok: true, status: "verified" });
      var wait = limited(st.user.id), q = db();
      if (wait > 0) return sendJson(res, 429, { ok: false, status: "rate_limited", retryAfterSeconds: wait });
      return Promise.resolve(q`SELECT 1 AS r FROM dispatch_email_verifications WHERE user_id = ${st.user.id} AND created_at > NOW() - INTERVAL '5 minutes' LIMIT 1`).then(function (rows) {
        if (rows && rows.length) return sendJson(res, 429, { ok: false, status: "rate_limited", retryAfterSeconds: 300 });
        noteSend(st.user.id);
        return issueToken(q, st.user.id).then(function (token) { return sendVerification(st.user.email, token, "resend"); }).then(function (ok) {
          sendJson(res, 200, { ok: !!ok, status: ok ? "sent" : "not_sent" });
        });
      });
    }).catch(function (e) { line("resend failed (" + errCode(e) + ")"); if (!res.headersSent) sendJson(res, 200, { ok: false, status: "not_sent" }); });
  }
  function handleStatus(req, res) {
    userState(req).then(function (st) { sendJson(res, 200, { show: !!(st && !st.verified) }); }, function () { sendJson(res, 200, { show: false }); });
  }
  var REMINDER_JS = "(function(){var K='c112vDismiss',S='c112vOk';try{if(Date.now()-(+localStorage.getItem(K)||0)<864e5)return;if(sessionStorage.getItem(S))return}catch(e){}" +
    "function go(){if(!window.fetch||document.getElementById('c112v'))return;fetch('/__auth/verify/status',{credentials:'same-origin',cache:'no-store'}).then(function(r){return r.ok?r.json():null}).then(function(j){" +
    "if(!j||!j.show){try{sessionStorage.setItem(S,'1')}catch(e){}return}if(document.getElementById('c112v'))return;" +
    "var st=document.createElement('style');st.textContent='#c112v{position:relative;z-index:60;display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:6px 12px;margin:0;padding:9px 44px 9px 14px;background:#1f3a5f;color:#fff;font:500 13px/1.4 Inter,system-ui,-apple-system,\"Segoe UI\",Arial,sans-serif;text-align:center;box-sizing:border-box;width:100%}#c112v button{font:inherit;cursor:pointer;border-radius:4px}#c112v .c112v-r{background:#fff;color:#1f3a5f;border:0;padding:4px 10px;font-weight:600}#c112v .c112v-x{position:absolute;right:8px;top:50%;transform:translateY(-50%);background:none;border:0;color:#fff;font-size:20px;line-height:1;padding:4px 8px}#c112v .c112v-m{opacity:.9}';" +
    "document.head.appendChild(st);var b=document.createElement('div');b.id='c112v';b.setAttribute('role','status');" +
    "b.innerHTML='<span class=\"c112v-t\">Please confirm your email. We sent you a link.</span><button type=\"button\" class=\"c112v-r\">Resend link</button><button type=\"button\" class=\"c112v-x\" aria-label=\"Dismiss\">\\u00d7</button>';" +
    "document.body.insertBefore(b,document.body.firstChild);var t=b.querySelector('.c112v-t'),r=b.querySelector('.c112v-r');" +
    "b.querySelector('.c112v-x').onclick=function(){try{localStorage.setItem(K,String(Date.now()))}catch(e){}b.parentNode&&b.parentNode.removeChild(b)};" +
    "r.onclick=function(){r.disabled=true;fetch('/__auth/verify/resend',{method:'POST',credentials:'same-origin'}).then(function(x){return x.json().catch(function(){return{}})}).then(function(d){" +
    "if(d.status==='verified'){b.parentNode&&b.parentNode.removeChild(b);return}t.textContent=d.status==='sent'?'A new link is on its way. Check your inbox.':d.status==='rate_limited'?'Link already sent. Please wait a few minutes before asking again.':'We could not send a link right now. Please try again later.';" +
    "r.style.display='none'})['catch'](function(){t.textContent='We could not send a link right now. Please try again later.';r.style.display='none'})}" +
    "})['catch'](function(){})}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',go);else go()})();\n";
  var REMINDER_TAG = "<script src=\"/__auth/verify/reminder.js?v=c112\" defer></script>";
  function wrapHtml(res) {  // only for signed-in requests: add the reminder script tag before </body>
    var chunks = [], mode = null, ended = false, w0 = res.write, e0 = res.end, wh0 = res.writeHead;
    function restore() { res.write = w0; res.end = e0; res.writeHead = wh0; }
    function decide() {
      if (mode) return mode;
      var ct = "", ce = null;
      try { ct = String(res.getHeader("content-type") || ""); ce = res.getHeader("content-encoding"); } catch (e) {}
      mode = (res.statusCode === 200 && /text\/html/i.test(ct) && !ce) ? "buf" : "pass";
      if (mode === "pass") restore();
      return mode;
    }
    function push(c, enc) {
      if (c == null) return;
      if (typeof c === "string") chunks.push(Buffer.from(c, typeof enc === "string" ? enc : "utf8"));
      else if (Buffer.isBuffer(c)) chunks.push(c); else if (c instanceof Uint8Array) chunks.push(Buffer.from(c));
    }
    res.writeHead = function (code, a, b) {
      var hdrs = (a && typeof a === "object") ? a : (b && typeof b === "object" ? b : null);
      if (typeof code === "number") res.statusCode = code;
      if (typeof a === "string") res.statusMessage = a;
      if (hdrs) {
        if (Array.isArray(hdrs)) { for (var i = 0; i + 1 < hdrs.length; i += 2) res.setHeader(hdrs[i], hdrs[i + 1]); }
        else Object.keys(hdrs).forEach(function (h) { res.setHeader(h, hdrs[h]); });
      }
      if (decide() === "pass") return wh0.call(res, res.statusCode);
      return res;
    };
    res.write = function (c, enc, cb) {
      if (decide() === "pass") return w0.apply(res, arguments);
      push(c, enc); if (typeof enc === "function") enc(); else if (typeof cb === "function") cb(); return true;
    };
    res.end = function (c, enc, cb) {
      if (ended) return res;
      if (decide() === "pass") { ended = true; return e0.apply(res, arguments); }
      ended = true;
      if (typeof c === "function") { cb = c; c = null; } else if (typeof enc === "function") { cb = enc; enc = null; }
      push(c, enc); restore();
      var body = Buffer.concat(chunks), fin = body;
      try {
        var s = body.toString("utf8"), i = s.lastIndexOf("</body>");
        if (i >= 0 && s.indexOf("/__auth/verify/reminder.js") < 0) {
          fin = Buffer.from(s.slice(0, i) + REMINDER_TAG + s.slice(i), "utf8");
          if (!res.headersSent) { try { res.setHeader("Cache-Control", "private, no-store"); } catch (eC) {} }
        }
      } catch (eT) { fin = body; logOnce("inject", "reminder tag skipped: " + errCode(eT)); }
      if (!res.headersSent) { try { res.setHeader("Content-Length", fin.length); } catch (eL) {} }
      return e0.call(res, fin, cb);
    };
  }
  try {
    if (VERIFY_ENFORCE) throw new Error("VERIFY_ENFORCE must stay false in release step 7");
    var http = require("http");
    var SP = http && http.Server && http.Server.prototype;
    if (!SP) throw new Error("http.Server not found");
    if (SP.emit && SP.emit.__chat112verifymail) return;
    if (!SP.emit || !SP.emit.__chat110navy) throw new Error("chat110navy is not attached; step 7 stays off");
    var emit0 = SP.emit;
    var emit = function (type, req, res) {
      if (type !== "request" || !req || !res) return emit0.apply(this, arguments);
      try {
        var u = String(req.url || ""), qi = u.indexOf("?"), path = qi < 0 ? u : u.slice(0, qi);
        var m = String(req.method || "GET").toUpperCase();
        if (path === "/__auth/verify" && (m === "GET" || m === "HEAD")) { handleVerify(req, res, new URL(u, "http://x")); return true; }
        if (path === "/__auth/verify/resend" && m === "POST") { handleResend(req, res); return true; }
        if (path === "/__auth/verify/status" && m === "GET") { handleStatus(req, res); return true; }
        if (path === "/__auth/verify/reminder.js" && (m === "GET" || m === "HEAD")) {
          var jb = Buffer.from(REMINDER_JS, "utf8");
          res.writeHead(200, { "Content-Type": "application/javascript; charset=utf-8", "Cache-Control": "public, max-age=300", "Content-Length": jb.length, "X-Content-Type-Options": "nosniff" });
          res.end(m === "HEAD" ? undefined : jb); return true;
        }
        if (m === "POST" && SIGNUP_PATHS[path] === 1) {
          res.once("finish", function () {
            try { if (res.statusCode === 302) { var t = freshSessionToken(res); if (t) onNewSignup(t); } }
            catch (eF) { logOnce("finish", "skipped after response: " + errCode(eF)); }
          });
        } else if (m === "GET" && signedInCookie(req) && !SKIP.test(path) && !/\.[a-z0-9]{1,8}$/i.test(path)) {
          wrapHtml(res);
        }
      } catch (eReq) { logOnce("req", "skipped: " + errCode(eReq)); }
      return emit0.apply(this, arguments);
    };
    Object.keys(emit0).forEach(function (k) { if (/^__/.test(k)) emit[k] = emit0[k]; });
    emit.__chat112verifymail = 1;
    SP.emit = emit;
    globalThis.__c112verify = { sends: sends };
    line("attached (enforcement off; verification emails " + (sender() ? "on" : "off: delivery not configured") + ")");
  } catch (e) {
    line("not attached: " + (e && e.message || e));
  }
})();
