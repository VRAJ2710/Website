#!/usr/bin/env python3
"""
patch_rt13.py — The Dispatch Markets: rt13 (chat12 -> chat13). CLIENT ONLY (server.js untouched).

Usage (from the Replit workspace root, next to app.js and index.html):
    python3 patch_rt13.py --check          # dry run: verify every anchor (+ node --check if available), write nothing
    python3 patch_rt13.py                  # apply app.js + index.html
    python3 patch_rt13.py --dir PATH       # files live elsewhere

What it changes:
  1. Desktop (IS_DESKTOP, width >= 768) /markets/: every table row joins the browser's Yahoo stream (existing
     150-symbol cap; on-screen + tape first), not only on-screen rows. Phone unchanged (on-screen only).
     Painter: offscreen table rows are not touched (repainted when they scroll into view), row meta is only
     rewritten when it changed, and price flashes are batched (one reflow per paint instead of one per cell);
     the legacy 10s _flashChanged pass is batched the same way (it became a >100ms task with every row live).
  2. A stream label (LIVE·YS / LIVE·CB / LIVE·KR) and the LIVE count need a tick in the last 30s; otherwise the
     row shows its delayed label at once (latest price kept; a Yahoo poll at least as new takes over).
  3. Gold: tape badge "P" (Proxy reference price) for proxy quotes such as XAU.
  Yahoo's stream honours only 100 symbols per connection (measured), so symbols 101..150 ride a second Yahoo
  socket (desktop /markets/ only); symbols the stream never sends (futures, ^GSPC, ^DJI) and shut markets are
  not subscribed (they stay on the existing poll).
Applies only on top of the live chat12 files (rt12 layer present). Every edit is an exact-string replacement
that must match exactly once; if any anchor fails, nothing is written. Refuses to run twice (rt13 marker /
chat13). CRLF safe. Writes go to *.rt13.tmp first and are renamed into place only after every check passed.
No new endpoint, no new server request, no server background work: the extra symbols ride the browser's own
existing Yahoo WebSocket.
"""
import argparse, os, shutil, subprocess, sys, tempfile

MARKER = "REALTIME PRICE LAYER (rt13)"
PREV_MARKER = "REALTIME PRICE LAYER (rt12)"

