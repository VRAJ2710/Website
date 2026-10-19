# bb8e: card Ask relevance, cited-only sources, House note, opening window, brief timestamp

Server-only patch, stacked on server.js md5 `e0a1e5ea2ba975298bd9a2177abd5a6f` (bb8d). Apply with
`python3 deploy/patch_bb8e.py <folder>` (`--check` is a dry run). It adds no tables, intervals, dependencies, secrets or paid feeds.
`app.js` and `index.html` are not changed.

1. **Ask relevance.** Intent is worked out by fixed rules, without a model call. Card questions ("What matters most about MU — Headwind?", or `card`/`intent` in the body)
   and questions that aren't about valuation are *move* questions. The answer leads with server-computed facts: the session move, the move against SPY (or the home index)
   and the sector ETF, the card-score reason and up to two neutral Yahoo RSS headlines (from the existing rt37s feed, marked "not confirmed as the cause").
   There is no peer block, rt41s PEER VALUATIONS or "In short" line. Only valuation and peer questions keep the bb8 peer block and "In short".
   The client's trailing "[Answer this question as asked… PEER VALUATIONS…]" note is no longer read as intent.
2. **Contradiction filter.** A whole sentence is dropped when it calls a valuation figure (P/E, P/S, P/B, EV/EBITDA, multiples, cheap/expensive) a headwind or tailwind.
   It uses the bb8d sentence splitter. The system prompt carries the same rule.
3. **Citations.** The Sources list holds only the sources the text cites, in their original order, renumbered 1..n. `done.sources` and the JSON `sources` match it.
   The peer header no longer ends in [n]: the cite moves to the last fact line and the "In short" line.
4. **House note.** "Each filing links to the official House disclosure (PDF)."
5. **Opening window.** A cash venue that has opened is checked with the real open time (bb6 holidays apply, and the reopen after a lunch break counts).
   If it has no price from this session yet, then from the open until open + delayMin + 20 min it reads `status: "delayed"` (unchanged, so older clients still work),
   with `phase: "opening"`, `stale: false`, `firstPriceAt` (ISO, open + delayMin) and `note: "opening · first prices due HH:MM UK"`.
   bb5h stale thresholds don't fire inside the window. Open quotes also carry `lagMs` = now − delayMin − quote ts (age on the delayed clock).
   **Frontend follow-up:** the "quiet (open, no new price for 20 min)" bucket is computed in the client (`_rt51Brk` → `_rt39Live`, wall clock).
   It should treat `phase === "opening"` as opening and use `lagMs` for the 20-minute rule.
6. **Brief timestamp.** `POST /api/brief` returns `generatedAt` (ISO) and `generatedAtUk` ("Mon 19 Oct, 07:05 UK"), both at the top level and inside `brief`.
   They are stamped when the brief is generated, and the client's stored brief keeps them. `/api/academy-daily` already returns `generatedAt` and `asOf` from its build time.

Tests: `node --test test/bb8e.test.js` (12 tests).
