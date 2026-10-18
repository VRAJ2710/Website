#!/usr/bin/env python3
"""patch_rt49about.py: About / brand panel redesign (client only) + founder photo file.
Appends one block to app.js (no in-place edits: it redefines openAbout/closeAbout and wraps renderAuthButtons, so it stacks
cleanly on chat49 or on rt48's chat50 output), bumps index.html app.js?v=chatN -> chatN+1, and writes founder.jpg next to
index.html only if no founder.jpg exists yet (never overwrites a photo you uploaded).
Usage: python3 patch_rt49about.py [--check] <dir containing app.js and index.html>"""
import sys, os, re, subprocess, tempfile, base64, hashlib
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX, JPG = os.path.join(D, 'app.js'), os.path.join(D, 'index.html'), os.path.join(D, 'founder.jpg')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt49about ──' in s: die('rt49about already applied')
for need in ['function openAbout(){', 'function closeAbout(){', 'function renderAuthButtons() {', 'const _a11yDialogState', 'function _openA11yDialog(', 'function _fxOverlayEnter(', 'function _openBillingPortal(', 'let _userAdmin']:
    if s.count(need) != 1: die('About anchor missing/not unique: ' + need)
if h.count('id="aboutOv"') != 1: die('index.html has no unique #aboutOv')
v = re.findall(r'app\.js\?v=chat(\d+)"', h)
if len(v) != 1: die('index app.js?v=chatN bust not found exactly once')
n = int(v[0]); base = 'chat%d' % n; nxt = 'chat%d' % (n + 1)
if n < 49: die('index is %s; expected chat49 or later' % base)
if base == 'chat50' and '// ── rt48' not in s: print('WARN: index is chat50 but no rt48 marker in app.js')
print('base:', base, '(rt48 present)' if '// ── rt48' in s else '(no rt48)')
BLOCK = r'''// ── rt49about ──
// About / brand panel rebuilt as a proper sheet (phone) / modal (desktop): sticky header + close, hero, coverage,
// membership cards (CTA to /pricing; signed-in members/admin see their status), founder card with photo
// (/founder.jpg, falls back to a monogram), honest data sources, collapsible disclaimer. Also fixes closeAbout()
// leaving the page scroll-locked (body position:fixed) after the panel was closed.
const RT49_PHOTO = '/founder.jpg';
const RT49_LI = 'https://www.linkedin.com/in/VRAJ2710';
let _rt49Built = false, _rt49PhotoTried = false, _rt49Guard = null, _rt49EscG = null;
function _rt49Esc(t) { return String(t == null ? '' : t).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]); }
function _rt49State() {
  let ready = true, signed = false, admin = false, prem = false;
  try { ready = typeof _userTierReady === 'undefined' ? true : !!_userTierReady; } catch (e) {}
  try { signed = typeof _userSignedIn !== 'undefined' && !!_userSignedIn; } catch (e) {}
  try { admin = _userAdmin === true; } catch (e) {}
  try { prem = typeof _isPremium === 'function' && !!_isPremium(); } catch (e) {}
  if (admin) return 'admin'; if (prem) return 'premium'; if (signed) return 'free'; return ready ? 'guest' : 'loading';
}
function _rt49AcctHtml(st) {
  if (st === 'admin') return `<div class="rt49-acct-in"><span class="rt49-badge rt49-badge-gd">Admin · Full access</span><span class="rt49-acct-acts"><a class="rt49-btn rt49-btn-gh" href="/__admin">Console</a><a class="rt49-btn rt49-btn-gh" href="/__auth/logout">Sign out</a></span></div>`;
  if (st === 'premium') return `<div class="rt49-acct-in"><span class="rt49-badge rt49-badge-gd">Premium active</span><span class="rt49-acct-acts"><button type="button" class="rt49-btn rt49-btn-gh" onclick="_openBillingPortal()">Manage billing</button><a class="rt49-btn rt49-btn-gh" href="/__auth/logout">Sign out</a></span></div>`;
  if (st === 'free') return `<div class="rt49-acct-in"><span class="rt49-badge">Signed in · Free plan</span><span class="rt49-acct-acts"><a class="rt49-btn rt49-btn-gd" href="/pricing">Upgrade to Premium</a><a class="rt49-btn rt49-btn-gh" href="/__auth/logout">Sign out</a></span></div>`;
  if (st === 'loading') return `<div class="rt49-acct-in rt49-acct-wait" aria-hidden="true"><span class="rt49-badge">Checking your account…</span></div>`;
  return `<div class="rt49-acct-in"><span class="rt49-acct-acts"><a class="rt49-btn rt49-btn-gd" href="/__auth/register">Create free account</a><a class="rt49-btn rt49-btn-gh" href="/__auth/login">Sign in</a></span></div>`;
}
function _rt49PlansHtml(st) {
  const tick = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8.5l3 3 7-7" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  const li = a => a.map(x => `<li>${tick}<span>${x}</span></li>`).join('');
  const freeCta = st === 'guest' || st === 'loading' ? `<a class="rt49-btn rt49-btn-gh rt49-btn-wide" href="/__auth/register">Create free account</a>`
    : st === 'free' ? `<span class="rt49-plan-mine">Your plan</span>` : '';
  const premCta = st === 'admin' ? `<span class="rt49-plan-mine">Included with admin access</span>`
    : st === 'premium' ? `<span class="rt49-plan-mine">Your plan</span>`
    : `<a class="rt49-btn rt49-btn-gd rt49-btn-wide" href="/pricing">${st === 'free' ? 'Upgrade to Premium' : 'Get Premium'}</a>`;
  return `<div class="rt49-plan">
      <div class="rt49-plan-hd"><span class="rt49-plan-n">Free</span><span class="rt49-plan-p">£0</span></div>
      <ul class="rt49-ul">${li(['Live and delayed market prices with charts', 'Markets, crypto, newsroom and heatmaps', 'Regime model and the free desk brief', 'Market Lab, Desk Run and the Letter', 'Watchlists and price alerts'])}</ul>
      ${freeCta}</div>
    <div class="rt49-plan rt49-plan-pr">
      <div class="rt49-plan-rib">Full research</div>
      <div class="rt49-plan-hd"><span class="rt49-plan-n">Premium</span><span class="rt49-plan-p">£15<small>/month</small></span></div>
      <ul class="rt49-ul">${li(['Everything in Free', 'Weekly Gold Playbook', 'AI Dispatch Brief', 'Ask research assistant and AI lenses', 'Company statements and institutional holders', 'Custom screener and document intelligence', 'No token mark-up · cancel any time'])}</ul>
      ${premCta}</div>`;
}
function _rt49Html() {
  const st = _rt49State();
  const cov = [
    ['Gold &amp; metals', 'Spot gold and silver, COMEX futures, copper'],
    ['Macro &amp; rates', 'Real yields, the 10-year, the Fed, inflation data'],
    ['FX &amp; the dollar', 'The majors and the dollar index'],
    ['Energy', 'WTI and Brent, with the official EIA spot price'],
    ['Crypto', 'Bitcoin and Ether, streaming 24/7'],
    ['Global stocks', 'US, Europe and Asia, each with its own open/closed status'],
  ].map(([a, b]) => `<li><b>${a}</b><span>${b}</span></li>`).join('');
  const src = [
    ['Crypto', 'Live streams from Coinbase and Kraken, with CoinGecko as back-up'],
    ['Metals spot', 'gold-api.com'],
    ['Stocks, FX, indices', 'Twelve Data, Finnhub and Yahoo Finance'],
    ['Futures', 'Yahoo Finance, about 10 minutes delayed (oil and metals)'],
    ['Official oil', 'US Energy Information Administration (EIA), published daily'],
  ].map(([a, b]) => `<li><b>${a}</b><span>${b}</span></li>`).join('');
  return `<div class="rt49-sheet" role="document">
  <div class="rt49-hd">
    <span class="rt49-grab" aria-hidden="true"></span>
    <span class="rt49-hd-k"><span class="rt49-hd-dot" aria-hidden="true"></span>About the desk</span>
    <button type="button" class="rt49-x" onclick="closeAbout()" aria-label="Close About"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button>
  </div>
  <div class="rt49-body">
    <section class="rt49-hero">
      <div class="rt49-kick">A gold &amp; macro research house</div>
      <h2 class="rt49-ttl" id="about-dialog-title" tabindex="-1">The <em>Dispatch</em> Markets</h2>
      <p class="rt49-lede">Every week, a conditional gold playbook built from disclosed, clearly dated market data. You get a stance you can defend: what would confirm it, what would invalidate it, and which events could change the thesis.</p>
      <div class="rt49-stats"><div><b>Weekly</b><span>Gold Playbook</span></div><div><b>24/7</b><span>Crypto streams</span></div><div><b>Every price</b><span>Dated and labelled</span></div></div>
      <div class="rt49-acct" id="rt49Acct">${_rt49AcctHtml(st)}</div>
    </section>
    <section class="rt49-sec"><h3 class="rt49-h">What the desk covers</h3><ul class="rt49-cov">${cov}</ul></section>
    <section class="rt49-sec"><h3 class="rt49-h">Membership</h3><div class="rt49-plans" id="rt49Plans">${_rt49PlansHtml(st)}</div>
      <a class="rt49-more" href="/pricing">Compare plans in full <span aria-hidden="true">→</span></a></section>
    <section class="rt49-sec"><h3 class="rt49-h">Founder &amp; analyst</h3>
      <div class="rt49-founder">
        <div class="rt49-ph rt49-nophoto"><img alt="Vraj Patel, founder of The Dispatch Markets" width="88" height="88" decoding="async" hidden><span class="rt49-mono" aria-hidden="true">VP</span></div>
        <div class="rt49-fd">
          <div class="rt49-name">Vraj Patel</div>
          <div class="rt49-role">Founder · Analyst</div>
          <p class="rt49-bio">Vraj founded The Dispatch to give independent traders a disciplined, honest read on gold and macro. He writes the desk's research and builds the platform himself, from the live data feeds to Dispatch Academy.</p>
          <a class="rt49-btn rt49-btn-li" href="${RT49_LI}" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 110-4.13 2.06 2.06 0 010 4.13zm1.78 13.02H3.56V9h3.56v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0z"/></svg>Connect on LinkedIn<span class="rt49-sr"> (opens in a new tab)</span></a>
        </div>
      </div></section>
    <section class="rt49-sec"><h3 class="rt49-h">Where the numbers come from</h3><ul class="rt49-src">${src}</ul>
      <p class="rt49-note">Every price shows its own status, LIVE, DELAYED or CLOSED, for the venue it trades on, so a closed stock market never hides live crypto or FX.</p></section>
    <details class="rt49-disc"><summary><span>Disclaimer</span><span class="rt49-disc-s">Research and education only</span></summary>
      <p>Research and education only. Market data may be delayed, incomplete or inaccurate. Nothing here is financial advice or a recommendation to buy or sell. See the <a href="/terms">Terms</a> and the <a href="/privacy">Privacy notice</a>.</p></details>
    <div class="rt49-ft"><nav class="rt49-links" aria-label="About links"><a href="/pricing">Pricing</a><a href="/learn/">Learn</a><a href="/terms">Terms</a><a href="/privacy">Privacy</a></nav>
      <button type="button" class="rt49-btn rt49-btn-gh rt49-done" onclick="closeAbout()">Close</button></div>
  </div>
</div>`;
}
function _rt49Photo(ov) {
  const box = ov.querySelector('.rt49-ph'), img = box && box.querySelector('img'); if (!img) return;
  const ok = () => { if (img.naturalWidth > 0) { img.hidden = false; box.classList.remove('rt49-nophoto'); } else bad(); };
  const bad = () => { img.hidden = true; box.classList.add('rt49-nophoto'); };
  if (_rt49PhotoTried && img.getAttribute('src')) { if (img.complete) ok(); return; }
  _rt49PhotoTried = true; img.addEventListener('load', ok, { once: true }); img.addEventListener('error', bad, { once: true }); img.src = RT49_PHOTO;
}
function _rt49Build() {
  const ov = document.getElementById('aboutOv'); if (!ov) return null;
  if (!_rt49Built || !ov.querySelector('.rt49-sheet')) {
    ov.removeAttribute('onclick'); ov.classList.add('rt49-ov'); ov.innerHTML = _rt49Html(); _rt49Built = true; _rt49PhotoTried = false;
    if (!ov._rt49Click) { ov._rt49Click = true; ov.addEventListener('click', e => { if (e.target === ov) closeAbout(); }); }
  }
  return ov;
}
function _rt49Refresh() {
  try { const ov = document.getElementById('aboutOv'); if (!ov || !_rt49Built) return; const st = _rt49State();
    if (ov.dataset.rt49st === st) return; ov.dataset.rt49st = st;
    const a = document.getElementById('rt49Acct'), p = document.getElementById('rt49Plans');
    const keep = document.activeElement && (a && a.contains(document.activeElement) || p && p.contains(document.activeElement));
    if (a) a.innerHTML = _rt49AcctHtml(st); if (p) p.innerHTML = _rt49PlansHtml(st);
    if (keep) ov.querySelector('.rt49-x')?.focus(); } catch (e) {}
}
openAbout = function () {
  const ov = _rt49Build(); if (!ov) return;
  if (!ov.classList.contains('hide') && _a11yDialogState.get(ov)) return;
  ov.dataset.rt49st = ''; _rt49Refresh();
  const d = ov.querySelector('.rt49-disc'); if (d) d.open = false;
  ov.classList.remove('hide'); ov.classList.add('fx-sov-enter');
  const body = ov.querySelector('.rt49-body'); if (body) body.scrollTop = 0;
  _rt49Photo(ov);
  try { _fxOverlayEnter(ov.querySelector('.rt49-sheet')); } catch (e) {}
  _openA11yDialog(ov, closeAbout, '.rt49-x');
  // keep focus inside even if a background re-render moves it (signed-in boot re-nav, live tape refresh)
  if (!_rt49Guard) { _rt49Guard = e => { const o = document.getElementById('aboutOv'); if (!o || o.classList.contains('hide') || o.contains(e.target)) return; try { e.stopPropagation(); } catch (x) {} (o.querySelector('.rt49-x') || o).focus({ preventScroll: true }); };
    _rt49EscG = e => { const o = document.getElementById('aboutOv'); if (e.key === 'Escape' && o && !o.classList.contains('hide') && !o.contains(e.target)) { e.preventDefault(); closeAbout(); } }; }
  document.addEventListener('focusin', _rt49Guard, true); document.addEventListener('keydown', _rt49EscG, true);
};
closeAbout = function () {
  const ov = document.getElementById('aboutOv'); if (!ov) return;
  ov.classList.add('hide');
  if (_rt49Guard) { document.removeEventListener('focusin', _rt49Guard, true); document.removeEventListener('keydown', _rt49EscG, true); }
  const s = _a11yDialogState.get(ov); if (!s) return;
  ov.removeEventListener('keydown', s.handler); _a11yDialogState.delete(ov);
  document.documentElement.style.overflow = s.htmlOverflow || ''; document.body.style.overflow = s.bodyOverflow || '';
  document.body.style.position = s.bodyPosition || ''; document.body.style.top = s.bodyTop || ''; document.body.style.width = s.bodyWidth || '';
  try { window.scrollTo(0, s.scrollY || 0); } catch (e) {}
  if (s.invoker && s.invoker.isConnected) setTimeout(() => { try { s.invoker.focus({ preventScroll: true }); } catch (e) {} }, 0);
};
{ const _ra49 = renderAuthButtons; renderAuthButtons = function () { const r = _ra49.apply(this, arguments); _rt49Refresh(); return r; }; }
try { const st = document.createElement('style'); st.id = 'rt49css'; st.textContent = `
#aboutOv.rt49-ov{position:fixed;inset:0;z-index:1000;display:flex;align-items:flex-end;justify-content:center;padding:0;margin:0;background:rgba(6,7,10,.74);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);overflow:hidden;overscroll-behavior:contain}
#aboutOv.rt49-ov.hide{display:none}
#aboutOv .rt49-sheet{--r49g:var(--gold,#D9AE52);position:relative;box-sizing:border-box;width:100%;max-width:100%;max-height:calc(100vh - 16px);max-height:calc(100dvh - 12px - env(safe-area-inset-top,0px));display:flex;flex-direction:column;background:var(--paper,#14151A);color:var(--ink,#EDEDE8);border:1px solid var(--rule,rgba(237,237,232,.14));border-bottom:0;border-radius:20px 20px 0 0;box-shadow:0 -18px 60px rgba(0,0,0,.45);overflow:hidden;text-align:left}
#aboutOv .rt49-sheet *{box-sizing:border-box}
#aboutOv .rt49-hd{position:relative;flex:0 0 auto;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 12px 10px 20px;border-bottom:1px solid var(--rule,rgba(237,237,232,.14));background:var(--paper,#14151A)}
#aboutOv .rt49-grab{position:absolute;top:6px;left:50%;width:38px;height:4px;margin-left:-19px;border-radius:4px;background:var(--rule,rgba(237,237,232,.2))}
#aboutOv .rt49-hd-k{display:inline-flex;align-items:center;gap:8px;font-family:var(--mn);font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--t2,#A8ADB6)}
#aboutOv .rt49-hd-dot{width:7px;height:7px;border-radius:50%;background:var(--r49g);box-shadow:0 0 0 3px rgba(217,174,82,.18)}
#aboutOv .rt49-x{flex:0 0 auto;width:44px;height:44px;display:inline-flex;align-items:center;justify-content:center;border-radius:50%;border:1px solid var(--rule,rgba(237,237,232,.14));background:transparent;color:var(--ink,#EDEDE8);cursor:pointer;padding:0;margin:0;transition:background .15s,border-color .15s}
#aboutOv .rt49-x svg{width:18px;height:18px}
#aboutOv .rt49-x:hover{background:var(--paper-2,#1B1D23);border-color:var(--r49g)}
#aboutOv .rt49-x:focus-visible,#aboutOv .rt49-btn:focus-visible,#aboutOv a:focus-visible,#aboutOv summary:focus-visible{outline:2px solid var(--r49g);outline-offset:2px}
#aboutOv .rt49-body{flex:1 1 auto;min-height:0;overflow-y:auto;overflow-x:hidden;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;padding:0 20px calc(20px + env(safe-area-inset-bottom,0px))}
#aboutOv .rt49-hero{padding:22px 0 20px;border-bottom:1px solid var(--rule,rgba(237,237,232,.14))}
#aboutOv .rt49-body{background:radial-gradient(90% 420px at 0% 0%,rgba(217,174,82,.09),transparent 70%) no-repeat local}
#aboutOv .rt49-sr{position:absolute!important;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
#aboutOv .rt49-kick{font-family:var(--mn);font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--r49g);margin:0 0 10px}
#aboutOv .rt49-ttl{font-family:var(--sf);font-weight:600;font-size:clamp(30px,8.6vw,44px);line-height:1.04;letter-spacing:-.02em;margin:0 0 12px;color:var(--ink,#EDEDE8);overflow-wrap:break-word;text-wrap:balance;outline:none}
#aboutOv .rt49-ttl em{font-style:italic;color:var(--r49g)}
#aboutOv .rt49-lede{font-family:var(--sf);font-size:16.5px;line-height:1.55;color:var(--t2,#A8ADB6);margin:0 0 16px;max-width:56ch}
#aboutOv .rt49-stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:0 0 16px}
#aboutOv .rt49-stats div{border:1px solid var(--rule,rgba(237,237,232,.14));border-radius:12px;padding:10px 10px 9px;background:var(--paper-2,#1B1D23);min-width:0}
#aboutOv .rt49-stats b{display:block;font-family:var(--sf);font-size:16px;font-weight:600;color:var(--ink,#EDEDE8);line-height:1.2}
#aboutOv .rt49-stats span{display:block;font-size:11.5px;line-height:1.3;color:var(--t3,#787E88);margin-top:3px}
#aboutOv .rt49-acct-in{display:flex;flex-wrap:wrap;align-items:center;gap:10px}
#aboutOv .rt49-acct-acts{display:flex;flex-wrap:wrap;gap:8px}
#aboutOv .rt49-acct-wait{min-height:44px}
#aboutOv .rt49-badge{display:inline-flex;align-items:center;min-height:30px;padding:5px 11px;border-radius:999px;border:1px solid var(--rule,rgba(237,237,232,.14));font-family:var(--mn);font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--t2,#A8ADB6)}
#aboutOv .rt49-badge-gd{border-color:rgba(217,174,82,.5);background:rgba(217,174,82,.12);color:var(--r49g)}
#aboutOv .rt49-btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:44px;padding:10px 16px;border-radius:10px;font-family:var(--sn);font-size:14px;font-weight:600;line-height:1.2;text-decoration:none;cursor:pointer;border:1px solid var(--rule,rgba(237,237,232,.18));background:transparent;color:var(--ink,#EDEDE8);transition:background .15s,border-color .15s,transform .15s}
#aboutOv .rt49-btn:hover{border-color:var(--r49g)}
#aboutOv .rt49-btn-gd{background:var(--r49g);border-color:var(--r49g);color:#14151A}
#aboutOv .rt49-btn-gd:hover{filter:brightness(1.07)}
#aboutOv .rt49-btn-wide{width:100%;margin-top:auto}
#aboutOv .rt49-btn-li svg{width:16px;height:16px;color:#0A66C2}
#aboutOv .rt49-sec{padding:22px 0;border-bottom:1px solid var(--rule,rgba(237,237,232,.14))}
#aboutOv .rt49-h{font-family:var(--mn);font-size:11px;font-weight:500;letter-spacing:.2em;text-transform:uppercase;color:var(--t3,#787E88);margin:0 0 14px}
#aboutOv .rt49-cov{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:1fr;gap:8px}
#aboutOv .rt49-cov li{display:flex;flex-direction:column;gap:2px;padding:11px 13px;border:1px solid var(--rule,rgba(237,237,232,.14));border-left:3px solid var(--r49g);border-radius:10px;background:var(--paper-2,#1B1D23);min-width:0}
#aboutOv .rt49-cov b{font-family:var(--sf);font-size:16px;font-weight:600;color:var(--ink,#EDEDE8)}
#aboutOv .rt49-cov span{font-size:13.5px;line-height:1.45;color:var(--t2,#A8ADB6)}
#aboutOv .rt49-plans{display:grid;grid-template-columns:1fr;gap:12px}
#aboutOv .rt49-plan{position:relative;display:flex;flex-direction:column;gap:12px;padding:18px 16px 16px;border:1px solid var(--rule,rgba(237,237,232,.14));border-radius:14px;background:var(--paper-2,#1B1D23);min-width:0}
#aboutOv .rt49-plan-pr{border-color:rgba(217,174,82,.6);background:linear-gradient(160deg,rgba(217,174,82,.16),rgba(217,174,82,.03) 55%),var(--paper-2,#1B1D23);box-shadow:0 10px 30px rgba(217,174,82,.08)}
#aboutOv .rt49-plan-rib{position:absolute;top:-10px;right:14px;padding:3px 10px;border-radius:999px;background:var(--r49g);color:#14151A;font-family:var(--mn);font-size:10px;font-weight:600;letter-spacing:.14em;text-transform:uppercase}
#aboutOv .rt49-plan-hd{display:flex;align-items:baseline;justify-content:space-between;gap:10px}
#aboutOv .rt49-plan-n{font-family:var(--sf);font-size:21px;font-weight:600;color:var(--ink,#EDEDE8)}
#aboutOv .rt49-plan-p{font-family:var(--sf);font-size:24px;font-weight:600;color:var(--ink,#EDEDE8);white-space:nowrap}
#aboutOv .rt49-plan-pr .rt49-plan-p{color:var(--r49g)}
#aboutOv .rt49-plan-p small{font-family:var(--sn);font-size:13px;font-weight:500;color:var(--t2,#A8ADB6)}
#aboutOv .rt49-ul{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:7px}
#aboutOv .rt49-ul li{display:flex;gap:9px;align-items:flex-start;font-size:14px;line-height:1.45;color:var(--t2,#A8ADB6)}
#aboutOv .rt49-ul svg{flex:0 0 16px;width:16px;height:16px;margin-top:2px;color:var(--r49g)}
#aboutOv .rt49-plan-mine{display:flex;align-items:center;justify-content:center;min-height:44px;margin-top:auto;border-radius:10px;border:1px dashed rgba(217,174,82,.55);font-family:var(--mn);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--r49g);text-align:center;padding:6px 10px}
#aboutOv .rt49-more{display:inline-flex;align-items:center;gap:6px;min-height:44px;margin-top:6px;font-size:14px;font-weight:600;color:var(--r49g);text-decoration:none}
#aboutOv .rt49-more:hover{text-decoration:underline}
#aboutOv .rt49-founder{display:flex;gap:16px;align-items:flex-start;padding:16px;border:1px solid var(--rule,rgba(237,237,232,.14));border-radius:14px;background:var(--paper-2,#1B1D23)}
#aboutOv .rt49-ph{position:relative;flex:0 0 88px;width:88px;height:88px;border-radius:50%;padding:3px;background:linear-gradient(140deg,var(--r49g),rgba(217,174,82,.25));overflow:hidden}
#aboutOv .rt49-ph img{display:block;width:100%;height:100%;object-fit:cover;border-radius:50%;background:var(--paper,#14151A)}
#aboutOv .rt49-ph img[hidden]{display:none}
#aboutOv .rt49-mono{display:none;width:100%;height:100%;border-radius:50%;align-items:center;justify-content:center;background:var(--paper,#14151A);font-family:var(--sf);font-style:italic;font-size:30px;font-weight:600;color:var(--r49g);letter-spacing:-.02em}
#aboutOv .rt49-ph.rt49-nophoto .rt49-mono{display:flex}
#aboutOv .rt49-fd{flex:1 1 auto;min-width:0}
#aboutOv .rt49-name{font-family:var(--sf);font-size:22px;font-weight:600;line-height:1.15;color:var(--ink,#EDEDE8)}
#aboutOv .rt49-role{font-family:var(--mn);font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--r49g);margin:4px 0 10px}
#aboutOv .rt49-bio{font-size:14.5px;line-height:1.55;color:var(--t2,#A8ADB6);margin:0 0 14px}
#aboutOv .rt49-src{list-style:none;margin:0;padding:0;border:1px solid var(--rule,rgba(237,237,232,.14));border-radius:12px;overflow:hidden}
#aboutOv .rt49-src li{display:grid;grid-template-columns:minmax(0,1fr);gap:2px;padding:10px 13px;border-top:1px solid var(--rule,rgba(237,237,232,.14));font-size:13.5px;line-height:1.45;color:var(--t2,#A8ADB6)}
#aboutOv .rt49-src li:first-child{border-top:0}
#aboutOv .rt49-src b{font-family:var(--mn);font-size:11px;font-weight:500;letter-spacing:.12em;text-transform:uppercase;color:var(--ink,#EDEDE8)}
#aboutOv .rt49-note{font-size:13px;line-height:1.5;color:var(--t3,#787E88);margin:12px 0 0}
#aboutOv .rt49-disc{margin:18px 0 0;border:1px solid var(--rule,rgba(237,237,232,.14));border-radius:12px;background:var(--paper-2,#1B1D23)}
#aboutOv .rt49-disc summary{display:flex;align-items:center;justify-content:space-between;gap:10px;min-height:48px;padding:10px 14px;cursor:pointer;list-style:none;font-family:var(--mn);font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--ink,#EDEDE8)}
#aboutOv .rt49-disc summary::-webkit-details-marker{display:none}
#aboutOv .rt49-disc summary::after{content:'+';font-family:var(--sn);font-size:20px;letter-spacing:0;color:var(--r49g);line-height:1}
#aboutOv .rt49-disc[open] summary::after{content:'−'}
#aboutOv .rt49-disc-s{flex:1;text-align:right;font-family:var(--sn);font-size:12.5px;letter-spacing:0;text-transform:none;color:var(--t3,#787E88)}
#aboutOv .rt49-disc p{margin:0;padding:0 14px 14px;font-size:13.5px;line-height:1.55;color:var(--t2,#A8ADB6)}
#aboutOv .rt49-disc a,#aboutOv .rt49-links a{color:var(--r49g)}
#aboutOv .rt49-ft{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;padding:18px 0 4px}
#aboutOv .rt49-links{display:flex;flex-wrap:wrap;gap:4px 16px}
#aboutOv .rt49-links a{display:inline-flex;align-items:center;min-height:44px;font-size:14px;text-decoration:none}
#aboutOv .rt49-links a:hover{text-decoration:underline}
#aboutOv .rt49-done{min-width:120px}
@media (max-width:379px){#aboutOv .rt49-body{padding-left:16px;padding-right:16px}#aboutOv .rt49-hd{padding-left:16px}#aboutOv .rt49-stats{gap:6px}#aboutOv .rt49-stats div{padding:9px 8px}#aboutOv .rt49-stats b{font-size:14.5px}#aboutOv .rt49-founder{flex-direction:column;gap:12px}#aboutOv .rt49-done{width:100%}}
@media (min-width:560px){#aboutOv .rt49-cov{grid-template-columns:1fr 1fr}#aboutOv .rt49-plans{grid-template-columns:1fr 1fr}#aboutOv .rt49-src li{grid-template-columns:150px minmax(0,1fr);gap:12px;align-items:baseline}}
@media (min-width:720px){#aboutOv.rt49-ov{align-items:center;padding:32px 24px}#aboutOv .rt49-sheet{width:min(720px,100%);max-height:min(900px,calc(100vh - 64px));border-bottom:1px solid var(--rule,rgba(237,237,232,.14));border-radius:18px;box-shadow:0 30px 90px rgba(0,0,0,.55)}#aboutOv .rt49-grab{display:none}#aboutOv .rt49-hd{padding:12px 12px 12px 28px}#aboutOv .rt49-body{padding:0 28px 26px}#aboutOv .rt49-hero{padding-top:28px}}
@media (prefers-reduced-motion:reduce){#aboutOv .rt49-btn,#aboutOv .rt49-x{transition:none}}
`; document.head.appendChild(st); } catch (e) {}
'''
s = s.rstrip('\n') + '\n' + BLOCK
h = h.replace('app.js?v=%s"' % base, 'app.js?v=%s"' % nxt)
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
JB = base64.b64decode('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')
if hashlib.sha256(JB).hexdigest() != '1f881f1f34d3383351a76d7d063690e449737e9498b18a0779143ab8f74afafd': die('embedded founder.jpg corrupt')
have = os.path.exists(JPG)
print('OK rt49about: block appended + index %s->%s; node --check passed; founder.jpg %s' % (base, nxt, 'kept (already present)' if have else 'will be written (%d bytes)' % len(JB)) + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    if not have: open(JPG, 'wb').write(JB)
    print('written', APP, IDX, '' if have else JPG)
