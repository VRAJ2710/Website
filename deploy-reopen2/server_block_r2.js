
// ── reopen2 (live QA fixes) ──
// F1 admin ?view=guest / ?view=exit act on the same request; signed-in pages are never publicly cached.
// F2 with no DISPATCH_BYOK_MASTER_KEY the copy says "Use your own AI key: coming soon" (the full copy returns when the key is set).
// F4 one free-brief form per page (the footer copy is dropped when the page already has one).
// Admin AI status: xAI is no longer listed as a site provider. Portfolio X-ray CSV: quoted amounts may carry thousands commas.
function r2ByokOn() { try { return typeof c96ByokAvailable === "function" ? !!c96ByokAvailable() : true; } catch (e) { return true; } }
const R2_SOON = "Use your own AI key: coming soon";
function r2NoByokHtml(h) {
  h = h.split("Ask, if you add your own AI key in Settings (your provider bills you)").join(R2_SOON);
  h = h.split("Ask, using our AI keys (or yours, if you prefer)").join("Ask, using our AI");
  h = h.replace(/<h2 style="margin-top:26px">Using your own AI key<\/h2><p>[\s\S]*?<\/p>/, `<h2 style="margin-top:26px">${R2_SOON}</h2><p>Soon you will be able to add your own key from an AI provider in Settings, so that Ask uses it and your provider bills you. It is not switched on yet.</p>`);
  h = h.replace(/<h2 id="byok">Your own AI key<\/h2><p>[\s\S]*?<\/p>/, `<h2 id="byok">${R2_SOON}</h2><p>Adding your own AI provider key in Settings is not switched on yet. When it is, Ask will use that key for that reader's questions only and say so; keys will be encrypted on our server, never sent back to the browser and deleted with the account.</p>`);
  return h;
}
const r2TransformPrev = c97Transform;
c97Transform = function (html, req) {
  let out = r2TransformPrev(html, req);
  if (typeof out !== "string" || out.indexOf("<!--r2-->") >= 0 || !/^\s*<!doctype html/i.test(out)) return out;
  if (out.indexOf('id="c97-theme"') < 0 && out.indexOf("<!--c97-theme-->") < 0) return out;
  const app = out.indexOf('id="cmdBar"') >= 0 || /\/app\.js\?v=/.test(out);
  if (!r2ByokOn()) {
    if (app) out = out.replace(/<html([^>]*?)\sclass="/i, '<html$1 class="r2-nobyok ');
    else out = r2NoByokHtml(out);
  }
  if (!app && out.indexOf("<div data-c96-footsu>") >= 0 && out.split('action="/free-brief"').length > 2) out = out.replace(/<div data-c96-footsu>[\s\S]*?<\/form><\/div>/, "");
  return out.replace(/<head([^>]*)>/i, "<head$1><!--r2-->");
};
function r2Split(ln) {
  const out = []; let cur = "", q = false;
  for (let i = 0; i < ln.length; i++) {
    const ch = ln[i];
    if (ch === '"') { if (q && ln[i + 1] === '"') { cur += '"'; i++; } else q = !q; continue; }
    if (!q && (ch === "," || ch === ";" || ch === "\t")) { out.push(cur.trim()); cur = ""; continue; }
    cur += ch;
  }
  out.push(cur.trim()); return out;
}
c98Parse = function (text) {
  const out = []; const lines = String(text || "").split(/\r?\n/).slice(0, 60);
  for (let ln of lines) {
    ln = ln.trim(); if (!ln || /^"?name"?\s*[,;\t]/i.test(ln)) continue;
    const parts = r2Split(ln); if (parts.length < 2) continue;
    const name = parts[0].replace(/["<>]/g, "").slice(0, 60), amt = c98Num(parts[1]); if (!name || amt == null || amt <= 0) continue;
    out.push({ name, amount: amt, cls: c98Classify(name, (parts[2] || "").trim()) });
  }
  return out.slice(0, 50);
};
function r2NoXai(d) {
  if (!d || typeof d !== "object") return d;
  const isX = p => p && (p.id === "xai" || /^xai\b|^xAI\b|grok/i.test(String(p.label || "")));
  if (Array.isArray(d.providers)) d.providers = d.providers.filter(p => !isX(p));
  if (Array.isArray(d.fallbackOrder)) d.fallbackOrder = d.fallbackOrder.filter(x => x !== "xai");
  return d;
}
var r2FrontPrev = handle;
handle = async function r2Front(req, res) {
  try {
    const m = req.method, gh = m === "GET" || m === "HEAD";
    const raw = String(req.url || "/"), qi = raw.indexOf("?"), p = qi >= 0 ? raw.slice(0, qi) : raw;
    const ck = String(req.headers.cookie || "");
    const hasSess = typeof dispatchSessionTokens === "function" && ck ? dispatchSessionTokens(ck).length > 0 : false;
    if (gh && hasSess) {                                                    // signed-in or preview pages: never a shared/public cache
      const fix = v => /public/i.test(String(v)) ? "private, no-store" : v;
      const sh0 = res.setHeader;
      res.setHeader = function (k, v) { return sh0.call(this, k, String(k).toLowerCase() === "cache-control" ? fix(v) : v); };
      const wh0 = res.writeHead;
      res.writeHead = function (s, a, b) { const h = (a && typeof a === "object" && !Array.isArray(a)) ? a : (b && typeof b === "object" && !Array.isArray(b)) ? b : null; if (h) for (const k of Object.keys(h)) if (k.toLowerCase() === "cache-control") h[k] = fix(h[k]); return wh0.apply(this, arguments); };
    }
    if (gh && qi >= 0 && hasSess && p.indexOf("/api/") !== 0) {
      const u = new URL(raw, "http://localhost"), view = u.searchParams.get("view");
      if (view === "guest" || view === "exit") {
        const user = await c96UserOf(req);
        if (c96IsAdmin(user)) {
          const on = view === "guest";
          const parts = ck.split(/;\s*/).filter(x => x && !/^dispatch_preview=/.test(x)); if (on) parts.push("dispatch_preview=1");
          req.headers.cookie = parts.join("; ");
          c96PvSet(res, on);
          u.searchParams.delete("view");
          req.url = u.pathname + (u.searchParams.toString() ? "?" + u.searchParams.toString() : "");
          req.r2View = view;
          try { res.setHeader("Cache-Control", "private, no-store"); } catch (e) {}
        }
      }
    }
    if (m === "GET" && (p === "/api/admin/ai-readiness" || p === "/api/ai-status")) {
      const wh0 = res.writeHead, e0 = res.end;
      res.writeHead = function (s, a, b) { const h = (a && typeof a === "object") ? a : (b && typeof b === "object") ? b : null; if (h) for (const k of Object.keys(h)) if (k.toLowerCase() === "content-length") delete h[k]; try { res.removeHeader("Content-Length"); } catch (e) {} return wh0.apply(this, arguments); };
      res.end = function (chunk, enc, cb) {
        res.end = e0;
        try { if (chunk != null && typeof chunk !== "function") { const s = Buffer.isBuffer(chunk) ? chunk.toString("utf8") : String(chunk); if (/^\s*\{/.test(s)) { const out = JSON.stringify(r2NoXai(JSON.parse(s))); if (!res.headersSent) { try { res.removeHeader("Content-Length"); } catch (e) {} } return e0.call(res, out, typeof enc === "function" ? enc : cb); } } } catch (e) {}
        return e0.apply(res, arguments);
      };
    }
  } catch (e) { console.warn("[r2 front]", e && e.message); }
  return r2FrontPrev.apply(this, arguments);
};
