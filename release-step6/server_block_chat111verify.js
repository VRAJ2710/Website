// ===== chat111verify (release step 6, 27 Nov 2026): email_verified bookkeeping, ENFORCEMENT OFF =====
// What it does: after a NEW account is created by POST /__auth/register or POST /__auth/subscribe and the response has
// already been sent (302 with a fresh dispatch_session cookie), it sets dispatch_users.email_verified = FALSE for that
// one brand-new account (created in the last 10 minutes, found through the session it was just given).
// What it never does: it does not change any response, header, cookie, redirect or page; it does not read email_verified
// anywhere; it does not block sign-in, /api/me, checkout or content; it sends no email and makes no outbound HTTP call;
// it creates or alters no table (the column already exists in production: boolean DEFAULT true NOT NULL); it adds no route,
// env var or secret. Existing accounts stay TRUE (column default). Any database error is logged once and ignored.
// VERIFY_ENFORCE is a code constant and is false: release step 7 is where verification emails and any gate would come.
;(function () {
  var TAG = "chat111verify";
  var VERIFY_ENFORCE = false;
  var SIGNUP_PATHS = { "/__auth/register": 1, "/__auth/subscribe": 1 };
  var seen = {};
  function logOnce(key, msg) { if (seen[key]) return; seen[key] = 1; try { console.log("[" + TAG + "] " + msg); } catch (e) {} }
  function freshSessionToken(res) {
    var sc; try { sc = res.getHeader("set-cookie"); } catch (e) { return null; }
    // Set-Cookie may be a string, an array, or (Premium sign-up) an array holding an array, which Node joins with ","
    var list = Array.isArray(sc) ? sc : (sc ? [sc] : []), tok = null, re = /(?:^|,)\s*dispatch_session=([0-9a-f]{64})(?=;|,|$)/g, m;
    for (var i = 0; i < list.length; i++) {
      var v = String(list[i] || ""); re.lastIndex = 0;
      while ((m = re.exec(v))) tok = m[1];
    }
    return tok;
  }
  function markNewAccountUnverified(token) {
    var q, h;
    try { q = (typeof sql === "function") ? sql : null; h = (typeof tokenHash === "function") ? tokenHash : null; } catch (e) { q = null; }
    if (!q || !h) return logOnce("nodb", "database helpers unavailable; new accounts keep the default (verified)");
    Promise.resolve().then(function () {
      return q`UPDATE dispatch_users u SET email_verified = FALSE FROM dispatch_sessions s
        WHERE s.token_hash = ${h(token)} AND s.user_id = u.id AND u.email_verified = TRUE
          AND u.created_at > NOW() - INTERVAL '10 minutes'`;
    }).catch(function (e) {
      var code = (e && (e.code || e.name)) || "error";
      logOnce("err:" + code, "could not record unverified status (" + code + "); account unaffected");
    });
  }
  try {
    if (VERIFY_ENFORCE) throw new Error("VERIFY_ENFORCE must stay false in release step 6");
    var http = require("http");
    var SP = http && http.Server && http.Server.prototype;
    if (!SP) throw new Error("http.Server not found");
    if (SP.emit && SP.emit.__chat111verify) return;
    if (!SP.emit || !SP.emit.__chat110navy) throw new Error("chat110navy is not attached; step 6 stays off");
    var emit0 = SP.emit;
    var emit = function (type, req, res) {
      if (type === "request" && req && res && String(req.method || "").toUpperCase() === "POST") {
        try {
          var u = String(req.url || ""), qi = u.indexOf("?"), path = qi < 0 ? u : u.slice(0, qi);
          if (SIGNUP_PATHS[path] === 1) {
            res.once("finish", function () {
              try { if (res.statusCode === 302) { var t = freshSessionToken(res); if (t) markNewAccountUnverified(t); } }
              catch (eF) { logOnce("finish", "skipped after response: " + (eF && eF.message || eF)); }
            });
          }
        } catch (eReq) { logOnce("req", "skipped: " + (eReq && eReq.message || eReq)); }
      }
      return emit0.apply(this, arguments);
    };
    Object.keys(emit0).forEach(function (k) { if (/^__/.test(k)) emit[k] = emit0[k]; });
    emit.__chat111verify = 1;
    SP.emit = emit;
    console.log("[" + TAG + "] attached (enforcement off, no emails)");
  } catch (e) {
    console.log("[" + TAG + "] not attached: " + (e && e.message || e));
  }
})();
