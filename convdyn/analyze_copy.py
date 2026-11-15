#!/usr/bin/env python3
"""analyze_copy.py — per-token copy-predictor regression on the convdyn grid (LOCAL).

Post-hoc mechanism analysis (NOT preregistered — feeds the convdyn-T prereg's mediator
definitions). Question: is the A−B floor collapse absorbed by graded self-copy predictors?

Per generated token (trimmed track only, all arms/orderings/turns):
  max_ngram  — longest suffix n-gram (cap 32) matching anywhere in PRIOR assistant turns
               of the same dialogue (trimmed; probes/user text excluded as source)
  in_copy8   — max_ngram >= 8 (the copy-run flag; threshold matches the planned
               copy-fraction metric)
  self_rep   — longest suffix n-gram matching earlier tokens of the SAME response
  pos_frac   — position within the trimmed response, 0..1

E114 meter = raw router logit at L14 (identical to w114 projection, grid r=1.000000).

Deliverables: copy_regression/copy_regression.{json,md,png}
  1. copy fraction per arm x turn (does A late >> B late?)
  2. E114 vs max_ngram (binned; the graded dose-response)
  3. fresh-vs-copied E114 gap (the "copied prose is colder" number)
  4. THE TEST: A-B floor_a slope raw vs after residualizing E114 on copy predictors
     (per ordering; % of the collapse absorbed)
"""
import json, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE / "pulled/convdyn_grid"
OUT  = HERE / "copy_regression"
OUT.mkdir(exist_ok=True)
BLUE, GRAY, ORANGE, INK = "#2563eb", "#9ca3af", "#ea580c", "#374151"
ARM_COLOR = {"A": BLUE, "B": GRAY, "C": ORANGE}
N_TURNS, NMAX, COPY_N = 14, 32, 8

npz  = np.load(ROOT / "scalars.npz")
meta = json.loads((ROOT / "scalars_meta.json").read_text())["meta"]

def load_turn(arm, o, t):
    rid = f"{arm}_o{o}_t{t:02d}"
    key = f"{rid}__gen_logit14"
    if key not in npz.files: return None, None, None
    n_trim = meta[rid]["n_trim"] or 0
    if n_trim <= 0: return None, None, None
    ents = json.loads((ROOT / f"cap_turn{t:02d}" / rid / "generated_tokens.json").read_text())[:n_trim]
    toks = [e["token_id"] for e in ents]
    entr = np.asarray([e["output_entropy"] for e in ents], dtype=np.float64)
    e114 = np.asarray(npz[key][:n_trim], dtype=np.float64)
    assert len(toks) == len(e114)
    return toks, e114, entr

def ngram_sets(seqs, nmax=NMAX):
    """set-per-n of all n-grams in the source sequences (no cross-sequence grams)."""
    S = [set() for _ in range(nmax + 1)]
    for seq in seqs:
        L = len(seq)
        for n in range(1, nmax + 1):
            if L < n: break
            s = S[n]
            for i in range(L - n + 1):
                s.add(tuple(seq[i:i + n]))
    return S

def longest_suffix(toks, i, S, nmax=NMAX):
    """longest n with toks[i-n+1..i] in S[n] (monotone in n -> early break)."""
    best = 0
    for n in range(1, min(nmax, i + 1) + 1):
        if tuple(toks[i - n + 1:i + 1]) in S[n]: best = n
        else: break
    return best

# ---------------- per-token table ----------------
rows = []   # (arm, o, t, i, pos_frac, max_ngram, self_rep, e114, entropy)
for arm in "ABC":
    for o in (1, 2, 3):
        turns = {}
        for t in range(1, N_TURNS + 1):
            toks, e114, entr = load_turn(arm, o, t)
            if toks is not None: turns[t] = (toks, e114, entr)
        for t, (toks, e114, entr) in sorted(turns.items()):
            src = ngram_sets([turns[j][0] for j in range(1, t) if j in turns])
            selfS = [set() for _ in range(NMAX + 1)]
            L = len(toks)
            for i in range(L):
                mg = longest_suffix(toks, i, src)
                sr = longest_suffix(toks, i, selfS)
                rows.append((arm, o, t, i, i / max(L - 1, 1), mg, sr, e114[i], entr[i]))
                for n in range(1, min(NMAX, i + 1) + 1):        # register grams ending at i
                    selfS[n].add(tuple(toks[i - n + 1:i + 1]))

