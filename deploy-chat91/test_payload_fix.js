// Unit/integration test of the chat91 boot SQL against a real Postgres engine (PGlite, test-only, not part of the deploy).
// Usage: node test_payload_fix.js <old-server.js ...> -- <patched-server.js>   (PGlite resolved from NODE_PATH or /tmp/pgl)
const fs = require("fs"), vm = require("vm"), assert = require("assert");
const { PGlite } = require(process.env.PGLITE_PATH || "/tmp/pgl/node_modules/@electric-sql/pglite");
const sep = process.argv.indexOf("--");
const seedFiles = process.argv.slice(2, sep), patched = process.argv[sep + 1];
function defs(file) {
  const t = fs.readFileSync(file, "utf8"), i = t.indexOf("const PUBLIC_ROUTE_DEFINITIONS = [");
  let d = 0, j = t.indexOf("[", i);
  for (let k = j; k < t.length; k++) { const c = t[k]; if (c === "[") d++; else if (c === "]" && --d === 0) { j = [j, k]; break; } }
  return vm.runInNewContext("(" + t.slice(j[0], j[1] + 1) + ")");
}
const src = fs.readFileSync(patched, "utf8");
const sqls = [...src.matchAll(/await sql`(UPDATE dispatch_editorial_content[^`]*)`/g)].map(m => m[1].replace(/ RETURNING id$/, "") + " RETURNING id");
assert.strictEqual(sqls.length, 2, "expected 2 boot UPDATE statements");
(async () => {
  for (const f of seedFiles) {
    const routes = defs(f);
    const db = new PGlite();
    await db.exec(`CREATE TABLE dispatch_editorial_content (id BIGSERIAL PRIMARY KEY, content_type TEXT NOT NULL, content_key TEXT NOT NULL, version INTEGER NOT NULL, status TEXT NOT NULL, payload JSONB NOT NULL, published_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), UNIQUE (content_type, content_key, version))`);
    for (const r of routes) {
      const p = { title: r.title, description: r.description, eyebrow: r.eyebrow, h1: r.h1, intro: r.intro, sections: (r.sections || []).map(s => ({ heading: s[0], copy: s[1] })) };
      await db.query("INSERT INTO dispatch_editorial_content (content_type,content_key,version,status,payload,published_at) VALUES ('page',$1,1,'published',$2::jsonb,NOW())", [r.key, JSON.stringify(p)]);
    }
    // extras: unrelated brief with old brand in body, a draft v2 page with admin-edited short suffix, a clean row, a non-string title
    await db.query("INSERT INTO dispatch_editorial_content (content_type,content_key,version,status,payload) VALUES ('brief','b1',1,'published',$1::jsonb),('page','home',2,'draft',$2::jsonb),('research','r1',1,'published',$3::jsonb),('report','x',1,'draft',$4::jsonb)",
      [JSON.stringify({ title: "Brief | The Dispatch Markets", body: "Welcome to The Dispatch Markets — “quotes” & é \\n" }),
       JSON.stringify({ title: "Home | The Dispatch", h1: "The Dispatch is not renamed in prose" }),
       JSON.stringify({ title: "R | The Dispatch Market", note: "already fine" }),
       JSON.stringify({ title: 42, n: "The Dispatch Markets" })]);
    const before = (await db.query("SELECT id,content_type,content_key,version,status,published_at,updated_at,payload FROM dispatch_editorial_content ORDER BY id")).rows;
    const nBrandBefore = before.filter(r => JSON.stringify(r.payload).includes("Dispatch Markets")).length;
    const counts = [];
    for (const q of sqls) counts.push((await db.query(q)).rows.length);
    const after = (await db.query("SELECT id,content_type,content_key,version,status,published_at,updated_at,payload FROM dispatch_editorial_content ORDER BY id")).rows;
    assert.strictEqual(after.length, before.length);
    after.forEach((a, i) => { const b = before[i]; for (const k of ["id","content_type","content_key","version","status","published_at","updated_at"]) assert.deepStrictEqual(a[k], b[k], k + " changed"); });
    const allText = after.map(r => JSON.stringify(r.payload)).join("\n");
    assert.ok(!allText.includes("Dispatch Markets"), "Dispatch Markets remains");
    const pageTitles = after.filter(r => r.content_type === "page").map(r => r.payload.title);
    pageTitles.forEach(t => assert.ok(/The Dispatch Market$/.test(t) || /^The Dispatch Market \|/.test(t), "title brand: " + t)); pageTitles.forEach(t => assert.ok(!/[|·] The Dispatch$/.test(t), "short suffix: " + t));
    assert.strictEqual(after.find(r => r.content_type === "page" && r.version === 2).payload.h1, "The Dispatch is not renamed in prose");
    assert.strictEqual(after.find(r => r.content_type === "brief").payload.body, "Welcome to The Dispatch Market — “quotes” & é \\n");
    assert.strictEqual(after.find(r => r.content_type === "report").payload.title, 42);
    // idempotent second run
    const c2 = []; for (const q of sqls) c2.push((await db.query(q)).rows.length);
    assert.deepStrictEqual(c2, [0, 0], "second run must touch 0 rows");
    console.log(`${f}: seed routes ${routes.length}; rows with 'Dispatch Markets' before ${nBrandBefore}; boot updates ${JSON.stringify(counts)}; after: 0 'Dispatch Markets', all ${pageTitles.length} page titles carry 'The Dispatch Market' (suffix, or home prefix) and none end '| The Dispatch'; 2nd run ${JSON.stringify(c2)}; metadata unchanged: OK`);
    await db.close();
  }
})().catch(e => { console.error("TEST FAIL", e.message); process.exit(1); });
