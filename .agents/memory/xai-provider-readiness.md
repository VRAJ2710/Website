---
name: xAI provider readiness
description: Credit provisioning requirement for xAI connector inference.
---

A Replit xAI connection proves that credentials are attached, but it does not guarantee that inference is enabled. xAI can return a permission-denied response until the connected team's account has available credits or an active license.

**Why:** A healthy connector otherwise looks like a provider outage and can prevent generated features from being verified.

**How to apply:** When xAI model discovery or generation returns this condition, surface a safe, actionable provider-credits message. Do not request credentials in chat or replace the approved connection.