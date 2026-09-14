#!/usr/bin/env python3
"""In-place billing/session patcher for the live Replit Autoscale tree.

Run from the project root that contains server.js and app.js (Replit cwd).

  python3 apply_live_billing_fix.py
  python3 scripts/apply_live_billing_fix.py

Idempotent: exits 0 without writing if canonicalPublicOrigin already exists.
Backs up to server.js.bak-billing and app.js.bak-billing, then runs
`node --check server.js`. On syntax failure the backups are restored.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

CANONICAL_ORIGIN = "https://thedispatch.uk"
HELPER_MARK = "function canonicalPublicOrigin"

HELPERS = """function canonicalPublicOrigin() {
  const raw = String(process.env.DISPATCH_PUBLIC_ORIGIN || process.env.PUBLIC_ORIGIN || "https://thedispatch.uk").trim().replace(/\\/$/, "");
  try {
    const host = new URL(raw).hostname.toLowerCase();
    if (host === "www.thedispatch.uk" || host === "thedispatch.uk") return "https://thedispatch.uk";
    return raw;
  } catch {
    return "https://thedispatch.uk";
  }
}
function sessionCookieHeader(token, req) {
  const host = String((req.headers && (req.headers["x-forwarded-host"] || req.headers.host)) || "").split(",")[0].trim().split(":")[0].toLowerCase();
  const proto = String((req.headers && req.headers["x-forwarded-proto"]) || "").split(",")[0].trim();
  const publicHost = host === "thedispatch.uk" || host === "www.thedispatch.uk";
  const secure = proto === "https" || publicHost;
  const parts = [`dispatch_session=${token}`, "Path=/", "HttpOnly", "SameSite=Lax", "Max-Age=2592000"];
  if (secure) parts.push("Secure");
  if (publicHost) parts.push("Domain=thedispatch.uk");
  return parts.join("; ");
}
function clearSessionCookieHeader(req) {
  const host = String((req.headers && (req.headers["x-forwarded-host"] || req.headers.host)) || "").split(",")[0].trim().split(":")[0].toLowerCase();
  const proto = String((req.headers && req.headers["x-forwarded-proto"]) || "").split(",")[0].trim();
  const publicHost = host === "thedispatch.uk" || host === "www.thedispatch.uk";
  const secure = proto === "https" || publicHost;
  const parts = ["dispatch_session=", "Path=/", "HttpOnly", "SameSite=Lax", "Max-Age=0"];
  if (secure) parts.push("Secure");
  if (publicHost) parts.push("Domain=thedispatch.uk");
  return parts.join("; ");
}
function writeCanonicalHostRedirect(req, res) {
  const host = String((req.headers && (req.headers["x-forwarded-host"] || req.headers.host)) || "").split(",")[0].trim().split(":")[0].toLowerCase();
  if (host !== "www.thedispatch.uk") return false;
  const origin = canonicalPublicOrigin();
  let location = origin + "/";
  try {
    const url = new URL(req.url || "/", origin);
    location = `${origin}${url.pathname}${url.search}`;
  } catch {}
  res.writeHead(308, { Location: location, "Cache-Control": "no-store" });
  res.end();
  return true;
}
"""

START_CHECKOUT = """async function _startCheckout(btn){
  if(!btn)return;
  btn.textContent='Redirecting to payment…';btn.disabled=true;btn.style.opacity='0.7';
  try{
    const r=await fetch('/api/create-checkout',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({})});
    const d=await r.json().catch(()=>({}));
    if(d.url){window.location.href=d.url;return;}
    if(r.status===401){
      try{
        const meRes=await fetch('/api/me',{credentials:'include'});
        const me=meRes.ok?await meRes.json():null;
        if(me?.checkoutSession?.url){window.location.href=me.checkoutSession.url;return;}
        if(me?.id){
          btn.textContent=d.error||'Unable to start checkout';
          btn.disabled=false;btn.style.opacity='1';
          return;
        }
      }catch{}
      window.location.href="/__auth/subscribe";
      return;
    }
    btn.textContent=d.error||'Something went wrong';btn.disabled=false;btn.style.opacity='1';
  }catch{btn.textContent='Network error — try again';btn.disabled=false;btn.style.opacity='1';}
}
"""


class PatchError(RuntimeError):
    pass


def die(message: str, code: int = 1) -> None:
    print(f"apply_live_billing_fix: {message}", file=sys.stderr)
    raise SystemExit(code)


def replace_once(src: str, old: str, new: str, label: str) -> str:
    count = src.count(old)
    if count == 1:
        return src.replace(old, new, 1)
    if count == 0:
        raise PatchError(f"could not find {label}")
    raise PatchError(f"found {count} copies of {label}; refusing to guess")


def replace_first_re(src: str, pattern: str, repl: str, label: str, flags: int = 0) -> str:
    updated, n = re.subn(pattern, repl, src, count=1, flags=flags)
    if n != 1:
        raise PatchError(f"could not find {label}")
    return updated


def replace_top_level_function(src: str, name: str, replacement: str) -> str:
    match = re.search(rf"^function {re.escape(name)}\s*\(", src, flags=re.M)
    if not match:
        raise PatchError(f"could not find function {name}()")
    start = match.start()
    i = src.find("{", match.end() - 1)
    if i < 0:
        raise PatchError(f"function {name}() has no body")
    depth = 0
    for j in range(i, len(src)):
        ch = src[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[:start] + replacement.rstrip() + "\n" + src[j + 1 :]
    raise PatchError(f"function {name}() is unclosed")


def patch_server(src: str) -> str:
    if HELPER_MARK in src:
        return src

    src = replace_once(
        src,
        "async function setSession(res, user, oldToken = null) {",
        HELPERS + "async function setSession(req, res, user, oldToken = null) {",
        "setSession(res, user, ...) definition",
    )
    src = replace_first_re(
        src,
        r'res\.setHeader\(\s*"Set-Cookie"\s*,\s*`dispatch_session=\$\{token\}[^`]*`\s*\)',
        'res.setHeader("Set-Cookie", sessionCookieHeader(token, req))',
        "setSession Set-Cookie assignment",
    )
    call_count = src.count("await setSession(res,")
    if call_count < 1:
        raise PatchError("could not find await setSession(res, ...) call sites")
    src = src.replace("await setSession(res,", "await setSession(req, res,")
    if "await setSession(res," in src:
        raise PatchError("leftover await setSession(res, ...) call sites")

    src = replace_top_level_function(
        src,
        "publicUrl",
        """function publicUrl(req) {
  return canonicalPublicOrigin();
}""",
    )

    webhook_patterns = [
        (
            '    const domain = process.env.REPLIT_DOMAINS?.split(",")[0];\n'
            '    if (!domain) throw new Error("REPLIT_DOMAINS is unavailable for managed Stripe webhooks.");\n'
            "    await sync.findOrCreateManagedWebhook(`https://${domain}/api/stripe/webhook`, {",
            "    const webhookOrigin = canonicalPublicOrigin();\n"
            '    if (!webhookOrigin) throw new Error("DISPATCH_PUBLIC_ORIGIN is required for managed Stripe webhooks.");\n'
            "    await sync.findOrCreateManagedWebhook(`${webhookOrigin}/api/stripe/webhook`, {",
        ),
        (
            "    await sync.findOrCreateManagedWebhook(`https://${domain}/api/stripe/webhook`, {",
            "    await sync.findOrCreateManagedWebhook(`${canonicalPublicOrigin()}/api/stripe/webhook`, {",
        ),
        (
            "    await sync.findOrCreateManagedWebhook(`${PUBLIC_ORIGIN}/api/stripe/webhook`, {",
            "    await sync.findOrCreateManagedWebhook(`${canonicalPublicOrigin()}/api/stripe/webhook`, {",
        ),
        (
            "    await sync.findOrCreateManagedWebhook(`${process.env.PUBLIC_ORIGIN}/api/stripe/webhook`, {",
            "    await sync.findOrCreateManagedWebhook(`${canonicalPublicOrigin()}/api/stripe/webhook`, {",
        ),
    ]
    webhook_ok = False
    last_error = None
    for old, new in webhook_patterns:
        try:
            src = replace_once(src, old, new, "Stripe webhook init")
            webhook_ok = True
            break
        except PatchError as exc:
            last_error = exc
    if not webhook_ok:
        raise PatchError(f"could not retarget Stripe webhook init ({last_error})")

    handle_call = "if (writeCanonicalHostRedirect(req, res)) return;"
    if handle_call not in src:
        handle_needles = [
            "async function handle(req, res) {\n",
            "async function handle(req, res){\n",
        ]
        handle_ok = False
        for needle in handle_needles:
            if needle in src:
                src = src.replace(needle, needle + f"  {handle_call}\n", 1)
                handle_ok = True
                break
        if not handle_ok:
            raise PatchError("could not insert writeCanonicalHostRedirect at start of handle()")

    logout_patterns = [
        (
            'res.setHeader("Set-Cookie", "dispatch_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")',
            'res.setHeader("Set-Cookie", clearSessionCookieHeader(req))',
        ),
        (
            "res.setHeader('Set-Cookie', 'dispatch_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax')",
            'res.setHeader("Set-Cookie", clearSessionCookieHeader(req))',
        ),
    ]
    logout_ok = False
    for old, new in logout_patterns:
        if old in src:
            src = src.replace(old, new, 1)
            logout_ok = True
            break
    if not logout_ok:
        src = replace_first_re(
            src,
            r'res\.setHeader\(\s*[\'"]Set-Cookie[\'"]\s*,\s*[\'"]dispatch_session=;[^\'"]*[\'"]\s*\)',
            'res.setHeader("Set-Cookie", clearSessionCookieHeader(req))',
            "logout Set-Cookie clear",
        )

    static_guard = (
        '  const blockedBase = path.basename(requested).toLowerCase();\n'
        '  if (blockedBase === "server.js" || blockedBase === "stripeclient.js" '
        '|| blockedBase === "package.json" || blockedBase.endsWith(".md")) return false;\n'
    )
    if "blockedBase === \"server.js\"" not in src:
        src = replace_once(
            src,
            '  const requested = pathname === "/" ? "/index.html" : pathname;\n'
            "  const file = path.normalize(path.join(root, requested));",
            '  const requested = pathname === "/" ? "/index.html" : pathname;\n'
            + static_guard
            + "  const file = path.normalize(path.join(root, requested));",
            "serveStatic requested-path assignment",
        )
    return src


def patch_app(src: str) -> str:
    if "checkoutSession" in src and re.search(r"credentials:\s*['\"]include['\"]", src):
        start = src.find("async function _startCheckout")
        end = src.find("async function ", start + 10) if start >= 0 else -1
        body = src[start:end] if start >= 0 and end > start else src
        if "checkoutSession" in body and re.search(r"credentials:\s*['\"]include['\"]", body):
            return src

    match = re.search(
        r"async function _startCheckout\s*\(\s*btn\s*\)\s*\{.*?\n\}",
        src,
        flags=re.S,
    )
    if not match:
        raise PatchError("could not find async function _startCheckout(btn)")
    return src[: match.start()] + START_CHECKOUT.rstrip() + src[match.end() :]


def backup(path: Path) -> Path:
    dest = path.with_name(path.name + ".bak-billing")
    shutil.copy2(path, dest)
    return dest


def restore(original: Path, bak: Path) -> None:
    shutil.copy2(bak, original)


def node_check(server: Path) -> None:
    try:
        result = subprocess.run(
            ["node", "--check", str(server)],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise PatchError("node is not installed; cannot run node --check server.js") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise PatchError(f"node --check server.js failed:\n{detail}")


def main() -> int:
    cwd = Path.cwd()
    server = cwd / "server.js"
    app = cwd / "app.js"
    if not server.is_file() or not app.is_file():
        die("run from the Replit project root that contains server.js and app.js")

    server_src = server.read_text(encoding="utf-8")
    app_src = app.read_text(encoding="utf-8")
    if HELPER_MARK in server_src:
        print("apply_live_billing_fix: already applied (canonicalPublicOrigin present); no-op")
        return 0

    try:
        next_server = patch_server(server_src)
        next_app = patch_app(app_src)
    except PatchError as exc:
        die(str(exc))

    if "function canonicalPublicOrigin" not in next_server:
        die("patch did not insert canonicalPublicOrigin")
    if "sessionCookieHeader(token, req)" not in next_server:
        die("patch did not switch setSession onto sessionCookieHeader")
    if "if (writeCanonicalHostRedirect(req, res)) return;" not in next_server:
        die("patch did not insert writeCanonicalHostRedirect at start of handle()")
    if "clearSessionCookieHeader(req)" not in next_server:
        die("patch did not use clearSessionCookieHeader on logout")
    if "canonicalPublicOrigin()" not in next_server:
        die("patch did not pin publicUrl / webhook to canonicalPublicOrigin")
    if "blockedBase === \"server.js\"" not in next_server:
        die("patch did not block source files in serveStatic")
    if "await setSession(req, res," not in next_server:
        die("patch did not update setSession call sites")
    if not re.search(r"credentials:\s*['\"]include['\"]", next_app) or "checkoutSession" not in next_app:
        die("patch did not update _startCheckout credentials / checkoutSession reuse")

    server_bak = backup(server)
    app_bak = backup(app)
    print(f"apply_live_billing_fix: backed up {server.name} -> {server_bak.name}")
    print(f"apply_live_billing_fix: backed up {app.name} -> {app_bak.name}")
    server.write_text(next_server, encoding="utf-8")
    app.write_text(next_app, encoding="utf-8")

    try:
        node_check(server)
    except PatchError as exc:
        restore(server, server_bak)
        restore(app, app_bak)
        die(f"{exc}\nrestored {server.name} and {app.name} from *.bak-billing")

    print("apply_live_billing_fix: patched server.js and app.js")
    print("apply_live_billing_fix: node --check server.js passed")
    print(
        "apply_live_billing_fix: set DISPATCH_PUBLIC_ORIGIN="
        f"{CANONICAL_ORIGIN} in Replit production Secrets, then redeploy Autoscale"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
