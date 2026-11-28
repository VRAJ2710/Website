# release-step10: chat115vizapp (visuals layer for signed-in readers in the member app)

Signed-in readers get the member app shell on /brief/, /gold/, /markets/ and /research/, so chat114viz (public pages) never applies.
This step appends one block to server.js (baseline: staged step 9b, md5 9a8758213ee7a63eb5d24757c3aa78f3, 2,588,699 B):

- For a GET with a dispatch_session cookie whose response is the app shell (`<main ... id="main">` + `/app.js?v=`), it adds the
  existing `/__chat114viz/viz.css` link before `</head>` and `/__chat115vizapp/vizapp.js` (served by the block) before `</body>`.
  The shell leaves the handler already brotli/gzip-compressed (rt20s), so the block decompresses that one body, adds the 2 tags and
  recompresses with the same encoding and settings. Anything else (guests, public pages, JSON, errors, non-UTF-8) keeps its bytes.
- vizapp.js mounts the SAME `<section id="chat114viz">` and runs the SAME `/__chat114viz/viz.js` (re-run per new snapshot), at the top of
  the visible page body: #main on phones; on desktop the page overlay body (#briefOv/#goldOv/#researchOv .term-overlay-body) or the
  prices panel (#p1body) for markets. It follows pushState/replaceState/popstate and a MutationObserver, keeps one section, re-attaches
  the already-drawn section when the app re-renders (no refetch), refreshes on route entry after 5 minutes, removes the section and the
  cz-* classes on other routes, and stops itself after 3 errors. app.js is not edited.
- Logs `[chat115vizapp] attached` once and `[chat115vizapp] injected <path>` once (plus at most 3 `not injected` reasons).

Usage (Replit Shell, project folder): `bash deploy.sh --measure`, `--dry-run`, then no flag. Expected result 2,603,237 B (md5 printed
by --measure). Snapshot .release-snapshots/step10-<TS>/ with restore_release.py. Tests: test/run_step10_tests.sh (35 checks).
