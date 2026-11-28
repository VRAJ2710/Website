# Box-only: Chrome cookie jar under production flags (HTTPS + Secure + Domain=thedispatch.uk).
# Expects the tiny HTTPS proof server on 127.0.0.1:$CK_PORT (started by run_step8_tests.sh).
import asyncio, os, sys
from playwright.async_api import async_playwright

PORT = os.environ.get("CK_PORT", "18444")

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(
            executable_path="/usr/bin/google-chrome",
            args=["--no-sandbox", "--ignore-certificate-errors",
                  "--host-resolver-rules=MAP thedispatch.uk 127.0.0.1"],
        )
        out = {}
        for path in ("/register", "/subscribe-bug", "/subscribe-fix"):
            ctx = await b.new_context(ignore_https_errors=True)
            pg = await ctx.new_page()
            await pg.goto("https://thedispatch.uk:%s%s" % (PORT, path), wait_until="domcontentloaded")
            body = (await pg.inner_text("body")).strip()
            jar = [(c["name"], c["value"], c.get("domain")) for c in await ctx.cookies()]
            sess = [c for c in jar if c[0] == "dispatch_session"]
            created = [c for c in jar if c[0] == "dispatch_account_created"]
            out[path] = {"body": body, "session_values": [c[1] for c in sess], "account_created": bool(created)}
            print(path, "body=", body, "session=", [v[:8] + "…" if len(v) > 8 else repr(v) for v in out[path]["session_values"]], "account_created=", bool(created))
            await ctx.close()
        await b.close()
        tok = "ab" * 32
        assert out["/register"]["session_values"] == [tok], out["/register"]
        assert out["/register"]["account_created"] is False
        # Bug: Chrome stores an empty session cookie (or none), never the token.
        assert tok not in out["/subscribe-bug"]["session_values"], out["/subscribe-bug"]
        assert out["/subscribe-bug"]["account_created"] is True
        # Fix: one session token plus the account_created cookie.
        assert out["/subscribe-fix"]["session_values"] == [tok], out["/subscribe-fix"]
        assert out["/subscribe-fix"]["account_created"] is True
        print("ALLOK chrome_cookies.py")

asyncio.run(run())
