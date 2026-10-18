#!/usr/bin/env python3
"""patch_rt52sri.py — Subresource Integrity for lightweight-charts in index.html.

Finds the unpkg lightweight-charts@4.2.0 standalone script tag (defer or not),
fetches that exact URL with Accept-Encoding: identity, and refuses the hash
unless the final URL is still unpkg.com and lightweight-charts@4.2.0
.../lightweight-charts.standalone.production.js. The tag is rewritten to that
pinned URL plus integrity="sha384-..." and crossorigin="anonymous".

Idempotent when that tag already has a sha384 integrity and crossorigin="anonymous".
Aborts if the tag is missing or repeated. Never starts server.js.

Usage:
  python3 deploy/patch_rt52sri.py [--check|--dry-run] <index.html | dir>
"""
import base64, hashlib, os, re, sys, urllib.request

TAG = re.compile(
    r'<script\b([^>]*?)\bsrc=(["\'])(https://unpkg\.com/lightweight-charts@4\.2\.0/dist/lightweight-charts\.standalone\.production\.js)\2([^>]*)>\s*</script>',
    re.I,
)
PIN_PATH = '/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js'


def die(m):
    print('ABORT:', m)
    sys.exit(1)


def index_path(arg):
    if os.path.isdir(arg):
        p = os.path.join(arg, 'index.html')
        if not os.path.isfile(p):
            die('no index.html in ' + arg)
        return p
    return arg


def fetch(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'DispatchSRI/rt52',
        'Accept-Encoding': 'identity',
    })
    with urllib.request.urlopen(req, timeout=45) as resp:
        final = resp.geturl()
        body = resp.read()
        ctype = resp.headers.get('Content-Type', '')
    return final, ctype, body


def pinned(final, fallback):
    from urllib.parse import urlsplit
    parts = urlsplit(final)
    host = (parts.hostname or '').lower()
    if host not in ('unpkg.com', 'www.unpkg.com'):
        die('lightweight-charts redirected off unpkg: ' + final)
    if parts.path != PIN_PATH:
        die('lightweight-charts URL is not the exact 4.2.0 file: ' + final)
    return 'https://unpkg.com' + PIN_PATH if parts.query or parts.path == PIN_PATH else fallback


def integrity_of(body):
    if len(body) < 10000 or b'Lightweight Charts' not in body or b'v4.2.0' not in body[:400]:
        die('fetched bytes are not lightweight-charts v4.2.0 (%d bytes)' % len(body))
    return 'sha384-' + base64.b64encode(hashlib.sha384(body).digest()).decode('ascii')


def strip_attr(blob, name):
    return re.sub(r'\s+\b' + name + r'\s*=\s*(["\']).*?\1', '', blob, flags=re.I)


def already(html):
    tags = list(TAG.finditer(html))
    if len(tags) != 1:
        return False
    m = tags[0]
    whole = m.group(0).lower()
    return 'integrity="sha384-' in whole or "integrity='sha384-" in whole


def transform(html):
    if already(html):
        return html, None
    tags = list(TAG.finditer(html))
    if len(tags) != 1:
        die('lightweight-charts@4.2.0 script tag matched %d times (want 1)' % len(tags))
    m = tags[0]
    src = m.group(3)
    final, ctype, body = fetch(src)
    if 'javascript' not in ctype.lower() and 'ecmascript' not in ctype.lower():
        die('unexpected content-type %s for %s' % (ctype, final))
    url = pinned(final, src)
    sri = integrity_of(body)
    pre = strip_attr(strip_attr(m.group(1), 'integrity'), 'crossorigin').strip()
    post = strip_attr(strip_attr(m.group(4), 'integrity'), 'crossorigin').strip()
    q = m.group(2)
    pre_s = (' ' + pre) if pre else ''
    post_s = (' ' + post) if post else ''
    new = '<script%s src=%s%s%s integrity=%s%s%s crossorigin=%sanonymous%s%s></script>' % (
        pre_s, q, url, q, q, sri, q, q, q, post_s,
    )
    return html[:m.start()] + new + html[m.end():], sri


def main():
    argv = [a for a in sys.argv[1:] if a not in ('--check', '--dry-run')]
    dry = '--check' in sys.argv or '--dry-run' in sys.argv
    if len(argv) != 1:
        die('usage: python3 patch_rt52sri.py [--check|--dry-run] <index.html|dir>')
    path = index_path(argv[0])
    if not os.path.isfile(path):
        die('not a file: ' + path)
    raw = open(path, 'rb').read()
    crlf = b'\r\n' in raw
    html = raw.decode('utf-8').replace('\r\n', '\n')
    out, sri = transform(html)
    if sri is None:
        print('OK rt52sri already applied; no change (%s)' % path)
        return
    tag = TAG.search(out)
    print('SRI: %s' % sri)
    print('PIN: %s' % (tag.group(3) if tag else '?'))
    if dry:
        print('DRY-RUN: index.html not written')
        return
    data = out.replace('\n', '\r\n') if crlf else out
    open(path, 'wb').write(data.encode('utf-8'))
    print('OK rt52sri written', path)


if __name__ == '__main__':
    main()
