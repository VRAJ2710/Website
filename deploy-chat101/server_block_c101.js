
// ── chat101 ──
// chat101: claim checker (/tools/verify/), ISA and SIPP gold planner (/tools/isa-sipp/), Fed and Bank of England
// statement tracker (/central-banks/), gold scenario simulator (/tools/scenario/), filing change detector
// (/research/filing-changes/), installable app (manifest, icons, /sw.js, /offline/), source inspector on the signed-in
// app's gold and brief views, and "Vraj Patel" without ", London" (guard in the transform below).
// Free public sources only. No DDL: caches use dispatch_openbb_research_cache. Not investment advice. Capital at risk.
const C101_V = "chat101";
const C101_UA_WEB = "Mozilla/5.0 (compatible; TheDispatchMarket/1.0; +https://thedispatch.uk)";
function c101E(s) { return c93Esc(s == null ? "" : String(s)); }
function c101Num(s) { const n = Number(String(s == null ? "" : s).replace(/[^0-9.\-]/g, "")); return isFinite(n) && String(s).replace(/[^0-9]/g, "") !== "" ? n : NaN; }
async function c101Get(url, accept, ua, ms) {
  const r = await fetch(url, { headers: { "User-Agent": ua || C97_UA, Accept: accept || "*/*" }, signal: AbortSignal.timeout(ms || 15000), redirect: "follow" });
  if (!r.ok) throw new Error("http " + r.status);
  return await readTextCapped(r, 6 * 1024 * 1024);
}
function c101Unesc(s) {
  const M = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " ", rsquo: "\u2019", lsquo: "\u2018", ldquo: "\u201c", rdquo: "\u201d", ndash: "\u2013", mdash: "\u2014", hellip: "\u2026", middot: "\u00b7", pound: "\u00a3", euro: "\u20ac", reg: "\u00ae", trade: "\u2122", sect: "\u00a7", bull: "\u2022", ensp: " ", emsp: " ", thinsp: " ", frac14: "\u00bc", frac12: "\u00bd", frac34: "\u00be" };
  return String(s).replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi, (m, c) => {
    if (c[0] === "#") { const n = c[1] === "x" || c[1] === "X" ? parseInt(c.slice(2), 16) : parseInt(c.slice(1), 10); return n > 0 && n < 0x110000 ? (n === 160 ? " " : String.fromCodePoint(n)) : " "; }
    const v = M[c.toLowerCase()]; return v != null ? v : m;
  });
}
function c101Text(html) {
  let s = String(html || "");
  s = s.replace(/<head[\s>][\s\S]*?<\/head>/i, " ").replace(/<ix:header[\s\S]*?<\/ix:header>/gi, " ").replace(/<(script|style|noscript|svg)[^>]*>[\s\S]*?<\/\1>/gi, " ").replace(/<!--[\s\S]*?-->/g, " ");
  s = s.replace(/<br\s*\/?>/gi, "\n").replace(/<\/?(p|div|tr|li|ul|ol|h[1-6]|table|section|article|header|footer|blockquote)\b[^>]*>/gi, "\n").replace(/<\/t[dh]>/gi, " ");
  s = s.replace(/<[^>]+>/g, " ");
  s = c101Unesc(s);
  return s.replace(/[ \t\r\f\v\u00a0\u200b\u2009\u202f]+/g, " ").replace(/ *\n */g, "\n").replace(/\n{2,}/g, "\n").trim();
}
// ── word-level diff (longest common subsequence) ──
function c101Lcs(a, b) {
  const n = a.length, m = b.length, ops = [];
  let pre = 0; while (pre < n && pre < m && a[pre] === b[pre]) pre++;
  let suf = 0; while (suf < n - pre && suf < m - pre && a[n - 1 - suf] === b[m - 1 - suf]) suf++;
  for (let i = 0; i < pre; i++) ops.push(["=", a[i]]);
  const A = a.slice(pre, n - suf), B = b.slice(pre, m - suf), N = A.length, M = B.length;
  if (N * M > 6e6 || N > 65000 || M > 65000) { A.forEach(w => ops.push(["-", w])); B.forEach(w => ops.push(["+", w])); }
  else {
    const W = M + 1, dp = new Uint16Array((N + 1) * W);
    for (let i = N - 1; i >= 0; i--) for (let j = M - 1; j >= 0; j--) dp[i * W + j] = A[i] === B[j] ? dp[(i + 1) * W + j + 1] + 1 : Math.max(dp[(i + 1) * W + j], dp[i * W + j + 1]);
    let i = 0, j = 0;
    while (i < N && j < M) { if (A[i] === B[j]) { ops.push(["=", A[i]]); i++; j++; } else if (dp[(i + 1) * W + j] >= dp[i * W + j + 1]) { ops.push(["-", A[i]]); i++; } else { ops.push(["+", B[j]]); j++; } }
    while (i < N) ops.push(["-", A[i++]]); while (j < M) ops.push(["+", B[j++]]);
  }
  for (let i = m - suf; i < m; i++) ops.push(["=", b[i]]);
  return ops;
}
const C101_PARA = "\u00b6";
function c101Redline(ops) {
  let out = "", cur = null, buf = [];
  const flush = () => {
    if (!buf.length) return;
    if (cur === "=") out += buf.map(w => w === C101_PARA ? "</p><p>" : c101E(w)).join(" ").replace(/ ?<\/p><p> ?/g, "</p><p>");
    else { const t = c101E(buf.filter(w => w !== C101_PARA).join(" ")); if (t) out += cur === "-" ? `<del><span class="c101sr">[removed: </span>${t}<span class="c101sr">]</span></del>` : `<ins><span class="c101sr">[added: </span>${t}<span class="c101sr">]</span></ins>`; }
    out += " "; buf = [];
  };
  ops.forEach(o => { if (o[0] !== cur) { flush(); cur = o[0]; } buf.push(o[1]); }); flush();
  return "<p>" + out.trim().replace(/<p>\s*<\/p>/g, "") + "</p>";
}
function c101DiffStats(ops) { let add = 0, del = 0, same = 0; ops.forEach(o => { if (o[1] === C101_PARA) return; if (o[0] === "+") add++; else if (o[0] === "-") del++; else same++; }); return { add, del, same }; }
function c101Tok(paras) { const w = []; paras.forEach((p, i) => { if (i) w.push(C101_PARA); String(p).split(/\s+/).filter(Boolean).forEach(x => w.push(x)); }); return w.slice(0, 6000); }
// ── Fed FOMC and Bank of England MPC: statement redline and tone ──
const C101_FOMC = ["2025-12-10"].concat(C97_FOMC);
const C101_MPC = ["2025-12-18"].concat(C97_MPC);
const C101_MONTH = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"];
// Tone lexicon, shown in full on the page. Longer phrases are counted first, so "less restrictive" is not also "restrictive".
const C101_HAWK = ["raise", "raised", "raising", "increase bank rate", "increase the target range", "tighten", "tightened", "tightening", "firming", "elevated", "upside", "persistent", "persistence", "persist", "second-round", "restrictive", "vigilant", "robust", "strong", "stronger", "resilient", "inflationary pressures", "above target", "higher energy prices", "lean against"];
const C101_DOVE = ["lower", "lowered", "lowering", "reduce bank rate", "cut", "cuts", "easing", "eased", "downside", "weak", "weaker", "weakness", "weakening", "soft", "softer", "softening", "slowed", "slowing", "moderated", "moderating", "moderation", "subdued", "disinflation", "loosening", "less restrictive", "accommodative", "slack", "declined", "moved up"];
function c101Tone(text) {
  let t = " " + String(text || "").toLowerCase().replace(/[\u2019']/g, "'").replace(/[\u2010-\u2013]/g, "-") + " ";
  const all = C101_HAWK.map(w => [w, "h"]).concat(C101_DOVE.map(w => [w, "d"])).sort((a, b) => b[0].length - a[0].length);
  const hits = { h: [], d: [] };
  all.forEach(([w, side]) => {
    const re = new RegExp("(?<![a-z-])" + w.replace(/[-]/g, "\\-").replace(/ /g, "\\s+") + "(?![a-z])", "g");
    let n = 0; t = t.replace(re, () => { n++; return " \u2588 "; });
    if (n) hits[side].push([w, n]);
  });
  const H = hits.h.reduce((s, x) => s + x[1], 0), D = hits.d.reduce((s, x) => s + x[1], 0);
  const score = H + D ? Math.round((H - D) / (H + D) * 100) : 0;
  return { score, hawk: H, dove: D, hawkTerms: hits.h.sort((a, b) => b[1] - a[1]), doveTerms: hits.d.sort((a, b) => b[1] - a[1]), label: score >= 20 ? "Leans hawkish" : score <= -20 ? "Leans dovish" : "Balanced" };
}
function c101Frac(s) { const m = /^(\d+)(?:-(\d+)\/(\d+))?$|^(\d+)\/(\d+)$/.exec(String(s).trim()); if (!m) return Number(s); if (m[4]) return Number(m[4]) / Number(m[5]); return Number(m[1]) + (m[2] ? Number(m[2]) / Number(m[3]) : 0); }
function c101FedUrl(d) { return "https://www.federalreserve.gov/newsevents/pressreleases/monetary" + d.replace(/-/g, "") + "a.htm"; }
function c101BoeUrl(d) { const y = d.slice(0, 4), mo = C101_MONTH[Number(d.slice(5, 7)) - 1]; return "https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes/" + y + "/" + mo + "-" + y; }
function c101FedParse(html) {
  const L = c101Text(html).split("\n").map(s => s.trim()).filter(s => s && !/^(-->|Share|PDF)$/.test(s));
  let i = L.findIndex(l => /approved the following statement for release/i.test(l) || /^The Committee (seeks|decided)/i.test(l));
  if (i < 0) { const r = L.findIndex(l => /^For release at/i.test(l)); if (r >= 0) i = r + 1; }
  if (i < 0) return null;
  if (/approved the following statement/i.test(L[i])) i++;
  let j = L.findIndex((l, k) => k > i && /^(For media inquiries|Implementation Note|Last Update)/i.test(l)); if (j < 0) j = Math.min(L.length, i + 12);
  const paras = L.slice(i, j).filter(l => l.length > 20);
  const text = paras.join("\n");
  if (text.length < 300 || !/federal funds rate/i.test(text)) return null;
  const dm = /decided to (maintain|raise|lower) the target range for the federal funds rate(?: by [^,]*?)? (?:at|to) ([\d\-\/]+) to ([\d\-\/]+) percent/i.exec(text);
  const vm = /by a (\d+)\s*[\u2013\u2014-]\s*(\d+) vote/i.exec(L.join(" "));
  const against = paras.find(l => /^Voting against/i.test(l)) || "";
  return { paras, text, action: dm ? dm[1].toLowerCase() : "", lo: dm ? c101Frac(dm[2]) : null, hi: dm ? c101Frac(dm[3]) : null, rateText: dm ? dm[2] + " to " + dm[3] + " percent" : "", vote: vm ? vm[1] + "\u2013" + vm[2] : against ? "" : "unanimous", against };
}
function c101BoeParse(html) {
  const L = c101Text(html).split("\n").map(s => s.trim()).filter(Boolean);
  let i = L.findIndex((l, k) => /^Monetary Policy Summary, [A-Z][a-z]+ \d{4}$/.test(l) && /^At its meeting/i.test(L[k + 1] || ""));
  if (i < 0) return null;
  let j = L.findIndex((l, k) => k > i && /^(Minutes of the Monetary Policy Committee|Monetary Policy Committee meeting|Other publications|Footnotes)/i.test(l)); if (j < 0) j = Math.min(L.length, i + 12);
  const paras = L.slice(i + 1, j).filter(l => l.length > 20);
  const text = paras.join("\n");
  if (text.length < 300 || !/Bank Rate/.test(text)) return null;
  const m = /voted (?:by a majority of (\d+)\s*[\u2013\u2014-]\s*(\d+)|unanimously) to (maintain|reduce|increase|cut|raise) Bank Rate(?: by [\d.]+ percentage points?)?,? (?:at|to) ([\d.]+)%/i.exec(text);
  const against = (/(?:One|Two|Three|Four|Five) members? (?:voted|preferred) [^\n]*?\.(?=\s+[A-Z][a-z]|\s*$)/m.exec(text) || [""])[0];
  return { paras, text, action: m ? m[3].toLowerCase() : "", rate: m ? Number(m[4]) : null, rateText: m ? m[4] + "%" : "", vote: m ? (m[1] ? m[1] + "\u2013" + m[2] : "unanimous") : "", against };
}
function c101Past(list, cutUtc, now) { return list.filter(d => Date.parse(d + "T" + cutUtc + "Z") <= now); }
async function c101Cb(bank) {
  return c97Cached("c101:cb:" + bank, 12 * 3600e3, async () => {
    const fed = bank === "fed", past = c101Past(fed ? C101_FOMC : C101_MPC, fed ? "19:30:00" : "12:30:00", Date.now());
    if (past.length < 2) throw new Error("no meetings");
    const urlOf = fed ? c101FedUrl : c101BoeUrl, parse = fed ? c101FedParse : c101BoeParse;
    const get = async d => { const u = urlOf(d); const h = await c101Get(u, "text/html,*/*", C101_UA_WEB, 15000); const p = parse(h); if (!p) throw new Error("layout"); p.date = d; p.url = u; p.tone = c101Tone(p.text); p.words = p.text.split(/\s+/).length; return p; };
    let latest, prev, k = past.length - 1;
    try { latest = await get(past[k]); } catch (e) { if (k < 2) throw e; k--; latest = await get(past[k]); latest.note = "The statement for " + c97DayLong(past[k + 1]) + " could not be read yet, so this compares the two before it."; }
    prev = await get(past[k - 1]);
    const ops = c101Lcs(c101Tok(prev.paras), c101Tok(latest.paras));
    const strip = p => { const o = Object.assign({}, p); delete o.paras; return o; };
    return { bank, latest: strip(latest), prev: strip(prev), redline: c101Redline(ops), stats: c101DiffStats(ops), at: Date.now() };
  }, 14000);
}
function c101ToneTerms(list) { return list.length ? list.map(x => c101E(x[0]) + (x[1] > 1 ? " \u00d7" + x[1] : "")).join(", ") : "none"; }
function c101CbCard(name, c, err) {
  if (!c) return `<section class="c101card"><h2>${c101E(name)}</h2><p class="note">We couldn't read the official statement pages just now${err ? " (" + c101E(err) + ")" : ""}. We'll try again on the next visit; meanwhile the statements are on the central bank's own site.</p></section>`;
  const L = c.latest, P = c.prev, fed = c.bank === "fed", T = L.tone, TP = P.tone, dT = T.score - TP.score;
  const dec = fed ? (L.action ? `Decision: <strong>${c101E(L.action)}</strong> the federal funds target range at <strong>${c101E(L.rateText)}</strong>.` : "") : (L.action ? `Decision: <strong>${c101E(L.action)}</strong> Bank Rate at <strong>${c101E(L.rateText)}</strong>.` : "");
  const pct = c.stats.same + c.stats.del ? Math.round((c.stats.add + c.stats.del) / (c.stats.same + c.stats.del + c.stats.add) * 100) : 0;
  return `<section class="c101card" id="${fed ? "fed" : "boe"}"><div class="kicker">${fed ? "US Federal Reserve \u00b7 FOMC" : "Bank of England \u00b7 MPC"}</div><h2>${c101E(name)}: ${c101E(c97DayLong(L.date))} against ${c101E(c97DayLong(P.date))}</h2>` +
    (L.note ? `<p class="note">${c101E(L.note)}</p>` : "") +
    `<p>${dec} Vote: <strong>${c101E(L.vote || "not stated")}</strong>.${L.against ? " " + c101E(L.against) : ""}</p>` +
    `<div class="c101kpis"><div><span>Tone score</span><strong data-c100 data-c100-name="${c101E(name)} tone score" data-c100-value="${T.score}" data-c100-src="The Dispatch Market word count of the official statement" data-c100-url="${c101E(L.url)}" data-c100-series="Hawkish minus dovish words, divided by all matched words, times 100" data-c100-at="${c101E(c97DayLong(L.date))}" data-c100-status="Model output from the official text, not a forecast" data-c100-formula="(hawkish words \u2212 dovish words) \u00f7 (hawkish + dovish words) \u00d7 100">${c97Sg(T.score, 0) || "0"}</strong><em>${c101E(T.label)}</em></div>` +
    `<div><span>Previous statement</span><strong>${c97Sg(TP.score, 0) || "0"}</strong><em>${c101E(TP.label)}</em></div><div><span>Shift in tone</span><strong>${c97Sg(dT, 0) || "0"}</strong><em>${dT > 0 ? "More hawkish" : dT < 0 ? "More dovish" : "No change"}</em></div>` +
    `<div><span>Words changed</span><strong>${pct}%</strong><em>${c.stats.add} added, ${c.stats.del} removed</em></div></div>` +
    `<p class="c101plain">In plain English: the ${fed ? "Fed" : "Bank of England"} ${L.action === "maintain" ? "held rates" : L.action ? (/raise|increase/.test(L.action) ? "raised rates" : "cut rates") : "set policy"} and its words ${dT >= 20 ? "turned noticeably more hawkish (more worried about inflation)" : dT <= -20 ? "turned noticeably more dovish (more worried about growth and jobs)" : dT > 0 ? "leaned a little more hawkish" : dT < 0 ? "leaned a little more dovish" : "kept the same tone"} ${dT === 0 ? "as" : "than"} last time. Higher rates or hawkish words tend to weigh on gold, which pays no interest; this is context, not a prediction.</p>` +
    `<details class="c101det"><summary>Words behind the score</summary><p><strong>Hawkish (${T.hawk}):</strong> ${c101ToneTerms(T.hawkTerms)}</p><p><strong>Dovish (${T.dove}):</strong> ${c101ToneTerms(T.doveTerms)}</p></details>` +
    `<h3>Redline: what changed in the words</h3><p class="note"><ins>Underlined green</ins> is new in ${c101E(c97DayLong(L.date))}; <del>struck-through red</del> was in ${c101E(c97DayLong(P.date))} and has gone.</p><div class="c101red">${c.redline}</div>` +
    `<p class="c97s">Source: <a href="${c101E(L.url)}" rel="noopener">${fed ? "Federal Reserve press release" : "Bank of England Monetary Policy Summary"}, ${c101E(c97DayLong(L.date))}</a> and <a href="${c101E(P.url)}" rel="noopener">${c101E(c97DayLong(P.date))}</a> \u00b7 official text, read ${c101E(c97UkWhen(c.at))}</p></section>`;
}
async function c101CbPage(req, res, user) {
  const [f, b] = await Promise.all([c101Cb("fed"), c101Cb("boe")]);
  const nextF = C97_FOMC.find(d => Date.parse(d + "T19:30:00Z") > Date.now()), nextB = C97_MPC.find(d => Date.parse(d + "T12:30:00Z") > Date.now());
  const body = `<style>${C97_CSS}${C101_CSS}</style><section><div class="kicker">Central banks \u00b7 statement tracker</div><h1>Fed and Bank of England: what changed in the words</h1><p class="dek">Each policy statement compared word by word with the one before, with a tone score you can check line by line.</p><p class="byline">${C93_EDITOR}</p>` +
    `<p class="note">Next decisions: Fed ${c101E(nextF ? c97DayLong(nextF) : "date to be set")}, Bank of England ${c101E(nextB ? c97DayLong(nextB) : "date to be set")}. Pages refresh twice a day.</p></section>` +
    c101CbCard("Federal Reserve", f.v, f.err) + c101CbCard("Bank of England", b.v, b.err) +
    `<section class="c101card"><h2>How the tone score works</h2><p>We count words and phrases that usually signal worry about inflation (hawkish) or about growth and jobs (dovish) in the official statement text. Score = (hawkish \u2212 dovish) \u00f7 (hawkish + dovish) \u00d7 100, so it runs from \u2212100 (all dovish) to +100 (all hawkish). From +20 up we say "leans hawkish"; from \u221220 down, "leans dovish"; in between, "balanced". Longer phrases are matched first, so "less restrictive" counts as dovish and not also as "restrictive".</p>` +
    `<p><strong>Hawkish list:</strong> ${c101E(C101_HAWK.join(", "))}.</p><p><strong>Dovish list:</strong> ${c101E(C101_DOVE.join(", "))}.</p><p class="note">Limits: a word count can't read context ("inflation is no longer elevated" still counts "elevated"), so read the redline itself. This is an educational gauge, not a forecast. ${C93_DISC}</p></section>`;
  return c93Html(req, res, c93Shell({ title: "Fed and Bank of England statement tracker | The Dispatch Market", path: "/central-banks/", desc: "The latest Fed and Bank of England policy statements compared word by word with the previous ones, with a transparent tone score.", user, body }), "private, max-age=60");
}
// ── "Verify this claim": rule parser first, AI (Gemini, then OpenAI) only to parse, never to supply figures ──
const C101_VM = [
  { k: "fed", re: /fed(?:eral)? funds|\bfomc\b|\bthe fed\b[^.]*\brates?\b|\bfed(?:'s)? (?:policy )?rates?\b|federal reserve[^.]*\brates?\b|\bus (?:policy |interest )?rates?\b/i, kind: "rate", name: "Fed funds target range" },
  { k: "boe", re: /\bbank rate\b|bank of england|\bboe\b|\bmpc\b|\buk (?:policy |interest |base )?rates?\b|\bbase rate\b/i, kind: "rate", name: "Bank of England Bank Rate" },
  { k: "ry", re: /real yields?|\btips\b|inflation[- ]protected|\bdfii10\b/i, kind: "rate" },
  { k: "tnx", re: /\b(?:10|ten)[- ]?(?:year|yr)\b|\b10y\b|treasury yield|\bbond yield/i, kind: "rate" },
  { k: "gold_gbp", re: /\bgold\b[^.]*?(?:\u00a3|\bgbp\b|\bpounds?\b|\bsterling\b)|(?:\u00a3|\bgbp\b|\bpounds?\b|\bsterling\b)[^.]*?\bgold\b/i, kind: "price" },
  { k: "silver", re: /\bsilver\b|\bxag\b/i, kind: "price" },
  { k: "gold_usd", re: /\bgold\b|\bxau\b|\bbullion\b/i, kind: "price" },
  { k: "dxy", re: /dollar index|\bdxy\b|\bdx-y\b/i, kind: "price" },
  { k: "brent", re: /\bbrent\b|\boil\b|\bcrude\b/i, kind: "price" },
  { k: "gbpusd", re: /\bgbp\s*\/?\s*usd\b|\bcable\b|\bthe pound\b|\bsterling\b|\bpound\b/i, kind: "price" },
  { k: "spx", re: /s\s*&\s*p(?:\s*500)?|\bspx\b|\bsp500\b/i, kind: "price" }
];
const C101_SECM = [
  ["fcf", /free cash flow/i], ["ocf", /operating cash flow|cash (?:flow )?from operations/i], ["capex", /\bcapex\b|capital (?:spending|expenditure)/i],
  ["op", /operating (?:income|profit)/i], ["ni", /net (?:income|profit|earnings)|\bprofit\b/i], ["eps", /earnings per share|\beps\b/i],
  ["rev", /\brevenues?\b|\bsales\b|\bturnover\b/i], ["debt", /\bdebt\b/i], ["eq", /(?:shareholders|stockholders)['\u2019]? equity/i], ["cash", /\bcash\b/i]
];
const C101_WORDS = ["fed", "boe", "ry", "tnx", "gold_gbp", "silver", "gold_usd", "dxy", "brent", "gbpusd", "spx"].concat(C101_SECM.map(x => x[0]));
const C101_VLIM = new FixedWindowRateLimiter({ limit: 30, windowMs: 10 * 60e3, maxKeys: 5000 });
const C101_AILIM = new FixedWindowRateLimiter({ limit: 6, windowMs: 10 * 60e3, maxKeys: 5000 });
const C101_AIDAY = { d: "", n: 0, cap: 300 };
function c101Nums(q) {
  const out = [], re = /([$\u00a3\u20ac])?\s?(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)(?:\s?(trillion|tn|billion|bn|million|mn|m|thousand|k|%|percent|per cent|pc|bps|bp|basis points)\b|(%))?/gi;
  let m;
  while ((m = re.exec(q))) {
    const raw = m[0].trim(), unitW = String(m[3] || m[4] || "").toLowerCase(); let v = Number(m[2].replace(/,/g, ""));
    if (!isFinite(v)) continue;
    const isYear = !m[1] && !unitW && /^(19|20)\d{2}$/.test(m[2]);
    const mult = /^(trillion|tn)$/.test(unitW) ? 1e12 : /^(billion|bn)$/.test(unitW) ? 1e9 : /^(million|mn|m)$/.test(unitW) ? 1e6 : /^(thousand|k)$/.test(unitW) ? 1e3 : 1;
    const pct = /^(%|percent|per cent|pc)$/.test(unitW), bp = /^(bps|bp|basis points)$/.test(unitW);
    out.push({ raw, n: v, v: bp ? v / 100 : v * mult, cur: m[1] || "", pct, bp, year: isYear, scaled: mult !== 1 });
  }
  return out;
}
function c101Cmp(q) {
  if (/\b(above|over|more than|higher than|greater than|exceeds?|exceeding|at least|north of|tops?|topped)\b/i.test(q)) return ">";
  if (/\b(below|under|less than|lower than|beneath|at most|south of)\b/i.test(q)) return "<";
  return "=";
}
function c101Dir(q) {
  if (/\b(rose|risen|rises|rising|up|gained|gains|climbed|climbs|higher|increased|jumped|rallied|surged|advanced)\b/i.test(q)) return "up";
  if (/\b(fell|fallen|falls|falling|down|lost|dropped|drops|lower|declined|slid|slumped|sank|tumbled|decreased)\b/i.test(q)) return "down";
  return "";
}
function c101Rules(q) {
  const s = String(q || "");
  const nums = c101Nums(s).filter(x => !x.year), years = c101Nums(s).filter(x => x.year).map(x => x.n);
  const sec = C101_SECM.find(x => x[1].test(s));
  const mk = C101_VM.find(x => x.re.test(s));
  return { nums, years, sec: sec ? sec[0] : "", metric: mk ? mk.k : "", cmp: c101Cmp(s), dir: c101Dir(s) };
}
let C101_NAMES = null;
function c101NameMap(tk) {
  if (C101_NAMES && C101_NAMES.at === tk.at) return C101_NAMES.m;
  const m = new Map();
  tk.rows.forEach(r => { const core = String(r[2] || "").toLowerCase().replace(/[\u2010-\u2013-]/g, " ").replace(/[.,&']/g, " ").replace(/\b(inc|corp|corporation|co|company|plc|ltd|limited|holdings?|group|sa|nv|ag|the|class [a-c]|com|incorporated)\b/g, " ").replace(/\s+/g, " ").trim(); if (core.length >= 3 && !m.has(core)) m.set(core, r[0]); });
  C101_NAMES = { at: tk.at, m }; return m;
}
function c101Lc1(x) { x = String(x || ""); return /^[A-Z][a-z]/.test(x) ? x.charAt(0).toLowerCase() + x.slice(1) : x; }
async function c101FindCo(q) {
  const tk = await c99Tickers(false); if (!tk) return null;
  const cash = /\$([A-Z]{1,5})\b/.exec(q); if (cash && c99Find(tk, cash[1])) return cash[1];
  const caps = (String(q).match(/\b[A-Z]{2,5}\b/g) || []).filter(t => !/^(US|UK|USD|GBP|EUR|EPS|FCF|CEO|SEC|FED|BOE|MPC|GDP|CPI|DXY|ETF|AI|IPO|ISA|SIPP|OK|Q[1-4]|FY|TTM|YOY|LSE|FOMC|S|P)$/.test(t));
  for (const t of caps) if (c99Find(tk, t)) return t;
  const m = c101NameMap(tk), w = String(q).toLowerCase().replace(/[\u2010-\u2013-]/g, " ").replace(/[^a-z0-9 ]/g, " ").split(/\s+/).filter(Boolean);
  for (let n = 3; n >= 1; n--) for (let i = 0; i + n <= w.length; i++) { const g = w.slice(i, i + n).join(" "); if (g.length >= 4 && m.has(g)) return m.get(g); }
  return null;
}
async function c101AiParse(q, nums, req) {
  const day = c97UkIso(Date.now()); if (C101_AIDAY.d !== day) { C101_AIDAY.d = day; C101_AIDAY.n = 0; }
  if (C101_AIDAY.n >= C101_AIDAY.cap || !C101_AILIM.allow(bb12cClientKey(req))) return null;
  C101_AIDAY.n++;
  const system = "You turn one market claim into JSON. Reply with JSON only, no prose: {\"metric\": one of " + JSON.stringify(C101_WORDS) + " or null, \"comparator\": \"=\" or \">\" or \"<\", \"value\": a number copied from the claim or null, \"ticker\": a US stock ticker named in the claim or null, \"year\": a year written in the claim or null}. Never add or change numbers. If unsure, use null.";
  try {
    const r = await bb3bGenerateAi({ system, messages: [{ role: "user", content: String(q).slice(0, 300) }], maxTokens: 120, temperature: 0, validate: t => {
      const m = /\{[\s\S]*\}/.exec(String(t || "")); if (!m) throw new Error("no json");
      const j = JSON.parse(m[0]);
      if (j.metric != null && C101_WORDS.indexOf(j.metric) < 0) throw new Error("metric");
      if (j.value != null && !nums.some(x => Math.abs(x.n - Number(j.value)) < 1e-9 || Math.abs(x.v - Number(j.value)) < 1e-6 * Math.max(1, Math.abs(x.v)))) throw new Error("value not in claim");
      if (j.ticker != null && !new RegExp("\\b" + String(j.ticker).replace(/[^A-Za-z.]/g, "") + "\\b", "i").test(q)) throw new Error("ticker not in claim");
      if (j.comparator != null && ["=", ">", "<"].indexOf(j.comparator) < 0) throw new Error("cmp");
      return j;
    } });
    const t = r && (r.validated || r.text); const j = typeof t === "object" && t ? t : JSON.parse(/\{[\s\S]*\}/.exec(String(t))[0]);
    return j && (j.metric || j.ticker) ? j : null;
  } catch (e) { return null; }
}
function c101Within(claim, actual, kind) { return kind === "rate" ? Math.abs(claim - actual) <= 0.10 + 1e-9 : Math.abs(claim - actual) <= Math.abs(actual) * 0.015; }
function c101Out(verdict, o) {
  const L = { supported: "Supported", not_supported: "Not supported", cant_verify: "Can't verify" };
  return Object.assign({ verdict, label: L[verdict], checkedUk: c97UkWhen(Date.now()), note: "Information only. Not investment advice. Capital at risk." }, o);
}
async function c101Verify(q, req, user) {
  q = String(q || "").replace(/\s+/g, " ").trim().slice(0, 300);
  if (q.length < 6) return c101Out("cant_verify", { claim: q, reasoning: "Type a claim with a figure in it, for example \u201cGold is above $4,000\u201d." });
  const R = c101Rules(q);
  let parser = "rules", metric = R.metric, sec = R.sec, cmp = R.cmp, nums = R.nums, year = R.years[0] || null, ticker = null;
  if (sec) ticker = await c101FindCo(q).catch(() => null);
  const needAi = !(ticker && sec) && !metric || (!nums.length && !R.dir);
  if (needAi) {
    const j = await c101AiParse(q, c101Nums(q), req);
    if (j) { parser = "ai"; if (j.metric && C101_SECM.some(x => x[0] === j.metric)) { sec = j.metric; ticker = j.ticker ? String(j.ticker).toUpperCase() : ticker; } else if (j.metric) metric = j.metric; if (j.comparator) cmp = j.comparator; if (j.value != null) nums = c101Nums(q).filter(x => Math.abs(x.n - Number(j.value)) < 1e-9 || Math.abs(x.v - Number(j.value)) < 1e-6 * Math.max(1, Math.abs(x.v))); if (j.year) year = Number(j.year); }
  }
  const base = { claim: q, parser: parser === "ai" ? "Read with AI (Gemini, then OpenAI as backup); the figures come only from our data" : "Read with fixed rules; no AI used" };
  // Company figures from SEC filings
  if (sec && ticker) {
    const dd = await c99Deep(ticker, false).catch(() => null);
    if (!dd) return c101Out("cant_verify", Object.assign(base, { reasoning: `We haven't downloaded ${ticker}'s SEC filings yet, so we can't check this. Open its filings page to fetch them (free for signed-in readers), then check again.`, link: "/research/sec/" + ticker + "/" }));
    const met = dd.metrics && dd.metrics[sec];
    const rows = met && Array.isArray(met.rows) ? met.rows.filter(r => isFinite(Number(r.val))) : [];
    if (!rows.length) return c101Out("cant_verify", Object.assign(base, { reasoning: `${dd.name || ticker}'s filings don't report ${met ? met.label.toLowerCase() : "that measure"} in a form we can read.`, link: "/research/sec/" + ticker + "/" }));
    const row = year ? rows.find(r => String(r.end).slice(0, 4) === String(year)) : rows[rows.length - 1];
    if (!row) return c101Out("cant_verify", Object.assign(base, { reasoning: `We have ${dd.name || ticker}'s annual figures for ${rows.map(r => String(r.end).slice(0, 4)).join(", ")}, but not for ${year}.`, link: "/research/sec/" + ticker + "/" }));
    const n = nums.filter(x => sec === "eps" ? !x.scaled : (x.scaled || x.cur || x.v >= 1e5))[0] || nums[0];
    const val = Number(row.val), shown = sec === "eps" ? "$" + c97N(val, 2) : c99Money(val);
    const reading = { name: (met.label || sec) + " \u00b7 " + (dd.name || ticker), value: shown, source: "SEC EDGAR, " + (row.form || "10-K") + " filed " + c97DayLong(row.filed || ""), sourceUrl: "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=" + dd.cik + "&type=10-K", asOf: "Fiscal year ending " + c97DayLong(row.end), status: "As filed" };
    if (!n) return c101Out("cant_verify", Object.assign(base, { reading, reasoning: "The claim has no figure to compare. Our figure is shown for reference." }));
    const claimV = n.v, tol = Math.abs(val) * 0.02;
    const ok = cmp === ">" ? val > claimV : cmp === "<" ? val < claimV : Math.abs(val - claimV) <= tol;
    return c101Out(ok ? "supported" : "not_supported", Object.assign(base, { reading, tolerance: cmp === "=" ? "within 2%" : "", reasoning: `${dd.name || ticker} reported ${(met.label || "").toLowerCase()} of ${shown} for the fiscal year ending ${c97DayLong(row.end)}. The claim says ${cmp === ">" ? "more than " : cmp === "<" ? "less than " : ""}${n.raw}. ${ok ? "That matches" + (cmp === "=" ? " within 2%" : "") + "." : "That doesn't match" + (cmp === "=" ? ": it is more than 2% away" : "") + "."}${year ? "" : " No year was given, so we used the latest annual filing."}` }));
  }
  if (sec && !ticker && !(await c99Tickers(false).catch(() => null))) return c101Out("cant_verify", Object.assign(base, { reasoning: "Our list of US-listed companies isn't loaded yet, so we can't match the company. It loads when anyone opens a company page under Research; try again after that, or open the company's figures at /research/." }));
  if (sec && !ticker) return c101Out("cant_verify", Object.assign(base, { reasoning: "We couldn't tell which company the claim is about. Use its US ticker, for example \u201cAAPL revenue was $391bn in 2024\u201d." }));
  if (!metric) return c101Out("cant_verify", Object.assign(base, { reasoning: "We couldn't match this to a figure we track. We can check gold, silver, gold in pounds, the dollar index, the US 10-year and real yields, Brent oil, the pound, the S&P 500, the Fed and Bank of England rates, and company figures from SEC filings." }));
  if (/\b(yesterday|last (?:week|month|year|quarter)|ago|record|all[- ]time|ever|since|peak|52[- ]week|year[- ]to[- ]date|ytd|in (?:19|20)\d{2}|on \d{1,2} [a-z]+|will|going to|next (?:week|month|year)|by (?:the )?end|forecast|expected to)\b/i.test(q))
    return c101Out("cant_verify", Object.assign(base, { reasoning: /\b(will|going to|next|by (?:the )?end|forecast|expected to)\b/i.test(q) ? "This is about the future. We can only check claims against figures published now." : "This is about a past date or a record. We check claims against the latest readings only, so we can't confirm or rule it out." }));
  // Policy rates
  if (metric === "fed" || metric === "boe") {
    const fed = metric === "fed", c = (await c101Cb(fed ? "fed" : "boe")).v;
    let lo, hi, reading;
    if (fed) { if (!c || c.latest.lo == null) return c101Out("cant_verify", Object.assign(base, { reasoning: "We couldn't read the latest Fed statement just now. Try again later." })); lo = c.latest.lo; hi = c.latest.hi; reading = { name: "Fed funds target range", value: c97N(lo, 2) + "% to " + c97N(hi, 2) + "%", source: "Federal Reserve FOMC statement", sourceUrl: c.latest.url, asOf: "Decision of " + c97DayLong(c.latest.date), status: "Official" }; }
    else {
      const b = await c97Boe().catch(() => null), rows = b && b.v; const last = rows && rows[rows.length - 1];
      if (last) { lo = hi = last[1]; reading = { name: "Bank of England Bank Rate", value: c97N(last[1], 2) + "%", source: "Bank of England database (series IUDBEDR)", sourceUrl: "https://www.bankofengland.co.uk/boeapps/database/Bank-Rate.asp", asOf: "Rate in force on " + c97DayLong(last[0]), status: "Official" }; }
      else if (c && c.latest.rate != null) { lo = hi = c.latest.rate; reading = { name: "Bank of England Bank Rate", value: c97N(lo, 2) + "%", source: "Bank of England Monetary Policy Summary", sourceUrl: c.latest.url, asOf: "Decision of " + c97DayLong(c.latest.date), status: "Official" }; }
      else return c101Out("cant_verify", Object.assign(base, { reasoning: "We couldn't read Bank Rate from the Bank of England just now. Try again later." }));
    }
    const ps = nums.filter(x => x.pct || x.v < 20);
    if (!ps.length) return c101Out("cant_verify", Object.assign(base, { reading, reasoning: "The claim has no rate to compare. Our figure is shown for reference." }));
    let ok, what;
    if (ps.length >= 2 && cmp === "=") { const a = Math.min(ps[0].v, ps[1].v), z = Math.max(ps[0].v, ps[1].v); ok = Math.abs(a - lo) <= 0.1 && Math.abs(z - hi) <= 0.1; what = ps[0].raw + " to " + ps[1].raw; }
    else { const v = ps[0].v; what = ps[0].raw; ok = cmp === ">" ? lo > v : cmp === "<" ? hi < v : (v >= lo - 0.1 && v <= hi + 0.1); }
    return c101Out(ok ? "supported" : "not_supported", Object.assign(base, { reading, tolerance: "within 0.10 percentage points", reasoning: `The ${reading.name} is ${reading.value} (${c101Lc1(reading.asOf)}). The claim says ${cmp === ">" ? "above " : cmp === "<" ? "below " : ""}${what}. ${ok ? "That matches." : "That doesn't match."}` }));
  }
  // Market readings
  const mac = await c100Macro().catch(() => null), row = mac && mac.rows.find(r => r.key === metric);
  if (!row) return c101Out("cant_verify", Object.assign(base, { reasoning: "Our feed for that figure didn't answer just now, so we can't check it. Try again in a few minutes." }));
  const kind = (C101_VM.find(x => x.k === metric) || {}).kind, actual = c101Num(row.value);
  const reading = { name: row.name, value: row.value, change: row.change, source: row.source, sourceUrl: row.sourceUrl, asOf: row.asOf, status: row.status };
  if (!isFinite(actual)) return c101Out("cant_verify", Object.assign(base, { reading, reasoning: "Our latest reading isn't a number we can compare." }));
  const lvl = nums.filter(x => !(x.pct && kind !== "rate") && !x.bp);
  const chg = nums.filter(x => x.pct && kind !== "rate" || x.bp);
  if (R.dir && cmp === "=" && !lvl.length) {
    const ch = c101Num(row.change); if (!isFinite(ch)) return c101Out("cant_verify", Object.assign(base, { reading, reasoning: "We don't have the change since the previous close for this figure right now." }));
    const sameSign = R.dir === "up" ? ch > 0 : ch < 0, cv = chg[0];
    const ok = sameSign && (!cv || Math.abs(Math.abs(ch) - cv.v) <= (cv.bp ? 0.05 : 0.5));
    return c101Out(ok ? "supported" : "not_supported", Object.assign(base, { reading, tolerance: cv ? (cv.bp ? "within 5 basis points" : "within 0.5 percentage points") : "", reasoning: `${row.name} is ${row.value}, ${row.change} since the previous close. The claim says it is ${R.dir}${cv ? " " + cv.raw : ""}. ${ok ? "That matches." : "That doesn't match."} We compare with the previous close only.` }));
  }
  const n = lvl[0];
  if (!n) return c101Out("cant_verify", Object.assign(base, { reading, reasoning: "The claim has no level to compare. Our latest reading is shown for reference." }));
  const ok = cmp === ">" ? actual > n.v : cmp === "<" ? actual < n.v : c101Within(n.v, actual, kind);
  return c101Out(ok ? "supported" : "not_supported", Object.assign(base, { reading, tolerance: cmp === "=" ? (kind === "rate" ? "within 0.10 percentage points" : "within 1.5%") : "", reasoning: `${row.name} is ${row.value} (${String(row.asOf || "").replace(/^Delayed \u00b7 /, "delayed, ")}). The claim says ${cmp === ">" ? "above " : cmp === "<" ? "below " : ""}${n.raw}. ${ok ? "That matches" + (cmp === "=" ? (kind === "rate" ? " within 0.10 percentage points" : " within 1.5%") : "") + "." : "That doesn't match" + (cmp === "=" ? (kind === "rate" ? ": it is more than 0.10 percentage points away" : ": it is more than 1.5% away") : "") + "."}` }));
}
function c101VerdictHtml(v) {
  const cls = v.verdict === "supported" ? "ok" : v.verdict === "not_supported" ? "no" : "cv";
  const r = v.reading;
  return `<section class="c101card c101v ${cls}" aria-live="polite"><div class="c101badge ${cls}">${c101E(v.label)}</div><p class="c101claim">\u201c${c101E(v.claim)}\u201d</p><p>${c101E(v.reasoning)}${v.link ? ` <a href="${c101E(v.link)}">Open the filings page</a>.` : ""}</p>` +
    (r ? `<table class="c97t c97r"><thead><tr><th scope="col">Measure</th><th scope="col">Our reading</th><th scope="col">Change</th><th scope="col">Source and time</th></tr></thead><tbody><tr><td><strong>${c101E(r.name)}</strong></td><td class="v">${c101E(r.value)}</td><td>${c101E(r.change || "")}</td><td><span class="c97s">${r.sourceUrl ? `<a href="${c101E(r.sourceUrl)}" rel="noopener">${c101E(r.source)}</a>` : c101E(r.source)}</span><span class="c97s">${c101E(r.asOf || "")}${r.status && !/delayed/i.test(r.asOf || "") ? " \u00b7 " + c101E(r.status) : ""}</span></td></tr></tbody></table>` : "") +
    `<p class="c97s">Checked ${c101E(v.checkedUk)}${v.tolerance ? " \u00b7 counted as a match " + c101E(v.tolerance) : ""} \u00b7 ${c101E(v.parser || "")}</p></section>`;
}
async function c101VerifyPage(req, res, user, u0) {
  const q = String(u0.searchParams.get("q") || "").slice(0, 300);
  let out = "";
  if (q.trim()) {
    if (!C101_VLIM.allow(bb12cClientKey(req))) out = `<section class="c101card"><p class="note" role="alert">You've checked a lot of claims in a short time. Wait ten minutes and try again.</p></section>`;
    else { try { out = c101VerdictHtml(await c101Verify(q, req, user)); } catch (e) { console.error("[c101] verify", e && e.message); out = `<section class="c101card"><p class="note" role="alert">Something went wrong checking that. Try again in a minute.</p></section>`; } }
  }
  const ex = ["Gold is above $4,000", "Gold in pounds is about \u00a33,000", "The Fed funds rate is 3.75% to 4%", "Bank Rate is 4%", "The US 10-year yield is 4.1%", "KO revenue was $47bn in 2025"];
  const body = `<style>${C97_CSS}${C99_CSS}${C101_CSS}</style><section><div class="kicker">Tools \u00b7 verify</div><h1>Verify this claim</h1><p class="dek">Paste a market claim. We check it against our own sourced data and tell you if it's supported, not supported, or something we can't verify.</p><p class="byline">${C93_EDITOR}</p>` +
    `<form method="get" action="/tools/verify/" class="c99f c101form" role="search"><div style="flex:1;min-width:240px"><label for="c101q">Claim</label><input id="c101q" name="q" maxlength="300" value="${c101E(q)}" placeholder="e.g. Gold is above $4,000" style="width:100%"></div><button type="submit">Check</button></form>` +
    `<p class="note">Try: ${ex.map(e => `<a href="/tools/verify/?q=${encodeURIComponent(e)}">${c101E(e)}</a>`).join(" \u00b7 ")}</p></section>` + out +
    `<section class="c101card"><h2>How we check</h2><p>We read the claim with fixed rules first. Only if that fails do we ask an AI model (Gemini, with OpenAI as backup) to say which measure and number the claim mentions; the AI never supplies a figure, and its answer is thrown away unless the number really appears in your claim. We then compare with our latest reading: prices count as a match within 1.5%, rates within 0.10 percentage points, company figures within 2%. Claims about the past, records or the future are marked "Can't verify".</p><p class="note">Sources: gold-api.com and Yahoo Finance (delayed), FRED, the Federal Reserve, the Bank of England and SEC EDGAR. ${C93_DISC}</p></section>`;
  const extraHead = q ? '<meta name="robots" content="noindex,follow">' : "";
  return c93Html(req, res, c93Shell({ title: "Verify a market claim | The Dispatch Market", path: "/tools/verify/", desc: "Check a market claim about gold, rates, the dollar or a company's filings against sourced data.", user, body, extraHead }), q ? "private, no-store" : "private, max-age=60");
}
// ── ISA and SIPP gold planner (illustrative, not advice) ──
// Allowances read from gov.uk on 2 Nov 2026 for the 2026 to 2027 tax year; the page re-checks gov.uk weekly.
const C101_TAX = { year: "2026 to 2027", checked: "2 Nov 2026", isa: 20000, lisa: 4000, aa: 60000, noEarn: 3600, taperIncome: 260000, taperThreshold: 200000, taperMin: 10000,
  isaUrl: "https://www.gov.uk/individual-savings-accounts", lisaUrl: "https://www.gov.uk/lifetime-isa", aaUrl: "https://www.gov.uk/tax-on-your-private-pension/annual-allowance", reliefUrl: "https://www.gov.uk/tax-on-your-private-pension/pension-tax-relief", goldUrl: "https://www.gov.uk/search/all?keywords=investment+gold" };
async function c101GovCheck() {
  return c97Cached("c101:gov", 7 * 86400e3, async () => {
    const [i, a] = await Promise.all([c101Get(C101_TAX.isaUrl, "text/html", C101_UA_WEB).catch(() => ""), c101Get(C101_TAX.aaUrl, "text/html", C101_UA_WEB).catch(() => "")]);
    const im = /maximum you can save in ISAs is\s*(?:<[^>]+>\s*)*\u00a3([\d,]+)/i.exec(i), ty = /In the (20\d\d to 20\d\d) tax year/i.exec(i), am = /lower than \u00a3([\d,]+)/i.exec(a) || /This is \u00a3([\d,]+) this tax year/i.exec(a);
    if (!im && !am) throw new Error("gov.uk layout");
    return { isa: im ? Number(im[1].replace(/,/g, "")) : null, aa: am ? Number(am[1].replace(/,/g, "")) : null, year: ty ? ty[1] : "", at: Date.now() };
  }, 6000);
}
function c101TaxYear(ms) { const d = new Date(ms), y = d.getUTCFullYear(), start = Date.UTC(y, 3, 6); const y0 = ms >= start ? y : y - 1; return { label: y0 + " to " + (y0 + 1), ends: Date.UTC(y0 + 1, 3, 5) }; }
function c101Fv(c, r, n) { let v = 0; for (let k = 0; k < n; k++) v = (v + c) * (1 + r); return v; }
function c101Plan(o) {
  const amt = Math.max(0, Math.min(1e6, Number(o.amt) || 0)), yrs = Math.max(1, Math.min(40, Math.round(Number(o.yrs) || 10))), isaPct = Math.max(0, Math.min(100, Number(o.isa) || 0)) / 100;
  const fee = Math.max(0, Math.min(3, Number(o.fee) || 0)) / 100, earn = o.earn === "" || o.earn == null ? null : Math.max(0, Number(o.earn) || 0), band = ["basic", "higher", "additional"].indexOf(o.band) >= 0 ? o.band : "basic";
  const isaIn = amt * isaPct, sippNet = amt - isaIn, isaUse = Math.min(isaIn, C101_TAX.isa), isaOver = Math.max(0, isaIn - C101_TAX.isa);
  let sippGross = sippNet / 0.8; const sippCap = earn == null ? C101_TAX.aa : earn <= 0 ? C101_TAX.noEarn : Math.min(C101_TAX.aa, Math.max(earn, C101_TAX.noEarn));
  const sippOver = Math.max(0, sippGross - sippCap); if (sippOver) sippGross = sippCap;
  const topUp = sippGross * 0.2, extra = sippGross * (band === "higher" ? 0.2 : band === "additional" ? 0.25 : 0);
  const rows = [0, 0.03, 0.06].map(g => { const r = g - fee; return { g, isa: c101Fv(isaUse, r, yrs), sipp: c101Fv(sippGross, r, yrs) }; });
  return { amt, yrs, isaPct, fee, earn, band, isaIn, isaUse, isaOver, sippNet: Math.min(sippNet, sippCap * 0.8), sippGross, sippCap, sippOver, topUp, extra, rows };
}
function c101Gbp(v) { return "\u00a3" + c97N(Math.round(v), 0); }
async function c101PlanPage(req, res, user, u0) {
  const sp = u0.searchParams, has = sp.has("amt");
  const o = { amt: has ? sp.get("amt") : "6000", yrs: sp.get("yrs") || "15", isa: sp.has("isa") ? sp.get("isa") : "50", fee: sp.get("fee") || "0.5", earn: sp.get("earn") || "", band: sp.get("band") || "basic" };
  const P = c101Plan(o), g = await c101GovCheck(), G = g.v, ty = c101TaxYear(Date.now());
  const days = Math.max(0, Math.ceil((ty.ends - Date.now()) / 864e5));
  const live = G ? `Re-checked on gov.uk ${c101E(c97UkWhen(G.at))}: ISA allowance ${G.isa ? c101Gbp(G.isa) : "not found"}, pension annual allowance ${G.aa ? c101Gbp(G.aa) : "not found"}${(G.isa && G.isa !== C101_TAX.isa) || (G.aa && G.aa !== C101_TAX.aa) ? ". <strong>gov.uk now shows a different figure from ours; use gov.uk's.</strong>" : ", matching the figures below."}` : "We couldn't re-check gov.uk just now; the figures below were checked on " + c101E(C101_TAX.checked) + ".";
  const stale = ty.label !== C101_TAX.year ? `<p class="note" role="alert">These allowances are for the ${c101E(C101_TAX.year)} tax year. It is now ${c101E(ty.label)}: check gov.uk for this year's figures.</p>` : "";
  const sel = (n, v, opts) => `<select id="c101${n}" name="${n}">${opts.map(x => `<option value="${x[0]}"${String(v) === String(x[0]) ? " selected" : ""}>${x[1]}</option>`).join("")}</select>`;
  const form = `<form method="get" action="/tools/isa-sipp/" class="c99f c101form"><div><label for="c101amt">You put in each year (\u00a3)</label><input id="c101amt" name="amt" type="number" min="0" max="1000000" step="100" value="${c101E(P.amt)}"></div>` +
    `<div><label for="c101isa">Share into the ISA (%)</label><input id="c101isa" name="isa" type="number" min="0" max="100" step="5" value="${c101E(Math.round(P.isaPct * 100))}"></div>` +
    `<div><label for="c101yrs">Years</label><input id="c101yrs" name="yrs" type="number" min="1" max="40" value="${P.yrs}"></div>` +
    `<div><label for="c101fee">Yearly costs (%)</label><input id="c101fee" name="fee" type="number" min="0" max="3" step="0.05" value="${c101E(o.fee)}"></div>` +
    `<div><label for="c101earn">UK earnings (\u00a3, optional)</label><input id="c101earn" name="earn" type="number" min="0" step="1000" value="${c101E(o.earn)}"></div>` +
    `<div><label for="c101band">Income tax band</label>${sel("band", P.band, [["basic", "Basic rate"], ["higher", "Higher rate"], ["additional", "Additional rate"]])}</div><button type="submit">Show the illustration</button></form>`;
  const t = `<table class="c97t"><thead><tr><th scope="col">If gold-linked holdings grew by</th><th scope="col">ISA after ${P.yrs} years</th><th scope="col">SIPP after ${P.yrs} years</th><th scope="col">Together</th></tr></thead><tbody>` +
    P.rows.map(r => `<tr><td><strong>${c97N(r.g * 100, 0)}% a year</strong><span class="c97p">less ${c97N(P.fee * 100, 2)}% costs</span></td><td>${c101Gbp(r.isa)}</td><td>${c101Gbp(r.sipp)}</td><td>${c101Gbp(r.isa + r.sipp)}</td></tr>`).join("") + `</tbody></table>` +
    `<p class="c97s">Illustration by The Dispatch Market, ${c101E(c97UkWhen(Date.now()))}. Growth rates are round numbers for comparison, not forecasts; gold can fall as well as rise and pays no income. Amounts are not adjusted for inflation.</p>`;
  const notes = [];
  if (P.isaOver) notes.push(`You'd put ${c101Gbp(P.isaIn)} a year into ISAs, ${c101Gbp(P.isaOver)} over the ${c101Gbp(C101_TAX.isa)} allowance; the illustration caps it at ${c101Gbp(C101_TAX.isa)}.`);
  if (P.sippOver) notes.push(`Your pension contribution plus tax relief would pass the ${P.earn != null && P.earn < C101_TAX.aa ? "limit set by your earnings (" + c101Gbp(P.sippCap) + ")" : "annual allowance (" + c101Gbp(C101_TAX.aa) + ")"}; the illustration caps it there. Going over can mean a tax charge.`);
  const body = `<style>${C97_CSS}${C99_CSS}${C101_CSS}</style><section><div class="kicker">Tools \u00b7 planner</div><h1>ISA and SIPP gold planner</h1><p class="dek">See how tax wrappers change what a regular gold-linked saving could look like. <strong>Illustrative, not advice.</strong> We don't recommend any product or provider.</p><p class="byline">${C93_EDITOR}</p>${stale}${form}</section>` +
    `<section class="c101card"><h2>Your illustration</h2><div class="c101kpis"><div><span>Into the ISA each year</span><strong>${c101Gbp(P.isaUse)}</strong><em>${c101Gbp(Math.max(0, C101_TAX.isa - P.isaUse))} of ISA allowance left</em></div><div><span>Into the SIPP each year</span><strong>${c101Gbp(P.sippNet)}</strong><em>Your money, after relief at source</em></div><div><span>Added by basic-rate relief</span><strong>${c101Gbp(P.topUp)}</strong><em>Paid into the SIPP by HMRC via your provider</em></div><div><span>Extra relief to claim</span><strong>${c101Gbp(P.extra)}</strong><em>${P.extra ? "Through Self Assessment; comes back to you, not the pension" : "None at basic rate"}</em></div></div>` +
    (notes.length ? `<ul class="note">${notes.map(n => `<li>${c101E(n)}</li>`).join("")}</ul>` : "") + t +
    `<p class="c101plain">In plain English: an ISA shelters growth and withdrawals from tax, and you can take money out at any time. A SIPP adds tax relief up front (each \u00a380 you pay in becomes \u00a3100), but you usually can't touch it until 55 (57 from 6 April 2028), and most of what you take out later is taxed as income. ${days} days are left in the ${c101E(ty.label)} tax year, which ends on 5 April.</p></section>` +
    `<section class="c101card"><h2>The rules we used</h2><table class="c97t"><thead><tr><th scope="col">Rule</th><th scope="col">Figure</th><th scope="col">Source and date</th></tr></thead><tbody>` +
    [["ISA allowance (all your ISAs together)", c101Gbp(C101_TAX.isa) + " a tax year", C101_TAX.isaUrl],
     ["Lifetime ISA (ages 18 to 39, counts towards the ISA allowance)", c101Gbp(C101_TAX.lisa) + " a year, plus a 25% government bonus", C101_TAX.lisaUrl],
     ["Pension annual allowance", c101Gbp(C101_TAX.aa) + " a tax year, or 100% of your UK earnings if lower; it tapers down to " + c101Gbp(C101_TAX.taperMin) + " if your adjusted income is over " + c101Gbp(C101_TAX.taperIncome) + " and threshold income over " + c101Gbp(C101_TAX.taperThreshold), C101_TAX.aaUrl],
     ["No UK earnings", "You can still pay up to " + c101Gbp(C101_TAX.noEarn * 0.8) + " a year and get relief to " + c101Gbp(C101_TAX.noEarn), C101_TAX.reliefUrl],
     ["Relief at source", "20% added by your provider; higher and additional-rate taxpayers claim the rest", C101_TAX.reliefUrl]]
      .map(r => `<tr><td><strong>${c101E(r[0])}</strong></td><td>${c101E(r[1])}</td><td><span class="c97s"><a href="${c101E(r[2])}" rel="noopener">gov.uk</a></span><span class="c97s">${c101E(C101_TAX.year)} tax year \u00b7 checked ${c101E(C101_TAX.checked)}</span></td></tr>`).join("") +
    `</tbody></table><p class="c97s">${live}</p></section>` +
    `<section class="c101card"><h2>Gold inside a wrapper: check gov.uk</h2><ul><li>ISAs: physical gold bars and coins can't normally be held in a stocks and shares ISA; gold funds and exchange-traded products that track gold often can, if your provider offers them. <strong>Check gov.uk and your provider.</strong></li><li>SIPPs: some providers allow investment-grade gold bullion or gold funds; rules on what a pension may hold are set by HMRC. <strong>Check gov.uk and your provider.</strong></li><li>Outside a wrapper, UK legal-tender gold coins are free of Capital Gains Tax and investment gold is free of VAT. <a href="${C101_TAX.goldUrl}" rel="noopener">Check gov.uk</a>.</li></ul><p class="note">Tax rules depend on your circumstances and can change. For personal advice, speak to a regulated financial adviser. ${C93_DISC}</p></section>`;
  return c93Html(req, res, c93Shell({ title: "ISA and SIPP gold planner | The Dispatch Market", path: "/tools/isa-sipp/", desc: "An illustrative planner showing how ISA and SIPP allowances affect regular gold-linked saving. Not advice.", user, body, extraHead: has ? '<meta name="robots" content="noindex,follow">' : "" }), "private, max-age=60");
}
// ── Gold scenario simulator: monthly OLS of gold on real yields and the dollar ──
function c101Csv(t) { const out = []; String(t).split(/\r?\n/).forEach(l => { const m = /^(\d{4}-\d{2}-\d{2}),\s*(-?[\d.]+)\s*$/.exec(l.trim()); if (m) out.push([m[1], Number(m[2])]); }); return out; }
function c101MonthEnd(rows) { const m = new Map(); rows.forEach(r => m.set(r[0].slice(0, 7), r[1])); return m; }
function c101Inv3(A) {
  const [a, b, c] = A[0], [d, e, f] = A[1], [g, h, i] = A[2];
  const D = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g); if (!D) return null;
  return [[(e * i - f * h) / D, (c * h - b * i) / D, (b * f - c * e) / D], [(f * g - d * i) / D, (a * i - c * g) / D, (c * d - a * f) / D], [(d * h - e * g) / D, (b * g - a * h) / D, (a * e - b * d) / D]];
}
function c101Ols(X, y) {
  const n = y.length, k = 3, XtX = [[0, 0, 0], [0, 0, 0], [0, 0, 0]], Xty = [0, 0, 0];
  for (let r = 0; r < n; r++) for (let i = 0; i < k; i++) { Xty[i] += X[r][i] * y[r]; for (let j = 0; j < k; j++) XtX[i][j] += X[r][i] * X[r][j]; }
  const inv = c101Inv3(XtX); if (!inv) return null;
  const b = inv.map(row => row.reduce((s, v, j) => s + v * Xty[j], 0));
  const ym = y.reduce((s, v) => s + v, 0) / n; let ssr = 0, sst = 0;
  for (let r = 0; r < n; r++) { const f = b[0] + b[1] * X[r][1] + b[2] * X[r][2]; ssr += (y[r] - f) ** 2; sst += (y[r] - ym) ** 2; }
  const s2 = ssr / (n - k), se = inv.map((row, i) => Math.sqrt(s2 * row[i]));
  return { b, se, t: b.map((v, i) => v / se[i]), r2: 1 - ssr / sst, n, s: Math.sqrt(s2) };
}
async function c101Model() {
  return c97Cached("c101:model", 24 * 3600e3, async () => {
    const [gy, ry, usd] = await Promise.all([
      c101Get("https://query1.finance.yahoo.com/v8/finance/chart/GC%3DF?range=20y&interval=1mo", "application/json", C101_UA_WEB),
      c101Get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10&cosd=2003-01-01", "text/csv,*/*"),
      c101Get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTWEXBGS&cosd=2006-01-01", "text/csv,*/*")]);
    const j = JSON.parse(gy), res0 = j && j.chart && j.chart.result && j.chart.result[0]; if (!res0) throw new Error("gold series");
    const ts = res0.timestamp || [], cl = (res0.indicators && res0.indicators.quote && res0.indicators.quote[0] && res0.indicators.quote[0].close) || [];
    const gold = new Map(); ts.forEach((t, i) => { const v = Number(cl[i]); if (v > 0) gold.set(new Date((t + 4 * 86400) * 1000).toISOString().slice(0, 7), v); });
    const R = c101MonthEnd(c101Csv(ry)), U = c101MonthEnd(c101Csv(usd)), cur = c97UkIso(Date.now()).slice(0, 7);
    const months = [...gold.keys()].filter(m => m < cur && R.has(m) && U.has(m)).sort();
    const X = [], y = [], used = [];
    for (let i = 1; i < months.length; i++) {
      const a = months[i - 1], b = months[i]; const [ya, mo] = a.split("-").map(Number), nx = (mo === 12 ? (ya + 1) + "-01" : ya + "-" + String(mo + 1).padStart(2, "0")); if (nx !== b) continue;
      y.push(100 * Math.log(gold.get(b) / gold.get(a))); X.push([1, R.get(b) - R.get(a), 100 * Math.log(U.get(b) / U.get(a))]); used.push(b);
    }
    if (y.length < 60) throw new Error("too few months");
    const fit = c101Ols(X, y); if (!fit) throw new Error("fit");
    const last = months[months.length - 1];
    return { fit, from: used[0], to: used[used.length - 1], last: { month: last, gold: gold.get(last), ry: R.get(last), usd: U.get(last) }, at: Date.now() };
  }, 15000);
}
function c101Scen(m, dry, dusd) { const f = m.fit; const pct = f.b[1] * dry + f.b[2] * 100 * Math.log(1 + dusd / 100); return { pct, lo: pct - 1.96 * f.s, hi: pct + 1.96 * f.s }; }
async function c101ScenPage(req, res, user, u0) {
  const sp = u0.searchParams, clamp = (v, a, b, d) => { const n = Number(v); return isFinite(n) && v !== null && v !== "" ? Math.max(a, Math.min(b, n)) : d; };
  const dry = clamp(sp.get("ry"), -2, 2, 0.5), dusd = clamp(sp.get("usd"), -15, 15, 0);
  const [M, mac] = await Promise.all([c101Model(), c100Macro().catch(() => null)]);
  const m = M.v, spot = mac && mac.rows.find(r => r.key === "gold_usd"), spotV = spot ? c101Num(spot.value) : NaN;
  let main;
  if (!m) main = `<section class="c101card"><p class="note" role="alert">We couldn't load the free data series just now${M.err ? " (" + c101E(M.err) + ")" : ""}. Try again in a few minutes; the model is rebuilt once a day.</p></section>`;
  else {
    const f = m.fit, S = c101Scen(m, dry, dusd);
    const lvl = isFinite(spotV) ? `<div><span>Gold level, illustrative</span><strong data-c100 data-c100-name="Illustrative gold level" data-c100-value="${c101E("$" + c97N(spotV * Math.exp(S.pct / 100), 0))}" data-c100-src="The Dispatch Market model, applied to gold-api.com spot" data-c100-url="/tools/scenario/" data-c100-series="Today's spot gold price times the scenario's modelled change" data-c100-at="${c101E(spot.asOf || "")}" data-c100-status="Model output, illustrative: not a forecast" data-c100-formula="spot \u00d7 e^(modelled % \u00f7 100)" id="c101lvl">$${c97N(spotV * Math.exp(S.pct / 100), 0)}</strong><em>from spot ${c101E(spot.value)} (${c101E(spot.source)})</em></div>` : "";
    const grid = [-1, 0, 1].map(r => [-5, 0, 5].map(u => c101Scen(m, r * 0.5, u).pct));
    main = `<section class="c101card"><h2>Your scenario</h2><form method="get" action="/tools/scenario/" class="c99f c101form" id="c101scen" data-b1="${f.b[1]}" data-b2="${f.b[2]}" data-s="${f.s}" data-spot="${isFinite(spotV) ? spotV : ""}"><div><label for="c101ry">Real yield change (percentage points)</label><input id="c101ry" name="ry" type="number" min="-2" max="2" step="0.05" value="${dry}"></div><div><label for="c101usd">Dollar change (%)</label><input id="c101usd" name="usd" type="number" min="-15" max="15" step="0.5" value="${dusd}"></div><button type="submit">Update</button></form>` +
      `<div class="c101kpis"><div><span>Modelled gold move</span><strong id="c101pct">${c97Sg(S.pct, 1, "%") || "0.0%"}</strong><em id="c101rng">95% of past months: ${c97Sg(S.lo, 1, "%")} to ${c97Sg(S.hi, 1, "%")}</em></div>${lvl}</div>` +
      `<p class="c101plain" id="c101pl">In plain English: in past months when US real yields moved ${c97Sg(dry, 2)} points and the broad dollar moved ${c97Sg(dusd, 1, "%") || "0%"}, gold moved by about ${c97Sg(S.pct, 1, "%") || "0%"} on average, but individual months were often far from that. Illustrative only; not a forecast.</p>` +
      `<h3>Quick grid: modelled monthly gold move</h3><table class="c97t"><thead><tr><th scope="col">Real yield change</th><th scope="col">Dollar \u22125%</th><th scope="col">Dollar unchanged</th><th scope="col">Dollar +5%</th></tr></thead><tbody>${grid.map((row, i) => `<tr><td><strong>${["\u22120.50 points", "Unchanged", "+0.50 points"][i]}</strong></td>${row.map(v => `<td>${c97Sg(v, 1, "%") || "0.0%"}</td>`).join("")}</tr>`).join("")}</tbody></table></section>` +
      `<section class="c101card"><h2>The model, in full</h2><p>Monthly change in gold (log %, COMEX gold futures front month, month-end close) = a + b \u00d7 change in the US 10-year real yield (percentage points) + c \u00d7 change in the broad US dollar (log %). Ordinary least squares, one month at a time.</p>` +
      `<table class="c97t"><thead><tr><th scope="col">Term</th><th scope="col">Estimate</th><th scope="col">Standard error</th><th scope="col">t-statistic</th></tr></thead><tbody>` +
      [["Constant (a): average month", f.b[0], f.se[0], f.t[0], "%"], ["Real yield (b): per +1 point", f.b[1], f.se[1], f.t[1], "%"], ["Dollar (c): per +1%", f.b[2], f.se[2], f.t[2], "%"]].map(r => `<tr><td><strong>${r[0]}</strong></td><td>${c97Sg(r[1], 2, r[4])}</td><td>${c97N(r[2], 2)}</td><td>${c97N(r[3], 1)}</td></tr>`).join("") + `</tbody></table>` +
      `<p>Sample: ${c101E(c97Period(m.from))} to ${c101E(c97Period(m.to))}, ${f.n} month-on-month changes (months missing from the free gold series are skipped, not filled in). R\u00b2 = ${c97N(f.r2, 2)}: these two measures explain about ${c97N(f.r2 * 100, 0)}% of gold's monthly moves. Typical miss (residual standard error): ${c97N(f.s, 1)}% a month. The scenario leaves out the constant, so it shows only the part linked to rates and the dollar.</p>` +
      `<p class="c97s">Sources: gold, <a href="https://finance.yahoo.com/markets/commodities/" rel="noopener">COMEX gold futures via Yahoo Finance</a>, monthly, delayed; real yield, <a href="https://fred.stlouisfed.org/series/DFII10" rel="noopener">FRED series DFII10</a>; dollar, <a href="https://fred.stlouisfed.org/series/DTWEXBGS" rel="noopener">FRED series DTWEXBGS (Federal Reserve broad dollar index)</a>. Model rebuilt ${c101E(c97UkWhen(m.at))}.</p>` +
      `<p class="note">Limits: past relationships shift, the sample includes crisis years, and a two-factor model leaves out central-bank buying, inflation surprises and geopolitics. Illustrative, not advice.</p></section>`;
  }
  const js = `<script>(function(){var f=document.getElementById("c101scen");if(!f)return;var b1=+f.dataset.b1,b2=+f.dataset.b2,s=+f.dataset.s,sp=+f.dataset.spot;function sg(v,d,u){return(v>0?"+":v<0?"\\u2212":"")+Math.abs(v).toFixed(d)+(u||"")}function up(){var r=+document.getElementById("c101ry").value||0,u=+document.getElementById("c101usd").value||0;u=Math.max(-15,Math.min(15,u));r=Math.max(-2,Math.min(2,r));var p=b1*r+b2*100*Math.log(1+u/100);document.getElementById("c101pct").textContent=sg(p,1,"%");document.getElementById("c101rng").textContent="95% of past months: "+sg(p-1.96*s,1,"%")+" to "+sg(p+1.96*s,1,"%");var l=document.getElementById("c101lvl");if(l&&sp){var v="$"+Math.round(sp*Math.exp(p/100)).toLocaleString("en-GB");l.textContent=v;l.setAttribute("data-c100-value",v)}var pl=document.getElementById("c101pl");if(pl)pl.textContent="In plain English: in past months when US real yields moved "+sg(r,2)+" points and the broad dollar moved "+sg(u,1,"%")+", gold moved by about "+sg(p,1,"%")+" on average, but individual months were often far from that. Illustrative only; not a forecast."}f.addEventListener("input",up)})();</script>`;
  const body = `<style>${C97_CSS}${C99_CSS}${C101_CSS}</style><section><div class="kicker">Tools \u00b7 scenarios</div><h1>Gold scenario simulator</h1><p class="dek">What has gold tended to do when real interest rates and the dollar move? A transparent two-factor model on free public data. <strong>Illustrative, not advice.</strong></p><p class="byline">${C93_EDITOR}</p></section>` + main + js;
  return c93Html(req, res, c93Shell({ title: "Gold scenario simulator | The Dispatch Market", path: "/tools/scenario/", desc: "Model how gold has moved with US real yields and the dollar, with the full regression shown. Illustrative.", user, body, extraHead: sp.has("ry") || sp.has("usd") ? '<meta name="robots" content="noindex,follow">' : "" }), "private, max-age=60");
}
// ── Filing change detector: Risk Factors and MD&A against the previous filing (SEC EDGAR) ──
const C101_FC_MEM = new Map();
async function c101CGet(k) { const m = C101_FC_MEM.get(k); if (m && m.exp > Date.now()) return m.v; const v = await c99CacheGet(k); if (v) C101_FC_MEM.set(k, { v, exp: Date.now() + 3600e3 }); return v; }
async function c101CPut(k, v, ttl) { C101_FC_MEM.set(k, { v, exp: Date.now() + Math.min(ttl, 86400) * 1000 }); if (C101_FC_MEM.size > 200) C101_FC_MEM.delete(C101_FC_MEM.keys().next().value); try { await c99CachePut(k, v, ttl); } catch (e) {} }
async function c101SecText(url, maxBytes) {
  const ua = bb11Ua(); if (!ua) throw c99Err("NO_UA", "SEC downloads are switched off on this site for now.");
  if (!(await c99Take())) throw c99Err("CAP", "Today's SEC download limit (" + C99_CAP + " a day) is used up. It resets at midnight UK time.");
  const r = await bb11SecGet(url, ua, null, 60000, maxBytes || 12 * 1024 * 1024);
  if (r && r.status && r.status !== 200) throw c99Err("SEC", "The SEC answered with an error (" + r.status + "). Try again later.");
  return r.text;
}
function c101Sections(html, form) {
  const lines = c101Text(html).split("\n").map(s => s.replace(/\s+/g, " ").trim()).filter(Boolean);
  const L = []; for (let i = 0; i < lines.length; i++) { if (/^item\s*\d+[a-c]?\.?$/i.test(lines[i]) && i + 1 < lines.length) { L.push(lines[i] + " " + lines[i + 1]); i++; } else L.push(lines[i]); }
  const head = s => { const m = /^item\s*(\d+[a-c]?)\.?\s/i.exec(s); return m && s.length < 200 ? m[1].toLowerCase() : null; };
  const span = (id) => { let best = null; for (let i = 0; i < L.length; i++) if (head(L[i]) === id) { let j = i + 1; while (j < L.length && !head(L[j])) j++; const body = L.slice(i + 1, j); const len = body.join(" ").length; if (!best || len > best.len) best = { len, body }; } return best && best.len > 400 ? best.body : null; };
  return form === "10-K" ? { rf: span("1a"), md: span("7") } : { rf: span("1a"), md: span("2") };
}
function c101Sents(paras) {
  const out = []; (paras || []).forEach(p => { String(p).replace(/([.!?])\s+(?=[A-Z(\u201c"])/g, "$1\u0001").split("\u0001").forEach(s => { s = s.trim(); if (s.split(/\s+/).length >= 6 && !/^(table of contents|\d+)$/i.test(s)) out.push(s.slice(0, 1200)); }); }); return out;
}
function c101Norm(s) { return s.toLowerCase().replace(/[\u2018\u2019]/g, "'").replace(/[\u201c\u201d]/g, '"').replace(/\s+/g, " ").trim(); }
function c101Jac(a, b) { const A = new Set(a.toLowerCase().match(/[a-z0-9']+/g) || []), B = new Set(b.toLowerCase().match(/[a-z0-9']+/g) || []); let i = 0; A.forEach(w => { if (B.has(w)) i++; }); return i / Math.max(1, A.size + B.size - i); }
function c101SentDiff(oldS, newS) {
  const O = new Map(); oldS.forEach(s => O.set(c101Norm(s), s)); const N = new Set(newS.map(c101Norm));
  let added = newS.filter(s => !O.has(c101Norm(s))), removed = oldS.filter(s => !N.has(c101Norm(s)));
  const re = [], usedR = new Set();
  if (added.length * removed.length <= 250000) added = added.filter(a => { let bi = -1, bj = 0; removed.forEach((r, j) => { if (usedR.has(j)) return; const v = c101Jac(a, r); if (v > bj) { bj = v; bi = j; } }); if (bj >= 0.5) { usedR.add(bi); re.push({ from: removed[bi], to: a, sim: bj }); return false; } return true; });
  removed = removed.filter((r, j) => !usedR.has(j));
  return { added, removed, reworded: re, same: newS.length - added.length - re.length };
}
function c101WordRed(a, b) { return c101Redline(c101Lcs(a.split(/\s+/), b.split(/\s+/))); }
async function c101Filings(cik, allowDownload) {
  const k = "c101:sub:" + cik; let v = await c101CGet(k); if (v || !allowDownload) return v;
  const j = await c99Sec("https://data.sec.gov/submissions/CIK" + String(cik).padStart(10, "0") + ".json", 8 * 1024 * 1024);
  const r = j && j.filings && j.filings.recent; if (!r || !Array.isArray(r.form)) throw c99Err("SEC", "The SEC's filing list was not in the expected format.");
  const list = []; for (let i = 0; i < r.form.length; i++) if (r.form[i] === "10-K" || r.form[i] === "10-Q") list.push({ form: r.form[i], accn: r.accessionNumber[i], filed: r.filingDate[i], period: r.reportDate[i], doc: r.primaryDocument[i] });
  v = { name: j.name || "", cik: Number(cik), list: list.slice(0, 24), at: Date.now() }; await c101CPut(k, v, 86400); return v;
}
async function c101Doc(cik, f, allowDownload) {
  const k = "c101:doc:" + f.accn; let v = await c101CGet(k); if (v || !allowDownload) return v;
  const url = "https://www.sec.gov/Archives/edgar/data/" + Number(cik) + "/" + f.accn.replace(/-/g, "") + "/" + f.doc;
  const s = c101Sections(await c101SecText(url, 12 * 1024 * 1024), f.form);
  v = { rf: s.rf ? c101Sents(s.rf) : null, md: s.md ? c101Sents(s.md) : null, url, at: Date.now() }; await c101CPut(k, v, 365 * 86400); return v;
}
function c101Pair(sub, form) { const l = sub.list.filter(x => x.form === form); return l.length >= 2 ? [l[0], l[1]] : null; }
async function c101FcCached(t, form) { return c101CGet("c101:fc:" + t + ":" + form); }
async function c101FcBuild(t, form) {
  const tk = await c99Tickers(true), row = c99Find(tk, t); if (!row) throw c99Err("UNKNOWN", "We couldn't find the US ticker " + t + " in the SEC's list.");
  let sub = await c101Filings(row[1], false), need = sub ? 0 : 1, pair = sub ? c101Pair(sub, form) : null;
  if (sub && !pair) throw c99Err("BAD", t + " has fewer than two " + form + " filings in its recent history.");
  if (pair) for (const f of pair) if (!(await c101CGet("c101:doc:" + f.accn))) need++; if (!pair) need += 2;
  const left = C99_CAP - (await c99Used()); if (need > left) throw c99Err("CAP", "This comparison needs " + need + " SEC downloads and only " + Math.max(0, left) + " of today's " + C99_CAP + " are left. It resets at midnight UK time.");
  sub = sub || await c101Filings(row[1], true); pair = c101Pair(sub, form); if (!pair) throw c99Err("BAD", t + " has fewer than two " + form + " filings in its recent history.");
  const [nw, od] = [await c101Doc(row[1], pair[0], true), await c101Doc(row[1], pair[1], true)];
  const sec = (a, b) => { if (!a || !b) return null; const d = c101SentDiff(a, b); return { added: d.added.slice(0, 25), removed: d.removed.slice(0, 25), reworded: d.reworded.slice(0, 25).map(x => ({ from: x.from, to: x.to })), counts: { added: d.added.length, removed: d.removed.length, reworded: d.reworded.length, same: d.same, oldN: a.length, newN: b.length } }; };
  const v = { t, name: sub.name || row[2], cik: row[1], form, now: Object.assign({ url: nw.url }, pair[0]), prev: Object.assign({ url: od.url }, pair[1]), rf: sec(od.rf, nw.rf), md: sec(od.md, nw.md), at: Date.now() };
  await c101CPut("c101:fc:" + t + ":" + form, v, 86400); return v;
}
function c101FcHtml(v) {
  const sec = (title, s, what) => {
    if (!s) return `<section class="c101card"><h2>${title}</h2><p class="note">We couldn't find this section in both filings (some companies place it differently or incorporate it by reference). Read the filings directly using the links above.</p></section>`;
    const c = s.counts, li = (arr, cls) => arr.map(x => `<li class="${cls}">${c101E(x)}</li>`).join("");
    const plain = c.added + c.removed + c.reworded === 0 ? `No sentence-level changes: the ${what} text reads the same as last time.` : `Of ${c.newN} sentences now, ${c.same} are unchanged, ${c.reworded} were reworded, ${c.added} are new and ${c.removed} were taken out since the previous ${v.form}.`;
    return `<section class="c101card"><h2>${title}</h2><div class="c101kpis"><div><span>New sentences</span><strong>${c.added}</strong></div><div><span>Removed</span><strong>${c.removed}</strong></div><div><span>Reworded</span><strong>${c.reworded}</strong></div><div><span>Unchanged</span><strong>${c.same}</strong></div></div><p class="c101plain">In plain English: ${plain}</p>` +
      (s.reworded.length ? `<details class="c101det"${what === "risk factors" ? " open" : ""}><summary>Reworded (${c.reworded > 25 ? "first 25 of " + c.reworded : c.reworded})</summary><ol class="c101red">${s.reworded.map(x => `<li>${c101WordRed(x.from, x.to)}</li>`).join("")}</ol></details>` : "") +
      (s.added.length ? `<details class="c101det"><summary>New (${c.added > 25 ? "first 25 of " + c.added : c.added})</summary><ol>${li(s.added, "c101add")}</ol></details>` : "") +
      (s.removed.length ? `<details class="c101det"><summary>Removed (${c.removed > 25 ? "first 25 of " + c.removed : c.removed})</summary><ol>${li(s.removed, "c101rem")}</ol></details>` : "") + `</section>`;
  };
  const per = f => `${c101E(f.form)} for the period ending ${c101E(c97DayLong(f.period))}, filed ${c101E(c97DayLong(f.filed))}`;
  return `<section class="c101card"><h2>${c101E(v.name)} (${c101E(v.t)})</h2><p>Comparing the latest <a href="${c101E(v.now.url)}" rel="noopener">${per(v.now)}</a> with the previous <a href="${c101E(v.prev.url)}" rel="noopener">${per(v.prev)}</a>.</p><p class="c97s">Source: SEC EDGAR filings (sec.gov), CIK ${c101E(String(v.cik))}. Compared ${c101E(c97UkWhen(v.at))}. Information only, not a recommendation.</p></section>` +
    sec("Risk factors", v.rf, "risk factors") + sec("Management's discussion and analysis (MD&amp;A)", v.md, "MD&amp;A");
}
async function c101FcPage(req, res, user, u0) {
  const sp = u0.searchParams, t = String(sp.get("t") || "").trim().toUpperCase().replace(/[^A-Z0-9.\-]/g, "").slice(0, 10), form = sp.get("form") === "10-K" ? "10-K" : "10-Q", err = sp.get("e");
  let v = null; if (t) { try { v = await c101FcCached(t, form); } catch (e) {} }
  const used = await c99Used(), on = !!bb11Ua(), preview = c99Preview(req, user);
  const pick = `<form method="get" action="/research/filing-changes/" class="c99f c101form"><div><label for="c101t">US ticker</label><input id="c101t" name="t" maxlength="10" autocomplete="off" required placeholder="for example KO" value="${c101E(t)}"></div><div><label for="c101form">Filing</label><select id="c101form" name="form"><option value="10-Q"${form === "10-Q" ? " selected" : ""}>Quarterly (10-Q)</option><option value="10-K"${form === "10-K" ? " selected" : ""}>Annual (10-K)</option></select></div><button type="submit">Show changes</button></form>`;
  let main = "";
  if (v) main = c101FcHtml(v);
  else if (t) {
    const need = `It takes up to 4 of today's ${C99_CAP} site-wide SEC downloads (${used} used so far).`;
    main = `<section class="c101card"><p>We haven't compared ${c101E(t)}'s last two ${form} filings yet today.</p>` +
      (!on ? `<p class="note">SEC downloads are switched off on this site for now, so only comparisons already made can be shown.</p>` : !user ? `<p class="note"><a href="/__auth/login">Sign in</a> to run the comparison (free). ${need}</p>` : preview ? `<p class="note">Guest preview is read-only.</p>` :
        `<form method="post" action="/api/c101/filing-changes" class="c99f"><input type="hidden" name="t" value="${c101E(t)}"><input type="hidden" name="form" value="${form}"><button type="submit">Compare ${c101E(t)}'s last two ${form} filings</button></form><p class="c97s">${need}</p>`) + `</section>`;
  }
  const body = `<style>${C97_CSS}${C99_CSS}${C101_CSS}</style><section><div class="kicker"><a href="/research/sec/">Company filings</a></div><h1>Filing change detector</h1><p class="dek">What did a company change in its Risk Factors and MD&amp;A since its previous 10-Q or 10-K? Sentence-by-sentence, with word-level redlines, straight from SEC EDGAR. Information only.</p><p class="byline">${C93_EDITOR}</p>${pick}</section>` +
    (err ? `<p class="c97note" role="alert">${c101E(String(err).slice(0, 200))}</p>` : sp.get("ok") ? `<p class="c97note" role="status">Done. The comparison is below.</p>` : "") + main +
    `<section class="c101card"><h2>How this works</h2><p>We download the two most recent filings of the type you pick from SEC EDGAR, pull out Item 1A (Risk Factors) and the MD&amp;A (Item 7 in a 10-K, Item 2 in a 10-Q), split them into sentences and match them. A sentence counts as reworded when at least half its words are shared with a removed one; the redline shows <del>deleted</del> and <ins>inserted</ins> words. Quarterly reports are compared with the previous quarterly report, annual with annual. Results are kept for a day; each filing is downloaded only once. A new comparison uses up to 4 of the site's ${C99_CAP} SEC downloads a day, and each signed-in reader can start ${C99_USER_DAY} a day.</p><p class="note">Many 10-Qs only say "no material changes" to risk factors, so an empty result can be normal. Formatting differences can show up as rewording. ${C93_DISC}</p></section>`;
  return c98Send(req, res, c93Shell({ title: (t ? t + " filing changes" : "Filing change detector") + " | The Dispatch Market", path: "/research/filing-changes/", desc: "See what a US company changed in its Risk Factors and MD&A since its previous SEC filing, with word-level redlines.", user, body }));
}
// ── Styles for the chat101 pages (light and dark) ──
const C101_CSS = ".c101card{padding:18px 0 6px;margin:18px 0 0}main>section.c101card{margin:0;padding:28px 0}.c101card h2{margin-top:0}.c101form label{display:block;font:600 13px/1.4 var(--sans);margin:0 0 4px}.c101form input,.c101form select{min-height:40px;box-sizing:border-box}" +
  ".c101kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:12px 0}.c101kpis>div{border:1px solid var(--rule,#d6d1c4);border-radius:6px;padding:10px 12px;background:#fff}.c101kpis span{display:block;font:600 12px/1.35 var(--sans);color:var(--muted)}.c101kpis strong{display:block;font:700 22px/1.25 var(--sans);margin:4px 0 2px;overflow-wrap:anywhere}.c101kpis em{display:block;font:400 12.5px/1.4 var(--sans);font-style:normal;color:var(--muted)}" +
  ".c101plain{background:#f4f2ec;border-left:3px solid #1f6f5c;padding:10px 12px;margin:12px 0;max-width:760px}.note{font-size:13.5px;color:var(--muted);max-width:760px}ul.note{padding-left:18px}" +
  ".c101red{font:16px/1.65 var(--serif,Georgia,serif);max-width:760px}.c101red p{margin:0 0 10px}.c101red del{background:#fbe3df;color:#7a2318;text-decoration:line-through}.c101red ins{background:#dcf1e3;color:#14532d;text-decoration:underline}.c101red li{margin-bottom:10px}" +
  ".c101sr{position:absolute!important;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}" +
  ".c101badge{display:inline-block;font:700 14px/1 var(--sans);letter-spacing:.02em;padding:8px 12px;border-radius:999px;color:#fff}.c101badge.ok{background:#1f6f5c}.c101badge.no{background:#a23b2a}.c101badge.cv{background:#5b5e66}.c101claim{font:italic 19px/1.45 var(--serif,Georgia,serif);margin:10px 0}" +
  ".c101det{margin:10px 0;border:1px solid var(--rule,#d6d1c4);border-radius:6px;padding:8px 12px}.c101det summary{cursor:pointer;font-weight:600;min-height:32px;display:flex;align-items:center}.c101add{border-left:3px solid #1f6f5c;padding-left:8px;margin:6px 0}.c101rem{border-left:3px solid #a23b2a;padding-left:8px;margin:6px 0;color:var(--muted)}" +
  ".c101tools{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin:12px 0}.c101tools a{display:block;border:1px solid var(--rule,#d6d1c4);border-radius:8px;padding:14px;text-decoration:none;color:inherit;background:#fff}.c101tools a:hover,.c101tools a:focus-visible{border-color:#1f6f5c}.c101tools strong{display:block;font:700 17px/1.3 var(--sans);margin-bottom:4px;color:var(--ink)}.c101tools span{font-size:14px;color:var(--muted)}" +
  "@media (max-width:600px){.c101kpis{grid-template-columns:1fr 1fr}.c101kpis strong{font-size:19px}.c101form>div{flex:1 1 100%}.c101form input,.c101form select{width:100%}}" +
  c97Css([[".c101kpis>div,.c101tools a", `background:${C97D.paper2};border-color:${C97D.rule}`], [".c101plain", `background:${C97D.paper3};border-left-color:${C97D.up}`], [".c101card,.c101det", `border-color:${C97D.rule}`],
    [".c101red del", "background:#4a2420;color:#ffd2cb"], [".c101red ins", "background:#173c27;color:#c9f2d6"], [".c101badge.ok", "background:#2f7d63"], [".c101badge.no", "background:#b4483c"], [".c101badge.cv", "background:#5f6875"], [".c101tools strong", `color:${C97D.ink}`]]);
// ── Tools hub ──
const C101_TOOLS = [["/tools/verify/", "Verify this claim", "Paste a claim about gold, rates, the dollar or a company's figures; get supported, not supported or can't verify, with the source."],
  ["/tools/isa-sipp/", "ISA and SIPP gold planner", "How tax wrappers change regular gold-linked saving, with allowances cited from gov.uk. Illustrative, not advice."],
  ["/tools/scenario/", "Gold scenario simulator", "What gold has tended to do when real yields and the dollar move, with the full regression shown."],
  ["/central-banks/", "Fed and BoE statement tracker", "Each policy statement redlined against the last, with a tone score you can check."],
  ["/research/filing-changes/", "Filing change detector", "What a US company changed in its Risk Factors and MD&A since its last 10-Q or 10-K."]];
function c101ToolsGrid() { return `<div class="c101tools">${C101_TOOLS.map(t => `<a href="${t[0]}"><strong>${c101E(t[1])}</strong><span>${c101E(t[2])}</span></a>`).join("")}</div>`; }
async function c101HubPage(req, res, user) {
  const body = `<style>${C101_CSS}</style><section><div class="kicker">Tools</div><h1>Check and plan</h1><p class="dek">Free tools that show their working: every figure comes with its source and time, and every model shows its method. Information only.</p><p class="byline">${C93_EDITOR}</p></section><section>${c101ToolsGrid()}</section>` +
    `<section class="c101card"><h2>Use it like an app</h2><p>Add The Dispatch Market to your home screen for one-tap access to Gold, the Brief and your Dashboard. <button type="button" id="c101-install-btn" class="c101btn" hidden>Install the app</button></p><p class="note" id="c101-install-help">On iPhone or iPad: tap Share, then \u201cAdd to Home Screen\u201d. On Android or desktop Chrome and Edge: use the install icon in the address bar or the menu. No notifications are sent.</p></section>` +
    `<p class="note">${C93_DISC}</p>`;
  return c93Html(req, res, c93Shell({ title: "Check and plan: tools | The Dispatch Market", path: "/tools/", desc: "Free tools that show their working: verify a claim, plan ISA and SIPP saving, model gold scenarios, track central banks and filings.", user, body }), "private, max-age=60");
}
// ── PWA: manifest, icons, service worker, offline page, install prompt ──
const C101_ICONS = { "/icons/icon-192.png": "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", "/icons/icon-512.png": "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", "/icons/icon-maskable-512.png": "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", "/apple-touch-icon.png": "iVBORw0KGgoAAAANSUhEUgAAALQAAAC0CAMAAAAKE/YAAAAAkFBMVEXUokzRoEvNnEnKmkjElkfBk0a7j0SyiUKshECngD6jfT2ifT2beDuWdDmMbTaIajWHaDWHaDSEZjSCZDN/YzJ7YDF2XDBzWS9wWC9rVC1oUSxlTytbRyhQQCVKOyNHOSJENyI8MR8wKBwsJRssJBorJBsoIhklIBgkHxgiHRgeGxccGRYYFhUSEhMODhENDhKK9s0WAAACWklEQVR42u3bXXPaMBCFYQUHQkqhLgQon4G0CcHg7P//d/VMemEZJmUmiqKTefeWvXjmzCJsSTgTLAcaNGjQoEGDBg0aNGjQoEGDBg0aNGjQoEGDBg0aNGjQoEGDBg0aNGjQoEG/Xc+9N6r/czJfbvbJoR/d/6sz2uihq7qeHBJC/3YXVjYv9dDVlGzExuO1+ge5pKtqb/WSrmqpl7RzVyvBpJ2710vaudaDYNKuvddL2rnvaSXd/eXXtHdWvUoKnZ98Xq5H16cDUqY0Hvm5lpdF1lRPk0ebPd02V5Ai6fH4Vz8a6rEC2u4az9cSaMvDLiBx0Nb1n1KT/yK+dl55D06lRNI2CjkfsdCF1zrQQNvQe2OUmGmzrddbaCRtnXAvA/HQ3i/MTAR9X+8dasy0HcO9CsRL2hvqG5Gk7VuwZ6aISQ/qzSpJj+vNRxH0vN68E0Ev6s1PikkXIl/EqeJMe6tHKZJ0fSshE1nyXlr1LTSRH5eHcK+28dCzcPs18dDdcKcv0WZ65/X+0Uh64oItHtHQhyzgFtPnbNYsJdD+BsL7nvFioYu21/m+l61Y6MZhwEIB3TgKaB0F0IPG8cXQPhN92UFRt3msv7fEk37MTw4Sc0safVz1zxzZ7lJCN46Z817n7DHz3Cyhmb6sbs1SSvrLXp3IFC+phLmdF/fi1dpMLulAl8W4TPjlrm1mSzMTS3q4MzF0Z1qYSaFvxlsLXR/3R4aqBrP1wT6g+J8LaNCgQYMGDRo0aNCgQYMGDRo0aNCgQYMGDRo0aNCgQYMGDRo0aNCgQYNOtP4C/6h/U5gJQ8sAAAAASUVORK5CYII=" };
const C101_ICON_BUF = {}; Object.keys(C101_ICONS).forEach(k => { C101_ICON_BUF[k] = Buffer.from(C101_ICONS[k], "base64"); });
const C101_MANIFEST = JSON.stringify({ name: "The Dispatch Market", short_name: "Dispatch Market", description: typeof C93_MISSION === "string" ? C93_MISSION : "Gold and markets research with sources.", id: "/", start_url: "/?source=pwa", scope: "/", display: "standalone", background_color: "#fbfaf7", theme_color: "#fbfaf7", lang: "en-GB", dir: "ltr", categories: ["finance", "news"],
  icons: [{ src: "/icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" }, { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" }, { src: "/icons/icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" }],
  shortcuts: [{ name: "Gold", short_name: "Gold", description: "Today's gold desk", url: "/gold/?source=pwa", icons: [{ src: "/icons/icon-192.png", sizes: "192x192" }] }, { name: "Brief", short_name: "Brief", description: "Today's brief", url: "/brief/?source=pwa", icons: [{ src: "/icons/icon-192.png", sizes: "192x192" }] }, { name: "Dashboard", short_name: "Dashboard", description: "Your dashboard", url: "/dashboard/?source=pwa", icons: [{ src: "/icons/icon-192.png", sizes: "192x192" }] }] });
c93Manifest = function (req, res) { res.writeHead(200, { "Content-Type": "application/manifest+json; charset=utf-8", "Cache-Control": "public, max-age=3600" }); return res.end(req.method === "HEAD" ? undefined : C101_MANIFEST); };
// The service worker never stores pages, API answers (including /api/me), sign-in or admin responses: pages go to the network and fall back to /offline/ only when offline.
const C101_SW = `/* The Dispatch Market service worker (${C101_V}). No push. Never caches pages, /api, sign-in or admin. */
const V = "dispatch-${C101_V}", PRE = ["/offline/", "/icons/icon-192.png", "/icons/icon-512.png", "/apple-touch-icon.png"];
const SKIP = /^\\/(api|__auth|__admin|admin|__theme)(\\/|$)|^\\/sw\\.js$/;
self.addEventListener("install", e => { e.waitUntil(caches.open(V).then(c => c.addAll(PRE)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const r = e.request; if (r.method !== "GET") return;
  let u; try { u = new URL(r.url); } catch (x) { return; }
  if (u.origin !== self.location.origin || SKIP.test(u.pathname)) return;
  if (r.mode === "navigate") { e.respondWith(fetch(r).catch(() => caches.match("/offline/"))); return; }
  if (PRE.indexOf(u.pathname) >= 0) e.respondWith(caches.match(u.pathname).then(m => m || fetch(r)));
});
`;
const C101_INSTALL_JS = `(function(){if(window.__c101i)return;window.__c101i=1;try{var h=location.hostname;if("serviceWorker" in navigator&&(location.protocol==="https:"||h==="localhost"||h==="127.0.0.1")){var rg=function(){navigator.serviceWorker.register("/sw.js",{scope:"/"}).catch(function(){})};if(document.readyState==="complete")rg();else window.addEventListener("load",rg)}}catch(e){}
var K="c101-install-dismissed",ev=null;function off(){try{var t=+localStorage.getItem(K)||0;return Date.now()-t<30*864e5}catch(e){return false}}
function bar(){if(off()||document.getElementById("c101-inst"))return;var d=document.createElement("div");d.id="c101-inst";d.setAttribute("role","region");d.setAttribute("aria-label","Install the app");d.innerHTML='<span>Add The Dispatch Market to your home screen for one-tap Gold, Brief and Dashboard.</span><button type="button" class="y">Install</button><button type="button" class="n" aria-label="Not now">Not now</button>';document.body.appendChild(d);d.querySelector(".y").onclick=go;d.querySelector(".n").onclick=function(){try{localStorage.setItem(K,String(Date.now()))}catch(e){}d.remove()}}
function go(){if(!ev)return;ev.prompt();ev.userChoice.then(function(){ev=null;var d=document.getElementById("c101-inst");if(d)d.remove();var b=document.getElementById("c101-install-btn");if(b)b.hidden=true}).catch(function(){})}
window.addEventListener("beforeinstallprompt",function(e){e.preventDefault();ev=e;var b=document.getElementById("c101-install-btn");if(b){b.hidden=false;b.onclick=go}if(!/[?&]source=pwa/.test(location.search))setTimeout(bar,4000)});
window.addEventListener("appinstalled",function(){var d=document.getElementById("c101-inst");if(d)d.remove()})})();`;
const C101_INSTALL_CSS = `#c101-inst{position:fixed;left:12px;right:12px;bottom:12px;z-index:2147482000;max-width:560px;margin:0 auto;display:flex;flex-wrap:wrap;gap:8px;align-items:center;background:#fff;color:#1b1b1b;border:1px solid #c9c4b8;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.18);padding:12px 14px;font:14px/1.45 Inter,system-ui,sans-serif}#c101-inst span{flex:1 1 220px}#c101-inst button{min-height:40px;padding:0 14px;border-radius:6px;font:600 14px Inter,system-ui,sans-serif;cursor:pointer}#c101-inst .y{background:#1f6f5c;color:#fff;border:1px solid #1f6f5c}#c101-inst .n{background:transparent;color:inherit;border:1px solid #c9c4b8}.c101btn{min-height:40px;padding:0 14px;border-radius:6px;background:#1f6f5c;color:#fff;border:1px solid #1f6f5c;font:600 14px var(--sans,Inter,system-ui,sans-serif);cursor:pointer;margin-left:6px}
html.c97-dark #c101-inst{background:#151b23;color:#ece9e2;border-color:#3a4452}@media (prefers-color-scheme:dark){html.c97-system #c101-inst{background:#151b23;color:#ece9e2;border-color:#3a4452}}`;
function c101OfflineHtml() {
  return c93Shell({ title: "You're offline | The Dispatch Market", path: "/offline/", desc: "You're offline.", user: null, body: `<section><div class="kicker">Offline</div><h1>You're offline</h1><p class="dek">We couldn't reach The Dispatch Market. Prices and stories need a connection, so nothing here is shown out of date.</p><p><a href="/">Try again</a></p><p class="note">${C93_DISC}</p></section>` });
}
// ── Routes ──
{
  const R0 = c93Route;
  c93Route = async function (req, res) {
    if (req.method === "GET" || req.method === "HEAD") {
      let u0; try { u0 = new URL(req.url, "http://localhost"); } catch (e) { u0 = null; }
      const p = u0 ? u0.pathname : "", k = p.replace(/\/$/, "");
      const PG = { "/tools": c101HubPage, "/tools/verify": c101VerifyPage, "/tools/isa-sipp": c101PlanPage, "/tools/scenario": c101ScenPage, "/central-banks": c101CbPage, "/research/filing-changes": c101FcPage };
      if (Object.prototype.hasOwnProperty.call(PG, k)) {
        if (!p.endsWith("/")) { res.writeHead(301, { Location: p + "/" + (u0.search || "") }); res.end(); return true; }
        let user = await c96UserOf(req); if (user && req.c96PreviewOn) { req.c94Preview = p; user = null; } if (user) req.c94Signed = true;
        try { await PG[k](req, res, user, u0); } catch (e) { console.error("[c101] page", k, e && e.message); if (!res.headersSent) c98Send(req, res, c93Shell({ title: "Something went wrong | The Dispatch Market", path: p, desc: "", user, body: `<section><h1>Something went wrong</h1><p class="dek">This page couldn't be built just now. Try again in a minute; if it keeps happening, email ${C93_CONTACT}.</p></section>` }), 500); }
        return true;
      }
    }
    return R0.apply(this, arguments);
  };
}
// ── JSON endpoints (inside the maintenance wrapper) ──
{
  const c101I0 = bb10iHandle0;
  bb10iHandle0 = async function c101Inner(req, res) {
    let u; try { u = new URL(req.url || "/", "http://localhost"); } catch (e) { return c101I0.apply(this, arguments); }
    const p = u.pathname; if (p.indexOf("/api/c101/") !== 0) return c101I0.apply(this, arguments);
    const m = req.method, H = { "Cache-Control": "no-store" }, note = C93_DISC;
    try {
      if (m === "GET" || m === "HEAD") {
        if (p === "/api/c101/verify") {
          const q = String(u.searchParams.get("q") || "").slice(0, 300); if (!q.trim()) return json(res, 400, { error: "Add ?q= with a claim." }, H);
          if (!C101_VLIM.allow(bb12cClientKey(req))) return json(res, 429, { error: "Too many checks. Wait ten minutes." }, H);
          const user = await c96UserOf(req); return json(res, 200, Object.assign(await c101Verify(q, req, user), { note }), H);
        }
        if (p === "/api/c101/cb") {
          const bank = u.searchParams.get("bank") === "boe" ? "boe" : "fed", c = await c101Cb(bank);
          return c.v ? json(res, 200, Object.assign({ bank, method: "Tone = (hawkish \u2212 dovish) \u00f7 (hawkish + dovish) \u00d7 100, from fixed word lists shown on /central-banks/", checkedUk: c97UkWhen(c.at), note }, c.v), { "Cache-Control": "public, max-age=600" }) : json(res, 503, { error: "The statements couldn't be read just now." }, H);
        }
        if (p === "/api/c101/scenario") {
          const M = await c101Model(); if (!M.v) return json(res, 503, { error: "The data series couldn't be loaded just now." }, H);
          const n = (k, a, b, d) => { const v = Number(u.searchParams.get(k)); return u.searchParams.has(k) && isFinite(v) ? Math.max(a, Math.min(b, v)) : d; };
          const ry = n("ry", -2, 2, 0.5), usd = n("usd", -15, 15, 0), f = M.v.fit;
          return json(res, 200, { label: "Illustrative model, not a forecast or advice", input: { realYieldChangePts: ry, dollarChangePct: usd }, modelledGoldMovePct: c101Scen(M.v, ry, usd), formula: "modelled % = b \u00d7 real-yield change + c \u00d7 100 \u00d7 ln(1 + dollar % \u00f7 100); the constant is left out; range = \u00b1 1.96 \u00d7 residual standard error", model: { n: f.n, r2: f.r2, coef: { constant: f.b[0], realYield: f.b[1], dollar: f.b[2] }, se: f.se, t: f.t, residualSe: f.s, sample: [M.v.from, M.v.to] }, sources: ["Yahoo Finance COMEX gold futures front month, monthly, delayed", "FRED DFII10", "FRED DTWEXBGS"], builtUk: c97UkWhen(M.v.at), note }, { "Cache-Control": "public, max-age=600" });
        }
        if (p === "/api/c101/allowances") {
          const g = await c101GovCheck();
          return json(res, 200, { label: "Illustrative, not advice. Check gov.uk.", taxYear: C101_TAX.year, checked: C101_TAX.checked, isa: C101_TAX.isa, lifetimeIsa: C101_TAX.lisa, pensionAnnualAllowance: C101_TAX.aa, noEarningsGross: C101_TAX.noEarn, sources: [C101_TAX.isaUrl, C101_TAX.aaUrl, C101_TAX.reliefUrl], liveCheck: g.v ? { isa: g.v.isa, aa: g.v.aa, checkedUk: c97UkWhen(g.v.at) } : null, note }, { "Cache-Control": "public, max-age=3600" });
        }
        if (p === "/api/c101/filing-changes") {
          const t = String(u.searchParams.get("t") || "").trim().toUpperCase().replace(/[^A-Z0-9.\-]/g, "").slice(0, 10), form = u.searchParams.get("form") === "10-K" ? "10-K" : "10-Q";
          const v = t ? await c101FcCached(t, form) : null; return v ? json(res, 200, Object.assign({ source: "SEC EDGAR", comparedUk: c97UkWhen(v.at), note }, v), H) : json(res, 404, { error: "Not compared yet.", ticker: t, form }, H);
        }
        return json(res, 404, { error: "Not found" }, H);
      }
      if (m !== "POST") return json(res, 404, { error: "Not found" }, H);
      if (!c98SameOrigin(req)) return json(res, 403, { error: "Changes must come from this site." }, H);
      const user = await c96UserOf(req), b = await c98Body(req);
      if (!user) return json(res, 401, { error: "Sign in required." }, H);
      if (c99Preview(req, user)) return json(res, 403, { error: "Guest preview is read-only.", preview: true }, H);
      if (p === "/api/c101/filing-changes") {
        const t = String(b.v.t || "").trim().toUpperCase().replace(/[^A-Z0-9.\-]/g, "").slice(0, 10), form = b.v.form === "10-K" ? "10-K" : "10-Q", back = "/research/filing-changes/?t=" + encodeURIComponent(t) + "&form=" + form + "&";
        if (!t) return c98Reply(req, res, b, 400, { error: "Enter a ticker." }, "/research/filing-changes/?");
        const rp = (st, body) => { if (b.json === false) { const q = body.error ? "e=" + encodeURIComponent(String(body.error).slice(0, 160)) : "ok=1"; res.writeHead(303, { Location: back + q, "Cache-Control": "no-store" }); return res.end(); } return json(res, st, body, H); };
        if (await c101FcCached(t, form)) return rp(200, { ok: true, cached: true });
        if (!c96IsAdmin(user) && !c99UserOk(String(user.id))) return rp(429, { error: "You have used your " + C99_USER_DAY + " SEC look-ups for today. Try again tomorrow." });
        try { const v = await c101FcBuild(t, form); return rp(200, { ok: true, ticker: t, form, name: v.name }); }
        catch (e) { console.error("[c101] filing-changes", e && (e.code || e.message)); return rp(e.code === "CAP" ? 429 : e.code === "NO_UA" ? 503 : e.code === "UNKNOWN" || e.code === "BAD" ? 404 : 502, { error: e.code ? e.message : "The SEC did not answer. Try again later." }); }
      }
      return json(res, 404, { error: "Not found" }, H);
    } catch (e) { console.error("[c101] api", p, e && e.message); return json(res, e && e.code === "C98_BIG" ? 413 : 500, { error: "Something went wrong. Try again in a minute." }, H); }
  };
}
// ── Static PWA files: outermost, so they work during maintenance too ──
{
  const c101H0 = handle;
  handle = async function (req, res) {
    const m = req.method;
    if (m === "GET" || m === "HEAD") {
      let p = ""; try { p = new URL(req.url || "/", "http://localhost").pathname; } catch (e) {}
      if (p === "/sw.js") { res.writeHead(200, { "Content-Type": "text/javascript; charset=utf-8", "Cache-Control": "no-cache", "Service-Worker-Allowed": "/", "X-Content-Type-Options": "nosniff" }); return res.end(m === "HEAD" ? undefined : C101_SW); }
      if (Object.prototype.hasOwnProperty.call(C101_ICON_BUF, p)) { const bf = C101_ICON_BUF[p]; res.writeHead(200, { "Content-Type": "image/png", "Content-Length": bf.length, "Cache-Control": "public, max-age=604800", "X-Content-Type-Options": "nosniff" }); return res.end(m === "HEAD" ? undefined : bf); }
      if (p === "/offline/" || p === "/offline") { try { c97Hook(req, res); } catch (e) {} return c98Send(req, res, c101OfflineHtml(), 200); }
    }
    return c101H0.apply(this, arguments);
  };
}
// ── Sitemap ──
{
  const c101Sm0 = renderPublicSitemap;
  renderPublicSitemap = async function () {
    const x = await c101Sm0.apply(this, arguments);
    const add = ["/tools/", "/tools/verify/", "/tools/isa-sipp/", "/tools/scenario/", "/central-banks/", "/research/filing-changes/"].filter(u => x.indexOf(`<loc>${PUBLIC_ORIGIN}${u}</loc>`) < 0);
    return x.replace("</urlset>", add.map(u => `  <url><loc>${PUBLIC_ORIGIN}${u}</loc><changefreq>${u === "/central-banks/" ? "weekly" : "monthly"}</changefreq><priority>0.6</priority></url>\n`).join("") + "</urlset>");
  };
}
// ── Page transforms: name guard, no raw ticker codes, install prompt, links to the tools ──
{
  const c101Tr0 = c97Transform;
  c97Transform = function (html, req) {
    let out = c101Tr0(html, req);
    if (typeof out !== "string" || !/<\/body>/i.test(out)) return out;
    out = out.replace(/(Vraj Patel),\s*London\b/gi, "$1").replace(/(VRAJ PATEL),\s*LONDON\b/g, "$1");
    out = out.replace(/\(GC=F([,)])/g, "(front month$1");
    if (out.indexOf('id="c101-inst-js"') >= 0) return out;
    let p = "/"; try { p = new URL(req.url || "/", "http://localhost").pathname; } catch (e) {}
    const server = out.indexOf('<header class="site"') >= 0;
    if (server && (p === "/gold/" || p === "/brief/") && out.indexOf("data-c101-tools") < 0) out = out.replace(/<\/main>(?![\s\S]*<\/main>)/, `<section data-c101-tools><style>${C101_CSS}</style><h2>Check and plan</h2>${c101ToolsGrid()}</section></main>`);
    if (server && p === "/research/" && out.indexOf("data-c101-tools") < 0) out = out.replace("<section><h2>Also from the desk</h2>", `<section data-c101-tools><style>${C101_CSS}</style><h2>Check and plan</h2>${c101ToolsGrid()}</section><section><h2>Also from the desk</h2>`);
    const touch = '<link rel="apple-touch-icon" href="/apple-touch-icon.png">';
    out = /<link rel="apple-touch-icon"[^>]*>/i.test(out) ? out.replace(/<link rel="apple-touch-icon"[^>]*>/i, touch) : out.replace(/<\/head>/i, touch + "</head>");
    if (!/rel="manifest"/i.test(out)) out = out.replace(/<\/head>/i, '<link rel="manifest" href="/manifest.json"></head>');
    return out.replace(/<\/head>/i, `<style id="c101-inst-css">${C101_INSTALL_CSS}</style></head>`).replace(/<\/body>(?![\s\S]*<\/body>)/i, `<script id="c101-inst-js">${C101_INSTALL_JS}</script></body>`);
  };
}
