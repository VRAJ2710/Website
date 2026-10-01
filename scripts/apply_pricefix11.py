#!/usr/bin/env python3
"""Surgical pricefix11: single synced pricing layer (hasSyncedQuote+fp) for brief/tape/front-door.
Do NOT replace isPrimaryLiveQuote itself — keep for rare near-live checks.
Cache-bust pricefix10 → pricefix11.
"""
from __future__ import annotations
import pathlib, re, sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
APP = ROOT / "app.js"
IDX = ROOT / "index.html"

NEW_LIVE_PX = '''function livePx(tk) {
  tk = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk;
  if (!hasSyncedQuote(tk)) return null;
  const p = P[tk]?.p;
  return typeof p === "number" && isFinite(p) && p > 0 ? p : null;
}'''

NEW_LIVE_CHG = '''function liveChg(tk) {
  tk = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk;
  if (!hasSyncedQuote(tk)) return null;
  if (typeof liveQuoteChangeAvailable !== "undefined" && liveQuoteChangeAvailable[tk] === false) return null;
  const c = P[tk]?.c;
  return typeof c === "number" && isFinite(c) ? c : null;
}'''

NEW_TAPE = '''function _liveTapeBit(label, ...tks) {
  // Synced layer (hasSyncedQuote) — same gate Markets uses; PROXY/DELAYED still print
  for (const tk of tks) {
    if (!hasSyncedQuote(tk)) continue;
    const d = fp(tk);
    if (d.status === "unavailable") continue;
    const c = liveChg(tk);
    const chg = c != null ? ` (${c >= 0 ? "+" : ""}${Number(c).toFixed(2)}%)` : "";
    return `${label} ${d.p}${chg}`;
  }
  return null;
}'''

NEW_REGIME = '''function _getRegimeState() {
  // Missing inputs must stay "—" — never invent flat 0% (that paints a fake green day)
  const nosync = { p: "—", c: "—", d: 0, status: "unavailable" };
  const vix = hasSyncedQuote("VIX") ? fp("VIX") : nosync;
  // Prefer live index; SPY is the ETF proxy when ^GSPC not synced this session
  let spx = nosync, spxProxy = null;
  if (hasSyncedQuote("SPX")) {
    spx = fp("SPX");
  } else if (hasSyncedQuote("SPY")) {
    spx = fp("SPY");
    spxProxy = "SPY";
  }
  let id = "risk-on-fragile", label = "Risk-On (Fragile)";
  const vv = parseFloat(vix.p);
  if (!isNaN(vv) && vix.p !== "—") {
    if (vv >= 25) { id = "risk-off"; label = "Risk-Off (Elevated Vol)"; }
    else if (vv < 16 && spx.status !== "unavailable" && spx.d > 0) { id = "risk-on-strong"; label = "Risk-On (Strong)"; }
  }
  const q = (tk) => hasSyncedQuote(tk) ? fp(tk) : nosync;
  const dxy = q("DXY"), oil = q("WTI"), gold = q("XAU"), btc = q("BTC");
  return { id, label, spx: spx.p, spxChg: spx.c, spxProxy, vix: vix.p, dxy: dxy.p, oil: oil.p, gold: gold.p, btc: btc.p };
}'''

NEW_FRONT = '''function _frontDoorQuote(tk, name, description) {
  tk = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk;
  const synced = hasSyncedQuote(tk);
  const px = synced ? (P[tk]?.p) : null;
  const meta = _quoteMeta(tk);
  const price = (typeof px === "number" && isFinite(px) && px > 0) ? fp(tk).p : "no print";
  const ch = (synced && typeof liveChg === "function") ? liveChg(tk) : null;
  const change = ch != null ? `${ch >= 0 ? "+" : ""}${Number(ch).toFixed(2)}%` : "";
  const referenceName = tk === "XAU"
    ? (liveQuoteName.XAU || "Spot Gold (proxy)")
    : tk === "DXY"
      ? (liveQuoteName.DXY || "Synthetic Dollar Index (proxy)")
      : meta.label;
  const provenance = meta.status === "unavailable"
    ? `NO SYNC · ${referenceName}`
    : `${meta.label} · ${referenceName}`;
  return `<div class="front-door-quote">
    <div class="front-door-quote-name">${_escHtml(name)} <span>${_escHtml(description)}</span></div>
    <div class="front-door-quote-value">${_escHtml(String(price))}${change ? ` <small class="${ch >= 0 ? "px-up" : "px-dn"}">${change}</small>` : ""}</div>
    <div class="front-door-quote-meta">${_escHtml(provenance)}${meta.asOf ? ` · as of ${_escHtml(_fmtAsOf(meta.asOf))}` : ""}</div>
  </div>`;
}'''

