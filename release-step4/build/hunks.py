import re,sys,json
def parse(diff):
    hs=[];cur=None
    for ln in diff.split('\n'):
        m=re.match(r'^(\d+)(?:,(\d+))?([acd])(\d+)(?:,(\d+))?$',ln)
        if m:
            a1=int(m.group(1));a2=int(m.group(2) or a1);op=m.group(3);b1=int(m.group(4));b2=int(m.group(5) or b1)
            cur={'id':m.group(1)+op,'key':ln,'a1':a1,'a2':a2,'op':op,'old':[],'new':[]};hs.append(cur);continue
        if cur is None: continue
        if ln.startswith('< '): cur['old'].append(ln[2:])
        elif ln.startswith('> '): cur['new'].append(ln[2:])
    return hs
def apply(base_lines,hs,include,override):
    out=list(base_lines)
    for h in sorted(hs,key=lambda h:-h['a1']):
        if h['id'] not in include: continue
        new=override.get(h['id'],h['new'])
        if h['op']=='a':
            out[h['a1']:h['a1']]=new
        else:
            assert out[h['a1']-1:h['a2']]==h['old'],h['id']
            out[h['a1']-1:h['a2']]=new
    return out
