import { useMemo, useState } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Bell,
  BookOpen,
  Bookmark,
  BriefcaseBusiness,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  Command,
  FileText,
  FlaskConical,
  Globe2,
  LayoutGrid,
  LineChart,
  Menu,
  Pause,
  Play,
  Plus,
  Search,
  Settings,
  Sparkles,
  Star,
  X,
  Zap,
} from "lucide-react";

type Surface = "Home" | "Brief" | "Playbook" | "Gold" | "Dash" | "Lab" | "Signals" | "Markets" | "Screener" | "Sectors" | "Heatmap" | "Rates & FX" | "News" | "Papers" | "Research" | "Documents" | "Geo" | "Watch" | "Port" | "Learn" | "Settings";
type Quote = { ticker: string; name: string; price: string; change: string; up: boolean; spark: string };

const quotes: Quote[] = [
  { ticker: "XAU", name: "Gold / USD", price: "4,780.20", change: "+0.62%", up: true, spark: "2,15 14,12 25,13 37,6 49,8 61,3 75,5" },
  { ticker: "DXY", name: "US Dollar Index", price: "98.90", change: "-0.34%", up: false, spark: "2,4 14,7 25,5 37,11 49,9 61,15 75,12" },
  { ticker: "WTI", name: "Crude Oil", price: "93.04", change: "-1.28%", up: false, spark: "2,3 14,5 25,6 37,12 49,10 61,16 75,14" },
  { ticker: "TNX", name: "US 10Y Yield", price: "4.23%", change: "-0.08%", up: false, spark: "2,5 14,7 25,6 37,10 49,8 61,14 75,12" },
  { ticker: "EURUSD", name: "EUR / USD", price: "1.0865", change: "+0.12%", up: true, spark: "2,15 14,13 25,14 37,9 49,10 61,5 75,7" },
  { ticker: "NVDA", name: "NVIDIA", price: "118.90", change: "+2.58%", up: true, spark: "2,17 14,14 25,15 37,9 49,7 61,4 75,2" },
];

const navGroups: { label: string; items: { label: Surface; icon: typeof Activity }[] }[] = [
  { label: "Desk", items: [{ label: "Home", icon: LayoutGrid }, { label: "Brief", icon: FileText }, { label: "Playbook", icon: BookOpen }, { label: "Gold", icon: Star }] },
  { label: "Workspace", items: [{ label: "Dash", icon: BarChart3 }, { label: "Lab", icon: FlaskConical }, { label: "Signals", icon: Zap }] },
  { label: "Markets", items: [{ label: "Markets", icon: LineChart }, { label: "Screener", icon: Search }, { label: "Sectors", icon: LayoutGrid }, { label: "Heatmap", icon: Activity }, { label: "Rates & FX", icon: Globe2 }] },
  { label: "Intel", items: [{ label: "News", icon: FileText }, { label: "Papers", icon: BookOpen }, { label: "Research", icon: Sparkles }, { label: "Documents", icon: FileText }, { label: "Geo", icon: Globe2 }] },
  { label: "Book", items: [{ label: "Watch", icon: Bookmark }, { label: "Port", icon: BriefcaseBusiness }, { label: "Learn", icon: BookOpen }] },
];

const searchItems = [
  ["XAU", "Gold / USD", "Commodity"],
  ["NVDA", "NVIDIA", "NASDAQ"],
  ["TNX", "US 10Y Yield", "Rates"],
  ["EURUSD", "EUR / USD", "FX"],
  ["AAPL", "Apple Inc", "NASDAQ"],
  ["DXY", "US Dollar Index", "Macro"],
  ["BRIEF", "Daily Dispatch Brief", "Published"],
  ["PLAYBOOK", "Gold Desk Playbook", "Published"],
];

const bottomNav: { label: string; icon: typeof LayoutGrid }[] = [
  { label: "Home", icon: LayoutGrid },
  { label: "Brief", icon: FileText },
  { label: "Gold", icon: Star },
  { label: "Markets", icon: LineChart },
  { label: "More", icon: Menu },
];

function Mark() {
  return <span className="fd-mark">D</span>;
}

