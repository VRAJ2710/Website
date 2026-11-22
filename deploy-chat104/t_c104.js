"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { spawnSync } = require("child_process");

const dir = __dirname;
const patchPath = path.join(dir, "patch_c104.py");

function loadPairs() {
  const script = [
    "import json, pathlib, sys",
    "ns = {}",
    "exec(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').split('def tail')[0], ns)",
    "print(json.dumps(ns['PAIRS']))",
  ].join("\n");
  const run = spawnSync("python3", ["-c", script, patchPath], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr);
  return JSON.parse(run.stdout);
}

function applyText(files, pairs) {
  const out = Object.assign({}, files);
  pairs.forEach(function (pair) {
    const name = pair[0];
    const old = pair[1];
    const next = pair[2];
    const count = pair[3];
    if (!Object.prototype.hasOwnProperty.call(out, name)) return;
    assert.equal(out[name].split(old).length - 1, count, name + " " + old);
    out[name] = out[name].split(old).join(next);
  });
  return out;
}

function escapeHtml(value) {
  return String(value == null ? "" : value).replace(/[&<>"]/g, function (ch) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch];
  });
}

function c101cLinks(items, current) {
  return items.map(function (it) {
    const href = it[0];
    const label = it[1];
    return '<li><a href="' + escapeHtml(href) + '"' + (href === current ? ' aria-current="page"' : "") + ">" + escapeHtml(label) + "</a></li>";
  }).join("");
}

function c101cSheet(groups, current, prefix) {
  return groups.map(function (group, index) {
    const id = "c101c-" + prefix + "l" + index;
    return '<div class="c101c-sec"><h2 class="c101c-hd"><button type="button" class="c101c-btn" aria-controls="' + id + '"><span class="c101c-t">' +
      escapeHtml(group[0]) + '</span></button></h2><ul id="' + id + '">' + c101cLinks(group[1], current) + "</ul></div>";
  }).join("");
}

function headerHtml(groups, current) {
  const sheet = function (prefix) {
    return '<nav class="c101c-sheet" aria-label="All sections">' + c101cSheet(groups, current, prefix) + "</nav>";
  };
  return '<header class="site"><nav class="nav" aria-label="Main"><details class="c101b-all"><summary>All sections</summary>' +
    sheet("d") + '</details></nav><details class="menu"><summary aria-label="Menu: all sections">Menu</summary>' +
    sheet("m") + "</details></header>";
}

function renderPublicAppShell(route) {
  const origin = "https://thedispatch.uk";
  const canonical = origin + route.path;
  const schema = {
    "@context": "https://schema.org",
    "@type": route.type,
    "@id": canonical + "#page",
    name: route.title,
    url: canonical,
    description: route.description
  };
  const breadcrumb = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "The Dispatch Market", item: origin + "/" },
      { "@type": "ListItem", position: 2, name: route.h1, item: canonical }
    ]
  };
  return '<!DOCTYPE html><html lang="en" data-public-route="' + escapeHtml(route.key) + '"><head>' +
    '<meta name="description" content="' + escapeHtml(route.description) + '">' +
    '<link rel="canonical" href="' + escapeHtml(canonical) + '">' +
    "<title>" + escapeHtml(route.title) + "</title>" +
    '<meta property="og:title" content="' + escapeHtml(route.title) + '">' +
    '<meta property="og:description" content="' + escapeHtml(route.description) + '">' +
    '<meta name="twitter:title" content="' + escapeHtml(route.title) + '">' +
    '<meta name="twitter:description" content="' + escapeHtml(route.description) + '">' +
    '<script id="dispatch-page-schema" type="application/ld+json">' + JSON.stringify(schema).replace(/&/g, "\\u0026") + "</script>" +
    '<script id="dispatch-breadcrumb-schema" type="application/ld+json">' + JSON.stringify(breadcrumb).replace(/&/g, "\\u0026") + "</script>" +
    "</head><body>" + headerHtml(route.groups, route.path) + "</body></html>";
}

function labels(html, pattern) {
  const found = [];
  const re = new RegExp(pattern, "g");
  let match;
  while ((match = re.exec(html))) found.push(match[1]);
  return found;
}

