#!/usr/bin/env python3
"""
patch_rt17s.py — The Dispatch Markets: rt17 SERVER patch (server.js only).

Usage (Replit workspace root, next to server.js):
    python3 patch_rt17s.py --check      # dry run, writes nothing
    python3 patch_rt17s.py              # apply
    python3 patch_rt17s.py --dir PATH

Adds:
  1. Migration: dispatch_user_prefs (user_id TEXT PK -> dispatch_users ON DELETE CASCADE, prefs JSONB, updated_at).
  2. Helpers (before `function isAdminUser(user) {`): rt17SanitizePrefs (whitelist schema), rt17ReadJson (size-limited),
     rt17SameOriginJson, rt17ApplyChatHints, rt17AccountRoute.
  3. Routes (before the /api/me GET block):
       /api/ai-status       -> 401 signed-out / 403 non-admin (falls through to the existing handler for admins)
       GET/PUT /api/prefs   -> auth required; PUT same-origin JSON, <= 16 KB, sanitised
       GET /api/account/export
       POST /api/account/delete {confirm:"DELETE"} -> blocked for admins and for active Stripe subscriptions
  4. /api/chat: validated Ask hints (length brief|detailed, focus gold|macro|crypto|em) appended to the last user turn.
No new background work, no pollers, no new connections. No email sending.
Exact anchors with counts; aborts with nothing written on any mismatch; refuses a second run; CRLF safe;
node --check; tmp-then-rename.
"""
import argparse, os, shutil, subprocess, sys, tempfile

MARKER = "// ── rt17: per-account prefs, account export/delete, admin-only AI provider status ──"

