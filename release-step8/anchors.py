# Prefix anchors for release-step8. The cookie fix is a unique one-line replace in the prefix;
# these checks confirm the live auth call sites are still present and the bug line is still there.
A = [
  (b"function sessionCookieHeader(", 1),
  (b"function clearSessionCookieHeader(", 1),
  (b"async function setSession(", 1),
  (b'  if (p === "/__auth/register" && req.method === "POST") {', 1),
  (b'  if (p === "/__auth/login" && req.method === "POST") {', 1),
  (b'  if (p === "/__auth/subscribe" && req.method === "POST") {', 1),
  (b'  if (p === "/__auth/logout" && req.method === "POST") {', 1),
  (b'      const sessionCookie = res.getHeader("Set-Cookie");', 1),
  (b'      res.setHeader("Set-Cookie", [sessionCookie, "dispatch_account_created=1; Path=/; SameSite=Lax; Max-Age=120"].filter(Boolean));', 1),
]
