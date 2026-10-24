#!/usr/bin/env python3
"""rt61d client patch: chat77 -> chat78. Anchors decide; md5 only warns."""
import hashlib
import pathlib
import re
import subprocess
import sys
import tempfile

EXPECT_APP_MD5 = "bd60d3b79fd072f75194286ccfefe8ad"
EXPECT_INDEX_MD5 = "2de8e542e16587ac857aee7628b44924"
NEED_MARKER = "// ── rt61b ──"
REFUSE_MARKER = "// ── rt61d ──"
NVDA_OPINION = (
    "AI infrastructure spend accelerating. Data center revenue dominant. "
    "TSMC Q1 confirms demand strength. Elevated valuation justified by 90%+ growth."
)

BLOCK = pathlib.Path(__file__).with_name("rt61d_fe78.js").read_text(encoding="utf-8")
if not BLOCK.startswith("// ── rt61d ──"):
    print("block marker", file=sys.stderr)
    sys.exit(1)


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        die("%s count %s" % (label, n))
    return text.replace(old, new, 1)


def md5(raw):
    return hashlib.md5(raw).hexdigest()


def read_text(path):
    raw = path.read_bytes()
    crlf = b"\r\n" in raw
    return raw, raw.replace(b"\r\n", b"\n").decode("utf-8"), crlf


def write_text(path, text, crlf):
    data = text.encode("utf-8")
    if crlf:
        data = data.replace(b"\n", b"\r\n")
    path.write_bytes(data)


def paths():
    if len(sys.argv) >= 3:
        return pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    if len(sys.argv) == 2:
        d = pathlib.Path(sys.argv[1])
        if d.is_dir():
            return d / "app.js", d / "index.html"
        return d, d.with_name("index.html")
    cwd = pathlib.Path.cwd()
    return cwd / "app.js", cwd / "index.html"


def factual_th(app):
    pat = re.compile(r'\bth:"((?:\\.|[^"\\])*)"')

    def repl(m):
        before = app[max(0, m.start() - 900):m.start()]
        cut = before.rfind("},")
        if cut >= 0:
            before = before[cut + 2:]

        def grab(key):
            found = list(re.finditer(r'\b%s:"((?:\\.|[^"\\])*)"' % key, before))
            return found[-1].group(1) if found else ""

        tk, nm, cat, ex = grab("tk"), grab("nm"), grab("cat"), grab("ex")
        if not tk:
            return m.group(0)
        where = (" listed on %s" % ex) if ex else ""
        text = "%s (%s) is a %s%s. Source: the desk instrument table." % (nm or tk, tk, cat or "instrument", where)
        text = text.replace("\\", "").replace('"', "'")
        return 'th:"%s"' % text

    new, n = pat.subn(repl, app)
    if n < 180:
        die("th replacements %s" % n)
    if NVDA_OPINION in new:
        die("nvda thesis remains")
    print("th factual", n)
    return new


