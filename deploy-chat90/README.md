# deploy-chat90 — brand rename "The Dispatch Markets" -> "The Dispatch Market"

Applies on top of live chat89: server.js 03fd66ca2c1ddac8417fcb0ed8e37414, app.js d45e0c8d6cb77fceb437ca9db6dfa73c, index.html 8987d0ba0999841844da72d9381ad2f0 (v=chat89).
Brand text only. Line 1 `BB10I_MAINTENANCE_ON = true` stays. Rate limiter / auth / Stripe / data code untouched. Never starts the server, never touches git/DB/.replit/package.json/env/Stripe/npm. Click Republish yourself afterwards.

## Run in the Replit Shell (from the project folder)
    curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/deploy/jack-chat90-brand/deploy-chat90/deploy.sh -o /tmp/deploy90.sh && echo "f0f91d9c6ce2bdd7f76ed8a0558b99e7f53df0179b370a2aa2faac3636749ae8  /tmp/deploy90.sh" | sha256sum -c - && bash /tmp/deploy90.sh --dry-run
    bash /tmp/deploy90.sh

Second run: "REFUSE: already applied". Any base md5 / patch sha256 / result mismatch aborts before touching live files.
Also edits (backup first) manifest.json and llms.txt next to server.js if present (literal brand replace only), and replaces og-card.png only if it is byte-identical to the known live card (md5 a2bd86fb...); otherwise leaves it and says so.
Backups: <file>.<YYYYmmdd-HHMMSS>.bak-chat90. Rollback = copy backups back, Republish.

## Expected results
| file | md5 | sha256 | replacements |
|---|---|---|---|
| server.js | 357d8300e6041fbee752ff6f10ee0a93 | e45f00b020c5eb4986ba9ed938ac5e719624b57292e7dc786a0b0d078cc11cff | 45 |
| app.js | 9caddff097af8e72adab562746973603 | 5e7e6c6dc2cacb482d6366fbbfdbced8e9d55e8007e098b85e5eb246fcaec474 | 16 |
| index.html | 65a78b0a630a306780d22708a2120590 | 5fe42feae40a13a2400d940569e1e09dbc48aa0c6de59c913e4f258db265ab75 | 14 (+ app.js?v=chat89 -> chat90) |
| manifest.json (known version 99759344...) | cd743da093cf288f530610d11576f381 | | 1 |
| llms.txt (known version b4dba7c8...) | 9a73ee75f3d6a92df10b5923d8879046 | | 3 |
| og-card.png | fac1f0a45e62f33b33e5e8f3dfd1d1f4 | cae73e252de7e7aa31b7183fc2624e9c89634708e1ec9192258dea5b7fef8a70 | last letter S of "MARKETS" painted out |

patch_brand.py sha256 4650c6b0ebe804c934f9739617dd8e26a8d705fac63ade6247df76d60fe11d26. replacements.txt = every changed line (before/after), review only.

## Deliberately left alone
- User-Agent / identifiers: "DispatchMarkets/1.0" (server.js 582 SEC UA, 1861, 3761, 5179, 7494), "TheDispatchMarkets admin@thedispatch.uk" (11716). SEC UA is a compliance identifier; renaming is a separate call.
- Generic "Markets": nav items, /markets/ routes, "Crypto Markets" page title, "Markets" panels, llms.txt "[Markets](.../markets/)", "market(s) research", tagline "Gold & Macro Research", CSS classes (logo-markets, cmd-logo-market), ids, localStorage keys, API paths, dispatch_market_data_coordination.
- Not shipped / not live copy: styles.css header comment, README.md, replit.md, package.json "description", og-card.svg (unused, og:image is the png).
