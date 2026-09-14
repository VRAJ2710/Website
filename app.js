// API CONFIG — Finnhub proxied via /api/finnhub (key never exposed to browser)
// ═══════════════════════════════════════════════════════════

// ── Chart request gate ──────────────────────────────────────
// Several loaders batch their own chart fetches (sector timeframes, sparkline
// priority tiers, sector holdings, per-page loads). Each batch is polite on its
// own, but they run concurrently, and the combined burst put 70+ simultaneous
// invocations on /api/yahoo-chart. Cloudflare kills functions at that
// concurrency and answers with an HTML 500 error page, so the charts that were
// dropped showed "no data" — verified against production 2026-08-13.
//
// One shared gate across every caller keeps the real in-flight count bounded no
// matter how many batch loops are running.
// Yahoo rate-limits on request RATE, not parallelism, so a concurrency cap on
// its own is not enough: the screener alone asks for ~100 sparklines, and fired
// back to back they still trip the limit. Pacing the launches spreads that same
// work over a few seconds, which upstream accepts.
const _CHART_GATE_MAX = 6;
const _CHART_GATE_SPACING_MS = 90;
let _chartGateActive = 0;
let _chartGateLastStart = 0;
const _chartGateQueue = [];

function _chartGateStart(run) {
  _chartGateActive++;
  const wait = Math.max(0, _chartGateLastStart + _CHART_GATE_SPACING_MS - Date.now());
  _chartGateLastStart = Date.now() + wait;
  if (wait) setTimeout(run, wait); else run();
}

function _chartGateRelease() {
  _chartGateActive--;
  const next = _chartGateQueue.shift();
  if (next) _chartGateStart(next);
}

/** fetch() for /api/yahoo-chart — at most _CHART_GATE_MAX in flight, paced. */
function chartFetch(url, opts) {
  return new Promise((resolve, reject) => {
    const run = () => {
      let settled = false;
      const done = () => { if (!settled) { settled = true; _chartGateRelease(); } };
      // Release on settle either way, so a rejection cannot wedge the queue.
      fetch(url, opts).then(
        (r) => { done(); resolve(r); },
        (e) => { done(); reject(e); }
      );
    };
    if (_chartGateActive < _CHART_GATE_MAX) _chartGateStart(run);
    else _chartGateQueue.push(run);
  });
}

// ═══════════════════════════════════════════════════════════
// CORE DATA
// ═══════════════════════════════════════════════════════════
const P = {
  SPX:{p:6824,c:0.11},DJIA:{p:47918,c:-0.56},IXIC:{p:22635,c:0.35},FTSE:{p:8418,c:0.22},
  DAX:{p:22840,c:0.68},N225:{p:38420,c:1.12},NSEI:{p:23190,c:0.45},HSI:{p:21780,c:-0.31},
  AAPL:{p:212.84,c:0.48},NVDA:{p:118.90,c:2.58},XOM:{p:142.80,c:0.72},MSFT:{p:388.42,c:0.91},
  AVGO:{p:218.42,c:1.34},TSLA:{p:248.60,c:-1.82},AMZN:{p:186.50,c:1.12},GOOGL:{p:165.30,c:0.85},
  META:{p:512.40,c:1.45},JPM:{p:198.60,c:0.32},GS:{p:478.20,c:0.56},AMD:{p:162.80,c:1.92},
  BTC:{p:71500,c:3.81},ETH:{p:1842,c:2.14},SOL:{p:148.50,c:4.20},XRP:{p:0.52,c:1.85},
  XAU:{p:4780,c:0.62},WTI:{p:93.04,c:-1.28},SLV:{p:28.45,c:1.15},NG:{p:2.18,c:-2.45},
  EURUSD:{p:1.0865,c:0.12},GBPUSD:{p:1.2645,c:-0.08},USDJPY:{p:154.32,c:0.22},
  DXY:{p:98.9,c:-0.34},VIX:{p:22.4,c:-8.2},
  // Extended seed prices — updated from live data Jun 2026
  NFLX:{p:77,c:0},DIS:{p:95,c:0},V:{p:327,c:0},MA:{p:490,c:0},PYPL:{p:65,c:0},
  CRM:{p:152,c:0},ORCL:{p:184,c:0},ADBE:{p:195,c:0},INTC:{p:134,c:0},QCOM:{p:226,c:0},
  MU:{p:1134,c:0},CSCO:{p:55,c:0},NOW:{p:95,c:0},PANW:{p:288,c:0},CRWD:{p:685,c:0},
  PLTR:{p:128,c:0},COIN:{p:163,c:0},UBER:{p:72,c:0},SHOP:{p:110,c:0},SNOW:{p:232,c:0},
  RIVN:{p:12,c:0},F:{p:11,c:0},GM:{p:52,c:0},BA:{p:223,c:0},CAT:{p:986,c:0},
  DE:{p:450,c:0},NKE:{p:45,c:0},SBUX:{p:82,c:0},MCD:{p:279,c:0},JNJ:{p:228,c:0},
  UNH:{p:401,c:0},PFE:{p:24,c:0},LLY:{p:1099,c:0},ABBV:{p:216,c:0},MRK:{p:114,c:0},
  WMT:{p:117,c:0},COST:{p:951,c:0},HD:{p:334,c:0},BAC:{p:56,c:0},WFC:{p:82,c:0},
  C:{p:68,c:0},BLK:{p:1050,c:0},ISRG:{p:407,c:0},TSM:{p:462,c:0},ASML:{p:1930,c:0},
  NVO:{p:43,c:0},SAP:{p:295,c:0},BABA:{p:100,c:0},BP:{p:30,c:0},SHEL:{p:68,c:0},
  ARM:{p:408,c:0},SMCI:{p:35,c:0},MRVL:{p:308,c:0},KO:{p:80,c:0},PEP:{p:141,c:0},
  PG:{p:148,c:0},ABNB:{p:139,c:0},DASH:{p:155,c:0},BRKB:{p:489,c:0},ACN:{p:125,c:0},
  SONY:{p:20,c:0},VALE:{p:16,c:0},RIO:{p:99,c:0},INFY:{p:11,c:0},
  COFFEE:{p:266,c:0},PLAT:{p:1678,c:0},COCOA:{p:4588,c:0},
  TMO:{p:464,c:0},ABT:{p:88,c:0},PM:{p:173,c:0},NEE:{p:86,c:0},RTX:{p:182,c:0},
  HON:{p:224,c:0},T:{p:28,c:0},VZ:{p:43,c:0},MS:{p:227,c:0},SCHW:{p:75,c:0},
  TXN:{p:332,c:0},AMAT:{p:185,c:0},LRCX:{p:75,c:0},REGN:{p:850,c:0},AMGN:{p:290,c:0},
  CVX:{p:175,c:0},COP:{p:110,c:0},INTU:{p:685,c:0},ADSK:{p:285,c:0},NET:{p:218,c:0},
  DDOG:{p:221,c:0},ZS:{p:124,c:0},UPS:{p:108,c:0},LOW:{p:230,c:0},DUK:{p:112,c:0},
  TM:{p:170,c:0},NVS:{p:149,c:0},UL:{p:58,c:0},DEO:{p:120,c:0},
  AUDUSD:{p:0.70,c:0},USDCAD:{p:1.41,c:0},USDCHF:{p:0.81,c:0},NZDUSD:{p:0.57,c:0},EURGBP:{p:0.86,c:0},
  COPPER:{p:6.34,c:0},WHEAT:{p:607,c:0},CORN:{p:411,c:0},USDMXN:{p:17.4,c:0},USDINR:{p:94.7,c:0},
  OJ:{p:185,c:0},PALLADIUM:{p:960,c:0},CAC:{p:8400,c:0},ASX200:{p:8816,c:0},KOSPI:{p:9115,c:0},
  DOGE:{p:0.083,c:0},ADA:{p:0.162,c:0},AVAX:{p:23,c:0},LINK:{p:7.94,c:0},DOT:{p:4.2,c:0},
  LTC:{p:87,c:0},UNI:{p:6.8,c:0},MATIC:{p:0.22,c:0},NEAR:{p:2.8,c:0},ALGO:{p:0.21,c:0},
  HBAR:{p:0.19,c:0},TON:{p:3.2,c:0},BCH:{p:395,c:0},XLM:{p:0.27,c:0},FIL:{p:3.1,c:0},
  APT:{p:5.8,c:0},SUI:{p:3.5,c:0},
  USDBRL:{p:5.65,c:0},LUMBER:{p:580,c:0},
  SPY:{p:682,c:0},QQQ:{p:520,c:0},IWM:{p:210,c:0},RUT:{p:2280,c:0},EEM:{p:42,c:0},
  SOXX:{p:240,c:0},TLT:{p:88,c:0},ARKK:{p:52,c:0},TNX:{p:4.2,c:0},
  XLK:{p:220,c:0},XLC:{p:95,c:0},XLY:{p:195,c:0},XLF:{p:48,c:0},XLV:{p:148,c:0},
  XLE:{p:92,c:0},XLI:{p:135,c:0},XLP:{p:82,c:0},XLB:{p:92,c:0},XLU:{p:78,c:0},XLRE:{p:42,c:0},
  RKLB:{p:28,c:0},HOOD:{p:42,c:0},MSTR:{p:380,c:0},GME:{p:28,c:0},SPOT:{p:580,c:0},
  LMT:{p:480,c:0},BMY:{p:52,c:0},GILD:{p:88,c:0},ENPH:{p:120,c:0},FSLR:{p:185,c:0},
  EOG:{p:135,c:0},SLB:{p:42,c:0},SO:{p:88,c:0},PLD:{p:112,c:0},AMT:{p:210,c:0},
  EQIX:{p:920,c:0},SPG:{p:158,c:0},O:{p:58,c:0},VRTX:{p:440,c:0},BRENT:{p:96,c:0},URA:{p:28,c:0},
  SHIB:{p:0.000018,c:0},PEPE:{p:0.000012,c:0},ATOM:{p:8.5,c:0},INJ:{p:22,c:0},
  EURJPY:{p:162,c:0},GBPJPY:{p:198,c:0},
};
// Index-level hints ONLY for Finnhub ETF→index scaling — never shown as prices
const SEED_INDEX_LEVELS = { SPX: 6824, DJIA: 47918, IXIC: 22635 };
// Wipe every seed number immediately — UI may only show feed-confirmed quotes
Object.keys(P).forEach(k => { P[k] = { p: null, c: null }; });
const BASE = JSON.parse(JSON.stringify(P));
// HIST is populated only from real data sources (Yahoo intraday, CoinGecko, or appended live ticks).
// Cards with insufficient real history will render "Chart unavailable" — never fabricate a line.
const HIST = {};
Object.keys(P).forEach(k=>{HIST[k]=[];});

const IDX = [
  {tk:"SPX",nm:"S&P 500",rg:"US"},{tk:"DJIA",nm:"Dow Jones",rg:"US"},{tk:"IXIC",nm:"Nasdaq",rg:"US"},
  {tk:"FTSE",nm:"FTSE 100",rg:"UK"},{tk:"DAX",nm:"DAX",rg:"EU"},{tk:"N225",nm:"Nikkei 225",rg:"JP"},
  {tk:"NSEI",nm:"Nifty 50",rg:"IN"},{tk:"HSI",nm:"Hang Seng",rg:"HK"}
];

const A = [
  {tk:"AAPL",nm:"Apple Inc",cat:"Stock",ex:"NASDAQ",sc:68,se:"Neutral",ra:"Hold",beta:1.18,pe:"33.4x",mc:"$3.28T",
   th:"iPhone 17 cycle intact but $4 gasoline and supply chain bottlenecks weighing on demand. AI integration via Apple Intelligence is the next catalyst."},
  {tk:"NVDA",nm:"NVIDIA",cat:"Stock",ex:"NASDAQ",sc:76,se:"Bullish",ra:"Strong Buy",beta:1.72,pe:"52.8x",mc:"$2.91T",
   th:"AI infrastructure spend accelerating. Data center revenue dominant. TSMC Q1 confirms demand strength. Elevated valuation justified by 90%+ growth."},
  {tk:"XOM",nm:"Exxon Mobil",cat:"Stock",ex:"NYSE",sc:84,se:"Bullish",ra:"Strong Buy",beta:0.82,pe:"12.4x",mc:"$476B",
   th:"Primary beneficiary of Iran oil shock. +42% YTD. Crude at $93 with Hormuz closed. Cash flow machine at current prices. Pioneer acquisition adds scale."},
  {tk:"MSFT",nm:"Microsoft",cat:"Stock",ex:"NASDAQ",sc:62,se:"Neutral",ra:"Hold",beta:0.92,pe:"34.2x",mc:"$2.89T",
   th:"Cloud resilient (Azure +28%) but $80B AI capex under scrutiny. Down 23% YTD. Copilot monetization slower than expected."},
  {tk:"AVGO",nm:"Broadcom",cat:"Stock",ex:"NASDAQ",sc:82,se:"Bullish",ra:"Strong Buy",beta:1.28,pe:"35.8x",mc:"$1.02T",
   th:"+18.1% in 2 weeks. Custom AI accelerator wins from Google, Meta, ByteDance. VMware integration driving margin expansion."},
  {tk:"BTC",nm:"Bitcoin",cat:"Crypto",ex:"GLOBAL",sc:65,se:"Neutral-Bull",ra:"Accumulate",beta:1.85,pe:"-",mc:"$1.43T",
   th:"ETF inflows $471M single day. MSBT launched at 0.14%. Exchange reserves at 9-year low. Range-bound $68-72K despite macro stress."},
  {tk:"XAU",nm:"Gold",cat:"Commodity",ex:"COMEX",sc:78,se:"Bullish",ra:"Buy",beta:-0.15,pe:"-",mc:"-",
   th:"$4,780, 3rd weekly gain. DXY below 99. Geopolitical safe-haven demand. Central bank buying continues globally."},
  {tk:"WTI",nm:"Crude Oil",cat:"Commodity",ex:"NYMEX",sc:72,se:"Volatile",ra:"Hold",beta:0.45,pe:"-",mc:"-",
   th:"Ceasefire crashed WTI 16% from $110+ to ~$93. But Hormuz STILL CLOSED. Iran imposing $2M/tanker fee. Ceasefire expires Apr 22."},
  {tk:"TSLA",nm:"Tesla Inc",cat:"Stock",ex:"NASDAQ",sc:58,se:"Volatile",ra:"Hold",beta:2.05,pe:"68.2x",mc:"$790B",
   th:"EV market share eroding globally. Robotaxi narrative intact but execution unclear. Energy storage strong. Valuation pricing in perfect execution."},
  {tk:"AMZN",nm:"Amazon",cat:"Stock",ex:"NASDAQ",sc:74,se:"Bullish",ra:"Buy",beta:1.22,pe:"58.4x",mc:"$1.94T",
   th:"AWS revenue acceleration to 19% growth. Retail margins expanding. Advertising segment $14B quarterly run-rate. Strong free cash flow generation."},
  {tk:"GOOGL",nm:"Alphabet",cat:"Stock",ex:"NASDAQ",sc:72,se:"Bullish",ra:"Buy",beta:1.08,pe:"22.8x",mc:"$2.05T",
   th:"Search moat remains. Cloud growing at 28%. YouTube ad revenue at $8.9B. Waymo autonomous driving optionality. AI integration across products."},
  {tk:"META",nm:"Meta Platforms",cat:"Stock",ex:"NASDAQ",sc:70,se:"Bullish",ra:"Buy",beta:1.35,pe:"24.6x",mc:"$1.31T",
   th:"Reels monetization catching up to Stories. Reality Labs losses narrowing. AI recommendation engine driving engagement. $40B+ annual buyback."},
  {tk:"JPM",nm:"JPMorgan Chase",cat:"Stock",ex:"NYSE",sc:75,se:"Bullish",ra:"Strong Buy",beta:1.12,pe:"11.8x",mc:"$580B",
   th:"Q1 trading revenue +28% YoY. NII resilient. Consumer credit stable. Investment banking pipeline recovering. Best-in-class management."},
  {tk:"GS",nm:"Goldman Sachs",cat:"Stock",ex:"NYSE",sc:71,se:"Bullish",ra:"Buy",beta:1.38,pe:"14.2x",mc:"$152B",
   th:"Q1 beat: EPS $14.12 vs $12.85 est. Trading dominant. Asset management pivot working. Platform Solutions losses contained."},
  {tk:"AMD",nm:"AMD",cat:"Stock",ex:"NASDAQ",sc:69,se:"Neutral-Bull",ra:"Buy",beta:1.68,pe:"42.6x",mc:"$264B",
   th:"MI300X AI accelerator gaining traction. Data center revenue doubling. PC cycle bottoming. Xilinx integration complete. NVDA competitor narrative."},
  {tk:"ETH",nm:"Ethereum",cat:"Crypto",ex:"GLOBAL",sc:62,se:"Neutral",ra:"Hold",beta:1.65,pe:"-",mc:"$221B",
   th:"ETH ETF approved but flows disappointing. Layer 2 adoption growing. Staking yield ~3.8%. Dencun upgrade reducing L2 costs. Network revenue declining."},
  {tk:"SOL",nm:"Solana",cat:"Crypto",ex:"GLOBAL",sc:67,se:"Neutral-Bull",ra:"Accumulate",beta:2.10,pe:"-",mc:"$68B",
   th:"Transaction throughput leader. DeFi TVL growing. NFT marketplace dominant. Firedancer client launch imminent. MEV revenue model emerging."},
  {tk:"XRP",nm:"XRP",cat:"Crypto",ex:"GLOBAL",sc:55,se:"Neutral",ra:"Hold",beta:1.42,pe:"-",mc:"$28B",
   th:"SEC clarity pending. Cross-border payment use case narrowing. Institutional adoption stalled. Ripple IPO speculation driving sentiment."},
  {tk:"SLV",nm:"Silver",cat:"Commodity",ex:"COMEX",sc:74,se:"Bullish",ra:"Buy",beta:0.35,pe:"-",mc:"-",
   th:"Industrial demand from solar panels surging. Gold-silver ratio historically elevated. Central bank buying. Supply deficit widening for third consecutive year."},
  {tk:"NG",nm:"Natural Gas",cat:"Commodity",ex:"NYMEX",sc:52,se:"Bearish",ra:"Avoid",beta:0.55,pe:"-",mc:"-",
   th:"Storage levels above 5-year average. LNG export capacity additions delayed. Mild weather forecast. Permian associated gas flooding market."},
  {tk:"EURUSD",nm:"EUR/USD",cat:"FX",ex:"FOREX",sc:60,se:"Neutral",ra:"Neutral",beta:0.15,pe:"-",mc:"-",
   th:"ECB rate path diverging from Fed. Euro area PMI recovery supports currency. Trade balance improving. DXY weakness benefiting EUR."},
  {tk:"GBPUSD",nm:"GBP/USD",cat:"FX",ex:"FOREX",sc:58,se:"Neutral",ra:"Neutral",beta:0.18,pe:"-",mc:"-",
   th:"BOE holding rates longer than expected. UK services inflation sticky. Political uncertainty post-budget. Sterling range-bound 1.25-1.28."},
  {tk:"USDJPY",nm:"USD/JPY",cat:"FX",ex:"FOREX",sc:64,se:"Volatile",ra:"Watch",beta:0.22,pe:"-",mc:"-",
   th:"BOJ intervention risk above 155. Carry trade unwinding fears. Japan Q1 GDP contracting. Rate differential narrowing slowly."},
  // ─── Additional US Stocks ───
  {tk:"NFLX",nm:"Netflix",cat:"Stock",ex:"NASDAQ",sc:72,se:"Bullish",ra:"Buy",beta:1.20,pe:"38.4x",mc:"$290B",th:"Ad-supported tier gaining subscribers. Password sharing crackdown drove growth. Content spend discipline improving margins."},
  {tk:"DIS",nm:"Walt Disney",cat:"Stock",ex:"NYSE",sc:58,se:"Neutral",ra:"Hold",beta:1.05,pe:"22.1x",mc:"$205B",th:"Streaming finally profitable. Parks remain resilient. Linear TV decline headwind. CEO succession uncertainty weighing on multiple."},
  {tk:"V",nm:"Visa Inc",cat:"Stock",ex:"NYSE",sc:78,se:"Bullish",ra:"Strong Buy",beta:0.92,pe:"29.6x",mc:"$560B",th:"Payment volume growth stable. Cross-border travel recovery intact. Network effects unassailable. Fee pricing power strong."},
  {tk:"MA",nm:"Mastercard",cat:"Stock",ex:"NYSE",sc:77,se:"Bullish",ra:"Strong Buy",beta:0.95,pe:"31.2x",mc:"$430B",th:"Premium card spending resilient. International expansion driving growth. Value-added services revenue accelerating above network fees."},
  {tk:"PYPL",nm:"PayPal Holdings",cat:"Stock",ex:"NASDAQ",sc:54,se:"Neutral",ra:"Hold",beta:1.38,pe:"14.2x",mc:"$72B",th:"Branded checkout losing share to Apple Pay. Venmo monetization slow. Cheap on earnings but secular headwinds from big tech."},
  {tk:"CRM",nm:"Salesforce",cat:"Stock",ex:"NYSE",sc:68,se:"Bullish",ra:"Buy",beta:1.18,pe:"27.4x",mc:"$256B",th:"AI features driving upsell in enterprise. Agentforce platform emerging as key differentiator. Margin expansion story on track."},
  {tk:"ORCL",nm:"Oracle",cat:"Stock",ex:"NYSE",sc:74,se:"Bullish",ra:"Buy",beta:0.88,pe:"22.6x",mc:"$380B",th:"Cloud revenue growth accelerating above 20%. AI GPU capacity partnerships with MSFT and OpenAI. Database moat still intact."},
  {tk:"ADBE",nm:"Adobe Inc",cat:"Stock",ex:"NASDAQ",sc:65,se:"Neutral",ra:"Hold",beta:1.22,pe:"26.8x",mc:"$210B",th:"Figma deal blocked but cash returned. AI Firefly features gaining traction. Creative suite subscription growth slowing at scale."},
  {tk:"INTC",nm:"Intel",cat:"Stock",ex:"NASDAQ",sc:42,se:"Bearish",ra:"Avoid",beta:1.28,pe:"N/A",mc:"$95B",th:"Foundry losses widening. Market share losses to AMD and ARM. Pat Gelsinger exit raised strategic uncertainty. Turnaround multi-year."},
  {tk:"QCOM",nm:"Qualcomm",cat:"Stock",ex:"NASDAQ",sc:70,se:"Bullish",ra:"Buy",beta:1.32,pe:"15.8x",mc:"$178B",th:"Snapdragon AI PC chip gaining PC market. Auto diversification on track. Smartphone cycle recovery supporting near-term earnings."},
  {tk:"MU",nm:"Micron Technology",cat:"Stock",ex:"NASDAQ",sc:73,se:"Bullish",ra:"Buy",beta:1.62,pe:"18.4x",mc:"$115B",th:"HBM memory for AI servers driving supercycle. DRAM pricing recovery ahead of expectations. US CHIPS Act funding secured."},
  {tk:"CSCO",nm:"Cisco Systems",cat:"Stock",ex:"NASDAQ",sc:62,se:"Neutral",ra:"Hold",beta:0.82,pe:"14.2x",mc:"$218B",th:"Splunk acquisition integration ongoing. AI networking demand emerging. Subscription transition reducing revenue visibility near-term."},
  {tk:"NOW",nm:"ServiceNow",cat:"Stock",ex:"NYSE",sc:76,se:"Bullish",ra:"Strong Buy",beta:1.08,pe:"56.2x",mc:"$190B",th:"AI workflow automation the core thesis. Enterprise IT spending sticky. 98%+ net revenue retention. CRO AI agent platform leading."},
  {tk:"PANW",nm:"Palo Alto Networks",cat:"Stock",ex:"NASDAQ",sc:74,se:"Bullish",ra:"Buy",beta:1.18,pe:"48.6x",mc:"$115B",th:"Platformisation strategy taking share from point products. AI-powered SASE the growth engine. Free cash flow inflecting positively."},
  {tk:"CRWD",nm:"CrowdStrike",cat:"Stock",ex:"NASDAQ",sc:72,se:"Bullish",ra:"Buy",beta:1.42,pe:"82.4x",mc:"$88B",th:"Endpoint security dominant. Recovery from July 2024 outage complete. Falcon platform expansion into identity and cloud security."},
  {tk:"PLTR",nm:"Palantir Technologies",cat:"Stock",ex:"NYSE",sc:68,se:"Bullish",ra:"Buy",beta:2.12,pe:"165x",mc:"$58B",th:"AIP AI platform driving US commercial growth. Government contracts resilient. Valuation stretched but software operating leverage emerging."},
  {tk:"COIN",nm:"Coinbase Global",cat:"Stock",ex:"NASDAQ",sc:63,se:"Neutral-Bull",ra:"Accumulate",beta:3.20,pe:"28.4x",mc:"$55B",th:"Crypto cycle dependent. Regulatory clarity improving post-election. Base L2 chain adding revenue stream. Institutional custody growing."},
  {tk:"UBER",nm:"Uber Technologies",cat:"Stock",ex:"NYSE",sc:74,se:"Bullish",ra:"Buy",beta:1.35,pe:"28.6x",mc:"$148B",th:"First GAAP profitable year. Delivery margins expanding. Autonomous vehicle partnerships optionality. Advertising growing fast."},
  {tk:"SHOP",nm:"Shopify",cat:"Stock",ex:"NYSE",sc:68,se:"Bullish",ra:"Buy",beta:1.65,pe:"68.2x",mc:"$110B",th:"Merchant solutions outgrowing subscriptions. Payments penetration increasing. Logistics exit improving margin. Enterprise moving upmarket."},
  {tk:"SNOW",nm:"Snowflake",cat:"Stock",ex:"NYSE",sc:60,se:"Neutral",ra:"Hold",beta:1.42,pe:"N/A",mc:"$44B",th:"Consumption model makes revenue hard to predict. AI features not yet monetised. CEO transition to Sridhar Ramaswamy positive but early."},
  {tk:"RIVN",nm:"Rivian Automotive",cat:"Stock",ex:"NASDAQ",sc:38,se:"Bearish",ra:"Avoid",beta:2.85,pe:"N/A",mc:"$12B",th:"Cash burn remains significant. R2 vehicle critical to unit economics. Amazon delivery van contract stabilising. Multi-year path to profitability."},
  {tk:"F",nm:"Ford Motor",cat:"Stock",ex:"NYSE",sc:52,se:"Neutral",ra:"Hold",beta:1.38,pe:"7.2x",mc:"$48B",th:"EV losses widening. Pro commercial truck segment strong. ICE cash flow funding EV transition. UAW contract costs weighing on margins."},
  {tk:"GM",nm:"General Motors",cat:"Stock",ex:"NYSE",sc:58,se:"Neutral",ra:"Hold",beta:1.22,pe:"6.4x",mc:"$52B",th:"Cruise autonomous unit losses contained. Strong truck and SUV margins. $10B+ buyback executing. EV ramp slower than planned."},
  {tk:"BA",nm:"Boeing",cat:"Stock",ex:"NYSE",sc:44,se:"Bearish",ra:"Hold",beta:1.42,pe:"N/A",mc:"$125B",th:"737 MAX production ramp constrained by FAA. 787 deliveries recovering. Defense losses persistent. Balance sheet stretched post-strike."},
  {tk:"CAT",nm:"Caterpillar",cat:"Stock",ex:"NYSE",sc:72,se:"Bullish",ra:"Buy",beta:1.08,pe:"14.8x",mc:"$178B",th:"Infrastructure spending supercycle early innings. Mining equipment demand from EV battery metals. Pricing power demonstrated through cycle."},
  {tk:"DE",nm:"John Deere",cat:"Stock",ex:"NYSE",sc:65,se:"Neutral",ra:"Hold",beta:0.95,pe:"12.4x",mc:"$108B",th:"Ag equipment destocking cycle ongoing. Precision agriculture software the long-term story. Cash generation strong through downturn."},
  {tk:"NKE",nm:"Nike Inc",cat:"Stock",ex:"NYSE",sc:52,se:"Neutral",ra:"Hold",beta:0.92,pe:"24.6x",mc:"$106B",th:"DTC inventory digestion ongoing. China recovery slower than expected. New CEO pivoting back to wholesale. Brand heat fading vs emerging competitors."},
  {tk:"SBUX",nm:"Starbucks",cat:"Stock",ex:"NASDAQ",sc:55,se:"Neutral",ra:"Hold",beta:0.88,pe:"22.4x",mc:"$82B",th:"Brian Niccol turnaround in early stages. US traffic recovering. China market challenged. Menu simplification and staffing models being reset."},
  {tk:"MCD",nm:"McDonald's",cat:"Stock",ex:"NYSE",sc:68,se:"Bullish",ra:"Buy",beta:0.72,pe:"22.8x",mc:"$208B",th:"Value platform resonating with inflation-fatigued consumer. Drive-through and digital ordering mix improving margins. Franchise model insulated."},
  {tk:"JNJ",nm:"Johnson & Johnson",cat:"Stock",ex:"NYSE",sc:65,se:"Neutral",ra:"Hold",beta:0.62,pe:"14.2x",mc:"$408B",th:"MedTech the growth driver post-Kenvue spin. Pharma pipeline solid. Talc litigation settlement progress reducing overhang."},
  {tk:"UNH",nm:"UnitedHealth Group",cat:"Stock",ex:"NYSE",sc:70,se:"Bullish",ra:"Buy",beta:0.68,pe:"18.4x",mc:"$555B",th:"Optum platform expanding. Medical loss ratio normalising. CEO transition managed well. Healthcare AI integration ahead of peers."},
  {tk:"PFE",nm:"Pfizer",cat:"Stock",ex:"NYSE",sc:45,se:"Bearish",ra:"Hold",beta:0.58,pe:"12.6x",mc:"$158B",th:"Post-COVID revenue normalisation complete. Pipeline rebuilding via Seagen oncology acquisition. Dividend yield attractive floor."},
  {tk:"LLY",nm:"Eli Lilly",cat:"Stock",ex:"NYSE",sc:84,se:"Bullish",ra:"Strong Buy",beta:0.48,pe:"48.6x",mc:"$798B",th:"GLP-1 obesity/diabetes market dominant position. Mounjaro and Zepbound supply expanding. Pipeline deep. Pricing power substantial."},
  {tk:"ABBV",nm:"AbbVie",cat:"Stock",ex:"NYSE",sc:72,se:"Bullish",ra:"Buy",beta:0.62,pe:"16.8x",mc:"$340B",th:"Humira biosimilar cliff navigated. Skyrizi and Rinvoq growing strongly. Neuroscience pipeline addition via Cerevel acquisition."},
  {tk:"MRK",nm:"Merck & Co",cat:"Stock",ex:"NYSE",sc:68,se:"Bullish",ra:"Buy",beta:0.55,pe:"12.4x",mc:"$268B",th:"Keytruda the world's top cancer drug. IRA pricing headwind manageable. Cardiovascular pipeline emerging. Robust free cash generation."},
  {tk:"WMT",nm:"Walmart",cat:"Stock",ex:"NYSE",sc:74,se:"Bullish",ra:"Buy",beta:0.52,pe:"36.2x",mc:"$690B",th:"Advertising revenue growing 26%. Membership and delivery economics improving. High-income consumer trading down adding addressable market."},
  {tk:"COST",nm:"Costco Wholesale",cat:"Stock",ex:"NASDAQ",sc:76,se:"Bullish",ra:"Buy",beta:0.72,pe:"52.4x",mc:"$385B",th:"Membership renewal rate 93%+. Private label Kirkland gaining share. International expansion runway. Premium to market justified by execution."},
  {tk:"HD",nm:"Home Depot",cat:"Stock",ex:"NYSE",sc:68,se:"Bullish",ra:"Buy",beta:1.02,pe:"22.6x",mc:"$362B",th:"Housing turnover recovery slow but coming. Pro contractor segment outperforming. SRS Distribution adds professional customer access."},
  {tk:"BAC",nm:"Bank of America",cat:"Stock",ex:"NYSE",sc:68,se:"Bullish",ra:"Buy",beta:1.38,pe:"12.8x",mc:"$318B",th:"NII sensitivity highest among big banks. Rate cut cycle headwind temporary. Consumer banking deposits stable. Capital return accelerating."},
  {tk:"WFC",nm:"Wells Fargo",cat:"Stock",ex:"NYSE",sc:65,se:"Neutral",ra:"Hold",beta:1.18,pe:"12.2x",mc:"$225B",th:"Asset cap removal catalyst pending OCC approval. Fee income rebuilding. Expense discipline under CEO Scharf. Rate sensitivity manageable."},
  {tk:"C",nm:"Citigroup",cat:"Stock",ex:"NYSE",sc:62,se:"Neutral",ra:"Hold",beta:1.45,pe:"9.8x",mc:"$128B",th:"Transformation plan multi-year. Services and markets performing. Consent order remediation costing capital. Cheap on tangible book."},
  {tk:"BLK",nm:"BlackRock",cat:"Stock",ex:"NYSE",sc:76,se:"Bullish",ra:"Buy",beta:1.28,pe:"22.4x",mc:"$145B",th:"GIP infrastructure acquisition adds alternatives scale. ETF market share dominant. Aladdin technology revenue recurring. Preqin data adds."},
  {tk:"ISRG",nm:"Intuitive Surgical",cat:"Stock",ex:"NASDAQ",sc:78,se:"Bullish",ra:"Strong Buy",beta:0.92,pe:"62.4x",mc:"$185B",th:"Da Vinci 5 surgical robot next-gen launch. Installed base procedure growth compounding. Razors-and-blades instrument revenue sticky."},
  {tk:"TSM",nm:"TSMC ADR",cat:"Stock",ex:"NYSE",sc:82,se:"Bullish",ra:"Strong Buy",beta:1.22,pe:"22.8x",mc:"$845B",th:"Sole manufacturer of most advanced chips. AI demand driving CoWoS packaging capacity constraints. Arizona fab on track."},
  {tk:"ASML",nm:"ASML Holding",cat:"Stock",ex:"NASDAQ",sc:80,se:"Bullish",ra:"Strong Buy",beta:1.18,pe:"34.2x",mc:"$388B",th:"EUV lithography monopoly with no viable competitor. AI chip demand = ASML demand with 2-3yr lag. China export restrictions manageable."},
  {tk:"NVO",nm:"Novo Nordisk ADR",cat:"Stock",ex:"NYSE",sc:78,se:"Bullish",ra:"Buy",beta:0.45,pe:"22.4x",mc:"$412B",th:"Ozempic/Wegovy GLP-1 co-leader with Eli Lilly. EU pricing advantage. CagriSema next-gen obesity drug in trials. Manufacturing scaling."},
  {tk:"SAP",nm:"SAP SE ADR",cat:"Stock",ex:"NYSE",sc:72,se:"Bullish",ra:"Buy",beta:0.82,pe:"42.6x",mc:"$282B",th:"Cloud ERP migration driving recurring revenue. Business AI integration sticky. Large enterprise switching costs substantial. Europe tech champion."},
  {tk:"BABA",nm:"Alibaba Group ADR",cat:"Stock",ex:"NYSE",sc:52,se:"Neutral",ra:"Hold",beta:0.92,pe:"10.2x",mc:"$212B",th:"China consumer recovery slow. Cloud business growing but competitive. Regulatory risk receding. Cheap on earnings but structural headwinds."},
  {tk:"BP",nm:"BP PLC ADR",cat:"Stock",ex:"NYSE",sc:60,se:"Neutral",ra:"Hold",beta:0.68,pe:"8.4x",mc:"$92B",th:"Strategy pivot back to oil from renewables. Dividend secure. Activist Elliott pressure for performance. Energy transition credibility lost."},
  {tk:"SHEL",nm:"Shell PLC ADR",cat:"Stock",ex:"NYSE",sc:65,se:"Neutral",ra:"Hold",beta:0.72,pe:"9.2x",mc:"$218B",th:"LNG leadership position valuable. Capital discipline improving. Buyback yield attractive. Energy transition slower than planned acceptable."},
  // ─── Additional Crypto ───
  {tk:"DOGE",nm:"Dogecoin",cat:"Crypto",ex:"GLOBAL",sc:42,se:"Volatile",ra:"Speculative",beta:3.20,pe:"-",mc:"$24B",th:"Meme coin with limited utility but massive retail following. Elon Musk association drives sentiment. DOGE payment acceptance growing slowly."},
  {tk:"ADA",nm:"Cardano",cat:"Crypto",ex:"GLOBAL",sc:48,se:"Neutral",ra:"Hold",beta:2.20,pe:"-",mc:"$16B",th:"Proof-of-stake pioneer. Academic research approach slow to deliver. DeFi ecosystem developing. Hydra scalability solution in progress."},
  {tk:"AVAX",nm:"Avalanche",cat:"Crypto",ex:"GLOBAL",sc:58,se:"Neutral-Bull",ra:"Accumulate",beta:2.45,pe:"-",mc:"$12B",th:"Subnet architecture enabling enterprise blockchain. Amazon Web Services partnership. Gaming and institutional finance use cases growing."},
  {tk:"LINK",nm:"Chainlink",cat:"Crypto",ex:"GLOBAL",sc:62,se:"Neutral-Bull",ra:"Accumulate",beta:1.95,pe:"-",mc:"$8B",th:"Oracle network dominant. CCIP cross-chain interoperability protocol strategic. Real-world asset tokenisation the core long-term thesis."},
  {tk:"DOT",nm:"Polkadot",cat:"Crypto",ex:"GLOBAL",sc:48,se:"Neutral",ra:"Hold",beta:2.10,pe:"-",mc:"$9B",th:"Parachain architecture interesting but execution slow. Ecosystem development lagging Ethereum L2s. JAM upgrade could re-ignite interest."},
  {tk:"LTC",nm:"Litecoin",cat:"Crypto",ex:"GLOBAL",sc:40,se:"Neutral",ra:"Hold",beta:1.65,pe:"-",mc:"$6B",th:"Digital silver narrative weakening. Halving cycle impact diminishing. Lightning Network competition from Bitcoin. Utility case narrow."},
  {tk:"UNI",nm:"Uniswap",cat:"Crypto",ex:"GLOBAL",sc:60,se:"Neutral-Bull",ra:"Accumulate",beta:2.25,pe:"-",mc:"$5B",th:"DEX volume leader. Fee switch governance vote pending. V4 hooks enabling customizable liquidity. Regulatory risk from SEC action lingering."},
  // ─── Additional FX ───
  {tk:"AUDUSD",nm:"AUD/USD",cat:"FX",ex:"FOREX",sc:52,se:"Neutral",ra:"Neutral",beta:0.18,pe:"-",mc:"-",th:"China commodity demand proxy. RBA rate path diverging. Iron ore prices supporting. Risk-off environment headwind for commodity currencies."},
  {tk:"USDCAD",nm:"USD/CAD",cat:"FX",ex:"FOREX",sc:55,se:"Neutral",ra:"Neutral",beta:0.15,pe:"-",mc:"-",th:"Oil price sensitivity high. BOC cutting rates ahead of Fed. Housing market vulnerability. Trade war risk with US largest partner."},
  {tk:"USDCHF",nm:"USD/CHF",cat:"FX",ex:"FOREX",sc:58,se:"Neutral",ra:"Watch",beta:0.12,pe:"-",mc:"-",th:"Safe haven franc demand elevated. SNB interventions capping appreciation. Negative real rates structural. Risk-off flows support CHF."},
  {tk:"NZDUSD",nm:"NZD/USD",cat:"FX",ex:"FOREX",sc:48,se:"Bearish",ra:"Avoid",beta:0.22,pe:"-",mc:"-",th:"RBNZ cutting rates aggressively. China export exposure. Commodity agricultural prices weak. Risk sentiment proxy at lower volatility."},
  {tk:"EURGBP",nm:"EUR/GBP",cat:"FX",ex:"FOREX",sc:50,se:"Neutral",ra:"Neutral",beta:0.10,pe:"-",mc:"-",th:"UK services inflation keeping BOE cautious vs ECB cuts. Post-Brexit trade normalisation slow. Rates differential moving in GBP favour."},
  // ─── Additional Commodities ───
  {tk:"COPPER",nm:"Copper",cat:"Commodity",ex:"COMEX",sc:72,se:"Bullish",ra:"Buy",beta:0.42,pe:"-",mc:"-",th:"EV and renewable energy copper intensity 3-4x ICE vehicles. Supply constrained by long permitting cycles. China restocking cycle due."},
  {tk:"WHEAT",nm:"Wheat",cat:"Commodity",ex:"CBOT",sc:58,se:"Neutral",ra:"Neutral",beta:0.35,pe:"-",mc:"-",th:"Ukraine supply disruption structural floor. La Nina weather risk in Southern Hemisphere. India export ban limiting global supply."},
  {tk:"CORN",nm:"Corn",cat:"Commodity",ex:"CBOT",sc:50,se:"Neutral",ra:"Neutral",beta:0.30,pe:"-",mc:"-",th:"US acreage competition with soybeans. Ethanol demand floor. Brazil record harvest capping upside. Livestock feed demand stable."},
  {tk:"COFFEE",nm:"Coffee (Arabica)",cat:"Commodity",ex:"ICE",sc:62,se:"Bullish",ra:"Buy",beta:0.28,pe:"-",mc:"-",th:"Brazil drought reduced supply. Vietnam robusta shortage. Structural demand growth in Asia. Climate change reducing suitable growing regions."},
  {tk:"PLAT",nm:"Platinum",cat:"Commodity",ex:"NYMEX",sc:58,se:"Neutral",ra:"Hold",beta:0.32,pe:"-",mc:"-",th:"Hydrogen fuel cell catalyst demand emerging. Autocatalyst demand falling with EV shift. South Africa supply constraints. Gold-platinum ratio historically stretched."},
  {tk:"COCOA",nm:"Cocoa",cat:"Commodity",ex:"ICE",sc:65,se:"Bullish",ra:"Buy",beta:0.25,pe:"-",mc:"-",th:"West Africa crop failures drove cocoa to all-time highs. El Nino disrupting production. Supply deficit for third consecutive year. Premium chocolate demand resilient."},
  // ─── Additional US Stocks ───
  {tk:"ARM",nm:"ARM Holdings",cat:"Stock",ex:"NASDAQ",sc:78,se:"Bullish",ra:"Strong Buy",beta:1.85,pe:"120x",mc:"$148B",th:"Every AI chip uses ARM architecture. Royalty model scales with silicon boom. Smartphone recovery adding. Licensing revenue highly recurring and sticky."},
  {tk:"SMCI",nm:"Super Micro Computer",cat:"Stock",ex:"NASDAQ",sc:65,se:"Neutral-Bull",ra:"Hold",beta:2.20,pe:"18x",mc:"$28B",th:"AI server manufacturer with NVDA GPU advantage. Accounting restatement overhang. Fastest time-to-market for AI infrastructure. Margin expansion story intact if issues resolve."},
  {tk:"MRVL",nm:"Marvell Technology",cat:"Stock",ex:"NASDAQ",sc:72,se:"Bullish",ra:"Buy",beta:1.65,pe:"42x",mc:"$62B",th:"Custom AI accelerator silicon for cloud hyperscalers. Data center networking essential. 5G infrastructure exposure. Electro-optics for AI data centre interconnects."},
  {tk:"KO",nm:"Coca-Cola",cat:"Stock",ex:"NYSE",sc:68,se:"Bullish",ra:"Buy",beta:0.58,pe:"22x",mc:"$306B",th:"Pricing power demonstrated through inflation. Emerging market volume growth. Brand moat unassailable. Dividend Aristocrat 62 consecutive years of dividend growth."},
  {tk:"PEP",nm:"PepsiCo",cat:"Stock",ex:"NASDAQ",sc:66,se:"Bullish",ra:"Buy",beta:0.52,pe:"20x",mc:"$218B",th:"Frito-Lay snacks more resilient than beverages. Pricing power through inflation. Dividend growth 51 consecutive years. International exposure to emerging middle class."},
  {tk:"PG",nm:"Procter & Gamble",cat:"Stock",ex:"NYSE",sc:70,se:"Bullish",ra:"Buy",beta:0.48,pe:"24x",mc:"$388B",th:"Essential consumer brands with pricing power. Dividend Aristocrat 67 years. Premium product mix shift. Emerging market penetration growing. Recession-resistant revenue base."},
  {tk:"ABNB",nm:"Airbnb",cat:"Stock",ex:"NASDAQ",sc:68,se:"Bullish",ra:"Buy",beta:1.42,pe:"16x",mc:"$85B",th:"Travel demand structurally higher post-COVID. Experiences category emerging. No debt. $10B+ buyback. International expansion in high-growth markets. Margin expansion story."},
  {tk:"DASH",nm:"DoorDash",cat:"Stock",ex:"NYSE",sc:62,se:"Neutral-Bull",ra:"Accumulate",beta:1.52,pe:"N/A",mc:"$48B",th:"Food delivery market consolidating. International DashPass growing. Advertising layer emerging. Unit economics improving but path to profitability still multi-year."},
  {tk:"BRKB",nm:"Berkshire Hathaway B",cat:"Stock",ex:"NYSE",sc:74,se:"Bullish",ra:"Buy",beta:0.88,pe:"21x",mc:"$1.1T",th:"$320B+ cash pile at record. Warren Buffett's 60-year compounding machine. Insurance float funding investments. Defensive in downturns. Dividend-free capital compounder."},
  {tk:"ACN",nm:"Accenture",cat:"Stock",ex:"NYSE",sc:70,se:"Bullish",ra:"Buy",beta:1.02,pe:"27x",mc:"$200B",th:"AI consulting demand accelerating. GenAI bookings exceeding $3B. Digital transformation multi-year secular trend. Government and enterprise contracts sticky."},
  {tk:"SONY",nm:"Sony Group ADR",cat:"Stock",ex:"NYSE",sc:68,se:"Bullish",ra:"Buy",beta:0.92,pe:"18x",mc:"$118B",th:"PlayStation 5 cycle mature but profitable. Music and film IP valuable. Imaging sensors dominant (60%+ market share). Financial services optionality. AI integration in content."},
  {tk:"VALE",nm:"Vale SA ADR",cat:"Stock",ex:"NYSE",sc:58,se:"Neutral",ra:"Hold",beta:1.02,pe:"6x",mc:"$46B",th:"Iron ore price dependent on China construction. Nickel division key for EV batteries. Brazilian political risk. Deep discount to peers on P/E. High dividend yield."},
  {tk:"RIO",nm:"Rio Tinto ADR",cat:"Stock",ex:"NYSE",sc:64,se:"Neutral",ra:"Hold",beta:0.78,pe:"9x",mc:"$98B",th:"Lithium via Rincon project for EV supply. Iron ore dominant. Copper exposure via Oyu Tolgoi. Capital discipline post-2010s write-downs. High dividend yield."},
  {tk:"INFY",nm:"Infosys ADR",cat:"Stock",ex:"NYSE",sc:62,se:"Neutral",ra:"Hold",beta:0.82,pe:"22x",mc:"$72B",th:"AI-driven IT outsourcing disruption risk. But also AI implementation beneficiary. Margin pressure from wage inflation. Strong balance sheet. Indian tech bellwether."},
  // ─── Additional Crypto ───
  {tk:"MATIC",nm:"Polygon",cat:"Crypto",ex:"GLOBAL",sc:55,se:"Neutral",ra:"Hold",beta:2.40,pe:"-",mc:"$4B",th:"Ethereum Layer 2 scaling leader. zkEVM technology competitive. Rebranded to POL. Institutional adoption via CDBC pilots. Competition from Arbitrum and Optimism intensifying."},
  {tk:"NEAR",nm:"NEAR Protocol",cat:"Crypto",ex:"GLOBAL",sc:58,se:"Neutral-Bull",ra:"Accumulate",beta:2.15,pe:"-",mc:"$3B",th:"Sharding architecture enables high throughput. AI-blockchain integration narrative. Developer-friendly. Nightshade upgrade improving scalability. Ecosystem growing steadily."},
  {tk:"ALGO",nm:"Algorand",cat:"Crypto",ex:"GLOBAL",sc:45,se:"Neutral",ra:"Hold",beta:1.80,pe:"-",mc:"$2B",th:"Pure proof-of-stake pioneer. Government and institutional blockchain use cases. Marshall Islands sovereign currency. Carbon-negative network. Execution slower than roadmap."},
  {tk:"HBAR",nm:"Hedera",cat:"Crypto",ex:"GLOBAL",sc:52,se:"Neutral",ra:"Hold",beta:1.95,pe:"-",mc:"$4B",th:"Enterprise-grade hashgraph consensus. Google, IBM on governing council. Tokenisation of real-world assets. HBAR Foundation grants driving adoption. Not a traditional blockchain."},
  {tk:"TON",nm:"Toncoin",cat:"Crypto",ex:"GLOBAL",sc:60,se:"Neutral-Bull",ra:"Accumulate",beta:2.30,pe:"-",mc:"$12B",th:"Telegram integration gives access to 900M users. Mini-apps ecosystem growing. Pavel Durov legal issues an overhang. Payment layer for Telegram commerce could be transformative."},
  // ─── Additional Global Indices ───
  {tk:"CAC",nm:"CAC 40",cat:"Stock",ex:"EURONEXT",sc:62,se:"Neutral",ra:"Neutral",beta:1.12,pe:"-",mc:"-",th:"French large-cap index. Luxury sector (LVMH, Hermes) dominant weighting. Political risk from France deficit concerns. ECB rate cuts supportive. Export-heavy composition."},
  {tk:"ASX200",nm:"ASX 200",cat:"Stock",ex:"ASX",sc:64,se:"Neutral",ra:"Neutral",beta:0.85,pe:"-",mc:"-",th:"Australian large-cap index. Commodities and banks dominant. China demand proxy. RBA rate path key driver. Strong mining sector with lithium and iron ore exposure."},
  {tk:"KOSPI",nm:"KOSPI",cat:"Stock",ex:"KRX",sc:58,se:"Neutral",ra:"Neutral",beta:1.05,pe:"-",mc:"-",th:"South Korea large-cap. Samsung Electronics dominant. Semiconductor cycle highly influential. Won weakness vs dollar headwind. North Korea geopolitical premium persistent."},
  // ─── More US Large Cap ───
  {tk:"TMO",nm:"Thermo Fisher Scientific",cat:"Stock",ex:"NYSE",sc:72,se:"Bullish",ra:"Buy",beta:0.72,pe:"28x",mc:"$212B",th:"Life science tools essential for drug discovery and manufacturing. Bioproduction recovery underway. AI-driven lab automation. Consistent double-digit earnings growth."},
  {tk:"ABT",nm:"Abbott Laboratories",cat:"Stock",ex:"NYSE",sc:70,se:"Bullish",ra:"Buy",beta:0.75,pe:"22x",mc:"$198B",th:"Medical devices and diagnostics diversified business. FreeStyle Libre CGM dominant. COVID test normalisation complete. Emerging market healthcare penetration opportunity."},
  {tk:"PM",nm:"Philip Morris International",cat:"Stock",ex:"NYSE",sc:68,se:"Bullish",ra:"Buy",beta:0.62,pe:"18x",mc:"$200B",th:"IQOS smoke-free product driving transformation. ZYN nicotine pouch leader. High dividend yield. Emerging market volume resilience. Regulatory risk manageable outside US."},
  {tk:"NEE",nm:"NextEra Energy",cat:"Stock",ex:"NYSE",sc:66,se:"Neutral",ra:"Hold",beta:0.52,pe:"20x",mc:"$152B",th:"Largest clean energy producer globally. Renewables buildout accelerating. AI data centre power demand tailwind. Rate sensitivity headwind from higher-for-longer environment."},
  {tk:"RTX",nm:"RTX Corporation",cat:"Stock",ex:"NYSE",sc:70,se:"Bullish",ra:"Buy",beta:0.92,pe:"32x",mc:"$162B",th:"Defence budget increases globally post-Russia-Ukraine. Pratt & Whitney GTF engine backlog massive. Commercial aerospace recovery supporting Collins Aerospace. Dual revenue streams."},
  {tk:"HON",nm:"Honeywell International",cat:"Stock",ex:"NASDAQ",sc:65,se:"Neutral",ra:"Hold",beta:0.95,pe:"22x",mc:"$138B",th:"Industrial conglomerate breakup under consideration. Aerospace the crown jewel. Building automation benefiting from energy efficiency focus. Valuation reasonable for quality."},
  {tk:"T",nm:"AT&T",cat:"Stock",ex:"NYSE",sc:52,se:"Neutral",ra:"Hold",beta:0.62,pe:"12x",mc:"$155B",th:"Debt reduction on track post-DirecTV disposal. 5G network build maturing. Dividend sustainable at current level. ARPU growth from price increases offsetting subscriber churn."},
  {tk:"VZ",nm:"Verizon Communications",cat:"Stock",ex:"NYSE",sc:50,se:"Neutral",ra:"Hold",beta:0.42,pe:"10x",mc:"$168B",th:"5G fixed wireless access growth offset by wireless subscriber losses. High yield attractive floor. Lead cable liability a wildcard. Capital allocation improving post-investment peak."},
  {tk:"MS",nm:"Morgan Stanley",cat:"Stock",ex:"NYSE",sc:70,se:"Bullish",ra:"Buy",beta:1.42,pe:"16x",mc:"$195B",th:"Wealth management the jewel — $7T+ client assets recurring revenue. Investment banking recovery. E*Trade integration complete. CEO Ted Pick executing well on Gorman's strategy."},
  {tk:"SCHW",nm:"Charles Schwab",cat:"Stock",ex:"NYSE",sc:65,se:"Neutral",ra:"Hold",beta:1.28,pe:"24x",mc:"$138B",th:"Ameritrade integration complete. Net interest income sensitive to rates. Cash sorting headwind fading. Scale in discount brokerage unassailable. Long runway as population ages."},
  {tk:"TXN",nm:"Texas Instruments",cat:"Stock",ex:"NASDAQ",sc:68,se:"Bullish",ra:"Buy",beta:1.08,pe:"30x",mc:"$175B",th:"Analog chip leader with 100,000+ product SKUs. Auto and industrial cycle bottoming. Fab expansion complete. Long dividend growth history. Capital returns generous."},
  {tk:"AMAT",nm:"Applied Materials",cat:"Stock",ex:"NASDAQ",sc:72,se:"Bullish",ra:"Buy",beta:1.45,pe:"22x",mc:"$158B",th:"Semiconductor equipment essential for chip fabrication. AI chip complexity driving equipment intensity higher. China exposure risk partially offset by US demand. Materials engineering leader."},
  {tk:"LRCX",nm:"Lam Research",cat:"Stock",ex:"NASDAQ",sc:70,se:"Bullish",ra:"Buy",beta:1.55,pe:"20x",mc:"$88B",th:"Etch and deposition equipment for leading-edge chips. AI-driven wafer starts rising. NAND cycle recovering. Customer concentration risk (Samsung, SK Hynix, Micron)."},
  {tk:"REGN",nm:"Regeneron Pharmaceuticals",cat:"Stock",ex:"NASDAQ",sc:72,se:"Bullish",ra:"Buy",beta:0.52,pe:"22x",mc:"$96B",th:"Eylea and Dupixent blockbusters. Oncology pipeline entering Phase 3. Weight loss drug Trevogrumab potential. Collaboration with Sanofi durable. Strong FCF generation."},
  {tk:"AMGN",nm:"Amgen",cat:"Stock",ex:"NASDAQ",sc:66,se:"Neutral",ra:"Hold",beta:0.55,pe:"16x",mc:"$152B",th:"MariTide obesity drug Phase 3 data critical. Horizon Therapeutics integration ongoing. Biosimilar competition to legacy products. Dividend growth 12+ years. FCF-generative."},
  {tk:"CVX",nm:"Chevron",cat:"Stock",ex:"NYSE",sc:68,se:"Bullish",ra:"Buy",beta:0.92,pe:"13x",mc:"$262B",th:"Permian Basin production growing. Hess merger adds Guyana exposure. $75B buyback authorisation. Lower breakeven vs majors. Renewable energy exposure via Chevron New Energies."},
  {tk:"COP",nm:"ConocoPhillips",cat:"Stock",ex:"NYSE",sc:70,se:"Bullish",ra:"Buy",beta:0.98,pe:"12x",mc:"$118B",th:"Pure-play E&P with lowest cost structure among majors. Marathon acquisition strengthens Permian. Disciplined capital allocation and return of cash. LNG exposure via APLNG."},
  {tk:"INTU",nm:"Intuit",cat:"Stock",ex:"NASDAQ",sc:68,se:"Bullish",ra:"Buy",beta:1.18,pe:"35x",mc:"$178B",th:"TurboTax and QuickBooks monopoly-like positions. AI-powered financial tools emerging. SMB accounting platform sticky. Credit Karma adds consumer data value. Margins expanding."},
  {tk:"ADSK",nm:"Autodesk",cat:"Stock",ex:"NASDAQ",sc:65,se:"Neutral",ra:"Hold",beta:1.12,pe:"30x",mc:"$58B",th:"3D design software essential for AEC and manufacturing. Transition to subscription complete. AI integration in Forma platform. Construction digitisation long runway."},
  {tk:"NET",nm:"Cloudflare",cat:"Stock",ex:"NYSE",sc:68,se:"Bullish",ra:"Buy",beta:1.42,pe:"N/A",mc:"$42B",th:"Network edge security platform attacking $100B+ TAM. Workers AI inference platform differentiator. Zero trust architecture adoption accelerating. Rule-of-40 approaching."},
  {tk:"DDOG",nm:"Datadog",cat:"Stock",ex:"NASDAQ",sc:70,se:"Bullish",ra:"Buy",beta:1.35,pe:"65x",mc:"$38B",th:"Observability platform essential for cloud operations. AI infrastructure monitoring demand. 20+ products expanding from monitoring to security. Net retention rate 120%+."},
  {tk:"ZS",nm:"Zscaler",cat:"Stock",ex:"NASDAQ",sc:68,se:"Bullish",ra:"Buy",beta:1.38,pe:"N/A",mc:"$32B",th:"Zero Trust cloud security leader. Government and enterprise digitalisation driving adoption. AI-powered threat detection. Large deal momentum. $4B ARR target approaching."},
  {tk:"UPS",nm:"United Parcel Service",cat:"Stock",ex:"NYSE",sc:58,se:"Neutral",ra:"Hold",beta:1.02,pe:"18x",mc:"$88B",th:"E-commerce volume recovery post-Amazon in-housing. Healthcare logistics growing. Restructuring accelerating. Dividend yield attractive at current valuation. Labour costs elevated."},
  {tk:"LOW",nm:"Lowe's Companies",cat:"Stock",ex:"NYSE",sc:66,se:"Neutral",ra:"Hold",beta:1.12,pe:"18x",mc:"$146B",th:"Housing turnover cycle recovery delayed but coming. Pro customer penetration increasing. Total Home Strategy executing. Technology investments in productivity. DIY mix normalising."},
  {tk:"DUK",nm:"Duke Energy",cat:"Stock",ex:"NYSE",sc:60,se:"Neutral",ra:"Hold",beta:0.42,pe:"18x",mc:"$88B",th:"Regulated utility with rate base growing 7%+. Data centre power demand in Carolinas. Clean energy transition adding capital deployment opportunities. Dividend yield 3.8%."},
  // ─── More International ───
  {tk:"TM",nm:"Toyota Motor ADR",cat:"Stock",ex:"NYSE",sc:65,se:"Neutral",ra:"Hold",beta:0.72,pe:"9x",mc:"$248B",th:"Hybrid strategy vindicated over pure EV pivot. Production volumes recovering. Hydrogen fuel cell long-term bet. Yen weakness boosts overseas earnings. Stable dividend payer."},
  {tk:"NVS",nm:"Novartis ADR",cat:"Stock",ex:"NYSE",sc:68,se:"Bullish",ra:"Buy",beta:0.48,pe:"16x",mc:"$248B",th:"Innovative core spin-off of Sandoz generics complete. Kisqali breast cancer blockbuster. Gene therapy pipeline. Swiss franc exposure. Dividend growth history strong."},
  {tk:"UL",nm:"Unilever ADR",cat:"Stock",ex:"NYSE",sc:58,se:"Neutral",ra:"Hold",beta:0.52,pe:"18x",mc:"$128B",th:"Beauty & Wellbeing separation potential value unlock. Emerging market volume growth. Ice cream IPO simplification. CEO Hein Schumacher restructuring underway. Dividend yield 3.5%."},
  {tk:"DEO",nm:"Diageo ADR",cat:"Stock",ex:"NYSE",sc:60,se:"Neutral",ra:"Hold",beta:0.58,pe:"18x",mc:"$65B",th:"Premium spirits challenged by US consumer destocking. Johnnie Walker and Guinness brands iconic. Emerging market long-term growth thesis intact. Valuation at multi-year lows."},
  // ─── More Crypto ───
  {tk:"BCH",nm:"Bitcoin Cash",cat:"Crypto",ex:"GLOBAL",sc:38,se:"Neutral",ra:"Hold",beta:1.85,pe:"-",mc:"$8B",th:"Bitcoin fork with larger blocks. Payment use case limited vs Lightning Network. Halving cycle impact diminishing. Losing relevance vs newer L1s."},
  {tk:"XLM",nm:"Stellar",cat:"Crypto",ex:"GLOBAL",sc:42,se:"Neutral",ra:"Hold",beta:1.62,pe:"-",mc:"$3B",th:"Cross-border payments focus. IBM World Wire partnership. Central bank digital currency experiments. Limited DeFi ecosystem vs competitors. PaySend integration positive."},
  {tk:"FIL",nm:"Filecoin",cat:"Crypto",ex:"GLOBAL",sc:45,se:"Neutral",ra:"Hold",beta:2.15,pe:"-",mc:"$3B",th:"Decentralised storage network. AI data storage demand narrative. Competition from Arweave. Storage capacity growth but tokenomics complex. Developer adoption slowly increasing."},
  {tk:"APT",nm:"Aptos",cat:"Crypto",ex:"GLOBAL",sc:52,se:"Neutral",ra:"Hold",beta:2.40,pe:"-",mc:"$3B",th:"Move language blockchain from ex-Meta engineers. High TPS architecture. Ecosystem building slowly. Institutional backing from a16z. Competition from SUI which shares same origins."},
  {tk:"SUI",nm:"Sui",cat:"Crypto",ex:"GLOBAL",sc:55,se:"Neutral-Bull",ra:"Accumulate",beta:2.60,pe:"-",mc:"$7B",th:"High throughput Move-based blockchain. Gaming and NFT ecosystem growing fastest. Mysticeti consensus mechanism. Korean retail interest significant. Strong VC backing."},
  // ─── More FX ───
  {tk:"USDMXN",nm:"USD/MXN",cat:"FX",ex:"FOREX",sc:52,se:"Volatile",ra:"Watch",beta:0.28,pe:"-",mc:"-",th:"Mexican peso carry trade popular given high rates. Nearshoring manufacturing boom supporting economy. AMLO successor policy uncertainty. US election trade policy risk significant."},
  {tk:"USDBRL",nm:"USD/BRL",cat:"FX",ex:"FOREX",sc:48,se:"Bearish",ra:"Avoid",beta:0.35,pe:"-",mc:"-",th:"Brazil fiscal deficit concerns weakening real. Lula spending plans under market scrutiny. High interest rates providing some support. Commodity exports backstop."},
  {tk:"USDINR",nm:"USD/INR",cat:"FX",ex:"FOREX",sc:55,se:"Neutral",ra:"Neutral",beta:0.12,pe:"-",mc:"-",th:"RBI managing rupee carefully. India strong growth supporting currency. FPI inflows from index inclusion. Limited volatility vs EM peers due to RBI intervention."},
  // ─── More Commodities ───
  {tk:"OJ",nm:"Orange Juice",cat:"Commodity",ex:"ICE",sc:58,se:"Bullish",ra:"Hold",beta:0.22,pe:"-",mc:"-",th:"Florida citrus greening disease destroying supply. Brazil crop variable. Record prices reflecting genuine supply crisis. Substitution risk at extreme prices."},
  {tk:"LUMBER",nm:"Lumber",cat:"Commodity",ex:"CME",sc:50,se:"Neutral",ra:"Neutral",beta:0.45,pe:"-",mc:"-",th:"Housing starts the key driver. Sawmill capacity additions capped upside. Canadian supply constraints. Housing affordability crisis reducing demand. High volatility commodity."},
  {tk:"PALLADIUM",nm:"Palladium",cat:"Commodity",ex:"NYMEX",sc:45,se:"Bearish",ra:"Avoid",beta:0.55,pe:"-",mc:"-",th:"EV transition reducing autocatalyst demand structurally. Russia supply risk partially priced. Platinum substitution ongoing in catalytic converters. Secular headwind from EV adoption."},
  // ─── ETFs, Indices & Macro ───
  {tk:"SPY",nm:"SPDR S&P 500 ETF",cat:"Stock",ex:"NYSE",sc:70,se:"Neutral",ra:"Hold",beta:1.0,pe:"-",mc:"-",th:"Broad US large-cap benchmark ETF. Most liquid equity instrument globally. Tracks S&P 500."},
  {tk:"QQQ",nm:"Invesco QQQ",cat:"Stock",ex:"NASDAQ",sc:72,se:"Bullish",ra:"Buy",beta:1.15,pe:"-",mc:"-",th:"Nasdaq-100 tracker. Mag 7 heavy. AI and growth tilt. Higher beta than SPY."},
  {tk:"IWM",nm:"iShares Russell 2000",cat:"Stock",ex:"NYSE",sc:58,se:"Neutral",ra:"Hold",beta:1.25,pe:"-",mc:"-",th:"Small-cap US equities. Rate-sensitive and domestic economy proxy. Outperforms early cycle."},
  {tk:"RUT",nm:"Russell 2000 Index",cat:"Stock",ex:"US",sc:58,se:"Neutral",ra:"Hold",beta:1.25,pe:"-",mc:"-",th:"Small-cap benchmark. Credit conditions and domestic GDP sensitive."},
  {tk:"EEM",nm:"iShares EM ETF",cat:"Stock",ex:"NYSE",sc:55,se:"Neutral",ra:"Hold",beta:1.1,pe:"-",mc:"-",th:"Emerging markets equities. China and India heavy. Dollar and commodity sensitive."},
  {tk:"SOXX",nm:"iShares Semiconductor",cat:"Stock",ex:"NASDAQ",sc:76,se:"Bullish",ra:"Buy",beta:1.6,pe:"-",mc:"-",th:"Semiconductor sector ETF. AI capex beneficiary. NVDA, AVGO, AMD weighted."},
  {tk:"TLT",nm:"iShares 20+ Year Treasury",cat:"Stock",ex:"NASDAQ",sc:48,se:"Bearish",ra:"Avoid",beta:-0.2,pe:"-",mc:"-",th:"Long-duration Treasury proxy. Inverse to yields. Risk-off hedge when rates fall."},
  {tk:"ARKK",nm:"ARK Innovation ETF",cat:"Stock",ex:"NYSE",sc:52,se:"Volatile",ra:"Speculative",beta:1.8,pe:"-",mc:"-",th:"Disruptive innovation basket. High beta growth. Rate-sensitive speculative proxy."},
  {tk:"TNX",nm:"US 10Y Treasury Yield",cat:"FX",ex:"US",sc:60,se:"Neutral",ra:"Watch",beta:0.1,pe:"-",mc:"-",th:"Benchmark risk-free rate. Drives equity multiples and mortgage rates. Fed policy anchor."},
  {tk:"XLK",nm:"Tech Select Sector",cat:"Stock",ex:"NYSE",sc:74,se:"Bullish",ra:"Buy",beta:1.2,pe:"-",mc:"-",th:"S&P 500 Technology sector ETF. Largest S&P sector weight."},
  {tk:"XLC",nm:"Communication Services",cat:"Stock",ex:"NYSE",sc:68,se:"Bullish",ra:"Buy",beta:1.1,pe:"-",mc:"-",th:"GOOGL, META, NFLX weighted communication sector ETF."},
  {tk:"XLY",nm:"Consumer Discretionary",cat:"Stock",ex:"NYSE",sc:65,se:"Neutral",ra:"Hold",beta:1.15,pe:"-",mc:"-",th:"AMZN, TSLA, HD weighted. Consumer spending and rate sensitive."},
  {tk:"XLF",nm:"Financial Select Sector",cat:"Stock",ex:"NYSE",sc:70,se:"Bullish",ra:"Buy",beta:1.1,pe:"-",mc:"-",th:"Banks and insurers. Yield curve and credit cycle sensitive."},
  {tk:"XLV",nm:"Health Care Select",cat:"Stock",ex:"NYSE",sc:66,se:"Neutral",ra:"Hold",beta:0.7,pe:"-",mc:"-",th:"Defensive healthcare sector. Drug pricing and M&A catalysts."},
  {tk:"XLE",nm:"Energy Select Sector",cat:"Stock",ex:"NYSE",sc:72,se:"Bullish",ra:"Buy",beta:0.9,pe:"-",mc:"-",th:"XOM, CVX weighted energy. Oil price and geopolitics driven."},
  {tk:"XLI",nm:"Industrial Select",cat:"Stock",ex:"NYSE",sc:64,se:"Neutral",ra:"Hold",beta:1.05,pe:"-",mc:"-",th:"CAT, RTX, UPS weighted. PMI and capex cycle proxy."},
  {tk:"XLP",nm:"Consumer Staples",cat:"Stock",ex:"NYSE",sc:62,se:"Neutral",ra:"Hold",beta:0.55,pe:"-",mc:"-",th:"PG, KO, WMT weighted defensive staples."},
  {tk:"XLB",nm:"Materials Select",cat:"Stock",ex:"NYSE",sc:60,se:"Neutral",ra:"Hold",beta:1.0,pe:"-",mc:"-",th:"Chemicals and mining. China and industrial demand sensitive."},
  {tk:"XLU",nm:"Utilities Select",cat:"Stock",ex:"NYSE",sc:58,se:"Neutral",ra:"Hold",beta:0.45,pe:"-",mc:"-",th:"Bond-proxy defensive sector. AI data centre power demand tailwind."},
  {tk:"XLRE",nm:"Real Estate Select",cat:"Stock",ex:"NYSE",sc:54,se:"Neutral",ra:"Hold",beta:0.85,pe:"-",mc:"-",th:"Rate-sensitive REITs basket. Benefits from falling rates."},
  // ─── High-beta & thematic ───
  {tk:"RKLB",nm:"Rocket Lab",cat:"Stock",ex:"NASDAQ",sc:62,se:"Bullish",ra:"Accumulate",beta:2.1,pe:"N/A",mc:"$14B",th:"Space launch and satellite infrastructure. Neutron rocket catalyst. Defense and commercial contracts growing."},
  {tk:"HOOD",nm:"Robinhood Markets",cat:"Stock",ex:"NASDAQ",sc:58,se:"Neutral-Bull",ra:"Hold",beta:2.4,pe:"28x",mc:"$42B",th:"Retail trading platform. Crypto and options revenue diversifying. Gold subscription growing. Rate on cash balances key driver."},
  {tk:"MSTR",nm:"MicroStrategy",cat:"Stock",ex:"NASDAQ",sc:55,se:"Volatile",ra:"Speculative",beta:3.5,pe:"N/A",mc:"$95B",th:"Bitcoin treasury strategy. Equity as leveraged BTC proxy. Software business secondary. Extreme volatility."},
  {tk:"GME",nm:"GameStop",cat:"Stock",ex:"NYSE",sc:40,se:"Volatile",ra:"Speculative",beta:2.8,pe:"N/A",mc:"$12B",th:"Meme stock with Bitcoin treasury pivot. Retail sentiment driven. Fundamentals disconnected from price action."},
  {tk:"SPOT",nm:"Spotify",cat:"Stock",ex:"NYSE",sc:68,se:"Bullish",ra:"Buy",beta:1.5,pe:"45x",mc:"$95B",th:"Audio streaming leader. Margin expansion from price increases and ad tier. Podcast and audiobook growth. Operating leverage emerging."},
  {tk:"LMT",nm:"Lockheed Martin",cat:"Stock",ex:"NYSE",sc:72,se:"Bullish",ra:"Buy",beta:0.65,pe:"18x",mc:"$115B",th:"Defense prime beneficiary of elevated geopolitical spending. F-35 backlog. Dividend aristocrat characteristics."},
  {tk:"BMY",nm:"Bristol-Myers Squibb",cat:"Stock",ex:"NYSE",sc:58,se:"Neutral",ra:"Hold",beta:0.45,pe:"8x",mc:"$98B",th:"Oncology pipeline post-Revlimid cliff. KarXT schizophrenia drug potential. High dividend yield floor."},
  {tk:"GILD",nm:"Gilead Sciences",cat:"Stock",ex:"NASDAQ",sc:64,se:"Neutral",ra:"Hold",beta:0.42,pe:"14x",mc:"$118B",th:"HIV franchise durable. Oncology expansion via Trodelvy. Yeztugo PrEP approval. Cash generative."},
  {tk:"ENPH",nm:"Enphase Energy",cat:"Stock",ex:"NASDAQ",sc:55,se:"Bearish",ra:"Hold",beta:2.0,pe:"22x",mc:"$12B",th:"Solar microinverter leader. US residential solar slowdown headwind. International expansion and storage attach rate key."},
  {tk:"FSLR",nm:"First Solar",cat:"Stock",ex:"NASDAQ",sc:70,se:"Bullish",ra:"Buy",beta:1.4,pe:"18x",mc:"$28B",th:"US-made thin-film solar panels. IRA subsidies tailwind. Data centre and utility scale demand."},
  {tk:"EOG",nm:"EOG Resources",cat:"Stock",ex:"NYSE",sc:72,se:"Bullish",ra:"Buy",beta:1.1,pe:"11x",mc:"$78B",th:"Premier US shale operator. Low-cost Permian production. Disciplined capital return."},
  {tk:"SLB",nm:"SLB (Schlumberger)",cat:"Stock",ex:"NYSE",sc:68,se:"Bullish",ra:"Buy",beta:1.2,pe:"14x",mc:"$62B",th:"Oilfield services leader. International offshore recovery. Digital and decarbonisation services growing."},
  {tk:"SO",nm:"Southern Company",cat:"Stock",ex:"NYSE",sc:62,se:"Neutral",ra:"Hold",beta:0.42,pe:"20x",mc:"$98B",th:"Regulated utility with nuclear and gas mix. Data centre power demand in Southeast US."},
  {tk:"PLD",nm:"Prologis",cat:"Stock",ex:"NYSE",sc:66,se:"Neutral",ra:"Hold",beta:1.0,pe:"28x",mc:"$108B",th:"Industrial logistics REIT leader. E-commerce warehouse demand. Rate sensitivity on cap rates."},
  {tk:"AMT",nm:"American Tower",cat:"Stock",ex:"NYSE",sc:64,se:"Neutral",ra:"Hold",beta:0.88,pe:"32x",mc:"$95B",th:"Cell tower REIT. 5G buildout and data transmission infrastructure. International exposure."},
  {tk:"EQIX",nm:"Equinix",cat:"Stock",ex:"NASDAQ",sc:72,se:"Bullish",ra:"Buy",beta:0.95,pe:"65x",mc:"$88B",th:"Data centre REIT. AI workload colocation demand. Interconnection revenue moat."},
  {tk:"SPG",nm:"Simon Property Group",cat:"Stock",ex:"NYSE",sc:60,se:"Neutral",ra:"Hold",beta:1.2,pe:"18x",mc:"$58B",th:"Premium mall REIT. Outlet and mixed-use pivot. Consumer discretionary exposure."},
  {tk:"O",nm:"Realty Income",cat:"Stock",ex:"NYSE",sc:65,se:"Neutral",ra:"Hold",beta:0.75,pe:"42x",mc:"$52B",th:"Monthly dividend REIT. Net lease retail and industrial. Bond-proxy with inflation escalators."},
  {tk:"VRTX",nm:"Vertex Pharmaceuticals",cat:"Stock",ex:"NASDAQ",sc:76,se:"Bullish",ra:"Buy",beta:0.55,pe:"28x",mc:"$118B",th:"CF franchise dominant. Pain and kidney disease pipeline expanding. Casgevy gene therapy approved."},
  {tk:"BRENT",nm:"Brent Crude",cat:"Commodity",ex:"ICE",sc:70,se:"Volatile",ra:"Hold",beta:0.5,pe:"-",mc:"-",th:"Global oil benchmark. Middle East supply risk premium. OPEC+ discipline key driver."},
  {tk:"URA",nm:"Global X Uranium ETF",cat:"Stock",ex:"NYSE",sc:68,se:"Bullish",ra:"Buy",beta:1.3,pe:"-",mc:"-",th:"Nuclear renaissance and AI power demand. Uranium miners and physical uranium exposure."},
  // ─── More Crypto ───
  {tk:"SHIB",nm:"Shiba Inu",cat:"Crypto",ex:"GLOBAL",sc:38,se:"Volatile",ra:"Speculative",beta:3.5,pe:"-",mc:"$12B",th:"Meme token with Shibarium L2. Retail-driven. Ecosystem development ongoing."},
  {tk:"PEPE",nm:"Pepe",cat:"Crypto",ex:"GLOBAL",sc:35,se:"Volatile",ra:"Speculative",beta:4.0,pe:"-",mc:"$5B",th:"Pure meme coin. No utility thesis. Extreme volatility and sentiment-driven."},
  {tk:"ATOM",nm:"Cosmos",cat:"Crypto",ex:"GLOBAL",sc:52,se:"Neutral",ra:"Hold",beta:1.9,pe:"-",mc:"$3B",th:"Inter-blockchain communication hub. IBC protocol connecting chains. App-chain thesis."},
  {tk:"INJ",nm:"Injective",cat:"Crypto",ex:"GLOBAL",sc:58,se:"Neutral-Bull",ra:"Accumulate",beta:2.3,pe:"-",mc:"$2B",th:"DeFi-focused L1 with order book DEX. Institutional derivatives narrative."},
  // ─── More FX crosses ───
  {tk:"EURJPY",nm:"EUR/JPY",cat:"FX",ex:"FOREX",sc:58,se:"Neutral",ra:"Watch",beta:0.2,pe:"-",mc:"-",th:"Carry trade barometer. ECB vs BOJ policy divergence. Risk sentiment proxy."},
  {tk:"GBPJPY",nm:"GBP/JPY",cat:"FX",ex:"FOREX",sc:56,se:"Volatile",ra:"Watch",beta:0.25,pe:"-",mc:"-",th:"High-volatility cross. UK inflation and BOJ intervention risk."},
];

const SIGS = [
  {a:"Energy",cat:"Bullish",s:"Strong",cf:88,x:"XOM +42% YTD. Hormuz closed. Supply constraints persist.",tg:"Sector",hz:"3-6mo"},
  {a:"Gold",cat:"Macro Tailwind",s:"Strong",cf:82,x:"$4,780. DXY <99. Central bank buying.",tg:"Commodity",hz:"6-12mo"},
  {a:"CPI/Fed",cat:"Warning",s:"Strong",cf:85,x:"CPI 3.3%. FOMC discussed hikes. Cuts off table.",tg:"Macro",hz:"Qtr"},
  {a:"Bitcoin",cat:"Accumulation",s:"Moderate",cf:68,x:"ETF inflows surging. MSBT launched. Reserves 9yr low.",tg:"Crypto",hz:"3-6mo"},
  {a:"Ceasefire",cat:"Geopolitical",s:"Strong",cf:78,x:"Expires Apr 22. Hormuz closed. Israel-Lebanon.",tg:"Risk",hz:"1-2wk"},
  {a:"AVGO",cat:"Momentum",s:"Strong",cf:80,x:"+18.1% in 2wk. AI accelerator wins driving rerating.",tg:"Stock",hz:"3-6mo"},
  {a:"Banks Q1",cat:"Catalyst",s:"Moderate",cf:65,x:"GS, JPM, C report. Trading rev strong from vol.",tg:"Earnings",hz:"1wk"},
  {a:"Sentiment",cat:"Contrarian",s:"Moderate",cf:72,x:"AAII bearish 51.4%. Historically → +16% fwd 12mo.",tg:"Signal",hz:"6-12mo"},
];

let NEWS = [];

const INVEST_LENSES = [
  {nm:"Value Lens",rl:"Fundamentals & Margin of Safety",cl:"var(--gn)",ic:"🏛",tagline:"Intrinsic value, moat durability, and margin of safety — not momentum."},
  {nm:"Quality Compounders",rl:"Durable Growth & Reinvestment",cl:"var(--gd)",ic:"🧠",tagline:"Invert the thesis first: what could permanently impair this business?"},
  {nm:"Catalyst Lens",rl:"Concentrated & Event-Driven",cl:"var(--bl)",ic:"⚡",tagline:"High conviction requires a specific catalyst and asymmetric payoff."},
  {nm:"Global Macro Lens",rl:"Cycles & Cross-Asset",cl:"var(--cy)",ic:"🌊",tagline:"Rates, liquidity, and regime determine when — not just what."},
  {nm:"Trend Lens",rl:"Momentum & Positioning",cl:"var(--pu)",ic:"📊",tagline:"Price action, flows, and narrative often lead fundamentals."},
];
const LENS_SYNTHESIS = "Risk Synthesis";
const LENS_REGIME_WEIGHTS = {
  "risk-on-strong": { "Trend Lens": 1.4, "Catalyst Lens": 1.2, "Global Macro Lens": 0.8, "Value Lens": 0.9, "Quality Compounders": 1.0 },
  "risk-on-fragile": { "Trend Lens": 1.1, "Catalyst Lens": 1.1, "Global Macro Lens": 1.0, "Value Lens": 1.0, "Quality Compounders": 1.0 },
  "risk-off": { "Global Macro Lens": 1.4, "Value Lens": 1.25, "Quality Compounders": 1.15, "Trend Lens": 0.7, "Catalyst Lens": 0.9 },
};
let lensThesis = {};
let lensMeta = null;
let lensIntel = null;
let termLensMeta = null;
let termLensIntel = null;

function _setLensThesis(tk, v) { lensThesis[tk] = v; }

function _getRegimeState() {
  // Missing inputs must stay "—" — never invent flat 0% (that paints a fake green day)
  const nosync = { p: "—", c: "—", d: 0, status: "unavailable" };
  const vix = liveSymbols.has("VIX") ? fp("VIX") : nosync;
  // Prefer live index; SPY is the ETF proxy when ^GSPC not synced this session
  let spx = nosync, spxProxy = null;
  if (liveSymbols.has("SPX")) {
    spx = fp("SPX");
  } else if (liveSymbols.has("SPY")) {
    spx = fp("SPY");
    spxProxy = "SPY";
  }
  let id = "risk-on-fragile", label = "Risk-On (Fragile)";
  const vv = parseFloat(vix.p);
  if (!isNaN(vv) && vix.p !== "—") {
    if (vv >= 25) { id = "risk-off"; label = "Risk-Off (Elevated Vol)"; }
    else if (vv < 16 && spx.status !== "unavailable" && spx.d > 0) { id = "risk-on-strong"; label = "Risk-On (Strong)"; }
  }
  const q = (tk) => liveSymbols.has(tk) ? fp(tk) : nosync;
  const dxy = q("DXY"), oil = q("WTI"), gold = q("XAU"), btc = q("BTC");
  return { id, label, spx: spx.p, spxChg: spx.c, spxProxy, vix: vix.p, dxy: dxy.p, oil: oil.p, gold: gold.p, btc: btc.p };
}

async function _prefetchLensData(tk) {
  const a = A.find(x => x.tk === tk);
  if (!a || a.cat !== "Stock") return;
  const tasks = [];
  if (!_finCache[tk]) tasks.push(fetch("/api/financials?symbol=" + encodeURIComponent(tk)).then(r => r.ok ? r.json() : null).then(d => { if (d) _finCache[tk] = d; }).catch(() => {}));
  if (!_earnCache[tk]) tasks.push(fetch("/api/earnings?symbol=" + encodeURIComponent(tk)).then(r => r.ok ? r.json() : null).then(d => { if (d) _earnCache[tk] = d; }).catch(() => {}));
  if (tasks.length) await Promise.allSettled(tasks);
}

function _buildLensContext(tk) {
  const a = A.find(x => x.tk === tk) || { nm: tk, th: "", sc: 50, se: "Neutral", cat: "Unknown" };
  // Feed-confirmed only — never pass "$—" / "—%" into the model as a quote
  const pxLive = livePx(tk);
  const chgLive = liveChg(tk);
  const priceLine = pxLive != null
    ? `Live price: $${pxLive}${chgLive != null ? ` (${chgLive >= 0 ? "+" : ""}${chgLive}%)` : ""} today [terminal feed]`
    : `Live price: NO SYNC — awaiting feed (do not invent a price)`;
  const regime = _getRegimeState();
  const powers = [pxLive != null ? "Live Price" : "Price Pending", "Regime", "Macro Signals", "Platform Thesis"];
  const signals = SIGS.slice().sort((x, y) => y.cf - x.cf).slice(0, 5).map(s => `${s.a} (${s.cf}% ${s.cat}): ${s.x}`).join("\n");
  const tickerNews = NEWS.filter(n => _tagNewsHeadline(n.x).includes(tk) || n.x.toUpperCase().includes(tk)).slice(0, 5).map(n => `[${n.tg}] ${n.x}`).join("\n");
  if (tickerNews) powers.push("News Feed");
  let finBlock = "";
  const fin = _finCache[tk];
  if (fin?.metrics) {
    powers.push("Financials");
    const m = fin.metrics;
    finBlock = `Financial metrics: P/E ${m.peTTM ?? "—"}, EV/EBITDA ${m.evEbitdaTTM ?? "—"}, ROE ${m.roeTTM ?? "—"}, ROIC ${m.roicTTM ?? "—"}, Net margin ${m.netProfitMarginTTM ?? "—"}, Rev growth ${m.revenueGrowthTTM ?? "—"}`;
    const rec = fin.recommendations?.[0];
    if (rec) finBlock += ` | Analyst: ${rec.strongBuy + rec.buy} buy / ${rec.hold} hold / ${rec.sell + rec.strongSell} sell`;
    if (fin.priceTarget?.targetMean) finBlock += ` | PT mean $${fin.priceTarget.targetMean}`;
  }
  let earnBlock = "";
  const ear = _earnCache[tk];
  if (ear?.history?.length) {
    powers.push("Earnings");
    const h = ear.history[0];
    const br = ear.beatRate != null ? ear.beatRate + "%" : "n/a";
    const as = ear.avgSurprise != null ? ear.avgSurprise + "%" : "n/a";
    earnBlock = `Earnings: beat rate ${br}, avg surprise ${as}, last ${h.quarter} EPS $${h.actual} vs est $${h.estimate} (${h.beat ? "beat" : "miss"})`;
    if (ear.nextEarnings?.date) earnBlock += `, next ${ear.nextEarnings.date}`;
  }
  const sector = typeof detectSector === "function" ? detectSector(tk) : "SP500";
  if (sector !== "SP500") powers.push("Sector Context");
  // Macro tape: omit legs without live marks (avoid "$—")
  const macroBits = [
    _liveTapeBit("SPX", "SPX") || _liveTapeBit("SPY", "SPY"),
    _liveTapeBit("VIX", "VIX"),
    _liveTapeBit("DXY", "DXY"),
    _liveTapeBit("Oil", "WTI"),
    _liveTapeBit("Gold", "XAU"),
    _liveTapeBit("BTC", "BTC"),
  ].filter(Boolean).join(" | ") || "awaiting live macro tape";
  const ctx = `═══ DISPATCH TERMINAL DATA (authoritative — prefer over stale search) ═══
Ticker: ${tk} (${a.nm})
Category: ${a.cat || "Unknown"} | Sector: ${sector}
${priceLine}
AI score: ${a.sc}/100 | Sentiment: ${a.se} | Rating: ${a.ra || "—"}
Beta: ${a.beta || "—"} | P/E: ${a.pe || "—"} | Market cap: ${a.mc || "—"}
Platform thesis: ${a.th || "None"}

Macro regime: ${regime.label}
Macro tape: ${macroBits}

Top macro signals:
${signals}${finBlock ? "\n" + finBlock : ""}${earnBlock ? "\n" + earnBlock : ""}${tickerNews ? "\nRecent headlines:\n" + tickerNews : ""}`;
  return { ctx, regime, powers, asset: a };
}

function _lensAnalysisPrompt(tk, nm, opts) {
  opts = opts || {};
  const built = opts.context || _buildLensContext(tk);
  const interrogate = (opts.userThesis || "").trim();
  const interrogateBlock = interrogate ? `

USER THESIS TO INTERROGATE — each lens must stress-test this view, not rubber-stamp it:
"${interrogate}"` : "";
  return `${built.ctx}${interrogateBlock}

Search for latest external data on ${tk} (${nm}) to supplement terminal data above. Evaluate through five investing PHILOSOPHIES only — do NOT name, quote, or impersonate any real investor, fund manager, or public figure.
Macro regime is "${built.regime.label}" — Global Macro Lens and Trend Lens must weight regime heavily.

Return ONLY a JSON array of 6 objects (no markdown/backticks):
[{"name":"Value Lens","role":"Fundamentals & Margin of Safety","analysis":"2-3 sentences citing terminal data","verdict":"BUY/HOLD/AVOID"},
{"name":"Quality Compounders","role":"Durable Growth & Reinvestment","analysis":"2-3 sentences citing terminal data","verdict":"HOLD/ACCUMULATE/AVOID"},
{"name":"Catalyst Lens","role":"Concentrated & Event-Driven","analysis":"2-3 sentences citing terminal data","verdict":"BUY/MONITOR/AVOID"},
{"name":"Global Macro Lens","role":"Cycles & Cross-Asset","analysis":"2-3 sentences citing terminal data","verdict":"OVERWEIGHT/NEUTRAL/REDUCE"},
{"name":"Trend Lens","role":"Momentum & Positioning","analysis":"2-3 sentences citing terminal data","verdict":"BUY/NEUTRAL/AVOID"},
{"name":"Risk Synthesis","role":"Final Synthesis","analysis":"3-4 sentences synthesizing lens disagreements, regime fit, and key risks","verdict":"IMPLEMENT/MONITOR/REJECT"}]

Prefer terminal live price when search conflicts. Risk Synthesis must name which lenses disagreed and why.`;
}

function _getSynthesis(res) { return res?.find(c => c.name === LENS_SYNTHESIS || c.name === "CRO"); }
function _getLensMembers(res) { return (res || []).filter(c => c.name !== LENS_SYNTHESIS && c.name !== "CRO"); }
function _verdictScore(v) {
  if (!v) return 0;
  const u = v.toUpperCase();
  if (u.includes("BUY") || u.includes("IMPLEMENT") || u.includes("OVERWEIGHT") || u.includes("ACCUMULATE")) return 1;
  if (u.includes("AVOID") || u.includes("SELL") || u.includes("REJECT") || u.includes("REDUCE")) return -1;
  return 0;
}
function _lensWeightedConsensus(members, regimeId) {
  const weights = LENS_REGIME_WEIGHTS[regimeId] || LENS_REGIME_WEIGHTS["risk-on-fragile"];
  let wSum = 0, score = 0;
  members.forEach(c => { const w = weights[c.name] || 1; score += _verdictScore(c.verdict) * w; wSum += w; });
  const avg = wSum ? score / wSum : 0;
  return { dir: avg > 0.25 ? "BUY" : avg < -0.25 ? "AVOID" : "HOLD", avg, regimeId };
}
function _lensMetaFromResult(members, context, userThesis, apiMeta) {
  const powers = [...(context.powers || [])];
  if (apiMeta?.dataSources) apiMeta.dataSources.forEach(s => { if (!powers.includes(s)) powers.push(s); });
  return { powers, regime: context.regime, weighted: _lensWeightedConsensus(members, context.regime.id), interrogate: !!(userThesis || "").trim(), engine: true, quote: apiMeta?.quote, momentum: apiMeta?.momentum };
}
function _renderLensPowers(meta) {
  if (!meta) return "";
  const pwr = meta.powers.map(p => `<span style="font-family:var(--mn);font-size:8px;background:var(--blG);color:var(--bl);border:1px solid rgba(79,142,247,0.2);padding:2px 7px;border-radius:12px">${p}</span>`).join("");
  const mode = meta.interrogate ? `<span style="font-family:var(--mn);font-size:8px;background:var(--puG);color:var(--pu);border:1px solid rgba(155,109,255,0.25);padding:2px 7px;border-radius:12px">Interrogate</span>` : "";
  const eng = meta.engine ? `<span style="font-family:var(--mn);font-size:8px;background:linear-gradient(135deg,rgba(59,130,246,0.15),rgba(155,109,255,0.15));color:var(--bl);border:1px solid rgba(59,130,246,0.3);padding:2px 7px;border-radius:12px">Lens Engine</span>` : "";
  return `<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px">${eng}${pwr}${mode}<span style="font-family:var(--mn);font-size:8px;background:var(--gdG);color:var(--gd);border:1px solid rgba(245,166,35,0.2);padding:2px 7px;border-radius:12px">${meta.regime?.label || "Regime"}</span></div>`;
}
function _renderLensIntel(intel) {
  if (!intel) return "";
  const conf = intel.confidence ?? 50;
  const confCol = conf >= 75 ? "var(--gn)" : conf >= 55 ? "var(--gd)" : "var(--rd)";
  const vc = (intel.verdict || "MONITOR").toUpperCase();
  const vcol = vc.includes("IMPLEMENT") || vc.includes("BUY") ? "var(--gn)" : vc.includes("REJECT") || vc.includes("AVOID") ? "var(--rd)" : "var(--gd)";
  let h = `<div class="gc" style="padding:14px;border:1.5px solid rgba(59,130,246,0.2);background:linear-gradient(135deg,rgba(59,130,246,0.06),rgba(155,109,255,0.03))">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px">
      <div>
        <div style="font-family:var(--mn);font-size:8px;color:var(--bl);letter-spacing:0.2em;margin-bottom:4px">⬢ LENS ENGINE INTELLIGENCE</div>
        <div style="font-size:22px;font-weight:900;color:${vcol};letter-spacing:-0.01em">${intel.verdict || "MONITOR"}</div>
        ${intel.positionSizing ? `<div style="font-family:var(--mn);font-size:9px;color:var(--t2);margin-top:4px">Sizing: <strong style="color:var(--tx)">${intel.positionSizing}</strong></div>` : ""}
      </div>
      <div style="text-align:center">
        <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">CONFIDENCE</div>
        <div style="font-family:var(--mn);font-size:28px;font-weight:900;color:${confCol};line-height:1">${conf}</div>
      </div>
    </div>`;
  if (intel.bullCase || intel.bearCase) {
    h += `<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px">
      <div style="background:var(--gnG);border:1px solid rgba(16,185,129,0.15);border-radius:9px;padding:11px">
        <div style="font-family:var(--mn);font-size:8px;color:var(--gn);letter-spacing:0.1em;margin-bottom:5px">▲ BULL CASE</div>
        <div style="font-size:11px;color:var(--t2);line-height:1.55">${intel.bullCase || "—"}</div>
      </div>
      <div style="background:var(--rdG);border:1px solid rgba(239,68,68,0.15);border-radius:9px;padding:11px">
        <div style="font-family:var(--mn);font-size:8px;color:var(--rd);letter-spacing:0.1em;margin-bottom:5px">▼ BEAR CASE</div>
        <div style="font-size:11px;color:var(--t2);line-height:1.55">${intel.bearCase || "—"}</div>
      </div>
    </div>`;
  }
  if (intel.actionPlan) {
    h += `<div style="background:var(--bg);border:1px solid var(--gb);border-radius:9px;padding:12px;margin-bottom:10px">
      <div style="font-family:var(--mn);font-size:8px;color:var(--bl);letter-spacing:0.15em;margin-bottom:6px">ACTION PLAN</div>
      <div style="font-size:12px;color:var(--t2);line-height:1.65">${intel.actionPlan}</div>
    </div>`;
  }
  if (intel.keyDisagreements?.length) {
    h += `<div style="margin-bottom:10px"><div style="font-family:var(--mn);font-size:8px;color:var(--pu);letter-spacing:0.15em;margin-bottom:6px">KEY DISAGREEMENTS</div>`;
    intel.keyDisagreements.forEach(d => { h += `<div style="font-size:11px;color:var(--t2);padding:4px 0;line-height:1.5;display:flex;gap:6px"><span style="color:var(--pu);flex-shrink:0">⚡</span>${d}</div>`; });
    h += `</div>`;
  }
  if (intel.catalysts?.length || intel.risks?.length) {
    h += `<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">`;
    if (intel.catalysts?.length) {
      h += `<div><div style="font-family:var(--mn);font-size:8px;color:var(--gn);letter-spacing:0.1em;margin-bottom:4px">CATALYSTS</div>${intel.catalysts.map(c => `<div style="font-size:10px;color:var(--t2);padding:2px 0">→ ${c}</div>`).join("")}</div>`;
    }
    if (intel.risks?.length) {
      h += `<div><div style="font-family:var(--mn);font-size:8px;color:var(--rd);letter-spacing:0.1em;margin-bottom:4px">MATERIAL RISKS</div>${intel.risks.map(r => `<div style="font-size:10px;color:var(--t2);padding:2px 0">⚠ ${r}</div>`).join("")}</div>`;
    }
    h += `</div>`;
  }
  h += `</div>`;
  return h;
}
async function _callLensEngine(tk, a, context, userThesis) {
  const res = await fetch("/api/lenses", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ticker: tk,
      name: a.nm,
      assetCategory: a.cat,
      terminalContext: context.ctx,
      userThesis,
      regime: context.regime,
    }),
  });
  if (res.status === 401) return { auth: true };
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const message = typeof data.error === "string" ? data.error : "Lens Engine is temporarily unavailable. Please try again shortly.";
    throw new Error(message);
  }
  const data = await res.json();
  if (!data.lenses?.length) throw new Error("No lens output");
  return { lenses: data.lenses, intelligence: data.intelligence, meta: data.meta };
}
function _lensFallback(tk, a) {
  const rows = INVEST_LENSES.map(m => ({ name: m.nm, role: m.rl, analysis: `${m.rl} view on ${tk}: Score ${a.sc}/100. ${(a.th || "").slice(0, 80)}...`, verdict: a.sc >= 70 ? "BUY" : "HOLD" }));
  rows.push({ name: LENS_SYNTHESIS, role: "Final Synthesis", analysis: `Lens consensus on ${tk}: ${a.sc >= 70 ? "Constructive" : "Mixed"}. Score ${a.sc}/100.`, verdict: a.sc >= 70 ? "IMPLEMENT" : "MONITOR" });
  return rows;
}

// ═══════════════════════════════════════════════════════════
// REGIME ENGINE · DISPATCH BRIEF · COMPARE · WATCHLIST SCAN
// ═══════════════════════════════════════════════════════════
function _computeRegimeEngine() {
  const r = _getRegimeState();
  // Never invent tape numbers (no default VIX 22 / DXY 99 / SPX 0%) — missing inputs stay neutral
  const num = (v) => {
    if (v == null || v === "—" || v === "") return null;
    const n = parseFloat(v);
    return isFinite(n) ? n : null;
  };
  const vix = num(r.vix);
  const spxC = num(r.spxChg); // null when unsynced — do NOT coerce to 0
  const oil = num(r.oil);
  const dxy = num(r.dxy);
  const btcC = liveSymbols.has("BTC") ? liveChg("BTC") : null;
  let score = 50;
  if (vix != null) {
    if (vix < 16) score += 18; else if (vix < 20) score += 8; else if (vix > 28) score -= 22; else if (vix > 22) score -= 12;
  }
  if (spxC != null) {
    if (spxC > 0.5) score += 8; else if (spxC < -0.5) score -= 10;
  }
  if (dxy != null) { if (dxy < 99) score += 6; else if (dxy > 101) score -= 6; }
  if (oil != null && oil > 95) score -= 5;
  if (btcC != null && btcC > 2) score += 4;
  score = Math.max(0, Math.min(100, score));
  const rot = typeof _sectorRotationSignal === "function" ? _sectorRotationSignal() : { label: "Mixed", col: "var(--gd)", desc: "" };
  let label = r.label, col = "var(--gd)";
  if (score >= 72) { label = "Risk-On (Strong)"; col = "var(--gn)"; }
  else if (score >= 55) { label = "Risk-On (Fragile)"; col = "var(--gd)"; }
  else if (score >= 40) { label = "Transition"; col = "var(--bl)"; }
  else { label = "Risk-Off"; col = "var(--rd)"; }
  const ow = [], uw = [], neu = [];
  if (score >= 60) { ow.push("Cyclicals", "Tech / AI", "Crypto"); uw.push("Long-duration bonds", "Defensive staples"); }
  else if (score >= 45) { ow.push("Quality compounders", "Energy", "Gold"); uw.push("High-beta growth", "Unprofitable tech"); neu.push("Healthcare", "Financials"); }
  else { ow.push("Gold", "Cash / T-bills", "Defensive sectors"); uw.push("Small caps", "Crypto", "High-beta"); }
  if (rot.label === "Risk-On Rotation") { if (!ow.includes("Cyclicals")) ow.unshift("Cyclicals (sector-led)"); }
  if (rot.label === "Defensive Rotation") { if (!ow.includes("Defensive sectors")) ow.unshift("Utilities / Staples"); }
  if (oil != null && oil > 90 && !ow.includes("Energy")) ow.push("Energy");
  const topSig = SIGS.slice().sort((a, b) => b.cf - a.cf)[0];
  const vixLbl = vix != null ? vix : "—";
  const spxLbl = spxC != null ? `${spxC >= 0 ? "+" : ""}${spxC}%` : "—";
  return { ...r, score, label, col, rotation: rot, overweight: ow.slice(0, 4), underweight: uw.slice(0, 4), neutral: neu, topSignal: topSig, narrative: `${label} · Regime score ${score}/100. ${rot.desc || ""} VIX ${vixLbl}, SPX ${spxLbl}.` };
}

function _renderRegimeEngine(re) {
  re = re || _computeRegimeEngine();
  return `<div class="gc gc-regime" style="border-left:3px solid ${re.col};cursor:pointer" onclick="nav('sectors')">
    <div style="display:flex;justify-content:space-between;align-items:flex-start">
      <div>
        <div style="display:flex;align-items:center;gap:6px"><div style="font-size:8px;color:${re.col};font-family:var(--mn);font-weight:700;letter-spacing:0.1em">REGIME ENGINE · MODEL</div><span class="live-dot" title="Uses live inputs when synced"></span></div>
        <div style="font-size:10px;color:var(--t3);margin-top:2px;font-family:var(--mn)">Educational score — not a forecast</div>
        <div style="font-size:15px;font-weight:800;color:${re.col};margin-top:4px">${re.label}</div>
        <div style="font-size:10px;color:var(--t2);margin-top:4px;line-height:1.5">${re.spxProxy ? "SPY" : "SPX"} ${re.spx === "—" ? "—" : "$" + re.spx}${re.spxChg === "—" ? "" : ` (${Number(re.spxChg) >= 0 ? "+" : ""}${re.spxChg}%)`}${re.spxProxy ? " · ETF proxy" : ""} · VIX ${re.vix} · Oil ${re.oil === "—" ? "—" : "$" + re.oil} · BTC ${re.btc === "—" ? "—" : "$" + re.btc}</div>
        <div style="font-size:9px;color:var(--t3);margin-top:6px;font-family:var(--mn)">${re.rotation?.label || ""}</div>
      </div>
      <div style="text-align:center;flex-shrink:0">
        <div style="font-family:var(--mn);font-size:8px;color:var(--t3)">SCORE</div>
        <div style="font-family:var(--mn);font-size:32px;font-weight:900;color:${re.col};line-height:1">${re.score}</div>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px;padding-top:10px;border-top:1px solid var(--gb)">
      <div><div style="font-family:var(--mn);font-size:7px;color:var(--gn);letter-spacing:0.12em;margin-bottom:4px">OVERWEIGHT</div>${re.overweight.map(x => `<div style="font-size:10px;color:var(--t2);padding:1px 0">+ ${x}</div>`).join("")}</div>
      <div><div style="font-family:var(--mn);font-size:7px;color:var(--rd);letter-spacing:0.12em;margin-bottom:4px">UNDERWEIGHT</div>${re.underweight.map(x => `<div style="font-size:10px;color:var(--t2);padding:1px 0">− ${x}</div>`).join("")}</div>
    </div>
  </div>`;
}

let _brief = null, _briefLoad = false, _briefAutoTried = false, _briefLastError = "";
function _briefCacheKey() { return "td_brief_" + new Date().toISOString().split("T")[0]; }

function _buildBriefContext() {
  const re = _computeRegimeEngine();
  const fg = calcFearGreed();
  const top = [...A].sort((a, b) => b.sc - a.sc).slice(0, 6).map(a => `${a.tk} (${a.sc}/100, ${a.se})`).join(", ");
  const sigs = SIGS.map(s => `${s.a} ${s.cf}% ${s.cat}: ${s.x}`).join("\n");
  const news = NEWS.slice(0, 8).map(n => `[${n.tg}] ${n.x}`).join("\n");
  // Live-only tape for AI brief — never pass "—" strings as prices
  const tape = [
    _liveTapeBit("SPX", "SPX") || _liveTapeBit("SPY", "SPY"),
    _liveTapeBit("VIX", "VIX"),
    _liveTapeBit("DXY", "DXY"),
    _liveTapeBit("WTI", "WTI"),
    _liveTapeBit("Gold", "XAU"),
    _liveTapeBit("BTC", "BTC"),
  ].filter(Boolean).join(" · ") || "awaiting live feed";
  const book = (typeof _newsBookTickers === "function" ? _newsBookTickers() : []).slice(0, 8);
  const bookLine = book.length
    ? book.map(tk => {
        const px = livePx(tk);
        const c = liveChg(tk);
        return px != null ? `${tk} $${px.toFixed(px >= 100 ? 2 : 4)}${c != null ? ` (${c >= 0 ? "+" : ""}${c.toFixed(2)}%)` : ""}` : `${tk} no-sync`;
      }).join(" · ")
    : "empty";
  return `Regime: ${re.label} (score ${re.score}/100)\n${re.narrative}\nOverweight: ${re.overweight.join(", ")}\nUnderweight: ${re.underweight.join(", ")}\nFear/Greed: ${fg.label} (${fg.score != null ? fg.score : "—"})\nLive tape: ${tape}\nBook: ${bookLine}\nTop conviction: ${top}\n\nMacro signals:\n${sigs}\n\nBreaking news:\n${news}`;
}

/**
 * Free-tier Dispatch Brief — pure client synthesis from free terminal data
 * (Yahoo prices, regime engine, signals, news). No Anthropic / no premium.
 */
function _liveTapeBit(label, ...tks) {
  // Only feed-confirmed marks — never treat fp().p "—" as a quote
  for (const tk of tks) {
    if (!liveSymbols.has(tk)) continue;
    const d = fp(tk);
    if (d.status === "unavailable") continue;
    const c = liveChg(tk);
    const chg = c != null ? ` (${c >= 0 ? "+" : ""}${Number(c).toFixed(2)}%)` : "";
    return `${label} ${d.p}${chg}`;
  }
  return null;
}
function _buildLocalBrief(reason) {
  const re = _computeRegimeEngine();
  const fg = calcFearGreed();
  const top = [...A].sort((a, b) => b.sc - a.sc).slice(0, 5);
  const house = re.score >= 68 ? "Constructive" : re.score >= 55 ? "Opportunistic" : re.score >= 40 ? "Cautious" : "Defensive";
  const topSig = SIGS.slice().sort((a, b) => b.cf - a.cf).slice(0, 4);
  const heads = NEWS.slice(0, 5).map(n => n.x || n.title || n.headline).filter(Boolean);
  // SPX preferred; SPY is live ETF proxy only when index not synced
  const tapeBits = [
    _liveTapeBit("SPX", "SPX") || _liveTapeBit("SPY", "SPY"),
    _liveTapeBit("VIX", "VIX"),
    _liveTapeBit("DXY", "DXY"),
    _liveTapeBit("EURUSD", "EURUSD"),
    _liveTapeBit("WTI", "WTI"),
    _liveTapeBit("Gold", "XAU"),
    _liveTapeBit("BTC", "BTC")
  ].filter(Boolean).join(" · ");
  const btcC = liveChg("BTC");
  const summaryParts = [
    re.narrative,
    tapeBits ? `Live tape: ${tapeBits}.` : "Live tape: awaiting feed sync.",
    `Fear/Greed: ${fg.label} (${fg.score != null ? fg.score : "—"}/100).`,
    heads[0] ? `Headline focus: ${heads[0]}.` : null,
    top[0] ? `Highest conviction on desk: ${top[0].tk} (${top[0].sc}/100, ${top[0].se || "n/a"}).` : null,
    "Research only — not investment advice."
  ].filter(Boolean);
  return {
    date: new Date().toISOString().split("T")[0],
    headline: `${re.label} — free desk brief from live tape`,
    houseView: house,
    confidence: Math.max(35, Math.min(88, re.score)),
    summary: summaryParts.join(" "),
    overweight: re.overweight || [],
    underweight: re.underweight || [],
    focusTickers: top.map(a => `${a.tk}: ${a.sc}/100 ${a.se || ""}`.trim()),
    catalysts: [
      ...topSig.map(s => `${s.a} (${s.cf}%): ${s.x}`),
      ...heads.slice(0, 2).map(h => `News: ${h}`)
    ].filter(Boolean).slice(0, 5),
    risks: [
      re.score < 50 ? "Risk-off regime — size down high-beta first" : "Risk-on can reverse fast if VIX spikes",
      "Free brief uses live free data only — no LLM synthesis",
      heads[1] || "Macro print / policy surprise can flip the score",
      btcC != null && Math.abs(btcC) > 3 ? `Crypto vol elevated (BTC ${btcC.toFixed(2)}%)` : null
    ].filter(Boolean).slice(0, 4),
    actionItems: [
      `Validate regime score (${re.score}) vs VIX / SPX move`,
      top[0] ? `Open ${top[0].tk} — check thesis vs ${house.toLowerCase()} house view` : "Build a 5-name watchlist for this regime",
      "Scan catalysts for the next 48h session",
      "Write one invalidation level for each open idea",
      _isPremium() ? "Upgrade path: AI Brief adds LLM house view (Premium)" : "Premium unlocks AI Brief, Lenses & Expert chat"
    ],
    _local: true,
    _free: true,
    _reason: reason || ""
  };
}

function _archiveBrief(brief) {
  if (!brief?.date) return;
  try {
    let hist = _lsJson(localStorage.getItem("td_brief_hist"), []);
    hist = hist.filter(h => h.date !== brief.date);
    hist.unshift(brief);
    if (hist.length > 14) hist.length = 14;
    localStorage.setItem("td_brief_hist", JSON.stringify(hist));
  } catch (e) { /* skip */ }
}

function _getBriefHistory() {
  try { return JSON.parse(localStorage.getItem("td_brief_hist") || "[]"); } catch (e) { return []; }
}

function _viewArchivedBrief(date) {
  const b = _getBriefHistory().find(h => h.date === date);
  if (b) { _brief = b; renderMain(); document.querySelector(".main")?.scrollTo(0, 0); }
}

function _renderBriefTeaser() {
  // Free users now get a real local brief — teaser only if generation not tried yet
  return `<div class="gc gc-a" style="padding:16px;border-left:3px solid var(--gd);cursor:pointer" onclick="loadDispatchBrief(true)">
    <div style="font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.2em;margin-bottom:6px">FREE DESK BRIEF · NO AI KEY NEEDED</div>
    <div style="font-size:14px;font-weight:700;color:var(--tx);margin-bottom:6px">Generate today's house view from live free data</div>
    <div style="font-size:11px;color:var(--t3);margin-bottom:10px">Regime engine · Yahoo tape · signals · headlines. Premium upgrades to LLM AI Brief.</div>
    <button onclick="event.stopPropagation();loadDispatchBrief(true)" style="width:100%;background:linear-gradient(135deg,#F59E0B,#F97316);color:#06060A;border:none;border-radius:8px;padding:11px;font-family:var(--sn);font-size:12px;font-weight:800;cursor:pointer">Generate Free Brief</button>
  </div>`;
}

function _briefNeedsRender() {
  // Never stomp news/port/analysis mid-interaction just because brief finished
  if (pg === "dash" || pg === "brief") return true;
  if (IS_DESKTOP() && (document.getElementById("briefOv") || document.getElementById("dashOv"))) return true;
  return false;
}
function _refreshBriefSurfaces() {
  if (!_briefNeedsRender()) return;
  if (IS_DESKTOP() && document.getElementById("briefOv") && typeof _refreshOverlay === "function") {
    _refreshOverlay("briefOv", renderBrief); return;
  }
  if (IS_DESKTOP() && document.getElementById("dashOv") && typeof _refreshOverlay === "function") {
    _refreshOverlay("dashOv", renderDash); return;
  }
  // Mobile: only full rebuild when user is on brief/dash; avoid thrash from silent auto-load
  if (MOBILE() && pg !== "brief" && pg !== "dash") return;
  renderMain();
}

async function loadDispatchBrief(force) {
  if (_briefLoad) return;
  const key = _briefCacheKey();
  const quiet = !force; // auto-loads should not toast spam

  // Serve today's cache unless force-refresh
  if (!force) {
    try {
      const c = localStorage.getItem(key);
      if (c) {
        _brief = JSON.parse(c);
        _briefAutoTried = true;
        _refreshBriefSurfaces();
        return;
      }
    } catch (e) { /* ignore bad cache */ }
  }

  // Stop renderMain → auto-load loops
  if (!force && _briefAutoTried && _brief) return;
  _briefAutoTried = true;
  _briefLoad = true;
  _briefLastError = "";
  _refreshBriefSurfaces();

  // 1) Always produce free local brief (works for everyone, no API cost)
  const local = _buildLocalBrief();
  _brief = local;
  try { localStorage.setItem(key, JSON.stringify(_brief)); } catch (e) { /* quota */ }
  _archiveBrief(_brief);

  // 2) AI upgrade: premium always; free users get 1 trial on explicit Generate only (not silent auto-load)
  const freeTrialKey = "td_ai_brief_trial_" + new Date().toISOString().slice(0, 10);
  const freeTrialLeft = !_isPremium() && !localStorage.getItem(freeTrialKey);
  // Never spam /api/brief on quiet boot for free users (was 401 every dash open)
  const tryAi = _isPremium() || (freeTrialLeft && !!force);
  if (tryAi) {
    try {
      const res = await fetch("/api/brief", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          context: _buildBriefContext(),
          force: !!force,
          trial: !_isPremium() && freeTrialLeft
        })
      });
      if (res.status === 401) {
        if (!quiet) showToast("Free desk brief ready · sign in for AI upgrade", "var(--gd)");
      } else if (res.status === 429) {
        try { localStorage.setItem(freeTrialKey, "1"); } catch (e) {}
        if (!quiet) showToast("Free AI trial used today · desk brief ready", "var(--gd)");
      } else {
        let data = {};
        try { data = await res.json(); } catch (e) { data = {}; }
        if (res.ok && data.brief) {
          _brief = data.brief;
          _brief._cached = !!data.cached;
          _brief._local = false;
          _brief._free = false;
          _brief._trial = !_isPremium();
          _briefLastError = "";
          if (!_isPremium()) try { localStorage.setItem(freeTrialKey, "1"); } catch (e) {}
          try { localStorage.setItem(key, JSON.stringify(_brief)); } catch (e) { /* quota */ }
          _archiveBrief(_brief);
          if (!quiet) showToast(
            data.trial || _brief._trial
              ? "AI Brief trial (1/day free) ready"
              : (data.cached ? "AI Brief (cached)" : "AI Dispatch Brief ready"),
            "var(--gn)"
          );
        } else {
          const raw = data?.error || "AI unavailable";
          _briefLastError = raw;
          const lowCredits = /credit|balance|billing|quota|rate.?limit|too low/i.test(raw);
          console.error("Brief AI error:", data);
          // Do NOT burn free trial key on AI billing/upstream failure — user can retry when credits restored
          _brief = _buildLocalBrief(lowCredits
            ? "AI credits empty — free desk brief from live tape (no LLM)"
            : raw);
          _brief._fallback = true;
          _brief._aiError = raw;
          try { localStorage.setItem(key, JSON.stringify(_brief)); } catch (e) { /* quota */ }
          _archiveBrief(_brief);
          if (!quiet) showToast(lowCredits
            ? "Free desk brief ready · AI provider temporarily unavailable"
            : "Free desk brief (AI offline)", "var(--gd)");
        }
      }
    } catch (e) {
      console.error("Brief network error:", e);
      _briefLastError = e?.message || "network error";
      if (!quiet) showToast("Free desk brief ready", "var(--gn)");
    }
  } else if (!quiet) {
    showToast(_isPremium() ? "Free desk brief ready" : (freeTrialLeft ? "Free desk brief ready · tap Generate for 1 AI trial/day" : "Free desk brief ready · AI trial used today"), "var(--gn)");
  }

  _briefLoad = false;
  _refreshBriefSurfaces();
}

function _briefMarkdown(b) {
  b = b || _brief;
  if (!b) return "";
  return [
    `# Dispatch Brief — ${b.date || "Today"}`,
    `## ${b.headline || "Market Brief"}`,
    `**House View:** ${b.houseView || "Neutral"}${b.confidence != null ? ` · Confidence ${b.confidence}` : ""}`,
    "",
    b.summary || "",
    "",
    b.overweight?.length ? `### Overweight\n${b.overweight.map(x => `- ${x}`).join("\n")}` : "",
    b.underweight?.length ? `### Underweight\n${b.underweight.map(x => `- ${x}`).join("\n")}` : "",
    b.focusTickers?.length ? `### Focus Tickers\n${b.focusTickers.map(t => `- ${t}`).join("\n")}` : "",
    b.catalysts?.length ? `### Catalysts\n${b.catalysts.map(c => `- ${c}`).join("\n")}` : "",
    b.risks?.length ? `### Risks\n${b.risks.map(r => `- ${r}`).join("\n")}` : "",
    b.actionItems?.length ? `### Research Agenda\n${b.actionItems.map(a => `- ${a}`).join("\n")}` : "",
    "",
    "---",
    "*Research only · Not investment advice · thedispatch.uk*"
  ].filter(Boolean).join("\n");
}

function _downloadBriefMd() {
  if (!_brief) { showToast("Generate a brief first", "var(--gd)"); return; }
  const blob = new Blob([_briefMarkdown()], { type: "text/markdown" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "dispatch-brief-" + (_brief.date || new Date().toISOString().split("T")[0]) + ".md";
  a.click();
  URL.revokeObjectURL(a.href);
  showToast("Brief downloaded", "var(--gn)");
}

function _exportBriefText() {
  if (!_brief) { showToast("Generate a brief first", "var(--gd)"); return; }
  const b = _brief;
  const lines = [
    `DISPATCH BRIEF — ${b.date || "Today"}`,
    `${b.headline || ""}`,
    `House View: ${b.houseView || "Neutral"}${b.confidence != null ? " (confidence " + b.confidence + ")" : ""}`,
    "",
    b.summary || "",
    "",
    b.overweight?.length ? "OVERWEIGHT: " + b.overweight.join(", ") : "",
    b.underweight?.length ? "UNDERWEIGHT: " + b.underweight.join(", ") : "",
    b.focusTickers?.length ? "\nFOCUS: " + b.focusTickers.join("; ") : "",
    b.catalysts?.length ? "\nCATALYSTS:\n" + b.catalysts.map(c => "• " + c).join("\n") : "",
    b.risks?.length ? "\nRISKS:\n" + b.risks.map(r => "• " + r).join("\n") : "",
    b.actionItems?.length ? "\nAGENDA:\n" + b.actionItems.map(a => "→ " + a).join("\n") : "",
    "",
    "Research only · Not investment advice · thedispatch.uk"
  ].filter(Boolean).join("\n");
  navigator.clipboard?.writeText(lines).then(() => showToast("Brief copied to clipboard", "var(--gn)")).catch(() => showToast("Copy failed — select text manually", "var(--rd)"));
}

function _renderDispatchBrief() {
  if (_briefLoad) return `<div class="gc" style="padding:20px;text-align:center;border-left:3px solid var(--gd)"><div style="width:14px;height:14px;border:2px solid var(--gd);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div><div style="font-family:var(--mn);font-size:10px;color:var(--gd)">GENERATING DISPATCH BRIEF…</div></div>`;
  if (!_brief) {
    return _renderBriefTeaser();
  }
  const b = _brief;
  const vc = b.houseView === "Constructive" || b.houseView === "Opportunistic" ? "var(--gn)" : b.houseView === "Defensive" || b.houseView === "Cautious" ? "var(--rd)" : "var(--gd)";
  const tierLbl = (b._local || b._free || b._fallback) ? "FREE DESK" : "AI PREMIUM";
  let h = `<div class="gc" style="padding:0;overflow:hidden;border-left:3px solid var(--gd)">
    <div style="padding:14px 16px;background:linear-gradient(135deg,rgba(245,166,35,0.08),transparent)">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;gap:6px;flex-wrap:wrap">
        <div style="font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.2em">DISPATCH BRIEF · ${b.date || "TODAY"} · ${tierLbl}${(b._local || b._free || b._fallback) ? " · MODEL (NOT LLM)" : " · AI"}</div>
        <div style="display:flex;gap:6px">${_renderBriefPlayBtn(true)}<button onclick="event.stopPropagation();loadDispatchBrief(true)" style="background:var(--b2);border:1px solid var(--gb);color:var(--t3);border-radius:5px;padding:3px 8px;font-family:var(--mn);font-size:8px;cursor:pointer">↻ Refresh</button></div>
      </div>
      <div style="font-family:var(--sf);font-size:20px;font-weight:400;line-height:1.2;margin-bottom:8px">${b.headline || "Market Brief"}</div>
      <div style="display:flex;gap:8px;align-items:center;margin-bottom:10px">
        <span style="font-family:var(--mn);font-size:11px;font-weight:800;color:${vc};padding:4px 10px;border:1px solid ${vc}40;border-radius:6px">${b.houseView || "Neutral"}</span>
        ${b.confidence != null ? `<span style="font-family:var(--mn);font-size:10px;color:var(--t3)">Confidence ${b.confidence}</span>` : ""}
      </div>
      <div style="font-size:12px;color:var(--t2);line-height:1.65">${b.summary || ""}</div>
      ${b._fallback&&b._aiError?`<div style="margin-top:8px;font-family:var(--mn);font-size:9px;color:var(--gd);letter-spacing:0.04em">AI upgrade offline · free tape brief active · ${String(b._aiError).slice(0,80).replace(/</g,"")}</div>`:""}
    </div>`;
  if (b.focusTickers?.length) {
    h += `<div style="padding:10px 16px;border-top:1px solid var(--gb)"><div style="font-family:var(--mn);font-size:8px;color:var(--bl);letter-spacing:0.15em;margin-bottom:6px">FOCUS TICKERS</div><div style="display:flex;flex-wrap:wrap;gap:5px">${b.focusTickers.map(t => { const tk = (t.match(/^[A-Z0-9.]+/) || [""])[0]; return tk ? `<button onclick="openA('${tk}')" style="font-family:var(--mn);font-size:9px;padding:4px 10px;border-radius:6px;border:1px solid var(--bl)30;background:var(--blG);color:var(--bl);cursor:pointer">${t.length > 28 ? t.slice(0, 28) + "…" : t}</button>` : `<span style="font-size:10px;color:var(--t2)">${t}</span>`; }).join("")}</div></div>`;
  }
  if (b.overweight?.length || b.underweight?.length) {
    h += `<div style="padding:10px 16px;border-top:1px solid var(--gb);display:grid;grid-template-columns:1fr 1fr;gap:10px">
      ${b.overweight?.length ? `<div><div style="font-family:var(--mn);font-size:7px;color:var(--gn);letter-spacing:0.12em;margin-bottom:4px">OVERWEIGHT</div>${b.overweight.map(x => `<div style="font-size:10px;color:var(--t2);padding:1px 0">+ ${x}</div>`).join("")}</div>` : ""}
      ${b.underweight?.length ? `<div><div style="font-family:var(--mn);font-size:7px;color:var(--rd);letter-spacing:0.12em;margin-bottom:4px">UNDERWEIGHT</div>${b.underweight.map(x => `<div style="font-size:10px;color:var(--t2);padding:1px 0">− ${x}</div>`).join("")}</div>` : ""}
    </div>`;
  }
  if (b.catalysts?.length || b.risks?.length) {
    h += `<div style="padding:10px 16px;border-top:1px solid var(--gb);display:grid;grid-template-columns:1fr 1fr;gap:10px">
      ${b.catalysts?.length ? `<div><div style="font-family:var(--mn);font-size:7px;color:var(--gn);letter-spacing:0.12em;margin-bottom:4px">CATALYSTS</div>${b.catalysts.map(c => `<div style="font-size:10px;color:var(--t2);padding:2px 0">⚡ ${c}</div>`).join("")}</div>` : ""}
      ${b.risks?.length ? `<div><div style="font-family:var(--mn);font-size:7px;color:var(--rd);letter-spacing:0.12em;margin-bottom:4px">RISKS</div>${b.risks.map(r => `<div style="font-size:10px;color:var(--t2);padding:2px 0">⚠ ${r}</div>`).join("")}</div>` : ""}
    </div>`;
  }
  if (b.actionItems?.length) {
    h += `<div style="padding:10px 16px;border-top:1px solid var(--gb)"><div style="font-family:var(--mn);font-size:8px;color:var(--pu);letter-spacing:0.15em;margin-bottom:6px">TODAY'S RESEARCH AGENDA</div>${b.actionItems.map(a => `<div style="font-size:11px;color:var(--t2);padding:3px 0;display:flex;gap:6px"><span style="color:var(--pu)">→</span>${a}</div>`).join("")}</div>`;
  }
  h += `<div style="font-family:var(--mn);font-size:7px;color:var(--t3);text-align:center;padding:8px;border-top:1px dotted var(--gb)">House view · Research only · Not investment advice</div></div>`;
  return h;
}

let _compareTks = [];
function compareWatchlist() {
  _compareTks = getActiveWl().tickers.slice(0, 3);
  if (_compareTks.length) _showOverlay("compareOv", "⚖ Compare Watchlist", _renderCompare());
  else showToast("Add tickers to watchlist first", "var(--gd)");
}

function _toggleCompare(tk) {
  const i = _compareTks.indexOf(tk);
  if (i >= 0) _compareTks.splice(i, 1);
  else if (_compareTks.length < 3) _compareTks.push(tk);
  else { showToast("Max 3 tickers to compare", "var(--gd)"); return; }
  if (_compareTks.length) _showOverlay("compareOv", "⚖ Ticker Compare", _renderCompare());
  else _hideOverlay("compareOv");
}
function _renderCompare() {
  if (!_compareTks.length) return `<div style="padding:20px;text-align:center;color:var(--t3)">Select tickers to compare</div>`;
  const rows = _compareTks.map(tk => A.find(x => x.tk === tk) || { tk, nm: tk, sc: 50, se: "—", ra: "—", beta: "—", pe: "—", mc: "—", th: "—", cat: "—" });
  const spyC = liveChg("SPY") ?? liveChg("SPX");
  const metrics = ["sc", "se", "ra", "pe", "beta", "mc", "cat"];
  const labels = { sc: "AI Score", se: "Sentiment", ra: "Rating", pe: "P/E", beta: "Beta", mc: "Mkt Cap", cat: "Category" };
  let h = `<div style="padding:12px;overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-family:var(--mn);font-size:11px;min-width:320px">
    <thead><tr style="border-bottom:2px solid var(--gb)"><th style="text-align:left;padding:8px;font-size:9px;color:var(--t3)">METRIC</th>${rows.map(r => `<th style="text-align:right;padding:8px;color:var(--gd)">${r.tk}</th>`).join("")}</tr></thead><tbody>`;
  h += `<tr style="border-bottom:1px solid var(--gb)"><td style="padding:8px;color:var(--t3)">Price</td>${rows.map(r => {
    const d = fp(r.tk);
    const na = d.status === "unavailable";
    return `<td style="text-align:right;padding:8px;font-weight:700;color:${na?"var(--t3)":"var(--tx)"}">${na?"—":"$"+d.p}</td>`;
  }).join("")}</tr>`;
  h += `<tr style="border-bottom:1px solid var(--gb)"><td style="padding:8px;color:var(--t3)">Day %</td>${rows.map(r => {
    const d = fp(r.tk);
    const na = d.status === "unavailable";
    const ch = liveChg(r.tk);
    const c = na || ch == null ? "var(--t3)" : ch > 0 ? "var(--gn)" : ch < 0 ? "var(--rd)" : "var(--t3)";
    return `<td style="text-align:right;padding:8px;color:${c}">${na||ch==null?"—":d.c+"%"}</td>`;
  }).join("")}</tr>`;
  h += `<tr style="border-bottom:1px solid var(--gb)"><td style="padding:8px;color:var(--t3)">vs SPY (day)</td>${rows.map(r => {
    const ch = liveChg(r.tk);
    if (ch == null || spyC == null) return `<td style="text-align:right;padding:8px;color:var(--t3)">—</td>`;
    const rel = ch - spyC;
    const c = rel >= 0 ? "var(--gn)" : "var(--rd)";
    return `<td style="text-align:right;padding:8px;color:${c}">${rel >= 0 ? "+" : ""}${rel.toFixed(2)}%</td>`;
  }).join("")}</tr>`;
  metrics.forEach(k => {
    h += `<tr style="border-bottom:1px solid var(--gb)"><td style="padding:8px;color:var(--t3)">${labels[k]}</td>${rows.map(r => `<td style="text-align:right;padding:8px">${r[k] ?? "—"}</td>`).join("")}</tr>`;
  });
  h += `</tbody></table></div>
    <div style="padding:12px;display:flex;gap:8px;flex-wrap:wrap">${rows.map(r => `<button onclick="openA('${r.tk}');_hideOverlay('compareOv')" style="flex:1;min-width:100px;background:var(--blG);color:var(--bl);border:1px solid rgba(79,142,247,0.2);border-radius:8px;padding:10px;font-family:var(--sn);font-size:11px;font-weight:700;cursor:pointer">Analyse ${r.tk}</button>`).join("")}
    <button onclick="_compareTks=[];_hideOverlay('compareOv')" style="background:var(--b2);border:1px solid var(--gb);color:var(--t3);border-radius:8px;padding:10px 14px;font-family:var(--mn);font-size:10px;cursor:pointer">Clear</button></div>`;
  return h;
}

let _wlScan = null;
function runWatchlistScan() {
  const wl = getActiveWl();
  // Full book — not only curated A[] (dyn / lookup names must scan too)
  const tks = (wl.tickers || []).filter(Boolean);
  if (!tks.length) { showToast("Add tickers to watchlist first", "var(--gd)"); return; }
  const w = tks.map(tk => {
    const a = A.find(x => x.tk === tk);
    return a || { tk, nm: tk, sc: 50, se: "Neutral", ra: "—", cat: "Other", beta: 1 };
  });
  const re = _computeRegimeEngine();
  const avgSc = Math.round(w.reduce((s, a) => s + (Number(a.sc) || 50), 0) / w.length);
  const bullish = w.filter(a => String(a.se || "").includes("Bull")).length;
  const bearish = w.filter(a => String(a.se || "").includes("Bear") || a.ra === "Avoid").length;
  const best = [...w].sort((a, b) => (b.sc || 0) - (a.sc || 0))[0];
  const worst = [...w].sort((a, b) => (a.sc || 0) - (b.sc || 0))[0];
  const spyC = liveChg("SPY") ?? liveChg("SPX");
  const leaders = spyC == null ? 0 : w.filter(a => { const c = liveChg(a.tk); return c != null && c > spyC; }).length;
  const cats = {};
  w.forEach(a => { cats[a.cat || "Other"] = (cats[a.cat || "Other"] || 0) + 1; });
  const topCat = Object.entries(cats).sort((a, b) => b[1] - a[1])[0];
  const aligned = re.score >= 55 ? bullish >= bearish : bearish <= bullish;
  _wlScan = { avgSc, bullish, bearish, best, worst, leaders, total: w.length, topCat, aligned, regime: re.label, tickers: w.map(a => a.tk) };
  renderMain();
}

function _renderWlScan() {
  if (!_wlScan) return "";
  const s = _wlScan;
  const alignCol = s.aligned ? "var(--gn)" : "var(--rd)";
  return `<div class="gc" style="padding:14px;border-left:3px solid var(--bl);margin-bottom:10px">
    <div style="font-family:var(--mn);font-size:8px;color:var(--bl);letter-spacing:0.18em;margin-bottom:10px">⬢ WATCHLIST SCAN</div>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--gb);border-radius:8px;overflow:hidden;margin-bottom:10px">
      <div style="background:var(--bg);padding:10px;text-align:center"><div style="font-size:8px;color:var(--t3)">AVG SCORE</div><div style="font-family:var(--mn);font-size:18px;font-weight:900;color:var(--gd)">${s.avgSc}</div></div>
      <div style="background:var(--bg);padding:10px;text-align:center"><div style="font-size:8px;color:var(--t3)">BULLISH</div><div style="font-family:var(--mn);font-size:18px;font-weight:900;color:var(--gn)">${s.bullish}</div></div>
      <div style="background:var(--bg);padding:10px;text-align:center"><div style="font-size:8px;color:var(--t3)">BEARISH</div><div style="font-family:var(--mn);font-size:18px;font-weight:900;color:var(--rd)">${s.bearish}</div></div>
      <div style="background:var(--bg);padding:10px;text-align:center"><div style="font-size:8px;color:var(--t3)">BEAT SPY</div><div style="font-family:var(--mn);font-size:18px;font-weight:900;color:var(--gn)">${s.leaders}/${s.total}</div></div>
    </div>
    <div style="font-size:11px;color:var(--t2);line-height:1.6;margin-bottom:8px">
      <strong style="color:var(--gn)">${s.best.tk}</strong> leads (${s.best.sc}/100) · <strong style="color:var(--rd)">${s.worst.tk}</strong> lags (${s.worst.sc}/100) · ${s.topCat ? s.topCat[0] + " heavy (" + s.topCat[1] + ")" : ""}
    </div>
    <div style="font-size:10px;color:${alignCol};font-family:var(--mn)">${s.aligned ? "✓ Watchlist tilt aligns with " + s.regime : "⚠ Watchlist tilt conflicts with " + s.regime + " — review sizing"}</div>
    <div style="display:flex;gap:6px;margin-top:10px;flex-wrap:wrap">${s.tickers.slice(0, 6).map(tk => `<button onclick="openA('${tk}')" style="font-family:var(--mn);font-size:9px;padding:4px 10px;border-radius:6px;border:1px solid var(--gb);background:var(--b2);color:var(--t2);cursor:pointer">${tk}</button>`).join("")}</div>
  </div>`;
}

function _tickerRelStrength(tk) {
  const spyC = liveChg("SPY") ?? liveChg("SPX");
  const ch = liveChg(tk);
  if (ch == null || spyC == null) {
    return { rel: null, col: "var(--t3)", label: "No sync" };
  }
  const rel = ch - spyC;
  // Flat vs SPY is neutral — not "outperforming"
  if (Math.abs(rel) < 0.05) return { rel, col: "var(--t3)", label: "In line" };
  return { rel, col: rel > 0 ? "var(--gn)" : "var(--rd)", label: rel > 0 ? "Outperforming" : "Underperforming" };
}

let _morningLoad = false;
/** Last Morning Desk Run summary (in-memory + session) */
let _deskRunResult = null;
try { _deskRunResult = JSON.parse(sessionStorage.getItem("td_desk_run") || "null"); } catch (e) { _deskRunResult = null; }

async function runMorningRoutine() {
  if (_morningLoad) return;
  _morningLoad = true;
  showToast("Syncing feeds…", "var(--gd)");
  if (pg === "dash" || pg === "brief") {
    if (IS_DESKTOP()) renderMain();
    else {
      const m = document.getElementById("main");
      if (m && m.querySelector(".section")) {
        const hero = m.querySelector(".card");
        if (hero) hero.style.opacity = "0.98";
        setTimeout(() => { if (hero) hero.style.opacity = "1"; }, 80);
      }
    }
  }
  fetchLivePrices();
  fetchLiveNews();
  if (getActiveWl().tickers.length) runWatchlistScan();
  await loadEarningsRadar();
  await loadDispatchBrief(false);
  _morningLoad = false;
  showToast("Sync complete", "var(--gn)");
  _onPageIntel(_INTEL_PAGE_MAP[pg] || "pulse", { tk: selTk });
  if (pg === "dash" || pg === "brief") {
    if (IS_DESKTOP()) renderMain();
    else {
      const m = document.getElementById("main");
      if (m && m.querySelector(".section")) {
        const hero = m.querySelector(".card");
        if (hero) hero.style.opacity = "0.98";
        setTimeout(() => { if (hero) hero.style.opacity = "1"; }, 80);
      }
    }
  }
}

/**
 * Morning Desk Run — full free ritual:
 * sync → free brief → regime pulse → top watchlist fits → suggest Lab action
 */
async function runMorningDeskRun() {
  if (_morningLoad) return;
  _morningLoad = true;
  showToast("Morning Desk Run…", "var(--gd)");
  if (pg !== "dash" && pg !== "brief") nav("dash");
  else if (IS_DESKTOP()) renderMain();

  fetchLivePrices();
  fetchLiveNews();
  if (getActiveWl().tickers.length) runWatchlistScan();
  await loadEarningsRadar();
  await loadDispatchBrief(false);

  const re = _computeRegimeEngine();
  const wl = getActiveWl().tickers || [];
  const fits = wl.map(tk => {
    const f = _tickerRegimeFit(tk, re);
    return { tk, score: f.score, label: f.label || "" };
  }).sort((a, b) => b.score - a.score);
  const top = fits.slice(0, 3);
  const weak = fits.filter(x => x.score < 45).slice(0, 2);
  const invHits = wl.filter(tk => {
    const inv = getInvalidation(tk);
    return inv && inv.rule && inv.rule.trim();
  }).length;

  _deskRunResult = {
    at: new Date().toISOString(),
    regime: re.label,
    regimeScore: re.score,
    briefHeadline: _brief?.headline || null,
    houseView: _brief?.houseView || null,
    top,
    weak,
    invHits,
    nextLab: (weak[0] || top[0] || { tk: "NVDA" }).tk
  };
  try { sessionStorage.setItem("td_desk_run", JSON.stringify(_deskRunResult)); } catch (e) { /* skip */ }

  _morningLoad = false;
  showToast("Desk Run complete", "var(--gn)");
  _onPageIntel("pulse", {});
  if (pg === "dash" || pg === "brief") {
    if (MOBILE()) { _patchLiveDataIfNeeded(); _patchCuratedPrices(); _refreshBriefSurfaces(); }
    else renderMain();
  } else nav("dash");
}

function _renderMorningRoutineBtn(compact) {
  if (_morningLoad) {
    return `<div style="${compact ? "" : "margin-bottom:10px;"}padding:12px;text-align:center;background:var(--b1);border:1px solid var(--gb);border-radius:9px"><div style="width:12px;height:12px;border:2px solid var(--gd);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 6px"></div><div style="font-family:var(--mn);font-size:9px;color:var(--gd)">DESK RUN…</div></div>`;
  }
  if (compact) {
    return `<button onclick="runMorningDeskRun()" title="Brief → regime → watchlist fits" style="background:linear-gradient(135deg,var(--gd),#F97316);color:var(--bg);border:none;border-radius:8px;padding:8px 12px;font-family:var(--mn);font-size:9px;font-weight:800;cursor:pointer">☀ Desk Run</button>`;
  }
  return `<button onclick="runMorningDeskRun()" style="width:100%;margin-bottom:10px;background:linear-gradient(135deg,var(--gd),#F97316);color:var(--bg);border:none;border-radius:8px;padding:11px;font-family:var(--mn);font-size:11px;font-weight:800;cursor:pointer">☀ Morning Desk Run</button>`;
}

function _renderMorningDeskRunCard() {
  const r = _deskRunResult;
  if (_morningLoad) {
    return `<div class="desk-run-card desk-run-loading"><div class="lab-panel-k">MORNING DESK RUN</div><div class="desk-run-spin"></div><div class="desk-run-sub">Syncing feeds · brief · regime · watchlist fits…</div></div>`;
  }
  if (!r) {
    return `<div class="desk-run-card">
      <div class="lab-panel-k">MORNING DESK RUN</div>
      <div class="desk-run-title">Start your independent analyst loop</div>
      <p class="desk-run-lead">One click: free brief → regime pulse → top watchlist fits → next Lab action. No AI credits required.</p>
      <div class="desk-run-steps">
        <span>1 Brief</span><span>→</span><span>2 Regime</span><span>→</span><span>3 Watch fits</span><span>→</span><span>4 Act</span>
      </div>
      <button type="button" class="desk-run-cta" onclick="runMorningDeskRun()">☀ Run Morning Desk</button>
    </div>`;
  }
  const t = r.at ? new Date(r.at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "";
  const topHtml = (r.top || []).map(x =>
    `<button type="button" class="desk-fit-chip ok" onclick="setLabTicker('${x.tk}');nav('lab')"><span>${x.tk}</span><b>${x.score}%</b></button>`
  ).join("") || `<span class="desk-run-muted">Add names to your watchlist for fit ranks</span>`;
  const weakHtml = (r.weak || []).map(x =>
    `<button type="button" class="desk-fit-chip weak" onclick="setLabTicker('${x.tk}');nav('lab')"><span>${x.tk}</span><b>${x.score}%</b></button>`
  ).join("");
  return `<div class="desk-run-card desk-run-done">
    <div class="desk-run-head">
      <div class="lab-panel-k">DESK RUN · ${t}</div>
      <button type="button" class="lab-fs-btn" onclick="runMorningDeskRun()">↻ Re-run</button>
    </div>
    <div class="desk-run-regime">${r.regime} <span>${r.regimeScore}/100</span></div>
    ${r.briefHeadline ? `<div class="desk-run-brief"><strong>Brief:</strong> ${r.briefHeadline}${r.houseView ? ` · <em>${r.houseView}</em>` : ""}</div>` : ""}
    <div class="desk-run-block"><div class="desk-run-lbl">Best regime fits</div><div class="desk-fit-row">${topHtml}</div></div>
    ${weakHtml ? `<div class="desk-run-block"><div class="desk-run-lbl">Fighting the tape — stress in Lab</div><div class="desk-fit-row">${weakHtml}</div></div>` : ""}
    <div class="desk-run-meta">${r.invHits || 0} invalidation rule(s) on watchlist · educational only</div>
    <div class="desk-run-actions">
      <button type="button" class="lab-hud-act lab-hud-gold" onclick="setLabTicker('${r.nextLab || "NVDA"}');nav('lab')">Lab → ${r.nextLab || "NVDA"}</button>
      <button type="button" class="lab-hud-act" onclick="nav('brief')">Open Brief</button>
      <button type="button" class="lab-hud-act" onclick="nav('watch')">Watchlist</button>
    </div>
  </div>`;
}

// ── Fixed multi-asset spine (always the same desk board) ────
const DESK_SPINE = [
  { tk: "XAU", lbl: "Gold" },
  { tk: "WTI", lbl: "Oil" },
  { tk: "NG", lbl: "Nat Gas" },
  { tk: "COPPER", lbl: "Copper" },
  { tk: "SPX", lbl: "S&P 500" },
  { tk: "IXIC", lbl: "Nasdaq" },
  { tk: "RUT", lbl: "Russell" },
  { tk: "DXY", lbl: "DXY" },
  { tk: "EURUSD", lbl: "EURUSD" },
  { tk: "BTC", lbl: "Bitcoin" },
  { tk: "VIX", lbl: "VIX" }
];

function _renderDeskSpine() {
  const cells = DESK_SPINE.map(s => {
    const d = fp(s.tk);
    const synced = d.status !== "unavailable";
    const chN = liveChg(s.tk);
    const col = !synced || chN == null ? "var(--t3)" : chN > 0 ? "var(--gn)" : chN < 0 ? "var(--rd)" : "var(--t3)";
    const chg = !synced || chN == null ? "—" : `${chN >= 0 ? "+" : ""}${d.c}%`;
    const title = _escAttr(`${s.lbl} · ${d.label || "NO SYNC"}${d.asOf ? ` · as of ${_fmtAsOf(d.asOf)}` : ""} · ${d.detail || "tap for Lab"}`);
    return `<button type="button" class="spine-cell${synced ? "" : " spine-nosync"}" onclick="setLabTicker('${s.tk}');nav('lab')" title="${title}">
      <span class="spine-lbl">${s.lbl} ${stat(s.tk)}</span>
      <span class="spine-tk">${s.tk}</span>
      <span class="spine-px">${synced ? d.p : "—"}</span>
      <span class="spine-chg" style="color:${col}">${chg}</span>
      <span class="spine-asof">${synced ? `as of ${_fmtAsOf(d.asOf)}` : "awaiting feed"}</span>
    </button>`;
  }).join("");
  return `<div class="desk-spine" id="desk-spine">
    <div class="desk-spine-head">
      <div class="lab-panel-k" style="margin:0">DESK SPINE · FIXED UNIVERSE</div>
      <span class="desk-spine-hint">Seed hidden until feed sync · badge = provenance</span>
    </div>
    <div class="desk-spine-row">${cells}</div>
  </div>`;
}

// ── Weekly Desk Letter (interactive, not inbox) ─────────────
function _weekMondayKey() {
  const d = new Date();
  const mon = new Date(d);
  mon.setHours(12, 0, 0, 0);
  mon.setDate(d.getDate() - ((d.getDay() + 6) % 7));
  return mon.toISOString().slice(0, 10);
}
function _weekLetterLabel() {
  const mon = new Date(_weekMondayKey() + "T12:00:00");
  return mon.toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric", year: "numeric" });
}
function _deskLetterTitle(re, brief) {
  if (brief?.headline) return brief.headline;
  const s = re?.score ?? 50;
  if (s >= 72) return "Risk appetite still runs the tape";
  if (s >= 55) return "Fragile risk-on — leadership is selective";
  if (s >= 40) return "Rotation without a clean regime";
  return "Defensive tape — protect first, size later";
}
function _deskLetterDeck(re, brief) {
  if (brief?.summary) return String(brief.summary).slice(0, 220) + (brief.summary.length > 220 ? "…" : "");
  return `${re.label} (score ${re.score}/100). ${re.narrative || ""} Favour: ${(re.overweight || []).slice(0, 3).join(", ") || "—"}. Underweight: ${(re.underweight || []).slice(0, 2).join(", ") || "—"}.`;
}
function _suggestMacroPack(re) {
  const s = re?.score ?? 50;
  if (s >= 68) return "soft_landing";
  if (s >= 55) return "balanced";
  if (s >= 42) return "sticky_inflation";
  return "risk_off_shock";
}

function _renderWeeklyDeskLetter() {
  const re = _computeRegimeEngine();
  const brief = _brief;
  const r = _deskRunResult;
  const title = _escHtml(_deskLetterTitle(re, brief));
  const deck = _escHtml(_deskLetterDeck(re, brief));
  const packId = _suggestMacroPack(re);
  const pack = (typeof LAB_MACRO_PACKS !== "undefined" && LAB_MACRO_PACKS[packId])
    ? LAB_MACRO_PACKS[packId]
    : { lbl: "Balanced base", desc: "Baseline teaching blend" };
  const weekLbl = _escHtml(_weekLetterLabel());
  const tier = brief?._local || brief?._free || brief?._fallback || !brief ? "FREE DESK" : "AI DESK";

  // Top 3 fits: prefer desk run, else compute live from watchlist
  let top = (r && r.top) || [];
  if (!top.length) {
    const wl = (typeof getActiveWl === "function" ? getActiveWl().tickers : []) || [];
    top = wl.map(tk => ({ tk, score: _tickerRegimeFit(tk, re).score }))
      .sort((a, b) => b.score - a.score).slice(0, 3);
  }
  const weak = (r && r.weak) || [];
  const topHtml = top.length
    ? top.map(x => `<button type="button" class="letter-chip" onclick="setLabTicker('${_escAttr(x.tk)}');nav('lab')">${_escHtml(x.tk)} <b>${Number(x.score) || 0}%</b></button>`).join("")
    : `<span class="desk-run-muted">Add watchlist names — fits appear here after Desk Run</span>`;
  const weakHtml = weak.length
    ? weak.map(x => `<button type="button" class="letter-chip weak" onclick="setLabTicker('${_escAttr(x.tk)}');nav('lab')">${_escHtml(x.tk)} <b>${Number(x.score) || 0}%</b></button>`).join("")
    : "";

  const ow = (brief?.overweight || re.overweight || []).slice(0, 3).map(_plainItem).map(_escHtml);
  const uw = (brief?.underweight || re.underweight || []).slice(0, 3).map(_plainItem).map(_escHtml);
  const focus = (brief?.focusTickers || []).slice(0, 3);
  const reLabel = _escHtml(re.label || "—");
  const house = brief?.houseView ? _escHtml(brief.houseView) : "";

  return `<div class="desk-letter" id="desk-letter">
    <div class="desk-letter-kicker">
      <span>DISPATCH WEEKLY DESK LETTER · RESEARCH ONLY</span>
      <span class="desk-letter-week">${weekLbl} · ${tier}${tier.includes("FREE") ? " · MODEL" : ""}</span>
    </div>
    <h2 class="desk-letter-title">${title}</h2>
    <p class="desk-letter-deck">${deck}</p>
    <div class="desk-letter-meta">
      <span class="desk-letter-tag" style="color:${re.col || "var(--gd)"}">${reLabel}</span>
      <span class="desk-letter-tag">Score ${Number(re.score) || 0}/100</span>
      ${house ? `<span class="desk-letter-tag">${house}</span>` : ""}
      ${brief?.confidence != null ? `<span class="desk-letter-tag">Conf ${Number(brief.confidence) || 0}</span>` : ""}
    </div>
    <div class="desk-letter-grid">
      <div class="desk-letter-col">
        <div class="desk-run-lbl">HOUSE TILT</div>
        <div class="desk-letter-lists">
          <div><span class="up">Overweight</span>${ow.map(x => `<div>· ${x}</div>`).join("") || "<div class='desk-run-muted'>—</div>"}</div>
          <div><span class="dn">Underweight</span>${uw.map(x => `<div>· ${x}</div>`).join("") || "<div class='desk-run-muted'>—</div>"}</div>
        </div>
        ${focus.length ? `<div class="desk-run-lbl" style="margin-top:10px">BRIEF FOCUS</div><div class="desk-fit-row">${focus.map(t => {
          const raw = _plainItem(t);
          const tk = (raw.match(/^[A-Z0-9.]+/) || [""])[0];
          const show = _escHtml(raw.slice(0, 28));
          return tk ? `<button type="button" class="letter-chip" onclick="setLabTicker('${_escAttr(tk)}');nav('lab')">${show}</button>` : `<span class="letter-chip">${show}</span>`;
        }).join("")}</div>` : ""}
      </div>
      <div class="desk-letter-col">
        <div class="desk-run-lbl">WATCHLIST FITS THIS WEEK</div>
        <div class="desk-fit-row">${topHtml}</div>
        ${weakHtml ? `<div class="desk-run-lbl" style="margin-top:10px">STRESS THESE IN LAB</div><div class="desk-fit-row">${weakHtml}</div>` : ""}
        <div class="desk-run-lbl" style="margin-top:10px">SUGGESTED MACRO PACK</div>
        <button type="button" class="letter-pack" onclick="applyLabMacroPack('${_escAttr(packId)}')">${_escHtml(pack.lbl)} → load in Lab</button>
        <div class="lab-pack-desc" style="margin-top:6px">${_escHtml(pack.desc)}</div>
      </div>
    </div>
    <div class="desk-letter-actions">
      <button type="button" class="desk-run-cta desk-letter-cta" onclick="runMorningDeskRun()">☀ Refresh letter (Desk Run)</button>
      <button type="button" class="lab-hud-act" onclick="nav('brief')">Full Brief</button>
      <button type="button" class="lab-hud-act lab-hud-gold" onclick="applyLabMacroPack('${_escAttr(packId)}')">Open Lab + pack</button>
      <button type="button" class="lab-hud-act" onclick="nav('watch')">Watchlist</button>
    </div>
    <div class="desk-letter-foot">Interactive desk letter · free live data · research only, not investment advice · not a third-party newsletter</div>
  </div>`;
}

// ── Named Macro Packs (Lab) ─────────────────────────────────
const LAB_MACRO_PACKS = {
  soft_landing: { riskOn: 55, neutral: 30, riskOff: 15, lbl: "Soft landing", desc: "Growth holds, vol cools — cyclicals / quality favoured" },
  sticky_inflation: { riskOn: 25, neutral: 30, riskOff: 45, lbl: "Sticky inflation", desc: "Higher for longer — pressure on duration & high-β growth" },
  risk_off_shock: { riskOn: 10, neutral: 20, riskOff: 70, lbl: "Risk-off shock", desc: "Equity selloff / liquidity stress — defensives & cash" },
  oil_spike: { riskOn: 28, neutral: 27, riskOff: 45, lbl: "Oil spike", desc: "Energy shock, stagflation tilt — energy up, consumers hurt" },
  liquidity_squeeze: { riskOn: 15, neutral: 25, riskOff: 60, lbl: "Liquidity squeeze", desc: "Credit tightens — high-β and unprofitable names hurt most" },
  balanced: { riskOn: 40, neutral: 35, riskOff: 25, lbl: "Balanced base", desc: "No strong macro bet — baseline teaching blend" }
};
let _labActivePack = localStorage.getItem("td_lab_pack") || "";

function applyLabMacroPack(id) {
  const p = LAB_MACRO_PACKS[id];
  if (!p) return;
  _labScenario = { riskOn: p.riskOn, neutral: p.neutral, riskOff: p.riskOff };
  _labActivePack = id;
  try {
    localStorage.setItem("td_lab_scenario", JSON.stringify(_labScenario));
    localStorage.setItem("td_lab_pack", id);
  } catch (e) { /* skip */ }
  showToast("Macro pack: " + p.lbl, "var(--gd)");
  if (pg === "lab") _refreshPageView();
  else { nav("lab"); }
}

function _renderLabMacroPacks() {
  return `<div class="lab-packs">
    <div class="lab-packs-lbl">Named packs <span>(Fed-style stories — tap to load sliders)</span></div>
    <div class="lab-packs-row">${Object.entries(LAB_MACRO_PACKS).map(([id, p]) =>
      `<button type="button" class="lab-pack-btn${_labActivePack === id ? " on" : ""}" onclick="applyLabMacroPack('${id}')" title="${p.desc}">${p.lbl}</button>`
    ).join("")}</div>
    ${_labActivePack && LAB_MACRO_PACKS[_labActivePack] ? `<div class="lab-pack-desc">${LAB_MACRO_PACKS[_labActivePack].desc}</div>` : `<div class="lab-pack-desc">Or drag sliders freehand. Packs are teaching scenarios, not forecasts.</div>`}
  </div>`;
}

// ── Invalidation Cards ──────────────────────────────────────
function _invStore() {
  try { return JSON.parse(localStorage.getItem("td_invalidations_v1") || "{}"); } catch (e) { return {}; }
}
function _invSaveStore(obj) {
  try { localStorage.setItem("td_invalidations_v1", JSON.stringify(obj)); } catch (e) { /* skip */ }
}
function getInvalidation(tk) {
  return _invStore()[tk] || null;
}
function saveInvalidation(tk) {
  tk = tk || _labTk;
  const thesis = document.getElementById("inv-thesis")?.value?.trim() || "";
  const why = document.getElementById("inv-why")?.value?.trim() || "";
  const rule = document.getElementById("inv-rule")?.value?.trim() || "";
  const size = document.getElementById("inv-size")?.value?.trim() || "";
  if (!rule && !thesis) {
    showToast("Add a thesis or invalidation rule", "var(--gd)");
    return;
  }
  const store = _invStore();
  store[tk] = { thesis, why, rule, size, updated: new Date().toISOString() };
  _invSaveStore(store);
  showToast("Invalidation saved for " + tk, "var(--gn)");
  const host = document.getElementById("lab-inv-card");
  if (host) host.outerHTML = _renderInvalidationCard(tk);
}
function clearInvalidation(tk) {
  tk = tk || _labTk;
  const store = _invStore();
  delete store[tk];
  _invSaveStore(store);
  showToast("Cleared " + tk, "var(--t2)");
  const host = document.getElementById("lab-inv-card");
  if (host) host.outerHTML = _renderInvalidationCard(tk);
}
function _escAttr(s) {
  return String(s || "").replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function _escHtml(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
function _plainItem(x) {
  if (x == null) return "";
  if (typeof x === "string" || typeof x === "number") return String(x);
  if (typeof x === "object") return String(x.label || x.name || x.tk || x.text || JSON.stringify(x));
  return String(x);
}
function _renderInvalidationCard(tk) {
  tk = tk || _labTk;
  const inv = getInvalidation(tk) || {};
  return `<div class="lab-panel lab-inv" id="lab-inv-card">
    <div class="lab-panel-k">INVALIDATION CARD · ${tk}</div>
    <p class="lab-panel-help">Munger-style inversion: write what would prove you wrong <em>before</em> you size the idea. Free · saved on this device.</p>
    <label class="lab-inv-label">Thesis (1 line)</label>
    <input id="inv-thesis" class="lab-inv-input" maxlength="160" placeholder="e.g. NVDA stays AI capex leader into 2027" value="${_escAttr(inv.thesis)}">
    <label class="lab-inv-label">Why it works</label>
    <input id="inv-why" class="lab-inv-input" maxlength="200" placeholder="e.g. Regime fit + sector leadership + earnings path" value="${_escAttr(inv.why)}">
    <label class="lab-inv-label">Invalidates if…</label>
    <input id="inv-rule" class="lab-inv-input lab-inv-kill" maxlength="200" placeholder="e.g. Weekly close below 200DMA or guidance cut" value="${_escAttr(inv.rule)}">
    <label class="lab-inv-label">Size intent</label>
    <input id="inv-size" class="lab-inv-input" maxlength="80" placeholder="e.g. Starter 1% · add on confirmation" value="${_escAttr(inv.size)}">
    <div class="lab-check-actions" style="margin-top:10px">
      <button type="button" class="lab-hud-act lab-hud-gold" onclick="saveInvalidation('${tk}')">Save kill-switch</button>
      ${inv.rule ? `<button type="button" class="lab-hud-act" onclick="clearInvalidation('${tk}')">Clear</button>` : ""}
    </div>
    ${inv.updated ? `<div class="lab-inv-meta">Updated ${new Date(inv.updated).toLocaleString()}</div>` : ""}
  </div>`;
}

// ── Desk Notes (Lab snapshots) ───────────────────────────────
function _deskNotesStore() {
  try { return JSON.parse(localStorage.getItem("td_desk_notes_v1") || "[]"); } catch (e) { return []; }
}
function _deskNotesSave(list) {
  try { localStorage.setItem("td_desk_notes_v1", JSON.stringify(list.slice(0, 14))); } catch (e) { /* skip */ }
}
function saveDeskNote() {
  const noteEl = document.getElementById("desk-note-text");
  const text = (noteEl?.value || "").trim();
  const re = _computeRegimeEngine();
  const fit = _tickerRegimeFit(_labTk, re);
  const entry = {
    id: Date.now().toString(36),
    at: new Date().toISOString(),
    tk: _labTk,
    range: _labRange,
    scenario: { ..._labScenario },
    pack: _labActivePack || null,
    fit: fit.score,
    regime: re.label,
    regimeScore: re.score,
    price: livePx(_labTk) ?? null,
    note: text
  };
  const list = _deskNotesStore();
  list.unshift(entry);
  _deskNotesSave(list);
  if (noteEl) noteEl.value = "";
  showToast("Desk note saved · " + _labTk, "var(--gn)");
  const host = document.getElementById("lab-notes");
  if (host) host.outerHTML = _renderDeskNotesPanel();
}
function loadDeskNote(id) {
  const n = _deskNotesStore().find(x => x.id === id);
  if (!n) return;
  _labTk = n.tk;
  _labRange = n.range || "1mo";
  if (n.scenario) _labScenario = { ...n.scenario };
  _labActivePack = n.pack || "";
  try {
    localStorage.setItem("td_lab_tk", _labTk);
    localStorage.setItem("td_lab_range", _labRange);
    localStorage.setItem("td_lab_scenario", JSON.stringify(_labScenario));
    if (_labActivePack) localStorage.setItem("td_lab_pack", _labActivePack);
  } catch (e) { /* skip */ }
  showToast("Loaded note · " + n.tk, "var(--bl)");
  if (pg === "lab") _refreshPageView();
  else nav("lab");
}
function deleteDeskNote(id) {
  _deskNotesSave(_deskNotesStore().filter(x => x.id !== id));
  showToast("Note deleted", "var(--t2)");
  const host = document.getElementById("lab-notes");
  if (host) host.outerHTML = _renderDeskNotesPanel();
}
function _renderDeskNotesPanel() {
  const list = _deskNotesStore();
  const rows = list.length
    ? list.map(n => {
      const when = new Date(n.at).toLocaleDateString([], { month: "short", day: "numeric" });
      const packLbl = n.pack && LAB_MACRO_PACKS[n.pack] ? LAB_MACRO_PACKS[n.pack].lbl : "custom";
      return `<div class="desk-note-row">
        <button type="button" class="desk-note-main" onclick="loadDeskNote('${n.id}')">
          <span class="desk-note-tk">${n.tk}</span>
          <span class="desk-note-meta">${when} · fit ${n.fit}% · ${packLbl}</span>
          ${n.note ? `<span class="desk-note-txt">${_escAttr(n.note).slice(0, 90)}</span>` : ""}
        </button>
        <button type="button" class="desk-note-del" onclick="deleteDeskNote('${n.id}')" title="Delete">✕</button>
      </div>`;
    }).join("")
    : `<div class="desk-run-muted">No notes yet — snapshot after you stress a name.</div>`;
  return `<div class="lab-panel lab-notes" id="lab-notes">
    <div class="lab-panel-k">DESK NOTES <span class="lab-panel-sub">last 14 · this device</span></div>
    <p class="lab-panel-help">Save Lab state (ticker, pack, fit, price) so you can compare yesterday’s view to today.</p>
    <textarea id="desk-note-text" class="lab-inv-input lab-note-ta" maxlength="280" rows="2" placeholder="Optional: what you believe right now…"></textarea>
    <div class="lab-check-actions" style="margin-top:8px;margin-bottom:12px">
      <button type="button" class="lab-hud-act lab-hud-gold" onclick="saveDeskNote()">Save desk note · ${_labTk}</button>
    </div>
    <div class="desk-note-list">${rows}</div>
  </div>`;
}

function _renderAlertDigest() {
  const active = alerts.filter(a => a.active);
  if (!active.length) return "";
  let h = `<div class="gc" style="padding:14px;border-left:3px solid var(--pu);margin-bottom:10px">
    <div style="font-family:var(--mn);font-size:8px;color:var(--pu);letter-spacing:0.18em;margin-bottom:10px">⬢ PRICE ALERT DIGEST · ${active.length}</div>`;
  active.slice(0, 5).forEach(a => {
    const price = livePx(a.tk);
    const dist = price != null && price > 0 ? Math.abs((a.targetPrice - price) / price * 100) : null;
    const near = dist != null && dist < 2;
    const col = a.dir === "above" ? "var(--gn)" : "var(--rd)";
    const arrow = a.dir === "above" ? "≥" : "≤";
    const nowLbl = price != null ? `now $${price.toFixed(price >= 100 ? 2 : 4)}` : "now — NO SYNC";
    const distLbl = dist == null ? "awaiting live price" : near ? "⚡ Near trigger" : dist.toFixed(1) + "% away";
    h += `<div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-top:1px solid var(--gb);cursor:pointer" onclick="openA('${a.tk}');_setATab('al')">
      <div><span style="font-family:var(--mn);font-weight:800;font-size:12px">${a.tk}</span><span style="font-size:9px;color:var(--t3);margin-left:8px">${nowLbl}</span></div>
      <div style="text-align:right"><span style="font-family:var(--mn);font-size:11px;font-weight:700;color:${col}">${arrow} $${a.targetPrice}</span><div style="font-size:8px;color:${near ? "var(--gd)" : "var(--t3)"}">${distLbl}</div></div></div>`;
  });
  h += `</div>`;
  return h;
}

// ═══════════════════════════════════════════════════════════
// SITE INTELLIGENCE LAYER — always-on brain across the terminal
// ═══════════════════════════════════════════════════════════
let _siteIntel = { surface: "pulse", local: null, ai: null, aiLoad: false, lastAi: 0, expanded: false };
const _SITE_INTEL_TTL = 20 * 60 * 1000;
const _INTEL_PAGE_MAP = { dash: "dash", brief: "brief", gold: "brief", playbook: "brief", mkt: "mkt", anlz: "ticker", sig: "signals", watch: "watchlist", port: "portfolio", news: "news", lab: "dash" };

function _tickerRegimeFit(tk, re) {
  const a = A.find(x => x.tk === tk);
  const chg = liveChg(tk);
  let score = 50;
  if (a?.se?.includes("Bull") && re.score >= 55) score += 18;
  if (a?.se?.includes("Bear") && re.score < 45) score += 12;
  if (a?.cat === "Commodity" && re.overweight.some(x => /Energy|Gold|commodit/i.test(x))) score += 15;
  if (a?.cat === "Crypto" && re.score >= 58) score += 12;
  if (a?.cat === "Crypto" && re.score < 42) score -= 15;
  if (chg != null && chg > 1.5 && re.score >= 55) score += 8;
  if (chg != null && chg < -2) score -= 10;
  if (re.underweight.some(x => /growth|crypto|beta/i.test(x)) && (a?.beta || 0) > 1.5) score -= 12;
  score = Math.max(0, Math.min(100, score));
  const label = score >= 68 ? "Regime-aligned" : score >= 45 ? "Neutral fit" : "Headwind";
  const chgLbl = chg == null ? "no sync" : `${chg >= 0 ? "+" : ""}${chg.toFixed(2)}% today`;
  return { tk, score, label, note: `${label} · ${a?.se || "—"} · ${chgLbl}` };
}

function _computeLocalIntel(surface, extra) {
  extra = extra || {};
  const re = _computeRegimeEngine();
  const fg = calcFearGreed();
  const topSig = SIGS.slice().sort((a, b) => b.cf - a.cf)[0];
  const anomalies = [];
  const actions = [];
  const fit = [];
  let headline = "";
  let insight = "";

  const vixN = livePx("VIX");
  if (vixN != null && vixN > 24) anomalies.push({ t: "warn", m: `VIX ${vixN.toFixed(1)} — volatility elevated` });
  if (vixN != null && vixN < 16 && re.score >= 60) anomalies.push({ t: "pos", m: "Low VIX + risk-on — complacency risk" });

  const wl = getActiveWl().tickers;
  if (wl.length) {
    const red = wl.filter(tk => { const c = liveChg(tk); return c != null && c < -1; }).length;
    const green = wl.filter(tk => { const c = liveChg(tk); return c != null && c > 1; }).length;
    if (red >= Math.ceil(wl.length * 0.6)) anomalies.push({ t: "alert", m: `${red}/${wl.length} watchlist names down >1%` });
    if (green >= Math.ceil(wl.length * 0.6)) anomalies.push({ t: "pos", m: `${green}/${wl.length} watchlist names up >1%` });
  }

  alerts.filter(a => a.active).forEach(a => {
    const price = livePx(a.tk);
    if (price != null && price > 0 && Math.abs((a.targetPrice - price) / price * 100) < 2.5) {
      anomalies.push({ t: "trigger", m: `${a.tk} near alert ${a.dir === "above" ? "≥" : "≤"} $${a.targetPrice}` });
    }
  });

  const highNews = NEWS.filter(n => n.im === "high").slice(0, 2);
  highNews.forEach(n => anomalies.push({ t: "news", m: n.x.slice(0, 72) }));

  if (surface === "pulse" || surface === "dash") {
    headline = `${re.label} · ${re.score}/100`;
    insight = `${re.narrative} Fear/Greed ${fg.label} (${fg.score != null ? fg.score : "—"}). Lead signal: ${topSig?.a} (${topSig?.cf}% conviction).`;
    if (re.score >= 58) actions.push({ label: "Sector rotation", type: "page", value: "sectors" });
    actions.push({ label: "Dispatch Brief", type: "page", value: "brief" });
    if (wl.length) actions.push({ label: "Scan watchlist", type: "scan", value: "" });
    if (_brief?.headline) insight = `Brief: ${_brief.headline}. ` + insight;
  } else if (surface === "ticker") {
    const tk = extra.tk || selTk;
    const a = A.find(x => x.tk === tk);
    if (a) {
      const rs = _tickerRelStrength(tk);
      const px = fp(tk);
      const f = _tickerRegimeFit(tk, re);
      fit.push(f);
      headline = `${tk} — ${f.label}`;
      const dayLbl = liveChg(tk) != null ? `${Number(px.c) >= 0 ? "+" : ""}${px.c}% today` : "no sync";
      const rsLbl = rs.rel == null ? rs.label : `${rs.label} SPY by ${rs.rel >= 0 ? "+" : ""}${rs.rel.toFixed(2)}%`;
      insight = `${a.nm}: ${a.se} · score ${a.sc}/100 · ${dayLbl} · ${rsLbl}. ${a.th?.slice(0, 140) || ""}`;
      actions.push({ label: `Lens on ${tk}`, type: "lens", value: tk });
      if (comRes) {
        const synth = _getSynthesis(comRes);
        if (synth) insight += ` Lens verdict: ${synth.verdict} (${synth.confidence || "—"}%).`;
      }
    }
  } else if (surface === "watchlist") {
    headline = `Watchlist · ${re.label}`;
    wl.forEach(tk => fit.push(_tickerRegimeFit(tk, re)));
    fit.sort((a, b) => b.score - a.score);
    const best = fit[0], worst = fit[fit.length - 1];
    insight = `${wl.length} names tracked. Regime favours ${re.overweight.slice(0, 2).join(", ")}. Top fit: ${best?.tk} (${best?.score}). Weakest: ${worst?.tk} (${worst?.score}).`;
    actions.push({ label: "Run scan", type: "scan", value: "" });
    actions.push({ label: "Compare", type: "action", value: "compare" });
  } else if (surface === "portfolio") {
    headline = `Portfolio · ${re.label}`;
    let dayPnl = 0, betaWt = 0, total = 0, liveTotal = 0, liveN = 0;
    portfolio.forEach(pos => {
      const m = _portMark(pos);
      const val = m.value;
      total += val;
      if (m.live) {
        liveN++;
        liveTotal += val;
        // Day P&L from current value: Δ = V · c/(100+c), not V·c/100
        if (m.chg != null && isFinite(m.chg) && m.chg > -99.9) {
          dayPnl += val * (m.chg / (100 + m.chg));
        }
      }
      fit.push(_tickerRegimeFit(pos.tk, re));
      const a = A.find(x => x.tk === pos.tk);
      if (m.live) betaWt += val * _deskBeta(a || pos.tk, 1);
    });
    const portBeta = liveTotal ? (betaWt / liveTotal).toFixed(2) : "—";
    const dayBit = liveN
      ? `est. day ${dayPnl >= 0 ? "+" : ""}$${Math.abs(dayPnl).toFixed(0)} (${liveTotal ? (dayPnl / liveTotal * 100).toFixed(2) : "0"}%)`
      : "day P&L NO SYNC";
    insight = `${portfolio.length} positions · ~$${total.toFixed(0)}${liveN < portfolio.length ? ` (${liveN} live)` : ""} · ${dayBit} · beta ${portBeta}. ${re.score < 45 ? "Elevated beta hurts in risk-off." : re.score >= 60 ? "Beta exposure rewarded in risk-on." : "Mixed regime — balance beta."}`;
    actions.push({ label: "Portfolio scan", type: "action", value: "portscan" });
    if (portfolio[0]) actions.push({ label: `Open ${portfolio[0].tk}`, type: "ticker", value: portfolio[0].tk });
  } else if (surface === "signals") {
    headline = `Signal stack · ${SIGS.length} active`;
    const top3 = SIGS.slice().sort((a, b) => b.cf - a.cf).slice(0, 3);
    insight = top3.map(s => `${s.a} (${s.cf}%): ${s.x.slice(0, 80)}`).join(" · ");
    actions.push({ label: "View regime", type: "page", value: "sectors" });
  } else if (surface === "mkt") {
    headline = `Markets · ${re.label}`;
    const leaders = [...A]
      .map(a => ({ a, c: liveChg(a.tk) }))
      .filter(x => x.c != null)
      .sort((x, y) => y.c - x.c)
      .slice(0, 3)
      .map(x => `${x.a.tk} ${x.c >= 0 ? "+" : ""}${x.c.toFixed(2)}%`);
    insight = `${leaders.length ? "Leaders: " + leaders.join(", ") + ". " : "Awaiting live tape. "}Regime overweight: ${re.overweight.slice(0, 3).join(", ")}.`;
    actions.push({ label: "Heatmap", type: "page", value: "heat" });
  } else if (surface === "sectors") {
    const sig = _sectorRotationSignal();
    headline = `Sector rotation · ${sig.label}`;
    insight = sig.desc;
    if (_sectorIsLoaded()) {
      const ranked = SECTORS_DEF
        .map(s => ({ s, pct: _sectorPct(s.etf, "1d") }))
        .filter(x => x.pct != null && isFinite(x.pct))
        .sort((a, b) => b.pct - a.pct);
      const best = ranked[0]?.s, worst = ranked.length ? ranked[ranked.length - 1].s : null;
      const bp = ranked[0]?.pct, wp = ranked.length ? ranked[ranked.length - 1].pct : null;
      insight += ` Today: ${best?.name || "—"} ${bp != null ? (bp >= 0 ? "+" : "") + bp.toFixed(2) + "%" : "—"} leads; ${worst?.name || "—"} lags.`;
      ranked.slice(0, 4).forEach(({ s }) => {
        const mom = _sectorMomentumScore(s.etf);
        if (mom == null) return;
        fit.push({ tk: s.etf, score: Math.max(0, Math.min(100, Math.round(50 + mom * 10))), label: mom >= 0 ? "RS positive" : "RS negative", note: `${s.name} · avg vs SPY ${mom >= 0 ? "+" : ""}${mom.toFixed(2)}%` });
      });
      if (vixN != null && vixN > 22 && sig.label === "Risk-On Rotation") {
        anomalies.push({ t: "warn", m: "Risk-on sector rotation with elevated VIX — fragile leadership" });
      }
    } else {
      insight += " Tap Refresh to load live sector ETF data.";
      actions.push({ label: "Load sectors", type: "action", value: "fetchsectors" });
    }
    actions.push({ label: "Dispatch Brief", type: "page", value: "brief" });
    actions.push({ label: "Signals", type: "page", value: "sig" });
  } else if (surface === "brief") {
    headline = _brief?.headline || `Dispatch Brief · ${re.label}`;
    insight = _brief?.summary || "Generate today's house view — regime, overweight sectors, and actionable playbook.";
    if (_brief?.houseView) insight = `House view: ${_brief.houseView}. ${(_brief.summary || "").slice(0, 160)}`;
    if (_brief?.overweight?.length) insight += ` Overweight: ${_brief.overweight.slice(0, 3).join(", ")}.`;
    actions.push({ label: "Refresh brief", type: "page", value: "brief" });
    actions.push({ label: "Sector rotation", type: "page", value: "sectors" });
    actions.push({ label: "Run lens", type: "lens", value: getActiveWl().tickers[0] || "NVDA" });
  } else if (surface === "news") {
    const high = NEWS.filter(n => n.im === "high").length;
    const latest = NEWS[0];
    headline = `Newsroom · ${NEWS.length} headlines`;
    insight = `${high ? high + " high-impact · " : ""}${newsLastFetch ? "Updated " + Math.round((Date.now() - newsLastFetch.getTime()) / 60000) + "m ago. " : ""}${latest ? latest.x.slice(0, 100) : "Fetching feeds…"}`;
    if (newsError) anomalies.push({ t: "warn", m: newsError });
    actions.push({ label: "Refresh feeds", type: "action", value: "refreshnews" });
    actions.push({ label: "Signals", type: "page", value: "sig" });
  } else if (surface === "heat") {
    const ranked = [...A].map(a => ({ a, c: liveChg(a.tk) })).filter(x => x.c != null).sort((x, y) => y.c - x.c);
    const leaders = ranked.slice(0, 3);
    const laggards = ranked.slice(-2).reverse();
    headline = `Heatmap · ${re.label}`;
    insight = ranked.length
      ? `Leaders: ${leaders.map(x => x.a.tk + " " + (x.c >= 0 ? "+" : "") + x.c.toFixed(2) + "%").join(", ")}. Laggards: ${laggards.map(x => x.a.tk + " " + x.c.toFixed(2) + "%").join(", ")}.`
      : "Awaiting live tape for heatmap leaders.";
    actions.push({ label: "Markets", type: "page", value: "mkt" });
    actions.push({ label: "Sector rotation", type: "page", value: "sectors" });
  } else if (surface === "crypto") {
    headline = _cryptoMktData ? `Crypto · ${_cryptoMktData.length} assets` : "Crypto Markets";
    if (_cryptoDominance) {
      const tmc = _cryptoDominance.totalMcap ? `$${(_cryptoDominance.totalMcap / 1e12).toFixed(2)}T` : "—";
      insight = `BTC dominance ${_cryptoDominance.btc}% · ETH ${_cryptoDominance.eth}% · Total mcap ${tmc}.`;
    }
    else insight = "Load live CoinGecko rankings and dominance.";
    if (_cryptoMktData?.length) {
      const top = _cryptoMktData.slice(0, 3);
      insight += ` Top: ${top.map(c => c.symbol?.toUpperCase() + " " + (c.price_change_percentage_24h >= 0 ? "+" : "") + (c.price_change_percentage_24h || 0).toFixed(1) + "%").join(", ")}.`;
    }
    if (!_cryptoMktData && !_cryptoMktLoading) actions.push({ label: "Load crypto", type: "action", value: "fetchcrypto" });
    actions.push({ label: "Heatmap", type: "page", value: "heat" });
  } else if (surface === "scr") {
    headline = `Screener · ${_scrResults.length || "no"} results`;
    insight = _scrError || (_scrResults.length ? `${_scrMode} mode · ${_scrResults.length} tickers matched. Sort by ${_scrSort.col}.` : "Run a preset screen or build a custom filter.");
    if (_scrLoading) insight = "Scanning markets…";
    actions.push({ label: "Run screen", type: "action", value: "runscr" });
    actions.push({ label: "Markets", type: "page", value: "mkt" });
  } else if (surface === "learn") {
    headline = `Learn · ${_learnTab} frameworks`;
    insight = _learnSub ? `Reading: ${_learnSub}.` : `${(LEARN_MODULES[_learnTab] || []).length} modules on professional analysis methodologies.`;
    actions.push({ label: "Dispatch Brief", type: "page", value: "brief" });
    actions.push({ label: "Lens Engine", type: "lens", value: selTk || "NVDA" });
  } else if (surface === "intel") {
    headline = _intelResult ? `Doc intel · ${_intelResult.sentiment || "Analysed"}` : "Document Intelligence";
    insight = _intelResult ? (_intelResult.summary || "Document analysed.") : "Paste earnings calls, 10-Ks, or research notes for AI signal extraction.";
    if (_intelLoading) insight = "Analysing document…";
    actions.push({ label: "Expert chat", type: "chat", value: "Summarise this document's trading implications" });
  } else if (surface === "research") {
    headline = selReport ? `Research · ${selReport}` : "Research Desk";
    insight = selReport ? "Flagship scenario analysis — adjust probability blender and read sector dispersion." : `${REPORTS.length} published reports. Start with the SPX 2026 outlook.`;
    actions.push({ label: "Open SPX 2026", type: "action", value: "openspx" });
    actions.push({ label: "Sector rotation", type: "page", value: "sectors" });
  }

  const priority = anomalies.some(a => a.t === "trigger" || a.t === "alert") ? "high" : "normal";
  return { headline, insight, anomalies, actions, fit, regime: re.label, score: re.score, priority, local: true };
}

function _siteIntelCacheKey(surface, tk) {
  return `td_si_${surface}_${tk || ""}_${new Date().toISOString().split("T")[0]}`;
}

function _siteIntelContext(surface, tk) {
  const parts = [_buildChatContext()];
  if (surface === "ticker" && tk) parts.push(`Focus ticker: ${tk}`);
  if (surface === "watchlist") parts.push(`Watchlist fit scores: ${getActiveWl().tickers.map(t => _tickerRegimeFit(t, _computeRegimeEngine()).score + " " + t).join(", ")}`);
  if (surface === "sectors" && _sectorIsLoaded()) {
    const sig = _sectorRotationSignal();
    const rows = [...SECTORS_DEF].map(s => `${s.etf} ${s.name}: 1d ${_sectorPct(s.etf, "1d") ?? "—"}% 1m ${_sectorPct(s.etf, "month") ?? "—"}% vs SPY 1m ${_sectorRelSpy(s.etf, "month") ?? "—"}%`).join("\n");
    parts.push(`Sector rotation: ${sig.label}. ${sig.desc}\n${rows}`);
  }
  if (surface === "brief" && _brief) parts.push(`Brief: ${_brief.headline || ""} · ${_brief.houseView || ""} · ${_brief.summary || ""}`);
  if (surface === "news") parts.push(`News (${NEWS.length}): ${NEWS.slice(0, 5).map(n => n.x).join(" | ")}`);
  if (surface === "crypto" && _cryptoMktData) parts.push(`Crypto top: ${_cryptoMktData.slice(0, 8).map(c => c.symbol + " " + (c.price_change_percentage_24h || 0).toFixed(1) + "%").join(", ")}`);
  if (surface === "scr" && _scrResults.length) parts.push(`Screener (${_scrMode}): ${_scrResults.slice(0, 10).map(s => s.symbol).join(", ")}`);
  return parts.join("\n");
}

async function _fetchSiteIntelAI(surface, extra) {
  if (!_isPremium() || _siteIntel.aiLoad) return;
  extra = extra || {};
  const tk = extra.tk || "";
  const key = _siteIntelCacheKey(surface, tk);
  try {
    const cached = sessionStorage.getItem(key);
    if (cached) {
      const c = JSON.parse(cached);
      if (c.ts && Date.now() - c.ts < _SITE_INTEL_TTL) {
        _siteIntel.ai = c.intel;
        _siteIntel.surface = surface;
        _siteIntel.lastAi = c.ts;
        _paintSiteIntelBar();
        return;
      }
    }
  } catch (e) { /* skip */ }

  _siteIntel.aiLoad = true;
  _intelBarSig = ""; // force paint spinner
  _paintSiteIntelBar();
  try {
    const res = await fetch("/api/intelligence", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ surface, ticker: tk, context: _siteIntelContext(surface, tk) })
    });
    // Always clear aiLoad — early 401 return used to leave spinner stuck forever
    if (res.status === 401) return;
    if (!res.ok) throw new Error("intel fail");
    const data = await res.json();
    if (data.intel) {
      _siteIntel.ai = data.intel;
      _siteIntel.surface = surface;
      _siteIntel.lastAi = Date.now();
      sessionStorage.setItem(key, JSON.stringify({ ts: _siteIntel.lastAi, intel: data.intel }));
    }
  } catch (e) { /* local intel still works */ }
  finally {
    _siteIntel.aiLoad = false;
    _intelBarSig = "";
    _paintSiteIntelBar();
  }
  const refreshMap = { pulse: ["dash"], dash: ["dash"], brief: ["brief"], ticker: ["anlz"], watchlist: ["watch"], portfolio: ["port"], signals: ["sig"], mkt: ["mkt"], sectors: ["sectors"], news: ["news"], heat: ["heat"], crypto: ["crypto"], scr: ["scr"], learn: ["learn"], intel: ["intel"], research: ["research"] };
  if ((refreshMap[surface] || []).includes(pg)) {
    // Surgical refresh — full renderMain kills focus and flickers Android
    if (pg === "news" && typeof _paintNewsListOnly === "function") _paintNewsListOnly(true);
    else if (pg === "anlz" && aTab === "nw") { /* keep analysis news panel */ }
    else if (MOBILE()) { _patchLiveDataIfNeeded(); _patchCuratedPrices(); }
    else renderMain();
  }
  if (IS_DESKTOP()) {
    if (termSelTk || _dynTk) { if (typeof _patchP2LiveHeader === "function") _patchP2LiveHeader(); renderP1(); renderP3(); renderP4(); }
    else renderTerminalPanels();
  }
}

function _mergeIntel(surface, extra) {
  const local = _computeLocalIntel(surface, extra);
  const ai = (_siteIntel.ai && _siteIntel.surface === surface) ? _siteIntel.ai : null;
  if (!ai) return local;
  return {
    headline: ai.headline || local.headline,
    insight: ai.insight || local.insight,
    anomalies: [...new Set([...(ai.anomalies || []), ...local.anomalies.map(a => a.m)])].slice(0, 5).map(m => typeof m === "string" ? { t: "ai", m } : m),
    actions: (ai.actions?.length ? ai.actions : local.actions),
    fit: (ai.fit?.length ? ai.fit : local.fit),
    regime: local.regime,
    score: local.score,
    priority: ai.priority === "high" || local.priority === "high" ? "high" : "normal",
    ai: true,
    usedSearch: ai.usedSearch,
    local: true
  };
}

function _siteIntelAction(act) {
  if (!act) return;
  const t = act.type, v = act.value || "";
  if (t === "ticker" && v) { openA(v); return; }
  if (t === "lens" && v) { openA(v); setTimeout(() => runCommittee(v), 400); return; }
  if (t === "page" || t === "brief") { nav(v || "brief"); if (v === "brief") loadDispatchBrief(true); return; }
  if (t === "scan") { nav("watch"); setTimeout(() => runWatchlistScan(), 300); return; }
  if (t === "action" && v === "compare") { compareWatchlist(); return; }
  if (t === "action" && v === "portscan") { runPortfolioScan(); return; }
  if (t === "action" && v === "fetchsectors") { fetchSectorData(); return; }
  if (t === "action" && v === "refreshnews") { fetchLiveNews(); return; }
  if (t === "action" && v === "fetchcrypto") { fetchCryptoMarket(); return; }
  if (t === "action" && v === "runscr") { runScreener(_scrMode); return; }
  if (t === "action" && v === "openspx") { nav("research"); openReport("spx2026"); return; }
  if (t === "chat") { toggleChat(); const inp = document.getElementById("chatInp"); if (inp && v) { inp.value = v; sendChatMessage(); } return; }
  _chatRunAction(act);
}

let _siteActMap = {};
function _siteIntelActionId(id) { _siteIntelAction(_siteActMap[id]); }

function _renderSiteIntelCard(surface, extra) {
  extra = extra || {};
  const intel = _mergeIntel(surface, extra);
  const col = intel.priority === "high" ? "var(--rd)" : intel.ai ? "var(--bl)" : "var(--gd)";
  const badge = intel.ai ? (_siteIntel.aiLoad ? "◆ SYNTHESISING…" : "◆ SITE INTELLIGENCE") : "◆ LIVE PULSE";
  let acts = "";
  (intel.actions || []).slice(0, 3).forEach((a, i) => {
    const id = `si${surface}${i}`;
    _siteActMap[id] = a;
    acts += `<button type="button" class="si-act" onclick="_siteIntelActionId('${id}')">${(a.label || "").replace(/</g, "&lt;")}</button>`;
  });
  let anom = "";
  (intel.anomalies || []).slice(0, 3).forEach(a => {
    const m = typeof a === "string" ? a : a.m;
    const tc = (typeof a === "object" && a.t === "trigger") ? "var(--gd)" : (typeof a === "object" && a.t === "alert") ? "var(--rd)" : "var(--t2)";
    anom += `<div class="si-anom" style="color:${tc}">${String(m).replace(/</g, "&lt;")}</div>`;
  });
  let fit = "";
  if ((intel.fit || []).length && (surface === "watchlist" || surface === "portfolio" || surface === "sectors")) {
    fit = `<div class="si-fit">${intel.fit.slice(0, 6).map(f => {
      const c = f.score >= 68 ? "var(--gn)" : f.score >= 45 ? "var(--gd)" : "var(--rd)";
      return `<span class="si-fit-chip" style="border-color:${c}40;color:${c}">${f.tk} ${f.score}</span>`;
    }).join("")}</div>`;
  }
  return `<div class="gc si-card" style="border-left:3px solid ${col};margin-bottom:10px" id="siteIntelCard">
    <div class="si-hdr">
      <span class="si-badge" style="color:${col}">${badge}</span>
      ${intel.usedSearch ? '<span class="si-web">↗ web</span>' : ""}
      <button type="button" class="si-ask" onclick="toggleChat()" title="Ask Dispatch Expert">Ask →</button>
    </div>
    <div class="si-headline">${(intel.headline || "").replace(/</g, "&lt;")}</div>
    <div class="si-insight">${(intel.insight || "").replace(/</g, "&lt;")}</div>
    ${anom ? `<div class="si-anoms">${anom}</div>` : ""}
    ${fit}
    ${acts ? `<div class="si-acts">${acts}</div>` : ""}
  </div>`;
}

let _intelBarSig = "";
function _paintSiteIntelBar() {
  const el = document.getElementById("siteIntelBar");
  if (!el) return;
  const intel = _mergeIntel(_siteIntel.surface || "pulse", { tk: selTk });
  const col = intel.priority === "high" ? "var(--rd)" : "var(--gd)";
  const spin = _siteIntel.aiLoad ? '<span class="si-spin"></span>' : '<span class="si-pulse-dot"></span>';
  const anom = (intel.anomalies || [])[0];
  const anomTxt = anom ? (typeof anom === "string" ? anom : anom.m) : "";
  const mob = !IS_DESKTOP();
  const headRaw = (intel.headline || reLabel()).replace(/</g, "&lt;");
  const anomRaw = anomTxt ? String(anomTxt).replace(/</g, "&lt;") : "";
  const scrollTxt = anomRaw && !mob ? `${headRaw} · ${anomRaw}` : headRaw;
  // Signature-gate: 30s timer was rewriting intel bar + neural strip → Android flicker
  const sig = [mob?"m":"d", intel.priority, !!intel.ai, !!_siteIntel.aiLoad, !!_siteIntel.expanded, headRaw, anomRaw, pg].join("|");
  if (sig === _intelBarSig && el.dataset.sig === sig) return;
  _intelBarSig = sig;
  el.dataset.sig = sig;
  const chunk = `${scrollTxt} · `;
  const scrollBlock = `<div class="si-bar-scroll-wrap"><div class="si-bar-scroll-track"><span class="si-bar-chunk">${chunk}</span><span class="si-bar-chunk">${chunk}</span></div></div>`;
  el.innerHTML = `<div class="si-bar-inner" onclick="_toggleSiteIntelExpand()">
    ${spin}
    <span class="si-bar-label" style="color:${col}">INTEL</span>
    ${scrollBlock}
    <span class="si-bar-more">${_siteIntel.expanded ? "▲" : "▼"}</span>
  </div>
  ${_siteIntel.expanded ? `<div class="si-bar-expand">
    <div class="si-bar-insight">${(intel.insight || "").replace(/</g, "&lt;")}</div>
    <div class="si-bar-acts">${(intel.actions || []).slice(0, 2).map((a, i) => { const id = "sib" + i; _siteActMap[id] = a; return `<button type="button" class="si-act-sm" onclick="event.stopPropagation();_siteIntelActionId('${id}')">${(a.label || "").replace(/</g, "&lt;")}</button>`; }).join("")}<button type="button" class="si-act-sm" onclick="event.stopPropagation();toggleChat()">Expert →</button></div>
  </div>` : ""}`;
  el.classList.toggle("si-high", intel.priority === "high");
  el.classList.toggle("si-ai", !!intel.ai);
  el.classList.toggle("si-mob", mob);
  el.classList.toggle("si-desk", !mob);
  if (!mob) requestAnimationFrame(_syncDeskChrome);
  requestAnimationFrame(_syncIntelScroll);
  // Only replace neural strip when content actually changed (sig already new)
  if (pg === "dash" || pg === "brief") {
    const strip = document.querySelector(".neural-strip");
    if (strip) strip.outerHTML = _renderNeuralSessionStrip();
  }
}

function reLabel() { return _computeRegimeEngine().label; }

function _syncIntelScroll() {
  const wrap = document.querySelector(".si-bar-scroll-wrap");
  const track = wrap?.querySelector(".si-bar-scroll-track");
  if (!wrap || !track) return;
  const half = track.scrollWidth / 2;
  const needs = half > wrap.clientWidth + 8;
  wrap.classList.toggle("si-scroll-on", needs);
  if (needs) track.style.animationDuration = Math.max(16, Math.min(55, half / 28)) + "s";
}

function _toggleSiteIntelExpand() {
  _siteIntel.expanded = !_siteIntel.expanded;
  _paintSiteIntelBar();
  _syncDeskChrome();
}

function _onPageIntel(surface, extra) {
  extra = extra || {};
  _siteIntel.surface = surface;
  _siteIntel.local = _computeLocalIntel(surface, extra);
  _paintSiteIntelBar();
  _fetchSiteIntelAI(surface, extra);
}

function _initSiteIntelligence() {
  _siteIntel.surface = "pulse";
  _paintSiteIntelBar();
  _onPageIntel("pulse");
  setInterval(() => {
    _siteIntel.local = _computeLocalIntel(_siteIntel.surface || "pulse", { tk: selTk });
    _paintSiteIntelBar();
    _checkProactiveIntel();
  }, 30000);
  setInterval(() => {
    if (_isPremium()) _fetchSiteIntelAI(_siteIntel.surface || "pulse", { tk: selTk });
  }, _SITE_INTEL_TTL);
  setTimeout(_checkProactiveIntel, 6000);
}

// ═══════════════════════════════════════════════════════════
// NEURAL TERMINAL — first-of-kind UX layer (mobile + web)
// ═══════════════════════════════════════════════════════════
let _chromeFocus = sessionStorage.getItem("td_chrome_focus") === "1";

function _regimeRingSvg(score, col) {
  const circ = 2 * Math.PI * 9;
  const off = circ * (1 - Math.min(100, Math.max(0, score)) / 100);
  return `<svg class="htec-regime-ring" width="20" height="20" viewBox="0 0 22 22" aria-hidden="true"><circle cx="11" cy="11" r="9" fill="none" stroke="rgba(255,255,255,0.07)" stroke-width="2"/><circle cx="11" cy="11" r="9" fill="none" stroke="${col}" stroke-width="2" stroke-dasharray="${circ.toFixed(2)}" stroke-dashoffset="${off.toFixed(2)}" stroke-linecap="round" transform="rotate(-90 11 11)"/></svg>`;
}

function _renderRegimeRing(re) {
  const circ = 2 * Math.PI * 42;
  const off = circ * (1 - Math.min(100, Math.max(0, re.score)) / 100);
  return `<svg class="lab-regime-ring" width="88" height="88" viewBox="0 0 96 96"><circle cx="48" cy="48" r="42" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="6"/><circle cx="48" cy="48" r="42" fill="none" stroke="${re.col}" stroke-width="6" stroke-dasharray="${circ.toFixed(1)}" stroke-dashoffset="${off.toFixed(1)}" stroke-linecap="round" transform="rotate(-90 48 48)"/><text x="48" y="52" text-anchor="middle" font-family="JetBrains Mono" font-size="15" font-weight="900" fill="${re.col}">${re.score}</text></svg>`;
}

function toggleChromeFocus() {
  _chromeFocus = !_chromeFocus;
  sessionStorage.setItem("td_chrome_focus", _chromeFocus ? "1" : "0");
  document.body.classList.toggle("chrome-focus", _chromeFocus);
  _syncDeskChrome();
  showToast(_chromeFocus ? "Focus mode — workspace maximized" : "Full terminal chrome restored", "var(--bl)");
}

function _applyChromeFocus() {
  document.body.classList.toggle("chrome-focus", _chromeFocus);
}

function _sectorHeatSummary() {
  const sig = _sectorRotationSignal();
  let lead = "—", trail = "—", leadPct = null, trailPct = null;
  if (_sectorIsLoaded()) {
    // Only rank sectors with a real day % — never treat missing as 0
    const ranked = SECTORS_DEF
      .map(s => ({ etf: s.etf, pct: _sectorPct(s.etf, "1d") }))
      .filter(x => x.pct != null && isFinite(x.pct))
      .sort((a, b) => b.pct - a.pct);
    if (ranked[0]) { lead = ranked[0].etf; leadPct = ranked[0].pct; }
    if (ranked.length) { trail = ranked[ranked.length - 1].etf; trailPct = ranked[ranked.length - 1].pct; }
  }
  const shortSig = sig.label === "Risk-On Rotation" ? "RISK+" : sig.label === "Defensive Rotation" ? "DEF" : sig.label === "Mixed / Neutral" ? "MIX" : "…";
  return { sig, lead, trail, leadPct, trailPct, shortSig };
}

function _renderNeuralSessionStrip() {
  const re = _computeRegimeEngine();
  const topSig = SIGS.slice().sort((a, b) => b.cf - a.cf)[0];
  const wl = getActiveWl().tickers.length;
  const port = portfolio.length;
  const aiOn = _isPremium() && (_siteIntel.ai || _siteIntel.aiLoad);
  const heat = _sectorHeatSummary();
  const leadCol = heat.leadPct == null ? "var(--t3)" : heat.leadPct >= 0 ? "var(--gn)" : "var(--rd)";
  const trailCol = heat.trailPct == null ? "var(--t3)" : heat.trailPct >= 0 ? "var(--gn)" : "var(--rd)";
  const leadTxt = heat.leadPct != null ? `${heat.lead} ${heat.leadPct >= 0 ? "+" : ""}${heat.leadPct.toFixed(1)}%` : heat.shortSig;
  const trailTxt = heat.trailPct != null ? `${heat.trail} ${heat.trailPct >= 0 ? "+" : ""}${heat.trailPct.toFixed(1)}%` : "—";
  return `<div class="neural-strip">
    <div class="ns-cell ns-regime">${_regimeRingSvg(re.score, re.col)}<div><span class="ns-lbl">REGIME</span><span class="ns-val" style="color:${re.col}">${IS_DESKTOP() ? re.label : _mobShortRegime(re.label)} · ${re.score}</span></div></div>
    <div class="ns-cell ns-sector gc-a" onclick="nav('sectors')" title="${heat.sig.desc || heat.sig.label}"><span class="ns-lbl">ROTATION</span><span class="ns-val" style="color:${heat.sig.col}">${heat.shortSig}</span></div>
    <div class="ns-cell ns-sector-lead gc-a" onclick="nav('sectors')"><span class="ns-lbl">LEAD</span><span class="ns-val" style="color:${leadCol}">${leadTxt}</span></div>
    <div class="ns-cell ns-sector-trail gc-a" onclick="nav('sectors')"><span class="ns-lbl">LAG</span><span class="ns-val" style="color:${trailCol}">${trailTxt}</span></div>
    <div class="ns-cell"><span class="ns-lbl">LIVE</span><span class="ns-val ns-live">${liveSymbols.size}</span></div>
    <div class="ns-cell"><span class="ns-lbl">VIX</span><span class="ns-val">${re.vix}</span></div>
    <div class="ns-cell" title="${_escAttr(topSig ? `${topSig.a} · ${topSig.cf}% · ${topSig.x || ""}` : "No signal")}"><span class="ns-lbl">SIG</span><span class="ns-val">${(topSig?.a || "—").slice(0, 12)}</span></div>
    <div class="ns-cell"><span class="ns-lbl">WL</span><span class="ns-val">${wl}</span></div>
    <div class="ns-cell ns-neural ${aiOn ? "ns-neural-on" : ""}"><span class="ns-lbl">NEURAL</span><span class="ns-val">${_siteIntel.aiLoad ? "SYNC" : aiOn ? "LINK" : _isPremium() ? "READY" : "LOCK"}</span></div>
  </div>`;
}

let _wlGlanceCollapsed = sessionStorage.getItem("td_wl_glance_coll") === "1";

function _paintWlGlance() {
  const wl = getActiveWl().tickers;
  let bar = document.getElementById("wlGlanceBar");
  if (!wl.length) {
    if (bar) bar.classList.add("hide");
    _syncDeskChrome();
    return;
  }
  if (!bar) {
    bar = document.createElement("div");
    bar.id = "wlGlanceBar";
    const anchor = document.getElementById("siteIntelBar");
    if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(bar, anchor.nextSibling);
    else document.getElementById("app")?.appendChild(bar);
  }
  if (_wlGlanceCollapsed) {
    bar.className = "wl-glance wl-glance-collapsed";
    bar.innerHTML = `<button type="button" class="wl-glance-coll-btn" onclick="_wlGlanceCollapsed=false;sessionStorage.setItem('td_wl_glance_coll','0');_paintWlGlance()">◎ WATCHLIST · ${wl.length} tickers ▴</button>`;
    bar.classList.remove("hide");
    _syncDeskChrome();
    return;
  }
  const chips = wl.map(tk => {
    const d = fp(tk);
    const na = d.status === "unavailable";
    const ch = liveChg(tk);
    const col = na || ch == null ? "var(--t3)" : ch > 0 ? "var(--gn)" : ch < 0 ? "var(--rd)" : "var(--t3)";
    const sign = ch != null && ch >= 0 ? "+" : "";
    const live = liveSymbols.has(tk) ? '<span class="wl-g-live"></span>' : "";
    const chgLbl = na || ch == null ? "—" : `${sign}${d.c}%`;
    return `<button type="button" class="wl-glance-chip" onclick="openA('${tk}')">${live}<span class="wl-g-tk">${tk}</span><span class="wl-g-p">${na?"—":d.p}</span><span class="wl-g-c" style="color:${col}">${chgLbl}</span></button>`;
  }).join("");
  bar.className = "wl-glance";
  bar.innerHTML = `<div class="wl-glance-hdr">
      <span class="wl-glance-lbl">◎ WATCHLIST GLANCE</span>
      <button type="button" class="wl-glance-mini" onclick="runWatchlistScan()" title="Scan watchlist">◎</button>
      <button type="button" class="wl-glance-mini" onclick="_wlGlanceCollapsed=true;sessionStorage.setItem('td_wl_glance_coll','1');_paintWlGlance()" title="Collapse">▾</button>
      <button type="button" class="wl-glance-all" onclick="nav('watch')">ALL →</button>
    </div>
    <div class="wl-glance-track">${chips}</div>`;
  bar.classList.remove("hide");
  _syncDeskChrome();
}

let _briefSpeaking = false;

function _briefSpeechText() {
  const b = _brief;
  if (!b) return "";
  return [
    `Dispatch Brief for ${b.date || "today"}.`,
    b.headline || "",
    `House view: ${b.houseView || "Neutral"}.`,
    b.summary || "",
    b.overweight?.length ? `Overweight: ${b.overweight.join(", ")}.` : "",
    b.underweight?.length ? `Underweight: ${b.underweight.join(", ")}.` : "",
    b.catalysts?.length ? `Catalysts: ${b.catalysts.join(". ")}.` : "",
    b.risks?.length ? `Risks: ${b.risks.join(". ")}.` : "",
    b.actionItems?.length ? `Research agenda: ${b.actionItems.join(". ")}.` : "",
    "Research only. Not investment advice.",
  ].filter(Boolean).join(" ").slice(0, 4000);
}

function _renderBriefPlayBtn(compact) {
  if (!_brief || _briefLoad) return "";
  const lbl = _briefSpeaking ? "■ Stop" : "▶ Listen";
  const col = _briefSpeaking ? "var(--rd)" : "var(--cy)";
  return `<button type="button" class="brief-play-btn${compact ? " brief-play-sm" : ""}" onclick="toggleBriefPlayback()" style="border-color:${col}55;color:${col}">${lbl}</button>`;
}

function toggleBriefPlayback() {
  if (!window.speechSynthesis) {
    showToast("Voice playback not supported in this browser", "var(--rd)");
    return;
  }
  if (_briefSpeaking || window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel();
    _briefSpeaking = false;
    _hideBriefPlayer();
    _refreshBriefSurfaces();
    return;
  }
  const text = _briefSpeechText();
  if (!text) { showToast("Generate a brief first", "var(--gd)"); return; }
  const u = new SpeechSynthesisUtterance(text);
  u.rate = IS_DESKTOP() ? 0.92 : 1;
  u.pitch = 1;
  u.onend = u.onerror = () => {
    _briefSpeaking = false;
    _hideBriefPlayer();
    _refreshBriefSurfaces();
  };
  _briefSpeaking = true;
  _showBriefPlayer();
  _refreshBriefSurfaces();
  window.speechSynthesis.speak(u);
}

function _showBriefPlayer() {
  let p = document.getElementById("briefPlayer");
  if (!p) {
    p = document.createElement("div");
    p.id = "briefPlayer";
    document.body.appendChild(p);
  }
  p.className = "brief-player";
  p.innerHTML = `<div class="brief-player-inner">
    <div class="brief-player-waves"><span></span><span></span><span></span><span></span><span></span></div>
    <div class="brief-player-txt"><span class="brief-player-lbl">DISPATCH BRIEF</span><span class="brief-player-sub">${(_brief?.headline || "Playing…").slice(0, 48)}</span></div>
    <button type="button" class="brief-player-stop" onclick="toggleBriefPlayback()">■ Stop</button>
  </div>`;
}

function _hideBriefPlayer() {
  document.getElementById("briefPlayer")?.classList.add("hide");
}

const _DOCK_BY_PAGE = {
  dash: [
    { l: "◆ Brief", a: "nav('brief');loadDispatchBrief(true);_toggleSmartDock()" },
    { l: "⬡ Expert", a: "toggleChat();_toggleSmartDock()" },
    { l: "⟳ Morning", a: "runMorningRoutine();_toggleSmartDock()" },
    { l: "▦ Heat", a: "nav('heat');_toggleSmartDock()" },
  ],
  brief: [
    { l: "▶ Listen", a: "toggleBriefPlayback();_toggleSmartDock()" },
    { l: "↻ Refresh", a: "loadDispatchBrief(true);_toggleSmartDock()" },
    { l: "⬡ Expert", a: "toggleChat();_toggleSmartDock()" },
    { l: "◎ Sectors", a: "nav('sectors');_toggleSmartDock()" },
  ],
  mkt: [
    { l: "◆ Regime sort", a: "_mktCuratedSort='smart';renderMain();_toggleSmartDock()" },
    { l: "▦ Heatmap", a: "nav('heat');_toggleSmartDock()" },
    { l: "◎ Screener", a: "nav('scr');_toggleSmartDock()" },
    { l: "⟳ Prices", a: "fetchLivePrices();_toggleSmartDock()" },
  ],
  news: [
    { l: "⟳ News", a: "fetchLiveNews();_toggleSmartDock()" },
    { l: "⚡ Signals", a: "nav('sig');_toggleSmartDock()" },
    { l: "⬡ Expert", a: "toggleChat();_toggleSmartDock()" },
  ],
  sig: [
    { l: "◎ Sectors", a: "nav('sectors');_toggleSmartDock()" },
    { l: "◆ Brief", a: "nav('brief');_toggleSmartDock()" },
    { l: "⬡ Expert", a: "toggleChat();_toggleSmartDock()" },
  ],
  watch: [
    { l: "◎ Scan WL", a: "runWatchlistScan();_toggleSmartDock()" },
    { l: "⬡ Expert", a: "toggleChat();_toggleSmartDock()" },
    { l: "+ Add", a: "openSearch();_toggleSmartDock()" },
    { l: "▾ Glance", a: "_wlGlanceCollapsed=false;sessionStorage.setItem('td_wl_glance_coll','0');_paintWlGlance();_toggleSmartDock()" },
  ],
  port: [
    { l: "◎ Scan", a: "runPortfolioScan();_toggleSmartDock()" },
    { l: "⬡ Expert", a: "toggleChat();_toggleSmartDock()" },
    { l: "▦ Heat", a: "nav('heat');_toggleSmartDock()" },
  ],
  sectors: [
    { l: "↻ Refresh", a: "fetchSectorData();_toggleSmartDock()" },
    { l: "▦ Heat", a: "nav('heat');_toggleSmartDock()" },
    { l: "◆ Brief", a: "nav('brief');_toggleSmartDock()" },
  ],
  anlz: [
    { l: "◎ Lenses", a: "if(selTk)runCommittee(selTk);_toggleSmartDock()" },
    { l: "⬡ Expert", a: "toggleChat();_toggleSmartDock()" },
    { l: "★ Watch", a: "if(selTk)togWatch(selTk);_toggleSmartDock()" },
  ],
  heat: [
    { l: "◎ Sectors", a: "nav('sectors');_toggleSmartDock()" },
    { l: "◆ Markets", a: "nav('mkt');_toggleSmartDock()" },
    { l: "⬡ Expert", a: "toggleChat();_toggleSmartDock()" },
  ],
};

function _updateSmartDock() {
  const menu = document.getElementById("smartDockMenu");
  if (!menu) return;
  const key = pg === "anlz" ? "anlz" : (_DOCK_BY_PAGE[pg] ? pg : "dash");
  const items = _DOCK_BY_PAGE[key] || _DOCK_BY_PAGE.dash;
  menu.innerHTML = items.map(i => `<button type="button" onclick="${i.a}">${i.l}</button>`).join("")
    + `<button type="button" onclick="openSearch();_toggleSmartDock()">⌕ Search</button>`
    + `<button type="button" onclick="toggleChromeFocus();_toggleSmartDock()">⛶ Focus</button>`;
}

function _statusSync() {
  fetchLiveNews();
  fetchLivePrices();
  showToast("Neural sync triggered", "var(--gn)");
}

function _initStatusGestures() {
  const bar = document.getElementById("statusBar");
  if (!bar || bar._tdGestures) return;
  bar._tdGestures = true;
  let lastTap = 0;
  bar.addEventListener("click", e => {
    if (e.target.closest("button")) return;
    const now = Date.now();
    if (now - lastTap < 380) _statusSync();
    lastTap = now;
  });
  let sy = 0;
  bar.addEventListener("touchstart", e => { sy = e.touches[0].clientY; }, { passive: true });
  bar.addEventListener("touchend", e => {
    if (e.changedTouches[0].clientY - sy > 28) _statusSync();
  }, { passive: true });
}

function _initKbdStrip() {
  if (document.getElementById("kbdStrip")) return;
  const s = document.createElement("div");
  s.id = "kbdStrip";
  s.className = "kbd-strip";
  s.innerHTML = `<span><kbd>/</kbd> Search</span><span><kbd>1–4</kbd> Expand panels</span><span><kbd>⌘K</kbd> Command palette</span><span><kbd>F</kbd> Focus mode</span><span><kbd>ESC</kbd> Close</span>`;
  const cmd = document.getElementById("cmdBar");
  if (cmd && cmd.parentNode) cmd.parentNode.insertBefore(s, cmd.nextSibling);
}

function _syncTapePulse() {
  const tape = document.querySelector(".tape");
  if (tape) tape.classList.toggle("tape-live", liveSymbols.size > 0 && !updatePaused && !priceFetching);
  if (tape) tape.classList.toggle("tape-sync", priceFetching || newsFetching);
}

// ═══════════════════════════════════════════════════════════
// SMART FEATURES — proactive UX across the terminal
// ═══════════════════════════════════════════════════════════
function _smartFitBadge(tk) {
  const f = _tickerRegimeFit(tk, _computeRegimeEngine());
  const c = f.score >= 68 ? "var(--gn)" : f.score >= 45 ? "var(--gd)" : "var(--rd)";
  return `<span class="smart-fit" style="color:${c};border-color:${c}55" title="${f.label}">${f.score}</span>`;
}

function _newsRelevanceTags(text) {
  const tags = _tagNewsHeadline(text);
  const out = [];
  tags.forEach(tk => {
    const wl = isWatched(tk);
    const port = portfolio.some(p => p.tk === tk || (typeof resolveInternalTicker==="function"&&resolveInternalTicker(p.tk)===tk));
    if (wl && port) out.push({ tag: "WL+PORT", col: "var(--gd)", tk });
    else if (wl) out.push({ tag: "WATCH", col: "var(--bl)", tk });
    else if (port) out.push({ tag: "PORT", col: "var(--pu)", tk });
  });
  return out.slice(0, 2);
}

function _renderPgHdr(title, sub, actionsHtml) {
  return `<div class="pg-hdr pg-hdr-v2"><div class="pg-hdr-accent"></div><div class="pg-hdr-inner"><div class="pg-hdr-title">${title}</div><div class="pg-hdr-sub">${sub}</div></div>${actionsHtml || ""}</div>`;
}

function _renderQuickActions() {
  return `<div class="qa-row">
    <button class="qa-btn qa-gold" onclick="runMorningDeskRun()"><span class="qa-ico">☀</span><span>Desk Run</span></button>
    <button class="qa-btn qa-gold" onclick="nav('brief');loadDispatchBrief(true)"><span class="qa-ico">◆</span><span>Brief</span></button>
    <button class="qa-btn" onclick="toggleBriefPlayback()"><span class="qa-ico">▶</span><span>Listen</span></button>
    <button class="qa-btn" onclick="toggleChat()"><span class="qa-ico">⬡</span><span>Expert</span></button>
    <button class="qa-btn" onclick="nav('watch');setTimeout(runWatchlistScan,300)"><span class="qa-ico">◎</span><span>Scan</span></button>
    <button class="qa-btn" onclick="nav('sig')"><span class="qa-ico">⚡</span><span>Signals</span></button>
    <button class="qa-btn" onclick="nav('heat')"><span class="qa-ico">▦</span><span>Heat</span></button>
    <button class="qa-btn qa-gold" onclick="nav('lab')"><span class="qa-ico">◈</span><span>Lab</span></button>
  </div>`;
}

function _renderSmartFeed() {
  const intel = _mergeIntel("dash");
  const items = (intel.anomalies || []).slice(0, 5);
  if (!items.length) return "";
  const feed = items.map(a => {
    const m = typeof a === "string" ? a : a.m;
    const t = typeof a === "object" ? a.t : "info";
    const ico = t === "trigger" ? "⚡" : t === "alert" ? "▼" : t === "pos" ? "▲" : t === "warn" ? "!" : "•";
    const col = t === "trigger" ? "var(--gd)" : t === "alert" ? "var(--rd)" : t === "pos" ? "var(--gn)" : "var(--t2)";
    return `<div class="sf-item"><span class="sf-ico" style="color:${col}">${ico}</span><span class="sf-txt">${String(m).replace(/</g, "&lt;")}</span></div>`;
  }).join("");
  return `<div class="gc sf-card"><div class="sec-label-v2">Live Detections</div><div class="sf-list">${feed}</div></div>`;
}

function _renderCrossAssetPulse() {
  const pairs = [
    { a: "BTC", b: "QQQ", lbl: "BTC ↔ Nasdaq" },
    { a: "WTI", b: "XOM", lbl: "Oil ↔ Energy" },
    { a: "XAU", b: "DXY", lbl: "Gold ↔ Dollar" },
    { a: "SPX", b: "VIX", lbl: "Equity ↔ Vol" },
  ];
  const rows = pairs.map(p => {
    const ca = liveChg(p.a), cb = liveChg(p.b);
    if (ca == null || cb == null) {
      return `<div class="cap-row"><span class="cap-lbl">${p.lbl}</span><span class="cap-nums">${p.a} — · ${p.b} —</span><span class="cap-st" style="color:var(--t3)">No sync</span></div>`;
    }
    const aligned = (ca >= 0 && cb >= 0) || (ca < 0 && cb < 0);
    const st = aligned ? (Math.abs(ca - cb) > 2 ? "Diverging" : "Aligned") : "Inverse";
    const col = st === "Aligned" ? "var(--gn)" : st === "Inverse" ? "var(--bl)" : "var(--gd)";
    return `<div class="cap-row"><span class="cap-lbl">${p.lbl}</span><span class="cap-nums">${p.a} ${ca >= 0 ? "+" : ""}${ca.toFixed(1)}% · ${p.b} ${cb >= 0 ? "+" : ""}${cb.toFixed(1)}%</span><span class="cap-st" style="color:${col}">${st}</span></div>`;
  }).join("");
  return `<div class="gc cap-card"><div class="sec-label-v2">Cross-Asset Pulse</div>${rows}</div>`;
}

function _renderContinueResearch() {
  let hist = [];
  try { hist = JSON.parse(localStorage.getItem("td_lens_hist") || "[]"); } catch (e) { /* skip */ }
  if (!hist.length) return "";
  return `<div class="gc cr-card"><div class="sec-label-v2">Continue Research</div><div class="cr-row">${hist.slice(0, 4).map(h =>
    `<button class="cr-chip" onclick="openA('${h.ticker}');_setATab('cm')"><span class="cr-tk">${h.ticker}</span><span class="cr-v">${h.verdict || "—"}</span></button>`
  ).join("")}</div></div>`;
}

const SMART_COMMANDS = [
  { k: "morning", l: "Morning Desk Run", d: "Brief → regime → watchlist fits → next action", act: "runMorningDeskRun();closeSearch()" },
  { k: "desk", l: "Morning Desk Run", d: "Start the independent analyst loop", act: "runMorningDeskRun();closeSearch()" },
  { k: "gold", l: "Gold Desk", d: "Weekly gold playbook · structure · S/R · macro", act: "nav('gold');closeSearch()" },
  { k: "playbook", l: "Weekly Gold Playbook", d: "Saturday playbook — conditional scenarios for gold", act: "nav('playbook');closeSearch()" },
  { k: "letter", l: "Weekly Desk Letter", d: "Jump to this week's interactive desk letter", act: "nav('dash');setTimeout(()=>document.getElementById('desk-letter')?.scrollIntoView({behavior:'smooth'}),200);closeSearch()" },
  { k: "spine", l: "Desk Spine", d: "Fixed multi-asset board on dashboard", act: "nav('dash');setTimeout(()=>document.getElementById('desk-spine')?.scrollIntoView({behavior:'smooth'}),200);closeSearch()" },
  { k: "brief", l: "Dispatch Brief", d: "Generate today's house view", act: "nav('brief');loadDispatchBrief(true);closeSearch()" },
  { k: "regime", l: "Regime & sectors", d: "Rotation tracker", act: "nav('dash');closeSearch()" },
  { k: "signals", l: "Macro signals", d: "Conviction-weighted playbook", act: "nav('sig');closeSearch()" },
  { k: "scan", l: "Scan watchlist", d: "Regime-fit scan", act: "nav('watch');runWatchlistScan();closeSearch()" },
  { k: "sync", l: "Morning Desk Run", d: "Full desk ritual (feeds + brief + fits)", act: "runMorningDeskRun();closeSearch()" },
  { k: "expert", l: "Dispatch Expert", d: "AI research copilot", act: "toggleChat();closeSearch()" },
  { k: "focus", l: "Focus mode", d: "Maximize workspace", act: "toggleChromeFocus();closeSearch()" },
  { k: "listen", l: "Listen to brief", d: "Voice playback", act: "nav('brief');toggleBriefPlayback();closeSearch()" },
  { k: "watch", l: "Watchlist glance", d: "Expand ticker strip", act: "_wlGlanceCollapsed=false;sessionStorage.setItem('td_wl_glance_coll','0');_paintWlGlance();closeSearch()" },
  { k: "heat", l: "Heatmap", d: "Market colour map", act: "nav('mkt');closeSearch()" },
  { k: "port", l: "Portfolio", d: "Your positions", act: "nav('port');closeSearch()" },
  { k: "lens", l: "Lens Engine", d: "Stress-test active ticker", act: "if(selTk){runCommittee(selTk);}else{showToast('Open a ticker first','var(--gd)');}closeSearch()" },
  { k: "risk", l: "Risk Command", d: "Portfolio β · stress test", act: "nav('port');closeSearch()" },
  { k: "corr", l: "Correlation matrix", d: "90-day cross-asset heatmap", act: "nav('port');setTimeout(()=>{const m=_calcPortRiskMetrics();if(m)loadCorrelationMatrix(m.symbols,'port-corr-matrix');},400);closeSearch()" },
  { k: "earnings", l: "Earnings CMD", d: "Watchlist catalyst calendar", act: "nav('dash');loadEarningsRadar();closeSearch()" },
  { k: "lab", l: "Market Lab", d: "Sandbox: stress-test one ticker vs regime & scenarios", act: "nav('lab');closeSearch()" },
  { k: "stress", l: "Stress risk-off", d: "Apply risk-off macro pack in Lab", act: "applyLabMacroPack('risk_off_shock');closeSearch()" },
  { k: "softland", l: "Soft landing pack", d: "Lab macro pack: soft landing", act: "applyLabMacroPack('soft_landing');closeSearch()" },
  { k: "oil", l: "Oil spike pack", d: "Lab macro pack: oil spike", act: "applyLabMacroPack('oil_spike');closeSearch()" },
  { k: "invalidate", l: "Invalidation card", d: "Set thesis kill-switch in Lab", act: "nav('lab');setTimeout(()=>document.getElementById('lab-inv-card')?.scrollIntoView({behavior:'smooth'}),280);closeSearch()" },
  { k: "note", l: "Save desk note", d: "Snapshot Lab state", act: "if(pg!=='lab'){nav('lab');setTimeout(saveDeskNote,350);}else saveDeskNote();closeSearch()" },
  { k: "notes", l: "Desk notes", d: "Review saved Lab snapshots", act: "nav('lab');setTimeout(()=>document.getElementById('lab-notes')?.scrollIntoView({behavior:'smooth'}),280);closeSearch()" },
  { k: "geo", l: "Geo Ops", d: "Chokepoints & country dossiers", act: "nav('geo');closeSearch()" },
  { k: "hormuz", l: "Hormuz dossier", d: "Iran chokepoint exposure", act: "openCountryDossier('IR');closeSearch()" },
];

function _checkProactiveIntel() {
  if (sessionStorage.getItem("td_intel_toast_v2")) return;
  const intel = _computeLocalIntel(_siteIntel.surface || "pulse", { tk: selTk });
  if (intel.priority === "high" && intel.anomalies.length) {
    sessionStorage.setItem("td_intel_toast_v2", "1");
    const m = typeof intel.anomalies[0] === "object" ? intel.anomalies[0].m : intel.anomalies[0];
    showToast("Intel: " + String(m).slice(0, 72), "var(--gd)");
  }
}

function _mktSmartSort(list) {
  const re = _computeRegimeEngine();
  return [...list].sort((a, b) => _tickerRegimeFit(b.tk, re).score - _tickerRegimeFit(a.tk, re).score);
}

const SEARCH_QUICK_CHIPS = [
  { l: "AAPL", q: "AAPL" }, { l: "NVDA", q: "NVDA" }, { l: "BTC", q: "BTC" },
  { l: "SPX", q: "SPX" }, { l: "Letter", q: "letter" }, { l: "Morning", q: "morning" },
  { l: "Brief", q: "brief" }, { l: "Lab", q: "lab" }, { l: "Stress", q: "stress" },
];
let _searchIdx = -1;

function _paintSearchChips() {
  const el = document.getElementById("sChips");
  if (!el) return;
  el.innerHTML = SEARCH_QUICK_CHIPS.map(c =>
    `<button type="button" class="schip" onclick="document.getElementById('sinp').value='${c.q}';doSearch('${c.q}')">${c.l}</button>`
  ).join("");
}

function _searchPriceBadge(tk) {
  const sym=(typeof resolveInternalTicker==="function"?resolveInternalTicker(tk):"")||tk;
  if (!liveSymbols.has(sym)) return "";
  const d = fp(sym);
  if (d.status === "unavailable") return "";
  const ch = liveChg(sym);
  const col = ch == null ? "var(--t3)" : ch > 0 ? "var(--gn)" : ch < 0 ? "var(--rd)" : "var(--t3)";
  const sign = ch != null && ch >= 0 ? "+" : "";
  return `<span class="sres-px" style="color:${col}">${d.p} ${ch != null ? sign + Number(ch).toFixed(2) + "%" : ""}</span>`;
}

function _searchHighlight() {
  const items = document.querySelectorAll("#sres .sres");
  items.forEach((el, i) => el.classList.toggle("sres-on", i === _searchIdx));
  if (items[_searchIdx]) items[_searchIdx].scrollIntoView({ block: "nearest" });
}

function _searchKeydown(e) {
  const items = document.querySelectorAll("#sres .sres");
  if (e.key === "ArrowDown") { e.preventDefault(); _searchIdx = Math.min(_searchIdx + 1, items.length - 1); _searchHighlight(); return; }
  if (e.key === "ArrowUp") { e.preventDefault(); _searchIdx = Math.max(_searchIdx - 1, 0); _searchHighlight(); return; }
  if (e.key === "Enter" && _searchIdx >= 0 && items[_searchIdx]) { e.preventDefault(); items[_searchIdx].click(); return; }
  if (e.key === "Escape") { e.preventDefault(); closeSearch(); }
}

function _renderSmartSearchDefault() {
  const re = _computeRegimeEngine();
  const top = [...A].sort((a, b) => b.sc - a.sc).slice(0, 5);
  const cmds = SMART_COMMANDS.slice(0, 6);
  const pages = SMART_COMMANDS.filter(c => ["lab", "geo", "brief", "port", "heat"].includes(c.k));
  let h = `<div class="ssec"><div class="ssec-lbl">QUICK COMMANDS</div>${cmds.map(c =>
    `<div class="sres sres-cmd" onclick="${c.act}"><span class="sres-nm">${c.l}</span><span class="sres-d">${c.d}</span>${bd(c.k, "var(--pu)")}</div>`
  ).join("")}</div>`;
  h += `<div class="ssec"><div class="ssec-lbl">PAGES</div>${pages.map(c =>
    `<div class="sres sres-cmd" onclick="${c.act}"><span class="sres-nm">${c.l}</span><span class="sres-d">${c.d}</span>${bd("go", "var(--cy)")}</div>`
  ).join("")}</div>`;
  h += `<div class="ssec"><div class="ssec-lbl">TOP CONVICTION · ${re.label}</div>${top.map(a =>
    `<div class="sres" onclick="openA('${a.tk}');closeSearch()"><span class="sres-nm">${a.tk} — ${a.nm}</span>${_searchPriceBadge(a.tk)}${_smartFitBadge(a.tk)}${bd(a.se, a.se.includes("Bull") ? "var(--gn)" : "var(--bl)")}</div>`
  ).join("")}</div>`;
  return h;
}

function _toggleSmartDock() {
  const menu = document.getElementById("smartDockMenu");
  const fab = document.getElementById("smartDockFab");
  if (!menu) { toggleChat(); return; }
  const open = menu.classList.toggle("hide");
  if (fab) fab.classList.toggle("on", !open);
}

function initSmartDock() {
  if (document.getElementById("smartDock")) return;
  const dock = document.createElement("div");
  dock.id = "smartDock";
  dock.className = "smart-dock";
  dock.innerHTML = `<div class="smart-dock-menu hide" id="smartDockMenu"></div>
    <button type="button" class="smart-dock-fab" id="smartDockFab" onclick="_toggleSmartDock()" title="Neural quick actions">◆</button>`;
  document.body.appendChild(dock);
  _updateSmartDock();
}

function _signalSuggestedTickers() {
  const wl = new Set(getActiveWl().tickers);
  const found = [];
  SIGS.forEach(s => {
    for (const a of A) {
      if (wl.has(a.tk) || found.includes(a.tk)) continue;
      const up = a.tk.toUpperCase();
      if (s.x.toUpperCase().includes(up) || s.x.toUpperCase().includes("$" + up) || s.a.toUpperCase().includes(up)) {
        found.push(a.tk);
      }
    }
  });
  return found.slice(0, 6);
}

function _renderSignalSuggestions() {
  const tks = _signalSuggestedTickers();
  if (!tks.length) return "";
  let h = `<div class="gc" style="padding:14px;border-left:3px solid var(--gn);margin-bottom:10px">
    <div style="font-family:var(--mn);font-size:8px;color:var(--gn);letter-spacing:0.18em;margin-bottom:8px">⬢ SIGNAL SUGGESTIONS · NOT ON WATCHLIST</div>
    <div style="display:flex;gap:6px;flex-wrap:wrap">${tks.map(tk => {
      const a = A.find(x => x.tk === tk);
      return `<button onclick="addToWatchlist('${tk}');watch=getActiveWl().tickers;renderMain();showToast('${tk} added','var(--gn)')" style="font-family:var(--mn);font-size:10px;font-weight:700;padding:6px 12px;border-radius:8px;cursor:pointer;border:1px solid var(--gn)30;background:var(--gnG);color:var(--gn)">+ ${tk}${a ? " " + a.sc : ""}</button>`;
    }).join("")}</div>
    <div style="font-size:9px;color:var(--t3);margin-top:8px">High-conviction signals mention these tickers</div></div>`;
  return h;
}

function _renderConvictionHeatmap() {
  const wl = getActiveWl();
  const tks = (wl.tickers || []).filter(Boolean);
  if (tks.length < 2) return "";
  let h = `<div class="gc" style="padding:14px;border-left:3px solid var(--bl);margin-bottom:10px">
    <div style="font-family:var(--mn);font-size:8px;color:var(--bl);letter-spacing:0.18em;margin-bottom:10px">⬢ CONVICTION HEATMAP</div>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(72px,1fr));gap:6px">`;
  tks.forEach(tk => {
    const a = A.find(x => x.tk === tk);
    const chg = liveChg(tk);
    const sc = a?.sc != null ? a.sc : Math.round(_tickerRegimeFit(tk, _computeRegimeEngine()).score);
    const bg = sc >= 75 ? "rgba(16,185,129,0.15)" : sc >= 55 ? "rgba(245,166,35,0.12)" : "rgba(239,68,68,0.1)";
    const border = chg == null ? "var(--t3)" : chg > 0 ? "var(--gn)" : chg < 0 ? "var(--rd)" : "var(--t3)";
    const chgLbl = chg == null ? "—" : `${chg >= 0 ? "+" : ""}${chg.toFixed(2)}%`;
    h += `<div onclick="openA('${tk}')" style="cursor:pointer;text-align:center;padding:10px 6px;border-radius:8px;background:${bg};border:1px solid ${border}40">
      <div style="font-family:var(--mn);font-size:11px;font-weight:800;color:var(--tx)">${tk}</div>
      <div style="font-family:var(--mn);font-size:16px;font-weight:900;color:var(--gd);margin:4px 0">${sc}</div>
      <div style="font-family:var(--mn);font-size:9px;color:${border}">${chgLbl}</div>
    </div>`;
  });
  h += `</div></div>`;
  return h;
}

const EM_SPOTLIGHT_TKS = ["EEM", "INDA", "INFY", "USDINR", "FXI", "EWZ", "NSEI"];
function _renderEMSpotlight() {
  const wlEm = getActiveWl().tickers.filter(tk => tk.endsWith(".NS") || tk.endsWith(".BO"));
  const tks = [...new Set([...wlEm, ...EM_SPOTLIGHT_TKS])].slice(0, 8);
  const re = _computeRegimeEngine();
  const emFriendly = re.score >= 55 && re.overweight.some(x => x.toLowerCase().includes("cyclical") || x.toLowerCase().includes("tech"));
  let h = `<div class="gc" style="padding:14px;border-left:3px solid var(--cy);margin-bottom:10px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
      <div style="font-family:var(--mn);font-size:8px;color:var(--cy);letter-spacing:0.18em">⬢ EM & INDIA SPOTLIGHT</div>
      <span style="font-family:var(--mn);font-size:9px;color:${emFriendly ? "var(--gn)" : "var(--t3)"}">${emFriendly ? "Risk-on tailwind" : "Neutral / cautious"}</span>
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:6px">`;
  tks.forEach(tk => {
    const a = A.find(x => x.tk === tk);
    const d = fp(tk);
    const na = d.status === "unavailable";
    const chg = liveChg(tk);
    h += `<div onclick="openA('${tk}')" style="cursor:pointer;padding:10px;background:var(--b1);border-radius:8px;border:1px solid var(--gb)">
      <div style="font-family:var(--mn);font-size:11px;font-weight:800">${tk}</div>
      <div style="font-size:9px;color:var(--t3);margin:2px 0">${a?.nm?.slice(0, 18) || "—"}</div>
      <div style="font-family:var(--mn);font-size:12px;font-weight:700">${na?"—":d.p}</div>
      <div style="font-family:var(--mn);font-size:9px;color:${chg==null?"var(--t3)":(chg >= 0 ? "var(--gn)" : "var(--rd)")}">${chg==null?"NO SYNC":`${chg >= 0 ? "+" : ""}${chg.toFixed(2)}%`}</div>
    </div>`;
  });
  h += `</div><div style="font-size:9px;color:var(--t3);margin-top:8px">Search NSE tickers: RELIANCE.NS · TCS.NS · HDFCBANK.NS</div></div>`;
  return h;
}

const LENS_QUICK_PROMPTS = [
  { lb: "Bull case", tx: "I'm constructive because fundamentals and momentum support a higher price. Key catalyst:" },
  { lb: "Bear stress-test", tx: "Attack this thesis: valuation is stretched, margins peak, and macro headwinds accelerate." },
  { lb: "Earnings setup", tx: "Into earnings — guide vs whisper, margin trajectory, and positioning into the print." },
  { lb: "Position sizing", tx: "Given beta and regime, what is appropriate sizing and max drawdown tolerance?" },
  { lb: "Regime fit", tx: "Does this holding align with the current macro regime or fight it? Rebalance case?" }
];

function _applyLensPrompt(tk, text) {
  lensThesis[tk] = text;
  const ta = document.getElementById("lens-thesis-" + tk) || document.getElementById("term-lens-thesis");
  if (ta) ta.value = text;
  showToast("Thesis prompt applied", "var(--pu)");
}

function _applyLensPromptIdx(tk, idx) {
  const p = LENS_QUICK_PROMPTS[idx];
  if (p) _applyLensPrompt(tk, p.tx);
}

function _renderLensQuickPrompts(tk) {
  return `<div style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:10px">${LENS_QUICK_PROMPTS.map((p, i) =>
    `<button type="button" onclick="event.stopPropagation();_applyLensPromptIdx('${tk}',${i})" style="font-family:var(--mn);font-size:9px;padding:5px 10px;border-radius:6px;cursor:pointer;border:1px solid var(--pu)30;background:var(--puG);color:var(--pu)">${p.lb}</button>`
  ).join("")}</div>`;
}

function _matchTickerSignals(tk) {
  const a = A.find(x => x.tk === tk);
  const up = tk.toUpperCase();
  const nm = (a?.nm || "").toLowerCase();
  const cat = (a?.cat || "").toLowerCase();
  return SIGS.filter(s => {
    const sx = s.x.toUpperCase(), sa = s.a.toUpperCase();
    if (sa.includes(up) || sx.includes(up) || sx.includes("$" + up)) return true;
    if (cat && s.tg.toLowerCase().includes(cat)) return true;
    if (nm && sa.includes(nm.split(" ")[0].toUpperCase())) return true;
    if (a?.cat === "Commodity" && (s.a === "Gold" && tk === "XAU" || s.a === "Energy" && (tk === "WTI" || tk === "XOM"))) return true;
    if (a?.cat === "Crypto" && s.tg === "Crypto") return true;
    return false;
  }).sort((a, b) => b.cf - a.cf);
}

function _renderTickerSignals(tk) {
  const matched = _matchTickerSignals(tk);
  if (!matched.length) return "";
  let h = `<div class="gc" style="padding:12px;border-left:3px solid var(--pu);margin-bottom:8px">
    <div style="font-family:var(--mn);font-size:8px;color:var(--pu);letter-spacing:0.15em;margin-bottom:8px">ACTIVE SIGNALS · ${matched.length}</div>`;
  matched.slice(0, 3).forEach(s => {
    const bc = s.cat.includes("Bull") || s.cat === "Momentum" || s.cat === "Accumulation" ? "var(--gn)" : s.cat.includes("Warning") || s.cat === "Geopolitical" ? "var(--rd)" : "var(--gd)";
    h += `<div style="padding:8px 0;border-top:1px solid var(--gb)"><div style="display:flex;justify-content:space-between;align-items:center"><span style="font-size:12px;font-weight:700">${s.a}</span><span style="font-family:var(--mn);font-size:13px;font-weight:800;color:${s.cf >= 75 ? "var(--gn)" : "var(--gd)"}">${s.cf}%</span></div>
      <div style="font-size:10px;color:var(--t2);line-height:1.45;margin-top:3px">${s.x}</div>
      <div style="display:flex;gap:3px;margin-top:4px">${bd(s.cat, bc)}${bd(s.hz, "var(--pu)")}</div></div>`;
  });
  h += `<button onclick="nav('sig')" style="margin-top:8px;width:100%;background:var(--b2);border:1px solid var(--gb);color:var(--t2);border-radius:7px;padding:8px;font-family:var(--mn);font-size:9px;cursor:pointer">View all signals →</button></div>`;
  return h;
}

let _portScan = null;
function runPortfolioScan() {
  if (!portfolio.length) { showToast("Add holdings first", "var(--gd)"); return; }
  const re = _computeRegimeEngine();
  let totalVal = 0, weightedSc = 0, bullishW = 0, bearishW = 0, beatSpy = 0, weightedBeta = 0;
  const spyC = liveChg("SPY") ?? liveChg("SPX");
  const rows = portfolio.map(pos => {
    const m = _portMark(pos);
    const a = A.find(x => x.tk === pos.tk);
    totalVal += m.value;
    return { pos, a, val: m.value, live: m.live, sc: a?.sc || 50, se: a?.se || "Neutral" };
  });
  rows.forEach(r => {
    const w = totalVal ? r.val / totalVal : 0;
    weightedSc += r.sc * w;
    const beta = parseFloat(String(r.a?.beta || "1").replace(/x/i, "")) || 1;
    weightedBeta += beta * w;
    if (r.se.includes("Bull")) bullishW += w;
    if (r.se.includes("Bear") || r.a?.ra === "Avoid") bearishW += w;
    if (r.live && spyC != null) {
      const c = liveChg(r.pos.tk);
      if (c != null && c > spyC) beatSpy += w;
    }
  });
  const best = [...rows].sort((a, b) => b.sc - a.sc)[0];
  const worst = [...rows].sort((a, b) => a.sc - b.sc)[0];
  const topPos = [...rows].sort((a, b) => b.val - a.val)[0];
  const concPct = totalVal ? Math.round((topPos.val / totalVal) * 100) : 0;
  const aligned = re.score >= 55 ? bullishW >= bearishW : bearishW <= bullishW;
  _portScan = { weightedSc: Math.round(weightedSc), weightedBeta: weightedBeta.toFixed(2), bullishW: Math.round(bullishW * 100), bearishW: Math.round(bearishW * 100), beatSpy: Math.round(beatSpy * 100), best, worst, concPct, topPos: topPos.pos.tk, aligned, regime: re.label, count: rows.length };
  renderMain();
}

function _renderPortScan() {
  if (!_portScan) return "";
  const s = _portScan;
  const alignCol = s.aligned ? "var(--gn)" : "var(--rd)";
  return `<div class="gc" style="padding:14px;border-left:3px solid var(--gd);margin-bottom:10px">
    <div style="font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.18em;margin-bottom:10px">⬢ PORTFOLIO REGIME SCAN</div>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--gb);border-radius:8px;overflow:hidden;margin-bottom:10px">
      <div style="background:var(--bg);padding:10px;text-align:center"><div style="font-size:8px;color:var(--t3)">WTD SCORE</div><div style="font-family:var(--mn);font-size:18px;font-weight:900;color:var(--gd)">${s.weightedSc}</div></div>
      <div style="background:var(--bg);padding:10px;text-align:center"><div style="font-size:8px;color:var(--t3)">BULL WT</div><div style="font-family:var(--mn);font-size:18px;font-weight:900;color:var(--gn)">${s.bullishW}%</div></div>
      <div style="background:var(--bg);padding:10px;text-align:center"><div style="font-size:8px;color:var(--t3)">BEAR WT</div><div style="font-family:var(--mn);font-size:18px;font-weight:900;color:var(--rd)">${s.bearishW}%</div></div>
      <div style="background:var(--bg);padding:10px;text-align:center"><div style="font-size:8px;color:var(--t3)">BEAT SPY</div><div style="font-family:var(--mn);font-size:18px;font-weight:900;color:var(--gn)">${s.beatSpy}%</div></div>
    </div>
    <div style="font-size:11px;color:var(--t2);line-height:1.6;margin-bottom:6px">
      <strong style="color:var(--gn)">${s.best.pos.tk}</strong> highest conviction (${s.best.sc}/100) · <strong style="color:var(--rd)">${s.worst.pos.tk}</strong> lowest (${s.worst.sc}/100) · Top holding <strong>${s.topPos}</strong> at ${s.concPct}% · Est. beta <strong>${s.weightedBeta}</strong>
    </div>
    <div style="font-size:10px;color:${alignCol};font-family:var(--mn)">${s.aligned ? "✓ Portfolio tilt aligns with " + s.regime : "⚠ Portfolio conflicts with " + s.regime + " — consider rebalance"}</div>
    ${s.concPct > 35 ? `<div style="font-size:10px;color:var(--rd);font-family:var(--mn);margin-top:6px">⚠ Concentration risk — ${s.topPos} is ${s.concPct}% of book</div>` : ""}
  </div>`;
}

/** Equity-like book names eligible for earnings API (curated stocks + dyn lookups) */
function _isDeskEquity(tk) {
  if (!tk) return false;
  const a = A.find(x => x.tk === tk);
  if (a) return a.cat === "Stock";
  const cat = typeof TICKER_CATS !== "undefined" ? TICKER_CATS[tk] : null;
  if (cat && cat !== "stk" && cat !== "idx") return false;
  const yh = typeof YAHOO_SYMBOLS !== "undefined" ? YAHOO_SYMBOLS[tk] : null;
  if (yh && (yh.includes("=X") || yh.includes("-USD") || yh.includes("=F") || yh.startsWith("^"))) return false;
  if (/-USD$|USD=X$|=F$|^\^/.test(tk)) return false;
  return true;
}

let _earnRadar = null, _earnRadarLoad = false;
async function loadEarningsRadar() {
  if (_earnRadarLoad) return;
  const tks = [...new Set([...getActiveWl().tickers, ...portfolio.map(p => p.tk)])]
    .filter(tk => _isDeskEquity(tk)).slice(0, 12);
  if (!tks.length) return;
  _earnRadarLoad = true;
  const upcoming = [];
  await Promise.all(tks.map(async tk => {
    try {
      if (!_earnCache[tk]) {
        const res = await fetch("/api/earnings?symbol=" + encodeURIComponent(tk));
        if (res.ok) _earnCache[tk] = await res.json();
      }
      const next = _earnCache[tk]?.nextEarnings;
      if (!next?.date) return;
      const days = Math.ceil((new Date(next.date) - Date.now()) / 86400000);
      if (days >= 0 && days <= 30) {
        const inPort = portfolio.some(p => p.tk === tk);
        const inWl = getActiveWl().tickers.includes(tk);
        upcoming.push({ tk, date: next.date, days, eps: next.epsEstimate, beatRate: _earnCache[tk]?.beatRate, src: inPort && inWl ? "Port+Watch" : inPort ? "Portfolio" : "Watchlist" });
      }
    } catch (e) { /* skip */ }
  }));
  upcoming.sort((a, b) => a.days - b.days);
  _earnRadar = upcoming;
  _earnRadarLoad = false;
  if (pg === "dash") renderMain();
}

function _renderEarningsRadar() {
  if (_earnRadarLoad) return `<div class="gc" style="padding:16px;text-align:center;border-left:3px solid var(--gn)"><div style="width:12px;height:12px;border:2px solid var(--gn);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 8px"></div><div style="font-family:var(--mn);font-size:9px;color:var(--gn)">SCANNING EARNINGS CATALYSTS…</div></div>`;
  if (!_earnRadar?.length) return "";
  let h = `<div class="gc" style="padding:14px;border-left:3px solid var(--gn);margin-bottom:10px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
      <div style="font-family:var(--mn);font-size:8px;color:var(--gn);letter-spacing:0.18em">⬢ EARNINGS CATALYST RADAR</div>
      <button onclick="loadEarningsRadar()" style="background:var(--b2);border:1px solid var(--gb);color:var(--t3);border-radius:5px;padding:2px 8px;font-family:var(--mn);font-size:8px;cursor:pointer">↻</button>
    </div>`;
  _earnRadar.slice(0, 5).forEach(e => {
    const urg = e.days <= 3 ? "var(--rd)" : e.days <= 7 ? "var(--gd)" : "var(--gn)";
    const when = e.days === 0 ? "Today" : e.days === 1 ? "Tomorrow" : e.days + "d";
    h += `<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-top:1px solid var(--gb);cursor:pointer" onclick="openA('${e.tk}');_setATab('earn')">
      <div><span style="font-family:var(--mn);font-weight:800;font-size:13px;color:var(--tx)">${e.tk}</span><span style="font-size:9px;color:var(--t3);margin-left:8px">${e.date}</span></div>
      <div style="text-align:right"><span style="font-family:var(--mn);font-size:12px;font-weight:800;color:${urg}">${when}</span>${e.eps != null ? `<div style="font-size:8px;color:var(--t3)">EPS est $${e.eps}</div>` : ""}</div></div>`;
  });
  h += `</div>`;
  return h;
}

// ═══════════════════════════════════════════════════════════
// PRO TERMINAL — 5 elite features (Koyfin · Bloomberg · TradingView class)
// ═══════════════════════════════════════════════════════════

function _saveSmartAlerts(){localStorage.setItem("td_smart_alerts",JSON.stringify(smartAlerts));}

function _calcPortRiskMetrics(){
  if(!portfolio.length)return null;
  let totalVal=0;const weights=[];
  const sectors={};
  portfolio.forEach(pos=>{
    const val=_portMark(pos).value;
    totalVal+=val;
    const a=A.find(x=>x.tk===pos.tk);
    weights.push({tk:pos.tk,val,beta:_deskBeta(a||pos.tk,1),cat:a?.cat||"Other"});
  });
  if(!totalVal)return null;
  weights.forEach(w=>{w.w=w.val/totalVal;sectors[w.cat]=(sectors[w.cat]||0)+w.w;});
  const beta=weights.reduce((s,w)=>s+w.w*w.beta,0);
  const hhi=weights.reduce((s,w)=>s+w.w*w.w,0);
  const maxPos=[...weights].sort((a,b)=>b.w-a.w)[0];
  const topSector=Object.entries(sectors).sort((a,b)=>b[1]-a[1])[0];
  const stressLoss=totalVal*beta*0.1;
  const riskScore=Math.min(10,Math.round(beta*2.5+hhi*8+(maxPos?.w>0.25?2:0)));
  const riskLabel=riskScore>=8?"High":riskScore>=5?"Moderate":"Low";
  return{totalVal,beta,hhi,maxPos,topSector,sectors,stressLoss,riskScore,riskLabel,symbols:weights.map(w=>w.tk)};
}

async function _fetchReturns(tk){
  if(_corrCache[tk]?.returns)return _corrCache[tk].returns;
  try{
    const ysym=YAHOO_SYMBOLS[tk]||tk;
    const res=await chartFetch(`/api/yahoo-chart?symbol=${encodeURIComponent(ysym)}&range=3mo&interval=1d`,{signal:AbortSignal.timeout(10000)});
    if(!res.ok)return null;
    const data=await res.json();
    const closes=(data?.chart?.result?.[0]?.indicators?.quote?.[0]?.close||[]).filter(v=>v!=null&&isFinite(v));
    if(closes.length<15)return null;
    const rets=[];for(let i=1;i<closes.length;i++)rets.push((closes[i]-closes[i-1])/closes[i-1]);
    _corrCache[tk]={returns:rets};return rets;
  }catch{return null;}
}

function _pearson(a,b){
  const n=Math.min(a.length,b.length);if(n<10)return null;
  const x=a.slice(-n),y=b.slice(-n);
  const mx=x.reduce((s,v)=>s+v,0)/n,my=y.reduce((s,v)=>s+v,0)/n;
  let num=0,dx=0,dy=0;
  for(let i=0;i<n;i++){num+=(x[i]-mx)*(y[i]-my);dx+=(x[i]-mx)**2;dy+=(y[i]-my)**2;}
  const den=Math.sqrt(dx*dy);return den?+(num/den).toFixed(2):null;
}

async function loadCorrelationMatrix(symbols,containerId){
  const el=document.getElementById(containerId);
  if(!el||_corrLoading)return;
  _corrLoading=true;
  const syms=[...new Set(["SPY",...symbols])].slice(0,6);
  el.innerHTML=`<div style="padding:16px;text-align:center"><div style="width:12px;height:12px;border:2px solid var(--bl);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 8px"></div><div style="font-family:var(--mn);font-size:9px;color:var(--bl)">COMPUTING 90-DAY CORRELATIONS…</div></div>`;
  const rets={};await Promise.all(syms.map(async s=>{rets[s]=await _fetchReturns(s);}));
  const matrix={};syms.forEach(a=>{matrix[a]={};syms.forEach(b=>{matrix[a][b]=!rets[a]||!rets[b]?null:a===b?1:_pearson(rets[a],rets[b]);});});
  _corrLoading=false;
  el.innerHTML=_renderCorrMatrixHTML(syms,matrix);
  if(pg==="dash")renderMain();
}

function _corrColor(v){
  if(v==null)return"var(--b3)";
  if(v>=0.7)return"rgba(239,68,68,0.55)";
  if(v>=0.4)return"rgba(245,158,11,0.45)";
  if(v>=0)return"rgba(16,185,129,0.35)";
  return"rgba(79,142,247,0.45)";
}

function _renderCorrMatrixHTML(syms,matrix){
  let h=`<div class="corr-wrap"><table class="corr-table"><thead><tr><th></th>`;
  syms.forEach(s=>{h+=`<th>${s}</th>`;});
  h+=`</tr></thead><tbody>`;
  syms.forEach(a=>{
    h+=`<tr><th>${a}</th>`;
    syms.forEach(b=>{const v=matrix[a][b];h+=`<td style="background:${_corrColor(v)}" title="${a}↔${b}">${v!=null?v.toFixed(2):"—"}</td>`;});
    h+=`</tr>`;
  });
  return h+`</tbody></table><div class="corr-legend"><span style="background:rgba(239,68,68,0.55)">High +</span><span style="background:rgba(245,158,11,0.45)">Moderate</span><span style="background:rgba(16,185,129,0.35)">Low +</span><span style="background:rgba(79,142,247,0.45)">Inverse</span></div></div>`;
}

function _renderPortfolioRiskCenter(){
  const m=_calcPortRiskMetrics();
  if(!m)return"";
  const col=m.riskScore>=8?"var(--rd)":m.riskScore>=5?"var(--gd)":"var(--gn)";
  const cid="port-corr-matrix";
  const symsArg=JSON.stringify(m.symbols);
  return`<div class="gc pro-risk-card">
    <div class="pro-feat-hdr"><div class="pro-feat-kicker">① PORTFOLIO RISK COMMAND</div><span class="pro-feat-badge">Bloomberg PORT</span></div>
    <div class="pro-risk-grid">
      <div class="pro-risk-stat"><div class="pro-risk-lbl">RISK SCORE</div><div class="pro-risk-val" style="color:${col}">${m.riskScore}/10</div><div class="pro-risk-sub">${m.riskLabel}</div></div>
      <div class="pro-risk-stat"><div class="pro-risk-lbl">PORTFOLIO β</div><div class="pro-risk-val">${m.beta.toFixed(2)}</div><div class="pro-risk-sub">vs SPY</div></div>
      <div class="pro-risk-stat"><div class="pro-risk-lbl">CONCENTRATION</div><div class="pro-risk-val">${(m.hhi*100).toFixed(0)}%</div><div class="pro-risk-sub">max ${m.maxPos.tk} ${(m.maxPos.w*100).toFixed(0)}%</div></div>
      <div class="pro-risk-stat"><div class="pro-risk-lbl">STRESS −10% SPX</div><div class="pro-risk-val" style="color:var(--rd)">−$${m.stressLoss.toLocaleString(undefined,{maximumFractionDigits:0})}</div><div class="pro-risk-sub">${m.topSector?m.topSector[0]+" "+(m.topSector[1]*100).toFixed(0)+"%":""}</div></div>
    </div>
    <div id="${cid}"><button class="pro-btn" onclick='loadCorrelationMatrix(${symsArg},"${cid}")'>② Load Correlation Matrix →</button></div>
  </div>`;
}

function _renderEarningsCommandCenter(){
  if(_earnRadarLoad)return`<div class="gc pro-earn-card" style="padding:16px;text-align:center"><div style="width:12px;height:12px;border:2px solid var(--gn);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 8px"></div><div style="font-family:var(--mn);font-size:9px;color:var(--gn)">BUILDING EARNINGS COMMAND CENTER…</div></div>`;
  const items=_earnRadar||[];
  if(!items.length)return"";
  let h=`<div class="gc pro-earn-card">
    <div class="pro-feat-hdr"><div class="pro-feat-kicker">③ EARNINGS COMMAND CENTER</div><span class="pro-feat-badge">Koyfin</span>
      <button onclick="loadEarningsRadar()" style="background:var(--b2);border:1px solid var(--gb);color:var(--t3);border-radius:5px;padding:2px 8px;font-family:var(--mn);font-size:8px;cursor:pointer;margin-left:auto">↻</button>
    </div>`;
  items.slice(0,8).forEach(e=>{
    const urg=e.days<=3?"var(--rd)":e.days<=7?"var(--gd)":"var(--gn)";
    const when=e.days===0?"TODAY":e.days===1?"TOMORROW":e.days+"d";
    const br=e.beatRate;
    const hasBr=br!=null&&isFinite(br);
    const beat=hasBr?br+"% beat":"";
    // null beatRate must not coerce to 0 → false "Caution"
    const pos=!hasBr?"—":br>=75?"Long bias":br<=40?"Caution":"Neutral";
    const posCol=!hasBr?"var(--t3)":br>=75?"var(--gn)":br<=40?"var(--rd)":"var(--gd)";
    h+=`<div class="pro-earn-row" onclick="openA('${e.tk}');_setATab('earn')">
      <div><span class="pro-earn-tk">${e.tk}</span><span class="pro-earn-src">${e.src||""}</span><span class="pro-earn-date">${e.date}</span></div>
      <div class="pro-earn-r"><span class="pro-earn-when" style="color:${urg}">${when}</span>${beat?`<span class="pro-earn-beat">${beat}</span>`:""}<span class="pro-earn-pos" style="color:${posCol}">${pos}</span></div>
    </div>`;
  });
  return h+`</div>`;
}

function _renderProTerminalHub(){
  const hasPort=portfolio.length>0;
  const earnN=(_earnRadar||[]).length;
  const smartN=smartAlerts.filter(a=>a.active).length;
  return`<div class="pro-hub">
    <div class="pro-hub-title">PRO TERMINAL · TOP 1% FEATURES</div>
    <div class="pro-hub-grid">
      <div class="pro-hub-card" onclick="nav('port')"><div class="pro-hub-n">①</div><div class="pro-hub-lbl">Risk Command</div><div class="pro-hub-sub">β · HHI · stress test</div></div>
      <div class="pro-hub-card" onclick="nav('port');setTimeout(()=>{const m=_calcPortRiskMetrics();if(m)loadCorrelationMatrix(m.symbols,'port-corr-matrix');},400)"><div class="pro-hub-n">②</div><div class="pro-hub-lbl">Correlation Matrix</div><div class="pro-hub-sub">90-day heatmap</div></div>
      <div class="pro-hub-card" onclick="nav('dash');loadEarningsRadar()"><div class="pro-hub-n">③</div><div class="pro-hub-lbl">Earnings CMD</div><div class="pro-hub-sub">${earnN?earnN+" catalysts":"scan watchlist"}</div></div>
      <div class="pro-hub-card" onclick="nav('port')"><div class="pro-hub-n">④</div><div class="pro-hub-lbl">Smart Alerts</div><div class="pro-hub-sub">${smartN} active rules</div></div>
      <div class="pro-hub-card" onclick="openA('NVDA');_setATab('val')"><div class="pro-hub-n">⑤</div><div class="pro-hub-lbl">Peer Battle</div><div class="pro-hub-sub">comps radar</div></div>
      <div class="pro-hub-card pro-hub-lab" onclick="nav('lab')"><div class="pro-hub-n">◆</div><div class="pro-hub-lbl">Market Lab</div><div class="pro-hub-sub">stress-test one ticker</div></div>
      <div class="pro-hub-card pro-hub-geo" onclick="nav('geo')"><div class="pro-hub-n">🌐</div><div class="pro-hub-lbl">Geo Ops</div><div class="pro-hub-sub">chokepoints · dossiers</div></div>
    </div>
    ${!hasPort?`<div class="pro-hub-hint">Add portfolio positions to unlock Risk Command + Correlation Matrix</div>`:""}
  </div>`;
}

function addSmartAlert(type,tk,threshold){
  smartAlerts=smartAlerts.filter(a=>!(a.type===type&&a.tk===tk));
  smartAlerts.push({type,tk:tk||"",threshold:threshold||10,active:true,ts:Date.now()});
  _saveSmartAlerts();
  showToast("Smart alert armed","var(--gd)");
  if(pg==="port")renderMain();
}

function removeSmartAlert(idx){
  smartAlerts.splice(idx,1);_saveSmartAlerts();
  if(pg==="port")renderMain();
}

function _renderSmartAlertsPanel(){
  let h=`<div class="gc pro-alert-card">
    <div class="pro-feat-hdr"><div class="pro-feat-kicker">④ INSTITUTIONAL SMART ALERTS</div><span class="pro-feat-badge">TradingView Pro</span></div>
    <div class="pro-alert-presets">
      <button class="pro-alert-btn" onclick="addSmartAlert('regime')">Regime shift</button>
      <button class="pro-alert-btn" onclick="addSmartAlert('drawdown','',15)">Portfolio −15%</button>
      <button class="pro-alert-btn" onclick="addSmartAlert('earnings','',7)">Earnings ≤7d</button>
      <button class="pro-alert-btn" onclick="addSmartAlert('conviction','',10)">Conviction drop</button>
      <button class="pro-alert-btn" onclick="addSmartAlert('convergence')">Geo convergence</button>
    </div>`;
  const active=smartAlerts.filter(a=>a.active);
  if(active.length){
    active.forEach((a,i)=>{
      const lbl=a.type==="regime"?"Regime change":a.type==="drawdown"?`Drawdown ≥${a.threshold}%`:a.type==="earnings"?`Earnings ≤${a.threshold}d`:a.type==="conviction"?`Conviction −${a.threshold}`:a.type==="convergence"?"Geo+price+regime converge":`${a.type} ${a.tk}`;
      h+=`<div class="pro-alert-row"><span>${lbl}</span><span onclick="removeSmartAlert(${smartAlerts.indexOf(a)})" style="color:var(--rd);cursor:pointer">✕</span></div>`;
    });
  }else h+=`<div style="font-family:var(--sn);font-size:11px;color:var(--t3);padding:8px 0">No smart alerts — arm a rule above</div>`;
  return h+`</div>`;
}

function checkSmartAlerts(){
  const re=_computeRegimeEngine();
  if(_lastRegimeLabel&&_lastRegimeLabel!==re.label){
    smartAlerts.filter(a=>a.type==="regime"&&a.active).forEach(a=>{
      showToast(`⬢ Regime shift: ${_lastRegimeLabel} → ${re.label}`,"var(--gd)");
      a.active=false;
    });
  }
  _lastRegimeLabel=re.label;
  portfolio.forEach(pos=>{
    const price=livePx(pos.tk),cost=pos.avgCost;
    if(!price||!cost)return;
    const pnlPct=((price-cost)/cost)*100;
    smartAlerts.filter(a=>a.type==="drawdown"&&a.active).forEach(a=>{
      if(pnlPct<=-a.threshold){showToast(`⬢ Drawdown: ${pos.tk} ${pnlPct.toFixed(1)}%`,"var(--rd)");a.active=false;}
    });
  });
  if((_earnRadar||[]).length){
    smartAlerts.filter(a=>a.type==="earnings"&&a.active).forEach(a=>{
      const hit=_earnRadar.find(e=>e.days<=a.threshold);
      if(hit){showToast(`⬢ Earnings: ${hit.tk} in ${hit.days}d`,"var(--gn)");a.active=false;}
    });
  }
  checkConvergenceAlerts();
  const triggered=smartAlerts.some(a=>!a.active);
  if(triggered)_saveSmartAlerts();
}

function _renderPeerBattleStation(tk,cache){
  const{finData,peerData,peers}=cache;
  if(!finData?.metrics||!peers.length)return"";
  const m=finData.metrics;
  const dims=[
    {k:"pe",lbl:"Value",inv:true,fn:v=>v?1/Math.min(v,80):0},
    {k:"revenueGrowthTTM",lbl:"Growth",fn:v=>v?Math.min(v,50)/50:0},
    {k:"netProfitMarginTTM",lbl:"Margin",fn:v=>v?Math.min(v,40)/40:0},
    {k:"roeTTM",lbl:"ROE",fn:v=>v?Math.min(v,50)/50:0},
  ];
  const all=[tk,...peers.filter(p=>peerData[p])].slice(0,5);
  const scores={};
  all.forEach(ptk=>{
    const pm=ptk===tk?m:peerData[ptk]?.metrics||{};
    const a=A.find(x=>x.tk===ptk);
    const lc=liveChg(ptk);
    const chg=lc!=null?Math.abs(lc)/5:0;
    scores[ptk]=dims.map(d=>d.fn(pm[d.k]||0)*0.85+(a?.sc||50)/100*0.15+chg*0.05);
  });
  const cx=120,cy=100,r=70,n=dims.length;
  const pts=tk=>dims.map((d,i)=>{const ang=Math.PI*2*i/n-Math.PI/2;const v=scores[tk][i]||0;return`${cx+Math.cos(ang)*r*v},${cy+Math.sin(ang)*r*v}`;}).join(" ");
  const labels=dims.map((d,i)=>{const ang=Math.PI*2*i/n-Math.PI/2;return`<text x="${cx+Math.cos(ang)*(r+16)}" y="${cy+Math.sin(ang)*(r+16)}" text-anchor="middle" font-family="JetBrains Mono" font-size="8" fill="var(--t3)">${d.lbl}</text>`;}).join("");
  const colors=["var(--gd)","var(--bl)","var(--gn)","var(--pu)","var(--cy)"];
  let polys=all.map((ptk,i)=>`<polygon points="${pts(ptk)}" fill="${colors[i%5]}" fill-opacity="${ptk===tk?0.25:0.08}" stroke="${colors[i%5]}" stroke-width="${ptk===tk?2:1}" stroke-opacity="${ptk===tk?0.9:0.4}"/>`).join("");
  let legend=all.map((ptk,i)=>`<span style="color:${colors[i%5]};font-family:var(--mn);font-size:9px;margin-right:10px">${ptk}${ptk===tk?" ★":""}</span>`).join("");
  const ranks=all.map(ptk=>({tk:ptk,s:scores[ptk].reduce((a,b)=>a+b,0)/dims.length})).sort((a,b)=>b.s-a.s);
  const rank=ranks.findIndex(r=>r.tk===tk)+1;
  return`<div class="pro-peer-card">
    <div class="pro-feat-hdr"><div class="pro-feat-kicker">⑤ PEER BATTLE STATION</div><span class="pro-feat-badge">Koyfin Comps</span></div>
    <div style="display:flex;gap:14px;align-items:center;flex-wrap:wrap">
      <svg width="240" height="200" viewBox="0 0 240 200" style="flex-shrink:0">${polys}<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="var(--gb)" stroke-width="1"/>${labels}</svg>
      <div><div style="font-family:var(--mn);font-size:22px;font-weight:900;color:var(--gd)">#${rank}</div><div style="font-family:var(--sn);font-size:12px;color:var(--t2)">of ${all.length} peers on composite score</div><div style="margin-top:8px">${legend}</div></div>
    </div>
  </div>`;
}

// ═══════════════════════════════════════════════════════════
// GEO OPS CENTER — World Monitor-inspired fusion layer
// ═══════════════════════════════════════════════════════════

const TD_CHOKEPOINTS = [
  {id:"hormuz",name:"Hormuz",full:"Strait of Hormuz",base:82,wow:-18,tickers:["XOM","CVX","XLE","SLB","WTI"]},
  {id:"bab",name:"Bab el-Mandeb",full:"Bab el-Mandeb",base:78,wow:-12,tickers:["XOM","BP","WTI","BRENT"]},
  {id:"suez",name:"Suez",full:"Suez Canal",base:38,wow:-4,tickers:["XLE"]},
  {id:"panama",name:"Panama",full:"Panama Canal",base:22,wow:2,tickers:["XLE"]},
  {id:"malacca",name:"Malacca",full:"Strait of Malacca",base:18,wow:0,tickers:["XOM","CVX"]},
];

const TD_COUNTRY_DOSSIERS = {
  IR:{flag:"🇮🇷",name:"Iran",cii:66,delta:3,signals:["Hormuz transit fee $2M/tanker","Ceasefire expires Apr 22"],tickers:["XOM","LMT","XLE","XAU","WTI"],lens:["XOM","LMT"]},
  IL:{flag:"🇮🇱",name:"Israel",cii:71,delta:2,signals:["Regional escalation risk","Defense spending tailwind"],tickers:["LMT","RTX","XAU"],lens:["LMT","RTX"]},
  UA:{flag:"🇺🇦",name:"Ukraine",cii:78,delta:0,signals:["Active conflict — UCDP events","Grain corridor volatility"],tickers:["LMT","RTX","WHEAT"],lens:["LMT"]},
  RU:{flag:"🇷🇺",name:"Russia",cii:62,delta:-1,signals:["Sanctions regime","Energy export rerouting"],tickers:["XOM","BP","XLE"],lens:["XOM"]},
  YE:{flag:"🇾🇪",name:"Yemen",cii:74,delta:4,signals:["Red Sea attacks","Bab el-Mandeb disruption"],tickers:["XOM","BP","WTI"],lens:["XOM","XLE"]},
  SA:{flag:"🇸🇦",name:"Saudi Arabia",cii:48,delta:1,signals:["OPEC+ policy lever","Red Sea shipping exposure"],tickers:["XOM","CVX","XLE"],lens:["XOM"]},
  CN:{flag:"🇨🇳",name:"China",cii:44,delta:0,signals:["Taiwan strait tension","Tech export controls"],tickers:["NVDA","TSM","AAPL"],lens:["NVDA","TSM"]},
};

const TD_SANCTIONS_MAP = {
  XOM:[{c:"Iran",r:"indirect",n:"Gulf ops / Hormuz exposure"}],
  CVX:[{c:"Iran",r:"indirect",n:"Middle East production"}],
  BP:[{c:"Russia",r:"direct",n:"Rosneft stake legacy / Russia ops"}],
  LMT:[{c:"Multiple",r:"export",n:"Defense export restrictions vary by program"}],
  RTX:[{c:"Multiple",r:"export",n:"Missile/defense export controls"}],
  NVDA:[{c:"China",r:"direct",n:"AI chip export restrictions"}],
  TSM:[{c:"China",r:"indirect",n:"Cross-strait supply chain risk"}],
  GS:[{c:"Russia",r:"indirect",n:"Deal flow restrictions post-2022"}],
  SLB:[{c:"Russia",r:"wind-down",n:"Operations wound down 2022"}],
};

const TD_COMMODITY_ROUTES = [
  {route:"Persian Gulf → Asia",choke:"Hormuz",share:"21% global oil",tickers:["XOM","CVX","XLE"]},
  {route:"Red Sea → Europe",choke:"Bab el-Mandeb",share:"12% trade flow",tickers:["BP","XOM"]},
  {route:"Gulf → Med",choke:"Suez",share:"30% container",tickers:["XLE"]},
  {route:"US Gulf → Atlantic",choke:"Panama",share:"6% LNG",tickers:["XLE","NG"]},
];

const TD_CONFLICT_EVENTS = [
  {t:"Iran",iso:"IR",h:"Hormuz STILL CLOSED — tanker fee imposed",src:"Intel",d:"1d",sev:"high"},
  {t:"Red Sea",iso:"YE",h:"Bab el-Mandeb transit down week-over-week",src:"Maritime",d:"2d",sev:"high"},
  {t:"Ukraine",iso:"UA",h:"Eastern front activity — UCDP GED events",src:"ACLED/UCDP",d:"3d",sev:"med"},
  {t:"Israel",iso:"IL",h:"Ceasefire window — expires Apr 22",src:"Geopolitical",d:"1d",sev:"med"},
  {t:"Taiwan",iso:"CN",h:"Strait patrol frequency elevated",src:"OSINT",d:"5d",sev:"low"},
];

const TD_GEO_SCENARIOS = {
  hormuz_close:{lbl:"Hormuz Closure",oil:25,spy:-4,tickers:["XOM","XLE","XAU","LMT"]},
  ceasefire_lapse:{lbl:"Ceasefire Expiry",oil:12,spy:-2,tickers:["WTI","LMT","XOM"]},
  cable_cut:{lbl:"Cable Cascade",oil:0,spy:-3,tickers:["META","GOOGL","NET"]},
  risk_off:{lbl:"Global Risk-Off",oil:-5,spy:-8,tickers:["XAU","TLT","XLE"]},
};

let _geoQuakes = [], _geoQuakeLoad = false, _geoDossierIso = null, _labGeoScenario = "hormuz_close";
let _lastConvergenceKey = "";

function _geoCpScore(cp) {
  // Live inputs only — never invent VIX=22 / oil % when unsynced
  const wtiC = liveChg("WTI");
  const vix = livePx("VIX");
  let adj = cp.base;
  if (cp.id === "hormuz" || cp.id === "bab") {
    if (wtiC != null) adj += Math.min(12, Math.abs(wtiC) * 2);
    if (vix != null && vix > 20) adj += 4;
  }
  return Math.min(99, Math.round(adj));
}

function _geoCpCol(s) { return s >= 70 ? "var(--rd)" : s >= 40 ? "var(--gd)" : "var(--gn)"; }

function _paintChokepointStrip() {
  let bar = document.getElementById("chokepointStrip");
  if (!bar) {
    bar = document.createElement("div");
    bar.id = "chokepointStrip";
    const anchor = document.getElementById("siteIntelBar");
    if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(bar, anchor.nextSibling);
    else document.getElementById("app")?.appendChild(bar);
  }
  const chips = TD_CHOKEPOINTS.map(cp => {
    const sc = _geoCpScore(cp);
    const col = _geoCpCol(sc);
    const wow = cp.wow >= 0 ? "+" + cp.wow : String(cp.wow);
    return `<button type="button" class="cp-chip" onclick="nav('geo')" title="${cp.full}">
      <span class="cp-name">${cp.name}</span>
      <span class="cp-score" style="color:${col}">${sc}</span>
      <span class="cp-wow" style="color:${cp.wow < 0 ? "var(--rd)" : "var(--gn)"}">${wow}%</span>
    </button>`;
  }).join("");
  bar.className = "chokepoint-strip";
  bar.innerHTML = `<div class="cp-strip-inner">
    <span class="cp-strip-lbl" onclick="nav('geo')">CHOKEPOINTS</span>
    <div class="cp-strip-track">${chips}</div>
    <button type="button" class="cp-strip-more" onclick="nav('geo')">GEO OPS →</button>
  </div>`;
  _syncDeskChrome();
}

function openCountryDossier(iso) {
  _geoDossierIso = iso;
  const ov = document.getElementById("geoDossierOv");
  if (!ov) return;
  ov.classList.remove("hide");
  ov.innerHTML = _renderCountryDossier(iso);
  _fxOverlayEnter(ov.querySelector(".geo-dossier-panel"));
}

function closeCountryDossier() {
  _geoDossierIso = null;
  document.getElementById("geoDossierOv")?.classList.add("hide");
}

function _renderCountryDossier(iso) {
  const d = TD_COUNTRY_DOSSIERS[iso];
  if (!d) return "";
  const col = d.cii >= 70 ? "var(--rd)" : d.cii >= 50 ? "var(--gd)" : "var(--gn)";
  const delta = d.delta > 0 ? "▲" + d.delta : d.delta < 0 ? "▼" + Math.abs(d.delta) : "─";
  const portHits = portfolio.filter(p => (d.tickers || []).includes(p.tk));
  const wlHits = getActiveWl().tickers.filter(t => (d.tickers || []).includes(t));
  return `<div class="geo-dossier-backdrop" onclick="closeCountryDossier()"></div>
  <div class="geo-dossier-panel">
    <div class="geo-dossier-hdr">
      <div><span class="geo-dossier-flag">${d.flag}</span><span class="geo-dossier-title">${d.name}</span><span class="geo-dossier-iso">${iso}</span></div>
      <button type="button" class="geo-dossier-x" onclick="closeCountryDossier()">✕</button>
    </div>
    <div class="geo-dossier-cii">
      <div class="geo-dossier-cii-val" style="color:${col}">${d.cii}</div>
      <div><div class="geo-dossier-cii-lbl">CII-LITE STRESS</div><div class="geo-dossier-cii-d" style="color:${d.delta > 0 ? "var(--rd)" : "var(--gn)"}">${delta} 24h</div></div>
    </div>
    <div class="geo-dossier-sec"><div class="geo-dossier-k">ACTIVE SIGNALS</div>${d.signals.map(s => `<div class="geo-dossier-sig">${s}</div>`).join("")}</div>
    <div class="geo-dossier-sec"><div class="geo-dossier-k">LINKED TICKERS</div><div class="geo-dossier-tks">${d.tickers.map(t => `<button type="button" class="geo-tk-chip" onclick="closeCountryDossier();openA('${t}')">${t}</button>`).join("")}</div></div>
    ${portHits.length ? `<div class="geo-dossier-sec geo-dossier-expo"><div class="geo-dossier-k">YOUR PORTFOLIO</div>${portHits.map(p => `<div class="geo-expo-row"><span>${p.tk}</span><span>${p.qty} units</span></div>`).join("")}</div>` : ""}
    ${wlHits.length ? `<div class="geo-dossier-sec"><div class="geo-dossier-k">WATCHLIST</div><div class="geo-dossier-tks">${wlHits.map(t => `<button type="button" class="geo-tk-chip" onclick="closeCountryDossier();openA('${t}')">${t}</button>`).join("")}</div></div>` : ""}
    <div class="geo-dossier-acts">
      <button type="button" class="geo-act-btn" onclick="runGeoLensBridge('${iso}')">⬢ Lens top exposures</button>
      <button type="button" class="geo-act-btn geo-act-gold" onclick="closeCountryDossier();nav('geo')">Open Geo Ops →</button>
    </div>
  </div>`;
}

function runGeoLensBridge(iso) {
  const d = TD_COUNTRY_DOSSIERS[iso];
  if (!d || !d.lens || !d.lens.length) { showToast("No lens targets for " + iso, "var(--gd)"); return; }
  closeCountryDossier();
  const tk = d.lens[0];
  openA(tk);
  setTimeout(function() { _setATab("cm"); runCommittee(tk); }, 400);
  showToast("Lens Engine → " + tk + " (" + d.name + " exposure)", "var(--bl)");
}

function _renderSanctionsWatch(tk) {
  const rows = TD_SANCTIONS_MAP[tk];
  if (!rows || !rows.length) return "";
  return `<div class="geo-sanctions-card">
    <div class="pro-feat-hdr"><div class="pro-feat-kicker">SANCTIONS & GEO EXPOSURE</div><span class="pro-feat-badge">Geo Ops</span></div>
    ${rows.map(r => `<div class="geo-sanctions-row"><span class="geo-sanctions-c">${r.c}</span><span class="geo-sanctions-r">${r.r}</span><span class="geo-sanctions-n">${r.n}</span></div>`).join("")}
  </div>`;
}

function _renderGeoMacroTiles() {
  const re = _computeRegimeEngine();
  // Live marks only — never paint "$—" or color VIX from string "—"
  const vixN = livePx("VIX");
  const dxyN = livePx("DXY");
  const oilN = livePx("WTI");
  const goldN = livePx("XAU");
  const tnxN = livePx("TNX");
  const tiles = [
    {l:"REGIME",v:re.label,c:re.col},
    {l:"VIX",v:vixN!=null?vixN.toFixed(1):"—",c:vixN==null?"var(--t3)":vixN>20?"var(--rd)":"var(--gn)"},
    {l:"DXY",v:dxyN!=null?dxyN.toFixed(2):"—",c:dxyN==null?"var(--t3)":"var(--bl)"},
    {l:"WTI",v:oilN!=null?"$"+oilN.toFixed(2):"—",c:oilN==null?"var(--t3)":"var(--gd)"},
    {l:"GOLD",v:goldN!=null?"$"+Math.round(goldN).toLocaleString():"—",c:goldN==null?"var(--t3)":"var(--gn)"},
    {l:"10Y",v:tnxN!=null?tnxN.toFixed(2)+"%":"—",c:tnxN==null?"var(--t3)":"var(--t2)"},
  ];
  return `<div class="geo-macro-tiles">${tiles.map(t => `<div class="geo-macro-tile"><div class="geo-macro-l">${t.l}</div><div class="geo-macro-v" style="color:${t.c}">${t.v}</div></div>`).join("")}</div>`;
}

function _geoEnergyRow(label, tk, fallbackTk) {
  // Prefer live primary; optional live fallback (never invent % from "—")
  let d = null, used = tk, via = "";
  if (liveSymbols.has(tk)) d = fp(tk);
  if ((!d || d.status === "unavailable") && fallbackTk && liveSymbols.has(fallbackTk)) {
    d = fp(fallbackTk);
    used = fallbackTk;
    via = " · via " + fallbackTk;
  }
  if (!d || d.status === "unavailable") {
    return `<div class="geo-energy-row"><span>${label}</span><span style="color:var(--t3)">—</span></div>`;
  }
  const chN = liveChg(used);
  const col = chN == null ? "var(--t3)" : chN > 0 ? "var(--gn)" : chN < 0 ? "var(--rd)" : "var(--t3)";
  const sign = chN != null && chN >= 0 ? "+" : "";
  return `<div class="geo-energy-row"><span>${label}${via}</span><span style="color:${col}">${d.p} (${chN != null ? sign + Number(chN).toFixed(2) : d.c}%)</span></div>`;
}

function _renderEnergyShockPanel() {
  const quakes = _geoQuakes.slice(0, 4);
  let qHtml = _geoQuakeLoad ? `<div class="geo-quake-load">Loading USGS…</div>` : !quakes.length
    ? `<div class="geo-quake-empty">No M4.5+ events (7d)</div>`
    : quakes.map(q => `<div class="geo-quake-row"><span class="geo-quake-m">M${(q.mag||0).toFixed(1)}</span><span class="geo-quake-p">${(q.place||"").slice(0,42)}</span></div>`).join("");
  return `<div class="gc geo-energy-card">
    <div class="pro-feat-hdr"><div class="pro-feat-kicker">ENERGY & PHYSICAL SHOCK</div><span class="pro-feat-badge">USGS · Live</span>
      <button onclick="_fetchGeoEarthquakes()" style="margin-left:auto;background:var(--b2);border:1px solid var(--gb);color:var(--t3);border-radius:5px;padding:2px 8px;font-family:var(--mn);font-size:8px;cursor:pointer">↻</button>
    </div>
    ${_geoEnergyRow("WTI", "WTI")}
    ${_geoEnergyRow("Brent", "BRENT", "WTI")}
    <div class="geo-quake-list">${qHtml}</div>
  </div>`;
}

function _renderCommodityExposureTable() {
  let h = `<div class="gc geo-commod-card"><div class="pro-feat-hdr"><div class="pro-feat-kicker">COMMODITY ROUTE EXPOSURE</div><span class="pro-feat-badge">Static registry</span></div><table class="geo-route-table"><thead><tr><th>Route</th><th>Choke</th><th>Share</th><th>Tickers</th></tr></thead><tbody>`;
  TD_COMMODITY_ROUTES.forEach(r => {
    h += `<tr><td>${r.route}</td><td>${r.choke}</td><td>${r.share}</td><td>${r.tickers.map(t => `<button type="button" class="geo-tk-chip sm" onclick="openA('${t}')">${t}</button>`).join("")}</td></tr>`;
  });
  return h + `</tbody></table></div>`;
}

function _renderConflictTimeline() {
  let h = `<div class="gc geo-conflict-card"><div class="pro-feat-hdr"><div class="pro-feat-kicker">CONFLICT TIMELINE</div><span class="pro-feat-badge">Intel fusion</span></div>`;
  TD_CONFLICT_EVENTS.forEach(e => {
    const col = e.sev === "high" ? "var(--rd)" : e.sev === "med" ? "var(--gd)" : "var(--t3)";
    h += `<div class="geo-conflict-row" onclick="openCountryDossier('${e.iso}')">
      <span class="geo-conflict-t" style="color:${col}">${e.t}</span><span class="geo-conflict-h">${e.h}</span><span class="geo-conflict-d">${e.d}</span></div>`;
  });
  return h + `</div>`;
}

function _renderPortfolioChokepointExposure() {
  if (!portfolio.length) return `<div class="geo-expo-hint">Add portfolio positions to see chokepoint exposure</div>`;
  const cpHits = {};
  portfolio.forEach(pos => {
    TD_CHOKEPOINTS.forEach(cp => {
      if (cp.tickers.includes(pos.tk)) {
        if (!cpHits[cp.id]) cpHits[cp.id] = { cp: cp, syms: [], val: 0 };
        cpHits[cp.id].syms.push(pos.tk);
        cpHits[cp.id].val += _portMark(pos).value;
      }
    });
  });
  const entries = Object.values(cpHits).sort((a, b) => b.val - a.val);
  if (!entries.length) return `<div class="geo-expo-hint">No direct chokepoint-linked holdings detected</div>`;
  const m = _calcPortRiskMetrics();
  let h = `<div class="gc geo-port-expo-card"><div class="pro-feat-hdr"><div class="pro-feat-kicker">PORTFOLIO CHOKEPOINT EXPOSURE</div><span class="pro-feat-badge">Route Explorer lite</span></div>`;
  entries.forEach(e => {
    const sc = _geoCpScore(e.cp);
    const stress = m ? Math.round(e.val * (m.beta || 1) * (sc / 100) * 0.12) : 0;
    h += `<div class="geo-port-expo-row"><div><span class="geo-port-expo-n">${e.cp.full}</span><span class="geo-port-expo-s" style="color:${_geoCpCol(sc)}">disruption ${sc}</span></div>
      <div class="geo-port-expo-r"><span>${e.syms.join(", ")}</span><span class="geo-port-expo-stress">stress −$${stress.toLocaleString()}</span></div></div>`;
  });
  return h + `</div>`;
}

function _renderGeoScenarioV2() {
  const sc = TD_GEO_SCENARIOS[_labGeoScenario] || TD_GEO_SCENARIOS.hormuz_close;
  const beta = _deskBeta(_labTk, 1);
  const oilImp = (sc.oil * 0.15 * beta).toFixed(1);
  const spyImp = (sc.spy * beta * 0.5).toFixed(1);
  const col = parseFloat(oilImp) >= 2 ? "var(--gn)" : parseFloat(oilImp) <= -2 ? "var(--rd)" : "var(--gd)";
  return `<div class="lab-geo-scenario">
    <div class="lab-panel-k">DISRUPTION SCENARIOS</div>
    <div class="geo-scenario-btns">${Object.entries(TD_GEO_SCENARIOS).map(([k, v]) => `<button type="button" class="geo-sc-btn${_labGeoScenario === k ? " on" : ""}" onclick="setLabGeoScenario('${k}')">${v.lbl}</button>`).join("")}</div>
    <div class="lab-proj-val" style="color:${col}">${parseFloat(oilImp) >= 0 ? "+" : ""}${oilImp}%</div>
    <div class="lab-proj-sub">${sc.lbl} · oil channel · β ${beta.toFixed(2)} · SPY est ${spyImp}%</div>
    <div class="geo-scenario-tks">${sc.tickers.map(t => `<button type="button" class="geo-tk-chip sm" onclick="setLabTicker('${t}')">${t}</button>`).join("")}</div>
  </div>`;
}

function setLabGeoScenario(k) {
  _labGeoScenario = k;
  const out = document.getElementById("lab-geo-scenario-out");
  if (out) out.innerHTML = _renderGeoScenarioV2();
  _refreshPageView();
}

function checkConvergenceAlerts() {
  const re = _computeRegimeEngine();
  const intel = _siteIntel.local || _computeLocalIntel(_siteIntel.surface || "pulse", { tk: selTk });
  const headline = (intel.headline || "").toLowerCase();
  // Live tape only — never treat unsynced "—" as 0% oil / VIX move
  const wtiChg = liveChg("WTI");
  const vixChg = liveChg("VIX");
  const geoKeywords = ["hormuz", "iran", "red sea", "ceasefire", "strike", "conflict", "sanction", "missile"];
  const geoHit = geoKeywords.some(k => headline.includes(k));
  const priceHit = (wtiChg != null && Math.abs(wtiChg) >= 1.5) || (vixChg != null && vixChg <= -5);
  const regimeHit = re.score < 45 || re.score > 65;
  const key = [geoHit, priceHit, regimeHit, headline.slice(0, 40)].join("|");
  if (geoHit && priceHit && regimeHit && key !== _lastConvergenceKey) {
    _lastConvergenceKey = key;
    smartAlerts.filter(a => a.type === "convergence" && a.active).forEach(() => {
      showToast("⬢ CONVERGENCE: geo headline + price move + regime shift", "var(--rd)");
    });
  }
}

async function _fetchGeoEarthquakes() {
  if (_geoQuakeLoad) return;
  _geoQuakeLoad = true;
  try {
    const res = await fetch("/api/geo?minmag=4.5&days=7", { signal: AbortSignal.timeout(12000) });
    if (res.ok) { const d = await res.json(); _geoQuakes = d.events || []; }
  } catch (e) { /* silent */ }
  _geoQuakeLoad = false;
  if (pg === "geo") renderMain();
}

function renderGeoOps() {
  _paintChokepointStrip();
  let h = _renderPgHdr("Geo Ops Center", "Chokepoints · country risk · convergence · portfolio route exposure");
  h += _renderSiteIntelCard("geo");
  h += `<div class="qa-row" style="grid-template-columns:repeat(3,1fr);margin-bottom:10px">
    <button class="qa-btn" onclick="openCountryDossier('IR')"><span class="qa-ico">🇮🇷</span><span>Iran</span></button>
    <button class="qa-btn" onclick="openCountryDossier('IL')"><span class="qa-ico">🇮🇱</span><span>Israel</span></button>
    <button class="qa-btn qa-gold" onclick="nav('port')"><span class="qa-ico">◎</span><span>Port Expo</span></button>
  </div>`;
  h += _renderGeoMacroTiles();
  h += `<div class="geo-ops-grid">`;
  h += _renderPortfolioChokepointExposure();
  h += _renderEnergyShockPanel();
  h += _renderConflictTimeline();
  h += _renderCommodityExposureTable();
  h += `</div>`;
  h += `<div class="gc geo-api-card"><div class="pro-feat-hdr"><div class="pro-feat-kicker">GEO TOOLS API</div><span class="pro-feat-badge">MCP-style</span></div>
    <div class="geo-api-paths"><code>/api/geo-tools?tool=chokepoints</code><code>/api/geo-tools?tool=country&amp;iso=IR</code><code>/api/geo-tools?tool=regime</code><code>/api/geo-tools?tool=portfolio_exposure&amp;symbols=XOM,CVX</code><code>/api/geo-tools?tool=scenarios</code></div>
    <div class="geo-api-hint">Premium required for portfolio_exposure · Use with Claude MCP or custom agents</div></div>`;
  h += `<div class="geo-country-grid"><div class="geo-country-k">COUNTRY DOSSIERS · tap to open</div><div class="geo-country-chips">`;
  Object.entries(TD_COUNTRY_DOSSIERS).forEach(([iso, d]) => {
    const col = d.cii >= 70 ? "var(--rd)" : d.cii >= 50 ? "var(--gd)" : "var(--gn)";
    h += `<button type="button" class="geo-country-chip" onclick="openCountryDossier('${iso}')"><span>${d.flag}</span><span>${d.name}</span><span style="color:${col}">${d.cii}</span></button>`;
  });
  h += `</div></div>`;
  return h;
}

function _initGeoOps() {
  _paintChokepointStrip();
  _fetchGeoEarthquakes();
  setInterval(_paintChokepointStrip, 60000);
  setInterval(checkConvergenceAlerts, 45000);
}

let lensHistory = [];
try { lensHistory = JSON.parse(localStorage.getItem("td_lens_hist") || "[]"); } catch (e) { lensHistory = []; }

function saveLensRun(entry) {
  const ts = entry.ts || new Date().toISOString();
  const day = String(ts).slice(0, 10);
  // One entry per ticker per day — stops Research Journal spam
  lensHistory = lensHistory.filter(e => !(e.ticker === entry.ticker && String(e.ts || "").slice(0, 10) === day));
  lensHistory.unshift({ ...entry, ts });
  if (lensHistory.length > 30) lensHistory.length = 30;
  localStorage.setItem("td_lens_hist", JSON.stringify(lensHistory));
  saveReason({ ticker: entry.ticker, thesis: entry.thesis, verdict: entry.verdict, ts, sc: entry.sc });
}

function _dedupeJournal(list) {
  const seen = new Set();
  const out = [];
  for (const r of list || []) {
    const key = `${r.ticker}|${String(r.ts || "").slice(0, 10)}|${r.verdict || ""}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(r);
  }
  return out;
}

function _renderLensJournal(limit) {
  const recent = _dedupeJournal(lensHistory.length ? lensHistory : reason);
  if (!recent.length) return `<div class="gc" style="padding:20px;text-align:center;border-left:3px solid var(--bl)"><div style="font-size:12px;color:var(--t2)">No lens runs yet</div><div style="font-size:10px;color:var(--t3);margin-top:6px">Open a ticker → Lenses tab → Run Lens Engine</div></div>`;
  let h = `<div class="gc" style="padding:0;overflow:hidden;border-left:3px solid var(--bl)">`;
  recent.slice(0, limit || 8).forEach((r, i) => {
    const vc = r.verdict === "IMPLEMENT" || r.verdict === "BUY" ? "var(--gn)" : r.verdict === "REJECT" || r.verdict === "SELL" ? "var(--rd)" : "var(--gd)";
    h += `<div style="padding:10px 14px;${i ? "border-top:1px solid var(--gb);" : ""}cursor:pointer" onclick="openA('${r.ticker}');_setATab('cm')">
      <div style="display:flex;justify-content:space-between;align-items:center"><span style="font-family:var(--mn);font-weight:800;font-size:12px">${r.ticker}</span><span style="font-family:var(--mn);font-size:9px;font-weight:700;color:${vc};padding:2px 8px;border:1px solid ${vc}40;border-radius:5px">${r.verdict || "MONITOR"}</span></div>
      <div style="font-size:10px;color:var(--t2);margin-top:4px;line-height:1.45">${(r.thesis || "").slice(0, 120)}${(r.thesis || "").length > 120 ? "…" : ""}</div>
      <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-top:4px">${new Date(r.ts).toLocaleDateString("en-GB", { day: "numeric", month: "short" })} · Score ${r.sc || "—"}${r.regime ? " · " + r.regime : ""}</div></div>`;
  });
  h += `</div>`;
  return h;
}

function _renderLensFeed() {
  const recent = lensHistory.length ? lensHistory : reason;
  if (!recent.length) return "";
  let h = `<div class="sec-label">Recent Lens Runs</div><div class="gc" style="padding:0;overflow:hidden;border-left:3px solid var(--bl)">`;
  recent.slice(0, 5).forEach((r, i) => {
    const vc = r.verdict === "IMPLEMENT" || r.verdict === "BUY" ? "var(--gn)" : r.verdict === "REJECT" || r.verdict === "SELL" ? "var(--rd)" : "var(--gd)";
    h += `<div style="padding:10px 14px;${i ? "border-top:1px solid var(--gb);" : ""}cursor:pointer" onclick="openA('${r.ticker}');_setATab('cm')">
      <div style="display:flex;justify-content:space-between;align-items:center"><span style="font-family:var(--mn);font-weight:800;font-size:12px">${r.ticker}</span><span style="font-family:var(--mn);font-size:9px;font-weight:700;color:${vc};padding:2px 8px;border:1px solid ${vc}40;border-radius:5px">${r.verdict || "MONITOR"}</span></div>
      <div style="font-size:10px;color:var(--t2);margin-top:4px;line-height:1.45">${(r.thesis || "").slice(0, 90)}${(r.thesis || "").length > 90 ? "…" : ""}</div></div>`;
  });
  h += `</div>`;
  return h;
}

// Brief and Gold Desk are deliberately SEPARATE surfaces:
//   Brief    = daily house view (regime, dispatch brief, archive, journal)
//   Gold Desk = weekly gold playbook + structure (renderGoldDesk)
// Do not collapse one into the other.
function renderBrief() {
  const hist = _getBriefHistory().filter(b => b.date !== (_brief?.date));
  const briefActs = `<div class="pg-hdr-actions" style="display:flex;gap:6px;flex-wrap:wrap">${_renderBriefPlayBtn(true)}${_brief ? `<button onclick="_exportBriefText()" class="hdr-act-btn">Copy</button><button onclick="_downloadBriefMd()" class="hdr-act-btn">↓ .md</button>` : ""}<button onclick="loadDispatchBrief(true)" class="hdr-act-btn hdr-act-gold">↻ Refresh</button></div>`;
  let h = _renderPgHdr("Dispatch Brief", "Daily house view", briefActs);
  h += _renderNeuralSessionStrip();
  h += _renderSiteIntelCard("brief");
  h += `<div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap">${_renderMorningRoutineBtn(true)}</div>`;

  h += _renderRegimeEngine();
  h += _renderDispatchBrief();

  if (hist.length) {
    h += `<div class="sec-label">Brief Archive</div>`;
    hist.slice(0, 7).forEach(b => {
      const vc = b.houseView === "Constructive" || b.houseView === "Opportunistic" ? "var(--gn)" : b.houseView === "Defensive" || b.houseView === "Cautious" ? "var(--rd)" : "var(--gd)";
      h += `<div class="gc gc-a" style="padding:12px;margin-bottom:6px;cursor:pointer" onclick="_viewArchivedBrief('${b.date}')">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px"><span style="font-family:var(--mn);font-size:9px;color:var(--t3)">${b.date}</span><span style="font-family:var(--mn);font-size:9px;font-weight:700;color:${vc}">${b.houseView || "Neutral"}</span></div>
        <div style="font-size:13px;font-weight:700;color:var(--tx)">${b.headline || "Market Brief"}</div>
        <div style="font-size:10px;color:var(--t2);margin-top:4px;line-height:1.45">${(b.summary || "").slice(0, 100)}…</div>
      </div>`;
    });
  }

  h += `<div class="sec-label">Research Journal</div>`;
  h += _renderLensJournal(8);

  const wl = getActiveWl();
  const topTk = wl.tickers[0] || [...A].sort((a, b) => b.sc - a.sc)[0]?.tk || "NVDA";
  h += `<div class="gc" style="padding:14px;margin-top:10px;border-left:3px solid var(--bl)">
    <div style="font-family:var(--mn);font-size:8px;color:var(--bl);letter-spacing:0.15em;margin-bottom:8px">NEXT STEP</div>
    <div style="font-size:12px;color:var(--t2);line-height:1.55;margin-bottom:10px">Run Lens Engine on your top conviction holding to stress-test your thesis against live data.</div>
    <button onclick="openA('${topTk}');_setATab('cm')" style="width:100%;background:var(--blG);color:var(--bl);border:1px solid rgba(79,142,247,0.25);border-radius:9px;padding:12px;font-family:var(--sn);font-size:12px;font-weight:700;cursor:pointer">⬢ Run Lens Engine on ${topTk}</button>
  </div>`;
  return h;
}

// ═══════════════════════════════════════════════════════════
// RESEARCH DATA
// ═══════════════════════════════════════════════════════════
const REPORTS = [
  {
    id:"spx2026",
    badge:"FLAGSHIP",
    kicker:"Year-End Outlook · 2026",
    headline:"Three <em>paths</em>, one tape",
    deck:"S&P 500 enters the final eight months from a fresh all-time high — but the dispersion of plausible year-end outcomes is the widest in recent memory. Equal-weighting three scenarios yields a blended target of ~6,800.",
    date:"Apr 26, 2026",
    readTime:"8 min",
    author:"Strategy Desk",
    tags:["SPX","Macro","Scenarios","VIX"]
  },
];

const SCENARIOS = {
  baseline:    { label:"Baseline", subtitle:"Iran truce extends · oil drifts · one Fed cut",
                 target:7650, pct:"+6.8%", range:"7,100 – 8,100",
                 eps:"$300–310", pe:"24.5×", vix:"13–18", y10:"3.90–4.40%",
                 narrative:"Pakistan-brokered ceasefire formalizes into a framework deal. Strait of Hormuz traffic normalizes, Brent drifts to the $80s. The Fed delivers a single 25-basis-point cut in the second half. EPS revisions stabilize at +18% growth, the multiple holds elevated on the disinflation glide.",
                 triggers:["Iran ceasefire formalized into framework","March–April PCE prints below 2.8%","Q1 EPS beats sustain 84% beat rate","Fed cuts once in H2 2026"],
                 color:"var(--bl)", colorG:"var(--blG)", vixAvg:15,
                 path:[7165,7250,7340,7400,7460,7510,7560,7610,7650],
                 vixPath:[18,16,15,14,15,16,15,14,13] },
  stagflation: { label:"Stagflation", subtitle:"Oil pins above $100 · Core PCE 3%+ · no cuts",
                 target:5050, pct:"−29.5%", range:"4,400 – 5,300",
                 eps:"$280–295", pe:"17–18×", vix:"25–32", y10:"4.75–5.50%",
                 narrative:"Iran ceasefire collapses or a fresh supply shock pins WTI above $100. Core PCE sticks at 3.0–3.5%. The Fed pauses cuts and prices in hike risk. Forward P/E compresses from 22× to 17×, while EPS gets cut 5–8%. Mega-cap concentration becomes the index's Achilles heel.",
                 triggers:["Strait of Hormuz re-closure","Core PCE accelerating to 3.3%+","CPI MoM > 0.4% sticky services","Powell-successor hawkish surprise","10Y breaching 5.0%"],
                 color:"var(--rd)", colorG:"var(--rdG)", vixAvg:27,
                 path:[7165,6750,6300,5950,5650,5350,5150,5050,5000],
                 vixPath:[22,25,28,27,26,28,30,27,25] },
  aiboom:      { label:"AI Boom", subtitle:"Hyperscaler 2026 capex > $660B · NDX leads",
                 target:7800, pct:"+8.9%", range:"7,500 – 8,200",
                 eps:"$315–325", pe:"23–24×", vix:"12–16", y10:"4.00–4.50%",
                 narrative:"MSFT, GOOGL, META, and AMZN combined 2026 capex confirmed at ~$665B — a 75% year-over-year increase. NVDA Data Center revenue runs above $200B. Mag 7 EPS growth at 25–28%, NDX outperforms SPX by 10–18 points. Multiple expands further on AI productivity narrative.",
                 triggers:["MSFT Azure growth >38% (Apr 29)","GOOGL/META capex guides raised","NVDA Q1 FY27 beats $78B guide","GE Vernova orders sustain 70%+","Stargate Phase 2 announced"],
                 color:"var(--gn)", colorG:"var(--gnG)", vixAvg:14,
                 path:[7165,7350,7500,7600,7670,7720,7770,7800,7800],
                 vixPath:[17,14,13,12,13,14,13,14,12] },
};

const SECTORS = [
  ["Energy (XLE)",          6,  25,   8],
  ["Tech (XLK)",           12, -30,  26],
  ["Comm Services (XLC)",  10, -28,  22],
  ["Cons Discretionary",    8, -32,  18],
  ["Industrials (XLI)",    10, -20,  13],
  ["Financials (XLF)",      7, -15,   8],
  ["Health Care (XLV)",     5,   0,   5],
  ["Cons Staples (XLP)",    4,   0,   3],
  ["Utilities (XLU)",       6,  -5,  12],
  ["Materials (XLB)",       6, -15,   7],
  ["Real Estate (XLRE)",    5, -25,   4],
];

const ASSUMPTIONS = [
  ["Brent oil",         "$78–88",         "$100–125",  "$70–85"],
  ["Core PCE YE26",     "2.4–2.7%",       "3.0–3.5%",  "2.3–2.6%"],
  ["Fed funds YE26",    "3.25–3.50%",     "3.50–3.75%","3.00–3.25%"],
  ["10Y UST",           "3.90–4.40%",     "4.75–5.50%","4.00–4.50%"],
  ["2026 EPS",          "$300–310",       "$280–295",  "$315–325"],
  ["Forward P/E",       "24.5×",          "17–18×",    "23–24×"],
  ["Iran / Hormuz",     "Truce extends",  "Re-closure","Truce extends"],
  ["Hyperscaler capex", "$580–620B",      "$540–580B", "$650–720B"],
  ["Dollar (DXY)",      "96–100",         "102–108",   "94–98"],
];

const MONTHS = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

// ═══════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════
const EVENTS=[
  {date:"Jun 25",ts:new Date("2026-06-25").getTime(),event:"CB Consumer Confidence",impact:"medium",cat:"Macro"},
  {date:"Jun 26",ts:new Date("2026-06-26").getTime(),event:"GDP Q1 — Final",impact:"high",cat:"Macro"},
  {date:"Jun 27",ts:new Date("2026-06-27").getTime(),event:"Core PCE Price Index (May)",impact:"high",cat:"Fed"},
  {date:"Jul 1",ts:new Date("2026-07-01").getTime(),event:"ISM Manufacturing PMI",impact:"medium",cat:"Macro"},
  {date:"Jul 3",ts:new Date("2026-07-03").getTime(),event:"ADP Jobs · Jobless Claims",impact:"medium",cat:"Macro"},
  {date:"Jul 4",ts:new Date("2026-07-04").getTime(),event:"Independence Day — US Market Closed",impact:"low",cat:"Holiday"},
  {date:"Jul 8",ts:new Date("2026-07-08").getTime(),event:"FOMC Minutes",impact:"high",cat:"Fed"},
  {date:"Jul 11",ts:new Date("2026-07-11").getTime(),event:"CPI — June",impact:"high",cat:"Macro"},
  {date:"Jul 15",ts:new Date("2026-07-15").getTime(),event:"JPM · WFC · C — Q2 Earnings",impact:"high",cat:"Earnings"},
  {date:"Jul 16",ts:new Date("2026-07-16").getTime(),event:"GS · MS — Q2 Earnings",impact:"high",cat:"Earnings"},
  {date:"Jul 22",ts:new Date("2026-07-22").getTime(),event:"GOOGL · TSLA — Q2 Earnings",impact:"high",cat:"Earnings"},
  {date:"Jul 23",ts:new Date("2026-07-23").getTime(),event:"MSFT · META — Q2 Earnings",impact:"high",cat:"Earnings"},
  {date:"Jul 24",ts:new Date("2026-07-24").getTime(),event:"AAPL · AMZN — Q2 Earnings",impact:"high",cat:"Earnings"},
  {date:"Jul 30",ts:new Date("2026-07-30").getTime(),event:"FOMC Rate Decision",impact:"high",cat:"Fed"},
  {date:"Jul 31",ts:new Date("2026-07-31").getTime(),event:"Core PCE — June",impact:"high",cat:"Fed"},
];

let pg="brief",selTk=null,aTab="ov",tick=0,comRes=null,comLoad=false,comErr="";
let selReport=null;
let blendW={baseline:33,stagflation:33,aiboom:34};
// Safe localStorage JSON read — one corrupt value must never blank the whole app
function _lsJson(raw,fallback){try{const v=JSON.parse(raw);return v==null?fallback:v;}catch(e){return fallback;}}
let watch=_lsJson(localStorage.getItem("td_w")||localStorage.getItem("qe_w"),[]);
let reason=_lsJson(localStorage.getItem("td_r")||localStorage.getItem("qe_r"),[]);
let portfolio=_lsJson(localStorage.getItem("td_port"),[]);
let alerts=_lsJson(localStorage.getItem("td_alerts"),[]);
// Drop corrupt NaN / zero targets so checkAlerts never stores fake triggers
if(Array.isArray(alerts)){
  const clean=alerts.filter(a=>a&&a.tk&&isFinite(+a.targetPrice)&&+a.targetPrice>0);
  if(clean.length!==alerts.length){alerts=clean;try{localStorage.setItem("td_alerts",JSON.stringify(alerts));}catch(e){}}
}else alerts=[];
let smartAlerts=_lsJson(localStorage.getItem("td_smart_alerts"),[]);
let _corrCache={},_corrLoading=false,_lastRegimeLabel=null;
let _labTk=localStorage.getItem("td_lab_tk")||"NVDA";
let _labRange=localStorage.getItem("td_lab_range")||"1mo";
let _labScenario=_lsJson(localStorage.getItem("td_lab_scenario"),{riskOn:40,neutral:35,riskOff:25});

// Premium feature state
let _portAiLoading=false,_portAiResult=null;
const _holdersCache={};
const _earAiResults={}; let _earAiLoading=false;

// ─── Multiple Watchlists ───
function _migrateWatchlists() {
  const legacy = localStorage.getItem('td_w') || localStorage.getItem('qe_w');
  if (legacy && !localStorage.getItem('td_wls')) {
    const tickers = _lsJson(legacy, []);
    localStorage.setItem('td_wls', JSON.stringify([{id:'wl1',name:'My Watchlist',tickers}]));
    localStorage.setItem('td_awl', 'wl1');
  }
}
_migrateWatchlists();
let watchlists = _lsJson(localStorage.getItem('td_wls'), [{id:'wl1',name:'My Watchlist',tickers:[]}]);
if (!Array.isArray(watchlists) || !watchlists.length) watchlists = [{id:'wl1',name:'My Watchlist',tickers:[]}];
let activeWlId = localStorage.getItem('td_awl') || 'wl1';
if (!watchlists[0]?.tickers?.length && !localStorage.getItem('td_wls')) {
  watchlists[0].tickers = ['SPY', 'NVDA', 'BTC', 'XAU', 'AAPL'];
  saveWatchlists();
}
function saveWatchlists(){localStorage.setItem('td_wls',JSON.stringify(watchlists));localStorage.setItem('td_awl',activeWlId);}
function getActiveWl(){const wl=watchlists.find(w=>w.id===activeWlId)||watchlists[0]||{id:'wl1',name:'My Watchlist',tickers:[]};if(!wl.notes)wl.notes={};return wl;}
/** Watchlist rows for UI — curated A[] meta when known, else dyn/lookup stub (never drop book names) */
function _wlAssetRows(wl){
  wl=wl||getActiveWl();
  return (wl.tickers||[]).filter(Boolean).map(tk=>{
    const a=A.find(x=>x.tk===tk);
    if(a)return a;
    const dyn=(typeof _dynMarkets!=="undefined"&&_dynMarkets[tk])?_dynMarkets[tk]:null;
    return{
      tk,nm:dyn?.name||tk,sc:50,se:"Neutral",ra:"—",cat:"Other",beta:1,pe:"—",mc:"—",
      th:"Lookup / live book name — no static desk thesis. Use Lab + Lens for your own view.",
      _dyn:true
    };
  });
}
function _deskAssetOrStub(tk){
  const a=A.find(x=>x.tk===tk);
  if(a)return a;
  const dyn=(typeof _dynMarkets!=="undefined"&&_dynMarkets[tk])?_dynMarkets[tk]:null;
  return{
    tk:tk||"—",nm:dyn?.name||tk||"—",sc:50,se:"Neutral",ra:"—",cat:"Other",beta:1,pe:"—",mc:"—",
    th:"Not in curated desk universe. Live prices when feed syncs — build thesis in Lab/Lens.",
    _dyn:true
  };
}
/** Numeric beta for models — never pass "—" into .toFixed / arithmetic */
function _deskBeta(aOrTk, fallback){
  const fb=fallback!=null&&isFinite(fallback)?fallback:1;
  const a=typeof aOrTk==="string"?_deskAssetOrStub(aOrTk):(aOrTk||null);
  const n=parseFloat(String(a?.beta??fb).replace(/x/i,""));
  return isFinite(n)&&n>0?n:fb;
}
function openWlNote(sym){
  const wl=getActiveWl();const note=wl.notes[sym]||'';const a=A.find(x=>x.tk===sym);
  let ov=document.getElementById('wln-ov');if(ov)ov.remove();
  ov=document.createElement('div');ov.id='wln-ov';
  ov.style.cssText='position:fixed;inset:0;z-index:900;background:rgba(0,0,0,0.75);display:flex;align-items:center;justify-content:center;backdrop-filter:blur(4px)';
  ov.innerHTML=`<div style="background:var(--b2);border:1px solid var(--b3);border-radius:14px;padding:20px;width:92%;max-width:420px;box-shadow:var(--shadow-lg)">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <div><div style="font-family:var(--mn);font-weight:800;font-size:14px;color:var(--gd)">${sym}</div>
        ${a?`<div style="font-family:var(--sn);font-size:10px;color:var(--t2);margin-top:2px">${a.nm}</div>`:''}
      </div>
      <button onclick="document.getElementById('wln-ov').remove()" style="background:var(--b3);border:none;color:var(--t2);border-radius:50%;width:28px;height:28px;cursor:pointer;font-size:16px">×</button>
    </div>
    <div style="font-family:var(--mn);font-size:8.5px;color:var(--t3);letter-spacing:0.15em;margin-bottom:6px">RESEARCH NOTE</div>
    <textarea id="wln-ta" placeholder="Long thesis, price targets, key catalysts, risk factors..."
      style="width:100%;height:110px;background:var(--b1);border:1px solid var(--b3);border-radius:8px;color:var(--tx);font-family:var(--sn);font-size:12px;line-height:1.5;padding:10px;resize:vertical;box-sizing:border-box;outline:none"
    >${note}</textarea>
    <div style="display:flex;gap:8px;margin-top:10px;justify-content:flex-end">
      <button onclick="document.getElementById('wln-ov').remove()" style="background:var(--b3);border:none;color:var(--t2);border-radius:7px;padding:8px 16px;font-family:var(--sn);font-size:12px;cursor:pointer">Cancel</button>
      <button onclick="saveWlNote('${sym}',document.getElementById('wln-ta').value)" style="background:var(--gd);border:none;color:var(--bg);border-radius:7px;padding:8px 20px;font-family:var(--sn);font-size:12px;font-weight:700;cursor:pointer">Save</button>
    </div>
  </div>`;
  document.body.appendChild(ov);
  setTimeout(()=>{const ta=document.getElementById('wln-ta');if(ta){ta.focus();ta.setSelectionRange(ta.value.length,ta.value.length);}},60);
}
function saveWlNote(sym,text){
  const wl=getActiveWl();
  if(text&&text.trim())wl.notes[sym]=text.trim();else delete wl.notes[sym];
  saveWatchlists();const ov=document.getElementById('wln-ov');if(ov)ov.remove();renderMain();
}
function createWatchlist(name){
  const nm=String(name||'').trim();
  if(nm.length<2){showToast('Name must be at least 2 characters','var(--gd)');return;}
  const id='wl'+Date.now();
  watchlists.push({id,name:nm,tickers:[],notes:{}});
  activeWlId=id;saveWatchlists();renderP4();
  if(typeof renderMain==='function'&&!IS_DESKTOP())renderMain();
  else if(document.getElementById('settingsOv')){openSettings();openSettings();}
  showToast('Created: '+nm,'var(--gn)');
}
function deleteWatchlist(id){
  if(watchlists.length<=1){showToast('Cannot delete last watchlist','var(--rd)');return;}
  watchlists=watchlists.filter(w=>w.id!==id);
  if(activeWlId===id)activeWlId=watchlists[0].id;
  saveWatchlists();renderP4();renderMain();
}
function renameWatchlist(id,name){
  const wl=watchlists.find(w=>w.id===id);
  if(wl){wl.name=name;saveWatchlists();renderP4();renderMain();}
}
function switchWatchlist(id){activeWlId=id;saveWatchlists();renderP4();renderMain();}
function addToWatchlist(tk,wlId){
  const raw=String(tk||"").trim();
  const sym=(typeof resolveInternalTicker==="function"?resolveInternalTicker(raw):"")||sanitizeTicker(raw)||raw.toUpperCase();
  if(!sym)return;
  const wl=watchlists.find(w=>w.id===(wlId||activeWlId));
  if(!wl)return;
  // Dedupe aliases (BTC-USD → BTC) so book stays clean
  if(wl.tickers.includes(sym)){showToast(sym+' already on '+wl.name,'var(--gd)');return;}
  wl.tickers.push(sym);saveWatchlists();renderP4();renderMain();showToast(sym+' added to '+wl.name,'var(--gn)');
}
function removeFromWatchlist(tk,wlId){
  const raw=String(tk||"").trim();
  const sym=(typeof resolveInternalTicker==="function"?resolveInternalTicker(raw):"")||sanitizeTicker(raw)||raw;
  const wl=watchlists.find(w=>w.id===(wlId||activeWlId));
  if(!wl)return;
  wl.tickers=wl.tickers.filter(t=>t!==sym&&t!==raw);saveWatchlists();renderP4();renderMain();
}

let toastTO=null;
// ─── Settings ───
let settingsOpen=false;
let panelVis=_lsJson(localStorage.getItem('td_pvis'),{p1:true,p2:true,p3:true,p4:true});
let updateFreq=parseInt(localStorage.getItem('td_freq')||'60');
let updatePaused=false;
let _priceInterval=null,_newsInterval=null;
function savePanelVis(){localStorage.setItem('td_pvis',JSON.stringify(panelVis));}
function saveFreq(){localStorage.setItem('td_freq',String(updateFreq));}
let newsFetching=false,newsLastFetch=null,newsError=null,newsFetchCount=0;
let newsFilter='all'; // all | book | world | stocks | commodities | fx | geopolitics | crypto | macro
let newsQ='';
let newsSort='relevant'; // relevant | latest
let newsFeedHealth={}; // src -> {ok, count, ts}
let _companyNewsCache={}; // tk -> {ts, items}
let _newsFocusTk=null; // company-news mode ticker
let priceFetching=false,priceLastFetch=null;
const NEWS_CACHE_KEY='td_news_cache_v3';
const NEWS_KEEP=80;
const NEWS_ALIASES={
  BTC:['bitcoin','btc'],ETH:['ethereum','ether','eth'],SOL:['solana','sol'],
  XAU:['gold','xau','bullion'],SLV:['silver'],WTI:['wti','crude','oil','brent'],
  BRENT:['brent','crude','oil'],SPX:['s&p','s&p 500','spx','sp500'],SPY:['spy','s&p'],
  IXIC:['nasdaq'],QQQ:['qqq','nasdaq'],DJIA:['dow','djia'],DXY:['dxy','dollar index'],
  VIX:['vix'],NVDA:['nvidia'],AAPL:['apple'],MSFT:['microsoft'],TSLA:['tesla'],
  AMZN:['amazon'],GOOGL:['google','alphabet'],META:['meta','facebook'],
  JPM:['jpmorgan','jp morgan'],XOM:['exxon'],COIN:['coinbase'],CRWD:['crowdstrike'],PLTR:['palantir'],
};

// ═══════════════════════════════════════════════════════════
// RSS FEED ENGINE
// ═══════════════════════════════════════════════════════════
const RSS_FEEDS = [
  // Markets / desk
  {url:"https://feeds.bbci.co.uk/news/business/rss.xml",src:"BBC Business",tier:1,cat:"Macro"},
  {url:"https://www.cnbc.com/id/100003114/device/rss/rss.html",src:"CNBC",tier:1,cat:"Stocks"},
  {url:"https://www.cnbc.com/id/20910258/device/rss/rss.html",src:"CNBC Markets",tier:1,cat:"Stocks"},
  {url:"https://www.cnbc.com/id/19854910/device/rss/rss.html",src:"CNBC Energy",tier:1,cat:"Commodities"},
  {url:"https://feeds.marketwatch.com/marketwatch/topstories",src:"MarketWatch",tier:2,cat:"Stocks"},
  {url:"https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5EGSPC,SPY,QQQ,IWM&region=US&lang=en-US",src:"Yahoo Markets",tier:1,cat:"Stocks"},
  {url:"https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",src:"NYT Business",tier:2,cat:"Macro"},
  {url:"https://www.theguardian.com/business/rss",src:"Guardian Biz",tier:2,cat:"Macro"},
  {url:"https://www.investing.com/rss/news_14.rss",src:"Investing Commodities",tier:1,cat:"Commodities"},
  {url:"https://www.investing.com/rss/news_1.rss",src:"Investing FX",tier:2,cat:"FX"},
  {url:"https://www.investing.com/rss/news_25.rss",src:"Investing Crypto",tier:2,cat:"Crypto"},
  {url:"https://feeds.finance.yahoo.com/rss/2.0/headline?s=CL=F,GC=F,SI=F,NG=F&region=US&lang=en-US",src:"Yahoo Futures",tier:1,cat:"Commodities"},
  {url:"https://www.coindesk.com/arc/outboundfeeds/rss/",src:"CoinDesk",tier:2,cat:"Crypto"},
  {url:"https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5EFTSE,%5EGDAXI,%5EN225,%5EHSI&region=US&lang=en-US",src:"Yahoo Global",tier:1,cat:"Stocks"},
  // World / regional (fintech hub density)
  {url:"https://feeds.bbci.co.uk/news/world/rss.xml",src:"BBC World",tier:1,cat:"Geopolitics"},
  {url:"https://feeds.bbci.co.uk/news/world/europe/rss.xml",src:"BBC Europe",tier:1,cat:"Geopolitics"},
  {url:"https://feeds.bbci.co.uk/news/world/asia/rss.xml",src:"BBC Asia",tier:1,cat:"Geopolitics"},
  {url:"https://feeds.bbci.co.uk/news/world/middle_east/rss.xml",src:"BBC MidEast",tier:1,cat:"Geopolitics"},
  {url:"https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml",src:"BBC Americas",tier:1,cat:"Geopolitics"},
  {url:"https://www.theguardian.com/world/rss",src:"Guardian World",tier:1,cat:"Geopolitics"},
  {url:"https://www.theguardian.com/uk-news/rss",src:"Guardian UK",tier:2,cat:"Geopolitics"},
  {url:"https://rss.nytimes.com/services/xml/rss/nyt/World.xml",src:"NYT World",tier:1,cat:"Geopolitics"},
  {url:"https://rss.nytimes.com/services/xml/rss/nyt/Europe.xml",src:"NYT Europe",tier:2,cat:"Geopolitics"},
  {url:"https://rss.nytimes.com/services/xml/rss/nyt/AsiaPacific.xml",src:"NYT Asia",tier:2,cat:"Geopolitics"},
  {url:"https://www.aljazeera.com/xml/rss/all.xml",src:"Al Jazeera",tier:1,cat:"Geopolitics"},
  {url:"https://feeds.npr.org/1004/rss.xml",src:"NPR World",tier:2,cat:"Geopolitics"},
  // CNN World removed 2026-08-13: rss.cnn.com no longer completes a TLS
  // handshake, so every load spent a request to earn a guaranteed 525.
].map((feed,id)=>({...feed,id:`f${id}`}));

// Heavier weights for specific tags so generic "market/stock" doesn't swallow oil/gold
const TAG_RULES = {
  "Geopolitics":{w:2,k:["war","military","ceasefire","iran","ukraine","russia","china","nato","sanctions","missile","conflict","troops","diplomacy","nuclear","strait","hormuz","israel","lebanon","houthi","geopolit"]},
  "Commodities":{w:3,k:["oil","crude","gold","silver","copper","wheat","natural gas","natgas","commodity","commodities","opec","brent","wti","energy price","barrel","bullion","lng","platinum","palladium","soybean","corn futures","mining","metals","iron ore","lithium","opec+","fuel","gasoline","diesel","heating oil"]},
  "Crypto":{w:3,k:["bitcoin","crypto","ethereum","btc","eth","blockchain","defi","nft","stablecoin","binance","coinbase","token","solana","altcoin"]},
  "Earnings":{w:2,k:["earnings","revenue","profit","quarterly","eps","beat estimates","missed estimates","guidance","results","dividend"]},
  "Central Bank":{w:2,k:["fed ","federal reserve","ecb","boe","boj","rate cut","rate hike","interest rate","monetary policy","inflation target","powell","lagarde","fomc"]},
  "Macro":{w:2,k:["gdp","cpi","inflation","unemployment","jobs report","pmi","recession","deficit","trade war","tariff","fiscal","payrolls"]},
  "Regulation":{w:2,k:["sec ","regulation","regulatory","compliance","finra","cftc","legislation","congress antitrust"]},
  "FX":{w:3,k:["forex","currency pair","exchange rate","dxy","usd/","eur/","gbp/","jpy","sterling","yen weak","dollar index","greenback"]},
  "Stocks":{w:1,k:["stock market","shares of","equities","ipo","s&p 500","nasdaq","dow jones","wall street"]},
};

function detectTag(text, feedCat){
  const low=(text||"").toLowerCase();
  let best=feedCat||"Stocks",bestScore=0;
  for(const[tag,cfg]of Object.entries(TAG_RULES)){
    let score=0;
    for(const kw of cfg.k){if(low.includes(kw))score+=cfg.w;}
    if(score>bestScore){bestScore=score;best=tag;}
  }
  // Feed category wins ties / weak keyword signal
  if(bestScore===0&&feedCat)return feedCat;
  if(bestScore>0&&bestScore<3&&feedCat&&feedCat!=="Stocks")return feedCat;
  return best;
}
const NEWS_CAT_KEYWORDS={
  commodities:["oil","crude","gold","silver","copper","wheat","opec","brent","wti","commodity","commodities","natural gas","lng","barrel","bullion","metals","mining","lithium","iron ore","gasoline","diesel","fuel","energy"],
  fx:["forex","currency","dxy","usd/","eur/","gbp/","jpy","sterling","yen","dollar index","greenback","exchange rate"],
  crypto:["bitcoin","crypto","ethereum","btc","eth","solana","blockchain","coinbase","binance","token","altcoin","defi"],
  geopolitics:["war","iran","ukraine","russia","china","nato","sanctions","missile","conflict","hormuz","israel","ceasefire","military","europe","asia","middle east","gaza","taiwan","kremlin","beijing","brussels","geopolit"],
  world:["war","iran","ukraine","russia","china","nato","sanctions","missile","conflict","hormuz","israel","ceasefire","military","europe","asia","middle east","gaza","taiwan","kremlin","beijing","brussels","geopolit","election","diplomacy","summit","border","refugee","coup"],
  macro:["gdp","cpi","inflation","fed","recession","unemployment","tariff","pmi","payrolls","fomc","central bank"],
  stocks:["stock","shares","s&p","nasdaq","dow","equities","ipo","earnings","wall street"],
};
const NEWS_WORLD_SRCS=new Set([
  "BBC World","BBC Europe","BBC Asia","BBC MidEast","BBC Americas",
  "Guardian World","Guardian UK","NYT World","NYT Europe","NYT Asia",
  "Al Jazeera","NPR World","CNN World"
]);

function detectImpact(text){
  const low=text.toLowerCase();
  const highWords=["breaking","war","ceasefire","crash","surge","plunge","record","crisis","emergency","attack","strike","sanction","nuclear"];
  const medWords=["rise","fall","cut","hike","beat","miss","warning","concern","rally","drop"];
  for(const w of highWords){if(low.includes(w))return"high";}
  for(const w of medWords){if(low.includes(w))return"medium";}
  return"low";
}

function parseRSSXML(xmlText,feedMeta){
  const items=[];
  const parser=new DOMParser();
  const doc=parser.parseFromString(xmlText,"text/xml");
  const entries=doc.querySelectorAll("item, entry");
  entries.forEach(entry=>{
    const title=(entry.querySelector("title")?.textContent||"").trim();
    const pubDate=entry.querySelector("pubDate, published, updated")?.textContent;
    const linkEl=entry.querySelector("link");
    const link=(linkEl?.getAttribute("href")||linkEl?.textContent||entry.querySelector("guid")?.textContent||"").trim();
    const desc=(entry.querySelector("description, summary, content")?.textContent||"").replace(/<[^>]*>/g,"").trim().slice(0,200);
    if(!title)return;
    const date=pubDate?new Date(pubDate):new Date();
    const hours=String(date.getHours()).padStart(2,"0");
    const mins=String(date.getMinutes()).padStart(2,"0");
    const tag=detectTag(title+" "+desc,feedMeta.cat);
    const imp=detectImpact(title);
    items.push({
      t:`${hours}:${mins}`,
      x:title.length>120?title.slice(0,117)+"...":title,
      desc:desc||"",
      tg:tag,im:imp,src:feedMeta.src,tier:feedMeta.tier,cat:feedMeta.cat,ts:date.getTime(),
      link:link.startsWith("http")?link:_newsLink({x:title})
    });
  });
  return items;
}

async function fetchViaServerProxy(feed){
  try{
    const res=await fetch(`/api/rss-feed?feed=${encodeURIComponent(feed.id)}`,{signal:AbortSignal.timeout(12000)});
    if(!res.ok)return null;
    const text=await res.text();
    if(!text||!text.includes("<"))return null;
    const items=parseRSSXML(text,feed);
    return items.length?items:null;
  }catch(e){return null;}
}

async function fetchSingleFeed(feed){
  // Keep all feeds same-origin. Third-party CORS policies are inconsistent and
  // should never surface as browser errors in a launch-facing product.
  return (await fetchViaServerProxy(feed)) || [];
}

// ─── Finnhub general news endpoint (via /api/finnhub proxy) ───
async function fetchFinnhubNews(){
  const cats=["general","forex","crypto"];
  const allItems=[];
  // Parallel cats — sequential was 3× timeout risk and slow newsroom on mobile
  const results=await Promise.allSettled(cats.map(async cat=>{
    const res=await fetch(`/api/finnhub?endpoint=news&category=${cat}`,
      {signal:AbortSignal.timeout(12000)});
    if(res.status===429)throw Object.assign(new Error("rate"),{code:429,cat});
    if(!res.ok)throw new Error("http "+res.status);
    const items=await res.json();
    return {cat,items:Array.isArray(items)?items:[]};
  }));
  let rateLimited=false;
  results.forEach(r=>{
    if(r.status==="rejected"){
      const cat=r.reason?.cat||"general";
      if(r.reason?.code===429){rateLimited=true;newsError="Finnhub rate limit — retrying next cycle";}
      newsFeedHealth["Finnhub·"+cat]={ok:false,count:0,ts:Date.now()};
      return;
    }
    const {cat,items}=r.value;
    items.slice(0,8).forEach(it=>{
      if(!it.headline)return;
      const date=new Date((it.datetime||0)*1000);
      const hours=String(date.getHours()).padStart(2,"0");
      const mins=String(date.getMinutes()).padStart(2,"0");
      const tag=detectTag(it.headline+" "+(it.summary||""));
      const imp=detectImpact(it.headline);
      allItems.push({
        t:`${hours}:${mins}`,
        x:it.headline.length>120?it.headline.slice(0,117)+"...":it.headline,
        desc:(it.summary||"").replace(/<[^>]*>/g,"").trim().slice(0,200),
        tg:tag,im:imp,
        src:it.source||"Finnhub",
        tier:1,
        ts:date.getTime()||Date.now(),
        link:(it.url&&it.url.startsWith("http"))?it.url:_newsLink({x:it.headline})
      });
    });
    newsFeedHealth["Finnhub·"+cat]={ok:true,count:Math.min(items.length,8),ts:Date.now()};
  });
  if(rateLimited&&!allItems.length)return [];
  return allItems;
}

function _saveNewsCache(){
  try{
    sessionStorage.setItem(NEWS_CACHE_KEY,JSON.stringify({
      ts:Date.now(),
      NEWS:NEWS.slice(0,NEWS_KEEP),
      health:newsFeedHealth
    }));
  }catch(e){}
}
function _loadNewsCache(){
  try{
    const raw=sessionStorage.getItem(NEWS_CACHE_KEY);
    if(!raw)return false;
    const d=JSON.parse(raw);
    if(!d?.ts||Date.now()-d.ts>30*60*1000)return false;
    if(!Array.isArray(d.NEWS)||!d.NEWS.length)return false;
    NEWS=d.NEWS;
    if(d.health)newsFeedHealth=d.health;
    newsLastFetch=new Date(d.ts);
    return true;
  }catch(e){return false;}
}

async function fetchLiveNews(){
  if(updatePaused)return;
  newsFetching=true;newsError=null;renderStatus();
  const _mnScroll=document.getElementById('main')?.scrollTop||0;
  const _p2Scroll=document.getElementById('p2body')?.scrollTop||0;
  try{
    let allItems=[];
    const health={};
    // Fetch ALL RSS feeds (no random drop)
    const results=await Promise.allSettled(RSS_FEEDS.map(async f=>{
      const items=await fetchSingleFeed(f);
      health[f.src]={ok:!!(items&&items.length),count:items?.length||0,ts:Date.now()};
      return items||[];
    }));
    results.forEach(r=>{if(r.status==="fulfilled"&&r.value?.length)allItems.push(...r.value);});
    // Always supplement Finnhub
    const fh=await fetchFinnhubNews();
    if(fh.length)allItems.push(...fh);
    Object.assign(newsFeedHealth,health);

    if(allItems.length>0){
      const seen=new Set();
      allItems=allItems.filter(item=>{
        const key=(item.x||"").toLowerCase().replace(/[^a-z0-9]/g,"").slice(0,48);
        if(!key||seen.has(key))return false;
        seen.add(key);return true;
      });
      allItems.sort((a,b)=>b.ts-a.ts);
      NEWS=allItems.slice(0,NEWS_KEEP);
      newsLastFetch=new Date();newsFetchCount++;
      _saveNewsCache();
      newsError=null;
    } else if(NEWS.length===0){
      if(!_loadNewsCache())newsError="No feeds reachable — retry with ⟳";
    } else {
      newsError="Refresh failed — showing previous batch";
    }
  }catch(e){newsError="News fetch error — retrying next cycle";}
  newsFetching=false;renderStatus();_syncTapePulse();

  // Re-render news surfaces without killing scroll / hard-resetting Android
  if(pg==="news"){
    if(typeof _paintNewsListOnly==="function"&&document.getElementById("news-list-body")){
      _paintNewsListOnly(true);
      const mn=document.getElementById('main');
      if(mn&&_mnScroll>40)requestAnimationFrame(()=>{mn.scrollTop=_mnScroll;});
    }else{
      renderMain();
      const mn=document.getElementById('main');
      if(mn&&_mnScroll>40)requestAnimationFrame(()=>{mn.scrollTop=_mnScroll;});
    }
  }else if(pg==="dash"&&_mnScroll<100){
    if(!MOBILE())renderMain();
    else{_patchLiveDataIfNeeded();_patchCuratedPrices();}
  }
  if(IS_DESKTOP()&&!termSelTk&&!_dynTk){
    renderP2();
    const p2=document.getElementById('p2body');
    if(p2&&_p2Scroll>20)requestAnimationFrame(()=>{p2.scrollTop=_p2Scroll;});
  }
}

// ═══════════════════════════════════════════════════════════
// LIVE PRICE FETCH
// ─ US Stocks:  Finnhub (real-time, native CORS)
// ─ Crypto:     CoinGecko (native CORS, no key)
// ─ Indices/Commodities/FX: Yahoo Finance (via server-side function)
// ═══════════════════════════════════════════════════════════

// Finnhub coverage:
//  ─ US stocks: real-time
//  ─ Indices: NOT available on free tier — we use ETF proxies (SPY, DIA, QQQ, etc.)
//  ─ Commodities/FX/VIX: NOT directly available — we use ETF/proxy tickers
// Mapping: dashboard ticker → (Finnhub symbol, display label, is_etf_proxy)
const FH_SYMBOLS = {
  // Indices via tracking ETFs (free-tier accessible)
  SPX:  {sym:"SPY",  proxy:true,  scale:10},   // SPY × 10 ≈ S&P 500 level
  DJIA: {sym:"DIA",  proxy:true,  scale:100},  // DIA × 100 ≈ Dow level
  IXIC: {sym:"QQQ",  proxy:true,  scale:50},   // QQQ × 50 ≈ Nasdaq level
  FTSE: {sym:"EWU",  proxy:true,  scale:1},    // UK ETF — show ETF price
  DAX:  {sym:"EWG",  proxy:true,  scale:1},    // Germany ETF
  N225: {sym:"EWJ",  proxy:true,  scale:1},    // Japan ETF
  NSEI: {sym:"INDA", proxy:true,  scale:1},    // India ETF
  HSI:  {sym:"EWH",  proxy:true,  scale:1},    // Hong Kong ETF
  // Real US stocks
  AAPL: {sym:"AAPL", proxy:false, scale:1},
  NVDA: {sym:"NVDA", proxy:false, scale:1},
  XOM:  {sym:"XOM",  proxy:false, scale:1},
  MSFT: {sym:"MSFT", proxy:false, scale:1},
  AVGO: {sym:"AVGO", proxy:false, scale:1},
  TSLA: {sym:"TSLA", proxy:false, scale:1},
  // Commodity ETF proxies
  WTI:  {sym:"USO",  proxy:true,  scale:1},    // Oil ETF
  XAU:  {sym:"GLD",  proxy:true,  scale:1},    // Gold ETF
  // New US stocks
  AMZN: {sym:"AMZN", proxy:false, scale:1},
  GOOGL:{sym:"GOOGL",proxy:false, scale:1},
  META: {sym:"META", proxy:false, scale:1},
  JPM:  {sym:"JPM",  proxy:false, scale:1},
  GS:   {sym:"GS",   proxy:false, scale:1},
  AMD:  {sym:"AMD",  proxy:false, scale:1},
  // FX via ETF proxies
  EURUSD:{sym:"FXE", proxy:true, scale:1},
  GBPUSD:{sym:"FXB", proxy:true, scale:1},
  USDJPY:{sym:"YCL", proxy:true, scale:1},
  // Additional commodities
  SLV:  {sym:"SLV",  proxy:true, scale:1},
  NG:   {sym:"UNG",  proxy:true, scale:1},
  // FX & VIX ETF proxies
  DXY:  {sym:"UUP",  proxy:true,  scale:1},    // Dollar bullish ETF
  VIX:  {sym:"VXX",  proxy:true,  scale:1},    // VIX short-term futures ETF
  // Additional stocks — routed via Yahoo Finance batch (proxy:true)
  // to avoid Finnhub rate limit (60 calls/min). All have YAHOO_SYMBOLS entries.
  NFLX: {sym:"NFLX", proxy:true, scale:1},
  DIS:  {sym:"DIS",  proxy:true, scale:1},
  V:    {sym:"V",    proxy:true, scale:1},
  MA:   {sym:"MA",   proxy:true, scale:1},
  PYPL: {sym:"PYPL", proxy:true, scale:1},
  CRM:  {sym:"CRM",  proxy:true, scale:1},
  ORCL: {sym:"ORCL", proxy:true, scale:1},
  ADBE: {sym:"ADBE", proxy:true, scale:1},
  INTC: {sym:"INTC", proxy:true, scale:1},
  QCOM: {sym:"QCOM", proxy:true, scale:1},
  MU:   {sym:"MU",   proxy:true, scale:1},
  CSCO: {sym:"CSCO", proxy:true, scale:1},
  NOW:  {sym:"NOW",  proxy:true, scale:1},
  PANW: {sym:"PANW", proxy:true, scale:1},
  CRWD: {sym:"CRWD", proxy:true, scale:1},
  PLTR: {sym:"PLTR", proxy:true, scale:1},
  COIN: {sym:"COIN", proxy:true, scale:1},
  UBER: {sym:"UBER", proxy:true, scale:1},
  SHOP: {sym:"SHOP", proxy:true, scale:1},
  SNOW: {sym:"SNOW", proxy:true, scale:1},
  RIVN: {sym:"RIVN", proxy:true, scale:1},
  F:    {sym:"F",    proxy:true, scale:1},
  GM:   {sym:"GM",   proxy:true, scale:1},
  BA:   {sym:"BA",   proxy:true, scale:1},
  CAT:  {sym:"CAT",  proxy:true, scale:1},
  DE:   {sym:"DE",   proxy:true, scale:1},
  NKE:  {sym:"NKE",  proxy:true, scale:1},
  SBUX: {sym:"SBUX", proxy:true, scale:1},
  MCD:  {sym:"MCD",  proxy:true, scale:1},
  JNJ:  {sym:"JNJ",  proxy:true, scale:1},
  UNH:  {sym:"UNH",  proxy:true, scale:1},
  PFE:  {sym:"PFE",  proxy:true, scale:1},
  LLY:  {sym:"LLY",  proxy:true, scale:1},
  ABBV: {sym:"ABBV", proxy:true, scale:1},
  MRK:  {sym:"MRK",  proxy:true, scale:1},
  WMT:  {sym:"WMT",  proxy:true, scale:1},
  COST: {sym:"COST", proxy:true, scale:1},
  HD:   {sym:"HD",   proxy:true, scale:1},
  BAC:  {sym:"BAC",  proxy:true, scale:1},
  WFC:  {sym:"WFC",  proxy:true, scale:1},
  C:    {sym:"C",    proxy:true, scale:1},
  BLK:  {sym:"BLK",  proxy:true, scale:1},
  ISRG: {sym:"ISRG", proxy:true, scale:1},
  TSM:  {sym:"TSM",  proxy:true, scale:1},
  ASML: {sym:"ASML", proxy:true, scale:1},
  NVO:  {sym:"NVO",  proxy:true, scale:1},
  SAP:  {sym:"SAP",  proxy:true, scale:1},
  BABA: {sym:"BABA", proxy:true, scale:1},
  BP:   {sym:"BP",   proxy:true, scale:1},
  SHEL: {sym:"SHEL", proxy:true, scale:1},
  // New US stocks
  ARM:  {sym:"ARM",  proxy:true, scale:1},
  SMCI: {sym:"SMCI", proxy:true, scale:1},
  MRVL: {sym:"MRVL", proxy:true, scale:1},
  KO:   {sym:"KO",   proxy:true, scale:1},
  PEP:  {sym:"PEP",  proxy:true, scale:1},
  PG:   {sym:"PG",   proxy:true, scale:1},
  ABNB: {sym:"ABNB", proxy:true, scale:1},
  DASH: {sym:"DASH", proxy:true, scale:1},
  BRKB: {sym:"BRK-B", proxy:true, scale:1},
  ACN:  {sym:"ACN",  proxy:true, scale:1},
  SONY: {sym:"SONY", proxy:true, scale:1},
  VALE: {sym:"VALE", proxy:true, scale:1},
  RIO:  {sym:"RIO",  proxy:true, scale:1},
  INFY: {sym:"INFY", proxy:true, scale:1},
  // New commodities
  COFFEE:{sym:"KC=F", proxy:true, scale:1},
  PLAT:  {sym:"PL=F", proxy:true, scale:1},
  COCOA: {sym:"CC=F", proxy:true, scale:1},
  // Additional global indices
  CAC:   {sym:"^FCHI", proxy:true, scale:1},
  ASX200:{sym:"^AXJO", proxy:true, scale:1},
  KOSPI: {sym:"^KS11", proxy:true, scale:1},
  // More US large-cap
  TMO:{sym:"TMO",proxy:true,scale:1}, ABT:{sym:"ABT",proxy:true,scale:1},
  PM: {sym:"PM", proxy:true,scale:1}, NEE:{sym:"NEE",proxy:true,scale:1},
  RTX:{sym:"RTX",proxy:true,scale:1}, HON:{sym:"HON",proxy:true,scale:1},
  T:  {sym:"T",  proxy:true,scale:1}, VZ: {sym:"VZ", proxy:true,scale:1},
  MS: {sym:"MS", proxy:true,scale:1}, SCHW:{sym:"SCHW",proxy:true,scale:1},
  TXN:{sym:"TXN",proxy:true,scale:1}, AMAT:{sym:"AMAT",proxy:true,scale:1},
  LRCX:{sym:"LRCX",proxy:true,scale:1}, REGN:{sym:"REGN",proxy:true,scale:1},
  AMGN:{sym:"AMGN",proxy:true,scale:1}, CVX:{sym:"CVX",proxy:true,scale:1},
  COP:{sym:"COP",proxy:true,scale:1}, INTU:{sym:"INTU",proxy:true,scale:1},
  ADSK:{sym:"ADSK",proxy:true,scale:1}, NET:{sym:"NET",proxy:true,scale:1},
  DDOG:{sym:"DDOG",proxy:true,scale:1}, ZS:{sym:"ZS",proxy:true,scale:1},
  UPS:{sym:"UPS",proxy:true,scale:1}, LOW:{sym:"LOW",proxy:true,scale:1},
  DUK:{sym:"DUK",proxy:true,scale:1},
  // More international ADRs
  TM: {sym:"TM", proxy:true,scale:1}, NVS:{sym:"NVS",proxy:true,scale:1},
  UL: {sym:"UL", proxy:true,scale:1}, DEO:{sym:"DEO",proxy:true,scale:1},
  // More FX
  USDMXN:{sym:"MXN=X",  proxy:true,scale:1},
  USDBRL:{sym:"BRL=X",  proxy:true,scale:1},
  USDINR:{sym:"INR=X",  proxy:true,scale:1},
  // More commodities
  OJ:      {sym:"OJ=F",  proxy:true,scale:1},
  LUMBER:  {sym:"LBS=F", proxy:true,scale:1},
  PALLADIUM:{sym:"PA=F", proxy:true,scale:1},
  // Additional FX pairs — via Yahoo Finance
  AUDUSD:{sym:"AUDUSD=X", proxy:true, scale:1},
  USDCAD:{sym:"CAD=X",    proxy:true, scale:1},
  USDCHF:{sym:"CHF=X",    proxy:true, scale:1},
  NZDUSD:{sym:"NZDUSD=X", proxy:true, scale:1},
  EURGBP:{sym:"EURGBP=X", proxy:true, scale:1},
  // Additional commodities — via Yahoo Finance
  COPPER:{sym:"HG=F",  proxy:true, scale:1},
  WHEAT: {sym:"ZW=F",  proxy:true, scale:1},
  CORN:  {sym:"ZC=F",  proxy:true, scale:1},
  USDBRL:{sym:"BRL=X", proxy:true, scale:1},
  LUMBER:{sym:"LBS=F", proxy:true, scale:1},
  // ETFs, indices & sector ETFs
  SPY:{sym:"SPY",proxy:true,scale:1}, QQQ:{sym:"QQQ",proxy:true,scale:1},
  IWM:{sym:"IWM",proxy:true,scale:1}, RUT:{sym:"^RUT",proxy:true,scale:1},
  EEM:{sym:"EEM",proxy:true,scale:1}, SOXX:{sym:"SOXX",proxy:true,scale:1},
  TLT:{sym:"TLT",proxy:true,scale:1}, ARKK:{sym:"ARKK",proxy:true,scale:1},
  TNX:{sym:"^TNX",proxy:true,scale:1},
  XLK:{sym:"XLK",proxy:true,scale:1}, XLC:{sym:"XLC",proxy:true,scale:1},
  XLY:{sym:"XLY",proxy:true,scale:1}, XLF:{sym:"XLF",proxy:true,scale:1},
  XLV:{sym:"XLV",proxy:true,scale:1}, XLE:{sym:"XLE",proxy:true,scale:1},
  XLI:{sym:"XLI",proxy:true,scale:1}, XLP:{sym:"XLP",proxy:true,scale:1},
  XLB:{sym:"XLB",proxy:true,scale:1}, XLU:{sym:"XLU",proxy:true,scale:1},
  XLRE:{sym:"XLRE",proxy:true,scale:1},
  // Thematic & energy
  RKLB:{sym:"RKLB",proxy:true,scale:1}, HOOD:{sym:"HOOD",proxy:true,scale:1},
  MSTR:{sym:"MSTR",proxy:true,scale:1}, GME:{sym:"GME",proxy:true,scale:1},
  SPOT:{sym:"SPOT",proxy:true,scale:1}, LMT:{sym:"LMT",proxy:true,scale:1},
  BMY:{sym:"BMY",proxy:true,scale:1}, GILD:{sym:"GILD",proxy:true,scale:1},
  ENPH:{sym:"ENPH",proxy:true,scale:1}, FSLR:{sym:"FSLR",proxy:true,scale:1},
  EOG:{sym:"EOG",proxy:true,scale:1}, SLB:{sym:"SLB",proxy:true,scale:1},
  SO:{sym:"SO",proxy:true,scale:1}, PLD:{sym:"PLD",proxy:true,scale:1},
  AMT:{sym:"AMT",proxy:true,scale:1}, EQIX:{sym:"EQIX",proxy:true,scale:1},
  SPG:{sym:"SPG",proxy:true,scale:1}, O:{sym:"O",proxy:true,scale:1},
  VRTX:{sym:"VRTX",proxy:true,scale:1},
  BRENT:{sym:"BZ=F",proxy:true,scale:1}, URA:{sym:"URA",proxy:true,scale:1},
  EURJPY:{sym:"EURJPY=X",proxy:true,scale:1},
  GBPJPY:{sym:"GBPJPY=X",proxy:true,scale:1},
};

// For symbols that we want to display as the underlying index level (not ETF price),
// we keep these display anchors so e.g. SPY $456 shows as ~SPX 6,820.
// Anchor = (dashboard_target_level / etf_price_at_init). Computed lazily on first fetch.
const DISPLAY_ANCHORS = {
  SPX:  null, DJIA: null, IXIC: null,
};

// ETF anchor seeds — approximate ratios so that ETF×ratio ≈ index level
// These get auto-calibrated on first successful fetch
const SEED_ANCHORS = {SPX:15.0, DJIA:107.0, IXIC:50.0};

let priceFetchCount=0,priceErrorCount=0;
let liveSymbols=new Set(); // symbols with confirmed feed data (never show seed as live)
let liveQuoteTs={}; // tk -> epoch ms last successful quote
let liveQuoteSrc={}; // tk -> yahoo | coingecko | finnhub | twelve-data | session-cache
let liveQuoteMarketClosed={}; // tk -> provider reported the cash session closed
let _priceFetchAttempted=false;
let _stripeMode=null; // null | "test" | "live" | "unknown"
const PRICE_CACHE_KEY="td_price_cache_v2";
const PRICE_CACHE_MAX_AGE=5*60*1000;
const PRICE_STALE_MS=3*60*1000; // >3m since last tick → STALE badge
const PRICE_PRIORITY=[
  "SPX","DJIA","IXIC","SPY","QQQ","RUT","VIX","DXY",
  "AAPL","NVDA","MSFT","TSLA","AMZN","GOOGL","META",
  "BTC","ETH","SOL","XAU","WTI","BRENT","NG","COPPER","SLV","EURUSD","USDJPY",
  "JPM","GS","XOM","COIN","MSTR","FTSE","DAX","N225","HSI","NSEI",
];
// Cross-asset core from Twelve Data's Basic plan. Eight symbols is the
// per-minute credit ceiling; the server always fetches this same set
// through one 15-minute shared cache (768 credits/day). MSFT/TSLA/AMZN
// and extra FX stay on delayed Yahoo so gold/crypto/ETFs can be live.
const TWELVE_DATA_SYMBOLS = Object.freeze({
  AAPL: "AAPL", NVDA: "NVDA",
  SPY: "SPY", QQQ: "QQQ",
  XAU: "XAU/USD", EURUSD: "EUR/USD",
  BTC: "BTC/USD", ETH: "ETH/USD",
});
const TWELVE_DATA_CACHE_WINDOW_MS = 16 * 60 * 1000;

function _providerTimestampMs(q) {
  const raw = Number(q?.ts ?? q?.fetchedAt);
  if (!Number.isFinite(raw) || raw <= 0) return null;
  const ms = raw < 10_000_000_000 ? raw * 1000 : raw;
  if (ms > Date.now() + 60_000) return null;
  return ms;
}

function _canReplaceQuote(tk, source) {
  const incoming = String(source || "");
  const current = liveQuoteSrc[tk] || "";
  const freshTwelveData = current === "twelve-data"
    && Date.now() - (liveQuoteTs[tk] || 0) <= TWELVE_DATA_CACHE_WINDOW_MS;
  if (freshTwelveData && incoming !== "twelve-data") return false;
  if (tk === "XAU" && incoming === "yahoo" && current.startsWith("gold-api")) {
    return false;
  }
  if (tk === "DXY" && incoming === "frankfurter-ecb" && current === "yahoo") return false;
  return true;
}

function _savePriceCache(){
  try{
    const payload={
      ts:Date.now(),
      P:Object.fromEntries([...liveSymbols].map(tk=>[tk,P[tk]])),
      BASE:Object.fromEntries([...liveSymbols].map(tk=>[tk,BASE[tk]])),
      live:[...liveSymbols],
      quoteTs:Object.fromEntries([...liveSymbols].map(tk=>[tk,liveQuoteTs[tk]||Date.now()])),
      quoteSrc:Object.fromEntries([...liveSymbols].map(tk=>[tk,liveQuoteSrc[tk]||"session-cache"])),
    };
    sessionStorage.setItem(PRICE_CACHE_KEY,JSON.stringify(payload));
  }catch(e){}
}

function _loadPriceCache(){
  try{
    const raw=sessionStorage.getItem(PRICE_CACHE_KEY)||sessionStorage.getItem("td_price_cache_v1");
    if(!raw)return false;
    const data=JSON.parse(raw);
    if(!data?.ts||Date.now()-data.ts>PRICE_CACHE_MAX_AGE)return false;
    if(!Array.isArray(data.live)||!data.live.length)return false;
    let n=0;
    data.live.forEach(tk=>{
      const row=data.P?.[tk];
      if(!row||typeof row.p!=="number"||!isFinite(row.p)||row.p<=0)return;
      P[tk]={p:row.p,c:typeof row.c==="number"?row.c:0};
      if(data.BASE?.[tk]?.p>0)BASE[tk]=data.BASE[tk];
      else BASE[tk]={p:row.p,c:0};
      liveSymbols.add(tk);
      // Restored session quotes are cached — never pretend they just hit the wire
      liveQuoteTs[tk]=data.quoteTs?.[tk]||data.ts;
      liveQuoteSrc[tk]=data.quoteSrc?.[tk]||"session-cache";
      n++;
    });
    if(!n)return false;
    priceLastFetch=new Date(data.ts);
    return true;
  }catch(e){return false;}
}

function _newsLink(n){
  if(n?.link&&n.link.startsWith("http"))return n.link;
  const q=(n?.x||"").replace(/\.\.\.$/,"").trim();
  return q?`https://www.google.com/search?q=${encodeURIComponent(q)}`:"";
}

function _applyLiveQuote(tk, q, source) {
  if (!tk || !q || typeof q.p !== "number" || !isFinite(q.p) || q.p <= 0) return false;
  const incoming = q.source || source || "yahoo";
  if (!_canReplaceQuote(tk, incoming)) return false;
  const hasProviderTs = q.ts != null || q.fetchedAt != null;
  const sourceFetchedAt = _providerTimestampMs(q);
  if (hasProviderTs && sourceFetchedAt == null) return false;
  const c = typeof q.c === "number" && isFinite(q.c) ? q.c : 0;
  const prev = typeof q.prev === "number" && q.prev > 0 ? q.prev : q.p / (1 + c / 100);
  P[tk] = { p: q.p, c: +c.toFixed(2) };
  BASE[tk] = { p: prev, c: 0 };
  if (!HIST[tk]) HIST[tk] = [];
  HIST[tk].push(q.p);
  if (HIST[tk].length > 120) HIST[tk].shift();
  liveSymbols.add(tk);
  // Provider timestamps are seconds for Yahoo/Twelve Data. Convert so a
  // seconds-since-epoch value cannot look ancient (and get overwritten)
  // or freshly live when it is hours old.
  liveQuoteTs[tk] = sourceFetchedAt != null ? sourceFetchedAt : Date.now();
  liveQuoteSrc[tk] = incoming;
  liveQuoteMarketClosed[tk] = !!q.marketClosed;
  return true;
}
/** Raw numeric price only when feed-confirmed — never seed */
function livePx(tk) {
  if (!liveSymbols.has(tk)) return null;
  const p = P[tk]?.p;
  return typeof p === "number" && isFinite(p) && p > 0 ? p : null;
}
function liveChg(tk) {
  if (!liveSymbols.has(tk)) return null;
  const c = P[tk]?.c;
  return typeof c === "number" && isFinite(c) ? c : null;
}

/** Honest provenance for a quote — seed is never “live” */
function _quoteMeta(tk) {
  if (!liveSymbols.has(tk)) {
    return {
      status: "unavailable",
      label: "NO SYNC",
      detail: "Not received from a market feed this session — seed not shown as price",
      ageMs: null,
      asOf: null,
      src: null,
      trusted: false
    };
  }
  const ts = liveQuoteTs[tk] || (priceLastFetch ? priceLastFetch.getTime() : null);
  const ageMs = ts != null ? Date.now() - ts : null;
  const src = liveQuoteSrc[tk] || "feed";
  const proxy = src.startsWith("gold-api") || src === "frankfurter-ecb";
  let status = "delayed";
  let label = "DELAYED";
  let detail = "Free Yahoo/proxy feed — typically delayed, not exchange co-located";
  if (liveQuoteMarketClosed[tk] && src === "twelve-data") {
    status = "closed";
    label = "MARKET CLOSED";
    detail = "Twelve Data reports the cash session closed — last print retained, not a live tick";
  } else if (proxy) {
    status = "proxy";
    label = src.startsWith("gold-api") ? "SPOT PROXY" : "SYNTH·DXY";
    detail = src.startsWith("gold-api")
      ? "Free gold-api spot proxy — not an exchange instrument, used only when Twelve Data XAU/USD is unavailable"
      : "Synthetic ICE-style dollar index from ECB/Frankfurter FX — not a live DXY print";
  } else if (src === "coingecko") {
    status = "live";
    label = "LIVE·CG";
    detail = "CoinGecko public API (near real-time crypto)";
  } else if (src === "session-cache") {
    status = "cached";
    label = "CACHED";
    detail = "Restored from this browser session — re-sync for a fresh tick";
  } else if (src === "finnhub") {
    status = "delayed";
    label = "DELAYED·FH";
    detail = "Finnhub free/proxy path — may be delayed or rate-limited";
  } else if (src === "twelve-data") {
    status = "live";
    label = "LIVE·TD";
    detail = "Twelve Data real-time source — shared free-plan core tape";
  } else if (src === "yahoo") {
    status = "delayed";
    label = tk === "XAU"
      ? "DELAYED · GC=F futures"
      : "DELAYED";
    detail = tk === "XAU"
      ? "Yahoo COMEX gold futures (GC=F) — delayed futures fallback, not live spot"
      : "Yahoo Finance via Dispatch proxy — free retail feed, not Bloomberg";
  }
  const staleAfterMs = src === "twelve-data" ? TWELVE_DATA_CACHE_WINDOW_MS
    : src === "coingecko" ? 10 * 60 * 1000
    : src === "yahoo" || src === "yahoo-screener" ? 30 * 60 * 1000
    : src.startsWith("gold-api") ? 30 * 60 * 1000
    : src === "frankfurter-ecb" ? 36 * 60 * 60 * 1000
    : PRICE_STALE_MS;
  if (ageMs != null && ageMs > staleAfterMs && status !== "unavailable" && status !== "closed") {
    status = "stale";
    label = proxy ? "STALE·PROXY" : "STALE";
    detail = `${proxy ? "Proxy value" : "Last feed tick"} ${_fmtAge(ts)} ago — treat carefully`;
  }
  return {
    status,
    label,
    detail,
    ageMs,
    asOf: ts,
    src,
    trusted: status === "live" || status === "delayed"
  };
}

function _fmtAsOf(ts) {
  if (!ts) return "—";
  try {
    return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch (e) { return "—"; }
}

async function _initStripeMode() {
  try {
    const res = await fetch("/api/stripe-status", { credentials: "include", signal: AbortSignal.timeout(8000) });
    if (!res.ok) { _stripeMode = "unknown"; return; }
    const d = await res.json();
    if (d.mode === "test" || d.keyMode === "test" || d.stripeLivemode === false) _stripeMode = "test";
    else if (d.mode === "live" || d.stripeLivemode === true) _stripeMode = "live";
    else _stripeMode = d.configured ? "unknown" : "unknown";
  } catch (e) {
    _stripeMode = "unknown";
  }
  // repaint trust bar if dash is open
  if (pg === "dash" && typeof renderMain === "function") {
    const el = document.getElementById("trust-bar");
    if (el) el.outerHTML = _renderTrustBar();
  }
}

function _renderTrustBar() {
  const nLive = [...liveSymbols].filter(tk => _quoteMeta(tk).status === "live").length;
  const nDel = [...liveSymbols].filter(tk => {
    const s = _quoteMeta(tk).status;
    return s === "delayed" || s === "stale" || s === "cached";
  }).length;
  const asOf = priceLastFetch ? _fmtAsOf(priceLastFetch.getTime()) : "—";
  const age = priceLastFetch ? _fmtAge(priceLastFetch.getTime()) : "never";
  const hasTwelveData = [...liveSymbols].some(tk => liveQuoteSrc[tk] === "twelve-data");
  const stripe = _stripeMode === "test"
    ? `<span class="trust-pill trust-warn">STRIPE TEST MODE</span>`
    : _stripeMode === "live"
      ? `<span class="trust-pill trust-ok">STRIPE LIVE</span>`
      : "";
  const feed = priceFetching
    ? `<span class="trust-pill trust-sync">SYNCING FEEDS…</span>`
    : liveSymbols.size
      ? `<span class="trust-pill trust-ok">${nLive ? nLive + " NEAR-LIVE" : "0 NEAR-LIVE"} · ${nDel} DELAYED/CACHED</span>`
      : `<span class="trust-pill trust-bad">NO FEED YET · prices show NO SYNC</span>`;
  return `<div class="trust-bar" id="trust-bar">
    <div class="trust-bar-top">
      <div class="lab-panel-k" style="margin:0">DATA TRUST</div>
      <span class="trust-asof">Feed as of <strong>${asOf}</strong> (${age})</span>
    </div>
    <div class="trust-pills">
      ${feed}
      ${hasTwelveData ? `<span class="trust-pill trust-ok">TWELVE DATA · GOLD/CRYPTO/ETF/FX CORE · SHARED 15M CACHE</span>` : ""}
      <span class="trust-pill">YAHOO DELAYED · NOT BLOOMBERG</span>
      <span class="trust-pill">FEED ONLY - NO SEED PRICES</span>
      <span class="trust-pill trust-model">REGIME / LAB = MODEL</span>
      ${stripe}
    </div>
    <p class="trust-note">Free market data can gap, lag, or fail. Models (regime score, scenario impulse, free desk brief, conviction scores) are educational synthesis — not audited research or investment advice. Verify material decisions against filings, exchange data, and your broker.</p>
  </div>`;
}

// ─── Finnhub /quote: real-time quote for a symbol ───
// Returns: {c: current, d: change, dp: percent change, h, l, o, pc: prev close}
async function fetchFinnhubQuote(symbol){
  try{
    const res=await fetch(`/api/finnhub?endpoint=quote&symbol=${encodeURIComponent(symbol)}`,{signal:AbortSignal.timeout(10000)});
    if(!res.ok)return null;
    const d=await res.json();
    if(!d||typeof d.c!=="number"||d.c===0)return null;
    return {p:d.c,c:d.dp||0,prev:d.pc||d.c,change:d.d||0};
  }catch(e){return null;}
}

// ─── Finnhub /stock/candle: historical OHLCV ───
// Note: Finnhub free tier dropped /stock/candle in 2024. We use the more reliable
// approach of pulling intraday quotes over time, OR fall back to seed history.
// For now we approximate sparkline from the current price + trend smoothing.
// Real history will populate organically as ticks come in.

// ─── CoinGecko: same-origin cached proxy with quiet public-feed failures ───
const CG_IDS="bitcoin,ethereum,solana,ripple,dogecoin,cardano,avalanche-2,chainlink,polkadot,litecoin,uniswap,polygon-ecosystem-token,matic-network,near,algorand,hedera-hashgraph,the-open-network,bitcoin-cash,stellar,filecoin,aptos,sui,shiba-inu,pepe,cosmos,injective-protocol";
// polygon-ecosystem-token is the live POL market — matic-network is often empty post-rebrand
const CG_MAP={bitcoin:"BTC",ethereum:"ETH",solana:"SOL",ripple:"XRP",dogecoin:"DOGE",cardano:"ADA","avalanche-2":"AVAX",chainlink:"LINK",polkadot:"DOT",litecoin:"LTC",uniswap:"UNI","polygon-ecosystem-token":"MATIC","matic-network":"MATIC",near:"NEAR",algorand:"ALGO","hedera-hashgraph":"HBAR","the-open-network":"TON","bitcoin-cash":"BCH",stellar:"XLM",filecoin:"FIL",aptos:"APT",sui:"SUI","shiba-inu":"SHIB",pepe:"PEPE",cosmos:"ATOM","injective-protocol":"INJ"};
// Yahoo *-USD pairs for long-tail alts are often wrong micro-tickers; majors only as CG fallback
const YAHOO_CRYPTO_OK=new Set(["BTC","ETH","SOL","XRP","DOGE","ADA","LTC","LINK","AVAX","BCH","DOT","ATOM","NEAR"]);
let _cgBackoffUntil=0; // epoch ms — don't retry CoinGecko before this

// The public tier can rate limit short bursts. Requests go through the
// same-origin cache so a provider limitation is handled as a quiet stale-data
// state rather than a browser CORS error.
const _CG_SPACING_MS = 1200;
let _cgGateLast = 0;
let _cgChain = Promise.resolve();

/** fetch() for CoinGecko: one at a time, spaced, with backoff on failure. */
function cgFetch(url, opts) {
  const run = async () => {
    const wait = Math.max(0, _cgGateLast + _CG_SPACING_MS - Date.now());
    if (wait) await new Promise(r => setTimeout(r, wait));
    _cgGateLast = Date.now();
    try {
      const proxyUrl = url.startsWith("https://api.coingecko.com/api/v3/")
        ? `/api/coingecko?path=${encodeURIComponent(url.slice("https://api.coingecko.com/api/v3".length))}`
        : url;
      const res = await fetch(proxyUrl, opts);
      // A real 429 does reach us when CORS headers happen to be present.
      if (res.status === 429 || res.headers.get("X-Dispatch-Data-Status") === "unavailable") {
        _cgBackoffUntil = Date.now() + 90000;
      }
      return res;
    } catch (e) {
      // Opaque CORS rejection — almost always the header-less 429. Treat it as
      // rate limiting rather than retrying into the same wall.
      _cgBackoffUntil = Date.now() + 90000;
      throw e;
    }
  };
  // Serialise: the chain is the queue.
  const next = _cgChain.then(run, run);
  _cgChain = next.then(() => {}, () => {});
  return next;
}
async function fetchCrypto(){
  if(Date.now()<_cgBackoffUntil)return null; // rate-limited, use stale data
  try{
    const res=await cgFetch(`https://api.coingecko.com/api/v3/simple/price?ids=${CG_IDS}&vs_currencies=usd&include_24hr_change=true`,
      {signal:AbortSignal.timeout(9000)});
    if(res.status===429){_cgBackoffUntil=Date.now()+90000;return null;} // back off 90s
    if(!res.ok)return null;
    const d=await res.json();
    const out={};
    // polygon-ecosystem-token last wins over empty matic-network when both present
    Object.entries(CG_MAP).forEach(([cgId, tk]) => {
      const row = d[cgId];
      if (row?.usd && row.usd > 0) out[tk] = { p: row.usd, c: typeof row.usd_24h_change === "number" ? row.usd_24h_change : 0 };
    });
    return out;
  }catch(e){return null;}
}

/** CoinGecko sparkline series for one id — real prices only, never fabricated */
async function fetchCgSpark(cgId, days=1){
  if(!cgId||Date.now()<_cgBackoffUntil)return null;
  try{
    const res=await cgFetch(
      `https://api.coingecko.com/api/v3/coins/${encodeURIComponent(cgId)}/market_chart?vs_currency=usd&days=${days}`,
      {signal:AbortSignal.timeout(9000)}
    );
    if(res.status===429){_cgBackoffUntil=Date.now()+90000;return null;}
    if(!res.ok)return null;
    const d=await res.json();
    const series=(d.prices||[]).map(p=>p[1]).filter(v=>typeof v==="number"&&isFinite(v)&&v>0);
    return series.length>=5?series:null;
  }catch(e){return null;}
}
function _cgIdForTicker(tk){
  if(typeof CG_MAP==="undefined")return null;
  // Prefer polygon-ecosystem-token over empty matic-network when both map to MATIC
  const hits=Object.entries(CG_MAP).filter(([,t])=>t===tk).map(([id])=>id);
  if(!hits.length)return null;
  if(hits.includes("polygon-ecosystem-token"))return "polygon-ecosystem-token";
  return hits[0];
}
async function fetchCryptoHistory(){
  const out={};
  // Tape majors + alts that must not use junk Yahoo *-USD sparklines
  const batch=[
    ["bitcoin","BTC"],["ethereum","ETH"],["solana","SOL"],["ripple","XRP"],
    ["dogecoin","DOGE"],["shiba-inu","SHIB"],["uniswap","UNI"],["the-open-network","TON"],
  ];
  for(const[id,tk]of batch){
    if(Date.now()<_cgBackoffUntil)break;
    const series=await fetchCgSpark(id,7);
    if(series)out[tk]=series.slice(-60);
  }
  return out;
}

// ─── Resolve a single dashboard ticker via Finnhub ───
async function fetchOneTicker(ticker){
  const cfg=FH_SYMBOLS[ticker];
  if(!cfg)return null;
  const q=await fetchFinnhubQuote(cfg.sym);
  if(!q)return null;
  // For index proxies (SPX, DJIA, IXIC), scale ETF to index level.
  // We auto-calibrate the anchor on first fetch using the seed price ÷ live ETF price.
  // This guarantees SPX ≈ correct level even as SPY drifts.
  if(cfg.proxy && (ticker==="SPX"||ticker==="DJIA"||ticker==="IXIC")){
    if(DISPLAY_ANCHORS[ticker]==null){
      // Finnhub-only ETF proxy — scale by fixed ratio (not stale seed index levels)
      // Yahoo path uses ^GSPC/^DJI/^IXIC directly and does not use this branch.
      const ratio=SEED_ANCHORS[ticker]||(cfg.scale||10);
      DISPLAY_ANCHORS[ticker]=ratio;
    }
    const anchor=DISPLAY_ANCHORS[ticker];
    return {p:q.p*anchor, c:q.c, prev:q.prev*anchor, source:"finnhub-etf-proxy"};
  }
  // Direct stocks and other ETF proxies — show the ETF price as-is
  return {p:q.p, c:q.c, prev:q.prev, source:"finnhub"};
}

async function _fetchYahooPriceChunk(chunk) {
  // CoinGecko-primary crypto: skip Yahoo first pass (UNI/APT/SUI/TON Yahoo pairs are often junk)
  // Majors in YAHOO_CRYPTO_OK still fill from Yahoo so tape works if CG is 429'd
  const cgPrimary = typeof CG_MAP !== "undefined" ? new Set(Object.values(CG_MAP)) : new Set();
  const filtered = chunk.filter(tk => {
    if (!cgPrimary.has(tk)) return true;
    return typeof YAHOO_CRYPTO_OK !== "undefined" && YAHOO_CRYPTO_OK.has(tk);
  }).filter(tk => _canReplaceQuote(tk, "yahoo"));
  const yhSyms = [...new Set(filtered.map(tk => YAHOO_SYMBOLS[tk]).filter(Boolean))];
  if (!yhSyms.length) return 0;
  let hits = 0;
  try {
    const res = await fetch(`/api/yahoo-quote?symbols=${encodeURIComponent(yhSyms.join(","))}`, { signal: AbortSignal.timeout(35000) });
    if (!res.ok) return 0;
    const yahooData = await res.json();
    filtered.forEach(tk => {
      const yhSym = YAHOO_SYMBOLS[tk];
      // Response may be keyed by desk alias (BTC) or wire (BTC-USD) depending on request
      const q = (yhSym && yahooData[yhSym]) || yahooData[tk];
      if (_applyLiveQuote(tk, q, "yahoo")) hits++;
    });
  } catch (e) { /* retry next cycle */ }
  return hits;
}
async function fetchTwelveDataPrices() {
  try {
    const symbols = Object.values(TWELVE_DATA_SYMBOLS);
    const res = await fetch(`/api/twelve-data-quote?symbols=${encodeURIComponent(symbols.join(","))}`, {
      signal: AbortSignal.timeout(10_000),
    });
    if (!res.ok) return 0;
    const data = await res.json();
    if (data?.configured === false || data?.unavailable) return 0;
    if (data?.provider && data.provider.id !== "twelve-data") return 0;
    const quotes = data?.quotes || {};
    const closedSymbols = new Set(data?.marketClosedSymbols || []);
    let hits = 0;
    Object.entries(TWELVE_DATA_SYMBOLS).forEach(([ticker, symbol]) => {
      const row = quotes[symbol];
      if (!row) return;
      const quote = {
        ...row,
        fetchedAt: row.ts ?? data.fetchedAt,
        marketClosed: !!row.marketClosed || closedSymbols.has(symbol),
      };
      if (_applyLiveQuote(ticker, quote, "twelve-data")) hits++;
    });
    return hits;
  } catch (e) {
    return 0;
  }
}

async function fetchReferencePrices() {
  try {
    const res = await fetch("/api/market-reference-quotes", { signal: AbortSignal.timeout(10_000) });
    if (!res.ok) return 0;
    const data = await res.json();
    let hits = 0;
    // Twelve Data XAU/USD wins when present; gold-api is an honest spot proxy only.
    if (data.XAU && _applyLiveQuote("XAU", data.XAU, data.XAU.source || "gold-api-spot-proxy")) hits++;
    // Delayed Yahoo DXY (ICE) beats this synthetic; apply only as a labeled fallback.
    if (data.DXY && _applyLiveQuote("DXY", data.DXY, data.DXY.source || "frankfurter-ecb")) hits++;
    return hits;
  } catch (e) {
    return 0;
  }
}

async function fetchLivePrices(){
  if(updatePaused)return;
  priceFetching=true;
  _priceFetchAttempted=true;
  renderStatus();
  let successCount=0;

  // Labeled free proxies first; Twelve Data overwrites XAU when the core tape hits.
  successCount += await fetchReferencePrices();
  // Real-time core gold / crypto / ETF / FX tape, cached centrally to protect the free plan.
  successCount += await fetchTwelveDataPrices();
  // Priority bootstrap — headline tickers land in one round-trip
  const priHits=await _fetchYahooPriceChunk(PRICE_PRIORITY.filter(tk=>YAHOO_SYMBOLS[tk]));
  successCount+=priHits;
  if(priHits>0){
    renderTape();
    if(IS_DESKTOP()){
      if(termSelTk||_dynTk){_patchP2LiveHeader();renderP1();renderP3();renderP4();}
      else renderTerminalPanels();
      _patchLiveDataIfNeeded(); _patchCuratedPrices();
    }
    else if(pg==="dash"||pg==="mkt")_patchLiveDataIfNeeded();
  }

  const restTickers=Object.keys(YAHOO_SYMBOLS).filter(tk=>!PRICE_PRIORITY.includes(tk));
  const CHUNK=40;
  const chunks=[];
  for(let i=0;i<restTickers.length;i+=CHUNK)chunks.push(restTickers.slice(i,i+CHUNK));

  for(let i=0;i<chunks.length;i+=2){
    const pair=chunks.slice(i,i+2);
    const results=await Promise.all(pair.map(c=>_fetchYahooPriceChunk(c)));
    successCount+=results.reduce((a,b)=>a+b,0);
    if(i===0&&priHits===0){
      renderTape();
      if(IS_DESKTOP()){
        if(termSelTk||_dynTk){_patchP2LiveHeader();renderP1();renderP3();renderP4();}
        else renderTerminalPanels();
        _patchLiveDataIfNeeded();
      }
      else if(pg==="dash"||pg==="mkt")_patchLiveDataIfNeeded();
    }
  }

  // Crypto: CoinGecko primary, Yahoo USD pairs fill gaps
  const cryptoData = await fetchCrypto();
  if (cryptoData) {
    Object.entries(cryptoData).forEach(([tk, row]) => {
      if (!row) return;
      if (_applyLiveQuote(tk, { p: row.p, c: row.c, prev: row.p / (1 + (row.c || 0) / 100) }, "coingecko")) successCount++;
    });
  }

  if(successCount>0){
    priceLastFetch=new Date();
    priceFetchCount++;
    priceErrorCount=0;
    _savePriceCache();
  }else{
    priceErrorCount++;
    if (priceErrorCount <= 3) setTimeout(fetchLivePrices, 4000);
  }

  priceFetching=false;
  renderStatus();
  renderTape();
  _paintFeedBanner();
  _syncTapePulse();
  _paintWlGlance();
  checkAlerts();
  checkSmartAlerts();
  const _me=document.getElementById('main'),_ms=_me?_me.scrollTop:0;
  if(pg==="mkt"&&_mktView==="curated")_patchCuratedPrices();
  else if(pg==="mkt") {
    // Prefer surgical patches — full renderMain feels like a page reload
    if (!MOBILE()) { _patchLiveDataIfNeeded(); _patchCuratedPrices(); }
    else _patchLiveDataIfNeeded();
  }
  else if((pg==="dash"||pg==="port")&&_ms<80)_patchCuratedPrices();
  else if((pg==="anlz"||pg==="watch")&&_ms<60) {
    if (!MOBILE()) { _patchLiveDataIfNeeded(); }
    else _patchLiveDataIfNeeded();
  }
  if(!MOBILE()){
    if(termSelTk||_dynTk){
      _patchP2LiveHeader();
      renderP1();renderP3();renderP4();
    }else{
      renderTerminalPanels();
    }
  }
}

// Yahoo Finance symbol map for intraday sparkline history
// (real OHLC; not a Math.random fabrication).
const YAHOO_SYMBOLS = {
  SPX:"^GSPC", DJIA:"^DJI", IXIC:"^IXIC",
  FTSE:"^FTSE", DAX:"^GDAXI", N225:"^N225", NSEI:"^NSEI", HSI:"^HSI",
  AAPL:"AAPL", NVDA:"NVDA", XOM:"XOM", MSFT:"MSFT", AVGO:"AVGO", TSLA:"TSLA",
  AMZN:"AMZN", GOOGL:"GOOGL", META:"META", JPM:"JPM", GS:"GS", AMD:"AMD",
  XAU:"GC=F", WTI:"CL=F", SLV:"SI=F", NG:"NG=F",
  EURUSD:"EURUSD=X", GBPUSD:"GBPUSD=X", USDJPY:"JPY=X",
  DXY:"DX-Y.NYB", VIX:"^VIX",
  // Additional stocks
  NFLX:"NFLX", DIS:"DIS", V:"V", MA:"MA", PYPL:"PYPL", CRM:"CRM", ORCL:"ORCL",
  ADBE:"ADBE", INTC:"INTC", QCOM:"QCOM", MU:"MU", CSCO:"CSCO", NOW:"NOW",
  PANW:"PANW", CRWD:"CRWD", PLTR:"PLTR", COIN:"COIN", UBER:"UBER", SHOP:"SHOP",
  SNOW:"SNOW", RIVN:"RIVN", F:"F", GM:"GM", BA:"BA", CAT:"CAT", DE:"DE",
  NKE:"NKE", SBUX:"SBUX", MCD:"MCD", JNJ:"JNJ", UNH:"UNH", PFE:"PFE",
  LLY:"LLY", ABBV:"ABBV", MRK:"MRK", WMT:"WMT", COST:"COST", HD:"HD",
  BAC:"BAC", WFC:"WFC", C:"C", BLK:"BLK", ISRG:"ISRG", TSM:"TSM",
  ASML:"ASML", NVO:"NVO", SAP:"SAP", BABA:"BABA", BP:"BP", SHEL:"SHEL",
  // New US stocks
  ARM:"ARM", SMCI:"SMCI", MRVL:"MRVL", KO:"KO", PEP:"PEP", PG:"PG",
  ABNB:"ABNB", DASH:"DASH", BRKB:"BRK-B", ACN:"ACN",
  SONY:"SONY", VALE:"VALE", RIO:"RIO", INFY:"INFY",
  // Additional FX
  AUDUSD:"AUDUSD=X", USDCAD:"CAD=X", USDCHF:"CHF=X", NZDUSD:"NZDUSD=X", EURGBP:"EURGBP=X",
  // Additional commodities
  COPPER:"HG=F", WHEAT:"ZW=F", CORN:"ZC=F",
  COFFEE:"KC=F", PLAT:"PL=F", COCOA:"CC=F",
  OJ:"OJ=F", LUMBER:"LBS=F", PALLADIUM:"PA=F",
  // Additional indices
  CAC:"^FCHI", ASX200:"^AXJO", KOSPI:"^KS11",
  // More US stocks
  TMO:"TMO",ABT:"ABT",PM:"PM",NEE:"NEE",RTX:"RTX",HON:"HON",
  T:"T",VZ:"VZ",MS:"MS",SCHW:"SCHW",TXN:"TXN",AMAT:"AMAT",
  LRCX:"LRCX",REGN:"REGN",AMGN:"AMGN",CVX:"CVX",COP:"COP",
  INTU:"INTU",ADSK:"ADSK",NET:"NET",DDOG:"DDOG",ZS:"ZS",
  UPS:"UPS",LOW:"LOW",DUK:"DUK",
  // More international
  TM:"TM",NVS:"NVS",UL:"UL",DEO:"DEO",
  // More FX
  USDMXN:"MXN=X",USDBRL:"BRL=X",USDINR:"INR=X",
  // ETFs, indices & sectors
  SPY:"SPY",QQQ:"QQQ",IWM:"IWM",RUT:"^RUT",EEM:"EEM",SOXX:"SOXX",TLT:"TLT",ARKK:"ARKK",TNX:"^TNX",
  XLK:"XLK",XLC:"XLC",XLY:"XLY",XLF:"XLF",XLV:"XLV",XLE:"XLE",XLI:"XLI",XLP:"XLP",XLB:"XLB",XLU:"XLU",XLRE:"XLRE",
  RKLB:"RKLB",HOOD:"HOOD",MSTR:"MSTR",GME:"GME",SPOT:"SPOT",LMT:"LMT",BMY:"BMY",GILD:"GILD",
  ENPH:"ENPH",FSLR:"FSLR",EOG:"EOG",SLB:"SLB",SO:"SO",PLD:"PLD",AMT:"AMT",EQIX:"EQIX",SPG:"SPG",O:"O",VRTX:"VRTX",
  BRENT:"BZ=F",URA:"URA",EURJPY:"EURJPY=X",GBPJPY:"GBPJPY=X",
  // Crypto via Yahoo (CoinGecko fallback in fetchLivePrices)
  BTC:"BTC-USD",ETH:"ETH-USD",SOL:"SOL-USD",XRP:"XRP-USD",DOGE:"DOGE-USD",
  ADA:"ADA-USD",AVAX:"AVAX-USD",LINK:"LINK-USD",DOT:"DOT-USD",LTC:"LTC-USD",
  // Long-tail still listed for chart lookup; live marks prefer CoinGecko (see YAHOO_CRYPTO_OK)
  UNI:"UNI-USD",MATIC:"MATIC-USD",NEAR:"NEAR-USD",ALGO:"ALGO-USD",HBAR:"HBAR-USD",
  BCH:"BCH-USD",XLM:"XLM-USD",FIL:"FIL-USD",APT:"APT-USD",SUI:"SUI-USD",
  ATOM:"ATOM-USD",INJ:"INJ-USD",SHIB:"SHIB-USD",PEPE:"PEPE-USD",TON:"TON11419-USD",
};

// Fetch one ticker's intraday closes from Yahoo Finance via server-side function.
// Returns an array of valid (>0) closes, or null on failure. Never fills gaps.
async function fetchYahooIntraday(yhSym){
  try{
    const res=await chartFetch(`/api/yahoo-chart?symbol=${encodeURIComponent(yhSym)}&range=1d&interval=5m`,{signal:AbortSignal.timeout(12000)});
    if(!res.ok) throw new Error("fail");
    const data=await res.json();
    const result=data?.chart?.result?.[0];
    const closes=result?.indicators?.quote?.[0]?.close;
    if(Array.isArray(closes)){
      const clean=closes.filter(v=>typeof v==="number"&&isFinite(v)&&v>0);
      if(clean.length>=5)return clean;
    }
  }catch(e){}
  // Fall back: try previous session if today returned nothing (closed market).
  try{
    const res=await chartFetch(`/api/yahoo-chart?symbol=${encodeURIComponent(yhSym)}&range=5d&interval=15m`,{signal:AbortSignal.timeout(12000)});
    if(!res.ok) return null;
    const data=await res.json();
    const closes=data?.chart?.result?.[0]?.indicators?.quote?.[0]?.close;
    if(Array.isArray(closes)){
      const clean=closes.filter(v=>typeof v==="number"&&isFinite(v)&&v>0);
      if(clean.length>=5)return clean.slice(-50);
    }
  }catch(e){}
  return null;
}

// Fetch initial history for sparklines: real intraday closes from Yahoo
// (or CoinGecko for BTC/ETH). Symbols that fail are left without a sparkline —
// the spark() renderer will show "no data" rather than fabricate a line.
async function fetchInitialHistory(){
  const ch=await fetchCryptoHistory();
  Object.keys(ch).forEach(tk=>{HIST[tk]=ch[tk];});

  // Priority-1: fetch indices and top stocks first (visible on dashboard immediately)
  const PRIORITY=['SPX','DJIA','IXIC','SPY','QQQ','RUT','FTSE','DAX','N225','AAPL','NVDA','MSFT','TSLA','AMZN','GOOGL','META','XAU','WTI','BRENT','BTC','ETH','SOL','XLK','XLF','XLE','VIX','DXY'];
  // Priority-2: rest of the symbol map, but only if not already populated
  const REST=Object.keys(YAHOO_SYMBOLS).filter(tk=>!PRIORITY.includes(tk));

  async function fetchBatch(tickers, batchSize=6){
    for(let i=0;i<tickers.length;i+=batchSize){
      const batch=tickers.slice(i,i+batchSize);
      const results=await Promise.all(batch.map(async tk=>{
        const yhSym=YAHOO_SYMBOLS[tk];
        if(!yhSym||HIST[tk]?.length>=5)return[tk,null];
        const series=await fetchYahooIntraday(yhSym);
        return[tk,series];
      }));
      results.forEach(([tk,series])=>{
        if(series&&series.length>=5){
          HIST[tk]=series.slice(-60);
          if(typeof _patchSparkline==="function")_patchSparkline(tk);
        }
      });
      // Never full renderMain on mobile mid-boot — hard-reset flicker on Android
      if(i===0&&!MOBILE())renderMain();
      else if(i===0){_patchLiveDataIfNeeded();_patchCuratedPrices();}
    }
  }

  // Run priority batch first (parallel 6), then the rest lazily
  await fetchBatch(PRIORITY,6);
  if(!MOBILE())renderMain();
  else{_patchLiveDataIfNeeded();_patchCuratedPrices();}
  // Sparklines for non-priority tickers load on demand when a row is selected (saves ~120 API calls on boot)
}

// ═══════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════
function bd(t,c){const bg=c==="var(--gn)"?"var(--gnG)":c==="var(--rd)"?"var(--rdG)":c==="var(--gd)"?"var(--gdG)":c==="var(--pu)"?"var(--puG)":"var(--blG)";
  return `<span class="bd" style="background:${bg};color:${c}">${t}</span>`;}
function scC(v){return v>=75?"var(--gn)":v>=50?"var(--bl)":v>=35?"var(--gd)":"var(--rd)";}
// Format a ticker. Seed prices are NEVER returned as market prices.
// status: live | delayed | stale | cached | unavailable
function fp(tk){
  const meta=_quoteMeta(tk);
  const d=P[tk];
  const hasPx=liveSymbols.has(tk)&&d&&typeof d.p==="number"&&isFinite(d.p)&&d.p>0;
  if (!hasPx) {
    if (liveSymbols.has(tk)) liveSymbols.delete(tk); // corrupt entry — drop
    return {
      p: "—", c: "—", chg: "—", raw: 0, d: 0,
      status: "unavailable", label: "NO SYNC",
      asOf: null, age: "—", src: null, detail: meta.detail||"Awaiting live feed"
    };
  }
  const base=BASE[tk]&&BASE[tk].p>0?BASE[tk]:{p:d.p};
  const chg=d.p-base.p;
  const p=d.p>=10000?Math.round(d.p).toLocaleString():d.p>=1?d.p.toFixed(2):d.p.toFixed(4);
  const fmtChg = Math.abs(chg)>=1000?Math.round(chg).toLocaleString():chg.toFixed(2);
  const pct = Number(d.c);
  const pctN = isFinite(pct) ? pct : 0;
  // d polarity: +1 up, -1 down, 0 flat — never treat flat as up
  const dir = pctN > 0 ? 1 : pctN < 0 ? -1 : 0;
  return{
    p, c: pctN.toFixed(2), chg: fmtChg, raw: chg, d: dir,
    status: meta.status, label: meta.label,
    asOf: meta.asOf, age: meta.asOf ? _fmtAge(meta.asOf) : "—",
    src: meta.src, detail: meta.detail
  };
}
// Neutral dim placeholder for change cells until a live quote arrives —
// a red ↓0.00% wall reads as "site is broken", a quiet — reads as "loading"
function chgDim(){return `<span style="color:var(--t3);opacity:0.55;font-weight:400">—</span>`;}
function ring(sc,sz=40){const r=(sz-4)/2,ci=2*Math.PI*r,of=ci-(sc/100)*ci,c=scC(sc);
  return `<div style="position:relative;width:${sz}px;height:${sz}px;flex-shrink:0"><svg width="${sz}" height="${sz}" style="transform:rotate(-90deg)"><circle cx="${sz/2}" cy="${sz/2}" r="${r}" fill="none" stroke="var(--b3)" stroke-width="3"/><circle cx="${sz/2}" cy="${sz/2}" r="${r}" fill="none" stroke="${c}" stroke-width="3" stroke-dasharray="${ci}" stroke-dashoffset="${of}" stroke-linecap="round"/></svg><span style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-family:var(--mn);font-weight:800;font-size:${sz*0.26}px;color:${c}">${sc}</span></div>`;}
// Sparkline: render only from real data points. If <5 valid points, show a
// muted placeholder rather than fabricating a line.
const _sparkPending=new Set();
async function _ensureSparkline(tk){
  if(_sparkPending.has(tk)||(HIST[tk]||[]).filter(v=>typeof v==="number"&&isFinite(v)&&v>0).length>=5)return;
  _sparkPending.add(tk);
  try{
    // Desk crypto: CoinGecko only — Yahoo UNI-USD/SHIB-USD etc. are junk micros
    const cgId=_cgIdForTicker(tk);
    if(cgId){
      const cgSeries=await fetchCgSpark(cgId,1);
      if(cgSeries&&cgSeries.length>=5){
        HIST[tk]=cgSeries.slice(-60);
        _patchSparkline(tk);
        return;
      }
      // Majors may still fall through to Yahoo if CG 429'd
      if(typeof YAHOO_CRYPTO_OK==="undefined"||!YAHOO_CRYPTO_OK.has(tk))return;
    }
    const yhSym=YAHOO_SYMBOLS[tk];
    if(!yhSym)return;
    const series=await fetchYahooIntraday(yhSym);
    if(series&&series.length>=5){
      HIST[tk]=series.slice(-60);
      _patchSparkline(tk);
    }
  }catch(e){}
  finally{_sparkPending.delete(tk);}
}
function _patchSparkline(tk){
  document.querySelectorAll(`[data-spark-tk="${tk}"]`).forEach(el=>{
    const w=parseInt(el.dataset.sparkW||"72",10),h=parseInt(el.dataset.sparkH||"18",10);
    el.innerHTML=spark(tk,w,h,true);
  });
}
function _patchCuratedPrices(){
  document.querySelectorAll("[data-price-card]").forEach(el=>{
    const tk=el.dataset.priceCard;
    if(!tk||!liveSymbols.has(tk))return;
    const d=fp(tk),showDollar=el.dataset.priceDollar==="1";
    const pctOnly=el.dataset.priceChg==="pct";
    const chgN=liveChg(tk);
    const col=chgN==null?"var(--t3)":chgN>0?"var(--gn)":chgN<0?"var(--rd)":"var(--t3)";
    const sign=d.raw>=0?"+":"";
    const priceEl=el.querySelector(".asset-price");
    const chgEl=el.querySelector(".asset-chg");
    if(priceEl)priceEl.textContent=(showDollar?"$":"")+d.p;
    if(chgEl){
      chgEl.style.color=col;
      chgEl.textContent=pctOnly?`${sign}${d.c}%`:`${sign}${d.chg} (${sign}${d.c}%)`;
      chgEl.classList.remove("px-up","px-dn","px-flat");
      chgEl.classList.add(chgN==null||chgN===0?"px-flat":chgN>0?"px-up":"px-dn");
    }
    const liveBadge=el.querySelector(".bd");
    if(liveBadge&&liveBadge.textContent==="N/A")liveBadge.outerHTML=stat(tk);
  });
}
function spark(tk,w=90,h=22,_skipLazy){
  const raw=HIST[tk]||[];
  const d=raw.filter(v=>typeof v==="number"&&isFinite(v)&&v>0);
  if(d.length<5){
    if(!_skipLazy)_ensureSparkline(tk);
    return `<div data-spark-tk="${tk}" data-spark-w="${w}" data-spark-h="${h}" role="img" aria-label="Chart loading" style="width:${w}px;height:${h}px;display:flex;align-items:center;justify-content:center;font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.08em;border:1px dashed var(--gb);border-radius:4px;opacity:0.55">— loading —</div>`;
  }
  const mn=Math.min(...d),mx=Math.max(...d),rng=mx-mn||Math.max(mx*0.001,1e-9);
  const chN=liveChg(tk);
  const col=chN==null?"var(--t3)":chN>0?"var(--gn)":chN<0?"var(--rd)":"var(--t3)";
  const pts=d.map((v,i)=>`${(i/(d.length-1))*w},${h-((v-mn)/rng)*h*0.8-h*0.08}`).join(" ");
  return `<svg role="img" aria-label="${tk} intraday sparkline" width="${w}" height="${h}" style="display:block"><polyline points="${pts}" fill="none" stroke="${col}" stroke-width="1.3"/></svg>`;
}
// Compact status pill — LIVE / DELAYED / STALE / CACHED / NO SYNC
function stat(tk){
  const d=fp(tk);
  const s=d.status||"unavailable";
  const title=_escAttr(`${d.label||s}${d.asOf?` · as of ${_fmtAsOf(d.asOf)} (${d.age})`:""}${d.detail?` · ${d.detail}`:""}`);
  if(s==="live")return `<span class="bd trust-stat trust-stat-live" title="${title}" style="background:var(--gnG);color:var(--gn);font-size:7.5px">${_esc(d.label||"LIVE")}</span>`;
  if(s==="delayed")return `<span class="bd trust-stat trust-stat-delayed" title="${title}" style="background:var(--blG);color:var(--bl);font-size:7.5px">DELAYED</span>`;
  if(s==="stale")return `<span class="bd trust-stat trust-stat-stale" title="${title}" style="background:var(--gdG);color:var(--gd);font-size:7.5px">STALE</span>`;
  if(s==="cached")return `<span class="bd trust-stat trust-stat-cached" title="${title}" style="background:var(--puG);color:var(--pu);font-size:7.5px">CACHED</span>`;
  return `<span class="bd trust-stat trust-stat-na" title="${title}" style="background:var(--b3);color:var(--t3);font-size:7.5px">NO SYNC</span>`;
}
function asOfTag(tk){
  const d=fp(tk);
  if(d.status==="unavailable"||!d.asOf)return `<span class="asof-tag asof-na" title="No feed tick this session">no sync</span>`;
  return `<span class="asof-tag" title="${_escAttr(d.detail||"")}">as of ${_fmtAsOf(d.asOf)} · ${d.age}</span>`;
}

// ═══════════════════════════════════════════════════════════
// FREEMIUM — AUTH GATE (server-verified via /api/me)
// ═══════════════════════════════════════════════════════════
let _userTier="free";
let _userTierReady=false;
let _userBilling=false;

async function _initUserTier(){
  try{
    const res=await fetch("/api/me",{credentials:"include"});
    if(res.ok){
      const d=await res.json();
      _userTier=d.tier==="premium"?"premium":"free";
      _userBilling=!!d.billingPortal;
    }
  }catch(e){}
  _userTierReady=true;
  renderAuthButtons();
}

function _isPremium(){
  if(_userTierReady)return _userTier==="premium";
  return document.cookie.split(";").some(c=>c.trim().startsWith("td_tier=premium"));
}

async function _openBillingPortal(){
  try{
    const res=await fetch("/api/billing-portal",{method:"POST",credentials:"include"});
    const d=await res.json();
    if(d.url)window.location.href=d.url;
    else showToast(d.error||"Billing portal unavailable","var(--rd)");
  }catch(e){showToast("Could not open billing portal","var(--rd)");}
}

function _handleApiError(res,feature){
  if(res.status===401){_showLoginGate(feature);return "auth";}
  if(res.status===503)return "capacity";
  if(res.status===502)return "parse";
  return "error";
}

function _showPremiumWelcome(){
  if(localStorage.getItem("td_premium_welcome_v1"))return;
  localStorage.setItem("td_premium_welcome_v1","1");
  let ov=document.getElementById("premWelcomeOv");
  if(ov)ov.remove();
  ov=document.createElement("div");
  ov.id="premWelcomeOv";
  ov.className="fx-sov-enter";
  ov.style.cssText="position:fixed;inset:0;z-index:960;background:rgba(0,0,0,0.85);display:flex;align-items:center;justify-content:center;padding:20px;backdrop-filter:blur(10px)";
  ov.innerHTML=`<div class="fx-overlay-enter" style="background:var(--b2);border:1px solid var(--pro-line,var(--gb));border-radius:12px;padding:28px 24px;width:100%;max-width:420px;box-shadow:var(--shadow-lg)">
    <div style="font-family:var(--mn);font-size:9px;color:var(--gd);letter-spacing:0.2em;margin-bottom:8px">PREMIUM ACTIVE</div>
    <div style="font-family:var(--sn);font-size:20px;font-weight:700;margin-bottom:8px">Welcome to Dispatch</div>
    <div style="font-family:var(--sn);font-size:13px;color:var(--t2);line-height:1.55;margin-bottom:20px">Your AI terminal is unlocked. Start with today's Brief, then stress-test a thesis with Lens Engine.</div>
    <button onclick="nav('brief');loadDispatchBrief(true);document.getElementById('premWelcomeOv').remove()" style="width:100%;background:rgba(212,160,23,0.15);color:var(--gd);border:1px solid rgba(212,160,23,0.35);border-radius:6px;padding:12px;font-family:var(--sn);font-size:13px;font-weight:600;cursor:pointer;margin-bottom:8px">1. Generate Daily Brief</button>
    <button onclick="nav('mkt');document.getElementById('premWelcomeOv').remove()" style="width:100%;background:var(--b1);color:var(--tx);border:1px solid var(--gb);border-radius:6px;padding:11px;font-family:var(--sn);font-size:12px;font-weight:600;cursor:pointer;margin-bottom:8px">2. Explore Markets</button>
    <button onclick="document.getElementById('premWelcomeOv').remove()" style="width:100%;background:transparent;border:none;color:var(--t3);padding:8px;font-family:var(--sn);font-size:11px;cursor:pointer">Skip tour</button>
  </div>`;
  document.body.appendChild(ov);
  ov.addEventListener("click",e=>{if(e.target===ov)ov.remove();});
}

function _subscribeBtn(compact) {
  if (compact) {
    return `<a href="/__auth/subscribe" class="subscribe-btn" style="padding:6px 12px;font-size:11px;border-radius:7px">★ Subscribe</a>`;
  }
  return `<a href="/__auth/subscribe" class="subscribe-btn" style="padding:8px 16px;font-size:12px">★ Subscribe <span style="opacity:0.85;font-weight:600;font-size:11px">£15/mo</span></a>`;
}

function _signInBtn(compact) {
  const cls = "auth-btn auth-btn--ghost" + (compact ? " auth-btn--compact" : "");
  return `<a href="/__auth/login" class="${cls}">Sign in</a>`;
}

function _renderPremiumUpsell() {
  if (_isPremium()) {
    return `<div class="premium-active-bar">
      <span class="auth-btn__badge">★ PREMIUM ACTIVE</span>
      <span class="premium-active-sub">AI Brief · Paper · Lenses · Expert</span>
       <button type="button" class="lab-fs-btn" onclick="_openBillingPortal()" title="Open Stripe billing to cancel your subscription">Unsubscribe</button>
      <a href="/__auth/logout" class="lab-fs-btn">Sign out</a>
    </div>`;
  }
  return `<a href="/__auth/subscribe" class="premium-upsell gc-a" aria-label="Subscribe to Dispatch Premium for £15 per month">
    <div class="pu-left">
      <div class="pu-kicker">★ DISPATCH PREMIUM · LIVE PAYMENTS</div>
      <div class="pu-title">AI Brief · Lenses · Statements · Expert · Custom screener</div>
      <div class="pu-sub">Free: tape, regime, desk brief, Lab models · Premium: LLM + deep data · £15/mo via Stripe</div>
    </div>
    <div class="pu-cta">£15/mo →</div>
  </a>`;
}

function _renderFreePremiumMap() {
  return `<div class="tier-map" id="tier-map">
    <div class="lab-panel-k">FREE VS PREMIUM</div>
    <div class="tier-map-grid">
      <div class="tier-col tier-free">
        <div class="tier-h">FREE</div>
        <ul>
          <li>Live/delayed free market tape</li>
          <li>Regime engine (model)</li>
          <li>Free desk brief (model)</li>
          <li>Desk Run · Letter · Lab packs</li>
          <li>Watchlist · news · heatmap</li>
        </ul>
      </div>
      <div class="tier-col tier-prem">
        <div class="tier-h">PREMIUM · £15/mo</div>
        <ul>
          <li>AI Dispatch Brief (LLM)</li>
          <li>Lens Engine · Expert chat</li>
          <li>Statements · institutions</li>
          <li>Custom screener · doc intel</li>
          <li>Billing portal · cancel anytime</li>
        </ul>
        ${_isPremium()?"":`<button type="button" class="btn btn-primary" style="width:100%;margin-top:8px" onclick="location.href='/__auth/subscribe'">Subscribe</button>`}
      </div>
    </div>
  </div>`;
}

function _paintFeedBanner() {
  let el = document.getElementById("feed-degraded-banner");
  const degraded = priceErrorCount >= 2 || (_priceFetchAttempted && liveSymbols.size === 0 && !priceFetching);
  const cgWait = typeof _cgBackoffUntil === "number" && _cgBackoffUntil > Date.now();
  if (!degraded && !cgWait) {
    if (el) el.remove();
    return;
  }
  if (!el) {
    el = document.createElement("div");
    el.id = "feed-degraded-banner";
    el.className = "feed-degraded-banner";
    const host = document.getElementById("app") || document.body;
    host.insertBefore(el, host.firstChild);
  }
  const parts = [];
  if (degraded) parts.push("Price feed degraded or empty — free Yahoo/proxy can lag or fail.");
  if (cgWait) parts.push("CoinGecko rate-limited — crypto may be stale.");
  el.innerHTML = `<span>${parts.join(" ")}</span>
    <button type="button" onclick="priceErrorCount=0;fetchLivePrices();showToast('Syncing feeds…','var(--bl)')">Retry sync</button>
    <button type="button" class="fd-x" onclick="this.parentElement.remove()" aria-label="Dismiss">×</button>`;
}

function _renderStartHereCard() {
  return `<div class="start-here-card" id="start-here">
    <div class="lab-panel-k">START HERE · ONE PATH</div>
    <div class="start-here-title">Independent analyst loop</div>
    <ol class="start-here-steps">
      <li><strong>Desk Run</strong> — free brief + regime + watchlist fits</li>
      <li><strong>Weekly Letter</strong> — house tilt for the week</li>
      <li><strong>Watchlist</strong> — track names you care about</li>
      <li><strong>Lab</strong> — stress one ticker · write invalidation</li>
    </ol>
    <div class="start-here-actions">
      <button type="button" class="desk-run-cta start-here-cta" onclick="runMorningDeskRun()">1 · Run Desk Run</button>
      <button type="button" class="lab-hud-act" onclick="document.getElementById('desk-letter')?.scrollIntoView({behavior:'smooth'})">2 · Letter</button>
      <button type="button" class="lab-hud-act" onclick="nav('watch')">3 · Watchlist</button>
      <button type="button" class="lab-hud-act lab-hud-gold" onclick="nav('lab')">4 · Lab</button>
    </div>
    <div class="start-here-foot">Free path works without AI credits · Premium unlocks LLM Brief &amp; Lenses</div>
  </div>`;
}

function renderAuthButtons() {
  const prem = _isPremium();
  const cmd = document.getElementById("cmdAuthBtn");
  const hdr = document.getElementById("hdrAuthBtn");
  const about = document.getElementById("aboutAuthRow");

  if (prem) {
     const bill = `<button type="button" class="auth-btn auth-btn--ghost auth-btn--compact" onclick="_openBillingPortal()" title="Open Stripe billing to cancel your subscription">Unsubscribe</button>`;
    const out = `<a href="/__auth/logout" class="auth-btn auth-btn--ghost auth-btn--compact">Sign out</a>`;
    const grp = `<span class="auth-group"><span class="auth-btn__badge">Premium</span>${bill}${out}</span>`;
    if (cmd) cmd.innerHTML = grp;
    if (hdr) hdr.innerHTML = grp;
     if (about) about.innerHTML = `<span class="auth-btn__badge">Premium active</span> · <button type="button" class="auth-btn auth-btn--ghost auth-btn--compact" onclick="_openBillingPortal()" title="Open Stripe billing to cancel your subscription" style="display:inline-flex;padding:4px 8px">Unsubscribe</button> · <a href="/__auth/logout" class="auth-btn auth-btn--ghost auth-btn--compact" style="display:inline-flex;padding:4px 8px">Sign out</a>`;
  } else {
    const authBar = (sub, sign) => `<span class="auth-group">${sign}<span class="auth-divider" aria-hidden="true"></span>${sub}</span>`;
    if (cmd) cmd.innerHTML = authBar(_subscribeBtn(false), _signInBtn(false));
    if (hdr) hdr.innerHTML = authBar(_subscribeBtn(true), _signInBtn(true));
    if (about) about.innerHTML = `<a href="/__auth/subscribe" class="about-signin">Get Premium · £15/month</a><div class="about-signin-hint">New users: pay with Stripe, then set your password. Returning? <a href="/__auth/login" style="color:var(--t2);text-decoration:none;font-weight:600">Sign in</a></div>`;
  }
}

function _showLoginGate(featureName){
  let ov=document.getElementById('loginGateOv');if(ov)ov.remove();
  ov=document.createElement('div');ov.id='loginGateOv';
  ov.style.cssText='position:fixed;inset:0;z-index:950;background:rgba(0,0,0,0.88);display:flex;align-items:center;justify-content:center;padding:20px;backdrop-filter:blur(12px)';
  ov.innerHTML = `
    <div class="premium-gate" style="max-width:480px">
      <div class="eyebrow">PREMIUM</div>
      <h3>${featureName}</h3>
      <p style="color:var(--text-secondary); max-width:360px; margin:12px auto 16px;">
        Free users keep tape, regime, desk brief &amp; Lab. This feature needs Premium (£15/mo · live Stripe).
      </p>
      ${_renderFreePremiumMap()}
      <button onclick="_startCheckout(this); document.getElementById('loginGateOv').remove()" class="btn btn-primary" style="width:100%; padding:14px;margin-top:12px;">
        Subscribe — £15 / month
      </button>
      <div style="margin-top:18px; font-size:12px;">
        <a href="/__auth/login" style="color:var(--text-secondary); text-decoration:none;">Already subscribed? Sign in</a>
      </div>
    </div>`;
  document.body.appendChild(ov);
  ov.addEventListener('click',e=>{if(e.target===ov)ov.remove();});
}

async function _startCheckout(btn){
  if(!btn)return;
  const orig=btn.textContent;
  btn.textContent='Redirecting to payment…';btn.disabled=true;btn.style.opacity='0.7';
  try{
    const r=await fetch('/api/create-checkout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({})});
    const d=await r.json();
    if(d.url){window.location.href=d.url;}
    else if(r.status===401){window.location.href="/__auth/subscribe";}
    else{btn.textContent=d.error||'Something went wrong';btn.disabled=false;btn.style.opacity='1';}
  }catch{btn.textContent='Network error — try again';btn.disabled=false;btn.style.opacity='1';}
}

// ═══════════════════════════════════════════════════════════
// PREMIUM: AI PORTFOLIO RISK ANALYSIS
// ═══════════════════════════════════════════════════════════
async function runPortfolioAI(){
  if(!_isPremium()){_showLoginGate('AI Portfolio Analysis');return;}
  if(!portfolio.length){showToast('Add holdings first','var(--gd)');return;}
  _portAiLoading=true;_portAiResult=null;_refreshView();
  const totalVal=portfolio.reduce((s,pos)=>s+_portMark(pos).value,0)||1;
  const lines=portfolio.map(pos=>{
    const m=_portMark(pos);
    const pct=(m.value/totalVal*100).toFixed(0);
    const pnl=m.pnlPct!=null?m.pnlPct.toFixed(1):"n/a";
    const a=A.find(x=>x.tk===pos.tk);
    return `${pos.tk} (${a?.nm||pos.tk}): $${m.value.toFixed(0)} (${pct}% of portfolio), P&L: ${pnl}%${m.live?"":" [NO SYNC @ cost]"}, category: ${a?.cat||'unknown'}, sentiment: ${a?.se||'unknown'}`;
  }).join('\n');
  const prompt=`Analyse this investment portfolio. Return ONLY valid JSON, no markdown, no backticks:
{"riskScore":6,"riskLabel":"Moderate-High","concentration":[{"issue":"Technology overweight at 45%","severity":"high"},{"issue":"No defensive holdings","severity":"medium"}],"strengths":[{"point":"Diversified across geographies"},{"point":"Strong recent performers in portfolio"}],"warnings":[{"point":"Single sector concentration amplifies drawdown risk"},{"point":"Portfolio beta likely >1.2 — high correlation to market"}],"rebalance":[{"action":"Trim largest position to <20%","priority":"high"},{"action":"Add defensive or low-correlation asset","priority":"medium"}],"summary":"2-3 sentences with specific observations about this portfolio's risk/return profile and key vulnerabilities."}

Total value: $${totalVal.toFixed(0)}
Holdings:
${lines}

riskScore 1-10 (10=very high risk). Be specific to these actual holdings.`;
  try{
    const res=await fetch('/api/committee',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({max_tokens:1500,messages:[{role:'user',content:prompt}]})});
    if(res.status===401){_portAiLoading=false;_showLoginGate('AI Portfolio Analysis');_refreshView();return;}
    const data=await res.json();
    const tb=data.content?.find(b=>b.type==='text');
    if(tb?.text){const clean=tb.text.replace(/```json|```/g,'').trim();_portAiResult=JSON.parse(clean);}
  }catch(e){showToast('AI analysis failed — try again','var(--rd)');}
  _portAiLoading=false;_refreshView();
}

function renderPortfolioAI(r){
  const scoreCol=r.riskScore>=8?'var(--rd)':r.riskScore>=6?'var(--gd)':r.riskScore>=4?'var(--bl)':'var(--gn)';
  const arc=r.riskScore/10;const circ=2*Math.PI*28;const dash=arc*circ;
  let h=`<div class="gc" style="padding:16px;margin-top:8px">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px">
      <div style="font-family:var(--mn);font-size:9px;color:var(--gd);letter-spacing:0.18em">⬢ AI PORTFOLIO RISK ANALYSIS</div>
      <button onclick="_portAiResult=null;renderMain()" style="background:transparent;border:none;color:var(--t3);font-size:11px;cursor:pointer;padding:2px 6px">✕</button>
    </div>
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:14px">
      <svg width="72" height="72" viewBox="0 0 72 72" style="flex-shrink:0">
        <circle cx="36" cy="36" r="28" fill="none" stroke="var(--b3)" stroke-width="6"/>
        <circle cx="36" cy="36" r="28" fill="none" stroke="${scoreCol}" stroke-width="6"
          stroke-dasharray="${dash.toFixed(1)} ${circ.toFixed(1)}"
          stroke-dashoffset="${(circ/4).toFixed(1)}" stroke-linecap="round"/>
        <text x="36" y="40" text-anchor="middle" font-family="JetBrains Mono" font-size="16" font-weight="900" fill="${scoreCol}">${r.riskScore}</text>
      </svg>
      <div>
        <div style="font-family:var(--mn);font-size:18px;font-weight:900;color:${scoreCol}">${r.riskLabel}</div>
        <div style="font-size:11px;color:var(--t2);margin-top:4px;line-height:1.5">${r.summary}</div>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px">
      ${r.warnings?.length?`<div style="background:var(--rdG);border:1px solid rgba(239,68,68,0.15);border-radius:9px;padding:11px">
        <div style="font-family:var(--mn);font-size:8px;color:var(--rd);letter-spacing:0.12em;margin-bottom:6px">⚠ WARNINGS</div>
        ${r.warnings.map(w=>`<div style="font-size:10.5px;color:var(--t2);padding:2px 0;line-height:1.4">· ${w.point}</div>`).join('')}
      </div>`:''}
      ${r.strengths?.length?`<div style="background:var(--gnG);border:1px solid rgba(16,185,129,0.15);border-radius:9px;padding:11px">
        <div style="font-family:var(--mn);font-size:8px;color:var(--gn);letter-spacing:0.12em;margin-bottom:6px">✓ STRENGTHS</div>
        ${r.strengths.map(s=>`<div style="font-size:10.5px;color:var(--t2);padding:2px 0;line-height:1.4">· ${s.point}</div>`).join('')}
      </div>`:''}
    </div>
    ${r.rebalance?.length?`<div style="background:var(--b1);border:1px solid var(--gb);border-radius:9px;padding:11px">
      <div style="font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.12em;margin-bottom:6px">REBALANCING ACTIONS</div>
      ${r.rebalance.map(x=>`<div style="display:flex;align-items:flex-start;gap:7px;padding:3px 0;font-size:10.5px;color:var(--t2);line-height:1.4">
        <span style="color:${x.priority==='high'?'var(--rd)':'var(--gd)'};flex-shrink:0;font-family:var(--mn);font-size:8px;margin-top:2px">${x.priority==='high'?'●':'○'}</span>
        ${x.action}
      </div>`).join('')}
    </div>`:''}
    <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-top:10px;text-align:center">AI analysis · Not investment advice · Portfolio data stored locally</div>
  </div>`;
  return h;
}

// ═══════════════════════════════════════════════════════════
// PREMIUM: INSTITUTIONAL HOLDERS
// ═══════════════════════════════════════════════════════════
async function loadHolders(tk, containerId){
  _holdersLoadTk = tk;
  const el=document.getElementById(containerId);
  if(!el)return;
  if(!_isPremium()){
    el.innerHTML=`<div style="padding:32px;text-align:center">
      <div style="font-size:28px;color:var(--gd);margin-bottom:10px">★</div>
      <div style="font-family:var(--sn);font-size:16px;font-weight:800;margin-bottom:6px">Premium Feature</div>
      <div style="font-size:12px;color:var(--t2);margin-bottom:18px">Institutional Holdings requires a signed-in account</div>
      <a href="/__auth/subscribe" style="display:inline-block;background:var(--gd);color:var(--bg);padding:10px 22px;border-radius:9px;font-weight:800;font-family:var(--sn);font-size:13px;text-decoration:none;margin-right:8px">Subscribe →</a><a href="/__auth/login" style="display:inline-block;background:transparent;color:var(--t2);border:1px solid var(--b4);padding:10px 16px;border-radius:9px;font-weight:700;font-family:var(--sn);font-size:12px;text-decoration:none">Sign In</a>
    </div>`;
    return;
  }
  if(_holdersCache[tk]){el.innerHTML=renderHolders(tk,_holdersCache[tk]);return;}
  el.innerHTML=`<div style="padding:20px;text-align:center"><div style="width:14px;height:14px;border:2px solid var(--gd);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div><div style="font-family:var(--mn);font-size:10px;color:var(--t3)">LOADING INSTITUTIONAL DATA…</div></div>`;
  try{
    const res=await fetch(`/api/holders?symbol=${encodeURIComponent(tk)}`,{signal:AbortSignal.timeout(10000)});
    if(res.status===401){_showLoginGate('Institutional Holdings');el.innerHTML=`<div style="padding:20px;text-align:center;font-family:var(--sn);font-size:13px;color:var(--t2)">Institutional Holdings requires sign-in</div>`;return;}
    if(!res.ok)throw new Error('no data');
    const data=await res.json();
    if(_holdersLoadTk!==tk)return;
    const el2=document.getElementById(containerId);
    if(!el2)return;
    _holdersCache[tk]=data;
    el2.innerHTML=renderHolders(tk,data);
  }catch(e){
    if(_holdersLoadTk!==tk)return;
    const el2=document.getElementById(containerId);
    if(el2)el2.innerHTML=`<div style="padding:20px;text-align:center;font-family:var(--sn);font-size:13px;color:var(--t3)">Institutional data not available for ${tk}<br><span style="font-size:11px">US-listed stocks only (FMP 13F filings)</span></div>`;
  }
}

function renderHolders(tk, data){
  if(!data.holders||!data.holders.length)return`<div style="padding:20px;text-align:center;font-family:var(--sn);font-size:13px;color:var(--t3)">No institutional holder data for ${tk}</div>`;
  const top=data.holders.slice(0,15);
  const maxSh=Math.max(...top.map(h=>h.shares||0),1);
  const fmtN=n=>n>=1e9?(n/1e9).toFixed(2)+'B':n>=1e6?(n/1e6).toFixed(1)+'M':n>=1e3?(n/1e3).toFixed(0)+'K':String(n);
  const totalInst=top.reduce((s,h)=>s+(h.shares||0),0);
  let out=`<div style="padding:10px 14px;border-bottom:1px solid var(--gb);display:flex;justify-content:space-between;align-items:center;background:var(--b1)">
    <div><div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.12em">TOP INSTITUTIONAL HOLDERS · ${tk}</div>
    <div style="font-family:var(--mn);font-size:10px;color:var(--gd);margin-top:2px">★ PREMIUM · 13F Filings · ${data.holders[0]?.dateReported||'Latest'}</div></div>
    <div style="text-align:right"><div style="font-family:var(--mn);font-size:10px;color:var(--tx);font-weight:700">${fmtN(totalInst)}</div><div style="font-size:9px;color:var(--t3)">total shares (top 15)</div></div>
  </div>
  <div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-family:var(--mn);font-size:11px;min-width:340px">
    <thead><tr style="background:var(--b1);border-bottom:1px solid var(--gb)">
      <th style="padding:7px 10px;text-align:left;font-size:8px;color:var(--t3);letter-spacing:0.1em">INSTITUTION</th>
      <th style="padding:7px 10px;text-align:right;font-size:8px;color:var(--t3)">SHARES</th>
      <th style="padding:7px 10px;text-align:right;font-size:8px;color:var(--t3)">QoQ Δ</th>
      <th style="padding:7px 10px;text-align:right;font-size:8px;color:var(--t3)">WEIGHT</th>
    </tr></thead><tbody>`;
  top.forEach(h=>{
    const chg=h.change||0;const cc=chg>0?'var(--gn)':chg<0?'var(--rd)':'var(--t3)';
    const bw=Math.round((h.shares/maxSh)*100);
    out+=`<tr style="border-bottom:1px solid rgba(255,255,255,0.025)">
      <td style="padding:7px 10px">
        <div style="font-size:10.5px;font-weight:600;color:var(--tx);max-width:155px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${h.holder}">${h.holder}</div>
        <div style="height:2px;background:rgba(79,142,247,0.15);border-radius:1px;margin-top:3px"><div style="height:100%;width:${bw}%;background:var(--bl);border-radius:1px"></div></div>
      </td>
      <td style="padding:7px 10px;text-align:right;color:var(--tx);font-weight:700">${fmtN(h.shares)}</td>
      <td style="padding:7px 10px;text-align:right;color:${cc};font-weight:700;font-size:10px">${chg>0?'+':''}${fmtN(chg)}</td>
      <td style="padding:7px 10px;text-align:right;color:var(--t2);font-size:10px">${h.weightPercent?h.weightPercent.toFixed(2)+'%':'—'}</td>
    </tr>`;
  });
  out+=`</tbody></table></div>
  <div style="padding:8px;font-family:var(--mn);font-size:8px;color:var(--t3);text-align:center">FMP · 13F Institutional Filings · Quarterly data · For research only</div>`;
  return out;
}

// ═══════════════════════════════════════════════════════════
// PREMIUM: AI EARNINGS INTELLIGENCE
// ═══════════════════════════════════════════════════════════
async function loadEarningsAI(tk, containerId, earData){
  if(!_isPremium()){_showLoginGate('AI Earnings Intelligence');return;}
  const aiTk=tk;
  _earAiLoading=true;
  const el=document.getElementById(containerId+'-ai');
  if(el)el.innerHTML=`<div style="padding:12px 16px;display:flex;align-items:center;gap:10px;border-top:1px solid var(--gb)"><div style="width:12px;height:12px;border:2px solid var(--gd);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;flex-shrink:0"></div><div style="font-family:var(--mn);font-size:10px;color:var(--gd)">AI ANALYSING EARNINGS HISTORY…</div></div>`;

  const a=A.find(x=>x.tk===tk);
  const h=earData?.history||[];const next=earData?.nextEarnings;
  const beatRate=earData?.beatRate;const avgSurp=earData?.avgSurprise;
  const curPrice=livePx(tk);
  const pxLbl=curPrice!=null?`$${curPrice.toFixed(2)}`:"unavailable (no live feed)";
  const histStr=h.slice(0,5).map(e=>`${e.quarter}: Est $${e.estimate?.toFixed(2)||'?'} → Act $${e.actual?.toFixed(2)||'?'} (${e.beat?'BEAT':'MISS'} ${e.surprisePct!=null?(e.surprisePct>0?'+':'')+e.surprisePct.toFixed(1)+'%':''})`).join(' | ');

  const brLbl=beatRate!=null?beatRate+"%":"n/a";
  const asLbl=avgSurp!=null?avgSurp+"%":"n/a";
  const histMove=avgSurp!=null?Math.abs(avgSurp).toFixed(1):"n/a";
  const prompt=`Analyse the earnings history for ${tk} (${a?.nm||tk}) and generate an earnings intelligence report. Return ONLY valid JSON, no markdown:
{"consensusRange":{"low":2.10,"high":2.50,"mean":2.28,"unit":"EPS"},"keyWatchPoints":["Revenue growth cadence vs guidance","Operating leverage and margin expansion","Forward guidance tone from management"],"historicalPattern":"Company has beaten estimates ${brLbl} of the time with avg ${asLbl} surprise. Pattern shows management tends to guide conservatively.","bullScenario":{"trigger":"Beat on both EPS and revenue with raised guidance","priceMove":"+8% to +14%"},"bearScenario":{"trigger":"Miss on revenue or guidance cut on macro headwinds","priceMove":"-7% to -12%"},"avgHistoricalMove":"±${histMove}%","tradeConsiderations":"2 sentences on trade setup, implied move vs historical move, and key risk to monitor.","verdict":"WATCH"}

${tk} context: price ${pxLbl}, next earnings ${next?.date||'TBC'} (${next?.daysToNext||'?'} days), beat rate ${brLbl}, avg surprise ${asLbl}
History: ${histStr}

verdict options: BULLISH_SETUP / WATCH / CAUTIOUS. Be specific and actionable.`;

  try{
    const res=await fetch('/api/committee',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({max_tokens:1200,messages:[{role:'user',content:prompt}]})});
    if(res.status===401){_earAiLoading=false;_showLoginGate('AI Earnings Intelligence');return;}
    const data=await res.json();
    const tb=data.content?.find(b=>b.type==='text');
    if(tb?.text){const clean=tb.text.replace(/```json|```/g,'').trim();_earAiResults[aiTk]=JSON.parse(clean);}
  }catch(e){showToast('AI earnings analysis failed','var(--rd)');}
  _earAiLoading=false;
  const stillViewing = IS_DESKTOP() ? termSelTk === aiTk : selTk === aiTk;
  if (!stillViewing) return;
  const el2=document.getElementById(containerId+'-ai');
  if(el2&&_earAiResults[aiTk])el2.innerHTML=renderEarningsAI(aiTk,_earAiResults[aiTk]);
  else if(el2&&!_earAiResults[aiTk])el2.innerHTML=`<div style="padding:12px 16px;border-top:1px solid var(--gb);font-family:var(--sn);font-size:12px;color:var(--t3)">AI earnings analysis unavailable</div>`;
}

function renderEarningsAI(tk, r){
  if(!r)return'';
  const vc=r.verdict==='BULLISH_SETUP'?'var(--gn)':r.verdict==='CAUTIOUS'?'var(--rd)':'var(--gd)';
  return`<div style="border-top:2px solid var(--gd);padding:14px;background:linear-gradient(180deg,rgba(245,166,35,0.04),transparent)">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
      <div style="font-family:var(--mn);font-size:9px;color:var(--gd);letter-spacing:0.15em">⬢ AI EARNINGS INTELLIGENCE ★ PREMIUM</div>
      <span style="font-family:var(--mn);font-size:10px;font-weight:800;color:${vc};padding:3px 10px;border:1px solid ${vc}30;border-radius:5px;letter-spacing:0.08em">${r.verdict?.replace('_',' ')}</span>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px">
      <div style="background:var(--gnG);border:1px solid rgba(16,185,129,0.15);border-radius:9px;padding:11px">
        <div style="font-family:var(--mn);font-size:8px;color:var(--gn);letter-spacing:0.1em;margin-bottom:5px">▲ BULL SCENARIO</div>
        <div style="font-size:10.5px;color:var(--t2);line-height:1.4">${r.bullScenario?.trigger}</div>
        <div style="font-family:var(--mn);font-size:13px;font-weight:800;color:var(--gn);margin-top:5px">${r.bullScenario?.priceMove}</div>
      </div>
      <div style="background:var(--rdG);border:1px solid rgba(239,68,68,0.15);border-radius:9px;padding:11px">
        <div style="font-family:var(--mn);font-size:8px;color:var(--rd);letter-spacing:0.1em;margin-bottom:5px">▼ BEAR SCENARIO</div>
        <div style="font-size:10.5px;color:var(--t2);line-height:1.4">${r.bearScenario?.trigger}</div>
        <div style="font-family:var(--mn);font-size:13px;font-weight:800;color:var(--rd);margin-top:5px">${r.bearScenario?.priceMove}</div>
      </div>
    </div>
    ${r.keyWatchPoints?.length?`<div style="background:var(--b1);border:1px solid var(--gb);border-radius:9px;padding:11px;margin-bottom:10px">
      <div style="font-family:var(--mn);font-size:8px;color:var(--bl);letter-spacing:0.1em;margin-bottom:6px">KEY WATCH POINTS</div>
      ${r.keyWatchPoints.map(p=>`<div style="font-size:10.5px;color:var(--t2);padding:2px 0;line-height:1.4;display:flex;gap:6px"><span style="color:var(--bl);flex-shrink:0">→</span>${p}</div>`).join('')}
    </div>`:''}
    <div style="background:var(--b1);border:1px solid var(--gb);border-radius:9px;padding:11px;margin-bottom:6px">
      <div style="font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.1em;margin-bottom:4px">TRADE CONSIDERATIONS</div>
      <div style="font-size:10.5px;color:var(--t2);line-height:1.55">${r.tradeConsiderations}</div>
      <div style="display:flex;gap:14px;margin-top:8px">
        <div><div style="font-family:var(--mn);font-size:8px;color:var(--t3)">EPS RANGE</div><div style="font-family:var(--mn);font-size:12px;font-weight:700;color:var(--tx)">${r.consensusRange?.low!=null?'$'+r.consensusRange.low+' – $'+r.consensusRange.high:'—'}</div></div>
        <div><div style="font-family:var(--mn);font-size:8px;color:var(--t3)">HIST. MOVE</div><div style="font-family:var(--mn);font-size:12px;font-weight:700;color:var(--tx)">${r.avgHistoricalMove||'—'}</div></div>
      </div>
    </div>
    <div style="font-family:var(--mn);font-size:8px;color:var(--t3);text-align:center">AI analysis · Not investment advice · Options-implied move may differ</div>
  </div>`;
}

// ═══════════════════════════════════════════════════════════
// PREMIUM: CSV EXPORT
// ═══════════════════════════════════════════════════════════
function _downloadCSV(rows,filename){
  const csv=rows.map(r=>r.map(v=>{const s=String(v??'');return s.includes(',')||s.includes('"')?'"'+s.replace(/"/g,'""')+'"':s;}).join(',')).join('\n');
  const blob=new Blob([csv],{type:'text/csv'});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');a.href=url;a.download=filename;a.click();
  URL.revokeObjectURL(url);
  showToast('CSV exported','var(--gn)');
}

function exportPortfolioCSV(){
  if(!_isPremium()){_showLoginGate('Portfolio Export');return;}
  if(!portfolio.length){showToast('No positions to export','var(--gd)');return;}
  const rows=[['Symbol','Name','Category','Qty','Avg Cost ($)','Current Price ($)','Value ($)','P&L ($)','P&L (%)','Mark','Date']];
  const now=new Date().toISOString().slice(0,10);
  portfolio.forEach(pos=>{
    const m=_portMark(pos);
    const a=A.find(x=>x.tk===pos.tk);
    rows.push([
      pos.tk,a?.nm||pos.tk,a?.cat||'',pos.qty,Number(pos.avgCost).toFixed(2),
      m.live?m.px.toFixed(2):"",m.value.toFixed(2),
      m.live&&m.pnl!=null?m.pnl.toFixed(2):"",
      m.live&&m.pnlPct!=null?m.pnlPct.toFixed(2):"",
      m.live?"LIVE":"COST",now
    ]);
  });
  _downloadCSV(rows,'dispatch-portfolio-'+new Date().toISOString().slice(0,10)+'.csv');
}

// ═══════════════════════════════════════════════════════════
// TOAST
// ═══════════════════════════════════════════════════════════
function showToast(msg,col){
  const el=document.getElementById("toast");
  if(!el)return;
  el.textContent=msg;el.style.borderColor=col||"rgba(255,255,255,0.1)";
  el.classList.add("show");
  clearTimeout(toastTO);toastTO=setTimeout(()=>el.classList.remove("show"),3200);
}

// ═══════════════════════════════════════════════════════════
// FEAR & GREED
// ═══════════════════════════════════════════════════════════
function calcFearGreed(){
  // Model only — uses LIVE feed inputs; never invents VIX=22 as a fake quote
  const vix=livePx('VIX');
  const changes=[...liveSymbols].map(tk=>{
    const c=P[tk]?.c;
    return(typeof c==="number"&&isFinite(c))?c:null;
  }).filter(c=>c!=null&&Math.abs(c)<20);
  const nLive=changes.length;
  // No live tape → incomplete model (do not paint a fake 50)
  if(vix==null&&!nLive){
    return{score:null,label:"Awaiting feed",color:"var(--t3)",vix:null,nLive:0,incomplete:true};
  }
  const vixScore=vix!=null?Math.max(0,Math.min(100,Math.round(100-(vix-10)/30*100))):50;
  const avgChg=nLive?(changes.reduce((a,b)=>a+b,0)/nLive):0;
  const momScore=nLive?Math.max(0,Math.min(100,Math.round(50+avgChg*7))):50;
  const score=Math.max(0,Math.min(100,Math.round(vixScore*0.65+momScore*0.35)));
  const label=score>=80?"Extreme Greed":score>=60?"Greed":score>=40?"Neutral":score>=20?"Fear":"Extreme Fear";
  const color=score>=80?"var(--gn)":score>=60?"#86efac":score>=40?"var(--bl)":score>=20?"var(--gd)":"var(--rd)";
  return{score,label,color,vix,nLive,incomplete:false};
}
function renderFearGreed(){
  const{score,label,color,vix,nLive,incomplete}=calcFearGreed();
  const vixStr=vix!=null?vix.toFixed(1):"—";
  const scoreStr=score!=null?String(score):"—";
  const feedNote=incomplete?"awaiting live feed":(vix!=null?`VIX live · ${nLive} chg inputs`:`${nLive} live inputs · VIX pending`);
  const needle=score!=null?score:50;
  return`<div class="gc" style="padding:14px">
    <div style="font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.18em;margin-bottom:10px">FEAR & GREED · MODEL</div>
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:10px">
      <div style="background:${color}18;border:2px solid ${color}40;border-radius:50%;width:56px;height:56px;display:flex;align-items:center;justify-content:center;flex-shrink:0">
        <span style="font-family:var(--mn);font-weight:900;font-size:18px;color:${color}">${scoreStr}</span>
      </div>
      <div>
        <div style="font-size:16px;font-weight:800;color:${color};line-height:1">${label}</div>
        <div style="font-size:9px;color:var(--t3);font-family:var(--mn);margin-top:4px">VIX ${vixStr} · ${feedNote}</div>
      </div>
    </div>
    <div style="position:relative;height:6px;border-radius:3px;background:linear-gradient(to right,#EF4444,#F59E0B,#3B82F6,#86efac,#10B981);opacity:${incomplete?0.35:1}">
      <div style="position:absolute;top:50%;left:${needle}%;transform:translate(-50%,-50%);width:14px;height:14px;border-radius:50%;background:var(--bg);border:3px solid ${color};box-shadow:0 0 8px ${color}80;${incomplete?"display:none":""}"></div>
    </div>
    <div style="display:flex;justify-content:space-between;font-family:var(--mn);font-size:7px;color:var(--t3);margin-top:5px">
      <span>Extreme Fear</span><span>Fear</span><span>Neutral</span><span>Greed</span><span>Extreme Greed</span>
    </div>
  </div>`;
}

// ═══════════════════════════════════════════════════════════
// ECONOMIC CALENDAR
// ═══════════════════════════════════════════════════════════
function renderCalendar(){
  const now=Date.now();
  const upcoming=EVENTS.filter(e=>e.ts>=now-86400000).slice(0,6);
  const catColor={Fed:"var(--bl)",Macro:"var(--gn)",Earnings:"var(--gd)",Holiday:"var(--t2)"};
  const impColor={high:"var(--rd)",medium:"var(--gd)",low:"var(--t3)"};
  let h=`<div class="gc" style="padding:14px">
    <div style="font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.18em;margin-bottom:10px">ECONOMIC CALENDAR · DESK MODEL</div>`;
  if(!upcoming.length){h+=`<div style="font-size:11px;color:var(--t3);text-align:center;padding:10px">No upcoming model events in window</div>`;}
  upcoming.forEach((e,i)=>{
    const daysAway=Math.ceil((e.ts-now)/86400000);
    const soon=daysAway<=2;
    const cc=catColor[e.cat]||"var(--bl)";
    const ic=impColor[e.impact]||"var(--t3)";
    h+=`<div class="cal-row" style="${i===0?"border-top:1px solid var(--gb)":""}">
      <div class="cal-date" style="color:${soon?"var(--gd)":"var(--t3)"}">${e.date}</div>
      <div style="flex:1">
        <div style="font-size:11px;font-weight:600;color:var(--tx);line-height:1.3">${e.event}</div>
        <div style="display:flex;gap:4px;margin-top:3px">${bd(e.cat,cc)}<span style="font-family:var(--mn);font-size:7.5px;color:${ic};align-self:center">${e.impact.toUpperCase()}</span></div>
      </div>
      ${soon?`<div style="font-family:var(--mn);font-size:8px;color:var(--gd);font-weight:700;flex-shrink:0">${daysAway<=0?"TODAY":daysAway+"d"}</div>`:""}
    </div>`;
  });
  h+=`</div>`;
  return h;
}

// ═══════════════════════════════════════════════════════════
// PRICE ALERTS
// ═══════════════════════════════════════════════════════════
function addAlert(tk,targetPrice,dir){
  const sym=typeof resolveInternalTicker==="function"?resolveInternalTicker(tk):String(tk||"").toUpperCase();
  const t=parseFloat(targetPrice);
  if(!sym){showToast("Select a ticker first","var(--rd)");return;}
  if(!isFinite(t)||t<=0){showToast("Enter a valid target price","var(--rd)");return;}
  const d=dir==="below"?"below":"above";
  alerts=alerts.filter(a=>!(a.tk===sym&&a.dir===d));
  alerts.push({tk:sym,targetPrice:t,dir:d,active:true,ts:Date.now()});
  localStorage.setItem("td_alerts",JSON.stringify(alerts));
  showToast(`Alert set: ${sym} ${d==="above"?"≥":"≤"} $${t}`,"var(--gd)");
  if (IS_DESKTOP() && termSelTk) renderP2();
  else _refreshView();
}
function removeAlert(idx){
  if(!isFinite(idx)||idx<0||idx>=alerts.length)return;
  alerts.splice(idx,1);
  localStorage.setItem("td_alerts",JSON.stringify(alerts));
  if (IS_DESKTOP() && termSelTk) renderP2();
  else _refreshView();
}
function checkAlerts(){
  let triggered=false;
  alerts.forEach((a,i)=>{
    if(!a.active)return;
    const price=livePx(a.tk);
    if(!price)return;
    if(a.dir==="above"&&price>=a.targetPrice){
      showToast(`🔔 ${a.tk} hit $${price.toFixed(2)} — target ≥$${a.targetPrice}`,"var(--gn)");
      alerts[i].active=false;triggered=true;
    } else if(a.dir==="below"&&price<=a.targetPrice){
      showToast(`🔔 ${a.tk} hit $${price.toFixed(2)} — target ≤$${a.targetPrice}`,"var(--rd)");
      alerts[i].active=false;triggered=true;
    }
  });
  if(triggered)localStorage.setItem("td_alerts",JSON.stringify(alerts));
}

// ═══════════════════════════════════════════════════════════
// PORTFOLIO TRACKER
// ═══════════════════════════════════════════════════════════
let _portDraft={tk:"",qty:"",cost:""};
function _syncPortDraft(){
  const tkEl=document.getElementById("port-tk");
  const qtyEl=document.getElementById("port-qty");
  const costEl=document.getElementById("port-cost");
  if(tkEl) _portDraft.tk=tkEl.value||"";
  if(qtyEl) _portDraft.qty=qtyEl.value||"";
  if(costEl) _portDraft.cost=costEl.value||"";
}
function _sanitizePortfolio(){
  const before=portfolio.length;
  portfolio=portfolio.filter(p=>p&&p.tk&&isFinite(+p.qty)&&+p.qty>0&&isFinite(+p.avgCost)&&+p.avgCost>=0);
  if(portfolio.length!==before) localStorage.setItem("td_port",JSON.stringify(portfolio));
}
_sanitizePortfolio();
/** Mark-to-market helper — never treat fp().p "—" as a number; unpriced → cost basis */
function _portMark(pos){
  const qty=Number(pos?.qty);
  const avg=Number(pos?.avgCost);
  const q=isFinite(qty)&&qty>0?qty:0;
  const costUnit=isFinite(avg)&&avg>=0?avg:0;
  const live=livePx(pos?.tk);
  const chg=liveChg(pos?.tk);
  if(live!=null){
    const value=live*q;
    const cost=costUnit*q;
    const pnl=value-cost;
    const pnlPct=cost? (pnl/cost*100) : 0;
    return {px:live,value,cost,pnl,pnlPct,live:true,chg:chg!=null?chg:null};
  }
  return {px:costUnit,value:costUnit*q,cost:costUnit*q,pnl:null,pnlPct:null,live:false,chg:null};
}
function addPosition(tk,qty,avgCost){
  const raw=String(tk||"").trim();
  const sym=(typeof resolveInternalTicker==="function"?resolveInternalTicker(raw):"")||sanitizeTicker(raw)||raw.toUpperCase();
  const q=parseFloat(qty), c=parseFloat(avgCost);
  if(!sym){showToast("Enter a ticker first","var(--rd)");return false;}
  if(!isFinite(q)||q<=0){showToast("Enter a valid quantity","var(--rd)");return false;}
  if(!isFinite(c)||c<0){showToast("Enter a valid average cost","var(--rd)");return false;}
  const existing=portfolio.findIndex(p=>p.tk===sym);
  if(existing>-1)portfolio.splice(existing,1);
  portfolio.push({tk:sym,qty:q,avgCost:c,addedAt:Date.now()});
  localStorage.setItem("td_port",JSON.stringify(portfolio));
  _portDraft={tk:"",qty:"",cost:""};
  // Kick a quote fetch so mark-to-market can land (CG for desk crypto; Yahoo otherwise)
  if(!liveSymbols.has(sym)){
    const cgId=typeof _cgIdForTicker==="function"?_cgIdForTicker(sym):null;
    if(cgId){
      try{
        cgFetch(`https://api.coingecko.com/api/v3/simple/price?ids=${encodeURIComponent(cgId)}&vs_currencies=usd&include_24hr_change=true`,{signal:AbortSignal.timeout(9000)})
          .then(r=>r.ok?r.json():null).then(d=>{
            const row=d&&d[cgId];
            if(row?.usd>0&&_applyLiveQuote(sym,{p:row.usd,c:typeof row.usd_24h_change==="number"?row.usd_24h_change:0,prev:row.usd/(1+(row.usd_24h_change||0)/100)},"coingecko"))_refreshView();
          }).catch(()=>{});
      }catch(e){}
    }else{
      try{ fetch(`/api/yahoo-quote?symbols=${encodeURIComponent((typeof YAHOO_SYMBOLS!=="undefined"&&YAHOO_SYMBOLS[sym])||sym)}`,{signal:AbortSignal.timeout(8000)})
        .then(r=>r.ok?r.json():null).then(data=>{
          if(!data)return;
          const yh=(typeof YAHOO_SYMBOLS!=="undefined"&&YAHOO_SYMBOLS[sym])||sym;
          const qrow=data[yh]||data[sym];
          if(qrow&&_applyLiveQuote(sym,qrow,"yahoo")){_refreshView();}
        }).catch(()=>{}); }catch(e){}
    }
  }
  showToast(`Added ${q} × ${sym} @ $${c}`,"var(--gn)");
  _refreshView();
  return true;
}
function addPositionFromForm(){
  _syncPortDraft();
  return addPosition(_portDraft.tk, _portDraft.qty, _portDraft.cost);
}
function removePosition(tk){
  portfolio=portfolio.filter(p=>p.tk!==tk);
  localStorage.setItem("td_port",JSON.stringify(portfolio));
  _refreshView();
}
// ── Portfolio analytics helpers ──
function _parseMc(s){if(!s||s==='-')return 0;const n=parseFloat(s.replace(/[$,\s]/g,''));if(s.includes('T'))return n*1e12;if(s.includes('B'))return n*1e9;if(s.includes('M'))return n*1e6;return n||0;}
function _portDonut(portfolio){
  const cats={},colors={Stock:'#4F8EF7',Crypto:'#9B6DFF',Commodity:'#F5A623',FX:'#00D4F5',Other:'#7A8BAA'};
  let total=0;
  portfolio.forEach(pos=>{const a=A.find(x=>x.tk===pos.tk);const val=_portMark(pos).value;const cat=a?.cat||'Other';cats[cat]=(cats[cat]||0)+val;total+=val;});
  if(total===0)return '';
  const r=44,cx=60,cy=60,C=2*Math.PI*r;
  let arcs='',legend='',accPct=0;
  for(const[cat,val]of Object.entries(cats)){
    if(!val)continue;const pct=val/total;const dash=pct*C;const gap=C-dash;const offset=C*(1-accPct);const col=colors[cat]||'#7A8BAA';
    arcs+=`<circle r="${r}" cx="${cx}" cy="${cy}" fill="none" stroke="${col}" stroke-width="20" stroke-dasharray="${dash.toFixed(2)} ${gap.toFixed(2)}" stroke-dashoffset="${offset.toFixed(2)}" transform="rotate(-90 ${cx} ${cy})"/>`;
    accPct+=pct;
    legend+=`<div style="display:flex;align-items:center;gap:6px;margin-bottom:5px"><span style="width:8px;height:8px;border-radius:50%;background:${col};flex-shrink:0;display:inline-block"></span><span style="color:var(--t2);font-size:10px">${cat}</span><span style="color:var(--tx);font-family:var(--mn);font-size:10px;margin-left:auto;font-weight:700">${(pct*100).toFixed(0)}%</span></div>`;
  }
  const ts='$'+total.toLocaleString(undefined,{maximumFractionDigits:0});
  return `<div style="display:flex;align-items:center;gap:16px"><div style="flex-shrink:0"><svg width="120" height="120" viewBox="0 0 120 120"><circle r="${r}" cx="${cx}" cy="${cy}" fill="none" stroke="var(--b3)" stroke-width="20"/>${arcs}<text x="${cx}" y="${cy-5}" text-anchor="middle" fill="var(--t3)" font-size="8" font-family="JetBrains Mono" letter-spacing="0.05em">TOTAL</text><text x="${cx}" y="${cy+8}" text-anchor="middle" fill="var(--tx)" font-size="${ts.length>9?8:10}" font-family="JetBrains Mono" font-weight="800">${ts}</text></svg></div><div style="flex:1">${legend}</div></div>`;
}
function _savePvSnapshot(total){
  if(total<=0)return;const today=new Date().toISOString().slice(0,10);
  let pvh=_lsJson(localStorage.getItem('td_pvh'),{});pvh[today]=total;
  const keys=Object.keys(pvh).sort().slice(-30);const trimmed={};keys.forEach(k=>trimmed[k]=pvh[k]);
  localStorage.setItem('td_pvh',JSON.stringify(trimmed));
}
function _portSparkline(){
  const pvh=_lsJson(localStorage.getItem('td_pvh'),{});const vals=Object.values(pvh);
  if(vals.length<2)return '<div style="font-family:var(--mn);font-size:9px;color:var(--t3);margin-top:6px">Value history builds over time</div>';
  const W=180,H=44,pad=4;const mn=Math.min(...vals),mx=Math.max(...vals);const range=mx-mn||1;
  const pts=vals.map((v,i)=>{const x=pad+(i/(vals.length-1))*(W-pad*2);const y=H-pad-((v-mn)/range)*(H-pad*2);return `${x.toFixed(1)},${y.toFixed(1)}`;}).join(' ');
  const last=vals[vals.length-1],first=vals[0];const up=last>=first;
  const col=up?'var(--gn)':'var(--rd)';const pctChg=((last-first)/first*100).toFixed(1);
  return `<div style="margin-top:8px"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.1em;margin-bottom:4px">30-DAY VALUE HISTORY</div>
    <div style="display:flex;align-items:center;gap:12px"><svg width="${W}" height="${H}" style="display:block"><polyline points="${pts}" fill="none" stroke="${col}" stroke-width="1.5" stroke-linejoin="round"/></svg>
    <div style="font-family:var(--mn);font-size:12px;font-weight:800;color:${col}">${up?'+':''}${pctChg}%</div></div></div>`;
}

function renderPortfolio(){
  let totalValue=0,totalCost=0;
  let h = _renderPgHdr("Portfolio", "Track your positions · saved locally");
  h += _renderSiteIntelCard("portfolio");
  h+=`<div class="qa-row" style="grid-template-columns:repeat(3,1fr);margin-bottom:10px">
    <button class="qa-btn" onclick="runPortfolioScan()"><span class="qa-ico">◎</span><span>Scan</span></button>
    <button class="qa-btn" onclick="nav('mkt')"><span class="qa-ico">▦</span><span>Markets</span></button>
    <button class="qa-btn qa-gold" onclick="toggleChat()"><span class="qa-ico">⬡</span><span>Expert</span></button>
  </div>`;

  // Free-text ticker + curated datalist — book can hold dyn/lookup names
  const assetOptions=A.map(a=>`<option value="${a.tk}">${a.tk} — ${a.nm}</option>`).join("");
  h+=`<div class="gc" style="padding:14px">
    <div style="font-size:11px;font-weight:700;margin-bottom:10px">Add Position</div>
    <div class="port-add">
      <input id="port-tk" class="port-inp" list="port-tk-list" placeholder="Ticker (AAPL, BTC, RELIANCE.NS…)" autocomplete="off" spellcheck="false" value="${_escAttr(_portDraft.tk)}" oninput="_portDraft.tk=this.value.toUpperCase()" style="text-transform:uppercase">
      <datalist id="port-tk-list">${assetOptions}</datalist>
      <div style="display:flex;gap:8px">
        <input id="port-qty" class="port-inp" type="number" placeholder="Quantity (shares/units)" min="0" step="any" style="flex:1" value="${_escAttr(_portDraft.qty)}" oninput="_portDraft.qty=this.value">
        <input id="port-cost" class="port-inp" type="number" placeholder="Avg cost ($)" min="0" step="any" style="flex:1" value="${_escAttr(_portDraft.cost)}" oninput="_portDraft.cost=this.value">
      </div>
      <button type="button" onclick="addPositionFromForm()" style="background:var(--gd);color:var(--bg);border:none;border-radius:8px;padding:10px;font-family:var(--sn);font-size:12px;font-weight:700;cursor:pointer">Add to Portfolio</button>
    </div>
  </div>`;

  if(!portfolio.length){
    h+=`<div class="gc" style="padding:24px;text-align:center"><div style="font-size:12px;color:var(--t2)">No positions yet — add your first above</div></div>`;
    h+=_renderSmartAlertsPanel();
    return h;
  }

  // Compute totals — unpriced names mark at cost (never $0 → fake -100% P&L)
  let liveValue=0, liveCost=0, unpriced=0;
  portfolio.forEach(pos=>{
    const m=_portMark(pos);
    totalValue+=m.value; totalCost+=m.cost;
    if(m.live){ liveValue+=m.value; liveCost+=m.cost; }
    else unpriced++;
  });
  _savePvSnapshot(totalValue);
  const hasLivePnl=liveCost>0;
  const totalPnl0=hasLivePnl?liveValue-liveCost:null;
  const totalPnlPct0=hasLivePnl&&liveCost?((totalPnl0/liveCost)*100):null;
  const totCol0=totalPnl0==null?"var(--t3)":totalPnl0>=0?"var(--gn)":"var(--rd)";
  const pnlLbl=totalPnl0==null?"—":`${totalPnl0>=0?"+":""}$${Math.abs(totalPnl0).toLocaleString(undefined,{maximumFractionDigits:0})}`;
  const retLbl=totalPnlPct0==null?"—":`${totalPnl0>=0?"+":""}${totalPnlPct0.toFixed(1)}%`;

  // Analytics card
  const donut=_portDonut(portfolio);
  if(donut){
    h+=`<div class="gc" style="padding:14px;margin-bottom:6px">
      <div style="font-family:var(--mn);font-size:9px;color:var(--gd);letter-spacing:0.18em;margin-bottom:12px">PORTFOLIO ANALYTICS${unpriced?` · ${unpriced} at cost`:""}</div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:4px;margin-bottom:12px">
        <div style="text-align:center;padding:8px;background:var(--b1);border-radius:6px"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.1em">TOTAL VALUE</div><div style="font-family:var(--mn);font-size:14px;font-weight:800;color:var(--tx);margin-top:3px">$${totalValue.toLocaleString(undefined,{maximumFractionDigits:0})}</div></div>
        <div style="text-align:center;padding:8px;background:var(--b1);border-radius:6px"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.1em">TOTAL P&L</div><div style="font-family:var(--mn);font-size:14px;font-weight:800;color:${totCol0};margin-top:3px">${pnlLbl}</div></div>
        <div style="text-align:center;padding:8px;background:var(--b1);border-radius:6px"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.1em">RETURN</div><div style="font-family:var(--mn);font-size:14px;font-weight:800;color:${totCol0};margin-top:3px">${retLbl}</div></div>
      </div>
      ${donut}
      ${_portSparkline()}
    </div>`;
  }

  h += _renderPortfolioRiskCenter();
  h += _renderPortfolioChokepointExposure();
  h += _renderSmartAlertsPanel();

  // Reset for per-row calculation
  totalValue=0;totalCost=0;

  // Positions
  h+=`<div class="gc" style="padding:14px">
    <div style="font-size:11px;font-weight:700;margin-bottom:10px">Holdings</div>`;
  portfolio.forEach(pos=>{
    const qty=Number(pos.qty), avg=Number(pos.avgCost);
    if(!isFinite(qty)||!isFinite(avg))return;
    const m=_portMark(pos);
    totalValue+=m.value;totalCost+=m.cost;
    const col=m.pnl==null?"var(--t3)":m.pnl>=0?"var(--gn)":"var(--rd)";
    const a=A.find(x=>x.tk===pos.tk);
    const pnlHtml=m.live&&m.pnl!=null
      ?`${m.pnl>=0?"+":""}$${Math.abs(m.pnl).toLocaleString(undefined,{maximumFractionDigits:2})} (${m.pnl>=0?"+":""}${m.pnlPct.toFixed(1)}%)`
      :`at cost · NO SYNC`;
    h+=`<div style="border-top:1px solid var(--gb);padding:10px 0">
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div>
          <div style="display:flex;align-items:center;gap:6px">
            <span style="font-family:var(--mn);font-weight:800;font-size:13px">${pos.tk}</span>
            ${a?bd(a.cat,catBd(a.cat)):""}
            ${m.live?stat(pos.tk):`<span class="bd" style="background:var(--b3);color:var(--t3);font-size:7.5px">NO SYNC</span>`}
          </div>
          <div style="font-size:9px;color:var(--t3);font-family:var(--mn);margin-top:2px">${qty} units · avg $${avg.toFixed(2)}${m.live?` · mkt $${m.px.toFixed(2)}`:""}</div>
          <div style="font-size:9px;color:var(--t2);margin-top:2px">${a?.nm||""}</div>
        </div>
        <div style="text-align:right">
          <div style="font-family:var(--mn);font-weight:700;font-size:13px">$${m.value.toLocaleString(undefined,{maximumFractionDigits:2})}</div>
          <div style="font-family:var(--mn);font-size:10px;color:${col}">${pnlHtml}</div>
          <button onclick="removePosition('${pos.tk}')" style="background:var(--rdG);color:var(--rd);border:1px solid rgba(239,68,68,0.2);border-radius:5px;padding:2px 8px;font-size:8px;font-family:var(--mn);cursor:pointer;margin-top:4px">Remove</button>
        </div>
      </div>
    </div>`;
  });

  // Footer honesty: no live marks → "at cost", never green +0% as if flat live
  const anyLiveMark=portfolio.some(pos=>_portMark(pos).live);
  const totalPnl=anyLiveMark?(totalValue-totalCost):null;
  const totalPnlPct=(anyLiveMark&&totalCost)?((totalPnl/totalCost)*100):null;
  const totCol=totalPnl==null?"var(--t3)":totalPnl>=0?"var(--gn)":"var(--rd)";
  const footPnl=totalPnl==null
    ?"at cost · NO SYNC"
    :`${totalPnl>=0?"+":""}$${Math.abs(totalPnl).toLocaleString(undefined,{maximumFractionDigits:2})} (${totalPnl>=0?"+":""}${totalPnlPct.toFixed(1)}%)`;
  h+=`<div style="border-top:2px solid var(--gd);padding-top:10px;margin-top:4px;display:flex;justify-content:space-between;align-items:center">
    <div style="font-size:11px;font-weight:700;color:var(--gd)">Total Portfolio</div>
    <div style="text-align:right">
      <div style="font-family:var(--mn);font-weight:800;font-size:16px">$${totalValue.toLocaleString(undefined,{maximumFractionDigits:2})}</div>
      <div style="font-family:var(--mn);font-size:10px;color:${totCol}">${footPnl}</div>
    </div>
  </div>
  <div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap">
    <button onclick="runPortfolioScan()" style="flex:1;min-width:140px;background:linear-gradient(135deg,var(--blG),transparent);color:var(--bl);border:1px solid rgba(79,142,247,0.25);border-radius:9px;padding:11px;font-family:var(--sn);font-size:12px;font-weight:700;cursor:pointer">⬢ Regime Scan</button>
    ${_portAiLoading?`<div style="flex:1;min-width:140px;display:flex;align-items:center;gap:8px;background:var(--b1);border:1px solid var(--gb);border-radius:9px;padding:11px"><div style="width:12px;height:12px;border:2px solid var(--gd);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;flex-shrink:0"></div><span style="font-family:var(--mn);font-size:10px;color:var(--gd)">AI ANALYSING…</span></div>`:
    `<button onclick="runPortfolioAI()" style="flex:1;min-width:140px;background:linear-gradient(135deg,var(--blG),rgba(245,158,11,0.05));color:var(--gd);border:1px solid rgba(245,158,11,0.3);border-radius:9px;padding:11px;font-family:var(--sn);font-size:12px;font-weight:700;cursor:pointer;letter-spacing:0.02em">⬢ AI Portfolio Analysis${_isPremium()?'':'  ★ Premium'}</button>`}
    <button onclick="exportPortfolioCSV()" style="background:var(--b1);border:1px solid var(--gb);border-radius:9px;padding:11px 14px;color:var(--t2);font-family:var(--sn);font-size:12px;cursor:pointer" title="Export to CSV${_isPremium()?'':' (Premium)'}">↓ CSV${_isPremium()?'':'★'}</button>
  </div>
  </div>`;
  h += _renderPortScan();
  if(_portAiResult)h+=renderPortfolioAI(_portAiResult);

  // Active alerts
  const activeAlerts=alerts.filter(a=>a.active);
  if(activeAlerts.length){
    h+=`<div class="gc" style="padding:14px">
      <div style="font-size:11px;font-weight:700;margin-bottom:8px">Active Price Alerts</div>`;
    activeAlerts.forEach((a)=>{
      const col=a.dir==="above"?"var(--gn)":"var(--rd)";
      // Index into full alerts[] — filtered active list indices are wrong after triggers
      const idx=alerts.findIndex(x=>x===a);
      h+=`<div class="alert-chip" style="border-color:${col}30;margin-bottom:4px;display:flex;justify-content:space-between;width:100%">
        <span style="color:var(--tx)">${a.tk} ${a.dir==="above"?"≥":"≤"} <strong style="color:${col}">$${a.targetPrice}</strong></span>
        <span onclick="removeAlert(${idx})" style="color:var(--rd);cursor:pointer;padding-left:8px">✕</span>
      </div>`;
    });
    h+=`</div>`;
  }
  return h;
}

// ─── Settings overlay ───
function openSettings(){
  let el=document.getElementById('settingsOv');
  if(el){el.remove();settingsOpen=false;return;}
  settingsOpen=true;
  el=document.createElement('div');
  el.id='settingsOv';
  el.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,0.8);z-index:700;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(6px)';
  el.innerHTML=`<div style="background:var(--b2);border:1px solid var(--b3);border-radius:14px;padding:0;max-width:460px;width:92%;max-height:85vh;overflow:hidden;box-shadow:var(--shadow-lg);display:flex;flex-direction:column">
    <div style="display:flex;justify-content:space-between;align-items:center;padding:20px 24px;border-bottom:1px solid var(--gb)">
      <div style="font-family:var(--sn);font-size:18px;font-weight:800">Settings</div>
      <button onclick="document.getElementById('settingsOv').remove();settingsOpen=false" style="background:var(--b3);border:none;color:var(--t2);border-radius:50%;width:30px;height:30px;cursor:pointer;font-size:16px">×</button>
    </div>
    <div style="padding:14px 24px;background:var(--b1);border-bottom:1px solid var(--gb);display:flex;align-items:center;justify-content:space-between;gap:10px">
      ${_isPremium()?`<div style="display:flex;align-items:center;gap:8px"><span style="font-family:var(--mn);font-size:9px;font-weight:700;color:var(--gd);letter-spacing:0.12em">★ PREMIUM</span><span style="font-family:var(--sn);font-size:12px;color:var(--t2)">All features unlocked</span></div><a href="/__auth/logout" style="font-family:var(--mn);font-size:9px;color:var(--t3);text-decoration:none;padding:5px 10px;border:1px solid var(--b4);border-radius:5px" onmouseover="this.style.borderColor='var(--rd)';this.style.color='var(--rd)'" onmouseout="this.style.borderColor='var(--b4)';this.style.color='var(--t3)'">Sign Out</a>`:`<div style="display:flex;flex-direction:column;gap:4px"><span style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.12em">FREE TIER</span><span style="font-family:var(--sn);font-size:12px;color:var(--t2)">Subscribe → pay → set password → premium</span></div><div style="display:flex;gap:6px;flex-shrink:0"><a href="/__auth/subscribe" style="font-family:var(--mn);font-size:9px;font-weight:700;color:var(--bg);background:var(--gd);text-decoration:none;padding:5px 12px;border-radius:5px">Subscribe</a><a href="/__auth/login" style="font-family:var(--mn);font-size:9px;font-weight:600;color:var(--t2);text-decoration:none;padding:5px 10px;border:1px solid var(--b4);border-radius:5px">Sign In</a></div>`}
    </div>
    <div style="overflow-y:auto;padding:20px 24px;display:flex;flex-direction:column;gap:20px">

      <!-- Panel Visibility -->
      <div>
        <div style="font-family:var(--mn);font-size:10px;color:var(--gd);letter-spacing:0.18em;margin-bottom:12px">PANEL VISIBILITY</div>
        ${[['p1','[1] Markets'],['p2','[2] News / Analysis'],['p3','[3] Signals & Calendar'],['p4','[4] Indices & Watchlist']].map(([id,label])=>`
        <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.04)">
          <span style="font-family:var(--sn);font-size:13px;color:var(--tx)">${label}</span>
          <label style="position:relative;width:40px;height:22px;cursor:pointer">
            <input type="checkbox" ${panelVis[id]?'checked':''} onchange="togglePanelVis('${id}',this.checked)" style="opacity:0;width:0;height:0">
            <span style="position:absolute;inset:0;background:${panelVis[id]?'var(--gn)':'var(--b4)'};border-radius:22px;transition:0.2s;display:block" id="tog-${id}"></span>
            <span style="position:absolute;top:3px;left:${panelVis[id]?'21':'3'}px;width:16px;height:16px;background:white;border-radius:50%;transition:0.2s;display:block" id="togknob-${id}"></span>
          </label>
        </div>`).join('')}
        <button onclick="resetPanelLayout()" style="margin-top:10px;background:var(--b3);border:1px solid var(--gb);border-radius:7px;padding:8px 16px;color:var(--t2);font-family:var(--mn);font-size:10px;cursor:pointer;width:100%">Reset to Default Layout</button>
      </div>

      <!-- Update Frequency -->
      <div>
        <div style="font-family:var(--mn);font-size:10px;color:var(--gd);letter-spacing:0.18em;margin-bottom:12px">PRICE UPDATE FREQUENCY</div>
        <div style="display:flex;gap:6px;flex-wrap:wrap">
          ${[[5,'5s'],[15,'15s'],[30,'30s'],[60,'60s'],[0,'Manual']].map(([f,l])=>`<button onclick="setUpdateFreq(${f})" style="font-family:var(--mn);font-size:11px;font-weight:700;padding:6px 14px;border-radius:6px;cursor:pointer;border:1px solid ${updateFreq===f?'var(--gd)':'var(--b4)'};background:${updateFreq===f?'var(--gdG)':'transparent'};color:${updateFreq===f?'var(--gd)':'var(--t2)'}" id="freq-${f}">${l}</button>`).join('')}
        </div>
        <div style="font-family:var(--mn);font-size:10px;color:var(--t3);margin-top:8px">News updates every 10 minutes regardless of price frequency.</div>
      </div>

      <!-- Watchlist Management -->
      <div>
        <div style="font-family:var(--mn);font-size:10px;color:var(--gd);letter-spacing:0.18em;margin-bottom:12px">WATCHLISTS</div>
        ${watchlists.map(wl=>`<div style="display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.04)">
          <span style="font-family:var(--sn);font-size:13px;color:var(--tx);flex:1">${wl.name}</span>
          <span style="font-family:var(--mn);font-size:10px;color:var(--t3)">${wl.tickers.length} assets</span>
          <button onclick="_renameWl('${wl.id}')" style="background:var(--b3);border:none;color:var(--t2);border-radius:5px;padding:4px 10px;font-family:var(--mn);font-size:10px;cursor:pointer">Rename</button>
          <button onclick="deleteWatchlist('${wl.id}');openSettings();openSettings()" style="background:var(--rdG);border:1px solid rgba(255,71,87,0.2);color:var(--rd);border-radius:5px;padding:4px 10px;font-family:var(--mn);font-size:10px;cursor:pointer">Delete</button>
        </div>`).join('')}
        <button onclick="_newWl();openSettings();openSettings()" style="margin-top:10px;background:var(--b3);border:1px dashed var(--b4);border-radius:7px;padding:8px 16px;color:var(--t2);font-family:var(--mn);font-size:10px;cursor:pointer;width:100%">+ Create New Watchlist</button>
      </div>

      <!-- About & Disclaimer -->
      <div>
        <div style="font-family:var(--mn);font-size:10px;color:var(--gd);letter-spacing:0.18em;margin-bottom:12px">ABOUT & DISCLAIMER</div>
        <div style="background:var(--b1);border:1px solid var(--gb);border-radius:10px;padding:16px">
          <div style="font-family:var(--mn);font-size:9px;color:var(--gd);letter-spacing:0.18em;text-align:center;margin-bottom:6px">— THE DISPATCH MARKETS · THEDISPATCH.UK —</div>

          <div style="font-family:var(--sn);font-size:10px;color:var(--t3);line-height:1.6">
            <strong style="color:var(--gd)">Disclaimer.</strong> The Dispatch Markets is for educational, analytical, and research purposes only. Nothing on this site is financial advice, investment advice, trading instruction, or a recommendation to buy or sell any security, commodity, cryptocurrency, derivative, or financial instrument. Market data may be delayed, incomplete, or inaccurate; AI-generated outputs may contain errors. You are responsible for your own research and decisions.
          </div>
        </div>
      </div>

    </div>
  </div>`;
  document.body.appendChild(el);
  el.addEventListener('click',e=>{if(e.target===el){el.remove();settingsOpen=false;}});
}

function togglePanelVis(id,show){
  panelVis[id]=show;savePanelVis();
  const panel=document.getElementById(id);
  if(panel){panel.style.display=show?'flex':'none';}
  const tog=document.getElementById('tog-'+id);
  const knob=document.getElementById('togknob-'+id);
  if(tog)tog.style.background=show?'var(--gn)':'var(--b4)';
  if(knob)knob.style.left=show?'21px':'3px';
}

function resetPanelLayout(){
  panelVis={p1:true,p2:true,p3:true,p4:true};
  savePanelVis();
  ['p1','p2','p3','p4'].forEach(id=>{
    const p=document.getElementById(id);
    if(p)p.style.display='flex';
  });
  openSettings();openSettings(); // refresh
  showToast('Layout reset to default','var(--gn)');
}

function setUpdateFreq(freq){
  updateFreq=freq;saveFreq();
  _restartIntervals();
  // Single re-open refreshes settings panel (was double-called → flicker)
  if(typeof openSettings==="function")openSettings();
  showToast(freq===0?'Manual updates only':`Updates every ${freq}s`,'var(--bl)');
}

function togglePause(){
  updatePaused=!updatePaused;
  const btn=document.getElementById('pauseBtn');
  const dot=document.getElementById('liveDot');
  if(updatePaused){
    if(_priceInterval)clearInterval(_priceInterval);
    if(btn){btn.textContent='▶';btn.style.color='var(--gd)';}
    if(dot){dot.style.background='var(--gd)';dot.style.animation='none';}
    showToast('Live updates paused','var(--gd)');
  } else {
    _restartIntervals();
    fetchLivePrices();
    if(btn){btn.textContent='⏸';btn.style.color='var(--t2)';}
    if(dot){dot.style.background='var(--gn)';dot.style.animation='pls 2s infinite';}
    showToast('Live updates resumed','var(--gn)');
  }
}

function _restartIntervals(){
  if(_priceInterval)clearInterval(_priceInterval);
  if(updateFreq>0&&!updatePaused){
    const isM = MOBILE();
    const freq = isM ? Math.max(updateFreq, MOBILE_PRICE_FREQ) : updateFreq;
    _priceInterval=setInterval(fetchLivePrices, freq * 1000);
  }
}

function _renameWl(id){
  const wl=watchlists.find(w=>w.id===id);
  if(!wl)return;
  const name=prompt('New name:',wl.name);
  if(name&&name.trim()){renameWatchlist(id,name.trim());openSettings();openSettings();}
}

// ─── Product onboarding (Brief → Lens → Journal workflow) ───
let _onboardStep = 0;
const _ONBOARD_PICKS = ["NVDA", "SPY", "AAPL", "BTC", "XAU"];

function _onboardPick(tk) {
  if (!getActiveWl().tickers.includes(tk)) addToWatchlist(tk);
  watch = getActiveWl().tickers;
  _renderOnboardStep();
}

function _finishOnboarding(goRun) {
  localStorage.setItem("td_onboard_v1", "1");
  localStorage.setItem("td_onboard_v2", "1");
  localStorage.setItem("td_guided", "1");
  document.getElementById("onboardOv")?.remove();
  nav("gold");
  if (goRun) {
    setTimeout(() => loadGoldDesk(true), 200);
    showToast("Your weekly gold playbook is loading…", "var(--gd)");
  } else {
    showToast("Open Gold anytime from the sidebar", "var(--gd)");
  }
}

function _renderOnboardStep() {
  const body = document.getElementById("onboardBody");
  if (!body) return;
  if (_onboardStep === 0) {
    body.innerHTML = `<div style="text-align:center;margin-bottom:16px">
      <div style="font-family:var(--sf);font-size:24px;line-height:1.2">Know what matters <em style="color:var(--gd);font-style:italic">before gold moves</em>.</div>
      <div style="font-size:12px;color:var(--t2);margin-top:10px;line-height:1.6">Gold desk · conditional weekly playbook · your own AI keys next. Not four chatbots.</div>
    </div>
    <ol class="start-here-steps" style="text-align:left">
      <li><strong>Gold Dashboard</strong> — structure, S/R, volume, sessions, DXY & yields</li>
      <li><strong>Weekly Playbook</strong> — bull / bear / range with if-then levels</li>
      <li><strong>BYOK AI</strong> — connect your keys; you control token cost (next)</li>
      <li><strong>Journal</strong> — your decision history becomes the moat (next)</li>
    </ol>`;
    document.getElementById("onboardBtn").textContent = "Open this week's gold playbook →";
    document.getElementById("onboardBtn").onclick = () => _finishOnboarding(true);
  } else {
    _finishOnboarding(true);
  }
}

function showProductOnboarding() {
  // A visitor should see the desk before being asked to choose a path. The Home
  // page already contains a clear "Start here" route, so use a one-time cue
  // rather than a blocking overlay.
  if (localStorage.getItem("td_onboard_v3")) return;
  localStorage.setItem("td_onboard_v3", "1");
  showToast("Welcome to The Dispatch — start with the Desk Run, search a ticker, or open Gold.", "var(--gd)");
}

// ─── First-time guide ───
function showGuide() {
  const existing = document.getElementById('guideOv');
  if (existing) { existing.remove(); return; }
  const div = document.createElement('div');
  div.id = 'guideOv';
  div.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.85);z-index:700;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(6px)';
  div.innerHTML = `<div style="background:var(--b2);border:1px solid var(--b3);border-radius:14px;padding:28px;max-width:440px;width:92%;max-height:80vh;overflow-y:auto;box-shadow:0 8px 32px rgba(0,0,0,0.6)">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
      <div>
        <div style="font-family:var(--sf);font-size:26px;font-weight:400">Welcome to <em style="font-style:italic;color:var(--gd)">The Dispatch</em></div>
        <div style="font-family:var(--mn);font-size:10px;color:var(--t3);letter-spacing:0.15em;margin-top:4px">AI MARKET INTELLIGENCE TERMINAL</div>
      </div>
      <button onclick="document.getElementById('guideOv').remove()" style="background:var(--b3);border:none;color:var(--t2);border-radius:50%;width:28px;height:28px;cursor:pointer;font-size:16px">×</button>
    </div>
    <div style="display:flex;flex-direction:column;gap:14px">
      <div style="background:var(--b1);border-radius:10px;padding:14px">
        <div style="font-family:var(--mn);font-size:9px;color:var(--gd);letter-spacing:0.15em;margin-bottom:8px">SEARCH ANY TICKER</div>
        <div style="font-family:var(--sn);font-size:13px;color:var(--t2);line-height:1.6">Type any stock, crypto, index or commodity in the search bar above. Examples: <span style="color:var(--gd);font-family:var(--mn)">AAPL</span>, <span style="color:var(--gd);font-family:var(--mn)">BTC</span>, <span style="color:var(--gd);font-family:var(--mn)">XAU</span>, <span style="color:var(--cy);font-family:var(--mn)">RELIANCE.NS</span></div>
      </div>
      <div style="background:var(--b1);border-radius:10px;padding:14px">
        <div style="font-family:var(--mn);font-size:9px;color:var(--gd);letter-spacing:0.15em;margin-bottom:8px">4-PANEL LAYOUT</div>
        <div style="font-family:var(--sn);font-size:13px;color:var(--t2);line-height:1.6"><strong style="color:var(--tx)">[1] Markets</strong> — all tracked assets with live prices<br><strong style="color:var(--tx)">[2] News/Analysis</strong> — live news or ticker deep-dive<br><strong style="color:var(--tx)">[3] Signals</strong> — conviction-weighted market signals<br><strong style="color:var(--tx)">[4] Indices & Watchlist</strong> — global markets at a glance</div>
      </div>
      <div style="background:var(--b1);border-radius:10px;padding:14px">
        <div style="font-family:var(--mn);font-size:9px;color:var(--gd);letter-spacing:0.15em;margin-bottom:8px">KEYBOARD SHORTCUTS</div>
        <div style="font-family:var(--sn);font-size:13px;color:var(--t2);line-height:1.8"><kbd style="background:var(--b3);padding:1px 7px;border-radius:3px;font-family:var(--mn);font-size:10px">/</kbd> Focus search · <kbd style="background:var(--b3);padding:1px 7px;border-radius:3px;font-family:var(--mn);font-size:10px">1-4</kbd> Expand panel · <kbd style="background:var(--b3);padding:1px 7px;border-radius:3px;font-family:var(--mn);font-size:10px">ESC</kbd> Close</div>
      </div>
      <div style="background:var(--gdG);border:1px solid rgba(245,166,35,0.15);border-radius:10px;padding:14px">
        <div style="font-family:var(--mn);font-size:9px;color:var(--gd);letter-spacing:0.15em;margin-bottom:6px">DISCLAIMER</div>
        <div style="font-family:var(--sn);font-size:11px;color:var(--t3);line-height:1.6">All scores, signals and AI analysis are for informational and research purposes only. Nothing on this platform constitutes financial advice or a recommendation to buy or sell any asset.</div>
      </div>
    </div>
    <button onclick="document.getElementById('guideOv').remove();localStorage.setItem('td_guided','1')" style="width:100%;background:var(--gd);color:var(--bg);border:none;border-radius:8px;padding:12px;font-family:var(--sn);font-size:14px;font-weight:700;cursor:pointer;margin-top:20px">Get Started →</button>
  </div>`;
  document.body.appendChild(div);
}

// ═══════════════════════════════════════════════════════════
// INTERACTIVE FEATURES
// ═══════════════════════════════════════════════════════════

// Price flash state
let _prevP={};
function _flashEl(el,up){el.classList.remove('fl-up','fl-dn');void el.offsetWidth;el.classList.add(up?'fl-up':'fl-dn');}
function _flashChanged(){
  Object.keys(P).forEach(tk=>{
    if(!liveSymbols.has(tk)){_prevP[tk]=P[tk]?.p;return;}
    const cur=P[tk]?.p;
    if(typeof cur!=="number"||!isFinite(cur)||cur<=0){_prevP[tk]=cur;return;}
    if(_prevP[tk]!==undefined&&_prevP[tk]!==cur){
      const up=cur>_prevP[tk];
      const d=fp(tk);
      document.querySelectorAll('[data-fl="'+tk+'"]').forEach(el=>{
        // Update the visible mark (flash alone left stale $ on desk tables)
        if(d.status!=="unavailable"){
          const isMoney=el.textContent.trim().startsWith("$")||el.closest("tr");
          el.textContent=(isMoney||el.dataset.money==="1")?"$"+d.p:d.p;
        }
        el.classList.remove('fl-up','fl-dn');
        void el.offsetWidth;
        el.classList.add(up?'fl-up':'fl-dn');
        el.classList.remove('roll-up','roll-dn');
        void el.offsetWidth;
        el.classList.add(up?'roll-up':'roll-dn');
      });
    }
    _prevP[tk]=cur;
  });
}

// Autocomplete
let _acIdx=-1,_acDebounce=null,_acLastQ='';

function _acRender(localHits,globalHits,q){
  const el=document.getElementById('cmdAc');
  if(!el)return;
  // Merge: local first (have live prices), then global results not already shown
  const localTks=new Set(localHits.map(a=>a.tk));
  // Rank Yahoo hits so TCS → TCS.NS not 0221.KL; RELIANCE → RELIANCE.NS not RS
  let globals=globalHits.filter(r=>r?.symbol&&!localTks.has(r.symbol)&&!localTks.has(resolveInternalTicker(r.symbol)));
  const best=typeof _bestYahooSearchMatch==="function"?_bestYahooSearchMatch(globals,q):null;
  if(best){
    globals=[best,...globals.filter(r=>r.symbol!==best.symbol)];
  }
  const merged=[
    ...localHits.map(a=>{
      const d=fp(a.tk);const na=d.status==="unavailable";
      const ch=liveChg(a.tk);
      const col=na||ch==null?"var(--t3)":ch>0?"var(--gn)":ch<0?"var(--rd)":"var(--t3)";
      const sign=ch!=null&&ch>=0?"+":"";
      const money=(a.cat==="Stock"||a.cat==="Crypto"||a.cat==="Commodity");
      return{tk:a.tk,name:a.nm,price:na?"":`${money?"$":""}${d.p}`,chg:na||ch==null?"":`${sign}${d.c}%`,chgCol:col,type:a.cat,local:true};
    }),
    ...globals.map(r=>({
      tk:r.symbol,name:r.name,price:'',chg:'',chgCol:'var(--t3)',type:r.type||'Stock',exchange:r.exchange,local:false
    }))
  ].slice(0,10);
  if(!merged.length){el.classList.remove('show');return;}
  el.innerHTML=merged.map((r,i)=>{
    const tkEsc=_escAttr(r.tk);
    const nmEsc=_escAttr(r.name||"");
    return `<div class="ac-item${i===_acIdx?' ac-focus':''}" onmousedown="event.preventDefault();_acPick('${String(r.tk).replace(/'/g,"")}')" title="${nmEsc}">
    <span class="ac-tk">${tkEsc}</span>
    <span class="ac-nm">${nmEsc}</span>
    ${r.price?`<span class="ac-pr">${r.price}</span><span style="color:${r.chgCol};font-family:var(--mn);font-size:9px;font-weight:700">${r.chg}</span>`:''}
    <span class="ac-cat">${_escAttr(String(r.type||"").slice(0,6).toUpperCase())}</span>
    ${r.exchange?`<span class="ac-cat" style="color:var(--cy)">${_escAttr(String(r.exchange).slice(0,6))}</span>`:''}
    ${!r.local?`<span class="ac-cat" style="background:var(--blG);color:var(--bl)">SEARCH</span>`:''}
  </div>`;
  }).join('');
  el.classList.add('show');
}

function _acShow(q){
  const el=document.getElementById('cmdAc');
  if(!el)return;
  if(!q){el.classList.remove('show');_acIdx=-1;clearTimeout(_acDebounce);return;}
  _acLastQ=q;
  const ql=q.toLowerCase();
  // 1. Instantly show local matches
  const localHits=A.filter(a=>a.tk.toLowerCase().startsWith(ql)||a.nm.toLowerCase().includes(ql)).slice(0,5);
  _acRender(localHits,[],q);
  // 2. Debounced global search (300ms)
  clearTimeout(_acDebounce);
  _acDebounce=setTimeout(async()=>{
    if(_acLastQ!==q)return;
    try{
      const res=await fetch(`/api/search?q=${encodeURIComponent(q)}`,{signal:AbortSignal.timeout(4000)});
      if(!res.ok)return;
      const data=await res.json();
      if(_acLastQ!==q)return; // query changed, discard
      _acRender(localHits,data.result||[],q);
    }catch(e){}
  },300);
}

function _acPick(tk,name){
  const el=document.getElementById('cmdAc');if(el)el.classList.remove('show');
  const inp=document.getElementById('cmdInput');if(inp)inp.value='';
  _acIdx=-1;clearTimeout(_acDebounce);_acLastQ='';
  // Prefer exact Yahoo wire symbol when user picked SEARCH hit (TCS.NS); resolve only aliases
  const raw=String(tk||"").trim();
  const desk=(typeof resolveInternalTicker==="function"?resolveInternalTicker(raw):"")||raw;
  // If pick is exchange-suffixed (RELIANCE.NS), lookup that symbol — not bare RELIANCE
  lookupTicker(/[.\-]/.test(raw)?raw:desk);
}
function _acNav(dir){
  const el=document.getElementById('cmdAc');if(!el||!el.classList.contains('show'))return;
  const items=el.querySelectorAll('.ac-item');
  _acIdx=Math.max(-1,Math.min(items.length-1,_acIdx+dir));
  items.forEach((it,i)=>it.classList.toggle('ac-focus',i===_acIdx));
}

// ─── Sidebar navigation — always real routes (never decorative) ───
const SB_MAP = {dash:'p2',mkt:'p1',news:'p2',sig:'p3',watch:'p4',settings:null};
function sbNav(section) {
  if (section === 'settings') { openSettings(); return; }
  // Collapse expanded panel when opening a full overlay page on desktop
  const overlayPages = ['dash','brief','gold','playbook','lab','port','intel','learn','sectors','heat','scr','geo','research','crypto','paper'];
  if (IS_DESKTOP() && overlayPages.includes(section) && _expPanel) toggleExpand(_expPanel);
  if (IS_DESKTOP() && section === 'dash') termClear();
  nav(section);
}

function _showOverlay(id, title, content) {
  const existing = document.getElementById(id);
  if (existing) { existing.remove(); return; }
  ['homeOv','dashOv','portOv','compareOv','briefOv','goldOv','playbookOv','labOv','intelOv','learnOv','sectorsOv','heatOv','scrOv','geoOv','researchOv','cryptoOv','paperOv'].forEach(oid => {
    if (oid !== id) document.getElementById(oid)?.remove();
  });
  const el = document.createElement('div');
  el.id = id;
  el.className = "term-overlay";
  const chrome = parseInt(getComputedStyle(document.documentElement).getPropertyValue("--desk-chrome"), 10) || 140;
  el.style.paddingTop = (chrome + 16) + "px";
  el.innerHTML = `<div class="term-overlay-card">
    <div class="term-overlay-hdr">
      <div class="term-overlay-title">${title}</div>
      <button class="term-overlay-close" onclick="document.getElementById('${id}').remove()" aria-label="Close">×</button>
    </div>
    <div class="term-overlay-body">${content}</div>
  </div>`;
  el.addEventListener('click', e => { if (e.target === el) el.remove(); });
  document.body.appendChild(el);
  const card = el.querySelector(".term-overlay-card") || el;
  _fxOverlayEnter(card);
  _fxStaggerChildren(el.querySelector(".term-overlay-body"));
}
function _hideOverlay(id) { document.getElementById(id)?.remove(); }

function _refreshOverlay(id, renderFn) {
  const ov = document.getElementById(id);
  if (!ov) return false;
  const body = ov.querySelector('.term-overlay-body');
  if (!body) return false;
  body.innerHTML = renderFn();
  return true;
}

/** Desktop: #main is CSS-hidden — never leave buttons writing into a blank page. */
// Desk overlays live on <body> above the panel grid, so routing to a panel
// page while one is open would leave it covering the terminal — click
// "Markets" and still be looking at the Gold Desk. sbNav() handled this for
// sidebar clicks only; nav() from the command bar, keyboard or a deep link
// did not. Close them wherever the route comes from.
function _closeDeskOverlays() {
  ['homeOv', 'dashOv', 'portOv', 'compareOv', 'briefOv', 'goldOv', 'playbookOv', 'labOv', 'intelOv','learnOv','sectorsOv','heatOv','scrOv','geoOv','researchOv','cryptoOv','paperOv']
    .forEach(id => document.getElementById(id)?.remove());
}

function _desktopRoute(page) {
  if (!IS_DESKTOP()) return false;

  // 4-panel terminal surfaces
  const panels = { mkt: "p1", news: "p2", sig: "p3", watch: "p4" };
  if (panels[page]) {
    _closeDeskOverlays();
    const pid = panels[page];
    if (_expPanel !== pid) {
      if (_expPanel) toggleExpand(_expPanel);
      toggleExpand(pid);
    }
    updateSidebarActive();
    return true;
  }

  if (page === "scr") {
    _closeDeskOverlays();
    _showScrOverlay();
    updateSidebarActive();
    return true;
  }
  if (page === "anlz") {
    _closeDeskOverlays();
    // ticker analysis lives in panel 2 via termSelect / openA
    if (termSelTk) termSelect(termSelTk);
    else if (_expPanel !== "p2") {
      if (_expPanel) toggleExpand(_expPanel);
      toggleExpand("p2");
    }
    updateSidebarActive();
    return true;
  }

  const overlays = {
    home: { id: "homeOv", title: "⌂ Home", render: renderHome },
    dash: { id: "dashOv", title: "⬡ Dashboard Overview", render: renderDash },
    brief: {
      id: "briefOv",
      title: "⬢ Dispatch Brief · Daily house view",
      render: renderBrief,
      after: () => loadDispatchBrief(false),
    },
    playbook: {
      id: "playbookOv",
      title: "◆ Weekly Playbook",
      render: renderPlaybook,
      after: () => {
        const ov = document.getElementById("playbookOv");
        if (ov) ov.classList.add("term-overlay-gold");
        loadGoldDesk(false);
      },
    },
    gold: {
      id: "goldOv",
      title: "◆ Gold Dashboard",
      render: renderGoldDesk,
      after: () => {
        const ov = document.getElementById("goldOv");
        if (ov) ov.classList.add("term-overlay-gold");
        loadGoldDesk(false);
      },
    },
    port: { id: "portOv", title: "📊 Portfolio", render: renderPortfolio },
    research: { id: "researchOv", title: "🔬 Research Desk", render: renderResearch },
    intel: { id: "intelOv", title: "⬢ AI Document Intelligence", render: renderDocIntel },
    learn: { id: "learnOv", title: "📚 Learn — Financial Education", render: renderLearn },
    sectors: {
      id: "sectorsOv",
      title: "🔄 Sector Rotation Tracker",
      render: renderSectorTracker,
      after: () => { if (_sectorNeedsFetch()) fetchSectorData(); },
    },
    heat: { id: "heatOv", title: "🗺 Market Heatmap", render: renderHeat },
    lab: { id: "labOv", title: "◆ Market Lab", render: renderLab, after: _initLabPage },
    geo: { id: "geoOv", title: "🌐 Geo Ops Center", render: renderGeoOps, after: _paintChokepointStrip },
    crypto: { id: "cryptoOv", title: "₿ Crypto Markets", render: renderCryptoPage },
    paper: {
      id: "paperOv",
      title: "▣ The Dispatch — Premium Edition",
      render: renderNewspaper,
      after: () => {
        if (!newsLastFetch && !newsFetching) fetchLiveNews();
        if (!_brief && !_briefLoad) loadDispatchBrief(false);
      },
    },
  };
  const cfg = overlays[page];
  if (!cfg) return false;
  document.getElementById(cfg.id)?.remove();
  _showOverlay(cfg.id, cfg.title, cfg.render());
  if (cfg.after) setTimeout(cfg.after, 80);
  updateSidebarActive();
  return true;
}
// Back-compat alias
function _openDeskFullPage(page) { return _desktopRoute(page); }

function _refreshPageView() {
  if (IS_DESKTOP()) {
    if (pg === "lab" && _refreshOverlay("labOv", renderLab)) { setTimeout(_initLabPage, 60); return; }
    if (pg === "geo" && _refreshOverlay("geoOv", renderGeoOps)) return;
  }
  renderMain();
  if (pg === "lab") _initLabPage();
}

function _refreshView() {
  if (document.getElementById('scrOv')) { _renderScr(); return; }
  if (_refreshOverlay('sectorsOv', renderSectorTracker)) return;
  if (_refreshOverlay('learnOv', renderLearn)) return;
  if (_refreshOverlay('intelOv', renderDocIntel)) return;
  if (_refreshOverlay('heatOv', renderHeat)) return;
  if (_refreshOverlay('dashOv', renderDash)) return;
  if (_refreshOverlay('portOv', renderPortfolio)) return;
  if (_refreshOverlay('compareOv', _renderCompare)) return;
  if (_refreshOverlay('briefOv', renderBrief)) {
    document.getElementById("briefOv")?.classList.add("term-overlay-gold");
    return;
  }
  if (_refreshOverlay('goldOv', renderGoldDesk)) return;
  if (_refreshOverlay('playbookOv', renderPlaybook)) return;
  if (_refreshOverlay('labOv', renderLab)) { setTimeout(_initLabPage, 60); return; }
  _refreshPageView();
}

function _peerNav(p) { if (IS_DESKTOP()) termSelect(p); else openA(p); }

let _lookupSeq = 0;
let _chartLoad = { tk: null, cid: null };
let _earnLoadTk = null;
let _valLoadTk = null;
let _holdersLoadTk = null;
let _scrError = null;
let _scrSeq = 0;
let _ecoSeq = 0;

function updateSidebarActive() {
  // Re-render first: which sub-items exist depends on the current page.
  if (window.__sbLastPg !== pg) { window.__sbLastPg = pg; const el=document.getElementById('sidebar'); if (el && typeof renderSidebarNav==='function') { renderSidebarNav(); return; } }
  document.querySelectorAll('.sb-item').forEach(el => el.classList.remove('sb-on'));
  const direct = NAV_ALL;
  if (direct.includes(pg)) {
    document.getElementById('sbi-'+pg)?.classList.add('sb-on');
    return;
  }
  if (pg === 'anlz' || termSelTk) {
    document.getElementById('sbi-mkt')?.classList.add('sb-on');
    return;
  }
  if (_expPanel) {
    const map = {p1:'mkt',p2:'news',p3:'sig',p4:'watch'};
    const id = map[_expPanel];
    if (id) { document.getElementById('sbi-'+id)?.classList.add('sb-on'); return; }
  }
  document.getElementById('sbi-dash')?.classList.add('sb-on');
}

// Panel expand
let _expPanel=null;
function toggleExpand(id){
  const p=document.getElementById(id);
  const g=document.getElementById('panelGrid');
  if(!p||!g)return;
  if(_expPanel===id){
    p.classList.remove('p-expanded');g.classList.remove('has-expanded');_expPanel=null;
  } else {
    if(_expPanel){document.getElementById(_expPanel)?.classList.remove('p-expanded');}
    p.classList.add('p-expanded');g.classList.add('has-expanded');_expPanel=id;
  }
  _syncDeskChrome();
  updateSidebarActive();
}

// Keyboard shortcuts
function _initKeyboard(){
  document.addEventListener('keydown',e=>{
    const tag=document.activeElement?.tagName;
    const inInput=tag==='INPUT'||tag==='TEXTAREA'||tag==='SELECT';
    if(inInput){
      if(e.key==='Escape'){
        if(document.activeElement?.id==='sinp'&&!document.getElementById('sov')?.classList.contains('hide')){closeSearch();return;}
        document.activeElement.blur();
        document.getElementById('cmdAc')?.classList.remove('show');
        if(_expPanel)toggleExpand(_expPanel);
      }
      if(document.activeElement?.id==='sinp')return;
      if(e.key==='ArrowDown'&&document.getElementById('cmdAc')?.classList.contains('show')){e.preventDefault();_acNav(1);}
      if(e.key==='ArrowUp'&&document.getElementById('cmdAc')?.classList.contains('show')){e.preventDefault();_acNav(-1);}
      if(e.key==='Enter'&&_acIdx>=0){
        const items=document.getElementById('cmdAc')?.querySelectorAll('.ac-item');
        if(items&&items[_acIdx]){items[_acIdx].dispatchEvent(new MouseEvent('mousedown'));e.preventDefault();}
      }
      return;
    }
    if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();openSearch();return;}
    if(!inInput&&e.key.toLowerCase()==='f'&&!e.ctrlKey&&!e.metaKey){e.preventDefault();toggleChromeFocus();return;}
    // Letter shortcuts only when focus is not on a control (avoids hijacking mid-click forms)
    const ae=document.activeElement;
    const onControl=ae&&ae!==document.body&&ae!==document.documentElement&&/^(INPUT|TEXTAREA|SELECT|BUTTON|A)$/i.test(ae.tagName||"");
    if(!e.ctrlKey&&!e.metaKey&&!e.altKey&&!e.shiftKey&&e.key.length===1&&!onControl){
      const k=e.key.toLowerCase();
      if(k==='n'){e.preventDefault();nav('news');return;}
      if(k==='b'){e.preventDefault();nav('brief');return;}
      if(k==='l'){e.preventDefault();nav('lab');return;}
      if(k==='w'){e.preventDefault();nav('watch');return;}
      if(k==='d'){e.preventDefault();nav('dash');return;}
      if(k==='m'){e.preventDefault();nav('mkt');return;}
      if(k==='p'){e.preventDefault();nav('port');return;}
      if(k==='s'){e.preventDefault();_shareDeskSnapshot();return;}
      if(k==='r'){e.preventDefault();runMorningDeskRun();return;}
    }
    switch(e.key){
      case '/':e.preventDefault();if(IS_DESKTOP())document.getElementById('cmdInput')?.focus();else openSearch();break;
      case 'Escape':
        if(_moreNavOpen){closeMoreNav();break;}
        if(!document.getElementById('sov')?.classList.contains('hide')){closeSearch();break;}
        if(_expPanel){toggleExpand(_expPanel);break;}
        if(termSelTk){termClear();break;}
        _ctxHide();break;
      case '1':if(IS_DESKTOP())toggleExpand('p1');break;
      case '2':if(IS_DESKTOP())toggleExpand('p2');break;
      case '3':if(IS_DESKTOP())toggleExpand('p3');break;
      case '4':if(IS_DESKTOP())toggleExpand('p4');break;
    }
  });
  // Wire command input events
  const ci=document.getElementById('cmdInput');
  if(ci){
    ci.addEventListener('input',e=>_acShow(e.target.value.trim()));
    ci.addEventListener('keydown',e=>{if(e.key==='Enter')runCmd();});
    ci.addEventListener('focus',()=>{_cmdFocused=true;const h=document.getElementById('cmdHint');if(h&&!ci.value.trim()&&!termSelTk&&!_dynTk)h.style.display='flex';});
    ci.addEventListener('blur',()=>setTimeout(()=>{document.getElementById('cmdAc')?.classList.remove('show');_cmdFocused=false;const h=document.getElementById('cmdHint');if(h)h.style.display='none';},150));
  }
}

// Context menu
let _ctxTk=null;
function _ctxShow(e,tk){
  e.preventDefault();_ctxTk=tk;
  const menu=document.getElementById('ctxMenu');if(!menu)return;
  const a=A.find(x=>x.tk===tk);const iw=isWatched(tk);
  const price=livePx(tk);
  const priceArg=price!=null?price:'null';
  const priceHint=price!=null?`$${price.toFixed(2)}`:'NO SYNC';
  menu.innerHTML=`
    <div class="ctx-tk-label">${tk}${a?' — '+a.nm:''} · ${priceHint}</div>
    <div class="ctx-item" onclick="termSelect('${tk}');_ctxHide()">🔍 &nbsp;Analyse</div>
    <div class="ctx-item" onclick="togWatch('${tk}');_ctxHide()">${iw?'★ &nbsp;Remove from Watchlist':'☆ &nbsp;Add to Watchlist'}</div>
    <div class="ctx-item" onclick="_ctxAlert('${tk}',${priceArg})">🔔 &nbsp;Set Price Alert</div>
    <div class="ctx-item" onclick="_ctxPort('${tk}')">📊 &nbsp;Add to Portfolio</div>
    <div class="ctx-item" onclick="_ctxHide()">✕ &nbsp;Close</div>`;
  const x=Math.min(e.clientX,window.innerWidth-185);
  const y=Math.min(e.clientY,window.innerHeight-210);
  menu.style.left=x+'px';menu.style.top=y+'px';
  menu.classList.add('show');
}
function _ctxHide(){document.getElementById('ctxMenu')?.classList.remove('show');_ctxTk=null;}
function _ctxAlert(tk,price){
  _ctxHide();
  const live=typeof price==="number"&&isFinite(price)&&price>0?price:livePx(tk);
  const curLbl=live!=null?`$${live.toFixed(2)}`:"NO SYNC";
  const t=prompt(`Set price alert for ${tk} (current: ${curLbl})\nEnter target price:`);
  if(!t||isNaN(parseFloat(t)))return;
  const target=parseFloat(t);
  const dir=live!=null?(target>live?'above':'below'):'above';
  addAlert(tk,t,dir);
}
function _ctxPort(tk){
  _ctxHide();
  const qty=prompt(`Add ${tk} to Portfolio\nEnter quantity (units/shares):`);
  if(!qty||isNaN(parseFloat(qty)))return;
  const cost=prompt(`Enter average cost per unit ($):`);
  if(!cost||isNaN(parseFloat(cost)))return;
  addPosition(tk,qty,cost);
}
document.addEventListener('click',e=>{if(!e.target.closest('#ctxMenu'))_ctxHide();});
document.addEventListener('contextmenu',e=>{if(!e.target.closest('#ctxMenu')&&!e.target.closest('.tt')&&!e.target.closest('.nr'))_ctxHide();});

// Expandable news
let _openNews=new Set();
function _toggleNews(idx){
  if(_openNews.has(idx))_openNews.delete(idx);else _openNews.add(idx);
  renderP2();
}

// Drag-to-reorder watchlist
let _dragIdx=null;
function _newWl(){
  const raw=prompt('Name for new watchlist:','');
  if(raw==null)return; // cancelled
  const name=String(raw).trim();
  if(name.length<2){showToast('Name must be at least 2 characters','var(--gd)');return;}
  if(name.length>40){showToast('Name too long (max 40)','var(--gd)');return;}
  createWatchlist(name);
}
// ═══════════════════════════════════════════════════════════
// DYNAMIC MARKET ENGINE — self-updating live ticker universe
// Fetches top stocks from Yahoo Finance screener automatically
// No manual list — auto-discovers thousands of live tickers
// ═══════════════════════════════════════════════════════════
let _dynMarkets = {};       // symbol → {name,price,change,prev,volume,mc,exchange,sector,region,_src}
let _dynLoadedTypes = {};   // 'us_top' | 'global'
let _dynLoadingTypes = {};
let _dynError = null;
let _mktView = 'curated';   // 'curated' | 'live' | 'global'
let _mktSort = 'default';   // 'chg_desc'|'chg_asc'|'vol'|'mc'|'az'
let _mktCuratedSort = 'smart';
let _mktFilter = 'all';
let _mktSearch = '';

async function fetchDynamicMarkets(type = 'us_top') {
  if (_dynLoadingTypes[type]) return;
  _dynLoadingTypes[type] = true;
  _dynError = null;
  try {
    const res = await fetch(`/api/screener?type=${type}&count=150`, { signal: AbortSignal.timeout(15000) });
    if (!res.ok) { _dynError = `Screener failed (${res.status})`; return; }
    const data = await res.json();
    if (data.tickers) {
      data.tickers.forEach((t) => {
        if (!t?.symbol) return;
        _dynMarkets[t.symbol] = { ...t, _src: type };
        // Map Yahoo wire symbols (BTC-USD, BRK-B) → desk tickers when known
        const deskTk = (typeof resolveInternalTicker === "function" ? resolveInternalTicker(t.symbol) : t.symbol) || t.symbol;
        if (typeof t.price === "number" && t.price > 0) {
          _applyLiveQuote(deskTk, {
            p: t.price,
            c: typeof t.change === "number" && isFinite(t.change) ? t.change : 0,
            prev: typeof t.prev === "number" && t.prev > 0 ? t.prev : undefined,
          }, "yahoo-screener");
        }
      });
      _dynLoadedTypes[type] = true;
    }
  } catch (e) { _dynError = e?.message || 'fetch failed'; }
  finally {
    _dynLoadingTypes[type] = false;
    // Mobile: surgical update only — full renderMain hard-resets scroll on Android
    if (pg === 'mkt' || pg === 'dash') {
      if (MOBILE()) { _patchLiveDataIfNeeded(); _patchCuratedPrices(); }
      else renderMain();
    }
    if (IS_DESKTOP()) renderTerminalPanels();
  }
}

async function fetchAllMarkets() {
  await fetchDynamicMarkets('us_top');
  await fetchDynamicMarkets('global');
}

function renderDynMarkets() {
  const typeKey = _mktView === 'global' ? 'global' : 'us_top';
  const allDyn = Object.values(_dynMarkets).filter((t) => t._src === typeKey);
  let tickers = allDyn;

  // Filter
  if (_mktFilter !== 'all') tickers = tickers.filter((t) => t.region === _mktFilter || t.sector === _mktFilter);
  if (_mktSearch) {
    const q = _mktSearch.toUpperCase();
    tickers = tickers.filter((t) => t.symbol.includes(q) || (t.name || '').toUpperCase().includes(q));
  }

  // Sort
  if (_mktSort === 'chg_desc') tickers = [...tickers].sort((a, b) => b.change - a.change);
  else if (_mktSort === 'chg_asc') tickers = [...tickers].sort((a, b) => a.change - b.change);
  else if (_mktSort === 'vol') tickers = [...tickers].sort((a, b) => (b.volume || 0) - (a.volume || 0));
  else if (_mktSort === 'mc') tickers = [...tickers].sort((a, b) => (b.marketCap || 0) - (a.marketCap || 0));
  else if (_mktSort === 'az') tickers = [...tickers].sort((a, b) => a.symbol.localeCompare(b.symbol));

  const regions = ['all','US','GB','DE','JP','IN','HK','CA','AU'];
  const sorts = [['default','Default'],['chg_desc','↑ Chg%'],['chg_asc','↓ Chg%'],['vol','Volume'],['mc','Mkt Cap'],['az','A-Z']];

  let h = `<div style="background:var(--b1);border-bottom:1px solid var(--gb);padding:10px 12px">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
      <input placeholder="Search symbol or name…" value="${_mktSearch}" oninput="_mktSrch(this.value)"
        style="flex:1;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:8px 12px;color:var(--tx);font-size:13px;outline:none;font-family:var(--sn)">
      <button onclick="fetchAllMarkets()" style="background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:8px 12px;color:var(--bl);font-family:var(--mn);font-size:10px;cursor:pointer;white-space:nowrap">⟳ Refresh</button>
    </div>
    <div style="display:flex;gap:4px;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;margin-bottom:6px">
      ${regions.map(r=>`<button onclick="_mktFilt('${r}')" style="font-family:var(--mn);font-size:9px;padding:3px 10px;border-radius:10px;cursor:pointer;border:1px solid ${_mktFilter===r?'var(--gd)':'var(--b4)'};background:${_mktFilter===r?'var(--gdG)':'transparent'};color:${_mktFilter===r?'var(--gd)':'var(--t3)'};white-space:nowrap;flex-shrink:0">${r==='all'?'All':r}</button>`).join('')}
    </div>
    <div style="display:flex;gap:4px;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none">
      ${sorts.map(([s,l])=>`<button onclick="_mktSrt('${s}')" style="font-family:var(--mn);font-size:9px;padding:3px 10px;border-radius:10px;cursor:pointer;border:1px solid ${_mktSort===s?'var(--bl)':'var(--b4)'};background:${_mktSort===s?'var(--blG)':'transparent'};color:${_mktSort===s?'var(--bl)':'var(--t3)'};white-space:nowrap;flex-shrink:0">${l}</button>`).join('')}
    </div>
  </div>`;

  if (_dynLoadingTypes[typeKey]) {
    h += `<div style="padding:32px;text-align:center"><div style="width:16px;height:16px;border:2px solid var(--bl);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 12px"></div><div style="font-family:var(--sn);font-size:13px;color:var(--t2)">Fetching live market data…</div><div style="font-family:var(--mn);font-size:10px;color:var(--t3);margin-top:4px">Scanning Yahoo Finance screeners across global exchanges</div></div>`;
    return h;
  }

  if (!_dynLoadedTypes[typeKey]) {
    h += `<div style="padding:32px;text-align:center"><div style="font-family:var(--sn);font-size:14px;color:var(--t2);margin-bottom:12px">Tap to load live market data</div><button onclick="fetchDynamicMarkets('${typeKey}')" style="background:var(--gd);color:var(--bg);border:none;border-radius:8px;padding:12px 24px;font-family:var(--sn);font-size:14px;font-weight:700;cursor:pointer">Load Markets</button></div>`;
    return h;
  }

  if (_dynError && !tickers.length) {
    h += `<div style="padding:32px;text-align:center"><div style="font-family:var(--sn);font-size:14px;color:var(--rd);margin-bottom:12px">${_dynError}</div><button onclick="fetchDynamicMarkets('${typeKey}')" style="background:var(--gd);color:var(--bg);border:none;border-radius:8px;padding:12px 24px;font-family:var(--sn);font-size:14px;font-weight:700;cursor:pointer">Retry</button></div>`;
    return h;
  }

  h += `<div style="padding:8px 12px 4px;display:flex;justify-content:space-between;align-items:center;font-family:var(--mn);font-size:9px;color:var(--t3)">${tickers.length} tickers · live from Yahoo Finance · click any row to analyse<button onclick="nav('intel')" style="background:var(--blG);color:var(--bl);border:1px solid rgba(79,142,247,0.2);border-radius:5px;padding:3px 10px;font-family:var(--mn);font-size:9px;cursor:pointer">⬢ AI Doc Intel</button></div>`;
  h += `<div style="overflow-x:auto;-webkit-overflow-scrolling:touch"><table style="width:100%;border-collapse:collapse;font-family:var(--mn);font-size:11px;min-width:500px">
    <thead><tr style="background:var(--b1);border-bottom:1px solid var(--gb)">
      <th style="padding:7px 10px;text-align:left;font-size:9px;color:var(--t3);letter-spacing:0.1em">SYMBOL</th>
      <th style="padding:7px 10px;text-align:left;font-size:9px;color:var(--t3);letter-spacing:0.1em">NAME</th>
      <th style="padding:7px 10px;text-align:right;font-size:9px;color:var(--t3)">PRICE</th>
      <th style="padding:7px 10px;text-align:right;font-size:9px;color:var(--t3)">CHG%</th>
      <th style="padding:7px 10px;text-align:right;font-size:9px;color:var(--t3)">VOLUME</th>
      <th style="padding:7px 10px;text-align:left;font-size:9px;color:var(--t3)">EXCH</th>
    </tr></thead><tbody>`;

  tickers.slice(0, 500).forEach((t) => {
    const ch = typeof t.change === "number" && isFinite(t.change) ? t.change : null;
    const px = typeof t.price === "number" && t.price > 0 ? t.price : null;
    const col = ch == null ? "var(--t3)" : ch > 0 ? "var(--gn)" : ch < 0 ? "var(--rd)" : "var(--t3)";
    const sign = ch != null && ch >= 0 ? "+" : "";
    const vol = t.volume >= 1e9 ? `${(t.volume/1e9).toFixed(1)}B` : t.volume >= 1e6 ? `${(t.volume/1e6).toFixed(0)}M` : t.volume >= 1e3 ? `${(t.volume/1e3).toFixed(0)}K` : (t.volume||'—');
    const isCurated = A.find((a) => a.tk === t.symbol);
    const symEsc = String(t.symbol || "").replace(/'/g, "");
    h += `<tr onclick="lookupTicker('${symEsc}')" style="border-bottom:1px solid rgba(255,255,255,0.025);cursor:pointer;transition:background 0.1s" onmouseover="this.style.background='var(--b1)'" onmouseout="this.style.background=''">
      <td style="padding:7px 10px;font-weight:800;color:var(--gd)">${t.symbol}${isCurated?'<span style="font-size:8px;color:var(--bl);margin-left:4px">★</span>':''}</td>
      <td style="padding:7px 10px;color:var(--t2);max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:10px">${t.name||'—'}</td>
      <td style="padding:7px 10px;text-align:right;font-weight:700">${px!=null?('$'+px.toFixed(px>100?2:4)):'—'}</td>
      <td style="padding:7px 10px;text-align:right;color:${col};font-weight:700">${ch!=null?sign+ch.toFixed(2)+'%':'—'}</td>
      <td style="padding:7px 10px;text-align:right;color:var(--t3)">${vol}</td>
      <td style="padding:7px 10px;color:var(--t3);font-size:9px">${t.exchange||'—'}</td>
    </tr>`;
  });

  h += `</tbody></table></div>`;
  if (tickers.length > 500) h += `<div style="padding:10px;text-align:center;font-family:var(--mn);font-size:9px;color:var(--t3)">Showing top 500 of ${tickers.length} · Use search to filter</div>`;
  return h;
}

function _mktSrch(q) { _mktSearch=q; renderMain(); }
function _mktFilt(f) { _mktFilter=f; renderMain(); }
function _mktSrt(s) { _mktSort=s; renderMain(); }
function _mktViewSet(v) { _mktView=v; renderMain(); if(v==='live'&&!_dynLoadedTypes.us_top)fetchDynamicMarkets('us_top'); if(v==='global'&&!_dynLoadedTypes.global)fetchDynamicMarkets('global'); }

// ─── Dynamic ticker lookup ───
let _dynTk=null,_dynData=null,_dynLoading=false;

/** Strip garbage so "POET]]" / "$poet," / markdown artifacts become valid Yahoo symbols */
function sanitizeTicker(tk){
  if(tk==null)return "";
  let s=String(tk).trim().toUpperCase();
  // remove common wrappers / markdown / html leftovers
  s=s.replace(/^\$/,"").replace(/^[`"'\(\[\{]+/,"").replace(/[`"'\.\,\!\?\)\]\}]+$/g,"");
  // keep only legal symbol chars (letters, digits, dots, dashes, equals for futures-like)
  s=s.replace(/[^A-Z0-9.\-=]/g,"");
  // collapse accidental double dots
  s=s.replace(/\.{2,}/g,".");
  // drop trailing junk separators
  s=s.replace(/[.\-]+$/,"");
  if(s.length>20)s=s.slice(0,20);
  return s;
}

/**
 * Pick best Yahoo search hit for a bare query.
 * Avoids RELIANCE → RS (Reliance Inc US) when RELIANCE.NS is the intended equity.
 */
function _bestYahooSearchMatch(results, query){
  if(!results?.length)return null;
  const up=String(query||"").toUpperCase().replace(/^\$/,"").trim();
  if(!up)return results[0];
  const score=r=>{
    const sym=String(r.symbol||"").toUpperCase();
    const name=String(r.name||"").toUpperCase();
    if(!sym)return -1;
    if(sym===up)return 10000;
    const suffixes=[".NS",".BO",".L",".T",".PA",".DE",".AX",".HK",".TO",".SW","-USD"];
    for(const suf of suffixes){if(sym===up+suf)return 9500;}
    if(sym.startsWith(up+".")||sym.startsWith(up+"-"))return 9000;
    if(sym.startsWith(up))return 8000-Math.min(sym.length,40);
    const prefix=up.slice(0,Math.min(4,up.length));
    const shares=prefix.length>=2&&(sym.startsWith(prefix)||sym.includes(up.slice(0,3)));
    if(name.startsWith(up)&&shares)return 6000;
    if(name.includes(up)&&shares)return 4000;
    // Avoid RS for RELIANCE — name-only brand collisions rank last
    if(name.startsWith(up)&&!shares)return 200;
    if(name.includes(up))return 100;
    const base=sym.split(/[.\-]/)[0];
    if(base===up)return 7000;
    return 0;
  };
  let best=results[0],bestS=score(best);
  for(let i=1;i<results.length;i++){
    const s=score(results[i]);
    if(s>bestS){best=results[i];bestS=s;}
  }
  return best;
}

/** Map Yahoo symbols (BTC-USD, CL=F, GC=F) → desk tickers (BTC, WTI, XAU) when known */
function resolveInternalTicker(raw){
  const s=sanitizeTicker(raw);
  if(!s)return "";
  if(typeof YAHOO_SYMBOLS!=="undefined"&&YAHOO_SYMBOLS[s])return s;
  if(typeof A!=="undefined"&&A.find(a=>a.tk===s))return s;
  if(typeof P!=="undefined"&&Object.prototype.hasOwnProperty.call(P,s))return s;
  if(typeof YAHOO_SYMBOLS!=="undefined"){
    for(const[tk,yh] of Object.entries(YAHOO_SYMBOLS)){
      if(yh===s||String(yh).toUpperCase()===s)return tk;
    }
  }
  // BTCUSD=X style leftovers
  if(s.endsWith("-USD")||s.endsWith("USD=X")){
    const base=s.replace(/-USD$/,"").replace(/USD=X$/,"");
    if(base&&typeof YAHOO_SYMBOLS!=="undefined"&&YAHOO_SYMBOLS[base])return base;
  }
  return s;
}

async function lookupTicker(tk){
  const seq=++_lookupSeq;
  const sym=resolveInternalTicker(tk);
  if(!sym){
    showToast("Enter a valid ticker symbol","var(--gd)");
    return;
  }
  const known=A.find(a=>a.tk===sym);
  if(known){
    if(IS_DESKTOP()) termSelect(sym);
    else openA(sym);
    return;
  }
  // Yahoo wire symbol (desk BTC → BTC-USD) for feeds
  const yhSym=(typeof YAHOO_SYMBOLS!=="undefined"&&YAHOO_SYMBOLS[sym])?YAHOO_SYMBOLS[sym]:sym;
  _dynTk=sym;_dynData=null;_dynLoading=true;termSelTk=null;
  if(IS_DESKTOP()){
    const p2title=document.getElementById('p2title');
    const p2sub=document.getElementById('p2sub');
    if(p2title)p2title.textContent=`${_dynTk} — LOADING`;
    if(p2sub)p2sub.textContent='FETCHING LIVE DATA';
    renderP2();
  } else {
    pg='anlz';
    renderMain();
    renderNav();
  }
  try{
    // All price data via Yahoo Finance — works for every exchange worldwide
    const [priceRes,searchRes,chartData]=await Promise.allSettled([
      fetch(`/api/yahoo-quote?symbols=${encodeURIComponent(yhSym)}`,{signal:AbortSignal.timeout(8000)}),
      fetch(`/api/search?q=${encodeURIComponent(sym)}`,{signal:AbortSignal.timeout(5000)}),
      fetchYahooIntraday(yhSym),
    ]);

    let priceJson=priceRes.status==='fulfilled'&&priceRes.value.ok?await priceRes.value.json():{};
    let priceInfo=priceJson[yhSym]||priceJson[sym]||null;
    if(priceInfo&&!(typeof priceInfo.p==="number"&&priceInfo.p>0))priceInfo=null;

    const searchJson=searchRes.status==='fulfilled'&&searchRes.value.ok?await searchRes.value.json():{result:[]};
    // Prefer exchange-suffixed / base match over unrelated first hit (RELIANCE ≠ RS)
    const match=_bestYahooSearchMatch(searchJson.result||[],sym)
      ||(searchJson.result||[]).find(r=>r.symbol===yhSym||r.symbol===sym||resolveInternalTicker(r.symbol)===sym)
      ||null;

    // RELIANCE → RELIANCE.NS: when bare symbol has no quote, retry Yahoo wire symbol from search
    let wireSym=yhSym;
    let deskSym=sym;
    if(!priceInfo&&match?.symbol&&match.symbol!==yhSym&&match.symbol!==sym){
      wireSym=match.symbol;
      deskSym=resolveInternalTicker(wireSym)||wireSym;
      try{
        const retry=await fetch(`/api/yahoo-quote?symbols=${encodeURIComponent(wireSym)}`,{signal:AbortSignal.timeout(8000)});
        if(retry.ok){
          priceJson=await retry.json();
          priceInfo=priceJson[wireSym]||Object.values(priceJson).find(v=>v&&typeof v.p==="number"&&v.p>0)||null;
        }
      }catch(e){}
    }
    if(priceInfo&&deskSym!==sym){
      _dynTk=deskSym; // surface the tradeable symbol on the desk
    }

    let chart=chartData.status==='fulfilled'?chartData.value:null;
    if((!chart||chart.length<5)&&wireSym!==yhSym){
      try{chart=await fetchYahooIntraday(wireSym);}catch(e){/* keep prior */}
    }

    // News: Finnhub for plain US tickers only (no dot/dash = US exchange)
    let newsArr=[];
    const newsSym=deskSym||sym;
    const isUS=!newsSym.includes('.')&&!newsSym.includes('-')&&newsSym.length<=5;
    if(isUS){
      try{
        const today=new Date();
        const from=new Date(today-7*86400000).toISOString().split('T')[0];
        const to=today.toISOString().split('T')[0];
        const nr=await fetch(`/api/finnhub?endpoint=company-news&symbol=${encodeURIComponent(newsSym)}&from=${from}&to=${to}`,{signal:AbortSignal.timeout(6000)});
        if(nr.ok){const nd=await nr.json();if(Array.isArray(nd))newsArr=nd.slice(0,8).map(n=>({t:new Date((n.datetime||0)*1000).toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit'}),x:(n.headline||'').slice(0,120),link:n.url||'',src:n.source||'',im:'medium'}));}
      }catch(e){}
    }

    // CoinGecko fallback for desk crypto Yahoo refuses (UNI/SHIB/APT…) or misses
    if((!priceInfo||!(typeof priceInfo.p==="number"&&priceInfo.p>0))){
      const cgId=_cgIdForTicker(deskSym||sym)||_cgIdForTicker(sym);
      if(cgId){
        try{
          const cgr=await cgFetch(`https://api.coingecko.com/api/v3/simple/price?ids=${encodeURIComponent(cgId)}&vs_currencies=usd&include_24hr_change=true`,{signal:AbortSignal.timeout(9000)});
          if(cgr.ok){
            const cgd=await cgr.json();
            const row=cgd[cgId];
            if(row?.usd>0){
              const c=typeof row.usd_24h_change==="number"?row.usd_24h_change:0;
              priceInfo={p:row.usd,c,prev:row.usd/(1+c/100),_src:"coingecko"};
              deskSym=resolveInternalTicker(deskSym||sym)||deskSym||sym;
              if(!chart||chart.length<5){
                const cgSpark=await fetchCgSpark(cgId,1);
                if(cgSpark)chart=cgSpark;
              }
            }
          }
        }catch(e){}
      }
    }

    if(!priceInfo||!(typeof priceInfo.p==="number"&&priceInfo.p>0)){
      _dynData=null; // ticker not found on Yahoo/CoinGecko
    } else {
      const markTk=deskSym||sym;
      const src=priceInfo._src||"yahoo";
      // Register feed-confirmed quote so book/tape/livePx treat this ticker as live
      _applyLiveQuote(markTk, {
        p: priceInfo.p,
        c: typeof priceInfo.c === "number" ? priceInfo.c : 0,
        prev: typeof priceInfo.prev === "number" && priceInfo.prev > 0 ? priceInfo.prev : undefined,
      }, src==="coingecko"?"coingecko":"yahoo");
      if (Array.isArray(chart) && chart.length >= 5) {
        HIST[markTk] = chart.slice(-60);
      }
      _dynData={
        name:match?.name||markTk,
        exchange:match?.exchange||(src==="coingecko"?"CoinGecko":''),
        type:match?.type||(src==="coingecko"?"CRYPTOCURRENCY":''),
        price:priceInfo.p,
        chgPct:typeof priceInfo.c==="number"?priceInfo.c:0,
        chgAbs:priceInfo.p-(priceInfo.prev||priceInfo.p),
        prev:priceInfo.prev||priceInfo.p,
        chart:chart||[],
        news:newsArr,
        mc:'—',
      };
    }
  }catch(e){_dynData=null;}
  if(seq!==_lookupSeq)return;
  _dynLoading=false;
  if(IS_DESKTOP()) renderP2();
  else renderMain();
}

function _dynClear(){_dynTk=null;_dynData=null;_dynLoading=false;if(IS_DESKTOP()){renderP2();}else{nav('mkt');}}

function _wlDragStart(e,idx){_dragIdx=idx;e.currentTarget.classList.add('dragging-row');e.dataTransfer.effectAllowed='move';}
function _wlDragOver(e,idx){e.preventDefault();e.dataTransfer.dropEffect='move';e.currentTarget.classList.add('drag-over-top');}
function _wlDragLeave(e){e.currentTarget.classList.remove('drag-over-top');}
function _wlDrop(e,idx){
  e.preventDefault();e.currentTarget.classList.remove('drag-over-top');
  if(_dragIdx===null||_dragIdx===idx)return;
  const wl=getActiveWl();
  const [moved]=wl.tickers.splice(_dragIdx,1);
  wl.tickers.splice(idx,0,moved);
  saveWatchlists();_dragIdx=null;renderP4();
}
function _wlDragEnd(e){e.currentTarget.classList.remove('dragging-row');_dragIdx=null;}

// ═══════════════════════════════════════════════════════════
// TERMINAL (DESKTOP) PANELS
// ═══════════════════════════════════════════════════════════
const IS_DESKTOP = () => window.innerWidth >= 768;
const MOBILE = () => !IS_DESKTOP() || (typeof window !== 'undefined' && window.innerWidth < 768);
let _layoutMode = null;

const MOBILE_PRICE_FREQ = 180;   // 3 minutes minimum on mobile
const MOBILE_NEWS_FREQ = 900;    // 15 minutes on mobile
const MOBILE_STATUS_FREQ = 15000; // 15s on mobile for status
const MOBILE_DO_TICK = 45000;    // 45s on mobile

function _mobShortRegime(label) {
  const m = { "Risk-On (Strong)": "RISK+", "Risk-On (Fragile)": "RISK", "Transition": "TRANS", "Risk-Off": "RISK-" };
  return m[label] || String(label || "").split(" ")[0].slice(0, 6).toUpperCase();
}

function _syncDeskChrome() {
  if (!IS_DESKTOP()) {
    document.documentElement.style.removeProperty("--desk-chrome");
    return;
  }
  const app = document.getElementById("app");
  if (!app) return;
  let h = 0;
  // .chokepoint-strip is part of the restored Geo surface and sits in the desk
  // chrome. Leaving it out of the measurement made the overlay start too high
  // and clip the command bar whenever the strip was present.
  app.querySelectorAll(".tape, .status, #siteIntelBar, #wlGlanceBar, #cmdBar, .chokepoint-strip").forEach(el => {
    if (el && !el.classList.contains("hide") && el.offsetHeight) h += el.offsetHeight;
  });
  document.documentElement.style.setProperty("--desk-chrome", (h || 140) + "px");
}

function _initResponsiveShell() {
  let _lastW = window.innerWidth;
  const apply = (force) => {
    const desk = IS_DESKTOP();
    const mode = desk ? "d" : "m";
    const w = window.innerWidth;
    // Android Chrome URL bar hide/show changes height only — ignore pure height resizes
    const widthChanged = Math.abs(w - _lastW) >= 8;
    const modeChanged = _layoutMode !== mode;
    if (!force && !modeChanged && !widthChanged) {
      _syncDeskChrome();
      return;
    }
    _lastW = w;
    _layoutMode = mode;
    document.body.classList.toggle("mob-mode", !desk);
    document.body.classList.toggle("desk-mode", desk);
    if (modeChanged || force) {
      _statusSig = ""; // force status rebuild after layout flip
      renderStatus();
      _paintSiteIntelBar();
    }
    _syncDeskChrome();
    if (modeChanged) {
      if (desk) { renderTerminalPanels(); updateSidebarActive(); }
      else { renderMain(); renderNav(); }
    }
  };
  _layoutMode = IS_DESKTOP() ? "d" : "m";
  document.body.classList.toggle("mob-mode", !IS_DESKTOP());
  document.body.classList.toggle("desk-mode", IS_DESKTOP());
  _applyChromeFocus();
  if (IS_DESKTOP()) _initKbdStrip();
  _syncDeskChrome();
  let rt;
  const onResize = () => { clearTimeout(rt); rt = setTimeout(() => apply(false), 200); };
  window.addEventListener("resize", onResize);
  // Orientation is a real layout change — full apply
  window.addEventListener("orientationchange", () => setTimeout(() => apply(true), 280));
}
let termSelTk = null; // selected ticker in terminal panel 2
let _cmdFocused = false; // command input focus — gates the Try-ticker hint bar
let termChartRange = '1d'; // chart timeframe
let _screenerSort = 'default'; // 'chg_desc','chg_asc','score_desc','az'
let _screenerFilter = 'all'; // 'all','Stock','Crypto','Commodity','FX'
let _screenerSearch = '';
let termComRes = null;
let termComLoad = false;
let termComErr = "";

// ─── TERMINAL PANEL 1: Markets (dense table) ───
function renderP1() {
  const el = document.getElementById('p1body');
  if (!el) return;
  const liveCount = A.filter(a => liveSymbols.has(a.tk)).length;
  if (priceFetching && liveSymbols.size === 0) {
    el.innerHTML = `<div style="padding:24px 16px;text-align:center"><div style="width:14px;height:14px;border:2px solid var(--bl);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div><div style="font-family:var(--mn);font-size:10px;color:var(--t3)">SYNCING ${Object.keys(YAHOO_SYMBOLS).length}+ INSTRUMENTS FROM YAHOO…</div></div>`;
    return;
  }
  // Screener controls
  const filterBtns = ['all','Stock','Crypto','Commodity','FX'].map(f =>
    `<button onclick="_sf('${f}')" style="font-family:var(--mn);font-size:9px;padding:3px 9px;border-radius:10px;cursor:pointer;border:1px solid ${_screenerFilter===f?'var(--gd)':'var(--b4)'};background:${_screenerFilter===f?'var(--gdG)':'transparent'};color:${_screenerFilter===f?'var(--gd)':'var(--t3)'};white-space:nowrap;flex-shrink:0">${f==='all'?'All':f}</button>`
  ).join('');
  const sortBtns = [['default','Default'],['chg_desc','↑ Chg%'],['chg_asc','↓ Chg%'],['score_desc','Score'],['az','A-Z']].map(([s,l]) =>
    `<button onclick="_ss('${s}')" style="font-family:var(--mn);font-size:9px;padding:3px 9px;border-radius:10px;cursor:pointer;border:1px solid ${_screenerSort===s?'var(--bl)':'var(--b4)'};background:${_screenerSort===s?'var(--blG)':'transparent'};color:${_screenerSort===s?'var(--bl)':'var(--t3)'};white-space:nowrap;flex-shrink:0">${l}</button>`
  ).join('');

  const controlsHtml = `<div style="background:var(--b1);border-bottom:1px solid var(--gb);padding:6px 10px;display:flex;flex-direction:column;gap:5px">
    <div style="display:flex;gap:4px;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none">${filterBtns}</div>
    <div style="display:flex;gap:4px;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none">${sortBtns}</div>
  </div>`;

  // Filter and sort
  let tickers = A.filter(a => _screenerFilter==='all' || a.cat===_screenerFilter);
  if (_screenerSearch) tickers = tickers.filter(a => a.tk.includes(_screenerSearch) || a.nm.toLowerCase().includes(_screenerSearch.toLowerCase()));
  if (_screenerSort === 'chg_desc') tickers = [...tickers].sort((a,b) => (liveChg(b.tk)??-Infinity)-(liveChg(a.tk)??-Infinity));
  else if (_screenerSort === 'chg_asc') tickers = [...tickers].sort((a,b) => (liveChg(a.tk)??Infinity)-(liveChg(b.tk)??Infinity));
  else if (_screenerSort === 'score_desc') tickers = [...tickers].sort((a,b) => b.sc-a.sc);
  else if (_screenerSort === 'az') tickers = [...tickers].sort((a,b) => a.tk.localeCompare(b.tk));

  document.getElementById('p1sub').textContent = `${tickers.length} of ${A.length} · ${liveCount} LIVE`;

  let h = controlsHtml + `<table class="tt">
    <thead><tr>
      <th>TKR</th><th>PRICE</th><th>CHG%</th><th>SC</th><th>CAT</th><th>★</th>
    </tr></thead><tbody>`;

  tickers.forEach(a => {
    const d = fp(a.tk);
    const na = d.status === 'unavailable';
    const ch = liveChg(a.tk);
    const col = na || ch == null ? 'var(--t3)' : ch > 0 ? 'var(--gn)' : ch < 0 ? 'var(--rd)' : 'var(--t3)';
    const sign = ch != null && ch >= 0 ? '+' : '';
    const arrow = ch == null || ch === 0 ? '' : (ch > 0 ? '↑' : '↓');
    const iw = isWatched(a.tk);
    const sel = termSelTk === a.tk;
    const scCol = a.sc >= 75 ? 'var(--gn)' : a.sc >= 50 ? 'var(--bl)' : a.sc >= 35 ? 'var(--gd)' : 'var(--rd)';
    h += `<tr class="${sel ? 'sel' : ''}" onclick="termSelect('${a.tk}')" oncontextmenu="_ctxShow(event,'${a.tk}')">
      <td style="font-weight:800;color:${catBd(a.cat)}">${a.tk}</td>
      <td data-fl="${a.tk}" style="font-weight:700">${na?'<span style="color:var(--t3);opacity:0.55">—</span>':((a.cat==='Stock'||a.cat==='Crypto'||a.cat==='Commodity')?'$':'')+d.p}</td>
      <td style="color:${col};font-weight:700">${na?chgDim():`${arrow}${sign}${d.c}%`}</td>
      <td style="color:${scCol};font-weight:800">${a.sc}</td>
      <td style="font-family:var(--sn);font-size:9px;color:var(--t3)">${a.cat.slice(0,4)}</td>
      <td onclick="event.stopPropagation();togWatch('${a.tk}')" style="color:${iw?'var(--gd)':'var(--t3)'};cursor:pointer;text-align:center">★</td>
    </tr>`;
  });
  h += '</tbody></table>';
  el.innerHTML = h;
}

// ─── TERMINAL PANEL 2: News or Analysis ───
function renderP2() {
  const el = document.getElementById('p2body');
  const titleEl = document.getElementById('p2title');
  const subEl = document.getElementById('p2sub');
  if (!el) return;
  const _p2Scroll = el.scrollTop || 0;
  const _p2KeepScroll = !!(termSelTk || _dynTk);

  // Dynamic lookup view
  if (_dynTk) {
    if (titleEl) titleEl.innerHTML = `<span class="panel-idx">02</span>${_dynTk}${_dynData?' · '+_dynData.name.toUpperCase().slice(0,20):''}`;
    if (subEl) subEl.textContent = _dynData ? (_dynData.exchange||'DYNAMIC LOOKUP') : (_dynLoading?'FETCHING…':'NOT FOUND');
    if (_dynLoading) {
      el.innerHTML = `<div style="padding:20px 8px;font-family:var(--mn);font-size:10px;color:var(--bl);display:flex;align-items:center;gap:10px"><div style="width:12px;height:12px;border:2px solid var(--bl);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;flex-shrink:0"></div>FETCHING LIVE DATA FOR ${_dynTk}…</div>`;
      return;
    }
    if (!_dynData||!_dynData.price) {
      const shown=_escHtml(_dynTk||"");
      el.innerHTML = `<div style="padding:20px 16px">
        <div style="font-family:var(--sn);font-size:14px;color:var(--rd);margin-bottom:12px">"${shown}" — no price data found.</div>
        <div style="font-family:var(--sn);font-size:12px;color:var(--t2);line-height:1.9;background:var(--b1);border-radius:10px;padding:14px;margin-bottom:14px">
          <strong style="color:var(--tx);display:block;margin-bottom:6px">What this screen is</strong>
          <span style="color:var(--t3);display:block;margin-bottom:10px">Dynamic ticker lookup: you typed a symbol that is not in the curated list, and Yahoo returned no quote for it (wrong symbol, bad suffix, or feed gap).</span>
          <strong style="color:var(--tx);display:block;margin-bottom:6px">Use the exchange suffix for international stocks:</strong>
          🇮🇳 India (NSE): <span style="color:var(--gd);font-family:var(--mn)">RELIANCE.NS</span> · <span style="color:var(--gd);font-family:var(--mn)">TCS.NS</span><br>
          🇫🇷 France: <span style="color:var(--gd);font-family:var(--mn)">MC.PA</span> (LVMH) · <span style="color:var(--gd);font-family:var(--mn)">AIR.PA</span><br>
          🇯🇵 Japan: <span style="color:var(--gd);font-family:var(--mn)">7203.T</span> (Toyota) · <span style="color:var(--gd);font-family:var(--mn)">9984.T</span><br>
          🇬🇧 UK: <span style="color:var(--gd);font-family:var(--mn)">HSBA.L</span> · <span style="color:var(--gd);font-family:var(--mn)">BP.L</span><br>
          🇦🇺 Australia: <span style="color:var(--gd);font-family:var(--mn)">BHP.AX</span> · <span style="color:var(--gd);font-family:var(--mn)">CBA.AX</span><br>
          🇺🇸 US: no suffix needed — <span style="color:var(--gd);font-family:var(--mn)">AAPL</span> · <span style="color:var(--gd);font-family:var(--mn)">NVDA</span> · <span style="color:var(--gd);font-family:var(--mn)">POET</span><br><br>
          <span style="color:var(--t3)">Tip: Start typing and click a result from the autocomplete dropdown — it shows the exact symbol to use. Avoid pasting markdown or brackets (e.g. POET]]).</span>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button onclick="_dynClear()" style="background:var(--b2);color:var(--t2);border:1px solid var(--gb);border-radius:6px;padding:7px 16px;font-family:var(--mn);font-size:10px;cursor:pointer">← Back</button>
          ${/^[A-Z]{1,5}$/.test(sanitizeTicker(_dynTk||"")) ? `<button onclick="lookupTicker('${sanitizeTicker(_dynTk)}')" style="background:var(--gdG);color:var(--gd);border:1px solid rgba(232,164,76,0.35);border-radius:6px;padding:7px 16px;font-family:var(--mn);font-size:10px;cursor:pointer">Retry ${sanitizeTicker(_dynTk)}</button>` : ""}
        </div>
      </div>`;
      return;
    }
    const d = _dynData;
    const chN = typeof d.chgPct === "number" && isFinite(d.chgPct) ? d.chgPct : null;
    const col = chN == null ? "var(--t3)" : chN > 0 ? "var(--gn)" : chN < 0 ? "var(--rd)" : "var(--t3)";
    const sign = chN != null && chN >= 0 ? "+" : "";
    let h = `<div class="ap-hdr">
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div>
          <div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.2em;margin-bottom:2px">${(d.name||_dynTk||"").toUpperCase()}</div>
          <div class="ap-price" style="color:${col}">$${Number(d.price).toFixed(2)}</div>
          <div class="ap-chg" style="color:${col}">${chN!=null?`${sign}${Number(d.chgAbs||0).toFixed(2)} (${sign}${chN.toFixed(2)}%)`:"—"}</div>
        </div>
        <div style="text-align:right">
          <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:3px">MKT CAP</div>
          <div style="font-family:var(--mn);font-size:14px;font-weight:700">${d.mc}</div>
          <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-top:4px">PREV CLOSE</div>
          <div style="font-family:var(--mn);font-size:11px;font-weight:600">$${d.prev.toFixed(2)}</div>
        </div>
      </div>
      <div style="display:flex;gap:6px;margin-top:6px;flex-wrap:wrap">
        <span style="font-family:var(--mn);font-size:8px;background:var(--b3);color:var(--t2);padding:2px 6px;border-radius:2px">${d.exchange}</span>
        ${d.industry?`<span style="font-family:var(--mn);font-size:8px;background:var(--b3);color:var(--t2);padding:2px 6px;border-radius:2px">${d.industry}</span>`:''}
        <span style="font-family:var(--mn);font-size:8px;background:var(--gdG);color:var(--gd);padding:2px 6px;border-radius:2px">DYNAMIC</span>
      </div>
    </div>`;
    // Sparkline
    const hd = (d.chart||[]).filter(v=>typeof v==='number'&&isFinite(v)&&v>0);
    if(hd.length>=5){
      const mn=Math.min(...hd),mx=Math.max(...hd),rng=mx-mn||Math.max(mx*0.001,1e-9);
      const pts=hd.map((v,i)=>`${(i/(hd.length-1))*280},${38-((v-mn)/rng)*32}`).join(' ');
      h+=`<div style="padding:6px 8px;border-bottom:1px solid var(--b4)">
        <div style="font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.15em;margin-bottom:3px">INTRADAY</div>
        <svg width="100%" viewBox="0 0 280 42" style="display:block"><polyline points="${pts}" fill="none" stroke="${col}" stroke-width="1.5"/></svg>
      </div>`;
    }
    // News
    if(d.news&&d.news.length){
      h+=`<div style="font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.15em;padding:4px 8px;background:#000;border-bottom:1px solid var(--b4)">— RECENT NEWS</div>`;
      d.news.forEach(n=>{
        h+=`<div class="nr" onclick="${n.link?`window.open('${n.link}','_blank','noopener')`:''}">
          <span class="nr-time">${n.t}</span>
          <span class="nr-tag" style="background:var(--blG);color:var(--bl)">${(n.src||'NEWS').slice(0,4).toUpperCase()}</span>
          <span class="nr-txt">${n.x}</span>
        </div>`;
      });
    } else {
      h+=`<div style="padding:12px 8px;font-family:var(--mn);font-size:9px;color:var(--t3)">No recent news found for ${_dynTk}</div>`;
    }
    h+=`<div style="padding:6px 8px;border-top:1px solid var(--b4)"><button onclick="_dynClear()" style="background:var(--b2);color:var(--t2);border:1px solid var(--gb);border-radius:3px;padding:4px 12px;font-family:var(--mn);font-size:8.5px;cursor:pointer;letter-spacing:0.1em">← BACK TO NEWS</button></div>`;
    el.innerHTML = h;
    return;
  }

  if (termSelTk) {
    const a = A.find(x => x.tk === termSelTk);
    if (!a) { lookupTicker(termSelTk); return; }
    const d = fp(a.tk);
    const na = d.status === 'unavailable';
    const ch = liveChg(a.tk);
    const col = na || ch == null ? 'var(--t3)' : ch > 0 ? 'var(--gn)' : ch < 0 ? 'var(--rd)' : 'var(--t3)';
    const sign = ch != null && ch >= 0 ? '+' : '';
    const arrow = ch == null || ch === 0 ? '' : (ch > 0 ? '↑' : '↓');
    const isLive = liveSymbols.has(a.tk);
    const feedLbl = na ? 'NO SYNC' : (d.status === 'live' ? 'LIVE' : d.status === 'stale' ? 'STALE' : d.status === 'cached' ? 'CACHED' : 'DELAYED');
    const scoreCol = a.sc >= 75 ? 'var(--gn)' : a.sc >= 50 ? 'var(--bl)' : a.sc >= 35 ? 'var(--gd)' : 'var(--rd)';
    const money = a.cat === 'Stock' || a.cat === 'Crypto' || a.cat === 'Commodity';

    // Bullish/bearish factors derived from thesis
    const thWords = a.th.split('. ');
    const bullish = thWords.filter(s => /grow|gain|strong|lead|dominan|accelerat|beat|recover|expand|surge|buy|bullish|upside/i.test(s)).slice(0, 3);
    const bearish = thWords.filter(s => /risk|concern|slow|headwind|declin|loss|weak|miss|challeng|uncertain|bearish|downside|eroding/i.test(s)).slice(0, 3);

    if (titleEl) titleEl.innerHTML = `<span class="panel-idx">02</span>${termSelTk} · Analysis`;
    if (subEl) subEl.textContent = `${a.cat.toUpperCase()} · ${a.ex} · ${feedLbl}`;

    let h = `<div class="ap-hdr">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px">
        <div style="flex:1">
          <div style="font-family:var(--mn);font-size:10px;color:var(--t3);letter-spacing:0.15em;margin-bottom:4px">${a.nm.toUpperCase()}</div>
          <div class="ap-price" style="color:${na?'var(--tx)':col}">${na?'—':(money?'$':'')+d.p}</div>
          <div class="ap-chg" style="color:${col}">${na?'awaiting live feed':`${arrow} ${sign}${d.chg} (${sign}${d.c}%) today`}</div>
          <div style="display:flex;align-items:center;gap:8px;margin-top:6px">
            <span style="font-family:var(--mn);font-size:9px;background:${isLive?'var(--gnG)':'var(--b3)'};color:${isLive?'var(--gn)':'var(--t3)'};padding:2px 8px;border-radius:4px;font-weight:700">${isLive?'● '+feedLbl:'◌ '+feedLbl}</span>
            ${priceLastFetch?`<span style="font-family:var(--mn);font-size:9px;color:var(--t3)">Feed ${Math.round((Date.now()-priceLastFetch.getTime())/1000)}s ago</span>`:''}
          </div>
        </div>
        <div style="text-align:right;flex-shrink:0">
          <div style="font-family:var(--mn);font-size:9px;color:var(--t3);margin-bottom:4px">AI SCORE <span title="Score from 0–100 based on sentiment, momentum, fundamentals and analyst ratings" style="cursor:help;color:var(--bl)">ⓘ</span></div>
          <div style="font-family:var(--mn);font-size:32px;font-weight:900;color:${scoreCol};line-height:1">${a.sc}</div>
          <div style="font-family:var(--mn);font-size:9px;color:${scoreCol};margin-top:2px">${a.sc>=75?'HIGH CONVICTION':a.sc>=50?'MODERATE':a.sc>=35?'CAUTIOUS':'LOW CONVICTION'}</div>
        </div>
      </div>
    </div>`;

    // Score explanation
    h += `<div style="padding:10px 16px;border-bottom:1px solid var(--gb);background:var(--b1)">
      <div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.12em;margin-bottom:6px">HOW THE SCORE IS CALCULATED</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px">
        <div style="font-family:var(--mn);font-size:9.5px;color:var(--t2)">Sentiment: <span style="color:${a.se.includes('Bull')?'var(--gn)':a.se.includes('Bear')?'var(--rd)':'var(--bl)'}">${a.se}</span></div>
        <div style="font-family:var(--mn);font-size:9.5px;color:var(--t2)">Rating: <span style="color:var(--tx)">${a.ra}</span></div>
        <div style="font-family:var(--mn);font-size:9.5px;color:var(--t2)">Beta: <span style="color:var(--tx)">${a.beta}</span></div>
        <div style="font-family:var(--mn);font-size:9.5px;color:var(--t2)">P/E: <span style="color:var(--tx)">${a.pe}</span></div>
      </div>
      <div style="font-family:var(--mn);font-size:9px;color:var(--t3);margin-top:6px">Score is indicative only. Not investment advice.</div>
    </div>`;

    // Timeframe controls
    const ranges = [['1d','1D'],['5d','5D'],['1mo','1M'],['6mo','6M'],['1y','1Y'],['2y','2Y']];
    h += `<div style="display:flex;gap:4px;padding:8px 16px;border-bottom:1px solid var(--gb);background:var(--b1);align-items:center">
      <span style="font-family:var(--mn);font-size:9px;color:var(--t3);margin-right:4px">CHART</span>
      ${ranges.map(([r,l])=>`<button onclick="_setRange('${termSelTk}','${r}')" style="font-family:var(--mn);font-size:10px;font-weight:700;padding:3px 10px;border-radius:5px;cursor:pointer;border:1px solid ${termChartRange===r?'var(--gd)':'var(--b4)'};background:${termChartRange===r?'var(--gdG)':'transparent'};color:${termChartRange===r?'var(--gd)':'var(--t3)'};">${l}</button>`).join('')}
      <span style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-left:auto">MA20 MA50 RSI(14) Vol</span>
    </div>
    <div id="candleChart" style="padding:8px 12px 4px;border-bottom:1px solid var(--gb)"></div>`;

    // Bullish / Bearish factors
    h += `<div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--gb)">`;
    h += `<div style="background:var(--bg);padding:10px 14px">
      <div style="font-family:var(--mn);font-size:9px;color:var(--gn);letter-spacing:0.12em;margin-bottom:6px">↑ BULLISH FACTORS</div>
      ${bullish.length ? bullish.map(s=>`<div style="font-family:var(--sn);font-size:11px;color:var(--t2);line-height:1.5;margin-bottom:4px;padding-left:8px;border-left:2px solid var(--gn)">· ${s.trim()}</div>`).join('') : `<div style="font-family:var(--mn);font-size:10px;color:var(--t3)">—</div>`}
    </div>`;
    h += `<div style="background:var(--bg);padding:10px 14px">
      <div style="font-family:var(--mn);font-size:9px;color:var(--rd);letter-spacing:0.12em;margin-bottom:6px">↓ BEARISH FACTORS</div>
      ${bearish.length ? bearish.map(s=>`<div style="font-family:var(--sn);font-size:11px;color:var(--t2);line-height:1.5;margin-bottom:4px;padding-left:8px;border-left:2px solid var(--rd)">· ${s.trim()}</div>`).join('') : `<div style="font-family:var(--mn);font-size:10px;color:var(--t3)">—</div>`}
    </div>`;
    h += `</div>`;

    h += `<div class="tabs"><button class="${aTab==="ov"?"on":""}" onclick="_setATab('ov')">Overview</button><button class="${aTab==="nw"?"on":""}" onclick="_setATab('nw')">News</button><button class="${aTab==="fi"?"on":""}" onclick="_setATab('fi')">Financials</button><button class="${aTab==="val"?"on":""}" onclick="_setATab('val')">💰 Valuation</button><button class="${aTab==="earn"?"on":""}" onclick="_setATab('earn')">📈 Earnings</button><button class="${aTab==="th"?"on":""}" onclick="_setATab('th')">Thesis</button><button class="${aTab==="al"?"on":""}" onclick="_setATab('al')">Alerts</button><button class="${aTab==="cm"?"on":""}" onclick="_setATab('cm')">Lenses</button><button class="${aTab==="inst"?"on":""}" onclick="_setATab('inst')">🏛 Institutions${!_isPremium()?'★':''}</button></div>`;

    if(aTab==="nw"){
      h+=`<div id="term-nw-root">${_renderTickerNewsPanel(termSelTk)}</div>`;
      setTimeout(()=>_ensureTickerCompanyNews(termSelTk),40);
    }

    if(aTab==="fi"){
      const stmtKey=`${termSelTk}_${_stmtPeriod}`;
      if(_finTab==='metrics'&&_finCache[termSelTk]){
        h+=`<div id="term-fin-root">${renderFinancials(termSelTk,_finCache[termSelTk])}</div>`;
      }else if(_finTab!=='metrics'&&_stmtCache[stmtKey]){
        h+=`<div id="term-fin-root"></div>`;
        setTimeout(()=>_fetchStatements(termSelTk,'term-fin-root'),0);
      }else{
        h+=`<div id="term-fin-root"><div style="padding:20px;text-align:center"><div style="width:14px;height:14px;border:2px solid var(--bl);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div><div style="font-family:var(--mn);font-size:10px;color:var(--t3)">LOADING FINANCIALS…</div></div></div>`;
        setTimeout(()=>loadFinancials(termSelTk,'term-fin-root'),50);
      }
    }

    if(aTab==="earn"){
      h+=`<div id="term-earn-root"><div style="padding:20px;text-align:center"><div style="width:14px;height:14px;border:2px solid var(--gn);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div><div style="font-family:var(--mn);font-size:10px;color:var(--t3)">LOADING EARNINGS INTELLIGENCE…</div></div></div>`;
      setTimeout(()=>loadEarnings(termSelTk,'term-earn-root'),50);
    }

    if(aTab==="inst"){
      h+=`<div id="term-inst-root"><div style="padding:20px;text-align:center"><div style="width:14px;height:14px;border:2px solid var(--gd);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div><div style="font-family:var(--mn);font-size:10px;color:var(--t3)">LOADING INSTITUTIONAL DATA…</div></div></div>`;
      setTimeout(()=>loadHolders(termSelTk,'term-inst-root'),50);
    }

    if(aTab==="val"){
      h+=`<div id="term-val-root"><div style="padding:20px;text-align:center"><div style="width:14px;height:14px;border:2px solid var(--pu);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div><div style="font-family:var(--mn);font-size:10px;color:var(--t3)">LOADING VALUATION DASHBOARD…</div></div></div>`;
      setTimeout(()=>loadValuation(termSelTk,'term-val-root'),50);
    }

    if(aTab==="ov"){
      h += `<div class="ap-thesis">${a.th}</div>`;
      h += `<div style="padding:8px 16px;border-bottom:1px solid var(--gb);background:var(--b1)">
        <div style="font-family:var(--mn);font-size:9px;color:var(--t3)">Data: Finnhub (real-time US equities) · Yahoo Finance · CoinGecko (crypto) · Score is AI-generated for research purposes only. Not financial advice.</div>
      </div>`;
    }

    if(aTab==="th"){
      h += `<div class="ap-thesis">${a.th}</div>`;
      const hist=reason.filter(r=>r.ticker===a.tk);
      if(hist.length){
        h += `<div style="padding:12px 16px;border-top:1px solid var(--gb)"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.1em;margin-bottom:8px">REASONING BANK HISTORY</div>`;
        hist.forEach((r,i)=>{
          h += `<div style="border-top:${i?'1px solid var(--gb)':'none'};padding-top:${i?8:0}px;margin-top:${i?8:0}px"><div style="display:flex;gap:5px;align-items:center"><span style="font-size:8px;color:var(--t3);font-family:var(--mn)">${new Date(r.ts).toLocaleDateString()}</span>${bd(r.verdict,r.verdict==="IMPLEMENT"?"var(--gn)":r.verdict==="REJECT"?"var(--rd)":"var(--gd)")}</div>
            <div style="font-size:11px;color:var(--t2);margin-top:3px;line-height:1.55">${r.thesis.slice(0,120)}...</div></div>`;
        });
        h += `</div>`;
      }
    }

    if(aTab==="al"){
      const curAlerts=alerts.filter(al=>al.tk===a.tk);
      const curPrice=livePx(a.tk);
      const pxShow=curPrice!=null?`$${curPrice.toFixed(2)}`:"— NO SYNC";
      h += `<div style="padding:14px 16px">
        <div style="font-size:11px;font-weight:700;margin-bottom:10px">Set Price Alert · ${a.tk}</div>
        <div style="font-size:10px;color:var(--t2);margin-bottom:10px">Current price: <strong style="color:var(--tx);font-family:var(--mn)">${pxShow}</strong></div>
        <div style="display:flex;flex-direction:column;gap:8px">
          <input id="al-price" class="port-inp" type="number" placeholder="Target price ($)" step="any" value="${curPrice!=null?(curPrice*1.05).toFixed(2):""}">
          <div style="display:flex;gap:6px">
            <button onclick="addAlert('${a.tk}',document.getElementById('al-price').value,'above')" style="flex:1;background:var(--gnG);color:var(--gn);border:1px solid rgba(16,185,129,0.25);border-radius:8px;padding:10px;font-family:var(--sn);font-size:11px;font-weight:700;cursor:pointer">Alert when ≥ (above)</button>
            <button onclick="addAlert('${a.tk}',document.getElementById('al-price').value,'below')" style="flex:1;background:var(--rdG);color:var(--rd);border:1px solid rgba(239,68,68,0.25);border-radius:8px;padding:10px;font-family:var(--sn);font-size:11px;font-weight:700;cursor:pointer">Alert when ≤ (below)</button>
          </div>
        </div>
        ${curAlerts.length?`<div style="margin-top:12px;border-top:1px solid var(--gb);padding-top:10px"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.1em;margin-bottom:6px">EXISTING ALERTS</div>`:""}
        ${curAlerts.map((al)=>{const col=al.dir==="above"?"var(--gn)":"var(--rd)";const idx=alerts.findIndex(x=>x===al);return`<div class="alert-chip" style="border-color:${col}30;margin-bottom:4px;display:flex;justify-content:space-between;width:100%"><span style="color:var(--tx)">${al.dir==="above"?"≥":"≤"} <strong style="color:${col}">$${al.targetPrice}</strong> · ${al.active?"Active":"Triggered"}</span><span onclick="removeAlert(${idx})" style="color:var(--rd);cursor:pointer;padding-left:8px">✕</span></div>`;}).join("")}
        ${curAlerts.length?"</div>":""}
      </div>`;
    }

    if(aTab==="cm"){
      if (!termComRes && !termComLoad && !termComErr) {
        h += `<div style="padding:10px 16px;border-top:1px solid var(--gb)">
          <div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.15em;margin-bottom:6px">INTERROGATE YOUR THESIS (OPTIONAL)</div>
          ${_renderLensQuickPrompts(a.tk)}
          <textarea id="term-lens-thesis" oninput="_setLensThesis('${a.tk}',this.value)" placeholder="e.g. NVDA breaks out on AI capex cycle — add your view to stress-test" style="width:100%;min-height:56px;background:var(--bg);border:1px solid var(--gb);border-radius:6px;padding:8px;font-family:var(--sn);font-size:11px;color:var(--t2);resize:vertical;box-sizing:border-box">${(lensThesis[a.tk]||'').replace(/</g,'&lt;')}</textarea>
          <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-top:5px">Lens Engine fuses live quote · momentum · financials · earnings · analyst data</div>
        </div>`;
        h += `<button class="ap-committee-btn" onclick="runTermCommittee('${a.tk}')">⬢ RUN LENS ENGINE${_isPremium()?'':'<span style="font-size:8px;opacity:0.7;margin-left:6px">★ Premium</span>'}</button>`;
      }
      if (termComLoad) {
        h += `<div style="padding:12px 16px;font-family:var(--mn);font-size:10px;color:var(--bl);display:flex;align-items:center;gap:10px"><div style="width:12px;height:12px;border:2px solid var(--bl);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;flex-shrink:0"></div>LENS ENGINE — FUSING LIVE DATA + AI…</div>`;
      }
      if (termComErr) {
        h += `<div style="padding:14px 16px;border-top:1px solid var(--gb);color:var(--rd);font-family:var(--sn);font-size:12px;line-height:1.5">
          ${_escHtml(termComErr)}
          <div style="margin-top:8px;color:var(--t3);font-size:10px">No substitute analysis was shown. Please retry when the provider is available.</div>
          <button class="ap-committee-btn" onclick="runTermCommittee('${a.tk}')">↻ RETRY LENS ENGINE</button>
        </div>`;
      }
      if (termComRes) {
        if (termLensMeta) h += `<div style="padding:8px 16px;border-top:1px solid var(--gb)">${_renderLensPowers(termLensMeta)}</div>`;
        if (termLensIntel) h += `<div style="padding:0 8px 8px">${_renderLensIntel(termLensIntel)}</div>`;
        const synth = _getSynthesis(termComRes);
        const members = _getLensMembers(termComRes);
        if (termLensMeta?.weighted) {
          const w = termLensMeta.weighted;
          const wcol = w.dir === 'BUY' ? 'var(--gn)' : w.dir === 'AVOID' ? 'var(--rd)' : 'var(--gd)';
          h += `<div style="padding:8px 16px;border-top:1px solid var(--gb);display:flex;justify-content:space-between;align-items:center">
            <div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.15em">REGIME-WEIGHTED VIEW</div>
            <div style="font-family:var(--mn);font-size:14px;font-weight:900;color:${wcol}">${w.dir}</div>
          </div>`;
        }
        if (synth) {
          const vc = synth.verdict?.toUpperCase();
          const vcol = vc?.includes('IMPLEMENT')||vc?.includes('BUY') ? 'var(--gn)' : vc?.includes('REJECT')||vc?.includes('AVOID') ? 'var(--rd)' : 'var(--gd)';
          h += `<div style="background:${vcol}10;border-top:2px solid ${vcol};padding:12px 16px">
            <div style="font-family:var(--mn);font-size:8px;color:${vcol};letter-spacing:0.2em;margin-bottom:4px">RISK SYNTHESIS — FINAL VERDICT</div>
            <div style="font-family:var(--mn);font-size:20px;font-weight:900;color:${vcol}">${synth.verdict}</div>
            <div style="font-family:var(--sn);font-size:12px;color:var(--t2);margin-top:8px;line-height:1.6">${synth.analysis}</div>
          </div>`;
        }
        members.forEach(c => {
          const vc = c.verdict?.toUpperCase();
          const vcol = vc?.includes('BUY')||vc?.includes('IMPLEMENT')||vc?.includes('OVERWEIGHT') ? 'var(--gn)' : vc?.includes('AVOID')||vc?.includes('SELL')||vc?.includes('REDUCE') ? 'var(--rd)' : 'var(--gd)';
          h += `<div style="padding:10px 16px;border-top:1px solid var(--gb)">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
              <span style="font-family:var(--mn);font-size:10px;font-weight:800">${c.name.toUpperCase()}</span>
              <span style="font-family:var(--mn);font-size:10px;font-weight:800;color:${vcol}">${c.verdict}</span>
            </div>
            <div style="font-family:var(--sn);font-size:12px;color:var(--t2);line-height:1.55">${c.analysis}</div>
          </div>`;
        });
        h += `<button class="ap-committee-btn" onclick="runTermCommittee('${a.tk}')">⬢ RE-RUN LENSES</button>`;
      }
    }

    h += `<div style="padding:8px 16px;border-top:1px solid var(--gb)"><button onclick="termClear()" style="background:var(--b2);color:var(--t2);border:1px solid var(--gb);border-radius:6px;padding:5px 14px;font-family:var(--mn);font-size:9px;cursor:pointer;letter-spacing:0.1em">← BACK TO NEWS</button></div>`;

    el.innerHTML = h;
    if (_p2KeepScroll) requestAnimationFrame(() => { el.scrollTop = _p2Scroll; });
    // Render Lightweight Chart asynchronously
    setTimeout(() => renderCandleChart(termSelTk, termChartRange, 'candleChart'), 50);
    return;
  } else {
    titleEl.innerHTML = '<span class="panel-idx">02</span>News';
    subEl.textContent = newsLastFetch ? _newsRelTime(newsLastFetch.getTime())+' AGO' : (newsFetching?'FETCHING…':'STANDBY');
    let h = `<div class="p2-news-desk">`;
    h += _renderNewsToolbar({compact:true});
    h += _renderNewsBody({compact:true});
    h += `<div style="padding:8px 4px"><button type="button" class="news-act news-act-gold" onclick="nav('news')">Open full Newsroom →</button></div>`;
    h += `</div>`;
    el.innerHTML = h;
    if (_p2KeepScroll) requestAnimationFrame(() => { el.scrollTop = _p2Scroll; });
  }
}

// ─── TERMINAL PANEL 3: Signals + Calendar ───
function renderP3() {
  const el = document.getElementById('p3body');
  if (!el) return;
  const catCol = { Bullish:'var(--gn)', 'Macro Tailwind':'var(--gn)', Warning:'var(--rd)', Geopolitical:'var(--rd)', Accumulation:'var(--bl)', Momentum:'var(--gd)', Catalyst:'var(--pu)', Contrarian:'var(--cy)' };
  const dirIcon = { Bullish:'↑', 'Macro Tailwind':'↑', Warning:'⚠', Geopolitical:'⚠', Accumulation:'↑', Momentum:'↑', Catalyst:'●', Contrarian:'●', Bearish:'↓' };

  let h = `<div style="padding:4px 16px 6px;background:var(--b1);border-bottom:1px solid var(--gb)">
    <div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.15em;padding-top:8px">MARKET SIGNALS <span title="Signals are generated by analysis of price action, news, macro data and sentiment. They are informational only." style="cursor:help;color:var(--bl)">ⓘ</span></div>
  </div>`;

  SIGS.forEach((s, i) => {
    const bc = catCol[s.cat] || 'var(--gd)';
    const icon = dirIcon[s.cat] || '●';
    const cfCol = s.cf >= 75 ? 'var(--gn)' : s.cf >= 50 ? 'var(--gd)' : 'var(--rd)';
    const isOpen = _openNews.has(1000 + i);
    h += `<div style="border-left:3px solid ${bc};border-bottom:1px solid rgba(255,255,255,0.03);cursor:pointer" onclick="_toggleSig(${i})">
      <div style="display:flex;align-items:center;gap:10px;padding:10px 14px">
        <span style="font-family:var(--mn);font-size:16px;color:${bc};flex-shrink:0;width:18px;text-align:center">${icon}</span>
        <div style="flex:1;min-width:0">
          <div style="display:flex;align-items:center;gap:6px;margin-bottom:2px">
            <span style="font-family:var(--sn);font-size:12px;font-weight:700">${s.a}</span>
            <span style="font-family:var(--mn);font-size:9px;background:${bc}18;color:${bc};padding:1px 6px;border-radius:3px;font-weight:700">${s.cat.toUpperCase().slice(0,6)}</span>
          </div>
          <div style="font-family:var(--sn);font-size:11px;color:var(--t2);line-height:1.4">${s.x}</div>
          <div style="display:flex;align-items:center;gap:8px;margin-top:5px">
            <div style="flex:1;height:3px;background:var(--b3);border-radius:2px;overflow:hidden">
              <div style="height:100%;width:${s.cf}%;background:${cfCol};border-radius:2px;transition:width 0.5s"></div>
            </div>
            <span style="font-family:var(--mn);font-size:10px;font-weight:800;color:${cfCol};flex-shrink:0">${s.cf}%</span>
          </div>
        </div>
        <span style="font-family:var(--mn);font-size:10px;color:var(--t3);flex-shrink:0">${isOpen?'▲':'▼'}</span>
      </div>
      ${isOpen ? `<div style="padding:8px 14px 12px 46px;border-top:1px solid var(--gb);background:var(--b1)">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px">
          <div><span style="font-family:var(--mn);font-size:9px;color:var(--t3)">TARGET</span><div style="font-family:var(--mn);font-size:10px;color:var(--tx);font-weight:700">${s.tg}</div></div>
          <div><span style="font-family:var(--mn);font-size:9px;color:var(--t3)">TIMEFRAME</span><div style="font-family:var(--mn);font-size:10px;color:var(--tx);font-weight:700">${s.hz}</div></div>
          <div><span style="font-family:var(--mn);font-size:9px;color:var(--t3)">STRENGTH</span><div style="font-family:var(--mn);font-size:10px;color:${s.s==='Strong'?'var(--gn)':'var(--gd)'};font-weight:700">${s.s}</div></div>
          <div><span style="font-family:var(--mn);font-size:9px;color:var(--t3)">CONFIDENCE</span><div style="font-family:var(--mn);font-size:10px;color:${cfCol};font-weight:700">${s.cf}%</div></div>
        </div>
        <div style="font-family:var(--sn);font-size:11px;color:var(--t2);line-height:1.6">${s.x}</div>
        <div style="font-family:var(--mn);font-size:9px;color:var(--t3);margin-top:6px">Signal is informational only. Not investment advice.</div>
      </div>` : ''}
    </div>`;
  });

  // Calendar section
  const now = Date.now();
  const upcoming = EVENTS.filter(e => e.ts >= now - 86400000).slice(0, 6);
  const impCol = { high: 'var(--rd)', medium: 'var(--gd)', low: 'var(--t3)' };

  h += `<div style="padding:4px 16px 6px;background:var(--b1);border-bottom:1px solid var(--gb);border-top:1px solid var(--gb);margin-top:4px">
    <div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.15em;padding-top:8px">ECONOMIC CALENDAR</div>
  </div>`;
  upcoming.forEach(e => {
    const daysAway = Math.ceil((e.ts - now) / 86400000);
    const ic = impCol[e.impact] || 'var(--t3)';
    const impIcon = e.impact === 'high' ? '⚠' : e.impact === 'medium' ? '●' : '·';
    h += `<div class="calr">
      <span class="calr-date" style="color:${daysAway<=2?'var(--gd)':'var(--t3)'}">${e.date}</span>
      <span class="calr-txt">${e.event}</span>
      <span style="font-family:var(--mn);font-size:10px;color:${ic};flex-shrink:0;font-weight:700">${impIcon} ${e.impact.toUpperCase()}</span>
    </div>`;
  });

  el.innerHTML = h;
}

function _sf(filter){_screenerFilter=filter;renderP1();}
function _ss(sort){_screenerSort=sort;renderP1();}

function _toggleSig(idx) {
  const key = 1000 + idx;
  if (_openNews.has(key)) _openNews.delete(key);
  else _openNews.add(key);
  renderP3();
}

// ─── TERMINAL PANEL 4: Indices + Watchlist ───
function renderP4() {
  const el = document.getElementById('p4body');
  if (!el) return;

  let h = `<div style="font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.2em;padding:4px 8px;background:#000;border-bottom:1px solid var(--b4)">— GLOBAL INDICES</div>`;
  h += `<table class="tt"><thead><tr><th>INDEX</th><th>REGION</th><th>LEVEL</th><th>CHG%</th><th>TREND</th></tr></thead><tbody>`;
  IDX.forEach(idx => {
    const d = fp(idx.tk);
    const na = d.status === 'unavailable';
    const ch = liveChg(idx.tk);
    const col = na || ch == null ? 'var(--t3)' : ch > 0 ? 'var(--gn)' : ch < 0 ? 'var(--rd)' : 'var(--t3)';
    const sign = ch != null && ch >= 0 ? '+' : '';
    const trend = ch == null || ch === 0 ? '·' : (ch > 0 ? '▲' : '▼');
    h += `<tr onclick="termSelect('${idx.tk}')">
      <td style="font-weight:800">${idx.nm}</td>
      <td style="color:var(--t3)">${idx.rg}</td>
      <td data-fl="${idx.tk}" style="font-weight:700">${na?'<span style="color:var(--t3);opacity:0.55">—</span>':d.p}</td>
      <td style="color:${col};font-weight:700">${na?chgDim():`${sign}${d.c}%`}</td>
      <td style="color:${col};font-size:12px">${na?'':trend}</td>
    </tr>`;
  });
  h += `</tbody></table>`;

  // Regime — live model, not a hardcoded string
  const reP4 = _computeRegimeEngine();
  const pxLbl = (tk, prefix) => {
    const d = fp(tk);
    return d.status === "unavailable" ? `${prefix}—` : `${prefix}${d.p}`;
  };
  h += `<div style="font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.2em;padding:4px 8px;background:#000;border-top:1px solid var(--b4);border-bottom:1px solid var(--b4);margin-top:4px">— REGIME · MODEL</div>
  <div style="padding:6px 8px;border-bottom:1px solid var(--b4)">
    <div style="font-family:var(--mn);font-size:11px;font-weight:800;color:${reP4.col}">${reP4.label} · ${reP4.score}/100</div>
    <div style="font-family:var(--mn);font-size:8.5px;color:var(--t2);margin-top:3px">SPX ${pxLbl("SPX","")} · OIL ${pxLbl("WTI","$")} · GOLD ${pxLbl("XAU","$")} · BTC ${pxLbl("BTC","$")}</div>
  </div>`;

  const wl = getActiveWl();
  // Full book order = wl.tickers (required for drag-reorder indices)
  const w = _wlAssetRows(wl);

  // Watchlist header with switcher
  h += `<div style="background:var(--b1);border-top:1px solid var(--gb);border-bottom:1px solid var(--gb)">
    <div style="display:flex;align-items:center;gap:6px;padding:6px 14px;overflow-x:auto;-webkit-overflow-scrolling:touch">
      ${watchlists.map(wls=>`<button onclick="switchWatchlist('${wls.id}')" style="font-family:var(--mn);font-size:9px;font-weight:700;padding:3px 10px;border-radius:12px;cursor:pointer;border:1px solid ${wls.id===activeWlId?'var(--gd)':'var(--b4)'};background:${wls.id===activeWlId?'var(--gdG)':'transparent'};color:${wls.id===activeWlId?'var(--gd)':'var(--t3)'};white-space:nowrap;flex-shrink:0">${wls.name}</button>`).join('')}
      <button onclick="_newWl()" style="font-family:var(--mn);font-size:9px;padding:3px 10px;border-radius:12px;cursor:pointer;border:1px dashed var(--b4);background:transparent;color:var(--t3);white-space:nowrap;flex-shrink:0">+ New</button>
    </div>
  </div>`;

  if (!w.length) {
    h += `<div style="padding:20px 14px;text-align:center;font-family:var(--sn);font-size:12px;color:var(--t3)">No assets in this watchlist.<br><span style="font-size:11px">Right-click any ticker to add it.</span></div>`;
  } else {
    h += `<table class="tt" id="wl-table"><thead><tr><th>⠿</th><th>TKR</th><th>PRICE</th><th>CHG%</th><th>SC</th><th>✕</th></tr></thead><tbody>`;
    w.forEach((a,wi) => {
      const d = fp(a.tk);
      const na = d.status === 'unavailable';
      const ch = liveChg(a.tk);
      const col = na ? 'var(--t3)' : (ch == null ? 'var(--t3)' : ch > 0 ? 'var(--gn)' : ch < 0 ? 'var(--rd)' : 'var(--t3)');
      const sign = ch != null && ch >= 0 ? '+' : '';
      const arrow = ch == null || ch === 0 ? '' : (ch > 0 ? '↑' : '↓');
      const scShow = a._dyn ? Math.round(_tickerRegimeFit(a.tk, reP4).score) : a.sc;
      h += `<tr class="drag-row" draggable="true"
        ondragstart="_wlDragStart(event,${wi})"
        ondragover="_wlDragOver(event,${wi})"
        ondragleave="_wlDragLeave(event)"
        ondrop="_wlDrop(event,${wi})"
        ondragend="_wlDragEnd(event)"
        onclick="termSelect('${a.tk}')"
        oncontextmenu="_ctxShow(event,'${a.tk}')">
        <td style="color:var(--t3);cursor:grab">⠿</td>
        <td style="font-weight:800;color:${catBd(a.cat)}">${a.tk}</td>
        <td data-fl="${a.tk}">${na?'<span style="color:var(--t3);opacity:0.55">—</span>':'$'+d.p}</td>
        <td style="color:${col};font-weight:700">${na?chgDim():`${arrow}${sign}${d.c}%`}</td>
        <td style="color:${scC(scShow)};font-weight:800" title="${a._dyn?'Regime fit (model)':'Desk score'}">${scShow}</td>
        <td onclick="event.stopPropagation();removeFromWatchlist('${a.tk}')" style="color:var(--t3);cursor:pointer;text-align:center;font-size:12px">✕</td>
      </tr>`;
    });
    h += `</tbody></table>`;
  }

  el.innerHTML = h;
}

// ─── Timeframe chart fetch ───
async function fetchTermChart(tk, range) {
  termChartRange = range;
  _destroyCharts();
  const yhSym = YAHOO_SYMBOLS[tk] || tk;
  const intervalMap = {'1d':'5m','5d':'15m','1mo':'1h','6mo':'1d','1y':'1d'};
  const interval = intervalMap[range] || '5m';
  try {
    const res = await chartFetch(`/api/yahoo-chart?symbol=${encodeURIComponent(yhSym)}&range=${range}&interval=${interval}`, {signal: AbortSignal.timeout(10000)});
    if (!res.ok) return;
    const data = await res.json();
    const closes = data?.chart?.result?.[0]?.indicators?.quote?.[0]?.close;
    if (Array.isArray(closes)) {
      const clean = closes.filter(v => typeof v === 'number' && isFinite(v) && v > 0);
      if (clean.length >= 5) HIST[tk] = clean.slice(-120);
    }
  } catch(e) {}
  renderP2();
}

function _setRange(tk, range) {
  termChartRange = range;
  _destroyCharts();
  renderP2();
}

// ─── Earnings Intelligence ───
const _earnCache = {};
async function loadEarnings(tk, containerId) {
  _earnLoadTk = tk;
  const el = document.getElementById(containerId);
  if (!el) return;
  if (_earnCache[tk]) { el.innerHTML = renderEarnings(tk, _earnCache[tk]); return; }
  el.innerHTML = '<div style="padding:20px;text-align:center"><div style="width:14px;height:14px;border:2px solid var(--gn);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div><div style="font-family:var(--mn);font-size:10px;color:var(--t3)">LOADING EARNINGS…</div></div>';
  try {
    const res = await fetch('/api/earnings?symbol='+encodeURIComponent(tk), { signal: AbortSignal.timeout(12000) });
    if (!res.ok) throw new Error('no data');
    const data = await res.json();
    if (_earnLoadTk !== tk) return;
    const el2 = document.getElementById(containerId);
    if (!el2) return;
    _earnCache[tk] = data;
    el2.innerHTML = renderEarnings(tk, data);
  } catch(e) {
    if (_earnLoadTk !== tk) return;
    const el2 = document.getElementById(containerId);
    if (el2) el2.innerHTML = '<div style="padding:20px;text-align:center;font-family:var(--sn);font-size:13px;color:var(--t3)">Earnings data not available for '+tk+'</div>';
  }
}
function renderEarnings(tk, data) {
  if (!data||!data.history||!data.history.length) return '<div style="padding:20px;text-align:center;font-family:var(--sn);font-size:13px;color:var(--t3)">No earnings history for '+tk+'</div>';
  const h=data.history, beats=h.filter(e=>e.beat).length;
  const beatRate=data.beatRate, avgSurp=data.avgSurprise;
  let daysToNext=null,nextStr='—';
  if(data.nextEarnings?.date){
    const nd=new Date(data.nextEarnings.date);
    if(isFinite(nd.getTime())){
      daysToNext=Math.ceil((nd-Date.now())/86400000);
      nextStr=daysToNext<=0?'This week':daysToNext===1?'Tomorrow':daysToNext+' days';
    }
  }
  const GN='var(--gn)',RD='var(--rd)',GD='var(--gd)',T3='var(--t3)';
  // null beatRate must not paint red (null>=75 / >=50 are false → fell through to RD)
  const brCol=beatRate==null?T3:beatRate>=75?GN:beatRate>=50?GD:RD;
  const asCol=avgSurp==null?T3:avgSurp>0?GN:avgSurp<0?RD:'var(--t2)';
  let out=`<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:1px;background:rgba(255,255,255,0.04)">
    <div style="background:var(--bg);padding:14px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.12em;margin-bottom:6px">BEAT RATE</div><div style="font-family:var(--mn);font-size:26px;font-weight:900;color:${brCol}">${beatRate!=null?beatRate+'%':'—'}</div><div style="font-family:var(--sn);font-size:10px;color:var(--t3);margin-top:3px">${beats} of ${h.length} qtrs</div></div>
    <div style="background:var(--bg);padding:14px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.12em;margin-bottom:6px">AVG SURPRISE</div><div style="font-family:var(--mn);font-size:26px;font-weight:900;color:${asCol}">${avgSurp!=null?(avgSurp>0?'+':'')+avgSurp+'%':'—'}</div><div style="font-family:var(--sn);font-size:10px;color:var(--t3);margin-top:3px">vs Wall Street est</div></div>
    <div style="background:var(--bg);padding:14px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.12em;margin-bottom:6px">NEXT EARNINGS</div><div style="font-family:var(--mn);font-size:${daysToNext!=null&&daysToNext<=14?'16':'20'}px;font-weight:900;color:${daysToNext!=null&&daysToNext<=14?GD:'var(--tx)'}">${nextStr}</div><div style="font-family:var(--sn);font-size:10px;color:var(--t3);margin-top:3px">${data.nextEarnings?.date||'TBC'}</div></div>
    <div style="background:var(--bg);padding:14px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.12em;margin-bottom:6px">LAST EPS</div><div style="font-family:var(--mn);font-size:26px;font-weight:900;color:${h[0]?.beat?GN:RD}">$${h[0]?.actual!=null?Number(h[0].actual).toFixed(2):'—'}</div><div style="font-family:var(--sn);font-size:10px;color:var(--t3);margin-top:3px">Est $${h[0]?.estimate!=null?Number(h[0].estimate).toFixed(2):'—'}</div></div>
  </div>`;
  // Bar chart
  const rev=[...h].reverse(), mx=Math.max(...rev.map(e=>Math.max(Math.abs(e.actual||0),Math.abs(e.estimate||0))),0.01);
  const BW=22,CH=90;
  out+=`<div style="padding:14px;border-top:1px solid var(--gb)"><div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.15em;margin-bottom:10px">EPS ACTUAL vs ESTIMATE — LAST ${h.length} QUARTERS</div>
  <div style="overflow-x:auto"><svg width="${Math.max(380,rev.length*(BW*2+14))}" height="${CH+36}" style="display:block">
    ${rev.map((e,i)=>{
      const x=i*(BW*2+14)+4;
      const eH=Math.round(((e.estimate||0)/mx)*CH*0.85);
      const aH=Math.round(((e.actual||0)/mx)*CH*0.85);
      const c=e.beat?'#00C896':'#FF4757';
      const sp=e.surprisePct!=null?(e.surprisePct>0?'+':'')+e.surprisePct.toFixed(1)+'%':'';
      return `<rect x="${x}" y="${CH-eH}" width="${BW}" height="${eH}" fill="rgba(255,255,255,0.1)" rx="2"/>
              <rect x="${x+BW+2}" y="${CH-aH}" width="${BW}" height="${aH}" fill="${c}" rx="2" opacity="0.9"/>
              <text x="${x+BW}" y="${CH+13}" text-anchor="middle" font-family="JetBrains Mono" font-size="8" fill="#3D4D6A">${e.quarter||''}</text>
              <text x="${x+BW}" y="${CH+25}" text-anchor="middle" font-family="JetBrains Mono" font-size="8" fill="${c}">${sp}</text>`;
    }).join('')}
    <line x1="0" y1="${CH}" x2="100%" y2="${CH}" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>
  </svg></div>
  <div style="display:flex;gap:14px;font-family:var(--mn);font-size:9px;color:var(--t3);margin-top:6px"><span>░ Estimate</span><span style="color:var(--gn)">▮ Beat</span><span style="color:var(--rd)">▮ Miss</span></div></div>`;
  // Table
  out+=`<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-family:var(--mn);font-size:11px;min-width:380px">
    <thead><tr style="background:var(--b1);border-bottom:1px solid var(--gb)">
      <th style="padding:7px 12px;text-align:left;font-size:9px;color:var(--t3);letter-spacing:0.1em">QUARTER</th>
      <th style="padding:7px 12px;text-align:right;font-size:9px;color:var(--t3)">EST</th>
      <th style="padding:7px 12px;text-align:right;font-size:9px;color:var(--t3)">ACTUAL</th>
      <th style="padding:7px 12px;text-align:right;font-size:9px;color:var(--t3)">SURPRISE</th>
      <th style="padding:7px 12px;text-align:center;font-size:9px;color:var(--t3)">RESULT</th>
    </tr></thead><tbody>`;
  h.forEach(e=>{
    const c=e.beat?GN:RD;
    const sgn=e.surprisePct>0?'+':'';
    out+=`<tr style="border-bottom:1px solid rgba(255,255,255,0.025)">
      <td style="padding:7px 12px;color:var(--t2);font-weight:600">${e.quarter}</td>
      <td style="padding:7px 12px;text-align:right;color:var(--t3)">$${e.estimate?.toFixed(2)||'—'}</td>
      <td style="padding:7px 12px;text-align:right;font-weight:800;color:${c}">$${e.actual?.toFixed(2)||'—'}</td>
      <td style="padding:7px 12px;text-align:right;color:${c};font-weight:700">${e.surprisePct!=null?sgn+e.surprisePct.toFixed(2)+'%':'—'}</td>
      <td style="padding:7px 12px;text-align:center"><span style="font-size:10px;font-weight:800;color:${c}">${e.beat?'✓ BEAT':'✗ MISS'}</span></td>
    </tr>`;
  });
  out+='</tbody></table></div>';
  out+=`<div style="padding:8px;font-family:var(--mn);font-size:8px;color:var(--t3);text-align:center">Finnhub · EPS = Earnings Per Share · For research only</div>`;

  // AI Earnings Intelligence section
  const aiRes=_earAiResults[tk];
  const containerId=IS_DESKTOP()?'term-earn-root':'anlz-earn-root';
  if(aiRes){
    out+=renderEarningsAI(tk,aiRes);
  } else {
    out+=`<div id="${containerId}-ai">
      <div style="padding:12px 16px;display:flex;align-items:center;gap:10px;border-top:1px solid var(--gb);background:linear-gradient(90deg,rgba(245,158,11,0.03),transparent)">
        <button onclick="loadEarningsAI('${tk}','${containerId}',_earnCache['${tk}'])" style="flex:1;background:linear-gradient(135deg,rgba(245,158,11,0.08),rgba(245,158,11,0.02));color:var(--gd);border:1px solid rgba(245,158,11,0.3);border-radius:9px;padding:11px 14px;font-family:var(--sn);font-size:12px;font-weight:700;cursor:pointer;text-align:left">
          ⬢ AI Earnings Intelligence — Bull/Bear scenarios, EPS consensus, trade setup${!_isPremium()?'  <span style="font-size:10px;opacity:0.7">★ Premium</span>':''}
        </button>
      </div>
    </div>`;
  }
  return out;
}

// ─── Valuation Dashboard ───
const _valCache = {};

// Sector average multiples (S&P 500 and sector benchmarks)
const SECTOR_AVGS = {
  Technology:    {pe:32,evEbitda:22,pfcf:30,pb:8,  peg:2.2},
  Healthcare:    {pe:24,evEbitda:16,pfcf:22,pb:4,  peg:1.8},
  Financials:    {pe:13,evEbitda:10,pfcf:14,pb:1.5,peg:1.2},
  Energy:        {pe:12,evEbitda:8, pfcf:11,pb:2,  peg:1.0},
  Industrials:   {pe:22,evEbitda:14,pfcf:20,pb:4,  peg:1.8},
  ConsStaples:   {pe:22,evEbitda:15,pfcf:20,pb:6,  peg:2.5},
  ConsDisc:      {pe:28,evEbitda:18,pfcf:25,pb:5,  peg:2.0},
  Materials:     {pe:18,evEbitda:12,pfcf:16,pb:3,  peg:1.5},
  Utilities:     {pe:18,evEbitda:11,pfcf:17,pb:2,  peg:2.0},
  RealEstate:    {pe:35,evEbitda:20,pfcf:30,pb:2,  peg:2.8},
  CommServices:  {pe:20,evEbitda:12,pfcf:18,pb:3,  peg:1.6},
  SP500:         {pe:22,evEbitda:15,pfcf:20,pb:4,  peg:1.8},
};

function detectSector(tk) {
  const a = A.find(x => x.tk === tk);
  if (!a) return 'SP500';
  const th = (a.th || '').toLowerCase();
  if (th.includes('software')||th.includes('cloud')||th.includes('ai chip')||th.includes('semiconductor')||th.includes('tech')) return 'Technology';
  if (th.includes('pharma')||th.includes('biotech')||th.includes('drug')||th.includes('healthcare')||th.includes('medical')) return 'Healthcare';
  if (th.includes('bank')||th.includes('insurance')||th.includes('asset management')||th.includes('brokerage')) return 'Financials';
  if (th.includes('oil')||th.includes('crude')||th.includes('gas')||th.includes('energy')||th.includes('petroleum')) return 'Energy';
  if (th.includes('consumer')||th.includes('retail')||th.includes('food')||th.includes('beverage')) return 'ConsStaples';
  return 'SP500';
}

async function loadValuation(tk, containerId) {
  _valLoadTk = tk;
  const el = document.getElementById(containerId);
  if (!el) return;
  if (_valCache[tk]) { el.innerHTML = renderValuation(tk, _valCache[tk]); return; }

  el.innerHTML = '<div style="padding:20px;text-align:center"><div style="width:14px;height:14px;border:2px solid var(--pu);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div><div style="font-family:var(--mn);font-size:10px;color:var(--t3)">LOADING VALUATION DATA…</div></div>';

  try {
    let finData = _finCache[tk];
    if (!finData) {
      const res = await fetch('/api/financials?symbol='+encodeURIComponent(tk), { signal: AbortSignal.timeout(12000) });
      if (res.ok) { finData = await res.json(); _finCache[tk] = finData; }
    }
    if (!finData?.metrics) throw new Error('no metrics');

    const peers = (finData?.peers || []).slice(0, 4).filter(p => p !== tk && A.find(a => a.tk === p));
    const peerData = {};
    if (peers.length) {
      await Promise.allSettled(peers.map(async peer => {
        if (_finCache[peer]) { peerData[peer] = _finCache[peer]; return; }
        try {
          const r = await fetch('/api/financials?symbol='+encodeURIComponent(peer), { signal: AbortSignal.timeout(8000) });
          if (r.ok) { peerData[peer] = await r.json(); _finCache[peer] = peerData[peer]; }
        } catch(e) {}
      }));
    }

    if (_valLoadTk !== tk) return;
    const el2 = document.getElementById(containerId);
    if (!el2) return;
    // Price is read live in renderValuation — never freeze a $0 snapshot from pre-sync load
    _valCache[tk] = { finData, peerData, peers };
    el2.innerHTML = renderValuation(tk, _valCache[tk]);
  } catch(e) {
    if (_valLoadTk !== tk) return;
    const el2 = document.getElementById(containerId);
    if (el2) el2.innerHTML = '<div style="padding:20px;text-align:center;font-family:var(--sn);font-size:13px;color:var(--t3)">Valuation data not available for '+tk+'<br><span style="font-size:11px">US-listed stocks with financial metrics only</span></div>';
  }
}

function renderValuation(tk, cache) {
  const { finData, peerData, peers } = cache;
  // Always prefer feed-confirmed mark — cache must not lock in pre-sync $0
  const price = livePx(tk);
  if (!finData?.metrics) return `<div style="padding:20px;text-align:center;font-family:var(--sn);font-size:13px;color:var(--t3)">Valuation metrics unavailable for ${tk}</div>`;
  const m = finData.metrics;
  const sector = detectSector(tk);
  const bench = SECTOR_AVGS[sector] || SECTOR_AVGS.SP500;
  const a = A.find(x => x.tk === tk);

  const fmt = (v, suffix='x') => v==null||v===0?'—':`${(+v).toFixed(1)}${suffix}`;
  const fmtP = (v) => v==null?'—':`$${(+v).toFixed(2)}`;

  // Valuation rating: cheap=green, fair=gold, expensive=red
  function rate(val, avg) {
    if (!val || !avg) return {col:'var(--t3)', label:'N/A', score:50};
    const ratio = val/avg;
    if (ratio < 0.8) return {col:'var(--gn)', label:'CHEAP', score:20};
    if (ratio < 1.0) return {col:'#86efac', label:'FAIR-CHEAP', score:35};
    if (ratio < 1.2) return {col:'var(--gd)', label:'FAIR', score:50};
    if (ratio < 1.5) return {col:'#fbbf24', label:'FAIR-RICH', score:65};
    if (ratio < 2.0) return {col:'var(--rd)', label:'EXPENSIVE', score:80};
    return {col:'#ff0000', label:'VERY EXPENSIVE', score:95};
  }

  const multiples = [
    {label:'P/E Ratio', val:m.peTTM, avg:bench.pe, desc:'Price vs trailing 12-month earnings'},
    {label:'EV/EBITDA', val:m.evEbitdaTTM, avg:bench.evEbitda, desc:'Enterprise value vs operating earnings'},
    {label:'P/FCF', val:m.pfcfShareTTM, avg:bench.pfcf, desc:'Price vs free cash flow per share'},
    {label:'P/Book', val:m.pbQuarterly, avg:bench.pb, desc:'Price vs book value of equity'},
    {label:'PEG Ratio', val:m.pegTTM, avg:bench.peg, desc:'P/E relative to earnings growth rate'},
  ];

  const ratings = multiples.map(mt => rate(mt.val, mt.avg));
  const validRatings = ratings.filter(r => r.label !== 'N/A');
  const overallScore = validRatings.length ? Math.round(validRatings.reduce((s,r)=>s+r.score,0)/validRatings.length) : 50;
  const overallCol = overallScore <= 35 ? 'var(--gn)' : overallScore <= 55 ? 'var(--gd)' : 'var(--rd)';
  const overallLabel = overallScore <= 35 ? 'UNDERVALUED' : overallScore <= 55 ? 'FAIRLY VALUED' : overallScore <= 70 ? 'OVERVALUED' : 'VERY EXPENSIVE';

  let out = '';

  // Overall verdict banner
  out += `<div style="padding:16px;background:${overallCol}10;border-bottom:3px solid ${overallCol};display:flex;justify-content:space-between;align-items:center">
    <div>
      <div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.18em;margin-bottom:4px">VALUATION VERDICT vs ${sector.toUpperCase()}</div>
      <div style="font-family:var(--sn);font-size:22px;font-weight:900;color:${overallCol}">${overallLabel}</div>
      <div style="font-family:var(--sn);font-size:11px;color:var(--t2);margin-top:4px">Based on ${validRatings.length} valuation metrics</div>
    </div>
    <div style="text-align:right">
      <div style="font-family:var(--mn);font-size:9px;color:var(--t3);margin-bottom:4px">EXPENSIVENESS</div>
      <div style="font-family:var(--mn);font-size:36px;font-weight:900;line-height:1;color:${overallCol}">${overallScore}</div>
      <div style="font-family:var(--mn);font-size:9px;color:var(--t3)">0=cheap 100=expensive</div>
    </div>
  </div>`;

  // Multiple comparison grid
  out += `<div style="border-bottom:1px solid var(--gb)">
    <div style="padding:8px 14px;font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.2em;background:var(--b1)">MULTIPLES vs ${sector.toUpperCase()} AVERAGE</div>
    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:1px;background:rgba(255,255,255,0.04)">
      ${multiples.map((mt, i) => {
        const r = ratings[i];
        return `<div style="background:var(--bg);padding:12px 8px;text-align:center">
          <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:6px;letter-spacing:0.05em">${mt.label}</div>
          <div style="font-family:var(--mn);font-size:18px;font-weight:900;color:${r.col}">${fmt(mt.val)}</div>
          <div style="font-family:var(--mn);font-size:9px;color:var(--t3);margin:3px 0">Avg: ${fmt(mt.avg)}</div>
          <div style="font-family:var(--mn);font-size:8px;font-weight:700;color:${r.col};background:${r.col}15;border-radius:3px;padding:1px 4px">${r.label}</div>
        </div>`;
      }).join('')}
    </div>
  </div>`;

  // 52-week range position
  const h52 = m['52WeekHigh'] || 0;
  const l52 = m['52WeekLow'] || 0;
  if (h52 && l52 && price) {
    const pos = Math.min(100, Math.max(0, ((price - l52) / (h52 - l52)) * 100));
    const posCol = pos < 30 ? 'var(--gn)' : pos < 70 ? 'var(--gd)' : 'var(--rd)';
    out += `<div style="padding:14px;border-bottom:1px solid var(--gb)">
      <div style="font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.2em;margin-bottom:10px">52-WEEK RANGE POSITION</div>
      <div style="display:flex;justify-content:space-between;font-family:var(--mn);font-size:10px;color:var(--t3);margin-bottom:6px">
        <span>Low: $${l52.toFixed(2)}</span>
        <span style="color:${posCol};font-weight:700">Current: $${price.toFixed(2)} (${pos.toFixed(0)}% of range)</span>
        <span>High: $${h52.toFixed(2)}</span>
      </div>
      <div style="position:relative;height:8px;background:linear-gradient(to right,var(--gn),var(--gd),var(--rd));border-radius:4px">
        <div style="position:absolute;top:50%;left:${pos}%;transform:translate(-50%,-50%);width:16px;height:16px;background:var(--bg);border:3px solid ${posCol};border-radius:50%;box-shadow:0 0 8px ${posCol}80"></div>
      </div>
      <div style="font-family:var(--sn);font-size:11px;color:var(--t2);margin-top:8px">${pos < 30 ? '⬇️ Near 52-week lows — potential value opportunity or deteriorating fundamentals' : pos > 70 ? '⬆️ Near 52-week highs — momentum strong but limited upside to historical range' : '↔️ Mid-range — balanced risk/reward from a price momentum perspective'}</div>
    </div>`;
  }

  // Reverse DCF — what growth is priced in
  const fcfPerShare = m.cashFlowPerShareTTM;
  const pe = m.peTTM;
  const eps = m.epsTTM;
  if (price && fcfPerShare && fcfPerShare > 0) {
    const wacc = 0.09; // 9% WACC assumption
    const termG = 0.03; // 3% terminal growth
    // Simplified: price ≈ FCF / (WACC - g_implied) → g_implied = WACC - FCF/price
    const impliedG = ((wacc - (fcfPerShare / price)) * 100).toFixed(1);
    const impliedCol = parseFloat(impliedG) > 20 ? 'var(--rd)' : parseFloat(impliedG) > 12 ? 'var(--gd)' : 'var(--gn)';

    out += `<div style="padding:14px;border-bottom:1px solid var(--gb);background:var(--b1)">
      <div style="font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.2em;margin-bottom:8px">REVERSE DCF — WHAT GROWTH IS PRICED IN?</div>
      <div style="display:flex;align-items:center;gap:16px;margin-bottom:8px">
        <div style="text-align:center">
          <div style="font-family:var(--mn);font-size:9px;color:var(--t3);margin-bottom:4px">IMPLIED FCF GROWTH</div>
          <div style="font-family:var(--mn);font-size:28px;font-weight:900;color:${impliedCol}">${impliedG}%</div>
          <div style="font-family:var(--mn);font-size:9px;color:var(--t3)">per year (∞ horizon)</div>
        </div>
        <div style="flex:1">
          <div style="font-family:var(--sn);font-size:12px;color:var(--t2);line-height:1.65">
            At <strong style="color:var(--tx)">$${price.toFixed(2)}</strong> with FCF/share of <strong style="color:var(--tx)">$${fcfPerShare.toFixed(2)}</strong> and WACC of 9%, the market is pricing in <strong style="color:${impliedCol}">${impliedG}% annual FCF growth</strong> in perpetuity.
            ${parseFloat(impliedG) > 20 ? '<br><br>This requires exceptional execution to justify.' : parseFloat(impliedG) > 12 ? '<br><br>Ambitious but achievable for a high-quality compounder.' : '<br><br>Conservative assumption — likely undervalued if growth continues.'}
          </div>
        </div>
      </div>
      <div style="font-family:var(--mn);font-size:8px;color:var(--t3)">Assumptions: WACC 9% · Gordon Growth simplified model · Not a precise DCF</div>
    </div>`;
  }

  const outSanctions = _renderSanctionsWatch(tk);
  let outPeer = _renderPeerBattleStation(tk, cache);

  // Peer comparison table
  const peerTks = [tk, ...peers.filter(p => peerData[p])];
  if (peerTks.length > 1) {
    out += `<div style="border-bottom:1px solid var(--gb)">
      <div style="padding:8px 14px;font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.2em;background:var(--b1)">PEER COMPARISON</div>
      <div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-family:var(--mn);font-size:11px;min-width:400px">
        <thead><tr style="background:var(--b1)">
          <th style="padding:7px 12px;text-align:left;font-size:9px;color:var(--t3)">TICKER</th>
          <th style="padding:7px 12px;text-align:right;font-size:9px;color:var(--t3)">P/E</th>
          <th style="padding:7px 12px;text-align:right;font-size:9px;color:var(--t3)">EV/EBITDA</th>
          <th style="padding:7px 12px;text-align:right;font-size:9px;color:var(--t3)">P/FCF</th>
          <th style="padding:7px 12px;text-align:right;font-size:9px;color:var(--t3)">NET MARGIN</th>
          <th style="padding:7px 12px;text-align:right;font-size:9px;color:var(--t3)">ROE</th>
        </tr></thead><tbody>`;

    peerTks.forEach(ptk => {
      const pm = ptk === tk ? m : peerData[ptk]?.metrics || {};
      const pa = A.find(x => x.tk === ptk);
      const isCurrent = ptk === tk;
      out += `<tr style="border-bottom:1px solid rgba(255,255,255,0.025);background:${isCurrent?'rgba(245,166,35,0.05)':''}">
        <td style="padding:7px 12px;font-weight:800;color:${isCurrent?'var(--gd)':'var(--t2)'}">${ptk}${isCurrent?' ★':''}</td>
        <td style="padding:7px 12px;text-align:right">${fmt(pm.peTTM)}</td>
        <td style="padding:7px 12px;text-align:right">${fmt(pm.evEbitdaTTM)}</td>
        <td style="padding:7px 12px;text-align:right">${fmt(pm.pfcfShareTTM)}</td>
        <td style="padding:7px 12px;text-align:right;color:${pm.netProfitMarginTTM>20?'var(--gn)':pm.netProfitMarginTTM>10?'var(--gd)':'var(--t2)'}">${pm.netProfitMarginTTM?pm.netProfitMarginTTM.toFixed(1)+'%':'—'}</td>
        <td style="padding:7px 12px;text-align:right;color:${pm.roeTTM>20?'var(--gn)':'var(--t2)'}">${pm.roeTTM?pm.roeTTM.toFixed(1)+'%':'—'}</td>
      </tr>`;
    });

    out += '</tbody></table></div></div>';
  }

  if (outPeer) out = outPeer + out;
  if (outSanctions) out = outSanctions + out;

  // Implied fair value scenarios
  if (eps && eps > 0 && bench.pe) {
    const bearFV = (eps * bench.pe * 0.75).toFixed(2);
    const baseFV = (eps * bench.pe).toFixed(2);
    const bullFV = (eps * bench.pe * 1.4).toFixed(2);
    const priceStr = price ? `$${price.toFixed(2)}` : '—';
    out += `<div style="padding:14px">
      <div style="font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.2em;margin-bottom:10px">IMPLIED FAIR VALUE — P/E METHOD (EPS × ${sector} Avg P/E ${bench.pe}x)</div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:10px">
        <div style="background:var(--rdG);border:1px solid rgba(255,71,87,0.2);border-radius:8px;padding:12px;text-align:center">
          <div style="font-family:var(--mn);font-size:9px;color:var(--rd);margin-bottom:4px">BEAR (0.75x avg)</div>
          <div style="font-family:var(--mn);font-size:18px;font-weight:800;color:var(--rd)">$${bearFV}</div>
        </div>
        <div style="background:var(--gdG);border:1px solid rgba(245,166,35,0.3);border-radius:8px;padding:12px;text-align:center">
          <div style="font-family:var(--mn);font-size:9px;color:var(--gd);margin-bottom:4px">BASE (avg P/E)</div>
          <div style="font-family:var(--mn);font-size:18px;font-weight:800;color:var(--gd)">$${baseFV}</div>
        </div>
        <div style="background:var(--gnG);border:1px solid rgba(0,200,150,0.2);border-radius:8px;padding:12px;text-align:center">
          <div style="font-family:var(--mn);font-size:9px;color:var(--gn);margin-bottom:4px">BULL (1.4x avg)</div>
          <div style="font-family:var(--mn);font-size:18px;font-weight:800;color:var(--gn)">$${bullFV}</div>
        </div>
      </div>
      <div style="font-family:var(--sn);font-size:11px;color:var(--t2);line-height:1.6">Current price <strong style="color:var(--tx)">${priceStr}</strong> vs base fair value <strong style="color:var(--gd)">$${baseFV}</strong> — ${price ? (price < parseFloat(baseFV) ? `<span style="color:var(--gn)">↓ ${((parseFloat(baseFV)-price)/price*100).toFixed(1)}% below base fair value</span>` : `<span style="color:var(--rd)">↑ ${((price-parseFloat(baseFV))/parseFloat(baseFV)*100).toFixed(1)}% above base fair value</span>`) : ''}</div>
      <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-top:8px">Simplified P/E method only · One of many approaches · Not investment advice</div>
    </div>`;
  }

  return out;
}

// ─── Financial Intelligence ───
const _finCache = {};
const _stmtCache = {};
let _stmtPeriod = 'annual';
let _finTab = 'metrics';
let _finTk = null;
let _finCid = null;

async function loadFinancials(tk, containerId) {
  _finTk = tk;
  _finCid = containerId;
  const el = document.getElementById(containerId);
  if (!el) return;

  if (_finTab !== 'metrics') {
    await _fetchStatements(tk, containerId);
    return;
  }

  if (_finCache[tk]) {
    el.innerHTML = renderFinancials(tk, _finCache[tk]);
    return;
  }

  el.innerHTML = `<div style="padding:20px;text-align:center"><div style="width:14px;height:14px;border:2px solid var(--bl);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div><div style="font-family:var(--mn);font-size:10px;color:var(--t3)">LOADING FINANCIALS…</div></div>`;
  try {
    const res = await fetch(`/api/financials?symbol=${encodeURIComponent(tk)}`, { signal: AbortSignal.timeout(12000) });
    if (!res.ok) throw new Error('no data');
    const data = await res.json();
    if (_finTk !== tk || _finCid !== containerId) return;
    const el2 = document.getElementById(containerId);
    if (!el2) return;
    _finCache[tk] = data;
    el2.innerHTML = renderFinancials(tk, data);
  } catch(e) {
    if (_finTk !== tk || _finCid !== containerId) return;
    const el2 = document.getElementById(containerId);
    if (el2) el2.innerHTML = `<div style="padding:20px;text-align:center;font-family:var(--sn);font-size:13px;color:var(--t3)">Financial data not available for ${tk}<br><span style="font-size:11px">Available for US-listed stocks only</span></div>`;
  }
}

function switchFinTab(tab) {
  if (tab !== 'metrics' && !_isPremium()) { _showLoginGate('Financial Statements'); return; }
  _finTab = tab;
  if (_finTk && _finCid) loadFinancials(_finTk, _finCid);
}

function switchStmtPeriod(period) {
  if (!_isPremium()) { _showLoginGate('Financial Statements'); return; }
  _stmtPeriod = period;
  if (_finTk && _finCid && _finTab !== 'metrics') _fetchStatements(_finTk, _finCid);
}

async function _fetchStatements(tk, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const cacheKey = `${tk}_${_stmtPeriod}`;
  const tabBar = _renderFinTabBar(tk);
  const periodToggle = `<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 14px;border-bottom:1px solid var(--gb);background:var(--b1)">
    <div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.12em">SOURCE: FMP · ${_stmtPeriod.toUpperCase()}</div>
    <div style="display:flex;gap:4px">
      <button onclick="switchStmtPeriod('annual')" style="font-family:var(--mn);font-size:9px;font-weight:700;padding:3px 10px;border-radius:5px;cursor:pointer;border:1px solid ${_stmtPeriod==='annual'?'var(--gd)':'var(--gb)'};background:${_stmtPeriod==='annual'?'var(--gdG)':'var(--bg)'};color:${_stmtPeriod==='annual'?'var(--gd)':'var(--t3)'}">Annual</button>
      <button onclick="switchStmtPeriod('quarter')" style="font-family:var(--mn);font-size:9px;font-weight:700;padding:3px 10px;border-radius:5px;cursor:pointer;border:1px solid ${_stmtPeriod==='quarter'?'var(--gd)':'var(--gb)'};background:${_stmtPeriod==='quarter'?'var(--gdG)':'var(--bg)'};color:${_stmtPeriod==='quarter'?'var(--gd)':'var(--t3)'}">Quarterly</button>
    </div>
  </div>`;
  if (_stmtCache[cacheKey]) {
    el.innerHTML = tabBar + periodToggle + renderStmtContent(_stmtCache[cacheKey]);
    return;
  }
  el.innerHTML = tabBar + periodToggle + `<div style="padding:40px;text-align:center"><div style="width:14px;height:14px;border:2px solid var(--bl);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 12px"></div><div style="font-family:var(--mn);font-size:10px;color:var(--t3)">LOADING FINANCIAL STATEMENTS…</div></div>`;
  try {
    const res = await fetch(`/api/statements?symbol=${encodeURIComponent(tk)}&period=${_stmtPeriod}`, { signal: AbortSignal.timeout(14000) });
    if (res.status === 401) { _showLoginGate('Financial Statements'); throw new Error('auth'); }
    if (!res.ok) throw new Error('no data');
    const data = await res.json();
    if (_finTk !== tk) return;
    const el2 = document.getElementById(containerId);
    if (!el2) return;
    _stmtCache[cacheKey] = data;
    el2.innerHTML = tabBar + periodToggle + renderStmtContent(data);
  } catch(e) {
    if (_finTk !== tk) return;
    const el2 = document.getElementById(containerId);
    if (el2) el2.innerHTML = tabBar + `<div style="padding:20px;text-align:center;font-family:var(--sn);font-size:13px;color:var(--t3)">Statement data unavailable.<br><span style="font-size:11px">Requires FMP_API_KEY — see Settings for setup guide.</span></div>`;
  }
}

function _renderFinTabBar(tk) {
  const tabs = [['metrics','📊 Metrics'],['income','📋 Income'],['balance','🏦 Balance'],['cashflow','💵 Cash Flow']];
  const prem = !_isPremium();
  return `<div style="display:flex;gap:0;border-bottom:1px solid var(--gb);background:var(--b1)">
    ${tabs.map(([id,lb])=>`<button onclick="switchFinTab('${id}')" style="flex:1;padding:9px 4px;font-family:var(--mn);font-size:9px;font-weight:700;cursor:pointer;border:none;border-bottom:2px solid ${_finTab===id?'var(--gd)':'transparent'};background:${_finTab===id?'var(--gdG)':'transparent'};color:${_finTab===id?'var(--gd)':'var(--t3)'};letter-spacing:0.08em;transition:color 0.15s">${lb}${prem&&id!=='metrics'?'<span style="color:var(--gd);font-size:7px;vertical-align:super">★</span>':''}</button>`).join('')}
  </div>`;
}

function renderStmtContent(data) {
  const fmtM = v => v == null ? '—' : Math.abs(v) >= 1e9 ? `${(v/1e9).toFixed(2)}B` : Math.abs(v) >= 1e6 ? `${(v/1e6).toFixed(1)}M` : v.toFixed(0);
  const fmtP = v => v == null ? '—' : `${(v*100).toFixed(1)}%`;
  const colVal = v => v == null ? '' : v >= 0 ? 'color:var(--gn)' : 'color:var(--rd)';

  const rows = _finTab === 'income' ? [
    { label: 'Revenue', key: 'revenue', fmt: fmtM },
    { label: 'Cost of Revenue', key: 'costOfRevenue', fmt: fmtM },
    { label: 'Gross Profit', key: 'grossProfit', fmt: fmtM, bold: true },
    { label: 'Gross Margin', key: 'grossMargin', fmt: fmtP, col: true },
    { label: 'R&D', key: 'rd', fmt: fmtM },
    { label: 'SG&A', key: 'sga', fmt: fmtM },
    { label: 'Operating Expenses', key: 'operatingExpenses', fmt: fmtM },
    { label: 'EBITDA', key: 'ebitda', fmt: fmtM, bold: true },
    { label: 'Operating Income', key: 'operatingIncome', fmt: fmtM, bold: true },
    { label: 'Operating Margin', key: 'operatingMargin', fmt: fmtP, col: true },
    { label: 'Interest Expense', key: 'interestExpense', fmt: fmtM },
    { label: 'Net Income', key: 'netIncome', fmt: fmtM, bold: true },
    { label: 'Net Margin', key: 'netMargin', fmt: fmtP, col: true },
    { label: 'EPS (Basic)', key: 'eps', fmt: v => v==null?'—':`$${(+v).toFixed(2)}` },
    { label: 'EPS (Diluted)', key: 'epsDiluted', fmt: v => v==null?'—':`$${(+v).toFixed(2)}` },
    { label: 'Shares Out', key: 'sharesOutstanding', fmt: v => v==null?'—':`${(v/1e6).toFixed(0)}M` },
  ] : _finTab === 'balance' ? [
    { label: 'Cash & Equivalents', key: 'cash', fmt: fmtM, bold: true },
    { label: 'Short-term Investments', key: 'shortTermInvestments', fmt: fmtM },
    { label: 'Accounts Receivable', key: 'accountsReceivable', fmt: fmtM },
    { label: 'Inventory', key: 'inventory', fmt: fmtM },
    { label: 'Total Current Assets', key: 'totalCurrentAssets', fmt: fmtM, bold: true },
    { label: 'Total Assets', key: 'totalAssets', fmt: fmtM, bold: true },
    { label: 'Total Current Liabilities', key: 'totalCurrentLiabilities', fmt: fmtM },
    { label: 'Long-term Debt', key: 'longTermDebt', fmt: fmtM },
    { label: 'Total Debt', key: 'totalDebt', fmt: fmtM, bold: true },
    { label: 'Total Liabilities', key: 'totalLiabilities', fmt: fmtM },
    { label: 'Total Equity', key: 'totalEquity', fmt: fmtM, bold: true },
    { label: 'Retained Earnings', key: 'retainedEarnings', fmt: fmtM },
    { label: 'Current Ratio', key: 'currentRatio', fmt: v => v==null?'—':`${(+v).toFixed(2)}x` },
    { label: 'Debt / Equity', key: 'debtToEquity', fmt: v => v==null?'—':`${(+v).toFixed(2)}x` },
  ] : [
    { label: 'Operating Cash Flow', key: 'operatingCF', fmt: fmtM, bold: true },
    { label: 'Capital Expenditure', key: 'capex', fmt: fmtM },
    { label: 'Free Cash Flow', key: 'freeCashFlow', fmt: fmtM, bold: true },
    { label: 'FCF Margin', key: 'fcfMargin', fmt: fmtP, col: true },
    { label: 'Dividends Paid', key: 'dividendsPaid', fmt: fmtM },
    { label: 'Stock Repurchase', key: 'stockRepurchase', fmt: fmtM },
    { label: 'Debt Repayment', key: 'debtRepayment', fmt: fmtM },
    { label: 'Investing CF', key: 'investingCF', fmt: fmtM },
    { label: 'Financing CF', key: 'financingCF', fmt: fmtM },
    { label: 'Net Change in Cash', key: 'netChangeInCash', fmt: fmtM },
  ];

  const stmtArr = _finTab === 'income' ? (data.income||[]) : _finTab === 'balance' ? (data.balance||[]) : (data.cashflow||[]);
  if (!stmtArr.length) return `<div style="padding:24px;text-align:center;font-family:var(--mn);font-size:11px;color:var(--t3)">No statement data available for this ticker.</div>`;

  const cols = stmtArr.slice(0, _stmtPeriod === 'quarter' ? 5 : 4);
  let h = `<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-family:var(--mn);font-size:11px;min-width:520px">
    <thead><tr style="background:var(--b1);border-bottom:1px solid var(--gb)">
      <th style="padding:8px 12px;text-align:left;font-size:9px;color:var(--t3);letter-spacing:0.1em;white-space:nowrap;font-weight:600">METRIC</th>
      ${cols.map(c=>`<th style="padding:8px 12px;text-align:right;font-size:9px;color:var(--t3);letter-spacing:0.08em;white-space:nowrap;font-weight:600">${(c.date||'').slice(0,7)}</th>`).join('')}
    </tr></thead><tbody>
    ${rows.map(r=>`<tr style="border-bottom:1px solid rgba(255,255,255,0.03);${r.bold?'background:rgba(255,255,255,0.02)':''}">
      <td style="padding:7px 12px;color:var(--t2);font-size:${r.bold?'10':'9'}px;font-weight:${r.bold?'700':'400'};white-space:nowrap">${r.label}</td>
      ${cols.map(c=>{const v=c[r.key];const fv=r.fmt(v);return `<td style="padding:7px 12px;text-align:right;font-weight:${r.bold?'700':'400'};${r.col&&v!=null?colVal(v):'color:var(--tx)'}">${fv}</td>`;}).join('')}
    </tr>`).join('')}
    </tbody></table></div>`;

  return h;
}

function renderFinancials(tk, data) {
  const m = data.metrics || {};
  const pt = data.priceTarget || {};
  const ins = data.insiders || [];
  const peers = data.peers || [];
  const recs = data.recommendations || [];
  const upgrades = data.upgrades || [];

  const fmt = (v, suffix='') => v == null || v === 0 ? '—' : `${(+v).toFixed(2)}${suffix}`;
  const pctCol = v => !v ? 'var(--t2)' : v > 0 ? 'var(--gn)' : 'var(--rd)';

  let h = _renderFinTabBar(tk);

  h += `<div style="padding:8px 14px 4px;font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.12em;background:var(--b1);border-bottom:1px solid var(--gb)">KEY RATIOS — TTM · Source: Finnhub</div>`;

  // 36 KEY METRICS
  const metrics = [
    ['VALUATION', [
      ['P/E (TTM)', fmt(m.peTTM, 'x')],
      ['EV/EBITDA', fmt(m.evEbitdaTTM, 'x')],
      ['P/FCF', fmt(m.pfcfShareTTM, 'x')],
      ['PEG Ratio', fmt(m.pegTTM, 'x')],
      ['EV/Revenue', fmt(m.evRevenueTTM, 'x')],
      ['P/B', fmt(m.pbQuarterly, 'x')],
    ]],
    ['PROFITABILITY', [
      ['Gross Margin', fmt(m.grossMarginTTM, '%')],
      ['Operating Margin', fmt(m.operatingMarginTTM, '%')],
      ['Net Margin', fmt(m.netProfitMarginTTM, '%')],
      ['ROE', fmt(m.roeTTM, '%')],
      ['ROA', fmt(m.roaTTM, '%')],
      ['ROIC', fmt(m.roicTTM, '%')],
    ]],
    ['GROWTH', [
      ['Revenue Growth YoY', fmt(m.revenueGrowthTTMYoy, '%')],
      ['EPS Growth TTM', fmt(m.epsGrowthTTMYoy, '%')],
      ['FCF Growth 5Y', fmt(m.fcfGrowth5Y, '%')],
      ['Rev Growth 5Y', fmt(m.revenueGrowth5Y, '%')],
      ['EPS Growth 5Y', fmt(m.epsGrowth5Y, '%')],
      ['Div Growth 5Y', fmt(m.dividendGrowthRate5Y, '%')],
    ]],
    ['FINANCIAL HEALTH', [
      ['Current Ratio', fmt(m.currentRatioQuarterly)],
      ['Quick Ratio', fmt(m.quickRatioQuarterly)],
      ['Debt/Equity', fmt(m.totalDebt_totalEquityQuarterly)],
      ['Net Debt/EBITDA', fmt(m.netDebt_ebitdaTTM, 'x')],
      ['Interest Coverage', fmt(m.netInterestCoverageTTM, 'x')],
      ['Asset Turnover', fmt(m.assetTurnoverTTM)],
    ]],
    ['PER SHARE', [
      ['EPS (TTM)', fmt(m.epsTTM)],
      ['FCF/Share', fmt(m.cashFlowPerShareTTM)],
      ['Dividend/Share', fmt(m.dividendPerShareTTM)],
      ['Dividend Yield', fmt(m.currentDividendYieldTTM, '%')],
      ['Payout Ratio', fmt(m.payoutRatioTTM, '%')],
      ['Book Value/Share', fmt(m.bookValuePerShareQuarterly)],
    ]],
    ['MARKET DATA', [
      ['52W High', m['52WeekHigh'] ? `$${(+m['52WeekHigh']).toFixed(2)}` : '—'],
      ['52W Low', m['52WeekLow'] ? `$${(+m['52WeekLow']).toFixed(2)}` : '—'],
      ['52W Return', fmt(m['52WeekPriceReturnDaily'], '%')],
      ['Beta', fmt(m.beta)],
      ['Shares Out', m.sharesOutstanding ? `${(m.sharesOutstanding/1e9).toFixed(2)}B` : '—'],
      ['Float', m.float ? `${(m.float/1e9).toFixed(2)}B` : '—'],
    ]],
  ];

  metrics.forEach(([cat, rows]) => {
    h += `<div style="margin-bottom:0;border-bottom:1px solid var(--gb)">
      <div style="padding:5px 14px;font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.2em;background:var(--b1)">${cat}</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:rgba(255,255,255,0.03)">
        ${rows.map(([label, val]) => `<div style="background:var(--bg);padding:8px 14px">
          <div style="font-family:var(--mn);font-size:9px;color:var(--t3);margin-bottom:2px">${label}</div>
          <div style="font-family:var(--mn);font-size:13px;font-weight:800;color:var(--tx)">${val}</div>
        </div>`).join('')}
      </div>
    </div>`;
  });

  // ── WALL STREET CONSENSUS GAUGE ──
  const rec = recs[0];
  if (rec) {
    const buyN = (rec.buy||0) + (rec.strongBuy||0);
    const holdN = rec.hold||0;
    const sellN = (rec.sell||0) + (rec.strongSell||0);
    const total = buyN + holdN + sellN || 1;
    const buyPct = Math.round(buyN / total * 100);
    const holdPct = Math.round(holdN / total * 100);
    const sellPct = 100 - buyPct - holdPct;
    const dominant = buyPct >= 60 ? 'Strong Buy' : buyPct >= 40 ? 'Buy' : holdPct >= 50 ? 'Hold' : sellPct >= 50 ? 'Sell' : 'Mixed';
    const domCol = buyPct >= 40 ? 'var(--gn)' : sellPct >= 40 ? 'var(--rd)' : 'var(--gd)';
    h += `<div style="padding:12px 14px;border-bottom:1px solid var(--gb)">
      <div style="font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.2em;margin-bottom:10px">WALL STREET CONSENSUS · ${total} ANALYSTS</div>
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
        <div style="font-family:var(--mn);font-size:18px;font-weight:900;color:${domCol};min-width:90px">${dominant}</div>
        <div style="flex:1;height:8px;border-radius:4px;overflow:hidden;display:flex;gap:1px">
          ${buyPct>0?`<div style="width:${buyPct}%;background:var(--gn);border-radius:4px 0 0 4px"></div>`:''}
          ${holdPct>0?`<div style="width:${holdPct}%;background:var(--gd)"></div>`:''}
          ${sellPct>0?`<div style="width:${sellPct}%;background:var(--rd);border-radius:0 4px 4px 0"></div>`:''}
        </div>
      </div>
      <div style="display:flex;gap:14px">
        <span style="font-family:var(--mn);font-size:9px;color:var(--gn)">▲ Buy ${buyN}</span>
        <span style="font-family:var(--mn);font-size:9px;color:var(--gd)">● Hold ${holdN}</span>
        <span style="font-family:var(--mn);font-size:9px;color:var(--rd)">▼ Sell ${sellN}</span>
      </div>
    </div>`;
  }

  // ── ANALYST PRICE TARGETS ──
  if (pt.targetMean) {
    const cp = data.currentPrice || pt.targetMean;
    const upside = ((pt.targetMean - cp) / cp * 100).toFixed(1);
    const range = (pt.targetHigh||0) - (pt.targetLow||0);
    const cpPos = range > 0 ? Math.max(0, Math.min(100, (cp - (pt.targetLow||0)) / range * 100)) : 50;
    const meanPos = range > 0 ? Math.max(0, Math.min(100, ((pt.targetMean||0) - (pt.targetLow||0)) / range * 100)) : 50;
    h += `<div style="padding:12px 14px;border-bottom:1px solid var(--gb)">
      <div style="font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.2em;margin-bottom:10px">ANALYST PRICE TARGETS</div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:1px;background:rgba(255,255,255,0.03);border-radius:6px;overflow:hidden;margin-bottom:10px">
        <div style="background:var(--bg);padding:10px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">LOW</div><div style="font-family:var(--mn);font-size:14px;font-weight:800;color:var(--rd)">$${pt.targetLow?.toFixed(0)||'—'}</div></div>
        <div style="background:var(--bg);padding:10px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">MEAN</div><div style="font-family:var(--mn);font-size:14px;font-weight:800;color:var(--gd)">$${pt.targetMean?.toFixed(0)||'—'}</div></div>
        <div style="background:var(--bg);padding:10px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">HIGH</div><div style="font-family:var(--mn);font-size:14px;font-weight:800;color:var(--gn)">$${pt.targetHigh?.toFixed(0)||'—'}</div></div>
        <div style="background:var(--bg);padding:10px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">UPSIDE</div><div style="font-family:var(--mn);font-size:14px;font-weight:800;color:${parseFloat(upside)>0?'var(--gn)':'var(--rd)'}">${upside}%</div></div>
      </div>
      <div style="position:relative;height:20px;background:var(--b2);border-radius:4px;margin:0 4px">
        <div style="position:absolute;left:0;right:0;top:8px;height:4px;background:linear-gradient(90deg,var(--rd),var(--gd),var(--gn));border-radius:2px"></div>
        <div style="position:absolute;top:2px;width:2px;height:16px;background:var(--tx);border-radius:1px;left:${cpPos}%;transform:translateX(-50%)" title="Current"></div>
        <div style="position:absolute;top:1px;width:10px;height:10px;background:var(--gd);border-radius:50%;border:2px solid var(--bg);left:${meanPos}%;transform:translateX(-50%)" title="Mean target"></div>
      </div>
      <div style="display:flex;justify-content:space-between;font-family:var(--mn);font-size:8px;color:var(--t3);margin-top:4px;padding:0 4px">
        <span>$${pt.targetLow?.toFixed(0)||'—'} low</span>
        <span style="color:var(--t2)">▲ = mean target</span>
        <span>$${pt.targetHigh?.toFixed(0)||'—'} high</span>
      </div>
    </div>`;
  }

  // ── UPGRADE / DOWNGRADE TIMELINE ──
  if (upgrades.length > 0) {
    h += `<div style="border-bottom:1px solid var(--gb)">
      <div style="padding:6px 14px;font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.2em;background:var(--b1)">ANALYST RATING CHANGES (6 MONTHS)</div>`;
    upgrades.slice(0, 8).forEach(u => {
      const act = (u.action||'').toLowerCase();
      const isUp = act.includes('upgrade') || act === 'up';
      const isInit = act.includes('init') || act.includes('reiterat') || act.includes('maintain');
      const col = isUp ? 'var(--gn)' : isInit ? 'var(--bl)' : 'var(--rd)';
      const label = isUp ? '↑ UPGRADE' : isInit ? '● REITERATED' : '↓ DOWNGRADE';
      h += `<div style="display:flex;gap:10px;padding:8px 14px;border-bottom:1px solid rgba(255,255,255,0.03);align-items:flex-start">
        <div style="width:3px;min-height:38px;border-radius:2px;background:${col};flex-shrink:0;margin-top:2px"></div>
        <div style="flex:1">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px">
            <span style="font-family:var(--mn);font-size:8px;font-weight:700;color:${col}">${label}</span>
            <span style="font-family:var(--mn);font-size:8px;color:var(--t3)">${(u.gradeDate||'').slice(0,10)}</span>
          </div>
          <div style="font-family:var(--sn);font-size:11px;color:var(--tx);font-weight:600">${u.firm||''}</div>
          <div style="font-family:var(--mn);font-size:9px;color:var(--t2);margin-top:1px">${u.fromGrade||'—'} → <strong style="color:${col}">${u.toGrade||'—'}</strong></div>
        </div>
      </div>`;
    });
    h += `</div>`;
  }

  // ── INSIDER TRANSACTIONS ──
  if (ins.length > 0) {
    h += `<div style="border-bottom:1px solid var(--gb)">
      <div style="padding:6px 14px;font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.2em;background:var(--b1)">INSIDER TRANSACTIONS (6 MONTHS)</div>
      <table style="width:100%;border-collapse:collapse;font-family:var(--mn);font-size:10px">
        <thead><tr style="background:var(--b1)">
          <th style="padding:6px 10px;text-align:left;font-size:8px;color:var(--t3);letter-spacing:0.1em">INSIDER</th>
          <th style="padding:6px 10px;text-align:right;font-size:8px;color:var(--t3)">SHARES</th>
          <th style="padding:6px 10px;text-align:right;font-size:8px;color:var(--t3)">TYPE</th>
          <th style="padding:6px 10px;text-align:right;font-size:8px;color:var(--t3)">DATE</th>
        </tr></thead><tbody>`;
    ins.slice(0, 8).forEach(tx => {
      const isBuy = tx.transactionCode === 'P' || (tx.change > 0 && tx.transactionCode !== 'S');
      const col = isBuy ? 'var(--gn)' : 'var(--rd)';
      const type = tx.transactionCode === 'P' ? 'BUY' : tx.transactionCode === 'S' ? 'SELL' : tx.transactionCode === 'G' ? 'GIFT' : tx.transactionCode;
      h += `<tr style="border-bottom:1px solid rgba(255,255,255,0.025)">
        <td style="padding:7px 10px;color:var(--t2);max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:9px">${(tx.name||'').split(' ').slice(-1)[0]}</td>
        <td style="padding:7px 10px;text-align:right;color:${col};font-weight:700">${tx.change < 0 ? '' : '+'}${(tx.change||0).toLocaleString()}</td>
        <td style="padding:7px 10px;text-align:right"><span style="color:${col};font-weight:700;font-size:9px">${type}</span></td>
        <td style="padding:7px 10px;text-align:right;color:var(--t3);font-size:9px">${(tx.transactionDate||tx.filingDate||'').slice(0,10)}</td>
      </tr>`;
    });
    h += `</tbody></table></div>`;
    const buys = ins.filter(t => t.transactionCode === 'P' || t.change > 0).length;
    const sells = ins.filter(t => t.transactionCode === 'S').length;
    const sentiment = buys > sells ? 'Accumulating' : sells > buys ? 'Distributing' : 'Neutral';
    const scol = buys > sells ? 'var(--gn)' : sells > buys ? 'var(--rd)' : 'var(--t2)';
    h += `<div style="padding:8px 14px;font-family:var(--sn);font-size:11px;color:var(--t2);border-bottom:1px solid var(--gb)">Insider sentiment: <strong style="color:${scol}">${sentiment}</strong> — ${buys} buys vs ${sells} sells in past 6 months</div>`;
  }

  // ── PEER COMPANIES ──
  if (peers.length > 0) {
    h += `<div style="padding:10px 14px;border-bottom:1px solid var(--gb)">
      <div style="font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.2em;margin-bottom:8px">PEER COMPANIES</div>
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        ${peers.map(p => `<button onclick="_peerNav('${p}')" style="font-family:var(--mn);font-size:10px;font-weight:700;padding:4px 10px;border-radius:6px;cursor:pointer;border:1px solid var(--b4);background:var(--b2);color:var(--gd)">${p}</button>`).join('')}
      </div>
    </div>`;
  }

  h += `<div style="padding:8px 14px;font-family:var(--mn);font-size:8px;color:var(--t3);text-align:center">Ratios: Finnhub · Statements: FMP · TTM = Trailing Twelve Months</div>`;
  return h;
}

// ─── Terminal select / clear ───
function termSelect(tk) {
  tk = (typeof resolveInternalTicker === "function" ? resolveInternalTicker(tk) : tk) || tk;
  if (!IS_DESKTOP()) { openA(tk); return; }
  if (termSelTk !== tk) {
    termComRes = null;
    termComLoad = false;
    termComErr = "";
    _finTab = 'metrics';
    _destroyCharts();
  }
  termSelTk = tk;
  // Surface analysis panel so ticker open is never a silent no-op
  if (_expPanel !== "p2") {
    if (_expPanel) toggleExpand(_expPanel);
    toggleExpand("p2");
  }
  renderP2();
  renderP1();
  updateSidebarActive();
}
function termClear() {
  termSelTk = null;
  termComRes = null;
  termComLoad = false;
  termComErr = "";
  _dynTk = null;
  _dynData = null;
  _dynLoading = false;
  renderP2();
  renderP1();
}

// ─── Terminal Investing Lenses ───
async function runTermCommittee(tk) {
  if (!_isPremium()) { _showLoginGate('Investing Lenses'); return; }
  termComLoad = true; termComRes = null; termLensMeta = null; termLensIntel = null; termComErr = "";
  renderP2();
  const a = A.find(x => x.tk === tk) || { nm: tk, th: 'No thesis available.', sc: 50, se: 'Neutral', cat: 'Unknown' };
  const userThesis = lensThesis[tk] || '';
  await _prefetchLensData(tk);
  const context = _buildLensContext(tk);
  try {
    const out = await _callLensEngine(tk, a, context, userThesis);
    if (out.auth) { termComLoad = false; _showLoginGate('Investing Lenses'); renderP2(); return; }
    termComRes = out.lenses;
    termLensIntel = out.intelligence;
    termLensMeta = _lensMetaFromResult(_getLensMembers(out.lenses), context, userThesis, out.meta);
    const synth = _getSynthesis(out.lenses);
    saveReason({ ticker: tk, thesis: synth?.analysis || out.intelligence?.analysis || a.th, verdict: synth?.verdict || 'MONITOR', ts: new Date().toISOString(), sc: a.sc });
  } catch(e) {
    termComErr = e?.message || "Lens Engine is temporarily unavailable. Please try again shortly.";
  }
  if (termSelTk !== tk) { termComLoad = false; return; }
  termComLoad = false;
  renderP2();
}

// ─── Command bar ───
function runCmd() {
  const input = document.getElementById('cmdInput');
  if (!input) return;
  const raw = input.value.trim();
  // Prefer cleaned ticker for symbol-like input; keep full upper for command words
  const cleaned = sanitizeTicker(raw);
  const val = (cleaned || raw).toUpperCase();
  if (!val) return;

  // If autocomplete is open, use the first result instead of raw input
  // This handles "RELIANCE" → autocomplete shows "RELIANCE.NS" → use RELIANCE.NS
  const ac = document.getElementById('cmdAc');
  if (ac && ac.classList.contains('show')) {
    const first = ac.querySelector('.ac-item');
    if (first) {
      first.dispatchEvent(new MouseEvent('mousedown', {bubbles:true}));
      input.value = '';
      return;
    }
  }

  input.value = '';

  // Commands first
  if (val === 'NEWS') {
    termClear();
    _dynTk = null; _dynData = null; _dynLoading = false;
    if (IS_DESKTOP()) renderP2();
    else nav('news');
    return;
  }
  if (val === 'PAPER' || val === 'EDITION' || val === 'NEWSPAPER') {
    nav('paper');
    return;
  }
  if (val === 'BRIEF' || val === 'DISPATCH') {
    if (IS_DESKTOP()) sbNav('brief');
    else nav('brief');
    return;
  }
  if (val === 'MORNING' || val === 'ROUTINE') {
    runMorningRoutine();
    return;
  }
  if (val === 'CHAT' || val === 'ASK' || val === 'EXPERT') {
    if (!_chatOpen) toggleChat();
    return;
  }
  if (val === 'MKT' || val === 'MARKETS') {
    if (IS_DESKTOP()) sbNav('mkt');
    else nav('mkt');
    return;
  }
  if (val === 'WATCH' || val === 'WATCHLIST') {
    if (IS_DESKTOP()) sbNav('watch');
    else nav('watch');
    return;
  }
  if (val === 'PORT' || val === 'PORTFOLIO') {
    if (IS_DESKTOP()) _showOverlay('portOv', '📊 Portfolio', renderPortfolio());
    else nav('port');
    return;
  }
  if (val === 'SIG' || val === 'SIGNALS') {
    if (IS_DESKTOP()) sbNav('sig');
    else nav('sig');
    return;
  }

  // Try dynamic lookup for any ticker
  lookupTicker(val);
}

// ─── Render all terminal panels ───
function renderTerminalPanels() {
  renderP1();
  renderP2();
  renderP3();
  renderP4();
  const liveEl = document.getElementById('cmdLive');
  const liveDot = document.getElementById('liveDot');
  if (liveEl) {
    if (updatePaused) liveEl.textContent = 'Paused';
    else if (liveSymbols.size > 0) liveEl.textContent = liveSymbols.size + ' live';
    else if (priceFetching) liveEl.textContent = 'Syncing…';
    else if (_priceFetchAttempted) liveEl.textContent = 'Tap ⟳ sync';
    else liveEl.textContent = 'Syncing…';
  }
  if (liveDot) {
    const col = updatePaused ? 'var(--gd)' : liveSymbols.size > 0 ? 'var(--gn)' : priceFetching ? 'var(--bl)' : 'var(--rd)';
    liveDot.style.background = col;
    liveDot.style.animation = updatePaused ? 'none' : 'pls 1.5s infinite';
  }
  const hintEl = document.getElementById('cmdHint');
  if (hintEl && _cmdFocused && !termSelTk && !_dynTk && !(document.getElementById('cmdInput')?.value.trim())) {
    hintEl.style.display = 'flex';
  } else if (hintEl) {
    hintEl.style.display = 'none';
  }
  setTimeout(_flashChanged, 50);
}

// ─── Terminal clock ───
function updateTermClock() {
  const el = document.getElementById('cmdClk');
  if (!el) return;
  const n = new Date();
  el.textContent = String(n.getHours()).padStart(2,'0') + ':' + String(n.getMinutes()).padStart(2,'0') + ':' + String(n.getSeconds()).padStart(2,'0');
}

// ═══════════════════════════════════════════════════════════
// CHART ENGINE — Lightweight Charts + Technical Indicators
// ═══════════════════════════════════════════════════════════

// Calculate Simple Moving Average
function calcMA(closes, period) {
  const result = [];
  for (let i = period - 1; i < closes.length; i++) {
    const slice = closes.slice(i - period + 1, i + 1);
    result.push(slice.reduce((a, b) => a + b, 0) / period);
  }
  return result;
}

// Calculate RSI (14-period)
function calcRSI(closes, period = 14) {
  if (closes.length < period + 1) return [];
  const gains = [], losses = [];
  for (let i = 1; i < closes.length; i++) {
    const diff = closes[i] - closes[i - 1];
    gains.push(diff > 0 ? diff : 0);
    losses.push(diff < 0 ? -diff : 0);
  }
  const avgGain = gains.slice(0, period).reduce((a, b) => a + b, 0) / period;
  const avgLoss = losses.slice(0, period).reduce((a, b) => a + b, 0) / period;
  const rsiValues = [];
  let ag = avgGain, al = avgLoss;
  for (let i = period; i < gains.length; i++) {
    ag = (ag * (period - 1) + gains[i]) / period;
    al = (al * (period - 1) + losses[i]) / period;
    const rs = al === 0 ? 100 : ag / al;
    rsiValues.push(+(100 - (100 / (1 + rs))).toFixed(2));
  }
  return rsiValues;
}

// Active chart instances (to destroy on re-render)
let _activeCharts = [];
function _destroyCharts() {
  _activeCharts.forEach(c => { try { c.remove(); } catch(e) {} });
  _activeCharts = [];
}

/** Chart symbol candidates — futures often empty on 1d/5m when session closed; ETF proxies fill the gap */
function _chartSymbolCandidates(tk) {
  const primary = YAHOO_SYMBOLS[tk] || tk;
  const proxies = {
    XAU: ["GC=F", "GLD"],
    WTI: ["CL=F", "USO"],
    BRENT: ["BZ=F", "BNO"],
    SLV: ["SI=F", "SLV"],
    NG: ["NG=F", "UNG"],
    COPPER: ["HG=F", "CPER"],
    BTC: ["BTC-USD", "BTCUSD=X"],
    ETH: ["ETH-USD"],
    DXY: ["DX-Y.NYB", "UUP"],
    VIX: ["^VIX"],
    SPX: ["^GSPC", "SPY"],
    IXIC: ["^IXIC", "QQQ"],
    RUT: ["^RUT", "IWM"],
  };
  const list = proxies[tk] || [primary];
  if (!list.includes(primary)) list.unshift(primary);
  return [...new Set(list)];
}

function _chartAttempts(range) {
  const intervalMap = { "1d": "5m", "5d": "15m", "1mo": "1h", "3mo": "1d", "6mo": "1d", "1y": "1d", "2y": "1wk" };
  const primary = { range: range || "1d", interval: intervalMap[range] || "5m" };
  // Fallbacks when futures/session has no bars (nights, weekends, thin contracts)
  const fallbacks = [
    { range: "5d", interval: "15m" },
    { range: "1mo", interval: "1h" },
    { range: "3mo", interval: "1d" },
    { range: "6mo", interval: "1d" },
    { range: "1y", interval: "1d" },
  ];
  const out = [primary];
  fallbacks.forEach(f => {
    if (!out.some(x => x.range === f.range && x.interval === f.interval)) out.push(f);
  });
  return out;
}

function _candlesFromYahooResult(result) {
  if (!result) return { candles: [], meta: {} };
  const timestamps = result.timestamp || [];
  const q = result.indicators?.quote?.[0] || {};
  const meta = result.meta || {};
  const candles = timestamps.map((t, i) => {
    const close = q.close?.[i];
    if (close == null || !isFinite(close) || close <= 0) return null;
    const open = q.open?.[i] != null && isFinite(q.open[i]) ? q.open[i] : close;
    const high = q.high?.[i] != null && isFinite(q.high[i]) ? q.high[i] : Math.max(open, close);
    const low = q.low?.[i] != null && isFinite(q.low[i]) ? q.low[i] : Math.min(open, close);
    return {
      time: t,
      open,
      high,
      low,
      close,
      volume: q.volume?.[i] || 0,
    };
  }).filter(Boolean);
  return { candles, meta };
}

// Render a full candlestick chart with MA + RSI into a container element
async function renderCandleChart(tk, range, containerId) {
  const container = document.getElementById(containerId);
  if (!container || typeof LightweightCharts === 'undefined') return;

  _chartLoad = { tk, cid: containerId };
  container.innerHTML = `<div style="padding:16px;text-align:center;font-family:var(--mn);font-size:10px;color:var(--t3)">LOADING CHART…</div>`;

  try {
    const symbols = _chartSymbolCandidates(tk);
    const attempts = _chartAttempts(range);
    let candles = [];
    let meta = {};
    let usedSym = symbols[0];
    let usedRange = range;

    outer:
    for (const yhSym of symbols) {
      for (const att of attempts) {
        try {
          const res = await chartFetch(
            `/api/yahoo-chart?symbol=${encodeURIComponent(yhSym)}&range=${att.range}&interval=${att.interval}`,
            { signal: AbortSignal.timeout(12000) }
          );
          if (!res.ok) continue;
          const data = await res.json();
          if (_chartLoad.tk !== tk || _chartLoad.cid !== containerId) return;
          const result = data?.chart?.result?.[0];
          const parsed = _candlesFromYahooResult(result);
          if (parsed.candles.length >= 3) {
            candles = parsed.candles;
            meta = parsed.meta || {};
            usedSym = yhSym;
            usedRange = att.range;
            break outer;
          }
        } catch (e) { /* try next */ }
      }
    }

    if (candles.length < 3) throw new Error('insufficient data');
    // annotate proxy for UI
    const proxyNote = usedSym !== (YAHOO_SYMBOLS[tk] || tk)
      ? ` · via ${usedSym}`
      : (usedRange !== range ? ` · ${usedRange}` : "");

    const closes = candles.map(c => c.close);
    const isUp = closes[closes.length - 1] >= closes[0];
    const upCol = '#00C896', dnCol = '#FF4757';
    const col = isUp ? upCol : dnCol;

    // Main chart
    container.innerHTML = '';
    const chartEl = document.createElement('div');
    const isLab = containerId === 'lab-chart';
    const chartH = isLab ? (document.body.classList.contains('lab-immersive') ? 380 : 240) : 160;
    chartEl.style.cssText = `width:100%;height:${chartH}px;`;
    container.appendChild(chartEl);

    const chart = LightweightCharts.createChart(chartEl, {
      width: chartEl.clientWidth || container.clientWidth,
      height: chartH,
      layout: { background: { type: 'solid', color: 'transparent' }, textColor: '#7A8BAA' },
      grid: { vertLines: { color: 'rgba(255,255,255,0.03)' }, horzLines: { color: 'rgba(255,255,255,0.03)' } },
      crosshair: { mode: 1 },
      timeScale: { borderColor: 'rgba(255,255,255,0.06)', timeVisible: true, rightOffset: 5 },
      rightPriceScale: { borderColor: 'rgba(255,255,255,0.06)', scaleMargins: { top: 0.1, bottom: 0.2 } },
      handleScroll: true,
      handleScale: true,
    });
    _activeCharts.push(chart);

    // Candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: upCol, downColor: dnCol,
      borderVisible: false,
      wickUpColor: upCol, wickDownColor: dnCol,
    });
    candleSeries.setData(candles);

    // MA20
    if (closes.length >= 20) {
      const ma20 = calcMA(closes, 20);
      const ma20Series = chart.addLineSeries({ color: '#F5A623', lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false });
      ma20Series.setData(candles.slice(19).map((c, i) => ({ time: c.time, value: ma20[i] })));
    }
    // MA50
    if (closes.length >= 50) {
      const ma50 = calcMA(closes, 50);
      const ma50Series = chart.addLineSeries({ color: '#4F8EF7', lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false });
      ma50Series.setData(candles.slice(49).map((c, i) => ({ time: c.time, value: ma50[i] })));
    }
    // Volume histogram
    const volSeries = chart.addHistogramSeries({ color: col + '40', priceFormat: { type: 'volume' }, priceScaleId: 'vol' });
    chart.priceScale('vol').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });
    volSeries.setData(candles.filter(c => c.volume).map(c => ({ time: c.time, value: c.volume, color: c.close >= c.open ? upCol + '60' : dnCol + '60' })));

    // Fit content
    chart.timeScale().fitContent();

    // Legend
    const legendEl = document.createElement('div');
    legendEl.style.cssText = 'display:flex;gap:12px;padding:6px 0 4px;font-family:var(--mn);font-size:9px;flex-wrap:wrap';
    legendEl.innerHTML = `<span style="color:var(--gd)">─ MA20</span><span style="color:var(--bl)">─ MA50</span><span style="color:var(--t3)">Vol bars</span><span style="color:var(--t3)">${tk}${proxyNote}</span>`;
    container.insertBefore(legendEl, chartEl);

    // RSI panel
    const rsiValues = calcRSI(closes, 14);
    let rsiChart = null, rsiEl = null;
    if (rsiValues.length > 5) {
      rsiEl = document.createElement('div');
      rsiEl.style.cssText = 'width:100%;height:56px;margin-top:4px;';
      container.appendChild(rsiEl);

      rsiChart = LightweightCharts.createChart(rsiEl, {
        width: rsiEl.clientWidth || container.clientWidth,
        height: 56,
        layout: { background: { type: 'solid', color: 'transparent' }, textColor: '#3D4D6A' },
        grid: { vertLines: { color: 'rgba(255,255,255,0.02)' }, horzLines: { color: 'rgba(255,255,255,0.02)' } },
        timeScale: { borderColor: 'rgba(255,255,255,0.04)', timeVisible: false, visible: false },
        rightPriceScale: { borderColor: 'rgba(255,255,255,0.04)', scaleMargins: { top: 0.1, bottom: 0.1 } },
        crosshair: { mode: 1 },
      });
      _activeCharts.push(rsiChart);

      const rsiSeries = rsiChart.addLineSeries({ color: '#9B6DFF', lineWidth: 1, priceLineVisible: false });
      const startIdx = candles.length - rsiValues.length;
      rsiSeries.setData(candles.slice(startIdx).map((c, i) => ({ time: c.time, value: rsiValues[i] })));

      // Overbought/oversold lines
      const ob = rsiChart.addLineSeries({ color: 'rgba(255,71,87,0.3)', lineWidth: 1, priceLineVisible: false, crosshairMarkerVisible: false, lastValueVisible: false });
      const os = rsiChart.addLineSeries({ color: 'rgba(0,200,150,0.3)', lineWidth: 1, priceLineVisible: false, crosshairMarkerVisible: false, lastValueVisible: false });
      ob.setData([{ time: candles[startIdx].time, value: 70 }, { time: candles[candles.length - 1].time, value: 70 }]);
      os.setData([{ time: candles[startIdx].time, value: 30 }, { time: candles[candles.length - 1].time, value: 30 }]);

      const curRsi = rsiValues[rsiValues.length - 1];
      const rsiLabel = document.createElement('div');
      rsiLabel.style.cssText = 'font-family:var(--mn);font-size:9px;color:var(--t3);padding:2px 0;display:flex;gap:10px';
      rsiLabel.innerHTML = `<span style="color:var(--pu)">RSI(14) ${curRsi.toFixed(1)}</span><span style="color:var(--rd)">─ 70 OB</span><span style="color:var(--gn)">─ 30 OS</span>`;
      container.insertBefore(rsiLabel, rsiEl);

      rsiChart.timeScale().fitContent();
    }

    // Session / range stats bar
    const cur = Number(meta.regularMarketPrice || closes[closes.length - 1]);
    const h24 = Number(meta.regularMarketDayHigh || Math.max(...candles.map(c => c.high)));
    const l24 = Number(meta.regularMarketDayLow || Math.min(...candles.map(c => c.low)));
    const vol = meta.regularMarketVolume || candles.reduce((s, c) => s + (c.volume || 0), 0) || null;
    // Guard h===l (flat session) — never emit NaN%/Infinity% as a "range position"
    const rangePos = (isFinite(cur) && isFinite(h24) && isFinite(l24) && h24 > l24)
      ? (((cur - l24) / (h24 - l24)) * 100).toFixed(0) + "%"
      : "—";
    const fmtPx = v => (isFinite(v) ? "$" + (v >= 1 ? v.toFixed(2) : v.toFixed(4)) : "—");
    const statsEl = document.createElement('div');
    statsEl.style.cssText = 'display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:rgba(255,255,255,0.04);margin-top:8px;border-radius:6px;overflow:hidden';
    statsEl.innerHTML = [
      ['HIGH', fmtPx(h24),'var(--gn)'],
      ['LOW', fmtPx(l24),'var(--rd)'],
      ['VOLUME', vol ? (vol >= 1e9 ? `${(vol/1e9).toFixed(2)}B` : vol >= 1e6 ? `${(vol/1e6).toFixed(1)}M` : Number(vol).toLocaleString()) : '—', 'var(--t2)'],
      ['RANGE', rangePos, 'var(--cy)'],
    ].map(([l,v,c]) => `<div style="background:var(--bg);padding:8px 10px"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:3px">${l}</div><div style="font-family:var(--mn);font-size:11px;font-weight:700;color:${c}">${v}</div></div>`).join('');
    container.appendChild(statsEl);

    // Resize observer
    const ro = new ResizeObserver(() => {
      chart.applyOptions({ width: chartEl.clientWidth });
      if (rsiChart && rsiEl) rsiChart.applyOptions({ width: rsiEl.clientWidth });
    });
    ro.observe(container);

  } catch (e) {
    if (_chartLoad.tk !== tk || _chartLoad.cid !== containerId) return;
    container.innerHTML = `<div style="padding:16px;font-family:var(--mn);font-size:10px;color:var(--t3);text-align:center;line-height:1.5">Chart unavailable for ${tk}<br><span style="font-size:9px;opacity:0.8">Tried futures + ETF proxies · try 1M / 6M range</span></div>`;
  }
}

// ═══════════════════════════════════════════════════════════
// TICK ENGINE — UI heartbeat only. Prices change ONLY when the live fetch
// returns new data. We never synthesize price moves between fetches.
// ═══════════════════════════════════════════════════════════
function _patchP2LiveHeader(){
  // Surgical price update for ticker analysis — never wipe scroll / tabs
  if(!termSelTk)return;
  const a=A.find(x=>x.tk===termSelTk);if(!a)return;
  const d=fp(a.tk);
  const na=d.status==="unavailable";
  const chN=liveChg(a.tk);
  const col=na||chN==null?"var(--t3)":chN>0?"var(--gn)":chN<0?"var(--rd)":"var(--t3)";
  const sign=chN!=null&&chN>=0?"+":"";
  const arrow=chN==null||chN===0?"":(chN>0?"↑":"↓");
  const money=a.cat==="Stock"||a.cat==="Crypto"||a.cat==="Commodity";
  const feedLbl=na?"NO SYNC":(d.status==="live"?"LIVE":d.status==="stale"?"STALE":d.status==="cached"?"CACHED":"DELAYED");
  const priceEl=document.querySelector('#p2body .ap-price');
  const chgEl=document.querySelector('#p2body .ap-chg');
  if(priceEl){
    priceEl.textContent=na?"—":(money?"$":"")+d.p;
    priceEl.style.color=na?"var(--tx)":col;
  }
  if(chgEl){
    chgEl.style.color=col;
    chgEl.textContent=na||chN==null?"awaiting live feed":`${arrow} ${sign}${d.chg} (${sign}${d.c}%) today`;
  }
  const subEl=document.getElementById('p2sub');
  if(subEl)subEl.textContent=`${a.cat.toUpperCase()} · ${a.ex} · ${feedLbl}`;
}

function doTick(){
  tick++;
  if(!updatePaused){
    renderTape();
    if(!MOBILE()){
      // While analysing a ticker, do NOT full-rebuild panel 2 (kills scroll + form state)
      if(termSelTk||_dynTk){
        _patchP2LiveHeader();
        renderP1();
        renderP3();
        renderP4();
      }else{
        renderTerminalPanels();
      }
    } else {
      // MOBILE: never full renderMain() here — it hard-resets scroll, inputs, and looks like a page reload.
      // Android Chrome already fires resize when the URL bar hides; full rebuilds make flicker worse.
      _patchLiveDataIfNeeded();
      _patchCuratedPrices();
    }
  }
  renderStatus(); // age chips only — signature-gated to avoid DOM thrash
}

let _lastPatch = 0;
function _patchLiveDataIfNeeded() {
  if (MOBILE() && Date.now() - _lastPatch < 30000) return; // extra throttle on mobile
  _lastPatch = Date.now();

  // Targeted updates for new UI to avoid flicker from full re-render
  try {
    const main = document.getElementById('main');
    if (!main) return;

    // Update price values if any marked elements exist (future proof)
    const priceEls = main.querySelectorAll('[data-live-price]');
    priceEls.forEach(el => {
      const tk = el.dataset.tk || el.getAttribute('data-live-price');
      if (!tk || !liveSymbols.has(tk)) return;
      const d = fp(tk);
      if (d.status === "unavailable") return;
      if (el.textContent !== String(d.p) && el.textContent !== "$" + d.p) {
        el.textContent = d.p;
        el.style.transition = 'color 120ms';
        const ch = liveChg(tk);
        el.style.color = ch == null ? 'var(--t3)' : ch > 0 ? 'var(--gn)' : ch < 0 ? 'var(--rd)' : 'var(--t3)';
        setTimeout(() => { if (el && el.parentNode) el.style.color = ''; }, 350);
      }
    });

    // For command center cards, update values directly if they have data-tk
    main.querySelectorAll('.data-card').forEach(card => {
      const tkAttr = card.getAttribute('data-tk') || card.onclick?.toString().match(/'([A-Z0-9.=^-]+)'/)?.[1];
      if (!tkAttr || !liveSymbols.has(tkAttr)) return;
      const d = fp(tkAttr);
      if (d.status === "unavailable") return;
      const valEl = card.querySelector('.value');
      if (valEl && valEl.textContent !== String(d.p)) valEl.textContent = d.p;
      const chEl = card.querySelector('.change');
      if (chEl) {
        const ch = liveChg(tkAttr);
        const sign = ch != null && ch >= 0 ? '+' : '';
        chEl.textContent = `${sign}${d.chg} (${sign}${d.c}%)`;
        chEl.style.color = ch == null ? 'var(--t3)' : ch > 0 ? 'var(--gn)' : ch < 0 ? 'var(--rd)' : 'var(--t3)';
      }
    });
  } catch(e) {}
}

// ═══════════════════════════════════════════════════════════
// RENDER: TAPE / STATUS / CLOCK
// ═══════════════════════════════════════════════════════════
const TICKER_CATS={
  SPX:'idx',DJIA:'idx',IXIC:'idx',FTSE:'idx',DAX:'idx',N225:'idx',NSEI:'idx',HSI:'idx',VIX:'idx',
  AAPL:'stk',NVDA:'stk',XOM:'stk',MSFT:'stk',AVGO:'stk',TSLA:'stk',AMZN:'stk',GOOGL:'stk',META:'stk',JPM:'stk',GS:'stk',AMD:'stk',
  BTC:'cry',ETH:'cry',SOL:'cry',XRP:'cry',
  XAU:'cmd',WTI:'cmd',SLV:'cmd',NG:'cmd',
  EURUSD:'fx',GBPUSD:'fx',USDJPY:'fx',DXY:'fx',
  // New stocks
  NFLX:'stk',DIS:'stk',V:'stk',MA:'stk',PYPL:'stk',CRM:'stk',ORCL:'stk',ADBE:'stk',
  INTC:'stk',QCOM:'stk',MU:'stk',CSCO:'stk',NOW:'stk',PANW:'stk',CRWD:'stk',
  PLTR:'stk',COIN:'stk',UBER:'stk',SHOP:'stk',SNOW:'stk',RIVN:'stk',
  F:'stk',GM:'stk',BA:'stk',CAT:'stk',DE:'stk',NKE:'stk',SBUX:'stk',MCD:'stk',
  JNJ:'stk',UNH:'stk',PFE:'stk',LLY:'stk',ABBV:'stk',MRK:'stk',
  WMT:'stk',COST:'stk',HD:'stk',BAC:'stk',WFC:'stk',C:'stk',BLK:'stk',ISRG:'stk',
  TSM:'stk',ASML:'stk',NVO:'stk',SAP:'stk',BABA:'stk',BP:'stk',SHEL:'stk',
  // New crypto
  DOGE:'cry',ADA:'cry',AVAX:'cry',LINK:'cry',DOT:'cry',LTC:'cry',UNI:'cry',
  MATIC:'cry',NEAR:'cry',ALGO:'cry',HBAR:'cry',TON:'cry',
  // New stocks
  ARM:'stk',SMCI:'stk',MRVL:'stk',KO:'stk',PEP:'stk',PG:'stk',
  ABNB:'stk',DASH:'stk',BRKB:'stk',ACN:'stk',SONY:'stk',VALE:'stk',RIO:'stk',INFY:'stk',
  // New commodities
  COFFEE:'cmd',PLAT:'cmd',COCOA:'cmd',OJ:'cmd',LUMBER:'cmd',PALLADIUM:'cmd',
  // New indices
  CAC:'idx',ASX200:'idx',KOSPI:'idx',
  // More US stocks
  TMO:'stk',ABT:'stk',PM:'stk',NEE:'stk',RTX:'stk',HON:'stk',
  T:'stk',VZ:'stk',MS:'stk',SCHW:'stk',TXN:'stk',AMAT:'stk',
  LRCX:'stk',REGN:'stk',AMGN:'stk',CVX:'stk',COP:'stk',
  INTU:'stk',ADSK:'stk',NET:'stk',DDOG:'stk',ZS:'stk',
  UPS:'stk',LOW:'stk',DUK:'stk',
  // More international
  TM:'stk',NVS:'stk',UL:'stk',DEO:'stk',
  // More FX
  USDMXN:'fx',USDBRL:'fx',USDINR:'fx',
  // More crypto
  BCH:'cry',XLM:'cry',FIL:'cry',APT:'cry',SUI:'cry',
  // New FX
  AUDUSD:'fx',USDCAD:'fx',USDCHF:'fx',NZDUSD:'fx',EURGBP:'fx',
  // New commodities
  COPPER:'cmd',WHEAT:'cmd',CORN:'cmd',BRENT:'cmd',URA:'stk',
  SPY:'idx',QQQ:'idx',IWM:'idx',RUT:'idx',EEM:'idx',SOXX:'stk',TLT:'idx',ARKK:'stk',TNX:'fx',
  XLK:'stk',XLC:'stk',XLY:'stk',XLF:'stk',XLV:'stk',XLE:'stk',XLI:'stk',XLP:'stk',XLB:'stk',XLU:'stk',XLRE:'stk',
  RKLB:'stk',HOOD:'stk',MSTR:'stk',GME:'stk',SPOT:'stk',LMT:'stk',BMY:'stk',GILD:'stk',
  ENPH:'stk',FSLR:'stk',EOG:'stk',SLB:'stk',SO:'stk',PLD:'stk',AMT:'stk',EQIX:'stk',SPG:'stk',O:'stk',VRTX:'stk',
  SHIB:'cry',PEPE:'cry',ATOM:'cry',INJ:'cry',EURJPY:'fx',GBPJPY:'fx',
};
const CAT_COLORS={idx:'var(--t2)',stk:'var(--bl)',cry:'var(--pu)',cmd:'var(--gd)',fx:'var(--cy)'};
function catBd(cat){return cat==="Stock"?"var(--bl)":cat==="Crypto"?"var(--pu)":cat==="FX"?"var(--cy)":"var(--gd)";}
function catSec(cat){return cat==="Stock"?"s-stk":cat==="Crypto"?"s-cry":cat==="Commodity"?"s-cmd":cat==="FX"?"s-fx":"s-idx";}

const TAPE_ORDER=[
  'SPX','DJIA','IXIC','SPY','QQQ','IWM','RUT','VIX','DXY','TNX',
  'AAPL','NVDA','MSFT','AMZN','GOOGL','META','TSLA','AVGO','AMD','LLY',
  'XLK','XLF','XLE','XLV','XLI','XLY','XLC','XLP','XLB','XLU','XLRE',
  'BTC','ETH','SOL','XRP','DOGE','SHIB',
  'XAU','WTI','BRENT','COPPER','SLV','NG',
  'EURUSD','GBPUSD','USDJPY','EURJPY',
  'JPM','GS','XOM','CVX','COIN','MSTR','RKLB','HOOD','SPOT',
  'FTSE','DAX','N225','NSEI','HSI','EEM',
];

let _tapePrev = {};
function renderTape(){
  const live = [...liveSymbols];
  if (!live.length && priceFetching) {
    const tape = document.getElementById("tape");
    if (tape) tape.innerHTML = `<span class="ti" style="color:var(--t3);letter-spacing:0.12em">SYNCING LIVE PRICES…</span>`;
    return;
  }
  const ordered=[
    ...TAPE_ORDER.filter(k=>liveSymbols.has(k)),
    ...live.filter(k=>!TAPE_ORDER.includes(k)).sort(),
  ];
  if (!ordered.length) {
    const tape = document.getElementById("tape");
    if (tape) tape.innerHTML = `<span class="ti" style="color:var(--t3)">Awaiting price feed — tap ⟳ to sync</span>`;
    return;
  }
  const flashMap = {};
  ordered.forEach(k => {
    const d = fp(k);
    const prev = _tapePrev[k];
    if (prev !== undefined && d.p !== prev && d.status !== "unavailable") {
      const ch = liveChg(k);
      flashMap[k] = ch == null || ch === 0 ? "" : (ch > 0 ? "flash-up" : "flash-dn");
    }
    _tapePrev[k] = d.p;
  });
  const items=ordered.map(k=>{
    const d=fp(k);
    const ch=liveChg(k);
    const cat=TICKER_CATS[k]||'idx';
    const catCol=CAT_COLORS[cat]||'var(--t2)';
    const badge=d.status==="live"?'<span class="htec-live-dot" title="Near real-time"></span>'
      :d.status==="delayed"?'<span class="tape-badge tape-del" title="Delayed free feed">D</span>'
      :d.status==="stale"?'<span class="tape-badge tape-stale" title="Stale tick">S</span>'
      :d.status==="cached"?'<span class="tape-badge tape-cache" title="Session cache">C</span>'
      :'<span style="opacity:0.35;font-size:7px">○</span>';
    const title=_escAttr(`${k} · ${d.label||"NO SYNC"}${d.asOf?` · as of ${_fmtAsOf(d.asOf)}`:""}`);
    const chCol=ch==null?"var(--t3)":ch>0?"var(--gn)":ch<0?"var(--rd)":"var(--t3)";
    const chSign=ch!=null&&ch>=0?"+":"";
    return `<span class="ti" data-tk="${k}" title="${title}"><span style="color:${catCol};font-weight:700">${k}${badge}</span><span style="color:var(--tx);font-weight:700">${d.p}</span><span style="color:${chCol};font-weight:600">${ch==null?"—":chSign+d.c+"%"}</span></span>`;
  }).join("");
  const tape = document.getElementById("tape");
  if (tape) {
    tape.innerHTML = items + items;
    if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      tape.querySelectorAll(".ti[data-tk]").forEach(el => {
        const cls = flashMap[el.dataset.tk];
        if (!cls) return;
        el.classList.add(cls);
        setTimeout(() => el.classList.remove(cls), 700);
      });
    }
  }
  _syncTapePulse();
}

function _fmtAge(ms){const s=Math.round((Date.now()-ms)/1000);return s<60?s+'s':Math.round(s/60)+'m';}

function initTechShell() {
  document.body.classList.add("htec-body");
  const app = document.getElementById("app");
  if (app) app.classList.add("htec-app");
  if (!sessionStorage.getItem("td_htec_boot_v1") && IS_DESKTOP()) {
    sessionStorage.setItem("td_htec_boot_v1", "1");
    const boot = document.createElement("div");
    boot.className = "htec-boot";
    boot.innerHTML = `<div class="htec-boot-inner">
      <div class="htec-boot-logo"><img class="brand-mark-img brand-mark-img-boot" src="/logo-mark.svg?v=1784230000" width="52" height="52" alt=""></div>
      <div class="htec-boot-txt">The Dispatch · Markets</div>
      <div class="htec-boot-bar"><div class="htec-boot-fill"></div></div>
    </div>`;
    document.body.appendChild(boot);
    setTimeout(() => boot.remove(), 2800);
  }
}

let _statusSig=""; // skip status DOM rewrite when nothing meaningful changed (Android flicker)
function renderStatus(){
  const pAge=priceLastFetch?_fmtAge(priceLastFetch.getTime()):"—";
  const nAge=newsLastFetch?_fmtAge(newsLastFetch.getTime()):"—";
  const cgThrottle=_cgBackoffUntil>Date.now();
  const spinning=newsFetching||priceFetching;
  const re=_computeRegimeEngine();
  const pulseCls=spinning?"htec-pulse htec-pulse-fetch":updatePaused?"htec-pulse htec-pulse-pause":"htec-pulse htec-pulse-live";
  const degraded=priceErrorCount>=2||(_priceFetchAttempted&&liveSymbols.size===0&&!priceFetching)||cgThrottle;
  const feedKey=updatePaused?"P":spinning?"S":degraded?"D":(liveSymbols.size>0?"L"+liveSymbols.size:"0");
  // Signature: avoid full statusBar.innerHTML every 15s when only pulse CSS would change
  const sig=[IS_DESKTOP()?"d":"m",feedKey,re.label,re.score,_isPremium()?"1":"0",_stripeMode,pAge,nAge,cgThrottle?"1":"0",_chromeFocus?"1":"0"].join("|");
  if(sig===_statusSig&&document.getElementById("statusBar")?.dataset.sig===sig)return;
  _statusSig=sig;
  const liveChip=updatePaused
    ?`<span class="htec-chip htec-chip-warn">PAUSED</span>`
    :spinning
      ?`<span class="htec-chip htec-chip-ai">SYNCING</span>`
      :degraded
        ?`<span class="htec-chip htec-chip-warn" title="Feed degraded — free Yahoo/CG can lag or fail">FEED DEGRADED</span>`
      :liveSymbols.size>0
        ?`<span class="htec-chip htec-chip-live" title="Synced symbols (mostly delayed free feeds)">FEED · ${liveSymbols.size}</span>`
        :`<span class="htec-chip htec-chip-muted">STANDBY</span>`;
  const aiChip=_isPremium()
    ?`<span class="htec-chip htec-chip-ai">★ PREMIUM</span>`
    :`<span class="htec-chip htec-chip-muted">FREE</span>`;
  const stripeChip=_stripeMode==="live"
    ?`<span class="htec-chip htec-chip-live htec-chip-mob-hide">STRIPE LIVE</span>`
    :_stripeMode==="test"
      ?`<span class="htec-chip htec-chip-warn htec-chip-mob-hide">STRIPE TEST</span>`:"";
  const regimeChip=`<span class="htec-chip htec-chip-regime" title="Educational model">${re.label} ${re.score}</span>`;
  const regimeChipMob=`<span class="htec-chip htec-chip-regime" title="${re.label}">${_mobShortRegime(re.label)} ${re.score}</span>`;
  const feedChip=`<span class="htec-chip htec-chip-muted htec-chip-mob-hide">P ${pAge} · N ${nAge}${cgThrottle?" · CG WAIT":""}${priceLastFetch?` · as of ${_fmtAsOf(priceLastFetch.getTime())}`:""}</span>`;
  const feedChipMob=`<span class="htec-chip htec-chip-muted htec-chip-feed" title="Prices ${pAge} · News ${nAge}">${pAge}</span>`;
  const el=document.getElementById("statusBar");
  if(!el)return;
  el.dataset.sig=sig;
  const focusBtn=`<button type="button" class="htec-act htec-act-focus" onclick="toggleChromeFocus()" title="Focus mode" aria-label="Toggle focus mode">${_chromeFocus?"◧":"⛶"}</button>`;
  const ring=_regimeRingSvg(re.score, re.col);
  if(!IS_DESKTOP()){
    el.innerHTML=`<div class="htec-status htec-status-mob" title="Double-tap or pull down to sync">
      <div class="htec-status-l">
        ${ring}<span class="${pulseCls}"></span>
        ${liveChip}${regimeChipMob}${aiChip}${stripeChip}${feedChipMob}
      </div>
      <div class="htec-status-r">
        ${focusBtn}
        <button type="button" class="htec-act htec-act-gn" onclick="_statusSync()" aria-label="Sync news and prices">⟳</button>
      </div>
    </div>`;
    return;
  }
  const regimeDesk = window.innerWidth < 1280 ? regimeChipMob : regimeChip;
  el.innerHTML=`<div class="htec-status htec-status-desk" title="Double-click to sync feeds">
    <div class="htec-status-l">
      ${ring}<span class="${pulseCls}"></span>
      ${liveChip}${regimeDesk}${aiChip}${stripeChip}${feedChip}
    </div>
    <div class="htec-status-r htec-status-desk-r">
      ${focusBtn}
    </div>
  </div>`;
  _paintFeedBanner();
  requestAnimationFrame(_syncDeskChrome);
}

function updateClock(){
  const n=new Date();
  const clk=document.getElementById("clk");
  const clkD=document.getElementById("clkD");
  if(clk) clk.textContent=`${String(n.getHours()).padStart(2,"0")}:${String(n.getMinutes()).padStart(2,"0")}:${String(n.getSeconds()).padStart(2,"0")}`;
  if(clkD) clkD.textContent=`${String(n.getDate()).padStart(2,"0")}-${String(n.getMonth()+1).padStart(2,"0")}-${n.getFullYear()}`;
}

// ═══════════════════════════════════════════════════════════
// RENDER: NAV STRUCTURE (single source of truth)
// ═══════════════════════════════════════════════════════════
// Icon paths shared by the sidebar, bottom nav and the mobile More sheet.
const NAV_ICONS = {
  // Home — a roof over a door, drawn at the same 1.8-2 stroke as the rest.
  home: '<path d="M4 10.5L12 4l8 6.5" stroke="currentColor" stroke-width="1.9" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M6 10v9.5h12V10" stroke="currentColor" stroke-width="1.9" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M10 19.5V14h4v5.5" stroke="currentColor" stroke-width="1.9" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
  brief: '<path d="M12 3l2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3z" stroke="currentColor" stroke-width="2" fill="none"/>',
  // Gold Desk — bullion bar, deliberately distinct from Brief's sparkle
  playbook: '<rect x="4.5" y="3.5" width="15" height="17" rx="2" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M8 8h8M8 12h8M8 16h5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
  gold: '<path d="M9.2 5.5h5.6l1.7 4.2H7.5L9.2 5.5z" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linejoin="round"/><path d="M4.6 13.5h6.2l1.7 4.2H2.9l1.7-4.2z" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linejoin="round"/><path d="M13.2 13.5h6.2l1.7 4.2h-9.6l1.7-4.2z" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linejoin="round"/>',
  dash: '<path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0h4" stroke="currentColor" stroke-width="2" fill="none"/>',
  lab: '<path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" stroke="currentColor" stroke-width="2" fill="none"/>',
  sig: '<path d="M13 10V3L4 14h7v7l9-11h-7z" stroke="currentColor" stroke-width="2" fill="none"/>',
  mkt: '<path d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" stroke="currentColor" stroke-width="2" fill="none"/>',
  scr: '<path d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" stroke="currentColor" stroke-width="2" fill="none"/>',
  sectors: '<path d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" stroke="currentColor" stroke-width="2" fill="none"/><path d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" stroke="currentColor" stroke-width="2" fill="none"/>',
  heat: '<path d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm6 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 11a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm6 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" stroke="currentColor" stroke-width="2" fill="none"/>',
  news: '<path d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" stroke="currentColor" stroke-width="2" fill="none"/>',
  paper: '<path d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" stroke="currentColor" stroke-width="2" fill="none"/><path d="M3 10h18" stroke="currentColor" stroke-width="2" fill="none"/>',
  research: '<path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" stroke="currentColor" stroke-width="2" fill="none"/>',
  intel: '<path d="M9.663 17h4.674M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" stroke="currentColor" stroke-width="2" fill="none"/>',
  geo: '<circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2" fill="none"/><path d="M2 12h20M12 3a14 14 0 010 18M12 3a14 14 0 000 18" stroke="currentColor" stroke-width="2" fill="none"/>',
  watch: '<path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" stroke="currentColor" stroke-width="2" fill="none"/>',
  port: '<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" stroke="currentColor" stroke-width="2" fill="none"/>',
  learn: '<path d="M12 14l9-5-9-5-9 5 9 5z" stroke="currentColor" stroke-width="2" fill="none"/><path d="M12 14l6.16-3.42A12 12 0 0118 16.5a12 12 0 01-12 0 12 12 0 01-.16-5.92L12 14z" stroke="currentColor" stroke-width="2" fill="none"/>',
  crypto: '<circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2" fill="none"/><path d="M9.5 8h4a2 2 0 010 4h-4m0 0h4.2a2 2 0 010 4H9.5m0-8v8M11 6v2m0 8v2m2.5-12v2m0 8v2" stroke="currentColor" stroke-width="2" fill="none"/>',
  settings: '<path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2" fill="none"/>',
  more: '<circle cx="5" cy="12" r="1.6" fill="currentColor"/><circle cx="12" cy="12" r="1.6" fill="currentColor"/><circle cx="19" cy="12" r="1.6" fill="currentColor"/>',
};

// Brief and Gold are both top-level products and stay SEPARATE surfaces:
// Brief = daily house view, Gold = weekly gold playbook.
// Home is the front door: orientation, then a doorway onward. It leads because
// it is where you arrive, not because it outranks the products below it.
const NAV_TOP = [["home","Home"],["brief","Brief"],["playbook","Playbook"],["gold","Gold"]];

// Grouped information architecture. Mirrors the desktop sidebar order.
const NAV_GROUPS = [
  { g: "Desk", items: [["dash","Dash"],["lab","Lab"],["sig","Signals"]] },
  { g: "Markets", items: [
      ["mkt","Markets", [["scr","Screener"],["sectors","Sectors"],["heat","Heatmap"],["crypto","Crypto"]]],
  ] },
  { g: "Intel", items: [
      ["news","News", [["paper","Papers"],["research","Research"],["intel","Documents"],["geo","Geo"]]],
  ] },
  { g: "Book", items: [["watch","Watch"],["port","Port"],["learn","Learn"]] },
];

// Every destination, flattened — used for active-state resolution.
const NAV_ALL = NAV_TOP.map(i => i[0]).concat(
  NAV_GROUPS.flatMap(gr => gr.items.flatMap(it => [it[0], ...((it[2]||[]).map(s2 => s2[0]))]))
);
// id -> label, for anything that needs to name a destination it was handed
// (Home's "pick up where you left off"). Derived, so it cannot drift.
const NAV_LABELS = {};
NAV_TOP.forEach(([id, l]) => { NAV_LABELS[id] = l; });
NAV_GROUPS.forEach(gr => gr.items.forEach(it => {
  NAV_LABELS[it[0]] = it[1];
  (it[2] || []).forEach(s2 => { NAV_LABELS[s2[0]] = s2[1]; });
}));

// Which parent a sub-destination belongs to, so the parent stays open and marked.
const NAV_PARENT = {};
NAV_GROUPS.forEach(gr => gr.items.forEach(it => (it[2]||[]).forEach(s2 => { NAV_PARENT[s2[0]] = it[0]; })));

// Pages that keep a permanent slot in the mobile bottom bar.
// Saturday is the product's moment, so Playbook holds a permanent slot.
const NAV_PRIMARY = [["home","Home"],["brief","Brief"],["playbook","Playbook"],["gold","Gold"],["dash","Dash"]];

function _navIco(id){ return `<svg viewBox="0 0 24 24" width="18" height="18">${NAV_ICONS[id]||""}</svg>`; }

function renderSidebarNav(){
  const el = document.getElementById("sidebar");
  if (!el) return;
  const item = (id, label, primary) =>
    `<button type="button" class="sb-item${primary?" sb-primary":""}" id="sbi-${id}" onclick="sbNav('${id}')" title="${label}" aria-label="${label}">${_navIco(id)}<span>${label}</span></button>`;

  // A sub-destination is only drawn while its section is the one in use —
  // either the parent itself is open, or one of its children is. Ten rows at
  // rest, fourteen at most. Progressive disclosure keeps the rail short
  // instead of listing every surface at all times.
  const sub = (id, label) =>
    `<button type="button" class="sb-item sb-sub" id="sbi-${id}" onclick="sbNav('${id}')" title="${label}" aria-label="${label}"><span>${label}</span></button>`;
  const openFor = (parentId) => pg === parentId || NAV_PARENT[pg] === parentId;

  el.innerHTML = NAV_TOP.map(([id, label]) => item(id, label, true)).join("") +
    NAV_GROUPS.map(gr =>
      `<div class="sb-grp" role="presentation"><span>${gr.g}</span></div>` +
      gr.items.map(([id, label, subs]) =>
        item(id, label, false) +
        (subs && openFor(id)
          ? `<div class="sb-subs">${subs.map(([sid, slabel]) => sub(sid, slabel)).join("")}</div>`
          : "")
      ).join("")
    ).join("") +
    `<div class="sb-spacer"></div>` +
    `<button type="button" class="sb-item sb-util" id="sbi-settings" onclick="openSettings()" title="Settings" aria-label="Settings">${_navIco("settings")}<span>Settings</span></button>`;
  updateSidebarActive();
}
renderSidebarNav();

// Every destination that is NOT in the bottom bar lives behind More.
function _navInMore(p){
  const primary = NAV_PRIMARY.map(i => i[0]);
  // Nested destinations (Screener, Sectors, Papers, …) live in it[2]. Counting
  // only the parents left the More tab unlit whenever a child was the active
  // page, so the phone gave no indication of where you were.
  const all = [
    ...NAV_TOP.map(i => i[0]),
    ...NAV_GROUPS.flatMap(gr => gr.items.flatMap(it => [it[0], ...((it[2] || []).map(s => s[0]))])),
  ];
  return all.includes(p) && !primary.includes(p);
}

function renderNav(){
  const el=document.getElementById("bnav");
  if(!el)return;
  let h = NAV_PRIMARY.map(([id,lb]) =>
    `<button class="${pg===id?"on":""}" onclick="nav('${id}')" aria-label="${lb}" aria-current="${pg===id?'page':'false'}">${_navIco(id)}<span>${lb}</span></button>`
  ).join("");
  const moreOn = _navInMore(pg);
  h += `<button class="${moreOn?"on":""}" data-more-nav-trigger onclick="openMoreNav()" aria-label="More" aria-haspopup="dialog" aria-controls="moreNav" aria-expanded="${_moreNavOpen?'true':'false'}">${_navIco("more")}<span>More</span></button>`;
  el.innerHTML = h;
}

// ── Mobile "More" sheet — exposes every destination the bottom bar omits ──
let _moreNavOpen = false;
let _moreNavCloseTimer = null;

function _moreNavFocusable(sheet){
  return Array.from(sheet.querySelectorAll('button:not([disabled]),a[href],[tabindex]:not([tabindex="-1"])'));
}

function _onMoreNavKeydown(e){
  if (!_moreNavOpen) return;
  const sheet = document.getElementById("moreNav");
  if (!sheet) return;
  if (e.key === "Escape") {
    e.preventDefault();
    closeMoreNav();
    return;
  }
  if (e.key !== "Tab") return;
  const focusable = _moreNavFocusable(sheet);
  if (!focusable.length) {
    e.preventDefault();
    sheet.focus();
    return;
  }
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (e.shiftKey && (document.activeElement === first || !sheet.contains(document.activeElement))) {
    e.preventDefault();
    last.focus();
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault();
    first.focus();
  }
}

function openMoreNav(){
  if (_moreNavCloseTimer) {
    clearTimeout(_moreNavCloseTimer);
    _moreNavCloseTimer = null;
  }
  _moreNavOpen = true;
  const trigger = document.querySelector("[data-more-nav-trigger]");
  trigger?.setAttribute("aria-expanded", "true");
  let sheet = document.getElementById("moreNav");
  if (!sheet) {
    sheet = document.createElement("div");
    sheet.id = "moreNav";
    sheet.className = "more-nav";
    sheet.setAttribute("role", "dialog");
    sheet.setAttribute("aria-modal", "true");
    sheet.setAttribute("aria-label", "All sections");
    sheet.setAttribute("tabindex", "-1");
    document.body.appendChild(sheet);
  }
  sheet.setAttribute("aria-hidden", "false");
  sheet.innerHTML = `
    <div class="more-nav-scrim" onclick="closeMoreNav()"></div>
    <div class="more-nav-panel">
      <div class="more-nav-hdr">
        <span class="more-nav-ttl">All sections</span>
        <button class="more-nav-x" onclick="closeMoreNav()" aria-label="Close">×</button>
      </div>
      <button class="more-nav-item ${pg==='home'?'on':''}" onclick="_moreNavGo('home')">
        ${_navIco('home')}<span>Home</span><em>Where the desk stands</em>
      </button>
      <button class="more-nav-item ${pg==='brief'?'on':''}" onclick="_moreNavGo('brief')">
        ${_navIco('brief')}<span>Brief</span><em>Daily house view</em>
      </button>
      <button class="more-nav-item ${pg==='gold'?'on':''}" onclick="_moreNavGo('gold')">
        ${_navIco('gold')}<span>Gold</span><em>Weekly gold playbook</em>
      </button>
      ${NAV_GROUPS.map(gr => `
        <div class="more-nav-grp">${gr.g}</div>
        ${gr.items.map(([id,lb,subs]) => `
          <button class="more-nav-item ${pg===id?'on':''}" onclick="_moreNavGo('${id}')">
            ${_navIco(id)}<span>${lb}</span>
          </button>
          ${(subs||[]).map(([sid,slb]) => `
            <button class="more-nav-item more-nav-sub ${pg===sid?'on':''}" onclick="_moreNavGo('${sid}')">
              ${_navIco(sid)}<span>${slb}</span>
            </button>`).join("")}`).join("")}
      `).join("")}
      <div class="more-nav-grp">Account</div>
      <button class="more-nav-item" onclick="closeMoreNav();openSettings()">
        ${_navIco("settings")}<span>Settings</span>
      </button>
    </div>`;
  // Force a reflow so the CSS transition still runs, then reveal synchronously.
  // Do NOT use requestAnimationFrame here — it is throttled in background tabs,
  // which would leave the sheet built but stuck at display:none.
  void sheet.offsetWidth;
  sheet.classList.add("on");
  document.addEventListener("keydown", _onMoreNavKeydown);
  (sheet.querySelector(".more-nav-item.on") || sheet.querySelector(".more-nav-x"))?.focus();
}

function closeMoreNav(){
  if (!_moreNavOpen) return;
  _moreNavOpen = false;
  const sheet = document.getElementById("moreNav");
  document.removeEventListener("keydown", _onMoreNavKeydown);
  if (sheet) {
    sheet.setAttribute("aria-hidden", "true");
    sheet.classList.remove("on");
    _moreNavCloseTimer = setTimeout(() => {
      sheet.remove();
      _moreNavCloseTimer = null;
    }, 180);
  }
  renderNav();
  document.querySelector("[data-more-nav-trigger]")?.focus();
}

function _moreNavGo(p){ closeMoreNav(); nav(p); }

// ═══════════════════════════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════════════════════════
function _setATab(t){aTab=t;if(IS_DESKTOP())renderP2();else renderMain();}
function nav(p){
  if(pg==='mkt'&&p!=='mkt'){_mktView='curated';_mktSearch='';_mktFilter='all';_mktSort='default';}
  if(!IS_DESKTOP())_siteIntel.expanded=false;
  // Keep research report selection when opening research; clear otherwise
  if(p!=='research') selReport=null;
  pg=p;selTk=null;aTab="ov";comRes=null;comErr="";_learnSub=null;_dynTk=null;_dynData=null;_dynLoading=false;
  _pushRecentNav(p);

  // Desktop: route to overlays/panels (main is hidden). Mobile: render multi-page shell.
  const deskHandled = _desktopRoute(p);
  if (!deskHandled) {
    renderMain();
    if (pg === "lab") _initLabPage();
  }
  renderNav();
  if (IS_DESKTOP()) updateSidebarActive();
  document.querySelector(".main")?.scrollTo(0,0);
  if(p==='lab'&&_sectorNeedsFetch())fetchSectorData();
  if(p==='dash'){if(_sectorNeedsFetch())fetchSectorData();loadDispatchBrief(false);if(!_earnRadar&&!_earnRadarLoad)loadEarningsRadar();}
  if(p==='gold'||p==='playbook'){loadGoldDesk(false);}
  if(p==='brief'){loadDispatchBrief(false);}
  _paintWlGlance();

  document.querySelectorAll('#mainNav a').forEach(a => {
    a.classList.toggle('active', a.dataset.nav === p || a.dataset.section === p || (p==='dash' && (a.dataset.nav==='briefing'||a.dataset.section==='briefing')));
  });

  if(p==='crypto'&&!_cryptoMktData&&!_cryptoMktLoading)fetchCryptoMarket();
  if(p==='news'&&!newsLastFetch&&!newsFetching)fetchLiveNews();
  if(p==='paper'){
    if(!newsLastFetch&&!newsFetching)fetchLiveNews();
    if(!_brief&&!_briefLoad)loadDispatchBrief(false);
  }
  if(p==='geo'&&!deskHandled)_paintChokepointStrip();
  _onPageIntel(_INTEL_PAGE_MAP[p] || "pulse");
  _updateSmartDock();
}

// Wire optional top bar (if present) — must not shadow global nav()
function wireTopNav() {
  const bar = document.getElementById('mainNav');
  if (!bar || bar.dataset.wired) return;
  bar.dataset.wired = 'true';
  bar.addEventListener('click', (e) => {
    const link = e.target.closest('a');
    if (!link) return;
    const target = link.dataset.nav || link.dataset.section;
    if (!target) return;
    e.preventDefault();
    if (target === 'briefing') nav('dash');
    else if (target === 'markets') nav('mkt');
    else if (target === 'research') nav('research');
    else if (target === 'news') nav('news');
    else if (target === 'intel') nav('intel');
    else if (target === 'lab') nav('lab');
    else if (target === 'port' || target === 'portfolio') nav('port');
    else nav(target);
  });
}

// Enhance global search to feel like a real command palette
function enhanceCommandPalette() {
  const inp = document.getElementById('globalSearch');
  if (!inp || inp.dataset.enhanced) return;
  inp.dataset.enhanced = 'true';
  inp.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && inp.value.trim()) {
      const raw = inp.value.trim();
      const q = (typeof resolveInternalTicker === "function" ? resolveInternalTicker(raw) : "") || sanitizeTicker(raw) || raw.toUpperCase();
      inp.value = '';
      const match = A.find(a => a.tk === q) || IDX.find(i => i.tk === q);
      if (match) {
        openA(q);
      } else if (q) {
        // Dyn / international symbols — never dump analysts to Newsroom by mistake
        lookupTicker(q);
      } else {
        openSearch();
      }
    }
  });
}

// Legacy duplicate removed - using the robust version above
// (kept for compatibility if old code paths call it)

// enhanceCardInteractions defined once near renderMain (do not duplicate)

// Deprecated — must not overwrite live statusBar (destroyed feed chips / Android flicker)
function renderBriefingHeader() {
  if (typeof renderStatus === "function") {
    _statusSig = "";
    renderStatus();
  }
}
function openA(tk){
  // Normalize Yahoo symbols (BTC-USD, CL=F) → desk tickers (BTC, WTI)
  tk = (typeof resolveInternalTicker === "function" ? resolveInternalTicker(tk) : tk) || tk;
  // Desktop analysis lives in the terminal panels — never dump into hidden #main
  if (IS_DESKTOP()) {
    if (selTk !== tk) { comRes = null; comLoad = false; lensMeta = null; lensIntel = null; }
    selTk = tk;
    pg = "anlz";
    aTab = "ov";
    termSelect(tk);
    _prefetchTicker(tk);
    _onPageIntel("ticker", { tk });
    _updateSmartDock();
    updateSidebarActive();
    return;
  }
  if(selTk!==tk){comRes=null;comLoad=false;comErr="";lensMeta=null;lensIntel=null;}
  selTk=tk;pg="anlz";aTab="ov";_learnSub=null;_dynTk=null;_dynData=null;_dynLoading=false;
  renderMain();renderNav();document.querySelector(".main")?.scrollTo(0,0);
  _prefetchTicker(tk);_onPageIntel("ticker", { tk });_updateSmartDock();
}
// Prefetch financial + earnings data in background after ticker is opened, so tab clicks hit cache
function _prefetchTicker(tk){
  if(!_isPremium())return;
  const a=A.find(x=>x.tk===tk);
  if(!a||a.cat!=='Stock')return;
  setTimeout(()=>{
    if(!_finCache[tk])fetch('/api/financials?symbol='+encodeURIComponent(tk)).then(r=>r.ok?r.json():null).then(d=>{if(d)_finCache[tk]=d;}).catch(()=>{});
    if(!_earnCache[tk])fetch('/api/earnings?symbol='+encodeURIComponent(tk)).then(r=>r.ok?r.json():null).then(d=>{if(d)_earnCache[tk]=d;}).catch(()=>{});
  },1500);
}
function openReport(id){
  selReport=id;pg="research";
  if (IS_DESKTOP()) {
    document.getElementById("researchOv")?.remove();
    _showOverlay("researchOv", "🔬 Research Desk", renderResearch());
    updateSidebarActive();
    return;
  }
  renderMain();document.querySelector(".main")?.scrollTo(0,0);
}
function closeReport(){
  selReport=null;
  if (IS_DESKTOP()) {
    if (_refreshOverlay("researchOv", renderResearch)) return;
    _showOverlay("researchOv", "🔬 Research Desk", renderResearch());
    return;
  }
  renderMain();document.querySelector(".main")?.scrollTo(0,0);
}
function openSearch(){
  const sov=document.getElementById("sov");
  sov.classList.remove("hide");
  sov.classList.add("sov-palette","fx-sov-enter");
  _searchIdx=-1;
  _paintSearchChips();
  const sinp=document.getElementById("sinp");
  if(sinp){
    if(!sinp.value)doSearch("");
    sinp.placeholder=IS_DESKTOP()?"Ticker, command, or research…":"Search tickers & commands…";
  }
  _fxOverlayEnter(sov.querySelector(".sbox"));
  setTimeout(()=>sinp?.focus(),80);
}
function closeSearch(){
  const sov=document.getElementById("sov");
  sov.classList.add("hide");
  sov.classList.remove("sov-palette","fx-sov-enter");
  const sinp=document.getElementById("sinp");
  if(sinp)sinp.value="";
  const sres=document.getElementById("sres");
  if(sres)sres.innerHTML="";
  _searchIdx=-1;
}
function openAbout(){const ov=document.getElementById("aboutOv");ov.classList.remove("hide");ov.classList.add("fx-sov-enter");_fxOverlayEnter(ov.querySelector(".about-card"));}
function closeAbout(){document.getElementById("aboutOv").classList.add("hide");}
let _searchDebounce=null,_searchLastQ="";
function _paintSearchResults(raw,r){
  const el=document.getElementById("sres");
  if(!el)return;
  _searchIdx=-1;
  r.sort((a,b)=>(b.priority||0)-(a.priority||0));
  el.innerHTML=r.length?r.slice(0,12).map(x=>`<div class="sres${x.tp==='Command'?' sres-cmd':''}" onclick="${x.act}"><span class="sres-nm">${_escHtml(x.nm)}</span>${x.sub?`<span class="sres-d">${_escHtml(x.sub)}</span>`:""}${x.tk?_searchPriceBadge(x.tk):""}${x.tk?_smartFitBadge(x.tk):""}${bd(x.tp,x.tp==="Research"?"var(--gd)":x.tp==="Command"?"var(--pu)":x.tp==="Lookup"?"var(--cy)":"var(--bl)")}</div>`).join(""):`<div class="sres-empty">No results for “${_escHtml(raw)}” — try AAPL, brief, lab, or sync</div>`;
}
function _buildLocalSearchHits(raw){
  const q=raw.toLowerCase();
  let r=[];
  SMART_COMMANDS.forEach(c=>{if(c.k.includes(q)||c.l.toLowerCase().includes(q)||c.d.toLowerCase().includes(q))r.push({nm:c.l,sub:c.d,tp:"Command",act:c.act,priority:2});});
  A.forEach(a=>{if(a.tk.toLowerCase().includes(q)||a.nm.toLowerCase().includes(q))r.push({nm:`${a.tk} — ${a.nm}`,sub:a.cat,tp:a.cat,act:`openA('${a.tk}');closeSearch()`,tk:a.tk,priority:liveSymbols.has(a.tk)?1:0});});
  REPORTS.forEach(rep=>{if(rep.headline.toLowerCase().includes(q)||rep.deck.toLowerCase().includes(q)||rep.tags.some(t=>t.toLowerCase().includes(q)))r.push({nm:rep.headline.replace(/<[^>]*>/g,""),sub:"Research report",tp:"Research",act:`nav('research');openReport('${rep.id}');closeSearch()`,priority:0});});
  const resolved=typeof resolveInternalTicker==="function"?resolveInternalTicker(raw):sanitizeTicker(raw);
  if(resolved){
    const a=A.find(x=>x.tk===resolved);
    if(a&&!r.some(x=>x.tk===a.tk)){
      r.unshift({nm:`${a.tk} — ${a.nm}`,sub:a.cat+" · desk",tp:a.cat,act:`openA('${a.tk}');closeSearch()`,tk:a.tk,priority:3});
    }else if(!a&&!r.some(x=>x.tk===resolved)){
      r.unshift({nm:resolved,sub:"Open on desk / Yahoo",tp:"Lookup",act:`lookupTicker('${resolved}');closeSearch()`,tk:resolved,priority:3});
    }
  }
  try{
    const book=new Set([...(getActiveWl().tickers||[]),...portfolio.map(p=>p.tk)]);
    book.forEach(tk=>{
      if(!tk||r.some(x=>x.tk===tk))return;
      if(String(tk).toUpperCase().includes(q.toUpperCase())||String(tk).toLowerCase().includes(q)){
        const a=A.find(x=>x.tk===tk);
        r.push({nm:a?`${a.tk} — ${a.nm}`:tk,sub:a?a.cat+" · book":"Book",tp:a?.cat||"Book",act:`openA('${tk}');closeSearch()`,tk,priority:2});
      }
    });
  }catch(e){}
  return r;
}
function doSearch(q){
  const el=document.getElementById("sres");
  if(!el)return;
  _searchIdx=-1;
  if(!q){el.innerHTML=_renderSmartSearchDefault();clearTimeout(_searchDebounce);_searchLastQ="";return;}
  const raw=q.trim();
  _searchLastQ=raw;
  const local=_buildLocalSearchHits(raw);
  _paintSearchResults(raw,local.slice());
  // Debounced Yahoo search — parity with desktop cmd autocomplete (RELIANCE → RELIANCE.NS)
  clearTimeout(_searchDebounce);
  _searchDebounce=setTimeout(async()=>{
    if(_searchLastQ!==raw)return;
    try{
      const res=await fetch(`/api/search?q=${encodeURIComponent(raw)}`,{signal:AbortSignal.timeout(4000)});
      if(!res.ok||_searchLastQ!==raw)return;
      const data=await res.json();
      if(_searchLastQ!==raw)return;
      const hits=_buildLocalSearchHits(raw);
      const seen=new Set(hits.map(x=>x.tk).filter(Boolean));
      const ranked=[...((data.result||[]))];
      // Promote best match for bare query to front of Yahoo hits
      const best=_bestYahooSearchMatch(ranked,raw);
      if(best){
        const bi=ranked.findIndex(x=>x.symbol===best.symbol);
        if(bi>0){ranked.splice(bi,1);ranked.unshift(best);}
      }
      ranked.slice(0,8).forEach(g=>{
        if(!g?.symbol||seen.has(g.symbol))return;
        const desk=resolveInternalTicker(g.symbol)||g.symbol;
        if(seen.has(desk))return;
        seen.add(g.symbol);seen.add(desk);
        const known=A.find(a=>a.tk===desk);
        // Prefer exchange-suffixed best match over weak bare lookups
        const isBest=best&&g.symbol===best.symbol;
        if(known){
          hits.push({nm:`${known.tk} — ${known.nm}`,sub:known.cat+" · Yahoo",tp:known.cat,act:`openA('${known.tk}');closeSearch()`,tk:known.tk,priority:isBest?3:2});
        }else{
          hits.push({nm:`${g.symbol} — ${g.name||g.symbol}`,sub:(g.exchange||"Yahoo")+" · global",tp:"Lookup",act:`lookupTicker('${g.symbol}');closeSearch()`,tk:g.symbol,priority:isBest?3:2});
        }
      });
      _paintSearchResults(raw,hits);
    }catch(e){}
  },300);
}
function togWatch(tk){
  tk=(typeof resolveInternalTicker==="function"?resolveInternalTicker(tk):tk)||tk;
  const wl=getActiveWl();
  if(wl.tickers.includes(tk)){removeFromWatchlist(tk);}
  else{addToWatchlist(tk);}
  // Keep legacy watch in sync for compatibility
  watch=getActiveWl().tickers;
  _paintWlGlance();
  renderMain();
  if(IS_DESKTOP())renderP4();
}
function isWatched(tk){
  const raw=String(tk||"").trim();
  if(!raw)return false;
  const sym=(typeof resolveInternalTicker==="function"?resolveInternalTicker(raw):"")||sanitizeTicker(raw)||raw;
  const tks=getActiveWl().tickers||[];
  if(tks.includes(sym)||tks.includes(raw))return true;
  // Match aliases both ways (list may hold BTC while UI checks BTC-USD)
  return tks.some(t=>{
    const r=(typeof resolveInternalTicker==="function"?resolveInternalTicker(t):"")||t;
    return r===sym||t===sym||r===raw;
  });
}
function saveReason(e){
  const day=String(e?.ts||new Date().toISOString()).slice(0,10);
  reason=reason.filter(r=>!(r.ticker===e.ticker&&String(r.ts||"").slice(0,10)===day&&r.verdict===e.verdict));
  reason.unshift(e);
  if(reason.length>50)reason.length=50;
  localStorage.setItem("td_r",JSON.stringify(reason));
}

// ═══════════════════════════════════════════════════════════
// INVESTING LENSES
// ═══════════════════════════════════════════════════════════
async function runCommittee(tk){
  if(!_isPremium()){_showLoginGate('Investing Lenses');return;}
  comLoad=true;comRes=null;comErr="";lensMeta=null;lensIntel=null;renderMain();
  const a=A.find(x=>x.tk===tk)||{nm:tk,th:'No thesis available.',sc:50,se:'Neutral',cat:'Unknown'};
  const userThesis=lensThesis[tk]||'';
  await _prefetchLensData(tk);
  const context=_buildLensContext(tk);
  try{
    const out=await _callLensEngine(tk,a,context,userThesis);
    if(out.auth){comLoad=false;_showLoginGate('Investing Lenses');renderMain();return;}
    comRes=out.lenses;lensIntel=out.intelligence;
    lensMeta=_lensMetaFromResult(_getLensMembers(out.lenses),context,userThesis,out.meta);
    const synth=_getSynthesis(out.lenses);
    const re=_computeRegimeEngine();
    saveLensRun({ticker:tk,thesis:synth?.analysis||out.intelligence?.analysis||a.th,verdict:synth?.verdict||"MONITOR",ts:new Date().toISOString(),sc:a.sc,regime:re.label,lenses:_getLensMembers(out.lenses)?.length||5});
  }catch(e){
    comErr = e?.message || "Lens Engine is temporarily unavailable. Please try again shortly.";
  }
  if(selTk!==tk||pg!=='anlz'){comLoad=false;return;}
  comLoad=false;renderMain();
}

// ═══════════════════════════════════════════════════════════
// PAGE: GOLD DESK + WEEKLY PLAYBOOK (Product V1 core)
// ═══════════════════════════════════════════════════════════
let _goldDesk = null;
let _goldDeskLoad = false;
let _goldDeskErr = null;
let _goldDeskFetchedAt = 0;
let _goldTab = "playbook"; // playbook | desk
// The ladder reads this on first paint, before any scenario button is clicked.
// Without a declaration here it is only created by setGoldScenario(), so
// rendering Playbook cold threw ReferenceError and the page stayed blank.
let _goldScenario = "bullish"; // bullish | bearish | range

async function loadGoldDesk(force) {
  if (_goldDeskLoad) return;
  if (!force && _goldDesk && Date.now() - _goldDeskFetchedAt < 120000) {
    if (pg === "gold") _refreshGoldView();
    return;
  }
  _goldDeskLoad = true;
  _goldDeskErr = null;
  if (pg === "gold") _refreshGoldView();
  try {
    const opts = {};
    try {
      if (typeof AbortSignal !== "undefined" && typeof AbortSignal.timeout === "function") {
        opts.signal = AbortSignal.timeout(25000);
      }
    } catch (_) {}
    const res = await fetch("/api/gold-desk", opts);
    const text = await res.text();
    let data = null;
    try {
      data = JSON.parse(text);
    } catch (_) {
      throw new Error(
        res.ok
          ? "Gold API returned HTML instead of JSON — try hard-refresh"
          : `Gold API HTTP ${res.status}`
      );
    }
    if (!res.ok || data.error) throw new Error(data.error || data.detail || "gold-desk failed");
    _goldDesk = data;
    _goldDeskFetchedAt = Date.now();
    try {
      localStorage.setItem("td_gold_playbook", JSON.stringify({
        weekId: data.playbook?.weekId,
        weekLabel: data.playbook?.weekLabel,
        savedAt: Date.now(),
        playbook: data.playbook,
      }));
    } catch (_) {}
  } catch (e) {
    _goldDeskErr = (e && e.message) || "Failed to load gold desk";
  }
  _goldDeskLoad = false;
  if (pg === "gold") _refreshGoldView();
}

function _refreshGoldView() {
  // Both gold surfaces share one payload, so either overlay may be the live one.
  const surfaces = { goldOv: renderGoldDesk, playbookOv: renderPlaybook };
  if (IS_DESKTOP()) {
    for (const id of Object.keys(surfaces)) {
      const ov = document.getElementById(id);
      if (!ov) continue;
      ov.classList.add("term-overlay-gold");
      const body = ov.querySelector(".term-overlay-body");
      if (body) {
        body.innerHTML = surfaces[id]();
        return;
      }
    }
    // Overlay missing on desktop — recreate via route
    if (pg === "gold" || pg === "playbook") {
      _desktopRoute(pg);
      return;
    }
  }
  if (pg === "gold" || pg === "playbook") renderMain();
}

function setGoldScenario(s) {
  _goldScenario = ["bullish", "bearish", "range"].includes(s) ? s : "bullish";
  _refreshGoldView();
}

// Kept as a redirect: the tabs became destinations, but older entry points
// (command palette, saved links, onboarding) still call this.
function setGoldTab(t) {
  nav(t === "desk" ? "gold" : "playbook");
}

function _gdPx(n) {
  if (n == null || !isFinite(n)) return "—";
  return Number(n).toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function _gdChg(n) {
  if (n == null || !isFinite(n)) return "";
  const s = n >= 0 ? "+" : "";
  return `${s}${n.toFixed(2)}%`;
}

function _gdSpark(arr) {
  if (!arr || arr.length < 2) return "";
  const w = 160, h = 36, pad = 2;
  const min = Math.min(...arr), max = Math.max(...arr);
  const span = max - min || 1;
  const pts = arr.map((v, i) => {
    const x = pad + (i / (arr.length - 1)) * (w - pad * 2);
    const y = pad + (1 - (v - min) / span) * (h - pad * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  const up = arr[arr.length - 1] >= arr[0];
  return `<svg class="gd-spark" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" aria-hidden="true"><polyline fill="none" stroke="${up ? "var(--gn)" : "var(--rd)"}" stroke-width="1.5" points="${pts}"/></svg>`;
}

function _gdVpBars(bins) {
  if (!bins || !bins.length) return `<div class="gd-muted">Volume profile unavailable on this feed.</div>`;
  return `<div class="gd-vp">${bins.map(b => {
    const pct = Math.max(4, (b.rel || 0) * 100);
    return `<div class="gd-vp-row" title="${_gdPx(b.low)}–${_gdPx(b.high)}"><div class="gd-vp-bar" style="width:${pct}%"></div><span class="gd-vp-lbl">${_gdPx(b.low)}</span></div>`;
  }).join("")}</div>`;
}

// ═══════════════════════════════════════════════════════════
// THE LADDER — the Gold Desk hero.
//
// Every number the desk computes is a PRICE, and prices have a natural
// spatial order. Printed as sentences they read as trivia; printed on one
// shared axis they answer the only question that matters: where is spot, and
// what breaks the thesis.
//
// Everything is placed at true proportional distance. Nothing is schematic.
// ═══════════════════════════════════════════════════════════
function _ladderScale(d) {
  const px = d?.gold?.price;
  if (!Number.isFinite(px)) return null;
  const pts = [px];
  const push = (v) => { if (Number.isFinite(v)) pts.push(v); };

  (d.levels?.support || []).forEach((s) => push(s.level));
  (d.levels?.resistance || []).forEach((r) => push(r.level));
  push(d.sessions?.sessionHigh); push(d.sessions?.sessionLow);
  push(d.sessions?.priorDayHigh); push(d.sessions?.priorDayLow);
  const named = d.sessions?.named;
  if (named) ["asia", "london", "newYork"].forEach((k) => { push(named[k]?.high); push(named[k]?.low); });
  const vp = d.volumeProfile;
  if (vp?.bins?.length) { push(vp.bins[0].low); push(vp.bins[vp.bins.length - 1].high); }
  push(vp?.poc); push(vp?.vah); push(vp?.val);
  Object.values(d.playbook?.scenarios || {}).forEach((s) =>
    (s?.targets || []).forEach(push));

  let lo = Math.min(...pts), hi = Math.max(...pts);
  if (!(hi > lo)) { lo = px * 0.99; hi = px * 1.01; }
  const pad = (hi - lo) * 0.06;
  return { lo: lo - pad, hi: hi + pad };
}

function _renderLadder(d) {
  const sc = _ladderScale(d);
  if (!sc) return "";
  const px = d.gold.price;

  const W = 760, H = 470, TOP = 26, BOT = 438;
  const AX = 176;              // the axis
  const RIGHT = 560;           // where level rules stop
  const y = (p) => TOP + ((sc.hi - p) / (sc.hi - sc.lo)) * (BOT - TOP);
  const fmt = (p) => (+p).toFixed(2);

  let g = "";

  // Sessions, furthest back: Asia / London / New York as bands at their range.
  const named = d.sessions?.named;
  const SESS = [["asia", "ASIA"], ["london", "LONDON"], ["newYork", "NEW YORK"]];
  if (named) {
    SESS.forEach(([k, label], i) => {
      const s = named[k];
      if (!s || !Number.isFinite(s.high) || !Number.isFinite(s.low)) return;
      const yh = y(s.high), yl = y(s.low);
      const x = AX + 8 + i * 22;
      g += `<rect class="ladder-session" x="${x}" y="${yh.toFixed(1)}" width="16" height="${Math.max(1, yl - yh).toFixed(1)}" rx="2"><title>${label} ${fmt(s.low)}–${fmt(s.high)}</title></rect>`;
      g += `<text class="ladder-lbl-k" x="${x + 8}" y="${(BOT + 14).toFixed(1)}" text-anchor="middle">${label.slice(0, 3)}</text>`;
    });
  }

  // Volume profile — the shape of where trade actually happened.
  const vp = d.volumeProfile;
  if (vp?.bins?.length) {
    vp.bins.forEach((b) => {
      if (!Number.isFinite(b.low) || !Number.isFinite(b.high)) return;
      const yh = y(b.high), yl = y(b.low);
      const w = Math.max(1, (b.rel || 0) * 150);
      const isPoc = Number.isFinite(vp.poc) && vp.poc >= b.low && vp.poc <= b.high;
      g += `<rect class="${isPoc ? "ladder-vp-poc" : "ladder-vp"}" x="${(AX - 8 - w).toFixed(1)}" y="${yh.toFixed(1)}" width="${w.toFixed(1)}" height="${Math.max(1, yl - yh - 1).toFixed(1)}"><title>${fmt(b.low)}–${fmt(b.high)}</title></rect>`;
    });
    if (Number.isFinite(vp.poc)) {
      // POC and spot converge exactly when the reading matters most, so nudge
      // the label clear rather than letting the two overprint.
      const yp = y(vp.poc), ysp = y(px);
      const off = Math.abs(yp - ysp) < 15 ? (yp <= ysp ? -13 : 15) : -4;
      g += `<text class="ladder-lbl-k" x="${AX - 12}" y="${(yp + off).toFixed(1)}" text-anchor="end">POC ${fmt(vp.poc)}</text>`;
    }
  }

  g += `<line class="ladder-axis" x1="${AX}" y1="${TOP}" x2="${AX}" y2="${BOT}"/>`;

  // Levels. Labels are nudged apart so a dense cluster stays readable —
  // the RULE stays at the true price, only the text moves.
  const marks = [];
  (d.levels?.resistance || []).forEach((r, i) =>
    marks.push({ p: r.level, kind: "r", key: "R" + (i + 1), note: r.strength || "" }));
  (d.levels?.support || []).forEach((s, i) =>
    marks.push({ p: s.level, kind: "s", key: "S" + (i + 1), note: s.strength || "" }));

  marks.sort((a, b) => b.p - a.p);
  let lastY = -99;
  marks.forEach((m) => {
    if (!Number.isFinite(m.p)) return;
    const yy = y(m.p);
    const ly = Math.max(yy, lastY + 13);
    lastY = ly;
    g += `<line class="ladder-tick ladder-tick-${m.kind}" x1="${AX}" y1="${yy.toFixed(1)}" x2="${RIGHT}" y2="${yy.toFixed(1)}"/>`;
    g += `<text class="ladder-lbl" x="${RIGHT + 10}" y="${(ly + 3.5).toFixed(1)}"><tspan class="ladder-lbl-k">${m.key}</tspan>  ${fmt(m.p)}${m.note ? `  ${m.note}` : ""}</text>`;
  });

  // Targets for the scenario currently on screen. Real numbers only —
  // invalidation is prose on the server, so it is not fabricated here.
  const scen = d.playbook?.scenarios || {};
  const active = scen[_goldScenario] || null;
  if (active?.targets?.length) {
    active.targets.forEach((t, i) => {
      if (!Number.isFinite(t)) return;
      const yy = y(t);
      const cls = _goldScenario === "bearish" ? "ladder-inval" : "ladder-target";
      g += `<path class="${cls}" d="M${AX - 4} ${yy.toFixed(1)} l-7 -4.5 v9 z" fill="currentColor" stroke="none"><title>${_goldScenario} target ${i + 1}: ${fmt(t)}</title></path>`;
    });
  }

  // Spot, struck across everything. The one moment of motion in the product.
  const ys = y(px);
  g += `<g class="ladder-spot">
    <line class="ladder-spot-line" x1="${AX - 18}" y1="${ys.toFixed(1)}" x2="${RIGHT + 4}" y2="${ys.toFixed(1)}"/>
    <text class="ladder-spot-lbl" x="${RIGHT + 10}" y="${(ys + 4).toFixed(1)}">${fmt(px)}</text>
  </g>`;

  const proxy = vp?.isProxy
    ? `<div class="gd-sm">Volume profile is a range-distributed proxy, not exchange volume-at-price.</div>`
    : "";

  return `<figure class="ladder-wrap">
    <svg class="ladder" viewBox="0 0 ${W} ${H}" role="img"
         aria-label="Price ladder: spot ${fmt(px)} against support, resistance, session ranges and volume profile">
      ${g}
    </svg>
    <figcaption class="ladder-key">
      <span><i class="k-spot"></i>Spot</span>
      <span><i class="k-r"></i>Resistance</span>
      <span><i class="k-s"></i>Support</span>
      <span><i class="k-vp"></i>Volume at price</span>
      <span><i class="k-sess"></i>Sessions</span>
    </figcaption>
    ${proxy}
  </figure>`;
}

// PRODUCT_V1 lists the automated dashboard and the weekly playbook as two
// separate pillars, and the whole visual system rests on published matter and
// live matter being different materials. Behind tabs on one page they were
// neither. They are now two destinations sharing one payload.
function renderPlaybook() { return _renderGoldSurface("playbook"); }
function renderGoldDesk() { return _renderGoldSurface("desk"); }

function _renderGoldSurface(mode) {
  const isPlay = mode === "playbook";
  const livePxN = typeof livePx === "function" ? livePx("XAU") : null;
  const hdrActions = `<div class="pg-hdr-actions">
    <button type="button" class="btn btn-ghost btn-sm" onclick="loadGoldDesk(true)">${_goldDeskLoad ? "Loading…" : "⟳ Refresh"}</button>
  </div>`;
  let h = _renderPgHdr(
    isPlay ? "Weekly Playbook" : "Gold Dashboard",
    isPlay
      ? "Conditional scenarios for the week · published Saturday"
      : "Live gold structure · levels, sessions, volatility and macro",
    hdrActions
  );

  if (_goldDeskLoad && !_goldDesk) {
    h += `<div class="gc gd-card"><div class="gd-muted">Building gold structure and weekly playbook from delayed market data…</div></div>`;
    return h;
  }
  if (_goldDeskErr && !_goldDesk) {
    h += `<div class="gc gd-card">
      <div class="empty-title">Gold desk unavailable</div>
      <div class="empty-sub">${_escHtml(_goldDeskErr)}</div>
      <button class="btn btn-primary" onclick="loadGoldDesk(true)">Retry</button>
    </div>`;
    return h;
  }
  if (!_goldDesk) {
    h += `<div class="gc gd-card">
      <div class="empty-title">Load this week's gold playbook</div>
      <div class="empty-sub">Evidence-based scenarios · support/resistance · macro context · conditional language only</div>
      <button class="btn btn-primary" onclick="loadGoldDesk(true)">Generate playbook</button>
    </div>`;
    return h;
  }

  const d = _goldDesk;
  const g = d.gold || {};
  const px = livePxN != null ? livePxN : g.price;
  const chg = g.changePct;
  const chgCls = chg == null ? "px-flat" : chg >= 0 ? "px-up" : "px-dn";
  const goldMeta = typeof _quoteMeta === "function" ? _quoteMeta("XAU") : null;
  const goldKicker = goldMeta?.src === "twelve-data"
    ? (goldMeta.status === "closed" ? "XAU · spot XAU/USD · MARKET CLOSED" : "XAU · spot XAU/USD · LIVE·TD")
    : String(goldMeta?.src || "").startsWith("gold-api")
      ? "XAU · spot proxy · not exchange live"
      : "XAU · COMEX proxy GC=F · delayed";

  h += `<div class="gd-hero gc">
    <div class="gd-hero-top">
      <div>
        <div class="gd-kicker">${goldKicker}</div>
        <div class="gd-px">$${_gdPx(px)} <span class="gd-chg ${chgCls}">${_gdChg(chg)}</span></div>
        <div class="gd-sub">${_escHtml(d.structure?.regime || "—")} · vol ${d.volatility?.condition || "—"} (ATR $${_gdPx(d.volatility?.atr14)})</div>
      </div>
      <div class="gd-hero-right">
        ${_gdSpark(g.spark)}
        <div class="gd-macro-mini">
          <span>DXY <b>${d.macro?.dxy?.px != null ? d.macro.dxy.px : "—"}</b></span>
          <span>10Y <b>${d.macro?.tnx?.px != null ? d.macro.tnx.px + "%" : "—"}</b></span>
          <span>VIX <b>${d.macro?.vix?.px != null ? d.macro.vix.px : "—"}</b></span>
        </div>
      </div>
    </div>
    <div class="gd-asof">As of ${d.asOf ? new Date(d.asOf).toLocaleString() : "—"} · ${_escHtml(d.dataSource || "")}</div>
  </div>`;

  if (isPlay) {
    const pb = d.playbook || {};
    const sc = pb.scenarios || {};

    // The Ladder leads. Read the map before reading the argument.
    const ladder = _renderLadder(d);
    if (ladder) {
      h += `<section class="gd-ladder-sec">
        <div class="gd-sec-h">Where price sits</div>
        <div class="gd-scen-pick" role="group" aria-label="Scenario to mark on the ladder">
          ${["bullish", "bearish", "range"].map(k => sc[k]
            ? `<button type="button" class="gd-scen-btn${_goldScenario === k ? " on" : ""}" onclick="setGoldScenario('${k}')">${k[0].toUpperCase() + k.slice(1)}</button>`
            : "").join("")}
        </div>
        ${ladder}
      </section>`;
    }

    h += `<div class="gd-card gc">
      <div class="gd-sec-h">Weekly Playbook · ${_escHtml(pb.weekLabel || d.week?.label || "")}</div>
      <div class="gd-badge-row">
        ${bd("CONDITIONAL", "var(--gd)")}
        ${bd((pb.regime?.bias || "range").toUpperCase(), pb.regime?.bias === "bullish" ? "var(--gn)" : pb.regime?.bias === "bearish" ? "var(--rd)" : "var(--bl)")}
        ${bd(pb.weekId || "", "var(--t3)")}
      </div>
      <p class="gd-body">${_escHtml(pb.regime?.summary || d.structure?.summary || "")}</p>
      <p class="gd-disclaimer">${_escHtml(pb.disclaimer || "")}</p>
    </div>`;

    if (pb.macroContext && pb.macroContext.length) {
      h += `<div class="gd-card gc"><div class="gd-sec-h">Macro context</div><ul class="gd-list">${pb.macroContext.map(x => `<li>${_escHtml(x)}</li>`).join("")}</ul></div>`;
    }

    ["bullish", "bearish", "range"].forEach(key => {
      const s = sc[key];
      if (!s) return;
      const col = key === "bullish" ? "var(--gn)" : key === "bearish" ? "var(--rd)" : "var(--bl)";
      h += `<div class="gd-card gc gd-scenario" style="border-left:3px solid ${col}">
        <div class="gd-sec-h" style="color:${col}">${_escHtml(s.title)}</div>
        <div class="gd-if"><span class="gd-if-k">IF / THEN</span>${_escHtml(s.thesis)}</div>
        <div class="gd-row2">
          <div><div class="gd-lbl">Entry conditions</div><div class="gd-sm">${_escHtml(s.entry)}</div></div>
          <div><div class="gd-lbl">Invalidation</div><div class="gd-sm">${_escHtml(s.invalidation)}</div></div>
        </div>
        <div class="gd-lbl" style="margin-top:10px">Targets</div>
        <div class="gd-levels">${(s.targets || []).map(t => `<span class="gd-chip">$${_gdPx(t)}</span>`).join("")}</div>
      </div>`;
    });

    const kl = pb.keyLevels || {};
    h += `<div class="gd-card gc">
      <div class="gd-sec-h">Gamma & liquidity zones</div>
      <p class="gd-disclaimer">${_escHtml(d.gamma?.disclaimer || "Proxy levels — not dealer GEX.")}</p>
      <div class="gd-levels">${(kl.gammaLiquidity || d.gamma?.levels || []).slice(0, 8).map(L =>
        `<span class="gd-chip" title="${_escHtml(L.label || "")}">$${_gdPx(L.level)} · ${_escHtml(L.label || L.kind || "")}</span>`
      ).join("")}</div>
    </div>`;

    if (pb.eventsThatChangeThesis && pb.eventsThatChangeThesis.length) {
      h += `<div class="gd-card gc"><div class="gd-sec-h">Events that could change the thesis</div>`;
      pb.eventsThatChangeThesis.forEach(e => {
        h += `<div class="gd-event">
          <div class="gd-event-d">${_escHtml(e.date)} · ${bd(e.impact || "medium", e.impact === "high" ? "var(--rd)" : "var(--gd)")}</div>
          <div class="gd-event-t">${_escHtml(e.event)}</div>
          <div class="gd-sm">${_escHtml(e.ifThen)}</div>
        </div>`;
      });
      h += `</div>`;
    }

    if (pb.checklist && pb.checklist.length) {
      h += `<div class="gd-card gc"><div class="gd-sec-h">Week checklist</div><ul class="gd-list">${pb.checklist.map(x => `<li>${_escHtml(x)}</li>`).join("")}</ul></div>`;
    }
  } else {
    // Dashboard tab
    h += `<div class="gd-grid">
      <div class="gd-card gc">
        <div class="gd-sec-h">Market structure</div>
        <div class="gd-body">${_escHtml(d.structure?.summary || "")}</div>
        <div class="gd-badge-row" style="margin-top:10px">${bd(d.structure?.bias || "range", "var(--gd)")}${bd(d.volatility?.condition || "vol", "var(--bl)")}</div>
      </div>
      <div class="gd-card gc">
        <div class="gd-sec-h">Session highs & lows</div>
        <div class="gd-kv"><span>Session high</span><b>$${_gdPx(d.sessions?.sessionHigh)}</b></div>
        <div class="gd-kv"><span>Session low</span><b>$${_gdPx(d.sessions?.sessionLow)}</b></div>
        <div class="gd-kv"><span>Prior day high</span><b>$${_gdPx(d.sessions?.priorDayHigh)}</b></div>
        <div class="gd-kv"><span>Prior day low</span><b>$${_gdPx(d.sessions?.priorDayLow)}</b></div>
        <div class="gd-muted" style="margin-top:8px">Source: ${_escHtml(d.sessions?.source || "—")}</div>
      </div>
    </div>`;

    h += `<div class="gd-grid">
      <div class="gd-card gc">
        <div class="gd-sec-h">Support</div>
        ${(d.levels?.support || []).map(s => `<div class="gd-kv"><span>S · ${s.hits || 0} touches</span><b>$${_gdPx(s.level)}</b></div>`).join("") || '<div class="gd-muted">—</div>'}
      </div>
      <div class="gd-card gc">
        <div class="gd-sec-h">Resistance</div>
        ${(d.levels?.resistance || []).map(s => `<div class="gd-kv"><span>R · ${s.hits || 0} touches</span><b>$${_gdPx(s.level)}</b></div>`).join("") || '<div class="gd-muted">—</div>'}
      </div>
    </div>`;

    h += `<div class="gd-card gc">
      <div class="gd-sec-h">Volume profile</div>
      <div class="gd-kv"><span>POC</span><b>$${_gdPx(d.volumeProfile?.poc)}</b></div>
      <div class="gd-kv"><span>Value area</span><b>$${_gdPx(d.volumeProfile?.val)} – $${_gdPx(d.volumeProfile?.vah)}</b></div>
      <div class="gd-muted" style="margin:8px 0">${_escHtml(d.volumeProfile?.note || "")}</div>
      ${_gdVpBars(d.volumeProfile?.bins)}
    </div>`;

    h += `<div class="gd-card gc">
      <div class="gd-sec-h">Volatility</div>
      <div class="gd-kv"><span>ATR(14)</span><b>$${_gdPx(d.volatility?.atr14)}</b></div>
      <div class="gd-kv"><span>Realized vol 20d</span><b>${d.volatility?.realizedVol20dPct != null ? d.volatility.realizedVol20dPct + "%" : "—"}</b></div>
      <div class="gd-kv"><span>Condition</span><b>${_escHtml(d.volatility?.condition || "—")}</b></div>
    </div>`;

    h += `<div class="gd-card gc">
      <div class="gd-sec-h">Dollar & yields</div>
      <div class="gd-kv"><span>DXY</span><b>${d.macro?.dxy?.px != null ? d.macro.dxy.px : "—"} <span class="${(d.macro?.dxy?.chg||0)>=0?"px-up":"px-dn"}">${d.macro?.dxy?.chg != null ? _gdChg(d.macro.dxy.chg) : ""}</span></b></div>
      <div class="gd-kv"><span>US 10Y</span><b>${d.macro?.tnx?.px != null ? d.macro.tnx.px + "%" : "—"}</b></div>
      <div class="gd-kv"><span>VIX</span><b>${d.macro?.vix?.px != null ? d.macro.vix.px : "—"}</b></div>
    </div>`;

    h += `<div class="gd-card gc">
      <div class="gd-sec-h">Gamma / liquidity proxies</div>
      <p class="gd-disclaimer">${_escHtml(d.gamma?.disclaimer || "")}</p>
      <div class="gd-levels">${(d.gamma?.levels || []).map(L =>
        `<span class="gd-chip">$${_gdPx(L.level)} · ${_escHtml(L.label || "")}</span>`
      ).join("")}</div>
    </div>`;

    h += `<div class="gd-card gc"><div class="gd-sec-h">Upcoming macro events</div>`;
    (d.events || []).forEach(e => {
      h += `<div class="gd-event">
        <div class="gd-event-d">${_escHtml(e.date)} · ${bd(e.impact || "medium", e.impact === "high" ? "var(--rd)" : "var(--gd)")} ${bd(e.cat || "Macro", "var(--bl)")}</div>
        <div class="gd-event-t">${_escHtml(e.event)}</div>
        <div class="gd-sm">${_escHtml(e.goldNote || "")}</div>
      </div>`;
    });
    if (!(d.events || []).length) h += `<div class="gd-muted">No model events in window</div>`;
    h += `</div>`;
  }

  h += `<div class="gd-roadmap gc">
    <div class="gd-sec-h">Build sequence</div>
    <div class="gd-roadmap-row"><span class="gd-done">✓</span> Gold dashboard (delayed data)</div>
    <div class="gd-roadmap-row"><span class="gd-done">✓</span> Weekly playbook engine</div>
    <div class="gd-roadmap-row"><span class="gd-todo">○</span> BYOK AI (OpenAI / Anthropic / Grok / Perplexity)</div>
    <div class="gd-roadmap-row"><span class="gd-todo">○</span> Alerts + personal trading journal</div>
  </div>`;

  return h;
}

// ═══════════════════════════════════════════════════════════
// PAGE: DASHBOARD
// ═══════════════════════════════════════════════════════════
// ═══════════════════════════════════════════════════════════
// PAGE: HOME — the front door of the desk
// ═══════════════════════════════════════════════════════════
// Orientation, not another dashboard: where the tape stands, what the desk is
// saying today, what your own book is doing, and a way back to wherever you
// were. Everything here is a doorway to a surface that owns the detail.
//
// Nothing on this page invents a number. A symbol that has not come back from
// a feed this session is simply absent — see PRODUCT.md on honest provenance.

// Recent destinations, most recent first. Stored because the desk is a tool
// people return to, and "where was I" should survive a reload.
let _recentNav = _lsJson(localStorage.getItem("td_recent_nav"), []);
function _pushRecentNav(p) {
  if (!p || p === "home" || !Array.isArray(_recentNav)) return;
  _recentNav = [p, ..._recentNav.filter(x => x !== p)].slice(0, 6);
  try { localStorage.setItem("td_recent_nav", JSON.stringify(_recentNav)); } catch (e) {}
}

function _homeGreeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

/** Live rows from the user's own book — watchlist first, then portfolio. */
function _homeBookRows() {
  const seen = new Set();
  const out = [];
  const push = (tk) => {
    if (!tk || seen.has(tk)) return;
    seen.add(tk);
    const ch = liveChg(tk);
    if (ch == null) return; // no feed this session — do not show a stale mark
    out.push({ tk, ch, px: fp(tk).p });
  };
  (getActiveWl().tickers || []).forEach(push);
  (portfolio || []).forEach(p => push(p.tk));
  return out.slice(0, 6);
}

function renderHome() {
  const re = _computeRegimeEngine();
  const liveN = liveSymbols.size;

  let h = `<div class="home-wrap">`;

  // ── Greeting and where the tape stands ──
  h += `<div class="home-hero">
    <div class="home-greet">${_homeGreeting()}</div>
    <div class="home-regime" style="color:${re.col}">${re.label}${re.score != null ? ` · <span class="home-regime-sc">${re.score}/100</span>` : ""}</div>
    <div class="home-tape">${liveN
      ? `${liveN} symbols live · VIX ${re.vix} · ${re.spxProxy ? "SPY" : "SPX"} ${re.spx === "—" ? "—" : re.spx}`
      : "Awaiting the price feed — nothing on this page is a stored guess"}</div>
  </div>`;

  // ── Today's brief ──
  h += `<section class="home-sec">
    <div class="home-sec-h">Today's brief</div>`;
  if (_brief?.headline) {
    // houseView is the short stance ("Constructive"); summary is the body.
    h += `<div class="home-brief gc-a" onclick="nav('brief')">
      <div class="home-brief-stance">${_escHtml(_brief.houseView || "House view")}</div>
      <div class="home-brief-h">${_escHtml(_brief.headline)}</div>
      ${_brief.summary ? `<div class="home-brief-s">${_escHtml(String(_brief.summary).slice(0, 220))}${String(_brief.summary).length > 220 ? "…" : ""}</div>` : ""}
      <div class="home-brief-go">Open brief →</div>
    </div>`;
  } else {
    h += `<div class="home-empty">
      <div>${_briefLoad ? "Loading today's brief…" : "No brief loaded yet."}</div>
      <button type="button" class="home-empty-btn" onclick="nav('brief');loadDispatchBrief(true)">Open the Brief</button>
    </div>`;
  }
  h += `</section>`;

  // ── Your book · session movers ──
  const book = _homeBookRows();
  const movers = [...A].filter(a => liveChg(a.tk) != null)
    .map(a => ({ tk: a.tk, ch: liveChg(a.tk), px: fp(a.tk).p }))
    .sort((a, b) => Math.abs(b.ch) - Math.abs(a.ch)).slice(0, 6);

  h += `<div class="home-cols">
    <section class="home-sec">
      <div class="home-sec-h">Your book</div>`;
  if (book.length) {
    h += `<div class="home-rows">${book.map(r => {
      const cls = r.ch > 0 ? "px-up" : r.ch < 0 ? "px-dn" : "px-flat";
      return `<button type="button" class="home-row" onclick="openA('${r.tk}')">
        <span class="home-row-tk">${r.tk}</span>
        <span class="home-row-px">${r.px}</span>
        <span class="home-row-ch ${cls}">${r.ch > 0 ? "+" : ""}${r.ch.toFixed(2)}%</span>
      </button>`;
    }).join("")}</div>
    <button type="button" class="home-more-link" onclick="nav('watch')">Open watchlist →</button>`;
  } else {
    h += `<div class="home-empty">
      <div>${liveN ? "Nothing in your book has a live mark yet." : "Your book is empty."}</div>
      <button type="button" class="home-empty-btn" onclick="nav('watch')">Build a watchlist</button>
    </div>`;
  }
  h += `</section>
    <section class="home-sec">
      <div class="home-sec-h">Session movers</div>`;
  if (movers.length) {
    h += `<div class="home-rows">${movers.map(m => {
      const cls = m.ch > 0 ? "px-up" : m.ch < 0 ? "px-dn" : "px-flat";
      return `<button type="button" class="home-row" onclick="openA('${m.tk}')">
        <span class="home-row-tk">${m.tk}</span>
        <span class="home-row-px">${m.px}</span>
        <span class="home-row-ch ${cls}">${m.ch > 0 ? "+" : ""}${m.ch.toFixed(2)}%</span>
      </button>`;
    }).join("")}</div>
    <button type="button" class="home-more-link" onclick="nav('mkt')">Open markets →</button>`;
  } else {
    h += `<div class="home-empty"><div>No live desk names yet this session.</div></div>`;
  }
  h += `</section>
  </div>`;

  // ── Pick up where you left off ──
  const recent = (Array.isArray(_recentNav) ? _recentNav : [])
    .filter(p => NAV_ALL.includes(p) && NAV_LABELS[p]).slice(0, 5);
  if (recent.length) {
    h += `<section class="home-sec">
      <div class="home-sec-h">Pick up where you left off</div>
      <div class="home-chips">${recent.map(p =>
        `<button type="button" class="home-chip" onclick="nav('${p}')">${_navIco(p)}<span>${NAV_LABELS[p]}</span></button>`
      ).join("")}</div>
    </section>`;
  } else {
    h += `<section class="home-sec">
      <div class="home-sec-h">Start here</div>
      <div class="home-chips">${[["gold","Gold Desk"],["brief","Brief"],["mkt","Markets"],["lab","Lab"]].map(([p, l]) =>
        `<button type="button" class="home-chip" onclick="nav('${p}')">${_navIco(p)}<span>${l}</span></button>`
      ).join("")}</div>
    </section>`;
  }

  h += `</div>`;
  return h;
}

function renderDash(){
  const liveBadge = liveSymbols.size > 0
    ? bd(liveSymbols.size + " feed", "var(--gn)")
    : bd(priceFetching ? "Syncing…" : (_priceFetchAttempted ? "Feed error" : "Syncing…"), priceFetching || !_priceFetchAttempted ? "var(--bl)" : "var(--rd)");
  let h = _renderPgHdr("Dashboard", "Book first · live tape · ink ledger desk", `<div class="pg-hdr-actions">${liveBadge}${_renderBriefPlayBtn(true)}${_renderMorningRoutineBtn(true)}</div>`);
  h += `<div class="gd-dash-cta gc-a" onclick="nav('gold')">
    <div class="gd-promise-k">V1 · GOLD FIRST</div>
    <div class="paper-dash-promo-h">Open Gold Desk · this week's playbook</div>
    <div class="paper-dash-promo-s">Structure · S/R · volume profile · conditional scenarios · macro calendar</div>
  </div>`;

  /* UI v6 hierarchy: feed strip → book wire-sheet → actions → spine → research → markets */
  h += _renderLatencyStrip();
  h += _renderBookHome();
  h += _isPremium()
    ? `<div class="paper-dash-promo gc-a" onclick="nav('paper')">
        <div class="paper-dash-promo-k">★ PREMIUM EDITION</div>
        <div class="paper-dash-promo-h">Open your Bloomberg-style newspaper</div>
        <div class="paper-dash-promo-s">Live index strips · lead wire · book column · house brief rail</div>
      </div>`
    : `<div class="paper-dash-promo gc-a paper-dash-promo-free" onclick="nav('paper')">
        <div class="paper-dash-promo-k">NEW · PAPER</div>
        <div class="paper-dash-promo-h">Custom market newspaper</div>
        <div class="paper-dash-promo-s">Bloomberg-style edition for Premium · tap to preview</div>
      </div>`;
  h += _renderQuickActions();
  h += `<div class="qa-row qa-row-secondary">
    <button class="qa-btn qa-gold" onclick="_shareDeskSnapshot()"><span class="qa-ico">↗</span><span>Share desk</span></button>
    <button class="qa-btn" onclick="newsFilter='book';_newsFocusTk=null;nav('news')"><span class="qa-ico">◎</span><span>Book news</span></button>
    <button class="qa-btn" onclick="nav('watch')"><span class="qa-ico">★</span><span>Watchlist</span></button>
    <button class="qa-btn" onclick="nav('port')"><span class="qa-ico">▣</span><span>Portfolio</span></button>
  </div>`;
  h += _renderDeskSpine();
  h += _renderWeeklyDeskLetter();
  h += _renderMorningDeskRunCard();
  h += _renderSiteIntelCard("dash");
  h += _renderSmartFeed();
  h += _renderRegimeEngine();
  h += _renderDispatchBrief();
  h += _renderEarningsCommandCenter();

  h += `<div class="dash-section">
    <div class="sec-hdr-row"><div class="sec-label-v2">Indices</div><span class="sec-hdr-link" onclick="nav('mkt')">Markets →</span></div>
    <div class="idx-grid">`;
  IDX.forEach(idx=>{
    const d=fp(idx.tk);
    const na=d.status==="unavailable";
    const chN=liveChg(idx.tk);
    const chgCls=na||chN==null?"px-flat":(chN>0?"px-up":(chN<0?"px-dn":"px-flat"));
    const sign=chN!=null&&chN>=0?"+":"";
    h+=`<button type="button" class="idx-card" onclick="nav('mkt')" data-price-card="${idx.tk}">
      <div class="idx-card-top"><span class="idx-card-name">${idx.nm}</span><span class="idx-card-stat">${stat(idx.tk)}</span></div>
      <div class="idx-card-px asset-price">${na?"—":d.p}</div>
      <div class="idx-card-chg asset-chg ${chgCls}">${na||chN==null?chgDim():`${sign}${d.chg} (${sign}${d.c}%)`}</div>
      <div class="idx-card-spark">${spark(idx.tk,108,16)}</div>
    </button>`;
  });
  h+=`</div></div>`;

  h+=`<div class="dash-section">
    <div class="sec-hdr-row"><div class="sec-label-v2">Top Conviction</div><span class="sec-hdr-link" onclick="nav('sig')">Signals →</span></div>
    <div class="conv-grid">`;
  [...A].sort((a,b)=>b.sc-a.sc).slice(0,6).forEach(a=>{
    const d=fp(a.tk);
    const na=d.status==="unavailable";
    const chN=liveChg(a.tk);
    const chgCls=na||chN==null?"px-flat":(chN>0?"px-up":(chN<0?"px-dn":"px-flat"));
    const sign=chN!=null&&chN>=0?"+":"";
    h+=`<button type="button" class="conv-card" onclick="openA('${a.tk}')" data-price-card="${a.tk}" data-price-dollar="1" data-price-chg="pct">
      <div class="conv-card-top"><span class="conv-tk">${a.tk}</span><span class="conv-chg asset-chg ${chgCls}">${na||chN==null?chgDim():`${sign}${d.c}%`}</span></div>
      <div class="conv-nm">${a.nm}</div>
      <div class="conv-px asset-price">${na?"—":"$"+d.p}</div>
    </button>`;
  });
  h+=`</div></div>`;

  h += _renderDashboardSectorPulse();
  h += _renderCrossAssetPulse();
  h += _renderContinueResearch();

  h+=`<div class="dash-split">${renderFearGreed()}${renderCalendar()}</div>`;

  /* Compact tools + trust — below primary tape, not competing with book */
  h += _renderPremiumUpsell();
  h += _renderProTerminalHub();
  h += _renderNeuralSessionStrip();
  h += `<details class="dash-details">
    <summary class="dash-details-sum">Desk path · data trust · free vs premium</summary>
    <div class="dash-details-body">
      ${_renderStartHereCard()}
      ${_renderTrustBar()}
      ${_renderFreePremiumMap()}
    </div>
  </details>`;

  h+=`<div class="card research-promo" onclick="nav('research');openReport('spx2026')">
    <div class="card-header">
      <div class="meta">FLAGSHIP RESEARCH</div>
      <span class="meta">8 MIN READ</span>
    </div>
    <div class="research-promo-h">Three <em>paths</em>, one tape</div>
    <div class="research-promo-d">S&P 500 year-end 2026 scenarios — baseline, stagflation, AI capex melt-up</div>
    <div class="research-promo-tags">${bd("SPX 7,650","var(--bl)")}${bd("SPX 5,050","var(--rd)")}${bd("SPX 7,800","var(--gn)")}</div>
  </div>`;

  h+=`<div class="sec-hdr-row"><div class="sec-label-v2">Breaking News</div><div class="sec-hdr-meta">${newsFetching?'<span class="si-spin"></span>':newsLastFetch?'<span class="live-dot"></span>':''}<span class="sec-hdr-link" onclick="nav('news')">ALL →</span></div></div>`;
  NEWS.slice(0,5).forEach((n,i)=>{const tc=n.im==="high"?"var(--rd)":n.tg==="Crypto"?"var(--pu)":n.tg==="Commodities"?"var(--gd)":n.tg==="FX"?"var(--cy)":n.tg==="Geopolitics"?"var(--rd)":"var(--bl)";
    const link=n.link?`onclick="window.open('${String(n.link).replace(/'/g,"%27")}','_blank','noopener')"style="cursor:pointer"`:"";
    const rel=_newsRelevanceTags((n.x||"")+" "+(n.desc||""));
    const relHtml=rel.map(r=>`<span class="news-rel" style="color:${r.col};border-color:${r.col}40" onclick="event.stopPropagation();openA('${r.tk}')">${r.tag}</span>`).join("");
    h+=`<div class="gc news-card news-card-dash" style="border-left-color:${tc};animation:fadeUp 0.15s ease ${i*0.04}s both" ${link}><div class="news-meta-row"><div class="news-meta-left">${bd(n.tg,tc)}${n.im==="high"?bd("⚡","var(--rd)"):""}${relHtml}</div><span class="news-age">${_newsRelTime(n.ts)}</span></div>
    <div class="news-hl">${_escHtml(n.x||"")}</div></div>`;});
  return h;
}

// ═══════════════════════════════════════════════════════════
// PAGE: MARKETS
// ═══════════════════════════════════════════════════════════
function renderMkt(){
  const liveCount=A.filter(a=>liveSymbols.has(a.tk)).length;
  const dynCount=Object.keys(_dynMarkets).length;

  // View switcher tabs
  let h = _renderPgHdr("Markets", `${liveCount} live · ${dynCount} dynamic`, `<span class="live-dot"></span>`);
  h += _renderSiteIntelCard("mkt");
  h+=`<div class="tabs" style="margin-bottom:12px">
    <button class="${_mktView==='curated'?'on':''}" onclick="_mktViewSet('curated')">★ Curated (${A.length})</button>
    <button class="${_mktView==='live'?'on':''}" onclick="_mktViewSet('live')">⚡ Live Markets${dynCount?` (${dynCount}+)`:''}</button>
    <button class="${_mktView==='global'?'on':''}" onclick="_mktViewSet('global')">🌍 Global</button>
  </div>`;
  if (_mktView === "curated") {
    h += `<div class="mkt-sort-row"><span class="mkt-sort-lbl">Sort</span>
      <button class="mkt-sort-btn${_mktCuratedSort === 'smart' ? ' on' : ''}" onclick="_mktCuratedSort='smart';renderMain()">◆ Regime fit</button>
      <button class="mkt-sort-btn${_mktCuratedSort === 'score' ? ' on' : ''}" onclick="_mktCuratedSort='score';renderMain()">Conviction</button>
      <button class="mkt-sort-btn${_mktCuratedSort === 'chg' ? ' on' : ''}" onclick="_mktCuratedSort='chg';renderMain()">% Change</button>
    </div>`;
  }

  // Dynamic live view
  if(_mktView==='live'||_mktView==='global'){
    if(_mktView==='global'&&!_dynLoadedTypes.global){fetchDynamicMarkets('global');}
    else if(_mktView==='live'&&!_dynLoadedTypes.us_top){fetchDynamicMarkets('us_top');}
    return h+renderDynMarkets();
  }

  // Curated view
  let mktList = [...A];
  if (_mktCuratedSort === "smart") mktList = _mktSmartSort(mktList);
  else if (_mktCuratedSort === "score") mktList.sort((a, b) => b.sc - a.sc);
  else if (_mktCuratedSort === "chg") mktList.sort((a, b) => (liveChg(b.tk) ?? -Infinity) - (liveChg(a.tk) ?? -Infinity));
  mktList.forEach(a=>{const d=fp(a.tk);const iw=isWatched(a.tk);
    const ch=liveChg(a.tk);
    const sign=ch!=null&&ch>=0?"+":"";
    const col=d.status==="unavailable"||ch==null?"var(--t3)":ch>0?"var(--gn)":ch<0?"var(--rd)":"var(--t3)";
    const showDollar=a.cat==="Stock"||a.cat==="Crypto"||a.cat==="Commodity";
    const sc=catSec(a.cat);
    h+=`<div class="gc gc-a gc-sector gc-glow ${sc}" data-price-card="${a.tk}" data-price-dollar="${showDollar?1:0}" onclick="openA('${a.tk}')">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:12px">
        <div style="display:flex;gap:10px;align-items:center;min-width:0">${ring(a.sc,38)}
          <div style="min-width:0">
            <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
              <span style="font-size:14px;font-weight:800;font-family:var(--mn)">${a.tk}</span>
              ${stat(a.tk)}
              ${_smartFitBadge(a.tk)}
              <span style="cursor:pointer;color:${iw?"var(--gd)":"var(--t3)"};font-size:14px;line-height:1" onclick="event.stopPropagation();togWatch('${a.tk}')" aria-label="${iw?'Remove from':'Add to'} watchlist">★</span>
            </div>
            <div style="font-size:11px;color:var(--t2);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${a.nm}</div>
            <div style="margin-top:5px">${bd(a.se,a.se.includes("Bull")?"var(--gn)":a.se.includes("Bear")?"var(--rd)":"var(--bl)")}${d.asOf?` <span class="asof-tag">as of ${_fmtAsOf(d.asOf)}</span>`:""}</div>
          </div>
        </div>
        <div style="text-align:right;flex-shrink:0">
          <div class="asset-price">${d.status==="unavailable"?"—":(showDollar?"$":"")+d.p}</div>
          <div class="asset-chg" style="color:${col}">${d.status==="unavailable"?chgDim():`${sign}${d.chg} (${sign}${d.c}%)`}</div>
          <div style="margin-top:4px">${spark(a.tk,72,18)}</div>
        </div>
      </div></div>`;});
  if(!mktList.length){
    h+=`<div class="gc empty-state"><div class="empty-title">No markets to show</div><div class="empty-sub">Feed may still be syncing. Tap ⟳ or run Desk Run.</div><button class="btn btn-primary" onclick="fetchLivePrices();runMorningDeskRun()">Sync feeds</button></div>`;
  }
  return h;
}

// ═══════════════════════════════════════════════════════════
// PAGE: ANALYZE
// ═══════════════════════════════════════════════════════════
function renderDynAnlz(){
  if(_dynLoading)return`<div class="gc" style="padding:28px;text-align:center"><div style="width:14px;height:14px;border:2px solid var(--bl);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div><div style="font-family:var(--sn);font-size:13px;color:var(--t2)">Loading ${_dynTk}…</div></div>`;
  if(!_dynData||!_dynData.price)return`<div class="gc" style="padding:28px;text-align:center"><div style="font-family:var(--sn);font-size:14px;color:var(--rd);margin-bottom:12px">"${_dynTk}" — no price data found</div><div style="font-size:12px;color:var(--t2);line-height:1.7">Try exchange suffixes: RELIANCE.NS · MC.PA · 7203.T · HSBA.L</div><button onclick="_dynClear()" style="margin-top:14px;background:var(--b2);color:var(--t2);border:1px solid var(--gb);border-radius:8px;padding:8px 16px;font-family:var(--sn);font-size:12px;cursor:pointer">← Back</button></div>`;
  const d=_dynData;
  const chN=typeof d.chgPct==="number"&&isFinite(d.chgPct)?d.chgPct:null;
  const col=chN==null?'var(--t3)':chN>0?'var(--gn)':chN<0?'var(--rd)':'var(--t3)';
  const sign=chN!=null&&chN>=0?'+':'';
  const pxN=typeof d.price==="number"&&d.price>0?d.price:null;
  const absN=typeof d.chgAbs==="number"&&isFinite(d.chgAbs)?d.chgAbs:null;
  let h=`<div class="gc"><div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px"><div><div style="font-family:var(--mn);font-size:18px;font-weight:800">${_dynTk}</div><div style="font-size:11px;color:var(--t2)">${d.name||""}</div><div style="font-size:9px;color:var(--t3);margin-top:4px">${d.exchange||'Dynamic lookup'}</div></div><div style="text-align:right"><div style="font-family:var(--mn);font-size:22px;font-weight:800">${pxN!=null?('$'+pxN.toFixed(2)):'—'}</div><div style="color:${col};font-family:var(--mn);font-size:12px">${chN!=null?`${sign}${absN!=null?absN.toFixed(2):'—'} (${sign}${chN.toFixed(2)}%)`:'NO SYNC'}</div></div></div>`;
  const hd=(d.chart||[]).filter(v=>typeof v==='number'&&isFinite(v)&&v>0);
  if(hd.length>=5){const mn=Math.min(...hd),mx=Math.max(...hd),rng=mx-mn||1;const pts=hd.map((v,i)=>`${(i/(hd.length-1))*300},${50-((v-mn)/rng)*44}`).join(' ');h+=`<svg viewBox="0 0 300 60" style="width:100%;height:60px;display:block;margin-bottom:10px"><polyline points="${pts}" fill="none" stroke="${col}" stroke-width="1.5"/></svg>`;}
  if(d.news&&d.news.length){h+=`<div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;margin-bottom:6px">RECENT NEWS</div>`;d.news.forEach(n=>{h+=`<div style="padding:8px 0;border-bottom:1px solid var(--gb);font-size:12px;color:var(--t2);line-height:1.4">${n.x}</div>`;});}
  h+=`<button onclick="_dynClear()" style="margin-top:12px;background:var(--b2);color:var(--t2);border:1px solid var(--gb);border-radius:8px;padding:8px 16px;font-family:var(--sn);font-size:12px;cursor:pointer">← Back</button></div>`;
  return h;
}

function renderAnlz(){
  if(_dynTk)return renderDynAnlz();
  if(!selTk){return `<div class="gc" style="padding:28px;text-align:center"><div style="font-size:13px;color:var(--t2)">Select an asset to analyze</div><div style="font-size:10px;color:var(--t3);margin-top:4px">Use search or Markets tab</div></div>`;}
  const a=A.find(x=>x.tk===selTk);
  if(!a){
    const tk=selTk;selTk=null;
    lookupTicker(tk);
    return `<div class="gc" style="padding:28px;text-align:center"><div style="width:14px;height:14px;border:2px solid var(--bl);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div><div style="font-family:var(--sn);font-size:13px;color:var(--t2)">Loading ${tk}…</div></div>`;
  }const d=fp(a.tk);const iw=isWatched(a.tk);
  const chAn=liveChg(a.tk);
  const chCol=d.status==="unavailable"||chAn==null?"var(--t3)":chAn>0?"var(--gn)":chAn<0?"var(--rd)":"var(--t3)";
  const chSign=chAn!=null&&chAn>=0?"+":"";

  let h=`<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;margin-bottom:10px">
    <div style="display:flex;gap:10px;align-items:center">${ring(a.sc,52)}
      <div><div style="display:flex;align-items:center;gap:5px;flex-wrap:wrap"><span style="font-size:18px;font-weight:800;font-family:var(--mn)">${a.tk}</span>${bd(a.cat,catBd(a.cat))}${stat(a.tk)}
        <span style="cursor:pointer;font-size:16px;color:${iw?"var(--gd)":"var(--t3)"}" onclick="togWatch('${a.tk}')" aria-label="${iw?'Remove from':'Add to'} watchlist">★</span>
        <button onclick="event.stopPropagation();_toggleCompare('${a.tk}')" style="background:${_compareTks.includes(a.tk)?'var(--puG)':'var(--b2)'};border:1px solid var(--gb);color:var(--t2);border-radius:5px;padding:2px 8px;font-family:var(--mn);font-size:9px;cursor:pointer">⚖</button></div>
        <div style="font-size:10px;color:var(--t2)">${a.nm}</div>
        <div style="display:flex;gap:3px;margin-top:3px">${bd(a.se,a.se.includes("Bull")?"var(--gn)":"var(--bl)")}${bd(a.ra,a.ra.includes("Buy")?"var(--gn)":"var(--bl)")}${bd("Score: "+a.sc,scC(a.sc))}</div></div></div>
    <div style="text-align:right"><div style="font-family:var(--mn);font-weight:800;font-size:24px;letter-spacing:-0.02em">${d.status==="unavailable"?"—":((a.cat==="Stock"||a.cat==="Crypto"||a.cat==="Commodity")?"$":"")+d.p}</div>
      <div class="asset-chg" style="color:${chCol}">${d.status==="unavailable"?'<span style="font-size:10px;letter-spacing:0.08em">AWAITING LIVE FEED</span>':`${chSign}${d.chg} (${chSign}${d.c}%)`}</div></div></div>`;

  h+=`<div class="gc"><div style="font-size:8px;color:var(--t3);font-family:var(--mn);letter-spacing:0.1em;margin-bottom:4px">INTRADAY · UPDATES ON FETCH</div>
    <svg viewBox="0 0 300 60" style="width:100%;height:60px;display:block" role="img" aria-label="${a.tk} intraday chart">`;
  const hdRaw=HIST[a.tk]||[];const hd=hdRaw.filter(v=>typeof v==="number"&&isFinite(v)&&v>0);
  if(hd.length>=5){const mn=Math.min(...hd),mx=Math.max(...hd),rng=mx-mn||Math.max(mx*0.001,1e-9);
    const sparkCol=chAn==null?"var(--t3)":chAn>0?"var(--gn)":chAn<0?"var(--rd)":"var(--t3)";
    const sparkFill=chAn==null?"rgba(255,255,255,0.04)":chAn>0?"var(--gnG)":chAn<0?"var(--rdG)":"rgba(255,255,255,0.04)";
    const pts=hd.map((v,i)=>`${(i/(hd.length-1))*300},${55-((v-mn)/rng)*48}`).join(" ");
    h+=`<polyline points="${pts}" fill="none" stroke="${sparkCol}" stroke-width="1.5"/>`;
    const fillPts=pts+` ${300},55 0,55`;
    h+=`<polyline points="${fillPts}" fill="${sparkFill}" stroke="none" opacity="0.5"/>`;
  } else {
    h+=`<text x="150" y="34" text-anchor="middle" font-family="JetBrains Mono" font-size="10" fill="var(--t3)" letter-spacing="0.08em">CHART UNAVAILABLE — INSUFFICIENT INTRADAY DATA</text>`;
  }
  h+=`</svg></div>`;

  h += _renderSiteIntelCard("ticker", { tk: a.tk });

  h+=`<div class="tabs"><button class="${aTab==="ov"?"on":""}" onclick="_setATab('ov')">Overview</button><button class="${aTab==="nw"?"on":""}" onclick="_setATab('nw')">News</button><button class="${aTab==="fi"?"on":""}" onclick="_setATab('fi')">Financials</button><button class="${aTab==="val"?"on":""}" onclick="_setATab('val')">💰 Valuation</button><button class="${aTab==="earn"?"on":""}" onclick="_setATab('earn')">📈 Earnings</button><button class="${aTab==="th"?"on":""}" onclick="_setATab('th')">Thesis</button><button class="${aTab==="al"?"on":""}" onclick="_setATab('al')">Alerts</button><button class="${aTab==="cm"?"on":""}" onclick="_setATab('cm')">Lenses</button><button class="${aTab==="inst"?"on":""}" onclick="_setATab('inst')">🏛 Institutions${!_isPremium()?'★':''}</button></div>`;

  if(aTab==="nw"){
    h+=`<div id="anlz-nw-root">${_renderTickerNewsPanel(a.tk)}</div>`;
    setTimeout(()=>_ensureTickerCompanyNews(a.tk),40);
  }

  if(aTab==="ov"){
    const rs=_tickerRelStrength(a.tk);
    const rsVal=rs.rel==null?"—":`${rs.rel>=0?"+":""}${rs.rel.toFixed(2)}%`;
    h+=`<div class="gc" style="padding:12px;border-left:3px solid ${rs.col};margin-bottom:8px">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div><div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.15em">RELATIVE STRENGTH vs SPY (DAY)</div>
        <div style="font-family:var(--mn);font-size:18px;font-weight:900;color:${rs.col};margin-top:4px">${rsVal}</div></div>
        <div style="font-family:var(--mn);font-size:10px;font-weight:700;color:${rs.col}">${rs.label}</div>
      </div></div>`;
    h+=`<div class="gr" style="grid-template-columns:1fr 1fr"><div class="gc"><div style="font-size:8px;color:var(--t3);font-family:var(--mn);letter-spacing:0.1em">METRICS</div>`;
    [{l:"P/E",v:a.pe},{l:"Mkt Cap",v:a.mc},{l:"Beta",v:a.beta},{l:"Sentiment",v:a.se}].forEach(m=>{h+=`<div style="border-top:1px solid var(--gb);padding:5px 0"><div style="font-size:8px;color:var(--t3)">${m.l}</div><div style="font-family:var(--mn);font-weight:700;font-size:12px;margin-top:1px">${m.v}</div></div>`;});
    h+=`</div><div class="gc"><div style="font-size:8px;color:var(--t3);font-family:var(--mn);letter-spacing:0.1em">AI THESIS</div>
      <div style="font-size:13px;font-weight:700;color:${a.se.includes("Bull")?"var(--gn)":"var(--bl)"};margin-top:6px">${a.se}</div>
      <div style="font-size:10.5px;color:var(--t2);line-height:1.55;margin-top:4px">${a.th.slice(0,120)}...</div></div></div>`;
    const re=_computeRegimeEngine();
    h+=`<div class="gc" style="padding:12px;margin-top:8px"><div style="font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.15em;margin-bottom:6px">REGIME FIT · ${re.label}</div>
      <div style="font-size:11px;color:var(--t2);line-height:1.5">${a.cat==="Commodity"&&re.overweight.includes("Energy")?"Aligned with regime overweight (Energy/commodities).":a.cat==="Crypto"&&re.score>=55?"Crypto favoured in risk-on regime — size to volatility.":a.se.includes("Bull")&&re.score>=55?"Bullish thesis aligns with risk-on regime.":a.se.includes("Bear")||re.score<45?"Defensive positioning may suit current regime.":"Mixed regime fit — verify with Lens Engine."}</div>
      <button onclick="_setATab('cm')" style="margin-top:10px;width:100%;background:var(--blG);color:var(--bl);border:1px solid rgba(79,142,247,0.2);border-radius:8px;padding:10px;font-family:var(--sn);font-size:11px;font-weight:700;cursor:pointer">⬢ Run Lens Engine on ${a.tk}</button></div>`;
    h += _renderTickerSignals(a.tk);
  }

  if(aTab==="al"){
    const curAlerts=alerts.filter(al=>al.tk===a.tk);
    const curPrice=livePx(a.tk);
    const pxShow=curPrice!=null?`$${curPrice.toFixed(2)}`:"— NO SYNC";
    h+=`<div class="gc" style="padding:14px">
      <div style="font-size:11px;font-weight:700;margin-bottom:10px">Set Price Alert · ${a.tk}</div>
      <div style="font-size:10px;color:var(--t2);margin-bottom:10px">Current price: <strong style="color:var(--tx);font-family:var(--mn)">${pxShow}</strong></div>
      <div style="display:flex;flex-direction:column;gap:8px">
        <input id="al-price" class="port-inp" type="number" placeholder="Target price ($)" step="any" value="${curPrice!=null?(curPrice*1.05).toFixed(2):""}">
        <div style="display:flex;gap:6px">
          <button onclick="addAlert('${a.tk}',document.getElementById('al-price').value,'above')" style="flex:1;background:var(--gnG);color:var(--gn);border:1px solid rgba(16,185,129,0.25);border-radius:8px;padding:10px;font-family:var(--sn);font-size:11px;font-weight:700;cursor:pointer">Alert when ≥ (above)</button>
          <button onclick="addAlert('${a.tk}',document.getElementById('al-price').value,'below')" style="flex:1;background:var(--rdG);color:var(--rd);border:1px solid rgba(239,68,68,0.25);border-radius:8px;padding:10px;font-family:var(--sn);font-size:11px;font-weight:700;cursor:pointer">Alert when ≤ (below)</button>
        </div>
      </div>
      ${curAlerts.length?`<div style="margin-top:12px;border-top:1px solid var(--gb);padding-top:10px"><div style="font-size:9px;color:var(--t3);font-family:var(--mn);letter-spacing:0.1em;margin-bottom:6px">EXISTING ALERTS</div>`:""}
      ${curAlerts.map((al,i)=>{const col=al.dir==="above"?"var(--gn)":"var(--rd)";const idx=alerts.findIndex(x=>x===al);return`<div class="alert-chip" style="border-color:${col}30;margin-bottom:4px;display:flex;justify-content:space-between;width:100%"><span style="color:var(--tx)">${al.dir==="above"?"≥":"≤"} <strong style="color:${col}">$${al.targetPrice}</strong> · ${al.active?"Active":"Triggered"}</span><span onclick="removeAlert(${idx})" style="color:var(--rd);cursor:pointer;padding-left:8px">✕</span></div>`;}).join("")}
      ${curAlerts.length?"</div>":""}
    </div>
    <div class="gc" style="border-left:3px solid var(--gd);padding:12px">
      <div style="font-size:10px;color:var(--t2);line-height:1.6">Alerts trigger an in-app notification when live price data matches your target. Alerts are stored in your browser — they reset if you clear site data.</div>
    </div>`;
  }

  if(aTab==="fi"){
    h+=`<div id="anlz-fin-root"><div style="padding:20px;text-align:center"><div style="width:14px;height:14px;border:2px solid var(--bl);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div><div style="font-family:var(--mn);font-size:10px;color:var(--t3)">LOADING FINANCIALS…</div></div></div>`;
    setTimeout(()=>loadFinancials(a.tk,'anlz-fin-root'),50);
  }

  if(aTab==="earn"){
    h+=`<div id="anlz-earn-root"><div style="padding:20px;text-align:center"><div style="width:14px;height:14px;border:2px solid var(--gn);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div><div style="font-family:var(--mn);font-size:10px;color:var(--t3)">LOADING EARNINGS INTELLIGENCE…</div></div></div>`;
    setTimeout(()=>loadEarnings(a.tk,'anlz-earn-root'),50);
  }

  if(aTab==="inst"){
    h+=`<div id="anlz-inst-root"><div style="padding:20px;text-align:center"><div style="width:14px;height:14px;border:2px solid var(--gd);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div><div style="font-family:var(--mn);font-size:10px;color:var(--t3)">LOADING INSTITUTIONAL DATA…</div></div></div>`;
    setTimeout(()=>loadHolders(a.tk,'anlz-inst-root'),50);
  }

  if(aTab==="val"){
    h+=`<div id="anlz-val-root"><div style="padding:20px;text-align:center"><div style="width:14px;height:14px;border:2px solid var(--pu);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div><div style="font-family:var(--mn);font-size:10px;color:var(--t3)">LOADING VALUATION DASHBOARD…</div></div></div>`;
    setTimeout(()=>loadValuation(a.tk,'anlz-val-root'),50);
  }

  if(aTab==="th"){
    h+=`<div class="gc" style="border-left:3px solid var(--bl)"><div style="font-size:8px;color:var(--t3);font-family:var(--mn);letter-spacing:0.1em">INVESTMENT THESIS</div>
      <div style="font-size:11.5px;color:var(--t2);line-height:1.6;margin-top:6px">${a.th}</div></div>`;
    const hist=reason.filter(r=>r.ticker===a.tk);
    if(hist.length){h+=`<div class="gc"><div style="font-size:8px;color:var(--t3);font-family:var(--mn);letter-spacing:0.1em">REASONING BANK HISTORY</div>`;
      hist.forEach((r,i)=>{h+=`<div style="border-top:${i?"1px solid var(--gb)":"none"};padding-top:${i?8:6}px;margin-top:${i?8:6}px"><div style="display:flex;gap:5px;align-items:center"><span style="font-size:8px;color:var(--t3);font-family:var(--mn)">${new Date(r.ts).toLocaleDateString()}</span>${bd(r.verdict,r.verdict==="IMPLEMENT"?"var(--gn)":r.verdict==="REJECT"?"var(--rd)":"var(--gd)")}</div>
        <div style="font-size:10px;color:var(--t2);margin-top:3px">${r.thesis.slice(0,100)}...</div></div>`;});
      h+=`</div>`;}
  }

  if(aTab==="cm"){
    const vClass=v=>{if(!v)return"hold";const u=v.toUpperCase();if(u.includes("BUY")||u.includes("IMPLEMENT")||u.includes("OVERWEIGHT")||u.includes("ACCUMULATE"))return"buy";if(u.includes("AVOID")||u.includes("SELL")||u.includes("REJECT")||u.includes("REDUCE"))return"avoid";return"hold";};
    const vcColor=vc=>vc==="buy"?"var(--gn)":vc==="avoid"?"var(--rd)":"var(--gd)";

    // ── Lenses header card ──
    h+=`<div class="gc" style="border-left:3px solid var(--bl);padding:14px">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
        <div style="width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,var(--bl),var(--pu));display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0">⬢</div>
        <div style="flex:1">
          <div style="font-size:15px;font-weight:800;letter-spacing:-0.01em">Investing Lenses</div>
          <div style="font-size:9px;color:var(--t2);font-family:var(--mn);margin-top:2px">Lens Engine · server-fused data + AI · ${a.tk}</div>
        </div>
        ${stat(a.tk)}
      </div>`;

    if(!comRes&&!comLoad){
      h+=`<div style="border-top:1px solid var(--gb);padding-top:12px">
        <div style="font-size:11px;color:var(--t3);line-height:1.6;margin-bottom:10px"><strong style="color:var(--tx)">${a.tk}</strong> — Lens Engine fuses live Yahoo quote, 52-week momentum, Finnhub financials, earnings, analyst targets, your terminal feed, and web search into five framework analyses.</div>
        <div style="display:flex;flex-wrap:wrap;gap:5px;margin-bottom:12px">
          ${INVEST_LENSES.map(m=>`<div style="display:flex;align-items:center;gap:5px;background:var(--bg);border:1px solid var(--gb);border-radius:8px;padding:5px 9px"><span style="font-size:13px">${m.ic}</span><span style="font-size:10px;font-weight:600;color:var(--t2)">${m.nm}</span></div>`).join("")}
        </div>
        <div style="margin-bottom:10px">
          <div style="font-family:var(--mn);font-size:8px;color:var(--pu);letter-spacing:0.15em;margin-bottom:6px">INTERROGATE YOUR THESIS (OPTIONAL)</div>
          ${_renderLensQuickPrompts(a.tk)}
          <textarea id="lens-thesis-${a.tk}" oninput="_setLensThesis('${a.tk}',this.value)" placeholder="Write your bull case — lenses will attack it, not agree with it" style="width:100%;min-height:72px;background:var(--bg);border:1px solid var(--gb);border-radius:8px;padding:10px;font-family:var(--sn);font-size:12px;color:var(--t2);resize:vertical;box-sizing:border-box;line-height:1.5">${(lensThesis[a.tk]||'').replace(/</g,'&lt;')}</textarea>
        </div>
        <button onclick="runCommittee('${a.tk}')" style="width:100%;background:linear-gradient(135deg,var(--bl),var(--pu));color:white;border:none;border-radius:9px;padding:12px;cursor:pointer;font-size:13px;font-weight:700;font-family:var(--sn);letter-spacing:0.01em">⬢ Run Lens Engine${_isPremium()?'':'<span style="font-size:10px;opacity:0.75;margin-left:6px">★ Premium</span>'}</button>
      </div>`;
    }

    if(comLoad){
      h+=`<div style="border-top:1px solid var(--gb);padding-top:12px">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
          <div style="width:14px;height:14px;border:2px solid var(--bl);border-top-color:transparent;border-radius:50%;animation:spin 1s linear infinite;flex-shrink:0"></div>
          <span style="font-size:12px;font-weight:600;color:var(--tx)">Lens Engine — fusing live data + AI reasoning…</span>
        </div>
        ${INVEST_LENSES.map((m,i)=>`<div style="display:flex;align-items:center;gap:8px;padding:7px 0;border-bottom:1px dotted var(--gb)">
          <span style="font-size:14px">${m.ic}</span>
          <span style="font-size:11px;color:var(--t2);flex:1">${m.nm}</span>
          <div style="width:50px;height:3px;background:linear-gradient(90deg,${m.cl},transparent);border-radius:2px;opacity:0.6;animation:flash 1.5s ease ${i*0.28}s infinite"></div>
        </div>`).join("")}
      </div>`;
    }

    h+=`</div>`;

    if(comErr){
      h+=`<div class="gc" style="padding:14px;border-top:1px solid var(--gb);color:var(--rd);font-family:var(--sn);font-size:12px;line-height:1.5">
        ${_escHtml(comErr)}
        <div style="margin-top:8px;color:var(--t3);font-size:10px">No substitute analysis was shown. Please retry when the provider is available.</div>
        <button onclick="runCommittee('${a.tk}')" style="margin-top:10px;width:100%;background:var(--b2);border:1px solid var(--rd)55;color:var(--rd);border-radius:8px;padding:9px;cursor:pointer;font-weight:700">↻ Retry Lens Engine</button>
      </div>`;
    }

    if(comRes){
      if(lensMeta)h+=`<div class="gc" style="padding:12px 14px">${_renderLensPowers(lensMeta)}</div>`;
      if(lensIntel)h+=_renderLensIntel(lensIntel);
      const members=_getLensMembers(comRes);
      const synth=_getSynthesis(comRes);
      const buyCount=members.filter(c=>vClass(c.verdict)==="buy").length;
      const avoidCount=members.filter(c=>vClass(c.verdict)==="avoid").length;
      const holdCount=members.length-buyCount-avoidCount;
      const tot=members.length||1;
      const buyPct=Math.round(buyCount/tot*100);
      const avoidPct=Math.round(avoidCount/tot*100);
      const holdPct=100-buyPct-avoidPct;
      const dir=buyCount>avoidCount&&buyCount>=holdCount?"BUY":avoidCount>buyCount&&avoidCount>=holdCount?"AVOID":"HOLD";
      const dirCol=vcColor(dir==="BUY"?"buy":dir==="AVOID"?"avoid":"hold");
      const wDir=lensMeta?.weighted?.dir;
      const wCol=wDir?vcColor(wDir==="BUY"?"buy":wDir==="AVOID"?"avoid":"hold"):dirCol;

      // ── Consensus overview ──
      h+=`<div class="gc" style="padding:14px;border-top:3px solid ${wCol};animation:fadeUp 0.2s ease both">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px">
          <div>
            <div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.18em;margin-bottom:4px">${wDir?`REGIME-WEIGHTED · ${lensMeta?.regime?.label||''}`:'LENS CONSENSUS'}</div>
            <div style="font-size:26px;font-weight:900;letter-spacing:-0.01em;color:${wCol};line-height:1">${wDir||dir}</div>
            <div style="font-size:9px;color:var(--t3);margin-top:3px;font-family:var(--mn)">${members.length} lenses · simple vote: ${dir}${wDir&&wDir!==dir?` · unweighted differed`:""}</div>
          </div>
          <div style="text-align:right">
            <div style="font-size:9px;color:var(--t3);font-family:var(--mn);margin-bottom:4px">SPLIT</div>
            <div style="display:flex;flex-direction:column;gap:2px;align-items:flex-end">
              ${buyCount>0?`<div style="font-family:var(--mn);font-size:10px;font-weight:700;color:var(--gn)">${buyCount} Buy</div>`:""}
              ${holdCount>0?`<div style="font-family:var(--mn);font-size:10px;font-weight:700;color:var(--gd)">${holdCount} Hold</div>`:""}
              ${avoidCount>0?`<div style="font-family:var(--mn);font-size:10px;font-weight:700;color:var(--rd)">${avoidCount} Avoid</div>`:""}
            </div>
          </div>
        </div>
        <div style="display:flex;gap:2px;border-radius:6px;overflow:hidden;height:10px;margin-bottom:8px">
          ${buyPct>0?`<div style="flex:${buyPct};background:var(--gn);border-radius:${avoidPct===0&&holdPct===0?"6px":""} 0 0 ${avoidPct===0&&holdPct===0?"6px":""}"></div>`:""}
          ${holdPct>0?`<div style="flex:${holdPct};background:var(--gd)"></div>`:""}
          ${avoidPct>0?`<div style="flex:${avoidPct};background:var(--rd);border-radius:0 6px 6px 0"></div>`:""}
        </div>
        <div style="display:flex;gap:14px;font-family:var(--mn);font-size:9px">
          <div style="display:flex;align-items:center;gap:5px"><span style="width:9px;height:9px;border-radius:2px;background:var(--gn);flex-shrink:0"></span><span style="color:var(--t2)">Buy ${buyPct}%</span></div>
          <div style="display:flex;align-items:center;gap:5px"><span style="width:9px;height:9px;border-radius:2px;background:var(--gd);flex-shrink:0"></span><span style="color:var(--t2)">Hold ${holdPct}%</span></div>
          <div style="display:flex;align-items:center;gap:5px"><span style="width:9px;height:9px;border-radius:2px;background:var(--rd);flex-shrink:0"></span><span style="color:var(--t2)">Avoid ${avoidPct}%</span></div>
        </div>
      </div>`;

      // ── Individual lens cards ──
      members.forEach((c,i)=>{
        const mem=INVEST_LENSES.find(m=>m.nm===c.name);
        const col=mem?.cl||"var(--bl)";
        const vc=vClass(c.verdict);
        const vcol=vcColor(vc);
        const tagline=mem?.tagline||"";
        h+=`<div class="gc" style="border-left:3px solid ${col};padding:14px;animation:fadeUp 0.3s ease ${i*0.08}s both">
          <div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:12px">
            <div style="width:46px;height:46px;border-radius:12px;background:linear-gradient(135deg,${col}25,${col}08);border:1.5px solid ${col}35;display:flex;align-items:center;justify-content:center;flex-shrink:0">
              <span style="font-size:22px">${mem?.ic||"?"}</span>
            </div>
            <div style="flex:1;min-width:0">
              <div style="font-size:14px;font-weight:800;letter-spacing:-0.01em">${c.name}</div>
              <div style="font-size:9px;color:${col};font-family:var(--mn);font-weight:700;letter-spacing:0.1em;text-transform:uppercase;margin-top:2px">${c.role}</div>
              ${tagline?`<div style="font-size:10px;color:var(--t3);font-style:italic;margin-top:4px;font-family:var(--sf);line-height:1.4">${tagline}</div>`:""}
            </div>
            <div style="background:${vcol}12;border:1.5px solid ${vcol}35;border-radius:8px;padding:6px 11px;text-align:center;flex-shrink:0;min-width:58px">
              <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:2px">VERDICT</div>
              <div style="font-family:var(--mn);font-size:10px;font-weight:900;color:${vcol};letter-spacing:0.03em">${c.verdict||"—"}</div>
            </div>
          </div>
          <div style="background:var(--bg);border-radius:8px;padding:12px;border:1px solid var(--gb)">
            <div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.15em;margin-bottom:6px">ANALYSIS</div>
            <div style="font-size:12px;color:var(--t2);line-height:1.7">${c.analysis}</div>
            ${c.confidence!=null?`<div style="margin-top:10px;padding-top:8px;border-top:1px dotted var(--gb);display:flex;justify-content:space-between;align-items:center"><span style="font-family:var(--mn);font-size:8px;color:var(--t3)">CONFIDENCE</span><span style="font-family:var(--mn);font-size:11px;font-weight:800;color:${c.confidence>=70?'var(--gn)':c.confidence>=50?'var(--gd)':'var(--rd)'}">${c.confidence}%</span></div>`:""}
            ${c.keyRisk?`<div style="font-size:10px;color:var(--rd);margin-top:6px;line-height:1.4">⚠ ${c.keyRisk}</div>`:""}
            ${c.catalyst&&c.catalyst!=="null"?`<div style="font-size:10px;color:var(--gn);margin-top:4px;line-height:1.4">⚡ ${c.catalyst}</div>`:""}
            ${c.timeHorizon?`<div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-top:6px">Horizon: ${c.timeHorizon}</div>`:""}
          </div>
        </div>`;
      });

      // ── Risk Synthesis ──
      if(synth&&!lensIntel){
        const vc=vClass(synth.verdict);
        const vcol=vcColor(vc);
        h+=`<div class="gc" style="background:linear-gradient(135deg,rgba(59,130,246,0.07),var(--b1));border:1.5px solid rgba(59,130,246,0.22);padding:16px;animation:fadeUp 0.3s ease ${(members.length+1)*0.08}s both">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">
            <div style="width:46px;height:46px;border-radius:12px;background:linear-gradient(135deg,var(--bl),var(--pu));display:flex;align-items:center;justify-content:center;flex-shrink:0">
              <span style="font-size:22px">⚖</span>
            </div>
            <div style="flex:1">
              <div style="font-family:var(--mn);font-size:8px;color:var(--bl);letter-spacing:0.18em;margin-bottom:3px">RISK SYNTHESIS</div>
              <div style="font-size:15px;font-weight:800;letter-spacing:-0.01em">Final Lens Verdict</div>
            </div>
          </div>
          <div style="border:1.5px solid ${vcol}30;border-radius:10px;padding:14px;background:${vcol}06;margin-bottom:12px;text-align:center">
            <div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.25em;margin-bottom:6px">SYNTHESIS VERDICT</div>
            <div style="font-size:28px;font-weight:900;color:${vcol};letter-spacing:0.06em;line-height:1">${synth.verdict||"MONITOR"}</div>
          </div>
          <div style="background:var(--bg);border-radius:8px;padding:12px;border:1px solid var(--gb);margin-bottom:10px">
            <div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.15em;margin-bottom:6px">SYNTHESIS RATIONALE</div>
            <div style="font-size:12px;color:var(--t2);line-height:1.7">${synth.analysis}</div>
          </div>
          <div style="font-family:var(--mn);font-size:8px;color:var(--t3);text-align:center;padding-top:8px;border-top:1px dotted var(--gb)">
            Live AI analysis · ${new Date().toLocaleDateString("en-GB",{day:"numeric",month:"short",year:"numeric"})} · Research purposes only · Not attributed to any real person
          </div>
        </div>`;
      }
      h+=`<button onclick="runCommittee('${a.tk}')" style="width:100%;background:var(--b2);color:var(--t2);border:1px solid var(--gb);border-radius:9px;padding:11px;cursor:pointer;font-size:12px;font-weight:600;font-family:var(--sn);margin-top:8px">⬢ Re-run Lens Engine</button>`;
    }
  }
  return h;
}

// ═══════════════════════════════════════════════════════════
// PAGE: SIGNALS
// ═══════════════════════════════════════════════════════════
function renderSig(){
  const re = _computeRegimeEngine();
  let h = _renderPgHdr("Signals", "Conviction-weighted · regime-aligned playbook");
  h += _renderSiteIntelCard("signals");
  h += `<div class="gc" style="padding:12px;border-left:3px solid ${re.col};margin-bottom:10px">
    <div style="font-family:var(--mn);font-size:8px;color:${re.col};letter-spacing:0.15em;margin-bottom:6px">REGIME PLAYBOOK · ${re.label}</div>
    <div style="font-size:11px;color:var(--t2);line-height:1.55;margin-bottom:8px">${re.narrative}</div>
    <div style="display:flex;gap:6px;flex-wrap:wrap">${re.overweight.slice(0,3).map(x => `<span style="font-family:var(--mn);font-size:9px;padding:3px 8px;border-radius:6px;background:var(--gnG);color:var(--gn);border:1px solid rgba(16,185,129,0.2)">+ ${x}</span>`).join("")}${re.underweight.slice(0,2).map(x => `<span style="font-family:var(--mn);font-size:9px;padding:3px 8px;border-radius:6px;background:var(--rdG);color:var(--rd);border:1px solid rgba(239,68,68,0.2)">− ${x}</span>`).join("")}</div>
  </div>`;
  SIGS.forEach(s=>{const bc=s.cat.includes("Bull")||s.cat==="Momentum"||s.cat==="Accumulation"||s.cat==="Contrarian"?"var(--gn)":s.cat.includes("Warning")||s.cat==="Geopolitical"?"var(--rd)":"var(--gd)";
    const linked=A.find(a=>s.a.toUpperCase().includes(a.tk)||s.x.toUpperCase().includes(a.tk));
    h+=`<div class="gc gc-a" style="border-left:3px solid ${bc};padding:10px;cursor:pointer" onclick="${linked?`openA('${linked.tk}')`:'void(0)'}"><div style="display:flex;justify-content:space-between;align-items:center"><span style="font-size:13px;font-weight:700">${s.a}</span><span style="font-family:var(--mn);font-weight:800;font-size:16px;color:${s.cf>=75?"var(--gn)":"var(--gd)"}">${s.cf}%</span></div>
      <div style="font-size:10.5px;color:var(--t2);line-height:1.45;margin-top:3px">${s.x}</div>
      <div style="display:flex;gap:3px;margin-top:5px;flex-wrap:wrap">${bd(s.cat,bc)}${bd(s.s,s.s==="Strong"?"var(--gn)":"var(--gd)")}${bd(s.tg,"var(--bl)")}${bd(s.hz,"var(--pu)")}${linked?bd(linked.tk,"var(--bl)"):""}</div></div>`;});
  return h;
}

// ═══════════════════════════════════════════════════════════
// ── News intelligence helpers ──
function _tagNewsHeadline(text){
  const found=[];
  const low=(text||"").toLowerCase();
  const up=(text||"").toUpperCase();
  // Alias map first (bitcoin → BTC, gold → XAU)
  for(const [tk,aliases] of Object.entries(NEWS_ALIASES)){
    if(found.length>=5)break;
    if(aliases.some(a=>low.includes(a))||up.includes(tk)){
      if(!found.includes(tk))found.push(tk);
    }
  }
  for(const a of A){
    if(!a.tk||found.length>=5)continue;
    if(found.includes(a.tk))continue;
    const sym=a.tk.toUpperCase();
    const esc=sym.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
    const re=new RegExp(sym.length>=3?`(\\$${esc}|\\b${esc}\\b)`:`(\\$${esc})`);
    if(re.test(up))found.push(a.tk);
  }
  return found;
}
function _newsSentiment(text){
  const t=(text||"").toLowerCase();
  const bull=['beat','beats','surge','surges','raise','raises','jump','jumps','upgrade','upgraded','profit','profits','record','rallies','rally','top'];
  const bear=['miss','misses','fall','falls','cut','cuts','warn','warns','downgrade','downgraded','loss','losses','decline','declines','crash','crashes','layoff'];
  if(bull.some(w=>t.includes(w)))return `<span class="sent-bull">▲ BULLISH</span>`;
  if(bear.some(w=>t.includes(w)))return `<span class="sent-bear">▼ BEARISH</span>`;
  return '';
}
function _newsBookTickers(){
  const set=new Set();
  const add=t=>{
    if(!t)return;
    const raw=String(t);
    set.add(raw);
    const desk=(typeof resolveInternalTicker==="function"?resolveInternalTicker(raw):"")||raw;
    if(desk)set.add(desk);
    // Also keep Yahoo wire form when known (BTC → also match BTC-USD in headlines)
    if(typeof YAHOO_SYMBOLS!=="undefined"&&YAHOO_SYMBOLS[desk])set.add(YAHOO_SYMBOLS[desk]);
  };
  try{getActiveWl().tickers.forEach(add);}catch(e){}
  try{portfolio.forEach(p=>add(p?.tk));}catch(e){}
  return [...set];
}
function _newsMatchesBook(n,book){
  if(!book?.length)return false;
  const hay=((n.x||"")+" "+(n.desc||"")).toLowerCase();
  const tags=_tagNewsHeadline((n.x||"")+" "+(n.desc||""));
  return book.some(tk=>{
    const desk=(typeof resolveInternalTicker==="function"?resolveInternalTicker(tk):"")||tk;
    if(tags.includes(tk)||tags.includes(desk))return true;
    if(hay.includes(String(tk).toLowerCase())||hay.includes(String(desk).toLowerCase()))return true;
    const aliases=[...(NEWS_ALIASES[tk]||[]),...(NEWS_ALIASES[desk]||[])];
    return aliases.some(a=>hay.includes(a));
  });
}
function _newsRegimeKeywords(){
  try{
    const re=_computeRegimeEngine();
    const blob=((re.label||"")+" "+(re.narrative||"")+" "+(re.overweight||[]).join(" ")+" "+(re.underweight||[]).join(" ")).toLowerCase();
    const keys=["oil","rates","fed","dollar","gold","risk","recession","inflation","yield","crypto","china","iran","growth","tech","energy"];
    return keys.filter(k=>blob.includes(k));
  }catch(e){return [];}
}
function _newsScore(n){
  let s=0;
  const book=_newsBookTickers();
  const tags=_tagNewsHeadline((n.x||"")+" "+(n.desc||""));
  const bookHits=tags.filter(t=>book.includes(t)).length;
  s+=bookHits*4;
  if(n.im==="high")s+=2;
  else if(n.im==="medium")s+=1;
  if(n.tier===1)s+=1;
  const rk=_newsRegimeKeywords();
  const hay=((n.x||"")+" "+(n.desc||"")).toLowerCase();
  s+=rk.filter(k=>hay.includes(k)).length;
  // recency: full points under 2h, decay after
  const ageH=n.ts?(Date.now()-n.ts)/3600000:24;
  if(ageH<1)s+=3;
  else if(ageH<3)s+=2;
  else if(ageH<12)s+=1;
  return s;
}
function _newsRelTime(ts){
  if(!ts)return "—";
  const age=Date.now()-ts;
  if(age<0)return "now";
  if(age<60000)return Math.max(1,Math.round(age/1000))+"s";
  if(age<3600000)return Math.round(age/60000)+"m";
  if(age<86400000)return Math.round(age/3600000)+"h";
  try{return new Date(ts).toLocaleDateString([],{month:"short",day:"numeric"});}catch(e){return "—";}
}
function _setNewsFilter(id){newsFilter=id;_newsFocusTk=null;_paintNewsListOnly(true);}
function _setNewsSort(s){newsSort=s;_paintNewsListOnly(true);}
function _setNewsQ(v){
  newsQ=v;
  // Surgical update only — full renderMain() kills input focus every keystroke
  _paintNewsListOnly(false);
}
function _paintNewsListOnly(updateToolbar){
  const body=document.getElementById("news-list-body");
  if(body){
    const compact=body.dataset.compact==="1";
    body.innerHTML=_renderNewsBodyInner({compact});
    if(updateToolbar){
      const tb=document.getElementById("news-toolbar");
      if(tb)tb.outerHTML=_renderNewsToolbar({compact});
    }
    const cnt=document.getElementById("news-result-count");
    if(cnt)cnt.textContent=_filteredNewsList().length+" shown";
    return;
  }
  _refreshNewsView();
}
function _refreshNewsView(){
  if(pg==="news")renderMain();
  else if(IS_DESKTOP()&&!termSelTk&&!_dynTk)renderP2();
  else if(pg==="dash")renderMain();
}
function _newsOpenLab(tk){
  if(tk){setLabTicker(tk);nav("lab");}
  else nav("lab");
}
function _newsHaystack(n){
  const tags=_tagNewsHeadline((n.x||"")+" "+(n.desc||""));
  return ((n.x||"")+" "+(n.desc||"")+" "+(n.src||"")+" "+(n.tg||"")+" "+(n.cat||"")+" "+tags.join(" ")).toLowerCase();
}
function _newsIsWorld(n){
  if(!n)return false;
  if(n.tg==="Geopolitics"||n.cat==="Geopolitics")return true;
  if(n.src&&NEWS_WORLD_SRCS.has(n.src))return true;
  const kws=NEWS_CAT_KEYWORDS.world||NEWS_CAT_KEYWORDS.geopolitics||[];
  const hay=_newsHaystack(n);
  return kws.some(k=>hay.includes(k));
}
function _newsInCategory(n, filterId){
  if(!filterId||filterId==="all")return true;
  if(filterId==="world")return _newsIsWorld(n);
  const filterMap={
    stocks:['Stocks','Earnings'],
    commodities:['Commodities'],
    fx:['FX'],
    geopolitics:['Geopolitics'],
    world:['Geopolitics'],
    crypto:['Crypto'],
    macro:['Macro','Central Bank','Regulation']
  };
  if(filterMap[filterId]?.includes(n.tg))return true;
  if(n.cat&&filterMap[filterId]?.includes(n.cat))return true;
  // Keyword fallback — commodity headlines often mis-tagged as Stocks/Macro
  const kws=NEWS_CAT_KEYWORDS[filterId];
  if(!kws)return false;
  const hay=_newsHaystack(n);
  return kws.some(k=>hay.includes(k));
}
function _filteredNewsList(){
  const book=_newsBookTickers();
  let list=NEWS.slice();
  if(_newsFocusTk){
    const tk=_newsFocusTk.toUpperCase();
    list=list.filter(n=>{
      const tags=_tagNewsHeadline((n.x||"")+" "+(n.desc||""));
      return tags.includes(tk)||(n.x||"").toUpperCase().includes(tk)||(n.company||"")===tk;
    });
    const cached=_companyNewsCache[tk];
    if(cached?.items?.length){
      const seen=new Set(list.map(n=>(n.x||"").toLowerCase().slice(0,40)));
      cached.items.forEach(n=>{
        const k=(n.x||"").toLowerCase().slice(0,40);
        if(!seen.has(k)){list.push(n);seen.add(k);}
      });
    }
  }else if(newsFilter==="book"){
    list=list.filter(n=>_newsMatchesBook(n,book));
  }else if(newsFilter!=="all"){
    list=list.filter(n=>_newsInCategory(n,newsFilter));
  }
  const q=(newsQ||"").trim().toLowerCase();
  if(q){
    // Multi-keyword: all terms must match (AND). Phrase still works as whole string too.
    const terms=q.split(/\s+/).filter(Boolean);
    list=list.filter(n=>{
      const hay=_newsHaystack(n);
      if(hay.includes(q))return true; // full phrase
      return terms.every(t=>hay.includes(t));
    });
  }
  if(newsSort==="relevant")list=[...list].sort((a,b)=>_newsScore(b)-_newsScore(a)||(b.ts||0)-(a.ts||0));
  else list=[...list].sort((a,b)=>(b.ts||0)-(a.ts||0));
  return list;
}
async function _loadCompanyNews(tk){
  const sym=sanitizeTicker(tk)||String(tk||"").toUpperCase();
  if(!sym)return;
  _newsFocusTk=sym;
  newsFilter="all";
  const cached=_companyNewsCache[sym];
  if(cached&&Date.now()-cached.ts<5*60*1000){_refreshNewsView();return;}
  try{
    const to=new Date();const from=new Date(Date.now()-7*86400000);
    const fmt=d=>d.toISOString().slice(0,10);
    const res=await fetch(`/api/finnhub?endpoint=company-news&symbol=${encodeURIComponent(sym)}&from=${fmt(from)}&to=${fmt(to)}`,{signal:AbortSignal.timeout(12000)});
    if(!res.ok)throw new Error("fail");
    const items=await res.json();
    const mapped=(Array.isArray(items)?items:[]).slice(0,20).map(it=>{
      const date=new Date((it.datetime||0)*1000);
      return {
        t:String(date.getHours()).padStart(2,"0")+":"+String(date.getMinutes()).padStart(2,"0"),
        x:(it.headline||"").slice(0,120),
        desc:(it.summary||"").replace(/<[^>]*>/g,"").trim().slice(0,200),
        tg:detectTag((it.headline||"")+" "+(it.summary||"")),
        im:detectImpact(it.headline||""),
        src:it.source||"Finnhub",
        tier:1,
        ts:date.getTime()||Date.now(),
        link:(it.url&&it.url.startsWith("http"))?it.url:_newsLink({x:it.headline}),
        company:sym
      };
    }).filter(n=>n.x);
    _companyNewsCache[sym]={ts:Date.now(),items:mapped};
  }catch(e){
    _companyNewsCache[sym]={ts:Date.now(),items:[]};
  }
  _refreshNewsView();
  if(pg!=="news")nav("news");
}
function _renderNewsCard(n,i,opts){
  const compact=!!opts?.compact;
  const tc=n.im==="high"?"var(--rd)":n.tg==="Crypto"?"var(--pu)":n.tg==="Commodities"?"var(--gd)":n.tg==="Macro"||n.tg==="Central Bank"?"var(--cy)":n.tg==="Geopolitics"?"var(--rd)":n.tg==="FX"?"var(--cy)":"var(--bl)";
  const tags=_tagNewsHeadline((n.x||"")+" "+(n.desc||""));
  const sent=_newsSentiment(n.x||"");
  const rel=_newsRelevanceTags((n.x||"")+" "+(n.desc||""));
  const relHtml=rel.map(r=>`<span class="news-rel" style="color:${r.col};border-color:${r.col}40" onclick="event.stopPropagation();openA('${r.tk}')">${r.tag}</span>`).join("");
  const topTk=tags[0]||"";
  const score=newsSort==="relevant"?_newsScore(n):null;
  const href=_newsLink(n);
  const pricePill=topTk&&liveSymbols.has(topTk)?(()=>{const d=fp(topTk);const ch=liveChg(topTk);const col=ch==null?"var(--t3)":ch>0?"var(--gn)":ch<0?"var(--rd)":"var(--t3)";return d.status==="unavailable"?"":`<span class="news-px" style="color:${col}">${topTk} ${d.p}</span>`;})():"";
  const desc=(!compact&&n.desc)?`<div class="news-desc">${_escHtml(n.desc.slice(0,160))}${n.desc.length>160?"…":""}</div>`:"";
  const acts=compact?"":`<div class="news-acts">
    ${href?`<button type="button" class="news-act" onclick="event.stopPropagation();window.open('${href.replace(/'/g,"%27")}','_blank','noopener')">Read</button>`:""}
    ${topTk?`<button type="button" class="news-act" onclick="event.stopPropagation();openA('${topTk}')">Open ${topTk}</button>`:""}
    ${topTk?`<button type="button" class="news-act" onclick="event.stopPropagation();togWatch('${topTk}')">${isWatched(topTk)?"★ Watch":"☆ Watch"}</button>`:""}
    ${topTk?`<button type="button" class="news-act news-act-gold" onclick="event.stopPropagation();_newsOpenLab('${topTk}')">Lab</button>`:""}
  </div>`;
  const bookHit=rel.some(r=>r.tag==="WATCH"||r.tag==="PORT"||r.tag==="WL+PORT");
  return `<div class="gc news-card${compact?" news-card-sm":""}${bookHit?" news-book":""}" style="padding:${compact?"8px 10px":"10px 12px"};border-left:3px solid ${tc};animation:fadeUp 0.12s ease ${Math.min(i,12)*0.02}s both">
    <div style="display:flex;justify-content:space-between;align-items:center;gap:6px;flex-wrap:wrap">
      <div style="display:flex;gap:3px;align-items:center;flex-wrap:wrap">${bd(n.tg,tc)}${n.im==="high"?bd("⚡","var(--rd)"):""}${relHtml}${sent}${pricePill}${n.src?`<span class="news-src">${_escHtml(n.src)}</span>`:""}${score!=null&&score>=4?`<span class="news-score" title="Desk relevance">R${score}</span>`:""}</div>
      <span class="news-time">${_newsRelTime(n.ts)}</span>
    </div>
    <div class="news-hl">${_escHtml(n.x||"")}</div>
    ${desc}
    ${tags.length?`<div class="news-tags">${tags.map(sym=>`<span class="news-tag" onclick="event.stopPropagation();_loadCompanyNews('${sym}')">${sym}</span>`).join("")}</div>`:""}
    ${acts}
  </div>`;
}
function _renderNewsToolbar(opts){
  const compact=!!opts?.compact;
  const bookN=_newsBookTickers().length;
  const shown=_filteredNewsList().length;
  const worldN=NEWS.filter(_newsIsWorld).length;
  const filters=[
    {id:'all',label:'All',icon:'◉'},
    {id:'book',label:`My Book${bookN?` (${bookN})`:""}`,icon:'◎'},
    {id:'world',label:`World${worldN?` (${worldN})`:""}`,icon:'🌐'},
    {id:'stocks',label:'Stocks',icon:'📈'},
    {id:'commodities',label:'Commodities',icon:'🛢'},
    {id:'fx',label:'FX',icon:'💱'},
    {id:'geopolitics',label:'Geopolitics',icon:'🌍'},
    {id:'crypto',label:'Crypto',icon:'₿'},
    {id:'macro',label:'Macro',icon:'🏛'}
  ];
  let h=`<div class="news-toolbar" id="news-toolbar">
    <div class="news-search-row">
      <input id="news-search-inp" class="news-search" type="search" placeholder="Search Fed, oil, Ukraine, NVDA…" value="${_escAttr(newsQ)}" oninput="_setNewsQ(this.value)" autocomplete="off" spellcheck="false">
      <div class="news-sort">
        <button type="button" class="news-sort-btn${newsSort==='relevant'?' on':''}" onclick="_setNewsSort('relevant')">Relevant</button>
        <button type="button" class="news-sort-btn${newsSort==='latest'?' on':''}" onclick="_setNewsSort('latest')">Latest</button>
      </div>
      <button type="button" class="hdr-act-btn news-refresh-btn" onclick="fetchLiveNews()">${newsFetching?'…':'⟳'}</button>
    </div>
    <div class="nf-wrap">`;
  filters.forEach(f=>{
    h+=`<button type="button" class="nf-btn${newsFilter===f.id&&!_newsFocusTk?' on':''}" data-cat="${f.id}" onclick="_setNewsFilter('${f.id}')">${f.icon} ${f.label}</button>`;
  });
  h+=`</div>`;
  h+=`<div class="news-result-meta"><span id="news-result-count">${shown} shown</span> · ${NEWS.length} loaded · ${worldN} world · ${RSS_FEEDS.length} feeds${newsQ?` · filter “${_escHtml(newsQ)}”`:""}</div>`;
  if(_newsFocusTk){
    h+=`<div class="news-focus-bar">Company news · <strong>${_escHtml(_newsFocusTk)}</strong>
      <button type="button" class="news-act" onclick="_newsFocusTk=null;_refreshNewsView()">Clear</button>
      <button type="button" class="news-act news-act-gold" onclick="openA('${_newsFocusTk}')">Open analysis</button>
    </div>`;
  }
  if(!compact){
    h+=_isPremium()
      ?`<button type="button" class="news-hub-promo news-hub-promo-prem" onclick="nav('paper')"><span class="news-hub-promo-k">★ PAPER</span><span class="news-hub-promo-h">Open your broadsheet edition</span><span class="news-hub-promo-s">Lead · World · Book · Macro wires</span></button>`
      :`<button type="button" class="news-hub-promo" onclick="nav('paper')"><span class="news-hub-promo-k">PREMIUM</span><span class="news-hub-promo-h">Unlock Paper newspaper</span><span class="news-hub-promo-s">Bloomberg-style desk edition from live free feeds</span></button>`;
    const tagCounts={};
    NEWS.forEach(n=>{tagCounts[n.tg]=(tagCounts[n.tg]||0)+1;});
    h+=`<div class="news-tag-stats">`;
    Object.entries(tagCounts).sort((a,b)=>b[1]-a[1]).forEach(([tag,count])=>{
      const tc2=tag==="Crypto"?"var(--pu)":tag==="Commodities"?"var(--gd)":tag==="Geopolitics"?"var(--rd)":tag==="FX"?"var(--cy)":tag==="Macro"||tag==="Central Bank"?"var(--gn)":"var(--bl)";
      h+=`<span style="font-size:7.5px;padding:2px 6px;border-radius:10px;background:${tc2}15;color:${tc2};font-family:var(--mn);font-weight:600;border:1px solid ${tc2}30">${tag} ${count}</span>`;
    });
    h+=`</div>`;
  }
  h+=`</div>`;
  return h;
}
function _renderNewsSourceHealth(){
  const keys=[...RSS_FEEDS.map(f=>f.src),...Object.keys(newsFeedHealth).filter(k=>k.startsWith("Finnhub"))];
  const uniq=[...new Set(keys)];
  let h=`<div class="news-sources"><div class="news-sources-lbl">FEED HEALTH</div><div class="news-sources-row">`;
  uniq.forEach(src=>{
    const hlt=newsFeedHealth[src];
    const ok=hlt?hlt.ok:undefined;
    const cls=ok===true?"ok":ok===false?"bad":"unk";
    h+=`<span class="news-src-pill ${cls}" title="${hlt?((hlt.ok?"OK":"Fail")+" · "+(hlt.count||0)+" items"):"Not fetched yet"}">${_escHtml(src)}</span>`;
  });
  h+=`</div></div>`;
  return h;
}
function _renderNewsSection(title, items, opts){
  opts=opts||{};
  if(!items||!items.length)return "";
  let h=`<div class="news-hub-sec${opts.cls?" "+opts.cls:""}"><div class="sec-label news-hub-sec-h">${_escHtml(title)}${opts.sub?`<span class="news-hub-sec-sub">${_escHtml(opts.sub)}</span>`:""}</div>`;
  items.forEach((n,i)=>{h+=_renderNewsCard(n,i,{compact:!!opts.compact});});
  if(opts.moreAct)h+=`<button type="button" class="news-act" style="margin:4px 0 10px" onclick="${opts.moreAct}">${_escHtml(opts.moreLabel||"View all →")}</button>`;
  h+=`</div>`;
  return h;
}
function _renderNewsBodyInner(opts){
  const compact=!!opts?.compact;
  const list=_filteredNewsList();
  const book=_newsBookTickers();
  let h="";
  if(newsError)h+=`<div class="gc" style="border-left:3px solid var(--gd);padding:8px;margin-bottom:8px"><div style="font-size:10px;color:var(--gd)">⚠ ${_escHtml(newsError)}</div></div>`;
  if(newsFetching&&!NEWS.length)h+=`<div class="gc" style="padding:20px;text-align:center"><div style="width:16px;height:16px;border:2px solid var(--bl);border-top-color:transparent;border-radius:50%;animation:spin 1s linear infinite;margin:0 auto"></div><div style="font-size:10px;color:var(--t2);margin-top:8px">Fetching ${RSS_FEEDS.length} feeds…</div></div>`;

  if(newsFilter==="book"&&!book.length){
    h+=`<div class="gc empty-state" style="padding:20px;text-align:center"><div class="empty-title">No book symbols yet</div><div class="empty-sub">Add ★ watchlist names or portfolio positions — My Book surfaces headlines that hit your desk.</div>
      <button class="btn btn-primary" onclick="nav('mkt')">Browse markets</button></div>`;
    return h+_renderNewsSourceHealth();
  }

  // Hub layout: Desk → World → Markets wire (All view, full newsroom only)
  const hubMode=!compact&&newsFilter==="all"&&!_newsFocusTk&&!newsQ;
  if(hubMode){
    const desk=book.length
      ? NEWS.filter(n=>_newsMatchesBook(n,book)).sort((a,b)=>_newsScore(b)-_newsScore(a)).slice(0,4)
      : [];
    const used=new Set(desk.map(n=>(n.x||"").toLowerCase().slice(0,40)));
    const world=NEWS.filter(n=>_newsIsWorld(n)&&!used.has((n.x||"").toLowerCase().slice(0,40)))
      .sort((a,b)=>_newsScore(b)-_newsScore(a)||(b.ts||0)-(a.ts||0)).slice(0,6);
    world.forEach(n=>used.add((n.x||"").toLowerCase().slice(0,40)));
    const wire=list.filter(n=>!used.has((n.x||"").toLowerCase().slice(0,40)));
    if(desk.length){
      h+=_renderNewsSection("On your desk",desk,{
        cls:"news-desk-sec",
        moreAct:"_setNewsFilter('book')",
        moreLabel:"View all book hits →"
      });
    }else if(!book.length){
      h+=`<div class="news-hub-hint gc"><div class="empty-sub" style="margin:0;max-width:none">Star names or add lots — book headlines surface here first.</div>
        <button type="button" class="news-act" onclick="nav('mkt')">Browse markets</button></div>`;
    }
    if(world.length){
      h+=_renderNewsSection("World",world,{
        cls:"news-world-sec",
        sub:`${world.length} on wire`,
        moreAct:"_setNewsFilter('world')",
        moreLabel:"Full world wire →"
      });
    }
    if(wire.length){
      h+=`<div class="sec-label news-hub-sec-h">Markets wire</div>`;
      wire.forEach((n,i)=>{h+=_renderNewsCard(n,i,{compact:false});});
    }else if(!desk.length&&!world.length){
      h+=`<div class="gc" style="padding:20px;text-align:center"><div style="font-size:12px;color:var(--t2)">No headlines yet</div><div style="font-size:9px;color:var(--t3);margin-top:4px">Tap ⟳ Refresh to pull ${RSS_FEEDS.length} feeds</div></div>`;
    }
    h+=_renderNewsSourceHealth();
    return h;
  }

  if(!list.length){
    const hint=newsFilter==="commodities"
      ? "No commodity hits yet — try search “oil” or “gold”, or tap ⟳ Refresh."
      : newsFilter==="world"
        ? "No world wire yet — tap ⟳ Refresh (BBC / NYT / Guardian / Al Jazeera)."
        : "Try All, clear search, or refresh";
    h+=`<div class="gc" style="padding:20px;text-align:center"><div style="font-size:12px;color:var(--t2)">No headlines match</div><div style="font-size:9px;color:var(--t3);margin-top:4px;line-height:1.5">${hint}</div></div>`;
  }else{
    if(!compact&&newsFilter==="world")h+=`<div class="sec-label news-hub-sec-h">World wire<span class="news-hub-sec-sub">${list.length} headlines</span></div>`;
    const show=compact?list.slice(0,18):list;
    show.forEach((n,i)=>{h+=_renderNewsCard(n,i,{compact});});
  }
  h+=_renderNewsSourceHealth();
  return h;
}
function _renderNewsBody(opts){
  const compact=!!opts?.compact;
  return `<div id="news-list-body" data-compact="${compact?"1":"0"}">${_renderNewsBodyInner(opts)}</div>`;
}

// ── Book-first home + share + ticker company news ──
function _renderLatencyStrip(){
  const pAge=priceLastFetch?_fmtAge(priceLastFetch.getTime()):"never";
  const nAge=newsLastFetch?_fmtAge(newsLastFetch.getTime()):"never";
  const pAs=priceLastFetch?_fmtAsOf(priceLastFetch.getTime()):"—";
  const nLive=liveSymbols.size;
  return `<div class="latency-strip" id="latency-strip">
    <span class="latency-pill">${nLive?nLive+" SYNCED":"NO FEED"}</span>
    <span class="latency-pill">PRICES ${pAge} · as of ${pAs}</span>
    <span class="latency-pill">NEWS ${nAge}</span>
    <span class="latency-pill latency-muted">YAHOO DELAYED · NOT BLOOMBERG</span>
    <button type="button" class="latency-sync" onclick="fetchLivePrices();fetchLiveNews()">⟳ Sync</button>
  </div>`;
}
function _renderBookHome(){
  const book=_newsBookTickers();
  const re=_computeRegimeEngine();
  const score=Math.max(0,Math.min(100,Number(re.score)||0));
  const liveN=book.filter(tk=>{
    const raw=String(tk||"");
    const desk=(typeof resolveInternalTicker==="function"?resolveInternalTicker(raw):"")||raw;
    return liveSymbols.has(raw)||liveSymbols.has(desk)||liveSymbols.has(raw.toUpperCase());
  }).length;
  const asOf=priceLastFetch?_fmtAsOf(priceLastFetch.getTime()):"—";
  let h=`<div class="book-home gc" data-ui="v6">
    <div class="book-home-head">
      <div>
        <div class="desk-kicker book-home-kicker">Book · first surface</div>
        <div class="book-home-meta">Regime <strong style="color:${re.col||"var(--wire)"}">${re.label}</strong>
          <span style="color:var(--ink-mute);font-family:var(--mn);font-size:12px"> · ${book.length||0} symbols${book.length?` · ${liveN} live`:""} · as of ${asOf}</span>
        </div>
      </div>
      <div class="book-home-actions">
        <span class="regime-score" style="--regime-col:${re.col||"var(--wire)"};--regime-pct:${score}" title="Regime score ${score}/100">
          <span class="regime-score-ring" data-score="${score}"></span>
          <span class="regime-score-label">${score}<span style="opacity:.55;font-weight:500">/100</span></span>
        </span>
        <button type="button" class="news-act news-act-gold" onclick="runMorningDeskRun()">☀ Desk Run</button>
        <button type="button" class="news-act" onclick="_shareDeskSnapshot()">↗ Share</button>
      </div>
    </div>`;
  if(!book.length){
    h+=`<div class="empty-state">
      <div class="empty-title">Build your book</div>
      <div class="empty-sub">Star names on the watchlist or add portfolio lots — prices, news, and alerts surface here first.</div>
      <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:14px">
        <button class="btn btn-primary" onclick="nav('mkt')">Browse markets</button>
        <button type="button" class="news-act" onclick="nav('watch')">Open watchlist</button>
        <button type="button" class="news-act" onclick="openSearch()">Search ticker</button>
      </div>
    </div></div>`;
    return h;
  }
  h+=`<div class="book-price-row" role="list" aria-label="Book prices">`;
  book.slice(0,10).forEach(tk=>{
    const d=fp(tk);
    const chN=liveChg(tk);
    const chgCls=d.status==="unavailable"||chN==null?"px-flat":(chN>0?"px-up":(chN<0?"px-dn":"px-flat"));
    const sign=chN!=null&&chN>0?"+":"";
    const chgTxt=d.status==="unavailable"||chN==null?"—":`${sign}${d.c}%`;
    h+=`<button type="button" class="book-px-chip" role="listitem" data-price-card="${tk}" onclick="openA('${tk}')" title="${tk}">
      <span class="book-px-tk">${tk}</span>
      <span class="book-px-p asset-price">${d.p}</span>
      <span class="book-px-c asset-chg ${chgCls}">${chgTxt}</span>
      ${stat(tk)}
    </button>`;
  });
  h+=`</div>`;
  const activeAlerts=(typeof alerts!=="undefined"?alerts:[]).filter(a=>a.active&&book.includes(a.tk)).slice(0,4);
  if(activeAlerts.length){
    h+=`<div class="book-alerts">
      <div class="book-section-lbl">Active alerts</div>
      ${activeAlerts.map(a=>`<div class="book-alert-row" onclick="openA('${a.tk}');_setATab('al')"><strong>${a.tk}</strong><span>${a.dir==="above"?"≥":"≤"} $${a.targetPrice}</span></div>`).join("")}
    </div>`;
  }
  const bookNews=NEWS.filter(n=>_newsMatchesBook(n,book)).sort((a,b)=>_newsScore(b)-_newsScore(a)).slice(0,4);
  h+=`<div class="book-section">
    <div class="book-section-head">
      <div class="book-section-lbl">Book news</div>
      <button type="button" class="news-act" onclick="newsFilter='book';_newsFocusTk=null;nav('news')">All book →</button>
    </div>`;
  if(!bookNews.length){
    h+=`<div class="empty-sub" style="margin:8px 0;max-width:none;color:var(--ink-mute)">No book headlines yet · <button type="button" class="news-act" onclick="fetchLiveNews()">⟳ Sync news</button></div>`;
  }else{
    bookNews.forEach((n,i)=>{h+=_renderNewsCard(n,i,{compact:true});});
  }
  h+=`</div>`;
  try{
    const inv=_invStore();
    const notes=_deskNotesStore();
    const invHits=book.filter(tk=>inv[tk]?.rule).slice(0,2);
    if(invHits.length||(notes&&notes.length)){
      h+=`<div class="book-memory">
        <div class="book-section-lbl">Desk memory</div>`;
      invHits.forEach(tk=>{
        h+=`<div class="book-memory-item" onclick="setLabTicker('${tk}');nav('lab')"><strong>${tk}</strong> kill: ${_escHtml((inv[tk].rule||"").slice(0,80))}</div>`;
      });
      if(notes&&notes[0])h+=`<div class="book-memory-note" style="font-family:var(--mn);font-size:11px;color:var(--ink-mute);margin-top:6px">Note: ${_escHtml(String(notes[0].text||notes[0].body||notes[0].note||"").slice(0,90))}</div>`;
      h+=`</div>`;
    }
  }catch(e){}
  h+=`</div>`;
  return h;
}
async function _shareDeskSnapshot(){
  const book=_newsBookTickers();
  const re=_computeRegimeEngine();
  const lines=[
    `The Dispatch · Desk snapshot`,
    `Regime: ${re.label} (${re.score})`,
    `As of: ${priceLastFetch?_fmtAsOf(priceLastFetch.getTime()):"—"} · ${liveSymbols.size} synced`,
    book.length?`Book: ${book.slice(0,8).map(tk=>{
      const d=fp(tk);
      return d.status==="unavailable"?`${tk} —`:`${tk} ${d.p} (${d.c}%)`;
    }).join(" · ")}`:"Book: empty",
    NEWS.filter(n=>_newsMatchesBook(n,book)).slice(0,3).map(n=>`• ${n.x}`).join("\n")||"• No book news yet",
    `https://thedispatch.uk`
  ];
  const text=lines.filter(Boolean).join("\n");
  try{
    if(navigator.clipboard?.writeText){
      await navigator.clipboard.writeText(text);
      showToast("Desk snapshot copied","var(--gn)");
    }else{
      prompt("Copy desk snapshot:",text);
    }
  }catch(e){
    prompt("Copy desk snapshot:",text);
  }
}
function _renderTickerNewsPanel(tk){
  const sym=String(tk||"").toUpperCase();
  const cached=_companyNewsCache[sym];
  const rssHits=NEWS.filter(n=>{
    const tags=_tagNewsHeadline((n.x||"")+" "+(n.desc||""));
    return tags.includes(sym)||(n.x||"").toUpperCase().includes(sym);
  }).slice(0,8);
  const company=cached?.items||[];
  const seen=new Set();
  const merged=[];
  [...company,...rssHits].forEach(n=>{
    const k=(n.x||"").toLowerCase().slice(0,40);
    if(!k||seen.has(k))return;
    seen.add(k);merged.push(n);
  });
  merged.sort((a,b)=>(b.ts||0)-(a.ts||0));
  let h=`<div class="gc" style="padding:12px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
      <div style="font-family:var(--mn);font-size:9px;color:var(--bl);letter-spacing:0.12em">COMPANY NEWS · ${sym}</div>
      <button type="button" class="news-act" onclick="_ensureTickerCompanyNews('${sym}',true)">⟳</button>
    </div>`;
  if(!cached)h+=`<div style="font-size:11px;color:var(--t3);padding:8px 0">Loading company news…</div>`;
  else if(!merged.length)h+=`<div style="font-size:11px;color:var(--t3);padding:8px 0">No recent company headlines · try full Newsroom search</div>`;
  else merged.slice(0,12).forEach((n,i)=>{h+=_renderNewsCard(n,i,{compact:true});});
  h+=`<button type="button" class="news-act news-act-gold" style="margin-top:8px" onclick="_loadCompanyNews('${sym}')">Open in Newsroom →</button></div>`;
  return h;
}
async function _ensureTickerCompanyNews(tk,force){
  const sym=sanitizeTicker(tk)||String(tk||"").toUpperCase();
  if(!sym)return;
  const cached=_companyNewsCache[sym];
  if(!force&&cached&&Date.now()-cached.ts<5*60*1000){
    _paintTickerNewsRoots(sym);return;
  }
  try{
    const to=new Date();const from=new Date(Date.now()-7*86400000);
    const fmt=d=>d.toISOString().slice(0,10);
    const res=await fetch(`/api/finnhub?endpoint=company-news&symbol=${encodeURIComponent(sym)}&from=${fmt(from)}&to=${fmt(to)}`,{signal:AbortSignal.timeout(12000)});
    if(res.ok){
      const items=await res.json();
      const mapped=(Array.isArray(items)?items:[]).slice(0,20).map(it=>{
        const date=new Date((it.datetime||0)*1000);
        return {
          t:String(date.getHours()).padStart(2,"0")+":"+String(date.getMinutes()).padStart(2,"0"),
          x:(it.headline||"").slice(0,120),
          desc:(it.summary||"").replace(/<[^>]*>/g,"").trim().slice(0,200),
          tg:detectTag((it.headline||"")+" "+(it.summary||""),"Stocks"),
          im:detectImpact(it.headline||""),
          src:it.source||"Finnhub",
          tier:1,ts:date.getTime()||Date.now(),
          link:(it.url&&it.url.startsWith("http"))?it.url:_newsLink({x:it.headline}),
          company:sym
        };
      }).filter(n=>n.x);
      _companyNewsCache[sym]={ts:Date.now(),items:mapped};
    }else{
      _companyNewsCache[sym]={ts:Date.now(),items:[]};
    }
  }catch(e){
    _companyNewsCache[sym]={ts:Date.now(),items:[]};
  }
  _paintTickerNewsRoots(sym);
}
function _paintTickerNewsRoots(sym){
  ["term-nw-root","anlz-nw-root"].forEach(id=>{
    const el=document.getElementById(id);
    if(el)el.innerHTML=_renderTickerNewsPanel(sym);
  });
}

// PAGE: NEWS
// ═══════════════════════════════════════════════════════════
function renderNews(){
  const ageStr=newsLastFetch?`Updated ${_newsRelTime(newsLastFetch.getTime())} ago`:(newsFetching?"Fetching feeds…":"Awaiting feeds");
  const worldN=NEWS.filter(_newsIsWorld).length;
  const paperBtn=_isPremium()
    ?`<button type="button" onclick="nav('paper')" class="hdr-act-btn hdr-act-gold" title="Bloomberg-style custom edition">▣ Paper</button>`
    :`<button type="button" onclick="nav('paper')" class="hdr-act-btn" title="Premium newspaper edition">▣ Paper ★</button>`;
  let h=_renderPgHdr("Newsroom",`${NEWS.length} headlines · ${worldN} world · ${RSS_FEEDS.length} feeds · ${ageStr}`,
    `<div class="pg-hdr-actions" style="display:flex;gap:6px;flex-wrap:wrap">${paperBtn}<button onclick="fetchLiveNews()" class="hdr-act-btn" style="color:var(--bl);border-color:rgba(79,142,247,0.3);display:flex;align-items:center;gap:4px">${newsFetching?'<span class="si-spin"></span>':'⟳'} Refresh</button></div>`);
  h+=_renderSiteIntelCard("news");
  h+=_renderNewsToolbar({compact:false});
  h+=_renderNewsBody({compact:false});
  return h;
}

// ═══════════════════════════════════════════════════════════
// PREMIUM NEWSPAPER — Bloomberg / wire-desk edition (live tape only)
// ═══════════════════════════════════════════════════════════
function _paperIndexChip(tk, label){
  const d=fp(tk);
  const ch=liveChg(tk);
  const na=d.status==="unavailable"||ch==null;
  const cls=na?"paper-idx-flat":(ch>0?"paper-idx-up":(ch<0?"paper-idx-dn":"paper-idx-flat"));
  const sign=ch!=null&&ch>0?"+":"";
  const px=na?"—":d.p;
  const chg=na?"—":`${sign}${d.c}%`;
  return `<button type="button" class="paper-idx ${cls}" onclick="openA('${tk}')" title="${label||tk}">
    <span class="paper-idx-tk">${label||tk}</span>
    <span class="paper-idx-px">${px}</span>
    <span class="paper-idx-ch">${chg}</span>
  </button>`;
}
function _paperStoryRow(n,i,opts){
  opts=opts||{};
  const src=_escHtml(n.src||"Wire");
  const age=_newsRelTime(n.ts);
  const title=_escHtml(n.x||"");
  const desc=opts.lead?_escHtml((n.desc||"").slice(0,220)):_escHtml((n.desc||"").slice(0,110));
  const tg=_escHtml(n.tg||n.cat||"Markets");
  const link=n.link&&String(n.link).startsWith("http")?n.link:"";
  const open=link
    ?`onclick="window.open('${String(link).replace(/'/g,"\\'")}','_blank','noopener')"`
    :`onclick="nav('news')"`;
  if(opts.lead){
    return `<article class="paper-lead" ${open}>
      <div class="paper-kicker">${tg} · ${src} · ${age}</div>
      <h2 class="paper-lead-h">${title}</h2>
      ${desc?`<p class="paper-lead-d">${desc}${n.desc&&n.desc.length>220?"…":""}</p>`:""}
      <div class="paper-lead-meta">Open source ↗ · Research only</div>
    </article>`;
  }
  return `<article class="paper-story ${opts.compact?"paper-story-sm":""}" ${open}>
    <div class="paper-story-meta"><span>${tg}</span><span>${src}</span><span>${age}</span></div>
    <h3 class="paper-story-h">${title}</h3>
    ${!opts.compact&&desc?`<p class="paper-story-d">${desc}${n.desc&&n.desc.length>110?"…":""}</p>`:""}
  </article>`;
}
function _paperCol(title, items, empty){
  let h=`<section class="paper-col"><div class="paper-col-h">${_escHtml(title)}</div>`;
  if(!items.length)h+=`<div class="paper-empty">${_escHtml(empty||"No wire copy yet — sync feeds.")}</div>`;
  else items.forEach((n,i)=>{h+=_paperStoryRow(n,i,{compact:i>0});});
  h+=`</section>`;
  return h;
}
function renderNewspaper(){
  // Free users: gate with preview strip
  if(!_isPremium()){
    let h=`<div class="paper-edition paper-locked">
      <div class="paper-mast">
        <div class="paper-mast-vol">VOL. I · PREMIUM EDITION</div>
        <h1 class="paper-mast-title">The Dispatch</h1>
        <div class="paper-mast-sub">Custom newspaper · Bloomberg-style wire desk</div>
        <div class="paper-mast-date">${new Date().toLocaleDateString("en-GB",{weekday:"long",day:"numeric",month:"long",year:"numeric"})}</div>
      </div>
      <div class="paper-lock-card">
        <div class="paper-lock-kicker">★ PREMIUM</div>
        <div class="paper-lock-h">Your custom market newspaper</div>
        <p class="paper-lock-p">A broadsheet built from <strong>live free feeds</strong> + your book: lead story, multi-column wires (markets / macro / book / crypto-geo), index strip, and house brief. No invented prices.</p>
        <ul class="paper-lock-list">
          <li>Live index strip (SPY · VIX · DXY · oil · gold · BTC · FX)</li>
          <li>Lead + deck from ranked headlines</li>
          <li>Book-first column from watchlist &amp; portfolio</li>
          <li>Regime + free desk brief in the rail</li>
        </ul>
        <a href="/__auth/subscribe" class="paper-lock-cta">Subscribe — unlock Paper</a>
        <button type="button" class="paper-lock-sec" onclick="nav('news')">← Back to free Newsroom</button>
      </div>
    </div>`;
    return h;
  }

  const re=_computeRegimeEngine();
  const fg=typeof calcFearGreed==="function"?calcFearGreed():{label:"—",score:null};
  const book=_newsBookTickers();
  const ranked=[...NEWS].sort((a,b)=>_newsScore(b)-_newsScore(a)||(b.ts||0)-(a.ts||0));
  const lead=ranked[0]||null;
  const deck=ranked.slice(1,4);
  const byCat=(id,n)=>{
    const out=[];
    for(const item of ranked){
      if(lead&&item===lead)continue;
      if(deck.includes(item))continue;
      if(_newsInCategory(item,id))out.push(item);
      if(out.length>=n)break;
    }
    return out;
  };
  const mktStories=byCat("stocks",5);
  const macroStories=byCat("macro",5);
  const worldStories=ranked.filter(n=>{
    if(lead&&n===lead)return false;
    if(deck.includes(n))return false;
    return _newsIsWorld(n);
  }).slice(0,6);
  const cryptoStories=byCat("crypto",4);
  const bookStories=book.length
    ? ranked.filter(n=>_newsMatchesBook(n,book)).filter(n=>n!==lead&&!deck.includes(n)).slice(0,6)
    : [];
  const asOf=priceLastFetch?_fmtAsOf(priceLastFetch.getTime()):"—";
  const edVol=String(100+Math.min(899,liveSymbols.size||0));
  const dateLine=new Date().toLocaleDateString("en-GB",{weekday:"long",day:"numeric",month:"long",year:"numeric"});

  let h=`<div class="paper-edition" data-edition="premium">
    <header class="paper-mast">
      <div class="paper-mast-top">
        <span class="paper-badge">★ PREMIUM</span>
        <span class="paper-vol">VOL. ${edVol} · No. ${new Date().getDate()}</span>
        <span class="paper-asof">FEED AS OF ${asOf} · ${liveSymbols.size} SYNCED</span>
      </div>
      <h1 class="paper-mast-title">The Dispatch</h1>
      <div class="paper-mast-rule"></div>
      <div class="paper-mast-subrow">
        <span>Custom newspaper · wire desk</span>
        <span class="paper-mast-date">${dateLine}</span>
        <span>Research only · Not advice</span>
      </div>
      <div class="paper-acts">
        <button type="button" class="news-act news-act-gold" onclick="fetchLiveNews();fetchLivePrices();if(typeof _refreshView==='function')_refreshView();else renderMain();showToast('Edition refreshing…','var(--gd)')">⟳ Sync edition</button>
        <button type="button" class="news-act" onclick="nav('news')">List view</button>
        <button type="button" class="news-act" onclick="nav('brief')">Brief</button>
        <button type="button" class="news-act" onclick="_shareDeskSnapshot()">↗ Share desk</button>
        <button type="button" class="news-act" onclick="window.print()">⎙ Print</button>
      </div>
    </header>

    <nav class="paper-toc" aria-label="Edition sections">
      <a href="#paper-lead">Lead</a>
      <a href="#paper-us">US</a>
      <a href="#paper-global">Global</a>
      <a href="#paper-world">World</a>
      <a href="#paper-wires">Wires</a>
      <a href="#paper-book">Book</a>
      <a href="#paper-rail">Brief</a>
    </nav>

    <div class="paper-index" aria-label="Live US market strip">
      ${_paperIndexChip("SPY","SPY")}
      ${_paperIndexChip("QQQ","QQQ")}
      ${_paperIndexChip("IWM","IWM")}
      ${_paperIndexChip("VIX","VIX")}
      ${_paperIndexChip("DXY","DXY")}
      ${_paperIndexChip("WTI","WTI")}
      ${_paperIndexChip("XAU","XAU")}
      ${_paperIndexChip("BTC","BTC")}
      ${_paperIndexChip("EURUSD","EUR")}
      ${_paperIndexChip("TNX","10Y")}
    </div>
    <div class="paper-index paper-index-global" aria-label="Live global index strip">
      ${_paperIndexChip("FTSE","FTSE")}
      ${_paperIndexChip("DAX","DAX")}
      ${_paperIndexChip("CAC","CAC")}
      ${_paperIndexChip("N225","N225")}
      ${_paperIndexChip("NSEI","NIFTY")}
      ${_paperIndexChip("HSI","HSI")}
      ${_paperIndexChip("ASX200","ASX")}
      ${_paperIndexChip("KOSPI","KOSPI")}
    </div>

    <div class="paper-regime">
      <span class="paper-regime-lbl">REGIME</span>
      <strong style="color:${re.col||"var(--gd)"}">${_escHtml(re.label)}</strong>
      <span class="paper-regime-sc">${re.score}/100</span>
      <span class="paper-regime-sep">·</span>
      <span>F&amp;G ${fg.score!=null?fg.score:"—"} ${_escHtml(fg.label||"")}</span>
      <span class="paper-regime-sep">·</span>
      <span>${book.length} book symbols</span>
      <span class="paper-regime-sep">·</span>
      <span>${NEWS.length} headlines on wire</span>
    </div>

    ${(()=>{
      // Live conviction movers (feed-synced only)
      const movers=[...A].filter(a=>liveChg(a.tk)!=null)
        .map(a=>({tk:a.tk,nm:a.nm,ch:liveChg(a.tk),d:fp(a.tk)}))
        .sort((a,b)=>Math.abs(b.ch)-Math.abs(a.ch)).slice(0,8);
      if(!movers.length)return "";
      return `<div class="paper-movers" id="paper-us">
        <div class="paper-movers-h">Session movers · live desk names</div>
        <div class="paper-movers-row">${movers.map(m=>{
          const cls=m.ch>0?"px-up":m.ch<0?"px-dn":"px-flat";
          const sign=m.ch>0?"+":"";
          return `<button type="button" class="paper-mover" onclick="openA('${m.tk}')"><span class="paper-mover-tk">${m.tk}</span><span class="paper-mover-px">${m.d.p}</span><span class="${cls}">${sign}${Number(m.ch).toFixed(2)}%</span></button>`;
        }).join("")}</div>
      </div>`;
    })()}

    <div class="paper-grid">
      <div class="paper-main">
        <div id="paper-lead">${lead?_paperStoryRow(lead,0,{lead:true}):`<div class="paper-empty paper-empty-lead">No headlines yet · <button type="button" class="news-act" onclick="fetchLiveNews()">⟳ Sync news</button></div>`}</div>
        ${deck.length?`<div class="paper-deck">${deck.map((n,i)=>_paperStoryRow(n,i,{compact:false})).join("")}</div>`:""}
        <div class="paper-cols" id="paper-wires">
          <div id="paper-book">${_paperCol(book.length?"Your book":"Book (empty)", bookStories, book.length?"No book headlines yet":"Star names or add portfolio lots")}</div>
          <div id="paper-world">${_paperCol("World", worldStories, "No world wire yet — sync feeds")}</div>
          ${_paperCol("Markets", mktStories, "No equity wire yet")}
          ${_paperCol("Macro & policy", macroStories, "No macro wire yet")}
          ${_paperCol("Crypto", cryptoStories, "No crypto wire yet")}
        </div>
      </div>
      <aside class="paper-rail" id="paper-rail">
        <div class="paper-rail-card">
          <div class="paper-rail-h">House brief</div>
          ${_brief?`
            <div class="paper-rail-brief-view">${_escHtml(_brief.houseView||"Neutral")}</div>
            <div class="paper-rail-brief-h">${_escHtml((_brief.headline||"").slice(0,90))}</div>
            <p class="paper-rail-brief-s">${_escHtml(String(_brief.summary||"").slice(0,200))}${(_brief.summary||"").length>200?"…":""}</p>
            <button type="button" class="news-act news-act-gold" onclick="nav('brief')">Open brief →</button>
          `:`
            <p class="paper-rail-muted">Generate today's desk brief from live tape.</p>
            <button type="button" class="news-act news-act-gold" onclick="nav('brief');loadDispatchBrief(true)">Generate brief</button>
          `}
        </div>
        <div class="paper-rail-card" id="paper-global">
          <div class="paper-rail-h">Global board</div>
          ${["FTSE","DAX","CAC","N225","NSEI","HSI"].map(tk=>{
            const d=fp(tk);const ch=liveChg(tk);
            const na=d.status==="unavailable"||ch==null;
            const cls=na?"px-flat":(ch>0?"px-up":(ch<0?"px-dn":"px-flat"));
            const sign=ch!=null&&ch>0?"+":"";
            return `<button type="button" class="paper-book-row" onclick="openA('${tk}')"><span>${tk}</span><span class="${cls}">${na?"—":d.p}</span><span class="${cls}">${na?"—":sign+d.c+"%"}</span></button>`;
          }).join("")}
        </div>
        <div class="paper-rail-card">
          <div class="paper-rail-h">Overweight</div>
          ${(re.overweight||[]).slice(0,4).map(x=>`<div class="paper-rail-li paper-ow">+ ${_escHtml(x)}</div>`).join("")||`<div class="paper-rail-muted">—</div>`}
          <div class="paper-rail-h" style="margin-top:12px">Underweight</div>
          ${(re.underweight||[]).slice(0,4).map(x=>`<div class="paper-rail-li paper-uw">− ${_escHtml(x)}</div>`).join("")||`<div class="paper-rail-muted">—</div>`}
        </div>
        <div class="paper-rail-card">
          <div class="paper-rail-h">Book marks</div>
          ${book.length?book.slice(0,8).map(tk=>{
            const d=fp(tk);const ch=liveChg(tk);
            const na=d.status==="unavailable"||ch==null;
            const cls=na?"px-flat":(ch>0?"px-up":(ch<0?"px-dn":"px-flat"));
            const sign=ch!=null&&ch>0?"+":"";
            return `<button type="button" class="paper-book-row" onclick="openA('${tk}')"><span>${tk}</span><span class="${cls}">${na?"—":d.p}</span><span class="${cls}">${na?"—":sign+d.c+"%"}</span></button>`;
          }).join(""):`<div class="paper-rail-muted">Empty book · <button type="button" class="news-act" onclick="nav('watch')">Watchlist</button></div>`}
        </div>
        <div class="paper-rail-card paper-rail-foot">
          <div class="paper-rail-h">Edition notes</div>
          <p class="paper-rail-muted">Bloomberg-style custom paper for premium desks. Headlines: RSS + Finnhub. Prices: Yahoo / CoinGecko delayed free feeds — never seed prints. Research only.</p>
        </div>
      </aside>
    </div>
  </div>`;
  return h;
}

// ═══════════════════════════════════════════════════════════
// SECTOR ROTATION TRACKER
// ═══════════════════════════════════════════════════════════

const SECTORS_DEF = [
  {name:'Technology',    etf:'XLK',  col:'#4F8EF7', tks:['AAPL','NVDA','MSFT','AVGO','AMD','INTC','QCOM','NOW','AMAT','LRCX']},
  {name:'Communication', etf:'XLC',  col:'#9B6DFF', tks:['GOOGL','META','NFLX','DIS','T','VZ']},
  {name:'Consumer Disc', etf:'XLY',  col:'#00D4F5', tks:['AMZN','TSLA','MCD','NKE','SBUX','ABNB','DASH']},
  {name:'Financials',    etf:'XLF',  col:'#F5A623', tks:['JPM','GS','BAC','MS','WFC','C','BLK','SCHW']},
  {name:'Healthcare',    etf:'XLV',  col:'#00C896', tks:['UNH','LLY','JNJ','ABBV','MRK','ABT','AMGN','REGN']},
  {name:'Energy',        etf:'XLE',  col:'#FF4757', tks:['XOM','CVX','COP','EOG','SLB']},
  {name:'Industrials',   etf:'XLI',  col:'#fbbf24', tks:['HON','RTX','CAT','UPS','DE','BA']},
  {name:'Consumer Stap', etf:'XLP',  col:'#86efac', tks:['PG','KO','PEP','WMT','COST','PM']},
  {name:'Materials',     etf:'XLB',  col:'#f97316', tks:['COPPER','XAU','SLV']},
  {name:'Utilities',     etf:'XLU',  col:'#a78bfa', tks:['NEE','DUK','SO']},
  {name:'Real Estate',   etf:'XLRE', col:'#fb7185', tks:['PLD','AMT','EQIX','SPG','O']},
];

// Approximate S&P 500 sector weights (for treemap sizing)
const SECTOR_WEIGHTS = { XLK:31, XLC:9, XLY:10, XLF:13, XLV:12, XLE:4, XLI:8, XLP:6, XLB:2, XLU:2, XLRE:2 };

// Sector rotation cycle context — which macro regime favors each sector
const ROTATION_CONTEXT = {
  'Technology':    {cycle:'Late Cycle / Early Recovery', note:'Benefits from falling rates, AI capex, digital transformation'},
  'Communication': {cycle:'Early-Mid Cycle', note:'Ad revenue tied to consumer spending. Rate-sensitive (long duration)'},
  'Consumer Disc': {cycle:'Early Cycle', note:'Consumer confidence and wage growth are key. Cyclical — first in, first out'},
  'Financials':    {cycle:'Early-Mid Cycle / Rising Rates', note:'NII expands with rate hikes. Benefits from steepening yield curve'},
  'Healthcare':    {cycle:'Defensive — All Cycles', note:'Non-cyclical demand. Outperforms in recessions and late-cycle slowdowns'},
  'Energy':        {cycle:'Mid-Late Cycle / Inflation', note:'Commodity prices driven by supply/demand and geopolitics. Stagflation hedge'},
  'Industrials':   {cycle:'Mid Cycle', note:'Tied to manufacturing PMI and infrastructure spending. Capital goods demand'},
  'Consumer Stap': {cycle:'Defensive — Recession', note:'Pricing power and non-discretionary demand. Safe haven in downturns'},
  'Materials':     {cycle:'Early-Mid Cycle', note:'Commodity demand from infrastructure and construction. China sensitivity high'},
  'Utilities':     {cycle:'Defensive — High Rates End', note:'Bond proxies. Outperform when rates fall. AI data centre power demand emerging'},
  'Real Estate':   {cycle:'Defensive / Rate-Sensitive', note:'Rate cuts are a major tailwind. Commercial real estate headwinds persistent'},
};

let _sectorData = {};
let _sectorLoading = false;
let _sectorTimeframe = '1d';
let _sectorView = 'heatmap'; // 'heatmap' | 'table' | 'rotation' | 'relative'
let _sectorSel = null;
let _sectorError = null;
let _sectorErrorAt = null;
let _sectorFetchedAt = null;
const SECTOR_RETRY_COOLDOWN = 60 * 1000;

function _sectorTfKey(tf) { return tf === '1d' ? 'day' : tf; }

function _sectorPct(etf, tf) {
  const d = _sectorData[etf];
  if (!d) return null;
  return d[_sectorTfKey(tf)];
}

function _sectorRelSpy(etf, tf) {
  const s = _sectorPct(etf, tf);
  const spy = _sectorPct('SPY', tf);
  if (s == null || spy == null) return null;
  return s - spy;
}

function _sectorFmtPct(v, bold) {
  if (v == null) return '—';
  const col = v > 0 ? 'var(--gn)' : v < 0 ? 'var(--rd)' : 'var(--t3)';
  const w = bold ? 'font-weight:900' : 'font-weight:700';
  return `<span style="color:${col};${w}">${v > 0 ? '+' : ''}${(+v).toFixed(2)}%</span>`;
}

function _sectorPick(tk) { if (IS_DESKTOP()) termSelect(tk); else openA(tk); }

function _sectorOpen(etf) {
  _sectorSel = _sectorSel === etf ? null : etf;
  _refreshView();
}

function _sectorRotationSignal() {
  const cyclical = ['XLY', 'XLF', 'XLI', 'XLK', 'XLC', 'XLE'];
  const defensive = ['XLV', 'XLP', 'XLU', 'XLRE'];
  let cSum = 0, cN = 0, dSum = 0, dN = 0;
  cyclical.forEach(e => { const p = _sectorPct(e, 'month'); if (p != null) { cSum += p; cN++; } });
  defensive.forEach(e => { const p = _sectorPct(e, 'month'); if (p != null) { dSum += p; dN++; } });
  if (!cN || !dN) return { label: 'Awaiting Data', col: 'var(--t3)', desc: 'Load sector data to see rotation signal' };
  const spread = (cSum / cN) - (dSum / dN);
  if (spread > 1.2) return { label: 'Risk-On Rotation', col: 'var(--gn)', desc: `Cyclicals beating defensives by ${spread.toFixed(1)}% (1M) — growth & rate-sensitive sectors leading` };
  if (spread < -1.2) return { label: 'Defensive Rotation', col: 'var(--rd)', desc: `Defensives beating cyclicals by ${Math.abs(spread).toFixed(1)}% (1M) — safety & yield favoured` };
  return { label: 'Mixed / Neutral', col: 'var(--gd)', desc: 'No dominant rotation theme — stock-picking environment' };
}

function _sectorMomentumScore(etf) {
  let score = 0, n = 0;
  ['day', 'week', 'month', 'ytd'].forEach(k => {
    const rel = _sectorRelSpy(etf, k === 'day' ? '1d' : k);
    if (rel != null) { score += rel; n++; }
  });
  return n ? score / n : null;
}

function _sectorIsLoaded() {
  const etfs = SECTORS_DEF.map(s => s.etf);
  const withDay = etfs.filter(e => _sectorData[e]?.day != null).length;
  return withDay >= Math.ceil(etfs.length * 0.6);
}

function _sectorNeedsFetch() {
  if (_sectorLoading) return false;
  // Back off after a failure. fetchSectorData() re-renders on the way out, so
  // without this an unavailable feed retries as fast as the event loop allows.
  if (_sectorError && _sectorErrorAt && Date.now() - _sectorErrorAt < SECTOR_RETRY_COOLDOWN) return false;
  if (!_sectorIsLoaded()) return true;
  if (!_sectorFetchedAt || Date.now() - _sectorFetchedAt > 15 * 60 * 1000) return true;
  const etfs = SECTORS_DEF.map(s => s.etf);
  const withMonth = etfs.filter(e => _sectorData[e]?.month != null).length;
  return withMonth < Math.ceil(etfs.length * 0.6);
}

function _sectorChartPct(payload) {
  const closes = payload?.chart?.result?.[0]?.indicators?.quote?.[0]?.close?.filter(v => v != null);
  if (!closes || closes.length < 2) return null;
  return parseFloat((((closes[closes.length - 1] - closes[0]) / closes[0]) * 100).toFixed(2));
}

async function _sectorFetchCharts(syms, tf) {
  const batchSize = 4;
  for (let i = 0; i < syms.length; i += batchSize) {
    const batch = syms.slice(i, i + batchSize);
    const results = await Promise.allSettled(
      batch.map(sym =>
        chartFetch(`/api/yahoo-chart?symbol=${sym}&range=${tf.range}&interval=${tf.interval}`, { signal: AbortSignal.timeout(12000) })
          .then(r => r.ok ? r.json() : null)
      )
    );
    results.forEach((r, j) => {
      if (r.status !== 'fulfilled' || !r.value) return;
      const pct = _sectorChartPct(r.value);
      if (pct == null) return;
      const sym = batch[j];
      if (!_sectorData[sym]) _sectorData[sym] = {};
      _sectorData[sym][tf.key] = pct;
    });
  }
}

async function _fetchSectorHoldings() {
  const need = [...new Set(SECTORS_DEF.flatMap(s => s.tks))].filter(tk => !liveSymbols.has(tk));
  if (!need.length) return;
  for (let i = 0; i < need.length; i += 20) {
    const batch = need.slice(i, i + 20);
    const yhKeys = batch.map(tk => YAHOO_SYMBOLS[tk] || tk);
    try {
      const res = await fetch('/api/yahoo-quote?symbols=' + yhKeys.join(','), { signal: AbortSignal.timeout(12000) });
      if (!res.ok) continue;
      const data = await res.json();
      batch.forEach((tk, j) => {
        const yh = yhKeys[j];
        const q = data[yh] || data[tk];
        if (!q) return;
        _applyLiveQuote(tk, { p: q.p, c: q.c, prev: q.prev }, "yahoo");
      });
    } catch (e) { /* skip chunk */ }
  }
}

async function fetchSectorData() {
  if (_sectorLoading) return;
  _sectorLoading = true;
  _sectorError = null;
  _refreshView();

  try {
    const allSyms = ['SPY', ...SECTORS_DEF.map(s => s.etf)];
    const res = await fetch('/api/yahoo-quote?symbols=' + allSyms.join(','), { signal: AbortSignal.timeout(15000) });
    if (!res.ok) throw new Error('Quote fetch failed');
    const data = await res.json();
    let quoteHits = 0;
    allSyms.forEach(sym => {
      const q = data[sym];
      if (q && _applyLiveQuote(sym, { p: q.p, c: q.c, prev: q.prev }, "yahoo")) {
        quoteHits++;
        if (!_sectorData[sym]) _sectorData[sym] = {};
        _sectorData[sym].day = q.c;
        _sectorData[sym].price = q.p;
        _sectorData[sym].prev = q.prev;
      }
    });
    if (quoteHits < 4) throw new Error('Insufficient sector quote data');

    const timeframes = [
      { key: 'week', range: '5d', interval: '1d' },
      { key: 'month', range: '1mo', interval: '1d' },
      { key: 'ytd', range: 'ytd', interval: '1wk' },
    ];
    for (const tf of timeframes) {
      await _sectorFetchCharts(allSyms, tf);
    }

    await _fetchSectorHoldings();
    _sectorFetchedAt = Date.now();
    _sectorError = null;
    _sectorErrorAt = null;
    renderTape();
  } catch (e) {
    _sectorError = e?.message || 'Failed to load sector data';
    _sectorErrorAt = Date.now();
  }

  _sectorLoading = false;
  const strip = document.querySelector(".neural-strip");
  if (strip) strip.outerHTML = _renderNeuralSessionStrip();
  _refreshView();
}

function _renderDashboardSectorPulse() {
  if (_sectorIsLoaded()) {
    const sig = _sectorRotationSignal();
    const sorted = [...SECTORS_DEF]
      .map(s => ({ s, pct: _sectorPct(s.etf, "1d") }))
      .filter(x => x.pct != null && isFinite(x.pct))
      .sort((a, b) => b.pct - a.pct);
    let h = `<div class="sec-hdr-row"><div class="sec-label-v2">S&P Sector Pulse</div><div class="sec-hdr-meta"><span style="font-family:var(--mn);font-size:8px;color:${sig.col};font-weight:700">${sig.label}</span><span class="sec-hdr-link" onclick="nav('sectors')">ROTATION →</span></div></div>`;
    h += `<div class="sector-dash-grid">`;
    sorted.forEach(({ s, pct }) => {
      const col = pct > 0 ? "var(--gn)" : pct < 0 ? "var(--rd)" : "var(--t3)";
      h += `<div class="sector-dash-tile gc gc-a" onclick="nav('sectors')" style="border-top:2px solid ${s.col}">
        <div class="sector-dash-name">${s.name}</div>
        <div class="sector-dash-etf">${s.etf}</div>
        <div class="sector-dash-pct" style="color:${col}">${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%</div>
      </div>`;
    });
    h += `</div>`;
    return h;
  }
  const sectors = [
    { nm: "Equities", tks: ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "JPM", "GS", "AMD", "XOM", "AVGO"], cl: "var(--bl)" },
    { nm: "Crypto", tks: ["BTC", "ETH", "SOL", "XRP"], cl: "var(--pu)" },
    { nm: "Commodities", tks: ["XAU", "WTI", "SLV", "NG"], cl: "var(--gd)" },
    { nm: "FX", tks: ["EURUSD", "GBPUSD", "USDJPY", "DXY"], cl: "var(--cy)" },
  ];
  let h = `<div class="sec-hdr-row"><div class="sec-label">Sector Pulse</div><span class="sec-hdr-link" onclick="nav('sectors')">S&P ROTATION →</span></div>`;
  h += `<div class="gr" style="grid-template-columns:1fr 1fr">`;
  sectors.forEach(s => {
    // Live day % only — never average unsynced names as 0%
    const vals = s.tks.map(tk => liveChg(tk)).filter(c => c != null);
    const nLive = vals.length;
    const avg = nLive ? vals.reduce((a, b) => a + b, 0) / nLive : null;
    const avgCol = avg == null ? "var(--t3)" : avg >= 0 ? "var(--gn)" : "var(--rd)";
    const avgLbl = avg == null ? "—" : `${avg >= 0 ? "+" : ""}${avg.toFixed(2)}%`;
    h += `<div class="gc gc-a" onclick="nav('sectors')" style="border-top:2px solid ${s.cl}">
      <div style="font-size:11px;font-weight:700;color:${s.cl};margin-bottom:4px">${s.nm}</div>
      <div style="font-family:var(--mn);font-weight:800;font-size:16px;color:${avgCol}">${avgLbl}</div>
      <div style="font-size:10px;color:var(--t3);margin-top:3px;font-family:var(--mn)">${nLive}/${s.tks.length} live</div>
    </div>`;
  });
  h += `</div>`;
  return h;
}

function renderSectorSummary() {
  const sig = _sectorRotationSignal();
  const spy = _sectorData.SPY || {};
  const ranked = SECTORS_DEF
    .map(s => ({ s, pct: _sectorPct(s.etf, '1d') }))
    .filter(x => x.pct != null && isFinite(x.pct))
    .sort((a, b) => b.pct - a.pct);
  const best = ranked[0]?.s;
  const worst = ranked.length ? ranked[ranked.length - 1].s : null;
  const updated = _sectorFetchedAt ? new Date(_sectorFetchedAt).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) : '—';

  return `<div class="sector-summary">
    <div class="sector-summary-signal" style="border-color:${sig.col}40;background:linear-gradient(135deg,${sig.col}12,transparent)">
      <div class="sector-summary-label" style="color:${sig.col}">${sig.label}</div>
      <div class="sector-summary-desc">${sig.desc}</div>
    </div>
    <div class="sector-summary-stat">
      <div class="sector-summary-k">S&P 500 (SPY)</div>
      <div class="sector-summary-v">${_sectorFmtPct(spy.day, true)}</div>
      <div class="sector-summary-s">1M ${_sectorFmtPct(spy.month)}</div>
    </div>
    <div class="sector-summary-stat">
      <div class="sector-summary-k">Leader Today</div>
      <div class="sector-summary-v" style="color:var(--gn)">${best?.name || '—'}</div>
      <div class="sector-summary-s">${best ? _sectorFmtPct(_sectorPct(best.etf, '1d')) : ''}</div>
    </div>
    <div class="sector-summary-stat">
      <div class="sector-summary-k">Laggard Today</div>
      <div class="sector-summary-v" style="color:var(--rd)">${worst?.name || '—'}</div>
      <div class="sector-summary-s">${worst ? _sectorFmtPct(_sectorPct(worst.etf, '1d')) : ''}</div>
    </div>
    <div class="sector-summary-stat">
      <div class="sector-summary-k">Updated</div>
      <div class="sector-summary-v" style="font-size:14px">${updated}</div>
      <div class="sector-summary-s">11 sector ETFs</div>
    </div>
  </div>`;
}

function renderSectorDrillDown(etf) {
  const s = SECTORS_DEF.find(x => x.etf === etf);
  if (!s) return '';
  const d = _sectorData[etf] || {};
  const ctx = ROTATION_CONTEXT[s.name];
  const mom = _sectorMomentumScore(etf);
  const momCol = mom == null ? 'var(--t3)' : mom >= 0 ? 'var(--gn)' : 'var(--rd)';

  let h = `<div class="sector-drill">
    <div class="sector-drill-hdr">
      <div style="display:flex;align-items:center;gap:10px;flex:1">
        <div style="width:12px;height:12px;border-radius:50%;background:${s.col}"></div>
        <div>
          <div style="font-family:var(--sn);font-size:17px;font-weight:800">${s.name}</div>
          <div style="font-family:var(--mn);font-size:10px;color:var(--t3)">${s.etf} · ${ctx?.cycle || 'Sector ETF'}</div>
        </div>
      </div>
      <button onclick="_sectorOpen('${etf}')" style="background:var(--b2);border:1px solid var(--gb);color:var(--t2);border-radius:6px;padding:6px 10px;font-family:var(--mn);font-size:10px;cursor:pointer">✕ Close</button>
    </div>
    <div class="sector-drill-grid">
      <div><span class="sector-drill-k">Today</span>${_sectorFmtPct(d.day, true)}</div>
      <div><span class="sector-drill-k">1 Week</span>${_sectorFmtPct(d.week, true)}</div>
      <div><span class="sector-drill-k">1 Month</span>${_sectorFmtPct(d.month, true)}</div>
      <div><span class="sector-drill-k">YTD</span>${_sectorFmtPct(d.ytd, true)}</div>
      <div><span class="sector-drill-k">vs SPY (1M)</span>${_sectorFmtPct(_sectorRelSpy(etf, 'month'), true)}</div>
      <div><span class="sector-drill-k">Momentum</span><span style="color:${momCol};font-family:var(--mn);font-weight:900">${mom != null ? (mom >= 0 ? '+' : '') + mom.toFixed(2) + '%' : '—'}</span></div>
    </div>
    ${d.price ? `<div style="font-family:var(--mn);font-size:11px;color:var(--t2);margin-bottom:10px">ETF Price: <strong style="color:var(--tx)">$${d.price.toFixed(2)}</strong></div>` : ''}
    ${ctx ? `<div style="font-family:var(--sn);font-size:12px;color:var(--t2);line-height:1.6;margin-bottom:12px;padding:10px 12px;background:var(--b1);border-radius:8px;border-left:3px solid ${s.col}">${ctx.note}</div>` : ''}
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px">
      <button onclick="_sectorPick('${etf}')" style="background:var(--gd);color:var(--bg);border:none;border-radius:8px;padding:9px 16px;font-family:var(--sn);font-size:12px;font-weight:700;cursor:pointer">Analyze ${etf}</button>
    </div>`;

  const tickers = s.tks.filter(tk => liveChg(tk) != null).sort((a, b) => (liveChg(b) ?? -Infinity) - (liveChg(a) ?? -Infinity));
  if (tickers.length) {
    h += `<div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.12em;margin-bottom:8px">TOP HOLDINGS — LIVE</div><div style="display:flex;flex-wrap:wrap;gap:6px">`;
    tickers.slice(0, 8).forEach(tk => {
      const ch = liveChg(tk);
      if (ch == null) return;
      h += `<button onclick="_sectorPick('${tk}')" class="sector-stock-chip" style="border-color:${ch >= 0 ? 'rgba(0,200,150,0.25)' : 'rgba(255,71,87,0.25)'};background:${ch >= 0 ? 'var(--gnG)' : 'var(--rdG)'};color:${ch >= 0 ? 'var(--gn)' : 'var(--rd)'}">${tk} ${ch >= 0 ? '+' : ''}${ch.toFixed(2)}%</button>`;
    });
    h += `</div>`;
  }
  h += `</div>`;
  return h;
}

function renderSectorTracker() {
  const loaded = _sectorIsLoaded();
  const tabs = [['heatmap','🗺 Heatmap'],['relative','📈 vs SPY'],['table','📊 Performance'],['rotation','🔄 Cycle']];

  let h = _renderPgHdr("Sector Rotation", "11 S&P 500 sectors · SPY benchmark · live rotation signals",
    `<button onclick="fetchSectorData()" class="hdr-act-btn" style="color:var(--bl);border-color:rgba(79,142,247,0.3)">${_sectorLoading ? '⟳ Loading…' : '⟳ Refresh'}</button>`);
  h += _renderSiteIntelCard("sectors");

  h += `<div class="tabs" style="margin-bottom:12px">${tabs.map(([id, lb]) => `<button class="${_sectorView === id ? 'on' : ''}" onclick="_sectorView='${id}';_refreshView()">${lb}</button>`).join('')}</div>`;

  if (_sectorLoading && !loaded) {
    h += `<div style="padding:40px;text-align:center"><div style="width:16px;height:16px;border:2px solid var(--bl);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 14px"></div><div style="font-family:var(--sn);font-size:13px;color:var(--t2)">Fetching all 11 sector ETFs + SPY benchmark…</div></div>`;
    return h;
  }

  if (_sectorError && !loaded) {
    h += `<div class="gc" style="padding:32px;text-align:center"><div style="font-family:var(--sn);font-size:14px;color:var(--rd);margin-bottom:12px">${_sectorError}</div><button onclick="fetchSectorData()" style="background:var(--gd);color:var(--bg);border:none;border-radius:8px;padding:12px 28px;font-family:var(--sn);font-size:14px;font-weight:700;cursor:pointer">Retry</button></div>`;
    return h;
  }

  if (!loaded) {
    h += `<div class="gc" style="padding:32px;text-align:center"><div style="font-family:var(--sn);font-size:14px;color:var(--t2);margin-bottom:8px">Professional sector rotation tracker</div><div style="font-family:var(--sn);font-size:12px;color:var(--t3);margin-bottom:16px;line-height:1.6">Live ETF performance · relative strength vs SPY · cyclical/defensive rotation signal · drill into any sector</div><button onclick="fetchSectorData()" style="background:var(--gd);color:var(--bg);border:none;border-radius:8px;padding:12px 28px;font-family:var(--sn);font-size:14px;font-weight:700;cursor:pointer">Load Sector Data</button></div>`;
    return h;
  }

  if (_sectorError && loaded) {
    h += `<div class="gc" style="padding:10px 14px;margin-bottom:10px;border-left:3px solid var(--rd);font-size:11px;color:var(--t2)">Partial refresh failed — showing cached data. <span style="color:var(--bl);cursor:pointer;font-weight:700" onclick="fetchSectorData()">Retry</span></div>`;
  }
  h += renderSectorSummary();
  if (_sectorSel) h += renderSectorDrillDown(_sectorSel);

  if (_sectorView === 'heatmap') h += renderSectorHeatmap();
  else if (_sectorView === 'relative') h += renderSectorRelative();
  else if (_sectorView === 'table') h += renderSectorTable2();
  else h += renderSectorRotationCycle();

  return h;
}

function renderSectorHeatmap() {
  const tf = _sectorTimeframe;
  const tfLabels = { '1d': 'Today', 'week': '1 Week', 'month': '1 Month', 'ytd': 'YTD' };
  // Rank only sectors with real TF % — missing must not sort as 0
  const sorted = SECTORS_DEF
    .map(s => ({ s, pct: _sectorPct(s.etf, tf) }))
    .filter(x => x.pct != null && isFinite(x.pct))
    .sort((a, b) => b.pct - a.pct);

  let h = `<div class="sector-tf-bar">
    ${[['1d', 'Day'], ['week', 'Week'], ['month', 'Month'], ['ytd', 'YTD']].map(([id, lb]) => `<button class="sector-tf-btn${_sectorTimeframe === id ? ' on' : ''}" onclick="_sectorTimeframe='${id}';_refreshView()">${lb}</button>`).join('')}
  </div>`;

  h += `<div class="sector-treemap-hdr">
    <span>SECTOR HEATMAP — ${tfLabels[tf]?.toUpperCase()}</span>
    <span style="color:var(--t3)">Size = S&P weight · Click to drill down</span>
  </div>`;
  h += `<div class="sector-treemap">`;

  sorted.forEach(({ s, pct }, idx) => {
    const rel = _sectorRelSpy(s.etf, tf);
    const isUp = pct > 0;
    const isFlat = pct === 0;
    const intensity = Math.min(Math.abs(pct) / 2.5, 1);
    const bg = isFlat ? 'rgba(255,255,255,0.04)' : isUp ? `rgba(0,200,150,${0.12 + intensity * 0.38})` : `rgba(255,71,87,${0.12 + intensity * 0.38})`;
    const col = isFlat ? 'var(--t3)' : isUp ? 'var(--gn)' : 'var(--rd)';
    const wt = SECTOR_WEIGHTS[s.etf] || 5;
    const sel = _sectorSel === s.etf;

    h += `<div class="sector-tile${sel ? ' sector-tile-sel' : ''}" onclick="_sectorOpen('${s.etf}')" style="flex:${wt};min-width:${wt > 10 ? '28%' : '18%'};background:${bg};border-color:${sel ? col : col + '35'}">
      <div class="sector-tile-top">
        <div class="sector-tile-dot" style="background:${s.col}"></div>
        <span class="sector-tile-rank" style="color:${col}">#${idx + 1}</span>
      </div>
      <div class="sector-tile-name">${s.name}</div>
      <div class="sector-tile-etf">${s.etf} · ${wt}% S&P</div>
      <div class="sector-tile-pct" style="color:${col}">${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%</div>
      ${rel != null ? `<div class="sector-tile-rel" style="color:${rel >= 0 ? 'var(--gn)' : 'var(--rd)'}">vs SPY ${rel >= 0 ? '+' : ''}${rel.toFixed(2)}%</div>` : ''}
    </div>`;
  });
  h += `</div>`;

  h += `<div style="margin-top:16px"><div class="sector-treemap-hdr"><span>SECTOR STOCK MOVERS</span><span style="color:var(--t3)">Top holdings today · live only</span></div>`;
  // `sorted` holds { s, pct } pairs — destructure, or every s.* below reads
  // off the wrapper and s.tks is undefined (this threw and blanked the page).
  sorted.slice(0, 5).forEach(({ s }) => {
    const ranked = (s.tks || []).map(tk => ({ tk, c: liveChg(tk) })).filter(x => x.c != null).sort((a, b) => b.c - a.c);
    if (!ranked.length) return;
    const top3 = ranked.slice(0, 3);
    const bot2 = ranked.slice(-2).reverse();
    h += `<div class="sector-mover-row">
      <div class="sector-mover-hdr" onclick="_sectorOpen('${s.etf}')" style="cursor:pointer">
        <div style="width:8px;height:8px;border-radius:50%;background:${s.col}"></div>
        <span style="font-family:var(--sn);font-size:13px;font-weight:700">${s.name}</span>
        <span style="margin-left:auto">${_sectorFmtPct(_sectorPct(s.etf, '1d'))}</span>
      </div>
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        ${top3.map(x => `<button onclick="_sectorPick('${x.tk}')" class="sector-stock-chip" style="border-color:rgba(0,200,150,0.25);background:var(--gnG);color:var(--gn)">${x.tk} ${x.c >= 0 ? '+' : ''}${x.c.toFixed(2)}%</button>`).join('')}
        ${bot2.length && bot2.some(b => !top3.find(t => t.tk === b.tk)) ? `<span style="font-family:var(--mn);font-size:10px;color:var(--t3);align-self:center">│</span>` : ""}
        ${bot2.filter(b => !top3.find(t => t.tk === b.tk)).map(x => `<button onclick="_sectorPick('${x.tk}')" class="sector-stock-chip" style="border-color:rgba(255,71,87,0.25);background:var(--rdG);color:var(--rd)">${x.tk} ${x.c >= 0 ? '+' : ''}${x.c.toFixed(2)}%</button>`).join('')}
      </div>
    </div>`;
  });
  h += `</div>`;
  return h;
}

function renderSectorRelative() {
  const tf = _sectorTimeframe;
  const tfLabels = { '1d': 'Today', 'week': '1 Week', 'month': '1 Month', 'ytd': 'YTD' };
  const sorted = SECTORS_DEF
    .map(s => ({ s, rel: _sectorRelSpy(s.etf, tf) }))
    .filter(x => x.rel != null && isFinite(x.rel))
    .sort((a, b) => b.rel - a.rel)
    .map(x => x.s);
  const spyPct = _sectorPct('SPY', tf);

  let h = `<div class="sector-tf-bar">
    ${[['1d', 'Day'], ['week', 'Week'], ['month', 'Month'], ['ytd', 'YTD']].map(([id, lb]) => `<button class="sector-tf-btn${_sectorTimeframe === id ? ' on' : ''}" onclick="_sectorTimeframe='${id}';_refreshView()">${lb}</button>`).join('')}
  </div>`;
  h += `<div class="gc" style="padding:12px 14px;margin-bottom:12px;border-left:3px solid var(--bl)">
    <div style="font-family:var(--mn);font-size:9px;color:var(--bl);letter-spacing:0.12em;margin-bottom:4px">BENCHMARK</div>
    <div style="display:flex;align-items:baseline;gap:10px"><span style="font-family:var(--sn);font-size:15px;font-weight:800">SPY</span>${_sectorFmtPct(spyPct, true)}<span style="font-family:var(--sn);font-size:11px;color:var(--t3)">S&P 500 · ${tfLabels[tf]}</span></div>
  </div>`;
  h += `<div class="sector-treemap-hdr"><span>RELATIVE STRENGTH vs SPY</span><span style="color:var(--t3)">${tfLabels[tf]}</span></div>`;

  sorted.forEach(s => {
    const rel = _sectorRelSpy(s.etf, tf);
    const abs = _sectorPct(s.etf, tf);
    if (rel == null) return;
    const isUp = rel >= 0;
    const barW = Math.min(Math.abs(rel) * 12, 100);
    const col = isUp ? 'var(--gn)' : 'var(--rd)';
    h += `<div class="sector-rs-row" onclick="_sectorOpen('${s.etf}')" style="cursor:pointer">
      <div class="sector-rs-label">
        <div style="width:8px;height:8px;border-radius:50%;background:${s.col};flex-shrink:0"></div>
        <span style="font-family:var(--sn);font-size:12px;font-weight:700;min-width:110px">${s.name}</span>
        <span style="font-family:var(--mn);font-size:9px;color:var(--t3)">${s.etf}</span>
      </div>
      <div class="sector-rs-bar-wrap">
        <div class="sector-rs-zero"></div>
        <div class="sector-rs-bar ${isUp ? 'sector-rs-bar-pos' : 'sector-rs-bar-neg'}" style="width:${barW}%;background:${col}"></div>
      </div>
      <div class="sector-rs-val" style="color:${col}">${isUp ? '+' : ''}${rel.toFixed(2)}%</div>
      <div class="sector-rs-abs" style="color:var(--t3)">${abs != null ? (abs >= 0 ? '+' : '') + abs.toFixed(2) + '%' : ''}</div>
    </div>`;
  });

  h += `<div style="font-family:var(--mn);font-size:9px;color:var(--t3);margin-top:10px;line-height:1.5">Positive = outperforming SPY · Negative = underperforming · Momentum score averages relative strength across all timeframes</div>`;
  return h;
}

function renderSectorTable2() {
  let h = `<div style="overflow-x:auto;-webkit-overflow-scrolling:touch"><table class="sector-table">
    <thead><tr>
      <th style="text-align:left">SECTOR</th>
      <th>ETF</th>
      <th>TODAY</th>
      <th>1W</th>
      <th>1M</th>
      <th>YTD</th>
      <th>vs SPY</th>
      <th>MOM</th>
      <th>PRICE</th>
    </tr></thead><tbody>`;

  // Sort by momentum when known; unknowns last (not treated as 0)
  const sorted = [...SECTORS_DEF].sort((a, b) => {
    const ma = _sectorMomentumScore(a.etf), mb = _sectorMomentumScore(b.etf);
    if (ma == null && mb == null) return 0;
    if (ma == null) return 1;
    if (mb == null) return -1;
    return mb - ma;
  });

  sorted.forEach(s => {
    const d = _sectorData[s.etf] || {};
    const mom = _sectorMomentumScore(s.etf);
    const fmtPct = v => v == null ? '—' : `<span style="color:${v > 0 ? 'var(--gn)' : v < 0 ? 'var(--rd)' : 'var(--t3)'};font-weight:700">${v >= 0 ? '+' : ''}${v.toFixed(2)}%</span>`;
    const momFmt = mom == null ? '—' : `<span style="color:${mom > 0 ? 'var(--gn)' : mom < 0 ? 'var(--rd)' : 'var(--t3)'};font-weight:800">${mom >= 0 ? '+' : ''}${mom.toFixed(2)}%</span>`;
    h += `<tr onclick="_sectorOpen('${s.etf}')" class="${_sectorSel === s.etf ? 'sector-row-sel' : ''}">
      <td><div style="display:flex;align-items:center;gap:8px"><div style="width:8px;height:8px;border-radius:50%;background:${s.col}"></div><span style="font-weight:700">${s.name}</span></div></td>
      <td style="color:var(--gd);font-weight:700">${s.etf}</td>
      <td>${fmtPct(d.day)}</td>
      <td>${fmtPct(d.week)}</td>
      <td>${fmtPct(d.month)}</td>
      <td>${fmtPct(d.ytd)}</td>
      <td>${fmtPct(_sectorRelSpy(s.etf, 'month'))}</td>
      <td>${momFmt}</td>
      <td style="color:var(--t2)">${d.price ? '$' + d.price.toFixed(2) : '—'}</td>
    </tr>`;
  });

  h += '</tbody></table></div>';

  // Best/worst performers summary
  const withData = SECTORS_DEF.filter(s => _sectorData[s.etf]?.month != null);
  if (withData.length) {
    const best = [...withData].sort((a,b)=>(_sectorData[b.etf].month||0)-(_sectorData[a.etf].month||0))[0];
    const worst = [...withData].sort((a,b)=>(_sectorData[a.etf].month||0)-(_sectorData[b.etf].month||0))[0];
    h += `<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px">
      <div class="gc" style="padding:14px;border-left:3px solid var(--gn)">
        <div style="font-family:var(--mn);font-size:8px;color:var(--gn);letter-spacing:0.15em;margin-bottom:6px">STRONGEST SECTOR (1M)</div>
        <div style="font-family:var(--sn);font-size:16px;font-weight:800;color:var(--tx)">${best.name}</div>
        <div style="font-family:var(--mn);font-size:14px;font-weight:900;color:var(--gn);margin-top:4px">${_sectorData[best.etf].month >= 0 ? "+" : ""}${_sectorData[best.etf].month.toFixed(2)}%</div>
        <div style="font-family:var(--sn);font-size:11px;color:var(--t2);margin-top:6px;line-height:1.5">${ROTATION_CONTEXT[best.name]?.note||''}</div>
      </div>
      <div class="gc" style="padding:14px;border-left:3px solid var(--rd)">
        <div style="font-family:var(--mn);font-size:8px;color:var(--rd);letter-spacing:0.15em;margin-bottom:6px">WEAKEST SECTOR (1M)</div>
        <div style="font-family:var(--sn);font-size:16px;font-weight:800;color:var(--tx)">${worst.name}</div>
        <div style="font-family:var(--mn);font-size:14px;font-weight:900;color:var(--rd);margin-top:4px">${_sectorData[worst.etf].month.toFixed(2)}%</div>
        <div style="font-family:var(--sn);font-size:11px;color:var(--t2);margin-top:6px;line-height:1.5">${ROTATION_CONTEXT[worst.name]?.note||''}</div>
      </div>
    </div>`;
  }
  return h;
}

function renderSectorRotationCycle() {
  let h = `<div class="gc" style="padding:16px;margin-bottom:12px;border-left:3px solid var(--gd)">
    <div style="font-family:var(--mn);font-size:9px;color:var(--gd);letter-spacing:0.15em;margin-bottom:8px">THE SECTOR ROTATION FRAMEWORK</div>
    <div style="font-family:var(--sn);font-size:13px;color:var(--t2);line-height:1.65">Sectors outperform at different points in the economic cycle. Understanding where we are in the cycle determines which sectors to overweight. The current <strong style="color:var(--gd)">Regime</strong> card on the Dashboard shows the current macro environment.</div>
  </div>`;

  const cycles = [
    {phase:'Early Recovery', col:'var(--gn)', sectors:['Consumer Disc','Financials','Industrials','Materials'], desc:'GDP turning up, rates low, credit loosening. Risk-on rotation begins.'},
    {phase:'Mid Cycle', col:'var(--bl)', sectors:['Technology','Communication','Industrials'], desc:'Growth accelerating. Earnings beating. Risk appetite high. Capex picks up.'},
    {phase:'Late Cycle', col:'var(--gd)', sectors:['Energy','Materials','Healthcare','Consumer Stap'], desc:'Inflation rising. Rates climbing. Pricing power matters. Defensive rotation begins.'},
    {phase:'Recession', col:'var(--rd)', sectors:['Consumer Stap','Healthcare','Utilities','Real Estate'], desc:'GDP contracting. Credit tightening. Safe havens outperform. Rate cuts expected.'},
  ];

  cycles.forEach(c => {
    const sectorPerfs = c.sectors.map(name => {
      const s = SECTORS_DEF.find(x => x.name === name);
      if (!s) return null;
      const pct = _sectorData[s.etf]?.month;
      return {name, pct, etf: s.etf, col: s.col};
    }).filter(Boolean);

    h += `<div class="gc" style="padding:0;overflow:hidden;margin-bottom:10px;border-top:3px solid ${c.col}">
      <div style="padding:14px 16px;background:${c.col}10">
        <div style="font-family:var(--mn);font-size:9px;color:${c.col};letter-spacing:0.18em;margin-bottom:4px">${c.phase.toUpperCase()} PHASE</div>
        <div style="font-family:var(--sn);font-size:12px;color:var(--t2);line-height:1.55">${c.desc}</div>
      </div>
      <div style="padding:10px 16px;display:flex;gap:8px;flex-wrap:wrap;border-top:1px solid var(--gb)">
        ${sectorPerfs.map(sp => `<div style="display:flex;align-items:center;gap:6px;background:var(--b1);border-radius:8px;padding:6px 10px;cursor:pointer" onclick="_sectorOpen('${sp.etf}')">
          <div style="width:7px;height:7px;border-radius:50%;background:${sp.col}"></div>
          <span style="font-family:var(--sn);font-size:12px;font-weight:600;color:var(--tx)">${sp.name}</span>
          ${sp.pct!=null?`<span style="font-family:var(--mn);font-size:10px;font-weight:700;color:${sp.pct>=0?'var(--gn)':'var(--rd)'}">${sp.pct>=0?'+':''}${sp.pct.toFixed(1)}%</span>`:''}
        </div>`).join('')}
      </div>
    </div>`;
  });

  SECTORS_DEF.forEach(s => {
    const ctx = ROTATION_CONTEXT[s.name];
    if (!ctx) return;
    const d = _sectorData[s.etf] || {};
    h += `<div class="gc" style="padding:12px 16px;margin-bottom:8px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
        <div style="width:10px;height:10px;border-radius:50%;background:${s.col};flex-shrink:0"></div>
        <span style="font-family:var(--sn);font-size:13px;font-weight:700;flex:1">${s.name}</span>
        <span style="font-family:var(--mn);font-size:8px;background:var(--b2);color:var(--t2);padding:2px 8px;border-radius:4px">${ctx.cycle}</span>
        ${d.month!=null?`<span style="font-family:var(--mn);font-size:10px;font-weight:700;color:${d.month>=0?'var(--gn)':'var(--rd)'}">${d.month>=0?'+':''}${d.month.toFixed(2)}% (1M)</span>`:''}
      </div>
      <div style="font-family:var(--sn);font-size:12px;color:var(--t2);line-height:1.55">${ctx.note}</div>
    </div>`;
  });

  return h;
}

// ─── Heatmap ───
function _heatTileSize(a){const mc=_parseMc(a.mc);if(!mc)return 4;return Math.max(4,Math.min(16,Math.log10(mc)*1.6-4.5));}
function _sectorAvg(tks){
  // Live % only — never multiply market-cap by fp().c "—" (→ NaN)
  // Return null when no live inputs (0 would paint a fake flat average)
  let wMc=0,wSum=0;
  tks.forEach(a=>{
    const ch=liveChg(a.tk);
    if(ch==null)return;
    const mc=_parseMc(a.mc)||1e9;
    wMc+=mc;wSum+=ch*mc;
  });
  return wMc?wSum/wMc:null;
}

function renderHeat(){
  let h = _renderPgHdr("Market Heatmap", "Size by market cap · Colour by daily change");
  h += _renderSiteIntelCard("heat");
  const sectors=[
    {name:'Equities',col:'var(--bl)',tks:A.filter(a=>a.cat==='Stock')},
    {name:'Crypto',col:'var(--pu)',tks:A.filter(a=>a.cat==='Crypto')},
    {name:'Commodities',col:'var(--gd)',tks:A.filter(a=>a.cat==='Commodity')},
    {name:'FX',col:'var(--cy)',tks:A.filter(a=>a.cat==='FX')},
  ];
  sectors.forEach(s=>{
    if(!s.tks.length)return;
    const avg=_sectorAvg(s.tks);
    const hasAvg=avg!=null&&isFinite(avg);
    const avgCol=!hasAvg?'var(--t3)':avg>0?'var(--gn)':avg<0?'var(--rd)':'var(--t3)';
    const avgLbl=!hasAvg?'— avg':`${avg>0?'+':''}${avg.toFixed(2)}% avg`;
    h+=`<div style="margin-bottom:16px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">
        <div style="font-family:var(--mn);font-size:9px;color:${s.col};letter-spacing:0.2em">${s.name.toUpperCase()}</div>
        <div style="font-family:var(--mn);font-size:9px;font-weight:700;color:${avgCol};background:${!hasAvg?'rgba(255,255,255,0.04)':avg>0?'rgba(0,200,150,0.1)':avg<0?'rgba(255,71,87,0.1)':'rgba(255,255,255,0.04)'};padding:2px 8px;border-radius:4px">${avgLbl}</div>
      </div>`;
    h+=`<div style="display:flex;flex-wrap:wrap;gap:3px;align-items:flex-start">`;
    s.tks.forEach(a=>{
      const d=fp(a.tk);
      const chg=liveChg(a.tk);
      const na=chg==null;
      const intensity=na?0:Math.min(Math.abs(chg)/5,1);
      // Flat (0%) is neutral — not green "up"
      const up=!na&&chg>0;
      const dn=!na&&chg<0;
      const bg=na||(!up&&!dn)?`rgba(255,255,255,0.03)`:(up?`rgba(0,200,150,${0.08+intensity*0.42})`:`rgba(255,71,87,${0.08+intensity*0.42})`);
      const col=na?'var(--t3)':up?'#00C896':dn?'#FF4757':'var(--t3)';
      const sz=_heatTileSize(a);
      h+=`<div class="heat-tile" onclick="openA('${a.tk}')" style="flex:${sz.toFixed(1)};min-width:60px;max-width:140px;background:${bg};border-color:${na?'rgba(255,255,255,0.08)':col+'30'}">
        <div style="font-family:var(--mn);font-size:${sz>8?'12':'10'}px;font-weight:800;color:var(--tx)">${a.tk}</div>
        <div style="font-family:var(--mn);font-size:10px;font-weight:700;color:${col};margin-top:2px">${na?'—':`${chg>0?'+':''}${chg.toFixed(2)}%`}</div>
        ${sz>6?`<div style="font-family:var(--mn);font-size:9px;color:var(--t2);margin-top:1px">${na?'no sync':((a.cat==='Stock'||a.cat==='Crypto'||a.cat==='Commodity')?'$':'')+d.p}</div>`:''}
      </div>`;
    });
    h+=`</div></div>`;
  });
  h+=`<div style="display:flex;align-items:center;gap:8px;padding:8px 0;font-family:var(--mn);font-size:9px;color:var(--t3)">
    <span>Legend:</span>
    <span style="background:rgba(0,200,150,0.4);padding:2px 8px;border-radius:3px;color:var(--gn)">↑ Strong up</span>
    <span style="background:rgba(0,200,150,0.12);padding:2px 8px;border-radius:3px;color:var(--gn)">↑ Mild up</span>
    <span style="background:rgba(255,71,87,0.12);padding:2px 8px;border-radius:3px;color:var(--rd)">↓ Mild dn</span>
    <span style="background:rgba(255,71,87,0.4);padding:2px 8px;border-radius:3px;color:var(--rd)">↓ Strong dn</span>
    <span style="margin-left:auto;color:var(--t3)">Tile size ∝ market cap</span>
  </div>`;
  return h;
}

// ─── Crypto Rankings ───
let _cryptoMktData=null,_cryptoMktLoading=false,_cryptoDominance=null;

async function fetchCryptoMarket(){
  _cryptoMktLoading=true;
  if(pg==='crypto')renderMain();
  try{
    const [mktRes,globalRes]=await Promise.allSettled([
      cgFetch('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1&sparkline=false&price_change_percentage=1h,24h,7d',{signal:AbortSignal.timeout(10000)}),
      cgFetch('https://api.coingecko.com/api/v3/global',{signal:AbortSignal.timeout(8000)}),
    ]);
    if(mktRes.status==='fulfilled'&&mktRes.value.ok){
      const data=await mktRes.value.json();
      _cryptoMktData=Array.isArray(data)?data:null;
      // Push desk-known crypto (BTC, ETH, …) into liveSymbols for book/tape
      if(Array.isArray(_cryptoMktData)){
        _cryptoMktData.forEach(coin=>{
          const sym=(coin.symbol||"").toUpperCase();
          if(!sym||!(coin.current_price>0))return;
          const tk=typeof resolveInternalTicker==="function"
            ? (resolveInternalTicker(sym)||resolveInternalTicker(sym+"-USD")||sym)
            : sym;
          if(!A.find(a=>a.tk===tk)&&!(typeof YAHOO_SYMBOLS!=="undefined"&&YAHOO_SYMBOLS[tk]))return;
          const chg=coin.price_change_percentage_24h??coin.price_change_percentage_24h_in_currency;
          _applyLiveQuote(tk,{
            p:coin.current_price,
            c:typeof chg==="number"&&isFinite(chg)?chg:0,
          },"coingecko");
        });
        try{renderTape();}catch(e){}
      }
    }
    if(globalRes.status==='fulfilled'&&globalRes.value.ok){
      const gd=await globalRes.value.json();
      _cryptoDominance={btc:gd.data?.market_cap_percentage?.btc?.toFixed(1),eth:gd.data?.market_cap_percentage?.eth?.toFixed(1),totalMcap:gd.data?.total_market_cap?.usd};
    }
  }catch(e){}
  _cryptoMktLoading=false;
  if(pg==='crypto')renderMain();
}

function renderCryptoPage(){
  let h = _renderPgHdr("Crypto Markets", "Top 50 by market cap · CoinGecko",
    `<button onclick="fetchCryptoMarket()" class="hdr-act-btn">${_cryptoMktLoading ? "⟳ Loading…" : "⟳ Refresh"}</button>`);
  h += _renderSiteIntelCard("crypto");

  // Dominance bar
  if(_cryptoDominance){
    const totalMcap=_cryptoDominance.totalMcap;
    h+=`<div class="gc" style="padding:14px;margin-bottom:12px">
      <div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.15em;margin-bottom:8px">CRYPTO MARKET DOMINANCE</div>
      <div style="display:flex;gap:16px;margin-bottom:8px">
        <div><div style="font-family:var(--mn);font-size:9px;color:var(--gd)">BTC DOMINANCE</div><div style="font-family:var(--mn);font-size:20px;font-weight:900;color:var(--gd)">${_cryptoDominance.btc}%</div></div>
        <div><div style="font-family:var(--mn);font-size:9px;color:var(--pu)">ETH DOMINANCE</div><div style="font-family:var(--mn);font-size:20px;font-weight:900;color:var(--pu)">${_cryptoDominance.eth}%</div></div>
        ${totalMcap?`<div><div style="font-family:var(--mn);font-size:9px;color:var(--t3)">TOTAL MARKET CAP</div><div style="font-family:var(--mn);font-size:14px;font-weight:700;color:var(--tx)">$${(totalMcap/1e12).toFixed(2)}T</div></div>`:''}
      </div>
      <div style="height:8px;border-radius:4px;overflow:hidden;display:flex;gap:1px">
        <div style="flex:${_cryptoDominance.btc};background:var(--gd);border-radius:4px 0 0 4px"></div>
        <div style="flex:${_cryptoDominance.eth};background:var(--pu)"></div>
        <div style="flex:${100-parseFloat(_cryptoDominance.btc)-parseFloat(_cryptoDominance.eth)};background:var(--b3);border-radius:0 4px 4px 0"></div>
      </div>
      <div style="display:flex;gap:12px;margin-top:6px;font-family:var(--mn);font-size:9px;color:var(--t3)">
        <span style="color:var(--gd)">█ BTC ${_cryptoDominance.btc}%</span>
        <span style="color:var(--pu)">█ ETH ${_cryptoDominance.eth}%</span>
        <span>█ Others ${(100-parseFloat(_cryptoDominance.btc)-parseFloat(_cryptoDominance.eth)).toFixed(1)}%</span>
      </div>
    </div>`;
  }

  if(_cryptoMktLoading&&!_cryptoMktData){
    h+=`<div style="padding:24px;text-align:center;font-family:var(--mn);font-size:10px;color:var(--t3)"><div style="width:14px;height:14px;border:2px solid var(--bl);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div>Loading crypto markets…</div>`;
    return h;
  }
  if(!_cryptoMktData){
    h+=`<div class="gc" style="padding:24px;text-align:center"><div style="font-family:var(--sn);font-size:13px;color:var(--t2)">Tap Refresh to load crypto rankings</div><button onclick="fetchCryptoMarket()" style="margin-top:12px;background:var(--gd);color:var(--bg);border:none;border-radius:6px;padding:8px 20px;font-family:var(--sn);font-size:12px;font-weight:700;cursor:pointer">Load Rankings</button></div>`;
    return h;
  }

  h+=`<div style="overflow-x:auto;-webkit-overflow-scrolling:touch"><table style="width:100%;border-collapse:collapse;font-family:var(--mn);font-size:11px;min-width:600px">
    <thead><tr style="background:var(--b1);border-bottom:1px solid var(--gb)">
      <th style="padding:8px 10px;text-align:left;font-size:9px;color:var(--t3);letter-spacing:0.1em;width:36px">#</th>
      <th style="padding:8px 10px;text-align:left;font-size:9px;color:var(--t3);letter-spacing:0.1em">NAME</th>
      <th style="padding:8px 10px;text-align:right;font-size:9px;color:var(--t3);letter-spacing:0.1em">PRICE</th>
      <th style="padding:8px 10px;text-align:right;font-size:9px;color:var(--t3);letter-spacing:0.1em">1H%</th>
      <th style="padding:8px 10px;text-align:right;font-size:9px;color:var(--t3);letter-spacing:0.1em">24H%</th>
      <th style="padding:8px 10px;text-align:right;font-size:9px;color:var(--t3);letter-spacing:0.1em">7D%</th>
      <th style="padding:8px 10px;text-align:right;font-size:9px;color:var(--t3);letter-spacing:0.1em">MKT CAP</th>
      <th style="padding:8px 10px;text-align:right;font-size:9px;color:var(--t3);letter-spacing:0.1em">24H VOL</th>
    </tr></thead><tbody>`;

  _cryptoMktData.forEach((coin,i)=>{
    const fmt=n=>{
      if(n==null||!isFinite(n))return "—";
      return n>=1e12?`$${(n/1e12).toFixed(2)}T`:n>=1e9?`$${(n/1e9).toFixed(2)}B`:n>=1e6?`$${(n/1e6).toFixed(1)}M`:'$'+n.toLocaleString();
    };
    // null/NaN only — 0% is a real flat print, not "missing"
    const priceFmt=n=>{
      if(n==null||!isFinite(n))return "—";
      return n>=1000?`$${n.toLocaleString(undefined,{maximumFractionDigits:2})}`:n>=1?`$${n.toFixed(2)}`:`$${n.toFixed(6)}`;
    };
    // 0% is flat (neutral), not a red "down" print
    const chgCol=v=>(v==null||!isFinite(v))?'var(--t3)':v>0?'var(--gn)':v<0?'var(--rd)':'var(--t3)';
    const chgFmt=v=>(v==null||!isFinite(v))?'—':`${v>0?'+':''}${v.toFixed(2)}%`;
    const h1=coin.price_change_percentage_1h_in_currency;
    const h24=coin.price_change_percentage_24h_in_currency;
    const d7=coin.price_change_percentage_7d_in_currency;
    const sym=(coin.symbol||"").toUpperCase();
    // Open desk ticker when known (BTC), else Yahoo lookup (PEPE → PEPE-USD resolve)
    const openAct=sym?`lookupTicker('${sym.replace(/'/g,"")}')`:"";
    h+=`<tr ${openAct?`onclick="${openAct}"`:""} style="border-bottom:1px solid rgba(255,255,255,0.03);cursor:${openAct?"pointer":"default"};transition:background 0.1s" onmouseover="this.style.background='var(--b1)'" onmouseout="this.style.background=''">
      <td style="padding:8px 10px;color:var(--t3);font-size:10px">${coin.market_cap_rank||i+1}</td>
      <td style="padding:8px 10px"><div style="display:flex;align-items:center;gap:8px">
        <img src="${coin.image||""}" width="20" height="20" style="border-radius:50%;flex-shrink:0" alt="" onerror="this.style.display='none'">
        <div><div style="font-weight:700;color:var(--tx)">${coin.name||sym||"—"}</div><div style="font-size:9px;color:var(--t3)">${sym}</div></div>
      </div></td>
      <td style="padding:8px 10px;text-align:right;font-weight:700">${priceFmt(coin.current_price)}</td>
      <td style="padding:8px 10px;text-align:right;color:${chgCol(h1)};font-weight:600">${chgFmt(h1)}</td>
      <td style="padding:8px 10px;text-align:right;color:${chgCol(h24)};font-weight:600">${chgFmt(h24)}</td>
      <td style="padding:8px 10px;text-align:right;color:${chgCol(d7)};font-weight:600">${chgFmt(d7)}</td>
      <td style="padding:8px 10px;text-align:right;color:var(--t2)">${fmt(coin.market_cap)}</td>
      <td style="padding:8px 10px;text-align:right;color:var(--t3)">${fmt(coin.total_volume)}</td>
    </tr>`;
  });
  h+=`</tbody></table></div>`;
  h+=`<div style="font-family:var(--mn);font-size:9px;color:var(--t3);padding:10px 0;text-align:center">Data: CoinGecko · Top 50 by market cap</div>`;
  return h;
}

// ═══════════════════════════════════════════════════════════
// LEARN SECTION — Hedge Fund Research Desk
// Professional-grade analysis frameworks for independent
// market analysts and traders
// ═══════════════════════════════════════════════════════════

let _learnTab = 'macro';
let _learnSub = null; // active article/module id
let _glossSearch = '';
let _ecoCountry = 'US';
let _ecoIndicator = 'NY.GDP.MKTP.KD.ZG';
let _ecoData = {};
let _ecoLoading = false;
let _calcTab = 'compound';

const ECO_COUNTRIES = [
  {code:'US',name:'United States 🇺🇸'},{code:'GB',name:'United Kingdom 🇬🇧'},
  {code:'DE',name:'Germany 🇩🇪'},{code:'JP',name:'Japan 🇯🇵'},
  {code:'CN',name:'China 🇨🇳'},{code:'IN',name:'India 🇮🇳'},
  {code:'FR',name:'France 🇫🇷'},{code:'BR',name:'Brazil 🇧🇷'},
];

const ECO_INDICATORS = [
  {code:'NY.GDP.MKTP.KD.ZG',name:'GDP Growth Rate',unit:'%',desc:'Annual % change in real GDP. The broadest measure of economic activity.'},
  {code:'FP.CPI.TOTL.ZG',name:'Inflation (CPI)',unit:'%',desc:'Annual change in Consumer Price Index. Central banks target ~2%.'},
  {code:'SL.UEM.TOTL.ZS',name:'Unemployment Rate',unit:'%',desc:'% of labour force without employment. Lags economic cycle by 6-12 months.'},
  {code:'FR.INR.RINR',name:'Real Interest Rate',unit:'%',desc:'Nominal rate minus inflation. Negative = loose monetary conditions.'},
  {code:'NE.TRD.GNFS.ZS',name:'Trade (% of GDP)',unit:'%',desc:'Trade openness. High = sensitive to global demand and currency moves.'},
  {code:'GC.DOD.TOTL.GD.ZS',name:'Govt Debt (% GDP)',unit:'%',desc:'Fiscal sustainability metric. Above 100% = limited room for stimulus.'},
];

// ─── Professional content modules ───
const LEARN_MODULES = {
  macro: [
    {
      id:'regime-framework',
      title:'The Four Macro Regimes',
      tag:'FRAMEWORK',
      tagCol:'var(--gd)',
      summary:'How to position across asset classes based on growth and inflation conditions',
      content:`
## The Macro Regime Framework

Every portfolio decision should start with answering one question: **What is the current macro regime?**

The regime framework maps the economy across two axes — growth (rising or falling) and inflation (rising or falling) — producing four distinct environments that have historically driven predictable patterns across asset classes.

---

### Regime 1: Goldilocks (↑Growth, ↓Inflation)
The optimal environment. GDP expanding, inflation cooling. Central banks can hold or cut rates. Risk assets flourish.

**Winners:** Equities (especially growth/tech), Credit, EM assets
**Losers:** Gold, Defensive bonds, USD
**Central bank stance:** Neutral to dovish

*Historical example: 1995-2000, 2013-2019, post-COVID 2020-2021*

---

### Regime 2: Reflation (↑Growth, ↑Inflation)
Economy running hot. Demand exceeding supply. Central banks begin tightening but economy still strong.

**Winners:** Commodities, Energy stocks, Financials (rate rise benefits banks), Real assets
**Losers:** Long-duration bonds, High-multiple growth stocks
**Central bank stance:** Hawkish — hiking or signalling hikes

*Historical example: 2004-2006, 2021-2022 early phase*

---

### Regime 3: Stagflation (↓Growth, ↑Inflation)
The worst regime. Economy weakening but inflation sticky. Central banks trapped — can't cut without stoking inflation, can't hike without crashing growth.

**Winners:** Gold, Commodities, Short-duration assets, Oil
**Losers:** Everything else — equities, bonds, EM. Classic "nowhere to hide"
**Central bank stance:** Paralysed — this is the 1970s trap

*Historical example: 1973-74, 2022 peak, 2008 briefly*

---

### Regime 4: Deflation / Recession (↓Growth, ↓Inflation)
Economy contracting, inflation falling or negative. Central banks cut aggressively. The "risk-off" regime.

**Winners:** Long-duration government bonds, USD, Gold initially
**Losers:** Equities, Credit, Commodities, EM
**Central bank stance:** Aggressively dovish — cutting, QE

*Historical example: 2008-09, 2020 briefly, Japan 1990s*

---

### How to Use This on The Dispatch

The **Regime card** on the Dashboard shows the current regime assessment. The **Signals panel** surfaces signals that indicate a regime transition. Cross-check with the **Economics section** (GDP growth vs CPI) to validate your regime read before positioning.

**The key insight:** Regime transitions are where alpha is made. Most losses in investment come from holding positions that were correct for the prior regime into a new one.
      `
    },
    {
      id:'rate-cycles',
      title:'Central Bank Cycle Analysis',
      tag:'FRAMEWORK',
      tagCol:'var(--bl)',
      summary:'How to trade Fed, ECB and BOE rate cycles across all asset classes',
      content:`
## Central Bank Cycle Analysis: The Professional Framework

Interest rate cycles are the single most powerful macro force driving asset prices. Every professional investor needs a systematic framework for tracking where we are in the cycle.

---

### The Four Phases of a Rate Cycle

**Phase 1: Tightening Begins**
The Fed signals rate hikes. Markets price in the path. Long-duration assets sell off immediately as discount rates rise. Yield curve typically flattens.

*Trade: Reduce duration, add financials, sell expensive growth, buy USD*

**Phase 2: Tightening Accelerates**
Multiple hikes delivered. Credit conditions tighten. Yield curve may invert. Risk assets come under pressure as funding costs rise and forward earnings are discounted more heavily.

*Trade: Maximum defensiveness — cash, short duration, quality over growth, commodities if inflation driving hikes*

**Phase 3: Pause**
The Fed stops hiking. Markets debate: soft landing or recession? This is the highest uncertainty phase. Volatility elevated. Both bulls and bears have arguments.

*Trade: Start rebuilding positions selectively. Long-duration bonds often their best entry point. Watch credit spreads for early warning of recession.*

**Phase 4: The Pivot (Cuts Begin)**
Historically one of the strongest buy signals across risk assets. Growth stocks, EM, credit, and gold all typically rally hard on the first cut — especially if accompanied by recession fears fading.

*Trade: Add risk broadly. Long duration. EM FX. High yield credit. This is where the 12-month forward return is historically highest.*

---

### The 2022-2026 Cycle in Context

The Fed hiked from 0% to 5.25-5.50% between March 2022 and July 2023 — the fastest hiking cycle since the 1980s. The tightening was driven by post-COVID supply disruption and fiscal excess combining to produce 9.1% CPI (June 2022).

By 2024, with inflation retreating to 3%, the Fed began its cutting cycle. The critical question for 2025-2026: whether this is a "soft landing" cycle (Regime 1/Goldilocks) or a delayed recession (Regime 4).

---

### The Yield Curve as Your Compass

The 2-year vs 10-year spread (2s10s) is the most important macro indicator:

- **Steep (10Y >> 2Y):** Markets expect growth and potentially higher rates. Normal environment.
- **Flat:** Transition. Markets uncertain about direction.
- **Inverted (2Y > 10Y):** Markets pricing in rate cuts ahead — which only happen in recessions. Has preceded every US recession since 1955 with 12-18 month lead time.

Watch the **VIX** and **credit spreads** alongside the yield curve for confirmation.
      `
    },
    {
      id:'fx-framework',
      title:'Currency Analysis for Equities Investors',
      tag:'ADVANCED',
      tagCol:'var(--cy)',
      summary:'How FX moves affect equity returns and sector rotation — the overlooked dimension',
      content:`
## Currency Analysis: What Every Equity Investor Must Understand

Most equity investors ignore FX — and pay for it with unexplained portfolio drawdowns. A 10% move in the US dollar can wipe out equity market returns entirely for non-US investors.

---

### The Dollar Cycle and Global Risk

The US dollar is the world's reserve currency and moves in multi-year cycles (typically 6-8 years) that profoundly affect global risk appetite.

**Strong Dollar (DXY Rising):**
- Tightens global financial conditions (dollar debt becomes more expensive)
- Pressures EM equities and currencies
- Benefits US consumers (cheaper imports) but hurts US multinationals
- Commodities typically fall (most priced in USD)

**Weak Dollar (DXY Falling):**
- Loosens global financial conditions
- EM equities and currencies outperform
- US multinationals benefit from translation gains
- Commodities typically rise

*The 2022 DXY spike to 114 (strongest in 20 years) was a direct consequence of the Fed's aggressive hiking cycle — and contributed significantly to global EM stress.*

---

### Sector Sensitivity to FX

| Sector | Strong USD | Weak USD |
|--------|-----------|---------|
| US Tech (global revenue) | Headwind | Tailwind |
| Energy/Commodities | Headwind | Tailwind |
| US Financials | Neutral | Neutral |
| EM Markets | Strong headwind | Strong tailwind |
| European exporters | Tailwind | Headwind |

---

### Carry Trade Dynamics

The carry trade (borrow in low-rate currency, invest in high-rate currency) is the dominant FX market force. When carry is unwound (risk-off events), it causes violent FX moves.

Key carry pairs: Long AUD/JPY, MXN/JPY, NZD/JPY in risk-on. These unwind rapidly in crises.

*The August 2024 yen carry unwind caused a 12% drop in the S&P in 3 days — a reminder of how FX dynamics can overwhelm equity fundamentals.*
      `
    },
  ],
  fundamental: [
    {
      id:'quality-earnings',
      title:'Quality of Earnings Analysis',
      tag:'PROFESSIONAL',
      tagCol:'var(--gn)',
      summary:'How professional analysts separate real earnings from accounting manipulation',
      content:`
## Quality of Earnings: The Most Important Skill in Fundamental Analysis

Two companies can report the same EPS number. One is genuinely profitable and creating shareholder value. The other is using accounting tricks to manufacture earnings while burning cash. The quality of earnings framework tells you which is which.

---

### The Golden Rule: Cash Is King

Always start with cash flow, not earnings. The income statement can be manipulated; cash flow is much harder to fake.

**High Quality Earnings:**
- Free Cash Flow closely tracks Net Income
- Revenue recognised when cash actually received (low receivables growth)
- Organic growth (not acquisition-driven)
- Consistent margins across reporting periods
- Management guidance that proves reliable

**Low Quality Earnings:**
- FCF significantly below Net Income (earnings are paper profits)
- Receivables growing faster than revenue (customers not paying)
- Heavy use of "adjusted" metrics excluding real costs
- Lumpy, one-off items that appear every quarter (they're not one-offs)
- Frequent goodwill impairments from acquisitions

---

### The Accruals Ratio

The accruals ratio measures the gap between accounting earnings and cash earnings:

**Accruals = (Net Income − Free Cash Flow) / Total Assets**

- Accruals ratio below 5%: High quality earnings
- 5-10%: Moderate — investigate further
- Above 10%: Red flag — earnings being manufactured by accounting choices

*Academic research shows high-accruals companies systematically underperform low-accruals companies over the following year.*

---

### The Operating Leverage Trap

Companies with high fixed costs (manufacturing, airlines, retailers) have high operating leverage — small revenue changes produce large earnings swings. In expansions this looks phenomenal (earnings grow fast). In contractions it's catastrophic (earnings collapse).

Investors systematically overpay for cyclical companies at the peak of cycles because trailing earnings look strong. The professional approach: normalise earnings across the cycle, pay attention to where you are in that cycle.

---

### Five Questions for Every Earnings Report

1. Does Free Cash Flow confirm the reported profit?
2. Is working capital (receivables, inventory) growing faster than sales?
3. Are the "one-off" charges recurring?
4. Has the accounting methodology changed vs prior periods?
5. What is management saying vs what the numbers show?
      `
    },
    {
      id:'roic-framework',
      title:'Return on Invested Capital (ROIC)',
      tag:'PROFESSIONAL',
      tagCol:'var(--gn)',
      summary:'The single best metric for identifying compounders — and avoiding value traps',
      content:`
## ROIC: The Professional Investor's North Star

Return on Invested Capital is the most important financial metric in fundamental analysis. It answers the question that separates great businesses from mediocre ones: **how efficiently does management deploy capital to generate returns?**

---

### The Formula

**ROIC = NOPAT / Invested Capital**

Where:
- **NOPAT** = Net Operating Profit After Tax = EBIT × (1 - tax rate)
- **Invested Capital** = Total Assets − Cash − Non-interest-bearing current liabilities

A simpler approximation: Operating Income × (1-tax) / (Equity + Debt − Cash)

---

### Why ROIC Matters More Than EPS

EPS can be inflated by:
- Share buybacks (fewer shares, same profit = higher EPS)
- Leverage (debt amplifies returns temporarily)
- Accounting choices

ROIC cannot be manipulated in the same way. A company earning 5% ROIC is destroying value if its cost of capital is 8%. A company earning 25% ROIC is compounding wealth regardless of what the P/E looks like.

---

### The ROIC-WACC Spread

**Value Creation = ROIC > WACC (cost of capital)**

- ROIC 15-20%+: Exceptional businesses with durable competitive advantages
- ROIC 10-15%: Good businesses, above average
- ROIC 6-10%: Mediocre — barely covering cost of capital
- ROIC <6%: Destroying shareholder value

*Buffett's Berkshire has averaged ~20% ROIC for 50 years. Most S&P 500 companies average 10-12%.*

---

### ROIC as a Moat Detector

Companies with **sustained high ROIC** (>15% for 10+ years) almost by definition have economic moats. The moat is what prevents competitors from driving ROIC down to the cost of capital through competition.

Cross-reference with score on this platform — assets with higher AI scores typically have stronger ROIC characteristics.

---

### Practical Application: The DuPont Decomposition

Break ROIC into components to understand WHERE the returns come from:

ROIC = (NOPAT Margin) × (Asset Turnover)

- **High margin, low turnover:** Luxury brands, software, pharma — price competitive advantage
- **Low margin, high turnover:** Retail, distribution — operational efficiency advantage
- **High both:** Exceptional (rare) — networks and platforms
      `
    },
    {
      id:'dcf-reverse',
      title:'Reverse DCF: What Is the Market Pricing In?',
      tag:'VALUATION',
      tagCol:'var(--pu)',
      summary:'How to use a reverse DCF to understand market expectations — and find mispricing',
      content:`
## Reverse DCF: The Professional Valuation Approach

Most analysts build a DCF model forward (project cash flows → discount to present value → compare to price). The professional approach does it backwards: **given the current price, what growth rate is the market implicitly assuming?**

This is far more powerful because it converts a subjective "is this stock cheap?" question into an objective "do I believe the market's implied growth rate?"

---

### The Reverse DCF Framework

For a simplified single-stage model:

**Implied Growth Rate = (Price × Cost of Capital − FCF) / FCF**

More precisely: solve for the growth rate (g) that makes the Gordon Growth Model output equal to the current market price:

Price = FCF₁ / (WACC − g)

Therefore: **g = WACC − (FCF₁ / Price)**

---

### Practical Example: NVDA at $800

If NVDA trades at $800 with FCF of $15/share and you assume:
- WACC of 10%
- Terminal growth of 3%

The market is implying ~28% annual FCF growth for the next 10 years.

Now the question becomes: **Do I believe Nvidia can grow FCF at 28% for 10 years?**

If you believe yes → the stock is fairly priced or cheap.
If you believe growth will be 15% → the stock is expensive at these assumptions.

---

### Three Zones of Implied Growth

**Zone 1: Implied growth < historical average**
Market is pessimistic. If you believe in the business, this is where you buy.

**Zone 2: Implied growth ≈ historical average**
Market is pricing in continuation of recent performance. Fairly valued.

**Zone 3: Implied growth >> historical average**
Market is pricing in perfection. Any shortfall = significant downside. This is where you reduce.

---

### Margin of Safety in DCF

Always run your DCF with conservative, base, and optimistic scenarios. Your buy price should be at a significant discount to even the conservative case. This is Graham's "margin of safety" translated into modern valuation terms.

The best investments: companies where even a "muddle through" scenario produces adequate returns, and the upside scenario is extraordinary.
      `
    },
  ],
  technical: [
    {
      id:'factor-investing',
      title:'Factor Investing: The Systematic Approach',
      tag:'SYSTEMATIC',
      tagCol:'var(--pu)',
      summary:'How to build systematic exposure to value, momentum, quality and low volatility',
      content:`
## Factor Investing: What Decades of Academic Research Shows

Factor investing (also called "smart beta" or systematic investing) is grounded in over 50 years of academic research showing that certain systematic characteristics — "factors" — earn persistent risk-adjusted returns above the market.

---

### The Five Core Factors

**1. Value**
Buying cheap stocks (low P/E, P/B, EV/EBITDA) relative to fundamentals. Works because markets systematically overprice glamour stocks and underprice neglected ones.
*Long-run premium: ~3-5% annually over market cap weight*
*Risk: Value traps, long drawdown periods (2010-2020 was brutal)*

**2. Momentum**
Buying recent winners and selling recent losers (typically 12-month return, excluding last month). Works because markets under-react to new information — trends persist.
*Long-run premium: ~6-8% annually*
*Risk: Momentum crashes (fast, severe reversals when sentiment shifts)*

**3. Quality**
Buying companies with high profitability (ROE, ROIC), low debt, stable earnings. Works because quality compounds and markets are slow to price durable advantages.
*Long-run premium: ~3-4% annually*
*Risk: Can be expensive in growth bull markets*

**4. Low Volatility**
Buying low-beta, low-volatility stocks. Counterintuitively outperforms high-volatility stocks over time. Works because fund managers are incentivised to reach for risk, creating a structural overvaluation of volatile stocks.
*Long-run premium: ~2-3% annually with lower drawdowns*
*Risk: Underperforms in strong bull markets*

**5. Size**
Small caps outperform large caps over very long periods. Works because small companies are less followed, creating mispricing opportunities.
*Long-run premium: ~2-3% annually*
*Risk: Very long drawdown periods, illiquidity*

---

### Factor Timing

Factors do NOT work all the time. They cycle. Key dynamics:

- **Value vs Growth:** 10-year cycles driven by interest rate environment. High rates → value. Low rates → growth.
- **Momentum:** Works until it doesn't — crashes fast when reversals come.
- **Quality:** Most consistent — expensive but rarely crashes hard.

Professional approach: combine multiple factors (diversification across factor risk) rather than betting on one.

---

### Applying to This Platform

The **AI Score** on this platform incorporates quality (ROIC, margins), momentum (price trend, earnings revisions), and value (P/E vs historical) signals. Stocks with high scores across multiple dimensions are the highest-quality opportunities.

Use the **screener** (sort by Score in the Markets panel) to surface multi-factor opportunities.
      `
    },
    {
      id:'market-microstructure',
      title:'Market Microstructure & Flow Analysis',
      tag:'ADVANCED',
      tagCol:'var(--rd)',
      summary:'Options market signals, positioning data and flow analysis professionals actually use',
      content:`
## Market Microstructure: The Hidden Layer of Market Intelligence

Price and earnings are public information. Professional edge comes from understanding the plumbing beneath the surface: who is positioned how, what options market makers are hedging, and where forced flows will hit.

---

### Options Market Signals

The options market is where informed money often expresses views before the equity market reflects them.

**Put/Call Ratio**
Total put volume / total call volume. Above 1.0 = more puts than calls = bearish sentiment.
*Contrarian indicator: extreme readings (>1.5 or <0.5) often precede reversals*

**Implied Volatility Skew**
The difference in implied volatility between out-of-the-money puts vs calls at the same strike distance. High skew = market paying up for downside protection.
*Elevated skew = institutional hedging = professional concern about downside*

**VIX Term Structure**
Short-dated VIX vs longer-dated VIX. When near-term VIX > longer-term VIX (backwardation), markets pricing in immediate stress. Normal structure (contango) = calm.

**Gamma Exposure (GEX)**
Net dealer gamma positioning. When dealers are long gamma, they BUY on dips and SELL on rips (stabilising). When short gamma, they SELL on dips and BUY on rips (destabilising = larger moves).
*Short gamma environments produce the largest directional moves*

---

### Commitment of Traders (COT) Report

Published weekly by the CFTC. Shows positioning of:
- **Commercials:** Hedgers (producers/consumers). "Smart money" for commodities.
- **Large Speculators:** Funds and CTAs. Follow trend.
- **Small Speculators:** Retail. Often wrong at extremes.

*Extreme net short/long positioning by large specs = contrarian opportunity*

---

### Fund Flow Data

Equity fund flows, ETF creation/redemption, and margin debt tell you about aggregate positioning. Markets have historically peaked when fund flows are most positive (everyone already in) and bottomed when flows are maximally negative (capitulation).

*CNN Fear & Greed Index, AAII Bull/Bear survey, II bulls/bears — all sentiment indicators that professional use as contrarian inputs*

---

### Dark Pool and Block Trade Activity

Large institutional trades (block trades) are often executed off-exchange (dark pools) to avoid market impact. Unusual dark pool activity in a stock can signal institutional accumulation or distribution before a move.

Services like Dark Pool Prints, Bloomberg TRACE (bonds) and FINRA's ADF track this.
      `
    },
  ],
  portfolio: [
    {
      id:'position-sizing',
      title:'Professional Position Sizing',
      tag:'RISK MANAGEMENT',
      tagCol:'var(--rd)',
      summary:'Kelly criterion, volatility targeting, and how hedge funds actually size positions',
      content:`
## Position Sizing: Where Returns Are Made and Preserved

The best stock pick in the world destroys your portfolio if you size it wrong. The worst stock pick is harmless if it's 0.5% of the portfolio. Position sizing is the most underrated skill in investing.

---

### The Kelly Criterion

Developed by John Kelly at Bell Labs, adopted by the world's greatest traders (Ed Thorp, Warren Buffett, George Soros).

**Full Kelly = Edge / Odds**

Where:
- Edge = Expected value of the trade (probability × payoff − probability of loss × loss)
- Odds = The payoff ratio (win size / loss size)

*Example: You believe a stock has 60% chance of rising 30% and 40% chance of falling 15%.*
*Kelly = (0.6 × 0.3 − 0.4 × 0.15) / 0.3 = (0.18 − 0.06) / 0.3 = 40% of portfolio*

In practice, professionals use **Half-Kelly** (20% in this example) because:
1. Your probability estimates are imprecise
2. Full Kelly produces devastating drawdowns
3. Emotional risk management requires smaller position sizes

---

### Volatility Targeting

Rather than equal weighting, professionals size positions inversely proportional to their volatility:

**Position Size = Target Volatility Contribution / Asset Volatility**

If you want each position to contribute 1% portfolio volatility, and TSLA has 50% annual vol:
*TSLA position = 1% / 50% = 2% of portfolio*

A utility stock with 15% vol would get: 1% / 15% = 6.7% of portfolio

This naturally reduces exposure to volatile assets and increases exposure to stable ones.

---

### The Pyramid Approach

Start with a partial position (1/3 of target size). Add on confirmation. This serves two purposes:
1. If wrong, loss is limited
2. Average cost is in the direction of the move (adding strength to strength)

*Never average down by adding to losing positions. This is the most dangerous mistake retail investors make.*

---

### Stop Losses and Risk Budget

Every position should have a predetermined risk budget: the maximum % of portfolio you will lose on this position before exiting regardless of conviction.

- Individual position max loss: 1-2% of total portfolio
- Sector concentration: no more than 25% in any sector
- Correlation budget: account for positions that move together in stress

**Example portfolio risk framework:**
- 20 positions × 2% risk each = 40% of portfolio at risk if all go wrong simultaneously
- In practice, correlations save you — but in crises they spike to 1 (everything falls together)

---

### Drawdown Management

The compounding mathematics of losses make large drawdowns devastating to recover from:
- 20% loss requires 25% gain to recover
- 50% loss requires 100% gain to recover
- 80% loss requires 400% gain to recover

**Rule: Protect capital first. Returns second.**

Professional funds often have hard rules: if portfolio is down 10% on the month, reduce risk by 50%. If down 15%, reduce to minimal positions. This prevents catastrophic drawdowns.
      `
    },
    {
      id:'correlation-risk',
      title:'Correlation, Diversification and Tail Risk',
      tag:'RISK MANAGEMENT',
      tagCol:'var(--rd)',
      summary:'Why diversification fails when you need it most — and how professionals hedge tail risk',
      content:`
## Correlation, Diversification, and Tail Risk

Modern Portfolio Theory says diversification reduces risk "for free." What they don't tell you: correlations spike to 1 in a crisis, destroying the benefit of diversification precisely when you need it most.

---

### The Correlation Illusion

In normal markets, stocks have low correlations with each other (0.3-0.5 average). A diversified portfolio of 20 stocks appears well-protected against individual stock risk.

But in risk-off environments — 2008, March 2020, 2022 — correlations spike:
- All sectors sell off simultaneously
- Bonds and stocks both fall (end of the "60/40" portfolio diversification)
- EM and DM equities both collapse
- Value and growth both fall together

**The only true diversifiers in stress:** USD (flight to safety), Short-dated government bonds, VIX calls (expensive insurance), Gold (sometimes)

---

### Measuring Portfolio Correlation

Correlation coefficient ranges from -1 (perfect inverse) to +1 (perfect positive):
- 0.0-0.3: Low correlation (good diversification)
- 0.3-0.6: Moderate (some diversification benefit)
- 0.6-0.9: High (limited diversification)
- 0.9-1.0: Near-perfect (no diversification — you just own the same thing twice)

*Common mistake: owning multiple tech stocks thinking you're diversified. NVDA, AMD, QCOM, AMAT all have 0.7+ correlation.*

---

### Tail Risk Hedging

Professional approach to tail risk (extreme negative outcomes):

**Option-based Hedges:**
- Buy out-of-the-money put options on the S&P 500
- Cost: typically 1-2% of portfolio annually in "insurance premium"
- Payoff: 5-15× in a severe correction

**Volatility Exposure:**
- Long VIX calls (cheap when VIX is low)
- VXX/UVXY as short-term hedges
- Note: These decay rapidly in calm markets

**Cross-Asset Hedges:**
- Long gold (performs in stagflation and monetary crises)
- Long JPY (yen strengthens in risk-off due to carry unwind)
- Long treasuries (works in deflationary recessions — 2008, 2020)

**The Barbell Strategy (Nassim Taleb):**
90% in ultra-safe assets (cash, treasuries), 10% in high-convexity bets (options, venture). Expected return similar to 60/40 but dramatically different risk profile.
      `
    },
  ],
  signals: [
    {
      id:'reading-signals',
      title:'How to Read and Act on Market Signals',
      tag:'PLATFORM GUIDE',
      tagCol:'var(--gn)',
      summary:'Professional framework for interpreting the signals on this platform',
      content:`
## How to Use Market Signals Professionally

The Signals panel on this platform aggregates conviction-weighted signals across macro, technical, and fundamental dimensions. Here is how to interpret and act on them professionally.

---

### Signal Hierarchy

Not all signals are equal. Professional signal classification:

**Tier 1 — Structural / Regime Signals (months to years)**
Macro regime shifts, central bank pivots, debt cycle turns. These override everything else. Once identified, position accordingly for the medium term.
*Example: "Fed Pivot" signal with 85%+ confidence → multi-month tailwind for risk assets*

**Tier 2 — Catalyst Signals (weeks to months)**
Earnings inflection, sector rotation, geopolitical event impact, regulatory change. Medium-term positioning adjustments.
*Example: "Bank Q2 Earnings" catalyst → tactical overweight financials ahead of results*

**Tier 3 — Technical / Momentum Signals (days to weeks)**
Price pattern, RSI divergence, volume climax, breakout. Short-term timing within a medium-term thesis.
*Example: "SPX above MA200" momentum → trend intact, don't fight it*

---

### Confidence Thresholds for Action

| Confidence | Interpretation | Action |
|-----------|----------------|--------|
| 85%+ | Very high conviction | Full position |
| 70-84% | High conviction | 2/3 position |
| 55-69% | Moderate | 1/3 position, watch |
| Below 55% | Low conviction | Monitor only |

**Never act on a single signal.** Look for confluence: a macro signal, a technical signal, AND a fundamental catalyst all pointing the same direction. That's where the highest probability setups are found.

---

### The Signal Flow Protocol

1. **Start with regime** (Signals panel, macro signals) — what is the macro environment?
2. **Identify sector tailwinds** — which sectors benefit from this regime?
3. **Screen for individual assets** — within the right sector, which specific names have the best setup?
4. **Check technical timing** — is the price action confirming or contradicting your view?
5. **Run Investing Lenses** — get an independent multi-framework perspective on your top idea
6. **Size appropriately** — use the position size calculator in the Learn section

---

### Common Mistakes in Signal Interpretation

**Confirmation bias:** Only noticing signals that confirm your existing view. Force yourself to steelman the opposing view.

**Signal stacking:** Using signals that are all derived from the same underlying factor (momentum signals from price, earnings, and analyst revisions are all correlated). Think about what independent evidence you have.

**Ignoring timeframes:** A bullish 3-month signal and a bearish 3-year signal are not contradictory — they operate on different timeframes. Your investment horizon determines which matters.

**Confusing cause and effect:** A signal that "gold is rising" is not by itself a buy signal for gold. Ask WHY it's rising — the reason determines whether the move continues.
      `
    },
    {
      id:'investing-lenses',
      title:'Working with Investing Lenses',
      tag:'PLATFORM GUIDE',
      tagCol:'var(--gn)',
      summary:'How to interpret multi-framework AI analysis and integrate it with your own research',
      content:`
## Working with Investing Lenses

Investing Lenses evaluates any asset through five distinct **investing philosophies** — not attributed to, named after, or impersonating any real investor, fund manager, or public figure. Each lens is fed with **terminal data** (live price, regime, macro signals, financials, earnings, news) plus live web search. Optional **Interrogate mode** lets you submit your own thesis for stress-testing.

---

### Understanding Each Lens

**Value Lens (Fundamentals & Margin of Safety)**
Focuses on: Intrinsic value, moat durability, management quality, margin of safety. Asks: Is the business understandable and priced below fair value?
*BUY signals: Strong fundamentals with clear moat at reasonable valuation*
*AVOID signals: Price too high for intrinsic value, or business quality unclear*

**Quality Compounders (Durable Growth & Reinvestment)**
Focuses on: Reinvestment runway, return on capital, what could permanently impair the business. Inverts the thesis first.
*AVOID is the most powerful signal — permanent impairment risks outweigh upside*

**Catalyst Lens (Concentrated & Event-Driven)**
Focuses on: Specific catalysts, corporate structure, events that unlock value, asymmetric payoff.
*BUY signals: Clear catalyst identified, sum-of-parts undervaluation, actionable timeline*

**Global Macro Lens (Cycles & Cross-Asset)**
Focuses on: Debt cycles, rates, liquidity, currency dynamics, correlation to macro regime.
*Critical for understanding WHEN to buy, not just WHAT to buy*

**Trend Lens (Momentum & Positioning)**
Focuses on: Price action, flows, positioning, narrative momentum relative to fundamentals.
*Most useful for timing entries and exits within a longer thesis*

**Risk Synthesis (Final Synthesis)**
Synthesises all five lenses and identifies the key risks to the bullish thesis. Pay particular attention when synthesis concerns are material — this is where single-lens optimism most commonly gets things wrong.

---

### How to Integrate Lens Analysis with Your Own Research

Investing Lenses is a research accelerator, not a decision-maker. Professional use:

1. **Run lenses AFTER you've formed your own view** — not before. This prevents anchoring to the AI's output.

2. **Look for the steelman of the opposing view** — if all lenses are unanimously bullish and you're also bullish, that's when to be most cautious. Where is the bear case?

3. **Use Risk Synthesis as a checklist** — the risks identified should be addressed in your own analysis before acting.

4. **Calibrate confidence** — Lens unanimity (all BUY) warrants more confidence than a split vote. A 3:2 split means you need to think carefully about why the two dissenting frameworks are wrong.

5. **Re-run after major news** — Lenses use live web search. Run again after earnings, macro data releases, or management changes.

---

### Limitations to Always Keep in Mind

- AI analysis reflects patterns in training data — it can miss genuinely novel situations
- Lenses cannot access real-time price data (uses search, not a live feed)
- Consensus lens views may reflect market consensus, not independent alpha
- No AI can substitute for deep domain expertise in niche sectors
- Analysis is philosophy-based only — not the opinion of any real person

*Everything on this platform is for research and educational purposes only. Not investment advice.*
      `
    },
  ],
};

// ─── Economics Data ───
async function fetchEcoData(country, indicator) {
  const key = `${country}_${indicator}`;
  if (_ecoData[key]) return _ecoData[key];
  const seq = ++_ecoSeq;
  _ecoLoading = true;
  _refreshView();
  try {
    const res = await fetch(`/api/economics?country=${encodeURIComponent(country)}&indicator=${encodeURIComponent(indicator)}&periods=25`, { signal: AbortSignal.timeout(10000) });
    if (res.ok) { const d = await res.json(); _ecoData[key] = d.data || []; }
  } catch(e) {}
  if (seq === _ecoSeq) {
    _ecoLoading = false;
    _refreshView();
  }
  return _ecoData[key] || [];
}

// Simple SVG line chart (no external library dependency)
function _ecoSVG(data, col) {
  if (!data || data.length < 2) return `<div style="padding:20px;text-align:center;font-family:var(--mn);font-size:10px;color:var(--t3)">No data available</div>`;
  const vals = data.map(d => d.value);
  const min = Math.min(...vals), max = Math.max(...vals), rng = max - min || 1;
  const W = 300, H = 80;
  const pts = data.map((d, i) => `${(i/(data.length-1))*W},${H - ((d.value-min)/rng)*H*0.85 - H*0.05}`).join(' ');
  const latest = data[data.length-1];
  const prev = data[data.length-2];
  const up = latest.value >= prev.value;
  const lineCol = up ? 'var(--gn)' : 'var(--rd)';
  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;height:80px;display:block">
    <polyline points="${pts}" fill="none" stroke="${lineCol}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="${W}" cy="${H - ((latest.value-min)/rng)*H*0.85 - H*0.05}" r="3" fill="${lineCol}"/>
  </svg>
  <div style="display:flex;justify-content:space-between;font-family:var(--mn);font-size:9px;color:var(--t3);margin-top:4px">
    <span>${data[0].year}</span>
    <span style="font-size:12px;font-weight:800;color:${lineCol}">${latest.value}%</span>
    <span>${latest.year}</span>
  </div>`;
}

function renderLearn() {
  const tabs = [
    ['macro','🌍 Macro'],
    ['fundamental','📊 Fundamental'],
    ['technical','⚡ Technical'],
    ['portfolio','🛡 Risk & Portfolio'],
    ['signals','🤖 AI & Signals'],
    ['economics','📈 Live Economics'],
    ['calc','🧮 Calculators'],
  ];
  let h = _renderPgHdr("Learn", "Professional analysis frameworks · Hedge fund methodologies");
  h += _renderSiteIntelCard("learn");
  h += `<div class="tabs">${tabs.map(([id,lb])=>`<button class="${_learnTab===id?'on':''}" onclick="_lt('${id}')">${lb}</button>`).join('')}</div>`;

  if (_learnSub) {
    h += renderLearnArticle(_learnSub);
    return h;
  }

  if (_learnTab === 'economics') return h + renderEconomicsSection();
  if (_learnTab === 'calc') return h + renderCalcs();

  const modules = LEARN_MODULES[_learnTab] || [];
  modules.forEach(m => {
    h += `<div class="gc gc-a" onclick="_openLearnSub('${m.id}')" style="padding:18px;margin-bottom:12px;border-left:3px solid ${m.tagCol}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">
        <span style="font-family:var(--mn);font-size:9px;background:${m.tagCol}18;color:${m.tagCol};padding:2px 8px;border-radius:4px;font-weight:700">${m.tag}</span>
        <span style="font-family:var(--mn);font-size:9px;color:var(--t3)">READ →</span>
      </div>
      <div style="font-family:var(--sn);font-size:17px;font-weight:800;color:var(--tx);margin-bottom:6px;line-height:1.2">${m.title}</div>
      <div style="font-family:var(--sn);font-size:12px;color:var(--t2);line-height:1.55">${m.summary}</div>
    </div>`;
  });

  if (!modules.length) h += `<div class="gc" style="padding:24px;text-align:center;color:var(--t2)">Content coming soon</div>`;
  return h;
}

function _lt(tab) { _learnTab=tab; _learnSub=null; _refreshView(); if(tab==='economics')fetchEcoData(_ecoCountry,_ecoIndicator); }
function _openLearnSub(id) { _learnSub=id; _refreshView(); if(typeof document!=='undefined')setTimeout(()=>document.querySelector('.main')?.scrollTo(0,0),50); }

function renderLearnArticle(id) {
  const all = Object.values(LEARN_MODULES).flat();
  const m = all.find(x => x.id === id);
  if (!m) return `<div class="gc" style="padding:24px;text-align:center;color:var(--rd)">Article not found</div>`;

  let h = `<button onclick="_learnSub=null;_refreshView()" style="background:var(--b2);border:1px solid var(--gb);color:var(--t2);padding:7px 16px;border-radius:6px;cursor:pointer;font-family:var(--mn);font-size:10px;margin-bottom:16px">← Back</button>`;
  h += `<span style="font-family:var(--mn);font-size:9px;background:${m.tagCol}18;color:${m.tagCol};padding:3px 10px;border-radius:4px;font-weight:700;display:inline-block;margin-bottom:12px">${m.tag}</span>`;
  h += `<h1 style="font-family:var(--sn);font-size:22px;font-weight:800;color:var(--tx);line-height:1.2;margin-bottom:10px">${m.title}</h1>`;
  h += `<div style="font-family:var(--sn);font-size:13px;color:var(--t2);font-style:italic;margin-bottom:20px;line-height:1.6;padding:12px 16px;background:var(--b1);border-radius:8px;border-left:3px solid ${m.tagCol}">${m.summary}</div>`;

  // Render markdown-like content
  const sections = m.content.trim().split('\n---\n');
  sections.forEach(section => {
    const lines = section.trim().split('\n');
    let html = '';
    lines.forEach(line => {
      if (line.startsWith('## ')) {
        html += `<h2 style="font-family:var(--sn);font-size:18px;font-weight:800;color:var(--tx);margin:20px 0 10px;padding-bottom:8px;border-bottom:1px solid var(--gb)">${line.slice(3)}</h2>`;
      } else if (line.startsWith('### ')) {
        html += `<h3 style="font-family:var(--sn);font-size:15px;font-weight:700;color:var(--gd);margin:16px 0 8px">${line.slice(4)}</h3>`;
      } else if (line.startsWith('**') && line.endsWith('**') && !line.slice(2,-2).includes('**')) {
        html += `<div style="font-family:var(--sn);font-size:13px;font-weight:700;color:var(--tx);margin:10px 0 4px">${line.slice(2,-2)}</div>`;
      } else if (line.startsWith('*') && line.endsWith('*') && !line.slice(1,-1).includes('*')) {
        html += `<div style="font-family:var(--sn);font-size:12px;color:var(--gd);font-style:italic;padding:8px 12px;background:var(--gdG);border-radius:6px;margin:8px 0">${line.slice(1,-1)}</div>`;
      } else if (line.startsWith('| ')) {
        // Table row
        if (!html.includes('<table')) html += `<div style="overflow-x:auto;margin:12px 0"><table style="width:100%;border-collapse:collapse;font-family:var(--mn);font-size:11px">`;
        const cells = line.split('|').filter(c=>c.trim()&&!c.trim().match(/^[-\s]+$/));
        const isHeader = !html.includes('<td');
        const tag = isHeader ? 'th' : 'td';
        const style = isHeader ? 'padding:8px 10px;text-align:left;font-size:9px;color:var(--t3);letter-spacing:0.1em;border-bottom:1px solid var(--gb);background:var(--b1)' : 'padding:7px 10px;border-bottom:1px solid rgba(255,255,255,0.03);color:var(--t2)';
        html += `<tr>${cells.map(c=>`<${tag} style="${style}">${c.trim()}</${tag}>`).join('')}</tr>`;
        return;
      } else if (line.startsWith('- ')) {
        html += `<div style="font-family:var(--sn);font-size:13px;color:var(--t2);padding:3px 0;display:flex;gap:8px;line-height:1.55"><span style="color:var(--gd);flex-shrink:0">→</span>${line.slice(2).replace(/\*\*([^*]+)\*\*/g,'<strong style="color:var(--tx)">$1</strong>')}</div>`;
      } else if (line.trim()) {
        const processed = line.replace(/\*\*([^*]+)\*\*/g,'<strong style="color:var(--tx)">$1</strong>');
        html += `<p style="font-family:var(--sn);font-size:13px;color:var(--t2);line-height:1.7;margin:6px 0">${processed}</p>`;
      } else {
        if (html.includes('<table') && !html.includes('</table>')) html += '</table></div>';
      }
    });
    if (html.includes('<table') && !html.includes('</table>')) html += '</table></div>';
    h += `<div style="margin-bottom:16px">${html}</div>`;
  });

  h += `<div style="margin-top:24px;padding:14px;background:var(--b1);border-radius:10px;border-top:3px solid var(--gd);font-family:var(--mn);font-size:9px;color:var(--t3);text-align:center">Research purposes only · Not investment advice · The Dispatch Markets</div>`;
  return h;
}

function renderEconomicsSection() {
  const ind = ECO_INDICATORS.find(i => i.code === _ecoIndicator) || ECO_INDICATORS[0];
  const country = ECO_COUNTRIES.find(c => c.code === _ecoCountry);
  const data = _ecoData[`${_ecoCountry}_${_ecoIndicator}`] || [];

  let h = `<div class="gc" style="padding:14px;margin-bottom:12px">
    <div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.15em;margin-bottom:10px">SELECT INDICATOR</div>
    <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px">
      ${ECO_INDICATORS.map(i=>`<button onclick="_setEco('ind','${i.code}')" style="font-family:var(--sn);font-size:11px;padding:6px 12px;border-radius:8px;cursor:pointer;border:1px solid ${_ecoIndicator===i.code?'var(--gd)':'var(--gb)'};background:${_ecoIndicator===i.code?'var(--gdG)':'var(--b2)'};color:${_ecoIndicator===i.code?'var(--gd)':'var(--t2)'};white-space:nowrap">${i.name}</button>`).join('')}
    </div>
    <div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.15em;margin-bottom:8px">SELECT COUNTRY</div>
    <div style="display:flex;gap:6px;flex-wrap:wrap">
      ${ECO_COUNTRIES.map(c=>`<button onclick="_setEco('country','${c.code}')" style="font-family:var(--sn);font-size:11px;padding:6px 12px;border-radius:8px;cursor:pointer;border:1px solid ${_ecoCountry===c.code?'var(--bl)':'var(--gb)'};background:${_ecoCountry===c.code?'var(--blG)':'var(--b2)'};color:${_ecoCountry===c.code?'var(--bl)':'var(--t2)'};white-space:nowrap">${c.name}</button>`).join('')}
    </div>
  </div>`;

  h += `<div class="gc" style="padding:16px;margin-bottom:12px">
    <div style="font-family:var(--sn);font-size:16px;font-weight:700;margin-bottom:4px">${ind.name} — ${country?.name}</div>
    <div style="font-family:var(--sn);font-size:12px;color:var(--t2);margin-bottom:12px;line-height:1.6;padding:10px;background:var(--gdG);border-radius:8px;border-left:3px solid var(--gd)">${ind.desc}</div>
    ${_ecoLoading ? `<div style="padding:20px;text-align:center;font-family:var(--mn);font-size:10px;color:var(--t3)"><div style="width:12px;height:12px;border:2px solid var(--bl);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 8px"></div>Loading from World Bank…</div>` : _ecoSVG(data)}
    ${data.length ? `<div style="font-family:var(--sn);font-size:12px;color:var(--t2);margin-top:10px;line-height:1.65;padding:10px;background:var(--b1);border-radius:8px"><strong style="color:var(--gd)">Market implication:</strong> ${_getEcoImpl(ind.code)}</div>` : ''}
  </div>`;

  if (!_ecoLoading && !data.length) {
    h += `<button onclick="fetchEcoData('${_ecoCountry}','${_ecoIndicator}')" style="width:100%;background:var(--gd);color:var(--bg);border:none;border-radius:8px;padding:12px;font-family:var(--sn);font-size:13px;font-weight:700;cursor:pointer;margin-bottom:12px">Load Data from World Bank</button>`;
  }

  return h;
}

function _getEcoImpl(code) {
  const m = {
    'NY.GDP.MKTP.KD.ZG':'GDP >3% = risk-on (equities, credit). GDP <1% = defensive (bonds, gold, cash). GDP negative 2 quarters = recession — maximum defensiveness.',
    'FP.CPI.TOTL.ZG':'CPI >4% = rate hikes likely → rotate to value, banks, short duration. CPI <2% = cuts possible → growth stocks, long duration bonds benefit.',
    'SL.UEM.TOTL.ZS':'Rising unemployment = economic weakness → defensive sectors (staples, healthcare, utilities). Low/falling = risk-on → cyclicals, consumer discretionary.',
    'FR.INR.RINR':'Negative real rates = loose conditions → risk assets supported (equities, gold, EM). Rising real rates = headwind for growth stocks and property.',
    'NE.TRD.GNFS.ZS':'High trade openness = sensitive to global demand and currency. Trade wars or supply shocks have outsized economic impact on high-trade economies.',
    'GC.DOD.TOTL.GD.ZS':'Debt >100% GDP = limited fiscal stimulus room. Structural growth headwind. Risk of fiscal dominance (printing to monetise debt = inflation risk).',
  };
  return m[code] || 'Monitor trends over time relative to consensus forecasts.';
}

function _setEco(type, value) {
  if (type === 'country') _ecoCountry = value;
  else _ecoIndicator = value;
  _refreshView();
  fetchEcoData(_ecoCountry, _ecoIndicator);
}

// ─── Financial Calculators ───
function renderCalcs() {
  const calcTabs = [['compound','Compound Interest'],['position','Position Size'],['pe','P/E Target'],['kelly','Kelly Criterion'],['roi','ROI & CAGR']];
  let h = `<div class="tabs" style="margin-bottom:14px">${calcTabs.map(([id,lb])=>`<button class="${_calcTab===id?'on':''}" onclick="_ct('${id}')">${lb}</button>`).join('')}</div>`;
  if (_calcTab==='compound') h += renderCompoundCalc();
  else if (_calcTab==='position') h += renderPositionCalc();
  else if (_calcTab==='pe') h += renderPECalc();
  else if (_calcTab==='kelly') h += renderKellyCalc();
  else if (_calcTab==='roi') h += renderROICalc();
  return h;
}
function _ct(tab) { _calcTab=tab; _refreshView(); }

function renderCompoundCalc() {
  return `<div class="gc" style="padding:18px">
    <div style="font-family:var(--sn);font-size:16px;font-weight:700;margin-bottom:4px">Compound Interest Calculator</div>
    <div style="font-family:var(--sn);font-size:12px;color:var(--t2);margin-bottom:14px">The most powerful force in investing — Einstein called it the eighth wonder of the world.</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px">
      <div><label style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;display:block;margin-bottom:6px">INITIAL INVESTMENT ($)</label><input id="ci_principal" type="number" value="10000" style="width:100%;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:11px 14px;color:var(--tx);font-size:16px;outline:none;font-family:var(--mn)"></div>
      <div><label style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;display:block;margin-bottom:6px">MONTHLY ADDITION ($)</label><input id="ci_monthly" type="number" value="500" style="width:100%;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:11px 14px;color:var(--tx);font-size:16px;outline:none;font-family:var(--mn)"></div>
      <div><label style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;display:block;margin-bottom:6px">ANNUAL RETURN (%)</label><input id="ci_rate" type="number" value="10" step="0.1" style="width:100%;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:11px 14px;color:var(--tx);font-size:16px;outline:none;font-family:var(--mn)"></div>
      <div><label style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;display:block;margin-bottom:6px">YEARS</label><input id="ci_years" type="number" value="20" min="1" max="50" style="width:100%;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:11px 14px;color:var(--tx);font-size:16px;outline:none;font-family:var(--mn)"></div>
    </div>
    <button onclick="_calcCompound()" style="width:100%;background:var(--gd);color:var(--bg);border:none;border-radius:8px;padding:13px;font-family:var(--sn);font-size:14px;font-weight:700;cursor:pointer;margin-bottom:14px">Calculate</button>
    <div id="ci_result"></div>
  </div>`;
}
function _calcCompound() {
  const p=+document.getElementById('ci_principal').value||0;
  const m=+document.getElementById('ci_monthly').value||0;
  const r=+document.getElementById('ci_rate').value/100||0;
  const y=+document.getElementById('ci_years').value||20;
  const mr=r/12;let bal=p,contrib=p;
  const milestones=[];
  for(let yr=1;yr<=y;yr++){for(let mo=0;mo<12;mo++){bal=bal*(1+mr)+m;}contrib+=m*12;if([5,10,15,20,25,30].includes(yr))milestones.push({yr,bal:Math.round(bal)});}
  const interest=Math.round(bal-contrib);
  const fmt=n=>n>=1e6?`$${(n/1e6).toFixed(2)}M`:n>=1e3?`$${(n/1e3).toFixed(0)}K`:`$${n.toFixed(0)}`;
  document.getElementById('ci_result').innerHTML=`
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1px;background:var(--gb);border-radius:8px;overflow:hidden;margin-bottom:10px">
      <div style="background:var(--bg);padding:12px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">FINAL VALUE</div><div style="font-family:var(--mn);font-size:18px;font-weight:900;color:var(--gn)">${fmt(Math.round(bal))}</div></div>
      <div style="background:var(--bg);padding:12px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">INVESTED</div><div style="font-family:var(--mn);font-size:18px;font-weight:900;color:var(--tx)">${fmt(Math.round(contrib))}</div></div>
      <div style="background:var(--bg);padding:12px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">RETURNS</div><div style="font-family:var(--mn);font-size:18px;font-weight:900;color:var(--gd)">${fmt(interest)}</div></div>
    </div>
    <div style="font-family:var(--mn);font-size:10px;color:var(--t3)">${milestones.map(ms=>`Yr ${ms.yr}: ${fmt(ms.bal)}`).join(' · ')}</div>`;
}

function renderKellyCalc() {
  return `<div class="gc" style="padding:18px">
    <div style="font-family:var(--sn);font-size:16px;font-weight:700;margin-bottom:4px">Kelly Criterion Position Sizer</div>
    <div style="font-family:var(--sn);font-size:12px;color:var(--t2);margin-bottom:14px;line-height:1.6">Used by Buffett, Munger, and professional gamblers. Calculates the mathematically optimal position size given your edge and payoff ratio.</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px">
      <div><label style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;display:block;margin-bottom:6px">WIN PROBABILITY (%)</label><input id="kl_prob" type="number" value="60" min="1" max="99" style="width:100%;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:11px 14px;color:var(--tx);font-size:16px;outline:none;font-family:var(--mn)"></div>
      <div><label style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;display:block;margin-bottom:6px">WIN AMOUNT (%)</label><input id="kl_win" type="number" value="30" style="width:100%;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:11px 14px;color:var(--tx);font-size:16px;outline:none;font-family:var(--mn)"></div>
      <div><label style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;display:block;margin-bottom:6px">LOSS AMOUNT (%)</label><input id="kl_loss" type="number" value="15" style="width:100%;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:11px 14px;color:var(--tx);font-size:16px;outline:none;font-family:var(--mn)"></div>
      <div><label style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;display:block;margin-bottom:6px">PORTFOLIO SIZE ($)</label><input id="kl_port" type="number" value="100000" style="width:100%;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:11px 14px;color:var(--tx);font-size:16px;outline:none;font-family:var(--mn)"></div>
    </div>
    <button onclick="_calcKelly()" style="width:100%;background:var(--gd);color:var(--bg);border:none;border-radius:8px;padding:13px;font-family:var(--sn);font-size:14px;font-weight:700;cursor:pointer;margin-bottom:14px">Calculate Kelly Size</button>
    <div id="kl_result"></div>
  </div>`;
}
function _calcKelly() {
  const p=+document.getElementById('kl_prob').value/100;
  const w=+document.getElementById('kl_win').value/100;
  const l=+document.getElementById('kl_loss').value/100;
  const port=+document.getElementById('kl_port').value;
  const kelly=((p*w-(1-p)*l)/(w));
  const half=kelly/2;
  const fullPos=Math.round(kelly*port);
  const halfPos=Math.round(half*port);
  const col=kelly>0?'var(--gn)':'var(--rd)';
  document.getElementById('kl_result').innerHTML=kelly<=0?
    `<div style="color:var(--rd);font-family:var(--sn);font-size:13px;padding:12px;background:var(--rdG);border-radius:8px">Negative Kelly — no edge in this trade. Do not enter.</div>`:
    `<div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--gb);border-radius:8px;overflow:hidden;margin-bottom:10px">
      <div style="background:var(--bg);padding:12px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">FULL KELLY (${(kelly*100).toFixed(1)}%)</div><div style="font-family:var(--mn);font-size:18px;font-weight:900;color:${col}">$${fullPos.toLocaleString()}</div></div>
      <div style="background:var(--bg);padding:12px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">HALF KELLY ★ (${(half*100).toFixed(1)}%)</div><div style="font-family:var(--mn);font-size:18px;font-weight:900;color:var(--gd)">$${halfPos.toLocaleString()}</div></div>
    </div>
    <div style="font-family:var(--sn);font-size:12px;color:var(--t2);padding:10px;background:var(--gdG);border-radius:8px">Professionals use Half Kelly (★) to reduce variance. Full Kelly maximises long-run growth but produces stomach-churning drawdowns.</div>`;
}

function renderPositionCalc() {
  return `<div class="gc" style="padding:18px">
    <div style="font-family:var(--sn);font-size:16px;font-weight:700;margin-bottom:4px">Risk-Based Position Sizer</div>
    <div style="font-family:var(--sn);font-size:12px;color:var(--t2);margin-bottom:14px">Professional method: risk a fixed % of portfolio, sized by distance to stop loss.</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px">
      <div><label style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;display:block;margin-bottom:6px">PORTFOLIO SIZE ($)</label><input id="ps_port" type="number" value="100000" style="width:100%;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:11px 14px;color:var(--tx);font-size:16px;outline:none;font-family:var(--mn)"></div>
      <div><label style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;display:block;margin-bottom:6px">MAX RISK PER TRADE (%)</label><input id="ps_risk" type="number" value="1" step="0.5" min="0.1" max="5" style="width:100%;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:11px 14px;color:var(--tx);font-size:16px;outline:none;font-family:var(--mn)"></div>
      <div><label style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;display:block;margin-bottom:6px">ENTRY PRICE ($)</label><input id="ps_entry" type="number" value="100" style="width:100%;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:11px 14px;color:var(--tx);font-size:16px;outline:none;font-family:var(--mn)"></div>
      <div><label style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;display:block;margin-bottom:6px">STOP LOSS ($)</label><input id="ps_stop" type="number" value="92" style="width:100%;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:11px 14px;color:var(--tx);font-size:16px;outline:none;font-family:var(--mn)"></div>
    </div>
    <button onclick="_calcPosition()" style="width:100%;background:var(--gd);color:var(--bg);border:none;border-radius:8px;padding:13px;font-family:var(--sn);font-size:14px;font-weight:700;cursor:pointer;margin-bottom:14px">Calculate</button>
    <div id="ps_result"></div>
  </div>`;
}
function _calcPosition() {
  const port=+document.getElementById('ps_port').value;
  const risk=+document.getElementById('ps_risk').value/100;
  const entry=+document.getElementById('ps_entry').value;
  const stop=+document.getElementById('ps_stop').value;
  if(entry<=stop){document.getElementById('ps_result').innerHTML=`<div style="color:var(--rd);font-family:var(--mn);font-size:10px">Stop loss must be below entry price</div>`;return;}
  const riskAmt=port*risk;
  const riskPerShare=entry-stop;
  const shares=Math.floor(riskAmt/riskPerShare);
  const posVal=shares*entry;
  const pctPort=(posVal/port*100).toFixed(1);
  const col=parseFloat(pctPort)>20?'var(--rd)':parseFloat(pctPort)>10?'var(--gd)':'var(--gn)';
  document.getElementById('ps_result').innerHTML=`
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--gb);border-radius:8px;overflow:hidden">
      <div style="background:var(--bg);padding:12px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">SHARES TO BUY</div><div style="font-family:var(--mn);font-size:20px;font-weight:900;color:var(--gd)">${shares.toLocaleString()}</div></div>
      <div style="background:var(--bg);padding:12px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">POSITION VALUE</div><div style="font-family:var(--mn);font-size:20px;font-weight:900;color:var(--tx)">$${posVal.toLocaleString()}</div></div>
      <div style="background:var(--bg);padding:12px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">MAX LOSS</div><div style="font-family:var(--mn);font-size:16px;font-weight:700;color:var(--rd)">$${riskAmt.toLocaleString()}</div></div>
      <div style="background:var(--bg);padding:12px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">% OF PORTFOLIO</div><div style="font-family:var(--mn);font-size:16px;font-weight:700;color:${col}">${pctPort}%</div></div>
    </div>`;
}

function renderPECalc() {
  return `<div class="gc" style="padding:18px">
    <div style="font-family:var(--sn);font-size:16px;font-weight:700;margin-bottom:4px">P/E Target Price Calculator</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px">
      <div><label style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;display:block;margin-bottom:6px">CURRENT EPS ($)</label><input id="pe_eps" type="number" value="5.00" step="0.01" style="width:100%;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:11px 14px;color:var(--tx);font-size:16px;outline:none;font-family:var(--mn)"></div>
      <div><label style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;display:block;margin-bottom:6px">EPS GROWTH (%/yr)</label><input id="pe_growth" type="number" value="12" style="width:100%;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:11px 14px;color:var(--tx);font-size:16px;outline:none;font-family:var(--mn)"></div>
      <div><label style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;display:block;margin-bottom:6px">TARGET P/E MULTIPLE</label><input id="pe_multiple" type="number" value="20" style="width:100%;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:11px 14px;color:var(--tx);font-size:16px;outline:none;font-family:var(--mn)"></div>
      <div><label style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;display:block;margin-bottom:6px">YEARS FORWARD</label><input id="pe_years" type="number" value="3" min="1" max="10" style="width:100%;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:11px 14px;color:var(--tx);font-size:16px;outline:none;font-family:var(--mn)"></div>
    </div>
    <button onclick="_calcPE()" style="width:100%;background:var(--gd);color:var(--bg);border:none;border-radius:8px;padding:13px;font-family:var(--sn);font-size:14px;font-weight:700;cursor:pointer;margin-bottom:14px">Calculate Target Price</button>
    <div id="pe_result"></div>
  </div>`;
}
function _calcPE() {
  const eps=+document.getElementById('pe_eps').value;
  const g=+document.getElementById('pe_growth').value/100;
  const pe=+document.getElementById('pe_multiple').value;
  const yr=+document.getElementById('pe_years').value;
  const futureEps=eps*Math.pow(1+g,yr);
  const target=futureEps*pe;
  const peg=(pe/(g*100)).toFixed(2);
  document.getElementById('pe_result').innerHTML=`
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1px;background:var(--gb);border-radius:8px;overflow:hidden">
      <div style="background:var(--bg);padding:12px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">FUTURE EPS (Yr ${yr})</div><div style="font-family:var(--mn);font-size:18px;font-weight:900;color:var(--bl)">$${futureEps.toFixed(2)}</div></div>
      <div style="background:var(--bg);padding:12px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">TARGET PRICE</div><div style="font-family:var(--mn);font-size:18px;font-weight:900;color:var(--gn)">$${target.toFixed(2)}</div></div>
      <div style="background:var(--bg);padding:12px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">PEG RATIO</div><div style="font-family:var(--mn);font-size:18px;font-weight:900;color:${parseFloat(peg)<1?'var(--gn)':parseFloat(peg)<2?'var(--gd)':'var(--rd)'}">${peg}x</div></div>
    </div>
    <div style="font-family:var(--sn);font-size:11px;color:var(--t3);margin-top:8px">PEG < 1.0 = potentially undervalued for growth rate (Lynch rule). PEG > 2 = expensive.</div>`;
}

function renderROICalc() {
  return `<div class="gc" style="padding:18px">
    <div style="font-family:var(--sn);font-size:16px;font-weight:700;margin-bottom:4px">Investment Return Calculator</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px">
      <div><label style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;display:block;margin-bottom:6px">BUY PRICE ($)</label><input id="roi_buy" type="number" value="100" style="width:100%;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:11px 14px;color:var(--tx);font-size:16px;outline:none;font-family:var(--mn)"></div>
      <div><label style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;display:block;margin-bottom:6px">CURRENT PRICE ($)</label><input id="roi_sell" type="number" value="145" style="width:100%;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:11px 14px;color:var(--tx);font-size:16px;outline:none;font-family:var(--mn)"></div>
      <div><label style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;display:block;margin-bottom:6px">SHARES HELD</label><input id="roi_shares" type="number" value="50" style="width:100%;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:11px 14px;color:var(--tx);font-size:16px;outline:none;font-family:var(--mn)"></div>
      <div><label style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.1em;display:block;margin-bottom:6px">HOLDING PERIOD (YRS)</label><input id="roi_years" type="number" value="3" step="0.5" style="width:100%;background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:11px 14px;color:var(--tx);font-size:16px;outline:none;font-family:var(--mn)"></div>
    </div>
    <button onclick="_calcROI()" style="width:100%;background:var(--gd);color:var(--bg);border:none;border-radius:8px;padding:13px;font-family:var(--sn);font-size:14px;font-weight:700;cursor:pointer;margin-bottom:14px">Calculate</button>
    <div id="roi_result"></div>
  </div>`;
}
function _calcROI() {
  const buy=+document.getElementById('roi_buy').value;
  const sell=+document.getElementById('roi_sell').value;
  const shares=+document.getElementById('roi_shares').value;
  const years=+document.getElementById('roi_years').value;
  const profit=(sell-buy)*shares;
  const roi=((sell-buy)/buy*100).toFixed(1);
  const cagr=((Math.pow(sell/buy,1/years)-1)*100).toFixed(1);
  const col=profit>=0?'var(--gn)':'var(--rd)';
  document.getElementById('roi_result').innerHTML=`
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:1px;background:var(--gb);border-radius:8px;overflow:hidden">
      <div style="background:var(--bg);padding:10px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">P&L</div><div style="font-family:var(--mn);font-size:16px;font-weight:900;color:${col}">${profit>=0?'+':'-'}$${Math.abs(Math.round(profit)).toLocaleString()}</div></div>
      <div style="background:var(--bg);padding:10px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">ROI</div><div style="font-family:var(--mn);font-size:16px;font-weight:900;color:${col}">${roi}%</div></div>
      <div style="background:var(--bg);padding:10px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">CAGR</div><div style="font-family:var(--mn);font-size:16px;font-weight:900;color:${col}">${cagr}%</div></div>
      <div style="background:var(--bg);padding:10px;text-align:center"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">VALUE</div><div style="font-family:var(--mn);font-size:16px;font-weight:900;color:var(--tx)">$${(sell*shares).toLocaleString()}</div></div>
    </div>`;
}

// ─── AI Document Intelligence ───
let _intelDoc = '';
let _intelResult = null;
let _intelLoading = false;
let _intelType = 'earnings';

const INTEL_TYPES = [
  ['earnings', '📞 Earnings Call'],
  ['10k', '📋 10-K / Annual Report'],
  ['news', '📰 News Article'],
  ['research', '🔬 Research Note'],
  ['any', '📄 Any Document'],
];

function renderDocIntel() {
  let h = _renderPgHdr("Document Intelligence", "Paste any financial document · AI extracts signals in seconds");
  h += _renderSiteIntelCard("intel");

  h += `<div style="background:var(--b1);border:1px solid var(--gb);border-radius:12px;padding:16px;margin-bottom:14px">
    <div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.15em;margin-bottom:10px">DOCUMENT TYPE</div>
    <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px">
      ${INTEL_TYPES.map(([id,lb])=>`<button onclick="_intelType='${id}';_refreshView()" style="font-family:var(--sn);font-size:11px;padding:6px 14px;border-radius:8px;cursor:pointer;border:1px solid ${_intelType===id?'var(--gd)':'var(--gb)'};background:${_intelType===id?'var(--gdG)':'var(--bg)'};color:${_intelType===id?'var(--gd)':'var(--t2)'}">${lb}</button>`).join('')}
    </div>
    <div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.12em;margin-bottom:8px">PASTE DOCUMENT TEXT</div>
    <textarea id="intelDoc" placeholder="Paste earnings call transcript, 10-K excerpt, news article, analyst note, or any financial text here…" style="width:100%;height:180px;background:var(--bg);border:1px solid var(--gb);border-radius:8px;padding:12px;color:var(--tx);font-size:13px;font-family:var(--sn);outline:none;resize:vertical;line-height:1.6" oninput="_intelDoc=this.value">${_intelDoc}</textarea>
    <div style="display:flex;gap:8px;margin-top:10px;align-items:center">
      <button onclick="_runIntel()" style="flex:1;background:linear-gradient(135deg,var(--bl),var(--pu));color:white;border:none;border-radius:8px;padding:13px;font-family:var(--sn);font-size:14px;font-weight:700;cursor:pointer">⬢ Analyse with AI</button>
      <button onclick="_intelDoc='';_intelResult=null;document.getElementById('intelDoc').value='';_refreshView()" style="background:var(--b2);border:1px solid var(--gb);color:var(--t2);border:none;border-radius:8px;padding:13px 16px;font-family:var(--sn);font-size:13px;cursor:pointer">Clear</button>
    </div>
  </div>`;

  if (_intelLoading) {
    h += `<div class="gc" style="padding:32px;text-align:center">
      <div style="width:16px;height:16px;border:2px solid var(--bl);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 14px"></div>
      <div style="font-family:var(--sn);font-size:14px;color:var(--t2);margin-bottom:6px">Analysing document…</div>
      <div style="font-family:var(--mn);font-size:10px;color:var(--t3)">AI is reading, extracting signals and identifying risks</div>
    </div>`;
  } else if (_intelResult) {
    h += renderIntelResult(_intelResult);
  } else {
    // Instructions
    h += `<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
      ${[
        ['📞 Earnings Call', 'Get instant bull/bear signals, management tone analysis, key numbers mentioned, and forward guidance summary'],
        ['📋 10-K / Annual Report', 'Extract risk factors, competitive moat analysis, financial health signals, and red flags from dense filings'],
        ['📰 News Article', 'Assess market impact, identify affected tickers, determine sentiment and signal direction'],
        ['🔬 Research Note', 'Extract analyst thesis, price target rationale, key assumptions, and where they might be wrong'],
      ].map(([title,desc]) => `<div class="gc" style="padding:14px">
        <div style="font-family:var(--sn);font-size:13px;font-weight:700;color:var(--tx);margin-bottom:6px">${title}</div>
        <div style="font-family:var(--sn);font-size:12px;color:var(--t2);line-height:1.55">${desc}</div>
      </div>`).join('')}
    </div>
    <div class="gc" style="padding:14px;margin-top:4px;border-left:3px solid var(--gd)">
      <div style="font-family:var(--mn);font-size:9px;color:var(--gd);margin-bottom:6px">COMPETING WITH ALPHASENSE & HEBBIA</div>
      <div style="font-family:var(--sn);font-size:12px;color:var(--t2);line-height:1.6">AlphaSense charges $2,000+/month for AI document search. Hebbia is enterprise-only. This platform gives you the same AI-powered document intelligence — paste any text and get institutional-quality analysis instantly.</div>
    </div>`;
  }

  return h;
}

function _extractJsonBlock(text) {
  if (!text) throw new Error('empty');
  const clean = String(text).replace(/```json|```/g, '').trim();
  try { return JSON.parse(clean); } catch (e) { /* fall through */ }
  const start = clean.indexOf('{');
  const end = clean.lastIndexOf('}');
  if (start >= 0 && end > start) return JSON.parse(clean.slice(start, end + 1));
  throw new Error('Invalid JSON');
}

async function _runIntel() {
  if (!_isPremium()) { _showLoginGate('AI Document Intelligence'); return; }
  _intelDoc = document.getElementById('intelDoc')?.value || _intelDoc;
  if (!_intelDoc.trim() || _intelDoc.trim().length < 50) {
    showToast('Please paste at least 50 characters of document text', 'var(--rd)');
    return;
  }
  _intelLoading = true;
  _intelResult = null;
  _refreshView();

  const typeLabels = { earnings:'earnings call transcript', '10k':'10-K annual report', news:'news article', research:'research note', any:'financial document' };
  const docType = typeLabels[_intelType] || 'financial document';

  try {
    const res = await fetch('/api/committee', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        max_tokens: 2000,
        system: 'You are an elite hedge fund document analyst. Reply with ONLY valid JSON — no markdown fences, no preamble.',
        messages: [{
          role: 'user',
          content: `Analyse this ${docType}. Return ONLY this JSON schema (no markdown):

{"documentType":"string","company":"string","ticker":"string","sentiment":"Bullish|Bearish|Neutral|Mixed","sentimentScore":0,"keyTakeaways":["..."],"bullishSignals":["..."],"bearishSignals":["..."],"keyNumbers":[{"metric":"name","value":"value","context":"why"}],"forwardGuidance":"string","riskFactors":["..."],"tradingImplication":"string","confidence":0,"summary":"2-3 sentences"}

DOCUMENT:
${_intelDoc.slice(0, 8000)}`
        }]
      })
    });

    const data = await res.json().catch(() => ({}));
    if (res.status === 401 || data.premium) {
      _intelLoading = false;
      _showLoginGate('AI Document Intelligence');
      return;
    }
    if (!res.ok) {
      const msg = data?.error?.message || data?.error || `API ${res.status}`;
      throw new Error(typeof msg === 'string' ? msg : 'API error');
    }
    // Provider response content blocks — take the final text block.
    const blocks = Array.isArray(data.content) ? data.content : [];
    const textBlocks = blocks.filter(b => b.type === 'text' && b.text).map(b => b.text);
    const raw = textBlocks.length ? textBlocks[textBlocks.length - 1] : (data.content?.[0]?.text || '');
    if (!raw) throw new Error(data?.error?.message || 'Empty model response');

    _intelResult = _extractJsonBlock(raw);
  } catch (e) {
    const detail = (e && e.message) ? String(e.message).slice(0, 160) : 'unknown error';
    _intelResult = {
      error: `Analysis failed — ${detail}. Confirm your premium membership and try a shorter excerpt.`
    };
  }

  _intelLoading = false;
  _refreshView();
}

function renderIntelResult(r) {
  if (r.error) return `<div class="gc" style="padding:20px;text-align:center;color:var(--rd)">${r.error}</div>`;

  const sentCol = r.sentiment==='Bullish'?'var(--gn)':r.sentiment==='Bearish'?'var(--rd)':r.sentiment==='Mixed'?'var(--gd)':'var(--bl)';
  const sentIcon = r.sentiment==='Bullish'?'↑':r.sentiment==='Bearish'?'↓':r.sentiment==='Mixed'?'↕':'●';

  let h = `<div class="gc" style="padding:0;overflow:hidden;margin-bottom:12px">
    <div style="display:flex;align-items:center;justify-content:space-between;padding:14px 16px;background:${sentCol}12;border-bottom:1px solid ${sentCol}20">
      <div>
        <div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.15em;margin-bottom:4px">${r.documentType?.toUpperCase()||'DOCUMENT ANALYSIS'} · ${r.company||'COMPANY'} ${r.ticker&&r.ticker!=='Unknown'?'('+r.ticker+')':''}</div>
        <div style="font-family:var(--sn);font-size:20px;font-weight:900;color:${sentCol}">${sentIcon} ${r.sentiment||'Neutral'}</div>
      </div>
      <div style="text-align:right">
        <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">AI CONFIDENCE</div>
        <div style="font-family:var(--mn);font-size:28px;font-weight:900;color:${sentCol}">${r.confidence||'—'}</div>
      </div>
    </div>
    <div style="padding:14px 16px;border-bottom:1px solid var(--gb)">
      <div style="font-family:var(--sn);font-size:13px;color:var(--tx);line-height:1.65">${r.summary||''}</div>
    </div>
  </div>`;

  // Key takeaways
  if (r.keyTakeaways?.length) {
    h += `<div class="gc" style="padding:14px;margin-bottom:10px">
      <div style="font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.18em;margin-bottom:10px">KEY TAKEAWAYS</div>
      ${r.keyTakeaways.map((k,i)=>`<div style="display:flex;gap:10px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);font-family:var(--sn);font-size:13px;color:var(--tx);line-height:1.55"><span style="font-family:var(--mn);font-weight:700;color:var(--gd);flex-shrink:0">${i+1}.</span>${k}</div>`).join('')}
    </div>`;
  }

  // Bull/Bear signals
  h += `<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px">`;
  if (r.bullishSignals?.length) {
    h += `<div class="gc" style="padding:14px;border-left:3px solid var(--gn)">
      <div style="font-family:var(--mn);font-size:8px;color:var(--gn);letter-spacing:0.15em;margin-bottom:8px">↑ BULLISH SIGNALS</div>
      ${r.bullishSignals.map(s=>`<div style="font-family:var(--sn);font-size:11px;color:var(--t2);padding:3px 0;line-height:1.5;display:flex;gap:6px"><span style="color:var(--gn);flex-shrink:0">+</span>${s}</div>`).join('')}
    </div>`;
  }
  if (r.bearishSignals?.length) {
    h += `<div class="gc" style="padding:14px;border-left:3px solid var(--rd)">
      <div style="font-family:var(--mn);font-size:8px;color:var(--rd);letter-spacing:0.15em;margin-bottom:8px">↓ BEARISH SIGNALS</div>
      ${r.bearishSignals.map(s=>`<div style="font-family:var(--sn);font-size:11px;color:var(--t2);padding:3px 0;line-height:1.5;display:flex;gap:6px"><span style="color:var(--rd);flex-shrink:0">−</span>${s}</div>`).join('')}
    </div>`;
  }
  h += `</div>`;

  // Key numbers
  if (r.keyNumbers?.length) {
    h += `<div class="gc" style="padding:14px;margin-bottom:10px">
      <div style="font-family:var(--mn);font-size:8px;color:var(--bl);letter-spacing:0.18em;margin-bottom:10px">KEY NUMBERS</div>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:8px">
        ${r.keyNumbers.map(n=>`<div style="background:var(--b1);border-radius:8px;padding:10px">
          <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:4px">${n.metric||''}</div>
          <div style="font-family:var(--mn);font-size:14px;font-weight:800;color:var(--tx)">${n.value||''}</div>
          <div style="font-family:var(--sn);font-size:10px;color:var(--t3);margin-top:3px;line-height:1.4">${n.context||''}</div>
        </div>`).join('')}
      </div>
    </div>`;
  }

  // Trading implication
  if (r.tradingImplication) {
    h += `<div class="gc" style="padding:14px;border-left:3px solid var(--gd);margin-bottom:10px">
      <div style="font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.18em;margin-bottom:6px">TRADING IMPLICATION</div>
      <div style="font-family:var(--sn);font-size:13px;color:var(--tx);line-height:1.65;font-weight:500">${r.tradingImplication}</div>
    </div>`;
  }

  // Risk factors
  if (r.riskFactors?.length) {
    h += `<div class="gc" style="padding:14px;border-left:3px solid var(--rd);margin-bottom:10px">
      <div style="font-family:var(--mn);font-size:8px;color:var(--rd);letter-spacing:0.18em;margin-bottom:8px">⚠ RISK FACTORS</div>
      ${r.riskFactors.map(rf=>`<div style="display:flex;gap:8px;padding:4px 0;border-bottom:1px solid rgba(255,71,87,0.06);font-family:var(--sn);font-size:11px;color:var(--t2);line-height:1.5"><span style="color:var(--rd);flex-shrink:0;font-weight:700">!</span>${rf}</div>`).join('')}
    </div>`;
  }

  h += `<div style="padding:10px;text-align:center;font-family:var(--mn);font-size:8px;color:var(--t3)">AI analysis · Research purposes only · Not investment advice</div>`;

  h += `<button onclick="_intelResult=null;_intelDoc='';_refreshView()" style="width:100%;background:var(--b2);border:none;color:var(--t2);border-radius:8px;padding:10px;font-family:var(--sn);font-size:12px;cursor:pointer;margin-top:6px">← Analyse Another Document</button>`;

  return h;
}

// ═══════════════════════════════════════════════════════════
// PAGE: WATCHLIST
// ═══════════════════════════════════════════════════════════
function renderWatch(){
  const wl=getActiveWl();
  const w=_wlAssetRows(wl);
  let h = _renderPgHdr("Watchlists", wl.name, `<button onclick="_newWl()" class="hdr-act-btn">+ New</button>`);
  h+=`<div style="display:flex;gap:6px;overflow-x:auto;padding-bottom:10px;margin-bottom:4px;-webkit-overflow-scrolling:touch">`;
  h+=watchlists.map(wls=>`<button onclick="switchWatchlist('${wls.id}');renderMain()" style="font-family:var(--mn);font-size:10px;font-weight:700;padding:5px 14px;border-radius:12px;cursor:pointer;border:1px solid ${wls.id===activeWlId?'var(--gd)':'var(--gb)'};background:${wls.id===activeWlId?'var(--gdG)':'var(--b1)'};color:${wls.id===activeWlId?'var(--gd)':'var(--t3)'};white-space:nowrap;flex-shrink:0">${wls.name}</button>`).join('');
  h+=`</div>`;
  h += _renderSiteIntelCard("watchlist");
  h+=`<div class="qa-row" style="grid-template-columns:repeat(3,1fr);margin-bottom:8px">
    <button class="qa-btn" onclick="runWatchlistScan()"><span class="qa-ico">◎</span><span>Scan</span></button>
    <button class="qa-btn" onclick="compareWatchlist()"><span class="qa-ico">⇄</span><span>Compare</span></button>
    <button class="qa-btn qa-gold" onclick="nav('sig')"><span class="qa-ico">⚡</span><span>Signals</span></button>
  </div>`;
  h+=`<div style="margin-bottom:10px">${_renderMorningRoutineBtn(true)}</div>`;
  h+=_renderWlScan();
  h+=_renderConvictionHeatmap();
  h+=_renderSignalSuggestions();
  if(!w.length){h+=`<div class="gc empty-state"><div class="empty-title">Watchlist empty</div><div class="empty-sub">Add names with ★ on Markets, or start the onboarding path.</div><div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:12px"><button class="btn btn-primary" onclick="nav('mkt')">Browse markets</button><button class="lab-hud-act lab-hud-gold" onclick="nav('lab')">Open Lab</button><button class="lab-hud-act" onclick="runMorningDeskRun()">Desk Run</button></div></div>`;return h;}
  const reWl=_computeRegimeEngine();
  w.forEach(a=>{const d=fp(a.tk);const na=d.status==="unavailable";const note=wl.notes&&wl.notes[a.tk];const hasNote=!!note;
    const inv=getInvalidation(a.tk);const hasInv=!!(inv&&inv.rule);
    const ch=liveChg(a.tk);
    const col=na?"var(--t3)":(ch==null?"var(--t3)":ch>0?"var(--gn)":ch<0?"var(--rd)":"var(--t3)");
    const pxLbl=na?"—":"$"+d.p;
    const chgLbl=na?"NO SYNC":`${ch!=null&&ch>=0?"+":""}${d.c}%`;
    const scShow=a._dyn?Math.round(_tickerRegimeFit(a.tk,reWl).score):a.sc;
    h+=`<div class="gc" style="padding:10px;margin-bottom:6px;cursor:pointer" onclick="openA('${a.tk}')">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
        <div style="display:flex;gap:8px;align-items:center">${ring(scShow,38)}<div><div style="font-family:var(--mn);font-weight:700;font-size:13px">${a.tk}${hasInv?' <span style="color:var(--rd);font-size:8px">KILL</span>':''}${a._dyn?' <span style="color:var(--bl);font-size:8px">LIVE</span>':''}</div><div style="font-size:9px;color:var(--t2)">${a.nm}</div></div></div>
        <div style="text-align:right;display:flex;align-items:center;gap:6px">
          <div><div style="font-family:var(--mn);font-weight:700;font-size:14px">${pxLbl}</div><div style="font-family:var(--mn);font-size:9px;color:${col}">${chgLbl}</div>${spark(a.tk,70,16)}</div>
          <button onclick="event.stopPropagation();setLabTicker('${a.tk}');nav('lab');setTimeout(()=>document.getElementById('lab-inv-card')?.scrollIntoView({behavior:'smooth'}),300)" style="background:${hasInv?'var(--rdG)':'var(--b2)'};border:1px solid ${hasInv?'rgba(239,68,68,0.35)':'var(--b3)'};color:${hasInv?'var(--rd)':'var(--t3)'};border-radius:6px;padding:5px 7px;font-size:10px;cursor:pointer;flex-shrink:0" title="Invalidation">⊘</button>
          <button onclick="event.stopPropagation();openWlNote('${a.tk}')" style="background:${hasNote?'var(--gdG)':'var(--b2)'};border:1px solid ${hasNote?'rgba(245,166,35,0.3)':'var(--b3)'};color:${hasNote?'var(--gd)':'var(--t3)'};border-radius:6px;padding:5px 7px;font-size:11px;cursor:pointer;flex-shrink:0">✏</button>
          <button onclick="event.stopPropagation();removeFromWatchlist('${a.tk}');renderMain()" style="background:var(--b2);border:1px solid var(--b3);color:var(--t3);border-radius:6px;padding:5px 7px;font-size:11px;cursor:pointer;flex-shrink:0" title="Remove">✕</button>
        </div>
      </div>
      ${hasInv?`<div class="wl-note-preview" style="border-left-color:var(--rd)" onclick="event.stopPropagation();setLabTicker('${a.tk}');nav('lab')">Invalidates: ${String(inv.rule).slice(0,70)}${inv.rule.length>70?'…':''}</div>`:''}
      ${hasNote?`<div class="wl-note-preview" onclick="event.stopPropagation();openWlNote('${a.tk}')">"${note.length>65?note.slice(0,65)+'…':note}"</div>`:''}
    </div>`;});
  return h;
}

// ═══════════════════════════════════════════════════════════
// PAGE: MARKET LAB — research sandbox for independent analysts
// Purpose: pick one ticker → test regime fit → stress macro paths → decide next action
// ═══════════════════════════════════════════════════════════

function setLabTicker(tk){
  tk=(typeof resolveInternalTicker==="function"?resolveInternalTicker(tk):tk)||tk;
  _labTk=tk;localStorage.setItem("td_lab_tk",tk);
  _refreshPageView();
}

function setLabRange(r){
  _labRange=r;localStorage.setItem("td_lab_range",r);
  _refreshPageView();
}

function updateLabScenario(key,val){
  _labScenario[key]=parseInt(val,10)||0;
  localStorage.setItem("td_lab_scenario",JSON.stringify(_labScenario));
  const out=document.getElementById("lab-scenario-out");
  if(out)out.innerHTML=_renderLabScenarioInner();
  ["riskOn","neutral","riskOff"].forEach(k=>{const el=document.getElementById("lab-pct-"+k);if(el)el.textContent=_labScenario[k]+"%";});
}

function toggleLabFullscreen(){
  document.body.classList.toggle("lab-immersive");
  setTimeout(_initLabPage,120);
}

function dismissLabGuide(){
  try{localStorage.setItem("td_lab_guide_v1","1");}catch(e){}
  const el=document.getElementById("lab-mission");
  if(el)el.classList.add("lab-mission-collapsed");
  const btn=document.getElementById("lab-guide-toggle");
  if(btn){btn.textContent="Show Lab guide";btn.onclick=expandLabGuide;}
}

function expandLabGuide(){
  try{localStorage.removeItem("td_lab_guide_v1");}catch(e){}
  const el=document.getElementById("lab-mission");
  if(el)el.classList.remove("lab-mission-collapsed");
  const btn=document.getElementById("lab-guide-toggle");
  if(btn){btn.textContent="Hide guide";btn.onclick=dismissLabGuide;}
}

function _initLabPage(){
  if(pg!=="lab")return;
  setTimeout(()=>{
    _destroyCharts();
    const host=document.getElementById("lab-chart");
    if(host)renderCandleChart(_labTk,_labRange,"lab-chart");
  },60);
}

function _labScenarioWeights(){
  const total=(_labScenario.riskOn+_labScenario.neutral+_labScenario.riskOff)||1;
  return {
    total,
    wR:_labScenario.riskOn/total,
    wN:_labScenario.neutral/total,
    wO:_labScenario.riskOff/total
  };
}

function _renderLabScenarioInner(){
  const beta=_deskBeta(_labTk,1);
  const {wR,wN,wO}=_labScenarioWeights();
  // Simple educational model: higher beta amplifies risk-on/off swings (not a forecast)
  const proj=(wR*beta*4.2+wN*0.2+wO*beta*-4.8);
  const p=proj.toFixed(1);
  const col=proj>=1?"var(--gn)":proj<=-1?"var(--rd)":"var(--gd)";
  const read=proj>=2
    ? "Your blend is risk-on heavy — high-β names tend to do better in this path."
    : proj<=-2
      ? "Your blend is risk-off heavy — expect pressure on growth/high-β names."
      : "Your blend is balanced — little directional edge from macro path alone.";
  const dominant=wR>=wN&&wR>=wO?"Risk-On":wO>=wN?"Risk-Off":"Neutral";
  return`<div class="lab-proj-val" style="color:${col}">${proj>=0?"+":""}${p}%</div>
    <div class="lab-proj-sub"><strong>MODEL · illustrative 30-day impulse</strong> for ${_labTk} (β ${beta.toFixed(2)})</div>
    <div class="lab-proj-read">${read}</div>
    <div class="lab-proj-math">Dominant path: <strong style="color:var(--tx)">${dominant}</strong> · weights ${(wR*100).toFixed(0)}% / ${(wN*100).toFixed(0)}% / ${(wO*100).toFixed(0)}% · <em>teaching model only — not a forecast or price target</em></div>`;
}

function _labSectorChg(etf){
  // Sector pack first, then live day % — never parse fp().c "—" as 0
  const d=_sectorData[etf];
  if(d?.month!=null&&isFinite(d.month))return d.month;
  if(d?.day!=null&&isFinite(d.day))return d.day;
  return liveChg(etf);
}
function _renderLabSectorBubbles(){
  // No fetch here — fetchSectorData() calls _refreshView(), which re-renders the
  // Lab and would call straight back into this function. nav() loads it instead.
  const etfs=SECTORS_DEF.map(s=>s.etf);
  const chgs=etfs.map(e=>_labSectorChg(e));
  const maxR=Math.max(...chgs.map(c=>c!=null?Math.abs(c):0),0.1);
  const rows=Math.ceil(etfs.length/4);
  let svg=`<svg class="lab-bubble-svg" viewBox="0 0 320 ${40+(rows-1)*72+40}" role="img" aria-label="Sector ETF performance map">`;
  etfs.forEach((etf,i)=>{
    const chg=chgs[i];
    const has=chg!=null&&isFinite(chg);
    const r=has?14+Math.abs(chg)/maxR*22:12;
    const cx=40+(i%4)*72, cy=40+Math.floor(i/4)*72;
    const col=has?(chg>0?"var(--gn)":chg<0?"var(--rd)":"var(--t3)"):"var(--t3)";
    const lbl=has?`${chg>0?"+":""}${(+chg).toFixed(1)}%`:"—";
    svg+=`<g class="lab-bubble-g" onclick="setLabTicker('${etf}')" style="cursor:pointer"><title>${etf}: ${has?lbl+" — tap to load chart":"no sync"}</title><circle cx="${cx}" cy="${cy}" r="${r}" fill="${col}" fill-opacity="${has?0.22:0.08}" stroke="${col}" stroke-width="1.5"/><text x="${cx}" y="${cy-2}" text-anchor="middle" font-family="JetBrains Mono" font-size="8" font-weight="800" fill="var(--tx)">${etf}</text><text x="${cx}" y="${cy+9}" text-anchor="middle" font-family="JetBrains Mono" font-size="7" fill="${col}">${lbl}</text></g>`;
  });
  return svg+`</svg>`;
}

function _renderLabMission(collapsed){
  return`<div class="lab-mission${collapsed?" lab-mission-collapsed":""}" id="lab-mission">
    <div class="lab-mission-top">
      <div>
        <div class="lab-mission-kicker">WHAT THIS PAGE IS FOR</div>
        <div class="lab-mission-title">Market Lab is a research sandbox — not a trade feed</div>
        <p class="lab-mission-lead">Use it to <strong>pick one ticker</strong>, check if it fits the current market regime, stress-test “what if risk-on / risk-off wins”, and only then decide your next step (watchlist, deep dive, or lens).</p>
      </div>
      <button type="button" class="lab-fs-btn" id="lab-guide-toggle" onclick="${collapsed?"expandLabGuide()":"dismissLabGuide()"}">${collapsed?"Show Lab guide":"Hide guide"}</button>
    </div>
    <div class="lab-mission-body">
      <div class="lab-learn-grid">
        <div class="lab-learn-card"><div class="lab-learn-n">01</div><div class="lab-learn-h">You learn</div><div class="lab-learn-p">Whether this name is aligned with today’s regime (fit score) or fighting the tape.</div></div>
        <div class="lab-learn-card"><div class="lab-learn-n">02</div><div class="lab-learn-h">You learn</div><div class="lab-learn-p">How sensitive the name is if macro paths shift (scenario blender + beta).</div></div>
        <div class="lab-learn-card"><div class="lab-learn-n">03</div><div class="lab-learn-h">You learn</div><div class="lab-learn-p">Where sector leadership is rotating — so you don’t buy laggards blind.</div></div>
        <div class="lab-learn-card"><div class="lab-learn-n">04</div><div class="lab-learn-h">You decide</div><div class="lab-learn-p">Add to watchlist, open Deep Dive, or run Lens Engine — with a clear why.</div></div>
      </div>
      <div class="lab-steps">
        <div class="lab-step"><span class="lab-step-n">1</span><div><strong>Select a ticker</strong><span>Use chips below or tap a sector bubble. Lab always studies one name at a time.</span></div></div>
        <div class="lab-step"><span class="lab-step-n">2</span><div><strong>Read the chart &amp; fit score</strong><span>Look for structure (trend vs chop). Fit ≥70% = regime-friendly; ≤45% = fighting the tape.</span></div></div>
        <div class="lab-step"><span class="lab-step-n">3</span><div><strong>Move the scenario sliders</strong><span>Ask: “If risk-off becomes more likely, does my impulse go negative?” That is the lesson.</span></div></div>
        <div class="lab-step"><span class="lab-step-n">4</span><div><strong>Act with intent</strong><span>Deep Dive for fundamentals · Lens for thesis stress · Watchlist to track — don’t just stare at price.</span></div></div>
      </div>
      <div class="lab-disclaimer">Educational models only · not investment advice · impulse % is a teaching tool, not a forecast</div>
    </div>
  </div>`;
}

function _renderLabLookFor(fit,re,a){
  const tips=[];
  if(fit.score>=70) tips.push(`Regime fit is <strong style="color:var(--gn)">${fit.score}%</strong> — ${_labTk} is aligned with ${re.label}. Look for pullbacks to add / confirm, not chase extended moves without a plan.`);
  else if(fit.score>=45) tips.push(`Regime fit is <strong style="color:var(--gd)">${fit.score}%</strong> — mixed. Look for a catalyst or sector confirmation before sizing up.`);
  else tips.push(`Regime fit is <strong style="color:var(--rd)">${fit.score}%</strong> — ${_labTk} is fighting ${re.label}. Look for invalidation levels; treat longs as counter-trend.`);
  const betaN=_deskBeta(a||_labTk,1);
  if(betaN>=1.3) tips.push(`Beta ~${betaN.toFixed(2)}: expect amplified moves when you slide Risk-On / Risk-Off.`);
  else if(betaN<0.8) tips.push(`Beta ~${betaN.toFixed(2)}: more defensive — scenario blender swings will be smaller than high-β names.`);
  tips.push("On the chart: mark swing highs/lows and whether price is above or below recent structure. Lab does not auto-trade — you do the reading.");
  return`<div class="lab-lookfor"><div class="lab-lookfor-k">WHAT TO LOOK FOR ON THIS TICKER</div><ul>${tips.map(t=>`<li>${t}</li>`).join("")}</ul></div>`;
}

function renderLab(){
  const re=_computeRegimeEngine();
  // Never fall back to NVDA meta for a different active ticker (mislabels dyn/lookup books)
  if(!_labTk)_labTk="NVDA";
  const a=_deskAssetOrStub(_labTk);
  const d=fp(_labTk);
  const fit=_tickerRegimeFit(_labTk,re);
  const strip=[...new Set([_labTk,...getActiveWl().tickers.slice(0,6),"SPX","BTC","XAU","XLK","XLE"])].slice(0,10);
  const ranges=[["1d","1D"],["5d","5D"],["1mo","1M"],["3mo","3M"],["1y","1Y"]];
  const fitCol=fit.score>=70?"var(--gn)":fit.score>=45?"var(--gd)":"var(--rd)";
  let guideCollapsed=false;
  try{guideCollapsed=localStorage.getItem("td_lab_guide_v1")==="1";}catch(e){}

  let h=`<div class="lab-shell">
    ${_renderPgHdr(
      "Market Lab",
      "Research sandbox · stress-test one ticker against regime, macro paths & sectors",
      `<button type="button" class="lab-fs-btn" onclick="toggleLabFullscreen()">⛶ Focus mode</button><button type="button" class="lab-fs-btn" onclick="toggleChat()">⬡ Ask Expert</button>`
    )}
    ${_renderLabMission(guideCollapsed)}

    <div class="lab-workflow-bar">
      <span class="lab-wf-lbl">WORKFLOW</span>
      <span class="lab-wf-item on">1 · Pick ticker</span>
      <span class="lab-wf-sep">→</span>
      <span class="lab-wf-item">2 · Chart + fit</span>
      <span class="lab-wf-sep">→</span>
      <span class="lab-wf-item">3 · Stress scenarios</span>
      <span class="lab-wf-sep">→</span>
      <span class="lab-wf-item">4 · Decide action</span>
    </div>

    <div class="lab-strip-label">Step 1 — Select the name you are studying <span>(watchlist + liquid benchmarks)</span></div>
    <div class="lab-strip">${strip.map(tk=>{
      const on=tk===_labTk?" on":"";
      const dd=fp(tk);
      const na=dd.status==="unavailable";
      const chN=liveChg(tk);
      const cc=na||chN==null?"flat":(chN>0?"up":chN<0?"dn":"flat");
      const px=na?"—":dd.p;
      const ch=na||chN==null?"—":`${chN>=0?"+":""}${dd.c}%`;
      return`<button type="button" class="lab-chip${on}" onclick="setLabTicker('${tk}')" title="Study ${tk}"><span class="lab-chip-tk">${tk}</span><span class="lab-chip-p">${px}</span><span class="lab-chip-c ${cc}">${ch}</span></button>`;
    }).join("")}</div>

    <div class="lab-grid">
      <div class="lab-panel lab-main">
        <div class="lab-panel-hdr">
          <div>
            <div class="lab-panel-k" style="margin-bottom:6px">STEP 2 — PRICE STRUCTURE · ${_labTk}</div>
            <span class="lab-tk-title">${_labTk}</span><span class="lab-tk-nm">${a?.nm||""}</span>
          </div>
          <div class="lab-range-row" title="Change lookback window">${ranges.map(([r,l])=>`<button type="button" class="lab-range${r===_labRange?" on":""}" onclick="setLabRange('${r}')">${l}</button>`).join("")}</div>
        </div>
        <p class="lab-panel-help">Read the candles: is the trend intact, range-bound, or breaking down? Switch 1D→1Y to separate noise from structure.</p>
        <div id="lab-chart" class="lab-chart-host"></div>
        <div class="lab-hud">
          <div class="lab-hud-stat" title="${_escAttr(d.detail||"Price from free feed when synced")}"><div class="lab-hud-l">PRICE ${stat(_labTk)}</div><div class="lab-hud-v">${d.p}</div><div class="lab-hud-asof">${d.status==="unavailable"?"no sync":`as of ${_fmtAsOf(d.asOf)}`}</div></div>
          <div class="lab-hud-stat" title="Session / latest % change from feed"><div class="lab-hud-l">CHANGE</div><div class="lab-hud-v" style="color:${(()=>{const c=liveChg(_labTk);return d.status==="unavailable"||c==null?"var(--t3)":c>0?"var(--gn)":c<0?"var(--rd)":"var(--t3)";})()}">${(()=>{const c=liveChg(_labTk);return d.status==="unavailable"||c==null?"—":`${c>=0?"+":""}${d.c}%`;})()}</div></div>
          <div class="lab-hud-stat" title="Desk conviction score 0–100 — static educational model, not live analytics"><div class="lab-hud-l">CONVICTION · MODEL</div><div class="lab-hud-v" style="color:var(--gd)">${a?.sc??"—"}</div></div>
          <div class="lab-hud-stat" title="How well this ticker matches current regime model"><div class="lab-hud-l">REGIME FIT · MODEL</div><div class="lab-hud-v" style="color:${fitCol}">${fit.score}%</div></div>
          <button type="button" class="lab-hud-act" onclick="openA('${_labTk}')" title="Fundamentals, thesis, earnings">Deep Dive →</button>
          <button type="button" class="lab-hud-act lab-hud-gold" onclick="runCommittee('${_labTk}')" title="Stress-test thesis with Lens Engine">Lens →</button>
        </div>
        ${_renderLabLookFor(fit,re,a)}
      </div>

      <div class="lab-side">
        <div class="lab-panel lab-regime">
          <div class="lab-panel-k">REGIME PULSE</div>
          <p class="lab-panel-help">Where the market is now. Overweight lists = styles favoured in this regime.</p>
          <div class="lab-regime-body">
            ${_renderRegimeRing(re)}
            <div>
              <div class="lab-regime-lbl">${re.label}</div>
              <div class="lab-regime-score">Score ${re.score}/100</div>
              <div class="lab-regime-hint"><strong>Favour:</strong> ${(re.overweight||[]).slice(0,3).join(" · ")||"—"}</div>
              <div class="lab-regime-hint"><strong>Avoid tilt:</strong> ${(re.underweight||[]).slice(0,2).join(" · ")||"—"}</div>
            </div>
          </div>
        </div>

        <div class="lab-panel lab-scenario">
          <div class="lab-panel-k">STEP 3 — MACRO SCENARIO BLENDER</div>
          <p class="lab-panel-help">Pick a <strong>named pack</strong> or drag sliders. Watch impulse % for <strong>${_labTk}</strong>. Higher beta → bigger swings.</p>
          ${_renderLabMacroPacks()}
          ${[["riskOn","RISK-ON","var(--gn)","Growth / risk assets favoured"],["neutral","NEUTRAL","var(--gd)","No strong macro bet"],["riskOff","RISK-OFF","var(--rd)","Defensives / cash favoured"]].map(([k,l,c,hint])=>`
          <div class="lab-sl-row">
            <div class="lab-sl-top"><span style="color:${c}">${l}</span><span id="lab-pct-${k}">${_labScenario[k]}%</span></div>
            <div class="lab-sl-hint">${hint}</div>
            <input type="range" min="0" max="100" value="${_labScenario[k]}" class="lab-slider" oninput="_labActivePack='';try{localStorage.removeItem('td_lab_pack')}catch(e){};updateLabScenario('${k}',this.value)" aria-label="${l} probability">
          </div>`).join("")}
          <div id="lab-scenario-out" class="lab-scenario-out">${_renderLabScenarioInner()}</div>
        </div>

        <div class="lab-panel lab-bubbles">
          <div class="lab-panel-k">SECTOR MAP <span class="lab-panel-sub">size = move · colour = direction</span></div>
          <p class="lab-panel-help">Tap a bubble to load that sector ETF on the chart. Leaders (large green) vs laggards (large red) tell you rotation.</p>
          ${_renderLabSectorBubbles()}
        </div>

        <div class="lab-panel lab-geo-scenario-panel" id="lab-geo-scenario-out">
          <div class="lab-panel-k" style="margin-bottom:8px">GEO SHOCK DRILL</div>
          <p class="lab-panel-help" style="margin-top:0">Optional: pick a disruption scenario and see an oil/beta-channel sketch for the active name. Teaching tool only.</p>
          ${_renderGeoScenarioV2()}
        </div>
      </div>
    </div>

    <div class="lab-checklist">
      <div class="lab-panel-k">STEP 4 — DECISION CHECKLIST</div>
      <div class="lab-check-grid">
        <label class="lab-check"><input type="checkbox"> Chart structure is clear (trend / range / breakdown)</label>
        <label class="lab-check"><input type="checkbox"> Regime fit matches how I want to position</label>
        <label class="lab-check"><input type="checkbox"> I tested at least one risk-off heavy pack</label>
        <label class="lab-check"><input type="checkbox"> Invalidation rule written (kill-switch)</label>
        <label class="lab-check"><input type="checkbox"> Desk note saved (optional)</label>
        <label class="lab-check"><input type="checkbox"> Next action clear: watch / dive / lens / pass</label>
      </div>
      <div class="lab-check-actions">
        <button type="button" class="lab-hud-act" onclick="addToWatchlist('${_labTk}');showToast('${_labTk} → watchlist','var(--gn)')">+ Watchlist</button>
        <button type="button" class="lab-hud-act" onclick="openA('${_labTk}')">Deep Dive</button>
        <button type="button" class="lab-hud-act lab-hud-gold" onclick="runCommittee('${_labTk}')">Run Lens</button>
        <button type="button" class="lab-hud-act" onclick="document.getElementById('lab-inv-card')?.scrollIntoView({behavior:'smooth'})">Invalidation ↓</button>
        <button type="button" class="lab-hud-act" onclick="saveDeskNote()">Save note</button>
        <button type="button" class="lab-hud-act" onclick="nav('brief')">← Brief</button>
      </div>
    </div>

    ${_renderInvalidationCard(_labTk)}
    ${_renderDeskNotesPanel()}

    <div class="lab-footer">Market Lab · research &amp; education only · free data + desk models · ⌘K: morning · stress · invalidate · note</div>
  </div>`;
  return h;
}

// ═══════════════════════════════════════════════════════════
// PAGE: RESEARCH
// ═══════════════════════════════════════════════════════════
function renderResearch(){
  if(selReport==="spx2026")return renderSPX2026();

  let h = _renderPgHdr("Research Desk", "Long-form scenario modeling · macro frameworks · conviction-weighted outlooks");
  h += _renderSiteIntelCard("research");

  // Featured report
  REPORTS.forEach(rep=>{
    h+=`<div class="gc gc-a" onclick="openReport('${rep.id}')" style="padding:18px;border-left:3px solid var(--gd);background:linear-gradient(135deg,var(--gl),rgba(245,158,11,0.04))">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <span style="font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.2em;font-weight:700">★ ${rep.badge}</span>
        <span style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.1em">${rep.readTime.toUpperCase()}</span>
      </div>
      <div class="r-kicker" style="margin-bottom:6px">— ${rep.kicker}</div>
      <div style="font-family:var(--sf);font-size:28px;line-height:1;letter-spacing:-0.02em;margin-bottom:8px">${rep.headline}</div>
      <div style="font-family:var(--sf);font-size:13px;color:var(--t2);font-style:italic;line-height:1.45">${rep.deck}</div>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:14px;padding-top:10px;border-top:1px dotted var(--gb)">
        <span style="font-family:var(--mn);font-size:8.5px;color:var(--t3);letter-spacing:0.1em">${rep.author.toUpperCase()} · ${rep.date.toUpperCase()}</span>
        <span style="font-family:var(--mn);font-size:9px;color:var(--gd);letter-spacing:0.1em">READ →</span>
      </div>
      <div style="display:flex;gap:3px;margin-top:8px;flex-wrap:wrap">${rep.tags.map(t=>bd(t,"var(--gd)")).join("")}</div>
    </div>`;
  });

  // Coming soon placeholder
  h+=`<div class="gc" style="padding:20px;text-align:center;border:1px dashed var(--gb);background:transparent;margin-top:10px">
    <div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.2em;margin-bottom:6px">— FORTHCOMING</div>
    <div style="font-family:var(--sf);font-size:18px;color:var(--t2);font-style:italic">More reports in the pipeline</div>
    <div style="font-size:10px;color:var(--t3);margin-top:4px">Hyperscaler capex deep-dive · Energy super-cycle · BTC halving cycle</div>
  </div>`;

  // Author block
  h+=`<div style="margin-top:14px;padding:14px;background:var(--b1);border-radius:10px;border:1px solid var(--gb)">
    <div style="display:flex;align-items:center;gap:10px">
      <div class="about-avatar" style="width:40px;height:40px;font-size:20px">V</div>
      <div style="flex:1">
        <div style="font-size:12px;font-weight:700">Vraj Patel</div>
        <div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.1em;text-transform:uppercase;margin-top:1px">Founder · Strategy Desk</div>
      </div>
      <a href="https://www.linkedin.com/in/VRAJ2710" target="_blank" rel="noopener" style="background:#0A66C2;color:white;padding:5px 10px;border-radius:5px;font-family:var(--sn);font-size:10px;font-weight:600;text-decoration:none;display:flex;align-items:center;gap:4px">in →</a>
    </div>
  </div>`;

  return h;
}

// ─── SPX 2026 Full Report ───
function renderSPX2026(){
  const wB=blendW.baseline,wS=blendW.stagflation,wA=blendW.aiboom;
  const total=wB+wS+wA||1;
  const blendPath=SCENARIOS.baseline.path.map((_,i)=>Math.round((SCENARIOS.baseline.path[i]*wB+SCENARIOS.stagflation.path[i]*wS+SCENARIOS.aiboom.path[i]*wA)/total));
  const blendTarget=blendPath[blendPath.length-1];
  const blendVix=((SCENARIOS.baseline.vixAvg*wB+SCENARIOS.stagflation.vixAvg*wS+SCENARIOS.aiboom.vixAvg*wA)/total).toFixed(1);
  const blendPct=((blendTarget/7165-1)*100).toFixed(1);

  let h=`<button onclick="closeReport()" style="background:var(--b2);border:1px solid var(--gb);color:var(--t2);padding:5px 10px;border-radius:6px;cursor:pointer;font-family:var(--mn);font-size:9px;letter-spacing:0.15em;margin-bottom:14px">← BACK TO RESEARCH</button>`;

  // Lede
  h+=`<div class="r-kicker">— Year-End Outlook · 2026</div>
  <div class="r-headline">Three <em>paths</em>,<br>one tape.</div>
  <div class="r-deck">The S&P 500 enters the final eight months of 2026 from a fresh all-time high — but the dispersion of plausible year-end outcomes is the widest in recent memory. <strong>Equal-weighting three scenarios — Iran-truce baseline, oil-shock stagflation, and a hyperscaler AI-capex boom — produces a blended target of ~6,800, flat from current levels but masking 60+ points of dispersion.</strong></div>
  <div class="r-byline"><span>Strategy Desk · Vraj Patel</span><span>Apr 26, 2026 · 8 min</span></div>`;

  // Vitals
  h+=`<div class="gr" style="grid-template-columns:repeat(3,1fr);gap:6px;margin-bottom:16px">
    <div class="gc" style="padding:8px"><div style="font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.15em">SPX</div><div style="font-family:var(--mn);font-size:14px;font-weight:700">7,165</div><div style="font-family:var(--mn);font-size:8px;color:var(--gn)">+4.7% YTD</div></div>
    <div class="gc" style="padding:8px"><div style="font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.15em">VIX</div><div style="font-family:var(--mn);font-size:14px;font-weight:700">18.7</div><div style="font-family:var(--mn);font-size:8px;color:var(--rd)">−3.1%</div></div>
    <div class="gc" style="padding:8px"><div style="font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.15em">10Y</div><div style="font-family:var(--mn);font-size:14px;font-weight:700">4.31%</div><div style="font-family:var(--mn);font-size:8px;color:var(--t3)">2Y · 3.78</div></div>
    <div class="gc" style="padding:8px"><div style="font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.15em">BRENT</div><div style="font-family:var(--mn);font-size:14px;font-weight:700">$105</div><div style="font-family:var(--mn);font-size:8px;color:var(--gd)">Iran prem</div></div>
    <div class="gc" style="padding:8px"><div style="font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.15em">CORE PCE</div><div style="font-family:var(--mn);font-size:14px;font-weight:700">3.0%</div><div style="font-family:var(--mn);font-size:8px;color:var(--t3)">FFR 3.50</div></div>
    <div class="gc" style="padding:8px"><div style="font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.15em">NDX</div><div style="font-family:var(--mn);font-size:14px;font-weight:700">25,450</div><div style="font-family:var(--mn);font-size:8px;color:var(--gn)">All-time</div></div>
  </div>`;

  // §01 Scenarios
  h+=`<div class="r-section-h"><span class="r-section-num">§ 01</span><span class="r-section-t">The <em>three</em> paths</span></div>`;

  ["baseline","stagflation","aiboom"].forEach(key=>{
    const s=SCENARIOS[key];
    h+=`<div class="gc" style="border-left:3px solid ${s.color};padding:14px;margin-bottom:10px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <span style="font-family:var(--mn);font-size:8px;color:${s.color};letter-spacing:0.2em;border:1px solid ${s.color};padding:3px 7px;border-radius:3px">◆ ${s.label.toUpperCase()}</span>
        <span style="font-family:var(--sf);font-size:36px;color:${s.color};line-height:0.9">${s.target.toLocaleString()}</span>
      </div>
      <div style="font-family:var(--sf);font-size:11px;color:var(--t2);font-style:italic;margin-bottom:8px">${s.subtitle}</div>
      <div style="display:flex;justify-content:space-between;align-items:baseline;border-top:1px solid var(--gb);border-bottom:1px solid var(--gb);padding:8px 0;margin-bottom:8px">
        <span style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.15em">YE TARGET</span>
        <span style="font-family:var(--mn);font-size:11px;color:${s.color}">${s.pct} · ${s.range}</span>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px">
        <div><div style="font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.15em">EPS</div><div style="font-family:var(--mn);font-size:11px;font-weight:600">${s.eps}</div></div>
        <div><div style="font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.15em">P/E</div><div style="font-family:var(--mn);font-size:11px;font-weight:600">${s.pe}</div></div>
        <div><div style="font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.15em">VIX AVG</div><div style="font-family:var(--mn);font-size:11px;font-weight:600">${s.vix}</div></div>
        <div><div style="font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.15em">10Y</div><div style="font-family:var(--mn);font-size:11px;font-weight:600">${s.y10}</div></div>
      </div>
      <p class="r-narrative" style="font-size:12px">${s.narrative}</p>
      <div style="border-top:1px solid var(--gb);padding-top:8px;margin-top:6px">
        <div style="font-family:var(--mn);font-size:8px;color:${s.color};letter-spacing:0.2em;margin-bottom:6px">→ TRIGGER WATCH</div>
        ${s.triggers.map(t=>`<div style="font-size:10.5px;color:var(--t2);padding:3px 0 3px 12px;position:relative;line-height:1.4"><span style="position:absolute;left:0;color:${s.color}">→</span>${t}</div>`).join("")}
      </div>
    </div>`;
  });

  // §02 Path chart
  h+=`<div class="r-section-h"><span class="r-section-num">§ 02</span><span class="r-section-t">Price <em>paths</em></span></div>`;
  h+=renderPathChart();

  // Pull quote
  h+=`<div class="r-pull"><blockquote>The right read of April 2026 is not bullish or bearish but <em style="font-style:italic;color:var(--gd)">wide</em>.</blockquote><div class="attr">— Strategy Desk</div></div>`;

  // §03 VIX
  h+=`<div class="r-section-h"><span class="r-section-num">§ 03</span><span class="r-section-t">VIX <em>regimes</em></span></div>`;
  h+=renderVixChart();

  // §04 Sectors
  h+=`<div class="r-section-h"><span class="r-section-num">§ 04</span><span class="r-section-t">Sector <em>dispersion</em></span></div>`;
  h+=renderSectorTable();

  // §05 Assumptions
  h+=`<div class="r-section-h"><span class="r-section-num">§ 05</span><span class="r-section-t">Key <em>assumptions</em></span></div>`;
  h+=renderAssumptionsTable();

  // §06 Blender
  h+=`<div class="r-section-h"><span class="r-section-num">§ 06</span><span class="r-section-t">Probability <em>blender</em></span></div>`;
  h+=`<div class="gc" style="padding:16px;background:linear-gradient(135deg,var(--gl),var(--b1));border:1px solid var(--gd)">
    <div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.2em;margin-bottom:14px">— DRAG TO ADJUST CONVICTION</div>

    <div style="margin-bottom:14px">
      <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px">
        <span style="font-family:var(--mn);font-size:9.5px;color:var(--bl);font-weight:700;letter-spacing:0.15em">BASELINE</span>
        <span style="font-family:var(--sf);font-size:22px;color:var(--bl)" id="pct-b">${wB}%</span>
      </div>
      <input type="range" min="0" max="100" value="${wB}" class="r-slider r-sl-b" oninput="updateBlend('baseline',this.value)">
    </div>
    <div style="margin-bottom:14px">
      <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px">
        <span style="font-family:var(--mn);font-size:9.5px;color:var(--rd);font-weight:700;letter-spacing:0.15em">STAGFLATION</span>
        <span style="font-family:var(--sf);font-size:22px;color:var(--rd)" id="pct-s">${wS}%</span>
      </div>
      <input type="range" min="0" max="100" value="${wS}" class="r-slider r-sl-s" oninput="updateBlend('stagflation',this.value)">
    </div>
    <div style="margin-bottom:14px">
      <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px">
        <span style="font-family:var(--mn);font-size:9.5px;color:var(--gn);font-weight:700;letter-spacing:0.15em">AI BOOM</span>
        <span style="font-family:var(--sf);font-size:22px;color:var(--gn)" id="pct-a">${wA}%</span>
      </div>
      <input type="range" min="0" max="100" value="${wA}" class="r-slider r-sl-a" oninput="updateBlend('aiboom',this.value)">
    </div>

    <div style="border-top:2px solid var(--gd);border-bottom:2px solid var(--gd);padding:14px 0;margin-top:14px;display:grid;grid-template-columns:2fr 1fr 1fr;gap:10px;align-items:center">
      <div>
        <div style="font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.2em">BLENDED SPX</div>
        <div style="font-family:var(--sf);font-size:46px;line-height:0.9;letter-spacing:-0.03em" id="blend-spx">${blendTarget.toLocaleString()}</div>
        <div style="font-family:var(--mn);font-size:9px;color:var(--t2)" id="blend-pct">${blendPct>=0?"+":""}${blendPct}% from spot</div>
      </div>
      <div>
        <div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.2em">VIX</div>
        <div style="font-family:var(--sf);font-size:28px" id="blend-vix">${blendVix}</div>
      </div>
      <div>
        <div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.2em">SUM</div>
        <div style="font-family:var(--sf);font-size:28px" id="blend-sum">${total}</div>
      </div>
    </div>

    <svg viewBox="0 0 320 130" style="width:100%;display:block;margin-top:14px" id="blend-svg">
      <line x1="40" y1="105" x2="310" y2="105" stroke="var(--b3)" stroke-width="0.5"/>
      <line x1="40" y1="65" x2="310" y2="65" stroke="var(--b3)" stroke-width="0.5" stroke-dasharray="2 3"/>
      <line x1="40" y1="25" x2="310" y2="25" stroke="var(--b3)" stroke-width="0.5" stroke-dasharray="2 3"/>
      <text x="35" y="108" text-anchor="end" font-family="JetBrains Mono" font-size="7" fill="var(--t3)">5K</text>
      <text x="35" y="68" text-anchor="end" font-family="JetBrains Mono" font-size="7" fill="var(--t3)">6.5K</text>
      <text x="35" y="28" text-anchor="end" font-family="JetBrains Mono" font-size="7" fill="var(--t3)">8K</text>
      <line x1="40" y1="59" x2="310" y2="59" stroke="var(--gd)" stroke-width="0.5" stroke-dasharray="3 3" opacity="0.5"/>
      <path id="path-b" d="${pathToSvgD(SCENARIOS.baseline.path)}" stroke="var(--bl)" stroke-width="1" fill="none" opacity="0.35"/>
      <path id="path-s" d="${pathToSvgD(SCENARIOS.stagflation.path)}" stroke="var(--rd)" stroke-width="1" fill="none" opacity="0.35"/>
      <path id="path-a" d="${pathToSvgD(SCENARIOS.aiboom.path)}" stroke="var(--gn)" stroke-width="1" fill="none" opacity="0.35"/>
      <path id="path-blend" d="${pathToSvgD(blendPath)}" stroke="var(--gd)" stroke-width="2.5" fill="none" stroke-linecap="round"/>
    </svg>
  </div>`;

  // Conclusion
  h+=`<div class="r-section-h"><span class="r-section-num">§ 07</span><span class="r-section-t"><em>Position</em> for dispersion</span></div>
  <div class="gc" style="padding:14px;border-left:3px solid var(--gd)">
    <p style="font-family:var(--sf);font-size:14px;line-height:1.55;color:var(--tx);font-style:italic">Index-level prediction has rarely been less informative — sector positioning, factor exposure, and volatility positioning carry the alpha.</p>
    <p style="font-family:var(--sf);font-size:13px;line-height:1.55;color:var(--t2);font-style:italic;margin-top:10px">The asymmetric setup favors barbells: long Energy + Mag 7 simultaneously — winners in two of three scenarios each, losers in only one — paired with VIX call spreads above 25 strike for stagflation tail protection. The April 29-30 events (FOMC, MSFT/GOOGL earnings, March PCE) will collapse this dispersion within five trading days.</p>
    <p style="font-family:var(--sf);font-size:13px;line-height:1.55;color:var(--t2);font-style:italic;margin-top:10px">Until then, the index at 7,165 is simultaneously priced for 8,000 and 5,000 — a feature, not a bug, of an economy where one Hormuz mine and one Azure deceleration print are both live priced events. Position sizing matters more than direction.</p>
  </div>`;

  // Colophon
  h+=`<div style="margin-top:18px;padding-top:14px;border-top:3px double var(--gb)">
    <div style="font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.25em;margin-bottom:10px">— METHOD & SOURCES</div>
    <div style="font-size:11px;color:var(--t3);line-height:1.6;margin-bottom:10px">Three illustrative scenarios modeled against current-cycle macro inputs. EPS and multiple assumptions calibrated to FactSet consensus. Volatility paths derived from 2017–2024 regime templates plus 2022 stagflation analog.</div>
    <div style="font-size:10px;color:var(--t3);line-height:1.5">Sources: BEA · BLS · Fed SEP (Mar 18, 2026) · FactSet Earnings Insight · Cboe · FRED · GS, JPM, MS, BofA, Citi, DB strategist notes · MSFT, GOOGL, META, AMZN earnings · NVIDIA Q4 FY26.</div>

    <div style="margin-top:14px;padding:10px;background:var(--b1);border-radius:8px">
      <div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.2em;margin-bottom:6px">— AUTHORED BY</div>
      <div style="display:flex;align-items:center;gap:10px">
        <div class="about-avatar" style="width:36px;height:36px;font-size:18px">V</div>
        <div style="flex:1">
          <div style="font-size:12px;font-weight:700">Vraj Patel</div>
          <div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.1em;text-transform:uppercase;margin-top:1px">The Dispatch · Strategy Desk</div>
        </div>
        <a href="https://www.linkedin.com/in/VRAJ2710" target="_blank" rel="noopener" style="background:#0A66C2;color:white;padding:5px 10px;border-radius:5px;font-family:var(--sn);font-size:10px;font-weight:600;text-decoration:none">in →</a>
      </div>
    </div>

    <div style="margin-top:10px;padding-top:10px;border-top:1px dotted var(--gb);font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.15em;text-align:center">
      THE DISPATCH · THEDISPATCH.UK · NOT INVESTMENT ADVICE
    </div>
  </div>`;

  return h;
}

// ─── SVG path helper ───
function pathToSvgD(values){
  const yMin=4800,yMax=8200,height=80,offsetY=20;
  const x0=40,x1=310;
  const dx=(x1-x0)/(values.length-1);
  return values.map((v,i)=>{
    const x=x0+i*dx;
    const y=offsetY+(height-((v-yMin)/(yMax-yMin))*height);
    return `${i===0?"M":"L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
  }).join(" ");
}

function pathToSvgD2(values,yMin,yMax,height,offsetY,x0,x1){
  const dx=(x1-x0)/(values.length-1);
  return values.map((v,i)=>{
    const x=x0+i*dx;
    const y=offsetY+(height-((v-yMin)/(yMax-yMin))*height);
    return `${i===0?"M":"L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
  }).join(" ");
}

// ─── Path Chart ───
function renderPathChart(){
  let h=`<div class="gc" style="padding:14px"><div style="margin-bottom:8px"><div style="font-family:var(--sf);font-size:18px">SPX · Apr → <em style="font-style:italic;color:var(--gd)">Dec 2026</em></div><div style="font-family:var(--mn);font-size:8.5px;color:var(--t3);margin-top:2px">Three monthly paths from spot 7,165</div></div>`;

  h+=`<svg viewBox="0 0 340 220" style="width:100%;display:block">
    <line x1="40" y1="180" x2="330" y2="180" stroke="var(--b3)" stroke-width="0.5"/>
    <line x1="40" y1="135" x2="330" y2="135" stroke="var(--b3)" stroke-width="0.5" stroke-dasharray="2 3"/>
    <line x1="40" y1="90" x2="330" y2="90" stroke="var(--b3)" stroke-width="0.5" stroke-dasharray="2 3"/>
    <line x1="40" y1="45" x2="330" y2="45" stroke="var(--b3)" stroke-width="0.5" stroke-dasharray="2 3"/>
    <text x="35" y="183" text-anchor="end" font-family="JetBrains Mono" font-size="7" fill="var(--t3)">5,000</text>
    <text x="35" y="138" text-anchor="end" font-family="JetBrains Mono" font-size="7" fill="var(--t3)">6,000</text>
    <text x="35" y="93" text-anchor="end" font-family="JetBrains Mono" font-size="7" fill="var(--t3)">7,000</text>
    <text x="35" y="48" text-anchor="end" font-family="JetBrains Mono" font-size="7" fill="var(--t3)">8,000</text>`;

  // X axis labels
  MONTHS.forEach((m,i)=>{
    const x=40+(i*(290/(MONTHS.length-1)));
    h+=`<text x="${x}" y="200" text-anchor="middle" font-family="JetBrains Mono" font-size="7" fill="var(--t3)">${m.toUpperCase()}</text>`;
  });

  // spot ref
  h+=`<line x1="40" y1="103" x2="330" y2="103" stroke="var(--gd)" stroke-width="0.5" stroke-dasharray="3 3" opacity="0.5"/>
  <text x="328" y="100" text-anchor="end" font-family="JetBrains Mono" font-size="6.5" fill="var(--gd)">SPOT 7,165</text>`;

  // Each path: yMin=4800, yMax=8200, height=135, offsetY=45, x0=40, x1=330
  ["stagflation","baseline","aiboom"].forEach(key=>{
    const s=SCENARIOS[key];
    const pd=pathToSvgD2(s.path,4800,8200,135,45,40,330);
    h+=`<path d="${pd}" stroke="${s.color}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`;
    // end dot & label
    const lastY=45+(135-((s.path[s.path.length-1]-4800)/(8200-4800))*135);
    h+=`<circle cx="330" cy="${lastY.toFixed(1)}" r="2.5" fill="${s.color}"/>`;
  });

  // spot dot
  h+=`<circle cx="40" cy="103" r="3" fill="var(--gd)" stroke="var(--bg)" stroke-width="1.5"/>`;

  h+=`</svg>
  <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;padding-top:8px;border-top:1px solid var(--gb)">
    <div style="display:flex;align-items:center;gap:5px;font-family:var(--mn);font-size:8.5px;color:var(--t2)"><span style="width:14px;height:2px;background:var(--bl);border-radius:1px"></span>BASELINE 7,650</div>
    <div style="display:flex;align-items:center;gap:5px;font-family:var(--mn);font-size:8.5px;color:var(--t2)"><span style="width:14px;height:2px;background:var(--rd);border-radius:1px"></span>STAGFLATION 5,050</div>
    <div style="display:flex;align-items:center;gap:5px;font-family:var(--mn);font-size:8.5px;color:var(--t2)"><span style="width:14px;height:2px;background:var(--gn);border-radius:1px"></span>AI BOOM 7,800</div>
  </div></div>`;

  return h;
}

// ─── VIX Chart ───
function renderVixChart(){
  let h=`<div class="gc" style="padding:14px"><div style="margin-bottom:8px"><div style="font-family:var(--sf);font-size:18px">Implied <em style="font-style:italic;color:var(--gd)">volatility</em> · monthly avg</div><div style="font-family:var(--mn);font-size:8.5px;color:var(--t3);margin-top:2px">VIX projections through year-end</div></div>`;

  h+=`<svg viewBox="0 0 340 200" style="width:100%;display:block">
    <line x1="40" y1="160" x2="330" y2="160" stroke="var(--b3)" stroke-width="0.5"/>
    <line x1="40" y1="125" x2="330" y2="125" stroke="var(--b3)" stroke-width="0.5" stroke-dasharray="2 3"/>
    <line x1="40" y1="90" x2="330" y2="90" stroke="var(--b3)" stroke-width="0.5" stroke-dasharray="2 3"/>
    <line x1="40" y1="55" x2="330" y2="55" stroke="var(--b3)" stroke-width="0.5" stroke-dasharray="2 3"/>
    <line x1="40" y1="20" x2="330" y2="20" stroke="var(--b3)" stroke-width="0.5" stroke-dasharray="2 3"/>
    <text x="35" y="163" text-anchor="end" font-family="JetBrains Mono" font-size="7" fill="var(--t3)">10</text>
    <text x="35" y="128" text-anchor="end" font-family="JetBrains Mono" font-size="7" fill="var(--t3)">17</text>
    <text x="35" y="93" text-anchor="end" font-family="JetBrains Mono" font-size="7" fill="var(--t3)">24</text>
    <text x="35" y="58" text-anchor="end" font-family="JetBrains Mono" font-size="7" fill="var(--t3)">31</text>
    <text x="35" y="23" text-anchor="end" font-family="JetBrains Mono" font-size="7" fill="var(--t3)">38</text>`;

  MONTHS.forEach((m,i)=>{
    const x=40+(i*(290/(MONTHS.length-1)));
    h+=`<text x="${x}" y="180" text-anchor="middle" font-family="JetBrains Mono" font-size="7" fill="var(--t3)">${m.toUpperCase()}</text>`;
  });

  // spot 18.7 ref. yMin=10, yMax=38, height=140, offsetY=20
  // 18.7: y = 20 + 140 - ((18.7-10)/28)*140 = 160 - 43.5 = 116.5
  h+=`<line x1="40" y1="117" x2="330" y2="117" stroke="var(--gd)" stroke-width="0.5" stroke-dasharray="3 3" opacity="0.5"/>
  <text x="328" y="114" text-anchor="end" font-family="JetBrains Mono" font-size="6.5" fill="var(--gd)">SPOT 18.7</text>`;

  ["stagflation","baseline","aiboom"].forEach(key=>{
    const s=SCENARIOS[key];
    const pd=pathToSvgD2(s.vixPath,10,38,140,20,40,330);
    h+=`<path d="${pd}" stroke="${s.color}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`;
  });

  h+=`<circle cx="40" cy="117" r="3" fill="var(--gd)" stroke="var(--bg)" stroke-width="1.5"/></svg>
  <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;padding-top:8px;border-top:1px solid var(--gb)">
    <div style="display:flex;align-items:center;gap:5px;font-family:var(--mn);font-size:8px;color:var(--t2)"><span style="width:12px;height:2px;background:var(--bl)"></span>AVG 15 · RVOL 12%</div>
    <div style="display:flex;align-items:center;gap:5px;font-family:var(--mn);font-size:8px;color:var(--t2)"><span style="width:12px;height:2px;background:var(--rd)"></span>AVG 27 · RVOL 23%</div>
    <div style="display:flex;align-items:center;gap:5px;font-family:var(--mn);font-size:8px;color:var(--t2)"><span style="width:12px;height:2px;background:var(--gn)"></span>AVG 14 · RVOL 11%</div>
  </div></div>`;
  return h;
}

// ─── Sector heatmap ───
function heatColor(v){
  if(v>=20)return{bg:"#0d3a26",fg:"#52d4a3"};
  if(v>=10)return{bg:"#0d2e1f",fg:"#52d4a3"};
  if(v>=3) return{bg:"#0d2018",fg:"#52d4a3"};
  if(v>-3) return{bg:"var(--b3)",fg:"var(--t2)"};
  if(v>-15)return{bg:"#3a1f1c",fg:"#e89580"};
  if(v>-25)return{bg:"#5a1a14",fg:"#ffb5a3"};
  return{bg:"#7a1410",fg:"#ffd0c2"};
}

function renderSectorTable(){
  let h=`<div class="gc" style="padding:12px"><div style="font-family:var(--mn);font-size:8.5px;color:var(--t3);letter-spacing:0.15em;margin-bottom:8px">— TOTAL RETURN · YE 2026 (%)</div>
  <table class="r-table">
    <thead><tr><th>Sector</th><th style="text-align:center;color:var(--bl)">BASE</th><th style="text-align:center;color:var(--rd)">STAG</th><th style="text-align:center;color:var(--gn)">AI</th></tr></thead>
    <tbody>`;
  SECTORS.forEach(([n,b,s,a])=>{
    const cb=heatColor(b),cs=heatColor(s),ca=heatColor(a);
    h+=`<tr>
      <td>${n}</td>
      <td class="r-cell" style="background:${cb.bg};color:${cb.fg}">${b>0?"+":""}${b}%</td>
      <td class="r-cell" style="background:${cs.bg};color:${cs.fg}">${s>0?"+":""}${s}%</td>
      <td class="r-cell" style="background:${ca.bg};color:${ca.fg}">${a>0?"+":""}${a}%</td>
    </tr>`;
  });
  h+=`</tbody></table></div>`;
  return h;
}

// ─── Assumption table ───
function renderAssumptionsTable(){
  let h=`<div class="gc" style="padding:12px;overflow-x:auto"><div style="font-family:var(--mn);font-size:8.5px;color:var(--t3);letter-spacing:0.15em;margin-bottom:8px">— INPUT MATRIX · YE 2026</div>
  <table class="r-table" style="font-size:9px">
    <thead><tr><th>Input</th><th style="color:var(--bl)">Base</th><th style="color:var(--rd)">Stag</th><th style="color:var(--gn)">AI</th></tr></thead>
    <tbody>`;
  ASSUMPTIONS.forEach(([k,b,s,a])=>{
    h+=`<tr><td style="font-size:11px">${k}</td><td>${b}</td><td>${s}</td><td>${a}</td></tr>`;
  });
  h+=`</tbody></table></div>`;
  return h;
}

// ─── Update blender ───
function updateBlend(key,val){
  blendW[key]=parseInt(val);
  const wB=blendW.baseline,wS=blendW.stagflation,wA=blendW.aiboom;
  const total=wB+wS+wA||1;
  const blendPath=SCENARIOS.baseline.path.map((_,i)=>Math.round((SCENARIOS.baseline.path[i]*wB+SCENARIOS.stagflation.path[i]*wS+SCENARIOS.aiboom.path[i]*wA)/total));
  const blendTarget=blendPath[blendPath.length-1];
  const blendVix=((SCENARIOS.baseline.vixAvg*wB+SCENARIOS.stagflation.vixAvg*wS+SCENARIOS.aiboom.vixAvg*wA)/total).toFixed(1);
  const blendPct=((blendTarget/7165-1)*100).toFixed(1);

  document.getElementById("pct-b").textContent=wB+"%";
  document.getElementById("pct-s").textContent=wS+"%";
  document.getElementById("pct-a").textContent=wA+"%";
  document.getElementById("blend-spx").textContent=blendTarget.toLocaleString();
  document.getElementById("blend-pct").textContent=(blendPct>=0?"+":"")+blendPct+"% from spot";
  document.getElementById("blend-vix").textContent=blendVix;
  document.getElementById("blend-sum").textContent=total;
  document.getElementById("path-blend").setAttribute("d",pathToSvgD(blendPath));
}

// ═══════════════════════════════════════════════════════════
// PAGE: ADVANCED SCREENER
// ═══════════════════════════════════════════════════════════
let _scrMode = 'us_top';
let _scrResults = [];
let _scrLoading = false;
let _scrSort = { col: 'marketCap', dir: -1 };
let _scrFilters = { marketCapMoreThan:'', marketCapLowerThan:'', priceMoreThan:'', priceLowerThan:'', betaMoreThan:'', betaLowerThan:'', volumeMoreThan:'', sector:'', country:'', exchange:'' };
let _scrCustom = false;

function _renderScr() {
  const ov = document.getElementById('scr-body');
  const main = document.getElementById('main');
  const html = renderScreener();
  if (ov) { ov.innerHTML = html; return; }
  if (main && pg === 'scr') { main.innerHTML = html + _siteFooter(); return; }
  if (main) main.innerHTML = html;
}

function _showScrOverlay() {
  const existing = document.getElementById('scrOv');
  if (existing) { existing.remove(); return; }
  const el = document.createElement('div');
  el.id = 'scrOv';
  el.style.cssText = 'position:fixed;inset:0;z-index:300;background:rgba(0,0,0,0.7);backdrop-filter:blur(4px);display:flex;align-items:flex-start;justify-content:center;padding-top:60px;overflow-y:auto';
  el.innerHTML = `<div style="background:var(--b2);border:1px solid var(--b3);border-radius:14px;width:96%;max-width:1100px;max-height:88vh;overflow-y:auto;box-shadow:var(--shadow-lg)">
    <div style="display:flex;justify-content:space-between;align-items:center;padding:14px 20px;border-bottom:1px solid var(--gb);position:sticky;top:0;background:var(--b2);z-index:1">
      <div style="font-family:var(--sn);font-size:16px;font-weight:700">🔍 Advanced Screener</div>
      <button onclick="document.getElementById('scrOv').remove()" style="background:var(--b3);border:none;color:var(--t2);border-radius:50%;width:30px;height:30px;cursor:pointer;font-size:16px">×</button>
    </div>
    <div id="scr-body" style="padding:16px">${renderScreener()}</div>
  </div>`;
  el.addEventListener('click', e => { if (e.target === el) el.remove(); });
  document.body.appendChild(el);
}

async function runScreener(mode, filters) {
  if (mode !== undefined) _scrMode = mode;
  if (filters !== undefined) _scrFilters = filters;
  _scrCustom = _scrMode === 'custom';
  const seq = ++_scrSeq;
  _scrLoading = true;
  _scrError = null;
  _renderScr();
  let url = `/api/screener?type=${_scrMode}&count=200`;
  if (_scrMode === 'custom') {
    Object.entries(_scrFilters).forEach(([k, v]) => { if (v !== '' && v != null) url += `&${k}=${encodeURIComponent(v)}`; });
  }
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(20000) });
    if (!res.ok) throw new Error('Screener failed (' + res.status + ')');
    const data = await res.json();
    if (seq !== _scrSeq) return;
    // Drop rows without a positive feed price — never paint $0.00 as a real print
    _scrResults = (data.tickers || []).filter(t =>
      t && t.symbol && typeof t.price === "number" && isFinite(t.price) && t.price > 0
    );
    if (!_scrResults.length) _scrError = 'No stocks matched your criteria';
  } catch (e) {
    if (seq !== _scrSeq) return;
    _scrResults = [];
    _scrError = e?.message || 'Screener unavailable — try again';
  }
  if (seq !== _scrSeq) return;
  _scrLoading = false;
  _renderScr();
}

function sortScr(col) {
  if (_scrSort.col === col) _scrSort.dir *= -1;
  else { _scrSort.col = col; _scrSort.dir = -1; }
  _renderScr();
}

function renderScreener() {
  const fmtMC = v => {
    const n = typeof v === 'number' ? v : parseFloat(v);
    if (!n || !isFinite(n) || n <= 0) return '—';
    if (n >= 1e12) return `$${(n/1e12).toFixed(2)}T`;
    if (n >= 1e9) return `$${(n/1e9).toFixed(1)}B`;
    if (n >= 1e6) return `$${(n/1e6).toFixed(0)}M`;
    return `$${Math.round(n).toLocaleString()}`;
  };
  const presets = [
    { id:'day_gainers', lb:'▲ Gainers' },
    { id:'day_losers', lb:'▼ Losers' },
    { id:'most_actives', lb:'◎ Active' },
    { id:'us_top', lb:'🇺🇸 US Top' },
    { id:'global', lb:'🌍 Global' },
    { id:'all', lb:'♾ All Markets' },
    { id:'custom', lb:'⚙ Custom Filter' },
  ];

  let h = _renderPgHdr("Advanced Screener", _scrResults.length ? `${_scrResults.length} stocks found` : "Screen global markets by 50+ criteria");
  h += _renderSiteIntelCard("scr");

  // Preset tabs
  h += `<div style="display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap">
    ${presets.map(p=>`<button onclick="runScreener('${p.id}')" style="padding:7px 14px;border-radius:8px;cursor:pointer;font-family:var(--sn);font-size:12px;font-weight:600;border:1px solid ${_scrMode===p.id?'var(--bl)':'var(--gb)'};background:${_scrMode===p.id?'var(--blG)':'var(--b1)'};color:${_scrMode===p.id?'var(--bl)':'var(--t2)'}">${p.lb}${p.id==='custom'&&!_isPremium()?'<span style="color:var(--gd);font-size:9px;margin-left:3px">★</span>':''}</button>`).join('')}
  </div>`;

  // Custom filter panel
  if (_scrCustom) {
    const SECTORS = ['Technology','Healthcare','Financial Services','Consumer Cyclical','Communication Services','Industrials','Consumer Defensive','Energy','Basic Materials','Real Estate','Utilities'];
    const EXCHANGES = ['NYSE','NASDAQ','AMEX','LSE','EURONEXT','TSX','ASX','NSE'];
    h += `<div class="gc" style="padding:14px;margin-bottom:12px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px"><div style="font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.15em">FILTER CRITERIA</div>${!_isPremium()?'<span style="font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.1em">★ PREMIUM · <a href="/__auth/subscribe" style="color:var(--gd);text-decoration:underline">Subscribe</a></span>':''}</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px">
        <div>
          <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:5px">MARKET CAP MIN ($)</div>
          <input id="scr-mcMin" type="number" placeholder="e.g. 1000000000" value="${_scrFilters.marketCapMoreThan||''}" style="width:100%;background:var(--bg);border:1px solid var(--gb);border-radius:6px;padding:7px 10px;color:var(--tx);font-family:var(--mn);font-size:11px;outline:none">
        </div>
        <div>
          <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:5px">MARKET CAP MAX ($)</div>
          <input id="scr-mcMax" type="number" placeholder="e.g. 500000000000" value="${_scrFilters.marketCapLowerThan||''}" style="width:100%;background:var(--bg);border:1px solid var(--gb);border-radius:6px;padding:7px 10px;color:var(--tx);font-family:var(--mn);font-size:11px;outline:none">
        </div>
        <div>
          <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:5px">PRICE MIN ($)</div>
          <input id="scr-pMin" type="number" placeholder="e.g. 10" value="${_scrFilters.priceMoreThan||''}" style="width:100%;background:var(--bg);border:1px solid var(--gb);border-radius:6px;padding:7px 10px;color:var(--tx);font-family:var(--mn);font-size:11px;outline:none">
        </div>
        <div>
          <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:5px">PRICE MAX ($)</div>
          <input id="scr-pMax" type="number" placeholder="e.g. 500" value="${_scrFilters.priceLowerThan||''}" style="width:100%;background:var(--bg);border:1px solid var(--gb);border-radius:6px;padding:7px 10px;color:var(--tx);font-family:var(--mn);font-size:11px;outline:none">
        </div>
        <div>
          <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:5px">BETA MIN</div>
          <input id="scr-bMin" type="number" step="0.1" placeholder="e.g. 0.5" value="${_scrFilters.betaMoreThan||''}" style="width:100%;background:var(--bg);border:1px solid var(--gb);border-radius:6px;padding:7px 10px;color:var(--tx);font-family:var(--mn);font-size:11px;outline:none">
        </div>
        <div>
          <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:5px">BETA MAX</div>
          <input id="scr-bMax" type="number" step="0.1" placeholder="e.g. 1.5" value="${_scrFilters.betaLowerThan||''}" style="width:100%;background:var(--bg);border:1px solid var(--gb);border-radius:6px;padding:7px 10px;color:var(--tx);font-family:var(--mn);font-size:11px;outline:none">
        </div>
        <div>
          <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:5px">MIN VOLUME</div>
          <input id="scr-vol" type="number" placeholder="e.g. 1000000" value="${_scrFilters.volumeMoreThan||''}" style="width:100%;background:var(--bg);border:1px solid var(--gb);border-radius:6px;padding:7px 10px;color:var(--tx);font-family:var(--mn);font-size:11px;outline:none">
        </div>
        <div>
          <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:5px">COUNTRY</div>
          <input id="scr-country" type="text" placeholder="e.g. US, GB, IN" value="${_scrFilters.country||''}" style="width:100%;background:var(--bg);border:1px solid var(--gb);border-radius:6px;padding:7px 10px;color:var(--tx);font-family:var(--mn);font-size:11px;outline:none">
        </div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px">
        <div>
          <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:5px">SECTOR</div>
          <select id="scr-sector" style="width:100%;background:var(--bg);border:1px solid var(--gb);border-radius:6px;padding:7px 10px;color:var(--tx);font-family:var(--mn);font-size:11px;outline:none">
            <option value="">All Sectors</option>
            ${SECTORS.map(s=>`<option value="${s}" ${_scrFilters.sector===s?'selected':''}>${s}</option>`).join('')}
          </select>
        </div>
        <div>
          <div style="font-family:var(--mn);font-size:8px;color:var(--t3);margin-bottom:5px">EXCHANGE</div>
          <select id="scr-exchange" style="width:100%;background:var(--bg);border:1px solid var(--gb);border-radius:6px;padding:7px 10px;color:var(--tx);font-family:var(--mn);font-size:11px;outline:none">
            <option value="">All Exchanges</option>
            ${EXCHANGES.map(e=>`<option value="${e}" ${_scrFilters.exchange===e?'selected':''}>${e}</option>`).join('')}
          </select>
        </div>
      </div>
      <div style="display:flex;gap:8px">
        <button onclick="_applyCustomScreen()" style="flex:1;background:var(--bl);color:white;border:none;border-radius:8px;padding:11px;font-family:var(--sn);font-size:13px;font-weight:700;cursor:pointer">Run Screen</button>
        <button onclick="_scrFilters={};_scrResults=[];_renderScr()" style="background:var(--b2);border:1px solid var(--gb);color:var(--t2);border:none;border-radius:8px;padding:11px 16px;font-family:var(--sn);font-size:12px;cursor:pointer">Reset</button>
      </div>
    </div>`;
  }

  if (_scrLoading) {
    h += `<div class="gc" style="padding:40px;text-align:center">
      <div style="width:16px;height:16px;border:2px solid var(--bl);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 14px"></div>
      <div style="font-family:var(--sn);font-size:13px;color:var(--t2)">Scanning markets…</div>
    </div>`;
  } else if (_scrResults.length === 0 && !_scrCustom && !_scrError) {
    h += `<div class="gc" style="padding:30px;text-align:center">
      <div style="font-family:var(--mn);font-size:11px;color:var(--t3);margin-bottom:8px">SELECT A SCREEN ABOVE TO BEGIN</div>
      <div style="font-family:var(--sn);font-size:12px;color:var(--t2)">Choose US Top, Global, or All Markets — or build a Custom Filter to screen by market cap, price, beta, sector, exchange and more.</div>
    </div>`;
  } else if (_scrError) {
    h += `<div class="gc" style="padding:30px;text-align:center">
      <div style="font-family:var(--sn);font-size:14px;color:var(--rd);margin-bottom:12px">${_scrError}</div>
      <button onclick="runScreener('${_scrMode}')" style="background:var(--gd);color:var(--bg);border:none;border-radius:8px;padding:10px 20px;font-family:var(--sn);font-size:13px;font-weight:700;cursor:pointer">Retry</button>
    </div>`;
  } else if (_scrResults.length > 0) {
    // Sort results
    const sorted = [..._scrResults].sort((a, b) => {
      const av = a[_scrSort.col] ?? (_scrSort.dir < 0 ? -Infinity : Infinity);
      const bv = b[_scrSort.col] ?? (_scrSort.dir < 0 ? -Infinity : Infinity);
      return _scrSort.dir * (bv - av);
    });
    const hd = (col, lb) => `<th onclick="sortScr('${col}')" style="padding:7px 10px;text-align:right;font-size:8px;color:${_scrSort.col===col?'var(--gd)':'var(--t3)'};letter-spacing:0.08em;cursor:pointer;white-space:nowrap;user-select:none">${lb}${_scrSort.col===col?(_scrSort.dir<0?' ↓':' ↑'):''}</th>`;
    h += `<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-family:var(--mn);font-size:11px;min-width:600px">
      <thead><tr style="background:var(--b1);border-bottom:1px solid var(--gb)">
        <th style="padding:7px 10px;text-align:left;font-size:8px;color:var(--t3);letter-spacing:0.08em">SYMBOL</th>
        <th style="padding:7px 10px;text-align:left;font-size:8px;color:var(--t3);letter-spacing:0.08em">NAME</th>
        ${hd('price','PRICE')}
        ${hd('change','CHG %')}
        ${hd('marketCap','MKT CAP')}
        ${hd('volume','VOLUME')}
        <th style="padding:7px 10px;text-align:right;font-size:8px;color:var(--t3)">SECTOR</th>
      </tr></thead><tbody>
      ${sorted.slice(0, 200).map((s,i)=>{
        const chN=typeof s.change==="number"&&isFinite(s.change)?s.change:null;
        const pxN=typeof s.price==="number"&&s.price>0?s.price:null;
        const cc = chN==null ? 'var(--t3)' : chN > 0 ? 'var(--gn)' : chN < 0 ? 'var(--rd)' : 'var(--t3)';
        const nm = s.name?.length > 22 ? s.name.slice(0,22)+'…' : (s.name||s.symbol);
        const sec = s.sector?.length > 14 ? s.sector.slice(0,14)+'…' : (s.sector||'—');
        const symEsc=String(s.symbol||"").replace(/'/g,"");
        return `<tr onclick="lookupTicker('${symEsc}')" style="border-bottom:1px solid rgba(255,255,255,0.025);cursor:pointer;transition:background 0.1s" onmouseover="this.style.background='var(--b1)'" onmouseout="this.style.background=''" >
          <td style="padding:7px 10px;font-weight:800;color:var(--gd)">${s.symbol}</td>
          <td style="padding:7px 10px;color:var(--t2);font-family:var(--sn);font-size:10px">${nm}</td>
          <td style="padding:7px 10px;text-align:right;color:var(--tx)">${pxN!=null?('$'+pxN.toFixed(pxN>=1?2:4)):'—'}</td>
          <td style="padding:7px 10px;text-align:right;color:${cc};font-weight:700">${chN!=null?((chN>=0?'+':'')+chN.toFixed(2)+'%'):'—'}</td>
          <td style="padding:7px 10px;text-align:right;color:var(--t2)">${fmtMC(s.marketCap)}</td>
          <td style="padding:7px 10px;text-align:right;color:var(--t3)">${s.volume ? (s.volume/1e6).toFixed(1)+'M' : '—'}</td>
          <td style="padding:7px 10px;text-align:right;color:var(--t3);font-size:9px">${sec}</td>
        </tr>`;
      }).join('')}
      </tbody></table></div>`;
  }

  return h;
}

function _applyCustomScreen() {
  if (!_isPremium()) { _showLoginGate('Custom Stock Screener'); return; }
  _scrFilters = {
    marketCapMoreThan: document.getElementById('scr-mcMin')?.value || '',
    marketCapLowerThan: document.getElementById('scr-mcMax')?.value || '',
    priceMoreThan: document.getElementById('scr-pMin')?.value || '',
    priceLowerThan: document.getElementById('scr-pMax')?.value || '',
    betaMoreThan: document.getElementById('scr-bMin')?.value || '',
    betaLowerThan: document.getElementById('scr-bMax')?.value || '',
    volumeMoreThan: document.getElementById('scr-vol')?.value || '',
    country: document.getElementById('scr-country')?.value || '',
    sector: document.getElementById('scr-sector')?.value || '',
    exchange: document.getElementById('scr-exchange')?.value || '',
  };
  runScreener('custom', _scrFilters);
}

// ═══════════════════════════════════════════════════════════
// MAIN RENDER
// ═══════════════════════════════════════════════════════════
function _siteFooter(){
  const feedAsOf = priceLastFetch ? `${_fmtAsOf(priceLastFetch.getTime())} (${_fmtAge(priceLastFetch.getTime())})` : "no feed yet";
  return `<footer class="site-trust-footer" style="margin-top:28px;padding:16px 0 6px;border-top:1px solid var(--gb);text-align:center">
    <div style="font-family:var(--mn);font-size:9px;color:var(--t3);line-height:1.65;max-width:420px;margin:0 auto">
      <strong style="color:var(--t2)">Research only · Not investment advice</strong><br>
      Quotes: free Yahoo / CoinGecko / proxies — delayed, can gap · Seed prices never shown as market · Regime, Lab impulse, free brief, conviction scores = educational models<br>
      Feed as of ${feedAsOf} · ${_stripeMode === "test" ? "Stripe checkout is in TEST mode · " : ""}<span style="color:var(--gd)">thedispatch.uk</span>
    </div>
  </footer>`;
}

let _lastFxPg = null;
function _fxStaggerChildren(el) {
  if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  el.classList.remove("fx-page-enter");
  void el.offsetWidth;
  el.classList.add("fx-page-enter");
}
function _fxPageEnter(el) {
  if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (_lastFxPg === pg) return;
  _lastFxPg = pg;
  _fxStaggerChildren(el);
}
function _fxOverlayEnter(node) {
  if (!node || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  node.classList.add("fx-overlay-enter");
  node.addEventListener("animationend", () => node.classList.remove("fx-overlay-enter"), { once: true });
}

// =====================================================
// COMPLETELY NEW UI — Intelligence Briefing Room
// =====================================================

function renderNewBriefingLayout() {
  const regime = _computeRegimeEngine ? _computeRegimeEngine() : { label: "Neutral", score: 52, col: "var(--neutral)" };
  const topAssets = [...A].sort((a, b) => b.sc - a.sc).slice(0, 6);

  // Use actual brief if loaded, else placeholder + generate button
  let briefSection = '';
  if (_briefLoad) {
    briefSection = `
      <div class="card" style="padding: var(--space-6); text-align:center;">
        <div style="width:16px;height:16px;border:2px solid var(--accent);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div>
        <div class="meta">GENERATING DISPATCH BRIEF…</div>
      </div>
    `;
  } else if (_brief) {
    const b = _brief;
    const vc = (b.houseView === "Constructive" || b.houseView === "Opportunistic") ? "var(--gn)" : (b.houseView === "Defensive" || b.houseView === "Cautious") ? "var(--rd)" : "var(--accent)";
    briefSection = `
      <div class="card reveal" style="padding: var(--space-5);">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
          <div>
            <div class="meta">DISPATCH BRIEF · ${b.date || 'TODAY'} · ${(b._local || b._free || b._fallback) ? 'FREE DESK' : 'AI PREMIUM'}</div>
            <div class="heading" style="font-size:20px; margin:4px 0;">${b.headline || 'Market Brief'}</div>
          </div>
          <div style="text-align:right; font-size:11px;">
            <span style="color:${vc}; font-weight:600;">${b.houseView || 'Neutral'}</span><br>
            ${b.confidence ? `Confidence ${b.confidence}` : ''}
          </div>
        </div>
        <p style="color:var(--text-secondary); font-size:14px; line-height:1.45;">${b.summary || ''}</p>
        ${b.focusTickers && b.focusTickers.length ? `<div style="margin-top:8px;"><span class="meta">FOCUS</span> ${b.focusTickers.map(t => `<button onclick="openA('${(t.match(/^[A-Z.]+/)||[t])[0]}')" class="btn" style="padding:2px 8px; font-size:11px; margin:2px;">${t}</button>`).join(' ')}</div>` : ''}
        <div style="margin-top:12px; display:flex; gap:8px; flex-wrap:wrap;">
          <button onclick="loadDispatchBrief(true)" class="btn">↻ Refresh Brief</button>
          <button onclick="_exportBriefText()" class="btn">Copy</button>
          <button onclick="nav('intel')" class="btn">Ask Expert</button>
        </div>
      </div>
    `;
  } else {
    briefSection = `
      <div class="card" style="padding: var(--space-6);">
        <div class="meta" style="margin-bottom:4px;">FREE DESK BRIEF</div>
        <div class="heading" style="font-size:22px; line-height:1.15; margin-bottom:8px;">Generate today's house view — free</div>
        <p style="color:var(--text-secondary); margin-bottom:12px;">Built from live Yahoo tape, regime engine, signals &amp; headlines. No API key needed. Premium upgrades to LLM AI Brief.</p>
        <button onclick="loadDispatchBrief(true)" class="btn btn-primary" style="width:100%;">Generate Free Brief</button>
      </div>
    `;
  }

  return `
    <div class="section reveal">
      <div class="section-header">
        <div>
          <div class="meta">LONDON • ${new Date().toLocaleDateString('en-GB', { weekday: 'long', month: 'long', day: 'numeric' })}</div>
          <h2 class="display">Morning Intelligence</h2>
        </div>
        <div>
          <span class="meta">REGIME</span><br>
          <strong style="font-size:15px; color:${regime.col}">${regime.label}</strong>
        </div>
      </div>

      <!-- Hero / Brief -->
      ${briefSection}
    </div>

    <!-- Command Center — beautiful cards -->
    <div class="section reveal">
      <div class="section-header">
        <h2>Command Center</h2>
        <span class="meta">LIVE · ${liveSymbols.size} SYNCED</span>
      </div>
      <div class="data-grid">
        ${topAssets.map(a => {
          const d = fp(a.tk);
          const na = d.status === "unavailable";
          const chN = liveChg(a.tk);
          const sign = chN != null && chN >= 0 ? '+' : '';
          const chgCol = na || chN == null ? '' : chN > 0 ? 'positive' : chN < 0 ? 'negative' : '';
          return `
            <div class="data-card hover-lift" data-tk="${a.tk}" onclick="openA('${a.tk}')">
              <div class="label">${a.nm}</div>
              <div class="value">${na?"—":d.p}</div>
              <div class="change ${chgCol}">${na||chN==null?"—":`${sign}${d.chg} (${sign}${d.c}%)`}</div>
              <div style="margin-top:10px; font-size:11px; color:var(--text-tertiary);">${a.se} · ${a.sc}/100</div>
            </div>
          `;
        }).join('')}
      </div>
    </div>

    <!-- Editorial News Feed -->
    <div class="section reveal">
      <div class="section-header">
        <h2>Editorial Desk</h2>
        <span onclick="nav('news')" style="cursor:pointer; color:var(--accent);" class="meta">VIEW ALL →</span>
      </div>
      <div class="news-list">
        ${renderNewNewsCards()}
      </div>
    </div>

    <!-- Intelligence Modules -->
    <div class="section reveal">
      <div class="section-header">
        <h2>Intelligence Modules</h2>
      </div>
      <div class="data-grid">
        <div class="card hover-lift" onclick="nav('sig')">
          <div class="card-header">
            <div class="card-title">Conviction Signals</div>
            <div class="meta">${(typeof SIGS!=="undefined"&&SIGS.length)?SIGS.length+" ACTIVE":"SIGNALS"}</div>
          </div>
          <p style="color:var(--text-secondary);">High-conviction macro and micro signals with confidence scores and time horizons.</p>
        </div>
        <div class="card hover-lift" onclick="nav('research')">
          <div class="card-header">
            <div class="card-title">Research Briefs</div>
            <div class="meta">${(typeof REPORTS!=="undefined"&&REPORTS.length)?REPORTS.length+" PUBLISHED":"RESEARCH"}</div>
          </div>
          <p style="color:var(--text-secondary);">Deep, scenario-based research with clear investment implications and risk frameworks.</p>
        </div>
        <div class="card hover-lift" onclick="nav('intel')">
          <div class="card-header">
            <div class="card-title">AI Committee</div>
            <div class="meta">${liveSymbols.size?liveSymbols.size+" FEED":"READY"}</div>
          </div>
          <p style="color:var(--text-secondary);">Multi-model synthesis. Ask anything about regime, assets, or thesis stress-testing.</p>
        </div>
      </div>
    </div>

    <div style="height:60px;"></div>
  `;
}

function renderNewNewsCards() {
  // Prefer live NEWS array; fall back to short placeholders only if feeds empty
  if (typeof NEWS !== "undefined" && NEWS.length) {
    return NEWS.slice(0, 4).map(n => `
    <div class="news-card hover-lift" onclick="${n.link?`window.open('${String(n.link).replace(/'/g,"%27")}','_blank','noopener')`:`nav('news')`}">
      <div>
        <div class="headline">${(n.x||"").replace(/</g,"&lt;")}</div>
        <div class="deck">${(n.desc||n.tg||"Dispatch wire").toString().replace(/</g,"&lt;").slice(0,120)}</div>
        <div class="byline">${n.src||"Wire"} · ${_newsRelTime?_newsRelTime(n.ts):(n.t||"")}</div>
      </div>
    </div>`).join("");
  }
  const news = [
    { title: "Energy complex re-pricing on supply constraints", source: "Dispatch Desk", time: "14m ago" },
    { title: "AI capex cycle showing early signs of broadening", source: "Research", time: "42m ago" },
    { title: "Central banks signal data-dependent stance into Q3", source: "Macro Note", time: "1h ago" },
  ];

  return news.map(item => `
    <div class="news-card hover-lift" onclick="nav('news')">
      <div>
        <div class="headline">${item.title || item.headline || 'Market development'}</div>
        <div class="deck">${item.summary || 'Key implications for positioning and risk.'}</div>
        <div class="byline">${item.source || 'Dispatch Desk'} · ${item.time || 'recent'}</div>
      </div>
    </div>
  `).join('');
}

// Legacy top-bar wiring — real routes only (no dummy “coming soon” shells)
function wireNewNavigation() {
  wireTopNav();
}

// Scroll reveals (subtle, editorial) - robust version to prevent flicker
let _revealObserver = null;

function setupScrollReveals() {
  const els = document.querySelectorAll('.reveal:not(.visible)');
  if (!els.length) return;

  if (!_revealObserver) {
    _revealObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          // Use requestAnimationFrame to avoid sync style changes
          requestAnimationFrame(() => {
            if (entry.target) entry.target.classList.add('visible');
          });
          _revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08, rootMargin: "0px 0px -80px 0px" });
  }

  els.forEach(el => {
    // Skip if already observed
    if (!el._observed) {
      el._observed = true;
      _revealObserver.observe(el);
    }
  });
}

// Card micro-interactions
function enhanceCardInteractions() {
  document.querySelectorAll('.card, .data-card, .news-card').forEach(card => {
    card.style.transition = `transform var(--duration) var(--ease), box-shadow var(--duration) var(--ease), border-color var(--duration-fast) var(--ease)`;
  });
}

// Full multi-page terminal (restored) — NOT the single briefing shell
function renderMain() {
  const el = document.getElementById("main");
  if (!el) return;

  // #main is the phone shell. On desktop it sits inside a display:none wrapper
  // while an overlay owns the page, so painting it is invisible work — and
  // worse, it duplicates every id the overlay already used. getElementById
  // returns the first match in document order, and #main comes first, so the
  // desk-letter / desk-spine jumps and the trust-bar repaint would silently
  // address the hidden copy. Leave the shell alone while it is not displayed.
  if (el.offsetParent === null && getComputedStyle(el).position !== "fixed") return;

  const _sv = el.scrollTop; // keep scroll on live updates
  let html = "";
  switch (pg) {
    case "home": html = renderHome(); break;
    case "dash": html = renderDash(); break;
    case "gold": html = renderGoldDesk(); break;
    case "playbook": html = renderPlaybook(); break;
    case "brief": html = renderBrief(); break;
    case "mkt": html = renderMkt(); break;
    case "anlz": html = renderAnlz(); break;
    case "sig": html = renderSig(); break;
    case "news": html = renderNews(); break;
    case "watch": html = renderWatch(); break;
    case "port": html = renderPortfolio(); break;
    case "lab": html = renderLab(); break;
    // Markets children
    case "scr": html = renderScreener(); break;
    case "sectors": html = renderSectorTracker(); break;
    case "heat": html = renderHeat(); break;
    case "crypto": html = renderCryptoPage(); break;
    // Intel children
    case "paper": html = renderNewspaper(); break;
    case "research": html = renderResearch(); break;
    case "intel": html = renderDocIntel(); break;
    case "geo": html = renderGeoOps(); break;
    // Book
    case "learn": html = renderLearn(); break;
    // Anything genuinely unknown lands on the desk rather than a blank screen.
    // Every route in NAV_ALL must have a case above — falling through to Dash
    // is how the nine restored surfaces silently showed the Dashboard on
    // phones while desktop looked correct.
    default: html = renderDash();
  }
  el.innerHTML = html + (typeof _siteFooter === "function" ? _siteFooter() : "");
  if (typeof _fxPageEnter === "function") _fxPageEnter(el);
  if (_sv > 10) requestAnimationFrame(() => { el.scrollTop = _sv; });

  // Auto-load free desk brief once when landing on dash/brief
  if (
    (pg === "dash" || pg === "brief") &&
    !_brief && !_briefLoad && !_briefAutoTried &&
    typeof loadDispatchBrief === "function"
  ) {
    setTimeout(() => loadDispatchBrief(false), 200);
  }
}

// ═══════════════════════════════════════════════════════════
// DISPATCH EXPERT — RESEARCH CHAT
// ═══════════════════════════════════════════════════════════
let _chatOpen = false, _chatLoad = false, _chatStatus = "", _chatStatusIv = null;
let _chatActMap = {};
let _chatMsgs = [];
try { _chatMsgs = JSON.parse(sessionStorage.getItem("td_chat") || "[]"); } catch (e) { _chatMsgs = []; }

const CHAT_STARTERS = [
  "Full regime brief — what to overweight now?",
  "Stress-test my portfolio against today's signals",
  "Deep dive my active ticker — setup, risks, catalysts",
  "What's the house view in today's Dispatch Brief?",
  "Rank my watchlist for this regime"
];

const CHAT_VERDICT_COL = { OVERWEIGHT: "var(--gn)", NEUTRAL: "var(--gd)", UNDERWEIGHT: "var(--rd)", MONITOR: "var(--bl)", "RISK-OFF": "var(--rd)" };

const CHAT_PAGE_NAMES = { dash: "Dashboard", brief: "Dispatch Brief", gold: "Gold Dashboard", playbook: "Weekly Playbook", mkt: "Markets", anlz: "Ticker Analysis", sig: "Signals", news: "News", watch: "Watchlist", port: "Portfolio", lab: "Market Lab" };

function _extractChatTickers(text) {
  const known = new Set();
  if (selTk) known.add(selTk);
  getActiveWl().tickers.forEach(t => known.add(t));
  portfolio.forEach(p => known.add(p.tk));
  const upper = (text || "").toUpperCase();
  A.forEach(a => { if (upper.includes(a.tk)) known.add(a.tk); });
  Object.keys(P).forEach(tk => { if (upper.includes(tk)) known.add(tk); });
  (text.match(/\$?([A-Z]{1,5}(?:\.[A-Z]{1,2})?)/g) || []).forEach(m => {
    const t = m.replace("$", "").toUpperCase();
    if (P[t] || A.find(x => x.tk === t)) known.add(t);
  });
  return [...known].slice(0, 6);
}

function _buildChatContext() {
  const re = _computeRegimeEngine();
  const fg = calcFearGreed();
  const parts = [
    `Page: ${CHAT_PAGE_NAMES[pg] || pg}`,
    `Regime: ${re.label} (score ${re.score}/100)`,
    re.narrative,
    `Overweight: ${re.overweight.join(", ")} | Underweight: ${re.underweight.join(", ")}`,
    `Sector rotation: ${re.rotation?.label || "—"}`,
    `Fear/Greed: ${fg.label} (${fg.score != null ? fg.score : "—"}/100)`,
  ];
  // Live tape only — never pass "—" / "$—" into the model as quotes
  const tapeLine = [
    _liveTapeBit(re.spxProxy ? "SPY" : "SPX", "SPX", "SPY"),
    _liveTapeBit("VIX", "VIX"),
    _liveTapeBit("DXY", "DXY"),
    _liveTapeBit("Oil", "WTI"),
    _liveTapeBit("Gold", "XAU"),
    _liveTapeBit("BTC", "BTC"),
  ].filter(Boolean).join(" · ") || "awaiting live feed";
  parts.push(`Live tape: ${tapeLine}`);
  if (_brief?.headline) {
    parts.push(`Dispatch Brief (${_brief.date || "today"}): ${_brief.headline} — ${_brief.houseView}`);
    if (_brief.summary) parts.push(`Brief summary: ${_brief.summary}`);
    if (_brief.focusTickers?.length) parts.push(`Brief focus: ${_brief.focusTickers.slice(0, 5).join("; ")}`);
    if (_brief.risks?.length) parts.push(`Brief risks: ${_brief.risks.join("; ")}`);
  }
  const topSig = SIGS.slice().sort((a, b) => b.cf - a.cf).slice(0, 6);
  parts.push("Macro signals:\n" + topSig.map(s => `• ${s.a} (${s.cf}% ${s.cat}): ${s.x}`).join("\n"));
  const headlines = NEWS.slice(0, 6).map(n => `• [${n.tg}] ${n.x}`).join("\n");
  if (headlines) parts.push("Latest headlines:\n" + headlines);
  const wl = getActiveWl().tickers;
  if (wl.length) {
    const wlPx = wl.slice(0, 8).map(tk => {
      const px = livePx(tk);
      const ch = liveChg(tk);
      const a = A.find(x => x.tk === tk);
      if (px == null) return `${tk} NO SYNC${a ? ` score ${a.sc}` : ""}`;
      const chg = ch != null ? ` (${ch >= 0 ? "+" : ""}${ch}%)` : "";
      return `${tk} $${px}${chg}${a ? ` score ${a.sc}` : ""}`;
    });
    parts.push(`Watchlist (${getActiveWl().name}): ${wlPx.join(" · ")}`);
  }
  if (portfolio.length) {
    const portLines = portfolio.slice(0, 6).map(pos => {
      const m = _portMark(pos);
      return m.live
        ? `${pos.tk} ×${pos.qty} @ $${pos.avgCost} → $${m.px.toFixed(2)} (${m.chg!=null?m.chg+"%":"—"}) ~$${m.value.toFixed(0)}`
        : `${pos.tk} ×${pos.qty} @ $${pos.avgCost} → NO SYNC (at cost ~$${m.value.toFixed(0)})`;
    });
    parts.push(`Portfolio:\n${portLines.join("\n")}`);
  }
  if (selTk) {
    const a = A.find(x => x.tk === selTk);
    const px = livePx(selTk);
    const ch = liveChg(selTk);
    const pxBit = px != null
      ? `$${px}${ch != null ? ` (${ch >= 0 ? "+" : ""}${ch}%)` : ""}`
      : "NO SYNC (do not invent a price)";
    if (a) {
      parts.push(`Active ticker: ${a.tk} ${a.nm} · Score ${a.sc}/100 · ${a.se} · ${a.ra || "—"} · ${pxBit} · Beta ${a.beta || "—"} · ${a.pe || "—"}`);
      if (a.th) parts.push(`Platform thesis: ${a.th}`);
    } else {
      parts.push(`Active ticker: ${selTk} · ${pxBit}`);
    }
    if (comRes && pg === "anlz") {
      const synth = _getSynthesis(comRes);
      if (synth) parts.push(`Lens verdict: ${synth.verdict || "—"} (${synth.confidence || "—"}% confidence) — ${(synth.analysis || "").slice(0, 400)}`);
      const members = _getLensMembers(comRes);
      if (members?.length) {
        parts.push("Lens breakdown: " + members.filter(l => l.name !== "Risk Synthesis").map(l => `${l.name}: ${l.verdict}`).join(" · "));
      }
    }
    const fin = _finCache[selTk];
    if (fin?.metrics) {
      const m = fin.metrics;
      parts.push(`Financials: P/E ${m.peTTM ?? "—"} · ROE ${m.roeTTM ?? "—"}% · Rev growth ${m.revenueGrowthTTM ?? "—"}%`);
    }
    const ear = _earnCache[selTk];
    if (ear?.history?.length) {
      const h = ear.history[0];
      const br = ear.beatRate != null ? ear.beatRate + "%" : "n/a";
      parts.push(`Earnings: beat rate ${br} · last ${h.quarter} $${h.actual} vs $${h.estimate} (${h.beat ? "beat" : "miss"})`);
    }
    const pxLive = livePx(selTk);
    const chgLive = liveChg(selTk);
    if (pxLive != null) {
      parts.push(`Live price: $${pxLive}${chgLive != null ? ` (${chgLive >= 0 ? "+" : ""}${chgLive}%)` : ""} [feed]`);
    } else {
      parts.push("Live price: NO SYNC");
    }
  }
  try {
    const hist = _lsJson(localStorage.getItem("td_lens_hist"), []);
    if (hist.length) {
      parts.push("Recent lens runs: " + hist.slice(0, 3).map(h => `${h.ticker} → ${h.verdict} (${h.regime || "—"})`).join(" · "));
    }
  } catch (e) { /* skip */ }
  const topConv = [...A].sort((a, b) => b.sc - a.sc).slice(0, 5).map(a => `${a.tk} ${a.sc}`).join(", ");
  parts.push(`Top conviction scores: ${topConv}`);
  return parts.join("\n");
}

function _chatKnownTickers() {
  const s = new Set();
  A.forEach(a => s.add(a.tk));
  Object.keys(P).forEach(tk => s.add(tk));
  getActiveWl().tickers.forEach(t => s.add(t));
  portfolio.forEach(p => s.add(p.tk));
  if (selTk) s.add(selTk);
  return [...s];
}

function _chatMd(text) {
  if (!text) return "";
  let s = String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  s = s.replace(/^## (.+)$/gm, '<div class="chat-h2">$1</div>');
  s = s.replace(/^### (.+)$/gm, '<div class="chat-h3">$1</div>');
  s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  s = s.replace(/`([^`]+)`/g, '<code class="chat-code">$1</code>');
  s = s.replace(/^[-•] (.+)$/gm, '<div class="chat-li"><span class="chat-li-dot">▸</span>$1</div>');
  s = s.replace(/\n\n/g, "</p><p>");
  return `<p>${s}</p>`;
}

function _chatVerdictCol(v) {
  return CHAT_VERDICT_COL[String(v || "").toUpperCase()] || "var(--bl)";
}

function _chatRunAction(act) {
  if (!act) return;
  const t = act.type, v = act.value || "";
  if (t === "ticker" && v) { openA(v); toggleChat(); return; }
  if (t === "lens" && v) { openA(v); setTimeout(() => runCommittee(v), 400); toggleChat(); return; }
  if (t === "page" && v) { nav(v); if (v === "brief") loadDispatchBrief(true); toggleChat(); return; }
}
function _chatRunActionById(id) { _chatRunAction(_chatActMap[id]); }

function _chatAskFollowUp(q) {
  const inp = document.getElementById("chatInp");
  if (inp) { inp.value = q; sendChatMessage(); }
}

function _renderBotMsg(m, idx) {
  const st = m.structured;
  if (!st) return `<div class="chat-msg bot">${_chatMd(m.content)}</div>`;
  const vc = _chatVerdictCol(st.verdict);
  const pills = (st.dataUsed || []).slice(0, 4).map(d => `<span class="chat-pill">${String(d).replace(/</g, "&lt;")}</span>`).join("");
  const risks = (st.risks || []).slice(0, 3).map(r => `<div class="chat-li chat-li-risk"><span class="chat-li-dot">!</span>${r.replace(/</g, "&lt;")}</div>`).join("");
  const cats = (st.catalysts || []).slice(0, 3).map(c => `<div class="chat-li chat-li-cat"><span class="chat-li-dot">◆</span>${c.replace(/</g, "&lt;")}</div>`).join("");
  const acts = (st.actions || []).map((a, i) => {
    const id = `c${idx}a${i}`;
    _chatActMap[id] = a;
    return `<button type="button" class="chat-act" onclick="_chatRunActionById('${id}')">${(a.label || a.value || "").replace(/</g, "&lt;")}</button>`;
  }).join("");
  const fus = (st.followUps || []).map(f => `<button type="button" class="chat-fu" onclick="_chatAskFollowUp(this.dataset.q)" data-q="${f.replace(/"/g, "&quot;").replace(/</g, "&lt;")}">${f.replace(/</g, "&lt;")}</button>`).join("");
  const searchTag = m.meta?.usedSearch ? '<span class="chat-pill chat-pill-web">↗ web search</span>' : "";
  return `<div class="chat-msg bot chat-rich">
    <div class="chat-verdict-row">
      <span class="chat-verdict" style="color:${vc};border-color:${vc}">${(st.verdict || "MONITOR").replace(/</g, "&lt;")}</span>
      ${st.confidence != null ? `<span class="chat-conf">${st.confidence}% conf.</span>` : ""}
    </div>
    ${st.headline ? `<div class="chat-headline">${st.headline.replace(/</g, "&lt;")}</div>` : ""}
    <div class="chat-body">${_chatMd(m.content)}</div>
    ${risks ? `<div class="chat-block"><div class="chat-block-lbl">RISKS</div>${risks}</div>` : ""}
    ${cats ? `<div class="chat-block"><div class="chat-block-lbl">CATALYSTS</div>${cats}</div>` : ""}
    ${acts ? `<div class="chat-acts">${acts}</div>` : ""}
    ${fus ? `<div class="chat-fus">${fus}</div>` : ""}
    <div class="chat-pills">${searchTag}${pills}</div>
  </div>`;
}

function _persistChat() {
  try { sessionStorage.setItem("td_chat", JSON.stringify(_chatMsgs.slice(-20))); } catch (e) { /* skip */ }
}

function _chatStartStatus() {
  const steps = ["Reading your session…", "Fetching live quotes…", "Grok analysis…", "Synthesising view…"];
  let i = 0;
  _chatStatus = steps[0];
  clearInterval(_chatStatusIv);
  _chatStatusIv = setInterval(() => { i = (i + 1) % steps.length; _chatStatus = steps[i]; _renderChatMsgs(); }, 2200);
}

function _chatStopStatus() {
  clearInterval(_chatStatusIv);
  _chatStatusIv = null;
  _chatStatus = "";
}

function _renderChatMsgs() {
  const el = document.getElementById("chatMsgs");
  const chips = document.getElementById("chatChips");
  if (!el) return;
  if (!_chatMsgs.length && !_chatLoad) {
    el.innerHTML = `<div class="chat-welcome">
      <div class="chat-welcome-icon">◆</div>
      <div class="chat-welcome-title">Dispatch Expert</div>
      <div class="chat-welcome-sub">Institutional research copilot — reads your live terminal and fuses market data with Grok.</div>
    </div>`;
    if (chips) chips.style.display = "";
    return;
  }
  let html = _chatMsgs.map((m, idx) => {
    if (m.role === "user") return `<div class="chat-msg user">${m.content.replace(/</g, "&lt;")}</div>`;
    return _renderBotMsg(m, idx);
  }).join("");
  if (_chatLoad) html += `<div class="chat-msg bot chat-thinking"><span class="chat-dot"></span><span class="chat-dot"></span><span class="chat-dot"></span><span>${_chatStatus || "Working…"}</span></div>`;
  el.innerHTML = html;
  el.scrollTop = el.scrollHeight;
  const fuEl = document.getElementById("chatChips");
  if (fuEl) {
    if (_chatLoad) { fuEl.style.display = "none"; }
    else if (!_chatMsgs.length) {
      fuEl.style.display = "";
      fuEl.innerHTML = CHAT_STARTERS.map((s, i) => `<button type="button" class="chat-chip" onclick="_chatChipIdx(${i})">${s}</button>`).join("");
    } else {
      const last = _chatMsgs.filter(m => m.role === "assistant").pop();
      if (last?.structured?.followUps?.length) {
        fuEl.style.display = "";
        fuEl.innerHTML = last.structured.followUps.map(f =>
          `<button type="button" class="chat-chip" onclick="_chatAskFollowUp(this.dataset.q)" data-q="${f.replace(/"/g, "&quot;").replace(/</g, "&lt;")}">${f.replace(/</g, "&lt;")}</button>`
        ).join("");
      } else { fuEl.style.display = "none"; }
    }
  }
}

function toggleChat() {
  _chatOpen = !_chatOpen;
  const panel = document.getElementById("chatPanel");
  const dockFab = document.getElementById("smartDockFab");
  const dock = document.querySelector(".smart-dock");
  if (panel) panel.classList.toggle("hide", !_chatOpen);
  if (dockFab) dockFab.classList.toggle("chat-on", _chatOpen);
  if (dock && !IS_DESKTOP()) dock.classList.toggle("smart-dock-chat-hide", _chatOpen);
  document.body.classList.toggle("chat-open", _chatOpen);
  if (_chatOpen) {
    _renderChatMsgs();
    setTimeout(() => document.getElementById("chatInp")?.focus(), 80);
  }
}

function _chatChipIdx(i) {
  const s = CHAT_STARTERS[i];
  if (!s) return;
  const inp = document.getElementById("chatInp");
  if (inp) { inp.value = s; sendChatMessage(); }
}

async function sendChatMessage() {
  if (_chatLoad) return;
  if (!_isPremium()) { _showLoginGate("Dispatch Expert"); return; }
  const inp = document.getElementById("chatInp");
  const text = (inp?.value || "").trim();
  if (!text) return;
  inp.value = "";
  _chatMsgs.push({ role: "user", content: text });
  _chatLoad = true;
  _chatStartStatus();
  _renderChatMsgs();
  const btn = document.getElementById("chatSend");
  if (btn) btn.disabled = true;
  const tickers = _extractChatTickers(text);
  try {
    await Promise.all(tickers.slice(0, 3).map(tk => _prefetchLensData(tk)));
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: _chatMsgs.map(m => ({ role: m.role, content: m.content })),
        context: _buildChatContext(),
        tickers,
        knownTickers: _chatKnownTickers()
      })
    });
    const data = await res.json().catch(() => ({}));
    if (res.status === 401) { _chatMsgs.pop(); _showLoginGate("Dispatch Expert"); return; }
    if (!res.ok) {
      const err = typeof data.error === "string" ? data.error : "";
      let msg = err || "Unable to respond right now. Try again shortly.";
      if (data.limitReached || /usage limits/i.test(err)) {
        msg = "Dispatch Expert is temporarily rate limited. Please try again shortly.";
      }
      _chatMsgs.push({ role: "assistant", content: msg });
      return;
    }
    _chatMsgs.push({
      role: "assistant",
      content: data.reply || "No response.",
      structured: data.structured || null,
      meta: data.meta || null
    });
    _persistChat();
  } catch (e) {
    _chatMsgs.push({ role: "assistant", content: "Network error — check your connection and try again." });
  } finally {
    _chatLoad = false;
    _chatStopStatus();
    if (btn) btn.disabled = false;
    _renderChatMsgs();
  }
}

function clearChat() {
  _chatMsgs = [];
  sessionStorage.removeItem("td_chat");
  _renderChatMsgs();
}

function initChatWidget() {
  if (document.getElementById("chatPanel")) return;
  const panel = document.createElement("div");
  panel.id = "chatPanel";
  panel.className = "chat-panel hide";
  panel.innerHTML = `<div class="chat-hdr">
      <div><div class="chat-hdr-title">Dispatch Expert</div><div class="chat-hdr-sub">Grok · live market fusion</div></div>
      <div style="display:flex;gap:6px">
        <button onclick="clearChat()" style="background:var(--b3);border:none;color:var(--t3);border-radius:6px;padding:4px 8px;font-family:var(--mn);font-size:8px;cursor:pointer">Clear</button>
        <button onclick="toggleChat()" style="background:var(--b3);border:none;color:var(--t2);border-radius:50%;width:28px;height:28px;cursor:pointer;font-size:14px">×</button>
      </div>
    </div>
    <div class="chat-msgs" id="chatMsgs"></div>
    <div class="chat-chips" id="chatChips">${CHAT_STARTERS.map((s, i) => `<button type="button" class="chat-chip" onclick="_chatChipIdx(${i})">${s}</button>`).join("")}</div>
    <div class="chat-input-row">
      <textarea id="chatInp" class="chat-input" rows="1" placeholder="Ask about markets, tickers, regime…" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendChatMessage();}"></textarea>
      <button id="chatSend" class="chat-send" onclick="sendChatMessage()">Send</button>
    </div>`;
  document.body.appendChild(panel);
}

// ═══════════════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════════════

renderAuthButtons();
_initUserTier().then(()=>{
  const checkout=new URLSearchParams(location.search).get("checkout");
  if(checkout==="1"){
    history.replaceState({}, "", location.pathname);
    _startCheckout({textContent:"Continue to secure checkout",disabled:false,style:{}});
    return;
  }
  if(checkout==="cancelled"){
    history.replaceState({}, "", location.pathname);
    showToast("Checkout cancelled — no payment was taken","var(--t3)");
    return;
  }
  if(_isPremium()&&(new URLSearchParams(location.search).get("welcome")==="premium"||checkout==="success")){
    history.replaceState({},"",location.pathname);
    showToast("Premium activated","var(--gd)");
    setTimeout(_showPremiumWelcome,400);
  } else if(checkout==="success"){
    history.replaceState({},"",location.pathname);
    showToast("Payment received — confirming your membership…","var(--gd)");
    let tries=0;
    const confirmMembership=setInterval(async()=>{
      tries++;
      await _initUserTier();
      if(_isPremium()||tries>=6){
        clearInterval(confirmMembership);
        if(_isPremium())setTimeout(_showPremiumWelcome,100);
      }
    },1500);
  }
});
initTechShell();
_applyChromeFocus();
_initResponsiveShell();
_initStatusGestures();
_loadPriceCache();
_loadNewsCache();
_initStripeMode();

// Boot lands on Home — the desk needed a front door, and arriving straight
// inside one product gave a first-time visitor nothing to orient against.
// Home is orientation only; Gold is one tap from it and keeps its own slot in
// both the rail and the bottom bar. Change this one string to go back to
// "gold" (the pre-Home behaviour, per PRODUCT_V1.md and commit a4da627) or to
// "brief" for the daily house view.
renderTape();
renderStatus();
renderNav();
try {
  nav("home");
} catch (e) {
  renderMain();
}
updateClock();
if (typeof updateSidebarActive === "function") updateSidebarActive();

// A lightweight first-visit cue leaves the terminal immediately available.
if (!localStorage.getItem("td_onboard_v3")) {
  setTimeout(showProductOnboarding, 600);
}
// Apply saved panel visibility
Object.entries(panelVis).forEach(([id,vis])=>{
  if(!vis){const p=document.getElementById(id);if(p)p.style.display='none';}
});
setInterval(updateClock,1000);
setInterval(updateTermClock,1000);

const isMobile = MOBILE();
setInterval(doTick, isMobile ? MOBILE_DO_TICK : 10000); // further throttled on mobile

fetchLiveNews();
// Crypto loads lazily on first visit to the Crypto page (see nav()).
fetchLivePrices();
fetchInitialHistory();
if(!Object.keys(_sectorData).length)setTimeout(()=>fetchSectorData(),2000);
setTimeout(()=>loadDispatchBrief(false),3000);
setTimeout(()=>loadEarningsRadar(),4500);
setInterval(fetchLiveNews, isMobile ? MOBILE_NEWS_FREQ * 1000 : 600000);
const effectivePriceFreq = isMobile ? Math.max(updateFreq || 60, MOBILE_PRICE_FREQ) : (updateFreq || 60);
_priceInterval=setInterval(fetchLivePrices, effectivePriceFreq * 1000);
setInterval(renderStatus, isMobile ? MOBILE_STATUS_FREQ : 5000);

_initKeyboard();
wireTopNav();
enhanceCommandPalette();
