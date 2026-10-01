#!/usr/bin/env python3
"""Patch the live Replit tree for the login kick-out and desk NO LIVE SYNC bugs.

Run from the project root that contains server.js (Replit cwd):

  python3 apply_pricefix12.py
  python3 scripts/apply_pricefix12.py
  python3 apply_pricefix12.py --self-test

Idempotent. Backs up files it changes to *.bak-pricefix12 and runs
`node --check` on changed JavaScript. On failure the backups are restored.

Does not replace app.js. It only rewrites the pricefix11 display gates and
the pricefix11 cache token. GitHub main's app.js does not contain those
gates; on that tree the client patch is skipped.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


class PatchError(RuntimeError):
    pass


def die(message: str) -> None:
    print(f"apply_pricefix12: {message}", file=sys.stderr)
    raise SystemExit(1)


def replace_function(src: str, name: str, replacement: str) -> str:
    match = re.search(rf"^(?:async\s+)?function {re.escape(name)}\s*\(", src, flags=re.M)
    if not match:
        raise PatchError(f"could not find function {name}()")
    start = match.start()
    # Parameter lists can contain `{ maxAge }`. Close the parameter parens
    # before looking for the function body brace.
    paren = match.end() - 1
    depth = 0
    params_end = None
    for index in range(paren, len(src)):
        char = src[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                params_end = index
                break
    if params_end is None:
        raise PatchError(f"function {name}() has an unclosed parameter list")
    brace = src.find("{", params_end)
    if brace < 0:
        raise PatchError(f"function {name}() has no body")
    depth = 0
    for index in range(brace, len(src)):
        char = src[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                rest = src[index + 1 :].lstrip("\n")
                return src[:start] + replacement.strip() + "\n\n" + rest
    raise PatchError(f"function {name}() is unclosed")


def has_function(src: str, name: str) -> bool:
    return re.search(rf"^(?:async\s+)?function {re.escape(name)}\s*\(", src, flags=re.M) is not None


def upsert_function(src: str, name: str, replacement: str, anchor: str) -> str:
    if has_function(src, name):
        return replace_function(src, name, replacement)
    index = src.find(anchor)
    if index < 0:
        raise PatchError(f"could not insert {name}(); missing {anchor}")
    return src[:index] + replacement.strip() + "\n\n" + src[index:]


CANONICAL_REDIRECT = """function canonicalRedirectLocation(req, publicOrigin = CANONICAL_ORIGIN) {
  const host = hostnameOf(requestHost(req));
  // www and the production Replit alias both 308 to apex. Preview hosts stay put.
  if (host !== "www.thedispatch.uk" && host !== REPLIT_PRODUCTION_HOST) return null;
  const origin = String(publicOrigin || CANONICAL_ORIGIN).replace(/\\/$/, "");
  try {
    const url = new URL(req.url || "/", origin);
    return `${origin}${url.pathname}${url.search}`;
  } catch {
    return `${origin}/`;
  }
}"""

USE_SECURE = """function useSecureCookie(req) {
  const host = hostnameOf(requestHost(req));
  return requestProtocol(req) === "https" || isPublicDispatchHost(host) || host === REPLIT_PRODUCTION_HOST;
}"""

SHOULD_PIN = """function shouldPinSessionDomain(req) {
  const host = hostnameOf(requestHost(req));
  // Apex and www share one cookie. The production Replit hostname must not mint
  // another host-only dispatch_session. Browsers drop Domain=thedispatch.uk on
  // that host; the 308 sends login to apex before a session cookie is set.
  // Localhost and other preview hosts stay host-only so a Domain attribute is
  // not written onto a host that cannot store it.
  return PUBLIC_HOSTS.has(host) || host === REPLIT_PRODUCTION_HOST;
}"""

COOKIE_FLAGS = """function cookieFlags(req, { maxAge, clear = false, domain } = {}) {
  const parts = ["Path=/", "HttpOnly", "SameSite=Lax"];
  parts.push(clear ? "Max-Age=0" : `Max-Age=${maxAge ?? 2592000}`);
  if (useSecureCookie(req)) parts.push("Secure");
  const pinDomain = domain === undefined ? shouldPinSessionDomain(req) : Boolean(domain);
  if (pinDomain) parts.push(`Domain=${CANONICAL_HOST}`);
  return parts;
}"""

DISPATCH_TOKENS = """function dispatchSessionTokens(cookieHeader) {
  const raw = Array.isArray(cookieHeader) ? cookieHeader.join("; ") : String(cookieHeader || "");
  const prefix = "dispatch_session=";
  const values = [];
  for (const part of raw.split(";")) {
    const trimmed = part.trim();
    if (!trimmed.startsWith(prefix)) continue;
    const encoded = trimmed.slice(prefix.length);
    if (!encoded) continue;
    try {
      values.push(decodeURIComponent(encoded));
    } catch {
      values.push(encoded);
    }
    if (values.length >= 8) break;
  }
  return values;
}"""

CLEAR_COOKIE = """function clearSessionCookieHeader(req) {
  const hostOnly = ["dispatch_session=", ...cookieFlags(req, { clear: true, domain: false })].join("; ");
  const domainScoped = ["dispatch_session=", ...cookieFlags(req, { clear: true, domain: true })].join("; ");
  return [hostOnly, domainScoped];
}"""

SESSION_COOKIE = """function sessionCookieHeader(token, req) {
  const established = [`dispatch_session=${token}`, ...cookieFlags(req)].join("; ");
  // Expire a host-only ghost and any previous Domain cookie, then set the new one.
  // The later Domain (or host-only) Set-Cookie wins for that cookie's identity.
  return [...clearSessionCookieHeader(req), established];
}"""

DELETE_PRESENTED = """async function deletePresentedSessions(req, extraToken = null) {
  try {
    const header = req && req.headers ? req.headers.cookie : "";
    const tokens = new Set(dispatchSessionTokens(header));
    if (extraToken) tokens.add(extraToken);
    for (const token of tokens) {
      await sql`DELETE FROM dispatch_sessions WHERE token_hash=${tokenHash(token)}`;
    }
  } catch (error) {
    console.error("dispatch session clear failed:", error && error.message ? error.message : error);
  }
}"""

WRITE_CANONICAL = """function writeCanonicalRedirect(req, res, publicOrigin = CANONICAL_ORIGIN) {
  const location = canonicalRedirectLocation(req, publicOrigin);
  if (!location) return false;
  res.writeHead(308, { Location: location, "Cache-Control": "no-store" });
  res.end();
  return true;
}"""

HOST_HELPERS = [
    ("headerFirst", """function headerFirst(value) {
  return String(value || "").split(",")[0].trim();
}"""),
    ("requestHost", """function requestHost(req) {
  const headers = req && req.headers ? req.headers : {};
  return headerFirst(headers["x-forwarded-host"]) || headerFirst(headers.host);
}"""),
    ("requestProtocol", """function requestProtocol(req) {
  const headers = req && req.headers ? req.headers : {};
  const forwarded = headerFirst(headers["x-forwarded-proto"]);
  if (forwarded === "https" || forwarded === "http") return forwarded;
  return "http";
}"""),
    ("hostnameOf", """function hostnameOf(host) {
  return String(host || "").split(":")[0].toLowerCase();
}"""),
    ("isPublicDispatchHost", """function isPublicDispatchHost(host) {
  return PUBLIC_HOSTS.has(hostnameOf(host));
}"""),
]

INLINE_CONSTS = [
    'const CANONICAL_ORIGIN = "https://thedispatch.uk";',
    'const CANONICAL_HOST = "thedispatch.uk";',
    'const REPLIT_PRODUCTION_HOST = "the-dispatch.replit.app";',
    'const PUBLIC_HOSTS = new Set(["thedispatch.uk", "www.thedispatch.uk"]);',
]

COOKIE_HELPERS = [
    ("useSecureCookie", USE_SECURE),
    ("shouldPinSessionDomain", SHOULD_PIN),
    ("cookieFlags", COOKIE_FLAGS),
    ("dispatchSessionTokens", DISPATCH_TOKENS),
    ("clearSessionCookieHeader", CLEAR_COOKIE),
    ("sessionCookieHeader", SESSION_COOKIE),
]

CURRENT_USER_OLD = (
    "async function currentUser(req) {\n"
    "  const token = cookieValue(req, \"dispatch_session\");\n"
    "  if (!databaseReady || !token) return null;\n"
)

CURRENT_USER_NEW = (
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
    "  if (!token) return null;\n"
)


def ensure_export(src: str, name: str, after: str) -> str:
    if re.search(rf"^\s*{re.escape(name)},\s*$", src, flags=re.M):
        return src
    anchor = f"  {after},\n"
    insert = anchor + f"  {name},\n"
    if anchor not in src:
        return src.replace("module.exports = {\n", f"module.exports = {{\n  {name},\n", 1)
    return src.replace(anchor, insert, 1)


def patch_billing_origin(src: str) -> str:
    host_line = 'const CANONICAL_HOST = "thedispatch.uk";\n'
    repl_line = 'const REPLIT_PRODUCTION_HOST = "the-dispatch.replit.app";\n'
    if "const REPLIT_PRODUCTION_HOST" not in src:
        if host_line not in src:
            raise PatchError("billingOrigin.js has no CANONICAL_HOST")
        src = src.replace(host_line, host_line + repl_line, 1)
    src = replace_function(src, "canonicalRedirectLocation", CANONICAL_REDIRECT)
    src = replace_function(src, "useSecureCookie", USE_SECURE)
    src = upsert_function(src, "shouldPinSessionDomain", SHOULD_PIN, "function cookieFlags")
    src = replace_function(src, "cookieFlags", COOKIE_FLAGS)
    src = upsert_function(src, "dispatchSessionTokens", DISPATCH_TOKENS, "function clearSessionCookieHeader")
    src = replace_function(src, "clearSessionCookieHeader", CLEAR_COOKIE)
    src = replace_function(src, "sessionCookieHeader", SESSION_COOKIE)
    src = ensure_export(src, "REPLIT_PRODUCTION_HOST", "PUBLIC_STATIC_PATHS")
    src = ensure_export(src, "dispatchSessionTokens", "cookieFlags")
    src = ensure_export(src, "shouldPinSessionDomain", "sessionCookieHeader")
    return src


def billing_import_block(src: str) -> re.Match[str] | None:
    return re.search(r"const \{([\s\S]*?)\} = require\(\"./billingOrigin\"\);", src)


def import_binds(src: str, name: str) -> bool:
    match = billing_import_block(src)
    return bool(match and re.search(rf"\b{re.escape(name)}\b", match.group(1)))


def ensure_billing_import(src: str) -> str:
    match = billing_import_block(src)
    if not match:
        return src
    if "dispatchSessionTokens" in match.group(1) or has_function(src, "dispatchSessionTokens"):
        return src
    block = match.group(0)
    if "  clearSessionCookieHeader,\n" in block:
        updated = block.replace(
            "  clearSessionCookieHeader,\n",
            "  clearSessionCookieHeader,\n  dispatchSessionTokens,\n",
            1,
        )
    else:
        updated = block.replace("const {\n", "const {\n  dispatchSessionTokens,\n", 1)
    return src.replace(block, updated, 1)


def drop_cookie_imports(src: str) -> str:
    """Drop cookie bindings that would load a missing billingOrigin.js."""
    match = billing_import_block(src)
    if not match:
        return src
    body = match.group(1)
    for name in (
        "clearSessionCookieHeader",
        "sessionCookieHeader",
        "dispatchSessionTokens",
        "cookieFlags",
        "useSecureCookie",
        "shouldPinSessionDomain",
        "canonicalRedirectLocation",
        "writeCanonicalRedirect",
    ):
        body = re.sub(rf"\n[ \t]*{name},", "\n", body)
        body = re.sub(rf"\b{name},[ \t]*", "", body)
    if not re.search(r"[A-Za-z_]", body):
        return src.replace(match.group(0), "", 1)
    return src.replace(match.group(0), "const {" + body + "} = require(\"./billingOrigin\");", 1)


def install_inline_cookie_helpers(src: str) -> str:
    """Define every session-cookie helper inside server.js."""
    anchor = "async function currentUser("
    if anchor not in src:
        anchor = "async function setSession("
    if anchor not in src:
        anchor = "function setSession("
    if anchor not in src:
        raise PatchError("server.js has no currentUser() or setSession() to anchor inline helpers")

    pieces: list[str] = []
    for line in INLINE_CONSTS:
        const_name = line.split("=", 1)[0].replace("const", "").strip()
        if not re.search(rf"^const {re.escape(const_name)}\b", src, flags=re.M):
            pieces.append(line)

    helpers = list(HOST_HELPERS) + list(COOKIE_HELPERS)
    redirect_imported = import_binds(src, "writeCanonicalRedirect") or import_binds(src, "canonicalRedirectLocation")
    if not redirect_imported:
        helpers.extend([
            ("canonicalRedirectLocation", CANONICAL_REDIRECT),
            ("writeCanonicalRedirect", WRITE_CANONICAL),
        ])

    for name, body in helpers:
        if import_binds(src, name):
            continue
        if has_function(src, name):
            src = replace_function(src, name, body)
        else:
            pieces.append(body.strip())

    if pieces:
        src = src.replace(anchor, "\n\n".join(pieces) + "\n\n" + anchor, 1)

    handle = re.search(r"(?:async\s+)?function handle\(req,\s*res\) \{\n", src)
    if handle and not import_binds(src, "writeCanonicalRedirect") and has_function(src, "writeCanonicalRedirect"):
        window = src[handle.end():handle.end() + 500]
        if "writeCanonicalRedirect(req, res)" not in window:
            src = src[:handle.end()] + "  if (writeCanonicalRedirect(req, res)) return;\n" + src[handle.end():]

    src = src.replace(
        'if (host !== "www.thedispatch.uk") return false;',
        'if (host !== "www.thedispatch.uk" && host !== "the-dispatch.replit.app") return false;',
    )
    src = src.replace(
        'if (hostnameOf(requestHost(req)) !== "www.thedispatch.uk") return null;',
        'if (hostnameOf(requestHost(req)) !== "www.thedispatch.uk" && hostnameOf(requestHost(req)) !== "the-dispatch.replit.app") return null;',
    )
    return src


def patch_server(src: str, billing_present: bool = False) -> str:
    if billing_present and import_binds(src, "sessionCookieHeader") and import_binds(src, "clearSessionCookieHeader"):
        src = ensure_billing_import(src)
    else:
        if not billing_present:
            src = drop_cookie_imports(src)
        src = install_inline_cookie_helpers(src)
    if "async function setSession(res, user, oldToken = null)" in src:
        src = src.replace(
            "async function setSession(res, user, oldToken = null)",
            "async function setSession(req, res, user, oldToken = null)",
            1,
        )
        src = src.replace("await setSession(res,", "await setSession(req, res,")
    if CURRENT_USER_OLD in src:
        src = src.replace(CURRENT_USER_OLD, CURRENT_USER_NEW, 1)
    elif "async function currentUserForToken" not in src:
        raise PatchError("could not find currentUser() dispatch_session lookup")
    if has_function(src, "deletePresentedSessions"):
        src = replace_function(src, "deletePresentedSessions", DELETE_PRESENTED)
    else:
        anchor = "async function setSession("
        if anchor not in src:
            anchor = "function setSession("
        index = src.find(anchor)
        if index < 0:
            raise PatchError("could not find setSession()")
        src = src[:index] + DELETE_PRESENTED.strip() + "\n\n" + src[index:]
    old_delete = "if (oldToken) await sql`DELETE FROM dispatch_sessions WHERE token_hash=${tokenHash(oldToken)}`;"
    new_delete = "await deletePresentedSessions(req, oldToken);"
    if old_delete in src:
        src = src.replace(old_delete, new_delete, 1)
    elif new_delete not in src:
        raise PatchError("setSession does not rotate the presented session tokens")
    logout = re.compile(
        r"const token = cookieValue\(req, \"dispatch_session\"\);\s*"
        r"if \(token\) await sql`DELETE FROM dispatch_sessions WHERE token_hash=\$\{tokenHash\(token\)\}`;"
    )
    updated, count = logout.subn("await deletePresentedSessions(req);", src, count=1)
    if count == 1:
        src = updated
    elif "await deletePresentedSessions(req);" not in src:
        raise PatchError("logout still deletes only the first dispatch_session")
    src = src.replace(
        'if (host !== "www.thedispatch.uk") return false;',
        'if (host !== "www.thedispatch.uk" && host !== "the-dispatch.replit.app") return false;',
    )
    return src


APP_REPLACEMENTS = [
    (
        "compare price",
        "    const na = !isPrimaryLiveQuote(r.tk);\n"
        "    return `<td style=\"text-align:right;padding:8px;font-weight:700;color:${na?\"var(--t3)\":\"var(--tx)\"}\">${na?\"NO LIVE SYNC\":\"$\"+d.p}<div>${asOfTag(r.tk)}</div></td>`;",
        "    const na = !hasSyncedQuote(r.tk);\n"
        "    return `<td style=\"text-align:right;padding:8px;font-weight:700;color:${na?\"var(--t3)\":\"var(--tx)\"}\">${na?\"NO LIVE SYNC\":\"$\"+d.p}<div>${asOfTag(r.tk)}</div></td>`;",
    ),
    (
        "compare change",
        "     const na = !isPrimaryLiveQuote(r.tk);",
        "     const na = !hasSyncedQuote(r.tk);",
    ),
    (
        "desk spine",
        "    const synced = isPrimaryLiveQuote(s.tk);",
        "    const synced = hasSyncedQuote(s.tk);",
    ),
    (
        "search price",
        "   if (!isPrimaryLiveQuote(sym)) return \"\";",
        "   if (!hasSyncedQuote(sym)) return \"\";",
    ),
    (
        "geo energy prefer",
        "  if (isPrimaryLiveQuote(tk)) d = fp(tk);\n"
        "  if ((!d || !isPrimaryLiveQuote(used)) && fallbackTk && isPrimaryLiveQuote(fallbackTk)) {",
        "  if (hasSyncedQuote(tk)) d = fp(tk);\n"
        "  if ((!d || !hasSyncedQuote(used)) && fallbackTk && hasSyncedQuote(fallbackTk)) {",
    ),
    (
        "geo energy blank",
        "  if (!d || !isPrimaryLiveQuote(used)) {",
        "  if (!d || !hasSyncedQuote(used)) {",
    ),
    (
        "dynamic lookup",
        "         livePrice: isPrimaryLiveQuote(markTk) ? livePx(markTk) : null,\n"
        "         liveChange: isPrimaryLiveQuote(markTk) ? liveChg(markTk) : null,",
        "         livePrice: hasSyncedQuote(markTk) ? livePx(markTk) : null,\n"
        "         liveChange: hasSyncedQuote(markTk) ? liveChg(markTk) : null,",
    ),
    (
        "live price patch",
        "       if (!tk || !isPrimaryLiveQuote(tk)) return;",
        "       if (!tk || !hasSyncedQuote(tk)) return;",
    ),
    (
        "dashboard count",
        "  const primaryLiveCount = [...liveSymbols].filter(isPrimaryLiveQuote).length;\n"
        "  const liveBadge = primaryLiveCount > 0\n"
        "    ? bd(primaryLiveCount + \" live feed\", \"var(--gn)\")",
        "  const primaryLiveCount = [...liveSymbols].filter(hasSyncedQuote).length;\n"
        "  const liveBadge = primaryLiveCount > 0\n"
        "    ? bd(primaryLiveCount + \" synced\", \"var(--gn)\")",
    ),
    (
        "latency strip",
        "   const nLive=[...liveSymbols].filter(isPrimaryLiveQuote).length;",
        "   const nLive=[...liveSymbols].filter(hasSyncedQuote).length;",
    ),
    (
        "book live count",
        "     return isPrimaryLiveQuote(raw)||isPrimaryLiveQuote(desk)||isPrimaryLiveQuote(raw.toUpperCase());",
        "     return hasSyncedQuote(raw)||hasSyncedQuote(desk)||hasSyncedQuote(raw.toUpperCase());",
    ),
    (
        "book live label",
        "` · ${liveN} live`",
        "` · ${liveN} synced`",
    ),
]


def patch_app_js(src: str) -> tuple[str, str]:
    if "isPrimaryLiveQuote" not in src:
        return src, "skip"
    missing = []
    changed = False
    for label, old, new in APP_REPLACEMENTS:
        count = src.count(old)
        if count:
            src = src.replace(old, new)
            changed = True
            continue
        if new not in src:
            missing.append(label)
    if missing:
        raise PatchError(
            "app.js looks like the live desk but these gates were not found: " + ", ".join(missing)
        )
    src, creds_changed = ensure_api_me_credentials(src)
    if creds_changed:
        changed = True
    return src, "patched" if changed else "already"


FETCH_ME = re.compile(r"""fetch\(\s*(['"])/api/me\1(\s*,\s*\{[^{}]*\})?\s*\)""")


def ensure_api_me_credentials(src: str) -> tuple[str, bool]:
    changed = False

    def repl(match: re.Match[str]) -> str:
        nonlocal changed
        quote = match.group(1)
        options = match.group(2)
        if options and re.search(r"credentials\s*:", options):
            return match.group(0)
        changed = True
        if options:
            body = re.sub(r"\{", "{ credentials: " + quote + "include" + quote + ",", options, count=1)
            return f"fetch({quote}/api/me{quote}{body})"
        return f"fetch({quote}/api/me{quote},{{credentials:{quote}include{quote}}})"

    return FETCH_ME.sub(repl, src), changed


def patch_html(src: str) -> str:
    return src.replace("pricefix11", "pricefix12")


def write_if_changed(path: Path, new_text: str, backups: list[tuple[Path, Path]]) -> bool:
    old = path.read_text() if path.exists() else None
    if old == new_text:
        return False
    backup = path.with_name(path.name + ".bak-pricefix12")
    if old is not None and not backup.exists():
        shutil.copy2(path, backup)
        backups.append((path, backup))
    path.write_text(new_text)
    return True


def restore(backups: list[tuple[Path, Path]]) -> None:
    for path, backup in reversed(backups):
        if backup.exists():
            shutil.copy2(backup, path)


def apply_tree(root: Path) -> None:
    server = root / "server.js"
    billing = root / "billingOrigin.js"
    if not server.exists() and not billing.exists():
        die("run this from the Replit project root that contains server.js")

    backups: list[tuple[Path, Path]] = []
    changed: list[Path] = []
    try:
        if billing.exists():
            updated = patch_billing_origin(billing.read_text())
            if write_if_changed(billing, updated, backups):
                changed.append(billing)
                print("billingOrigin.js: patched dual-clear cookies and replit.app 308")
            else:
                print("billingOrigin.js: already patched")
        else:
            print("billingOrigin.js: not present; cookie helpers patched in server.js when found")

        if server.exists():
            updated = patch_server(server.read_text(), billing_present=billing.exists())
            if write_if_changed(server, updated, backups):
                changed.append(server)
                print("server.js: session lookup tries every dispatch_session; logout clears both cookies")
            else:
                print("server.js: already patched")

        app = root / "app.js"
        if app.exists():
            updated, status = patch_app_js(app.read_text())
            print(f"app.js: {status}")
            if status == "patched" and write_if_changed(app, updated, backups):
                changed.append(app)
        else:
            print("app.js: missing, skip")

        html_hits = 0
        for html in sorted(root.glob("*.html")):
            text = html.read_text()
            if "pricefix11" not in text:
                continue
            updated = patch_html(text)
            html_hits += 1
            if write_if_changed(html, updated, backups):
                changed.append(html)
                print(f"{html.name}: pricefix11 → pricefix12")
            else:
                print(f"{html.name}: cache token already pricefix12")
        if html_hits == 0:
            print("html: no pricefix11 cache token (skip; do not copy GitHub index.html over live)")

        saw_modal = False
        for path in sorted(root.glob("*.js")) + sorted(root.glob("*.html")):
            if path.name.endswith(".bak-pricefix12"):
                continue
            text = path.read_text(errors="replace") if False else path.read_text()
            if "Failed to get user data after login" not in text and "Authentication Error" not in text:
                continue
            saw_modal = True
            updated, creds_changed = ensure_api_me_credentials(text)
            if creds_changed and write_if_changed(path, updated, backups):
                if path not in changed:
                    changed.append(path)
                print(f"{path.name}: auth modal path now sends credentials on /api/me")
            else:
                print(f"{path.name}: contains the auth modal text; /api/me already uses credentials")
        if not saw_modal:
            print("auth modal: text not in this tree. Login kick-out is /api/me without id; dual-cookie clear covers it.")

        for path in changed:
            if path.suffix == ".js":
                subprocess.check_call(["node", "--check", str(path)], cwd=root)
        if changed:
            print("node --check passed for " + ", ".join(path.name for path in changed if path.suffix == ".js"))
        print("apply_pricefix12: done")
    except Exception as error:
        restore(backups)
        if isinstance(error, PatchError):
            die(str(error))
        if isinstance(error, subprocess.CalledProcessError):
            die("node --check failed; restored backups")
        raise


def self_test() -> None:
    sample_parts = [old for _label, old, _new in APP_REPLACEMENTS]
    sample = "\n".join(sample_parts) + "\nfunction isPrimaryLiveQuote(tk) {\n  return true;\n}\n    const primary = isPrimaryLiveQuote(tk);\n    const live = isPrimaryLiveQuote(tk) ? '' : '';\n"
    patched, status = patch_app_js(sample)
    if status != "patched":
        raise SystemExit(f"expected app patch, got {status}")
    for label, old, new in APP_REPLACEMENTS:
        if old in patched:
            raise SystemExit(f"old gate still present: {label}")
        if new not in patched:
            raise SystemExit(f"new gate missing: {label}")
    if "function isPrimaryLiveQuote" not in patched:
        raise SystemExit("predicate definition was rewritten")
    if "const primary = isPrimaryLiveQuote(tk);" not in patched:
        raise SystemExit("non-display live dot gate was rewritten")

    html = "<script src=\"/app.js?v=pricefix11\"></script>\nvar V='TD-pricefix11';\n"
    bumped = patch_html(html)
    if "pricefix11" in bumped or bumped.count("pricefix12") != 2:
        raise SystemExit("cache token bump failed")
    if patch_html(bumped) != bumped:
        raise SystemExit("cache token bump is not idempotent")

    auth = 'const res = await fetch("/api/me");\nif (!user || !user.id) throw new Error("Failed to get user data after login");\n'
    authed, changed = ensure_api_me_credentials(auth)
    if not changed or 'credentials:"include"' not in authed:
        raise SystemExit("auth modal fetch was not given credentials")
    if "Failed to get user data after login" not in authed:
        raise SystemExit("auth error text should remain so the UI still reports a real failure")
    again, changed_again = ensure_api_me_credentials(authed)
    if changed_again or again != authed:
        raise SystemExit("credentials inject is not idempotent")

    billing = '''const CANONICAL_HOST = "thedispatch.uk";
function canonicalRedirectLocation(req, publicOrigin = CANONICAL_ORIGIN) {
  if (hostnameOf(requestHost(req)) !== "www.thedispatch.uk") return null;
  return "/";
}
function useSecureCookie(req) {
  return false;
}
function cookieFlags(req, { maxAge, clear = false } = {}) {
  return ["Path=/"];
}
function sessionCookieHeader(token, req) {
  return "one";
}
function clearSessionCookieHeader(req) {
  return "clear";
}
module.exports = {
  PUBLIC_STATIC_PATHS,
  cookieFlags,
  sessionCookieHeader,
};
'''
    billed = patch_billing_origin(billing)
    billed_again = patch_billing_origin(billed)
    if billed != billed_again:
        raise SystemExit("billingOrigin patch is not idempotent")
    if "REPLIT_PRODUCTION_HOST" not in billed or "dispatchSessionTokens" not in billed:
        raise SystemExit("billingOrigin patch missed helpers")
    if "the-dispatch.replit.app" not in billed:
        raise SystemExit("billingOrigin patch missed replit redirect")

    server = '''const {
  clearSessionCookieHeader,
  sessionCookieHeader,
} = require("./billingOrigin");
async function currentUser(req) {
  const token = cookieValue(req, "dispatch_session");
  if (!databaseReady || !token) return null;
  return token;
}
async function setSession(req, res, user, oldToken = null) {
  if (oldToken) await sql`DELETE FROM dispatch_sessions WHERE token_hash=${tokenHash(oldToken)}`;
  res.setHeader("Set-Cookie", sessionCookieHeader(token, req));
}
if (p === "/__auth/logout") { const token = cookieValue(req, "dispatch_session"); if (token) await sql`DELETE FROM dispatch_sessions WHERE token_hash=${tokenHash(token)}`; res.end(); }
'''
    patched_server = patch_server(server, billing_present=True)
    patched_server_again = patch_server(patched_server, billing_present=True)
    if patched_server != patched_server_again:
        raise SystemExit("server patch is not idempotent")
    if "currentUserForToken" not in patched_server or "deletePresentedSessions" not in patched_server:
        raise SystemExit("server patch missed session helpers")
    if "cookieValue(req, \"dispatch_session\")" in patched_server.split("async function currentUser", 1)[-1].split("async function setSession", 1)[0]:
        raise SystemExit("currentUser still reads only the first cookie")

    # Live Replit has no billingOrigin.js. A previous apply left the auth
    # routes calling helpers that were never defined, which 500s login.
    broken = r'''function cookieValue(req, name) {
  const raw = (req.headers && req.headers.cookie) || "";
  const found = raw.split(";").map(v => v.trim()).find(v => v.startsWith(name + "="));
  return found ? decodeURIComponent(found.slice(name.length + 1)) : null;
}
function tokenHash(token) { return String(token || ""); }
async function currentUser(req) {
  if (!databaseReady) return null;
  const tokens = dispatchSessionTokens(req.headers && req.headers.cookie);
  for (const token of tokens) {
    const user = await currentUserForToken(token);
    if (user) return user;
  }
  return null;
}
async function currentUserForToken(token) {
  if (!token) return null;
  return null;
}
async function deletePresentedSessions(req, extraToken = null) {
  const header = req && req.headers ? req.headers.cookie : "";
  const tokens = new Set(dispatchSessionTokens(header));
  if (extraToken) tokens.add(extraToken);
  for (const token of tokens) {
    await sql`DELETE FROM dispatch_sessions WHERE token_hash=${tokenHash(token)}`;
  }
}
async function setSession(req, res, user, oldToken = null) {
  const token = "tok";
  await deletePresentedSessions(req, oldToken);
  res.setHeader("Set-Cookie", sessionCookieHeader(token, req));
}
async function handle(req, res) {
  if (p === "/__auth/login" && req.method === "POST") await setSession(req, res, user, null);
  if (p === "/__auth/register" && req.method === "POST") await setSession(req, res, user, null);
  if (p === "/__auth/logout") { await deletePresentedSessions(req); res.setHeader("Set-Cookie", clearSessionCookieHeader(req)); }
}
'''
    healed = patch_server(broken, billing_present=False)
    healed_again = patch_server(healed, billing_present=False)
    if healed != healed_again:
        raise SystemExit("standalone server patch is not idempotent")
    required = [
        "const CANONICAL_HOST",
        "const REPLIT_PRODUCTION_HOST",
        "function shouldPinSessionDomain",
        "function cookieFlags",
        "function useSecureCookie",
        "function clearSessionCookieHeader",
        "function sessionCookieHeader",
        "function dispatchSessionTokens",
        "async function deletePresentedSessions",
        "async function setSession(req, res, user, oldToken = null)",
        "function canonicalRedirectLocation",
        "function writeCanonicalRedirect",
        "the-dispatch.replit.app",
    ]
    missing = [name for name in required if name not in healed]
    if missing:
        raise SystemExit("standalone heal missed: " + ", ".join(missing))
    if 'require("./billingOrigin")' in healed:
        raise SystemExit("standalone heal must not require the missing billingOrigin.js")
    if "try {" not in healed.split("async function deletePresentedSessions", 1)[1].split("async function setSession", 1)[0]:
        raise SystemExit("deletePresentedSessions has no try/catch")
    if "isPrimaryLiveQuote" in healed:
        raise SystemExit("server heal touched a desk gate")
    harness = r'''
const req = { headers: { host: "thedispatch.uk", "x-forwarded-proto": "https" }, url: "/__auth/login?next=1" };
const cleared = clearSessionCookieHeader(req);
if (!Array.isArray(cleared) || cleared.length !== 2) throw new Error("clearSessionCookieHeader must return both clears");
if (!/Max-Age=0/.test(cleared[0]) || /Domain=/.test(cleared[0])) throw new Error("host-only clear missing: " + cleared[0]);
if (!/Domain=thedispatch\.uk/.test(cleared[1]) || !/Max-Age=0/.test(cleared[1])) throw new Error("domain clear missing: " + cleared[1]);
const set = sessionCookieHeader("tok", req);
if (!Array.isArray(set) || set.length !== 3) throw new Error("sessionCookieHeader must dual-clear then set");
if (!/dispatch_session=tok/.test(set[2]) || !/Domain=thedispatch\.uk/.test(set[2]) || /Max-Age=0/.test(set[2])) throw new Error("domain session missing: " + set[2]);
const tokens = dispatchSessionTokens("dispatch_session=dead; other=1; dispatch_session=valid");
if (tokens.join(",") !== "dead,valid") throw new Error("tokens " + tokens.join(","));
const loc = canonicalRedirectLocation({ headers: { host: "the-dispatch.replit.app" }, url: "/__auth/login?next=1" });
if (loc !== "https://thedispatch.uk/__auth/login?next=1") throw new Error("replit redirect " + loc);
if (canonicalRedirectLocation({ headers: { host: "thedispatch.uk" }, url: "/" }) !== null) throw new Error("apex must stay");
let hit = false;
function sql() { hit = true; throw new Error("db down"); }
deletePresentedSessions({ headers: { cookie: "dispatch_session=dead" } }, "dead").then(() => {
  if (!hit) throw new Error("deletePresentedSessions did not attempt the delete");
  console.log("replit-fixture-ok");
}).catch((error) => { console.error(error); process.exit(1); });
'''
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "server.js"
        path.write_text(healed + "\n" + harness)
        subprocess.check_call(["node", "--check", str(path)])
        subprocess.check_call(["node", str(path)])

    imported = (
        'const {\n  clearSessionCookieHeader,\n  sessionCookieHeader,\n} = require("./billingOrigin");\n'
        + broken
    )
    stripped = patch_server(imported, billing_present=False)
    if 'require("./billingOrigin")' in stripped or "function sessionCookieHeader" not in stripped:
        raise SystemExit("heal left a require of the missing billingOrigin.js")
    if patch_server(stripped, billing_present=False) != stripped:
        raise SystemExit("import-stripping heal is not idempotent")
    print("apply_pricefix12 self-test ok")


def main() -> None:
    if "--self-test" in sys.argv[1:]:
        self_test()
        return
    root = Path.cwd()
    apply_tree(root)


if __name__ == "__main__":
    main()
