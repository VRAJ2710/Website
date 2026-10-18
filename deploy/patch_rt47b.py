#!/usr/bin/env python3
"""patch_rt47b.py: chat48 -> chat49 (client only). Stacks on rt47 output (app.js 1df058b0).
Chart gym reliability: retries the site's chart feed across 6mo/1y/3mo daily ranges (the markets detail chart's pattern), starts each
request timeout only when the request leaves the shared chart queue, falls back to CoinGecko hourly prices (grouped into daily candles)
for Bitcoin/Ether, then to an embedded last-known daily snapshot clearly labelled with its date. Skip always advances; the last drill finishes.
Usage: python3 patch_rt47b.py [--check] <dir containing app.js and index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt47b ──' in s: die('rt47b already applied')
if '// ── rt47 ──' not in s: die('base is not rt47 output')
if 'app.js?v=chat48' not in h: die('index.html is not chat48')
for need in ['function _rt47Fetch(', 'function _rt47ChartPick(', 'function _rt47Skip(', 'function _rt47Can(', 'function _rt47Redraw(', 'function _rt47Finish(', 'function _rt47PlayerHtml(', 'function chartFetch(', 'function cgFetch(', 'const _rt47CD', 'const RT47_CHART_SYMS', 'function _rt46Swap(', 'function _rt46Toast(']:
    if need not in s: die('missing ' + need)
EDITS = [
    ("const kick = s.k === 'view' ? 'REAL CHART' : 'CHART GYM · REAL DATA';", "const kick = _rt47bKick(s, sym);"),
    ("const err = !sym && RT47_CHART_SYMS.every(x => _rt47CD[x[0]] && _rt47CD[x[0]].st === 'err') || (c && c.st === 'err');", "const err = _rt47bErr(i, sym, c);"),
    ("source: Yahoo Finance via the site's chart feed</p>`", "${_rt47bSrc(sym)}</p>`"),
    ('box = `<div class="rt47-chartbox" id="rt47chartbox">', 'box = `${_rt47bBadge(sym)}<div class="rt47-chartbox" id="rt47chartbox">'),
]
for a, b in EDITS:
    if s.count(a) != 1: die('anchor not unique/missing: ' + a[:60])
    s = s.replace(a, b)
SK = '${fine}`; }'
if s.count(SK) != 2: die('skip anchor')
s = s.replace(SK, '${fine}${_rt47bSkipBtn(i)}`; }')
BLOCK = r'''// ── rt47b ──
const RT47B_SNAP = {"GC=F":{"t":[20658,20661,20662,20663,20664,20665,20668,20669,20670,20671,20672,20675,20676,20677,20678,20679,20682,20683,20684,20685,20686,20689,20690,20691,20692,20693,20696,20697,20698,20699,20700,20704,20705,20706,20707,20710,20711,20712,20713,20714,20717,20718,20719,20720,20721,20724,20725,20726,20727,20728,20731,20732,20733,20734,20735,20738,20739,20740,20741,20742],"o":[4053.4,4097.5,4083,4020.9,4060.7,4163.9,4135.2,4109.6,4133.8,4307,4298.3,4400,4446.9,4430,4468.8,4408.2,4440,4473.4,4391.4,4580,4577,4673.4,4710.1,4715.7,4650,4656,4483.2,4498.7,4377.2,4436.4,4522,4466.5,4399,4448,4359.4,4375,4340.3,4333.5,4301.4,4381.6,4413,4382.5,4394.7,4324.4,4309.5,4315,4150.1,4216.2,4190.1,4204.6,4169.4,4169.2,4195,4139.9,4159.7,4220.8,4195.5,4184.2,4128.3,4192.1],"h":[4085.2,4119.3,4085.7,4115.2,4118.5,4170.7,4145.5,4163.8,4328.2,4363.7,4432.3,4453.8,4495,4502.7,4509.1,4454.6,4486.5,4493.1,4582.8,4597.1,4690.4,4738.5,4755,4730.9,4697.7,4688,4521.5,4510.5,4444.4,4558.5,4537.8,4488.8,4479,4479.9,4444.9,4396.8,4358.2,4413.1,4423.3,4439.8,4422.1,4414.1,4407.5,4338,4351.6,4315.6,4218.1,4251.1,4222.8,4259,4198.9,4212.4,4197.8,4170.7,4233.7,4242.3,4224.8,4193.5,4197.7,4220.4],"l":[4024,4067.1,4011.1,3993.8,4028.5,4076.4,4074,4098.2,4121.6,4281.2,4288,4373.9,4415.7,4421.4,4400,4365.5,4422.3,4383.3,4378,4506,4565.5,4651.8,4659.5,4638.2,4616,4495,4445.6,4369.7,4329.2,4426.7,4412,4381,4384.1,4354.7,4333,4293,4301.6,4273.3,4294.5,4372.2,4360.3,4327.6,4310.7,4278.3,4289.2,4143.1,4145.2,4178.2,4169.4,4153.8,4150.4,4130.7,4091.2,4128.1,4156.1,4178.1,4169.7,4095,4120.9,4167.5],"c":[4070.8,4077,4038.7,4036.3,4100.1,4107,4090.5,4152.6,4305.2,4299.6,4399.7,4419.7,4441.1,4467.5,4420.4,4437.3,4473.7,4420.6,4545.3,4571.4,4680.6,4697.8,4694.5,4653.3,4664,4529.9,4481.5,4396.4,4414.6,4539.9,4476.6,4439,4460.7,4407.3,4408.9,4351.9,4332.8,4387.5,4399.7,4424.9,4383.9,4376.4,4318.4,4298,4321.2,4168.4,4179.7,4186.7,4202.3,4162.3,4156.8,4187.1,4140.7,4157,4216.3,4190.6,4177.3,4107.9,4170.1,4181.1]},"^GSPC":{"t":[20658,20661,20662,20663,20664,20665,20668,20669,20670,20671,20672,20675,20676,20677,20678,20679,20682,20683,20684,20685,20686,20689,20690,20691,20692,20693,20696,20697,20698,20699,20700,20704,20705,20706,20707,20710,20711,20712,20713,20714,20717,20718,20719,20720,20721,20724,20725,20726,20727,20728,20731,20732,20733,20734,20735,20738,20739,20740,20741,20742],"o":[7406.3,7464.2,7395.55,7418.16,7390.45,7462.13,7504.78,7630.62,7771.62,7713.79,7735.18,7751.74,7767.51,7765.46,7763.18,7806.6,7790.68,7700.04,7716.74,7690.49,7665.68,7663.38,7676.66,7666.88,7710.34,7735.17,7697.52,7635.47,7634.58,7686.71,7750.19,7717.81,7660.68,7594.74,7636.75,7611.44,7612.3,7601.25,7631.44,7657.17,7692.83,7770.81,7761.94,7666.99,7709.86,7721.7,7699.6,7688.99,7666.47,7726.24,7730.86,7805.96,7792.98,7778.45,7786.36,7813.04,7795.27,7774.18,7687.31,7745.32],"h":[7460.98,7480.57,7452.09,7450.84,7448.75,7512.04,7610.04,7758.21,7793.68,7742.85,7763.08,7773.76,7767.51,7766.01,7816.7,7810.01,7790.68,7713.95,7743.93,7699.96,7697.11,7670.3,7686.11,7690.73,7741.27,7771.48,7697.52,7663.63,7681.19,7756.76,7750.19,7717.81,7660.68,7612.86,7677.02,7647.99,7617.26,7626.79,7646.86,7657.17,7779.22,7782.19,7761.94,7719.01,7752.07,7724.15,7699.6,7722.88,7684.75,7754.67,7794.35,7844.52,7807.02,7797.79,7820.57,7821.67,7814.15,7789.15,7754.15,7756.84],"l":[7396.53,7382.74,7382.95,7313.92,7370.98,7399.83,7504.78,7629.1,7720.17,7698.15,7719.19,7743.11,7717.25,7737.95,7763.18,7776.31,7744.88,7688.63,7700.07,7639.01,7660.06,7638.17,7650.92,7657.41,7689.89,7700.91,7665.06,7611.2,7633.62,7686.71,7706.12,7666.99,7624.16,7580.06,7636.75,7592.28,7572.69,7507.77,7611.81,7610.52,7691.19,7756.26,7694.89,7662.57,7693.08,7666.6,7653.55,7651.54,7616.78,7700.51,7727.59,7805.96,7763.34,7731.26,7779.34,7796.94,7786.11,7693.31,7669.66,7631.77],"c":[7411.98,7413.18,7428.78,7316.15,7437.63,7489.72,7600.5,7736.52,7723.55,7709.96,7757.64,7753.11,7728.2,7748.5,7798.99,7785.76,7745.06,7691.76,7707.98,7641.16,7674.37,7652.86,7677.28,7675.7,7730.99,7711.76,7686.14,7631.47,7666.6,7747.71,7718.6,7673.52,7636.36,7591.7,7656.98,7619.98,7585.73,7551.81,7637.76,7650.5,7764.7,7764.64,7706.03,7704.13,7743.41,7683.69,7670.84,7651.54,7666.45,7722.72,7773.95,7818.93,7801.77,7765.36,7811.54,7807.24,7805.45,7718.94,7744.06,7659.44]},"BTC-USD":{"t":[20684,20685,20686,20687,20688,20689,20690,20691,20692,20693,20694,20695,20696,20697,20698,20699,20700,20701,20702,20703,20704,20705,20706,20707,20708,20709,20710,20711,20712,20713,20714,20715,20716,20717,20718,20719,20720,20721,20722,20723,20724,20725,20726,20727,20728,20729,20730,20731,20732,20733,20734,20735,20736,20737,20738,20739,20740,20741,20742,20743],"o":[64680,69268,73031,78333,77083,77749,78960,78539,79038,80265,77831,78246,77674,78540,77402,77300,81272,79672,79825,80349,79115,78441,78260,76559,77175,77270,76830,78162,75612,76152,76405,80900,81234,81144,86604,86177,84382,84380,84036,84413,84454,83500,83621,83554,84856,84503,84766,86480,85786,85555,83281,81676,82546,82912,83679,81763,83095,81562,82141,81501],"h":[69997,73370,79464,78801,78037,79970,81235,79240,80807,81347,78328,79373,79247,79197,77738,82262,81433,80195,80531,80432,79463,79737,78521,79818,77480,77416,79569,78243,76474,77079,81332,81911,81455,87364,86700,87265,84876,85230,84423,85126,84973,84511,85600,85224,87146,85019,86766,86972,86665,85595,83475,83418,83092,84104,84249,84061,84049,82540,82821,81649],"l":[64111,68868,73011,76527,75625,76689,77871,77640,78591,76909,77382,77056,77378,76399,76248,76941,78642,79465,79328,78685,77636,77768,76471,76163,77045,76498,76367,74945,74996,75946,76228,80815,80099,80867,85098,83520,82907,83166,83781,84121,82571,82739,82928,83133,83853,84430,84707,84972,85120,82772,80337,81558,82473,82722,81682,80963,81346,79736,80719,80729],"c":[69266,73033,78335,77083,77755,78964,78565,79027,80258,77830,78246,77668,78549,77404,77300,81272,79672,79824,80350,79116,78439,78260,76568,77174,77270,76838,78163,75613,76150,76404,80901,81234,81143,86603,86172,84383,84379,84035,84406,84458,83503,83622,83554,84853,84497,84764,86480,85787,85558,83276,81676,82546,82912,83679,81763,83095,81562,82141,81501,81382]},"CL=F":{"t":[20658,20661,20662,20663,20664,20665,20668,20669,20670,20671,20672,20675,20676,20677,20678,20679,20682,20683,20684,20685,20686,20689,20690,20691,20692,20693,20696,20697,20698,20699,20700,20704,20705,20706,20707,20710,20711,20712,20713,20714,20717,20718,20719,20720,20721,20724,20725,20726,20727,20728,20731,20732,20733,20734,20735,20738,20739,20740,20741,20742],"o":[92.55,86.12,82,80.04,84.65,83.92,80.1,80.1,75.17,75.14,78.17,78.42,82.35,83.49,82.7,81.27,82.53,84.98,85.42,85.8,86.27,86.5,85.03,81.11,82,83.67,84.69,86.31,90.65,90.7,91.67,92.26,94.31,96.88,104.32,102.25,102.01,105.48,102.18,101.06,101,95.39,89.89,92.72,94.75,93.58,93.53,89,90.4,93.46,91.77,89.27,89.96,89,91.29,91.83,93.21,94.75,95.19,96.14],"h":[92.83,86.2,82.43,85.57,85.94,86.87,81.3,82.33,76.7,78.51,78.77,82.38,84.61,84.35,83.3,82.99,85.04,85.94,87.19,89,87.51,86.57,85.84,83.31,84.27,83.78,86.79,90.97,92.29,93.14,92.17,94.73,96.93,104.04,104.46,104.95,106.75,105.63,102.47,103.48,101.08,97.42,93.06,96.78,94.75,96.54,94.74,91.96,93.68,93.51,91.88,90.05,90.98,93.2,92.17,94.36,95.11,96.06,98.32,99.34],"l":[87.68,81.63,77.78,79.92,82.97,81.06,78.43,75.11,74.24,74.57,76.53,77.79,81.27,82.4,80.09,80.71,81.5,84.57,84.32,85.6,85.8,84.36,80.23,79.62,80.65,82.25,84.11,86.13,88.97,89.57,88.72,90.87,93.76,95.37,98.48,100.53,101.21,100.97,99.1,99.19,94.22,92.4,88.71,91.23,91.51,91.25,88.78,88.58,88.79,88.06,88.74,86.86,87.96,88.77,90.01,89.61,91.7,93.97,93.58,95.29],"c":[89.31,82.61,79.26,84.46,83.59,84.67,80.34,75.77,75.22,77.29,78.18,82.13,83.2,83.27,81.25,82.4,84.5,84.94,85.83,87.83,87.06,85.01,82.36,82.23,83.53,83.4,85.76,90.22,91.01,91.3,91.48,93.03,96.05,102.48,100.05,101.39,105.83,102.43,101.91,100.3,95.78,94.59,92.16,94.61,92.41,92.6,89.38,90.42,92.87,91.11,89.43,89.44,88.28,91.49,91.85,93.74,94.14,95.09,97.97,99.02]}};
// Chart gym data: retry the site's chart feed across ranges (same pattern as the markets detail chart), never let time spent
// in the shared chart queue count against the request timeout, fall back to CoinGecko for crypto, then to a saved snapshot.
const RT47B_WAIT = 9000;
const _RT47B_TRY = [['6mo', '1d'], ['1y', '1d'], ['3mo', '1d']];
const RT47B_CG = { 'BTC-USD': 'bitcoin', 'ETH-USD': 'ethereum' };
function _rt47bOpts(ms) { const o = {}; try { Object.defineProperty(o, 'signal', { enumerable: true, get() { try { return AbortSignal.timeout(ms); } catch (e) { return undefined; } } }); } catch (e) {} return o; }
function _rt47bParse(j) { const r = j && j.chart && j.chart.result && j.chart.result[0], q = r && r.indicators && r.indicators.quote && r.indicators.quote[0], ts = r && r.timestamp; if (!q || !Array.isArray(ts)) return null;
  const d = { t: [], o: [], h: [], l: [], c: [] }, seen = {};
  ts.forEach((t, i) => { const o = q.open && q.open[i], h = q.high && q.high[i], l = q.low && q.low[i], c = q.close && q.close[i]; if (![o, h, l, c].every(v => typeof v === 'number' && isFinite(v) && v > 0)) return;
    const day = Math.floor(t / 86400); if (seen[day] != null) { const k = seen[day]; d.h[k] = Math.max(d.h[k], h, o, c); d.l[k] = Math.min(d.l[k], l, o, c); d.c[k] = c; return; }
    seen[day] = d.t.length; d.t.push(t * 1000); d.o.push(o); d.h.push(Math.max(h, o, c)); d.l.push(Math.min(l, o, c)); d.c.push(c); });
  return d.c.length >= 40 ? d : null; }
async function _rt47bCg(id) {
  if (typeof cgFetch !== 'function' || (typeof _cgBackoffUntil !== 'undefined' && Date.now() < _cgBackoffUntil)) return null;
  const res = await cgFetch(`https://api.coingecko.com/api/v3/coins/${id}/market_chart?vs_currency=usd&days=90`, _rt47bOpts(12000));
  if (!res || !res.ok || res.headers.get('X-Dispatch-Data-Status') === 'unavailable') return null;
  const j = await res.json(), px = (j && j.prices || []).filter(p => Array.isArray(p) && typeof p[1] === 'number' && isFinite(p[1]) && p[1] > 0);
  const today = Math.floor(Date.now() / 86400000), by = new Map();
  px.forEach(([t, v]) => { const day = Math.floor(t / 86400000); if (day >= today) return; let b = by.get(day); if (!b) { b = { o: v, h: v, l: v, c: v, n: 0 }; by.set(day, b); } b.h = Math.max(b.h, v); b.l = Math.min(b.l, v); b.c = v; b.n++; });
  const d = { t: [], o: [], h: [], l: [], c: [] }; [...by.keys()].sort((a, b) => a - b).forEach(day => { const b = by.get(day); if (b.n < 6) return; d.t.push(day * 86400000); d.o.push(b.o); d.h.push(b.h); d.l.push(b.l); d.c.push(b.c); });
  return d.c.length >= 40 ? d : null; }
function _rt47bSnap(sym) { const s = RT47B_SNAP[sym]; if (!s) return null; return { t: s.t.map(x => x * 86400000), o: s.o.slice(), h: s.h.slice(), l: s.l.slice(), c: s.c.slice() }; }
function _rt47bSnapFill() { Object.keys(RT47B_SNAP).forEach(sym => { const c = _rt47CD[sym]; if (!c || c.st !== 'ok') _rt47CD[sym] = { st: 'ok', d: _rt47bSnap(sym), src: 'snap', at: Date.now() }; }); }
function _rt47bWaiting() { try { if (!_rt47L.id) return false; const s = _rt47Steps(_rt47L.id)[_rt47L.i], a = _rt47L.a[_rt47L.i]; return !!(s && s.t === 'chart' && !(a && a.sym && _rt47CD[a.sym] && _rt47CD[a.sym].st === 'ok' && a.shown === a.sym)); } catch (e) { return false; } }
function _rt47Fetch(sym) { const c = _rt47CD[sym]; if (c && (c.st !== 'err' || Date.now() - c.at < 20000)) return c;
  const mine = _rt47CD[sym] = { st: 'loading', at: Date.now() };
  (async () => { let d = null, src = 'yahoo';
    for (const [rg, iv] of _RT47B_TRY) { try { const f = typeof chartFetch === 'function' ? chartFetch : fetch;
      const res = await f(`/api/yahoo-chart?symbol=${encodeURIComponent(sym)}&range=${rg}&interval=${iv}`, _rt47bOpts(12000)); if (res && res.ok) { d = _rt47bParse(await res.json()); if (d) break; } } catch (e) {} }
    if (!d && RT47B_CG[sym]) { try { d = await _rt47bCg(RT47B_CG[sym]); if (d) src = 'cg'; } catch (e) {} }
    if (!d && RT47B_SNAP[sym]) { d = _rt47bSnap(sym); src = 'snap'; }
    const cur = _rt47CD[sym]; if (cur && cur.st === 'ok' && cur !== mine) return; // never swap data under an exercise that is already showing it
    _rt47CD[sym] = d ? { st: 'ok', d, src, at: Date.now() } : { st: 'err', at: Date.now() };
  })().catch(() => {}).finally(() => { try { if (_rt47bWaiting()) _rt47Redraw(); } catch (e) {} });
  return mine; }
function _rt47ChartPick(i, s) { const a = _rt47L.a[i] || (_rt47L.a[i] = {}); if (a.sym && _rt47CD[a.sym] && _rt47CD[a.sym].st === 'ok') return a.sym;
  if (!a.t0) { a.t0 = Date.now(); setTimeout(() => { try { if (_rt47L.a[i] === a && !a.sym && _rt47L.i === i) _rt47Redraw(); } catch (e) {} }, RT47B_WAIT + 150); }
  const late = Date.now() - a.t0 >= RT47B_WAIT, syms = RT47_CHART_SYMS.map(x => x[0]);
  if (s.k === 'trend') { const order = s.s ? [s.s, ...syms.filter(x => x !== s.s)] : syms; order.forEach(x => _rt47Fetch(x));
    if (late) _rt47bSnapFill();
    const ok = order.filter(x => _rt47CD[x].st === 'ok'), loading = order.some(x => _rt47CD[x].st === 'loading');
    if (!late && (!ok.length || (s.s && _rt47CD[s.s].st === 'loading'))) return '';
    if (!late && loading && !ok.some(x => _rt47CD[x].src !== 'snap')) return ''; // prefer live data (e.g. Bitcoin via CoinGecko) over the snapshot while it is still loading
    if (!ok.length) return '';
    const live = ok.filter(x => _rt47CD[x].src !== 'snap'), pool = live.length ? live : ok;
    const clear = pool.filter(x => _rt47Trend(_rt47Win(_rt47CD[x].d, 60).c).k);
    if (!clear.length) { if (loading && !late) return ''; a.fallback = 1; a.sym = pool[0]; return a.sym; }
    a.sym = clear[s.alt ? Math.min(1, clear.length - 1) : 0]; return a.sym; }
  const want = s.s || 'GC=F', c = _rt47Fetch(want); if (c.st === 'ok') { a.sym = want; return want; }
  if (c.st === 'loading' && !late) return '';
  if (late) _rt47bSnapFill(); if (_rt47CD[want] && _rt47CD[want].st === 'ok') { a.sym = want; return want; }
  const alt = syms.find(x => _rt47CD[x] && _rt47CD[x].st === 'ok'); if (alt) a.sym = alt; return a.sym || ''; }
function _rt47bSrc(sym) { const c = _rt47CD[sym] || {}; if (c.src === 'cg') return "source: CoinGecko hourly prices via the site's crypto feed, grouped into UTC daily candles";
  if (c.src === 'snap') return `source: saved snapshot of Yahoo Finance daily data to ${_rt47bTo(sym)}, because the live chart feed is unavailable right now`;
  return "source: Yahoo Finance via the site's chart feed"; }
function _rt47bTo(sym) { try { const s = RT47B_SNAP[sym]; return new Date(s.t[s.t.length - 1] * 86400000).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }); } catch (e) { return ''; } }
function _rt47bBadge(sym) { const c = _rt47CD[sym] || {}; try { const a = _rt47L.a[_rt47L.i]; if (a) a.shown = sym; } catch (e) {}
  return c.src === 'snap' ? `<div class="rt47b-snap" role="note"><b>Saved snapshot</b> · daily candles to ${_rt47bTo(sym)} · the live chart feed is unavailable right now</div>` : ''; }
function _rt47bKick(s, sym) { const c = _rt47CD[sym] || {}; return s.k === 'view' ? (c.src === 'snap' ? 'REAL CHART · SAVED' : 'REAL CHART') : (c.src === 'snap' ? 'CHART GYM · SAVED DATA' : 'CHART GYM · REAL DATA'); }
// Skip always moves on (and the last drill finishes), even if the normal Continue gate would refuse
function _rt47Skip(i) { try { const st = _rt47Steps(_rt47L.id); if (!st.length) return; i = Number(i); if (!isFinite(i)) i = _rt47L.i;
  const a = _rt47L.a[i] || (_rt47L.a[i] = {}); a.skip = true; _rt47Act = Date.now(); const nx = Math.min(i + 1, st.length - 1);
  try { _rt47Go(nx); } catch (e) {}
  if (_rt47L.i !== nx) { _rt47L.dir = 1; _rt47L.i = nx; _rt47Prog = Date.now(); if (st[nx].t === 'end') { try { _rt47Finish(); } catch (e) {} } _rt46Swap('rt47pl', _rt47PlayerHtml(), '#rt47plh'); try { _rt47Top(); } catch (e) {} setTimeout(_rt45SyncUrl, 0); }
  const sg = document.getElementById('rt47stage'); if (!sg || String(sg.dataset.i) !== String(nx)) { _rt47Prog = Date.now(); _refreshView(); }
  try { _rt46Toast(st[nx].t === 'end' ? 'Exercise skipped. Drills finished.' : 'Exercise skipped. No XP for this one.'); } catch (e) {} } catch (e) {} }
function _rt47Can(i) { const s = _rt47Steps(_rt47L.id)[i], a = _rt47L.a[i]; if (!s) return false;
  if (s.t === 'q') return !!a; if (s.t === 'scen') return !!(a && a.done); if (s.t === 'chart' && s.k !== 'view') return !!(a && (a.done || a.skip || (!a.sym && a.t0 && Date.now() - a.t0 >= RT47B_WAIT))); return true; }
try { const st = document.createElement('style'); st.id = 'rt47bcss'; st.textContent = `.rt47b-snap{font-size:12.5px;line-height:1.45;color:var(--tx);background:rgba(217,174,82,.10);border:1px solid rgba(217,174,82,.45);border-radius:10px;padding:8px 11px;margin:0 0 10px}.rt47b-snap b{color:var(--gd)}`; document.head.appendChild(st); } catch (e) {}
function _rt47bErr(i, sym, c) { const a = _rt47L.a[i] || {}, late = !a.t0 || Date.now() - a.t0 >= RT47B_WAIT; if (!late) return false;
  return (!sym && RT47_CHART_SYMS.every(x => !_rt47CD[x[0]] || _rt47CD[x[0]].st !== 'loading')) || !!(c && c.st === 'err'); }
function _rt47bSkipBtn(i) { const a = _rt47L.a[i] || {}; return a.done ? '' : `<button type="button" class="rt47-link rt47b-skip" onclick="_rt47Skip(${i})">Skip this drill</button>`; }
// drills where every exercise was skipped end quietly: no confetti, no "Nice work"
{ const _fi7b = _rt47Finish; _rt47Finish = function () { try { const st = _rt47Steps(_rt47L.id), dr = st.map((s, k) => [s, k]).filter(([s]) => s.t === 'chart' && s.k !== 'view');
  if (!RT47_LESSONS[_rt47L.id] && dr.length && dr.every(([s, k]) => _rt47L.a[k] && _rt47L.a[k].skip && !_rt47L.a[k].done)) { _rt47L.fin = true; _rt47L.res = { ok: 0, n: 0, need: 0, pass: false }; return; } } catch (e) {}
  return _fi7b.apply(this, arguments); }; }
'''
s = s.rstrip('\n') + '\n' + BLOCK
if h.count('app.js?v=chat48') != 1: die('index bust anchor')
h = h.replace('app.js?v=chat48', 'app.js?v=chat49')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print('OK rt47b: 6 anchored edits + block appended + index chat48->chat49; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
