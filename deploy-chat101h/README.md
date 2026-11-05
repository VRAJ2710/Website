# deploy-chat101h

Publishes three sourced notes in the existing Research section of The Dispatch Market, on top of the live chat101g build. Line 1 of `server.js` stays the maintenance-off line. No database change, no Stripe change, no service-worker change, and the server is not started.

## What is published

| Path | Kind |
| --- | --- |
| `/research/bank-rate-energy-shock-sterling-gold/` | Timely analysis. Bank Rate 4%, up 0.25 percentage points, vote 8–1, meeting ending 4 November 2026. Rechecked on the Bank of England site at 20:01 UK (GMT), 5 November 2026. |
| `/research/gold-real-yields-breakeven-inflation/` | Evergreen explainer. Federal Reserve TIPS methodology. No current yield. |
| `/research/central-bank-gold-reserves-value-volume/` | Evergreen explainer. IMF reserve-template guidelines. No current reserve total. |

The Research hub keeps the Capital Sustainability Monitor, Check and plan, and Also from the desk. Signed-in Research desk keeps its existing reports and gains the same three links at the top. Byline is the site line “Edited by Vraj Patel”. Each page shows “Not investment advice. Capital at risk.”

## Live base this script requires

Checked against https://thedispatch.uk on 5 November 2026 before the patch was written:

- `app.js` md5 `0b4c442a055584920d9539fb50c9a7f1` (downloaded and matched)
- `c93.css` md5 `9d6a86a64135b1cc58e6af7b12973550` (downloaded and matched)
- `server.js` md5 `6f4266e5439b000710b218785b1007bc` and sha256 `2507caad03ec81b57436de8c4a7610cdcf2c82a5e7d613d95f203f079c18a57e` (chat101g left the chat101f server unchanged; the file is not public)
- `index.html` md5 `4b7ffe2b91d4bd3c8438cf62d81df5e9` and sha256 `0a5f2834eaf5c9147106d63baf364e8759ed6adda8a2af17a6437e5b1ccfc22d`

Resulting `app.js` md5 `6c8ddd1be4db078df1de146163f99b11`, sha256 `80954f1cfde5add82ee75d9b783e3740c799e1fb8237bc8f01881a5514fbf989`. The app block was not changed by the London scrub, so this hash still stands.

Patch sha256: `patch_c101h.py` `958fd7f71273c37ca532afca283e58c70610755e8542e4bb2ae85ef9dc768b07`, `server_block_c101h.js` `f8d60e6d7814374ba60c174ac07b179fa7808da0e5937c204838ceaf2a043db6`, `app_block_c101h.js` `d3ea0f5453b9dfa38d93da83de4395c82d5f0bb5225c008532e51c7fe651805b`. The byline in the articles is “Edited by Vraj Patel”.

`server.js` and `index.html` are not given a single precomputed hash in this script. The scratch check requires `server.js` to be the live bytes plus the pinned block, and `index.html` to be the one swap of `app.js?v=chat101g` to `app.js?v=chat101h`. The script prints the resulting sha256.

Patch files are pinned to commit `c4b804e8c722b258887c165f0fb142bd0a1af4e9`:
https://github.com/VRAJ2710/Website/commit/c4b804e8c722b258887c165f0fb142bd0a1af4e9

## Deploy (coordinator, Replit Shell)

Do not `git pull` or merge on the production Replit. Do not run `node server.js` or press Run. Do not republish until the dry run passes.

```sh
bash deploy.sh --dry-run
bash deploy.sh
```

Then one Republish of the existing Autoscale deployment. Undo is restore `server.js`, `app.js` and `index.html` from their `.bak-chat101h` copies. A second run refuses if those backups or the chat101h markers are already present.
