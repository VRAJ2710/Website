#!/usr/bin/env python3
"""patch_rt53.py — sync Academy XP, streak and badges to the signed-in account.

Uses only the existing /api/prefs route and dispatch_user_prefs.prefs JSON.
No new table, no new column, no migration, no Stripe, no secrets.

Progress is stored under prefs.academy. Logged-out play stays in localStorage
(td_academy_v1, td_learn_v1, td_academy_act_v1). On sign-in the browser merges
with the account: max XP, the streak implied by the last activity date (or the
union of activity days when those were stored), and the union of badges.
The server checks and caps the payload. Writes are debounced (800ms). A prefs
row carries a rev; two tabs that write at once retry and merge, so neither
XP, day or badge is dropped. A settings save that does not send academy leaves
the stored academy in place. An academy-only save does not reset layout,
watchlist or the other prefs fields.

Primary base is the plain live site after rt52, rt52s, and rt52ops: chat57, with
function hasPremiumAccess( already present. bb2 (PR #23) is not required, so
this also applies after that patch. Requires the rt52 markers, function
hasPremiumAccess(, and app.js?v=chatNN with NN >= 57. Detects the current bust
and adds one. It does not hard-code the next number. A later client bust still
increments whatever it finds. No tier-string checks: sign-in stays on the
existing /api/prefs route, which uses currentUser. Premium gating, where it
already exists, stays inside hasPremiumAccess.

Usage:
    python3 patch_rt53.py --check <dir with app.js, index.html, server.js>
    python3 patch_rt53.py <dir>
Refuses a second run. CRLF-safe. node --check before the write; a failed write
restores backups. Prints md5 and line count of each file before and after.
"""
import hashlib, os, re, subprocess, sys, tempfile

CHECK = "--check" in sys.argv
args = [a for a in sys.argv[1:] if a != "--check"]
D = args[0] if args else "."
APP, IDX, SRV = os.path.join(D, "app.js"), os.path.join(D, "index.html"), os.path.join(D, "server.js")

def die(m):
    print("ABORT (nothing written):", m)
    sys.exit(1)

def load(path):
    b = open(path, "rb").read()
    return b.decode("utf-8").replace("\r\n", "\n"), b"\r\n" in b

def stats(text, crlf):
    raw = (text.replace("\n", "\r\n") if crlf else text).encode("utf-8")
    return hashlib.md5(raw).hexdigest(), len(text.splitlines()), len(raw)

def show(label, text, crlf):
    md5, lines, nbytes = stats(text, crlf)
    print("%s md5=%s lines=%d bytes=%d" % (label, md5, lines, nbytes))

def nodecheck(text, label):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as t:
        t.write(text)
        tmp = t.name
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    os.unlink(tmp)
    if r.returncode:
        die("node --check failed for %s: %s" % (label, (r.stderr or "")[:500]))

for p in (APP, IDX, SRV):
    if not os.path.isfile(p):
        die("not found: " + p)
s, crlf = load(APP)
h, hcrlf = load(IDX)
v, vcrlf = load(SRV)
show("rt53 before app.js", s, crlf)
show("rt53 before index.html", h, hcrlf)
show("rt53 before server.js", v, vcrlf)
# Plain live files after rt52, rt52s, and rt52ops, before bb2. A mismatch warns
# only; anchors decide, so a later bb2 or home-freeze edit can still apply.
EXPECTED_MD5 = {
    "app.js": "45107b5b78039f675ffd94646ce4d309",
    "index.html": "87ee1667f8e6deef4c449ff9a61cce8d",
    "server.js": "4e8c340439b57d202b6c13711cc7a338",
}
for path, text, use_crlf in ((APP, s, crlf), (IDX, h, hcrlf), (SRV, v, vcrlf)):
    digest = stats(text, use_crlf)[0]
    expect = EXPECTED_MD5.get(os.path.basename(path))
    if expect and digest != expect:
        print("WARN md5 %s: have %s expected live %s (anchors still decide)" % (os.path.basename(path), digest, expect))
if "// ── rt53a ──" in s or "// ── rt53a ──" in v:
    die("REFUSE: rt53 already applied")

errors = []
if "// ── rt52 ──" not in s:
    errors.append("app.js missing rt52 marker (apply patch_rt52.py first)")
if "// ── rt52s" not in v:
    errors.append("server.js missing rt52s marker (apply patch_rt52s.py first)")