BLOCK = r'''// ── rt17: per-account prefs, account export/delete, admin-only AI provider status ──
const RT17_PREFS_MAX_BYTES = 16 * 1024;
const RT17_ENUMS = {
  density: ["comfortable", "compact"],
  fontSize: ["s", "m", "l"],
  theme: ["dark"],
  askLength: ["brief", "detailed"],
  askFocus: ["gold", "macro", "crypto", "em"],
  panels: ["p1", "p2", "p3", "p4"],
};
function rt17Bool(v, d = false) { return typeof v === "boolean" ? v : d; }
function rt17Pick(v, list, d) { return list.includes(v) ? v : d; }
function rt17Ticker(v) { const t = String(v || "").trim().toUpperCase(); return /^[A-Z0-9.=^\-]{1,15}$/.test(t) ? t : null; }
function rt17Tz(v) {
  const t = String(v || "");
  if (!t || t.length > 64 || !/^[A-Za-z_\/+\-0-9]+$/.test(t)) return "Europe/London";
  try { new Intl.DateTimeFormat("en-GB", { timeZone: t }); return t; } catch { return "Europe/London"; }
}
/** Whitelist schema: unknown keys dropped, every value validated. */
function rt17SanitizePrefs(input) {
  const p = input && typeof input === "object" && !Array.isArray(input) ? input : {};
  const lay = p.layout && typeof p.layout === "object" ? p.layout : {};
  const mk = p.markets && typeof p.markets === "object" ? p.markets : {};
  const al = p.alerts && typeof p.alerts === "object" ? p.alerts : {};
  const di = p.display && typeof p.display === "object" ? p.display : {};
  const ak = p.ask && typeof p.ask === "object" ? p.ask : {};
  const nl = p.newsletter && typeof p.newsletter === "object" ? p.newsletter : {};
  const order = Array.isArray(lay.order) ? lay.order.filter(x => RT17_ENUMS.panels.includes(x)) : [];
  const fullOrder = [...new Set([...order, ...RT17_ENUMS.panels])];
  const vis = lay.vis && typeof lay.vis === "object" ? lay.vis : {};
  const wl = Array.isArray(mk.watchlist) ? [...new Set(mk.watchlist.map(rt17Ticker).filter(Boolean))].slice(0, 50) : null;
  const alerts = (Array.isArray(al.price) ? al.price : []).slice(0, 20).map(a => {
    const tk = rt17Ticker(a && a.tk);
    const px = Number(a && a.px);
    if (!tk || !Number.isFinite(px) || px <= 0 || px > 1e9) return null;
    const firedAt = Number(a.firedAt);
    return { tk, op: a.op === "below" ? "below" : "above", px, on: rt17Bool(a.on, true), ...(Number.isFinite(firedAt) && firedAt > 0 ? { firedAt } : {}) };
  }).filter(Boolean);
  return {
    v: 1,
    layout: {
      order: fullOrder,
      vis: Object.fromEntries(RT17_ENUMS.panels.map(id => [id, rt17Bool(vis[id], true)])),
      density: rt17Pick(lay.density, RT17_ENUMS.density, "comfortable"),
    },
    markets: { ...(wl ? { watchlist: wl } : {}), tz: rt17Tz(mk.tz) },
    alerts: { price: alerts, dailyBrief: rt17Bool(al.dailyBrief) },
    display: { theme: "dark", fontSize: rt17Pick(di.fontSize, RT17_ENUMS.fontSize, "m"), reduceMotion: rt17Bool(di.reduceMotion) },
    ask: { length: rt17Pick(ak.length, RT17_ENUMS.askLength, "detailed"), focus: rt17Pick(ak.focus, RT17_ENUMS.askFocus, "macro") },
    newsletter: { daily: rt17Bool(nl.daily), weekly: rt17Bool(nl.weekly) },
  };
}
async function rt17ReadJson(req, maxBytes) {
  let size = 0; const chunks = [];
  for await (const c of req) {
    size += c.length;
    if (size > maxBytes) { const e = new Error("too large"); e.code = "RT17_TOO_LARGE"; throw e; }
    chunks.push(c);
  }
  const t = Buffer.concat(chunks).toString("utf8");
  if (!t) return {};
  try { return JSON.parse(t); } catch { const e = new Error("bad json"); e.code = "RT17_BAD_JSON"; throw e; }
}
/** State-changing calls must be same-origin JSON (blocks cross-site form posts). */
function rt17SameOriginJson(req) {
  const ct = String(req.headers["content-type"] || "").toLowerCase();
  if (!ct.startsWith("application/json")) return false;
  const origin = req.headers.origin;
  if (!origin) return true;
  try {
    const host = new URL(origin).host;
    const hosts = [req.headers.host, req.headers["x-forwarded-host"]].filter(Boolean).flatMap(h => String(h).split(",").map(s => s.trim()));
    return hosts.includes(host);
  } catch { return false; }
}
/** Ask/Expert hints: validated enums appended to the latest user turn (never free text). */
function rt17ApplyChatHints(body) {
  const h = body && body.hints && typeof body.hints === "object" ? body.hints : null;
  if (!h || !Array.isArray(body.messages) || !body.messages.length) return;
  const length = rt17Pick(h.length, RT17_ENUMS.askLength, null);
  const focus = rt17Pick(h.focus, RT17_ENUMS.askFocus, null);
  if (!length && !focus) return;
  const focusTxt = { gold: "gold", macro: "macro and rates", crypto: "crypto", em: "emerging markets" }[focus];
  const note = `\n\n[Reader preferences: ${length === "brief" ? "keep the answer brief (3-5 sentences)" : length === "detailed" ? "a detailed answer is welcome" : ""}${length && focus ? "; " : ""}${focus ? `where relevant, frame it for a reader focused on ${focusTxt}` : ""}.]`;
  for (let i = body.messages.length - 1; i >= 0; i--) {
    const m = body.messages[i];
    if (m && m.role === "user" && typeof m.content === "string") { m.content = m.content.slice(0, 7800) + note; break; }
  }
}
async function rt17AccountRoute(p, req, res) {
  const noStore = { "Cache-Control": "no-store" };
  const user = await currentUser(req);
  if (!user) return json(res, 401, { error: "Sign in required." }, noStore);
  try {
    if (p === "/api/prefs") {
      if (req.method === "GET") {
        const rows = await sql`SELECT prefs, updated_at FROM dispatch_user_prefs WHERE user_id=${user.id} LIMIT 1`;
        const row = rows[0];
        return json(res, 200, { prefs: row ? rt17SanitizePrefs(row.prefs) : null, updatedAt: row ? row.updated_at : null }, noStore);
      }
      if (req.method === "PUT") {
        if (!rt17SameOriginJson(req)) return json(res, 403, { error: "Same-origin JSON required." }, noStore);
        const body = await rt17ReadJson(req, RT17_PREFS_MAX_BYTES);
        const prefs = rt17SanitizePrefs(body && body.prefs);
        await sql`INSERT INTO dispatch_user_prefs (user_id, prefs, updated_at) VALUES (${user.id}, ${JSON.stringify(prefs)}::jsonb, NOW())
          ON CONFLICT (user_id) DO UPDATE SET prefs=EXCLUDED.prefs, updated_at=NOW()`;
        return json(res, 200, { ok: true, prefs }, noStore);
      }
      res.setHeader("Allow", "GET, PUT");
      return json(res, 405, { error: "Method not allowed." }, noStore);
    }
    if (p === "/api/account/export") {
      if (req.method !== "GET") { res.setHeader("Allow", "GET"); return json(res, 405, { error: "Method not allowed." }, noStore); }
      const rows = await sql`SELECT prefs, updated_at FROM dispatch_user_prefs WHERE user_id=${user.id} LIMIT 1`;
      const created = await sql`SELECT created_at FROM dispatch_users WHERE id=${user.id} LIMIT 1`;
      const out = {
        exportedAt: new Date().toISOString(),
        account: { email: user.email, plan: isAdminUser(user) ? "admin" : user.tier === "premium" ? "premium" : "free", createdAt: created[0] ? created[0].created_at : null, billingPortal: Boolean(user.billingPortal) },
        prefs: rows[0] ? rt17SanitizePrefs(rows[0].prefs) : null,
        prefsUpdatedAt: rows[0] ? rows[0].updated_at : null,
      };
      return json(res, 200, out, { ...noStore, "Content-Disposition": "attachment; filename=\"dispatch-my-data.json\"" });
    }
    if (p === "/api/account/delete") {
      if (req.method !== "POST") { res.setHeader("Allow", "POST"); return json(res, 405, { error: "Method not allowed." }, noStore); }
      if (!rt17SameOriginJson(req)) return json(res, 403, { error: "Same-origin JSON required." }, noStore);
      const body = await rt17ReadJson(req, 2048);
      if (!body || body.confirm !== "DELETE") return json(res, 400, { error: "Type DELETE to confirm." }, noStore);
      if (isAdminUser(user)) return json(res, 409, { error: "Administrator accounts can't be deleted from Settings.", code: "ADMIN" }, noStore);
      if (user.stripeCustomerId || user.stripeSubscriptionId || user.tier === "premium") {
        let active = user.tier === "premium";
        if (user.stripeCustomerId) {
          try {
            const stripe = await getUncachableStripeClient();
            if (!stripe) throw new Error("stripe unavailable");
            const subs = await stripe.subscriptions.list({ customer: user.stripeCustomerId, status: "all", limit: 100 });
            active = subs.data.some(s => ["active", "trialing", "past_due", "unpaid", "incomplete"].includes(s.status));
          } catch {
            return json(res, 503, { error: "We couldn't check your billing status just now. Nothing was deleted; please try again later.", code: "BILLING_UNKNOWN" }, noStore);
          }
        }
        if (active) return json(res, 409, { error: "Cancel your subscription first (Manage billing), then delete your account.", code: "BILLING_ACTIVE" }, noStore);
      }
      // User row first: if anything blocks it, nothing else has been removed. Sessions/prefs cascade; the extra deletes are belt and braces.
      await sql`DELETE FROM dispatch_users WHERE id=${user.id}`;
      await sql`DELETE FROM dispatch_sessions WHERE user_id=${user.id}`;
      await sql`DELETE FROM dispatch_user_prefs WHERE user_id=${user.id}`;
      res.setHeader("Set-Cookie", "dispatch_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax");
      return json(res, 200, { ok: true, deleted: true }, noStore);
    }
  } catch (error) {
    if (error && error.code === "RT17_TOO_LARGE") return json(res, 413, { error: "Settings are too large." }, noStore);
    if (error && error.code === "RT17_BAD_JSON") return json(res, 400, { error: "Invalid JSON." }, noStore);
    console.error("rt17 account route failed", error && error.message);
    return json(res, 500, { error: "Something went wrong. Nothing was changed." }, noStore);
  }
  return json(res, 404, { error: "Not found." }, noStore);
}

'''

