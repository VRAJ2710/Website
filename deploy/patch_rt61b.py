#!/usr/bin/env python3
"""rt61b client patch: chat76 -> chat77. Anchors decide; md5 only warns."""
import hashlib
import pathlib
import subprocess
import sys
import tempfile

EXPECT_APP_MD5 = "2352fdd5aaa0ac23d4bf0fc37cc0fc10"
EXPECT_INDEX_MD5 = "94a37eaab0c596059e5af3eeaf60f038"
NEED_MARKER = "// ── rt61 ──"
REFUSE_MARKER = "// ── rt61b ──"

BLOCK = pathlib.Path(__file__).with_name("rt61b_fe77.js").read_text(encoding="utf-8")
if not BLOCK.startswith("// ── rt61b ──"):
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


def times(text, old, new, label, n):
    c = text.count(old)
    if c != n:
        die("%s count %s" % (label, c))
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


def neutral_prompts(app):
    app = once(
        app,
        '"verdict":"BUY/HOLD/AVOID"',
        '"whatTheDataShows":"2-3 sentences on what the data shows","keyRisks":"a risk in the data","whatToWatch":"what to watch","verdict":"MONITOR"',
        "value lens prompt",
    )
    app = once(
        app,
        '"verdict":"HOLD/ACCUMULATE/AVOID"',
        '"whatTheDataShows":"2-3 sentences on what the data shows","keyRisks":"a risk in the data","whatToWatch":"what to watch","verdict":"MONITOR"',
        "quality lens prompt",
    )
    app = once(
        app,
        '"verdict":"BUY/MONITOR/AVOID"',
        '"whatTheDataShows":"2-3 sentences on what the data shows","keyRisks":"a risk in the data","whatToWatch":"what to watch","verdict":"MONITOR"',
        "catalyst lens prompt",
    )
    app = once(
        app,
        '"verdict":"OVERWEIGHT/NEUTRAL/REDUCE"',
        '"whatTheDataShows":"2-3 sentences on what the data shows","keyRisks":"a risk in the data","whatToWatch":"what to watch","verdict":"MONITOR"',
        "macro lens prompt",
    )
    app = once(
        app,
        '"verdict":"BUY/NEUTRAL/AVOID"',
        '"whatTheDataShows":"2-3 sentences on what the data shows","keyRisks":"a risk in the data","whatToWatch":"what to watch","verdict":"MONITOR"',
        "trend lens prompt",
    )
    app = once(
        app,
        '"verdict":"IMPLEMENT/MONITOR/REJECT"',
        '"whatTheDataShows":"3-4 sentences on what the data shows","keyRisks":"the key risks","whatToWatch":"what to watch","verdict":"MONITOR"',
        "synthesis lens prompt",
    )
    app = once(
        app,
        '"rebalance":[{"action":"Trim largest position to <20%","priority":"high"},{"action":"Add defensive or low-correlation asset","priority":"medium"}]',
        '"whatTheDataShows":"2-3 sentences on what the holdings show","keyRisks":["concentration","correlation"],"whatToWatch":["the largest weight","a holding that diversifies the book"]',
        "portfolio prompt",
    )
    app = once(
        app,
        '{"issue":"Technology overweight at 45%","severity":"high"}',
        '{"issue":"Technology is 45% of the book","severity":"high"}',
        "portfolio example",
    )
    app = once(
        app,
        '"priceMove":"+8% to +14%"',
        '"whatTheDataShows":"what a beat has meant in this history"',
        "earnings up move",
    )
    app = once(
        app,
        '"priceMove":"-7% to -12%"',
        '"keyRisks":"what a miss has meant in this history"',
        "earnings down move",
    )
    app = once(
        app,
        '"tradeConsiderations":"2 sentences on trade setup, implied move vs historical move, and key risk to monitor.","verdict":"WATCH"',
        '"whatToWatch":"a figure to watch next","verdict":"MONITOR"',
        "earnings watch",
    )
    app = once(
        app,
        "verdict options: BULLISH_SETUP / WATCH / CAUTIOUS. Be specific and actionable.",
        "verdict is MONITOR. Describe what the data shows, the key risks, and what to watch.",
        "earnings verdict ask",
    )
    app = once(
        app,
        '"tradingImplication":"string"',
        '"whatTheDataShows":"string","keyRisks":["..."],"whatToWatch":"string"',
        "document prompt",
    )
    app = once(
        app,
        ' — consider rebalance"}',
        ' — review how the book sits against the regime"}',
        "rebalance copy",
    )
    return app


