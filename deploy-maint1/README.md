# deploy-maint1 — SERVER-ONLY bb10i for thedispatch.uk

Applies bb10i to server.js only, on top of live bb10g (md5 9777ab9b8bebaa77f475b738995aa3d8). app.js (21f3cee5…) and index.html (35084b10…) are never modified; deploy.sh prints their md5s before and after and fails if they change. Does not include chat87 / rt62j / bb10h. Never starts the server, never touches git/DB/.replit/package.json/env/Stripe/npm. Click Republish yourself afterwards.

## Run in the Replit Shell (from the project folder)
    curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/deploy/jack-maint1-bb10i/deploy-maint1/deploy.sh -o /tmp/deploy_maint1.sh && echo "acf00d74d3bf1c05f080b1e7ee7cd95ca0f06ba21668bfd9e676faef5a298308  /tmp/deploy_maint1.sh" | sha256sum -c - && bash /tmp/deploy_maint1.sh --dry-run
    bash /tmp/deploy_maint1.sh

--dry-run also prints one informational Coinbase reachability line. Option: --dir /path/to/project. Second run: "REFUSE: already applied", exit 0. Base md5 mismatch, patch sha256 mismatch or result mismatch aborts before touching the live file.

## Expected result
| file | md5 | sha256 |
|---|---|---|
| server.js | d01094a38f0fbf00800ccd1bbc5f733c | 8fa0ff7ff1ed2e2b39c705c496113abee0f365b1124b151cf2c7361dc973e069 |
| app.js | 21f3cee5da20d9fc2f2f03d21623dcb4 | unchanged |
| index.html | 35084b102b38f99b582838aa19dadfad | unchanged |

Backup: server.js.<YYYYmmdd-HHMMSS>.bak-maint1. Rollback = copy it back to server.js, then Republish.

## sha256
acf00d74d3bf1c05f080b1e7ee7cd95ca0f06ba21668bfd9e676faef5a298308  deploy.sh
90d962dedd0554e517fc13f6c5c76ba4bb170d002a80618a605499815c9452ad  patch_bb10i.py

patch_bb10i.py = /workspace/bb10i/patch_bb10i.py (md5 6772c583f79bd206ac0ad6115b3c29ab, sha256 a458341f5eb72ae6d2ce07486257d0c9bf0d85c6656b790edc72479f448acb94; kept as patch_bb10i.orig.py) plus a 3-line Python<3.12 portability fix (b'\n' inside f-string braces fails before 3.12). Identical output on Python 3.10-3.13. bb10i.diff is for review only.

## Fallback if raw GitHub is unreachable (bundle-b64-part-00..00)
    cat > /tmp/b.b64 <<'EOB'      # paste the part files back to back, then EOB
    base64 -d /tmp/b.b64 | tar xz -C /tmp && bash /tmp/deploy-maint1/deploy.sh --dry-run && bash /tmp/deploy-maint1/deploy.sh
bundle.tgz sha256: 77f2bc42d982feb9ca8f46cc9cb49a046263e9b4ae7222ca4c717e0b8209a641
