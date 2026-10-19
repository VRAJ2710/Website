#!/usr/bin/env python3
"""patch_rt56b.py: client patch on chat67. Reads app.js?v=chatNN and writes chatNN+1.

The known base is chat67, the output of patch_rt56.py on chat66:
  app.js md5 2d9e26642fa00696c5cae16d57e8fdab
  index.html md5 61dcd48045470f2b12edb473e34efad8
A different checksum prints WARN and continues. Anchors still decide: a missing
or ambiguous anchor aborts with a non-zero status. A second run prints
REFUSE (already applied) and exits 0. Finishes with node --check.

A venue midday break reads "Lunch break · resumes HH:MM UK". The clock is
Europe/London, computed from the venue calendar. A server lunch flag or note
wins. A server status of closed, stale, delayed or quiet is left alone.
Holiday closes stay closed even when the clock is inside the lunch window.

No server file is changed.

Usage: python3 patch_rt56b.py [--check] <dir containing app.js and index.html>"""
import sys, os, re, hashlib, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')

EXPECT_APP_MD5 = "2d9e26642fa00696c5cae16d57e8fdab"
EXPECT_INDEX_MD5 = "61dcd48045470f2b12edb473e34efad8"
NEED_MARKER = "// ── rt56 ──"

def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
def already(m): print('REFUSE:', m); sys.exit(0)
raw = open(APP, 'rb').read()
raw_idx = open(IDX, 'rb').read()
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt56b ──' in s: already('rt56b already applied')
if NEED_MARKER not in s: die('base lacks ' + NEED_MARKER)
md5 = hashlib.md5(raw).hexdigest()
imd5 = hashlib.md5(raw_idx).hexdigest()
if md5 != EXPECT_APP_MD5:
    print('WARN md5 app.js: have %s expected %s (anchors still decide)' % (md5, EXPECT_APP_MD5))
if imd5 != EXPECT_INDEX_MD5:
    print('WARN md5 index.html: have %s expected %s (anchors still decide)' % (imd5, EXPECT_INDEX_MD5))
v = re.findall(r'app\.js\?v=chat(\d+)"', h)
if len(v) != 1: die('index app.js?v=chatN bust matched %d times' % len(v))
n = int(v[0]); base, nxt = 'chat%d' % n, 'chat%d' % (n + 1)
print('base:', base, 'app.md5', md5, 'index.md5', imd5, '->', nxt)

def sub1(src, old, new, label):
    c = src.count(old)
    if c != 1: die('%s matched %d times' % (label, c))
    return src.replace(old, new, 1)

# Publish the venue calendar that already carries lunch windows (TSE, HKEX, and any later row with the same shape).
s = sub1(s,
    '  const H = { LSE: ["Europe/London", 480, 990], XETRA: ["Europe/Berlin", 540, 1050], EURONEXT: ["Europe/Paris", 540, 1050], TSE: ["Asia/Tokyo", 540, 930, 690, 750], HKEX: ["Asia/Hong_Kong", 570, 960, 720, 780], KRX: ["Asia/Seoul", 540, 930] };',
    '  const H = { LSE: ["Europe/London", 480, 990], XETRA: ["Europe/Berlin", 540, 1050], EURONEXT: ["Europe/Paris", 540, 1050], TSE: ["Asia/Tokyo", 540, 930, 690, 750], HKEX: ["Asia/Hong_Kong", 570, 960, 720, 780], KRX: ["Asia/Seoul", 540, 930] };\n  var fe66b_cal = H;',
    'venue calendar')

# Keep a lunch flag on the quote bag the fe64 formatter already reads.
s = sub1(s,
    '  var known = st === "closed" || st === "quiet" || st === "stale" || st === "delayed" || st === "fresh";',
    '  var known = st === "closed" || st === "quiet" || st === "stale" || st === "delayed" || st === "fresh" || st === "live" || st === "open" || st === "lunch";',
    'keep known status')
