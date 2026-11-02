# deploy-final: one combined publish of chat96 + chat97 + chat98 + chat99 (built and tested, not published)

Run in the Replit shell from the project folder, only when Vraj says so:

    curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/deploy/jack-chat99/deploy-final/deploy.sh -o /tmp/deploy-final.sh
    sha256sum /tmp/deploy-final.sh   # must match the sha256 in the report
    bash /tmp/deploy-final.sh --dry-run && bash /tmp/deploy-final.sh

- Base must be the live chat94 files (md5 checked). Takes .bak-final backups, refuses a second run,
  runs node --check, greps for DDL, checks line 1 still says `const BB10I_MAINTENANCE_ON = true;`.
- It never starts the server. Maintenance stays ON.
- Before it: run deploy-chat98/dev_create.sql by hand (3 CREATE TABLE IF NOT EXISTS, no DROP/ALTER).
- To reopen later: deploy-reopen/deploy.sh flips only line 1 to false (sha256-pinned, base = final server.js).
