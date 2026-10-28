# deploy-chat91 (staged, NOT published)

Builds on live chat90 (md5s: server 357d8300…, app 9caddff0…, index 65a78b0a…). Maintenance stays ON (server line 1 unchanged).

1. **Boot data fix** (server.js, right after `await seedEditorialContent();` in the DB init): two idempotent UPDATEs on
   `dispatch_editorial_content`, in try/catch (never blocks boot), logging affected row counts. Only `payload` changes.
   ```sql
   UPDATE dispatch_editorial_content SET payload = replace(payload::text, 'Dispatch Markets', 'Dispatch Market')::jsonb WHERE payload::text LIKE '%Dispatch Markets%' RETURNING id;
   UPDATE dispatch_editorial_content SET payload = jsonb_set(payload, '{title}', to_jsonb(left(payload->>'title', char_length(payload->>'title') - 15) || ' | The Dispatch Market')) WHERE content_type = 'page' AND jsonb_typeof(payload->'title') = 'string' AND payload->>'title' LIKE '% | The Dispatch' RETURNING id;
   ```
2. **Title suffix**: see replacements.txt (server.js 12 + app.js 4 strings).
3. **index.html**: `app.js?v=chat90` -> `chat91` (one line).

Files: `deploy.sh` (run in the Replit Shell: `bash deploy.sh --dry-run` then `bash deploy.sh`; refuses on second run; never starts the server),
`patch_brand2.py` (sha256-pinned in deploy.sh), `test_payload_fix.js` + `test_payload_fix.out` (PGlite test of the exact SQL, not part of the deploy).
Backups: `*.<timestamp>.bak-chat91`. The SQL runs only when the server boots after you Republish.
