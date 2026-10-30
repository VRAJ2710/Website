# deploy-chat92 (on top of live chat91). NOT published. server.js only.
Run in the Replit Shell (never `node server.js`, never Run):  `bash deploy-chat92/deploy.sh --dry-run` then `bash deploy-chat92/deploy.sh`, then Republish.
Base: server b6cff45b… / app 1640cc0d… / index ad60345d… (chat91). Result: server df10e32fb82311423f475c62833d0763; app.js and index.html unchanged (no token bump).
1. Boot SQL (after the chat91 statements, own try/catch, no DDL, idempotent): case-insensitive, case-preserving `Dispatch<sep>Markets -> Dispatch<sep>Market`
   (sep = whitespace, NBSP, &nbsp; &#160; &#xa0;, JSON \n \t \r, hyphen, middle dot, simple inline tags). Not inside words, paths or domains. Fixes QA's
   `THE DISPATCH MARKETS · GOLD &amp; MACRO RESEARCH` eyebrow (from the stored payload; no code source exists).
2. Server-rendered head for /research/capital-sustainability, /method, /{TICKER} (title, description, canonical, og:*, twitter:*), same text as app.js fe88. Unknown ticker -> radar head.
3. /pricing: canonical + og:* + twitter:* tags.  4. Maintenance gate exempts GET/HEAD /manifest.json only.  5. /api/monitor sec.downloads_today / sec.downloads_cap.
Tests: test_boot_sql.out (PGlite), test_harness.out (handler rendered in-process, no listener).
