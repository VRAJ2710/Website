#!/usr/bin/env node
"use strict";
/**
 * Isolated rt52ops harness. Speaks raw http to a serveStatic-shaped function.
 * Does not load or start the repo server.js (that process deletes Stripe webhooks).
 */
const http = require("http");
const fs = require("fs");
const os = require("os");
const path = require("path");
const crypto = require("crypto");
const { spawnSync } = require("child_process");

const ROOT = path.resolve(__dirname, "../..");
const PATCH = path.join(ROOT, "deploy/patch_rt52ops.py");
const SRI = path.join(ROOT, "deploy/patch_rt52sri.py");
const ROUTES = [
  "pricing", "brief", "playbook", "gold", "markets", "news", "research", "signals",
  "dashboard", "learn", "portfolio", "watchlist", "lab", "screener", "sectors",
  "heatmap", "crypto", "paper", "geo", "brief/dispatch-brief", "report/spx2026",
  "research/research-desk",
];

const fails = [];
function check(name, cond, extra) {
  const ok = !!cond;
  console.log((ok ? "PASS " : "FAIL ") + name + (extra ? "  [" + extra + "]" : ""));
  if (!ok) fails.push(name);
}

function writeFile(p, body) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, body);
}

function sha(p) {
  return crypto.createHash("sha256").update(fs.readFileSync(p)).digest("hex");
}

const FIXTURE_BODY = String.raw`
const fs = require("fs");
const path = require("path");
const root = process.env.RT52OPS_ROOT;
const ROUTES = ${JSON.stringify(ROUTES)};
function json(res, status, body) {
  const data = JSON.stringify(body);
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
  });
  res.end(data);
}
function serveStatic(req, res, pathname, searchParams) {
  if (pathname === "/index.html") {
    res.writeHead(308, { Location: "/", "Cache-Control": "no-store", "Content-Type": "text/html" });
    res.end();
    return true;
  }
  if (pathname === "/favicon.ico") {
    res.writeHead(301, { Location: "/logo-mark.svg", "Cache-Control": "public, max-age=86400", "Content-Type": "text/html" });
    res.end();
    return true;
  }
  let rel = String(pathname || "/");
  if (rel.length > 1 && rel.endsWith("/")) rel = rel.slice(0, -1);
  const lower = rel.toLowerCase();
  if (rel === "/" ) rel = "index.html";
  else {
    let mapped = null;
    for (const r of ROUTES) {
      if (lower === "/" + r || lower === "/" + r + "/index.html") mapped = r + "/index.html";
    }
    rel = mapped || rel.replace(/^\//, "");
  }
  const file = path.resolve(root, rel);
  const rootResolved = path.resolve(root);
  if (file !== rootResolved && !file.startsWith(rootResolved + path.sep)) return false;
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) return false;
  const types = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
    ".json": "application/json",
    ".txt": "text/plain",
    ".xml": "application/xml; charset=utf-8",
    ".webp": "image/webp",
  };
  const ext = path.extname(file).toLowerCase();
  res.writeHead(200, {
    "Content-Type": types[ext] || "application/octet-stream",
    "Cache-Control": "no-store",
  });
  fs.createReadStream(file).pipe(res);
  return true;
}
async function handle(req, res) {
  const url = new URL(req.url || "/", "http://localhost");
  const p = url.pathname;
  if (p.startsWith("/api/")) return json(res, 404, { error: "Not found" });
  if (serveStatic(req, res, p, url.searchParams)) return;
  json(res, 404, { error: "Not found" });
}
module.exports = {
  serveStatic: serveStatic,
  rt52opsNormalize: typeof rt52opsNormalize === "function" ? rt52opsNormalize : null,
  rt52opsClassify: typeof rt52opsClassify === "function" ? rt52opsClassify : null,
};
`;

const WRITE_MODE_TAIL = String.raw`
function sendSpaShell(req, res) {
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" });
  res.end("SPA-SHELL");
  return true;
}
async function handle(req, res) {
  const url = new URL(req.url || "/", "http://localhost");
  const p = url.pathname;
  if (serveStatic(req, res, p, url.searchParams)) return;
  return sendSpaShell(req, res);
}
module.exports = { serveStatic: serveStatic };
`;

