const assert = require("node:assert/strict");
const http = require("node:http");
const Module = require("node:module");
const test = require("node:test");

const originalLoad = Module._load;
Module._load = function loadStub(request, parent, isMain) {
  if (request === "@neondatabase/serverless") {
    return { neon: () => async () => [] };
  }
  if (request === "@replit/connectors-sdk") {
    return { ReplitConnectors: class { async proxy() { return { ok: false, status: 503 }; } } };
  }
  if (request === "stripe-replit-sync") {
    return { runMigrations: async () => {} };
  }
  if (request === "./stripeClient") {
    return {
      ensureDispatchPremiumPrice: async () => ({ id: "price" }),
      getStripeMode: async () => "test",
      getStripeSync: async () => ({}),
      getUncachableStripeClient: async () => ({}),
    };
  }
  return originalLoad.call(this, request, parent, isMain);
};

const { attachSecurityHeaders } = require("../marketProxy");
const { handle } = require("../server");

const USGS_FIXTURE = {
  features: [
    {
      id: "us7000keep",
      properties: {
        mag: 4.8,
        place: "119 km S of Dampit, Indonesia",
        time: Date.now() - 3600_000,
        url: "https://earthquake.usgs.gov/earthquakes/eventpage/us7000keep",
      },
      geometry: { coordinates: [112.9014, -9.2825, 33.378] },
    },
  ],
};

function withMockedFetch(impl, work) {
  const original = global.fetch;
  const mocked = async (...args) => impl(...args);
  mocked.original = original;
  global.fetch = mocked;
  return Promise.resolve()
    .then(work)
    .finally(() => { global.fetch = original; });
}

function listen() {
  const server = http.createServer((req, res) => {
    attachSecurityHeaders(res);
    handle(req, res).catch(err => {
      if (!res.headersSent) res.writeHead(500).end(String(err));
    });
  });
  return new Promise(resolve => {
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address();
      resolve({ server, baseUrl: `http://127.0.0.1:${port}` });
    });
  });
}

async function request(baseUrl, path) {
  const response = await fetch(`${baseUrl}${path}`);
  const headers = Object.fromEntries(response.headers);
  const text = await response.text();
  let body;
  try { body = JSON.parse(text); } catch { body = text; }
  return { status: response.status, headers, body };
}

test("geo, CoinGecko, assets, and security headers on the real request handler", async () => {
  const { server, baseUrl } = await listen();
  const fetchCalls = [];
  await withMockedFetch(async (url, options) => {
    const href = String(url);
    if (href.startsWith("http://127.0.0.1") || href.startsWith("http://localhost")) {
      return fetch.original(url, options);
    }
    fetchCalls.push(href);
    if (href.includes("earthquake.usgs.gov")) {
      assert.match(href, /4\.5_week\.geojson/);
      return { ok: true, json: async () => USGS_FIXTURE };
    }
    if (href.includes("api.coingecko.com/api/v3/simple/price")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          bitcoin: { usd: 77651, usd_24h_change: 0.49 },
          ethereum: { usd: 2513.98, usd_24h_change: -0.24 },
        }),
      };
    }
    return { ok: false, status: 599, json: async () => ({}) };
  }, async () => {
    const cold = await request(baseUrl, "/api/geo?minmag=4.5&days=7");
    assert.equal(cold.status, 200);
    assert.equal(cold.headers["cache-control"], "public, max-age=60");
    assert.equal(cold.headers["x-dispatch-cache"], "miss");
    assert.equal(cold.headers["x-content-type-options"], "nosniff");
    assert.equal(cold.headers["referrer-policy"], "strict-origin-when-cross-origin");
    assert.equal(cold.headers["x-frame-options"], "DENY");
    assert.match(cold.headers["permissions-policy"], /camera=\(\)/);
    assert.equal(cold.headers["content-security-policy"], undefined);
    assert.equal(cold.body.status, "available");
    assert.equal(cold.body.events.length, 1);
    assert.equal(cold.body.events[0].mag, 4.8);

    const warm = await request(baseUrl, "/api/geo?minmag=4.5&days=7");
    assert.equal(warm.headers["x-dispatch-cache"], "hit");
    assert.equal(fetchCalls.filter(url => url.includes("earthquake.usgs.gov")).length, 1);

    const encoded = await request(
      baseUrl,
      "/api/coingecko?path=%2Fsimple%2Fprice%3Fids%3Dbitcoin%2Cethereum%26vs_currencies%3Dusd%26include_24hr_change%3Dtrue",
    );
    assert.equal(encoded.status, 200);
    assert.equal(encoded.body.bitcoin.usd, 77651);
    assert.equal(encoded.headers["cache-control"], "public, max-age=30");

    const sibling = await request(
      baseUrl,
      "/api/coingecko?path=/simple/price&ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true",
    );
    assert.equal(sibling.body.ethereum.usd, 2513.98);
    assert.equal(sibling.headers["x-dispatch-cache"], "hit");

    const html = await request(baseUrl, "/");
    assert.equal(html.status, 200);
    assert.equal(html.headers["cache-control"], "no-store");
    assert.equal(html.headers["x-content-type-options"], "nosniff");
    assert.equal(html.headers["x-frame-options"], "DENY");
    assert.match(html.body, /app\.js\?v=1789358000/);
    assert.match(html.body, /styles\.css\?v=1789358000/);

    const asset = await request(baseUrl, "/app.js?v=1789358000");
    assert.equal(asset.status, 200);
    assert.equal(asset.headers["cache-control"], "public, max-age=31536000, immutable");
    assert.equal(asset.headers["x-content-type-options"], "nosniff");

    const css = await request(baseUrl, "/styles.css?v=1789358000");
    assert.equal(css.headers["cache-control"], "public, max-age=31536000, immutable");
  }).finally(() => new Promise(resolve => server.close(resolve)));
});
