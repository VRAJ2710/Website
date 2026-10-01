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
  assert.match(fn, /yhSyms\.join/);
  assert.match(fn, /const yhSym = YAHOO_SYMBOLS\[tk\] \|\| tk/);
  assert.match(fn, /data\[yhSym\] \|\| data\[tk\]/);
  assert.match(fn, /_applyLiveQuote\(tk, q, "yahoo"\)/);
  assert.match(out, /Promise\.allSettled\(pair\.map\(c=>_fetchYahooPriceChunk\(c\)\)\)/);
  assert.doesNotMatch(out, /Promise\.all\(pair\.map\(c=>_fetchYahooPriceChunk/);
  assert.match(out, /\{id:"f0",url:"https:\/\/feeds\.bbci\.co\.uk\/news\/business\/rss\.xml"/);
  assert.match(out, /\{id:"f1",url:"https:\/\/www\.cnbc\.com\/id\/100003114\/device\/rss\/rss\.html"/);
  assert.match(out, /id:feed\.id\|\|`f\$\{id\}`/);
  const html = fs.readFileSync(path.join(dir, "index.html"), "utf8");
  assert.match(html, /app\.js\?v=pricefix7/);
  assert.match(html, /var V='TD-pricefix7'/);
  const again = spawnSync("python3", [script, dir], { encoding: "utf8" });
  assert.equal(again.status, 0, again.stderr || again.stdout);
  assert.equal(fs.readFileSync(path.join(dir, "app.js"), "utf8"), out);
});
