# deploy-chat100c

Cumulative bundle: **chat100** (unpublished, branch `deploy/jack-chat100`) **plus chat100b with the chat100c fix**
(spot-on-spot gold change), applied on top of the **live reopen2 build** (maintenance OFF). It replaces deploy-chat100b
(do not run both). Line 1 of server.js stays
`const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)`. c93.css unchanged.

Base (live) md5s: server.js `bd50fb5335bcaf937fa3e68ed3bf96bb`, app.js `9ebadee3093d77dafb70559b4984ee12`,
index.html `79b9249f6afcbf65b0af7464a4c2afb6`, c93.css `9d6a86a64135b1cc58e6af7b12973550`.
Result md5s: server.js `768966ac099ebf4b3f3865b2f15a3be8`, app.js `98b036f7acf0e2033e50dfcd219e29a1`,
index.html `27d43faa42cacff7d7c6fe2dd45d059a` (cache tag `app.js?v=chat100c`), c93.css unchanged.
New file: `assets/founder.webp` (400x400, 8,732 bytes, sha256 `fe56cbdeba4feb5aee61a1dc175aa1e67df85f3807cd3276e1aff0d501eee08f`).

## What this adds (on top of chat100, see deploy-chat100/README.md)
1. **Gold change, spot against spot only** on "Gold spot, US$", "Gold spot, £" (and £ per gram, and € on the gold
   dashboard), everywhere gold spot shows: Market context on `/`, `/gold/`, `/brief/`; the dashboard "Gold and macro"
   tiles; the gold dashboard (`/gold/dashboard/`).
   - The change is today's gold-api.com spot minus **our own recorded gold-api.com spot snapshot from the previous UK
     day** (the last spot reading we took before UK midnight). The pound row compares the pound spot now with the pound
     spot snapshot; the euro row compares the euro spot now with the euro spot snapshot.
   - Label: "vs previous UK close, our spot snapshot (gold-api), <snapshot time> UK" (pound/euro: "our pound/euro spot
     snapshot (gold-api spot ÷ pound/euro in dollars)"). Amount and %, green up / red down.
   - **No futures prices** are used for any spot row (the chat100b Yahoo COMEX previous-close path is removed).
   - Snapshots: recorded on every gold dashboard read (saved at most every 15 minutes, every reading in the last half
     hour before UK midnight), plus a background read at least hourly and every 5 minutes after 23:30 UK, so a snapshot
     exists even with no visitors. Stored in the existing `dispatch_openbb_research_cache` table under the key
     `c100c:gold-spot-day` (no new tables, no DDL). Snapshots older than 4 days are not used (covers weekends).
   - Until a previous-UK-day snapshot exists, every gold spot row shows **"Change not available yet"**. This is
     expected for the rest of the day after publish; changes appear from the first reading after UK midnight.
   - One server function (`c100bGoldChange`, `GET /api/c100b/gold-change`) supplies the snapshot; Market context
     computes the change from the level it shows and that snapshot. No raw ticker codes are shown.
2. **About: founder card** on the guest page `/about` and in the app's About panel: photo, **Vraj Patel**,
   "Edited by Vraj Patel, London", short bio, and a LinkedIn link (new tab, `rel="noopener noreferrer"`).
   If the photo file is missing the card shows no image at all (no initials, no broken image). Identical to chat100b.
3. Long gold source lines are clamped to 3 lines on the dashboard tiles (full text in the source inspector).

No DDL, no new tables, no Stripe, no env, no package changes. deploy.sh never starts the server.

## Photo drop-in (how to change the photo later)
- The photo path is one constant at the top of the chat100b block (section `// ── chat100b ──`) in server.js:
  `const C100B_FOUNDER_PHOTO_FILE = "assets/founder.webp";` (relative to the folder that holds server.js).
- To change the photo: replace `assets/founder.webp` next to server.js with a new square image (webp, ~400x400,
  under ~50 KB is ideal). It is re-read within 5 minutes, or at the next restart/Republish. The URL carries a
  content hash (`/assets/founder.webp?v=...`) so browsers pick up the new file.
- To remove the photo: delete the file. The card then shows name, byline and link only.
- Alt text is always "Vraj Patel".

## LinkedIn link (swap in a personal profile)
- One line: `const C100B_FOUNDER_LINKEDIN = "https://www.linkedin.com/company/thedispatchmarket";`
- Change it to e.g. `https://www.linkedin.com/in/<profile>`; the label switches by itself from
  "The Dispatch Market on LinkedIn" to "Vraj Patel on LinkedIn" for `/in/` URLs. Restart to apply.

## Files
patch_c100.py, server_block_c100.js, app_block_c100.js (chat100, identical to deploy-chat100),
patch_c100c.py, server_block_c100b.js (chat100c spot-only gold change + About), app_block_c100b.js (identical to chat100b),
founder.webp, t_c100_b.js / t_c100c.js (harness tests), t_c100c_unit.js (snapshot day-rollover test, runs standalone:
`node t_c100c_unit.js`), deploy.sh (sha256-pinned; also writes assets/founder.webp from an embedded, sha256-checked copy).

## Deploy (only after Vraj approves; Republish is done by others)
`bash deploy.sh --dry-run` first, then `bash deploy.sh`. It checks the live md5s, refuses a second run
(or if any `.bak-chat100c` backup exists), builds in scratch, runs `node --check`, a DDL grep and the line-1 check,
makes timestamped `.bak-chat100c` backups, installs, and verifies the final md5s. It does NOT start the server.
Undo: restore each file from its `.<timestamp>.bak-chat100c` copy (and delete assets/founder.webp if it was new).
