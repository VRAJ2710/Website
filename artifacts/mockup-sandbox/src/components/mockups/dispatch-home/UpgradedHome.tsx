import { useMemo, useState } from "react";

const movers = [
  { ticker: "NVDA", name: "NVIDIA", price: "$118.90", change: "+2.58%", tone: "up" },
  { ticker: "XAU", name: "Gold", price: "$4,780", change: "+0.62%", tone: "up" },
  { ticker: "WTI", name: "Crude Oil", price: "$93.04", change: "-1.28%", tone: "down" },
  { ticker: "TNX", name: "US 10Y Yield", price: "4.23%", change: "-0.08%", tone: "down" },
  { ticker: "EURUSD", name: "EUR / USD", price: "1.0865", change: "+0.12%", tone: "up" },
];

const searchItems = [
  ["XAU", "Gold", "Commodity"],
  ["NVDA", "NVIDIA", "NASDAQ"],
  ["TNX", "US 10Y Yield", "Rates"],
  ["EURUSD", "EUR / USD", "FX"],
  ["AAPL", "Apple Inc", "NASDAQ"],
  ["DXY", "US Dollar Index", "Macro"],
];

function BrandMark() {
  return <span className="dh-mark" aria-hidden="true">D</span>;
}

function TinySpark({ down = false }: { down?: boolean }) {
  const points = down ? "0,9 9,6 18,12 27,8 36,15 45,13 54,18" : "0,16 9,14 18,17 27,8 36,11 45,4 54,7";
  return (
    <svg className="dh-spark" viewBox="0 0 54 20" role="img" aria-label="session movement">
      <polyline points={points} fill="none" stroke="currentColor" strokeWidth="1.6" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

export function UpgradedHome() {
  const [query, setQuery] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [notice, setNotice] = useState(true);
  const [bookAdded, setBookAdded] = useState(false);
  const [activeNav, setActiveNav] = useState("Home");
  const [briefOpen, setBriefOpen] = useState(false);

  const filtered = useMemo(
    () => searchItems.filter(([ticker, name, market]) =>
      `${ticker} ${name} ${market}`.toLowerCase().includes(query.toLowerCase())
    ),
    [query]
  );

  const go = (label: string) => setActiveNav(label);

  return (
    <div className="dh-shell">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=IBM+Plex+Mono:wght@400;500;600&family=Public+Sans:wght@400;500;600;700&display=swap');
        .dh-shell { --paper:#eeece5; --paper2:#e5e3db; --carbon:#d9ddd9; --carbon2:#cfd5d1; --ink:#191b1d; --muted:#646a6e; --faint:#858b8d; --rule:rgba(25,27,29,.16); --hair:rgba(25,27,29,.09); --gold:#7b5513; --goldleaf:#ae7c24; --goldwash:rgba(123,85,19,.11); --green:#21664a; --red:#a33831; min-height:100vh; background:var(--paper); color:var(--ink); font-family:'Public Sans',sans-serif; overflow-x:hidden; }
        .dh-shell * { box-sizing:border-box; }
        .dh-shell button, .dh-shell input { font:inherit; }
        .dh-shell button { cursor:pointer; }
        .dh-shell a { color:inherit; text-decoration:none; }
        .dh-topline { height:25px; padding:0 24px; display:flex; align-items:center; gap:22px; background:var(--paper2); border-bottom:1px solid var(--hair); color:var(--muted); font:10px 'IBM Plex Mono',monospace; white-space:nowrap; overflow:hidden; }
        .dh-topline span:nth-child(2), .dh-topline span:nth-child(4) { color:var(--green); }
        .dh-layout { display:grid; grid-template-columns:194px minmax(0,1fr); min-height:calc(100vh - 25px); }
        .dh-rail { background:#e3e2da; border-right:1px solid var(--rule); padding:26px 13px 20px; display:flex; flex-direction:column; }
        .dh-brand { display:flex; gap:9px; align-items:center; margin:0 10px 35px; }
        .dh-mark { display:grid; place-items:center; width:28px; height:28px; border-radius:7px; background:#202225; color:#d5a745; font:italic 21px Georgia,serif; }
        .dh-brand-copy { line-height:1; }
        .dh-brand-title { font:600 15px Fraunces,serif; letter-spacing:-.02em; }
        .dh-brand-sub { margin-top:5px; color:var(--muted); font:9px 'IBM Plex Mono',monospace; letter-spacing:.12em; }
        .dh-rail-label { margin:0 12px 9px; color:var(--faint); font-size:9px; font-weight:700; letter-spacing:.2em; text-transform:uppercase; }
        .dh-nav { display:flex; flex-direction:column; gap:2px; }
        .dh-nav button { border:0; background:transparent; color:#555b60; text-align:left; padding:9px 11px; border-radius:4px; font:500 12px 'IBM Plex Mono',monospace; transition:background .16s,color .16s,transform .16s; }
        .dh-nav button:hover { background:rgba(123,85,19,.08); color:var(--ink); transform:translateX(2px); }
        .dh-nav button.active { color:var(--ink); background:var(--goldwash); box-shadow:inset 2px 0 var(--gold); }
        .dh-nav .primary { font:600 16px Fraunces,serif; }
        .dh-rail-group { margin-top:25px; }
        .dh-rail-footer { margin-top:auto; border-top:1px solid var(--hair); padding:17px 10px 0; color:var(--faint); font:10px 'IBM Plex Mono',monospace; line-height:1.7; }
        .dh-main { min-width:0; }
        .dh-command { height:65px; display:flex; align-items:center; gap:18px; padding:0 27px; border-bottom:1px solid var(--rule); }
        .dh-command-brand { display:flex; align-items:center; gap:8px; white-space:nowrap; }
        .dh-command-brand strong { font:700 17px Fraunces,serif; }
        .dh-command-brand small { color:var(--muted); font-size:10px; font-weight:600; letter-spacing:.16em; }
        .dh-command-search { flex:1; max-width:610px; display:flex; position:relative; }
        .dh-command-search input { width:100%; height:36px; padding:0 49px 0 13px; color:var(--ink); background:var(--carbon); border:1px solid var(--rule); border-radius:4px; outline:0; font:12px 'IBM Plex Mono',monospace; }
        .dh-command-search input:focus { border-color:var(--goldleaf); box-shadow:0 0 0 3px var(--goldwash); }
        .dh-go { position:absolute; right:0; top:0; height:36px; width:45px; border:0; border-radius:0 4px 4px 0; background:var(--gold); color:var(--paper); font:600 10px 'IBM Plex Mono',monospace; letter-spacing:.08em; }
        .dh-results { position:absolute; z-index:10; top:42px; left:0; right:0; padding:6px; background:var(--paper); border:1px solid var(--rule); box-shadow:0 12px 24px rgba(22,23,26,.16); border-radius:5px; }
        .dh-result { display:flex; align-items:center; justify-content:space-between; width:100%; padding:9px 10px; color:var(--ink); background:transparent; border:0; text-align:left; }
        .dh-result:hover { background:var(--goldwash); }
        .dh-result b { font:600 11px 'IBM Plex Mono',monospace; }
        .dh-result span { color:var(--muted); font-size:11px; }
        .dh-command-right { margin-left:auto; display:flex; align-items:center; gap:14px; color:var(--muted); white-space:nowrap; font:10px 'IBM Plex Mono',monospace; }
        .dh-live { display:flex; align-items:center; gap:6px; }
        .dh-live i { width:6px; height:6px; border-radius:50%; background:var(--green); display:block; box-shadow:0 0 0 3px rgba(33,102,74,.12); }
        .dh-auth { display:flex; align-items:center; gap:10px; }
        .dh-auth button { border:0; padding:7px 10px; color:var(--muted); background:transparent; font-size:11px; }
        .dh-auth .premium { background:var(--gold); color:var(--paper); border-radius:3px; font-weight:700; }
        .dh-content { max-width:1240px; padding:34px 46px 70px; margin:0 auto; }
        .dh-welcome { display:flex; justify-content:space-between; align-items:flex-end; padding-bottom:23px; border-bottom:1px solid var(--rule); animation:dh-in .5s ease both; }
        .dh-kicker { color:var(--gold); font:600 10px 'IBM Plex Mono',monospace; letter-spacing:.17em; text-transform:uppercase; }
        .dh-welcome h1 { max-width:660px; margin:8px 0 7px; font:600 clamp(32px,4vw,51px)/.98 Fraunces,serif; letter-spacing:-.045em; }
        .dh-welcome p { margin:0; color:var(--muted); font-size:14px; }
        .dh-date { color:var(--muted); text-align:right; font:11px/1.7 'IBM Plex Mono',monospace; }
        .dh-date strong { color:var(--ink); display:block; font-weight:500; }
        .dh-grid { display:grid; grid-template-columns:minmax(0,1.58fr) minmax(290px,.82fr); gap:36px; padding-top:27px; }
        .dh-section-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:11px; }
        .dh-section-head h2 { margin:0; font:600 18px Fraunces,serif; }
        .dh-section-head span { color:var(--faint); font:10px 'IBM Plex Mono',monospace; letter-spacing:.12em; text-transform:uppercase; }
        .dh-regime { display:grid; grid-template-columns:1.1fr .9fr; min-height:214px; background:#26292a; color:#f1eee5; border-radius:6px; overflow:hidden; animation:dh-in .55s .08s ease both; }
        .dh-regime-copy { padding:23px 25px; }
        .dh-regime .dh-kicker { color:#d7af5b; }
        .dh-regime h3 { margin:10px 0 10px; font:600 29px/1.05 Fraunces,serif; letter-spacing:-.035em; }
        .dh-regime p { margin:0; max-width:360px; color:#bbbcb5; font-size:12px; line-height:1.65; }
        .dh-regime-side { display:flex; flex-direction:column; justify-content:space-between; padding:25px; background:linear-gradient(125deg,rgba(184,140,48,.16),rgba(255,255,255,.025)); border-left:1px solid rgba(238,236,229,.1); }
        .dh-score { font:600 45px 'IBM Plex Mono',monospace; color:#d7af5b; letter-spacing:-.08em; }
        .dh-score small { display:block; margin-top:-5px; color:#93968f; font:10px 'IBM Plex Mono',monospace; letter-spacing:.12em; text-transform:uppercase; }
        .dh-scenarios { display:flex; gap:7px; flex-wrap:wrap; }
        .dh-scenarios span { padding:4px 7px; border:1px solid rgba(215,175,91,.28); border-radius:3px; color:#c8c8be; font:10px 'IBM Plex Mono',monospace; }
        .dh-brief { margin-top:26px; padding:21px 0 19px; border-top:1px solid var(--rule); border-bottom:1px solid var(--rule); }
        .dh-brief h3 { margin:0 0 9px; font:600 24px/1.08 Fraunces,serif; }
        .dh-brief p { max-width:680px; color:var(--muted); font-size:13px; line-height:1.7; }
        .dh-link { border:0; padding:0; color:var(--gold); background:transparent; font:600 11px 'IBM Plex Mono',monospace; }
        .dh-link:hover { text-decoration:underline; }
        .dh-brief-detail { max-width:680px; margin:9px 0 12px; padding:11px 13px; color:var(--ink); background:var(--goldwash); border-left:2px solid var(--gold); font-size:12px; line-height:1.6; }
        .dh-book { padding:20px 0; border-bottom:1px solid var(--rule); }
        .dh-book-empty { display:flex; align-items:center; justify-content:space-between; gap:18px; padding:16px; background:var(--carbon); border:1px solid var(--hair); border-radius:5px; }
        .dh-book-empty strong { display:block; margin-bottom:4px; font:600 15px Fraunces,serif; }
        .dh-book-empty p { margin:0; color:var(--muted); font-size:11px; }
        .dh-add { flex-shrink:0; padding:8px 10px; border:1px solid var(--gold); border-radius:3px; color:var(--gold); background:transparent; font:600 10px 'IBM Plex Mono',monospace; }
        .dh-add:hover { background:var(--gold); color:var(--paper); }
        .dh-side-block { padding-bottom:25px; margin-bottom:24px; border-bottom:1px solid var(--rule); }
        .dh-side-block h2 { margin:0 0 14px; font:600 18px Fraunces,serif; }
        .dh-mover { display:grid; grid-template-columns:56px 1fr 66px 55px; align-items:center; gap:8px; padding:10px 0; border-bottom:1px solid var(--hair); }
        .dh-mover:last-child { border:0; }
        .dh-mover b { font:600 11px 'IBM Plex Mono',monospace; }
        .dh-mover small { display:block; margin-top:3px; color:var(--muted); font-size:10px; }
        .dh-price { text-align:right; font:11px 'IBM Plex Mono',monospace; }
        .dh-change { text-align:right; font:11px 'IBM Plex Mono',monospace; }
        .dh-change.up { color:var(--green); } .dh-change.down { color:var(--red); }
        .dh-spark { width:54px; height:20px; color:var(--green); } .dh-spark + .dh-change.down { color:var(--red); }
        .dh-start { display:grid; gap:8px; }
        .dh-route { display:flex; align-items:center; justify-content:space-between; padding:12px 13px; border:1px solid var(--hair); background:rgba(229,227,219,.42); transition:background .16s,transform .16s; }
        .dh-route:hover { background:var(--goldwash); transform:translateX(2px); }
        .dh-route strong { display:block; font:600 13px Fraunces,serif; } .dh-route span { color:var(--muted); font-size:10px; }
        .dh-route em { color:var(--gold); font:14px Georgia,serif; font-style:normal; }
        .dh-member { padding:17px; background:linear-gradient(140deg,var(--carbon),#e8e5db); border:1px solid var(--hair); border-radius:5px; }
        .dh-member .dh-kicker { color:var(--gold); }
        .dh-member h3 { margin:8px 0 6px; font:600 20px Fraunces,serif; }
        .dh-member p { margin:0 0 13px; color:var(--muted); font-size:11px; line-height:1.55; }
        .dh-member button { padding:8px 11px; color:var(--paper); background:var(--gold); border:0; border-radius:3px; font-size:11px; font-weight:700; }
        .dh-dismiss { border:0; color:var(--faint); background:transparent; font:14px 'IBM Plex Mono',monospace; }
        @keyframes dh-in { from { opacity:0; transform:translateY(7px); } to { opacity:1; transform:none; } }
        @media (prefers-reduced-motion:reduce) { .dh-shell *, .dh-shell *::before, .dh-shell *::after { animation:none !important; transition:none !important; } }
        @media (max-width:900px) { .dh-rail { width:164px; } .dh-layout { grid-template-columns:164px minmax(0,1fr); } .dh-content { padding-left:26px; padding-right:26px; } .dh-command { padding:0 18px; } .dh-command-right { gap:7px; } .dh-command-brand small { display:none; } }
        @media (max-width:700px) { .dh-topline { padding:0 14px; gap:16px; } .dh-layout { display:block; } .dh-rail { display:none; } .dh-command { height:auto; min-height:58px; padding:10px 14px; gap:10px; flex-wrap:wrap; } .dh-command-brand { flex:1; } .dh-command-brand strong { font-size:16px; } .dh-command-search { order:3; flex-basis:100%; max-width:none; } .dh-command-right { margin-left:0; } .dh-live { display:none; } .dh-auth button { padding:7px 5px; } .dh-content { padding:25px 16px 50px; } .dh-welcome { display:block; } .dh-welcome h1 { font-size:38px; max-width:330px; } .dh-date { margin-top:16px; text-align:left; } .dh-grid { display:block; padding-top:23px; } .dh-regime { grid-template-columns:1fr; } .dh-regime-side { min-height:130px; border-left:0; border-top:1px solid rgba(238,236,229,.1); flex-direction:row; align-items:flex-end; } .dh-regime h3 { font-size:27px; } .dh-side-block { margin-top:27px; } .dh-mover { grid-template-columns:52px 1fr 58px 53px; } }
        @media (max-width:390px) { .dh-content { padding-left:13px; padding-right:13px; } .dh-topline span:nth-child(n+3) { display:none; } .dh-book-empty { align-items:flex-start; flex-direction:column; } .dh-add { width:100%; } .dh-command-right { font-size:9px; } }
      `}</style>

       <div className="dh-topline"><span>DISPATCH MARKETS</span><span>LIVE</span><span>•</span><span>EQUITY / RATES / COMMODITIES / FX</span><span>18 APR 2026 · 08:42 UTC</span></div>
      <div className="dh-layout">
        <aside className="dh-rail">
          <div className="dh-brand"><BrandMark /><div className="dh-brand-copy"><div className="dh-brand-title">The Dispatch</div><div className="dh-brand-sub">MARKETS</div></div></div>
          <div className="dh-rail-label">Desk</div>
          <nav className="dh-nav">
            {["Home", "Brief", "Playbook", "Gold"].map((item) => <button key={item} className={activeNav === item ? "active primary" : "primary"} onClick={() => go(item)}>{item}</button>)}
          </nav>
          <div className="dh-rail-group">
            <div className="dh-rail-label">Explore</div>
            <nav className="dh-nav">{["Markets", "Lab"].map((item) => <button key={item} className={activeNav === item ? "active" : ""} onClick={() => go(item)}>{item}</button>)}</nav>
          </div>
          <div className="dh-rail-footer">Live prices and desk tools are free.<br />Premium adds AI research.</div>
        </aside>

        <main className="dh-main">
          <header className="dh-command">
            <div className="dh-command-brand"><BrandMark /><strong>THE DISPATCH</strong><small>MARKETS</small></div>
            <div className="dh-command-search">
              <input aria-label="Search tickers or commands" value={query} onFocus={() => setSearchOpen(true)} onChange={(e) => { setQuery(e.target.value); setSearchOpen(true); }} onKeyDown={(e) => e.key === "Escape" && setSearchOpen(false)} placeholder="Enter ticker or command — AAPL, NEWS, WATCH" />
              <button className="dh-go" onClick={() => setSearchOpen(true)}>GO</button>
              {searchOpen && <div className="dh-results">{filtered.length ? filtered.map(([ticker, name, market]) => <button className="dh-result" key={ticker} onClick={() => { setQuery(ticker); setSearchOpen(false); }}><b>{ticker}</b><span>{name} · {market}</span></button>) : <div className="dh-result"><span>No desk result. Try XAU, NVDA, TNX, or EURUSD.</span></div>}</div>}
            </div>
            <div className="dh-command-right"><span className="dh-live"><i /> LIVE</span><span>08:42:16</span><div className="dh-auth"><button>Sign in</button><button className="premium">Subscribe · £15/mo</button></div></div>
          </header>

          <div className="dh-content">
            <section className="dh-welcome"><div><div className="dh-kicker">Friday, 18 April 2026 · Opening desk</div><h1>Good morning. Start with the state of the market.</h1><p>A focused read on gold, macro conditions, and the moves worth keeping in view.</p></div><div className="dh-date"><strong>YOUR COMMAND CENTER</strong>Updated as sessions move</div></section>
            <div className="dh-grid">
              <div>
                <div className="dh-section-head"><h2>Market regime</h2><span>Live context</span></div>
                <section className="dh-regime"><div className="dh-regime-copy"><div className="dh-kicker">Risk / reward</div><h3>Defensive, but not dislocated</h3><p>Gold is holding its bid as the dollar softens. Oil volatility remains the macro fault line; equities are absorbing the news rather than chasing it.</p></div><div className="dh-regime-side"><div className="dh-score">68<small>regime score / 100</small></div><div className="dh-scenarios"><span>Gold · bid</span><span>Dollar · soft</span><span>Oil · volatile</span></div></div></section>
                <section className="dh-brief"><div className="dh-section-head"><h2>Today&apos;s brief</h2><span>Desk note · 6 min</span></div><h3>Three things that can change the gold thesis this week</h3><p>Central-bank demand is doing the quiet work, but the next leg depends on the dollar and real yields. Here is the cleanest way to frame the decision before the US session gets busy.</p>{briefOpen && <div className="dh-brief-detail">The base case is constructive, not certain: watch DXY below 99, real yields for confirmation, and the $4,700 area as the first level that would challenge the current structure.</div>}<button className="dh-link" onClick={() => setBriefOpen(!briefOpen)}>{briefOpen ? "Hide brief detail" : "Read today's brief →"}</button></section>
                <section className="dh-book"><div className="dh-section-head"><h2>Your book</h2><span>Watchlist</span></div>{bookAdded ? <div className="dh-book-empty"><div><strong>Book ready for a first name</strong><p>Use the command field above to add a ticker when the market gives you one.</p></div><button className="dh-add" onClick={() => setBookAdded(false)}>Clear book</button></div> : <div className="dh-book-empty"><div><strong>Your book is empty</strong><p>Keep the names and levels you want to return to here.</p></div><button className="dh-add" onClick={() => setBookAdded(true)}>Add first ticker</button></div>}</section>
              </div>
              <aside>
                <section className="dh-side-block"><div className="dh-section-head"><h2>Session movers</h2><span>Tracked</span></div>{movers.map((item, index) => <div className="dh-mover" key={item.ticker}><b>{item.ticker}<small>{item.name}</small></b><TinySpark down={item.tone === "down"} /><span className="dh-price">{item.price}</span><span className={`dh-change ${item.tone}`}>{item.change}</span></div>)}</section>
                <section className="dh-side-block"><div className="dh-section-head"><h2>Start here</h2><span>Desk routes</span></div><div className="dh-start">{[["Brief", "The morning read"], ["Gold", "Weekly conditional playbook"], ["Markets", "Live prices and context"], ["Lab", "Research tools"]].map(([title, copy]) => <button className="dh-route" key={title} onClick={() => go(title)}><span><strong>{title}</strong><span>{copy}</span></span><em>→</em></button>)}</div></section>
                {notice && <section className="dh-member"><button className="dh-dismiss" aria-label="Dismiss membership message" onClick={() => setNotice(false)}>×</button><div className="dh-kicker">Premium research</div><h3>Keep the desk close.</h3><p>Gold Desk playbooks, Daily Dispatch Brief, Dispatch Expert chat, and xAI-powered research. Stripe-managed billing, £15/month.</p><button onClick={() => go("Subscribe")}>See Premium</button></section>}
              </aside>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default UpgradedHome;