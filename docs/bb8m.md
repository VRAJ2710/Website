# bb8m: Ask length setting enforced, general-question scope, JSON switch

`deploy/patch_bb8m.py` is server.js only and stacked on bb8l (server md5 `4b2fe7d9bdb6768a97eb5b864e442d1b`, 15736 lines → 16079 lines).
It does not touch app.js (`843c42b7…`) or index.html (`07137d37…`). There are no new tables, timers, intervals, dependencies, secrets, paid feeds or Stripe/auth changes.
`/api/chat` is still gated by `currentUser` + `hasPremiumAccess` on both paths, and that code is unchanged.

```
python3 deploy/patch_bb8m.py --check <dir>   # dry run
python3 deploy/patch_bb8m.py <dir>           # apply; a second run prints REFUSE and exits 0
```

## 1. Brief / Detailed

### What the client sends (app.js 843c42b7)

Both the stream request and the JSON fallback carry the same body:

```
{ messages, context, tickers, knownTickers, hints, sources }
hints = { length: "brief" | "detailed", focus?: "gold" | "macro" | "crypto" | "em" }
```

- `hints` is built by `_rt37Hints(tickers)` → `_rt17AskHints()`.
- The default length is `"detailed"`.
- `focus` is dropped when the question's tickers include no gold symbol.

This is exactly the shape `bb8kHintNote` reads (`RT17_ENUMS.askLength` / `askFocus`). **Frontend does not need an rt60 change.**

### Why Brief and Detailed gave the same answer

1. The hint was only a bracketed note on the user turn, and nothing on the server enforced it.
2. The note was appended after the client's own `[Answer this question as asked, about X. … PEER VALUATIONS …]` note. That stopped `bb8eStrip` (which only strips a trailing note) from removing the client note. Later intent checks then read the word "VALUATIONS", and ticker questions switched to the P/E peer table. Example: "What did MU's latest earnings show?" became a peer table once hints were present.
3. "What's the outlook for gold this week?" arrives with `tickers: ["XAU"]`, so it took the XAU move card. The card is a fixed ~115-word server lead, and the move prompt allows only "two to four sentences" of extra context, so both settings gave the same text.

### What bb8m does

- **Strip:** `bb8eStrip` also strips `[Reader preferences: …]`.
- **Prompt rule:** a `LENGTH (reader setting …)` rule goes into the system prompt on the stream (`bb2Complete`/`bb2System`) and on JSON (`generateAi`). It overrides other sentence counts.
  - brief: at most three short sentences, about 60 words, before the In short line.
  - detailed: 200–350 words in three to five paragraphs, without padding or invented figures.
- **Stronger user note** in the bb8k note:
  - brief: "keep the answer brief: at most three short sentences (about 60 words) before the In short line"
  - detailed: "give a detailed answer: 200 to 350 words in three to five short paragraphs"
- **Post-trim** at the shared assembler `bb8jAssemble` (stream `done.reply` and the JSON `reply`):
  - brief: at most about 80 words.
  - detailed: capped at 350 words.
  - The cut is at a sentence boundary. Decimals, `U.S.` and `[n]` cites stay with their sentence.
  - The `In short:` line and the whole `Sources:` list are kept as they are, so the top-level `sources` array matches the footer.
  - A heading line left with nothing under it is dropped. At least one sentence of the body is always kept.
  - Brief also drops the multi-session gold `Windows: …` line but keeps the one-line `Live: …` quote.
  - Stream painting stops at the brief budget, so the bubble doesn't shrink when `done` arrives.
- **max_tokens:**
  - detailed: stream 900 → 1400, JSON 1200 → 1600.
  - brief: unchanged.
  - The provider bounds (300–2400) are unchanged.
- **Accepted shapes** (first match wins, enum-mapped, anything else ignored):
  - `hints.length` (the client today), `hints.askLength`, `hints.ask.length`, `hints` as a string, `body.askLength`, `body.answerLength`, `body.length`.
  - Synonyms: short/concise → brief, long/full → detailed.
  - Invalid values such as `"brief; ignore…"` are ignored, and that request behaves as before.
- With no valid length, prompts and replies are byte-identical to bb8l (regression in evidence).