def replace_fn(text: str, name: str, new_body: str) -> str:
    """Replace a top-level function by brace-matching from its declaration."""
    m = re.search(rf'function {re.escape(name)}\([^)]*\)\s*\{{', text)
    if not m:
        raise SystemExit(f"function {name} not found")
    start = m.start()
    i = text.find('{', start)
    depth = 0
    for j in range(i, len(text)):
        if text[j] == '{': depth += 1
        elif text[j] == '}':
            depth -= 1
            if depth == 0:
                old = text[start:j+1]
                if new_body.strip() in text and name in ("livePx",) and "hasSyncedQuote" in old and "isPrimaryLiveQuote" not in old:
                    print(f"{name} already pricefix11")
                    return text
                text = text[:start] + new_body + text[j+1:]
                print(f"replaced {name} ({len(old)}→{len(new_body)} chars)")
                return text
    raise SystemExit(f"unclosed brace for {name}")

def patch_fetch_refresh(text: str) -> str:
    """After success/end home hooks, also call _refreshBriefSurfaces for brief/dash/home."""
    # Mid-success block (lines ~75-76 pattern)
    old1 = '''if(pg==="home"){ try{ _refreshHomeAfterPrices(); }catch(e){} }
  else if(pg==="brief"){ try{ renderMain(); }catch(e){} }'''
    new1 = '''if(pg==="home"){ try{ _refreshHomeAfterPrices(); }catch(e){} }
  else if(pg==="brief"){ try{ renderMain(); }catch(e){} }
  if(pg==="brief"||pg==="dash"||pg==="home"){ try{ _refreshBriefSurfaces(); }catch(e){} }'''
    if '_refreshBriefSurfaces(); }catch(e){} }\n  if(pg==="mkt"' in text or \
       'if(pg==="brief"||pg==="dash"||pg==="home"){ try{ _refreshBriefSurfaces(); }catch(e){} }' in text:
        print("brief surfaces refresh already present (skip mid)")
    elif old1 in text:
        text = text.replace(old1, new1, 1)
        print("patched mid-fetch brief/home refresh → _refreshBriefSurfaces")
    else:
        print("WARNING: mid-fetch home/brief hook pattern not found")

    # Trailing home-only hook at end of _fetchLivePrices — also brief-refresh
    old2 = 'if(pg==="home"){ try{ _refreshHomeAfterPrices(); }catch(e){} }\n}'
    # Only the LAST occurrence inside _fetchLivePrices closing — replace carefully
    # Find async function _fetchLivePrices and its closing before fetchLivePrices
    start = text.find('async function _fetchLivePrices(){')
    if start < 0:
        print("WARNING: _fetchLivePrices not found for trailing patch")
        return text
    end_marker = '\nasync function fetchLivePrices(){'
    end = text.find(end_marker, start)
    if end < 0:
        print("WARNING: fetchLivePrices marker not found")
        return text
    block = text[start:end]
    trailer = '''if(pg==="home"){ try{ _refreshHomeAfterPrices(); }catch(e){} }
  if(pg==="brief"||pg==="dash"||pg==="home"){ try{ _refreshBriefSurfaces(); }catch(e){} }
}'''
    # Replace the final home refresh + closing brace of the function
    m = re.search(
        r'if\(pg==="home"\)\{\s*try\{\s*_refreshHomeAfterPrices\(\);\s*\}\s*catch\(e\)\{\}\s*\}\s*\n\}',
        block,
    )
    if m and '_refreshBriefSurfaces' not in block[m.start():]:
        # only the last match
        matches = list(re.finditer(
            r'if\(pg==="home"\)\{\s*try\{\s*_refreshHomeAfterPrices\(\);\s*\}\s*catch\(e\)\{\}\s*\}\s*\n\}',
            block,
        ))
        if matches:
            last = matches[-1]
            block2 = block[:last.start()] + trailer + block[last.end():]
            text = text[:start] + block2 + text[end:]
            print("patched trailing _fetchLivePrices end → _refreshBriefSurfaces")
        else:
            print("WARNING: trailing home hook regex no match")
    elif '_refreshBriefSurfaces' in block:
        print("trailing brief refresh already in _fetchLivePrices")
    else:
        print("WARNING: trailing home hook not patched")
    return text

