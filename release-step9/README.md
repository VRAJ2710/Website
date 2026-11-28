# release-step9: chat114viz, the visuals pass (Market Snapshot, gauges, key prices, sparklines, tiles, events timeline)

Owner approval (Vraj, via Star): "Publish the visuals as shown". This installer packages the preview EXACTLY as previewed
(viz.js and viz.css are byte-for-byte the files QA'd in /workspace/qa-dispatch/visuals-preview/; no gauge is collapsed).
Not staged and not published by the packager.

Changes ONLY server.js: one trailing block (`server_block_chat114viz.js`) appended after the step-8 chat113cookie block. No prefix edit, no new
file in the project, no endpoint, secret, config, schema, Stripe, app.js, index.html, styles.css or c93.css change.

## What the block does
- Serves `GET|HEAD /__chat114viz/viz.css` and `/__chat114viz/viz.js` from two embedded strings (`Cache-Control: public, max-age=300`, ETag, 304 on
  If-None-Match, nosniff). Pages reference them as `?v=chat114viz`; a future change must bump that token.
- For a finished **200 text/html GET without content-encoding** on exactly `/brief/`, `/gold/`, `/markets/`, `/research/` (query strings allowed; the
  no-slash forms are 301s from the app and pass through), it makes the same three insertions as `inject()` in the preview proxy and adds
  `cz-on cz-<page>` to the `<html>` class: stylesheet link before `</head>`, a `<section id="chat114viz">` mount after the first `</section>`
  inside `<main class="wrap">`, a deferred script before the last `</body>`.
- Same wrapper pattern as chat110navy (buffers write/end, recomputes Content-Length after injection, tail of the page and `</html>` unchanged).
  It sits last, so it sees the page after chat110navy, the c102r6p scrub and chat97 length handling have finished.
- Fail-safe: no `</head>`/`<main class="wrap">`/`</body>`, not clean UTF-8, tail changed, already injected, or any exception => the page is served
  byte-for-byte as it was (one `[chat114viz] skipped: ...` log line, max 5). Encoded (br/gzip) responses, non-200s, HEAD and POST are passed through.
- Attaches only if chat113cookie is attached; logs `[chat114viz] attached` once at startup (else `[chat114viz] not attached: ...`).
- The preview proxy's `/sw.js` replacement is NOT shipped (see the service-worker finding in the release notes).

## Installer
`bash deploy.sh --measure | --dry-run | (apply)`; every payload file is sha256-pinned (release_step9.py, restore_release.py, the chat112verifymail and
chat113cookie blocks, the chat114viz block, viz.css, viz.js). It refuses unless server.js is the live step 8 (md5 a633becfed6eb4e12c88415cdccf6fd7,
2,539,589 B), ends with the exact chat112verifymail + chat113cookie blocks, contains no `chat114viz`, the block-derived anchors match,
app.js/index.html/styles.css/c93.css are the live files, and the block embeds exactly the pinned viz.css/viz.js. Snapshot:
`.release-snapshots/step9-<TS>/` (server.js, manifest.json, restore_release.py). Output = step 8 server.js + block, expected size = 2,539,589 + block bytes
(printed by --measure together with the md5).

## Tests
`bash test/run_step9_tests.sh` (box only): block unit tests (`node test/unit_block.js`), guards, apply/restore/re-apply, startup log, 57-route comparison
against step 8, auth pages unchanged, and a Chrome render of the four pages vs the preview proxy.
