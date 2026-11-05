# deploy-chat101i

Revises one Research note, `/research/bank-rate-energy-shock-sterling-gold/`, on the live chat101h build. The other two notes, the Capital Sustainability Monitor, and every other section stay. `app.js` and `index.html` are checked and not written. Line 1 of `server.js` stays the maintenance-off line. The server is not started.

## Live base this script requires

After chat101h, confirmed for `app.js` by downloading https://thedispatch.uk/app.js on 5 November 2026:

- `server.js` md5 `6077bef9728ffe5b26d8d6fcb887294b`
- `app.js` md5 `6c8ddd1be4db078df1de146163f99b11`, sha256 `80954f1cfde5add82ee75d9b783e3740c799e1fb8237bc8f01881a5514fbf989`
- `index.html` md5 `e5ab1af080974da456e086a1835d1e7b`

The chat101h handoff gave server and index as md5 only. This script checks those md5s. It checks both md5 and sha256 for `app.js`, which was re-downloaded.

## What the article now says

Checked at 21:57 UK (GMT) on 5 November 2026 against the November 2026 Monetary Policy Summary, minutes and Monetary Policy Report. The futures averages are the front-month Brent and UK front-month gas contracts over the 15 UK working days ending 27 October: $108 a barrel and 216 pence a therm, on curves the minutes describe as downward sloping. September CPI at 3.5% is an outturn. The 4.9% average for 2027 Q2, and the curve levels of around 4.9% at end-2027 and around 4.7% by late 2029, are the Bank’s November descriptions, not outcomes and not a promise. The minutes entries are set out one by one. Box A is cited for margins and for the December pay-settlement estimate. Fixed-price contracts and hedging stay with the Chart 1.3 passage. A dated correction at the end of the note records the earlier mis-attribution. The table follows minutes paragraph 16. It is not a forecast.

`sw.js` is not edited. If it is present, the script records its md5 and stops if that md5 changes. After Republish, confirm in the browser that the service worker request is still the existing file.

Byline remains “Edited by Vraj Patel”. The page still ends with “Not investment advice. Capital at risk.”

Patch files are pinned to commit `f1a5f6461b2214bf4103ca36f524013c05fdf417`:
https://github.com/VRAJ2710/Website/commit/f1a5f6461b2214bf4103ca36f524013c05fdf417

`patch_c101i.py` `938beb5f3d7ee0b967f9ed657bee85a2a108d6bbbd036eb09db54686a5ff21fa`
`old_bank.frag` `333170c1957dbfde1be7f45b57cc45b58c0cced520de8faab927e4811f044f52`
`new_bank.frag` `0e00ca34110ee29e0dee434d4b6771a0cf51e5bef645083741fe73ea389a323a`
`css_old.frag` `d373b97494ffead9612421305e351f57eafd31629d272c4b04e8e91a09491b5b`
`css_new.frag` `bb8afbbdd66ca2b3fe56c1a8f9c5652f418b6343879bb0eb261cc461f4c97a22`

## Deploy (coordinator, Replit Shell)

Do not git pull. Do not run `node server.js`. Do not republish until the dry run passes.

```sh
bash deploy.sh --dry-run
bash deploy.sh
```

Then one Republish of the existing Autoscale deployment. Undo is restore `server.js` from its `.bak-chat101i` copy. A second run refuses.
