"use strict";

const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");
const { RSS_FEED_URLS } = require("../rssFeeds");

const ROOT = path.join(__dirname, "..");
const APP = fs.readFileSync(path.join(ROOT, "app.js"), "utf8");

function sliceFn(src, name) {
  const marker = `async function ${name}(`;
  const start = src.indexOf(marker);
  assert.ok(start >= 0, `missing ${name}`);
  const next = src.indexOf("\nasync function ", start + marker.length);
  assert.ok(next > start, `${name} has no following function`);
  return src.slice(start, next);
}

test("lumber uses a live Yahoo contract and DXY stays on the Yahoo tape", () => {
  assert.match(APP, /LUMBER:"LBR=F"/);
  assert.doesNotMatch(APP, /LBS=F/);
  assert.match(APP, /Lumber ETF proxy \(WOOD\)/);
  assert.doesNotMatch(APP, /!\["XAU","DXY"\]/);
  const prices = sliceFn(APP, "fetchLivePrices");
  assert.match(prices, /PRICE_PRIORITY\.filter\(tk=>YAHOO_SYMBOLS\[tk\]\)/);
});

test("a full lumber chunk stays at 40 Yahoo symbols and applies LBR=F", () => {
  const fn = sliceFn(APP, "_fetchYahooPriceChunk");
  assert.match(fn, /slice\(i, i \+ 40\)/);
  assert.match(fn, /encodeURIComponent\("WOOD"\)/);
  assert.doesNotMatch(fn, /\?\s*\[primary,\s*"WOOD"\]/);
  const tickers = Array.from({ length: 39 }, (_, i) => `T${i}`);
  tickers.push("LUMBER");
  const map = Object.fromEntries(tickers.map(tk => [tk, tk === "LUMBER" ? "LBR=F" : tk]));
  const symbols = [...new Set(tickers.map(tk => map[tk] || tk).filter(Boolean))];
  assert.equal(symbols.length, 40);
  assert.equal(symbols.includes("LBR=F"), true);
  assert.equal(symbols.includes("WOOD"), false);
  for (let i = 0; i < symbols.length; i += 40) {
    assert.ok(symbols.slice(i, i + 40).length <= 40);
  }
  const payload = { "LBR=F": { p: 531, c: 0.4, prev: 529 }, WOOD: { p: 67.22, c: 0.1, prev: 67 } };
  const primary = payload["LBR=F"] || payload.LUMBER;
  assert.equal(primary.p, 531);
  assert.ok(primary.p > 0);
});

test("RSS_FEEDS literals carry allowlist ids f0..f25", () => {
  const start = APP.indexOf("const RSS_FEEDS = [");
  const end = APP.indexOf("const TAG_RULES", start);
  const block = APP.slice(start, end);
  const rows = [...block.matchAll(/\{id:"(f\d+)",url:"([^"]+)"/g)];
  assert.equal(rows.length, 26);
  rows.forEach((row, i) => {
    const id = `f${i}`;
    assert.equal(row[1], id);
    assert.equal(row[2], RSS_FEED_URLS[id]);
  });
  assert.match(block, /id:feed\.id\|\|`f\$\{id\}`/);
  assert.doesNotMatch(block, /id:`f\$\{id\}`\}\)/);
});

test("yahoo price chunks request wire symbols and keep a sibling when one chunk rejects", () => {
  const fn = sliceFn(APP, "_fetchYahooPriceChunk");
  assert.doesNotMatch(fn, /chunk\.join/);
  assert.match(fn, /YAHOO_SYMBOLS\[tk\] \|\| tk/);
  assert.match(fn, /yahooData\[yhSym\] \|\| yahooData\[tk\]/);
  assert.match(fn, /_applyLiveQuote\(tk, q, "yahoo"\)/);
  const prices = sliceFn(APP, "fetchLivePrices");
  assert.match(prices, /Promise\.allSettled\(pair\.map\(c=>_fetchYahooPriceChunk\(c\)\)\)/);
  assert.doesNotMatch(prices, /Promise\.all\(pair\.map\(c=>_fetchYahooPriceChunk\(c\)\)\)/);
});

