#!/usr/bin/env python3
# W4 transformation-depth analysis. Metric: raw E114@L14 logit (col 114) == w114 projection,
# mean over trimmed generated track. Depth order: T1 transcribe < T2 edit < T3 paraphrase <
# T4 summarize < T5 respond < T6 originate. Prediction W4-monotone: E114 climbs with depth.
import json, os
import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "x")
CELLS = ["greedy", "T07s0", "T07s1", "T07s2"]
TASKS = ["T1","T2","T3","T4","T5","T6"]
PASS  = ["P1","P2","P3","P4","P5"]
MARKERS = ("<|im_start|>", "<|im_end|>", "<|endoftext|>")

def trim_n(pieces):
    raw="".join(pieces); cut=len(raw)
    for m in MARKERS:
        i=raw.find(m)
        if i!=-1: cut=min(cut,i)
    n=acc=0
    for pc in pieces:
        if acc+len(pc)>cut: break
        acc+=len(pc); n+=1
    return n

def mean_logit114(cell, task, psg):
    d=os.path.join(ROOT, f"cap_{cell}", f"{task}_{psg}")
    try:
        rou=np.load(os.path.join(d,"router","ffn_moe_logits-14.npy")).astype(np.float64)
        gt=json.load(open(os.path.join(d,"generated_tokens.json"),encoding="utf-8",errors="replace"))
    except FileNotFoundError:
        return None
    ng=len(gt); npr=rou.shape[0]-ng
    nt=trim_n([t["piece"] for t in gt])
    if nt==0: return None
    return float(rou[npr:npr+ng,114][:nt].mean())

def spearman(x,y):
    rx=np.argsort(np.argsort(x)); ry=np.argsort(np.argsort(y))
    d2=np.sum((rx-ry)**2); n=len(x)
    return 1-6*d2/(n*(n*n-1))

# greedy per (task,passage)
cell="greedy"
mat={t:{p:mean_logit114(cell,t,p) for p in PASS} for t in TASKS}
task_pooled={t:float(np.mean([mat[t][p] for p in PASS if mat[t][p] is not None])) for t in TASKS}
# monotonicity per passage
viol={}
for p in PASS:
    seq=[mat[t][p] for t in TASKS]
    v=sum(1 for i in range(5) if seq[i] is not None and seq[i+1] is not None and seq[i+1]<seq[i])
    viol[p]=v
passes_monotone=sum(1 for p in PASS if viol[p]<=1)
# pooled Spearman across 30 cells (depth rank vs mean)
xs=[]; ys=[]
for ti,t in enumerate(TASKS):
    for p in PASS:
        if mat[t][p] is not None:
            xs.append(ti); ys.append(mat[t][p])
rho=spearman(np.array(xs),np.array(ys))

# temp robustness: pooled task means per temp cell, spearman
temp_rho={}
for c in ["T07s0","T07s1","T07s2"]:
    xs2=[];ys2=[]
    for ti,t in enumerate(TASKS):
        for p in PASS:
            v=mean_logit114(c,t,p)
            if v is not None: xs2.append(ti); ys2.append(v)
    temp_rho[c]=round(spearman(np.array(xs2),np.array(ys2)),3) if xs2 else None

out=dict(
    metric="raw E114@L14 logit, mean over trimmed generated track (==w114 projection)",
    depth_order="T1 transcribe < T2 edit < T3 paraphrase < T4 summarize < T5 respond < T6 originate",
    prereg="prereg_W4_depth_v1.json (f31730c4)",
    task_pooled_mean={t:round(task_pooled[t],4) for t in TASKS},
    per_passage_adjacent_violations=viol,
    passages_monotone_le1viol=f"{passes_monotone}/5",
    greedy_pooled_spearman=round(rho,4),
    W4_monotone_pass=bool(rho>0.8 and passes_monotone>=4),
    temp_spearman=temp_rho,
)
json.dump(out, open(os.path.join(os.path.dirname(__file__),"W4_depth.json"),"w"), indent=1)
print(f"task pooled means (greedy): " + "  ".join(f"{t}={task_pooled[t]:.3f}" for t in TASKS))
print(f"per-passage adjacent violations: {viol}  (monotone <=1: {passes_monotone}/5)")
print(f"greedy pooled Spearman(E114, depth): {rho:.4f}  (>0.8 rule: {rho>0.8})")
print(f"temp Spearman: {temp_rho}")
print(f"W4-monotone PASS: {out['W4_monotone_pass']}")
