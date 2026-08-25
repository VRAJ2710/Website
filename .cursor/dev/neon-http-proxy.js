#!/usr/bin/env node
// Local development shim: implements the Neon serverless driver's HTTP `/sql`
// protocol on top of a plain local PostgreSQL instance using node-postgres.
//
// The application talks to Postgres exclusively through `@neondatabase/serverless`'s
// HTTP `neon()` client, which expects a Neon-hosted `/sql` endpoint. Neon databases
// are not available offline, so this proxy lets the unmodified app run against a
// local PostgreSQL cluster in Cloud Agent / local dev environments.
//
// Protocol (reverse-engineered from @neondatabase/serverless):
//   POST <endpoint>
//   headers: Neon-Connection-String, Neon-Raw-Text-Output: true, Neon-Array-Mode: true
//   body (single):  { query, params }
//   body (batch):   { queries: [ { query, params }, ... ] }
//   response (single): { command, rowCount, rows: [[...raw text...]], fields: [{ name, dataTypeID }] }
//   response (batch):  { results: [ <single>, ... ] }
//   error: HTTP 400 with JSON { message, code, detail, hint, ... pg error fields }

const http = require("http");
const { Client } = require("pg");

const PORT = Number(process.env.NEON_LOCAL_PROXY_PORT || 5433);
const HOST = process.env.NEON_LOCAL_PROXY_HOST || "127.0.0.1";

// Return every column value as its raw text representation. The Neon driver sends
// `Neon-Raw-Text-Output: true` and parses values client-side using the field OIDs,
// so the proxy must not let node-postgres pre-parse them.
const RAW_TEXT_TYPES = { getTypeParser: () => (value) => value };

// pg error fields the Neon driver copies onto NeonDbError (mirrors the driver's list).
const PG_ERROR_FIELDS = [
  "severity", "code", "detail", "hint", "position", "internalPosition",
  "internalQuery", "where", "schema", "table", "column", "dataType",
  "constraint", "file", "line", "routine",
];

function serializeResult(result) {
  return {
    command: result.command,
    rowCount: result.rowCount,
    rows: result.rows,
    fields: (result.fields || []).map((f) => ({
      name: f.name,
      dataTypeID: f.dataTypeID,
      tableID: f.tableID,
      columnID: f.columnID,
      dataTypeSize: f.dataTypeSize,
      dataTypeModifier: f.dataTypeModifier,
      format: f.format,
    })),
  };
}

// Neon's HTTP `/sql` endpoint is stateless: every request is a fresh, short-lived
// connection. We mirror that with an ephemeral client per request and always close
// it, so the proxy never holds an idle session that would block e.g. `DROP DATABASE`.
async function withClient(connectionString, fn) {
  const client = new Client({ connectionString });
  await client.connect();
  try {
    return await fn(client);
  } finally {
    await client.end().catch(() => {});
  }
}

async function runSingle(connectionString, { query, params }) {
  return withClient(connectionString, async (client) => {
    const result = await client.query({ text: query, values: params || [], rowMode: "array", types: RAW_TEXT_TYPES });
    return serializeResult(result);
  });
}

async function runBatch(connectionString, queries, headers) {
  const isolation = headers["neon-batch-isolation-level"];
  const readOnly = headers["neon-batch-read-only"] === "true";
  const deferrable = headers["neon-batch-deferrable"] === "true";
  return withClient(connectionString, async (client) => {
    let begin = "BEGIN";
    if (isolation) begin += ` ISOLATION LEVEL ${isolation}`;
    if (readOnly) begin += " READ ONLY";
    if (deferrable) begin += " DEFERRABLE";
    await client.query(begin);
    try {
      const results = [];
      for (const q of queries) {
        const result = await client.query({ text: q.query, values: q.params || [], rowMode: "array", types: RAW_TEXT_TYPES });
        results.push(serializeResult(result));
      }
      await client.query("COMMIT");
      return { results };
    } catch (error) {
      try { await client.query("ROLLBACK"); } catch {}
      throw error;
    }
  });
}

function sendError(res, error) {
  const body = { message: error.message };
  for (const field of PG_ERROR_FIELDS) {
    if (error[field] !== undefined) body[field] = error[field];
  }
  res.writeHead(400, { "Content-Type": "application/json" });
  res.end(JSON.stringify(body));
}

const server = http.createServer((req, res) => {
  if (req.method === "GET" && req.url === "/health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ ok: true }));
    return;
  }
  if (req.method !== "POST") {
    res.writeHead(405, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ message: "Method not allowed" }));
    return;
  }

  const connectionString = req.headers["neon-connection-string"] || process.env.DATABASE_URL;
  if (!connectionString) {
    res.writeHead(400, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ message: "Missing Neon-Connection-String header" }));
    return;
  }

  let raw = "";
  req.on("data", (chunk) => { raw += chunk; });
  req.on("end", async () => {
    let payload;
    try {
      payload = JSON.parse(raw || "{}");
    } catch {
      res.writeHead(400, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ message: "Invalid JSON body" }));
      return;
    }
    try {
      const body = Array.isArray(payload.queries)
        ? await runBatch(connectionString, payload.queries, req.headers)
        : await runSingle(connectionString, payload);
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify(body));
    } catch (error) {
      sendError(res, error);
    }
  });
});

server.listen(PORT, HOST, () => {
  console.log(`[neon-proxy] Neon HTTP -> local PostgreSQL proxy listening on http://${HOST}:${PORT}`);
});
