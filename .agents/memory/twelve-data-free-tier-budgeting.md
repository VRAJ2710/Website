---
name: Twelve Data free-tier budgeting
description: Free-plan constraints for the server-side Twelve Data core equity and FX tape.
---

Treat the Twelve Data Basic plan as a tightly budgeted shared resource: a multi-symbol quote request can consume credits per requested symbol, so keep the public app to a small fixed core and serve it through one server-side shared cache.

**Why:** The plan's per-minute and daily credit ceilings can reject a broad dashboard request even though a small quote request succeeds. Calling the provider directly per browser, or accepting arbitrary symbols, would exhaust the shared account quickly.

**How to apply:** Keep the quote route allowlisted, preserve a cache longer than the polling cadence, and retain delayed Yahoo fallbacks for broader equities, rates, and commodities. When changing the core set, calculate both its per-request credit cost and the cache-refresh budget before increasing it.