def takeaway_labels(app):
    pairs = [
        ("⬢ AI SYNTHESIS VERDICT", "⬢ AI SYNTHESIS TAKEAWAY", "intel heading"),
        ("RISK SYNTHESIS — FINAL VERDICT", "RISK SYNTHESIS — TAKEAWAY", "desk synth heading"),
        ("VALUATION VERDICT", "VALUATION TAKEAWAY", "valuation heading"),
        (">VERDICT</div>", ">TAKEAWAY</div>", "card heading"),
        ("Final Lens Verdict", "Final Lens Takeaway", "phone synth heading"),
        ("SYNTHESIS VERDICT", "SYNTHESIS TAKEAWAY", "phone chip heading"),
        ("TRADING IMPLICATION", "TAKEAWAY", "document heading"),
        ("TRADE CONSIDERATIONS", "TAKEAWAY", "earnings heading"),
    ]
    for old, new, label in pairs:
        app = once(app, old, new, label)
    app = once(
        app,
        "${r.rebalance?.length?`<div style=\"background:var(--b1);border:1px solid var(--gb);border-radius:9px;padding:11px\">\n"
        "      <div style=\"font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.12em;margin-bottom:6px\">REBALANCING ACTIONS</div>\n"
        "      ${r.rebalance.map(x=>`<div style=\"display:flex;align-items:flex-start;gap:7px;padding:3px 0;font-size:10.5px;color:var(--t2);line-height:1.4\">\n"
        "        <span style=\"color:${x.priority==='high'?'var(--rd)':'var(--gd)'};flex-shrink:0;font-family:var(--mn);font-size:8px;margin-top:2px\">${x.priority==='high'?'●':'○'}</span>\n"
        "        ${x.action}\n"
        "      </div>`).join('')}\n"
        "    </div>`:''}",
        "${fe77_portWatch(r)}",
        "portfolio takeaway",
    )
    app = once(app, "${r.tradeConsiderations}", "${fe77_earnTake(r)}", "earnings takeaway")
    app = once(
        app,
        "  if (r.tradingImplication) {\n"
        "    h += `<div class=\"gc\" style=\"padding:14px;border-left:3px solid var(--gd);margin-bottom:10px\">\n"
        "      <div style=\"font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.18em;margin-bottom:6px\">TAKEAWAY</div>\n"
        "      <div style=\"font-family:var(--sn);font-size:13px;color:var(--tx);line-height:1.65;font-weight:500\">${r.tradingImplication}</div>\n"
        "    </div>`;\n"
        "  }",
        "  h += fe77_intelTake(r);",
        "document takeaway",
    )
    return app