ROUTES = r"""  // rt17 routes: account prefs / export / delete; AI provider status is admin-only.
  if (p === "/api/ai-status") {
    const rt17AiUser = await currentUser(req);
    if (!isAdminUser(rt17AiUser)) return json(res, rt17AiUser ? 403 : 401, { error: "Administrator access required." });
  }
  if (p === "/api/prefs" || p === "/api/account/export" || p === "/api/account/delete") return rt17AccountRoute(p, req, res);
"""

EDITS = [
    ("migration: dispatch_user_prefs",
     "await sql`CREATE TABLE IF NOT EXISTS dispatch_editorial_audit (",
     "await sql`CREATE TABLE IF NOT EXISTS dispatch_user_prefs (\n    user_id TEXT PRIMARY KEY REFERENCES dispatch_users(id) ON DELETE CASCADE,\n    prefs JSONB NOT NULL DEFAULT '{}'::jsonb, updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()\n  )`;\n  await sql`CREATE TABLE IF NOT EXISTS dispatch_editorial_audit ("),
    ("helpers before isAdminUser",
     "function isAdminUser(user) {",
     None),  # filled below
    ("routes before /api/me",
     'if (p === "/api/me" && req.method === "GET")',
     None),
    ("chat hints after AI-route body read",
     'const body = req.method === "POST" ? await readBody(req) : {};',
     'const body = req.method === "POST" ? await readBody(req) : {};\n    if (p === "/api/chat") rt17ApplyChatHints(body);'),
]
EDITS[1] = (EDITS[1][0], EDITS[1][1], BLOCK + "function isAdminUser(user) {")
EDITS[2] = (EDITS[2][0], EDITS[2][1], ROUTES + '  if (p === "/api/me" && req.method === "GET")')
REQUIRED = ["async function currentUser(req)", "function json(res, status, body", '"/api/ai-status"', "getUncachableStripeClient", "CREATE TABLE IF NOT EXISTS dispatch_users ("]


