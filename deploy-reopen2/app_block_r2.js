
// ── reopen2 (app): "Use your own AI key: coming soon" while the server has no BYOK master key (html.r2-nobyok);
// the dashboard shows last-known values with a calm "Updating…" instead of a greyed overlay. ──
function r2NoByok() { try { return document.documentElement.classList.contains("r2-nobyok"); } catch (e) { return false; } }
(function () {
  try {
    if (typeof _renderOnboardStep === "function") {
      var r0 = _renderOnboardStep;
      _renderOnboardStep = function () {
        var out = r0.apply(this, arguments);
        if (r2NoByok()) { try { var b = document.getElementById("onboardBody"); if (b) b.innerHTML = b.innerHTML.replace("Ask, our AI research assistant, on Premium or with your own AI key.", "Ask, our AI research assistant, on Premium. Use your own AI key: coming soon.").replace(/<li><strong>Your own AI key<\/strong>[^<]*<\/li>/, "<li><strong>Use your own AI key</strong> \u2014 coming soon</li>"); } catch (e) {} }
        return out;
      };
    }
    if (typeof c96KBody === "function") {
      var k0 = c96KBody;
      c96KBody = function () {
        var S = (typeof c96K !== "undefined" && c96K) ? c96K.st : null;
        if (S && !S.available && (S.code === "BYOK_UNAVAILABLE" || r2NoByok())) return '<div class="rt17-note"><strong>Use your own AI key: coming soon.</strong> Adding a key from an AI provider is not switched on yet.</div>';
        return k0.apply(this, arguments);
      };
    }
  } catch (e) {}
  try {
    var st = document.createElement("style"); st.id = "r2-app";
    st.textContent = ".gd-dash-cta{background:linear-gradient(135deg,rgba(31,58,95,.06),rgba(31,58,95,0)),var(--paper-2,transparent)!important}" +
      "html:not(.c97-dark) .gd-dash-cta{background:#fff linear-gradient(135deg,rgba(31,58,95,.07),rgba(31,58,95,0))!important}" +
      "html:not(.c97-dark) .dash-details{background:transparent!important}" +
      ".latency-strip{background:var(--paper-2,transparent)!important}" +
      ".spine-cell.spine-nosync{opacity:1!important}.spine-nosync{opacity:1!important}" +
      ".book-price-row{background:transparent!important}.c97-pvbar a{color:#fff!important;text-decoration:underline}";
    (document.head || document.documentElement).appendChild(st);
  } catch (e) {}
})();
