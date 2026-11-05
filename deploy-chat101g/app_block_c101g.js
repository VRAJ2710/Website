
// ── chat101g: phone Account drawer (full height, readable, close X, backdrop, Esc, scroll lock) + tap-through fixes ──
(() => { try {
  const st = document.createElement("style"); st.id = "c101g-css";
  st.textContent =
    "@media (max-width:767px){.hdr .hdr-auth.has-acct .acct-menu-btn{font:600 13px/1 var(--ui,var(--sn))!important;padding:0 12px!important;min-width:44px!important;min-height:44px!important;color:var(--ink,#1b1b1b)!important;border-color:var(--rule-2,rgba(27,27,27,.28))!important;gap:6px}" +
    ".hdr .hdr-auth.has-acct .acct-menu-btn::before{content:none!important}}" +
    ".c101g-bd{position:fixed;inset:0;z-index:2990;background:rgba(0,0,0,.55);-webkit-tap-highlight-color:transparent}" +
    "#acctMenu.c101g-drawer{position:fixed;top:0!important;left:0!important;right:auto!important;bottom:0;width:85vw;max-width:360px;min-width:0;height:100vh;height:100dvh;z-index:3000;box-sizing:border-box;" +
    "margin:0;padding:0 0 24px;border:0;border-right:1px solid var(--rule-2,rgba(27,27,27,.28));border-radius:0;background:var(--paper,#fbfaf7);color:var(--ink,#1b1b1b);box-shadow:8px 0 30px rgba(0,0,0,.35);overflow-y:auto;overscroll-behavior:contain}" +
    "#acctMenu.c101g-drawer .c101g-bar{position:sticky;top:0;display:flex;align-items:center;justify-content:space-between;gap:12px;height:60px;padding:0 16px 0 20px;background:var(--paper,#fbfaf7);border-bottom:1px solid var(--rule-2,rgba(27,27,27,.28));box-sizing:border-box}" +
    "#acctMenu.c101g-drawer .c101g-title{font:600 15px/1.2 var(--ui,system-ui);color:var(--ink,#1b1b1b)}" +
    "#acctMenu.c101g-drawer .c101g-x{display:inline-flex;align-items:center;justify-content:center;width:44px;height:44px;min-height:44px;padding:0;background:var(--paper,#fbfaf7);color:var(--ink,#1b1b1b);border:1px solid var(--rule-2,rgba(27,27,27,.28));border-radius:4px;cursor:pointer}" +
    "#acctMenu.c101g-drawer .c101g-x:focus-visible,#acctMenu.c101g-drawer a:focus-visible,#acctMenu.c101g-drawer button:focus-visible{outline:2px solid var(--gold,#1f3a5f);outline-offset:2px}" +
    "#acctMenu.c101g-drawer .acct-lbl{font:600 11px/1.3 var(--ui,system-ui);letter-spacing:.08em;color:var(--ink-2,#45443f);padding:18px 20px 8px}" +
    "#acctMenu.c101g-drawer .c101g-list{padding:0 8px}" +
    "#acctMenu.c101g-drawer .c101g-list a,#acctMenu.c101g-drawer .c101g-list button{display:flex;align-items:center;width:100%;min-height:48px;padding:0 12px;box-sizing:border-box;background:none;border:0;border-bottom:1px solid var(--rule-soft,rgba(27,27,27,.07));border-radius:0;color:var(--ink,#1b1b1b)!important;font:500 15px/1.3 var(--ui,system-ui);text-decoration:none;text-align:left;cursor:pointer}" +
    "#acctMenu.c101g-drawer .c101g-list a:hover,#acctMenu.c101g-drawer .c101g-list button:hover{background:var(--paper-2,rgba(127,127,127,.08))}" +
    "html.c101g-lock,html.c101g-lock body{overflow:hidden!important}" +
    "@media (prefers-reduced-motion:no-preference){#acctMenu.c101g-drawer{animation:c101gIn .16s ease-out}@keyframes c101gIn{from{transform:translateX(-100%)}to{transform:none}}}" +
    "#ctxMenu:not(.show){display:none!important}" +
    // tap-through audit fixes: dark-only backgrounds and dimmed text that left text unreadable
    ".paper-locked .paper-lock-card{background:radial-gradient(ellipse 80% 60% at 0% 0%,var(--gold-wash,transparent),transparent 55%),var(--paper-2,#f4f2ec)!important;color:var(--ink,#1b1b1b)}" +
    ".paper-locked .paper-lock-card .paper-lock-p,.paper-locked .paper-lock-card .paper-lock-list,.paper-locked .paper-lock-card .paper-lock-sec{color:var(--ink-2,#45443f)!important}" +
    ".paper-locked .paper-lock-card .paper-lock-h{color:var(--ink,#1b1b1b)!important}.paper-locked .paper-lock-card .paper-lock-kicker{color:var(--gold,#1f3a5f)!important}" +
    ".paper-locked .paper-lock-card .paper-lock-cta{background:var(--gold,#1f3a5f)!important;color:var(--paper,#fbfaf7)!important}" +
    ".desk-letter{background:linear-gradient(165deg,var(--paper-2,#f4f2ec),var(--paper,#fbfaf7))!important}" +
    ".rt47-bd:not(.on){opacity:1!important;color:var(--ink-3,#66655f)!important;border-style:dashed!important}" +
    ".sector-tile .sector-tile-rank,.sector-tile .sector-tile-etf,.sector-tile .sector-tile-pct,.sector-tile .sector-tile-rel{color:var(--ink,#1b1b1b)!important}" +
    ".heat-tile>div{color:var(--ink,#1b1b1b)!important}.heat-tile{overflow:hidden}.heat-tile>div{overflow:hidden;text-overflow:ellipsis}" +
    "span[style*=\"background:rgba(0,200,150\"],span[style*=\"background:rgba(255,71,87\"]{color:var(--ink,#1b1b1b)!important}" +
    "small[style=\"opacity:.6\"]{opacity:1!important}" +
    "button[onclick=\"_runIntel()\"]{background:var(--gold,#1f3a5f)!important;color:var(--paper,#fbfaf7)!important}" +
    ".chat-send{background:var(--gold,#1f3a5f)!important;color:var(--paper,#fbfaf7)!important}";
  document.head.appendChild(st);
  // Label the phone button in words; the old icon looked like a second menu.
  const label = () => document.querySelectorAll(".acct-menu-btn").forEach(b => { if (b.dataset.c101g) return; b.dataset.c101g = "1"; b.textContent = "Account"; b.setAttribute("aria-haspopup", "dialog"); b.setAttribute("aria-label", "Account menu"); });
  label(); new MutationObserver(label).observe(document.documentElement, { childList: true, subtree: true });
  // Signed-in free accounts were shown "Sign in" / "Create free account" and had no way to sign out. Give them the same Account menu.
  const freeBar = () => `<span class="auth-group c101g-free"><a href="/settings/" class="auth-btn auth-btn--ghost auth-btn--compact" onclick="if(typeof openSettings==='function'){event.preventDefault();openSettings()}">Settings</a><a href="/__auth/logout" class="auth-btn auth-btn--ghost auth-btn--compact">Sign out</a></span>`;
  window._rt16AcctDecorate = function () {
    const hdr = document.getElementById("hdrAuthBtn");
    const signedIn = typeof _userSignedIn !== "undefined" && _userSignedIn === true && (typeof _userTierReady === "undefined" || _userTierReady);
    const admin = typeof _userAdmin !== "undefined" && _userAdmin === true, prem = typeof _isPremium === "function" && _isPremium();
    if (signedIn && !admin && !prem) ["hdrAuthBtn", "cmdAuthBtn"].forEach(id => { const h = document.getElementById(id); if (h && !h.querySelector(".c101g-free") && (h.querySelector('a[href="/__auth/login"]') || !h.textContent.trim())) h.innerHTML = freeBar(); });
    if (!hdr) return;
    hdr.classList.toggle("has-acct", !!signedIn);
    if (signedIn && !hdr.querySelector(".acct-menu-btn")) hdr.insertAdjacentHTML("beforeend", `<button type="button" class="acct-menu-btn" aria-haspopup="dialog" aria-expanded="false" aria-label="Account menu" data-c101g="1" onclick="_rt16AcctToggle(this)">Account</button>`);
  };
  try { window._rt16AcctDecorate(); } catch (e) {}
  // Esc closes the Ask (research assistant) panel, like its X; other open dialogs keep Esc for themselves.
  document.addEventListener("keydown", e => { try {
    if (e.key !== "Escape" || e.defaultPrevented || typeof _chatOpen === "undefined" || !_chatOpen || typeof toggleChat !== "function") return;
    const p = document.getElementById("chatPanel"); if (!p || p.classList.contains("hide")) return;
    const other = [...document.querySelectorAll('[aria-modal="true"],[role="dialog"]')].some(d => d !== p && !p.contains(d) && d.getClientRects().length && getComputedStyle(d).visibility !== "hidden");
    if (other) return;
    e.preventDefault(); toggleChat();
  } catch (x) {} });
  let lastBtn = null;
  const onKey = e => { const m = document.getElementById("acctMenu"); if (!m) return;
    if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); window._rt16AcctClose(); return; }
    if (e.key === "Tab") { const f = [...m.querySelectorAll("a[href],button:not([disabled])")]; if (!f.length) return; const a = f[0], z = f[f.length - 1];
      if (e.shiftKey && document.activeElement === a) { e.preventDefault(); z.focus(); } else if (!e.shiftKey && document.activeElement === z) { e.preventDefault(); a.focus(); } else if (!m.contains(document.activeElement)) { e.preventDefault(); a.focus(); } } };
  window._rt16AcctClose = function () {
    const had = !!document.getElementById("acctMenu");
    document.getElementById("acctMenu")?.remove(); document.querySelectorAll(".c101g-bd").forEach(x => x.remove());
    document.documentElement.classList.remove("c101g-lock");
    document.querySelectorAll(".acct-menu-btn").forEach(b => b.setAttribute("aria-expanded", "false"));
    document.removeEventListener("keydown", onKey, true);
    try { document.removeEventListener("click", _rt16AcctOutside, true); } catch (e) {}
    if (had && lastBtn && document.contains(lastBtn)) try { lastBtn.focus({ preventScroll: true }); } catch (e) {}
  };
  window._rt16AcctToggle = function (btn) {
    if (document.getElementById("acctMenu")) { window._rt16AcctClose(); return; }
    lastBtn = btn || null;
    const admin = typeof _userAdmin !== "undefined" && _userAdmin === true, prem = typeof _isPremium === "function" && _isPremium();
    const bd = document.createElement("div"); bd.className = "c101g-bd"; bd.setAttribute("aria-hidden", "true"); bd.addEventListener("click", () => window._rt16AcctClose());
    const m = document.createElement("div");
    m.id = "acctMenu"; m.className = "acct-menu c101g-drawer"; m.setAttribute("role", "dialog"); m.setAttribute("aria-modal", "true"); m.setAttribute("aria-label", "Account");
    m.innerHTML = `<div class="c101g-bar"><span class="c101g-title">Account</span><button type="button" class="c101g-x" aria-label="Close account menu"><svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false"><path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></button></div>`
      + `<div class="acct-lbl">${admin ? "ADMIN · FULL ACCESS" : prem ? "PREMIUM" : "FREE"}</div><div class="c101g-list">`
      + (admin ? `<a href="/__admin">Admin console</a><a href="/?view=guest">Guest preview</a>` : "")
      + (prem && !admin ? `<button type="button" data-act="billing">Manage billing</button>` : "")
      + `<button type="button" data-act="settings">Settings</button>`
      + `<a href="/__auth/logout">Sign out</a></div>`;
    m.querySelector(".c101g-x").addEventListener("click", () => window._rt16AcctClose());
    m.querySelectorAll("[data-act]").forEach(b => b.addEventListener("click", () => { const a = b.dataset.act; window._rt16AcctClose(); if (a === "billing" && typeof _openBillingPortal === "function") _openBillingPortal(); if (a === "settings" && typeof openSettings === "function") openSettings(); }));
    document.body.appendChild(bd); document.body.appendChild(m);
    document.documentElement.classList.add("c101g-lock");
    if (btn) btn.setAttribute("aria-expanded", "true");
    document.addEventListener("keydown", onKey, true);
    try { m.querySelector(".c101g-x").focus({ preventScroll: true }); } catch (e) {}
  };
} catch (e) {} })();