if "function hasPremiumAccess(" not in v:
    errors.append("server.js missing function hasPremiumAccess( (admins share the premium helper; do not compare tier strings)")
CLIENT_NEEDLES = [
    "function _rt47Save()",
    "function _rt48Save()",
    "function _rt46Save()",
    "function _rt17LoadServer()",
    "const _RT47_KEY = 'td_academy_v1';",
    "Saved in this browser only.",
]
for needle in CLIENT_NEEDLES:
    n = s.count(needle)
    if n != 1:
        errors.append("app.js anchor %r matched %d times (need 1)" % (needle, n))
vers = re.findall(r'app\.js\?v=chat(\d+)"', h)
if len(vers) != 1:
    errors.append("index app.js?v=chatNN matched %d times (need 1)" % len(vers))
else:
    nver = int(vers[0])
    if nver < 57:
        errors.append("index is chat%d; expected chat57 or later (post rt52)" % nver)
PUT = (
    "        const prefs = rt17SanitizePrefs(body && body.prefs);\n"
    "        await sql`INSERT INTO dispatch_user_prefs (user_id, prefs, updated_at) VALUES (${user.id}, ${JSON.stringify(prefs)}::jsonb, NOW())\n"
    "          ON CONFLICT (user_id) DO UPDATE SET prefs=EXCLUDED.prefs, updated_at=NOW()`;\n"
    "        return json(res, 200, { ok: true, prefs }, noStore);"
)
READJ = "async function rt17ReadJson(req, maxBytes) {"
CATCH = '    if (error && error.code === "RT17_BAD_JSON") return json(res, 400, { error: "Invalid JSON." }, noStore);'
for name, needle, hay in (
    ("rt17ReadJson", READJ, v),
    ("prefs PUT", PUT, v),
    ("prefs error catch", CATCH, v),
    ("rt17SanitizePrefs", "function rt17SanitizePrefs(", v),
):
    n = hay.count(needle)
    if n != 1:
        errors.append("server.js anchor %s matched %d times (need 1)" % (name, n))
# The table name is in GET, PUT, export, and delete. Presence is the check.
if v.count("dispatch_user_prefs") < 1:
    errors.append("server.js anchor dispatch_user_prefs matched 0 times (need at least 1)")
if errors:
    die("; ".join(errors))

nver = int(vers[0])
nxt = nver + 1
h2 = h.replace('app.js?v=chat%d"' % nver, 'app.js?v=chat%d"' % nxt, 1)
s2 = s.replace(
    "Saved in this browser only.",
    'Saved in this browser${typeof _rt53Signed==="function"&&_rt53Signed()?" and your account":""}.',
    1,
)