def grey_verdicts(app):
    app = once(
        app,
        'const vcol = vc.includes("IMPLEMENT") || vc.includes("BUY") ? "var(--gn)" : vc.includes("REJECT") || vc.includes("AVOID") ? "var(--rd)" : "var(--gd)";',
        'const vcol = "var(--t3)";',
        "intel chip",
    )
    app = times(
        app,
        'const vc = r.verdict === "IMPLEMENT" || r.verdict === "BUY" ? "var(--gn)" : r.verdict === "REJECT" || r.verdict === "SELL" ? "var(--rd)" : "var(--gd)";',
        'const vc = "var(--t3)";',
        "journal chip",
        2,
    )
    app = once(
        app,
        "const vc=r.verdict==='BULLISH_SETUP'?'var(--gn)':r.verdict==='CAUTIOUS'?'var(--rd)':'var(--gd)';",
        'const vc="var(--t3)";',
        "earnings chip",
    )
    app = once(
        app,
        "const wcol = w.dir === 'BUY' ? 'var(--gn)' : w.dir === 'AVOID' ? 'var(--rd)' : 'var(--gd)';",
        "const wcol = 'var(--t3)';",
        "desk vote",
    )
    app = once(
        app,
        "const vcol = vc?.includes('IMPLEMENT')||vc?.includes('BUY') ? 'var(--gn)' : vc?.includes('REJECT')||vc?.includes('AVOID') ? 'var(--rd)' : 'var(--gd)';",
        "const vcol = 'var(--t3)';",
        "desk synth chip",
    )
    app = once(
        app,
        "const vcol = vc?.includes('BUY')||vc?.includes('IMPLEMENT')||vc?.includes('OVERWEIGHT') ? 'var(--gn)' : vc?.includes('AVOID')||vc?.includes('SELL')||vc?.includes('REDUCE') ? 'var(--rd)' : 'var(--gd)';",
        "const vcol = 'var(--t3)';",
        "desk member chip",
    )
    app = once(
        app,
        'const vcColor=vc=>vc==="buy"?"var(--gn)":vc==="avoid"?"var(--rd)":"var(--gd)";',
        'const vcColor=vc=>"var(--t3)";',
        "phone verdict colour",
    )
    app = times(
        app,
        'r.verdict==="IMPLEMENT"?"var(--gn)":r.verdict==="REJECT"?"var(--rd)":"var(--gd)"',
        '"var(--t3)"',
        "history chip",
        2,
    )
    app = once(
        app,
        'const CHAT_VERDICT_COL = { OVERWEIGHT: "var(--gn)", NEUTRAL: "var(--gd)", UNDERWEIGHT: "var(--rd)", MONITOR: "var(--bl)", "RISK-OFF": "var(--rd)" };',
        'const CHAT_VERDICT_COL = { OVERWEIGHT: "var(--t3)", NEUTRAL: "var(--t3)", UNDERWEIGHT: "var(--t3)", MONITOR: "var(--t3)", "RISK-OFF": "var(--t3)" };',
        "chat verdict map",
    )
    app = once(
        app,
        'return CHAT_VERDICT_COL[String(v || "").toUpperCase()] || "var(--bl)";',
        'return "var(--t3)";',
        "chat verdict colour",
    )
    app = once(
        app,
        '${r.verdict?.replace(\'_\',\' \')}',
        '${fe76_vword(r.verdict)||"MONITOR"}',
        "earnings word",
    )
    app = once(
        app,
        'background:var(--gn);border-radius:${avoidPct===0&&holdPct===0?"6px":""}',
        'background:var(--t3);border-radius:${avoidPct===0&&holdPct===0?"6px":""}',
        "buy bar",
    )
    app = once(
        app,
        '${holdPct>0?`<div style="flex:${holdPct};background:var(--gd)"></div>`:""}',
        '${holdPct>0?`<div style="flex:${holdPct};background:var(--t3)"></div>`:""}',
        "hold bar",
    )
    app = once(
        app,
        '${avoidPct>0?`<div style="flex:${avoidPct};background:var(--rd);border-radius:0 6px 6px 0"></div>`:""}',
        '${avoidPct>0?`<div style="flex:${avoidPct};background:var(--t3);border-radius:0 6px 6px 0"></div>`:""}',
        "avoid bar",
    )
    app = once(
        app,
        'background:var(--gn);flex-shrink:0"></span><span style="color:var(--t2)">${fe76_vword("Buy")}',
        'background:var(--t3);flex-shrink:0"></span><span style="color:var(--t2)">${fe76_vword("Buy")}',
        "buy swatch",
    )
    app = once(
        app,
        'background:var(--gd);flex-shrink:0"></span><span style="color:var(--t2)">Hold',
        'background:var(--t3);flex-shrink:0"></span><span style="color:var(--t2)">Hold',
        "hold swatch",
    )
    app = once(
        app,
        'background:var(--rd);flex-shrink:0"></span><span style="color:var(--t2)">${fe76_vword("Avoid")}',
        'background:var(--t3);flex-shrink:0"></span><span style="color:var(--t2)">${fe76_vword("Avoid")}',
        "avoid swatch",
    )
    app = once(
        app,
        '${buyCount>0?`<div style="font-family:var(--mn);font-size:10px;font-weight:700;color:var(--gn)">',
        '${buyCount>0?`<div style="font-family:var(--mn);font-size:10px;font-weight:700;color:var(--t3)">',
        "buy count",
    )
    app = once(
        app,
        '${holdCount>0?`<div style="font-family:var(--mn);font-size:10px;font-weight:700;color:var(--gd)">',
        '${holdCount>0?`<div style="font-family:var(--mn);font-size:10px;font-weight:700;color:var(--t3)">',
        "hold count",
    )
    app = once(
        app,
        '${avoidCount>0?`<div style="font-family:var(--mn);font-size:10px;font-weight:700;color:var(--rd)">',
        '${avoidCount>0?`<div style="font-family:var(--mn);font-size:10px;font-weight:700;color:var(--t3)">',
        "avoid count",
    )
    return app


def spacing_and_chrome(app):
    app = once(
        app,
        '<div><strong>${label === "site intelligence" ? "AI update unavailable" : "AI upgrade unavailable"}</strong><span>${copy} Try again to request the same research.</span></div>',
        '<div class="ai-retry-copy"><strong>${label === "site intelligence" ? "AI update unavailable" : "AI upgrade unavailable"}</strong><span>${copy} Try again to request the same research.</span></div>',
        "ai retry gap",
    )
    app = once(
        app,
        '<div><strong>${unavailable?"AI scoring unavailable":"No AI score published"}</strong><span>${message}</span></div>',
        '<div class="ai-retry-copy"><strong>${unavailable?"AI scoring unavailable":"No AI score published"}</strong><span>${message}</span></div>',
        "news retry gap",
    )
    app = once(
        app,
        "        ${_renderOverlayAccountActions()}\n",
        "",
        "overlay account actions",
    )
    return app


