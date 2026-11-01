
// ── chat95 ── Real-yield warm at boot, and a short cache in front of the desk and crypto quote routes.
// The limiter itself (yahooRateLimiter, 30 per minute per address) is unchanged. A repeat of the same request within
// 15 seconds is answered from the cache without counting against it, and if the limiter does refuse, the last good
// answer from the past 30 minutes is sent (marked served:"last-good") so a page never loses its own tiles to a 429.
(function c95Boot() {
  try {
    const t = setTimeout(() => {
      try {
        if (typeof RT53_RY === "object" && RT53_RY && !RT53_RY.v && !RT53_RY.p && typeof rt53RyFetch === "function") {
          RT53_RY.tryAt = Date.now();
          RT53_RY.p = rt53RyFetch().catch(e => { RT53_RY.reason = String(e && e.message || "error").replace(/[^\w .-]/g, "").slice(0, 80); }).finally(() => { RT53_RY.p = null; });
        }
      } catch (e) {}
    }, 3000);
    if (t && t.unref) t.unref();
  } catch (e) {}
})();
const C95_MC = new Map();
const C95_FRESH_MS = 15e3, C95_LASTGOOD_MS = 30 * 60e3, C95_MC_MAX = 200;
const c95Json0 = json;
json = function (res, status, body, extraHeaders) {
  try {
    const k = res && res.__c95k;
    if (k) {
      if (status === 200 && body && typeof body === "object" && !body.error) {
        if (C95_MC.size >= C95_MC_MAX && !C95_MC.has(k)) C95_MC.delete(C95_MC.keys().next().value);
        C95_MC.set(k, { at: Date.now(), body: JSON.stringify(body), headers: extraHeaders || {} });
      } else if (status === 429) {
        const hit = C95_MC.get(k);
        if (hit && Date.now() - hit.at < C95_LASTGOOD_MS) {
          let b = null; try { b = JSON.parse(hit.body); } catch (e) { b = null; }
          if (b && typeof b === "object" && !Array.isArray(b)) {
            b.served = "last-good"; b.servedReason = "rate limit"; b.servedFrom = new Date(hit.at).toISOString();
            return c95Json0(res, 200, b, hit.headers);
          }
        }
      }
    }
  } catch (e) {}
  return c95Json0.apply(this, arguments);
};
function c95Micro(orig, tag) {
  return async function c95MicroRoute(req, res, url) {
    let k = "";
    try {
      const u = url && url.searchParams ? url : new URL(req.url, "http://localhost");
      k = tag + "?" + Array.from(u.searchParams.entries()).sort((a, b) => a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0).map(p => p[0] + "=" + p[1]).join("&");
    } catch (e) { k = ""; }
    if (k && (req.method === "GET" || req.method === "HEAD")) {
      const hit = C95_MC.get(k);
      if (hit && Date.now() - hit.at < C95_FRESH_MS) {
        res.writeHead(200, Object.assign({ "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" }, SECURITY_HEADERS, hit.headers, { "X-Dispatch-Cache": "fresh" }));
        return res.end(req.method === "HEAD" ? undefined : hit.body);
      }
      res.__c95k = k;
    }
    return orig.apply(this, arguments);
  };
}
if (typeof bb10DeskRoute === "function") bb10DeskRoute = c95Micro(bb10DeskRoute, "desk");
if (typeof bb10bCryptoRoute === "function") bb10bCryptoRoute = c95Micro(bb10bCryptoRoute, "crypto");
// chat95 end