PURE = r'''/* RT53_PURE_START */
const RT53_BADGES = ["start-markets-table", "start-gold-macro", "start-oil", "start-fx", "start-crypto", "start-stocks", "start-charts", "start-risk", "start-data", "start-dispatch", "speed100", "combo", "match", "paper3", "stop", "price", "cal", "pattern", "scen10", "news", "weekly"];
const RT53_XP_CAP = 20000;
const RT53_DAY_CAP = 120;
function rt53Today() {
  try { return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/London" }).format(new Date()); }
  catch (e) { return new Date().toISOString().slice(0, 10); }
}
function rt53DayShift(iso, delta) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso || ""));
  if (!m) return "";
  const t = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3] + delta));
  return t.toISOString().slice(0, 10);
}
function rt53ValidDay(iso, today) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(iso)) return false;
  const shift = rt53DayShift(today, 1);
  if (iso < "2024-01-01" || (shift && iso > shift)) return false;
  const y = +iso.slice(0, 4), mo = +iso.slice(5, 7), d = +iso.slice(8, 10);
  const dt = new Date(Date.UTC(y, mo - 1, d));
  return dt.getUTCFullYear() === y && dt.getUTCMonth() === mo - 1 && dt.getUTCDate() === d;
}
function rt53StreakFromDays(days, today) {
  const set = new Set(days);
  const sorted = [...set].sort();
  const last = sorted.length ? sorted[sorted.length - 1] : "";
  let n = 0;
  const start = set.has(today) ? today : rt53DayShift(today, -1);
  if (start && set.has(start)) {
    let cursor = start;
    while (set.has(cursor) && n < RT53_DAY_CAP) { n++; cursor = rt53DayShift(cursor, -1); }
  }
  return { n: n, last: last, days: sorted.slice(-RT53_DAY_CAP) };
}
function rt53StreakPair(n, last, today) {
  n = Math.max(0, Math.min(RT53_DAY_CAP, Math.round(Number(n) || 0)));
  if (!last || !rt53ValidDay(last, today)) return { n: 0, last: "", days: [] };
  const yday = rt53DayShift(today, -1);
  if (last !== today && last !== yday) return { n: 0, last: last, days: [last] };
  if (!n) return { n: 0, last: last, days: [last] };
  const days = [];
  let cursor = last;
  for (let i = 0; i < n; i++) { days.push(cursor); cursor = rt53DayShift(cursor, -1); }
  days.sort();
  return rt53StreakFromDays(days, today);
}
function rt53Gap(a, b) {
  const am = /^(\d{4})-(\d{2})-(\d{2})$/.exec(a), bm = /^(\d{4})-(\d{2})-(\d{2})$/.exec(b);
  if (!am || !bm) return 99;
  return Math.round((Date.UTC(+bm[1], +bm[2] - 1, +bm[3]) - Date.UTC(+am[1], +am[2] - 1, +am[3])) / 86400000);
}
function rt53CleanAcademy(input, today) {
  today = today || rt53Today();
  const p = input && typeof input === "object" && !Array.isArray(input) ? input : null;
  if (!p) return null;
  let xp = Math.round(Number(p.xp));
  if (!isFinite(xp) || xp < 0) xp = 0;
  if (xp > RT53_XP_CAP) xp = RT53_XP_CAP;
  const badges = [];
  const seenB = new Set();
  const srcB = Array.isArray(p.badges) ? p.badges : [];
  for (let i = 0; i < srcB.length && badges.length < RT53_BADGES.length; i++) {
    const id = String(srcB[i] || "");
    if (RT53_BADGES.indexOf(id) < 0 || seenB.has(id)) continue;
    seenB.add(id); badges.push(id);
  }
  badges.sort(function (a, b) { return RT53_BADGES.indexOf(a) - RT53_BADGES.indexOf(b); });
  const days = [];
  const seenD = new Set();
  const srcD = Array.isArray(p.days) ? p.days : [];
  for (let i = 0; i < srcD.length; i++) {
    const iso = String(srcD[i] || "");
    if (!rt53ValidDay(iso, today) || seenD.has(iso)) continue;
    seenD.add(iso); days.push(iso);
  }
  days.sort();
  if (days.length) {
    const part = rt53StreakFromDays(days.slice(-RT53_DAY_CAP), today);
    return { v: 1, xp: xp, badges: badges, days: part.days, last: part.last, streak: part.n };
  }
  let last = rt53ValidDay(String(p.last || ""), today) ? String(p.last) : "";
  let streak = Math.round(Number(p.streak));
  if (!isFinite(streak) || streak < 0) streak = 0;
  if (streak > RT53_DAY_CAP) streak = RT53_DAY_CAP;
  if (!last) streak = 0;
  else {
    const yday = rt53DayShift(today, -1);
    if (last !== today && last !== yday) streak = 0;
  }
  if (!xp && !badges.length && !last) return null;
  return { v: 1, xp: xp, badges: badges, days: [], last: last, streak: streak };
}
function rt53MergeStreakOnly(a, b, today) {
  let A = { n: a.streak || 0, last: a.last || "" };
  let B = { n: b.streak || 0, last: b.last || "" };
  if (!A.last) return rt53StreakPair(B.n, B.last, today);
  if (!B.last) return rt53StreakPair(A.n, A.last, today);
  if (A.last > B.last) { const t = A; A = B; B = t; }
  if (A.last === B.last) return rt53StreakPair(Math.max(A.n, B.n), A.last, today);
  if (rt53Gap(A.last, B.last) === 1) return rt53StreakPair(Math.min(RT53_DAY_CAP, Math.max(B.n, A.n + 1)), B.last, today);
  return rt53StreakPair(B.n, B.last, today);
}
function rt53MergeAcademy(a, b, today) {
  today = today || rt53Today();
  const left = rt53CleanAcademy(a, today) || { v: 1, xp: 0, badges: [], days: [], last: "", streak: 0 };
  const right = rt53CleanAcademy(b, today) || { v: 1, xp: 0, badges: [], days: [], last: "", streak: 0 };
  const xp = Math.min(RT53_XP_CAP, Math.max(left.xp || 0, right.xp || 0));
  const badges = [];
  const seen = new Set();
  const src = (left.badges || []).concat(right.badges || []);
  for (let i = 0; i < src.length; i++) { if (!seen.has(src[i]) && RT53_BADGES.indexOf(src[i]) >= 0) { seen.add(src[i]); badges.push(src[i]); } }
  const hasDays = (left.days && left.days.length) || (right.days && right.days.length);
  let part;
  if (hasDays) {
    const bag = (left.days || []).concat(right.days || []);
    if (!(left.days || []).length) bag.push.apply(bag, rt53StreakPair(left.streak, left.last, today).days);
    if (!(right.days || []).length) bag.push.apply(bag, rt53StreakPair(right.streak, right.last, today).days);
    part = rt53StreakFromDays(bag, today);
  } else part = rt53MergeStreakOnly(left, right, today);
  return rt53CleanAcademy({ v: 1, xp: xp, badges: badges, days: part.days || [], last: part.last || "", streak: part.n || 0 }, today);
}
/* RT53_PURE_END */
'''

