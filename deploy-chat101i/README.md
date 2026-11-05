# deploy-chat101i

Revises one Research note, `/research/bank-rate-energy-shock-sterling-gold/`, on the live chat101h build. The other two notes, the Capital Sustainability Monitor, and every other section stay. `app.js` and `index.html` are checked and not written. Line 1 of `server.js` stays the maintenance-off line. The server is not started.

## Live base this script requires

After chat101h, confirmed for `app.js` by downloading https://thedispatch.uk/app.js on 5 November 2026:

- `server.js` md5 `6077bef9728ffe5b26d8d6fcb887294b`
- `app.js` md5 `6c8ddd1be4db078df1de146163f99b11`, sha256 `80954f1cfde5add82ee75d9b783e3740c799e1fb8237bc8f01881a5514fbf989`
- `index.html` md5 `e5ab1af080974da456e086a1835d1e7b`

The chat101h handoff gave server and index as md5 only. This script checks those md5s. It checks both md5 and sha256 for `app.js`, which was re-downloaded.

## What the article now says

Checked at 21:46 UK (GMT) on 5 November 2026 against the November 2026 Monetary Policy Summary, minutes and Monetary Policy Report. The futures averages are the front-month Brent and UK front-month gas contracts over the 15 UK working days ending 27 October: $108 a barrel and 216 pence a therm, 38% and 81% above the July Report. September CPI at 3.5% is an outturn. The 4.9% figure for 2027 Q2 is the Bank’s projection. Alan Taylor’s minutes entry is quoted for the next step. Catherine L Mann’s vote for 4.25% is the summary’s vote, not a forecast. The table follows the three cases in minutes paragraph 16. It is not a forecast.

Byline remains “Edited by Vraj Patel”. The page still ends with “Not investment advice. Capital at risk.”

## Deploy (coordinator, Replit Shell)

Do not git pull. Do not run `node server.js`. Do not republish until the dry run passes.

```sh
bash deploy.sh --dry-run
bash deploy.sh
```

Then one Republish of the existing Autoscale deployment. Undo is restore `server.js` from its `.bak-chat101i` copy. A second run refuses.
