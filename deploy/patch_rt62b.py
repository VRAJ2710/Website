#!/usr/bin/env python3
"""rt62b client patch: chat79 -> chat80. Anchors decide; md5 only warns.

One self-contained script. The fe80 runtime is inlined below. A loading
regime ({score, label} and no theme arrays) must not throw, and one
section throwing must not blank the ticker page or raise the boot modal.
"""
import hashlib
import pathlib
import re
import subprocess
import sys
import tempfile

EXPECT_APP_MD5 = "d16d919877becccafd142f86bda132a2"
EXPECT_INDEX_PREFIX = "b50d5cd2"
NEED_MARKER = "// ── rt62 ──"
REFUSE_MARKER = "// ── rt62b ──"
REG_ARR_EXPECT = 49

BLOCK = r"""
// ── rt62b ──
// FE80_PURE_START
function fe80_regArr(re, key) {
  var v = re && typeof re === "object" ? re[key] : undefined;
  return Array.isArray(v) ? v : [];
}
function fe80_isSkel(re) {
  if (!re || typeof re !== "object" || Array.isArray(re)) return true;
  if (re.skeleton === true || re.available === false) return true;
  if (re.score == null || re.score === "" || !isFinite(Number(re.score))) return true;
  return false;
}
function fe80_keepArr(raw, local, key) {
  if (raw && Array.isArray(raw[key])) return raw[key];
  if (local && Array.isArray(local[key])) return local[key];
  return [];
}
function fe80_skelRegime(raw, local) {
  raw = raw && typeof raw === "object" ? raw : {};
  return {
    label: "",
    score: null,
    loading: true,
    skeleton: true,
    available: false,
    narrative: "",
    col: "var(--t3)",
    overweight: fe80_keepArr(raw, local, "overweight"),
    underweight: fe80_keepArr(raw, local, "underweight"),
    neutral: fe80_keepArr(raw, local, "neutral"),
    inputs: raw.inputs && typeof raw.inputs === "object" && !Array.isArray(raw.inputs) ? raw.inputs : {},
    rotation: {},
    asOf: raw.asOf || "",
    asOfUk: raw.asOfUk || raw.computedAtUk || ""
  };
}
function fe80_reg(re) {
  if (fe80_isSkel(re)) return fe80_skelRegime(re, null);
  var ow = re.overweight, uw = re.underweight, neu = re.neutral;
  var complete = Array.isArray(ow) && Array.isArray(uw) && Array.isArray(neu) && re.narrative != null && re.col != null && re.label != null && re.score != null && re.skeleton !== true;
  if (complete) return re;
  var copy = {}, k;
  for (k in re) if (Object.prototype.hasOwnProperty.call(re, k)) copy[k] = re[k];
  if (!Array.isArray(copy.overweight)) copy.overweight = [];
  if (!Array.isArray(copy.underweight)) copy.underweight = [];
  if (!Array.isArray(copy.neutral)) copy.neutral = [];
  if (copy.narrative == null) copy.narrative = "";
  if (copy.col == null) copy.col = "var(--t3)";
  if (!copy.rotation || typeof copy.rotation !== "object" || Array.isArray(copy.rotation)) copy.rotation = {};
  if (copy.inputs == null || typeof copy.inputs !== "object" || Array.isArray(copy.inputs)) copy.inputs = {};
  return copy;
}
function fe80_hideScore(re) {
  if (fe80_isSkel(re)) return true;
  if (re && (re.loading || /loading/i.test(String(re.label || "")))) return true;
  return false;
}
function fe80_regText(re, chat) {
  if (fe80_hideScore(re)) return chat ? "loading" : "Regime";
  re = re || {};
  return chat ? (re.label + " (score " + re.score + "/100)") : (re.label + " · " + re.score + "/100");
}
function fe80_regimeChip(re) {
  re = fe80_reg(re);
  if (re.skeleton || re.score == null) return '<span class="htec-chip htec-chip-regime htec-chip-muted fe80-skel" data-fe80="regime">Regime</span>';
  if (re.loading && re._hide) return "";
  if (re.loading || /loading/i.test(String(re.label || ""))) return '<span class="htec-chip htec-chip-regime htec-chip-muted" data-fe80="regime" title="Waiting for regime inputs">Regime</span>';
  var title = "";
  try { title = typeof fe78_regimeTitle === "function" ? fe78_regimeTitle(re) : re.label; } catch (e) { title = re.label; }
  return '<span class="htec-chip htec-chip-regime" title="' + title + '">' + re.label + " · " + re.score + "/100</span>";
}
function fe80_chatCtx(tickers, text) {
  var peer = "";
  try { peer = typeof _rt38PeerCtx === "function" ? String(_rt38PeerCtx(tickers, text) || "").trim() : ""; } catch (e) {}
  var ctx = "";
  try { ctx = _buildChatContext(); } catch (e2) { try { console.error("fe80", "ask", e2); } catch (e3) {} ctx = "Regime: loading"; }
  return (peer ? peer + "\n\n" : "") + ctx;
}
function fe80_empty(name) {
  name = String(name || "section");
  if (name === "chip") return '<span class="bd trust-stat" data-fe80="chip">—</span>';
  if (name === "chart") return '<div class="gc" data-fe80="chart"><div style="font-family:var(--mn);font-size:10px;color:var(--t3);letter-spacing:0.08em;padding:18px;text-align:center">LOADING CHART…</div></div>';
  if (name === "signals") return '<div class="gc" data-fe80="signals" style="padding:12px"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.12em">SIGNALS</div></div>';
  if (name === "header") return '<div class="rt23-stock" data-fe80="header"></div>';
  if (name === "tab" || name === "page") return '<div class="gc" data-fe80="' + name + '" style="padding:16px;font-family:var(--mn);font-size:10px;color:var(--t3)">—</div>';
  return '<div data-fe80="' + name + '"></div>';
}
function fe80_section(name, fn, empty) {
  try {
    var v = fn();
    return v == null ? (empty == null ? "" : empty) : v;
  } catch (e) {
    try { console.error("fe80", name, e); } catch (e2) {}
    return empty == null ? "" : empty;
  }
}
// FE80_PURE_END
try {
  var fe80_eng = _computeRegimeEngine;
  _computeRegimeEngine = function () {
    var re = null;
    try { re = fe80_eng.apply(this, arguments); } catch (e) { try { console.error("fe80", "regime", e); } catch (e2) {} }
    return fe80_reg(re);
  };
} catch (eEng) {}
try {
  var fe80_stat = stat;
  stat = function () {
    try { return fe80_stat.apply(this, arguments); }
    catch (e) { try { console.error("fe80", "chip", e); } catch (e2) {} return fe80_empty("chip"); }
  };
} catch (eStat) {}
try {
  var fe80_sig = _renderTickerSignals;
  _renderTickerSignals = function () {
    try { return fe80_sig.apply(this, arguments); }
    catch (e) { try { console.error("fe80", "signals", e); } catch (e2) {} return fe80_empty("signals"); }
  };
} catch (eSig) {}
try {
  var fe80_loc = _computeLocalIntel;
  _computeLocalIntel = function () {
    try { return fe80_loc.apply(this, arguments); }
    catch (e) {
      try { console.error("fe80", "intel", e); } catch (e2) {}
      return { headline: "", insight: "", anomalies: [], actions: [], fit: [], priority: "normal", local: true, regime: "", score: 50 };
    }
  };
} catch (eLoc) {}
try {
  var fe80_cc = renderCandleChart;
  renderCandleChart = async function (tk, range, containerId) {
    try { return await fe80_cc.apply(this, arguments); }
    catch (e) {
      try { console.error("fe80", "chart", e); } catch (e2) {}
      try { var el = document.getElementById(containerId); if (el) el.innerHTML = fe80_empty("chart"); } catch (e3) {}
    }
  };
} catch (eCc) {}
try {
  var fe80_p2 = renderP2;
  renderP2 = function () {
    try { return fe80_p2.apply(this, arguments); }
    catch (e) { try { console.error("fe80", "desk", e); } catch (e2) {} }
  };
} catch (eP2) {}
try {
  var fe80_p3 = renderP3;
  renderP3 = function () {
    try { return fe80_p3.apply(this, arguments); }
    catch (e) { try { console.error("fe80", "signals", e); } catch (e2) {} }
  };
} catch (eP3) {}
try {
  var fe80_dyn = renderDynAnlz;
  renderDynAnlz = function () {
    try { return fe80_dyn.apply(this, arguments); }
    catch (e) { try { console.error("fe80", "dyn", e); } catch (e2) {} return fe80_empty("page"); }
  };
} catch (eDyn) {}
try {
  var fe80_sub = fe78_regimeSub;
  fe78_regimeSub = function (re) {
    if (fe80_isSkel(re)) return "";
    var s = "";
    try { s = String(fe80_sub.apply(this, arguments) || ""); } catch (e) { s = ""; }
    return s.replace(/Regime:\s*loading[^\n]{0,16}\d+\s*\/\s*100/gi, "");
  };
  var fe80_title = fe78_regimeTitle;
  fe78_regimeTitle = function (re) {
    if (fe80_isSkel(re)) return "Regime";
    var s = "";
    try { s = String(fe80_title.apply(this, arguments) || ""); } catch (e) { s = ""; }
    return s.replace(/Regime:\s*loading[^\n]{0,16}\d+\s*\/\s*100/gi, "Regime");
  };
} catch (eSub) {}
try {
  var fe80_paint = fe79_paintRegime;
  fe79_paintRegime = function () {
    var re = fe79_regimeBox;
    if (fe80_hideScore(re)) {
      var nodes = document.querySelectorAll(".htec-chip-regime,.home-regime,.lab-regime-lbl");
      for (var i = 0; i < nodes.length; i++) nodes[i].textContent = "Regime";
      var scores = document.querySelectorAll(".lab-regime-score,.paper-regime-sc,.home-regime-sc,.regime-score-label");
      for (var j = 0; j < scores.length; j++) scores[j].textContent = "";
      return;
    }
    try { return fe80_paint.apply(this, arguments); } catch (e) {}
  };
} catch (ePaint) {}
function fe80_scrubRegime(root) {
  if (!root || !root.querySelectorAll) return;
  var bad = /Regime:\s*loading[^\n]{0,24}\d+\s*\/\s*100/ig;
  var nodes = root.querySelectorAll(".htec-chip-regime,.home-regime,.lab-regime-lbl,.lab-regime-score,.regime-score-label,.paper-regime-sc,.home-brief-t");
  var skel = false;
  try {
    var src = (typeof fe79_regimeHold !== "undefined" && fe79_regimeHold) ? fe79_regimeBox : null;
    if (!src && typeof fe78_srvRegime !== "undefined" && fe78_srvRegime) src = fe78_srvRegime;
    if (src) skel = fe80_isSkel(src);
  } catch (e) {}
  for (var i = 0; i < nodes.length; i++) {
    var t = nodes[i].textContent || "";
    if (bad.test(t)) { nodes[i].textContent = t.replace(bad, "Regime"); bad.lastIndex = 0; continue; }
    if (skel && ((/Cautious/.test(t) && /\b50\b/.test(t)) || /null\s*\/\s*100/i.test(t))) nodes[i].textContent = "Regime";
  }
}
try {
  setInterval(function () { try { fe80_scrubRegime(document.body); } catch (e) {} }, 400);
} catch (eScr) {}
"""