SERVER = r'''// ── rt53a ── Academy progress inside prefs.academy. No new column.
/* RT53_SERVER_START */
''' + PURE + r'''
function rt53AsObj(v) {
  if (!v) return {};
  if (typeof v === "string") { try { v = JSON.parse(v); } catch (e) { return {}; } }
  return v && typeof v === "object" && !Array.isArray(v) ? v : {};
}
async function rt53PutPrefs(user, body) {
  const raw = rt53AsObj(body && body.prefs);
  const academyOnly = raw.academy != null && raw.layout == null && raw.v == null && raw.markets == null && raw.alerts == null && raw.display == null && raw.ask == null && raw.newsletter == null;
  for (let attempt = 0; attempt < 5; attempt++) {
    const rows = await sql`SELECT prefs, updated_at FROM dispatch_user_prefs WHERE user_id=${user.id} LIMIT 1`;
    const row = rows && rows[0];
    const stored = rt53AsObj(row && row.prefs);
    const rev = Math.max(0, Math.round(Number(stored.rev) || 0));
    const base = rt17SanitizePrefs(academyOnly ? stored : raw);
    const prev = rt53CleanAcademy(stored.academy);
    let academy = prev;
    if (raw.academy != null) academy = rt53MergeAcademy(prev, raw.academy);
    if (academy) base.academy = academy;
    else if (base.academy) delete base.academy;
    base.rev = rev + 1;
    const payload = JSON.stringify(base);
    if (payload.length > 48 * 1024) { const e = new Error("too large"); e.code = "RT17_TOO_LARGE"; throw e; }
    if (!row) {
      const ins = await sql`INSERT INTO dispatch_user_prefs (user_id, prefs, updated_at) VALUES (${user.id}, ${payload}::jsonb, NOW()) ON CONFLICT (user_id) DO NOTHING RETURNING prefs, updated_at`;
      if (ins && ins[0]) return { prefs: rt17SanitizePrefs(rt53AsObj(ins[0].prefs)), updatedAt: ins[0].updated_at };
      continue;
    }
    const upd = await sql`UPDATE dispatch_user_prefs SET prefs=${payload}::jsonb, updated_at=NOW() WHERE user_id=${user.id} AND COALESCE((prefs->>'rev')::int, 0)=${rev} RETURNING prefs, updated_at`;
    if (upd && upd[0]) return { prefs: rt17SanitizePrefs(rt53AsObj(upd[0].prefs)), updatedAt: upd[0].updated_at };
  }
  const err = new Error("conflict"); err.code = "RT53_CONFLICT"; throw err;
}
{
  const rt53PrefsOrig = rt17SanitizePrefs;
  rt17SanitizePrefs = function (input) {
    const out = rt53PrefsOrig(input);
    if (!out || typeof out !== "object") return out;
    const ac = rt53CleanAcademy(input && input.academy);
    if (ac) out.academy = ac;
    return out;
  };
}
/* RT53_SERVER_END */
'''

