# Fold of rt patches into source (chat56)

Production (`thedispatch.uk`, Replit Autoscale, build chat56) was the result of running `deploy/patch_rt*.py` on top of files that had already left this repo. On `rt9-patch` the patch scripts lived beside an older `app.js` / `index.html` / `server.js`. This branch puts the served client bytes in the tree and keeps an approximate `server.js`.

The scripts were applied, in git introduction order, to a scratch copy of the `rt9-patch` files. Each script was read first. They rewrite only the path they are given, plus `node --check`. `patch_rt20s.py` can start `node server.js` when passed `--selftest`; that flag was not used. Nothing here was deployed, and `server.js` was not executed.

The 83 scripts now live in `deploy/archive/` so a later deploy does not run them again on top of the folded tree. `deploy/founder.jpg` stays put.

Current script text was used. `patch_rt37.py` is the expanded script (applied once). The earlier server-only `patch_rt43b.py` was rewritten in git into the client script plus `patch_rt43bs.py`; only those surviving files were run. `patch_rt18s2.py` is byte-identical to `patch_rt18s.py`.

## Client parity

Checked with `md5sum -c` against the chat56 manifest. Live `curl` of `/`, `/app.js?v=chat56`, `/styles.css?v=chat1`, and `/sitemap.xml` returned the same four md5s during this fold.

| file | md5 | vs manifest |
| --- | --- | --- |
| index.html | c688363b4b777ed022c4ae1def68a77c | match |
| app.js | b9d3d0a3fc9cbd3e094ec28245f3285e | match |
| styles.css | 8023e711df4aaadbab1e1b4264bfd8c5 | match |
| logo-mark.svg | ff0e681027bc672d6fd12abe04ab7274 | match |
| og-card.png | a2bd86fb5760361cc879178b1302d38c | match |
| founder.jpg | a702682fe38d214a0cfa219fbfd3f3c6 | match |
| manifest.json | 99759344788b05ccb3b448a28cc6934d | match |
| robots.txt | e91e216e60815614c6ad9c51573d22a2 | match |
| sitemap.xml | ebce323946d1d1245553d774b93901db | match |
| llms.txt | b4dba7c8029ea83b9d92dcc36beb90e6 | match |
| pricing/index.html | 4234aeb768daba70f70458a73e985478 | match |
| brief/index.html | 012a0d90df31b549c4bd6c5191111ee6 | match |
| playbook/index.html | 83b1721f56f3fb2853a3866437eaa922 | match |
| gold/index.html | dc5c6aacda41149c7e4164f8a6d50cda | match |
| markets/index.html | b730b28affc3dc40d41dc1c585eace4a | match |
| news/index.html | 142a70ff7f7ed39d70c6d48a82d8d663 | match |
| research/index.html | a7b1c2feb631e58de97ffc49b58987da | match |
| signals/index.html | 7a10afba3bd129c7d9ec1dbfcb79ff20 | match |
| dashboard/index.html | 0510ac28f823c3f030399326c771f175 | match |
| learn/index.html | 708f61279085a0faf2ac520fcf4ac4d7 | match |
| portfolio/index.html | 103f9d319d05cf6e4977cc9d78094591 | match |
| watchlist/index.html | ea2c777b9a868d9f9397738a3a5bd64b | match |
| lab/index.html | 8539903b8422266636892dc04ccfe81a | match |
| screener/index.html | 05f22b02544c5bd814780d7a6cae116d | match |
| sectors/index.html | 2149d18b249ece096b00f323958c5261 | match |
| heatmap/index.html | 72a0a0424ef5ac4ef50e7910c83fe77e | match |
| crypto/index.html | d9b062b78be581922654f2a58cc9c616 | match |
| paper/index.html | e05cb19f0a6e5dbba4899ba5a3ec17ec | match |
| geo/index.html | d8e15d9720a9edc8cd32bf446cb9fbeb | match |
| brief/dispatch-brief/index.html | 151b9acb387a8619733c746707062ac1 | match |
| report/spx2026/index.html | 4a59a20f76dfdea9b179d313bb91ea1f | match |
| research/research-desk/index.html | eec0eee2ec06287f502e714e18ec05da | match |

No client patch wrote a file. The repo base is not the chat8 tree the first script requires (`app.js?v=1786750800` in `index.html`, and `_quoteMeta` uses `if (src === "coingecko")` where the script looks for `} else if (src === "coingecko")`). Every later client script then misses the previous chat marker. Those files were replaced with the served bytes.