function runPatch(args) {
  return spawnSync("python3", [PATCH, ...args], { encoding: "utf8" });
}

function buildWorkspace(dir) {
  const files = {
    "index.html": "FILE:index.html",
    "app.js": "FILE:app.js",
    "styles.css": "FILE:styles.css",
    "logo-mark.svg": "<svg>FILE:logo-mark.svg</svg>",
    "og-card.png": Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00]),
    "og-card.svg": "<svg>FILE:og-card.svg</svg>",
    "founder.jpg": Buffer.from("FILE:founder.jpg"),
    "manifest.json": '{"name":"FILE:manifest.json"}',
    "robots.txt": "FILE:robots.txt",
    "sitemap.xml": "<urlset>FILE:sitemap.xml</urlset>",
    "llms.txt": "FILE:llms.txt",
    "photo.webp": "FILE:photo.webp",
  };
  for (const [rel, body] of Object.entries(files)) writeFile(path.join(dir, rel), body);
  for (const r of ROUTES) writeFile(path.join(dir, r, "index.html"), "FILE:" + r + "/index.html");
  const leaks = {
    "zipFile.zip": "LEAKED-zipFile",
    "pnpm-lock.yaml": "LEAKED-pnpm",
    "uv.lock": "LEAKED-uv",
    "deploy/patch_rt51.py": "LEAKED-deploy-py",
    "server.js.bak-rt48c": "LEAKED-server-bak",
    "app.js.bak-rt48b": "LEAKED-app-bak",
    "index.html.bak-rt51": "LEAKED-index-bak",
    "artifacts/secret.txt": "LEAKED-artifacts",
    ".pythonlibs/lib.py": "LEAKED-pythonlibs",
    "node_modules/leftpad/index.js": "LEAKED-node-modules",
    "README.md": "LEAKED-readme",
    "notes.yml": "LEAKED-yml",
    "script.py": "LEAKED-py",
    "file.backup": "LEAKED-backup",
    ".env": "LEAKED-env",
    ".git/config": "LEAKED-git",
    "package.json": "LEAKED-package",
    "server.js": "LEAKED-server",
    "stripeClient.js": "LEAKED-stripe",
  };
  for (const [rel, body] of Object.entries(leaks)) writeFile(path.join(dir, rel), body);
}

function request(port, reqPath) {
  return new Promise((resolve, reject) => {
    const req = http.request({ hostname: "127.0.0.1", port, path: reqPath, method: "GET" }, (res) => {
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => resolve({
        status: res.statusCode,
        headers: res.headers,
        body: Buffer.concat(chunks),
      }));
    });
    req.on("error", reject);
    req.end();
  });
}

function spaPath(pathname) {
  if (pathname === "/settings" || pathname === "/settings/") return true;
  const parts = pathname.split("/").filter(Boolean);
  if (parts.length === 2 && ROUTES.includes(parts[0]) && !parts[1].includes(".")) return true;
  return false;
}

