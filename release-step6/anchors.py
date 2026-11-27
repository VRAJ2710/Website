# shared anchor list: (bytes, expected count in the live server.js before step 6)
A = [
 (b'const sql = process.env.DATABASE_URL ? neon(process.env.DATABASE_URL) : null;', 1),
 (b'function tokenHash(token) {\n  return crypto.createHash("sha256").update(String(token || "")).digest("hex");\n}', 1),
 (b'async function setSession(req, res, user, oldToken = null) {', 1),
 (b'res.setHeader("Set-Cookie", sessionCookieHeader(token, req));', 1),
 (b'const established = [`dispatch_session=${token}`, ...cookieFlags(req)].join("; ");', 1),
 (b'if (p === "/__auth/register" && req.method === "POST") {', 1),
 (b'if (p === "/__auth/subscribe" && req.method === "POST") {', 1),
 (b'created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()\n  )`;\n  await sql`CREATE TABLE IF NOT EXISTS dispatch_sessions (', 1),
 (b'email_verified', 0), (b'emailVerified', 0), (b'issueEmailVerification', 0), (b'/__auth/verify', 0),
]