function Spark({ points, up }: { points: string; up: boolean }) {
  return <svg className={`fd-spark ${up ? "fd-up" : "fd-down"}`} viewBox="0 0 77 20" aria-label="session chart"><polyline points={points} fill="none" stroke="currentColor" strokeWidth="1.7" vectorEffect="non-scaling-stroke" /></svg>;
}

function SectionTitle({ eyebrow, title, aside }: { eyebrow?: string; title: string; aside?: string }) {
  return <div className="fd-section-title">{eyebrow && <span className="fd-eyebrow">{eyebrow}</span>}<h2>{title}</h2>{aside && <span className="fd-section-aside">{aside}</span>}</div>;
}

function PriceRow({ quote, saved, onSave, onSelect }: { quote: Quote; saved: boolean; onSave: () => void; onSelect: () => void }) {
  return <div className="fd-quote-row" onClick={onSelect} role="button" tabIndex={0} onKeyDown={(e) => e.key === "Enter" && onSelect()}>
    <button className={`fd-star ${saved ? "saved" : ""}`} aria-label={`${saved ? "Remove" : "Add"} ${quote.ticker} ${saved ? "from" : "to"} watchlist`} onClick={(e) => { e.stopPropagation(); onSave(); }}><Star size={14} fill={saved ? "currentColor" : "none"} /></button>
    <div className="fd-ticker"><strong>{quote.ticker}</strong><span>{quote.name}</span></div>
    <Spark points={quote.spark} up={quote.up} />
    <strong className="fd-price">{quote.price}</strong>
    <span className={`fd-change ${quote.up ? "fd-up" : "fd-down"}`}>{quote.up ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}{quote.change}</span>
  </div>;
}