`logo-mark.svg`, `manifest.json`, and `robots.txt` were already identical on `rt9-patch`. No script rewrites them.

No script writes `styles.css`, `sitemap.xml`, `llms.txt`, `og-card.png`, or the route `index.html` files. `styles.css` and `sitemap.xml` differed from prod; the others were absent. All of them are the served bytes.

`founder.jpg` matches `deploy/founder.jpg` (md5 `a702682f…`, sha256 `568f5182…`). `patch_rt49about.py` did not run. The JPEG embedded in that script is a different file (sha256 `1f881f1f34d3383351a76d7d063690e449737e9498b18a0779143ab8f74afafd`); the script refuses to overwrite a photo that is already present, which is how production kept `deploy/founder.jpg`.

## Server (approximate, unverified)

`server.js` is an approximate reconstruction. It was not compared to production, because production does not serve it. `node --check` passes. The file was not started.

### Patches that changed server.js

| patch | what landed |
| --- | --- |
| patch_rt24s.py | `safeText` word-boundary clip |
| patch_rt25s.py | part C only (CoinGecko 429 backoff). Part A skipped because rt24s was already present. Part B skipped (anchor below) |
| patch_rt29s.py | part A (CoinGecko stale-while-error). Part B skipped (anchor below) |
| patch_rt32s.py | `/api/financials` stub replaced; helpers appended |
| patch_rt33s.py | parts D (both) and E. Parts A, B, C, F skipped (anchors below) |
| patch_rt34s.py | auth Terms / Privacy links |
| patch_rt37s.py | ticker-news route, CoinGecko 24h rule, premium-active |
| patch_rt38s.py | CoinGecko aged pass-through |
| patch_rt41s.py | server-side peer valuations wrap of `generateAi` |
| patch_rt42s.py | ticker URL redirects and Ask latency guard |
| patch_rt43s.py | `/pricing`, `/upgrade`, `/api/spot-energy`, terms copy, monkeypatches |
| patch_rt43bs.py | `/api/ext-hours` and pricing admin note |
| patch_rt43d.py | energy spot off unless `RT43D_TD_ENERGY=1` (rt43c had not applied; the script allows that) |
| patch_rt43es.py | pricing "Cancel any time" copy |
| patch_rt44s.py | `/api/eia-spot` |
| patch_rt48s.py | `/api/academy-daily` inserted, then replaced by the next two |
| patch_rt48bs.py | academy-daily block replaced (matched the rt48s block) |
| patch_rt48c.py | academy-daily block replaced (matched the rt48bs block) |

### Patches that failed to anchor

Repo file, script, anchor that was not found (match count 0 unless noted). Where a script aborts the whole write, nothing from that script is in `server.js` or the client files.

**Client chain (nothing written).** Root miss is `patch_realtime.py` against `app.js` and `index.html`:

- `quoteMeta stream branches`: `} else if (src === "coingecko") {\n    status = "live";\n    label = "LIVE·CG";`
- `quoteMeta stream stale window`: `: src === "coingecko" ? 10*60*1000`
- `quoteSourceLabel streams`: `if (!src) return "unknown feed";`
- `front door PAXG line`: `<div class="front-door-quote-meta">${_escHtml(provenance)}${meta.asOf ? \` · as of ${_escHtml(_fmtAsOf(meta.asOf))}\` : ""}</div>`
- `crypto as-of note`: `Delayed \u00b7 as of ${_cryptoAsOf.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}</div>\`;`
- `cache-bust chat8 -> chat9`: `/app.js?v=chat8"`

Every following client script stopped on the previous layer, which was never written:

| patch | anchor that was absent |
| --- | --- |
| patch_rt10.py | `REALTIME PRICE LAYER (rt9)` and `app.js?v=chat9` |
| patch_rt11.py | `REALTIME PRICE LAYER (rt10)` and `app.js?v=chat10` (server edits not attempted) |
| patch_rt11b.py | same chat10 precondition (alternate server anchors for a legacy `yahooQuote`; not attempted) |
| patch_rt12.py | rt11 marker and `app.js?v=chat11` |
| patch_rt13.py | rt12 marker and `app.js?v=chat12` |
| patch_rt14.py | rt13 marker and `app.js?v=chat13` |
| patch_rt16.py | rt14 marker and `app.js?v=chat14` |
| patch_rt17.py | rt16 marker and `app.js?v=chat15` |
| patch_rt18.py | rt17 output (`app.js?v=chat16`) |
| patch_rt19.py | rt18 output (`app.js?v=chat17`) |
| patch_rt19b.py | rt18 output (`app.js?v=chat17`); favicon skip never reached |
| patch_rt20.py | rt19 output (`app.js?v=chat18`) |
| patch_rt21.py | rt20 output (`app.js?v=chat19`) |
| patch_rt22.py | rt21 output (`app.js?v=chat20`) |
| patch_rt23.py | rt22 output (`app.js?v=chat21`) |
| patch_rt24.py | rt23 output (`app.js?v=chat22`) |
| patch_rt26.py | rt24 output (`app.js?v=chat23`) |
| patch_rt27.py | rt26 output (`app.js?v=chat24`) |
| patch_rt28.py | rt27 output (`app.js?v=chat25`) |
| patch_rt30.py | rt28 output (`app.js?v=chat26`) |
| patch_rt31.py | rt30 output (`app.js?v=chat27`) |
| patch_rt32.py | rt31 output (`app.js?v=chat28`) |
| patch_rt33.py | rt32 output (`app.js?v=chat29`) |
| patch_rt34.py | rt33 output (`app.js?v=chat30`) |
| patch_rt35.py | rt34 output (`app.js?v=chat31`) |
| patch_rt36.py | rt35 output (`app.js?v=chat32`) |
| patch_rt37.py | rt36 output (`app.js?v=chat33`) |
| patch_rt38.py | rt37 output (`app.js?v=chat34`) |
| patch_rt39.py | rt38 output (`app.js?v=chat35`) |
| patch_rt40.py | rt39 output (`app.js?v=chat36`) |
| patch_rt41.py | rt40 output (`app.js?v=chat37`) |
| patch_rt42.py | rt41 output (`app.js?v=chat38`) |
| patch_rt43.py | rt42 output (`app.js?v=chat39`) |
| patch_rt43b.py | rt43 output (`app.js?v=chat40`) |
| patch_rt43e.py | rt43b output (`app.js?v=chat41`) |
| patch_rt44.py | rt43e output (`app.js?v=chat42`) |
| patch_rt45.py | rt44 output (`app.js?v=chat43`) |
| patch_rt45b.py | rt45 output (`app.js?v=chat44`) |
| patch_rt46.py | rt45b output (`app.js?v=chat45`) |
| patch_rt46b.py | rt46 output (`app.js?v=chat46`) |
| patch_rt47.py | rt46b output (`app.js?v=chat47`) |
| patch_rt47b.py | rt47 output (`app.js?v=chat48`) |
| patch_rt49about.py | `const _a11yDialogState` |
| patch_rt48.py | rt47b output (`// ── rt47b ──`) |
| patch_rt50console.py | `function _rt19AiHtml(` (aborted before the server anchors were tested; nothing written) |
| patch_rt48b.py | rt48 output (`// ── rt48 ──`) |
| patch_rt48d.py | rt48b output |
| patch_rt48e.py | rt48d output |
| patch_rt51.py | `// ── rt43` and `function _rt43eReady(` |

**Server scripts that missed anchors** (`server.js` unless noted):