APP_EDITS = [
    ("module header rt12 -> rt13",
     r'''// REALTIME PRICE LAYER (rt12) — browser-direct, free, keyless.''',
     r'''// REALTIME PRICE LAYER (rt13) — browser-direct, free, keyless.'''),
    ("module notes",
     r'''// socket connects; summary card + status chip tick; closed-market stocks keep the newer quote.
''',
     r'''// socket connects; summary card + status chip tick; closed-market stocks keep the newer quote.
// rt13: desktop /markets/ streams every table row (cap 150) with offscreen rows painted on scroll-in;
// a stream label / LIVE count needs a tick in the last 30s; batched flashes; proxy tape badge "P".
'''),
    ("RT_LIVE_MS constant",
     r'''const RT_CHG_HOLD_MS = 3000;''',
     r'''const RT_LIVE_MS = 30_000;     // a stream label (LIVE·YS/CB/KR) needs a tick at least this recent
const RT_CHG_HOLD_MS = 3000;'''),
    ("_rt state",
     r'''  holdUntil: {}, heldPrev: {}, lastSt: {}, recountAt: 0, recountT: 0, lazyT: 0, cgSwrT: 0,''',
     r'''  holdUntil: {}, heldPrev: {}, lastSt: {}, recountAt: 0, recountT: 0, lazyT: 0, cgSwrT: 0,
  warm: new Set(), fresh: new Set(), freshChg: false, offDirty: new Set(), flashQ: [],'''),
    ("_rtTickFresh helper",
     r'''function _rtLagMs(tk) { return _rt.lag[tk] || 0; }''',
     r'''function _rtLagMs(tk) { return _rt.lag[tk] || 0; }
/** A stream label is only honest while ticks keep arriving. */
function _rtTickFresh(tk) { try { return Date.now() - (_rt.lastRecv[tk] || 0) <= RT_LIVE_MS; } catch (e) { return true; } }'''),
    ("_rtApply: track fresh stream tickers",
     r'''  _rt.lag[tk] = Math.max(0, now - ts);''',
     r'''  _rt.lag[tk] = Math.max(0, now - ts);
  if (!_rt.fresh.has(tk)) { _rt.fresh.add(tk); _rt.freshChg = true; }'''),
    ("_rtGuard: Yahoo poll may take over a silent stream",
     r'''  if (RT_SRC.has(liveQuoteSrc[tk]) && now - (_rt.lastRecv[tk] || 0) <= RT_HOLD_MS) return adoptPrev();''',
     r'''  if (RT_SRC.has(liveQuoteSrc[tk]) && now - (_rt.lastRecv[tk] || 0) <= RT_HOLD_MS) {
    // rt13: no tick for RT_LIVE_MS -> a Yahoo poll at least as new as the last streamed print takes over (own label).
    const qr = Number(q.ts ?? q.fetchedAt), qTs = qr > 0 && qr < 10_000_000_000 ? qr * 1000 : qr;
    if (!(liveQuoteSrc[tk] === "yahoo-stream" && src === "yahoo" && now - (_rt.lastRecv[tk] || 0) > RT_LIVE_MS
      && qTs > 0 && qTs >= Number(liveQuoteTs[tk] || 0))) return adoptPrev();
  }'''),
    ("_rtCoinView: live dot needs a recent tick",
     r'''out.live = now - (_rt.lastRecv[tk] || 0) <= RT_HOLD_MS;''',
     r'''out.live = now - (_rt.lastRecv[tk] || 0) <= RT_LIVE_MS;'''),
    ("_rtWanted: Yahoo keys ys + ys2",
     r'''  if (key === "ys" ? !RT_USE.yahoo : !RT_USE.crypto) return out;
  if (key === "ys") {''',
     r'''  const isYs = key === "ys" || key === "ys2";
  if (isYs ? !RT_USE.yahoo : !RT_USE.crypto) return out;
  if (isYs) {'''),
    ("_rtWanted: skip symbols Yahoo does not stream / shut markets",
     r'''      if (!yh || !rev[yh]) continue;
      if (_rtIsUsEquitySym(yh) && !usOpen) continue; // nothing to stream outside the regular session''',
     r'''      if (!yh || !rev[yh] || _rtYsSkip(tk, yh)) continue;
      if (_rtIsUsEquitySym(yh) && !usOpen) continue; // nothing to stream outside the regular session'''),
    ("_rtWanted: desktop /markets/ warm rows",
     r'''      out.add(yh);
      if (out.size >= cap) break;
    }
    return out;''',
     r'''      out.add(yh);
      if (out.size >= cap) break;
    }
    // rt13: desktop /markets/ — the rest of the table joins, up to the cap.
    if (out.size < cap) for (const tk of _rt.warm) {
      const yh = YAHOO_SYMBOLS[tk];
      if (!yh || !rev[yh] || out.has(yh) || _rtYsSkip(tk, yh)) continue;
      if (_rtIsUsEquitySym(yh) && !usOpen) continue;
      out.add(yh);
      if (out.size >= cap) break;
    }
    // Yahoo honours only the first 100 symbols per connection (measured): symbols 101..cap ride a second socket.
    const all = [...out];
    return new Set(key === "ys" ? all.slice(0, RT_YS_PER_SOCK) : all.slice(RT_YS_PER_SOCK));'''),
    ("_rtScan: offscreen rows repaint on scroll-in",
     r'''  _rt.visible = vis;''',
     r'''  _rt.visible = vis;
  if (_rt.offDirty.size) for (const tk of _rt.offDirty) if (vis.has(tk)) { _rt.offDirty.delete(tk); _rt.dirty.add(tk); }'''),
    ("_rtScan: warm set",
     r'''  _rt.want = want;
}''',
     r'''  _rt.want = want;
  // rt13: desktop /markets/ keeps every table row streaming (phone stays on-screen only).
  const warm = new Set();
  if (IS_DESKTOP() && pg === "mkt") document.querySelectorAll("td[data-fl]").forEach(el => { const tk = el.dataset.fl; if (tk && !want.has(tk)) warm.add(tk); });
  _rt.warm = warm;
  if (!warm.size && _rt.offDirty.size) { _rt.offDirty.forEach(tk => _rt.dirty.add(tk)); _rt.offDirty.clear(); }
}'''),
    ("_rtFlash: batched",
     r'''  el.classList.remove("rt-up", "rt-dn"); void el.offsetWidth; el.classList.add(d > 0 ? "rt-up" : "rt-dn");''',
     r'''  _rt.flashQ.push([el, d > 0 ? "rt-up" : "rt-dn"]); // applied once per paint (one reflow, not one per cell)'''),
    ("_rtTapeBadge: proxy P",
     r'''    : d.status === "extended" ? '<span class="tape-badge tape-del" title="Extended-hours print (delayed)">D</span>'
    : '<span style="opacity:0.35;font-size:7px">○</span>';''',
     r'''    : d.status === "extended" ? '<span class="tape-badge tape-del" title="Extended-hours print (delayed)">D</span>'
    : d.status === "proxy" ? '<span class="tape-badge tape-cache" title="Proxy reference price">P</span>'
    : '<span style="opacity:0.35;font-size:7px">○</span>';'''),
    ("_rtPaint: stream labels age out",
     r'''function _rtPaint() {
  if (!_rt.dirty.size || document.hidden) return;''',
     r'''function _rtPaint() {
  if (document.hidden) return;
  // rt13: a ticker whose stream went quiet for RT_LIVE_MS drops its LIVE label now (repaint + recount).
  if (_rt.fresh.size) { const now = Date.now(); for (const tk of _rt.fresh) if (now - (_rt.lastRecv[tk] || 0) > RT_LIVE_MS) { _rt.fresh.delete(tk); _rt.dirty.add(tk); _rt.freshChg = true; } }
  if (_rt.freshChg) { _rt.freshChg = false; _rtRecountSoon(); }
  if (!_rt.dirty.size) return;'''),
    ("_rtPaint: skip offscreen table rows",
     r'''    if (!tk || !dirty.has(tk) || !hasSyncedQuote(tk)) return;
    const { d, ch, col, sign } = get(tk);''',
     r'''    if (!tk || !dirty.has(tk) || !hasSyncedQuote(tk)) return;
    if (_rt.warm.size && el.tagName === "TD" && !_rt.visible.has(tk)) { _rt.offDirty.add(tk); return; } // painted on scroll-in
    const { d, ch, col, sign } = get(tk);'''),
    ("_rtPaint: row meta only when changed",
     r'''      if (meta) meta.innerHTML = `${stat(tk)} ${asOfTag(tk)}`;''',
     r'''      if (meta) { const mh = `${stat(tk)} ${asOfTag(tk)}`; if (meta._rtH !== mh) { meta.innerHTML = mh; meta._rtH = mh; } }'''),
    ("_rtPaint: apply batched flashes",
     r'''  _rt.stats.paints++; _rt.stats.cells += n;''',
     r'''  if (_rt.flashQ.length) {
    const q = _rt.flashQ; _rt.flashQ = [];
    q.forEach(([el]) => el.classList.remove("rt-up", "rt-dn"));
    void document.body.offsetWidth;
    q.forEach(([el, c]) => el.classList.add(c));
  }
  _rt.stats.paints++; _rt.stats.cells += n;'''),
    ("_quoteMeta: stream label needs a recent tick",
     r'''  const staleAfterMs = src === "twelve-data" ? TWELVE_DATA_CACHE_WINDOW_MS''',
     r'''  // rt13: LIVE·YS / LIVE·CB / LIVE·KR only while ticks arrive (last 30s); otherwise the delayed label, same price.
  if (status === "live" && (src === "yahoo-stream" || src === "coinbase-ws" || src === "kraken-ws") && typeof _rtTickFresh === "function" && !_rtTickFresh(tk)) {
    status = "delayed";
    label = src === "yahoo-stream" ? (ts ? `DELAYED ${Math.max(1, Math.round((Date.now() - ts) / 60_000))}m` : "LAST PRINT") : src === "coinbase-ws" ? "DELAYED·CB" : "DELAYED·KR";
    detail = `${src === "yahoo-stream" ? "Yahoo Finance public stream" : src === "coinbase-ws" ? "Coinbase Exchange stream" : "Kraken stream"} · no tick in the last 30s (last print ${ts ? _fmtAge(ts) : "—"} ago) — shown as delayed until ticks resume or the next poll`;
  }
  const staleAfterMs = src === "twelve-data" ? TWELVE_DATA_CACHE_WINDOW_MS'''),
    ("initial tape render: proxy P",
     r'''      :d.status==="closed"?'<span class="tape-badge tape-cache" title="Provider reports market closed">CLOSED</span>'
      :'<span style="opacity:0.35;font-size:7px">○</span>';''',
     r'''      :d.status==="closed"?'<span class="tape-badge tape-cache" title="Provider reports market closed">CLOSED</span>'
      :d.status==="proxy"?'<span class="tape-badge tape-cache" title="Proxy reference price">P</span>'
      :'<span style="opacity:0.35;font-size:7px">○</span>';'''),
    ("Yahoo per-socket limit + no-stream list",
     r'''const RT_YS_CAP_DESK = 150, RT_YS_CAP_PHONE = 40;''',
     r'''const RT_YS_CAP_DESK = 150, RT_YS_CAP_PHONE = 40;
const RT_YS_PER_SOCK = 100;    // Yahoo's stream ignores symbols past the first 100 on one connection (measured)
const RT_YS_NOSTREAM = /=F$|^\^(GSPC|DJI)$/; // measured: the stream sends nothing for futures, S&P 500, Dow (poll covers them)
function _rtYsSkip(tk, yh) {
  if (RT_YS_NOSTREAM.test(yh)) return true;
  const ts = liveQuoteTs[tk];
  return !!ts && Date.now() - ts > 30 * 60_000; // last print >30 min old: that market is shut, nothing to stream
}'''),
    ("_rt.subd ys2",
     r'''subd: { cb: new Set(), kr: new Set(), ys: new Set() },''',
     r'''subd: { cb: new Set(), kr: new Set(), ys: new Set(), ys2: new Set() },'''),
    ("stats connects ys2",
     r'''    connects: { cb: 0, kr: 0, ys: 0 }, closes: 0,''',
     r'''    connects: { cb: 0, kr: 0, ys: 0, ys2: 0 }, closes: 0,'''),
    ("_rtStats subscribed ys2",
     r'''subscribed: { cb: [..._rt.subd.cb], kr: [..._rt.subd.kr], ys: [..._rt.subd.ys] },''',
     r'''subscribed: { cb: [..._rt.subd.cb], kr: [..._rt.subd.kr], ys: [..._rt.subd.ys], ys2: [..._rt.subd.ys2] },'''),
    ("onmessage: ys2 is not a crypto provider",
     r'''if (key !== "ys") _rt.provFails = 0;''',
     r'''if (key !== "ys" && key !== "ys2") _rt.provFails = 0;'''),
    ("onclose: ys2 is not a crypto provider",
     r'''if (key !== "ys" && !_rt.gotData[key] && ++_rt.provFails >= 3)''',
     r'''if (key !== "ys" && key !== "ys2" && !_rt.gotData[key] && ++_rt.provFails >= 3)'''),
    ("_rtSyncAll: ys2",
     r'''  [cryptoKey, "ys"].forEach(key => {''',
     r'''  [cryptoKey, "ys", "ys2"].forEach(key => {'''),
    ("_rtSyncAll: ys2 watchdog like ys",
     r'''    const limit = key === "ys" ? (_rtWeekend() ? Infinity : 120_000) : 45_000;''',
     r'''    const limit = key === "ys" || key === "ys2" ? (_rtWeekend() ? Infinity : 120_000) : 45_000;'''),
    ("_rtPause: ys2",
     r'''  ["cb", "kr", "ys"].forEach(_rtClose);''',
     r'''  ["cb", "kr", "ys", "ys2"].forEach(_rtClose);'''),
    ("_flashChanged: batched (one reflow)",
     r'''function _flashChanged(){
  Object.keys(P).forEach(tk=>{''',
     r'''function _flashChanged(){
  const q=[];
  Object.keys(P).forEach(tk=>{'''),
    ("_flashChanged: apply flashes once",
     r'''        el.classList.remove('fl-up','fl-dn');
        void el.offsetWidth;
        el.classList.add(up?'fl-up':'fl-dn');
        el.classList.remove('roll-up','roll-dn');
        void el.offsetWidth;
        el.classList.add(up?'roll-up':'roll-dn');
      });
    }
    _prevP[tk]=cur;
  });
}''',
     r'''        q.push([el,up]);
      });
    }
    _prevP[tk]=cur;
  });
  // rt13: one reflow for all flashes (was two forced reflows per cell: a long task once every row streams)
  if(q.length){q.forEach(([el])=>el.classList.remove('fl-up','fl-dn','roll-up','roll-dn'));void document.body.offsetWidth;q.forEach(([el,up])=>el.classList.add(up?'fl-up':'fl-dn',up?'roll-up':'roll-dn'));}
}'''),
]