async function main() {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "rt52ops-"));
  const ws = path.join(tmp, "ws");
  buildWorkspace(ws);
  const fixture = path.join(tmp, "fixture-server.js");
  fs.writeFileSync(fixture, FIXTURE_BODY);
  const before = sha(fixture);
  const dry = runPatch(["--dry-run", fixture]);
  check("dry-run exits 0", dry.status === 0, dry.stderr || dry.stdout.slice(0, 200));
  check("dry-run does not write the file", sha(fixture) === before);
  check("dry-run names the anchor", /function serveStatic\(req, res, pathname, searchParams\)/.test(dry.stdout));
  check("dry-run prints a diff", dry.stdout.includes("rt52ops, not written") && dry.stdout.includes("rt52opsNormalize"));
  check("dry-run deny mode is return-false", /DENY: return false/.test(dry.stdout));

  const applied = runPatch([fixture]);
  check("apply exits 0", applied.status === 0, applied.stdout + applied.stderr);
  check("apply changes the fixture", sha(fixture) !== before);
  const twice = runPatch([fixture]);
  const afterOnce = sha(fixture);
  check("second apply is a no-op", twice.status === 0 && sha(fixture) === afterOnce && /already applied/.test(twice.stdout), twice.stdout);

  process.env.RT52OPS_ROOT = ws;
  const mod = require(fixture);
  check("classify is exported", typeof mod.rt52opsClassify === "function");
  const cls = (p) => mod.rt52opsClassify(mod.rt52opsNormalize(p));
  const denySamples = [
    "/zipFile.zip", "/ZIPFILE.ZIP", "/zipFile.zip/", "//zipFile.zip", "/%7AipFile.zip",
    "/zipFile%2Ezip", "/zipFile%252Ezip", "/foo/bar.zip", "/pnpm-lock.yaml", "/PNPM-LOCK.YAML",
    "/uv.lock", "/notes.yml", "/config.yaml", "/README.md", "/script.py", "/file.backup",
    "/server.js.bak-rt48c", "/app.js.bak-rt48b", "/index.html.bak-rt51",
    "/deploy/patch_rt51.py", "/DEPLOY/patch_rt51.py", "/deploy/", "/artifacts/secret.txt",
    "/.pythonlibs/lib.py", "/node_modules/leftpad/index.js", "/.env", "/.git/config",
    "/pricing/../../uv.lock", "/%2e%2e/uv.lock", "/app.js/../../uv.lock",
    "/markets/foo.zip", "/learn/readme.md",
  ];
  for (const p of denySamples) check("classify deny " + p, cls(p) === "deny", cls(p));
  const allowSamples = [
    ["/", "allow"], ["/index.html", "allow"], ["/favicon.ico", "allow"],
    ["/app.js", "allow"], ["/styles.css", "allow"], ["/manifest.json", "allow"],
    ["/robots.txt", "allow"], ["/sitemap.xml", "allow"], ["/llms.txt", "allow"],
    ["/logo-mark.svg", "allow"], ["/founder.jpg", "allow"], ["/og-card.svg", "allow"],
    ["/photo.webp", "allow"], ["/og-card.png", "og"], ["/OG-CARD.PNG", "og"],
    ["/pricing", "allow"], ["/pricing/", "allow"], ["/pricing/index.html", "allow"],
    ["/brief/dispatch-brief", "allow"], ["/report/spx2026/", "allow"],
    ["/research/research-desk/index.html", "allow"],
    ["/settings", "skip"], ["/markets/AAPL", "skip"], ["/api/me", "skip"],
    ["/server.js", "skip"], ["/package.json", "skip"], ["/stripeClient.js", "skip"],
  ];
  for (const [p, want] of allowSamples) check("classify " + want + " " + p, cls(p) === want, cls(p));

  const server = http.createServer((req, res) => {
    let pathname = "/";
    let searchParams = new URLSearchParams();
    try {
      const u = new URL(req.url, "http://127.0.0.1");
      pathname = u.pathname;
      searchParams = u.searchParams;
    } catch (e) {
      res.writeHead(400); res.end("bad"); return;
    }
    if (pathname === "/api" || pathname.startsWith("/api/")) {
      res.writeHead(404, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" });
      res.end(JSON.stringify({ error: "Not found" }));
      return;
    }
    if (mod.serveStatic(req, res, pathname, searchParams)) return;
    if (spaPath(pathname)) {
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" });
      res.end("SPA " + pathname);
      return;
    }
    res.writeHead(404, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" });
    res.end("Page not found");
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const port = server.address().port;

  const expectType = [
    ["/", "text/html; charset=utf-8", "FILE:index.html"],
    ["/app.js", "text/javascript; charset=utf-8", "FILE:app.js"],
    ["/app.js?v=chat56", "text/javascript; charset=utf-8", "FILE:app.js"],
    ["/styles.css", "text/css; charset=utf-8", "FILE:styles.css"],
    ["/styles.css?v=chat1", "text/css; charset=utf-8", "FILE:styles.css"],
    ["/logo-mark.svg", "image/svg+xml", "FILE:logo-mark.svg"],
    ["/logo-mark.svg?v=fd7364ffa1e17f1c", "image/svg+xml", "FILE:logo-mark.svg"],
    ["/founder.jpg", "application/octet-stream", "FILE:founder.jpg"],
    ["/manifest.json", "application/json", "FILE:manifest.json"],
    ["/robots.txt", "text/plain", "FILE:robots.txt"],
    ["/sitemap.xml", "application/xml; charset=utf-8", "FILE:sitemap.xml"],
    ["/llms.txt", "text/plain", "FILE:llms.txt"],
    ["/og-card.svg", "image/svg+xml", "FILE:og-card.svg"],
    ["/photo.webp", "image/webp", "FILE:photo.webp"],
  ];
  for (const r of ROUTES) {
    expectType.push(["/" + r + "/", "text/html; charset=utf-8", "FILE:" + r + "/index.html"]);
    expectType.push(["/" + r + "/index.html", "text/html; charset=utf-8", "FILE:" + r + "/index.html"]);
  }
  check("manifest URL count is 32 plus route index aliases", expectType.length === 10 + 4 + ROUTES.length * 2, String(expectType.length));
  const manifestUrls = new Set(["/", "/app.js", "/styles.css", "/logo-mark.svg", "/founder.jpg", "/manifest.json", "/robots.txt", "/sitemap.xml", "/llms.txt", "/og-card.png", ...ROUTES.map((r) => "/" + r + "/")]);
  check("32 public manifest URLs", manifestUrls.size === 32, String(manifestUrls.size));

  for (const [url, type, body] of expectType) {
    const res = await request(port, url);
    check("200 " + url, res.status === 200 && res.headers["content-type"] === type && res.body.toString().includes(body), res.status + " " + res.headers["content-type"]);
  }
  const og = await request(port, "/og-card.png");
  check("og-card.png image/png cached", og.status === 200 && og.headers["content-type"] === "image/png" && og.headers["cache-control"] === "public, max-age=86400" && og.body[0] === 0x89, og.status + " " + og.headers["content-type"] + " " + og.headers["cache-control"]);
  const idx = await request(port, "/index.html");
  check("index.html 308 to /", idx.status === 308 && idx.headers.location === "/", String(idx.status) + " " + idx.headers.location);
  const ico = await request(port, "/favicon.ico");
  check("favicon.ico 301 to logo", ico.status === 301 && ico.headers.location === "/logo-mark.svg", String(ico.status) + " " + ico.headers.location);

  const leakedUrls = [
    "/zipFile.zip", "/ZIPFILE.ZIP", "/zipFile.zip/", "/pnpm-lock.yaml", "/PNPM-LOCK.YAML",
    "/uv.lock", "/deploy/patch_rt51.py", "/server.js.bak-rt48c", "/app.js.bak-rt48b",
    "/index.html.bak-rt51", "/artifacts/secret.txt", "/.pythonlibs/lib.py",
    "/node_modules/leftpad/index.js", "/README.md", "/notes.yml", "/script.py",
    "/file.backup", "/.env", "/.git/config", "/package.json", "/server.js", "/stripeClient.js",
    "/markets/foo.zip", "/learn/readme.md", "/foo/bar.png",
  ];
  for (const url of leakedUrls) {
    const res = await request(port, url);
    const text = res.body.toString();
    check("404 " + url, res.status === 404 && !text.includes("LEAKED") && res.headers["content-type"].includes("text/html"), res.status + " " + text.slice(0, 40));
  }
  const api = await request(port, "/api/me");
  check("/api/me stays the caller's JSON 404", api.status === 404 && api.headers["content-type"].includes("application/json") && api.body.toString().includes('"error":"Not found"'), api.body.toString());
  const spa = await request(port, "/markets/AAPL");
  check("SPA /markets/AAPL still 200", spa.status === 200 && spa.body.toString().includes("SPA /markets/AAPL"), spa.status + " " + spa.body.toString());
  const settings = await request(port, "/settings");
  check("SPA /settings still 200", settings.status === 200 && settings.body.toString().includes("SPA /settings"));
  const missingPng = await request(port, "/does-not-exist.png");
  check("missing root image is a normal 404", missingPng.status === 404 && !missingPng.body.toString().includes("LEAKED"));

  server.close();

  const repoCopy = path.join(tmp, "repo-server.js");
  fs.copyFileSync(path.join(ROOT, "server.js"), repoCopy);
  const repoBefore = sha(repoCopy);
  const repoRun = runPatch([repoCopy]);
  check("repo 3-arg serveStatic aborts", repoRun.status !== 0 && /ABORT:/.test(repoRun.stdout + repoRun.stderr) && sha(repoCopy) === repoBefore, (repoRun.stdout + repoRun.stderr).split("\n")[0]);

  const ambiguous = path.join(tmp, "ambiguous.js");
  fs.writeFileSync(ambiguous, FIXTURE_BODY + "\n" + FIXTURE_BODY);
  const ambBefore = sha(ambiguous);
  const amb = runPatch(["--check", ambiguous]);
  check("two anchors abort", amb.status !== 0 && /matched 2 times/.test(amb.stdout + amb.stderr) && sha(ambiguous) === ambBefore, (amb.stdout + amb.stderr).split("\n")[0]);

  const spaFile = path.join(tmp, "spa-fixture.js");
  const spaSrc = FIXTURE_BODY.replace(/async function handle[\s\S]*module\.exports = \{[\s\S]*?\};/, WRITE_MODE_TAIL);
  fs.writeFileSync(spaFile, spaSrc);
  const spaPatch = runPatch([spaFile]);
  check("SPA-fallback caller selects write-404", spaPatch.status === 0 && /write-404/.test(spaPatch.stdout), spaPatch.stdout.split("\n").find((l) => l.startsWith("DENY:")));
  process.env.RT52OPS_ROOT = ws;
  delete require.cache[require.resolve(spaFile)];
  const spaMod = require(spaFile);
  const leakRes = await new Promise((resolve) => {
    const s = http.createServer((req, res) => {
      const u = new URL(req.url, "http://127.0.0.1");
      if (spaMod.serveStatic(req, res, u.pathname, u.searchParams)) return;
      res.writeHead(200, { "Content-Type": "text/html" });
      res.end("SPA-SHELL");
    });
    s.listen(0, "127.0.0.1", async () => {
      const r = await request(s.address().port, "/zipFile.zip");
      s.close();
      resolve(r);
    });
  });
  check("write-404 mode does not serve the zip via the SPA shell", leakRes.status === 404 && leakRes.body.toString().includes("That market page is not here") && !leakRes.body.toString().includes("LEAKED") && !leakRes.body.toString().includes("SPA-SHELL"), leakRes.status + " " + leakRes.headers["content-type"]);

  const indexCopy = path.join(tmp, "index.html");
  fs.copyFileSync(path.join(ROOT, "index.html"), indexCopy);
  const sri1 = spawnSync("python3", [SRI, indexCopy], { encoding: "utf8" });
  check("sri apply exits 0", sri1.status === 0, sri1.stdout + sri1.stderr);
  const html = fs.readFileSync(indexCopy, "utf8");
  const tag = html.match(/<script\b[^>]*lightweight-charts@4\.2\.0\/dist\/lightweight-charts\.standalone\.production\.js[^>]*>/i);
  check("sri tag present", !!tag, tag && tag[0]);
  const integrity = tag && (tag[0].match(/integrity="(sha384-[^"]+)"/) || [])[1];
  const cross = tag && /crossorigin="anonymous"/.test(tag[0]);
  check("sri integrity and crossorigin", !!integrity && cross, integrity);
  const sri2 = spawnSync("python3", [SRI, "--check", indexCopy], { encoding: "utf8" });
  check("sri second run is a no-op", sri2.status === 0 && /already applied/.test(sri2.stdout) && fs.readFileSync(indexCopy, "utf8") === html, sri2.stdout);

  const deferCopy = path.join(tmp, "index-defer.html");
  fs.writeFileSync(deferCopy, '<script defer src="https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>\n');
  const sri3 = spawnSync("python3", [SRI, deferCopy], { encoding: "utf8" });
  const deferHtml = fs.readFileSync(deferCopy, "utf8");
  check("sri keeps defer and pins the same hash", sri3.status === 0 && deferHtml.includes("defer") && deferHtml.includes('integrity="' + integrity + '"'), sri3.stdout + deferHtml);

  console.log(fails.length ? "FAILED " + fails.length : "ALL PASSED");
  if (integrity) console.log("SRI " + integrity);
  process.exit(fails.length ? 1 : 0);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
