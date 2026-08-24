---
name: Neon empty-result quirk
description: Workaround for the hosted Neon HTTP driver returning incomplete metadata on empty result sets.
---

When using the Neon HTTP tagged-template driver, queries that return zero rows can fail while decoding the response instead of producing an empty array. Wrap application lookups in an aggregate that always returns one row, then unwrap the JSON array.

**Why:** Empty account and session lookups triggered a driver decoder error during the persistent-auth rollout.

**How to apply:** Use an aggregate wrapper for optional lookups rather than relying on a zero-row result from a direct SELECT.