export function FullDesk() {
  const [surface, setSurface] = useState<Surface>("Home");
  const [search, setSearch] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [live, setLive] = useState(true);
  const [saved, setSaved] = useState<string[]>(["XAU"]);
  const [selectedTicker, setSelectedTicker] = useState("XAU");
  const [briefOpen, setBriefOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const [membershipOpen, setMembershipOpen] = useState(false);
  const [toast, setToast] = useState("");

  const results = useMemo(() => searchItems.filter(([ticker, name, type]) => `${ticker} ${name} ${type}`.toLowerCase().includes(search.toLowerCase())), [search]);
  const toggleSave = (ticker: string) => {
    setSaved((current) => current.includes(ticker) ? current.filter((item) => item !== ticker) : [...current, ticker]);
    setToast(saved.includes(ticker) ? `${ticker} removed from your book` : `${ticker} saved to your book`);
    window.setTimeout(() => setToast(""), 2200);
  };
  const go = (next: Surface) => { setSurface(next); setMoreOpen(false); };

  return <div className="fd-shell">
    <style>{`
      @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=IBM+Plex+Mono:wght@400;500;600&family=Public+Sans:wght@400;500;600;700&display=swap');
      .fd-shell{--paper:#efeee9;--paper2:#e4e3dc;--carbon:#dce0dd;--carbon2:#d2d7d3;--ink:#17191c;--muted:#62686c;--faint:#888e90;--rule:rgba(23,25,28,.16);--hair:rgba(23,25,28,.08);--gold:#7d5816;--leaf:#b2873e;--wash:rgba(125,88,22,.11);--green:#21694d;--red:#a53d35;min-height:100vh;background:var(--paper);color:var(--ink);font-family:'Public Sans',sans-serif;overflow:hidden}
      .fd-shell *{box-sizing:border-box}.fd-shell button,.fd-shell input{font:inherit}.fd-shell button{cursor:pointer}.fd-shell svg{display:block}.fd-shell:focus-visible{outline:2px solid var(--gold)}
      .fd-top{height:25px;background:var(--paper2);border-bottom:1px solid var(--hair);display:flex;align-items:center;gap:22px;padding:0 20px;color:var(--muted);font:10px 'IBM Plex Mono',monospace;white-space:nowrap;overflow:hidden}.fd-top b{font-weight:500;color:var(--green)}.fd-top span:last-child{margin-left:auto}
      .fd-layout{display:grid;grid-template-columns:196px minmax(0,1fr);height:calc(100vh - 25px)}
      .fd-rail{background:#e4e3dc;border-right:1px solid var(--rule);padding:25px 12px 18px;overflow:auto}.fd-brand{display:flex;align-items:center;gap:9px;margin:0 11px 35px}.fd-mark{display:grid;place-items:center;width:29px;height:29px;border-radius:7px;background:#212326;color:#d7ad54;font:italic 21px Georgia,serif}.fd-brand strong{display:block;font:600 15px Fraunces,serif;line-height:1}.fd-brand small{display:block;margin-top:5px;color:var(--muted);font:9px 'IBM Plex Mono',monospace;letter-spacing:.13em}.fd-group{margin:22px 0 8px;padding:0 12px;color:var(--faint);font-size:9px;font-weight:700;letter-spacing:.19em;text-transform:uppercase}.fd-nav{display:flex;flex-direction:column;gap:2px}.fd-nav button{display:flex;align-items:center;gap:10px;width:100%;padding:8px 11px;border:0;border-radius:4px;background:transparent;color:#555c60;text-align:left;font:500 11px 'IBM Plex Mono',monospace;transition:background .16s,color .16s,transform .16s}.fd-nav button:hover{background:var(--wash);color:var(--ink);transform:translateX(2px)}.fd-nav button.active{background:var(--wash);box-shadow:inset 2px 0 var(--gold);color:var(--ink)}.fd-nav button.active svg{color:var(--gold)}.fd-nav button.primary{font:600 16px Fraunces,serif;padding-top:7px;padding-bottom:7px}.fd-rail-foot{margin-top:28px;padding:16px 10px 0;border-top:1px solid var(--hair);color:var(--faint);font:10px/1.7 'IBM Plex Mono',monospace}
      .fd-main{min-width:0;display:flex;flex-direction:column;overflow:hidden}.fd-command{min-height:66px;display:flex;align-items:center;gap:18px;padding:0 27px;border-bottom:1px solid var(--rule)}.fd-command-brand{display:flex;align-items:center;gap:8px;white-space:nowrap}.fd-command-brand strong{font:700 17px Fraunces,serif}.fd-command-brand small{color:var(--muted);font-size:10px;font-weight:600;letter-spacing:.16em}.fd-search{position:relative;display:flex;flex:1;max-width:610px}.fd-search input{height:37px;width:100%;padding:0 48px 0 13px;background:var(--carbon);border:1px solid var(--rule);border-radius:4px;outline:0;color:var(--ink);font:12px 'IBM Plex Mono',monospace}.fd-search input:focus{border-color:var(--leaf);box-shadow:0 0 0 3px var(--wash)}.fd-search button{position:absolute;right:0;top:0;height:37px;width:45px;border:0;border-radius:0 4px 4px 0;background:var(--gold);color:var(--paper);font:600 10px 'IBM Plex Mono',monospace;letter-spacing:.08em}.fd-results{position:absolute;z-index:40;top:43px;left:0;right:0;padding:6px;background:var(--paper);border:1px solid var(--rule);border-radius:5px;box-shadow:0 12px 25px rgba(20,22,24,.15)}.fd-result{display:flex;align-items:center;justify-content:space-between;width:100%;padding:9px 10px;border:0;background:none;text-align:left}.fd-result:hover{background:var(--wash)}.fd-result b{font:600 11px 'IBM Plex Mono',monospace}.fd-result span{color:var(--muted);font-size:11px}.fd-command-right{margin-left:auto;display:flex;align-items:center;gap:13px;color:var(--muted);white-space:nowrap;font:10px 'IBM Plex Mono',monospace}.fd-live{display:flex;align-items:center;gap:6px}.fd-live i{width:6px;height:6px;border-radius:50%;background:var(--green);box-shadow:0 0 0 3px rgba(33,105,77,.12)}.fd-live.paused i{background:var(--faint);box-shadow:none}.fd-ctl{display:flex;gap:5px}.fd-ctl button{display:grid;place-items:center;width:25px;height:25px;border:1px solid var(--rule);border-radius:3px;color:var(--muted);background:transparent}.fd-ctl button:hover{color:var(--ink);border-color:var(--gold)}.fd-auth{display:flex;gap:8px;align-items:center}.fd-auth button{border:0;padding:7px 9px;background:transparent;color:var(--muted);font-size:11px}.fd-auth .premium{background:var(--gold);color:var(--paper);border-radius:3px;font-weight:700}
      .fd-content{max-width:1280px;width:100%;margin:0 auto;padding:32px 44px 70px;overflow:auto}.fd-welcome{display:flex;justify-content:space-between;align-items:flex-end;padding-bottom:24px;border-bottom:1px solid var(--rule);animation:fd-in .45s ease both}.fd-eyebrow{display:block;color:var(--gold);font:600 10px 'IBM Plex Mono',monospace;letter-spacing:.16em;text-transform:uppercase}.fd-welcome h1{max-width:700px;margin:9px 0 8px;font:600 clamp(32px,4vw,51px)/.98 Fraunces,serif;letter-spacing:-.045em}.fd-welcome p{margin:0;color:var(--muted);font-size:14px}.fd-date{text-align:right;color:var(--muted);font:10px/1.7 'IBM Plex Mono',monospace}.fd-date strong{display:block;color:var(--ink);font-weight:500}
      .fd-grid{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(290px,.82fr);gap:38px;padding-top:28px}.fd-section-title{display:flex;align-items:baseline;gap:11px;margin-bottom:12px}.fd-section-title h2{margin:0;font:600 19px Fraunces,serif;letter-spacing:-.02em}.fd-section-aside{margin-left:auto;color:var(--faint);font:10px 'IBM Plex Mono',monospace;letter-spacing:.1em;text-transform:uppercase}
      .fd-regime{display:grid;grid-template-columns:1.1fr .9fr;min-height:224px;background:#282b2b;color:#f1eee6;border-radius:6px;overflow:hidden;animation:fd-in .5s .06s ease both}.fd-regime-copy{padding:24px 26px}.fd-regime .fd-eyebrow{color:#d5ad5b}.fd-regime h3{max-width:360px;margin:10px 0 10px;font:600 30px/1.05 Fraunces,serif;letter-spacing:-.035em}.fd-regime p{max-width:380px;margin:0;color:#b9bbb5;font-size:12px;line-height:1.65}.fd-regime-side{display:flex;flex-direction:column;justify-content:space-between;padding:26px;background:linear-gradient(125deg,rgba(184,140,48,.16),rgba(255,255,255,.025));border-left:1px solid rgba(238,236,229,.1)}.fd-score{color:#d9b568;font:600 46px 'IBM Plex Mono',monospace;letter-spacing:-.08em}.fd-score small{display:block;margin-top:-5px;color:#93968f;font:10px 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase}.fd-scenarios{display:flex;gap:7px;flex-wrap:wrap}.fd-scenarios span{padding:4px 7px;border:1px solid rgba(215,175,91,.28);border-radius:3px;color:#c8c8be;font:10px 'IBM Plex Mono',monospace}
      .fd-brief{padding:23px 0 20px;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);margin-top:27px}.fd-brief h3{margin:0 0 9px;font:600 25px/1.08 Fraunces,serif}.fd-brief p{max-width:710px;margin:0 0 11px;color:var(--muted);font-size:13px;line-height:1.7}.fd-detail{max-width:710px;margin:11px 0;padding:11px 13px;background:var(--wash);border-left:2px solid var(--gold);font-size:12px;line-height:1.65}.fd-link{padding:0;border:0;background:none;color:var(--gold);font:600 11px 'IBM Plex Mono',monospace}.fd-link:hover{text-decoration:underline}
      .fd-book{padding:21px 0;border-bottom:1px solid var(--rule)}.fd-book-box{display:flex;justify-content:space-between;gap:15px;align-items:center;padding:16px;background:var(--carbon);border:1px solid var(--hair);border-radius:5px}.fd-book-box strong{display:block;margin-bottom:4px;font:600 15px Fraunces,serif}.fd-book-box p{margin:0;color:var(--muted);font-size:11px}.fd-action{display:inline-flex;align-items:center;gap:6px;flex-shrink:0;padding:8px 11px;border:1px solid var(--gold);border-radius:3px;background:transparent;color:var(--gold);font:600 10px 'IBM Plex Mono',monospace}.fd-action:hover{background:var(--gold);color:var(--paper)}
      .fd-side-section{padding-bottom:25px;margin-bottom:24px;border-bottom:1px solid var(--rule)}.fd-quotes{border-top:1px solid var(--hair)}.fd-quote-row{display:grid;grid-template-columns:23px 1fr 78px 73px 65px;align-items:center;gap:8px;min-height:52px;border-bottom:1px solid var(--hair);cursor:pointer}.fd-quote-row:hover{background:var(--wash)}.fd-star{display:grid;place-items:center;color:var(--faint)}.fd-star:hover,.fd-star.saved{color:var(--gold)}.fd-ticker strong{display:block;font:600 11px 'IBM Plex Mono',monospace}.fd-ticker span{display:block;margin-top:2px;color:var(--muted);font-size:10px;white-space:nowrap}.fd-price{text-align:right;font:11px 'IBM Plex Mono',monospace;font-weight:500}.fd-change{display:flex;align-items:center;justify-content:flex-end;gap:2px;font:11px 'IBM Plex Mono',monospace}.fd-up{color:var(--green)}.fd-down{color:var(--red)}.fd-spark{width:77px;height:20px}.fd-next{display:grid;gap:7px}.fd-route{display:flex;align-items:center;justify-content:space-between;padding:12px 13px;border:1px solid var(--hair);background:rgba(229,227,219,.42);text-align:left;transition:background .16s,transform .16s}.fd-route:hover{background:var(--wash);transform:translateX(2px)}.fd-route strong{display:block;font:600 13px Fraunces,serif}.fd-route span{display:block;color:var(--muted);font-size:10px}.fd-route svg{color:var(--gold)}
      .fd-member{position:relative;padding:18px;background:linear-gradient(140deg,var(--carbon),#e9e5da);border:1px solid var(--hair);border-radius:5px}.fd-member .fd-eyebrow{color:var(--gold)}.fd-member h3{margin:8px 0 6px;font:600 20px Fraunces,serif}.fd-member p{margin:0 0 13px;color:var(--muted);font-size:11px;line-height:1.55}.fd-close{position:absolute;right:10px;top:8px;border:0;color:var(--faint);background:none}.fd-primary{border:0!important;background:var(--gold)!important;color:var(--paper)!important;font-weight:700}
      .fd-bottom{display:none}.fd-more{position:fixed;inset:0;z-index:100;background:rgba(23,25,28,.28);display:flex;align-items:flex-end}.fd-more-card{width:100%;max-height:82vh;overflow:auto;padding:20px 16px 30px;background:var(--paper);border-radius:16px 16px 0 0;box-shadow:0 -10px 30px rgba(23,25,28,.2)}.fd-more-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}.fd-more-head h2{margin:0;font:600 22px Fraunces,serif}.fd-more-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px}.fd-more-grid button{display:flex;align-items:center;gap:9px;padding:12px;border:1px solid var(--hair);background:var(--carbon);text-align:left;color:var(--ink);font-size:12px}.fd-more-grid button.active{color:var(--gold);border-color:var(--gold)}.fd-toast{position:fixed;right:22px;bottom:22px;z-index:120;padding:10px 13px;background:#282b2b;color:#f1eee6;border-radius:4px;font:11px 'IBM Plex Mono',monospace;box-shadow:0 8px 20px rgba(23,25,28,.2)}
      @keyframes fd-in{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:none}}@media(prefers-reduced-motion:reduce){.fd-shell *{animation:none!important;transition:none!important}}
      @media(max-width:980px){.fd-layout{grid-template-columns:166px minmax(0,1fr)}.fd-content{padding-left:26px;padding-right:26px}.fd-command{padding:0 18px;gap:11px}.fd-command-brand small{display:none}.fd-command-right{gap:7px}.fd-auth button{padding-left:4px;padding-right:4px}}
      @media(max-width:700px){.fd-shell{overflow:visible;min-height:100dvh}.fd-top{padding:0 14px;gap:16px}.fd-top span:nth-child(n+3){display:none}.fd-layout{display:block;height:auto}.fd-rail{display:none}.fd-command{min-height:59px;padding:10px 14px;flex-wrap:wrap;gap:10px}.fd-command-brand{flex:1}.fd-command-brand strong{font-size:16px}.fd-search{order:3;flex-basis:100%;max-width:none}.fd-command-right{margin-left:0}.fd-command-right>span,.fd-ctl button:first-child{display:none}.fd-auth button{padding:6px 4px}.fd-main{overflow:visible}.fd-content{padding:25px 16px 84px;overflow:visible}.fd-welcome{display:block}.fd-welcome h1{font-size:39px;max-width:345px}.fd-date{margin-top:16px;text-align:left}.fd-grid{display:block;padding-top:24px}.fd-regime{grid-template-columns:1fr}.fd-regime-side{min-height:130px;border-left:0;border-top:1px solid rgba(238,236,229,.1);flex-direction:row;align-items:flex-end}.fd-regime h3{font-size:28px}.fd-side-section{margin-top:28px}.fd-quote-row{grid-template-columns:22px 1fr 66px 65px}.fd-quote-row .fd-spark{display:none}.fd-bottom{position:fixed;z-index:60;display:flex;bottom:0;left:0;right:0;padding-bottom:env(safe-area-inset-bottom);background:var(--paper2);border-top:1px solid var(--rule)}.fd-bottom button{display:flex;flex:1;flex-direction:column;align-items:center;gap:3px;padding:9px 2px 7px;border:0;border-top:2px solid transparent;background:transparent;color:var(--muted);font-size:10px;font-weight:600}.fd-bottom button.active{border-top-color:var(--gold);color:var(--gold)}.fd-bottom svg{width:17px;height:17px}.fd-toast{right:12px;bottom:76px}.fd-book-box{align-items:flex-start;flex-direction:column}.fd-action{width:100%;justify-content:center}}
      @media(max-width:390px){.fd-content{padding-left:13px;padding-right:13px}.fd-top span:nth-child(2){display:none}.fd-regime-copy{padding:22px 20px}.fd-regime-side{padding:21px 20px}}
    `}</style>
     <div className="fd-top"><span>DISPATCH MARKETS</span><b>LIVE</b><span>·</span><span>EQUITY / RATES / COMMODITIES / FX</span><span>18 APR 2026 · 08:42 UTC</span></div>
    <div className="fd-layout">
      <aside className="fd-rail"><div className="fd-brand"><Mark /><div><strong>The Dispatch</strong><small>MARKETS</small></div></div>
        {navGroups.map((group) => <div key={group.label}><div className="fd-group">{group.label}</div><nav className="fd-nav">{group.items.map(({ label, icon: Icon }) => <button key={label} className={`${surface === label ? "active " : ""}${group.label === "Desk" ? "primary" : ""}`} onClick={() => go(label)}><Icon size={group.label === "Desk" ? 16 : 14} />{label}</button>)}</nav></div>)}
        <div className="fd-group">Account</div><nav className="fd-nav"><button onClick={() => go("Settings")} className={surface === "Settings" ? "active" : ""}><Settings size={14} />Settings</button><button onClick={() => setMembershipOpen(true)}><CircleHelp size={14} />About & Guide</button></nav><div className="fd-rail-foot">Live prices and desk tools are free.<br />Premium adds xAI research.</div>
      </aside>
      <main className="fd-main">
        <header className="fd-command"><div className="fd-command-brand"><Mark /><strong>THE DISPATCH</strong><small>MARKETS</small></div>
           <div className="fd-search"><Search size={15} style={{ position: "absolute", left: 12, top: 11, color: "var(--muted)", zIndex: 1 }} /><input aria-label="Search tickers, commands, and research" style={{ paddingLeft: 35 }} value={search} onFocus={() => setSearchOpen(true)} onChange={(e) => { setSearch(e.target.value); setSearchOpen(true); }} onKeyDown={(e) => e.key === "Escape" && setSearchOpen(false)} placeholder="Enter ticker or command — AAPL, NEWS, WATCH" /><button onClick={() => setSearchOpen(true)}>GO</button>{searchOpen && <div className="fd-results">{results.length ? results.map(([ticker, name, type]) => <button className="fd-result" key={ticker} onClick={() => { setSearch(ticker); setSelectedTicker(ticker); setSearchOpen(false); }}><b>{ticker}</b><span>{name} · {type}</span></button>) : <div className="fd-result"><span>No desk result. Try XAU, NVDA, TNX, or EURUSD.</span></div>}</div>}</div>
          <div className="fd-command-right"><span className={`fd-live ${live ? "" : "paused"}`}><i />{live ? "LIVE" : "PAUSED"}</span><span>08:42:16</span><div className="fd-ctl"><button aria-label={live ? "Pause live updates" : "Resume live updates"} onClick={() => setLive(!live)}>{live ? <Pause size={12} /> : <Play size={12} />}</button><button aria-label="Refresh prices" onClick={() => setToast("Market tape refreshed")}><Activity size={13} /></button></div><div className="fd-auth"><button onClick={() => setMembershipOpen(true)}>Sign in</button><button className="premium" onClick={() => setMembershipOpen(true)}>Premium · £15/mo</button></div></div>
        </header>
        <div className="fd-content">
          {surface === "Home" ? <><section className="fd-welcome"><div><span className="fd-eyebrow">Friday, 18 April 2026 · Opening desk</span><h1>Good morning. Start with the state of the market.</h1><p>A focused read on gold, macro conditions, and the moves worth keeping in view.</p></div><div className="fd-date"><strong>YOUR COMMAND CENTER</strong>Updated as sessions move</div></section>
            <div className="fd-grid"><div><SectionTitle title="Market regime" aside="Live context" /><section className="fd-regime"><div className="fd-regime-copy"><span className="fd-eyebrow">Risk / reward</span><h3>Defensive, but not dislocated</h3><p>Gold is holding its bid as the dollar softens. Oil volatility remains the macro fault line; equities are absorbing the news rather than chasing it.</p></div><div className="fd-regime-side"><div className="fd-score">68<small>regime score / 100</small></div><div className="fd-scenarios"><span>Gold · bid</span><span>Dollar · soft</span><span>Oil · volatile</span></div></div></section>
              <section className="fd-brief"><SectionTitle title="Today's brief" aside="Desk note · 6 min" /><h3>Three things that can change the gold thesis this week</h3><p>Central-bank demand is doing the quiet work, but the next leg depends on the dollar and real yields. Here is the cleanest way to frame the decision before the US session gets busy.</p>{briefOpen && <div className="fd-detail">The base case is constructive, not certain: watch DXY below 99, real yields for confirmation, and the $4,700 area as the first level that would challenge the current structure.</div>}<button className="fd-link" onClick={() => setBriefOpen(!briefOpen)}>{briefOpen ? "Hide brief detail" : "Read today's brief →"}</button></section>
              <section className="fd-book"><SectionTitle title="Your book" aside="Watchlist" /><div className="fd-book-box"><div>{saved.length ? <><strong>{saved.length} name{saved.length > 1 ? "s" : ""} in your book</strong><p>{saved.join(" · ")} · Return to the levels that matter.</p></> : <><strong>Your book is empty</strong><p>Keep the names and levels you want to return to here.</p></>}</div><button className="fd-action" onClick={() => saved.length ? go("Watch") : toggleSave("XAU")}><Plus size={13} />{saved.length ? "Open watchlist" : "Add first ticker"}</button></div></section>
            </div><aside><section className="fd-side-section"><SectionTitle title="Session movers" aside="Tracked" /><div className="fd-quotes">{quotes.map((quote) => <PriceRow key={quote.ticker} quote={quote} saved={saved.includes(quote.ticker)} onSave={() => toggleSave(quote.ticker)} onSelect={() => setSelectedTicker(quote.ticker)} />)}</div></section>
              <section className="fd-side-section"><SectionTitle title="Start here" aside="Desk routes" /><div className="fd-next">{[["Brief", "The morning read"], ["Gold", "Weekly conditional playbook"], ["Markets", "Live prices and context"], ["Lab", "Research tools"]].map(([label, copy]) => <button className="fd-route" key={label} onClick={() => go(label as Surface)}><span><strong>{label}</strong><span>{copy}</span></span><ChevronRight size={16} /></button>)}</div></section>
              <section className="fd-member"><button className="fd-close" onClick={(e) => (e.currentTarget.parentElement!.style.display = "none")} aria-label="Dismiss premium message"><X size={14} /></button><span className="fd-eyebrow">Premium research</span><h3>Keep the desk close.</h3><p>Gold Desk playbooks, Daily Dispatch Brief, Dispatch Expert chat, and xAI-powered research. Stripe-managed billing, £15/month.</p><button className="fd-action fd-primary" onClick={() => setMembershipOpen(true)}>See Premium <ChevronRight size={13} /></button></section>
            </aside></div></> : <section className="fd-welcome"><div><span className="fd-eyebrow">Dispatch Markets · workspace</span><h1>{surface}</h1><p>{surface === "Playbook" ? "The weekly gold work: conditional scenarios, levels, and invalidation." : surface === "Brief" ? "The daily house view, written for the opening hour." : `A focused workspace for ${surface.toLowerCase()} — built around context, not prediction theater.`}</p></div><div className="fd-date"><strong>SELECTED TICKER</strong>{selectedTicker}<br /><button className="fd-action" onClick={() => go("Home")}>Back to Home</button></div></section>}
        </div>
        <nav className="fd-bottom">{bottomNav.map(({ label, icon: Icon }) => <button key={label} className={surface === label ? "active" : ""} onClick={() => label === "More" ? setMoreOpen(true) : go(label as Surface)}><Icon size={17} />{label}</button>)}</nav>
      </main>
    </div>
    {moreOpen && <div className="fd-more" onClick={() => setMoreOpen(false)}><div className="fd-more-card" onClick={(e) => e.stopPropagation()}><div className="fd-more-head"><h2>All destinations</h2><button className="fd-close" onClick={() => setMoreOpen(false)}><X size={18} /></button></div><div className="fd-more-grid">{navGroups.flatMap((group) => group.items).map(({ label, icon: Icon }) => <button key={label} className={surface === label ? "active" : ""} onClick={() => go(label)}><Icon size={15} />{label}</button>)}<button onClick={() => go("Settings")}><Settings size={15} />Settings</button><button onClick={() => setMembershipOpen(true)}><Sparkles size={15} />Premium & Guide</button></div></div></div>}
    {membershipOpen && <div className="fd-more" onClick={() => setMembershipOpen(false)}><div className="fd-more-card" style={{ maxWidth: 520, margin: "auto", borderRadius: 8 }} onClick={(e) => e.stopPropagation()}><div className="fd-more-head"><h2>About the desk</h2><button className="fd-close" onClick={() => setMembershipOpen(false)}><X size={18} /></button></div><span className="fd-eyebrow">The Dispatch Markets</span><p style={{ color: "var(--muted)", lineHeight: 1.7, fontSize: 13, margin: "10px 0 18px" }}>A gold and macro research workspace. Every Saturday the Gold Desk builds a conditional weekly playbook — market structure, key levels, volatility and dollar context, and the events that could change the thesis — stated as scenarios, never predictions.</p><div className="fd-detail"><strong>Premium · £15/month</strong><br />Gold Desk weekly playbook · Daily Dispatch Brief · Dispatch Expert chat · AI research with xAI.<br /><small style={{ color: "var(--muted)" }}>Billing is managed securely through Stripe.</small></div><button className="fd-action fd-primary" style={{ width: "100%", justifyContent: "center", marginTop: 14 }} onClick={() => setMembershipOpen(false)}>Continue to membership <ChevronRight size={14} /></button></div></div>}
    {toast && <div className="fd-toast">{toast}</div>}
  </div>;
}

export default FullDesk;