def anchors(app):
    app = once(
        app,
        "const RT_ROLL_RANK = Object.freeze({ stream: 3, y24: 2, cg: 1 });",
        "const RT_ROLL_RANK = Object.freeze({ srv24: 4, stream: 3, y24: 2, cg: 1 });",
        "roll rank",
    )
    app = once(
        app,
        "  P[tk] = { p, c: prev ? +(((p - prev) / prev) * 100).toFixed(2) : 0 };\n"
        "  if (prev) BASE[tk] = { p: prev, c: 0 };\n"
        '  if (prev && (o.src === "coinbase-ws" || o.src === "kraken-ws")) _rt.roll[tk] = { prev, at: now, kind: "stream" };',
        "  var fe78srv = _rt.roll[tk] && _rt.roll[tk].kind === \"srv24\" && now - _rt.roll[tk].at < 30 * 60_000 && _rt.roll[tk].c != null && isFinite(_rt.roll[tk].c) ? _rt.roll[tk].c : null;\n"
        "  P[tk] = { p, c: fe78srv != null ? fe78srv : (prev ? +(((p - prev) / prev) * 100).toFixed(2) : null) };\n"
        "  if (fe78srv == null && prev) BASE[tk] = { p: prev, c: 0 };\n"
        "  if (fe78srv == null && prev && (o.src === \"coinbase-ws\" || o.src === \"kraken-ws\")) _rt.roll[tk] = { prev, at: now, kind: \"stream\" };",
        "stream baseline",
    )
    app = once(
        app,
        "  liveQuoteChangeAvailable[tk] = prev != null;",
        "  liveQuoteChangeAvailable[tk] = (typeof fe78srv !== \"undefined\" && fe78srv != null) || prev != null;",
        "stream change flag",
    )
    app = once(
        app,
        """  if (_rtIsCrypto(tk) && !RT_SRC.has(src) && fin(q.p) && q.p > 0) {
    const r = _rt.roll[tk], rOk = r && r.prev > 0 && now - r.at < 30 * 60_000;
    const c = Number(q.c);
    let kind = null, own = null;
    if (src === "coingecko" && isFinite(c) && c > -100) { kind = "cg"; own = q.p / (1 + c / 100); }
    else if (src.startsWith("yahoo") && q.basis === "rolling_24h" && fin(q.prev) && q.prev > 0) { kind = "y24"; own = q.prev; }""",
        """  if (_rtIsCrypto(tk) && fin(q.p) && q.p > 0 && (!RT_SRC.has(src) || (q && q.baseline === "24h") || (_rt.roll[tk] && _rt.roll[tk].kind === "srv24"))) {
    try { fe78_take(tk, q); } catch (e78) {}
    const fe78b = fe78_cryptoBasis(q, _rt.roll[tk], now);
    if (fe78b.mode === "srv") {
      if (fe78b.c == null) { delete q.c; delete q.change; delete q.changePct; }
      else { q.c = fe78b.c; q.changePct = fe78b.c; }
      if (fe78b.prev) q.prev = fe78b.prev;
      _rt.roll[tk] = { prev: fe78b.prev, at: now, kind: "srv24", c: fe78b.c };
    } else if (fe78b.mode === "keep") {
      if (fe78b.c == null) { delete q.c; delete q.change; delete q.changePct; }
      else { q.c = fe78b.c; q.changePct = fe78b.c; }
      if (fe78b.prev) q.prev = fe78b.prev;
    }
    const r = _rt.roll[tk], rOk = r && r.prev > 0 && now - r.at < 30 * 60_000 && r.kind !== "srv24";
    const c = Number(q.c);
    let kind = null, own = null;
    if (fe78b.mode === "client" && src === "coingecko" && isFinite(c) && c > -100) { kind = "cg"; own = q.p / (1 + c / 100); }
    else if (fe78b.mode === "client" && src.startsWith("yahoo") && q.basis === "rolling_24h" && fin(q.prev) && q.prev > 0) { kind = "y24"; own = q.prev; }""",
        "server 24h basis",
    )
    app = once(
        app,
        """    } else if (!kind) {
      delete q.c; delete q.prev; delete q.change;
    }""",
        """    } else if (!kind && fe78b.mode === "client") {
      delete q.c; delete q.prev; delete q.change;
    }""",
        "keep server change",
    )
    app = once(
        app,
        '&& !(cur && cur.kind === "stream" && now - cur.at < 30 * 60_000)) {',
        '&& !(cur && (cur.kind === "stream" || cur.kind === "srv24") && now - cur.at < 30 * 60_000)) {',
        "hold skips srv24",
    )
    app = once(
        app,
        'if (rOk && r.kind !== "cg" && out.p > 0) out.c24 = ((out.p - r.prev) / r.prev) * 100;',
        'if (r && r.kind === "srv24" && r.c != null && isFinite(Number(r.c))) out.c24 = Number(r.c);\n'
        '  else if (rOk && r.kind !== "cg" && out.p > 0) out.c24 = ((out.p - r.prev) / r.prev) * 100;',
        "coin view srv24",
    )
    app = once(
        app,
        'const powers = [pxLive != null ? "Live Price" : "Price Pending", "Regime", "Macro Signals", "Platform Thesis"];',
        'const powers = [pxLive != null ? "Live Price" : "Price Pending", "Regime", "Macro Signals"].concat((typeof fe78_about === "function" && fe78_about(a)) ? ["Platform Thesis"] : []);',
        "thesis power",
    )
    app = once(
        app,
        'Platform thesis: ${a.th || "None"}',
        '${(function(){var tx=typeof fe78_about==="function"?fe78_about(a):"";return tx?("Platform thesis: "+tx):"";})()}',
        "lens thesis line",
    )
    app = once(
        app,
        '${_rt16Clip(a.th || "", 80)}',
        '${_rt16Clip((typeof fe78_about==="function"?fe78_about(a):"") || "", 80)}',
        "lens fallback",
    )
    app = once(
        app,
        "const thWords = a.th.split('. ');",
        'const thWords = String((typeof fe78_about==="function"?fe78_about(a):(a&&a.th)) || "").split(". ");',
        "factor split",
    )
    app = once(
        app,
        'if (a.th) parts.push(`Platform thesis: ${a.th}`);',
        'var fe78th = typeof fe78_about==="function" ? fe78_about(a) : ""; if (fe78th) parts.push("Platform thesis: " + fe78th);',
        "ask thesis",
    )
    app = once(
        app,
        "why: _rt52E(a.th || '')",
        "why: _rt52E((typeof fe78_about==='function' ? fe78_about(a) : '') || '')",
        "desk why",
    )
    app = once(
        app,
        'h += `<div class="ap-thesis">${_rt26Sent(_rt24Th(a), 200)}</div>`;',
        "h += fe78_profileHtml(a, \"ov\");",
        "overview profile",
    )
    app = once(
        app,
        'h += `<div class="ap-thesis">${_rt24Th(a)}</div>`;',
        'h += fe78_profileHtml(a, "th");',
        "thesis tab",
    )
    app = once(
        app,
        """    h+=`</div><div class="gc"><div style="font-size:8px;color:var(--t3);font-family:var(--mn);letter-spacing:0.1em">AI THESIS</div>
      <div style="font-size:13px;font-weight:700;color:${a.se.includes("Bull")?"var(--gn)":"var(--bl)"};margin-top:6px">${a.se}</div>
      <div style="font-size:10.5px;color:var(--t2);line-height:1.55;margin-top:4px">${_rt26Sent(_rt24Th(a), 140)}</div></div></div>`;""",
        '    h+=`</div>` + fe78_profileHtml(a, "card") + `</div>`;',
        "mobile profile",
    )
    app = once(
        app,
        """    h+=`<div class="gc" style="border-left:3px solid var(--bl)"><div style="font-size:8px;color:var(--t3);font-family:var(--mn);letter-spacing:0.1em">INVESTMENT THESIS</div>
      <div style="font-size:11.5px;color:var(--t2);line-height:1.6;margin-top:6px">${_rt24Th(a)}</div></div>`;""",
        '    h+=fe78_profileHtml(a, "full");',
        "thesis heading",
    )
    app = once(
        app,
        'const chg = !synced || chN == null ? "—" : `${chN >= 0 ? "+" : ""}${d.c}%`;',
        'const chg = !synced || chN == null ? "—" : fe78_chgHtml(s.tk, `${chN >= 0 ? "+" : ""}${d.c}%`);',
        "spine change",
    )
    app = once(
        app,
        'setText(k[2], ch == null ? "—" : sign + d.c + "%"); k[2].style.color = col;',
        'k[2].style.color = col; var fe78tape = ch == null ? "—" : fe78_chgHtml(tk, sign + d.c + "%"); if (k[2].innerHTML !== fe78tape) { k[2].innerHTML = fe78tape; n++; }',
        "tape change",
    )
    app = once(
        app,
        'setText(next, ch == null ? "—" : `${keepArrow ? arrow : ""}${sign}${d.c}%`); next.style.color = col;',
        'next.style.color = col; var fe78cell = ch == null ? "—" : fe78_chgHtml(tk, `${keepArrow ? arrow : ""}${sign}${d.c}%`); if (next.innerHTML !== fe78cell) { next.innerHTML = fe78cell; n++; }',
        "table change",
    )
    app = once(
        app,
        'setText(ce, ch == null ? "—" : (pctOnly ? `${sign}${d.c}%` : `${sign}${d.chg} (${sign}${d.c}%)`));',
        'var fe78ce = ch == null ? "—" : fe78_chgHtml(tk, pctOnly ? `${sign}${d.c}%` : `${sign}${d.chg} (${sign}${d.c}%)`); if (ce.innerHTML !== fe78ce) { ce.innerHTML = fe78ce; n++; }',
        "card change",
    )
    app = once(
        app,
        'if (c) { setText(c, ch == null ? "—" : `${sign}${d.chg} (${sign}${d.c}%)`); c.style.color = col; }',
        'if (c) { c.style.color = col; var fe78dc = ch == null ? "—" : fe78_chgHtml(tk, `${sign}${d.chg} (${sign}${d.c}%)`); if (c.innerHTML !== fe78dc) { c.innerHTML = fe78dc; n++; } }',
        "data card change",
    )
    app = once(
        app,
        '       chgEl.textContent=chgN==null?"—":(pctOnly?`${sign}${d.c}%`:`${sign}${d.chg} (${sign}${d.c}%)`);',
        '       chgEl.innerHTML=chgN==null?"—":fe78_chgHtml(tk, pctOnly?`${sign}${d.c}%`:`${sign}${d.chg} (${sign}${d.c}%)`);',
        "price card paint",
    )
    app = once(
        app,
        '        chEl.textContent = `${sign}${d.chg} (${sign}${d.c}%)`;',
        '        chEl.innerHTML = ch == null ? "—" : fe78_chgHtml(tkAttr, `${sign}${d.chg} (${sign}${d.c}%)`);',
        "command change",
    )
    app = once(
        app,
        '${ch==null?"—":chSign+d.c+"%"}',
        '${ch==null?"—":fe78_chgHtml(k, chSign+d.c+"%")}',
        "tape html",
    )
    app = once(
        app,
        '<div class="idx-card-chg asset-chg ${chgCls}">${na||chN==null?chgDim():`${sign}${d.chg} (${sign}${d.c}%)`}</div>',
        '<div class="idx-card-chg asset-chg ${chgCls}">${na||chN==null?chgDim():fe78_chgHtml(idx.tk, `${sign}${d.chg} (${sign}${d.c}%)`)}</div>',
        "index change",
    )
    app = once(
        app,
        '<span class="conv-chg asset-chg ${chgCls}">${na||chN==null?chgDim():`${sign}${d.c}%`}</span>',
        '<span class="conv-chg asset-chg ${chgCls}">${na||chN==null?chgDim():fe78_chgHtml(a.tk, `${sign}${d.c}%`)}</span>',
        "desk score change",
    )
    app = once(
        app,
        '<div class="change ${chgCol}">${na||chN==null?"—":`${sign}${d.chg} (${sign}${d.c}%)`}</div>',
        '<div class="change ${chgCol}">${na||chN==null?"—":fe78_chgHtml(a.tk, `${sign}${d.chg} (${sign}${d.c}%)`)}</div>',
        "home card change",
    )
    app = once(
        app,
        "  const c = hasChange ? q.c : 0;\n"
        "  const prev = hasPrevious ? q.prev : (hasChange ? q.p / (1 + c / 100) : q.p);\n"
        "  P[tk] = { p: q.p, c: +c.toFixed(2) };\n"
        "  BASE[tk] = { p: prev, c: 0 };",
        "  const c = hasChange && q.c !== 0 ? q.c : null;\n"
        "  const prev = hasPrevious && Math.abs(q.prev - q.p) > Math.max(1e-9, Math.abs(q.p) * 1e-8) ? q.prev : (c != null ? q.p / (1 + c / 100) : null);\n"
        "  P[tk] = { p: q.p, c: c == null ? null : +Number(c).toFixed(2) };\n"
        "  if (prev > 0) BASE[tk] = { p: prev, c: 0 };",
        "quote zero",
    )
    app = once(
        app,
        "    liveQuoteChangeAvailable[tk] = hasChange || hasPrevious;",
        "    liveQuoteChangeAvailable[tk] = c != null;",
        "quote change flag",
    )
    app = once(
        app,
        "  const pct = Number(d.c);\n"
        "  const pctN = isFinite(pct) ? pct : 0;\n"
        "  // d polarity: +1 up, -1 down, 0 flat — never treat flat as up\n"
        "  const dir = pctN > 0 ? 1 : pctN < 0 ? -1 : 0;\n"
        "  return{\n"
        "    p, ..._rt24XauFp(tk, d.p, { c: pctN.toFixed(2), chg: fmtChg, raw: chg, d: dir }),",
        "  const pctN = typeof d.c === \"number\" && isFinite(d.c) ? d.c : null;\n"
        "  // d polarity: +1 up, -1 down, 0 flat — never treat flat as up\n"
        "  const dir = pctN == null ? 0 : (pctN > 0 ? 1 : pctN < 0 ? -1 : 0);\n"
        "  return{\n"
        "    p, ..._rt24XauFp(tk, d.p, { c: pctN == null ? \"—\" : pctN.toFixed(2), chg: pctN == null ? \"—\" : fmtChg, raw: chg, d: dir }),",
        "fp zero",
    )
    app = once(
        app,
        "    priceEl.textContent=fe66_priceLine(a.tk, d, na);\n"
        "    priceEl.style.color=na?\"var(--tx)\":col;\n"
        "  }\n"
        "  if(chgEl){\n"
        "    chgEl.style.color=col;\n"
        "    chgEl.textContent=fe66_chgLine(a.tk, d, na);",
        "    priceEl.innerHTML=fe66_priceLine(a.tk, d, na);\n"
        "    priceEl.style.color=na?\"var(--tx)\":col;\n"
        "  }\n"
        "  if(chgEl){\n"
        "    chgEl.style.color=col;\n"
        "    chgEl.innerHTML=fe66_chgLine(a.tk, d, na);",
        "header html",
    )
    app = once(
        app,
        """          <div style="font-family:var(--mn);font-size:9px;color:var(--t3);margin-bottom:4px">AI score <span title="Desk score from 0–100. This is not the regime fit." style="cursor:help;color:var(--bl)">ⓘ</span></div>
          <div style="font-family:var(--mn);font-size:32px;font-weight:900;color:${scoreCol};line-height:1">${a.sc}</div>
          <div style="font-family:var(--mn);font-size:9px;color:${scoreCol};margin-top:2px">${a.sc>=75?'HIGH DESK SCORE':a.sc>=50?'MODERATE':a.sc>=35?'CAUTIOUS':'LOW DESK SCORE'}</div>""",
        """          <div style="font-family:var(--mn);font-size:12px;font-weight:700;color:${scoreCol};line-height:1.35">${fe78_deskScore(a.sc)}</div>""",
        "desk score panel",
    )
    app = once(
        app,
        '${bd("AI score "+a.sc,scC(a.sc))}',
        '${bd(fe78_deskScore(a.sc),scC(a.sc))}',
        "desk score mobile",
    )
    app = once(
        app,
        '<div style="margin-top:10px; font-size:11px; color:var(--text-tertiary);">${a.se} · ${a.sc}/100</div>',
        '<div style="margin-top:10px; font-size:11px; color:var(--text-tertiary);">${fe78_deskScore(a.sc)}</div>',
        "desk score home",
    )
    app = once(
        app,
        '<div class="ssec"><div class="ssec-lbl">TOP DESK SCORE · ${re.label}</div>',
        '<div class="ssec"><div class="ssec-lbl">Top desk score</div>',
        "top desk search",
    )
    app = app.replace("US Dollar Index (computed from live FX)", "US Dollar Index (ICE)")
    app = app.replace("US Dollar Index (ICE, Yahoo DX-Y.NYB)", "US Dollar Index (ICE)")
    app = app.replace("US Dollar Index (DXY)", "US Dollar Index (ICE)")
    app = once(
        app,
        'name: tk === "DXY" ? "US Dollar Index" : undefined',
        'name: tk === "DXY" ? "US Dollar Index (ICE)" : undefined',
        "dxy stream name",
    )
    app = once(
        app,
        'nm: "US Dollar Index", cat: "FX", ex: "ICE (computed)"',
        'nm: "US Dollar Index (ICE)", cat: "FX", ex: "ICE"',
        "dxy instrument",
    )
    app = app.replace("| 85%+ | Very high desk score | Full position |", "| 85%+ | Desk score 85+/100 | Full position |")
    app = app.replace("| 70-84% | High desk score | 2/3 position |", "| 70-84% | Desk score 70–84/100 | 2/3 position |")
    app = app.replace("| Below 55% | Low desk score | Monitor only |", "| Below 55% | Desk score below 55/100 | Monitor only |")
    app = once(
        app,
        "const f = a0 && a0.sc != null ? { score: a0.sc, label: `Desk score · ${f0.label}` } : f0;",
        'const f = a0 && a0.sc != null ? { score: a0.sc, label: "Desk score " + a0.sc + "/100" } : f0;',
        "smart fit desk score",
    )
    if "HIGH DESK SCORE" in app or "LOW DESK SCORE" in app or "High desk score" in app or "Low desk score" in app:
        die("desk score tier remains")
    if "US Dollar Index (computed from live FX)" in app or "Yahoo DX-Y.NYB" in app:
        die("long dxy label remains")
    app = once(
        app,
        'title="Market regime model (educational)"',
        'title="${fe78_regimeTitle(re)}"',
        "regime chip title",
    )
    app = once(
        app,
        'title="Market regime model (educational): ${re.label} · ${re.score}/100"',
        'title="${fe78_regimeTitle(re)}"',
        "regime chip mobile title",
    )
    app = once(
        app,
        '` · current regime ${_escHtml(re.label)} ${re.score}/100`',
        '` · ${_escHtml(fe78_regimeSub(re))}`',
        "brief regime line",
    )
    app = once(
        app,
        '<div class="home-regime" style="color:${re.col}">${re.label}${re.score != null && !re.loading ? ` · <span class="home-regime-sc">${re.score}/100</span>${_rt20RegCached(re)}` : ""}</div>',
        '<div class="home-regime" style="color:${re.col}">${re.label}${re.score != null && !re.loading ? ` · <span class="home-regime-sc">${re.score}/100</span>${_rt20RegCached(re)}${re.asOfUk ? ` <span class="home-regime-src">${_escHtml(re.asOfUk)}</span>` : ""}` : ""}</div>',
        "home regime as-of",
    )
    app = once(
        app,
        '<div class="ns-cell ns-regime"><div><span class="ns-lbl">REGIME</span>',
        '<div class="ns-cell ns-regime" title="${fe78_regimeTitle(re)}"><div><span class="ns-lbl">REGIME</span>',
        "regime strip title",
    )
    app = once(
        app,
        '<div class="lab-regime-score">Score ${re.score}/100</div>',
        '<div class="lab-regime-score" title="${fe78_regimeTitle(re)}">Score ${re.score}/100</div>${re.asOfUk ? `<div class="fe78-acad">${_escHtml(re.asOfUk)}</div>` : ""}',
        "regime ring as-of",
    )
    app = once(
        app,
        '<div style="font-size:15px;font-weight:800;color:${re.col};margin-top:4px">${re.label}</div>',
        '<div style="font-size:15px;font-weight:800;color:${re.col};margin-top:4px">${re.label}</div>${re.asOfUk ? `<div style="font-size:10px;color:var(--t3);margin-top:2px;font-family:var(--mn)">${_escHtml(re.asOfUk)}</div>` : ""}',
        "regime card as-of",
    )
    app = once(
        app,
        "    if (_rt46Day() !== day) return; const items = j && j.date === day && Array.isArray(j.items) ? j.items.map(_rt48AiOk).filter(Boolean).slice(0, 3) : [];\n"
        "    if (items.length) _rt48Ai = { at: Date.parse(j.generatedAt) || Date.now(), items, kind: j.kind === 'ai' ? 'ai' : 'template', n, tryAt: Date.now() }; })",
        "    if (_rt46Day() !== day) return; const items = j && fe78_academyKeep(j) ? j.items.map(_rt48AiOk).filter(Boolean).slice(0, 3) : [];\n"
        "    if (items.length) _rt48Ai = fe78_academyStore({ at: Date.parse(j.generatedAt) || Date.now(), items, kind: j.kind === 'ai' ? 'ai' : 'template', n, tryAt: Date.now() }, j, day); })",
        "academy yesterday b",
    )
    app = once(
        app,
        "    if (_rt46Day() !== day || !j || j.date !== day || !Array.isArray(j.items)) return; const items = j.items.map(_rt48AiOk).filter(Boolean).slice(0, RT48D_MAX);\n"
        "    // never swap a fuller or AI result for a poorer one\n"
        "    const score = l => l.length + (l.some(x => x.kind === 'ai') ? 10 : 0);\n"
        "    if (items.length && score(items) >= score(prev)) _rt48Ai = { at: Date.parse(j.generatedAt) || Date.now(), items, kind: items.some(x => x.kind === 'ai') ? 'ai' : 'template', n, tryAt: Date.now(), got: Date.now(), v: Number(j.v) || 0 };\n"
        "    else if (items.length) _rt48Ai = Object.assign({}, _rt48Ai, { got: Date.now(), v: Number(j.v) || 0 }); })",
        "    if (_rt46Day() !== day || !fe78_academyKeep(j)) return; const items = j.items.map(_rt48AiOk).filter(Boolean).slice(0, RT48D_MAX);\n"
        "    // never swap a fuller or AI result for a poorer one\n"
        "    const score = l => l.length + (l.some(x => x.kind === 'ai') ? 10 : 0);\n"
        "    if (items.length && score(items) >= score(prev)) _rt48Ai = fe78_academyStore({ at: Date.parse(j.generatedAt) || Date.now(), items, kind: items.some(x => x.kind === 'ai') ? 'ai' : 'template', n, tryAt: Date.now(), got: Date.now(), v: Number(j.v) || 0 }, j, day);\n"
        "    else if (items.length) _rt48Ai = fe78_academyStore(Object.assign({}, _rt48Ai, { got: Date.now(), v: Number(j.v) || 0 }), j, day); })",
        "academy yesterday d",
    )
    return app


