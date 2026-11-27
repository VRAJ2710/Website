// TEST ONLY: neon()-compatible tagged-template over an in-process PGlite (real Postgres 17 in WASM).
const { PGlite } = require("/workspace/c113/pgl/node_modules/@electric-sql/pglite");
const db = new PGlite();
function neon() {
  return function sql(strings, ...vals) {
    let text = strings[0]; for (let i = 0; i < vals.length; i++) text += "$" + (i + 1) + strings[i + 1];
    return db.query(text, vals).then(r => r.rows);
  };
}
// production schema (already in prod): dispatch_users.email_verified boolean DEFAULT true NOT NULL
async function testSchema(sql) { if (process.env.TEST_NO_COLUMN) return; await sql`ALTER TABLE dispatch_users ADD COLUMN IF NOT EXISTS email_verified boolean DEFAULT true NOT NULL`; }
function testUsers(sql) { return sql`SELECT id, email, tier, email_verified, created_at FROM dispatch_users ORDER BY created_at`; }
module.exports = { neon, db, testSchema, testUsers };
