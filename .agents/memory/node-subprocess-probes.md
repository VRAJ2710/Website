---
name: Node subprocess probes
description: How to keep signal lifecycle regression probes reliable in Node integration tests
---

Use a plain Node child process for signal lifecycle probes when the parent test runner needs to interrupt setup or execution. Keep the child alive with an active event-loop handle and use an explicit readiness marker before sending the signal.

**Why:** A nested `node --test` child can finish or report an unresolved test independently of the signal path, making the parent test flaky or unable to observe the intended shutdown.

**How to apply:** Have the child run the same setup and cleanup functions, write ordered lifecycle markers, and let the parent assert the exit code plus exact resource identity.