test("apply script rewrites a production-shaped desk-ticker chunk", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "feed-bootstrap-"));
  const fixture = `const RSS_FEEDS = [
  {url:"https://feeds.bbci.co.uk/news/business/rss.xml",src:"BBC Business",tier:1,cat:"Macro"},
  {url:"https://www.cnbc.com/id/100003114/device/rss/rss.html",src:"CNBC",tier:1,cat:"Stocks"},
].map((feed,id)=>({...feed,id:\`f\${id}\`}));
const TAG_RULES = {};
async function _fetchYahooPriceChunk(chunk) {
  try {
    const res = await fetch(\`/api/yahoo-quote?symbols=\${encodeURIComponent(chunk.join(','))}\`, { signal: AbortSignal.timeout(12000) });
    const data = await res.json();
    let hits = 0;
    for (const tk of chunk) {
      if (data && data[tk] && _applyLiveQuote(tk, data[tk], 'yahoo')) hits++;
    }
    return hits;
  } catch {
    return 0;
  }
}
async function fetchTwelveDataPrices(){ return 0; }
async function _fetchLivePrices(){
  for(let i=0;i<chunks.length;i+=2){
    const pair=chunks.slice(i,i+2);
    const results=await Promise.all(pair.map(c=>_fetchYahooPriceChunk(c)));
    successCount+=results.reduce((a,b)=>a+b,0);
  }
}
async function after(){}
`;
  fs.writeFileSync(path.join(dir, "app.js"), fixture);
  fs.writeFileSync(
    path.join(dir, "index.html"),
    `<script>var V='TD-pricefix5';</script>\n<script defer src="/app.js?v=pricefix5"></script>\n`,
  );
  const script = path.join(ROOT, "scripts", "apply_feed_bootstrap_replit.py");
  const run = spawnSync("python3", [script, dir], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr || run.stdout);
  const out = fs.readFileSync(path.join(dir, "app.js"), "utf8");
  const fn = sliceFn(out, "_fetchYahooPriceChunk");
  assert.doesNotMatch(fn, /chunk\.join/);
  assert.match(fn, /batch\.join/);
  assert.match(fn, /i \+ 40/);
  assert.match(fn, /const yhSym = YAHOO_SYMBOLS\[tk\] \|\| tk/);
  assert.match(fn, /data\[yhSym\] \|\| data\[tk\]/);
  assert.match(fn, /_applyLiveQuote\(tk, q, "yahoo"\)/);
  assert.match(out, /Promise\.allSettled\(pair\.map\(c=>_fetchYahooPriceChunk\(c\)\)\)/);
  assert.doesNotMatch(out, /Promise\.all\(pair\.map\(c=>_fetchYahooPriceChunk/);
  assert.match(out, /\{id:"f0",url:"https:\/\/feeds\.bbci\.co\.uk\/news\/business\/rss\.xml"/);
  assert.match(out, /\{id:"f1",url:"https:\/\/www\.cnbc\.com\/id\/100003114\/device\/rss\/rss\.html"/);
  assert.match(out, /id:feed\.id\|\|`f\$\{id\}`/);
  const html = fs.readFileSync(path.join(dir, "index.html"), "utf8");
  assert.match(html, /app\.js\?v=pricefix9/);
  assert.match(html, /var V='TD-pricefix9'/);
  const again = spawnSync("python3", [script, dir], { encoding: "utf8" });
  assert.equal(again.status, 0, again.stderr || again.stdout);
  assert.equal(fs.readFileSync(path.join(dir, "app.js"), "utf8"), out);
});

test("apply script patches the live pricefix7 chunk, DXY exclusion, and RSS redirect refusal", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "feed-pricefix7-"));
  fs.writeFileSync(path.join(dir, "app.js"), `const RSS_FEEDS = [
  {id:"f0",url:"https://feeds.bbci.co.uk/news/business/rss.xml",src:"BBC Business",tier:1,cat:"Macro"},
].map((feed,id)=>({...feed,id:feed.id||\`f\${id}\`}));
const TAG_RULES = {};
LUMBER:"LBS=F",
async function _fetchYahooPriceChunk(chunk) {
 try {
  const wire=(chunk||[]).flatMap(tk=>{const primary=(typeof YAHOO_SYMBOLS!=="undefined"&&YAHOO_SYMBOLS[tk])?YAHOO_SYMBOLS[tk]:tk;return tk==="LUMBER"?[primary,"WOOD"]:[primary];});
  const res=await fetch(\`/api/yahoo-quote?symbols=\${encodeURIComponent(wire.join(','))}\`,{signal:AbortSignal.timeout(12000)});
  if(!res.ok){await _fetchFinnhubPriceFallback(chunk);return 0}
  const data=await res.json();let hits=0;
  for(const tk of chunk){const ysym=(typeof YAHOO_SYMBOLS!=="undefined"&&YAHOO_SYMBOLS[tk])?YAHOO_SYMBOLS[tk]:tk;const primary=data&&(data[ysym]||data[tk]);const lumberEtf=tk==="LUMBER"&&!(primary&&primary.p>0)&&data&&data.WOOD&&data.WOOD.p>0?{...data.WOOD,name:data.WOOD.name||"Lumber ETF proxy (WOOD)"}:null;const q=(primary&&primary.p>0)?primary:lumberEtf;if(q&&_applyLiveQuote(tk,q,'yahoo'))hits++}
  if(!hits)hits+=await _fetchFinnhubPriceFallback(chunk);return hits;
 }catch{return await _fetchFinnhubPriceFallback(chunk)}
}
async function fetchTwelveDataPrices(){ return 0; }
async function _fetchLivePrices(){
  const priHits=await _fetchYahooPriceChunk(PRICE_PRIORITY.filter(tk=>YAHOO_SYMBOLS[tk]&&!["XAU","DXY"].includes(tk)));
  const restTickers=Object.keys(YAHOO_SYMBOLS).filter(tk=>!PRICE_PRIORITY.includes(tk)&&!["XAU","DXY"].includes(tk));
  const results=await Promise.allSettled(pair.map(c=>_fetchYahooPriceChunk(c)));
}
function referencePx(tk) {
  const meta = _quoteMeta(tk);
  const p = P[tk]?.p;
  const retained = true;
  if (!retained || (!["live", "proxy"].includes(meta.status) || (meta.proxy && ["cached", "stale", "delayed", "proxy"].includes(meta.status)))) return null;
  return p;
}
_frontDoorQuote("DXY", "DOLLAR", "synthetic proxy");
async function after(){}
`);
  fs.writeFileSync(path.join(dir, "server.js"), `const { approvedRssFeedUrl } = require("./rssFeeds");
async function rssFeed(){
  if (symbols.length > 40) return json(res, 400, { error: "Too many Yahoo symbols requested." });
  try {
    const response = await fetch(feedUrl, {
      headers: { "User-Agent": "DispatchMarkets/1.0" },
      redirect: "error",
      signal: AbortSignal.timeout(8_000),
    });
    if (!response.ok) throw new Error(\`RSS \${response.status}\`);
    const body = await readTextCapped(response, 512 * 1024);
    return body;
  } catch {
    return "";
  }
}
`);
  const script = path.join(ROOT, "scripts", "apply_feed_bootstrap_replit.py");
  const run = spawnSync("python3", [script, dir], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr || run.stdout);
  const out = fs.readFileSync(path.join(dir, "app.js"), "utf8");
  assert.doesNotMatch(out, /LBS=F/);
  assert.match(out, /LUMBER:"LBR=F"/);
  assert.match(out, /Lumber ETF proxy \(WOOD\)/);
  assert.match(out, /encodeURIComponent\("WOOD"\)/);
  assert.match(out, /i \+ 40/);
  assert.doesNotMatch(out, /\?\[primary,"WOOD"\]/);
  assert.match(out, /data\[yhSym\] \|\| data\[tk\]/);
  assert.doesNotMatch(out, /!\["XAU","DXY"\]/);
  assert.match(out, /tk!=="XAU"/);
  assert.match(out, /meta\.status === "stale"/);
  assert.match(out, /ICE index/);
  const server = fs.readFileSync(path.join(dir, "server.js"), "utf8");
  assert.match(server, /fetchRssDocument\(feedUrl/);
  assert.doesNotMatch(server, /redirect:\s*"error"/);
  assert.doesNotMatch(server, /Too many Yahoo symbols requested/);
  assert.equal(fs.existsSync(path.join(dir, "rssFetch.js")), true);
});
