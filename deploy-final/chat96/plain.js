// chat95: plain names for market codes in reader-facing text (GC=F -> Gold futures (COMEX, front month)).
var C95_RX = /\^[A-Z][A-Z0-9]{1,8}\b|\bDX-Y\.NYB\b|\b[A-Z]{1,4}=F\b|\b[A-Z]{3}(?:[A-Z]{3})?=X\b|\b(?:BTC|ETH|SOL|XRP|DOGE|ADA|AVAX|LTC|DOT|LINK|BNB|MATIC|SHIB|TRX|BCH|XLM|USDT|USDC)-USD\b/g;
var C95_TEST = /\^[A-Z]|DX-Y\.NYB|=[FX]\b|-USD\b/;
var C95_F = { GC: ["Gold futures", "COMEX"], SI: ["Silver futures", "COMEX"], HG: ["Copper futures", "COMEX"], PL: ["Platinum futures", "NYMEX"], PA: ["Palladium futures", "NYMEX"],
  CL: ["WTI crude futures", "NYMEX"], BZ: ["Brent crude futures", "ICE"], NG: ["Natural gas futures", "NYMEX"], RB: ["Gasoline futures", "NYMEX"], HO: ["Heating oil futures", "NYMEX"],
  ZW: ["Wheat futures", "CBOT"], ZC: ["Corn futures", "CBOT"], ZS: ["Soybean futures", "CBOT"], KC: ["Coffee futures", "ICE"], SB: ["Sugar futures", "ICE"], CC: ["Cocoa futures", "ICE"],
  CT: ["Cotton futures", "ICE"], OJ: ["Orange juice futures", "ICE"], LBR: ["Lumber futures", "CME"], LE: ["Live cattle futures", "CME"], HE: ["Lean hog futures", "CME"],
  ES: ["S&P 500 futures", "CME"], NQ: ["Nasdaq 100 futures", "CME"], YM: ["Dow futures", "CBOT"], RTY: ["Russell 2000 futures", "CME"], ZN: ["US 10-year note futures", "CBOT"], ZB: ["US Treasury bond futures", "CBOT"] };
var C95_I = { TNX: ["US 10-year Treasury yield", "Cboe"], IRX: ["US 13-week bill yield", "Cboe"], FVX: ["US 5-year Treasury yield", "Cboe"], TYX: ["US 30-year Treasury yield", "Cboe"],
  VIX: ["VIX", "Cboe"], GSPC: ["S&P 500", ""], DJI: ["Dow Jones Industrial Average", ""], IXIC: ["Nasdaq Composite", ""], NDX: ["Nasdaq 100", ""], RUT: ["Russell 2000", ""],
  FTSE: ["FTSE 100", ""], FTMC: ["FTSE 250", ""], GDAXI: ["DAX", ""], FCHI: ["CAC 40", ""], STOXX50E: ["Euro Stoxx 50", ""], N225: ["Nikkei 225", ""], HSI: ["Hang Seng", ""],
  NSEI: ["Nifty 50", ""], BSESN: ["Sensex", ""], AXJO: ["S&P/ASX 200", ""], GSPTSE: ["S&P/TSX Composite", ""], KS11: ["Kospi", ""], SSEC: ["Shanghai Composite", ""] };
var C95_C = { BTC: "Bitcoin", ETH: "Ether", SOL: "Solana", XRP: "XRP", DOGE: "Dogecoin", ADA: "Cardano", AVAX: "Avalanche", LTC: "Litecoin", DOT: "Polkadot", LINK: "Chainlink", BNB: "BNB",
  MATIC: "Polygon", SHIB: "Shiba Inu", TRX: "Tron", BCH: "Bitcoin Cash", XLM: "Stellar", USDT: "Tether", USDC: "USD Coin" };
