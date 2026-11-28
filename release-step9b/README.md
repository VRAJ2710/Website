# release-step9b: fix for chat114viz (the visuals pass on /brief/, /gold/, /markets/, /research/)

Root cause of step 9 "attached but never injects": the block's own last safety check. After building the injected page it compared
the final 24 characters of the page before and after injection (`s.slice(-24)`). The script tag is inserted just before `</body>`,
and on dev the pages end `...Research</a></nav></body></html>`, so those 24 characters always changed and the block silently served
the page unchanged (no log line). The box tests used live copies, which end with Replit's published-hosting analytics tag
`...></script></body></html>`; that happens to end exactly like the inserted `defer></script>`, so the check passed there.
Replit adds that tag after the server responds, so the server never sees it, in dev or in production.

Step 9b replaces the trailing step-9 block. The check now compares everything from the last `</body>` to the end. Same hook point
as chat110navy (http.Server.prototype.emit, per-request res wrappers), same assets (viz.css/viz.js byte-identical), same four
insertions as the approved preview. New logs: `[chat114viz] injected <path>` once on the first page it changes, and up to 3
`[chat114viz] not injected <path>: <reason>` lines.

Usage (Replit Shell, project folder): `bash deploy.sh --measure`, then `--dry-run`, then no flag to apply. Baseline must be the staged
step 9 server.js (md5 8e08169ab4b4f8bc570eda7342ce5756, 2,587,429 B). Expected result: 2,588,699 B (md5 printed by --measure).
Snapshot: .release-snapshots/step9b-<TS>/ with restore_release.py. Tests: test/run_step9b_tests.sh (37 checks).
