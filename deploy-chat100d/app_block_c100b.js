
// ── chat100b ──
// About (app view): founder card shows the photo the server publishes (window.C100B_FOUNDER, set from the one
// constant in server.js), "Edited by Vraj Patel, London" and the LinkedIn link. No monogram or broken image: with no
// photo the slot is simply left out.
function _c100bFounder() {
  var f = (typeof window !== 'undefined' && window.C100B_FOUNDER) || {};
  return { photo: typeof f.photo === 'string' ? f.photo : '/assets/founder.webp', li: f.li || 'https://www.linkedin.com/in/vraj2710', liLabel: f.liLabel || 'Vraj Patel on LinkedIn' };
}
(function () {
  var h0 = _rt49Html;
  _rt49Html = function () {
    var h = h0.apply(this, arguments), F = _c100bFounder();
    try {
      h = h.replace('<h3 class="rt49-h">Founder &amp; analyst</h3>', '<h3 class="rt49-h">Founder and editor</h3>');
      h = h.replace('alt="Vraj Patel, founder of The Dispatch Market"', 'alt="Vraj Patel"');
      h = h.replace('<div class="rt49-role">Founder · Analyst</div>', '<div class="rt49-role">Founder · Editor</div><div class="rt49-by">Edited by Vraj Patel, London</div>');
      h = h.replace(/<a class="rt49-btn rt49-btn-li" href="[^"]*" target="_blank" rel="noopener">([\s\S]*?<\/svg>)Connect on LinkedIn/, function (m, svg) { return '<a class="rt49-btn rt49-btn-li" href="' + _rt49Esc(F.li) + '" target="_blank" rel="noopener noreferrer">' + svg + _rt49Esc(F.liLabel); });
      h = h.replace('</svg>Connect on LinkedIn', '</svg>' + _rt49Esc(F.liLabel));
    } catch (e) {}
    return h;
  };
  _rt49Photo = function (ov) {
    var box = ov.querySelector('.rt49-ph'), img = box && box.querySelector('img'), src = _c100bFounder().photo; if (!img) return;
    var ok = function () { if (img.naturalWidth > 0) { img.hidden = false; box.classList.remove('rt49-nophoto'); } else bad(); };
    var bad = function () { img.hidden = true; box.classList.add('rt49-nophoto'); };
    if (!src) return bad();
    if (img.getAttribute('src') === src) { if (img.complete) ok(); return; }
    img.addEventListener('load', ok, { once: true }); img.addEventListener('error', bad, { once: true }); img.src = src;
  };
  try {
    var st = document.createElement('style'); st.id = 'c100b-about';
    st.textContent = '#aboutOv .rt49-by{font-family:var(--sn,system-ui);font-size:14px;font-weight:600;color:var(--ink,#EDEDE8);margin:-4px 0 10px}' +
      '#aboutOv .rt49-ph{flex-basis:104px;width:104px;height:104px}' +
      '@media (max-width:379px){#aboutOv .rt49-ph{flex-basis:96px;width:96px;height:96px}}' +
      '.c100-tile .c100-src:not(:last-child){display:-webkit-box;-webkit-line-clamp:3;line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}';  // long gold sources: 3 lines on the tile, full text in the inspector
    (document.head || document.documentElement).appendChild(st);
  } catch (e) {}
})();
