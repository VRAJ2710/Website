# bb8d: server-built Ask conclusion and UK time everywhere

Stacked on bb8c (server md5 `2d807112acf22009af0fa09da742f94c`). Server-only. app.js and index.html are unchanged.

Apply: `python3 deploy/patch_bb8d.py <folder>` (use `--check` for a dry run). Running it a second time prints REFUSE and exits 0. CRLF-safe.

Result: server.js md5 `e0a1e5ea2ba975298bd9a2177abd5a6f`, 13407 lines.

No new tables, intervals, dependencies, secrets, paid feeds or Stripe changes. Every new top-level function starts with `bb8d`.

## P1: deterministic conclusion (stream and JSON paths)
- When the answer has peer facts (bb2BuildFacts), the final reply is rebuilt in three parts:
  - the server lead (peer comparison lines);
  - the cleaned model body;
  - a server-built `In short:` line.
- The verdict comes only from the fact numbers and is appended after every filter. It never passes through one.
- Cases, per basis (next-12-month forward first, then trailing TTM):
  - cheapest: "MU is the cheapest of its peers at 4.9x, against 13.6–45.2x";
  - most expensive;
  - in line;
  - in the middle: "sits in the middle of its peers at 12.0x: below B (15.0x), above A (8.0x), in line with C".
- Missing data gives notes such as "INTC's trailing P/E (TTM) isn't reported", "X's forward P/E isn't reported" or "trailing P/E (TTM) isn't reported for A and B". The wording is neutral: no buy/sell calls, no targets, no "undervalued" or "opportunity".
- The body filter drops whole sentences only. The splitter is bracket-aware and does not split at decimals or initials ("U.S."). It also splits run-on joins such as "x).Next". A sentence is dropped when it:
  - is a model conclusion ("In short", "In conclusion", "Overall"…);
  - is a dead-end or different-bases sentence ("cannot directly compare", "not compared");
  - uses banned wording;
  - is filler;
  - has unbalanced brackets, `**` or quotes;
  - is a fragment;
  - mixes trailing and forward numbers;
  - quotes P/E multiples that aren't in the facts.
- bb2FixSentence no longer inserts "Trailing P/E (TTM) and forward P/E are different bases and are not compared." (that insert caused "Micron (Trailing…").
- Stream path: the bb2Complete wrapper keeps the raw model text for the final reply. It paints only whole cleaned sentences and stops at the model's own Sources. The `done` reply (the final replace event) and the JSON reply both use the same compose step.
- Answers without peer facts keep the existing path. Only their timestamps change.

## P2: UK time
- Every "as of" or timestamp in Ask text is shown as `Fri 16 Oct, 21:00 UK` (Intl, Europe/London, so BST and GMT are both handled). This covers:
  - the lead and peer comparisons;
  - the Sources footer;
  - the system prompt;
  - the live market block.
- Quote notes ("opens …", "early close …", "updated …") use the same day/date/time format.
- Machine JSON fields (ISO `ts` and `asOf`) are unchanged. Only text is rewritten.

## Tests
`node --test test/bb8d.test.js` (8 tests, offline). It covers:
- the stream path in chunks of 1–29, including chunks that split mid-bracket and mid-sentence;
- the JSON path;
- garbled input;
- all verdict cases;
- the splitter;
- BST and GMT formatting;
- the no-facts path.
