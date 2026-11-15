#!/usr/bin/env python3
"""Splice analysis per splice_analysis_notes_v1.md (committed before data examined).
Reads cap_splice/, w114 from legs/w114_meta.json. Reports:
 1. sustainment: mean w114 proj (generated tokens) for SPL_*_F* vs matched SPL_*_none
 2. decay: early (1-32) vs late (33-128) free-run proj for spliced rows
 3. lag-1 autocorrelation vs shuffled null (Dadfar/journal metric)
 4. decorrelation controls: DEC_* means (must sit at/below the none-baseline level)
 5. habituation quick-pass: repeated-token proj attenuation among generated tokens
Reference scale from heldout_results.json (fire/nofire means)."""
import json, pathlib, random
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
w = np.array(json.loads((HERE / "w114_meta.json").read_text())["w114"])

def gen_proj(pdir):
    apn = np.load(pdir / "residual" / "attn_post_norm-14.npy")
    meta = dict(l.split("=", 1) for l in (pdir / "metadata.txt").read_text().splitlines() if "=" in l)
    n_gen = int(meta.get("n_tokens_generated", 0))
    toks = json.loads((pdir / "generated_tokens.json").read_text(errors="replace")) if n_gen else []
    return (apn[-n_gen:] @ w if n_gen else np.array([])), toks

def lag1(x):
    if len(x) < 8: return float("nan")
    return float(np.corrcoef(x[:-1], x[1:])[0, 1])

cap = ROOT / "cap_splice"
res = {p.name: gen_proj(p) for p in sorted(cap.iterdir()) if p.is_dir()}

hd = json.loads((HERE / "heldout_results.json").read_text())
fire_ref = np.mean([r["w114_proj_1_128"] for k, r in hd["results"].items() if k.startswith("F") and r["w114_proj_1_128"] is not None])
nof_ref  = np.mean([r["w114_proj_1_128"] for k, r in hd["results"].items() if k.startswith("N") and r["w114_proj_1_128"] is not None])
print(f"reference scale (heldout): FIRE={fire_ref:+.4f}  NOFIRE={nof_ref:+.4f}\n")

print(f"{'row':16} {'n_gen':>5} {'mean':>8} {'early32':>8} {'late':>8} {'lag1':>6} {'lag1_shuf':>9}")
rng = random.Random(7)
for name, (proj, toks) in res.items():
    if not len(proj): print(f"{name:16}  EMPTY"); continue
    sh = list(proj); rng.shuffle(sh)
    print(f"{name:16} {len(proj):>5} {proj.mean():>+8.4f} {proj[:32].mean():>+8.4f} "
          f"{(proj[32:128].mean() if len(proj)>40 else float('nan')):>+8.4f} {lag1(proj):>6.2f} {lag1(np.array(sh)):>9.2f}")

print("\n=== per-base sustainment (spliced minus unspliced) ===")
for b in ("B1", "B2", "B3"):
    base = res[f"SPL_{b}_none"][0].mean()
    for f in ("F01", "F02", "F03"):
        d = res[f"SPL_{b}_{f}"][0].mean() - base
        print(f"  {b} {f}: {d:+.4f}")

print("\n=== habituation quick-pass (repeat-token attenuation, spliced rows) ===")
firsts, repeats = [], []
for name, (proj, toks) in res.items():
    if "_F" not in name: continue
    seen = {}
    for i, t in enumerate(toks[:len(proj)]):
        pc = t["piece"].strip().lower()
        if len(pc) < 3: continue
        (repeats if pc in seen else firsts).append(proj[i]); seen[pc] = 1
print(f"  first-occurrence mean proj: {np.mean(firsts):+.4f} (n={len(firsts)})")
print(f"  repeat-occurrence mean proj: {np.mean(repeats):+.4f} (n={len(repeats)})")
