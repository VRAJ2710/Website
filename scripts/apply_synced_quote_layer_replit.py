#!/usr/bin/env python3
"""Point Brief, regime, gold hero, and the front door at Markets' synced quotes.

Live app.js?v=pricefix10 keeps livePx / liveChg / _liveTapeBit / _getRegimeState
on isPrimaryLiveQuote (status === "live" only). That drops Yahoo DELAYED,
CACHED, and PROXY prints, so those surfaces stay on "—" / NO SYNC while
Markets already has XAU and DXY via hasSyncedQuote + fp.

Patch is in-place and idempotent. It does not replace app.js.
Cache token becomes pricefix11.
"""
from __future__ import annotations

import pathlib
import sys

EM = "\u2014"
CACHE_FROM = "pricefix10"
CACHE_TO = "pricefix11"


def fail(message: str) -> None:
    print(f"apply_synced_quote_layer_replit: {message}", file=sys.stderr)
    raise SystemExit(1)


def sub_once(src: str, old: str, new: str, label: str) -> tuple[str, bool]:
    if old == new:
        fail(f"{label} replacement is a no-op")
    if new in src:
        return src, False
    count = src.count(old)
    if count != 1:
        fail(f"{label}: expected 1 anchor, found {count}")
    return src.replace(old, new, 1), True


def patch_app(src: str) -> tuple[str, list[str]]:
    notes: list[str] = []

    def apply(old: str, new: str, label: str) -> None:
        nonlocal src
        src, changed = sub_once(src, old, new, label)
        notes.append(f"{'patched' if changed else 'already'}: {label}")

    apply(
        "  const vix = isPrimaryLiveQuote(\"VIX\") ? fp(\"VIX\") : nosync;\n"
        "  // Prefer live index; SPY is the ETF proxy when ^GSPC not synced this session\n"
        "  let spx = nosync, spxProxy = null;\n"
        "  if (isPrimaryLiveQuote(\"SPX\")) {\n"
        "    spx = fp(\"SPX\");\n"
        "  } else if (isPrimaryLiveQuote(\"SPY\")) {\n"
        "    spx = fp(\"SPY\");\n",
        "  const vix = hasSyncedQuote(\"VIX\") ? fp(\"VIX\") : nosync;\n"
        "  // Prefer synced index; SPY is the ETF proxy when ^GSPC is not synced\n"
        "  let spx = nosync, spxProxy = null;\n"
        "  if (hasSyncedQuote(\"SPX\")) {\n"
        "    spx = fp(\"SPX\");\n"
        "  } else if (hasSyncedQuote(\"SPY\")) {\n"
        "    spx = fp(\"SPY\");\n",
        "regime tape",
    )
    apply(
        "  const q = (tk) => isPrimaryLiveQuote(tk) ? fp(tk) : nosync;",
        "  const q = (tk) => hasSyncedQuote(tk) ? fp(tk) : nosync;",
        "regime quotes",
    )
    apply(
        "    if (!isPrimaryLiveQuote(tk)) continue;",
        "    if (!hasSyncedQuote(tk)) continue;",
        "brief tape",
    )
    apply(
        "/** Raw numeric price only when a qualifying live feed confirms it — never seed, delayed, cached, stale, or proxy. */\n"
        "function livePx(tk) {\n"
        "  if (!isPrimaryLiveQuote(tk)) return null;\n"
        "  const p = P[tk]?.p;\n"
        "  return typeof p === \"number\" && isFinite(p) && p > 0 ? p : null;\n"
        "}\n"
        "function liveChg(tk) {\n"
        "  if (!isPrimaryLiveQuote(tk)) return null;\n"
        "  if (typeof liveQuoteChangeAvailable !== \"undefined\" && liveQuoteChangeAvailable[tk] === false) return null;\n"
        "  const c = P[tk]?.c;\n"
        "  return typeof c === \"number\" && isFinite(c) ? c : null;\n"
        "}",
        "/** Numeric print when Markets has a synced quote. Never invent a price. */\n"
        "function livePx(tk) {\n"
        "  const key = (typeof resolveInternalTicker === \"function\" && resolveInternalTicker(tk)) || tk;\n"
        "  if (!hasSyncedQuote(key)) return null;\n"
        "  const p = P[key]?.p;\n"
        "  return typeof p === \"number\" && isFinite(p) && p > 0 ? p : null;\n"
        "}\n"
        "function liveChg(tk) {\n"
        "  const key = (typeof resolveInternalTicker === \"function\" && resolveInternalTicker(tk)) || tk;\n"
        "  if (!hasSyncedQuote(key)) return null;\n"
        "  if (typeof liveQuoteChangeAvailable !== \"undefined\" && liveQuoteChangeAvailable[key] === false) return null;\n"
        "  const c = P[key]?.c;\n"
        "  return typeof c === \"number\" && isFinite(c) ? c : null;\n"
        "}",
        "livePx liveChg",
    )
    apply(
        "  const px = referencePx(tk);\n"
        "  const ch = referenceChg(tk);\n"
        "  const meta = _quoteMeta(tk);\n"
        "  const price = px != null ? fp(tk).p : \"no print\";\n"
        "  const change = ch != null ? `${ch >= 0 ? \"+\" : \"\"}${Number(ch).toFixed(2)}%` : \"\";",
        "  const synced = hasSyncedQuote(tk);\n"
        "  const d = fp(tk);\n"
        "  const ch = liveChg(tk);\n"
        "  const meta = _quoteMeta(tk);\n"
        "  const price = synced ? d.p : \"no print\";\n"
        "  const change = synced && ch != null ? `${ch >= 0 ? \"+\" : \"\"}${Number(ch).toFixed(2)}%` : \"\";",
        "front door quote",
    )
    apply(
        "  if(pg===\"home\"){ try{ _refreshHomeAfterPrices(); }catch(e){} }\n"
        "  else if(pg===\"brief\"){ try{ renderMain(); }catch(e){} }",
        "  if(pg===\"home\"||pg===\"brief\"||pg===\"dash\"){\n"
        "    try{ if(typeof _refreshBriefSurfaces===\"function\") _refreshBriefSurfaces(); }catch(e){}\n"
        "  }\n"
        "  if(pg===\"home\"){ try{ _refreshHomeAfterPrices(); }catch(e){} }",
        "brief refresh",
    )
    apply(
        f'<span>DXY <b>${{d.macro?.dxy?.px != null ? d.macro.dxy.px : "{EM}"}}</b></span>',
        '<span>DXY <b>${livePx("DXY") != null ? livePx("DXY").toFixed(2) : (d.macro?.dxy?.px != null ? d.macro.dxy.px : "' + EM + '")}</b></span>',
        "gold hero dollar",
    )
    apply(
        f'<div class="gd-kv"><span>DXY</span><b>${{d.macro?.dxy?.px != null ? d.macro.dxy.px : "{EM}"}} <span class="${{(d.macro?.dxy?.chg||0)>=0?"px-up":"px-dn"}}">${{d.macro?.dxy?.chg != null ? _gdChg(d.macro.dxy.chg) : ""}}</span></b></div>',
        '<div class="gd-kv"><span>DXY</span><b>${livePx("DXY") != null ? livePx("DXY").toFixed(2) : (d.macro?.dxy?.px != null ? d.macro.dxy.px : "' + EM + '")} <span class="${((liveChg("DXY") ?? d.macro?.dxy?.chg ?? 0) >= 0 ? "px-up" : "px-dn")}">${liveChg("DXY") != null ? _gdChg(liveChg("DXY")) : (d.macro?.dxy?.chg != null ? _gdChg(d.macro.dxy.chg) : "")}</span></b></div>',
        "gold dollar card",
    )
    return src, notes