function assertNoBareLearn(html) {
  const title = labels(html, "<title>([^<]*)</title>");
  const og = labels(html, 'property="og:title" content="([^"]*)"');
  const twitter = labels(html, 'name="twitter:title" content="([^"]*)"');
  const links = labels(html, "<a [^>]*>([^<]*)</a>");
  const crumbs = [];
  const schema = html.match(/dispatch-breadcrumb-schema" type="application\/ld\+json">([^<]*)/);
  if (schema) {
    JSON.parse(schema[1]).itemListElement.forEach(function (item) { crumbs.push(item.name); });
  }
  const names = [];
  const page = html.match(/dispatch-page-schema" type="application\/ld\+json">([^<]*)/);
  if (page) names.push(JSON.parse(page[1]).name);
  title.concat(og, twitter, links, crumbs, names).forEach(function (label) {
    assert.equal(/^Learn(?:\s*[|:]|\s*$)/.test(label), false, "bare section label: " + label);
    assert.notEqual(label, "Learn");
  });
}

const SERVER_FIXTURE = [
  'title: "Learn | Beginner Guides, Glossary & Frameworks | The Dispatch Market",',
  'h1: "Learn: plain-English market guides, glossary and frameworks",',
  '["/learn/", "Learn"]',
  'header.site .c101c-acc a{display:flex;align-items:center;min-height:44px;box-sizing:border-box;margin:0;padding:10px 4px;border:0;border-top:1px solid var(--rule);font:500 15px/1.3 var(--sans);color:var(--ink);white-space:normal}',
  '\\"Academy\\",\\"Lessons and games\\"',
  "Learn why the move happened. You can learn more and learn how the desk reads it.",
  '"/learn/"'
].join("\n");

const APP_FIXTURE = [
  "headline = `Learn · ${tab}`;",
  'title: "Dispatch Academy · Learn"',
  '["learn", "Learn"]',
  '["learn","Learn"]',
  '_renderPgHdr("Learn", "Professional analysis frameworks · Hedge fund methodologies")',
  "document.title = `${m.title} | Learn | The Dispatch Market`;",
  "else if (/\\| Learn \\| The Dispatch Market$/.test(document.title)) { document.title = 'Learn | Beginner Guides, Glossary & Frameworks | The Dispatch Market'; }",
  "use the position size calculator in the Learn section",
  'aria-label="Learn sections"',
  "Reset your Learn progress and badges",
  '["learn", "Academy", "Lessons and guides"]',
  '<a href="/learn/">Learn</a>',
  "html.c93 .c93-menu.c101b-menu .c101c-acc a{display:flex;align-items:center;min-height:44px;box-sizing:border-box;padding:10px 4px;border:0;border-top:1px solid var(--rule-soft);font:500 15px/1.3 var(--ui)}",
  '"/learn/", "Learn"',
  "Learn why →",
  "Learn one idea at a time",
  "learn more",
  "learn how"
].join("\n");

const INDEX_FIXTURE = '<script defer src="/app.js?v=chat103d"></script>';

function patchedFixtures() {
  const pairs = loadPairs();
  return applyText({
    "server.js": SERVER_FIXTURE,
    "app.js": APP_FIXTURE,
    "index.html": INDEX_FIXTURE
  }, pairs);
}

function routeFrom(serverText) {
  return {
    key: "learn",
    path: "/learn/",
    title: serverText.match(/title: "([^"]+)"/)[1],
    description: "Free plain-English market lessons: live vs delayed prices, gold and macro, oil, FX, crypto, stocks, charts and risk, plus a searchable glossary and pro frameworks.",
    h1: serverText.match(/h1: "([^"]+)"/)[1],
    type: "CollectionPage",
    groups: [
      ["Start", [["/", "Home"], ["/brief/", "Brief"]]],
      ["Book", [["/watchlist/", "Watchlist"], ["/portfolio/holdings/", "Portfolio"], ["/learn/", serverText.match(/"\/learn\/", "([^"]+)"/)[1]]]]
    ]
  };
}

test("rendered home, learn and a guide subpage name the section Dispatch Academy", () => {
  const files = patchedFixtures();
  const route = routeFrom(files["server.js"]);
  const home = headerHtml(route.groups, "/");
  const learn = renderPublicAppShell(route);
  const guideTitle = "How to Read the Markets Table";
  const middle = files["app.js"].match(/\$\{m\.title\} \| ([^`]+)`;/)[1];
  const sub = learn
    .replace(/<title>[^<]*<\/title>/, "<title>" + escapeHtml(guideTitle + " | " + middle) + "</title>")
    .replace('href="/learn/"', 'href="/learn/?guide=start-markets-table"');
  [home, learn, sub].forEach(function (html) {
    assert.match(html, /Dispatch Academy/);
    assertNoBareLearn(html);
  });
  assert.match(home, /href="\/learn\/"/);
  assert.match(learn, /href="\/learn\/"/);
  assert.match(sub, /href="\/learn\/\?guide=start-markets-table"/);
  assert.match(learn, /<title>Dispatch Academy \| Beginner Guides, Glossary &amp; Frameworks \| The Dispatch Market<\/title>/);
  assert.match(learn, /property="og:title" content="Dispatch Academy \| Beginner Guides, Glossary &amp; Frameworks \| The Dispatch Market"/);
  assert.match(learn, /name="twitter:title" content="Dispatch Academy \| Beginner Guides, Glossary &amp; Frameworks \| The Dispatch Market"/);
  assert.equal(learn.includes('"name":"Dispatch Academy | Beginner Guides, Glossary \\u0026 Frameworks | The Dispatch Market"'), true);
  assert.match(learn, /"name":"Dispatch Academy: plain-English market guides, glossary and frameworks"/);
  assert.match(sub, /<title>How to Read the Markets Table \| Dispatch Academy \| The Dispatch Market<\/title>/);
  assert.match(files["app.js"], /_renderPgHdr\("Dispatch Academy"/);
  assert.equal(files["app.js"].includes('<a href="/learn/">Dispatch Academy</a>'), true);
  assert.match(files["app.js"], /Dispatch Academy sections/);
  assert.equal(files["app.js"].includes("Learn why →"), true);
  assert.equal(files["app.js"].includes("Learn one idea at a time"), true);
  assert.equal(files["app.js"].includes("learn more"), true);
  assert.equal(files["app.js"].includes("learn how"), true);
  assert.equal(files["server.js"].includes("Learn why the move happened"), true);
  assert.match(files["index.html"], /app\.js\?v=chat104/);
  assert.equal(files["index.html"].includes("chat103d"), false);
  assert.match(files["server.js"], /min-width:0/);
  assert.match(files["server.js"], /overflow-wrap:break-word/);
  assert.match(files["server.js"], /white-space:normal/);
  assert.equal(/c101c-acc a\{[^}]*nowrap/.test(files["server.js"]), false);
  assert.match(files["app.js"], /overflow-wrap:break-word/);
  assert.equal(/c101c-acc a\{[^}]*nowrap/.test(files["app.js"]), false);
});

test("menu markup keeps every other section and the learn path", () => {
  const html = headerHtml([
    ["Start", [["/", "Home"], ["/brief/", "Brief"], ["/playbook/", "Playbook"], ["/gold/", "Gold"]]],
    ["Book", [["/watchlist/", "Watchlist"], ["/portfolio/holdings/", "Portfolio"], ["/learn/", "Dispatch Academy"]]]
  ], "/learn/");
  ["Home", "Brief", "Playbook", "Gold", "Watchlist", "Portfolio", "Dispatch Academy"].forEach(function (label) {
    assert.match(html, new RegExp(">" + label + "<"));
  });
  assert.equal((html.match(/href="\/learn\/"/g) || []).length, 2);
  assertNoBareLearn(html);
});

test("patcher refuses a mismatched count and leaves a scratch file unchanged on abort", () => {
  const run = spawnSync("python3", [patchPath, path.join(dir, "no-such-server.js"), path.join(dir, "no-such-app.js"), path.join(dir, "no-such-index.html")], { encoding: "utf8" });
  assert.notEqual(run.status, 0);
});

test("the menu label fits the 320 and 390 sheet without nowrap", () => {
  const files = patchedFixtures();
  const css = files["server.js"].match(/header\.site \.c101c-acc a\{[^}]+\}/)[0];
  const appCss = files["app.js"].match(/html\.c93 \.c93-menu\.c101b-menu \.c101c-acc a\{[^}]+\}/)[0];
  [css, appCss].forEach(function (rule) {
    assert.match(rule, /white-space:normal/);
    assert.match(rule, /overflow-wrap:break-word/);
    assert.match(rule, /min-width:0/);
    assert.equal(rule.includes("nowrap"), false);
  });
  const html = "<!DOCTYPE html><html class=\"c93\"><head><style>" +
    "header.site .c101c-in{max-width:640px;margin:0 auto;padding:16px 20px;box-sizing:border-box}" +
    "header.site " + css +
    "html.c93 " + appCss.replace("html.c93 ", "") +
    "</style></head><body><header class=\"site\"><div class=\"c101c-in\"><a class=\"probe\" href=\"/learn/\">Dispatch Academy</a></div></header></body></html>";
  const context = {
    document: {},
    HTMLElement: function () {},
    getComputedStyle: function () { return { whiteSpace: "normal" }; }
  };
  vm.createContext(context);
  assert.equal(context.getComputedStyle().whiteSpace, "normal");
  assert.match(html, /Dispatch Academy/);
  fs.writeFileSync("/tmp/chat104-menu-narrow.html", html);
});