REG_PAT = re.compile(
    r"(?<![\w$])(_brief|brief|re|b)(\??)\.(overweight|underweight)(?![A-Za-z0-9_])"
)


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        die("%s count %s" % (label, n))
    return text.replace(old, new, 1)


def counted(text, old, new, label, expect):
    n = text.count(old)
    if n != expect:
        die("%s count %s expected %s" % (label, n, expect))
    return text.replace(old, new)


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


def reg_repl(m):
    return 'fe80_regArr(%s,"%s")' % (m.group(1), m.group(3))


def guard_regime(app):
    found = REG_PAT.findall(app)
    if len(found) != REG_ARR_EXPECT:
        die("regime array reads %s expected %s" % (len(found), REG_ARR_EXPECT))
    app = REG_PAT.sub(reg_repl, app)
    if REG_PAT.findall(app):
        die("regime array reads remain")
    app = once(
        app,
        '(fe80_regArr(brief,"overweight") || fe80_regArr(re,"overweight") || [])',
        '(function(){var _a=brief&&brief.overweight;return Array.isArray(_a)?_a:fe80_regArr(re,"overweight");})()',
        "brief overweight fallback",
    )
    app = once(
        app,
        '(fe80_regArr(brief,"underweight") || fe80_regArr(re,"underweight") || [])',
        '(function(){var _a=brief&&brief.underweight;return Array.isArray(_a)?_a:fe80_regArr(re,"underweight");})()',
        "brief underweight fallback",
    )
    leftover = REG_PAT.findall(app)
    if leftover != [("brief", "", "overweight"), ("brief", "", "underweight")]:
        die("unexpected leftover regime reads %s" % (leftover,))
    if "re.overweight" in app or "re.underweight" in app:
        die("raw re.overweight remains")
    if app.count("fe80_regArr(") != 47:
        die("fe80_regArr count %s" % app.count("fe80_regArr("))
    return app


