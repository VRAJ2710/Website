#!/usr/bin/env python3
"""Emergency heal for The Dispatch server.js auth cookie helpers (no billingOrigin.js)."""
from __future__ import annotations
import re, shutil, subprocess, sys
from pathlib import Path

DELETE_PRESENTED = r"""
async function deletePresentedSessions(req, extraToken = null) {
  try {
    const header = req && req.headers ? req.headers.cookie : "";
    const tokens = new Set(dispatchSessionTokens(header));
    if (extraToken) tokens.add(extraToken);
    for (const token of tokens) {
      if (!token) continue;
      try {
        await sql`DELETE FROM dispatch_sessions WHERE token_hash=${tokenHash(token)}`;
      } catch (e) {
        console.error("deletePresentedSessions token", e && e.message);
      }
    }
  } catch (e) {
    console.error("deletePresentedSessions", e && e.message);
  }
}
""".lstrip()

FUNCTIONS = r"""
function hostnameOf(host) {
  return String(host || "").split(":")[0].trim().toLowerCase();
}
function requestHost(req) {
  const xf = req && req.headers && (req.headers["x-forwarded-host"] || req.headers.host);
  return Array.isArray(xf) ? xf[0] : xf;
}
function requestProtocol(req) {
  const xp = req && req.headers && req.headers["x-forwarded-proto"];
  if (xp) return String(Array.isArray(xp) ? xp[0] : xp).split(",")[0].trim().toLowerCase();
  return "https";
}
function isPublicDispatchHost(host) {
  return PUBLIC_HOSTS.has(hostnameOf(host));
}
function useSecureCookie(req) {
  const host = hostnameOf(requestHost(req));
  return requestProtocol(req) === "https" || isPublicDispatchHost(host) || host === REPLIT_PRODUCTION_HOST;
}
function shouldPinSessionDomain(req) {
  const host = hostnameOf(requestHost(req));
  return PUBLIC_HOSTS.has(host) || host === REPLIT_PRODUCTION_HOST;
}
function cookieFlags(req, { maxAge, clear = false, domain } = {}) {
  const parts = ["Path=/", "HttpOnly", "SameSite=Lax"];
  parts.push(clear ? "Max-Age=0" : `Max-Age=${maxAge ?? 2592000}`);
  if (useSecureCookie(req)) parts.push("Secure");
  const pinDomain = domain === undefined ? shouldPinSessionDomain(req) : Boolean(domain);
  if (pinDomain) parts.push(`Domain=${CANONICAL_HOST}`);
  return parts;
}
function clearSessionCookieHeader(req) {
  const hostOnly = ["dispatch_session=", ...cookieFlags(req, { clear: true, domain: false })].join("; ");
  const domainScoped = ["dispatch_session=", ...cookieFlags(req, { clear: true, domain: true })].join("; ");
  return [hostOnly, domainScoped];
}
function sessionCookieHeader(token, req) {
  const established = [`dispatch_session=${token}`, ...cookieFlags(req)].join("; ");
  return [...clearSessionCookieHeader(req), established];
}
function dispatchSessionTokens(cookieHeader) {
  const raw = Array.isArray(cookieHeader) ? cookieHeader.join("; ") : String(cookieHeader || "");
  const prefix = "dispatch_session=";
  const values = [];
  for (const part of raw.split(";")) {
    const trimmed = part.trim();
    if (!trimmed.startsWith(prefix)) continue;
    const encoded = trimmed.slice(prefix.length);
    if (!encoded) continue;
    try { values.push(decodeURIComponent(encoded)); } catch { values.push(encoded); }
    if (values.length >= 8) break;
  }
  return values;
}
""".lstrip()