def desk_and_themes(app):
    app = once(
        app,
        "    top[0] ? `Highest conviction on desk: ${top[0].tk} (${top[0].sc}/100, ${top[0].se || \"n/a\"}).` : null,\n"
        "    \"Research only — not investment advice.\"\n"
        "  ].filter(Boolean);",
        "    top[0] ? fe77_deskLine(top[0].tk, top[0].sc) : null,\n"
        "    \"Research only — not investment advice.\"\n"
        "  ].filter(function (part) { return part != null; });",
        "local desk score",
    )
    app = once(
        app,
        'focusTickers: top.map(a => `${a.tk}: ${a.sc}/100 ${a.se || ""}`.trim()),',
        "focusTickers: top.map(a => `${a.tk}: ${a.sc}/100`),",
        "focus tickers",
    )
    app = once(
        app,
        '<strong style="color:var(--gn)">${s.best.pos.tk}</strong> highest conviction (${s.best.sc}/100) · ',
        "${fe77_deskLine(s.best.pos.tk, s.best.sc)} · ",
        "portfolio desk score",
    )
    app = once(
        app,
        "  if (b.overweight?.length || b.underweight?.length) {\n"
        "    h += `<div style=\"padding:10px 16px;border-top:1px solid var(--gb);display:grid;grid-template-columns:1fr 1fr;gap:10px\">\n"
        "      ${b.overweight?.length ? `<div><div style=\"font-family:var(--mn);font-size:7px;color:var(--gn);letter-spacing:0.12em;margin-bottom:4px\">OVERWEIGHT · ${_rt31BriefSrc(b)}</div>${b.overweight.map(x => `<div style=\"font-size:10px;color:var(--t2);padding:1px 0\">+ ${x}</div>`).join(\"\")}</div>` : \"\"}\n"
        "      ${b.underweight?.length ? `<div><div style=\"font-family:var(--mn);font-size:7px;color:var(--rd);letter-spacing:0.12em;margin-bottom:4px\">UNDERWEIGHT</div>${b.underweight.map(x => `<div style=\"font-size:10px;color:var(--t2);padding:1px 0\">− ${x}</div>`).join(\"\")}</div>` : \"\"}\n"
        "    </div>`;\n"
        "  }",
        "  h += fe77_briefThemes(b);",
        "brief themes",
    )
    app = once(
        app,
        'b.overweight?.length ? "OVERWEIGHT: " + b.overweight.join(", ") : "",',
        "(fe77_themesPlain(b) || \"\"),",
        "brief copy",
    )
    app = once(
        app,
        "b.overweight?.length ? `### Overweight\\n${b.overweight.map(x => `- ${x}`).join(\"\\n\")}` : \"\",",
        "(fe77_themesPlain(b) ? \"### \" + fe77_themesPlain(b) : \"\"),",
        "brief markdown",
    )
    app = once(
        app,
        "b.overweight?.length ? `Overweight: ${b.overweight.join(\", \")}.` : \"\",",
        "(fe77_themesPlain(b) ? fe77_themesPlain(b) + \".\" : \"\"),",
        "brief speech",
    )
    app = once(
        app,
        "OVERWEIGHT · REGIME ENGINE · LIVE",
        "LEADING THEMES · REGIME ENGINE · LIVE",
        "regime label",
    )
    app = once(
        app,
        '<span class="up">Overweight</span>',
        '<span class="up">Leading themes</span>',
        "desk letter label",
    )
    app = once(
        app,
        "\\nOverweight: ${re.overweight.join(\", \")}\\nUnderweight:",
        "\\nLeading themes: ${re.overweight.join(\", \")}\\nUnderweight:",
        "brief context themes",
    )
    app = once(
        app,
        "\\nTop conviction: ${top}\\n",
        "\\nTop desk score: ${top}\\n",
        "brief context score",
    )
    app = once(
        app,
        "if (_brief?.overweight?.length) insight += ` Overweight: ${_brief.overweight.slice(0, 3).join(\", \")}.`;",
        "if (_brief?.overweight?.length) insight += ` Leading themes: ${_brief.overweight.slice(0, 3).join(\", \")}.`;",
        "brief insight themes",
    )
    app = once(
        app,
        "Generate today's house view — regime, overweight sectors, and actionable playbook.",
        "Generate today's house view — regime, leading themes, and the research agenda.",
        "brief teaser",
    )
    app = once(
        app,
        "Regime overweight: ${re.overweight.slice(0, 3).join(\", \")}.",
        "Leading themes: ${re.overweight.slice(0, 3).join(\", \")}.",
        "tape insight themes",
    )
    app = once(
        app,
        '<div class="paper-rail-h">Overweight</div>',
        '<div class="paper-rail-h">Leading themes</div>',
        "paper rail themes",
    )
    app = once(
        app,
        "Where the market is now. Overweight lists = styles favoured in this regime.",
        "Where the market is now. Leading themes = styles favoured in this regime.",
        "lab themes help",
    )
    app = once(
        app,
        '`Overweight: ${re.overweight.join(", ")} | Underweight: ${re.underweight.join(", ")}`',
        '`Leading themes: ${re.overweight.join(", ")} | Underweight: ${re.underweight.join(", ")}`',
        "chat context themes",
    )
    app = once(
        app,
        '"Full regime brief — what to overweight now?"',
        '"Full regime brief — which themes lead now?"',
        "ask chip themes",
    )
    return app


