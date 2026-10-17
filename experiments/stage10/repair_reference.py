"""Independent enumeration with explicit output intervals and survival masks."""
from __future__ import annotations


def explicit_repaired_counts(calibrated, raw, max_states=1_000_000,
                             max_transitions=50_000_000):
    n = len(raw)-1
    # Key: success count, actual raw/cal running endpoints, all-time survivors.
    all_counts = (1 << (n+1))-1
    states = {(0,0,n,0,n,all_counts):1}
    transitions = 0
    for t in range(1,n+1):
        new = {}
        for (s,rl,ru,cl,cu,mask),mass in states.items():
            for outcome in (0,1):
                transitions += 1
                if transitions > max_transitions:
                    raise RuntimeError("Independent repaired transition cap")
                ns = s+outcome
                nrl = max(rl,int(raw[t,ns,0])); nru = min(ru,int(raw[t,ns,1]))
                ncl = max(cl,int(calibrated[t,ns,0])); ncu = min(cu,int(calibrated[t,ns,1]))
                lower,upper = (nrl,nru) if ncl>ncu else (ncl,ncu)
                if t == n:
                    lower=upper=ns
                accepted = 0 if lower>upper else ((1 << (upper+1))-1)^((1 << lower)-1)
                survive = mask & accepted
                if not survive:
                    continue
                # Normalize empty running intervals; only emptiness matters later.
                if nrl>nru:nrl,nru=n,0
                if ncl>ncu:ncl,ncu=n,0
                key = (ns,nrl,nru,ncl,ncu,survive)
                new[key] = new.get(key,0)+mass
                if len(new)>max_states:
                    raise RuntimeError("Independent repaired state cap")
        states=new
    answer=[0]*(n+1)
    for (s,rl,ru,cl,cu,mask),mass in states.items():
        if mask & (1 << s):answer[s]+=mass
    return answer
