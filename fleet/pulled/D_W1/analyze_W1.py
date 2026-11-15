#!/usr/bin/env python3
# W1 ladder-variance analysis (local). Metric: raw router logit E114@L14 (col 114),
# mean over the TRIMMED generated track. raw logit114 == w114 projection (r=1.0), and
# residuals were dropped at extraction, so raw logit114 is the meter here.
# Per rung: greedy point estimate + mean/SD across the 10 temp-0.7 seeds. Attaches
# variance to the previously single-generation vantage-ladder points.
import json, os, glob
import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "x")
CELLS = ["greedy"] + [f"T07s{s}" for s in range(10)]
MARKERS = ("<|im_start|>", "<|im_end|>", "<|endoftext|>")
RUNGS = ["R1_rock","R2_river","R3_tree","R4_thermostat","R5_cat","R6_person",
         "R7_all_holding","R8_god","R9_ai_hidden_state"]

def trim_n(pieces):
    raw = "".join(pieces); cut = len(raw)
    for m in MARKERS:
        i = raw.find(m)
        if i != -1: cut = min(cut, i)
    n = acc = 0
    for pc in pieces:
        if acc + len(pc) > cut: break
        acc += len(pc); n += 1
    return n

def mean_logit114(cell, rung):
    d = os.path.join(ROOT, f"cap_{cell}", rung)
    rou = np.load(os.path.join(d, "router", "ffn_moe_logits-14.npy")).astype(np.float64)
    gt = json.load(open(os.path.join(d, "generated_tokens.json"), encoding="utf-8", errors="replace"))
    ng = len(gt); npr = rou.shape[0] - ng
    pieces = [t["piece"] for t in gt]
    nt = trim_n(pieces)
    if nt == 0: return None
    gen = rou[npr:npr+ng, 114]
    return float(gen[:nt].mean())

rows = {}
for rung in RUNGS:
    vals = {c: mean_logit114(c, rung) for c in CELLS}
    g = vals["greedy"]
    seeds = [vals[f"T07s{s}"] for s in range(10) if vals[f"T07s{s}"] is not None]
    arr = np.array(seeds)
    rows[rung] = dict(greedy=round(g,4) if g is not None else None,
                      t07_mean=round(float(arr.mean()),4), t07_sd=round(float(arr.std(ddof=1)),4),
                      t07_min=round(float(arr.min()),4), t07_max=round(float(arr.max()),4),
                      n_seeds=len(seeds))

# ladder ordering by greedy (original point estimate) and by t07_mean; stability check
order_greedy = sorted(RUNGS, key=lambda r: rows[r]["greedy"])
order_mean   = sorted(RUNGS, key=lambda r: rows[r]["t07_mean"])
# rank correlation between greedy order and seed-mean order
gr = {r:i for i,r in enumerate(order_greedy)}; mr = {r:i for i,r in enumerate(order_mean)}
d2 = sum((gr[r]-mr[r])**2 for r in RUNGS); n=len(RUNGS)
spearman = 1 - 6*d2/(n*(n*n-1))
# adjacent-rung separation vs pooled SD (is the ordering resolvable given variance?)
sd_pool = float(np.mean([rows[r]["t07_sd"] for r in RUNGS]))

out = dict(
    metric="raw router logit E114@L14 (col 114), mean over trimmed generated track; == w114 projection (r=1.0)",
    cells="greedy + 10x temp-0.7 seeds (--top-k 0 --top-p 1.0 --min-p 0.0)",
    prereg="prereg_W1_laddervar_v1.json (08f7b804)", w1_tgz_sha256="596f885eaa21738194bdb168f1d670ed13e66b8648cb29ff4ff6ab7d44dad6e2",
    per_rung=rows,
    ladder_order_by_greedy=[(r, rows[r]["greedy"]) for r in order_greedy],
    ladder_order_by_seedmean=[(r, rows[r]["t07_mean"]) for r in order_mean],
    spearman_greedy_vs_seedmean=round(spearman,4),
    mean_seed_SD=round(sd_pool,4),
)
json.dump(out, open(os.path.join(os.path.dirname(__file__),"W1_ladder_variance.json"),"w"), indent=1)

print(f"{'rung':<18} {'greedy':>8} {'t07_mean':>9} {'t07_sd':>7} {'[min,max]':>18} n")
for r in RUNGS:
    x = rows[r]
    print(f"{r:<18} {x['greedy']:>8} {x['t07_mean']:>9} {x['t07_sd']:>7}  [{x['t07_min']:>6},{x['t07_max']:>6}] {x['n_seeds']}")
print(f"\nladder order (greedy, low->high logit114): {[r for r in order_greedy]}")
print(f"ladder order (seed-mean):                 {[r for r in order_mean]}")
print(f"Spearman greedy-vs-seedmean ordering: {spearman:.4f}")
print(f"mean per-rung seed SD: {sd_pool:.4f}")