def patch_index(src: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    pairs = [
        (f"var V='TD-{CACHE_FROM}'", f"var V='TD-{CACHE_TO}'", "session cache token"),
        (f"/app.js?v={CACHE_FROM}", f"/app.js?v={CACHE_TO}", "app.js cache token"),
    ]
    for old, new, label in pairs:
        if new in src and old not in src:
            notes.append(f"already: {label}")
            continue
        src, changed = sub_once(src, old, new, label)
        notes.append(f"{'patched' if changed else 'already'}: {label}")
    return src, notes


def main(argv: list[str]) -> None:
    root = pathlib.Path(argv[1] if len(argv) > 1 else ".").resolve()
    app_path = root / "app.js"
    index_path = root / "index.html"
    if not app_path.is_file() or not index_path.is_file():
        fail(f"expected app.js and index.html in {root}")
    app_src, app_notes = patch_app(app_path.read_text(encoding="utf-8"))
    index_src, index_notes = patch_index(index_path.read_text(encoding="utf-8"))
    app_path.write_text(app_src, encoding="utf-8")
    index_path.write_text(index_src, encoding="utf-8")
    print(f"apply_synced_quote_layer_replit: {root}")
    for note in app_notes + index_notes:
        print(f"  {note}")


if __name__ == "__main__":
    main(sys.argv)
