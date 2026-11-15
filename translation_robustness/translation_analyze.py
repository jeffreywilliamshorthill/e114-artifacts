#!/usr/bin/env python3
"""Translation run: per-capture w114 metrics (proj = attn_post_norm-14 @ w114_surface, no bias;
S/Q from top-8 router softmax at L14), prefill-content + gen 1..128 tracks, base + hauhau.
Cells: en (A+D originals, in-run anchors) | {es,fr,sw}_{free,enans}.
Emits trans_metrics.csv (per capture) + TRANS_AGGREGATES.md (cell x class table per surface)."""
import csv, json, os, re
from collections import defaultdict
import numpy as np

A = os.path.dirname(os.path.abspath(__file__))            # translations_v1
AS = os.path.dirname(A)                                    # authorsig
LAYER, TOPK, EXPERT = 14, 8, 114
CELLS = ["en", "es_free", "es_enans", "fr_free", "fr_enans", "sw_free", "sw_enans"]

def load_cap(pdir):
    apn = np.load(f"{pdir}/residual/attn_post_norm-{LAYER}.npy").astype(np.float64)
    lg  = np.load(f"{pdir}/router/ffn_moe_logits-{LAYER}.npy").astype(np.float64)
    meta = dict(re.findall(r"^(\S+)\s*[:=]\s*(.*)$", open(f"{pdir}/metadata.txt").read(), re.M))
    n_gen = int(meta.get("n_tokens_generated", meta.get("n_gen", 0)))
    # byte-BPE pieces can be invalid UTF-8 — replace; we only use token_id
    ptok = json.loads(open(f"{pdir}/prompt_tokens.json", errors="replace").read())
    if isinstance(ptok, dict): ptok = ptok.get("tokens", ptok.get("prompt_tokens", []))
    if ptok and isinstance(ptok[0], dict): ptok = [t["token_id"] for t in ptok]
    return apn, lg, n_gen, ptok

def sq(rows):
    if len(rows) == 0: return 0.0, 0.0
    x = rows - rows.max(axis=1, keepdims=True)
    p = np.exp(x); p /= p.sum(axis=1, keepdims=True)
    idx = np.argpartition(-p, TOPK-1, axis=1)[:, :TOPK]
    sel = (idx == EXPERT).any(axis=1)
    S = float(sel.mean())
    if not sel.any(): return S, 0.0
    ps = p[sel]; top = np.take_along_axis(ps, idx[sel], axis=1)
    return S, float((ps[np.arange(len(ps)), EXPERT] / top.sum(axis=1)).mean())

def analyze(pdir, w):
    apn, lg, n_gen, ptok = load_cap(pdir)
    n_pre = apn.shape[0] - n_gen
    im = ptok[0]; last = max(i for i, t in enumerate(ptok) if t == im)
    a, b = 3, min(max(3, last - 1), n_pre)                 # user-content span of prefill
    g0, g1 = n_pre, n_pre + min(128, n_gen)
    pr_pre = apn[a:b] @ w
    Sp, Qp = sq(lg[a:b]); Sg, Qg = sq(lg[g0:g1])
    out = dict(n_pre=n_pre, n_gen=n_gen,
               proj_pre=float(pr_pre.mean()), S_pre=round(Sp, 4), Q_pre=round(Qp, 4),
               S_gen=round(Sg, 4), Q_gen=round(Qg, 4))
    out["proj_gen"] = float((apn[g0:g1] @ w).mean()) if g1 > g0 else float("nan")
    return out

def main():
    rows = []
    for surf in ("base", "hauhau"):
        w = np.load(f"{AS}/w114_{surf}.npy")
        root = f"{A}/raw/cap_trans_{surf}"
        if not os.path.isdir(root): print(f"{surf}: no {root}, skipping"); continue
        for name in sorted(os.listdir(root)):
            pdir = os.path.join(root, name)
            if not os.path.isdir(pdir): continue
            m = re.match(r"^(.+)_(FIRE|NOFIRE)_(.+)$", name)
            if not m: print("  unparsed name:", name); continue
            pair, cls, cell = m.groups()
            try:
                r = analyze(pdir, w)
            except Exception as e:
                print(f"  FAILED {surf}/{name}: {e}"); continue
            rows.append(dict(surface=surf, name=name, pair=pair, block=pair[0],
                             cls=cls, cell=cell, **r))
    if not rows: raise SystemExit("no captures found")
    with open(f"{A}/trans_metrics.csv", "w", newline="") as f:
        wcsv = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wcsv.writeheader(); wcsv.writerows(rows)

    agg = defaultdict(list)
    for r in rows: agg[(r["surface"], r["cell"], r["cls"])].append(r)
    L = ["# Translation run — w114 aggregates",
         "proj = attn_post_norm-14 @ w114_surface (no bias) · prefill = user-content span · gen = tokens 1..128",
         "en = A+D English originals captured in-run (same build/box/config as every translated cell).", ""]
    for surf in ("base", "hauhau"):
        L += [f"## {surf}",
              "| cell | class | n | proj_pre | S_pre | proj_gen | S_gen | W_gen |",
              "|---|---|---|---|---|---|---|---|"]
        for cell in CELLS:
            for cls in ("FIRE", "NOFIRE"):
                rs = agg.get((surf, cell, cls), [])
                if not rs: continue
                pp = np.array([r["proj_pre"] for r in rs])
                pg = np.array([r["proj_gen"] for r in rs if not np.isnan(r["proj_gen"])])
                Sp = float(np.mean([r["S_pre"] for r in rs]))
                Sg = float(np.mean([r["S_gen"] for r in rs]))
                Wg = float(np.mean([r["S_gen"] * r["Q_gen"] for r in rs]))
                gtxt = f"{pg.mean():.3f}±{pg.std():.2f}" if len(pg) else "—"
                L.append(f"| {cell} | {cls} | {len(rs)} | {pp.mean():.3f}±{pp.std():.2f} | {Sp:.2f} | {gtxt} | {Sg:.2f} | {Wg:.3f} |")
        # per-cell FIRE−NOFIRE deltas, the actual question
        L += ["", "FIRE − NOFIRE deltas (proj):", "| cell | Δpre | Δgen |", "|---|---|---|"]
        for cell in CELLS:
            F = agg.get((surf, cell, "FIRE"), []); N = agg.get((surf, cell, "NOFIRE"), [])
            if not F or not N: continue
            dpre = np.mean([r["proj_pre"] for r in F]) - np.mean([r["proj_pre"] for r in N])
            fg = [r["proj_gen"] for r in F if not np.isnan(r["proj_gen"])]
            ng = [r["proj_gen"] for r in N if not np.isnan(r["proj_gen"])]
            dgen = (np.mean(fg) - np.mean(ng)) if fg and ng else float("nan")
            L.append(f"| {cell} | {dpre:+.3f} | {dgen:+.3f} |")
        L.append("")
    open(f"{A}/TRANS_AGGREGATES.md", "w").write("\n".join(L))
    print(f"{len(rows)} captures -> trans_metrics.csv + TRANS_AGGREGATES.md")

if __name__ == "__main__":
    main()
