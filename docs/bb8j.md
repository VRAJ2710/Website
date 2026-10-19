# bb8j: one source assembly and one final assembler for /api/chat (JSON and stream), server only

Stacked on bb8i. server.js md5 `eb6937c7284919ed1a86f7e9d8b87d9c` (15051 lines) becomes `ccab2b5891c284d7d68aeb84c19291c6` (15150 lines).
The patch makes four in-place edits (each anchor matches once) and appends one block (`// ── bb8j ──` … `// BB8J_JS_END`). app.js and index.html are not touched. It adds no tables, intervals, timers, dependencies, secrets or paid feeds.

Apply: `python3 deploy/patch_bb8j.py <folder> --check`, then `python3 deploy/patch_bb8j.py <folder>`. A second run prints REFUSE and exits 0.

## Root cause
- The JSON request store (bb2 `handle`) starts with `clientSources: []`. The bb2 and bb8e "fill if missing" checks treat an empty array as already filled, so they never ran.
- Effect on general JSON answers: they listed no Sources ("No news or price sources were supplied") and kept dangling `[n]`.
- Effect on card JSON answers: the move sources were numbered from [1] instead of after the client sources. The model's numbers then disagreed with the stream's.

## What changed
- **`bb8jSources(body)`**: the stream path's source gathering, `bb3bFilterSources(bb3bRawSources(body), body)`.
  - `bb3bStreamInner` now calls it.
  - The JSON path calls it before prompting, keeping the same "Yahoo Finance" peer split.
  - The JSON prompt lists the same `CITABLE SOURCES` block, in the format of `bb2System`.
- **`bb8jAssemble(reply, store)`**: the one final assembler. Both the stream tail in `bb3bStreamInner` and the JSON finish (`bb2Finish`, called by bb2's `res.end` hook) call it. It runs `bb3bCompose` and its whole wrapper chain:
  - bb8d/bb8g card and valuation rules
  - bb8h citation matching
  - bb8i speculative-claim filter
  - bb8e pruning and contiguous renumbering

  It then adds the `bb2Footer` Sources footer, with a blank line before it and UK times.
- **General answers get bb8h citation matching** on both paths (stream sentence painter and final). Before, bb8h covered only card and valuation.
  - A cite to a news headline that shares the sentence's topic words counts as a match.
  - Other cites are re-pointed or stripped.
  - A figure that no source carries is dropped together with its sentence (the bb8h rule).
- **`[n]` markers are stripped only as a last resort**, when there are no sources at all.
- **Expert mode** uses the same `/api/chat` route (only `hints` differ), so it goes through the same assembler.

## Remaining, documented differences between JSON and stream
- The JSON body carries the model's own `structured.sources` and no top-level `sources` array. The stream's `done` event has `sources`. Both render the same `reply` text.
- Text painted while streaming is renumbered only in the `done` reply. This was already the case; the client renders `done.reply`.
- The Ask/Expert `hints` (length and focus) are applied only on the JSON path. This was already the case.