INDEX_EDITS = [
    ("cache-bust app.js chat12 -> chat13",
     '/app.js?v=chat12"',
     '/app.js?v=chat13"'),
]

def load(path):
    with open(path, "rb") as f:
        raw = f.read().decode("utf-8")
    crlf = "\r\n" in raw
    return raw.replace("\r\n", "\n"), crlf


def apply(text, edits, label, errors):
    for e in edits:
        name, old, new = e[0], e[1], e[2]
        want = e[3] if len(e) > 3 else 1
        n = text.count(old)
        if n != want:
            errors.append(f"{label}: '{name}' anchor matched {n} times (need exactly {want})")
            continue
        text = text.replace(old, new)
    return text


def node_check(js_text, label, errors, required):
    node = shutil.which("node")
    if not node:
        if required:
            errors.append(f"{label}: node not found on PATH for `node --check` (use --skip-node-check to override)")
        else:
            print(f"WARN: node not found; {label} not syntax-checked")
        return
    fd, tmp = tempfile.mkstemp(suffix=".js")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(js_text.encode("utf-8"))
        r = subprocess.run([node, "--check", tmp], capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            errors.append(f"{label}: node --check failed: {(r.stderr or r.stdout).strip()[:400]}")
    finally:
        try: os.remove(tmp)
        except OSError: pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="dry run; write nothing")
    ap.add_argument("--dir", default=".", help="folder containing app.js and index.html")
    a = ap.parse_args()
    app_p, idx_p = (os.path.join(a.dir, n) for n in ("app.js", "index.html"))
    for p in (app_p, idx_p):
        if not os.path.isfile(p):
            sys.exit(f"ABORT: {p} not found — nothing written")
    app, app_crlf = load(app_p)
    idx, idx_crlf = load(idx_p)
    if MARKER in app or 'app.js?v=chat13"' in idx:
        sys.exit("ABORT: rt13 already applied (marker / chat13 found) — refusing to run twice; nothing written")
    if PREV_MARKER not in app or 'app.js?v=chat12"' not in idx:
        sys.exit("ABORT: these are not the chat12 (rt12) files — nothing written")
    errors = []
    new_app = apply(app, APP_EDITS, "app.js", errors)
    new_idx = apply(idx, INDEX_EDITS, "index.html", errors)
    if not errors:
        if (new_app.count(MARKER) != 1 or PREV_MARKER in new_app or "function _rtTickFresh(" not in new_app
                or new_app.count("RT_LIVE_MS") < 5 or 'void el.offsetWidth; el.classList.add(d > 0 ? "rt-up" : "rt-dn")' in new_app or new_idx.count('app.js?v=chat13"') != 1):
            errors.append("post-edit sanity check failed")
        node_check(new_app, "app.js", errors, required=False)
    if errors:
        print("ABORT — no files written:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print(f"OK: {len(APP_EDITS)} app.js edits, {len(INDEX_EDITS)} index.html edit verified"
          f" (app.js {len(new_app) - len(app):+d} chars); server.js not touched")
    if a.check:
        print("--check: dry run, nothing written")
        return
    outs = [(app_p, new_app, app_crlf), (idx_p, new_idx, idx_crlf)]
    tmps = []
    try:
        for p, text, crlf in outs:
            if crlf:
                text = text.replace("\n", "\r\n")
            tmp = p + ".rt13.tmp"
            with open(tmp, "wb") as f:
                f.write(text.encode("utf-8"))
            tmps.append((tmp, p))
    except Exception as e:
        for tmp, _ in tmps:
            try: os.remove(tmp)
            except OSError: pass
        sys.exit(f"ABORT: could not stage output ({e}) — no files written")
    for tmp, p in tmps:
        os.replace(tmp, p)
    print("Written: app.js, index.html (app.js?v=chat13)")


if __name__ == "__main__":
    main()