def anchors(app):
    app = guard_regime(app)
    app = once(
        app,
        "function _tickerRegimeFit(tk, re) {\n  const a = A.find(x => x.tk === tk);",
        "function _tickerRegimeFit(tk, re) {\n  re = fe80_reg(re);\n  const a = A.find(x => x.tk === tk);",
        "fit guard",
    )
    app = once(
        app,
        "try { _tickerRegimeFit = function (tk, re) { const a = A.find(x => x.tk === tk), chg = liveChg(tk); let score = 50;",
        "try { _tickerRegimeFit = function (tk, re) { re = fe80_reg(re); const a = A.find(x => x.tk === tk), chg = liveChg(tk); let score = 50;",
        "live fit guard",
    )
    app = once(
        app,
        "function _rt52Fit(tk) { const re = _computeRegimeEngine(), a = A.find(x => x.tk === tk), chg = liveChg(tk), rows = [['Starting point', 50]];",
        "function _rt52Fit(tk) { const re = fe80_reg(_computeRegimeEngine()), a = A.find(x => x.tk === tk), chg = liveChg(tk), rows = [['Starting point', 50]];",
        "rt52 fit guard",
    )
    app = once(
        app,
        "    if (fe79_regimeHold && fe79_regimeBox) return fe79_regimeBox;",
        "    if (fe79_regimeHold) return fe80_reg(fe79_regimeBox);",
        "held regime",
    )
    app = once(
        app,
        '${bd(_rt39Cat(a),catBd(a.cat))}${stat(a.tk)}',
        '${bd(_rt39Cat(a),catBd(a.cat))}${fe80_section("chip",function(){return stat(a.tk);},fe80_empty("chip"))}',
        "header chip",
    )
    app = once(
        app,
        '  let h=`<button type="button" class="rt26-back" onclick="_rt26Back()" aria-label="Back">← Back</button><div class="rt23-stock"',
        '  let h=fe80_section("header",function(){return `<button type="button" class="rt26-back" onclick="_rt26Back()" aria-label="Back">← Back</button><div class="rt23-stock"',
        "header start",
    )
    app = once(
        app,
        'Context only · ${_quoteSourceLabel(d.src)} · as of ${_fmtAsOf(d.asOf)}</div>`:""}</div></div>`;',
        'Context only · ${_quoteSourceLabel(d.src)} · as of ${_fmtAsOf(d.asOf)}</div>`:""}</div></div>`},fe80_empty("header"));',
        "header end",
    )
    app = once(
        app,
        """  h+=`<div class="gc"><div style="font-size:8px;color:var(--t3);font-family:var(--mn);letter-spacing:0.1em;margin-bottom:4px">${_rt23ChartLbl(a.tk, (HIST[a.tk]||[]).filter(v=>typeof v==="number"&&isFinite(v)&&v>0).length>=5)}</div>
    <svg viewBox="0 0 300 60" style="width:100%;height:60px;display:block" role="img" aria-label="${a.tk} intraday chart">`;
  const hdRaw=HIST[a.tk]||[];let hd=hdRaw.filter(v=>typeof v==="number"&&isFinite(v)&&v>0);
  if(hd.length<5){const fb=_rt23Ch[a.tk];if(fb&&fb.pts&&fb.pts.length>=5)hd=fb.pts;else _rt23ChartFetch(a.tk);}
  if(hd.length>=5){const mn=Math.min(...hd),mx=Math.max(...hd),rng=mx-mn||Math.max(mx*0.001,1e-9);
    const sparkCol=chAn==null?"var(--t3)":chAn>0?"var(--gn)":chAn<0?"var(--rd)":"var(--t3)";
    const sparkFill=chAn==null?"rgba(255,255,255,0.04)":chAn>0?"var(--gnG)":chAn<0?"var(--rdG)":"rgba(255,255,255,0.04)";
    const pts=hd.map((v,i)=>`${(i/(hd.length-1))*300},${55-((v-mn)/rng)*48}`).join(" ");
    h+=`<polyline points="${pts}" fill="none" stroke="${sparkCol}" stroke-width="1.5"/>`;
    const fillPts=pts+` ${300},55 0,55`;
    h+=`<polyline points="${fillPts}" fill="${sparkFill}" stroke="none" opacity="0.5"/>`;
  } else {
    h+=`<text x="150" y="34" text-anchor="middle" font-family="JetBrains Mono" font-size="10" fill="var(--t3)" letter-spacing="0.08em">${_rt23Ch[a.tk]&&_rt23Ch[a.tk].failed?"CHART DATA UNAVAILABLE RIGHT NOW":"LOADING CHART…"}</text>`;
  }
  h+=`</svg></div>`;""",
        """  h += fe80_section("chart", function () {
    var h = "";
    h+=`<div class="gc"><div style="font-size:8px;color:var(--t3);font-family:var(--mn);letter-spacing:0.1em;margin-bottom:4px">${_rt23ChartLbl(a.tk, (HIST[a.tk]||[]).filter(v=>typeof v==="number"&&isFinite(v)&&v>0).length>=5)}</div>
    <svg viewBox="0 0 300 60" style="width:100%;height:60px;display:block" role="img" aria-label="${a.tk} intraday chart">`;
  const hdRaw=HIST[a.tk]||[];let hd=hdRaw.filter(v=>typeof v==="number"&&isFinite(v)&&v>0);
  if(hd.length<5){const fb=_rt23Ch[a.tk];if(fb&&fb.pts&&fb.pts.length>=5)hd=fb.pts;else _rt23ChartFetch(a.tk);}
  if(hd.length>=5){const mn=Math.min(...hd),mx=Math.max(...hd),rng=mx-mn||Math.max(mx*0.001,1e-9);
    const sparkCol=chAn==null?"var(--t3)":chAn>0?"var(--gn)":chAn<0?"var(--rd)":"var(--t3)";
    const sparkFill=chAn==null?"rgba(255,255,255,0.04)":chAn>0?"var(--gnG)":chAn<0?"var(--rdG)":"rgba(255,255,255,0.04)";
    const pts=hd.map((v,i)=>`${(i/(hd.length-1))*300},${55-((v-mn)/rng)*48}`).join(" ");
    h+=`<polyline points="${pts}" fill="none" stroke="${sparkCol}" stroke-width="1.5"/>`;
    const fillPts=pts+` ${300},55 0,55`;
    h+=`<polyline points="${fillPts}" fill="${sparkFill}" stroke="none" opacity="0.5"/>`;
  } else {
    h+=`<text x="150" y="34" text-anchor="middle" font-family="JetBrains Mono" font-size="10" fill="var(--t3)" letter-spacing="0.08em">${_rt23Ch[a.tk]&&_rt23Ch[a.tk].failed?"CHART DATA UNAVAILABLE RIGHT NOW":"LOADING CHART…"}</text>`;
  }
  h+=`</svg></div>`;
    return h;
  }, fe80_empty("chart"));""",
        "chart section",
    )
    app = once(
        app,
        '  h += _renderSiteIntelCard("ticker", { tk: a.tk });',
        '  h += fe80_section("intel", function () { return _renderSiteIntelCard("ticker", { tk: a.tk }); }, "");',
        "intel section",
    )
    app = once(
        app,
        "    h+=_rt53FitHtml(a.tk)+",
        '    h+=fe80_section("regime-fit", function () { return _rt53FitHtml(a.tk); }, "")+',
        "regime fit section",
    )
    app = once(
        app,
        "    h += _renderTickerSignals(a.tk);",
        '    h += fe80_section("signals", function () { return _renderTickerSignals(a.tk); }, fe80_empty("signals"));',
        "signals section",
    )
    app = counted(
        app,
        'h+=(typeof _rt53FitHtml==="function"?_rt53FitHtml(_dynTk):"");',
        'h+=fe80_section("regime-fit", function () { return (typeof _rt53FitHtml==="function"?_rt53FitHtml(_dynTk):""); }, "");',
        "dyn regime fit",
        2,
    )
    app = once(
        app,
        """  if(aTab==="nw"){
    h+=`<div id="anlz-nw-root">${_renderTickerNewsPanel(a.tk)}</div>`;""",
        """  try {
  if(aTab==="nw"){
    h+=`<div id="anlz-nw-root">${_renderTickerNewsPanel(a.tk)}</div>`;""",
        "tab try",
    )
    app = once(
        app,
        """      h+=`<button onclick="runCommittee('${a.tk}')" style="width:100%;background:var(--b2);color:var(--t2);border:1px solid var(--gb);border-radius:9px;padding:11px;cursor:pointer;font-size:12px;font-weight:600;font-family:var(--sn);margin-top:8px">⬢ Re-run Lens Engine</button>`;
    }
  }
  return h;
}""",
        """      h+=`<button onclick="runCommittee('${a.tk}')" style="width:100%;background:var(--b2);color:var(--t2);border:1px solid var(--gb);border-radius:9px;padding:11px;cursor:pointer;font-size:12px;font-weight:600;font-family:var(--sn);margin-top:8px">⬢ Re-run Lens Engine</button>`;
    }
  }
  } catch (e) { try { console.error("fe80", "tab", e); } catch (e2) {} h += fe80_empty("tab"); }
  return h;
}""",
        "tab catch",
    )
    app = once(
        app,
        """  let html = "";
  switch (pg) {""",
        """  let html = "";
  try {
  switch (pg) {""",
        "renderMain try",
    )
    app = once(
        app,
        """    default: html = renderDash();
  }
  el.innerHTML = html + (typeof _siteFooter === "function" ? _siteFooter() : "");""",
        """    default: html = renderDash();
  }
  } catch (e) { try { console.error("fe80", "page", e); } catch (e2) {} html = fe80_empty("page"); }
  el.innerHTML = html + (typeof _siteFooter === "function" ? _siteFooter() : "");""",
        "renderMain catch",
    )
    app = once(
        app,
        "function _setATab(t){aTab=t;if(IS_DESKTOP())renderP2();else renderMain();_rt22TabIntoView();}",
        "function _setATab(t){aTab=t;try{if(IS_DESKTOP())renderP2();else renderMain();}catch(e){try{console.error(\"fe80\",\"tab\",e);}catch(e2){}}try{_rt22TabIntoView();}catch(e3){}}",
        "set tab",
    )
    app = once(
        app,
        "function fe78_regimeFrom(raw, local) {\n  var srv = null;",
        "function fe78_regimeFrom(raw, local) {\n  if (raw && typeof raw === \"object\" && raw.localEstimate !== true && (raw.available === false || raw.score == null || raw.score === \"\")) return fe80_skelRegime(raw, local);\n  var srv = null;",
        "regimeFrom skeleton",
    )
    app = once(
        app,
        "    out.col = fe78_regimeCol(srv.score);\n    return out;",
        "    out.col = fe78_regimeCol(srv.score);\n    out.overweight = Array.isArray(raw.overweight) ? raw.overweight : (Array.isArray(out.overweight) ? out.overweight : []);\n    out.underweight = Array.isArray(raw.underweight) ? raw.underweight : (Array.isArray(out.underweight) ? out.underweight : []);\n    out.neutral = Array.isArray(raw.neutral) ? raw.neutral : (Array.isArray(out.neutral) ? out.neutral : []);\n    return out;",
        "regimeFrom arrays",
    )
    app = once(
        app,
        "function fe79_takeRegime(raw) {\n  var v = fe79_regimeView(raw);",
        "function fe79_takeRegime(raw) {\n  if (raw && typeof raw === \"object\" && (raw.available === false || raw.score == null || raw.score === \"\")) {\n    fe79_regimeBox = fe80_skelRegime(raw, null);\n    fe79_regimeHold = true;\n    try { fe79_paintRegime(); } catch (eSk) {}\n    return fe79_regimeBox;\n  }\n  var v = fe79_regimeView(raw);",
        "takeRegime skeleton",
    )
    app = once(
        app,
        "  fe79_regimeBox.source = \"server\";\n  fe79_regimeHold = true;",
        "  fe79_regimeBox.source = \"server\";\n  if (Array.isArray(raw.overweight)) fe79_regimeBox.overweight = raw.overweight;\n  if (Array.isArray(raw.underweight)) fe79_regimeBox.underweight = raw.underweight;\n  if (Array.isArray(raw.neutral)) fe79_regimeBox.neutral = raw.neutral;\n  fe79_regimeHold = true;",
        "takeRegime arrays",
    )
    app = once(
        app,
        """  return {
    label: label,
    score: isFinite(score) ? score : null,
    asOf: raw.asOf || asOf,
    asOfUk: asOf,
    localEstimate: raw.localEstimate === true,
    loading: false
  };
}""",
        """  return {
    label: label,
    score: isFinite(score) ? score : null,
    asOf: raw.asOf || asOf,
    asOfUk: asOf,
    localEstimate: raw.localEstimate === true,
    loading: false,
    overweight: Array.isArray(raw.overweight) ? raw.overweight : fe80_regArr(cur, "overweight"),
    underweight: Array.isArray(raw.underweight) ? raw.underweight : fe80_regArr(cur, "underweight"),
    neutral: Array.isArray(raw.neutral) ? raw.neutral : fe80_regArr(cur, "neutral")
  };
}""",
        "setRegime arrays",
    )
    app = once(
        app,
        '`Regime: ${re.label} (score ${re.score}/100)`,',
        '`Regime: ${fe80_regText(re, true)}`,',
        "chat regime line",
    )
    app = once(
        app,
        'return `Regime: ${re.label} (score ${re.score}/100)\\n',
        'return `Regime: ${fe80_regText(re, true)}\\n',
        "brief regime line",
    )
    app = once(
        app,
        '`Leading themes: ${fe80_regArr(re,"overweight").join(", ")} | Underweight: ${fe80_regArr(re,"underweight").join(", ")}`,',
        '`Leading themes: ${fe80_regArr(re,"overweight").join(", ")} | Underweight: ${fe80_regArr(re,"underweight").join(", ")} | Neutral: ${fe80_regArr(re,"neutral").join(", ")}`,',
        "chat neutral",
    )
    app = once(
        app,
        'Leading themes: ${fe80_regArr(re,"overweight").join(", ")}\\nUnderweight: ${fe80_regArr(re,"underweight").join(", ")}\\n',
        'Leading themes: ${fe80_regArr(re,"overweight").join(", ")}\\nUnderweight: ${fe80_regArr(re,"underweight").join(", ")}\\nNeutral: ${fe80_regArr(re,"neutral").join(", ")}\\n',
        "brief neutral",
    )
    app = once(
        app,
        'context: (_rt38PeerCtx(tickers, text).trim() ? _rt38PeerCtx(tickers, text).trim() + "\\n\\n" : "") + _buildChatContext(),',
        'context: fe80_chatCtx(tickers, text),',
        "chat payload",
    )
    app = counted(
        app,
        're.loading&&re._hide?"":re.loading?`<span class="htec-chip htec-chip-regime htec-chip-muted" title="Waiting for VIX and S&amp;P 500 inputs">Regime: loading…</span>`:`<span class="htec-chip htec-chip-regime" title="${fe78_regimeTitle(re)}">${re.label} · ${re.score}/100</span>`',
        'fe80_regimeChip(re)',
        "regime chips",
        2,
    )
    app = once(
        app,
        '<div class="home-regime" style="color:${re.col}">${re.label}${re.score != null && !re.loading ?',
        '<div class="home-regime" style="color:${re.col}">${fe80_hideScore(re)?"Regime":re.label}${!fe80_hideScore(re) && re.score != null && !re.loading ?',
        "home regime",
    )
    app = once(
        app,
        '${re && re.loading ? (re._hide ? "" : " · Regime: loading…") : re && re.label ?',
        '${re && fe80_isSkel(re) ? "" : re && re.loading ? (re._hide ? "" : " · Regime: loading…") : re && re.label ?',
        "home brief skel",
    )
    app = once(
        app,
        'function _renderRegimeEngine(re) {\n  re = re || _computeRegimeEngine();',
        'function _renderRegimeEngine(re) {\n  re = re || _computeRegimeEngine();\n  if (fe80_hideScore(re)) return \'<div class="gc gc-regime fe80-skel" data-fe80="regime" style="padding:12px;border-left:3px solid var(--b4)"><div style="font-size:8px;color:var(--t3);font-family:var(--mn);letter-spacing:0.1em">REGIME</div><div style="font-size:15px;font-weight:800;margin-top:4px">Regime</div></div>\';',
        "regime card skel",
    )
    app = once(
        app,
        'function _renderRegimeRing(re) {\n  const circ = 2 * Math.PI * 42;',
        'function _renderRegimeRing(re) {\n  if (fe80_hideScore(re)) return \'<svg class="lab-regime-ring fe80-skel" data-fe80="regime" width="88" height="88" viewBox="0 0 96 96"><text x="48" y="52" text-anchor="middle" font-family="JetBrains Mono" font-size="11" fill="var(--t3)">Regime</text></svg>\';\n  const circ = 2 * Math.PI * 42;',
        "regime ring skel",
    )
    app = once(
        app,
        'headline = `${re.label} · ${re.score}/100`;',
        'headline = fe80_regText(re);',
        "pulse headline",
    )
    app = once(
        app,
        '${reP4.label} · ${reP4.score}/100',
        '${fe80_regText(reP4)}',
        "desk regime line",
    )
    app = once(
        app,
        '<span class="paper-regime-sc">${re.score}/100</span>',
        '<span class="paper-regime-sc">${fe80_hideScore(re)?"":re.score+"/100"}</span>',
        "paper score",
    )
    app = once(
        app,
        '<strong style="color:${re.col||"var(--gd)"}">${_escHtml(re.label)}</strong>',
        '<strong style="color:${re.col||"var(--gd)"}">${_escHtml(fe80_hideScore(re)?"Regime":re.label)}</strong>',
        "paper label",
    )
    app = once(
        app,
        '<div class="lab-regime-lbl">${re.label}</div>\n              <div class="lab-regime-score" title="${fe78_regimeTitle(re)}">Score ${re.score}/100</div>',
        '<div class="lab-regime-lbl">${fe80_hideScore(re)?"Regime":re.label}</div>\n              <div class="lab-regime-score" title="${fe78_regimeTitle(re)}">${fe80_hideScore(re)?"":("Score "+re.score+"/100")}</div>',
        "lab score",
    )
    app = once(
        app,
        "  const score=Math.max(0,Math.min(100,Number(re.score)||0));",
        "  const _fe80Sk=fe80_isSkel(re);\n  const score=_fe80Sk?null:Math.max(0,Math.min(100,Number(re.score)||0));",
        "book score",
    )
    app = once(
        app,
        'Regime <strong style="color:${re.col||"var(--wire)"}">${re.label}</strong>',
        'Regime <strong style="color:${re.col||"var(--wire)"}">${_fe80Sk?"Regime":re.label}</strong>',
        "book label",
    )
    app = once(
        app,
        '<span class="regime-score" style="--regime-col:${re.col||"var(--wire)"};--regime-pct:${score}" title="Regime score ${score}/100">\n          <span class="regime-score-ring" data-score="${score}"></span>\n          <span class="regime-score-label">${score}<span style="opacity:.55;font-weight:500">/100</span></span>',
        '<span class="regime-score" style="--regime-col:${re.col||"var(--wire)"};--regime-pct:${_fe80Sk?0:score}" title="${_fe80Sk?"Regime":("Regime score "+score+"/100")}">\n          <span class="regime-score-ring" data-score="${_fe80Sk?"":score}"></span>\n          <span class="regime-score-label">${_fe80Sk?"Regime":score}<span style="opacity:.55;font-weight:500">${_fe80Sk?"":"/100"}</span></span>',
        "book ring",
    )
    app = once(
        app,
        "function _deskLetterTitle(re, brief) {\n  if (brief?.headline) return brief.headline;\n  const s = re?.score ?? 50;",
        "function _deskLetterTitle(re, brief) {\n  if (brief?.headline) return brief.headline;\n  if (fe80_hideScore(re)) return \"Regime\";\n  const s = re?.score ?? 50;",
        "letter title",
    )
    app = once(
        app,
        "function _suggestMacroPack(re) {\n  const s = re?.score ?? 50;",
        "function _suggestMacroPack(re) {\n  if (fe80_isSkel(re)) return \"balanced\";\n  const s = re?.score ?? 50;",
        "macro pack",
    )
    app = once(
        app,
        'return `${re.label} (score ${re.score}/100). ${re.narrative || ""} Favour: ${(fe80_regArr(re,"overweight") || []).slice(0, 3).join(", ") || "—"}. Underweight: ${(fe80_regArr(re,"underweight") || []).slice(0, 2).join(", ") || "—"}.`;',
        'return `${fe80_regText(re)}. ${re.narrative || ""} Favour: ${(fe80_regArr(re,"overweight") || []).slice(0, 3).join(", ") || "—"}. Underweight: ${(fe80_regArr(re,"underweight") || []).slice(0, 2).join(", ") || "—"}.`;',
        "letter deck",
    )
    app = once(
        app,
        "if (!re.loading) h += `<div class=\"gc\" style=\"padding:12px;border-left:3px solid ${re.col};margin-bottom:10px\">",
        "if (!fe80_hideScore(re)) h += `<div class=\"gc\" style=\"padding:12px;border-left:3px solid ${re.col};margin-bottom:10px\">",
        "signals playbook",
    )
    return app