def load(path):
    with open(path, "rb") as f:
        raw = f.read().decode("utf-8")
    return raw.replace("\r\n", "\n"), "\r\n" in raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dir", default=".")
    a = ap.parse_args()
    sp = os.path.join(a.dir, "server.js")
    if not os.path.isfile(sp):
        sys.exit(f"ABORT: {sp} not found — nothing written")
    src, crlf = load(sp)
    if MARKER in src or "dispatch_user_prefs" in src or "rt17AccountRoute" in src:
        sys.exit("ABORT: rt17 server patch already applied — refusing to run twice; nothing written")
    errors = [f"required context missing: {r!r}" for r in REQUIRED if r not in src]
    # The admin gate must run before the existing /api/ai-status handler.
    me_i, ai_i = src.find('if (p === "/api/me" && req.method === "GET")'), src.find('p === "/api/ai-status"')
    if me_i < 0 or ai_i < 0 or ai_i < me_i:
        errors.append(f"route order: /api/me at {me_i}, /api/ai-status at {ai_i} (need /api/me first)")
    chat_i, body_i = src.find('"/api/chat"'), src.find('const body = req.method === "POST" ? await readBody(req) : {};')
    if body_i >= 0 and (chat_i < 0 or body_i < chat_i):
        errors.append("chat hint anchor is not inside the AI routes block")
    out = src
    for name, old, new in EDITS:
        n = out.count(old)
        if n != 1:
            errors.append(f"'{name}' anchor matched {n} times (need exactly 1)")
            continue
        out = out.replace(old, new)
    if not errors:
        node = shutil.which("node")
        if node:
            fd, tmp = tempfile.mkstemp(suffix=".js")
            try:
                with os.fdopen(fd, "wb") as f: f.write(out.encode("utf-8"))
                r = subprocess.run([node, "--check", tmp], capture_output=True, text=True, timeout=120)
                if r.returncode != 0: errors.append("node --check failed: " + (r.stderr or r.stdout)[:400])
            finally:
                os.remove(tmp)
        else:
            print("WARN: node not found; not syntax-checked")
    if errors:
        print("ABORT — nothing written:")
        for e in errors: print("  -", e)
        sys.exit(1)
    print(f"OK: {len(EDITS)} server.js edits verified ({len(out) - len(src):+d} chars)")
    if a.check:
        print("--check: dry run, nothing written"); return
    data = out.replace("\n", "\r\n") if crlf else out
    tmp = sp + ".rt17s.tmp"
    try:
        with open(tmp, "wb") as f: f.write(data.encode("utf-8"))
    except Exception as e:
        try: os.remove(tmp)
        except OSError: pass
        sys.exit(f"ABORT: could not stage output ({e}) — nothing written")
    os.replace(tmp, sp)
    print("Written: server.js")


if __name__ == "__main__":
    main()
