# chat97 (on chat96) — built and tested, not published

Applied by the cumulative FINAL deploy.sh (chat99 branch); not run on its own.

- Light / Dark / System theme: header toggle + Settings > Display > Theme; saved in prefs `display.scheme`
  for accounts, localStorage + `dispatch_theme` cookie for everyone; class set before first paint (no flash);
  covers app, site pages, auth, 404 and maintenance; WCAG AA audited at 390 and 1280.
- Gold dashboard `/gold/dashboard/`: gold in $, £, €; gold/silver ratio; DFII10; DGS10; dollar index; WGC links + note.
  Market feeds labelled "Delayed · as of <UK time>".
- Macro calendar `/calendar/`: BLS, BEA, ONS (07:00 UK), Fed, BoE; previous and actual only. Consensus,
  rate-cut odds and transcripts are left out (they need a paid source) and the page says so.
- "What changed today" timeline on /brief/ and the gold dashboard.
- Site AI: Gemini first, OpenAI fallback; xAI is not a site provider any more (readers can still use their own xAI key).
- Leftovers: House filings newest first; DGS10 first in live tables with Yahoo labelled fallback; guest preview
  covers /api/prefs (GET 401 / PUT 403) and the app shows the preview bar; full disclaimer in Settings.
- No new tables, no DDL.