def visible_conviction(app):
    pairs = [
        ("High conviction requires a specific catalyst and asymmetric payoff.", "A specific catalyst and an asymmetric payoff are what this lens looks for.", "lens tagline"),
        ("(${topSig?.cf}% conviction).", "(${topSig?.cf}% desk score).", "signal insight"),
        ("Conviction-weighted playbook", "Desk-weighted playbook", "search blurb"),
        ("TOP CONVICTION", "TOP DESK SCORE", "signals kicker"),
        ("High-conviction signals mention these tickers", "High desk-score signals mention these tickers", "signal note"),
        ("⬢ CONVICTION HEATMAP", "⬢ DESK SCORE HEATMAP", "heatmap"),
        (">Conviction drop<", ">Desk score drop<", "alert button"),
        ("`Conviction −${a.threshold}`", "`Desk score −${a.threshold}`", "alert label"),
        ("your top conviction holding", "your top desk-score holding", "lens prompt copy"),
        ("free desk brief, conviction scores)", "free desk brief, desk scores)", "trust note"),
        ("conviction-weighted market signals", "desk-weighted market signals", "help copy"),
        ("HIGH CONVICTION", "HIGH DESK SCORE", "high score"),
        ("LOW CONVICTION", "LOW DESK SCORE", "low score"),
        (">Top Conviction<", ">Top desk score<", "home section"),
        ('>Conviction</button>', ">Desk score</button>", "sort button"),
        ('"Conviction-weighted · regime-aligned playbook"', '"Desk-weighted · regime-aligned playbook"', "signals header"),
        ("before exiting regardless of conviction.", "before exiting regardless of the desk score.", "learn risk"),
        ("aggregates conviction-weighted signals", "aggregates desk-weighted signals", "learn signals"),
        ("| Very high conviction |", "| Very high desk score |", "learn very high"),
        ("| High conviction |", "| High desk score |", "learn high"),
        ("| Low conviction |", "| Low desk score |", "learn low"),
        ('title="Desk conviction score 0–100 — static educational model, not live analytics"', 'title="Desk score 0–100 — static educational model, not live analytics"', "lab title"),
        ("conviction-weighted outlooks", "desk-weighted outlooks", "lab outlook"),
        ("DRAG TO ADJUST CONVICTION", "DRAG TO ADJUST DESK SCORE", "lab drag"),
        (">Conviction Signals<", ">Desk score signals<", "card title"),
        ("High-conviction macro and micro signals", "High desk-score macro and micro signals", "card body"),
        ("Top conviction scores:", "Top desk scores:", "ask context"),
        ("suggests real conviction.", "suggests real participation.", "volume copy"),
        ("conviction-weighted reads", "desk-weighted reads", "signals glossary"),
        ("'Signal conviction'", "'Signal desk score'", "glossary title"),
        ("Higher conviction means more of the inputs point the same way", "A higher desk score means more of the inputs point the same way", "glossary body"),
        ("${s.a}: conviction ", "${s.a}: desk score ", "signal title"),
        ("Conviction is how strongly the desk holds the view", "The desk score is how strongly the desk holds the view", "signal explain"),
        ("s.a + ' conviction'", "s.a + ' desk score'", "signal tip"),
        ("DESK CONVICTION", "DESK SCORE", "signal kicker"),
        ("Conviction is the desk’s own 0–100 rating", "The desk score is the desk’s own 0–100 rating", "signal foot"),
        ("CONVICTION 0–100", "DESK SCORE 0–100", "signal header"),
        ("sp.textContent = 'CONVICTION'", "sp.textContent = 'DESK SCORE'", "column label"),
        ("// Live conviction movers (feed-synced only)", "// Live desk-score movers (feed-synced only)", "comment movers"),
        ("// 4) Signals: the conviction is the desk's fixed rating", "// 4) Signals: the desk score is the desk's fixed rating", "comment score"),
    ]
    for old, new, label in pairs:
        app = once(app, old, new, label)
    # The lab HUD and the later h.replace() both contain this label.
    app = times(app, "CONVICTION · MODEL", "DESK SCORE · MODEL", "lab label", 2)
    app = times(
        app,
        'title="Dispatch conviction score, 0–100"',
        'title="Dispatch desk score, 0–100"',
        "score tooltip",
        2,
    )
    return app