def strip_fn(src: str, name: str) -> str:
    m = re.search(rf"^(?:async\s+)?function {re.escape(name)}\s*\(", src, flags=re.M)
    if not m:
        return src
    start = m.start()
    paren = m.end() - 1
    depth = 0
    params_end = None
    for i in range(paren, len(src)):
        if src[i] == "(":
            depth += 1
        elif src[i] == ")":
            depth -= 1
            if depth == 0:
                params_end = i
                break
    brace = src.find("{", params_end)
    depth = 0
    end = None
    for i in range(brace, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end is None:
        raise SystemExit(f"unclosed {name}")
    return src[:start] + src[end:].lstrip("\n")


def ensure_const(src: str, name: str, expr: str) -> str:
    if re.search(rf"^const {re.escape(name)}\s*=", src, flags=re.M):
        return src
    last = 0
    for m in re.finditer(r"^const .+ = require\(.+\);\n", src, flags=re.M):
        last = m.end()
    return src[:last] + f"const {name} = {expr};\n" + src[last:]


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    server = root / "server.js"
    if not server.exists():
        raise SystemExit("server.js not found")
    bak = server.with_name("server.js.bak-auth-emergency")
    text = server.read_text()
    if not bak.exists():
        shutil.copy2(server, bak)

    for name in [
        "clearSessionCookieHeader", "sessionCookieHeader", "cookieFlags", "shouldPinSessionDomain",
        "useSecureCookie", "dispatchSessionTokens", "deletePresentedSessions", "isPublicDispatchHost",
        "hostnameOf", "requestHost", "requestProtocol",
    ]:
        text = strip_fn(text, name)

    text = ensure_const(text, "CANONICAL_HOST", '"thedispatch.uk"')
    text = ensure_const(text, "CANONICAL_ORIGIN", '"https://thedispatch.uk"')
    text = ensure_const(text, "REPLIT_PRODUCTION_HOST", '"the-dispatch.replit.app"')
    text = ensure_const(text, "PUBLIC_HOSTS", 'new Set(["thedispatch.uk", "www.thedispatch.uk"])')

    insert_at = text.find("async function setSession")
    if insert_at < 0:
        insert_at = text.find("async function currentUser")
    if insert_at < 0:
        raise SystemExit("no setSession/currentUser anchor")
    text = text[:insert_at] + FUNCTIONS + "\n" + DELETE_PRESENTED + "\n" + text[insert_at:]

    text = text.replace(
        "async function setSession(res, user, oldToken = null)",
        "async function setSession(req, res, user, oldToken = null)",
    )
    text = text.replace("await setSession(res,", "await setSession(req, res,")
    idx = text.find("async function setSession")
    chunk = text[idx:idx + 900]
    if "sessionCookieHeader(token, req)" not in chunk:
        text = text[:idx] + re.sub(
            r'res\.setHeader\(\s*"Set-Cookie"\s*,\s*[^)]+\)',
            'res.setHeader("Set-Cookie", sessionCookieHeader(token, req))',
            text[idx:],
            count=1,
        )
    if "await deletePresentedSessions(req, oldToken)" not in text:
        text = text.replace(
            "if (oldToken) await sql`DELETE FROM dispatch_sessions WHERE token_hash=${tokenHash(oldToken)}`;",
            "await deletePresentedSessions(req, oldToken);",
        )

    old_cu = (
        "async function currentUser(req) {\n"
        '  const token = cookieValue(req, "dispatch_session");\n'
        "  if (!databaseReady || !token) return null;\n"
    )
    if old_cu in text and "async function currentUserForToken" not in text:
        text = text.replace(
            old_cu,
            "async function currentUser(req) {\n"
            "  if (!databaseReady) return null;\n"
            "  const tokens = dispatchSessionTokens(req.headers && req.headers.cookie);\n"
            "  for (const token of tokens) {\n"
            "    const user = await currentUserForToken(token);\n"
            "    if (user) return user;\n"
            "  }\n"
            "  return null;\n"
            "}\n"
            "async function currentUserForToken(token) {\n"
            "  if (!token) return null;\n",
            1,
        )

    text = re.sub(
        r'if \(p === "/__auth/logout"\) \{[^}]+\}',
        'if (p === "/__auth/logout") { await deletePresentedSessions(req); res.setHeader("Set-Cookie", clearSessionCookieHeader(req)); res.writeHead(302, { Location: "/" }); return res.end(); }',
        text,
        count=1,
    )
    text = text.replace(
        'if (host !== "www.thedispatch.uk") return false;',
        'if (host !== "www.thedispatch.uk" && host !== "the-dispatch.replit.app") return false;',
    )
    text = text.replace(
        'if (host !== "www.thedispatch.uk") return null;',
        'if (host !== "www.thedispatch.uk" && host !== "the-dispatch.replit.app") return null;',
    )

    server.write_text(text)
    r = subprocess.run(["node", "--check", str(server)], capture_output=True, text=True)
    if r.returncode != 0:
        shutil.copy2(bak, server)
        print(r.stderr)
        raise SystemExit("node --check failed; restored backup")
    print("AUTH_EMERGENCY_OK")


if __name__ == "__main__":
    main()
