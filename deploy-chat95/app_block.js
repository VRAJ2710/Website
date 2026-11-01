
// ── chat95: reader-facing text never shows raw market codes (GC=F, ^TNX, DX-Y.NYB, EURUSD=X, BTC-USD) ──
// A text-only pass over the page: values, attributes other than title and aria-label, inputs, scripts and styles are left alone.
@@PLAIN@@
function c95Src(line) { line = String(line || ""); return !line || /Yahoo Finance/.test(line) ? line : "Yahoo Finance, delayed \u00b7 " + line; }
(function c95_sanitize() {
  if (typeof document === "undefined" || typeof MutationObserver === "undefined") return;
  var SKIP = { SCRIPT: 1, STYLE: 1, TEXTAREA: 1, INPUT: 1, SELECT: 1, NOSCRIPT: 1 };
  window.__c95n = 0;
  var skip = function (el) { for (var e = el; e && e.nodeType === 1; e = e.parentNode) { if (SKIP[e.nodeName] || e.isContentEditable || (e.hasAttribute && e.hasAttribute("data-c95-raw"))) return true; } return false; };
  var fixText = function (t) { var v = t.nodeValue; if (!v || !C95_TEST.test(v) || skip(t.parentNode)) return; var w = c95Plain(v); if (w !== v) { t.nodeValue = w; window.__c95n++; } };
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
  var go = function () {
    try { walk(document.body); if (document.title && C95_TEST.test(document.title)) document.title = c95Plain(document.title); } catch (e) {}
    try { mo.observe(document.documentElement, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ["title", "aria-label"] }); } catch (e) {}
    try { var tt = document.querySelector("title"); if (tt) new MutationObserver(function () { if (C95_TEST.test(document.title)) document.title = c95Plain(document.title); }).observe(tt, { childList: true, characterData: true, subtree: true }); } catch (e) {}
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", go); else go();
})();
(function c95_css() { try { var st = document.createElement("style"); st.setAttribute("data-c95", ""); st.textContent = '.bb1-wait .bb1-pv{margin-top:5px;font:500 20px/1.15 var(--data,ui-monospace);color:var(--ink-3,#8b909a)}.bb1-wait .bb1-wmeta{margin-top:8px;color:var(--ink-3,#8b909a);font:400 10px/1.4 var(--data,ui-monospace)}.bb1-wait .bb1-why{opacity:.8}@media (prefers-reduced-motion:no-preference){.bb1-wait .bb1-pv{animation:c95p 1.6s ease-in-out infinite}@keyframes c95p{50%{opacity:.45}}}'; document.head.appendChild(st); } catch (e) {} })();
