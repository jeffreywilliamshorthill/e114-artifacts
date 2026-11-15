#!/usr/bin/env python3
"""analyze_coalition.py — copy-coalition contrast on the convdyn grid (LOCAL, post-hoc).

Question (friend's-AI proposal 2, adopted): when arm-A generation flips from composing
register text to copying it, which experts' router logits RISE while E114 falls — and is
E114's fall an outlier against the all-expert distribution, or just a generic routing shift?

Data: full 256-expert router matrices at L13/L14/L15/L26 survived in the pulled grid
(only residuals were deleted). Arm A tokens only, trimmed gen track.

Contrast per expert e per layer L:
  d(e,L) = Cohen's d of logit(e,L) on COPY tokens (max_ngram>=8) vs COMPOSE tokens (<8)
Robustness: same contrast restricted to late turns (t5-14) only — controls the turn confound.

Highlights: (L14,E114) rank + z-score vs all-expert contrast distribution; (L14,E87) —
the documented L14 anti-correlate, predicted member of the "negative image"; per-layer
sharpness (max |d|, n experts |d|>1) as a mini flip-onset bracket L13 vs L14 vs L15.
Selection-level: P(E114 in top-8 | fresh) vs | copied) from gen_sel14.
"""
import json, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE / "pulled/convdyn_grid"
OUT  = HERE / "coalition"
OUT.mkdir(exist_ok=True)
BLUE, GRAY, ORANGE, INK, RED = "#2563eb", "#9ca3af", "#ea580c", "#374151", "#dc2626"
N_TURNS, NMAX, COPY_N = 14, 32, 8
LAYERS = [13, 14, 15, 26]

npz  = np.load(ROOT / "scalars.npz")
meta = json.loads((ROOT / "scalars_meta.json").read_text())["meta"]

def ngram_sets(seqs, nmax=NMAX):
    S = [set() for _ in range(nmax + 1)]
    for seq in seqs:
        for n in range(1, nmax + 1):
            if len(seq) < n: break
            s = S[n]
            for i in range(len(seq) - n + 1): s.add(tuple(seq[i:i + n]))
    return S

def longest_suffix(toks, i, S, nmax=NMAX):
    best = 0
    for n in range(1, min(nmax, i + 1) + 1):
        if tuple(toks[i - n + 1:i + 1]) in S[n]: best = n
        else: break
    return best

# ---------------- arm-A per-token copy mask + router logits ----------------
tok_turn, tok_ord, tok_copy, tok_sel14 = [], [], [], []
logits = {L: [] for L in LAYERS}
for o in (1, 2, 3):
    turns = {}
    for t in range(1, N_TURNS + 1):
        rid = f"A_o{o}_t{t:02d}"
        if f"{rid}__gen_logit14" not in npz.files: continue
        n_trim = meta[rid]["n_trim"] or 0
        if n_trim <= 0: continue
        ents = json.loads((ROOT / f"cap_turn{t:02d}" / rid / "generated_tokens.json").read_text())[:n_trim]
        turns[t] = [e["token_id"] for e in ents]
    for t, toks in sorted(turns.items()):
        rid = f"A_o{o}_t{t:02d}"
        n_prompt, n_trim = meta[rid]["n_prompt"], meta[rid]["n_trim"]
        src = ngram_sets([turns[j] for j in range(1, t) if j in turns])
        R = {L: np.load(ROOT / f"cap_turn{t:02d}" / rid / "router" / f"ffn_moe_logits-{L}.npy") for L in LAYERS}
        sel = np.asarray(npz[f"{rid}__gen_sel14"][:n_trim]) if f"{rid}__gen_sel14" in npz.files else np.full(n_trim, np.nan)
        for i in range(len(toks)):
            tok_turn.append(t); tok_ord.append(o)
            tok_copy.append(longest_suffix(toks, i, src) >= COPY_N)
            tok_sel14.append(float(sel[i]))
        for L in LAYERS:
            logits[L].append(R[L][n_prompt:n_prompt + n_trim].astype(np.float64))

tok_turn = np.array(tok_turn); tok_ord = np.array(tok_ord)
tok_copy = np.array(tok_copy, dtype=bool); tok_sel14 = np.array(tok_sel14)
X = {L: np.vstack(logits[L]) for L in LAYERS}          # [n_tokens, 256]
n_tok = len(tok_turn)
assert all(X[L].shape == (n_tok, 256) for L in LAYERS)

def contrast(mask_scope):
    """per-layer per-expert Cohen's d, COPY minus COMPOSE, within mask_scope."""
    out = {}
    mc, mf = mask_scope & tok_copy, mask_scope & ~tok_copy
    for L in LAYERS:
        a, b = X[L][mc], X[L][mf]
        sp = np.sqrt((a.var(0, ddof=1) * (len(a) - 1) + b.var(0, ddof=1) * (len(b) - 1)) / (len(a) + len(b) - 2))
        out[L] = (a.mean(0) - b.mean(0)) / np.maximum(sp, 1e-9)
    return out, int(mc.sum()), int(mf.sum())

