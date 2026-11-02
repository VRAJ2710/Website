
// ── chat96 (app): plain market names (from chat95, no source defaults), the BYOK section in Settings, Ask with the reader's key,
// /settings/ as its own page, brand-safe titles. ──
@@PLAIN@@
function c95Src(line) { return String(line || ""); } // chat96: no default source name; each line names its own feed
(function c95_sanitize() {
  if (typeof document === "undefined" || typeof MutationObserver === "undefined") return;
  var SKIP = { SCRIPT: 1, STYLE: 1, TEXTAREA: 1, INPUT: 1, SELECT: 1, NOSCRIPT: 1 };
  window.__c95n = 0;
  var skip = function (el) { for (var e = el; e && e.nodeType === 1; e = e.parentNode) { if (SKIP[e.nodeName] || e.isContentEditable || (e.hasAttribute && e.hasAttribute("data-c95-raw"))) return true; } return false; };
  var fixText = function (t) { var v = t.nodeValue; if (!v || skip(t.parentNode)) return; var w = v; if (C95_TEST.test(w)) w = c95Plain(w); if (/\bUNAVAILABLE\b/.test(w)) w = w.replace(/\bAI UNAVAILABLE\b/g, "AI unavailable").replace(/\bUNAVAILABLE\b/g, "Unavailable"); if (w !== v) { t.nodeValue = w; window.__c95n++; } };
  var fixAttr = function (el) { if (!el || el.nodeType !== 1 || skip(el)) return; ["title", "aria-label"].forEach(function (a) { var v = el.getAttribute(a); if (v && C95_TEST.test(v)) { var w = c95Plain(v); if (w !== v) { el.setAttribute(a, w); window.__c95n++; } } }); };
  var walk = function (root) {
    if (!root) return;
    if (root.nodeType === 3) return fixText(root);
    if (root.nodeType !== 1 || SKIP[root.nodeName]) return;
    fixAttr(root);
    var all = root.querySelectorAll ? root.querySelectorAll("[title],[aria-label]") : [];
    for (var i = 0; i < all.length; i++) fixAttr(all[i]);
    var tw = document.createTreeWalker(root, 4, null), n;
    while ((n = tw.nextNode())) fixText(n);
  };
  var mo = new MutationObserver(function (list) {
    for (var i = 0; i < list.length; i++) {
      var m = list[i];
      if (m.type === "characterData") fixText(m.target);
      else if (m.type === "attributes") fixAttr(m.target);
      else for (var j = 0; j < m.addedNodes.length; j++) walk(m.addedNodes[j]);
    }
  });
  var brand = function (t) { return c96Title(C95_TEST.test(t) ? c95Plain(t) : t); };
  var go = function () {
    try { walk(document.body); var t0 = brand(document.title); if (t0 !== document.title) document.title = t0; } catch (e) {}
    try { mo.observe(document.documentElement, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ["title", "aria-label"] }); } catch (e) {}
    try { var tt = document.querySelector("title"); if (tt) new MutationObserver(function () { var t = brand(document.title); if (t !== document.title) document.title = t; }).observe(tt, { childList: true, characterData: true, subtree: true }); } catch (e) {}
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", go); else go();
})();
function c96Title(t) { // one brand, never plural, never doubled
  t = String(t || "").replace(/\bDispatch Markets\b/g, "Dispatch Market").replace(/\bThe Dispatch\b(?! Market)/g, "The Dispatch Market").replace(/\bTHE DISPATCH\b(?! MARKET)/g, "THE DISPATCH MARKET");
  return t.replace(/(\s*[|\u00b7\u2014-]\s*The Dispatch Market)(?:\s*[|\u00b7\u2014-]\s*The Dispatch Market)+/g, "$1");
}
(function c95_css() { try { var st = document.createElement("style"); st.setAttribute("data-c96", ""); st.textContent = '.bb1-wait .bb1-pv{margin-top:5px;font:500 20px/1.15 var(--data,ui-monospace);color:var(--ink-3,#8b909a)}.bb1-wait .bb1-wmeta{margin-top:8px;color:var(--ink-3,#8b909a);font:400 10px/1.4 var(--data,ui-monospace)}.bb1-wait .bb1-why{opacity:.8}@media (prefers-reduced-motion:no-preference){.bb1-wait .bb1-pv{animation:c95p 1.6s ease-in-out infinite}@keyframes c95p{50%{opacity:.45}}}' +
  '.c96k-row{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;padding:8px 0;border-top:1px solid var(--b2,rgba(127,127,127,.2))}.c96k-row:first-child{border-top:0}.c96k-n{font-weight:600;min-width:120px}.c96k-m{font-size:12px;color:var(--t2,#777);flex:1 1 180px}.c96k-ok{color:#2e7d32}.c96k-bad{color:#c62828}.c96k-in{flex:1 1 220px;min-width:0;font:13px var(--mn,ui-monospace);padding:7px 8px}.c96k-msg{font-size:12px;margin-top:6px;min-height:1em}.c96-bl{font-size:11px;color:var(--t2,#777);margin:0 0 4px;letter-spacing:.02em}' +
  'html.c96-settings body>*:not(#settingsOv):not(script):not(style){visibility:hidden!important}html.c96-settings #settingsOv{background:var(--bg,#fbfaf7)!important}#settingsOv .rt17-btn-gold{color:#fff!important}.c96k-edit{flex-basis:100%;display:flex;gap:6px;flex-wrap:wrap}.c96k-edit[hidden]{display:none!important}'; document.head.appendChild(st); } catch (e) {} })();

