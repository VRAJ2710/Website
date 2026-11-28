// ===== chat113cookie (release step 8, 28 Nov 2026): flatten the Premium sign-up Set-Cookie array =====
// The prefix change is one call site in POST /__auth/subscribe (after a NEW account and setSession):
// sessionCookie = res.getHeader("Set-Cookie") is already an array of three dispatch_session strings.
// Wrapping that array in another array made Node join the three cookies with commas into one Set-Cookie
// header, which browsers store as an empty session cookie. The prefix now uses [].concat so the
// headers stay flat and dispatch_account_created is appended. This block only logs that the release
// is attached. It does not change Stripe, the webhook, secrets, config, routes or pages.
;(function () {
  var TAG = "chat113cookie";
  try {
    var http = require("http");
    var SP = http && http.Server && http.Server.prototype;
    if (!SP) throw new Error("http.Server not found");
    if (SP.emit && SP.emit.__chat113cookie) return;
    if (!SP.emit || !SP.emit.__chat112verifymail) throw new Error("chat112verifymail is not attached; step 8 stays off");
    SP.emit.__chat113cookie = 1;
    console.log("[" + TAG + "] attached");
  } catch (e) {
    console.log("[" + TAG + "] not attached: " + (e && e.message || e));
  }
})();