d_all,  n_c_all,  n_f_all  = contrast(np.ones(n_tok, dtype=bool))
d_late, n_c_late, n_f_late = contrast(tok_turn >= 5)

def zscore(d_vec, e): return float((d_vec[e] - d_vec.mean()) / d_vec.std())
def rank_of(d_vec, e): return int(np.argsort(d_vec)[::-1].tolist().index(e)) + 1   # 1 = biggest riser

res = dict(n_tokens=n_tok, n_copy=n_c_all, n_compose=n_f_all,
           n_copy_late=n_c_late, n_compose_late=n_f_late, layers=LAYERS)
for tag, D in (("all_turns", d_all), ("late_only", d_late)):
    per_layer = {}
    for L in LAYERS:
        d = D[L]
        order = np.argsort(d)[::-1]
        per_layer[L] = dict(
            top_risers=[[int(e), float(d[e])] for e in order[:10]],
            top_fallers=[[int(e), float(d[e])] for e in order[-10:][::-1]],
            max_abs_d=float(np.abs(d).max()),
            n_abs_d_gt1=int((np.abs(d) > 1).sum()),
            E114=dict(d=float(d[114]), rank_riser=rank_of(d, 114), z=zscore(d, 114)) if L in (13, 14, 15, 26) else None,
            E87=dict(d=float(d[87]), rank_riser=rank_of(d, 87), z=zscore(d, 87)),
        )
    res[tag] = per_layer
res["selection_L14_E114"] = dict(
    p_sel_fresh=float(np.nanmean(tok_sel14[~tok_copy])),
    p_sel_copied=float(np.nanmean(tok_sel14[tok_copy])),
)
(OUT / "coalition.json").write_text(json.dumps(res, indent=1))

# ---------------- figure ----------------
fig, axes = plt.subplots(2, 2, figsize=(13, 9), facecolor="white")
for ax, L in zip(axes.flat, LAYERS):
    d = d_all[L]
    ax.hist(d, bins=60, color=GRAY, alpha=0.8)
    ax.axvline(d[114], color=RED, lw=2, label=f"E114 (d={d[114]:+.2f}, z={zscore(d,114):+.1f})")
    ax.axvline(d[87], color=BLUE, lw=2, ls="--", label=f"E87 (d={d[87]:+.2f})")
    ax.set_title(f"L{L}: per-expert copy-vs-compose Cohen's d (arm A)", color=INK, fontsize=10)
    ax.set_xlabel("d (copy - compose)"); ax.legend(frameon=False, fontsize=8); ax.grid(alpha=0.15)
fig.tight_layout(); fig.savefig(OUT / "coalition.png", dpi=150)

# ---------------- report ----------------
L_ = ["# Copy-coalition contrast (arm A, convdyn grid; post-hoc)", "",
      f"tokens: {n_tok} (copy {n_c_all} / compose {n_f_all}); late-only scope: copy {n_c_late} / compose {n_f_late}",
      "d = Cohen's d of router logit, COPY minus COMPOSE. Positive = rises when copying.", ""]
for tag, D in (("all_turns", d_all), ("late_only (t5-14)", d_late)):
    key = tag.split(" ")[0]
    L_ += [f"## {tag}", ""]
    for Ly in LAYERS:
        info = res[key][Ly]
        L_ += [f"### L{Ly} — max|d| {info['max_abs_d']:.2f}, experts |d|>1: {info['n_abs_d_gt1']}",
               f"- E114: d={info['E114']['d']:+.3f}, riser-rank {info['E114']['rank_riser']}/256, z={info['E114']['z']:+.2f}",
               f"- E87:  d={info['E87']['d']:+.3f}, riser-rank {info['E87']['rank_riser']}/256",
               "- top risers: " + ", ".join(f"E{e}({v:+.2f})" for e, v in info["top_risers"][:6]),
               "- top fallers: " + ", ".join(f"E{e}({v:+.2f})" for e, v in info["top_fallers"][:6]), ""]
s = res["selection_L14_E114"]
L_ += ["## Selection level (L14, E114 in top-8)",
       f"- P(selected | compose) = {s['p_sel_fresh']:.3f} · P(selected | copied) = {s['p_sel_copied']:.3f}", "",
       "Read: 'coalition' = experts with large POSITIVE d (rise during copying). E114 expected among",
       "top fallers. Generic-shift control: if E114's z is modest (|z|<2), its drop is part of a",
       "broad routing shift, not a targeted anti-alignment; if |z|>3 it is an outlier. Late-only",
       "scope controls the turn confound. NOT preregistered; candidates named here get frozen",
       "predictions in the convdyn-T prereg."]
(OUT / "coalition.md").write_text("\n".join(L_) + "\n")
print("\n".join(L_))
