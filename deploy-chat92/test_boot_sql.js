// PGlite (real Postgres engine, test-only) check of every boot UPDATE in the patched server.js (chat91 x2 + chat92).
// Usage: node test_boot_sql.js <seed-source server.js ...> -- <patched server.js>
const fs = require("fs"), vm = require("vm"), assert = require("assert");
const { PGlite } = require(process.env.PGLITE_PATH || "/tmp/pgl/node_modules/@electric-sql/pglite");
const sep = process.argv.indexOf("--"), seedFiles = process.argv.slice(2, sep), patched = process.argv[sep + 1];
function defs(file) {
  const t = fs.readFileSync(file, "utf8"), i = t.indexOf("const PUBLIC_ROUTE_DEFINITIONS = [");
  let d = 0, j = t.indexOf("[", i), e = -1;
  for (let k = j; k < t.length; k++) { const c = t[k]; if (c === "[") d++; else if (c === "]" && --d === 0) { e = k; break; } }
  return vm.runInNewContext("(" + t.slice(j, e + 1) + ")");
}
const src = fs.readFileSync(patched, "utf8");
const sqls = [...src.matchAll(/await sql`(UPDATE dispatch_editorial_content[^`]*)`/g)].map(m => m[1]);
assert.strictEqual(sqls.length, 3, "expected 3 boot UPDATE statements"); sqls.forEach(q => assert.ok(!q.includes("\\"), "no backslash in SQL text"));
const NB = "\u00a0";
const POS = [ // [input, expected]
  ["THE DISPATCH MARKETS · GOLD & MACRO RESEARCH", "THE DISPATCH MARKET · GOLD & MACRO RESEARCH"],   // QA's eyebrow
  ["the dispatch markets desk", "the dispatch market desk"],
  ["The Dispatch" + NB + "Markets", "The Dispatch" + NB + "Market"],
  ["The Dispatch&nbsp;Markets", "The Dispatch&nbsp;Market"],
  ["The Dispatch&#160;MARKETS.", "The Dispatch&#160;MARKET."],
  ["The Dispatch\nMarkets", "The Dispatch\nMarket"],
  ["The Dispatch \t Markets", "The Dispatch \t Market"],
  ["Dispatch-Markets team", "Dispatch-Market team"],
  ["THE DISPATCH · MARKETS", "THE DISPATCH · MARKET"],
  ["The <em>Dispatch</em> Markets", "The <em>Dispatch</em> Market"],
  ["The Dispatch Markets, The DISPATCH markets and the dispatch Markets!", "The Dispatch Market, The DISPATCH market and the dispatch Market!"],
];
const NEG = ["/research/dispatch-markets-weekly/", "https://thedispatch-markets.com/x", "dispatchmarkets", "THE DISPATCH MARKETSX", "The Dispatch Market", "The Dispatch is for markets", "Dispatch Marketing", "nodispatch markets"];
(async () => {
  // A: synthetic rows
  {
    const db = new PGlite();
    await db.exec(`CREATE TABLE dispatch_editorial_content (id BIGSERIAL PRIMARY KEY, content_type TEXT NOT NULL, content_key TEXT NOT NULL, version INTEGER NOT NULL, status TEXT NOT NULL, payload JSONB NOT NULL, published_at TIMESTAMPTZ, updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), UNIQUE (content_type, content_key, version))`);
    let v = 0;
    for (const s of [...POS.map(x => x[0]), ...NEG]) await db.query("INSERT INTO dispatch_editorial_content (content_type,content_key,version,status,payload,published_at) VALUES ('page','home',$1,'published',$2::jsonb,NOW())", [++v, JSON.stringify({ title: "The Dispatch Market | Gold & Macro Research", eyebrow: s, sections: [{ heading: "h", copy: s }] })]);
    const before = (await db.query("SELECT id,version,status,published_at,updated_at FROM dispatch_editorial_content ORDER BY id")).rows;
    const counts = []; for (const q of sqls) counts.push((await db.query(q)).rows.length);
    const rows = (await db.query("SELECT id,version,status,published_at,updated_at,payload FROM dispatch_editorial_content ORDER BY id")).rows;
    POS.forEach(([inp, exp], i) => { assert.strictEqual(rows[i].payload.eyebrow, exp, "POS " + JSON.stringify(inp)); assert.strictEqual(rows[i].payload.sections[0].copy, exp); });
    NEG.forEach((inp, i) => assert.strictEqual(rows[POS.length + i].payload.eyebrow, inp, "NEG changed: " + inp));
    rows.forEach((r, i) => ["id","version","status","published_at","updated_at"].forEach(k => assert.deepStrictEqual(r[k], before[i][k], k)));
    const qa = /dispatch\W+markets/i, left = rows.filter((r, i) => i < POS.length && qa.test(JSON.stringify(r.payload)) && !/<em>/.test(r.payload.eyebrow));
    assert.strictEqual(left.length, 0, "QA regex still matches");
    const c2 = []; for (const q of sqls) c2.push((await db.query(q)).rows.length);
    assert.deepStrictEqual(c2, [0, 0, 0]);
    console.log(`synthetic: ${POS.length} positive variants fixed (case kept), ${NEG.length} negatives untouched; updates ${JSON.stringify(counts)}; 2nd run ${JSON.stringify(c2)}; metadata unchanged: OK`);
    await db.close();
  }
  // B: seed payloads from PUBLIC_ROUTE_DEFINITIONS (+ uppercase QA eyebrow on home)
  for (const f of seedFiles) {
    const routes = defs(f), db = new PGlite();
    await db.exec(`CREATE TABLE dispatch_editorial_content (id BIGSERIAL PRIMARY KEY, content_type TEXT NOT NULL, content_key TEXT NOT NULL, version INTEGER NOT NULL, status TEXT NOT NULL, payload JSONB NOT NULL, published_at TIMESTAMPTZ, updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), UNIQUE (content_type, content_key, version))`);
    for (const r of routes) {
      const p = { title: r.title, description: r.description, eyebrow: r.key === "home" ? "THE DISPATCH MARKETS · GOLD & MACRO RESEARCH" : r.eyebrow, h1: r.h1, intro: r.intro, sections: (r.sections || []).map(s => ({ heading: s[0], copy: s[1] })) };
      await db.query("INSERT INTO dispatch_editorial_content (content_type,content_key,version,status,payload,published_at) VALUES ('page',$1,1,'published',$2::jsonb,NOW())", [r.key, JSON.stringify(p)]);
    }
    const counts = []; for (const q of sqls) counts.push((await db.query(q)).rows.length);
    const rows = (await db.query("SELECT content_key,payload FROM dispatch_editorial_content ORDER BY id")).rows;
    rows.forEach(r => { const t = JSON.stringify(r.payload); assert.ok(!/dispatch\W+markets/i.test(t), "QA regex matches in " + r.content_key); assert.ok(!/[|·] The Dispatch"/.test(t)); });
    assert.strictEqual(rows.find(r => r.content_key === "home").payload.eyebrow, "THE DISPATCH MARKET · GOLD & MACRO RESEARCH");
    const c2 = []; for (const q of sqls) c2.push((await db.query(q)).rows.length);
    assert.deepStrictEqual(c2, [0, 0, 0]);
    console.log(`${f}: ${routes.length} seed pages; updates ${JSON.stringify(counts)}; after: 0 matches of /dispatch\\W+markets/i, home eyebrow 'THE DISPATCH MARKET · GOLD & MACRO RESEARCH'; 2nd run ${JSON.stringify(c2)}: OK`);
    await db.close();
  }
})().catch(e => { console.error("TEST FAIL", e.message); process.exit(1); });
