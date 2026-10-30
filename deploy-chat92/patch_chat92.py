#!/usr/bin/env python3
"""chat92 patch (server.js only): case-insensitive brand boot fix, monitor SSR head, /pricing social tags,
maintenance exemption for GET/HEAD /manifest.json, /api/monitor sec.downloads_today + sec.downloads_cap.
Usage: patch_chat92.py server.js   (written in place ONLY if every anchor matches exactly once). python3.8+ safe."""
import sys

EDITS = []
def edit(label, old, new):
    EDITS.append((label, old, new))

# 1) boot SQL: case-insensitive, separator-tolerant, case-preserving "Dispatch <sep> Markets" -> "... Market"
edit("1 boot brand fix (case-insensitive)",
"""    console.log(`[chat91] editorial brand fix: ${bb91Brand.length} row(s) 'Dispatch Markets' -> 'Dispatch Market'; ${bb91Title.length} page title suffix row(s) '| The Dispatch' -> '| The Dispatch Market'`);
  } catch (bb91Err) {
    console.warn("[chat91] editorial brand fix skipped:", bb91Err && bb91Err.message ? bb91Err.message : bb91Err);
  }
""",
"""    console.log(`[chat91] editorial brand fix: ${bb91Brand.length} row(s) 'Dispatch Markets' -> 'Dispatch Market'; ${bb91Title.length} page title suffix row(s) '| The Dispatch' -> '| The Dispatch Market'`);
  } catch (bb91Err) {
    console.warn("[chat91] editorial brand fix skipped:", bb91Err && bb91Err.message ? bb91Err.message : bb91Err);
  }
  // chat92: same fix, case-insensitive and separator-tolerant (space, NBSP, &nbsp;/&#160;/&#xa0;, JSON-escaped newline/tab, hyphen, middle dot,
  // bare inline tags). Only the trailing s/S is dropped, so the original case is kept: Markets->Market, MARKETS->MARKET, markets->market.
  // Not inside a word, path or domain (e.g. /dispatch-markets-x or thedispatch-markets.com stay). Idempotent; payload only; never blocks boot.
  // Backslashes are built with chr(92) so the SQL text has none.
  try {
    const bb92Brand = await sql`UPDATE dispatch_editorial_content SET payload = regexp_replace(payload::text, bb92.rx, chr(92) || '1', 'gi')::jsonb FROM (SELECT '(?<![[:alnum:]_./-])(dispatch(?:[[:space:]]|' || chr(160) || '|&nbsp;|&#160;|&#xa0;|' || chr(92) || chr(92) || '[ntr]|-|' || chr(183) || '|</?[A-Za-z][A-Za-z0-9]{0,9}>)+market)s(?![[:alnum:]_])(?![-/.][[:alnum:]])' AS rx) AS bb92 WHERE payload::text ~* bb92.rx RETURNING id`;
    console.log(`[chat92] editorial brand fix (case-insensitive): ${bb92Brand.length} row(s)`);
  } catch (bb92Err) {
    console.warn("[chat92] editorial brand fix skipped:", bb92Err && bb92Err.message ? bb92Err.message : bb92Err);
  }
""")

# 2) monitor SSR head
edit("2 monitor route uses page-specific head",
"""    return text(res, 200, withAssetVersion(INDEX_TEMPLATE), "text/html; charset=utf-8");
  }
  const editorialRoute =""",
"""    return text(res, 200, bb92MonitorShell(p), "text/html; charset=utf-8");
  }
  const editorialRoute =""")