PUT_NEW = (
    "        const rt53Saved = await rt53PutPrefs(user, body);\n"
    "        return json(res, 200, { ok: true, prefs: rt53Saved.prefs, updatedAt: rt53Saved.updatedAt }, noStore);"
)
CATCH_NEW = CATCH + '\n    if (error && error.code === "RT53_CONFLICT") return json(res, 409, { error: "Your settings changed in another tab. Nothing was overwritten; try again." }, noStore);'
v2 = v.replace(READJ, SERVER + READJ, 1).replace(PUT, PUT_NEW, 1).replace(CATCH, CATCH_NEW, 1)
if v2.count("// ── rt53a ──") != 1 or v2.count(PUT) != 0:
    die("server edit did not land once")

CLIENT = r'''
// ── rt53a ── Academy XP, streak and badges sync to the signed-in account via /api/prefs (prefs.academy).
// Logged-out play stays in this browser. Sign-in merges: max XP, streak from the last activity date, union of badges.
''' + PURE + r'''
function _rt53Signed() { try { return typeof _rt17Signed === "function" && _rt17Signed(); } catch (e) { return false; } }
function _rt53Snapshot() {
  const days = [];
  try { const D = _rt47S && _rt47S.days || {}; Object.keys(D).forEach(k => { if (D[k]) days.push(k); }); } catch (e) {}
  const badges = [];
  try {
    RT53_BADGES.forEach(id => {
      if (id.indexOf("start-") === 0) {
        if (typeof _rt46Passed === "function" && _rt46Passed(id)) badges.push(id);
        else if (_rt47S && _rt47S.done && _rt47S.done[id] && _rt47S.done[id].pass) badges.push(id);
      } else if (_rt48S && _rt48S.bd && _rt48S.bd[id]) badges.push(id);
    });
  } catch (e) {}
  let last = "";
  days.forEach(d => { if (!last || d > last) last = d; });
  let streak = 0;
  try { streak = (_rt47Streak().n) || 0; } catch (e) {}
  const xp = Math.max(0, Math.min(RT53_XP_CAP, Math.round(Number(_rt47S && _rt47S.xp) || 0)));
  return rt53CleanAcademy({ v: 1, xp: xp, streak: streak, last: last, days: days, badges: badges }) || { v: 1, xp: 0, streak: 0, last: "", days: [], badges: [] };
}
let _rt53Quiet = false, _rt53T = 0, _rt53Flight = null, _rt53Dirty = false;
function _rt53Apply(ac) {
  const merged = rt53CleanAcademy(ac);
  if (!merged || !_rt47S) return;
  _rt53Quiet = true;
  try {
    _rt47S.xp = Math.max(Number(_rt47S.xp) || 0, merged.xp || 0);
    (merged.days || []).forEach(d => { if (!_rt47S.days[d]) _rt47S.days[d] = 1; });
    (merged.badges || []).forEach(id => {
      if (String(id).indexOf("start-") === 0) {
        if (_rt46P) {
          const prev = _rt46P.quiz && _rt46P.quiz[id];
          if (!_rt46P.quiz) _rt46P.quiz = {};
          _rt46P.quiz[id] = { best: Math.max((prev && prev.best) || 0, 1), n: (prev && prev.n) || 1, passed: true, at: (prev && prev.at) || Date.now() };
        }
        if (!_rt47S.done[id]) _rt47S.done[id] = { at: Date.now(), pass: true, best: 1, n: 1 };
        else _rt47S.done[id].pass = true;
      } else if (_rt48S) {
        if (!_rt48S.bd) _rt48S.bd = {};
        if (!_rt48S.bd[id]) _rt48S.bd[id] = Date.now();
      }
    });
    try { _rt53Orig47(); } catch (e) {}
    try { _rt53Orig48(); } catch (e) {}
    try { _rt53Orig46(); } catch (e) {}
    try {
      document.querySelectorAll("[data-rt47xp]").forEach(el => { el.innerHTML = (typeof _rt47Ic === "function" ? _rt47Ic("bolt") : "") + "<span>" + _rt47S.xp + " XP</span>"; });
      if (_rt47L && _rt47L.id && typeof _rt47Redraw === "function") _rt47Redraw();
      else if (typeof pg !== "undefined" && pg === "learn" && typeof _refreshView === "function") _refreshView();
    } catch (e) {}
  } finally { _rt53Quiet = false; }
}
function _rt53Schedule() {
  if (_rt53Quiet || !_rt53Signed()) return;
  if (_rt53Flight) { _rt53Dirty = true; return; }
  clearTimeout(_rt53T);
  _rt53T = setTimeout(_rt53Push, 800);
}
async function _rt53Push() {
  if (!_rt53Signed() || _rt53Flight) { if (_rt53Flight) _rt53Dirty = true; return; }
  const snap = _rt53Snapshot();
  _rt53Flight = (async () => {
    let opts = { method: "PUT", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prefs: { academy: snap } }) };
    try { opts.signal = AbortSignal.timeout(8000); } catch (e) {}
    const r = await fetch("/api/prefs", opts);
    if (!r.ok) return;
    const d = await r.json();
    if (d && d.prefs && d.prefs.academy) _rt53Apply(rt53MergeAcademy(snap, d.prefs.academy));
  })();
  try { await _rt53Flight; } catch (e) {}
  finally { _rt53Flight = null; if (_rt53Dirty) { _rt53Dirty = false; _rt53Schedule(); } }
}
async function _rt53Pull() {
  if (!_rt53Signed()) return;
  try {
    let opts = { credentials: "include" };
    try { opts.signal = AbortSignal.timeout(8000); } catch (e) {}
    const r = await fetch("/api/prefs", opts);
    if (!r.ok) return;
    const d = await r.json();
    const remote = d && d.prefs ? d.prefs.academy : null;
    const local = _rt53Snapshot();
    const merged = rt53MergeAcademy(local, remote);
    if (merged) _rt53Apply(merged);
    const after = rt53CleanAcademy(_rt53Snapshot());
    const srv = rt53CleanAcademy(remote);
    if (JSON.stringify(after) !== JSON.stringify(srv)) _rt53Schedule();
  } catch (e) {}
}
const _rt53Orig47 = _rt47Save, _rt53Orig48 = _rt48Save, _rt53Orig46 = _rt46Save;
_rt47Save = function () { const r = _rt53Orig47.apply(this, arguments); _rt53Schedule(); return r; };
_rt48Save = function () { const r = _rt53Orig48.apply(this, arguments); _rt53Schedule(); return r; };
_rt46Save = function () { const r = _rt53Orig46.apply(this, arguments); _rt53Schedule(); return r; };
{
  const _rt53Ld = _rt17LoadServer;
  _rt17LoadServer = function () {
    const p = _rt53Ld.apply(this, arguments);
    Promise.resolve(p).then(() => { _rt53Pull(); }, () => { _rt53Pull(); });
    return p;
  };
}
setTimeout(() => { try { _rt53Pull(); } catch (e) {} }, 1200);
'''
s2 = s2.rstrip("\n") + "\n" + CLIENT
if s2.count("// ── rt53a ──") != 1:
    die("client marker count is %d" % s2.count("// ── rt53a ──"))