| patch | anchor |
| --- | --- |
| patch_rt15.py | `const YAHOO_CHART_CACHE_MS = 30_000;` |
| patch_rt15.py | the `/api/gold-desk` handler that starts `if (p === "/api/gold-desk") {` and calls `generateAi` with the gold-desk snapshot (whole edit must match once) |
| patch_rt15.py | `  validateGoldDeskResponse,\n  normaliseGoldDesk,\n` |
| patch_rt17s.py | required context `"\/api\/ai-status"` |
| patch_rt17s.py | `await sql\`CREATE TABLE IF NOT EXISTS dispatch_editorial_audit (` |
| patch_rt17s.py | `function isAdminUser(user) {` |
| patch_rt17s.py | `if (p === "/api/me" && req.method === "GET")` |
| patch_rt18s.py | `  attachSecurityHeaders(res);\n  if (writeCanonicalHostRedirect(req, res)) return;\n` |
| patch_rt18s2.py | same anchor as rt18s (the two scripts are identical) |
| patch_rt19s.py | same `attachSecurityHeaders` / `writeCanonicalHostRedirect` pair (the script names this the handle() anchor) |
| patch_rt20s.py | same `attachSecurityHeaders` / `writeCanonicalHostRedirect` pair |
| patch_rt21s.py | `if (!headlines.length) return json(res, 400, { error: "Supply between 1 and 20 headlines." });` followed by `const result = await generateAi({` |
| patch_rt22s.py | `    eyebrow: "THE DISPATCH MARKETS · GOLD & MACRO RESEARCH",` |
| patch_rt25s.py | part B: `  if (RECOVERY_SENDER_PREFLIGHT) await runRecoverySenderPreflight();\n` (part C still applied) |
| patch_rt29s.py | part B anchors `try { result = await generateAi({ system: MARKET_SYSTEM + "Score ONLY these supplied headlines."` and `} catch (rt21sErr)` (both absent; part A still applied) |
| patch_rt33s.py | yahoo-quote block beginning `const clientAddress = req.socket?.remoteAddress \|\| "unknown";` plus `yahooRateLimiter` and `Too many Yahoo symbols requested.` |
| patch_rt33s.py | `if (!yahooChartRateLimiter.allow(clientAddress))` |
| patch_rt33s.py | `const yahooChartRateLimiter = new FixedWindowRateLimiter({ limit: 30, windowMs: 60_000, maxKeys: 256 });` |
| patch_rt33s.py | `const yahooRateLimiter = new FixedWindowRateLimiter({ limit: 30, windowMs: 60_000, maxKeys: 256 });` |
| patch_rt33s.py | `return json(res, 200, { brief: result.validated \|\| validateBriefResponse(result.text), cached: false,` |
| patch_rt33b.py | yahoo-quote block that returns `Invalid Yahoo symbols requested.` (the rt33s block, which would have rewritten this region, also missed) |
| patch_rt35s.py | `or start your Premium checkout.</p>` |
| patch_rt36s.py | screener description `Run free market screens across supported quotes…` |
| patch_rt36s.py | sectors description `Review free sector rotation…` |
| patch_rt36s.py | heatmap description `Scan market breadth…` |
| patch_rt36s.py | crypto description `Review free crypto market rankings…` |
| patch_rt36s.py | geo description `Review free geopolitical and chokepoint context…` |
| patch_rt39s.py | `if (/gold\|xau\|level\|support\|resistance\|macro/i.test(_lu) && Number.isFinite(sn.goldLast))` |
| patch_rt42b.py | refused because `// rt42s: pretty ticker URLs` was already present (see below); the insert anchor was not the failure |
| patch_rt43c.py | `const twelveDataAllowedSymbols = ` |
| patch_rt43c.py | `const TWELVE_DATA_COORDINATION_KEY = ` |
| patch_rt43c.py | `dispatch_market_data_coordination` |
| patch_rt45s.py | `title: "Learn \| Market Analysis Frameworks \| The Dispatch Markets",` (script stops on the first miss; the description and h1 anchors were not tested) |

`patch_rt29s.py` part B looks for the news-scores handler shape that `patch_rt21s.py` would have produced. That earlier patch had already failed, so part B had nothing to wrap. The two missing strings are `        try {\n        result = await generateAi({\n          system: \`${MARKET_SYSTEM}\\nScore ONLY these supplied headlines.` and `          },\n        });\n        } catch (rt21sErr) {`.

### Order notes

- `patch_rt42s.py` part A inserted `// rt42s: pretty ticker URLs`. `patch_rt42b.py` is documented as running after rt42s, but it exits immediately when that marker is present, so its own insert (after `writeCanonicalRedirect`) did not run. The approximate server has the rt42s redirects.
- `patch_rt25s.py` was written for a production server where rt24s had been rolled back. Here rt24s applied, so part A was skipped as already present and only part C was new. That is the repo sequence, and it differs from the history the script's comment describes.
- `patch_rt43d.py` applied after `patch_rt43c.py` refused. rt43d's own comment allows rt43c to be absent. The shared Twelve Data credit budget from rt43c is missing; the energy-off switch from rt43d is present.
- `patch_rt48s.py`, `patch_rt48bs.py`, and `patch_rt48c.py` ran in that order and each replacement matched the previous block. That chain is consistent.
- `patch_rt11.py` and `patch_rt11b.py` are two versions of the same client step. rt11b adds legacy `yahooQuote` server anchors. Both stopped on the missing chat10 client, so neither server edit ran.
- Client scripts after `patch_realtime.py` failed in order because that first write never happened. They were not applied out of sequence.
