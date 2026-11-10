# deploy-chat103

Public `/cpi/` for The Dispatch Market. It is added to the live chat102r5 files (installer `5fe33d23`, payload `023165d`). It does not start the server, change `EXPECT_TAG`, publish, or touch Stripe or Replit.

## Live base

| File | Required |
| --- | --- |
| `server.js` | md5 `0284a3b26acaa055ed4699b1c36b6ddc`, chat102 tail sha256 `099d7a7ebefb146220659d519fee5150315b18dee61f71fdc421cfcc9da8a054` |
| `app.js` | md5 `b84058f6da16ad022640b06c9cdda72d` |
| `index.html` | md5 `b3e02b0c6e403133843a96adf45d219c` |

That server md5 is the staged chat102r5 dev root. App and index are the same bytes as r4. A different full file, tail, app or index is refused.

```sh
bash deploy.sh --dry-run
bash deploy.sh
```

A dry run writes nothing in the project root. A refusal exits non-zero. Backups are `*.bak-chat103`. The DDL check allows `CREATE TABLE IF NOT EXISTS` of `cpi_releases`, `cpi_series_values`, `cpi_gold_reactions`, `cpi_gold_snapshots` and `cpi_notice_dismissals` only.

Local checks:

```sh
node build_block.js
node --test t_c103.js
```
