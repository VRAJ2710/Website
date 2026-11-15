// chat102r6b reader-facing scrub. Append-only. Symbol fields stay machine-readable.
(function () {
  var RX = /GC=F|DX-Y|\^TNX|=X\b|\^VIX|\^GSPC|CL=F|BTC-USD/;
  var SKIP = { symbol: 1, symbols: 1, id: 1, wire: 1 };

  function plain(s) {
    var t = String(s);
    t = t.replace(/Gold futures \(GC=F, delayed (\d+) min\)/g, "Gold futures (COMEX, front month), delayed $1 min");
    t = t.replace(/gold futures \(GC=F\)/g, "gold futures (COMEX, front month)");
    t = t.replace(/\(GC=F, delayed (\d+) min\)/g, "(COMEX, front month), delayed $1 min");
    t = t.replace(/\(GC=F\)/g, "(COMEX, front month)");
    t = t.replace(/\bGC=F\b/g, "COMEX gold futures, front month");
    t = t.replace(/Yahoo Finance \(\^TNX,\s*/g, "Yahoo Finance (");
    t = t.replace(/\(\^TNX,\s*/g, "(");
    t = t.replace(/\^TNX\b/g, "the US 10-year yield");
    t = t.replace(/Yahoo DX-Y\.NYB/g, "ICE");
    t = t.replace(/\bDX-Y\.NYB\b/g, "the ICE dollar index");
    t = t.replace(/\^VIX\b/g, "the VIX");
    t = t.replace(/\^GSPC\b/g, "the S&P 500");
    t = t.replace(/\bCL=F\b/g, "WTI crude futures");
    t = t.replace(/\bBTC-USD\b/g, "Bitcoin");
    t = t.replace(/\b([A-Z]{3})([A-Z]{3})=X\b/g, "$1/$2");
    t = t.replace(/\b([A-Z]{3})=X\b/g, "USD/$1");
    t = t.replace(/\(\s*,\s*/g, "(").replace(/\(\s*\)/g, "").replace(/ {2,}/g, " ").trim();
    return t;
  }
  function readerKey(key) {
    return /label|note|text|source|name|narrative|method|basis|title|summary|plain|kicker/i.test(String(key || ""));
  }
  function scrub(value, key) {
    if (typeof value === "string") {
      if (key && SKIP[key]) return value;
      if (readerKey(key)) return plain(value);
      return value;
    }
    if (Array.isArray(value)) return value.map(function (item) { return scrub(item, key); });
    if (!value || typeof value !== "object") return value;
    var out = {};
    Object.keys(value).forEach(function (k) { out[k] = scrub(value[k], k); });
    return out;
  }
  function quoteBody(body) {
    return !!(body && typeof body === "object" && !Array.isArray(body) && (body.XAU || body.US10Y || body.DXY));
  }
  if (typeof marketReferenceQuotesSWR === "function" && !marketReferenceQuotesSWR.__c102r6b) {
    var prevSwr = marketReferenceQuotesSWR;
    var swr = function () {
      return Promise.resolve(prevSwr.apply(this, arguments)).then(function (body) {
        return quoteBody(body) ? scrub(body) : body;
      });
    };
    swr.__c102r6b = 1;
    try { marketReferenceQuotesSWR = swr; } catch (e) {}
    try { globalThis.marketReferenceQuotesSWR = swr; } catch (e2) {}
  }
  if (typeof bb5gPublish === "function" && !bb5gPublish.__c102r6b) {
    var prevPub = bb5gPublish;
    var pub = function (data) {
      var out = prevPub.apply(this, arguments);
      if (quoteBody(out)) out = scrub(out);
      else if (quoteBody(data)) out = scrub(data);
      return out;
    };
    pub.__c102r6b = 1;
    try { bb5gPublish = pub; } catch (e3) {}
  }
  if (typeof json === "function" && !json.__c102r6b) {
    var prevJson = json;
    var wrapped = function (res, status, body, headers) {
      if (quoteBody(body)) body = scrub(body);
      return prevJson.call(this, res, status, body, headers);
    };
    wrapped.__c102r6b = 1;
    try { json = wrapped; } catch (e4) {}
  }
})();