def pure_slice(text):
    a = text.find("// FE80_PURE_START")
    b = text.find("// FE80_PURE_END")
    if a < 0 or b < 0 or b <= a:
        die("pure slice missing")
    return text[a:b]


def run_unit(app_text):
    src = pure_slice(BLOCK) + """
function assert(c, m) { if (!c) throw new Error(m || "assert"); }
var full = { score: 55, label: "Risk-On", narrative: "Risk-On.", col: "var(--gn)", overweight: ["Gold", "Energy"], underweight: ["growth"], neutral: [] };
assert(fe80_reg(full) === full, "full same ref");
assert(fe80_regArr(full, "overweight") === full.overweight, "full array");
assert(fe80_regArr({ score: 50, label: "Cautious" }, "overweight").length === 0, "loading");
assert(fe80_regArr(null, "underweight").length === 0, "null");
assert(fe80_regArr({}, "overweight").length === 0, "empty");
assert(fe80_regArr({ overweight: null, underweight: null }, "overweight").length === 0, "null arr");
var sk = fe80_reg(null);
assert(sk.score == null && sk.label === "" && sk.skeleton === true && sk.available === false, "null reg");
var blank = fe80_reg({});
assert(blank.overweight.length === 0 && blank.narrative === "" && blank.skeleton === true && blank.score == null, "blank reg");
var cautious = fe80_reg({ score: 50, label: "Cautious" });
assert(cautious.label === "Cautious" && cautious.score === 50 && cautious.skeleton !== true && cautious.overweight.length === 0, "cautious stays");
var avail = fe80_reg({ available: false, score: null, overweight: ["Gold"], underweight: ["cash"], neutral: ["x"] });
assert(avail.skeleton === true && avail.score == null && avail.label === "" && avail.overweight[0] === "Gold" && avail.underweight[0] === "cash" && avail.neutral[0] === "x", "avail keeps arrays");
assert(fe80_keepArr({ overweight: [] }, { overweight: ["Gold"] }, "overweight").length === 0, "empty server wins");
assert(fe80_keepArr({}, { overweight: ["Gold"] }, "overweight")[0] === "Gold", "local kept");
assert(fe80_regText({ score: 50, label: "Cautious" }, true) === "Cautious (score 50/100)", "text cautious");
assert(fe80_regText(null, true) === "loading", "text skel chat");
assert(fe80_regText({ available: false, score: 50, label: "Cautious" }) === "Regime", "text avail");
assert(fe80_regText({ score: 50, label: "Regime: loading…", loading: true }).indexOf("50") < 0, "text load");
assert(fe80_regimeChip(null).indexOf(">Regime<") >= 0 && fe80_regimeChip(null).indexOf("50") < 0, "chip null");
assert(fe80_regimeChip({ score: 50, label: "Cautious" }).indexOf("Cautious") >= 0, "chip cautious");
var brief = {}, re = { overweight: ["Gold"], underweight: ["growth"] };
var ow = (Array.isArray(brief && brief.overweight) ? brief.overweight : fe80_regArr(re, "overweight"));
assert(ow[0] === "Gold", "brief falls through");
brief = { overweight: ["Cash"] };
ow = (Array.isArray(brief && brief.overweight) ? brief.overweight : fe80_regArr(re, "overweight"));
assert(ow[0] === "Cash", "brief wins");
assert(fe80_regArr({ overweight: ["Gold"] }, "overweight").some(function (x) { return /Energy|Gold|commodit/i.test(x); }) === true, "gold some");
assert(fe80_regArr({ score: 50, label: "Cautious" }, "overweight").some(function (x) { return /Energy|Gold|commodit/i.test(x); }) === false, "loading some");
assert(fe80_section("ok", function () { return "x"; }, "e") === "x", "section ok");
assert(fe80_section("bad", function () { throw new Error("nope"); }, "e") === "e", "section catch");
var inputs = fe80_reg({ score: 50, label: "Cautious", inputs: null }).inputs;
assert(inputs && typeof inputs === "object" && !Array.isArray(inputs), "inputs obj");
console.log("fe80 unit ok");
"""
    # The patched app must call the accessor on the old crash lines.
    if 'fe80_regArr(re,"overweight").some' not in app_text:
        die("overweight some not guarded")
    if 'fe80_regArr(re,"underweight").some' not in app_text:
        die("underweight some not guarded")
    if "re.overweight.some" in app_text or "re.underweight.some" in app_text:
        die("raw some remains")
    if "re.overweight.join" in app_text or "re.underweight.join" in app_text:
        die("raw join remains")
    if "fe80_chatCtx(" not in app_text:
        die("chat ctx missing")
    if 'fe80_regArr(re,"neutral")' not in app_text:
        die("neutral missing")
    if "fe80_skelRegime(raw, local)" not in app_text:
        die("regimeFrom skel missing")
    if "Array.isArray(raw.overweight)" not in app_text:
        die("server arrays dropped")
    tmp = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
    try:
        tmp.write(src)
        tmp.close()
        test = subprocess.run(["node", tmp.name], capture_output=True, text=True)
        if test.returncode != 0:
            die("fe80 tests failed\n" + test.stdout + test.stderr)
        print(test.stdout.strip())
    finally:
        pathlib.Path(tmp.name).unlink(missing_ok=True)


