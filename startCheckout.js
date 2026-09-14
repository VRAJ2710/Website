"use strict";

/**
 * Browser checkout handoff used by app.js `/?checkout=1` and the premium gate.
 * Always send cookies so a same-site fetch cannot drop dispatch_session.
 * On 401, reuse /api/me.checkoutSession instead of bouncing a signed-in member
 * back to /__auth/subscribe.
 */
async function startCheckout(options = {}) {
  const fetchFn = options.fetchImpl || fetch;
  const assign = options.locationAssign || (url => {
    if (typeof globalThis.location !== "undefined") globalThis.location.href = url;
  });

  const response = await fetchFn("/api/create-checkout", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  const data = await response.json().catch(() => ({}));

  if (data.url) {
    assign(data.url);
    return { ok: true, url: data.url };
  }

  if (response.status === 401) {
    try {
      const meResponse = await fetchFn("/api/me", { credentials: "include" });
      const account = meResponse.ok ? await meResponse.json() : null;
      if (account?.checkoutSession?.url) {
        assign(account.checkoutSession.url);
        return { ok: true, url: account.checkoutSession.url, reused: true };
      }
      if (account?.id) {
        return {
          ok: false,
          signedIn: true,
          error: data.error || "Unable to start checkout",
        };
      }
    } catch {
      // Fall through to subscribe so a guest can still create an account.
    }
    assign("/__auth/subscribe");
    return { ok: false, redirect: "/__auth/subscribe" };
  }

  return { ok: false, error: data.error || "Something went wrong" };
}

module.exports = { startCheckout };