s = sub1(s,
    '  if (!known && !note && nextOpen === "" && delayMin == null) return;',
    '  var fe66bLunch = !!(q && (q.lunch === true || q.session === "lunch" || st === "lunch" || /lunch/i.test(note)));\n  if (!known && !note && nextOpen === "" && delayMin == null && !fe66bLunch) return;',
    'keep lunch flag')
s = sub1(s,
    '  var bag = { status: known ? st : (prev.status || ""), delayMin: delayMin != null ? delayMin : (prev.delayMin != null ? prev.delayMin : null), note: note || prev.note || "", nextOpen: nextOpen || prev.nextOpen || "" };\n  if (bag.status) fe64_keepYq.map[key] = bag;',
    '  var bag = { status: known ? st : (prev.status || ""), delayMin: delayMin != null ? delayMin : (prev.delayMin != null ? prev.delayMin : null), note: note || prev.note || "", nextOpen: nextOpen || prev.nextOpen || "" };\n  if (fe66bLunch) bag.lunch = true; else if (prev.lunch) bag.lunch = true;\n  if (q && typeof q.session === "string" && q.session) bag.session = q.session; else if (prev.session) bag.session = prev.session;\n  if (q && q.marketOpen === true) bag.marketOpen = true; else if (prev.marketOpen) bag.marketOpen = true;\n  if (bag.status || bag.lunch) fe64_keepYq.map[key] = bag;',
    'store lunch on bag')

# Status pill, glance chip, and the desktop watchlist row read the formatter output.
s = sub1(s,
    '  if(s==="closed")return `<span class="bd trust-stat trust-stat-cached" title="${title}" style="background:var(--puG);color:var(--pu);font-size:7.5px">CLOSED${d.fe64Note?" · "+_escHtml(d.fe64Note):""}</span>`;',
    '  if(s==="lunch")return `<span class="bd trust-stat trust-stat-cached" title="${title}" style="background:var(--blG);color:var(--bl);font-size:7.5px">${_escHtml(d.fe64Note||d.label||"Lunch break")}</span>`;\n  if(s==="closed")return `<span class="bd trust-stat trust-stat-cached" title="${title}" style="background:var(--puG);color:var(--pu);font-size:7.5px">CLOSED${d.fe64Note?" · "+_escHtml(d.fe64Note):""}</span>`;',
    'status pill')
s = sub1(s,
    '''       return `<button type="button" class="wl-glance-chip" onclick="openA('${tk}')" title="${String(sourceMeta)}">${live}<span class="wl-g-tk">${tk}</span><span class="wl-g-p">${state}</span><span class="wl-g-c" aria-label="${changeLabel}" title="${changeLabel}" style="color:${col}">${chgLbl}</span>${sourceTag}</button>`;''',
    '''       const lunchBadge = d.status === "lunch" && (d.fe64Note || d.label) ? `<span class="tape-badge tape-cache" style="margin-left:4px">${_escHtml(d.fe64Note || d.label)}</span>` : "";
       return `<button type="button" class="wl-glance-chip" onclick="openA('${tk}')" title="${String(sourceMeta)}">${live}<span class="wl-g-tk">${tk}</span><span class="wl-g-p">${state}</span><span class="wl-g-c" aria-label="${changeLabel}" title="${changeLabel}" style="color:${col}">${chgLbl}</span>${lunchBadge}${sourceTag}</button>`;''',
    'glance badge')
s = sub1(s,
    '''        <td style="font-weight:800;color:${catBd(a.cat)}">${a.tk}</td>''',
    '''        <td style="font-weight:800;color:${catBd(a.cat)}">${a.tk}${d.status==="lunch"?` <span class="tape-badge tape-cache">${_escHtml(d.fe64Note||d.label||"")}</span>`:""}</td>''',
    'watchlist badge')