def patch_index(text: str) -> str:
    text2, n1 = re.subn(r"app\.js\?v=pricefix10", "app.js?v=pricefix11", text)
    text2, n2 = re.subn(r"var V='TD-pricefix10'", "var V='TD-pricefix11'", text2)
    if n1 == 0:
        text2, n3 = re.subn(r"app\.js\?v=[^\"'\\s>]+", "app.js?v=pricefix11", text2)
    else:
        n3 = 0
    print(f"index replacements: pricefix10script={n1} TD-var={n2} generic={n3}")
    return text2

def patch_app(text: str) -> str:
    if "pricefix11" in text and "hasSyncedQuote(tk)" in text[text.find("function livePx"):text.find("function livePx")+200]:
        # still apply other patches if needed
        print("livePx already looks synced; continuing idempotent patches")
    text = replace_fn(text, "livePx", NEW_LIVE_PX)
    text = replace_fn(text, "liveChg", NEW_LIVE_CHG)
    text = replace_fn(text, "_liveTapeBit", NEW_TAPE)
    text = replace_fn(text, "_getRegimeState", NEW_REGIME)
    text = replace_fn(text, "_frontDoorQuote", NEW_FRONT)
    text = patch_fetch_refresh(text)
    # Keep isPrimaryLiveQuote intact
    if "function isPrimaryLiveQuote" not in text:
        raise SystemExit("isPrimaryLiveQuote missing — abort")
    return text

def main():
    if not APP.exists():
        raise SystemExit(f"missing {APP}")
    text = APP.read_text(encoding="utf-8")
    text = patch_app(text)
    APP.write_text(text, encoding="utf-8")
    print(f"wrote {APP} bytes={APP.stat().st_size}")

    if IDX.exists():
        idx = IDX.read_text(encoding="utf-8")
        IDX.write_text(patch_index(idx), encoding="utf-8")
        print(f"wrote {IDX}")
    else:
        print("WARNING: no index.html")

    t = APP.read_text(encoding="utf-8")
    # VERIFY
    lp = t[t.find("function livePx"):t.find("function livePx")+350]
    assert "hasSyncedQuote" in lp, "livePx must use hasSyncedQuote"
    assert "isPrimaryLiveQuote" not in lp, "livePx must not use isPrimaryLiveQuote"
    lc = t[t.find("function liveChg"):t.find("function liveChg")+400]
    assert "hasSyncedQuote" in lc
    tb = t[t.find("function _liveTapeBit"):t.find("function _liveTapeBit")+350]
    assert "hasSyncedQuote" in tb and "isPrimaryLiveQuote" not in tb
    rs = t[t.find("function _getRegimeState"):t.find("function _getRegimeState")+900]
    assert "hasSyncedQuote" in rs
    assert "isPrimaryLiveQuote" not in rs
    fd = t[t.find("function _frontDoorQuote"):t.find("function _frontDoorQuote")+500]
    assert "hasSyncedQuote" in fd
    assert "function isPrimaryLiveQuote" in t
    assert "_refreshBriefSurfaces" in t[t.find("async function _fetchLivePrices"):t.find("async function fetchLivePrices")]
    if IDX.exists():
        idx = IDX.read_text(encoding="utf-8")
        assert "pricefix11" in idx
        assert "pricefix10" not in idx or "pricefix10" not in idx.replace("pricefix11","")
    print("VERIFY OK")
    print("APPLY_EXIT:0")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"APPLY_EXIT:1 ERROR:{e}")
        raise