arm_a  = np.array([r[0] for r in rows])
ord_a  = np.array([r[1] for r in rows])
turn_a = np.array([r[2] for r in rows], dtype=float)
pos_a  = np.array([r[4] for r in rows])
mg_a   = np.array([r[5] for r in rows], dtype=float)
sr_a   = np.array([r[6] for r in rows], dtype=float)
e_a    = np.array([r[7] for r in rows])
ent_a  = np.array([r[8] for r in rows])
copy_a = mg_a >= COPY_N

# ---------------- 1. descriptives: copy fraction per arm x turn ----------------
frac = {a: [float(copy_a[(arm_a == a) & (turn_a == t)].mean()) if ((arm_a == a) & (turn_a == t)).any() else np.nan
            for t in range(1, N_TURNS + 1)] for a in "ABC"}

# ---------------- 2. dose-response: E114 vs max_ngram (arm A) ----------------
bins = [0, 1, 2, 4, 8, 16, 32]
dose = []
mA = arm_a == "A"
for lo, hi in zip(bins[:-1], bins[1:]):
    sel = mA & (mg_a >= lo) & (mg_a < hi)
    dose.append((f"{lo}-{hi-1}", int(sel.sum()), float(e_a[sel].mean()) if sel.any() else np.nan))
sel = mA & (mg_a >= bins[-1]); dose.append((f"{bins[-1]}+", int(sel.sum()), float(e_a[sel].mean()) if sel.any() else np.nan))

# ---------------- 3. fresh vs copied gap ----------------
gap = {}
for a in "ABC":
    for phase, tsel in (("early(t1-4)", turn_a <= 4), ("late(t5-14)", turn_a >= 5)):
        m = (arm_a == a) & tsel
        fr, cp = e_a[m & ~copy_a], e_a[m & copy_a]
        gap[f"{a}_{phase}"] = dict(fresh_mean=float(fr.mean()) if len(fr) else None, n_fresh=int(len(fr)),
                                   copied_mean=float(cp.mean()) if len(cp) else None, n_copied=int(len(cp)))

# ---------------- 4. pooled OLS within arm A + per-ordering betas ----------------
def ols(y, X):
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ b
    r2 = 1 - resid.var() / y.var()
    return b, r2, resid

def design(m):
    return np.column_stack([np.ones(m.sum()), np.log2(1 + mg_a[m]), (sr_a[m] >= COPY_N).astype(float),
                            ent_a[m], pos_a[m], (turn_a[m] - 7.5)])
COLS = ["const", "log2(1+max_ngram)", "self_rep>=8", "output_entropy", "pos_frac", "turn_c"]
bA, r2A, _ = ols(e_a[mA], design(mA))
per_ord = {o: ols(e_a[mA & (ord_a == o)], design(mA & (ord_a == o)))[0].tolist() for o in (1, 2, 3)}

# ---------------- 5. THE TEST: floor slope raw vs copy-residualized ----------------
# copy model fit on A+B pooled (copy effect assumed arm-general), turn/pos NOT in the
# residualizer (they carry the effect under test). Two variants:
#   v1: n-gram overlap terms only (surface copying)
#   v2: + output entropy (decoder-confidence copy signature)
mAB = arm_a != "C"
def residualize(cols_all, cols_fit):
    bfit, _, _ = ols(e_a[mAB], cols_fit)
    return e_a - (cols_all @ bfit - bfit[0]), bfit
X1_all = np.column_stack([np.ones(len(e_a)), np.log2(1 + mg_a), (mg_a >= COPY_N).astype(float), np.log2(1 + sr_a)])
X2_all = np.column_stack([X1_all, ent_a])
e_adj,  bc  = residualize(X1_all, X1_all[mAB])
e_adj2, bc2 = residualize(X2_all, X2_all[mAB])

