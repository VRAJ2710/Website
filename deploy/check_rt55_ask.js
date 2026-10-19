#!/usr/bin/env node
"use strict";
/* bb5g sends one newline after the lead. fe64_joinChunk and fe64_flattenName
   must not add, drop, or rewrite newlines or spaces. The entity span copies
   the matched characters. A legacy stream (a newline before each chunk) must
   stay equal to chat63 concatenation, which is stricter than the old joiner
   that turned "has\\n"+"a" into "hasa" and "N\\n"+"VIDIA" into "N VIDIA". */
const fs = require("fs");
const appPath = process.argv[2] || "/tmp/rt55/out/app.js";
const src = fs.readFileSync(appPath, "utf8");

function grab(name) {
  const at = src.indexOf("function " + name);
  if (at < 0) throw new Error("missing " + name);
  if (name === "_chatMd") {
    const end = src.indexOf("\nfunction _chatVerdictCol", at);
    if (end < 0) throw new Error("missing chat markdown end");
    return src.slice(at, end);
  }
  let i = src.indexOf("{", at), n = 0, q = "";
  for (; i < src.length; i++) {
    const c = src[i];
    if (q) {
      if (c === "\\") { i++; continue; }
      if (c === q) q = "";
      continue;
    }
    if (c === "'" || c === '"' || c === "`") { q = c; continue; }
    if (c === "{") n++;
    else if (c === "}" && --n === 0) return src.slice(at, i + 1);
  }
  throw new Error("unclosed " + name);
}

const vm = require("vm");
const ctx = {};
vm.createContext(ctx);
vm.runInContext(grab("_chatMd") + "\n" + grab("fe64_joinChunk") + "\n" + grab("fe64_flattenName") + "\n" + grab("fe64_entHtml") + "\nthis._chatMd=_chatMd;this.fe64_joinChunk=fe64_joinChunk;this.fe64_flattenName=fe64_flattenName;this.fe64_entHtml=fe64_entHtml;", ctx);

function join(chunks) {
  return chunks.reduce((acc, chunk) => ctx.fe64_joinChunk(acc, chunk), "");
}
function render(text) {
  return ctx.fe64_entHtml(ctx._chatMd(ctx.fe64_flattenName(text)));
}
function textOf(html) {
  return String(html).replace(/<[^>]+>/g, "").replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">");
}
function oldJoin(acc, chunk) {
  chunk = String(chunk == null ? "" : chunk);
  acc = String(acc == null ? "" : acc);
  if (!chunk) return acc;
  if (!acc) return chunk;
  var a = acc.replace(/[\n\r]+$/g, "");
  var c = chunk.replace(/^[\n\r]+/g, "");
  var broke = a.length !== acc.length || c.length !== chunk.length;
  var end = a.slice(-1), start = c.charAt(0);
  if (!broke) return acc + chunk;
  if (end === "(" && /[A-Za-z0-9]/.test(start)) return a + c;
  if (/[A-Za-z0-9]$/.test(end) && /^[a-z0-9)]/.test(start)) return a + c;
  if (/[A-Za-z0-9)]$/.test(end) && /^[A-Z(]/.test(start)) return a + " " + c;
  return a + c;
}

let failed = 0;
function ok(cond, msg) {
  if (cond) console.log("ok", msg);
  else { failed++; console.error("FAIL", msg); }
}

const canonical = [
  "Micron has a memory cycle.",
  "\n",
  "**NV",
  "IDIA (NV",
  "DA)** does not have a similar setup to **AV",
  "GO** or **W",
  "DC**.",
  "\n- Mic",
  "ron (MU) leads the group",
  "\n- Intel (INT",
  "C) lags"
].join("");
const bb5g = [
  "Micron has a memory cycle.",
  "\n",
  "**NV",
  "IDIA (NV",
  "DA)** does not have a similar setup to **AV",
  "GO** or **W",
  "DC**.",
  "\n- Mic",
  "ron (MU) leads the group",
  "\n- Intel (INT",
  "C) lags"
];
const got = join(bb5g);
ok(got === canonical, "bb5g join equals the canonical text");
ok(got === bb5g.join(""), "bb5g join equals concatenation");
ok(ctx.fe64_flattenName(got) === got, "flatten does not rewrite the answer");
const html = render(got);
const plain = textOf(html);
ok(html.indexOf("<strong>") >= 0, "markdown strong");
ok(html.indexOf("chat-li") >= 0, "markdown list");
ok(html.indexOf("**") < 0, "no raw asterisks");
["has a", "NVIDIA", "NVDA", "AVGO", "WDC", "INTC", "Micron", "does not have a"].forEach(w => ok(plain.indexOf(w) >= 0, "word intact: " + w));
["hasa", "N VIDIA", "NV DA", "AV GO", "W DC", "INT C", "doesnothavea"].forEach(w => ok(plain.indexOf(w) < 0, "not smashed: " + w));
const ent = html.match(/<span class="fe64-ent">([^<]*)<\/span>/g) || [];
ok(ent.length >= 2, "entity spans");
ent.forEach(span => {
  const inner = span.replace(/<[^>]+>/g, "");
  ok(canonical.indexOf(inner) >= 0, "entity text unchanged: " + inner);
});
ok(ctx.fe64_joinChunk("has\n", "a") === "has\na", "legacy has+a keeps the newline");
ok(ctx.fe64_joinChunk("N\n", "VIDIA") === "N\nVIDIA", "legacy N+VIDIA keeps the newline");
ok(oldJoin("has\n", "a") === "hasa" && ctx.fe64_joinChunk("has\n", "a") !== "hasa", "not the old hasa join");
ok(oldJoin("N\n", "VIDIA") === "N VIDIA" && ctx.fe64_joinChunk("N\n", "VIDIA") !== "N VIDIA", "not the old N VIDIA join");

const pieces = ["Micron has a memory cycle.", "**NVIDIA (NVDA)** does not have a similar setup.", "- Micron (MU) leads"];
const legacy = pieces.map(p => "\n" + p);
ok(join(legacy) === legacy.join(""), "legacy newline-before-chunk equals chat63 concatenation");
const legacyHtml = render(join(legacy));
const chat63Html = render(legacy.join(""));
ok(legacyHtml === chat63Html, "legacy render matches chat63");
ok(textOf(legacyHtml).indexOf("hasa") < 0 && textOf(legacyHtml).indexOf("N VIDIA") < 0, "legacy render is not the smashed join");

if (failed) { console.error(failed + " failed"); process.exit(1); }
console.log("ask fixture passed");
