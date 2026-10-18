#!/usr/bin/env python3
"""patch_rt21s.py — server: /api/news-scores returns 200 {scores:[],unavailable:true,reason} when the AI call or
its validation fails (logged server-side; 400/401/403 still thrown), plus honest wording in 4 server strings.
No startup work. Independent of rt20s (compression skips /api/*), stacks in either order.
Usage: python3 patch_rt21s.py [--check] path/to/server.js     (never run `node server.js` in the Replit workspace)"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
P = args[0] if args else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
def die(m): print('ABORT:', m); sys.exit(1)
if 'rt21sErr' in s: die('rt21s already applied')
A = '        if (!headlines.length) return json(res, 400, { error: "Supply between 1 and 20 headlines." });\n        const result = await generateAi({\n'
B = '        });\n        return json(res, 200, { scores: result.validated || normaliseNewsScores(jsonFromText(result.text), headlines), meta: { provider: result.provider, model: result.model } });\n'
for nm, a in (('news-scores start', A), ('news-scores return', B)):
    if s.count(a) != 1: die(f'{nm} anchor matched {s.count(a)} times (want 1)')
ia, ib = s.find(A), s.find(B)
if not (ia < ib and ib - ia < 2500): die('news-scores anchors are not one handler (order/distance check failed)')
s = s.replace(A, A.replace('        const result = await generateAi({\n', '        let result;\n        try {\n        result = await generateAi({\n'))
s = s.replace(B, '''        });
        } catch (rt21sErr) {
          const rt21sStatus = Number(rt21sErr && rt21sErr.status) || 0;
          if (rt21sStatus === 400 || rt21sStatus === 401 || rt21sStatus === 403) throw rt21sErr;
          const reason = String((rt21sErr && rt21sErr.code) || "AI_UNAVAILABLE").replace(/[^A-Z0-9_]/gi, "").slice(0, 40) || "AI_UNAVAILABLE";
          console.warn(`news-scores unavailable: ${reason} status=${rt21sStatus || "-"} headlines=${headlines.length}`);
          return json(res, 200, { scores: [], unavailable: true, reason });
        }
        return json(res, 200, { scores: result.validated || normaliseNewsScores(jsonFromText(result.text), headlines), meta: { provider: result.provider, model: result.model } });
''')
# wording: applied when present exactly once, skipped (reported) when absent, abort when ambiguous
W = [('eyebrow: "LIVE NEWS & ANALYSIS",', 'eyebrow: "NEWS & ANALYSIS",'),
     ('summary: "A concise daily house view belongs beside live market context, not ahead of it.",', 'summary: "A concise daily house view belongs beside current market context, not ahead of it.",'),
     ('`Live congressional disclosures are temporarily unavailable.', '`Congressional disclosures are temporarily unavailable.'),
     ('"Live gold market data is unavailable. Please try again shortly."', '"Gold market data is unavailable. Please try again shortly."')]
done = 0
for a, c in W:
    n = s.count(a)
    if n > 1: die(f'wording anchor ambiguous ({n}x): {a[:50]}')
    if n == 1: s = s.replace(a, c); done += 1
    else: print('  note: wording anchor not found, skipped:', a[:60])
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:300])
print(f'OK rt21s: news-scores fallback + {done}/{len(W)} wording edits; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('written', P)
