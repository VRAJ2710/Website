// TEST ONLY: stands in for @replit/connectors-sdk. Records every proxy() call; behaviour from $MOCK_RESEND_MODE_FILE:
// ok | fail (HTTP 422) | throw (transport error) | hang (never answers). No network.
const fs = require("fs");
class ReplitConnectors {
  async proxy(name, path, opts) {
    let mode = "ok"; try { mode = fs.readFileSync(process.env.MOCK_RESEND_MODE_FILE, "utf8").trim() || "ok"; } catch (e) {}
    fs.appendFileSync(process.env.MOCK_RESEND_LOG, JSON.stringify({ t: Date.now(), name, path, opts, mode }) + "\n");
    if (mode === "fail") return { ok: false, status: 422, json: async () => ({}) };
    if (mode === "throw") throw new Error("mock transport error");
    if (mode === "hang") return new Promise(() => {});
    return { ok: true, status: 200, json: async () => ({ id: "mock-id" }) };
  }
}
module.exports = { ReplitConnectors };
