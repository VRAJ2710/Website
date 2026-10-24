#!/usr/bin/env python3
"""rt62 client patch: chat78 -> chat79. Anchors decide; md5 only warns."""
import hashlib
import pathlib
import subprocess
import sys
import tempfile

EXPECT_APP_MD5 = "cb0ca833c4f4dcc9daa579b603d92e85"
EXPECT_INDEX_PREFIX = "8a73c6ac"
NEED_MARKER = "// ── rt61d ──"
REFUSE_MARKER = "// ── rt62 ──"

BLOCK = pathlib.Path(__file__).with_name("rt62_fe79.js").read_text(encoding="utf-8")
if not BLOCK.startswith("// ── rt62 ──"):
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


def anchors(app):
    app = once(
        app,
        '{tk:"TNX",nm:"US 10Y Treasury Yield",cat:"FX",ex:"US",sc:60,se:"Neutral",beta:0.1,pe:"-",mc:"-",th:"US 10Y Treasury Yield (TNX) is a FX listed on US. Source: the desk instrument table."}',
        '{tk:"TNX",nm:"US 10Y Treasury Yield",cat:"Yield",ex:"US",sc:60,se:"Neutral",beta:0.1,pe:"-",mc:"-",th:"US 10Y Treasury Yield (TNX) is a yield listed on US. Source: the desk instrument table."}',
        "tnx category",
    )
    app = once(
        app,
        'A.push({ tk: "DXY", nm: "US Dollar Index (ICE)", cat: "FX", ex: "ICE", sc: 55, se: "Neutral", beta: null, pe: "-", mc: "-",',
        'A.push({ tk: "DXY", nm: "US Dollar Index (ICE)", cat: "Index", ex: "ICE", sc: 55, se: "Neutral", beta: null, pe: "-", mc: "-",',
        "dxy category",
    )
    app = once(
        app,
        "EURUSD:'fx',GBPUSD:'fx',USDJPY:'fx',DXY:'fx',",
        "EURUSD:'fx',GBPUSD:'fx',USDJPY:'fx',DXY:'idx',",
        "dxy tape cat",
    )
    app = once(
        app,
        "ARKK:'stk',TNX:'fx',",
        "ARKK:'stk',TNX:'yld',",
        "tnx tape cat",
    )
    n = app.count("US dollar index")
    if n != 11:
        die("US dollar index count %s" % n)
    app = app.replace("US dollar index", "US Dollar Index")
    app = once(
        app,
        """<td data-fl="${a.tk}" style="font-weight:700">${na?'<span style="color:var(--t3);opacity:0.55">NO LIVE SYNC</span>':((a.cat==='Stock'||a.cat==='Crypto'||a.cat==='Commodity')?'$':'')+d.p}<div class="price-row-meta">${stat(a.tk)} ${asOfTag(a.tk)}</div></td>
      <td style="color:${col};font-weight:700">${na||ch==null?chgDim():`${arrow}${sign}${d.c}%`}</td>""",
        """<td data-fl="${a.tk}" style="font-weight:700">${na?(a.cat==='Crypto'?fe78_skel():'<span style="color:var(--t3);opacity:0.55">NO LIVE SYNC</span>'):(a.tk==='DXY'?fe79_dxyPx(d.p):((a.cat==='Stock'||a.cat==='Crypto'||a.cat==='Commodity')?'$':'')+d.p)}<div class="price-row-meta">${stat(a.tk)} ${asOfTag(a.tk)}</div></td>
      <td style="color:${col};font-weight:700">${na||ch==null?(a.cat==='Crypto'?fe78_skel():chgDim()):fe79_pctHtml(a.tk, ch)}</td>""",
        "home crypto cell",
    )
    app = once(
        app,
        """<div class="asset-chg" style="color:${col}">${d.status==="unavailable"||ch==null?chgDim():`${sign}${d.chg} (${sign}${d.c}%)`}</div>""",
        """<div class="asset-chg" style="color:${col}">${d.status==="unavailable"||ch==null?(a.cat==="Crypto"?fe78_skel():chgDim()):fe79_pctHtml(a.tk, ch)}</div>""",
        "market change",
    )
    app = once(
        app,
        """[{l:"P/E",v:a.pe},{l:"Mkt Cap",v:a.mc},{l:"Beta",v:a.cat==="Stock"?fe64_betaCell(a.beta):a.beta},{l:"Sentiment",v:a.se}].forEach(m=>{h+=`<div style="border-top:1px solid var(--gb);padding:5px 0"><div style="font-size:8px;color:var(--t3)">${m.l}</div><div style="font-family:var(--mn);font-weight:700;font-size:12px;margin-top:1px">${m.v}</div></div>`;});""",
        """[{l:"P/E",v:a.pe},{l:"Mkt Cap",v:fe79_capFor(a)||a.mc},{l:"Beta",v:a.cat==="Stock"?fe64_betaCell(a.beta):a.beta},{l:"Sentiment",v:a.se}].forEach(m=>{if(m.l==="Beta"&&!fe79_showBeta(a.tk))return;if(m.l==="Mkt Cap"){var fe79cap=fe79_capFor(a);if(!fe79cap)return;m={l:m.l,v:fe79cap};}if(!fe79_metricOk(m.l,m.v)&&m.l!=="Sentiment")return;h+=`<div style="border-top:1px solid var(--gb);padding:5px 0"><div style="font-size:8px;color:var(--t3)">${m.l}</div><div style="font-family:var(--mn);font-weight:700;font-size:12px;margin-top:1px">${m.v}</div></div>`;});""",
        "metrics",
    )
    app = once(
        app,
        """<div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:3px">MKT CAP</div>
          <div style="font-family:var(--mn);font-size:14px;font-weight:700">${d.mc}</div>""",
        """<div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:3px">${fe79_metricOk("Mkt Cap", d.mc) ? "MKT CAP" : ""}</div>
          <div style="font-family:var(--mn);font-size:14px;font-weight:700">${fe79_metricOk("Mkt Cap", d.mc) ? d.mc : (typeof _rtIsCrypto==="function"&&_rtIsCrypto(_dynTk)?fe78_skel():"")}</div>""",
        "lookup cap",
    )
    app = once(
        app,
        'if (surface === "crypto" && _cryptoMktData) parts.push(`Crypto top: ${_cryptoMktData.slice(0, 8).map(c => c.symbol + " " + (c.price_change_percentage_24h || 0).toFixed(1) + "%").join(", ")}`);',
        'if (surface === "crypto" && _cryptoMktData) parts.push(`Crypto top: ${_cryptoMktData.slice(0, 8).map(c => { const tk = String(c.symbol || "").toUpperCase(); const pct = fe79_liveCryptoPct(tk, c.current_price); const lab = (typeof fe79_labelFor==="function"&&fe79_labelFor(tk))||"24h"; return tk + " " + (pct == null ? "—" : pct.toFixed(2) + "% " + lab); }).join(", ")}`);',
        "ask crypto",
    )
    app = once(
        app,
        "const RT48B_AS = { gold: 'the gold price', oil: 'oil prices', usd: 'the US dollar', yields: 'US Treasury yields', spx: 'the S&P 500', nasdaq: 'the Nasdaq', btc: 'Bitcoin', eth: 'Ether', eurusd: 'EUR/USD', gbp: 'the British pound' };",
        "const RT48B_AS = { gold: 'the gold price', oil: 'oil prices', usd: 'the US dollar', yields: 'US Treasury yields', spx: 'the S&P 500', nasdaq: 'the Nasdaq', btc: 'Bitcoin', eth: 'Ether', eurusd: 'EUR/USD', gbp: 'the British pound', natgas: 'natural gas prices' };\n"
        "const RT48B_LOOK = { gold:{label:'Gold',ic:'gold',col:'var(--gd)'}, oil:{label:'Oil',ic:'oil',col:'#e07a3d'}, usd:{label:'US dollar',ic:'fx',col:'#7aa2f7'}, yields:{label:'US yields',ic:'bars',col:'#c4b48a'}, spx:{label:'S&P 500',ic:'bars',col:'#8fb9a8'}, nasdaq:{label:'Nasdaq',ic:'bars',col:'#9aa7ff'}, btc:{label:'Bitcoin',ic:'coin',col:'#f2a900'}, eth:{label:'Ether',ic:'coin',col:'#8aa4ff'}, eurusd:{label:'EUR/USD',ic:'fx',col:'#6fbf9b'}, gbp:{label:'Sterling',ic:'fx',col:'#d98b8b'}, natgas:{label:'Natural gas',ic:'flame',col:'#2f9e8f'} };",
        "natgas asset",
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
    if not index_sum.startswith(EXPECT_INDEX_PREFIX):
        print("WARN index.html md5 %s expected prefix %s" % (index_sum, EXPECT_INDEX_PREFIX))
    if REFUSE_MARKER in app:
        print("REFUSE")
        return 0
    if NEED_MARKER not in app:
        die("missing anchor %s" % NEED_MARKER)
    if index.count('app.js?v=chat78"') != 1:
        die("cache bust anchor missing")
    app = anchors(app)
    app = app + "\n" + BLOCK
    if app.count("function fe79_cryptoPct(") != 1:
        die("fe79_cryptoPct count")
    if app.count("function fe79_academyNote(") != 1:
        die("fe79_academyNote count")
    if app.count("function fe79_goldChip(") != 1:
        die("fe79_goldChip count")
    index = index.replace('app.js?v=chat78"', 'app.js?v=chat79"', 1)
    tmp = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
    try:
        tmp.write(app)
        tmp.close()
        chk = subprocess.run(["node", "--check", tmp.name], capture_output=True, text=True)
        if chk.returncode != 0:
            die("node --check failed\n" + chk.stdout + chk.stderr)
        print("node --check ok")
        test = subprocess.run(
            ["node", str(pathlib.Path(__file__).with_name("rt62_fe79_test.js")), tmp.name],
            capture_output=True,
            text=True,
        )
        if test.returncode != 0:
            die("fe79 tests failed\n" + test.stdout + test.stderr)
        print(test.stdout.strip())
    finally:
        pathlib.Path(tmp.name).unlink(missing_ok=True)
    write_text(app_path, app, app_crlf)
    write_text(index_path, index, index_crlf)
    print("patched", app_path, index_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
