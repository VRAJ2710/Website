---
name: Stripe connector credential shape
description: Compatibility note for obtaining server-side credentials from the Replit Stripe connection.
---

Use `settings.secret_key || settings.secret` when creating a Stripe SDK client from the Replit connection API.

**Why:** The current managed Stripe connection returned its server secret under `secret`, while older integration setup material used `secret_key`.

**How to apply:** Keep credential handling server-only, never log values, and support both field names when updating the Stripe client helper.