function c95Ent(c) { // [plain name, venue, futures?]
  var m;
  if (c === "DX-Y.NYB") return ["US Dollar Index", "ICE", 0];
  if ((m = /^\^([A-Z0-9]+)$/.exec(c))) return C95_I[m[1]] ? [C95_I[m[1]][0], C95_I[m[1]][1], 0] : ["index", "", 0];
  if ((m = /^([A-Z]+)=F$/.exec(c))) return C95_F[m[1]] ? [C95_F[m[1]][0], C95_F[m[1]][1], 1] : ["futures contract", "", 1];
  if ((m = /^([A-Z]{3})([A-Z]{3})=X$/.exec(c))) return [m[1] + "/" + m[2], "", 0];
  if ((m = /^([A-Z]{3})=X$/.exec(c))) return ["USD/" + m[1], "", 0];
  if ((m = /^([A-Z]+)-USD$/.exec(c))) return [(C95_C[m[1]] || m[1]) + " in US dollars", "", 0];
  return null;
}
function c95Plain(s) {
  s = String(s == null ? "" : s);
  if (!C95_TEST.test(s)) return s;
  var one = new RegExp(C95_RX.source);
  s = s.replace(/\bYahoo(?: Finance)?\s*\(\s*([^()]*?)\s*\)/g, function (m, inner) { return one.test(inner) && /^[\^A-Z0-9=.\- ,]+$/.test(inner) && !/[a-z]/.test(inner) ? "Yahoo Finance, delayed" : m; });
  s = s.replace(/(\s?)\(([^()]*)\)/g, function (m, sp, inner, off, all) {
    if (!one.test(inner)) return m;
    var pre = all.slice(Math.max(0, off - 48), off).toLowerCase(), before = (pre + " " + inner.replace(C95_RX, "")).toLowerCase(), out = [], seen = {};
    var add = function (t, plain) { t = String(t).trim(); var k = t.toLowerCase(); if (!t || seen[k] || ((plain ? pre : before).indexOf(k) >= 0 && /^(comex|nymex|ice|cboe|cbot|cme|yahoo|yahoo finance)$/.test(k))) return; seen[k] = 1; out.push(t); };
    inner.split(/\s*,\s*/).forEach(function (p) {
      var t = p.replace(/^Yahoo(?: Finance)?\s+(?=\^|[A-Z]{1,4}=F|DX-Y)/i, "").trim(), e = new RegExp("^(?:" + C95_RX.source + ")$").test(t) ? c95Ent(t) : null;
      if (e) { if (e[1]) add(e[1]); if (e[2]) add("front month"); if (!e[1] && !e[2] && before.indexOf(e[0].toLowerCase().split(" ")[0]) < 0) add(e[0]); return; }
      add(p.replace(C95_RX, function (c) { var x = c95Ent(c); return x ? x[0] : c; }), 1);
    });
    return out.length ? sp + "(" + out.join(", ") + ")" : "";
  });
  s = s.replace(new RegExp("\\bYahoo(?: Finance)? (?:" + C95_RX.source + ") (?=\\()", "g"), "Yahoo Finance ");
  s = s.replace(/\bYahoo(?: Finance)? (?=\^|[A-Z]{1,4}=F\b|DX-Y)/g, "Yahoo Finance ");
  s = s.replace(C95_RX, function (c, off, all) {
    var e = c95Ent(c); if (!e) return c;
    var before = all.slice(Math.max(0, off - 40), off), lb = before.toLowerCase(), nm = e[0];
    if (lb.replace(/\s+$/, "").slice(-nm.length) === nm.toLowerCase()) return e[2] ? "(" + (e[1] ? e[1] + ", " : "") + "front month)" : "";
    var mid = /[a-z,;:]\s*$/.test(before) && !/[.!?]\s*$/.test(before);
    if (mid && /^[A-Z][a-z]/.test(nm) && !/^(S&P|US|VIX|Dow|Nasdaq|FTSE|DAX|CAC|Euro|Nikkei|Hang|Nifty|Sensex|Kospi|Shanghai|Russell|Brent|WTI|Bitcoin|Ether|Solana|XRP|Dogecoin|Cardano|Tether|BNB)/.test(nm)) nm = nm.charAt(0).toLowerCase() + nm.slice(1);
    return nm;
  });
  return s.replace(/ {2,}/g, " ").replace(/ +([,.;:)])/g, "$1").replace(/\(\s*\)/g, "");
}
