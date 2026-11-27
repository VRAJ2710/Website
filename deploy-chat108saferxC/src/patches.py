# Exact text replacements applied to the v3 renderer (/__v3p/home.js) for the preview's cache-busted URL only.
# Each OLD must occur exactly COUNT times in the served file, or the block serves the file unchanged.
import re
PATCHES = []
def P(old, new, count=1): PATCHES.append((old, new, count))
# helpers: is a time today (UK)? relabel an old "Delayed"/"Live" figure as "Last close"
P('function lag(s){return s?\'<span class="v3-lag \'+lagCls(s)+\'">\'+esc(s)+\'</span>\':""}',
  'function lag(s){return s?\'<span class="v3-lag \'+lagCls(s)+\'">\'+esc(s)+\'</span>\':""}\n'
  '/* chat108saferxC: a figure dated before today (UK) is not labelled Delayed or Live; it is the last close */\n'
  'function isTodayUK(ms){return isFinite(ms)&&ms>0&&ukDate(ms)===ukDate(Date.now())}\n'
  'function strToday(s){var m=/\\b(\\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\\b/.exec(String(s||""));return !m||(Number(m[1])+" "+m[2])===ukDate(Date.now())}\n'
  'function lagFix(st,t){return /^\\s*(delayed|live)\\s*$/i.test(String(st||""))&&!strToday(t)?"Last close":st}')
# gauges: range-bar figures (Yahoo delayed quote, or the last close when the market has not traded today)
P("function src(r,extra){return 'Yahoo Finance, '+esc(extra)+' \\u00b7 as of '+esc(uk(r.t))+' '+lag(\"Delayed\")}",
  "function src(r,extra){return 'Yahoo Finance, '+esc(extra)+' \\u00b7 as of '+esc(uk(r.t))+' '+lag(isTodayUK(r.t)?\"Delayed\":\"Last close\")}")
P('"Cboe VIX index, delayed"', '"Cboe VIX index"')
# key prices and five things that moved: macro rows
P('lag(r.status||a.lag)', 'lag(lagFix(r.status||a.lag,a.time))', 2)
# chart tiles
P("' '+lag(\"Delayed\")+'</p></div>'})", "' '+lag(isTodayUK(m.regularMarketTime*1000)?\"Delayed\":\"Last close\")+'</p></div>'})")
P("the big number is the latest delayed quote.", "the big number is the latest delayed quote, or the last close where it is labelled so.")