edit("2 monitor head renderer",
"""async function rt43sPricing(req, res) {""",
"""// chat92: server-rendered head for /research/capital-sustainability[/method|/{TICKER}], same titles as app.js fe88_docTitle / fe88_metaDesc.
// Unknown or invalid tickers get the radar head. Company name from the monitor state (or the embedded seed). All values escaped.
function bb92MonitorMeta(p) {
  const base = "/research/capital-sustainability";
  let seg = String(p || "").slice(base.length).replace(/^\\/+|\\/+$/g, "");
  try { seg = decodeURIComponent(seg); } catch (e) { seg = ""; }
  let kind = "radar", tk = null;
  if (seg && seg.toLowerCase() === "method") kind = "method";
  else if (seg && /^[A-Za-z0-9.\\-]{1,10}$/.test(seg) && typeof BB11_TICKERS !== "undefined" && BB11_TICKERS.indexOf(seg.toUpperCase()) >= 0) { kind = "company"; tk = seg.toUpperCase(); }
  if (kind === "method") return { path: base + "/method", title: "How to read the Capital Sustainability Monitor | The Dispatch Market", description: "How the Capital Sustainability Monitor reads filings and delayed daily market data. Not a recommendation. Capital at risk.", h1: "How to read the Capital Sustainability Monitor" };
  if (kind === "company") {
    let co = "";
    try { co = (bb11St && bb11St.companies && bb11St.companies[tk] && bb11St.companies[tk].company) || (BB11_SEED.companies[tk] && BB11_SEED.companies[tk].company) || ""; } catch (e) { co = ""; }
    const name = co ? co + " (" + tk + ")" : tk;
    return { path: base + "/" + tk, title: name + " · Capital Sustainability Monitor | The Dispatch Market", description: "Filing flags, attention and delayed market data for one company on the Capital Sustainability Monitor. Not a recommendation. Capital at risk.", h1: name };
  }
  return { path: base, title: "Capital Sustainability Monitor | The Dispatch Market", description: "A ranking of what is drawing attention and what filings show about how capital spending is funded. Not a recommendation. Capital at risk.", h1: "Capital Sustainability Monitor" };
}
function bb92MonitorShell(p) {
  const m = bb92MonitorMeta(p), canonical = PUBLIC_ORIGIN + m.path;
  const schema = { "@context": "https://schema.org", "@type": "WebPage", "@id": canonical + "#page", name: m.title, url: canonical, description: m.description,
    isPartOf: { "@type": "WebSite", name: "The Dispatch Market", url: PUBLIC_ORIGIN + "/" }, publisher: { "@type": "Person", name: "Vraj Patel", url: "https://www.linkedin.com/in/VRAJ2710" } };
  const head = `<!-- SEO_HEAD_START -->
<meta name="description" content="${escapeHtml(m.description)}">
<meta name="author" content="Vraj Patel">
<meta name="robots" content="index,follow">
<link rel="canonical" href="${escapeHtml(canonical)}">
<title>${escapeHtml(m.title)}</title>
<meta property="og:type" content="website">
<meta property="og:site_name" content="The Dispatch Market">
<meta property="og:title" content="${escapeHtml(m.title)}">
<meta property="og:description" content="${escapeHtml(m.description)}">
<meta property="og:url" content="${escapeHtml(canonical)}">
<meta property="og:image" content="${PUBLIC_ORIGIN}/og-card.png">
<meta property="og:image:alt" content="The Dispatch Market — gold and macro research house">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${escapeHtml(m.title)}">
<meta name="twitter:description" content="${escapeHtml(m.description)}">
<meta name="twitter:image" content="${PUBLIC_ORIGIN}/og-card.png">
<script id="dispatch-page-schema" type="application/ld+json">${safeJson(schema)}</script>
<!-- SEO_HEAD_END -->`;
  return withAssetVersion(INDEX_TEMPLATE.replace(/<!-- SEO_HEAD_START -->[\\s\\S]*?<!-- SEO_HEAD_END -->/, () => head));
}
async function rt43sPricing(req, res) {""")

# 3) /pricing social tags
edit("3 pricing og/twitter tags",
"""<meta name="description" content="The Dispatch Market: Free and Premium (£15/month) plans.">
<style>body{margin:0;background:#0b1018""",
"""<meta name="description" content="The Dispatch Market: Free and Premium (£15/month) plans.">
<link rel="canonical" href="https://thedispatch.uk/pricing">
<meta property="og:type" content="website">
<meta property="og:site_name" content="The Dispatch Market">
<meta property="og:title" content="Pricing · The Dispatch Market">
<meta property="og:description" content="The Dispatch Market: Free and Premium (£15/month) plans.">
<meta property="og:url" content="https://thedispatch.uk/pricing">
<meta property="og:image" content="https://thedispatch.uk/og-card.png">
<meta property="og:image:alt" content="The Dispatch Market — gold and macro research house">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Pricing · The Dispatch Market">
<meta name="twitter:description" content="The Dispatch Market: Free and Premium (£15/month) plans.">
<meta name="twitter:image" content="https://thedispatch.uk/og-card.png">
<style>body{margin:0;background:#0b1018""")

# 4) maintenance: exempt GET/HEAD /manifest.json only (icons are inline data: URIs, nothing else needed)
edit("4 maintenance exempt /manifest.json",
"""    if (h === "/health" || h === "/healthz" || h === "/api/health") return true;
  }""",
"""    if (h === "/health" || h === "/healthz" || h === "/api/health") return true;
    if (p === "/manifest.json") return true;                                       // chat92: browsers fetch it without cookies; its icon is an inline data: URI
  }""")

# 5) monitor API visibility of the daily facts cap
edit("5 /api/monitor sec.downloads_today/cap",
"""sec.last_errors = st.sec.errors.slice(-3); }
""",
"""sec.last_errors = st.sec.errors.slice(-3); }
  sec.downloads_today = st.sec.day === today ? (st.sec.facts_today || 0) : 0; sec.downloads_cap = BB11_MAX_FACTS_PER_DAY;   // chat92: = facts_today for today's UK day
""")

def main(argv):
    if len(argv) != 2: raise SystemExit("usage: patch_chat92.py server.js")
    s = open(argv[1], encoding="utf-8").read()
    if "chat92" in s: raise SystemExit("ABORT: server.js already contains chat92")
    for label, old, new in EDITS:
        n = s.count(old)
        if n != 1: raise SystemExit("ABORT: anchor for '%s' found %d times (expected 1)" % (label, n))
        s = s.replace(old, new)
        print("server.js: %s: 1" % label)
    if not s.startswith("const BB10I_MAINTENANCE_ON = true;"): raise SystemExit("ABORT: server line 1 changed")
    open(argv[1], "w", encoding="utf-8", newline="").write(s)
    print("patch_chat92: ok (%d edits)" % len(EDITS))

if __name__ == "__main__":
    main(sys.argv)