def quotes_and_stream(app):
    app = once(
        app,
        """async function fetchReferencePrices() {
  try {
    const res = await fetch("/api/market-reference-quotes", { signal: AbortSignal.timeout(10_000) });
    if (!res.ok) return 0;
    const data = await res.json();
    let hits = 0;
    if (_applyLiveQuote("XAU", _rt37Ref("XAU", data.XAU), data.XAU?.source)) hits++;
    if (_applyLiveQuote("DXY", _rt37Ref("DXY", data.DXY), data.DXY?.source)) hits++;
    return hits;
  } catch (e) {
    return 0;
  }
}""",
        """async function fetchReferencePrices() {
  try {
    const res = await fetch("/api/market-reference-quotes", { signal: AbortSignal.timeout(10_000) });
    if (!res.ok) return 0;
    const data = await res.json();
    try { fe77_takeRef(data); } catch (e77) {}
    let hits = 0;
    var xq = (typeof fe77_prepXau === "function") ? fe77_prepXau(data.XAU) : _rt37Ref("XAU", data.XAU);
    var dq = (typeof fe77_prepDxy === "function") ? fe77_prepDxy(data) : _rt37Ref("DXY", data.DXY);
    if (xq && _applyLiveQuote("XAU", xq, xq.source)) hits++;
    if (dq && _applyLiveQuote("DXY", dq, dq.source)) hits++;
    return hits;
  } catch (e) {
    return 0;
  }
}""",
        "reference quotes",
    )
    app = once(
        app,
        """          if (ev.t) note(ev.t);
          else if (ev.status) note(String(ev.status));
          if (ev.done) final = ev;
          if (ev.error) broken = true;""",
        """          if (ev.t) note(ev.t);
          else if (ev.status) note(String(ev.status));
          try { fe77_takeStreamMeta(ev); } catch (e77m) {}
          if (ev.done) final = ev;
          if (ev.error) broken = true;""",
        "stream meta event",
    )
    app = once(
        app,
        "    let buf = \"\", final = null, broken = false;\n",
        "    let buf = \"\", final = null, broken = false;\n    try { fe77_streamState = { early: null, done: null }; } catch (e77r) {}\n",
        "stream state reset",
    )
    app = once(
        app,
        "    var fe76Meta = (final && final.meta) || null;\n",
        "    var fe76Meta = (typeof fe77_streamMeta === \"function\" ? fe77_streamMeta(final) : null) || (final && final.meta) || null;\n",
        "stream meta attach",
    )
    app = once(
        app,
        '    const title = _escAttr(`${s.lbl} · ${d.label || "NO SYNC"}${d.asOf ? ` · as of ${_fmtAsOf(d.asOf)}` : ""} · ${d.detail || "tap for Lab"}`);\n'
        '    return `<button type="button" class="spine-cell${synced ? "" : " spine-nosync"}" onclick="setLabTicker(\'${s.tk}\');nav(\'lab\')" title="${title}">\n'
        '      <span class="spine-lbl">${s.lbl} ${stat(s.tk)}</span>',
        '    const fe77Lbl = s.tk === "DXY" && typeof fe77_dxyName === "function" ? fe77_dxyName() : s.lbl;\n'
        '    const title = _escAttr(`${fe77Lbl} · ${d.label || "NO SYNC"}${d.asOf ? ` · as of ${_fmtAsOf(d.asOf)}` : ""} · ${d.detail || "tap for Lab"}`);\n'
        '    return `<button type="button" class="spine-cell${synced ? "" : " spine-nosync"}" onclick="setLabTicker(\'${s.tk}\');nav(\'lab\')" title="${title}">\n'
        '      <span class="spine-lbl">${fe77Lbl} ${stat(s.tk)}</span>',
        "spine dxy label",
    )
    return app


