// TEST ONLY: neon()-compatible tagged-template over an in-process PGlite (real Postgres 17 in WASM).
const { PGlite } = require("/workspace/c113/pgl/node_modules/@electric-sql/pglite");
const crypto = require("crypto");
const db = new PGlite();
function neon() {
  return function sql(strings, ...vals) {
    let text = strings[0]; for (let i = 0; i < vals.length; i++) text += "$" + (i + 1) + strings[i + 1];
    return db.query(text, vals).then(r => r.rows);
  };
}
// production schema (already in prod): dispatch_users.email_verified + dispatch_email_verifications. TEST DB SETUP ONLY.
async function testSchema(sql) {
  if (process.env.TEST_NO_COLUMN) return;
  await sql`ALTER TABLE dispatch_users ADD COLUMN IF NOT EXISTS email_verified boolean DEFAULT true NOT NULL`;
  if (process.env.TEST_NO_VTABLE) return;
  await sql`CREATE TABLE IF NOT EXISTS dispatch_email_verifications (
    token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL UNIQUE REFERENCES dispatch_users(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())`;
}
function testUsers(sql) { return sql`SELECT id, email, tier, email_verified, created_at FROM dispatch_users ORDER BY created_at`; }
async function testRoute(sql, p, q, tokenHash) {
  const email = q.get("email") || "";
  const u = (await sql`SELECT id FROM dispatch_users WHERE email=${email}`)[0];
  if (p === "/__testdb/verifications") return await sql`SELECT v.user_id, u.email, v.expires_at, v.created_at FROM dispatch_email_verifications v JOIN dispatch_users u ON u.id=v.user_id ORDER BY u.email`;
  if (!u) return { error: "no user" };
  if (p === "/__testdb/expire") { await sql`UPDATE dispatch_email_verifications SET expires_at = NOW() - INTERVAL '1 minute' WHERE user_id=${u.id}`; return { ok: true }; }
  if (p === "/__testdb/age") {  // shift this user's send history back N minutes (DB row + the block's in-memory limiter)
    const min = Number(q.get("min") || 6);
    await sql`UPDATE dispatch_email_verifications SET created_at = created_at - make_interval(mins => ${min}) WHERE user_id=${u.id}`;
    const m = globalThis.__c112verify && globalThis.__c112verify.sends;
    if (m && m.has(u.id)) m.set(u.id, m.get(u.id).map(t => t - min * 60000));
    return { ok: true, mem: m ? (m.get(u.id) || []).length : null };
  }
  if (p === "/__testdb/token") {
    const token = crypto.randomBytes(32).toString("hex");
    await sql`DELETE FROM dispatch_email_verifications WHERE user_id=${u.id}`;
    await sql`INSERT INTO dispatch_email_verifications (token_hash, user_id, expires_at) VALUES (${tokenHash(token)}, ${u.id}, NOW() + INTERVAL '24 hours')`;
    await sql`UPDATE dispatch_users SET email_verified = FALSE WHERE id=${u.id}`;
    return { token };
  }
  return { error: "unknown" };
}
module.exports = { neon, db, testSchema, testUsers, testRoute };
