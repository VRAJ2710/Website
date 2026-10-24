# deploy-chat81 — bb10b (server) + rt62b + rt62c (app/index) for thedispatch.uk

Applies on top of the live chat79 files (verified md5): server.js 56ebb9729fc8866d1be6488f244f550e (bb10), app.js d16d919877becccafd142f86bda132a2 (chat79), index.html c4cc3fe04d896fa0d6b1c05c5839b0e8 (chat79).
Apply order: bb10b (server.js) -> rt62b (app.js chat79->chat80, index v=chat80) -> rt62c (app.js chat80->chat81, index v=chat81). deploy.sh also checks the intermediate rt62b app md5.
Never starts the server, never touches git/DB/.replit/package.json/env/Stripe/npm. Click Republish yourself afterwards.

## Run in the Replit Shell (from the project folder)
    curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/deploy/jack-chat81-bb10b-rt62bc/deploy-chat81/deploy.sh -o /tmp/deploy81.sh && echo "b98692c89d7b9fd02ba791d71f42deb7fd1d116119361dafb2cf896845cf68e2  /tmp/deploy81.sh" | sha256sum -c - && bash /tmp/deploy81.sh --dry-run
    bash /tmp/deploy81.sh

--dry-run also prints one informational line: whether Coinbase https://api.exchange.coinbase.com/products/BTC-USD/stats is REACHABLE from Replit (10 s timeout; never aborts; bb10/bb10b fall back to a labelled previous-close basis if unreachable).
Options: --dir /path/to/project. Second run: "REFUSE: already applied", exit 0. Any md5/sha256 mismatch (live base, patch file, intermediate or final) aborts before touching live files.
The patch scripts print "WARN index.html md5 ... expected prefix b50d5cd2 / 0f56bcfa" — harmless: they were authored against a different on-disk index; anchors decide, and deploy.sh verifies the real final index md5.

## Expected results
| file | md5 | sha256 |
|---|---|---|
| server.js | e7f75c9bccd6668a8b075d682444af49 | b34b606080cb09143ac98daca8d73ae1c188d206c3a34a1348ec98fb2d5dc6b2 (21967 lines) |
| app.js | 78e28a26d768f8cbd0458f1609717ffb | b37c868e64fa52e0a5b0ed6e1ab91739ee5e3af688d4a7733234520d03942a3c |
| index.html | 1d1a37cfa43dde4d1281363414452954 | 1bfc0a61c3b83639253353bce516780966af6e98377f9687cafdf28016df844e |

app.js after rt62b only: 777effe4bca52c3cc1dbd0d14d5f54f8.
index.html differs from the live chat79 file by exactly one line: app.js?v=chat79 -> app.js?v=chat81. (The Frontend agent quoted index md5 83bb6a285a55ca509ef134089b0ad53d; that came from a different base copy of index.html. On the verified live chat79 index the correct result is 1d1a37cf…; app.js and server.js match the quoted hashes exactly.)
Backups: <file>.<YYYYmmdd-HHMMSS>.bak-chat81 next to each file. Rollback = copy the three backups back, then Republish.

## Patch file sha256
b98692c89d7b9fd02ba791d71f42deb7fd1d116119361dafb2cf896845cf68e2  deploy.sh
0f64894806684d40578323b00ba6ec7b219a5a9756db3b8bb00658b6dc16420b  patch_bb10b.py
8b3fc31ccbe962a69568cad9b59379cc6f206a51fe5402945693baa31e44066c  patch_rt62b.py
e48dd9ec0351ed244948bae3d8915b4d09bf12ecb9f60373f4c05860e429e964  patch_rt62c.py

patch_rt62b.py = PR #76 commit c758551d17e22ba61650129d1ca02fe676d43355 (deploy/), byte-identical. patch_rt62c.py = PR #77 commit 6f0e049dcf2402b486b528e5bd20f8e9dd16eddc (deploy/), byte-identical.
patch_bb10b.py = /workspace/bb10b/patch_bb10b.py (sha256 5e60b4a3dc0a9f45e5b298165e238b9f321aee8caf9dc26df61c0925c4c892bd, kept as patch_bb10b.orig.py) plus the same 3-line Python<3.12 portability fix as chat78/chat79 (b'\n' inside f-string braces is a SyntaxError before 3.12). Outputs identical on Python 3.10/3.11/3.13. bb10b.diff is for review only (not used by deploy.sh).

## Fallback if raw GitHub is unreachable from Replit (local files only: bundle-b64-part-00..02, 16 KB each)
    cat > /tmp/b.b64 <<'EOB'      # paste part-00, part-01, part-02 contents back to back, then EOB
    base64 -d /tmp/b.b64 | tar xz -C /tmp && bash /tmp/deploy-chat81/deploy.sh --dry-run && bash /tmp/deploy-chat81/deploy.sh
bundle.tgz sha256: be0e82bb5aa6713d721e814853dec02a76b4a20607180c5be9f51dd173671d70