def qa_client(app):
    app = once(
        app,
        'if (t === "chat") { toggleChat(); const inp = document.getElementById("chatInp"); if (inp && v) { inp.value = v; sendChatMessage(); } return; }',
        'if (t === "chat") { toggleChat(); const inp = document.getElementById("chatInp"); if (inp && v) { inp.value = v; try { inp.focus(); } catch (eChat) {} } return; }',
        "chat shortcut fill",
    )
    app = once(
        app,
        "  if (inp) { inp.value = q; sendChatMessage(); }",
        "  if (inp) { inp.value = q; try { inp.focus(); } catch (eFu) {} }",
        "follow-up fill",
    )
    app = once(
        app,
        "  if (inp) { inp.value = s; sendChatMessage(); }",
        "  if (inp) { inp.value = s; try { inp.focus(); } catch (eChip) {} }",
        "chip fill",
    )
    app = once(
        app,
        """  if (fe69_asked[key]) return;
  var inp = document.getElementById("chatInp");
  if (!inp || typeof sendChatMessage !== "function") return;
  fe69_asked[key] = 1;
  inp.value = "What matters most about " + fe69_askHead(btn) + "?";
  try { sendChatMessage(); } catch (e6) {}""",
        """  var inp = document.getElementById("chatInp");
  if (!inp) return;
  inp.value = "What matters most about " + fe69_askHead(btn) + "?";
  try { inp.focus(); } catch (e6) {}""",
        "pulse ask fill",
    )
    app = once(
        app,
        '_openResearchAssistant("What matters most in markets right now?")',
        "_openResearchAssistant()",
        "ask open prefill",
    )
    app = once(
        app,
        "try { if (focus) focus.focus(); } catch (e3) {}",
        "try { if (focus) focus.focus({ preventScroll: true }); } catch (e3) {}",
        "sheet focus",
    )
    app = once(
        app,
        """    function fe73_reveal(n) {
      try {
        var on = sheet && sheet.querySelector(".fe71-tile.on");
        var panel = sheet && sheet.querySelector(".more-nav-panel");
        if (!on || !panel) return;
        var delta = on.getBoundingClientRect().top - panel.getBoundingClientRect().top - 64;
        if (Math.abs(delta) > 8) panel.scrollTop += delta;
        if (n < 4) setTimeout(function () { fe73_reveal(n + 1); }, 160);
      } catch (e4) {}
    }
    try { setTimeout(function () { fe73_reveal(0); }, 80); } catch (e3) {}""",
        """    function fe73_reveal() {
      try {
        var panel = sheet && sheet.querySelector(".more-nav-panel");
        if (!panel) return;
        var on = sheet.querySelector(".fe71-tile.on");
        var id = on ? on.getAttribute("data-fe71") : "";
        var home = !on || id === "home" || (typeof pg !== "undefined" && pg === "home");
        if (home) { panel.scrollTop = 0; return; }
        var delta = on.getBoundingClientRect().top - panel.getBoundingClientRect().top - 64;
        if (Math.abs(delta) > 8) panel.scrollTop += delta;
      } catch (e4) {}
    }
    try { requestAnimationFrame(function () { requestAnimationFrame(fe73_reveal); }); } catch (e3) {}""",
        "sheet reveal once",
    )
    app = once(
        app,
        """      if (n < 6) setTimeout(function () { fe76_sheet(n + 1); }, 180);
    }
    try { setTimeout(function () { fe76_sheet(0); }, 100); } catch (e) {}""",
        """    }
    try { requestAnimationFrame(function () { requestAnimationFrame(function () { fe76_sheet(99); }); }); } catch (e) {}""",
        "sheet retry",
    )
    app = once(
        app,
        "const why = ev.conviction == null ? `On hold: no comparable price for ${s.tk} yet` : held ? (Math.abs(mv || 0) > 1.5 ? `Desk rating ${s.cf}, held at ${ev.conviction}: ${s.tk} moved ${mvT}, past the 1.5% review line` : `Desk rating ${s.cf}, held at ${ev.conviction}: the ${s.tk} price is not current`) : `Desk rating ${s.cf} · ${s.tk} ${mvT || 'unchanged'}, within the 1.5% review line`;",
        "const why = ev.conviction == null ? `On hold: no comparable price for ${s.tk} yet` : held ? (Math.abs(mv || 0) > 1.5 ? `Desk score ${s.cf}/100, held at ${ev.conviction}: ${s.tk} moved ${mvT}, past the 1.5% review line` : `Desk score ${s.cf}/100, held at ${ev.conviction}: the ${s.tk} price is not current`) : `Desk score ${s.cf}/100 · ${s.tk} ${mvT || 'unchanged'}, within the 1.5% review line`;",
        "desk score line",
    )
    app = once(
        app,
        'title="Desk rating ${s.cf}"',
        'title="Desk score ${s.cf}/100"',
        "desk score title",
    )
    app = once(
        app,
        "<div>Morning brief not published yet today.</div>",
        "<div>${fe77_emptyBrief()}</div>",
        "brief empty label",
    )
    app = once(
        app,
        """    if (p && typeof p.then === "function" && String(u).indexOf("/api/brief") >= 0) {
      p.then(function (res) { return res.clone().json().then(function (j) { fe76_noteEdition(j); }).catch(function () {}); }).catch(function () {});
    }""",
        """    if (p && typeof p.then === "function" && String(u).indexOf("/api/brief") >= 0 && String(u).indexOf("/api/brief/edition") < 0) {
      p.then(function (res) { if (!res || !res.ok) return null; return res.clone().json().then(function (j) { fe76_noteEdition(j); }).catch(function () {}); }).catch(function () {});
    }""",
        "edition parse",
    )
    app = once(
        app,
        'try { setTimeout(function () { try { fetch("/api/brief/edition", { signal: AbortSignal.timeout(8000) }).catch(function () {}); } catch (e) {} }, 600); } catch (e) {}',
        'try { setTimeout(function () { try { fetch("/api/brief/edition", { signal: AbortSignal.timeout(8000) }).then(function (res) { if (!res || !res.ok) return null; return res.json(); }).then(function (j) { if (j) fe76_noteEdition(j); }).catch(function () {}); } catch (e) {} }, 600); } catch (e) {}',
        "edition fetch",
    )
    app = once(
        app,
        'const fx4=d.p<50&&tk!=="TNX"&&typeof TICKER_CATS!=="undefined"&&TICKER_CATS[tk]==="fx";',
        'const fx4=typeof fe77_fxPair==="function"&&!!fe77_fxPair(tk)&&fe77_fxPair(tk).indexOf("JPY")<0;',
        "fx dp exact",
    )
    app = once(
        app,
        ': (b && b.date ? ` (brief for ${b.date})` : "");',
        ': "";',
        "brief iso kicker",
    )
    app = times(
        app,
        'd.macro?.tnx?.px != null ? d.macro.tnx.px + "%" : "—"',
        'd.macro?.tnx?.px != null ? fe77_yieldText(d.macro.tnx.px) : "—"',
        "gold yield 2dp",
        2,
    )
    app = once(
        app,
        """    const candleSeries = chart.addCandlestickSeries({
      upColor: upCol, downColor: dnCol,
      borderVisible: false,
      wickUpColor: upCol, wickDownColor: dnCol,
    });""",
        """    const fe77Fmt = typeof fe77_chartFmt === "function" ? fe77_chartFmt(tk) : null;
    const candleSeries = chart.addCandlestickSeries({
      upColor: upCol, downColor: dnCol,
      borderVisible: false,
      wickUpColor: upCol, wickDownColor: dnCol,
      ...(fe77Fmt ? { priceFormat: fe77Fmt } : {}),
    });""",
        "chart dp",
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
    if index.count('app.js?v=chat76"') != 1:
        die("cache bust anchor missing")
    app = neutral_prompts(app)
    app = takeaway_labels(app)
    app = grey_verdicts(app)
    app = spacing_and_chrome(app)
    app = desk_and_themes(app)
    app = visible_conviction(app)
    app = quotes_and_stream(app)
    app = qa_client(app)
    app = app + "\n" + BLOCK
    if app.count("function fe77_deskLine(") != 1:
        die("fe77_deskLine count")
    if app.count("function fe77_themesView(") != 1:
        die("fe77_themesView count")
    if app.count("function fe77_takeStreamMeta(") != 1:
        die("fe77_takeStreamMeta count")
    index = index.replace('app.js?v=chat76"', 'app.js?v=chat77"', 1)
    tmp = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
    try:
        tmp.write(app)
        tmp.close()
        chk = subprocess.run(["node", "--check", tmp.name], capture_output=True, text=True)
        if chk.returncode != 0:
            die("node --check failed\n" + chk.stdout + chk.stderr)
        test = subprocess.run(
            ["node", str(pathlib.Path(__file__).with_name("rt61b_fe77_test.js")), tmp.name],
            capture_output=True,
            text=True,
        )
        if test.returncode != 0:
            die("fe77 tests failed\n" + test.stdout + test.stderr)
        print(test.stdout.strip())
    finally:
        pathlib.Path(tmp.name).unlink(missing_ok=True)
    write_text(app_path, app, app_crlf)
    write_text(index_path, index, index_crlf)
    print("patched", app_path, index_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