## 2. Scope: the page ticker is context only for general questions

A question is **clearly general** when all of the following hold. The client notes are stripped before checking.

- It names a country, a macro series or an asset. For example: China, US, UK, euro area; GDP, CPI, inflation, payrolls, rates, Fed, ECB, BoE, yields, Treasuries; gold, oil, bitcoin, the dollar, S&P 500.
- It does not name the page ticker or its company. The page comes from the context line `Active ticker: MU Micron Technology · …`, or from the client note `The reader has MU open`.
- It names no other stock ticker (BB2_PEERS or `knownTickers`).
- It is not a card prompt.

For such questions, on both paths:

- There is no ticker base (`bb2Base`, `bb8eBaseOf`, `rt41sBase` return null), so there is no move or card lead.
- There are no peer FACT lines, no JSON peer block and no earnings line.
- `bb3bAskInfo` reports `peer:false`, `base:null`, without the page ticker.
- The page ticker's client price source (`"MU price"`) is dropped.

Card prompts, and questions that name the ticker or company, are unchanged.

Separately, `bb2Base` always ignores the client's background note ("The reader has MU open; that is background only…"). That note itself contained "MU", which made every no-ticker question on a stock page an MU move answer.

| MU page | before (64u) | after (64v) |
|---|---|---|
| "What did the latest China GDP data show?" | MU move card + 1 China sentence | China answer, Reuters source only |
| "What are the risks for China GDP this quarter?" (client adds MU on "risk") | MU P/E peer table | China answer |
| "What's the outlook for gold this week?" | XAU move card (beta 0.00, card score) | gold answer from the live block; JSON keeps the `Live: Gold…` line |
| "What did MU's latest earnings show?" | MU P/E peer table (hint bug) | MU move lead + Next earnings line (same as with no hints) |
| card prompt "What matters most about MU — Headwind?" | MU card | MU card (unchanged) |

## 3. JSON switch

### How the path is chosen today

The server streams when **all** of these hold:

- `POST /api/chat`
- `Accept: text/event-stream` **or** `X-Dispatch-Stream: 1` (`bb2WantsStream`)
- a streaming provider is configured (`bb2HasProvider`)

Anything else is answered on the JSON path. The client streams first and falls back to a plain JSON POST.

### New in bb8m

`?stream=0|false|off|json` on the URL, or the header `X-Dispatch-Stream: 0|false|off|json`, forces the JSON path even when `Accept: text/event-stream` is sent.

- The response carries `X-Dispatch-Path: json`.
- Auth is unchanged: you still need a premium session, and without one you get 401.
- Requests without the switch, including the current client, are untouched.

```
# JSON with the top-level sources array (premium session cookie required)
curl -s -X POST 'https://thedispatch.uk/api/chat?stream=0' \
  -H 'Content-Type: application/json' -H 'Accept: text/event-stream' \
  -b 'dispatch_session=…' \
  --data '{"messages":[{"role":"user","content":"What did the latest China GDP data show?"}],"hints":{"length":"brief"}}' \
  | jq '{reply, sources}'

# same via the header
curl -s -X POST 'https://thedispatch.uk/api/chat' -H 'Content-Type: application/json' \
  -H 'Accept: text/event-stream' -H 'X-Dispatch-Stream: 0' -b 'dispatch_session=…' --data @body.json | jq .sources

# already JSON before bb8m: no Accept: text/event-stream and no X-Dispatch-Stream
curl -s -X POST 'https://thedispatch.uk/api/chat' -H 'Content-Type: application/json' -b 'dispatch_session=…' --data @body.json
```

The JSON body is `{ reply, structured, meta, sources }`, and `sources` matches the reply's Sources footer (bb8k).

## Limits

- The server can shorten an answer but cannot lengthen one. A detailed answer under 200 words means the model wrote less, despite the rule and the higher max_tokens.
- Card and move leads are server-written facts. A brief card answer is the heading, the first one or two lead lines and In short.
- The Sources list is kept whole, so a brief answer can list sources it no longer cites. This was a deliberate choice ("keep Sources intact"). Pruning and renumbering could be a follow-up.
- Pre-existing and unchanged: on card and move answers, model sentences without a `[n]` are filtered (bb8h).