nodecheck(s2, "app.js")
nodecheck(v2, "server.js")
show("rt53 after app.js", s2, crlf)
show("rt53 after index.html", h2, hcrlf)
show("rt53 after server.js", v2, vcrlf)
print("OK rt53: academy progress in prefs.academy; index chat%d -> chat%d; node --check passed%s" % (nver, nxt, " (dry run, nothing written)" if CHECK else ""))
if CHECK:
    sys.exit(0)

def restore(baks):
    for path, bak in baks:
        if os.path.exists(bak):
            open(path, "wb").write(open(bak, "rb").read())
            os.unlink(bak)

pairs = [(APP, s2, crlf), (IDX, h2, hcrlf), (SRV, v2, vcrlf)]
baks = []
try:
    for path, text, use_crlf in pairs:
        bak = path + ".rt53abak"
        open(bak, "wb").write(open(path, "rb").read())
        baks.append((path, bak))
        data = (text.replace("\n", "\r\n") if use_crlf else text).encode("utf-8")
        open(path, "wb").write(data)
    for path in (APP, SRV):
        r = subprocess.run(["node", "--check", path], capture_output=True, text=True)
        if r.returncode:
            restore(baks)
            print("ABORT: node --check failed after write; backups restored:", (r.stderr or "")[:400])
            sys.exit(1)
    for path, bak in baks:
        os.unlink(bak)
except Exception as e:
    restore(baks)
    print("ABORT: write failed; backups restored:", e)
    sys.exit(1)
print("written", APP, IDX, SRV)
