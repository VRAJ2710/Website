#!/usr/bin/env python3
"""Patch a live Replit server.js so Ask/Expert can call xAI and /api/me stays a guest 200.

Does not replace the Replit tree with this Git checkout. Run it from the live app
directory (the one that contains server.js). Stripe checkout code is not edited.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ME_OLD = 'if (p === "/api/me") return json(res, 200, publicUser(await currentUser(req)));'
ME_NEW = """if (p === "/api/me") {
    try {
      const meUser = await currentUser(req);
      if (!meUser || !meUser.id) {
        return json(res, 200, { guest: true, tier: "free", billingPortal: false, isAdmin: false });
      }
      return json(res, 200, publicUser(meUser));
    } catch (error) {
      console.error("GET /api/me failed:", error && error.message ? error.message : error);
      return json(res, 200, { guest: true, tier: "free", billingPortal: false, isAdmin: false });
    }
  }"""

GENERATE_NEEDLE = "async function generateAi({ system, messages, maxTokens = 1000, temperature = 0.2 }) {\n"
GENERATE_INSERT = """async function generateAi({ system, messages, maxTokens = 1000, temperature = 0.2 }) {
  const dispatchXaiKey = String(process.env.XAI_API_KEY || "").trim();
  if (dispatchXaiKey) {
    const { completeWithXaiKey, xaiBaseUrl, xaiModel } = require("./aiProvider");
    return completeWithXaiKey({
      apiKey: dispatchXaiKey,
      model: xaiModel(),
      baseUrl: xaiBaseUrl(),
      system,
      messages,
      maxTokens: Math.max(300, Math.min(Number(maxTokens) || 1000, 2400)),
      temperature,
      timeoutMs: Number(process.env.AI_TIMEOUT_MS || 25000),
    });
  }
"""


def backup(path: Path) -> Path:
    dest = path.with_name(path.name + ".bak-chat-me")
    shutil.copy2(path, dest)
    return dest


def restore(path: Path, copy: Path) -> None:
    shutil.copy2(copy, path)


def patch_server(source: str) -> str:
    already = ("resolvePublicUser" in source and "xaiApiKey()" in source) or ("dispatchXaiKey" in source and "guest: true" in source)
    if already:
        return source
    updated = source
    if ME_OLD not in updated:
        raise SystemExit("server.js has no exact /api/me one-liner to patch; refusing to guess.")
    if GENERATE_NEEDLE not in updated:
        raise SystemExit("server.js has no generateAi({ system, messages, maxTokens = 1000, temperature = 0.2 }) to patch.")
    if updated.count(ME_OLD) != 1 or updated.count(GENERATE_NEEDLE) != 1:
        raise SystemExit("expected exactly one /api/me handler and one generateAi signature.")
    updated = updated.replace(ME_OLD, ME_NEW, 1)
    updated = updated.replace(GENERATE_NEEDLE, GENERATE_INSERT, 1)
    opaque = 'throw new AiRequestError(503, "The AI provider is not ready. Please try again shortly.", "PROVIDER_UNAVAILABLE");'
    clear = 'throw new AiRequestError(503, "AI is not configured. In Replit Secrets, set XAI_API_KEY to an xAI API key from console.x.ai. Ask/Expert cannot publish an answer until that secret is set.", "AI_KEY_MISSING");'
    if opaque in updated:
        updated = updated.replace(opaque, clear, 1)
    return updated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Live app directory containing server.js")
    parser.add_argument("--ai-provider", default="", help="Path to aiProvider.js (defaults to this repo copy)")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    server = root / "server.js"
    if not server.is_file():
        print(f"No server.js in {root}", file=sys.stderr)
        return 1
    provider_src = Path(args.ai_provider) if args.ai_provider else Path(__file__).resolve().parents[1] / "aiProvider.js"
    if not provider_src.is_file():
        print(f"Missing {provider_src}", file=sys.stderr)
        return 1

    server_bak = backup(server)
    provider_dest = root / "aiProvider.js"
    provider_bak = backup(provider_dest) if provider_dest.exists() else None
    try:
        provider_dest.write_text(provider_src.read_text())
        server.write_text(patch_server(server_bak.read_text()))
        for file in (server, provider_dest):
            check = subprocess.run(["node", "--check", str(file)], cwd=root)
            if check.returncode != 0:
                raise RuntimeError(f"node --check failed for {file.name}")
    except BaseException:
        restore(server, server_bak)
        if provider_bak:
            restore(provider_dest, provider_bak)
        elif not provider_bak and provider_dest.exists():
            provider_dest.unlink()
        raise
    print("Patched server.js and aiProvider.js. Set Replit secret XAI_API_KEY, then restart node server.js.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit as exc:
        if exc.code not in (0, None):
            print(exc, file=sys.stderr)
        raise
