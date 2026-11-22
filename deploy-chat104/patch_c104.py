#!/usr/bin/env python3
"""Rename the reader-facing Learn section to Dispatch Academy.

The /learn/ path stays. Generic verbs such as "learn more" are not in the
replacement list. The CPI block and the last-write scrub stay byte for byte.
"""
import pathlib
import sys

CPI = "// chat103 cpi day"
SCRUB = "// chat102r6c last-write scrub."
OLD_TAG = "app.js?v=chat103d"
NEW_TAG = "app.js?v=chat104"

# (filename, old, new, expected count). Longer menu labels are replaced by the
# shorter "/learn/", "Learn" pair, which is the visible link text.
PAIRS = [
    (
        "server.js",
        'Learn | Beginner Guides, Glossary & Frameworks | The Dispatch Market',
        'Dispatch Academy | Beginner Guides, Glossary & Frameworks | The Dispatch Market',
        1,
    ),
    (
        "server.js",
        'h1: "Learn: plain-English market guides, glossary and frameworks",',
        'h1: "Dispatch Academy: plain-English market guides, glossary and frameworks",',
        1,
    ),
    (
        "server.js",
        '"/learn/", "Learn"',
        '"/learn/", "Dispatch Academy"',
        1,
    ),
    (
        "server.js",
        'header.site .c101c-acc a{display:flex;align-items:center;min-height:44px;box-sizing:border-box;margin:0;padding:10px 4px;border:0;border-top:1px solid var(--rule);font:500 15px/1.3 var(--sans);color:var(--ink);white-space:normal}',
        'header.site .c101c-acc a{display:flex;align-items:center;min-width:0;max-width:100%;min-height:44px;box-sizing:border-box;margin:0;padding:10px 4px;border:0;border-top:1px solid var(--rule);font:500 15px/1.3 var(--sans);color:var(--ink);white-space:normal;overflow-wrap:break-word}',
        1,
    ),
    (
        "server.js",
        '\\"Academy\\",\\"Lessons and games\\"',
        '\\"Dispatch Academy\\",\\"Lessons and games\\"',
        1,
    ),
    (
        "app.js",
        'Learn | Beginner Guides, Glossary & Frameworks | The Dispatch Market',
        'Dispatch Academy | Beginner Guides, Glossary & Frameworks | The Dispatch Market',
        1,
    ),
    (
        "app.js",
        '"/learn/", "Learn"',
        '"/learn/", "Dispatch Academy"',
        1,
    ),
    (
        "app.js",
        "headline = `Learn · ${",
        "headline = `Dispatch Academy · ${",
        1,
    ),
    (
        "app.js",
        'title: "Dispatch Academy · Learn"',
        'title: "Dispatch Academy"',
        1,
    ),
    (
        "app.js",
        '["learn", "Learn"]',
        '["learn", "Dispatch Academy"]',
        1,
    ),
    (
        "app.js",
        '["learn","Learn"]',
        '["learn","Dispatch Academy"]',
        1,
    ),
    (
        "app.js",
        '_renderPgHdr("Learn", "Professional analysis frameworks · Hedge fund methodologies")',
        '_renderPgHdr("Dispatch Academy", "Professional analysis frameworks · Hedge fund methodologies")',
        1,
    ),
    (
        "app.js",
        "| Learn | The Dispatch Market",
        "| Dispatch Academy | The Dispatch Market",
        1,
    ),
    (
        "app.js",
        "in the Learn section",
        "in the Dispatch Academy section",
        1,
    ),
    (
        "app.js",
        'aria-label="Learn sections"',
        'aria-label="Dispatch Academy sections"',
        1,
    ),
    (
        "app.js",
        "Reset your Learn progress",
        "Reset your Dispatch Academy progress",
        1,
    ),
    (
        "app.js",
        '["learn", "Academy", "Lessons and guides"]',
        '["learn", "Dispatch Academy", "Lessons and guides"]',
        1,
    ),
    (
        "app.js",
        '<a href="/learn/">Learn</a>',
        '<a href="/learn/">Dispatch Academy</a>',
        1,
    ),
    (
        "app.js",
        "html.c93 .c93-menu.c101b-menu .c101c-acc a{display:flex;align-items:center;min-height:44px;box-sizing:border-box;padding:10px 4px;border:0;border-top:1px solid var(--rule-soft);font:500 15px/1.3 var(--ui)}",
        "html.c93 .c93-menu.c101b-menu .c101c-acc a{display:flex;align-items:center;min-width:0;max-width:100%;min-height:44px;box-sizing:border-box;padding:10px 4px;border:0;border-top:1px solid var(--rule-soft);font:500 15px/1.3 var(--ui);white-space:normal;overflow-wrap:break-word}",
        1,
    ),
    (
        "index.html",
        OLD_TAG,
        NEW_TAG,
        1,
    ),
]


def tail(text, label):
    at = text.find(CPI)
    if at < 0:
        sys.exit(label + " is missing the CPI block")
    rest = text[at:]
    if SCRUB not in rest:
        sys.exit(label + " scrub block is not after the CPI block")
    if not rest.rstrip().endswith("})();"):
        sys.exit(label + " scrub block is not last")
    return rest


def apply_pairs(files):
    original = {name: files[name] for name in files}
    learn_urls = {name: files[name].count("/learn/") for name in files}
    for name, old, new, count in PAIRS:
        found = files[name].count(old)
        if found != count:
            sys.exit("%s %r matched %d times, expected %d" % (name, old, found, count))
        files[name] = files[name].replace(old, new, count)
        if files[name].count(old) != 0:
            sys.exit("%s still contains %r" % (name, old))
    if tail(files["server.js"], "patched server.js") != tail(original["server.js"], "original server.js"):
        sys.exit("CPI block or last-write scrub changed")
    for name in files:
        if files[name].count("/learn/") != learn_urls[name]:
            sys.exit("%s /learn/ count changed" % name)
    if OLD_TAG in files["index.html"] or NEW_TAG not in files["index.html"]:
        sys.exit("index cache tag was not bumped to chat104")
    kept = (
        "Learn why",
        "Learn one idea at a time",
        "learn more",
        "learn how",
    )
    for phrase in kept:
        if original["app.js"].count(phrase) != files["app.js"].count(phrase):
            sys.exit("generic wording changed: " + phrase)
    return files


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: patch_c104.py server.js app.js index.html")
    paths = [pathlib.Path(p) for p in sys.argv[1:]]
    files = {path.name: path.read_text(encoding="utf-8") for path in paths}
    apply_pairs(files)
    for path in paths:
        path.write_text(files[path.name], encoding="utf-8")
    print("renamed the Learn section to Dispatch Academy")
    print("CPI block and last-write scrub are byte-identical and the scrub is last")
    print("/learn/ paths are unchanged")
    print("index cache tag is app.js?v=chat104")


if __name__ == "__main__":
    main()