def main():
    if not BLOCK.lstrip().startswith("// ── rt62b ──"):
        die("block marker")
    app_path, index_path = paths()
    if not app_path.is_file() or not index_path.is_file():
        die("missing app.js or index.html")
    app_raw, app, app_crlf = read_text(app_path)
    index_raw, index, index_crlf = read_text(index_path)
    app_sum = md5(app_raw)
    index_sum = md5(index_raw)
    if app_sum != EXPECT_APP_MD5:
        print("WARN app.js md5 %s expected %s" % (app_sum, EXPECT_APP_MD5))
    if not index_sum.startswith(EXPECT_INDEX_PREFIX):
        print("WARN index.html md5 %s expected prefix %s" % (index_sum, EXPECT_INDEX_PREFIX))
    if REFUSE_MARKER in app:
        print("REFUSE")
        return 0
    if NEED_MARKER not in app:
        die("missing anchor %s" % NEED_MARKER)
    if index.count('app.js?v=chat79"') != 1:
        die("cache bust anchor missing")
    app = anchors(app)
    app = app + "\n" + BLOCK.strip() + "\n"
    if app.count("function fe80_regArr(") != 1:
        die("fe80_regArr def")
    if app.count("function fe80_section(") != 1:
        die("fe80_section def")
    if app.count('app.js?v=chat80"') != 0:
        die("cache bust already in app")
    index = index.replace('app.js?v=chat79"', 'app.js?v=chat80"', 1)
    tmp = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
    try:
        tmp.write(app)
        tmp.close()
        chk = subprocess.run(["node", "--check", tmp.name], capture_output=True, text=True)
        if chk.returncode != 0:
            die("node --check failed\n" + chk.stdout + chk.stderr)
        print("node --check ok")
        run_unit(app)
    finally:
        pathlib.Path(tmp.name).unlink(missing_ok=True)
    write_text(app_path, app, app_crlf)
    write_text(index_path, index, index_crlf)
    print("patched", app_path, index_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