s = sub1(s,
    '''    if (subEl) subEl.textContent = _dynData ? (fe66_closedQuote(_dynTk, {status:_dynData.status}) ? (fe66_note(_dynTk) || "Last close") : (_dynData.exchange||'DYNAMIC LOOKUP')) : (_dynLoading?'FETCHING…':'NOT FOUND');''',
    '''    if (subEl) subEl.textContent = _dynData ? (fe66b_line(_dynTk) || (fe66_closedQuote(_dynTk, {status:_dynData.status}) ? (fe66_note(_dynTk) || "Last close") : (_dynData.exchange||'DYNAMIC LOOKUP'))) : (_dynLoading?'FETCHING…':'NOT FOUND');''',
    'dynamic header')

BLOCK = r'''
// ── rt56b ──
// fe66b-pure-begin
function fe66b_now() {
  try { if (typeof fe66b_now.pin === "number" && isFinite(fe66b_now.pin)) return fe66b_now.pin; } catch (e) {}
  return Date.now();
}
function fe66b_ms(v) {
  if (v == null || v === "") return 0;
  var n = typeof v === "number" ? v : Date.parse(v);
  if (typeof v === "string" && /^\d{11,}$/.test(v)) n = Number(v);
  if (!isFinite(n) || n <= 0) return 0;
  if (n < 1e10) n *= 1000;
  return n;
}
function fe66b_ex(tk) {
  var t = String(tk || "");
  try {
    var a = (typeof A !== "undefined" && A && A.find) ? A.find(function (x) { return x && x.tk === t; }) : null;
    if (a && a.ex) return a.ex;
  } catch (e) {}
  if (/\.HK$/i.test(t)) return "HKEX";
  if (/\.T$/i.test(t)) return "TSE";
  if (/\.SS$/i.test(t)) return "SSE";
  if (/\.SZ$/i.test(t)) return "SZSE";
  if (/\.KS$/i.test(t)) return "KRX";
  if (/\.L$/i.test(t)) return "LSE";
  return "";
}
function fe66b_span(tk) {
  var row = null;
  try { row = (typeof fe66b_cal !== "undefined" && fe66b_cal) ? fe66b_cal[fe66b_ex(tk)] : null; } catch (e) { row = null; }
  if (!row || row.length < 5) return null;
  var lo = Number(row[3]), lc = Number(row[4]);
  if (!(lo >= 0) || !(lc > lo) || !(lc <= 1440)) return null;
  return { tz: row[0], lo: lo, lc: lc };
}
function fe66b_parts(tz, ms) {
  try { if (typeof _rt18Parts === "function") return _rt18Parts(tz, new Date(ms)); } catch (e) {}
  return null;
}
function fe66b_in(span, ms) {
  var p = fe66b_parts(span.tz, ms);
  if (!p) return false;
  if (p.wd === "Sat" || p.wd === "Sun") return false;
  return p.m >= span.lo && p.m < span.lc;
}
function fe66b_atMin(tz, ms, minute) {
  var p = fe66b_parts(tz, ms);
  if (!p) return 0;
  var guess = ms + (minute - p.m) * 60000;
  var i;
  for (i = 0; i < 4; i++) {
    var q = fe66b_parts(tz, guess);
    if (!q) return guess;
    var diff = minute - q.m;
    if (diff > 720) diff -= 1440;
    if (diff < -720) diff += 1440;
    if (diff === 0) return guess;
    guess += diff * 60000;
  }
  return guess;
}
function fe66b_uk(ms) {
  var hm = "";
  try { if (typeof fe64_ukHm === "function") hm = fe64_ukHm(ms) || ""; } catch (e) { hm = ""; }
  if (!hm) {
    try {
      var parts = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date(ms));
      var h = "", mi = "";
      parts.forEach(function (p) { if (p.type === "hour") h = p.value; if (p.type === "minute") mi = p.value; });
      if (h && mi) hm = h + ":" + mi;
    } catch (e2) { hm = ""; }
  }
  if (/^\d:\d{2}$/.test(hm)) hm = "0" + hm;
  return hm;
}
function fe66b_phrase(ms) {
  var hm = fe66b_uk(ms);
  return hm ? ("Lunch break \u00b7 resumes " + hm + " UK") : "Lunch break";
}
function fe66b_signal(bag) {
  if (!bag) return false;
  if (bag.lunch === true || bag.session === "lunch" || bag.status === "lunch") return true;
  return /lunch/i.test(String(bag.note || ""));
}
function fe66b_hold(bag) {
  if (!bag || fe66b_signal(bag)) return false;
  var s = String(bag.status || "");
  return s === "closed" || s === "stale" || s === "delayed" || s === "quiet";
}
function fe66b_calOk(bag) {
  if (!bag || !bag.status) return true;
  if (bag.marketOpen === true) return true;
  var s = String(bag.status);
  return s === "fresh" || s === "live" || s === "open";
}
function fe66b_text(tk, bag, when) {
  var ms = typeof when === "number" && isFinite(when) ? when : fe66b_now();
  if (fe66b_hold(bag)) return "";
  var span = fe66b_span(tk);
  if (fe66b_signal(bag)) {
    var told = fe66b_ms(bag && bag.nextOpen);
    if (told) return fe66b_phrase(told);
    if (span) return fe66b_phrase(fe66b_atMin(span.tz, ms, span.lc));
    return "Lunch break";
  }
  if (!fe66b_calOk(bag) || !span || !fe66b_in(span, ms)) return "";
  return fe66b_phrase(fe66b_atMin(span.tz, ms, span.lc));
}
function fe66b_line(tk) {
  var bag = null;
  try { bag = fe64_yqBag(tk); } catch (e) { bag = null; }
  return fe66b_text(tk, bag, fe66b_now());
}
function fe66b_applyMeta(tk, m) {
  var line = fe66b_line(tk);
  if (!line) return m;
  return Object.assign({}, m || {}, { status: "lunch", label: line, detail: line, fe64Note: line });
}
// fe66b-pure-end
function fe66b_show(fn, feed) {
  return function () {
    try {
      var tk = feed ? arguments[1] : arguments[0];
      var line = fe66b_line(tk);
      if (line) return line;
    } catch (e) {}
    return fn.apply(this, arguments);
  };
}
try { fe66_feedLbl = fe66b_show(fe66_feedLbl, true); } catch (e) {}
try { fe66_chgLine = fe66b_show(fe66_chgLine, false); } catch (e) {}
try { fe66_chartBit = fe66b_show(fe66_chartBit, false); } catch (e) {}
try { fe66_dynHead = fe66b_show(fe66_dynHead, false); } catch (e) {}
try {
  var fe66b_cl = _rt23ChartLbl;
  _rt23ChartLbl = function (tk) {
    try { var line = fe66b_line(tk); if (line) return line; } catch (e) {}
    return fe66b_cl.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe66b_qa = fe64_quoteApply;
  fe64_quoteApply = function (tk, m) {
    var r = m;
    try { r = fe66b_qa.apply(this, arguments); } catch (e) { r = m; }
    try { r = fe66b_applyMeta(tk, r); } catch (e2) {}
    return r;
  };
} catch (e) {}
try {
  var fe66b_qm = _quoteMeta;
  _quoteMeta = function (tk) {
    var m = fe66b_qm.apply(this, arguments);
    try { m = fe66b_applyMeta(tk, m); } catch (e) {}
    return m;
  };
} catch (e) {}
'''

if '// ── rt56b ──' in s: die('rt56b marker landed twice')
s = s.rstrip('\n') + '\n' + BLOCK
h = sub1(h, 'app.js?v=' + base + '"', 'app.js?v=' + nxt + '"', 'cache bust')

with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t:
    t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
os.unlink(tmp)
if r.returncode: die('node --check failed: ' + (r.stderr or '')[:800])
print('OK rt56b: %s -> %s; node --check passed%s' % (base, nxt, ' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
