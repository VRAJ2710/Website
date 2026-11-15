#!/usr/bin/env python3
"""Replace the r6g last-write scrub, skip guest alert polls, and bump the app cache tag.

Bytes before the scrub marker stay identical. app.js changes only the alert poll.
"""
import hashlib
import pathlib
import sys

MARKER = "// chat102r6c last-write scrub."
OLD_TAG = "app.js?v=chat103c"
NEW_TAG = "app.js?v=chat103d"
OLD_POLL = """function _c98Poll() {
  if (!_c98St || !_c98St.alerts || window._tdMePreview) return;
  fetch("/api/c98/alerts", { credentials: "same-origin", cache: "no-store" }).then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
    if (!j || !j.unseen) return;
    var e = (j.events || []).filter(function (x) { return !x.seen; })[0]; if (!e) return;
    try { if (sessionStorage.getItem("c98Dismiss") === e.message) return; } catch (x) {}
    _c98Banner(j.unseen, e.message);
  }).catch(function () {});
}"""
NEW_POLL = """function _c98Poll() {
  if (!_c98St || !_c98St.alerts || window._tdMePreview) return;
  if (typeof _userTierReady !== "undefined" && !_userTierReady) {
    if (!_c98Poll.waiting) {
      _c98Poll.waiting = 1;
      setTimeout(function () { _c98Poll.waiting = 0; _c98Poll(); }, 1000);
    }
    return;
  }
  if (typeof _userSignedIn === "undefined" || _userSignedIn !== true) return;
  fetch("/api/c98/alerts", { credentials: "same-origin", cache: "no-store" }).then(function (r) {
    if (!r || r.status === 401 || !r.ok) return null;
    return r.json();
  }).then(function (j) {
    if (!j || !j.unseen) return;
    var e = (j.events || []).filter(function (x) { return !x.seen; })[0]; if (!e) return;
    try { if (sessionStorage.getItem("c98Dismiss") === e.message) return; } catch (x) {}
    _c98Banner(j.unseen, e.message);
  }).catch(function () {});
}"""


def main():
    if len(sys.argv) != 6:
        sys.exit("usage: patch_c102r6h.py server.js app.js index.html old_block.js new_block.js")
    server, app, index, old_path, new_path = [pathlib.Path(p) for p in sys.argv[1:]]
    text = server.read_text(encoding="utf-8")
    old = old_path.read_text(encoding="utf-8")
    new = new_path.read_text(encoding="utf-8")
    at = app.read_text(encoding="utf-8")
    it = index.read_text(encoding="utf-8")
    if not old.endswith("\n"):
        old += "\n"
    if not new.endswith("\n"):
        new += "\n"
    if MARKER not in old or MARKER not in new:
        sys.exit("scrub block is missing its marker")
    if text.count(old) != 1:
        sys.exit("staged scrub block matched %d times" % text.count(old))
    if at.count(OLD_POLL) != 1:
        sys.exit("app.js alert poll matched %d times" % at.count(OLD_POLL))
    if it.count(OLD_TAG) != 1:
        sys.exit("index.html app.js?v=chat103c matched %d times" % it.count(OLD_TAG))
    if "chat102r6h:" not in new:
        sys.exit("new scrub block is not chat102r6h")
    prefix, suffix = text.split(old, 1)
    suffix_out = suffix + "\n" if suffix and not suffix.endswith("\n") else suffix
    result = prefix + suffix_out + new
    if not result.endswith(new):
        sys.exit("updated scrub block is not last")
    if result[: len(prefix)] != prefix:
        sys.exit("bytes before the scrub block changed")
    server.write_text(result, encoding="utf-8")
    app.write_text(at.replace(OLD_POLL, NEW_POLL, 1), encoding="utf-8")
    index.write_text(it.replace(OLD_TAG, NEW_TAG, 1), encoding="utf-8")
    print("replaced the last-write scrub block; bytes before it unchanged; block is last")
    print("prefix sha256 " + hashlib.sha256(prefix.encode("utf-8")).hexdigest())
    print("app.js skips /api/c98/alerts until a signed-in session is known")
    print("index cache tag is app.js?v=chat103d")


if __name__ == "__main__":
    main()
