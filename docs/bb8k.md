# bb8k: Ask/Expert reader hints on both /api/chat paths; JSON body `sources` (server only)

Stacked on bb8j. server.js md5 `ccab2b5891c284d7d68aeb84c19291c6` (15150 lines) becomes `0510fe845e43ec1e865dbc4257b00418` (15197 lines).
The patch makes two one-line inserts (each anchor matches once) and appends one block (`// ── bb8k ──` … `// BB8K_JS_END`). app.js and index.html are not touched. It adds no tables, intervals, timers, dependencies, secrets or paid feeds.

Apply: `python3 deploy/patch_bb8k.py <folder> --check`, then `python3 deploy/patch_bb8k.py <folder>`. A second run prints REFUSE and exits 0.

## What the client sends
`sendChatMessage` in app.js sends the same body to both paths: `{ messages, context, tickers, knownTickers, hints, sources }`.
- The stream request adds `Accept: text/event-stream` and `X-Dispatch-Stream: 1`.
- The JSON fallback uses the same body.
- `hints` is the reader's Ask setting, `{ length: brief|detailed, focus: gold|macro|crypto|em }` (`_rt17AskHints`). `_rt37Hints` drops `focus` when the question names non-gold tickers.

There is no separate Expert mode flag. Every `/api/chat` answer is "Dispatch Expert": the client gates it with `_isPremium()`, and both server paths check `currentUser` and `hasPremiumAccess` before reading the body (401 "Premium membership required"). bb8k does not change the gate.

## 1) Hints on both paths
- Before: only the JSON route applied the hints (`rt17ApplyChatHints`, which appends `[Reader preferences: …]` to the latest user turn). The stream path ignored them.
- Now one builder serves both:
  - `bb8kHintNote(hints)` builds the note from the same validated enums with the same text; free text never passes.
  - `bb8kApplyHints(body)` applies it once per body: latest user turn, same 7800-character clip.
  - `rt17ApplyChatHints` delegates to it.
  - `bb3bStreamInner` calls it right after reading the body, at the same point the JSON route does.

## 2) JSON body `sources`
The JSON body now has a top-level `sources`. It is the list the final Sources footer printed (`bb8jAssemble`): the same objects, order and numbering as the stream's done-event `sources`. `structured.sources` (the model's own list) is unchanged.

## 3) JSON CITABLE SOURCES in UK time
bb8j's JSON prompt list printed ISO times. It now prints UK times, as the stream prompt does.

## Documented prompt differences, stream vs JSON (same hints, same body)
- **Messages are identical**, including the hint note.
- **CITABLE SOURCES lists are identical.** The JSON list is followed by one extra bb8j line ("Cite a source only for what its line says…").
- **The system prompt bases differ, as before.**
  - The stream uses `bb2System`: "You are Dispatch Expert, a market-research assistant…", TERMINAL CONTEXT, and the bb3/bb3b/bb8b/bb8d rules.
  - The JSON route uses `MARKET_SYSTEM` plus `buildChatLiveMarketBlock` (live gold / 10y block) and its JSON reply format.
  - The bb8e/bb8g/bb8i rule lines and the card facts block are shared.
  - For valuation, the JSON route adds its own PEER VALUATIONS block and a UTC-stamped AUTHORITATIVE PEER COMPARISONS block, where the stream's block is in UK time.
- None of these differences are mode-specific; they were already there and bb8k does not merge them.
