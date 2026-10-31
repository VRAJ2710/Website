function fe88_bn(v) {
  if (v == null || v === "") return "";
  var n = Number(v);
  if (!isFinite(n)) return "";
  var a = Math.abs(n), s = n < 0 ? "-" : "";
  if (a >= 1e12) return s + "$" + (a / 1e12).toFixed(2) + "tn";
  if (a >= 1e9) return s + "$" + (a / 1e9).toFixed(1) + "bn";
  if (a >= 1e6) return s + "$" + (a / 1e6).toFixed(1) + "m";
  return s + "$" + fe88_INT.format(a);
}
function fe88_sgn(n, dp, unit) {
  if (n == null || n === "" || !isFinite(Number(n))) return "";
  var x = Number(n);
  return (x > 0 ? "+" : x < 0 ? "-" : "") + Math.abs(x).toFixed(dp) + unit;
}
function fe88_gr(v) { return v == null || v === "" ? "" : fe88_sgn(Number(v) * 100, 1, "%"); }
function fe88_p1(v) { return v == null || v === "" || !isFinite(Number(v)) ? "" : Number(v).toFixed(1) + "%"; }
function fe88_ukDate(s) {
  var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(s || ""));
  if (!m) return s ? String(s) : "";
  var mon = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][Number(m[2]) - 1];
  return mon ? Number(m[3]) + " " + mon + " " + m[1] : String(s);
}
function fe88_plain(s) {                                                 // chat93: reader words, not field names
  return String(s || "")
    .replace(/\b(sustainability_gap|fcf_coverage|debt_reliance|interest_burden|margin_trend)\b/g, function (k) { return fe88_flagName(k); })
    .replace(/\bcapex\b/gi, "capital spending").replace(/\bOCF\b/g, "operating cash flow").replace(/\bFCF\b/g, "free cash flow")
    .replace(/\(TTM\)/g, "(last 12 months)").replace(/\bTTM\b/g, "last 12 months").replace(/_/g, " ");
}
function fe88_word(v) {
  var s = String(v == null ? "" : v).toLowerCase();
  var w = s === "red" ? "Red" : s === "amber" ? "Amber" : s === "green" ? "Green" : "Not disclosed";
  return '<span class="fe88-word" data-flag="' + fe88_esc(s || "n/a") + '">' + w + "</span>";
}
function fe88_tc(s) {
  var t = String(s == null ? "" : s).trim();
  if (!t || /[a-z]/.test(t) || /&/.test(t)) return t;
  return t.toLowerCase().replace(/\b([a-z])/g, function (c) { return c.toUpperCase(); });
}
function fe88_cell(v) { var t = fe88_bn(v); return t ? fe88_esc(t) : "Not disclosed"; }
function fe88_companyHtml(payload, neighbors) {
  var inst = (payload && payload.instrument) || {};
  var tk = payload && payload.ticker ? payload.ticker : inst.ticker;
  var co = fe88_tc(inst.company);
  var title = co ? co + " (" + (tk || "") + ")" : (tk || "Company");
  var score = fe88_scoreBits(inst);
  var of = payload && payload.rank_of != null ? payload.rank_of : (payload && payload.total != null ? payload.total : null);
  var rank = inst.rank != null ? "Rank " + inst.rank + (of != null ? " of " + of : "") : "";
  var att = inst.attention ? String(inst.attention) : "";
  var group = inst.group ? fe88_human(inst.group) : "";
  var facts = [rank, score.note && score.text ? score.note + " " + score.text : "", att ? "Attention " + att : "", group].filter(Boolean);
  var m = inst.metrics || {}, t = inst.ttm || {}, tp = inst.ttm_prior || {}, q = inst.latest_quarter || {};
  var filing = inst.filing || {};
  var fig = function (k, v, d) {
    return '<div class="fe88-fig"><p class="fe88-fig-k">' + k + '</p><p class="fe88-fig-v">' + (v ? fe88_esc(v) : "Not disclosed") + "</p>" + (d ? '<p class="fe88-fig-d">' + fe88_esc(d) + "</p>" : "") + "</div>";
  };
  var cov = m.fcf_coverage_of_capex != null && isFinite(Number(m.fcf_coverage_of_capex)) ? "Covers " + Math.round(Number(m.fcf_coverage_of_capex) * 100) + "% of capital spending" : "";
  var figs = '<div class="fe88-figs">' +
    fig("Capital spending, last 12 months", fe88_bn(t.capex), m.capex_growth_ttm != null ? fe88_gr(m.capex_growth_ttm) + " on the prior 12 months" : "") +
    fig("Operating cash flow, last 12 months", fe88_bn(t.ocf), m.ocf_growth_ttm != null ? fe88_gr(m.ocf_growth_ttm) + " on the prior 12 months" : "") +
    fig("Free cash flow, last 12 months", fe88_bn(t.fcf), cov) +
    fig("Operating margin, last 12 months", fe88_p1(m.opmargin_ttm_pct), m.opmargin_change_pp != null ? fe88_sgn(m.opmargin_change_pp, 1, " points") + " on the prior 12 months" : "") +
    "</div>";
  var href = fe88_secHref({ accession: filing.latest_accession, url: inst.disclosures && inst.disclosures.filing && inst.disclosures.filing.url }, inst.cik);
  var srcBits = ["Source: SEC " + (filing.form || "filing")];
  if (filing.latest_period_end) srcBits.push("period to " + fe88_ukDate(filing.latest_period_end));
  if (filing.latest_filed) srcBits.push("filed " + fe88_ukDate(filing.latest_filed));
  var srcLine = '<p class="c93-src">' + fe88_esc(srcBits.join(", ")) + (href ? ' · <a href="' + fe88_esc(href) + '" rel="noopener noreferrer">Read the filing</a>' : "") + "</p>";
  var flag = inst.filing_flag || {};
  var flags = flag.flags || {};
  var lines = fe88_flagLines(payload && payload.thresholds);
  var flagHtml = lines.map(function (pair, idx) {
    return "<li>" + fe88_word(flags[FE88_FLAG_ORDER[idx]]) + " <strong>" + fe88_esc(pair[0]) + "</strong> " + fe88_esc(pair[1]) + "</li>";
  }).join("");
  var ch = inst.changes_since_last_quarter || {};
  var sent = [];
  var prevOv = ch.overall_prev || flag.previous_overall, nowOv = ch.overall_now || flag.overall;
  var since = ch.previous_period_end ? " since the period to " + fe88_ukDate(ch.previous_period_end) : " since last quarter";
  if (prevOv && nowOv) sent.push(prevOv === nowOv ? "The overall flag stayed " + fe88_human(nowOv) + since + "." : "The overall flag moved from " + fe88_human(prevOv) + " to " + fe88_human(nowOv) + since + ".");
  var worse = ch.flags_worse || flag.turned_worse, better = ch.flags_better || flag.turned_better;
  if (Array.isArray(worse) && worse.length) sent.push("Turned worse: " + worse.map(fe88_flagName).join(", ") + ".");
  if (Array.isArray(better) && better.length) sent.push("Turned better: " + better.map(fe88_flagName).join(", ") + ".");
  if (ch.capex_growth_ttm_prev != null && ch.capex_growth_ttm_now != null) sent.push("Growth in capital spending over 12 months went from " + fe88_gr(ch.capex_growth_ttm_prev) + " to " + fe88_gr(ch.capex_growth_ttm_now) + ".");
  var changed = sent.length ? "<p>" + fe88_esc(sent.join(" ")) + "</p>" : "<p>No quarter-on-quarter change was supplied.</p>";
  var fcfPrior = tp.fcf != null ? tp.fcf : (tp.ocf != null && tp.capex != null ? Number(tp.ocf) - Number(tp.capex) : null);
  var row = function (k, a, b, c) { return '<tr><th scope="row">' + k + '</th><td class="n">' + fe88_cell(a) + '</td><td class="n">' + fe88_cell(b) + '</td><td class="n">' + fe88_cell(c) + "</td></tr>"; };
  var keyTbl = '<table class="fe88-tbl"><thead><tr><th scope="col">Figure</th><th scope="col" class="n">Last 12 months</th><th scope="col" class="n">Prior 12 months</th><th scope="col" class="n">Latest quarter</th></tr></thead><tbody>' +
    row("Capital spending", t.capex, tp.capex, q.capex) + row("Operating cash flow", t.ocf, tp.ocf, q.ocf) + row("Free cash flow", t.fcf, fcfPrior, q.fcf) +
    row("Revenue", t.revenue, tp.revenue, q.revenue) + row("Operating income", t.operating_income, tp.operating_income, q.operating_income) +
    row("New long-term borrowing", t.debt_issuance, tp.debt_issuance, q.debt_issuance) + row("Interest expense", t.interest_expense, tp.interest_expense, q.interest_expense) +
    "</tbody></table>";
  var rr = function (k, v) { return '<tr><th scope="row">' + k + '</th><td class="n">' + (v ? fe88_esc(v) : "Not disclosed") + "</td></tr>"; };
  var ratioTbl = '<table class="fe88-tbl"><tbody>' +
    rr("Sustainability gap (capital spending growth minus cash flow growth)", m.sustainability_gap_pp != null ? fe88_num(m.sustainability_gap_pp) + " points" : "") +
    rr("Free cash flow as a share of capital spending", m.fcf_coverage_of_capex != null ? Math.round(Number(m.fcf_coverage_of_capex) * 100) + "%" : "") +
    rr("Capital spending as a share of operating cash flow", fe88_p1(m.capex_pct_ocf)) +
    rr("New borrowing as a share of capital spending", fe88_p1(m.debt_issuance_pct_capex)) +
    rr("Interest as a share of operating income", fe88_p1(m.interest_pct_opinc)) +
    rr("Revenue growth, last 12 months", fe88_gr(m.rev_growth_ttm)) +
    rr("Operating income growth, last 12 months", fe88_gr(m.opinc_growth_ttm)) +
    "</tbody></table>";
  var disc = inst.disclosures || {};
  var dis = [];
  if (disc.customer_concentration && disc.customer_concentration.summary) dis.push("<p><strong>Customer concentration.</strong> " + fe88_esc(disc.customer_concentration.summary) + (disc.customer_concentration.section ? ' <span class="c93-src">(' + fe88_esc(disc.customer_concentration.section) + ")</span>" : "") + "</p>");
  if (Array.isArray(disc.power_and_data_centre_commitments) && disc.power_and_data_centre_commitments.length) {
    dis.push("<p><strong>Power and data centre commitments.</strong></p><ul>" + disc.power_and_data_centre_commitments.map(function (c) {
      return "<li>" + fe88_esc(c.item || "Commitment") + (c.usd_bn != null && isFinite(Number(c.usd_bn)) ? ": " + fe88_esc(fe88_bn(Number(c.usd_bn) * 1e9)) : "") + (c.section ? ' <span class="c93-src">(' + fe88_esc(c.section) + ")</span>" : "") + "</li>";
    }).join("") + "</ul>");
  }
  if (Array.isArray(disc.other) && disc.other.length) {
    dis.push("<ul>" + disc.other.map(function (c) { return "<li>" + fe88_esc(typeof c === "string" ? c : (c.item || c.summary || "")) + (c && c.section ? ' <span class="c93-src">(' + fe88_esc(c.section) + ")</span>" : "") + "</li>"; }).join("") + "</ul>");
  }
  var srcList = [];
  if (href) srcList.push('<li><a href="' + fe88_esc(href) + '" rel="noopener noreferrer">SEC ' + fe88_esc(filing.form || "filing") + (filing.latest_filed ? ", filed " + fe88_esc(fe88_ukDate(filing.latest_filed)) : "") + "</a></li>");
  if (filing.source_api && /^https:\/\/data\.sec\.gov\//.test(filing.source_api)) srcList.push('<li><a href="' + fe88_esc(filing.source_api) + '" rel="noopener noreferrer">' + fe88_esc(filing.source || "SEC company facts") + "</a></li>");
  else if (filing.source) srcList.push("<li>" + fe88_esc(filing.source) + "</li>");
  var pager = "";
  if (neighbors && (neighbors.prev || neighbors.next)) {
    pager = '<nav class="fe88-pager" aria-label="Adjacent companies">';
    if (neighbors.prev) pager += '<a href="' + FE88_BASE + "/" + neighbors.prev + '">Previous: ' + fe88_esc(neighbors.prev) + "</a>";
    if (neighbors.next) pager += '<a href="' + FE88_BASE + "/" + neighbors.next + '">Next: ' + fe88_esc(neighbors.next) + "</a>";
    pager += "</nav>";
  }
  var summary = fe88_plain(fe88_summary(inst));
  if (summary) summary = summary.charAt(0).toUpperCase() + summary.slice(1);
  var body = '<p class="fe88-back"><a href="' + FE88_BASE + '">Back to the radar</a></p>' +
    (facts.length ? '<p class="fe88-facts">' + fe88_esc(facts.join(" · ")) + "</p>" : "") +
    (summary ? '<p class="fe88-summary">' + fe88_esc(summary) + "</p>" : "") +
    figs + srcLine +
    "<section><h2>Five filing flags</h2><p>Overall: " + fe88_word(flag.overall) + "</p><ul class=\"fe88-flags\">" + flagHtml + "</ul></section>" +
    "<section><h2>What changed since last quarter</h2>" + changed + "</section>" +
    "<section><h2>Key numbers</h2>" + keyTbl + srcLine + "</section>" +
    "<section><h2>Ratios behind the flags</h2>" + ratioTbl + "</section>" +
    (dis.length ? "<section><h2>What the filing discloses</h2>" + dis.join("") + "</section>" : "") +
    "<section><h2>Share price</h2>" + fe88_marketBlock(inst.market) + "</section>" +
    "<section><h2>Sources</h2>" + (srcList.length ? "<ul>" + srcList.join("") + "</ul>" : "<p>" + fe88_esc(fe88_filingStamp(payload && payload.as_of && payload.as_of.filings)) + "</p>") + "</section>" +
    pager +
    '<section class="fe88-read"><h2>How to read the flags</h2>' + fe88_glossary() + "</section>";
  var lede = co ? co + (group ? " · " + group : "") : "";
  return fe88_shell("company", title, lede, fe88_stamps(payload).replace(/(\d{4}-\d{2}-\d{2})/g, function (d) { return fe88_ukDate(d); }), body);
}
