# strip_credits.py a b : exit 0 if a (step 3 output) minus the credits additions equals b (step 2 output)
import re, sys
def strip(s):
    s = re.sub(r'<p class="c107-fred">[^<]*</p>', "", s)
    s = re.sub(r'<p class="c107-meth">[\s\S]*?</p>', "", s)
    s = re.sub(r'<style id="c107-css">[\s\S]*?</style><script id="c107-credits">[\s\S]*?</script>', "", s)
    s = re.sub(r'\(FRED<span class="c107-ids" data-c107-ids="([^"]+)"></span>\)', lambda m: "(FRED " + m.group(1).replace(",", ", ") + ")", s)
    return s
a = open(sys.argv[1], encoding="utf-8", errors="replace").read(); b = open(sys.argv[2], encoding="utf-8", errors="replace").read()
sys.exit(0 if strip(a) == b else 1)
