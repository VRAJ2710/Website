#!/usr/bin/env python3
"""Surgical pricefix10 client patch for The Dispatch production app.js + index.html.
A) _refreshHomeAfterPrices so anonymous Home repaints after quotes
B) Alias COMEX-style tickers (GC=F→XAU etc.) in quote predicates via resolveInternalTicker
C) Cache-bust pricefix9 → pricefix10
"""
from __future__ import annotations
import pathlib, re, sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
APP = ROOT / "app.js"
IDX = ROOT / "index.html"

HELPER = r'''function _refreshHomeAfterPrices(){
  if(pg!=="home")return;
  if(typeof _isPublicDocumentVisitor==="function"&&_isPublicDocumentVisitor()){
    try{
      if(typeof IS_DESKTOP==="function"&&IS_DESKTOP()&&typeof _desktopRoute==="function"){
        _desktopRoute("home");
      }else{
        const main=document.getElementById("main");
        if(main) main.innerHTML=renderPublicHome();
      }
    }catch(e){}
    return;
  }
  try{ renderMain(); }catch(e){}
}
'''

def patch_app(text: str) -> str:
    if "_refreshHomeAfterPrices" not in text:
        marker = "async function _fetchLivePrices(){"
        if marker not in text:
            raise SystemExit("marker _fetchLivePrices not found")
        text = text.replace(marker, HELPER + marker, 1)
        print("inserted _refreshHomeAfterPrices")
    else:
        print("_refreshHomeAfterPrices already present")

    old1 = 'if(pg==="home"||pg==="brief"){ try{ renderMain(); }catch(e){} }'
    new1 = 'if(pg==="home"){ try{ _refreshHomeAfterPrices(); }catch(e){} }\n  else if(pg==="brief"){ try{ renderMain(); }catch(e){} }'
    if old1 in text:
        text = text.replace(old1, new1, 1)
        print("patched mid-fetch home/brief hook")
    elif "_refreshHomeAfterPrices()" in text:
        print("mid-fetch home hook already uses _refreshHomeAfterPrices")
    else:
        print("WARNING: mid-fetch home/brief hook not found exactly")

    old2 = 'if(pg==="home"){ try{ renderMain(); }catch(e){} }'
    new2 = 'if(pg==="home"){ try{ _refreshHomeAfterPrices(); }catch(e){} }'
    count = text.count(old2)
    if count:
        text = text.replace(old2, new2)
        print(f"patched trailing home renderMain hooks: {count}")
    elif 'if(pg==="home"){ try{ _refreshHomeAfterPrices(); }catch(e){} }' in text:
        print("trailing home hook already refreshed")
    else:
        print("WARNING: trailing home hook not found")

    old_hs = '''function hasSyncedQuote(tk) {
  const p = P[tk]?.p;
  return typeof p === "number" && isFinite(p) && p > 0 && _quoteMeta(tk).status !== "unavailable";
}'''
    new_hs = '''function hasSyncedQuote(tk) {
  tk = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk;
  const p = P[tk]?.p;
  return typeof p === "number" && isFinite(p) && p > 0 && _quoteMeta(tk).status !== "unavailable";
}'''
    if "function hasSyncedQuote(tk) {\n  tk = (typeof resolveInternalTicker" in text:
        print("hasSyncedQuote already aliases")
    elif old_hs in text:
        text = text.replace(old_hs, new_hs, 1)
        print("patched hasSyncedQuote")
    else:
        print("WARNING: hasSyncedQuote not patched")

    old_hu = '''function hasUsableQuote(tk) {
  const p = P[tk]?.p;
  return liveSymbols.has(tk)
    && typeof p === "number"
    && isFinite(p)
    && p > 0
    && _quoteMeta(tk).status !== "unavailable";
}'''
    new_hu = '''function hasUsableQuote(tk) {
  tk = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk;
  const p = P[tk]?.p;
  return liveSymbols.has(tk)
    && typeof p === "number"
    && isFinite(p)
    && p > 0
    && _quoteMeta(tk).status !== "unavailable";
}'''
    if "function hasUsableQuote(tk) {\n  tk = (typeof resolveInternalTicker" in text:
        print("hasUsableQuote already aliases")
    elif old_hu in text:
        text = text.replace(old_hu, new_hu, 1)
        print("patched hasUsableQuote")
    else:
        print("WARNING: hasUsableQuote not patched exactly")

    old_qm = '''function _quoteMeta(tk) {
  if (!liveSymbols.has(tk)) {'''
    new_qm = '''function _quoteMeta(tk) {
  tk = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk;
  if (!liveSymbols.has(tk)) {'''
    if "function _quoteMeta(tk) {\n  tk = (typeof resolveInternalTicker" in text:
        print("_quoteMeta already aliases")
    elif old_qm in text:
        text = text.replace(old_qm, new_qm, 1)
        print("patched _quoteMeta")
    else:
        print("WARNING: _quoteMeta not patched")

    old_rp = '''function referencePx(tk) {
  const meta = _quoteMeta(tk);
  const p = P[tk]?.p;
  const retained = liveSymbols.has(tk)'''
    new_rp = '''function referencePx(tk) {
  tk = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk;
  const meta = _quoteMeta(tk);
  const p = P[tk]?.p;
  const retained = liveSymbols.has(tk)'''
    if "function referencePx(tk) {\n  tk = (typeof resolveInternalTicker" in text:
        print("referencePx already aliases")
    elif old_rp in text:
        text = text.replace(old_rp, new_rp, 1)
        print("patched referencePx")
    else:
        print("WARNING: referencePx not patched")

    old_fp = '''function fp(tk){
  const meta=_quoteMeta(tk);
  const d=P[tk];
  const hasPx=liveSymbols.has(tk)&&d&&typeof d.p==="number"&&isFinite(d.p)&&d.p>0;'''
    new_fp = '''function fp(tk){
  tk=(typeof resolveInternalTicker==="function"&&resolveInternalTicker(tk))||tk;
  const meta=_quoteMeta(tk);
  const d=P[tk];
  const hasPx=liveSymbols.has(tk)&&d&&typeof d.p==="number"&&isFinite(d.p)&&d.p>0;'''
    if "function fp(tk){\n  tk=(typeof resolveInternalTicker" in text:
        print("fp already aliases")
    elif old_fp in text:
        text = text.replace(old_fp, new_fp, 1)
        print("patched fp")
    else:
        print("WARNING: fp not patched")

    return text

def patch_index(text: str) -> str:
    text2, n1 = re.subn(r"app\.js\?v=pricefix9", "app.js?v=pricefix10", text)
    text2, n2 = re.subn(r"var V='TD-pricefix9'", "var V='TD-pricefix10'", text2)
    if n1 == 0:
        text2, n3 = re.subn(r"app\.js\?v=[^\"'\\s>]+", "app.js?v=pricefix10", text2)
    else:
        n3 = 0
    print(f"index replacements: pricefix9script={n1} TD-var={n2} generic={n3}")
    return text2

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
    assert "_refreshHomeAfterPrices" in t, "missing helper"
    assert "_refreshHomeAfterPrices();" in t
    assert "resolveInternalTicker" in t[t.find("function hasSyncedQuote"):t.find("function hasSyncedQuote")+280]
    assert "resolveInternalTicker" in t[t.find("function _quoteMeta"):t.find("function _quoteMeta")+200]
    assert "resolveInternalTicker" in t[t.find("function fp(tk)"):t.find("function fp(tk)")+180]
    print("VERIFY OK")

if __name__ == "__main__":
    main()
