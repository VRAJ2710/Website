// Preloaded via `node --require` before the application starts. Points the
// Neon serverless HTTP driver at the local proxy (neon-http-proxy.js) instead
// of Neon's cloud `/sql` endpoint, so the unmodified app runs against a local
// PostgreSQL cluster. No-op unless NEON_LOCAL_PROXY_URL is set.
const url = process.env.NEON_LOCAL_PROXY_URL;
if (url) {
  try {
    const { neonConfig } = require("@neondatabase/serverless");
    neonConfig.fetchEndpoint = url;
    console.log(`[neon-shim] Routing Neon HTTP queries to ${url}`);
  } catch (error) {
    console.error("[neon-shim] Failed to configure Neon fetch endpoint:", error.message);
  }
}