def main():
    app_path, index_path = paths()
    if not app_path.is_file() or not index_path.is_file():
        die("missing app.js or index.html")
    app_raw, app, app_crlf = read_text(app_path)
    index_raw, index, index_crlf = read_text(index_path)
    app_sum = md5(app_raw)
    index_sum = md5(index_raw)
    if app_sum != EXPECT_APP_MD5:
        print("WARN app.js md5 %s expected %s" % (app_sum, EXPECT_APP_MD5))
    if index_sum != EXPECT_INDEX_MD5:
        print("WARN index.html md5 %s expected %s" % (index_sum, EXPECT_INDEX_MD5))
    if REFUSE_MARKER in app:
        print("REFUSE")
        return 0
    if NEED_MARKER not in app:
        die("missing anchor %s" % NEED_MARKER)
    if index.count('app.js?v=chat77"') != 1:
        die("cache bust anchor missing")
    app = factual_th(app)
    app = anchors(app)
    app = app + "\n" + BLOCK
    if app.count("function fe78_about(") != 1:
        die("fe78_about count")
    if app.count("function fe78_cryptoBasis(") != 1:
        die("fe78_cryptoBasis count")
    if app.count("function fe78_quoteLabel(") != 1:
        die("fe78_quoteLabel count")
    if app.count("function fe78_academyNote(") != 1:
        die("fe78_academyNote count")
    if app.count("function fe78_regimeFrom(") != 1:
        die("fe78_regimeFrom count")
    index = index.replace('app.js?v=chat77"', 'app.js?v=chat78"', 1)
    tmp = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
    try:
        tmp.write(app)
        tmp.close()
        chk = subprocess.run(["node", "--check", tmp.name], capture_output=True, text=True)
        if chk.returncode != 0:
            die("node --check failed\n" + chk.stdout + chk.stderr)
        test = subprocess.run(
            ["node", str(pathlib.Path(__file__).with_name("rt61d_fe78_test.js")), tmp.name],
            capture_output=True,
            text=True,
        )
        if test.returncode != 0:
            die("fe78 tests failed\n" + test.stdout + test.stderr)
        print(test.stdout.strip())
    finally:
        pathlib.Path(tmp.name).unlink(missing_ok=True)
    write_text(app_path, app, app_crlf)
    write_text(index_path, index, index_crlf)
    print("patched", app_path, index_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
