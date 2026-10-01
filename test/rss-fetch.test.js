"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { fetchRssDocument, assertPublicHttps } = require("../rssFetch");
const { RSS_FEED_URLS } = require("../rssFeeds");

function xmlResponse(status, body, headers = {}) {
  return {
    status,
    ok: status >= 200 && status < 300,
    headers: { get: name => headers[name.toLowerCase()] || null },
    text: async () => body,
  };
}

test("RSS fetch follows a public HTTPS redirect and rejects an empty body", async () => {
  const calls = [];
  const body = await fetchRssDocument("https://feeds.example.test/topstories", {
    fetch: async url => {
      calls.push(url);
      if (url.endsWith("/topstories")) return xmlResponse(301, "", { location: "https://feeds.example.test/mw_topstories" });
      return xmlResponse(200, "<rss><channel><item><title>Desk</title></item></channel></rss>");
    },
  });
  assert.match(body, /<rss>/);
  assert.deepEqual(calls, [
    "https://feeds.example.test/topstories",
    "https://feeds.example.test/mw_topstories",
  ]);
  await assert.rejects(
    () => fetchRssDocument("https://feeds.example.test/empty", {
      fetch: async () => xmlResponse(200, ""),
    }),
    /empty body/,
  );
  assert.throws(() => assertPublicHttps("http://feeds.example.test/rss"), /HTTPS/);
  assert.throws(() => assertPublicHttps("https://127.0.0.1/rss"), /public host/);
});

test("allowlisted f4, f7, and f12 return XML after redirects", async () => {
  for (const id of ["f4", "f7", "f12"]) {
    const body = await fetchRssDocument(RSS_FEED_URLS[id]);
    assert.ok(body.includes("<"), `${id} body was empty`);
    assert.match(body, /<(rss|feed)\b/i, `${id} was not a feed document`);
  }
});
