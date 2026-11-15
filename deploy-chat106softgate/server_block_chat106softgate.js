// chat106softgate: email verification is a reminder, not a gate (Vraj, 15 Nov 2026: "keep checkout open with a reminder until it works").
// Sign-up, sign-in and checkout are never blocked because email_verified is false. They are blocked only when
// VERIFY_ENFORCE below is true. This is a code constant: not an env var, not a secret, not config.
// The email_verified column, the verification emails (issueEmailVerification) and the Ask order are unchanged.
const VERIFY_ENFORCE = false;
const C106SG_RESEND_GAP_MS = 60 * 1000;
const c106sgLastResend = new Map();
function c106sgEsc(value) {
  return String(value == null ? "" : value).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function c106sgNeedsReminder(user) {
  return !!(user && user.id && user.emailVerified === false);
}
// Sends the existing verification email. Never throws, so sign-up and checkout always continue.
// Delivery failures are already logged once by reportRecoveryDeliveryFailure inside the existing send path;
// anything that throws (for example the token insert) is logged here, once, without the address.
async function c106sgSend(user, where) {
  try {
    return (await issueEmailVerification(user)) === true;
  } catch (error) {
    try { console.error(JSON.stringify({ event: "verification_email_failed", tag: "chat106softgate", where: String(where || ""), reason: "error" })); } catch {}
    return false;
  }
}
function c106sgReminderHtml(user) {
  if (VERIFY_ENFORCE || !c106sgNeedsReminder(user)) return "";
  // Colours follow the page theme (text inherits; amber tint and border read on light and dark auth pages).
  return `<div class="c106sg-reminder" role="status" style="border:1px solid #c9a227;background:rgba(201,162,39,.14);border-radius:6px;padding:12px 14px;margin:0 0 18px;font-size:14px;line-height:1.45;overflow-wrap:anywhere"><p style="margin:0"><strong>Please verify your email.</strong> We sent a confirmation link to ${c106sgEsc(user.email)}. Your account and checkout work while you wait.</p><form method="post" action="/__auth/verify/resend" style="margin:0"><button type="submit" style="margin-top:10px">Resend verification email</button></form></div>`;
}
const C106SG_MESSAGES = {
  sent: "We've sent a new confirmation link. Check your inbox and spam folder.",
  wait: "We've just sent one. Please wait a minute before asking again.",
  failed: "We couldn't send the email just now. Your account still works; please try again later.",
  verified: "Your email address is already verified.",
  signed_out: "Please sign in first.",
};
async function c106sgResendState(req) {
  let user = null;
  try { user = await currentUser(req); } catch { user = null; }
  if (!user || !user.id) return "signed_out";
  if (!c106sgNeedsReminder(user)) return "verified";
  const now = Date.now();
  if (now - (c106sgLastResend.get(user.id) || 0) < C106SG_RESEND_GAP_MS) return "wait";
  if (c106sgLastResend.size > 5000) c106sgLastResend.clear();
  c106sgLastResend.set(user.id, now);
  return (await c106sgSend(user, "resend")) ? "sent" : "failed";
}
// Browser script for the signed-in app pages (account/settings and the checkout hand-off). Shown only to a
// signed-in reader whose address is unverified. Dismissing hides it for the rest of the browser session.
function c106sgClient() {
  try {
    if (window.__c106sg) return;
    window.__c106sg = 1;
    var KEY = "c106sg-dismissed";
    try { if (window.sessionStorage && sessionStorage.getItem(KEY) === "1") return; } catch (e) {}
    var M = {
      sent: "We've sent a new confirmation link. Check your inbox and spam folder.",
      wait: "We've just sent one. Please wait a minute before asking again.",
      failed: "We couldn't send the email just now. Your account still works; please try again later.",
      verified: "Your email address is already verified.",
      signed_out: "Please sign in first."
    };
    var show = function () {
      if (document.getElementById("c106sg-reminder") || !document.body) return;
      var box = document.createElement("div");
      box.id = "c106sg-reminder";
      box.setAttribute("role", "status");
      var s = box.style;
      s.position = "fixed"; s.left = "12px"; s.right = "12px"; s.bottom = "calc(84px + env(safe-area-inset-bottom, 0px))";
      s.maxWidth = "520px"; s.margin = "0 auto"; s.zIndex = "2147483000"; s.boxSizing = "border-box";
      s.padding = "12px 44px 12px 14px"; s.borderRadius = "6px"; s.border = "1px solid #c9a227";
      s.background = "#fff8e1"; s.color = "#3d3420"; s.font = "14px/1.45 system-ui,-apple-system,'Segoe UI',Arial,sans-serif";
      s.boxShadow = "0 6px 24px rgba(0,0,0,.25)"; s.overflowWrap = "anywhere";
      var p = document.createElement("div");
      p.style.margin = "0"; p.style.color = "#3d3420";
      var strong = document.createElement("strong");
      strong.textContent = "Please verify your email."; strong.style.color = "#3d3420";
      p.appendChild(strong);
      p.appendChild(document.createTextNode(" We sent you a confirmation link. Your account and checkout work while you wait."));
      var msg = document.createElement("div");
      msg.style.margin = "6px 0 0"; msg.style.color = "#3d3420"; msg.setAttribute("aria-live", "polite");
      var btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Resend verification email";
      var b = btn.style;
      b.marginTop = "8px"; b.padding = "8px 12px"; b.border = "0"; b.borderRadius = "4px"; b.background = "#1f3a5f"; b.color = "#fff";
      b.font = "600 13px/1.2 system-ui,-apple-system,'Segoe UI',Arial,sans-serif"; b.cursor = "pointer"; b.minHeight = "36px";
      btn.onclick = function () {
        btn.disabled = true;
        fetch("/__auth/verify/resend", { method: "POST", credentials: "same-origin", cache: "no-store", headers: { Accept: "application/json", "Content-Type": "application/x-www-form-urlencoded" }, body: "" })
          .then(function (r) { return r.ok ? r.json() : { state: "failed" }; })
          .then(function (d) { var st = d && M[d.state] ? d.state : "failed"; msg.textContent = M[st]; if (st !== "sent") btn.disabled = false; })
          .catch(function () { msg.textContent = M.failed; btn.disabled = false; });
      };
      var x = document.createElement("button");
      x.type = "button"; x.textContent = "\u00d7"; x.setAttribute("aria-label", "Dismiss");
      var xs = x.style;
      xs.position = "absolute"; xs.top = "4px"; xs.right = "4px"; xs.width = "36px"; xs.height = "36px"; xs.border = "0";
      xs.background = "transparent"; xs.color = "#3d3420"; xs.font = "22px/1 system-ui,Arial,sans-serif"; xs.cursor = "pointer";
      x.onclick = function () { try { sessionStorage.setItem(KEY, "1"); } catch (e) {} if (box.parentNode) box.parentNode.removeChild(box); };
      box.appendChild(p); box.appendChild(btn); box.appendChild(msg); box.appendChild(x);
      document.body.appendChild(box);
    };
    fetch("/__auth/verify/status", { credentials: "same-origin", cache: "no-store", headers: { Accept: "application/json" } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d || d.reminder !== true) return;
        if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", show); else show();
      })
      .catch(function () {});
  } catch (e) {}
}
const C106SG_CLIENT_JS = "(" + c106sgClient.toString() + ")();\n";
const C106SG_TAG = '<script defer src="/__auth/verify/reminder.js?v=chat106softgate"></script>';
// The signed-in app pages are built from INDEX_TEMPLATE through withAssetVersion; add the reminder script there.
const c106sgBaseWithAssetVersion = withAssetVersion;
withAssetVersion = function (html) {
  const out = c106sgBaseWithAssetVersion(html);
  if (VERIFY_ENFORCE || typeof out !== "string" || out.indexOf("/__auth/verify/reminder.js") >= 0) return out;
  const at = out.lastIndexOf("</body>");
  return at < 0 ? out : out.slice(0, at) + C106SG_TAG + out.slice(at);
};
// Routes, called from handle() just before the existing /__auth/verify routes. Returns true when it answered.
async function c106sgRoute(p, req, res) {
  if (p === "/__auth/verify/reminder.js") {
    if (req.method !== "GET" && req.method !== "HEAD") { res.setHeader("Allow", "GET, HEAD"); text(res, 405, "Method not allowed."); return true; }
    res.writeHead(200, { "Content-Type": "application/javascript; charset=utf-8", "Cache-Control": "no-store", "Content-Length": Buffer.byteLength(C106SG_CLIENT_JS), "X-Content-Type-Options": "nosniff" });
    res.end(req.method === "HEAD" ? undefined : C106SG_CLIENT_JS);
    return true;
  }
  if (p === "/__auth/verify/status") {
    if (req.method !== "GET" && req.method !== "HEAD") { res.setHeader("Allow", "GET, HEAD"); json(res, 405, { error: "Method not allowed." }); return true; }
    let user = null;
    try { user = await currentUser(req); } catch { user = null; }
    res.setHeader("Cache-Control", "no-store");
    json(res, 200, { reminder: !VERIFY_ENFORCE && c106sgNeedsReminder(user) });
    return true;
  }
  if (p === "/__auth/verify/resend") {
    if (req.method !== "POST") { res.setHeader("Allow", "POST"); text(res, 405, "Method not allowed."); return true; }
    if (!sameOriginMutation(req)) { text(res, 403, "Cross-site requests are not allowed."); return true; }
    if (!allowAuthRequest(req, res)) return true;
    const raw = await readAuthForm(req, res); if (raw === null) return true;
    const state = await c106sgResendState(req);
    if (/application\/json/i.test(String(req.headers.accept || ""))) { res.setHeader("Cache-Control", "no-store"); json(res, 200, { state }); return true; }
    const back = state === "signed_out" ? "<a href='/__auth/login'>Sign in</a>" : "<a href='/'>Back to The Dispatch</a>";
    page(res, "Verify your email · The Dispatch Market", `<h1>Verify your email</h1><p>${c106sgEsc(C106SG_MESSAGES[state] || C106SG_MESSAGES.failed)}</p>${back}`);
    return true;
  }
  return false;
}
console.log("[chat106softgate] attached: verification reminder on; enforcement " + (VERIFY_ENFORCE ? "ON" : "off"));