def floor_slope(evec):
    out = {}
    for o in (1, 2, 3):
        fA, fB = [], []
        for t in range(1, N_TURNS + 1):
            for a, acc in (("A", fA), ("B", fB)):
                m = (arm_a == a) & (ord_a == o) & (turn_a == t)
                idx = np.where(m)[0]
                acc.append(evec[idx[-15:]].mean() if len(idx) >= 15 else (evec[idx].mean() if len(idx) else np.nan))
        d = np.array(fA) - np.array(fB)
        tt = np.arange(1, N_TURNS + 1, dtype=float); mm = np.isfinite(d)
        out[o] = float(np.polyfit(tt[mm], d[mm], 1)[0])
    return out

slope_raw, slope_adj, slope_adj2 = floor_slope(e_a), floor_slope(e_adj), floor_slope(e_adj2)
absorbed  = {o: 1 - slope_adj[o]  / slope_raw[o] if slope_raw[o] else np.nan for o in (1, 2, 3)}
absorbed2 = {o: 1 - slope_adj2[o] / slope_raw[o] if slope_raw[o] else np.nan for o in (1, 2, 3)}

# ---------------- figure ----------------
fig, axes = plt.subplots(2, 2, figsize=(13, 9), facecolor="white")
tx = np.arange(1, N_TURNS + 1)
ax = axes[0, 0]
for a in "ABC": ax.plot(tx, frac[a], "o-", color=ARM_COLOR[a], lw=2, ms=4, label=f"Arm {a}")
ax.set_title("fraction of tokens in a copied run (max_ngram>=8)", color=INK, fontsize=10)
ax.set_xlabel("turn"); ax.legend(frameon=False); ax.grid(alpha=0.15)
ax = axes[0, 1]
labs = [d[0] for d in dose]; vals = [d[2] for d in dose]; ns = [d[1] for d in dose]
ax.plot(range(len(dose)), vals, "o-", color=BLUE, lw=2)
for i, (v, n) in enumerate(zip(vals, ns)):
    if np.isfinite(v): ax.annotate(f"n={n}", (i, v), textcoords="offset points", xytext=(0, 8), fontsize=7, color=INK)
ax.set_xticks(range(len(dose))); ax.set_xticklabels(labs)
ax.set_title("Arm A: mean E114 logit by longest prior-turn n-gram match", color=INK, fontsize=10)
ax.set_xlabel("max_ngram bin"); ax.grid(alpha=0.15)
ax = axes[1, 0]
w = 0.26
ax.bar(np.arange(3) - w, [slope_raw[o] for o in (1, 2, 3)], width=w, color=BLUE, label="raw")
ax.bar(np.arange(3), [slope_adj[o] for o in (1, 2, 3)], width=w, color=ORANGE, label="resid: n-gram")
ax.bar(np.arange(3) + w, [slope_adj2[o] for o in (1, 2, 3)], width=w, color=GRAY, label="resid: n-gram+entropy")
ax.axhline(0, color=INK, lw=0.5); ax.set_xticks(range(3)); ax.set_xticklabels([f"ord {o}" for o in (1, 2, 3)])
ax.set_title("A-B floor_a slope: raw vs copy-residualized", color=INK, fontsize=10)
ax.legend(frameon=False, fontsize=8); ax.grid(alpha=0.15)
ax = axes[1, 1]
rid = "A_o1_t12"; n_trim = meta[rid]["n_trim"]
x = np.asarray(npz[f"{rid}__gen_logit14"][:n_trim])
m12 = (arm_a == "A") & (ord_a == 1) & (turn_a == 12)
cmask = copy_a[np.where(m12)[0]]
ax.plot(x, color=GRAY, lw=1.0)
ax.scatter(np.where(cmask)[0], x[cmask], s=12, color=ORANGE, label="copied (>=8-gram)", zorder=3)
ax.scatter(np.where(~cmask)[0], x[~cmask], s=12, color=BLUE, label="fresh", zorder=3)
ax.set_title("A_o1 turn 12 per-token E114, copy mask overlaid", color=INK, fontsize=10)
ax.set_xlabel("response token"); ax.legend(frameon=False, fontsize=8); ax.grid(alpha=0.15)
fig.tight_layout(); fig.savefig(OUT / "copy_regression.png", dpi=150)