// ── Your AI keys (every signed-in account). The key is sent once, on save, and never comes back: only provider, last 4 and dates. ──
var c96K = { st: null, csrf: "", busy: false, msg: "", err: false, loading: false };
function c96KEsc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
function c96KDate(s) { try { return new Date(s).toLocaleString("en-GB", { timeZone: "Europe/London", day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }) + " UK"; } catch (e) { return ""; } }
function c96KLoad() {
  if (c96K.loading) return; c96K.loading = true;
  fetch("/api/byok/keys", { credentials: "same-origin", cache: "no-store", headers: { Accept: "application/json" } }).then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { s: r.status, j: j }; }); })
    .then(function (x) { c96K.loading = false; c96K.st = x.j && typeof x.j === "object" ? x.j : {}; if (x.s !== 200) c96K.st.available = false; c96K.csrf = (x.j && x.j.csrf) || ""; c96KPaint(); })
    .catch(function () { c96K.loading = false; c96K.st = { available: false, error: "Your AI keys could not be loaded. Please try again." }; c96KPaint(); });
}
function c96KBody() {
  var S = c96K.st;
  if (!S) return '<div class="rt17-note">Loading your AI keys\u2026</div>';
  if (!S.available) return '<div class="rt17-note">Your AI keys are not available yet. ' + c96KEsc(S.error && S.code !== "BYOK_UNAVAILABLE" ? S.error : "") + '</div>';
  var have = {}; (S.keys || []).forEach(function (k) { have[k.provider] = k; });
  var rows = (S.providers || []).map(function (p) {
    var k = have[p.id], st = k ? ({ ok: '<span class="c96k-ok">OK</span>', invalid: '<span class="c96k-bad">Invalid key</span>', nocredit: '<span class="c96k-bad">No credit/permission</span>', error: '<span class="c96k-bad">Provider error</span>' }[k.status] || "Not tested") : "";
    return '<div class="c96k-row"><span class="c96k-n">' + c96KEsc(p.label) + '</span>' + (k
      ? '<span class="c96k-m">Key ending \u2026' + c96KEsc(k.last4) + ' \u00b7 added ' + c96KEsc(c96KDate(k.addedAt)) + ' \u00b7 ' + st + (k.checkedAt ? ' (' + c96KEsc(c96KDate(k.checkedAt)) + ')' : '') + '</span><button type="button" class="rt17-btn" data-c96k="test" data-p="' + p.id + '">Test</button><button type="button" class="rt17-btn" data-c96k="replace" data-p="' + p.id + '">Replace</button><button type="button" class="rt17-btn rt17-btn-danger" data-c96k="delete" data-p="' + p.id + '">Delete</button>'
      : '<span class="c96k-m">No key saved</span><button type="button" class="rt17-btn" data-c96k="replace" data-p="' + p.id + '">Add key</button>') +
      '<div class="c96k-edit" id="c96k-e-' + p.id + '" hidden><input class="c96k-in rt17-sel" type="password" id="c96k-i-' + p.id + '" autocomplete="off" spellcheck="false" maxlength="300" aria-label="' + c96KEsc(p.label) + ' API key" placeholder="Paste your ' + c96KEsc(p.label) + ' API key"><button type="button" class="rt17-btn" data-c96k="save" data-p="' + p.id + '">Save</button><button type="button" class="rt17-btn" data-c96k="cancel" data-p="' + p.id + '">Cancel</button></div></div>';
  }).join("");
  return '<div class="rt17-note">Use your own key from an AI provider for your Ask questions. Your provider bills you. We encrypt the key on our server, never show it again in full and never send it to your browser. Ask always says when it is using your key.</div>' + rows +
    '<div class="c96k-msg" id="c96k-msg" role="status" style="color:' + (c96K.err ? "#c62828" : "inherit") + '">' + c96KEsc(c96K.msg) + '</div>';
}
function c96KPaint() { var b = document.getElementById("c96k-body"); if (b) b.innerHTML = c96KBody(); }
function c96KSay(msg, err) { c96K.msg = msg || ""; c96K.err = !!err; var m = document.getElementById("c96k-msg"); if (m) { m.textContent = c96K.msg; m.style.color = err ? "#c62828" : "inherit"; } }
function c96KPost(path, body) {
  return fetch(path, { method: "POST", credentials: "same-origin", cache: "no-store", headers: { "Content-Type": "application/json", Accept: "application/json", "X-Dispatch-CSRF": c96K.csrf }, body: JSON.stringify(body) })
    .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { s: r.status, j: j }; }); });
}
document.addEventListener("click", function (ev) {
  var b = ev.target && ev.target.closest ? ev.target.closest("[data-c96k]") : null; if (!b || c96K.busy) return;
  var act = b.getAttribute("data-c96k"), p = b.getAttribute("data-p"), ed = document.getElementById("c96k-e-" + p), inp = document.getElementById("c96k-i-" + p);
  if (act === "replace") { if (ed) { ed.hidden = false; if (inp) inp.focus(); } return; }
  if (act === "cancel") { if (inp) inp.value = ""; if (ed) ed.hidden = true; return; }
  if (act === "delete" && !confirm("Delete your saved key for this provider? Ask will stop using it.")) return;
  var path = act === "save" ? "/api/byok/keys" : act === "test" ? "/api/byok/test" : "/api/byok/delete";
  var body = { provider: p }; if (act === "save") { body.key = inp ? inp.value.trim() : ""; if (!body.key) { c96KSay("Paste a key first.", true); return; } }
  c96K.busy = true; c96KSay(act === "test" ? "Testing with one small request\u2026" : act === "save" ? "Saving\u2026" : "Deleting\u2026", false);
  c96KPost(path, body).then(function (x) {
    c96K.busy = false; if (inp) inp.value = ""; body.key = "";
    if (x.j && x.j.keys) c96K.st.keys = x.j.keys;
    if (x.s === 200) { c96KPaint(); c96KSay(act === "test" ? "Test result: " + (x.j.resultText || x.j.result) : act === "save" ? "Saved. Use Test to check it works." : "Deleted.", act === "test" && x.j.result !== "ok"); }
    else { if (x.j && x.j.code === "CSRF") { c96K.st = null; c96KLoad(); } c96KSay((x.j && x.j.error) || "That didn't work. Please try again.", true); }
  }).catch(function () { c96K.busy = false; c96KSay("Network error. Nothing changed.", true); });
});
if (typeof _rt17Html === "function") {
  var c96H0 = _rt17Html;
  _rt17Html = function () {
    var h = c96H0.apply(this, arguments);
    try {
      var signed = typeof _rt17Signed === "function" && _rt17Signed();
      if (signed) { h = h.replace('<div class="rt17-foot">', _rt17Sec("c96keys", "Your AI keys", '<div id="c96k-body">' + c96KBody() + '</div>') + '<div class="rt17-foot">'); if (!c96K.st) setTimeout(c96KLoad, 0); }
    } catch (e) {}
    return h;
  };
}
// /settings/ is its own page: the desk behind is hidden while Settings is open there, and the tab title says Settings.
(function c96SettingsPage() {
  try {
    if (!(/^\/settings\/?$/.test(location.pathname) || /[?&]settings(=|&|$)/.test(location.search))) return;
    var de = document.documentElement; de.classList.add("c96-settings");
    var seen = false, t0 = Date.now();
    var tick = setInterval(function () {
      var ov = document.getElementById("settingsOv");
      if (ov) { seen = true; if (ov.parentNode !== document.body) de.classList.remove("c96-settings"); if (!/^Settings/.test(document.title)) document.title = "Settings | The Dispatch Market"; }
      if ((seen && !ov) || (!seen && Date.now() - t0 > 8000)) { de.classList.remove("c96-settings"); clearInterval(tick); }
    }, 150);
  } catch (e) {}
})();
// Ask: the reader's own key is labelled on every answer; a failure says why, and Premium readers can choose the site's AI instead.
if (typeof _bb2CommitJson === "function") {
  var c96Cj0 = _bb2CommitJson;
  _bb2CommitJson = function (data) {
    var r = c96Cj0.apply(this, arguments);
    try { if (data && data.byok && data.byok.label && _chatMsgs.length) { _chatMsgs[_chatMsgs.length - 1].byok = String(data.byok.label); if (typeof _persistChat === "function") _persistChat(); } } catch (e) {}
    return r;
  };
}
function c96ByokFailMsg(d) {
  _chatMsgs.push({ role: "assistant", kind: "c96-byok", content: String(d.error || "Your AI key couldn't be used."), byok: d.byok && d.byok.label ? String(d.byok.label) : "", offer: !!d.siteKeysOffer, retryable: true });
}
if (typeof _renderBotMsg === "function") {
  var c96Rb0 = _renderBotMsg;
  _renderBotMsg = function (m, idx) {
    if (m && m.byok && typeof m.byok === "object") m.byok = String(m.byok.label || "");
    if (m && m.kind === "c96-byok") return '<div class="chat-msg bot chat-retry-state is-unavailable" role="status"><div class="chat-retry-copy"><strong>' + c96KEsc(m.byok || "Your AI key") + '</strong><span>' + c96KEsc(m.content) + (m.offer ? " You can ask this one question with The Dispatch Market's AI instead." : " Free accounts don't switch to our AI.") + '</span></div>' +
      (m.offer ? '<button type="button" class="chat-retry-btn" onclick="c96UseSite(' + Number(idx) + ')">Use The Dispatch Market\'s AI for this question</button>' : '') + '<button type="button" class="chat-retry-btn" onclick="_chatRetry(' + Number(idx) + ')">Try again</button></div>';
    var h = c96Rb0.apply(this, arguments);
    return m && m.byok ? '<div class="c96-bl">' + c96KEsc(m.byok) + '</div>' + h : h;
  };
}
window.__c96site = false;
function c96UseSite(idx) { window.__c96site = true; Promise.resolve(_chatRetry(idx)).finally(function () { window.__c96site = false; }); }
(function c96FetchSite() {
  if (typeof window.fetch !== "function") return;
  var f0 = window.fetch;
  window.fetch = function (u, o) {
    try {
      if (window.__c96site && String(u && u.url || u).indexOf("/api/chat") >= 0) {
        o = Object.assign({}, o || {}); var h = new Headers(o.headers || {}); h.set("X-Dispatch-AI-Keys", "site"); o.headers = h;
      }
    } catch (e) {}
    return f0.call(this, u, o);
  };
})();
