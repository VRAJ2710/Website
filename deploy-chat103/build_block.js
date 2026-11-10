"use strict";
// Rebuilds server_block_c103.js from lib_c103.js and client_c103.js.
const fs = require("fs");
const path = require("path");
const dir = __dirname;
const lib = fs.readFileSync(path.join(dir, "lib_c103.js"), "utf8");
const client = fs.readFileSync(path.join(dir, "client_c103.js"), "utf8");
if (client.indexOf("</" + "script") >= 0) throw new Error("client contains a script close tag");
if (client.indexOf("GC=F") >= 0) throw new Error("client shows a raw ticker");
const out = "// chat103 cpi day. Built from lib_c103.js and client_c103.js. Edit those, then run node build_block.js.\n" +
  "(function () {\n" +
  "  var module = { exports: {} };\n" +
  lib + "\n" +
  "  var c103api = module.exports;\n" +
  "  c103api.c103Install.clientJs = " + JSON.stringify(client) + ";\n" +
  "  if (typeof globalThis !== \"undefined\") globalThis.c103 = c103api;\n" +
  "  if (!globalThis.C103_NO_INSTALL) c103api.c103Install();\n" +
  "})();\n";
fs.writeFileSync(path.join(dir, "server_block_c103.js"), out);
const sql = "-- chat103 new tables only. Each statement creates one of the five cpi_ tables if it is missing.\n" +
  require("./lib_c103.js").C103_DDL.join(";\n\n") + ";\n";
fs.writeFileSync(path.join(dir, "ddl_c103.sql"), sql);
console.log("server_block_c103.js", out.length);