# ---------------- outputs ----------------
res = dict(
    n_tokens=len(rows), copy_threshold=COPY_N, ngram_cap=NMAX,
    copy_frac_by_arm_turn=frac, dose_response=dose, fresh_copied_gap=gap,
    ols_armA=dict(cols=COLS, beta=bA.tolist(), r2=float(r2A), per_ordering_beta=per_ord),
    copy_residualizer_v1=dict(cols=["const", "log2(1+max_ngram)", "in_copy8", "log2(1+self_rep)"], beta=bc.tolist()),
    copy_residualizer_v2=dict(cols=["const", "log2(1+max_ngram)", "in_copy8", "log2(1+self_rep)", "output_entropy"], beta=bc2.tolist()),
    floor_slope_raw=slope_raw, floor_slope_adj_v1=slope_adj, floor_slope_adj_v2=slope_adj2,
    fraction_absorbed_v1=absorbed, fraction_absorbed_v2=absorbed2,
)
(OUT / "copy_regression.json").write_text(json.dumps(res, indent=1))

L = ["# Copy regression on the convdyn grid (post-hoc; feeds convdyn-T prereg)", "",
     f"tokens analysed: {len(rows)} (trimmed gen track, arms A/B/C x 3 orderings x 14 turns)",
     f"copy flag: longest prior-ASSISTANT-turn n-gram match >= {COPY_N} (cap {NMAX}); source excludes probes/user text and spill", "",
     "## Copy fraction (arm A vs B, by turn)", "",
     "| turn | " + " | ".join(str(t) for t in tx) + " |", "|---|" + "---|" * N_TURNS,
     "| A | " + " | ".join(f"{v:.2f}" for v in frac["A"]) + " |",
     "| B | " + " | ".join(f"{v:.2f}" for v in frac["B"]) + " |",
     "| C | " + " | ".join(f"{v:.2f}" for v in frac["C"]) + " |", "",
     "## Dose-response (arm A): mean E114 by max_ngram bin", "",
     "| bin | n | mean E114 |", "|---|---|---|"]
for lab, n, v in dose: L.append(f"| {lab} | {n} | {v:+.3f} |" if np.isfinite(v) else f"| {lab} | {n} | — |")
L += ["", "## Fresh vs copied mean E114", "", "| cell | fresh (n) | copied (n) | gap |", "|---|---|---|---|"]
for k, g in gap.items():
    fm, cm = g["fresh_mean"], g["copied_mean"]
    gp = (fm - cm) if (fm is not None and cm is not None) else None
    L.append(f"| {k} | {fm:+.3f} ({g['n_fresh']}) | " + (f"{cm:+.3f} ({g['n_copied']})" if cm is not None else f"— ({g['n_copied']})")
             + " | " + (f"{gp:+.3f}" if gp is not None else "—") + " |")
L += ["", "## Pooled OLS, arm A (E114 ~ copy + position + turn)", "",
      "| term | beta (pooled) | ord1 | ord2 | ord3 |", "|---|---|---|---|---|"]
for i, c in enumerate(COLS):
    L.append(f"| {c} | {bA[i]:+.4f} | " + " | ".join(f"{per_ord[o][i]:+.4f}" for o in (1, 2, 3)) + " |")
L += [f"", f"pooled R^2 = {r2A:.3f}", "",
      "## THE TEST — A-B floor_a slope, raw vs copy-residualized", "",
      "| ordering | raw | adj v1 (n-gram) | absorbed v1 | adj v2 (+entropy) | absorbed v2 |", "|---|---|---|---|---|---|"]
for o in (1, 2, 3):
    L.append(f"| {o} | {slope_raw[o]:+.4f} | {slope_adj[o]:+.4f} | {absorbed[o]:.0%} | {slope_adj2[o]:+.4f} | {absorbed2[o]:.0%} |")
L += ["", "Interpretation rule (stated before running): if the adjusted slope loses most of its magnitude",
      "and its 3/3 sign consistency, the floor collapse is carried by the copy predictors ->",
      "mechanism = generation route (self-copy), not register fatigue. Residualizer deliberately",
      "excludes turn/position (they carry the effect under test).",
      "", "NOT preregistered; descriptive. Thresholds here calibrate the convdyn-T prereg mediator."]
(OUT / "copy_regression.md").write_text("\n".join(L) + "\n")
print("\n".join(L[:40]))
print("...")
print(f"\nwrote {OUT}/copy_regression.json .md .png")
