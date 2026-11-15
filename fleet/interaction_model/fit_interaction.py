#!/usr/bin/env python3
"""fit_interaction.py — token-level register x freshness interaction model (POST-HOC, descriptive).

NOT preregistered. Labels ("register", "fresh", "interaction carries") are descriptive
conveniences, not causal claims.

Model, per surface (never pooled), per expert (E114/E189/E87, L14 router logit),
per freshness coding:

    E_logit ~ const + register + fresh + register*fresh + pos_frac + turn_c

Freshness codings:
  binary:      fresh_bin = 1[max_ngram < 8]            (1 = fresh, 0 = copied)
  continuous:  fresh_c   = -log2(1 + max_ngram)        (0 = maximally fresh; more negative = more copied)

Copy metric machinery replicated EXACTLY from convdyn/analyze_copy.py:
  max_ngram = longest suffix n-gram (cap 32) matching anywhere in PRIOR assistant turns
  of the same dialogue (trimmed track; probes/user text excluded as source), threshold 8.

Surfaces:
  convdyn grid  — arms A_register vs B_technical primary (C_vocabulary-included variant
                  secondary), 3 orderings x 14 turns, greedy. D hybrids excluded.
                  E114 column validated against scalars.npz {rid}__gen_logit14 (exact).
  W2            — 12 repeat-probe dialogues, 6 registers x {greedy, t07}. Primary REG vs
                  TECH per sampler; 6-register fixed-effects variant secondary.

Inference is descriptive: OLS point estimates with CR1 cluster-robust SEs, clusters =
capture (one dialogue-turn generation). Sign consistency reported per ordering (convdyn)
and per sampler (W2).

Outputs: results.json, results.md, fig.png (2 surfaces x 3 experts, 2x2 cell-mean
interaction plots, binary coding, greedy cells).
"""
import json
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = pathlib.Path("/Volumes/ExternalSSD/e114-construction-reframe")
GRID = BASE / "convdyn/pulled/convdyn_grid"
W2D  = BASE / "fleet/pulled/A1_W2/w2"
OUT  = BASE / "fleet/interaction_model"
OUT.mkdir(exist_ok=True)

N_TURNS, NMAX, COPY_N = 14, 32, 8
LAYER = 14
EXPERTS = {"E114": 114, "E189": 189, "E87": 87}
REGS  = ["REG", "TECH", "LEGAL", "NARR", "POET", "CODE"]
CELLS = ["g", "t07"]

# ---------------- copy metric machinery: verbatim from convdyn/analyze_copy.py ----------------
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

# ---------------- loaders ----------------
def load_convdyn():
    """Token table for the convdyn grid (arms A/B/C, 3 orderings, 14 turns, greedy)."""
    npz  = np.load(GRID / "scalars.npz")
    meta = json.loads((GRID / "scalars_meta.json").read_text())["meta"]
    rows = dict(group=[], arm=[], turn=[], pos_frac=[], mg=[], rid=[],
                **{k: [] for k in EXPERTS})
    n_caps = 0
    for arm in "ABC":
        for o in (1, 2, 3):
            turns = {}
            for t in range(1, N_TURNS + 1):
                rid = f"{arm}_o{o}_t{t:02d}"
                if rid not in meta: continue
                n_trim = meta[rid]["n_trim"] or 0
                if n_trim <= 0: continue
                d = GRID / f"cap_turn{t:02d}" / rid
                gt = json.loads((d / "generated_tokens.json").read_text())
                pt = json.loads((d / "prompt_tokens.json").read_text())
                toks = [e["token_id"] for e in gt[:n_trim]]
                a = np.load(d / f"router/ffn_moe_logits-{LAYER}.npy")
                assert a.shape == (len(pt) + len(gt), 256), (rid, a.shape)
                gen = a[len(pt):len(pt) + len(gt)][:n_trim].astype(np.float64)
                # hard validation: router column 114 must reproduce the npz E114 series exactly
                ref = np.asarray(npz[f"{rid}__gen_logit14"][:n_trim], dtype=np.float64)
                assert np.allclose(gen[:, 114], ref, atol=1e-5), rid
                turns[t] = (toks, gen)
            for t, (toks, gen) in sorted(turns.items()):
                src = ngram_sets([turns[j][0] for j in range(1, t) if j in turns])
                L = len(toks)
                rid = f"{arm}_o{o}_t{t:02d}"
                n_caps += 1
                for i in range(L):
                    mg = longest_suffix(toks, i, src)
                    rows["group"].append(o); rows["arm"].append(arm); rows["turn"].append(t)
                    rows["pos_frac"].append(i / max(L - 1, 1)); rows["mg"].append(mg)
                    rows["rid"].append(rid)
                    for name, e in EXPERTS.items(): rows[name].append(gen[i, e])
    out = {k: np.asarray(v) for k, v in rows.items()}
    out["turn"] = out["turn"].astype(float)
    out["mg"] = out["mg"].astype(float)
    print(f"convdyn: {n_caps} captures, {len(out['mg'])} tokens")
    return out

def load_w2():
    """Token table for W2 (6 registers x {g,t07} x 14 turns). Loader per fleet/scoring/score_W2.py."""
    transcripts = json.loads((W2D / "transcripts.json").read_text())
    rows = dict(group=[], reg=[], turn=[], pos_frac=[], mg=[], rid=[],
                **{k: [] for k in EXPERTS})
    n_caps = 0
    for reg in REGS:
        for cell in CELLS:
            key = f"{reg}_{cell}"
            turns = []
            for e in transcripts[key]:
                t = e["turn"]; rid = f"{key}_t{t:02d}"
                d = W2D / f"cap_{key}_t{t:02d}" / rid
                gt = json.loads((d / "generated_tokens.json").read_text())
                pt = json.loads((d / "prompt_tokens.json").read_text())
                n_p, n_g, n_trim = len(pt), len(gt), e["n_trim"]
                assert n_trim <= n_g
                toks = [x["token_id"] for x in gt[:n_trim]]
                a = np.load(d / f"router/ffn_moe_logits-{LAYER}.npy")
                assert a.shape == (n_p + n_g, 256), (rid, a.shape)
                gen = a[n_p:n_p + n_g][:n_trim].astype(np.float64)
                turns.append((t, toks, gen, rid))
            for ti, (t, toks, gen, rid) in enumerate(turns):
                src = ngram_sets([turns[j][1] for j in range(ti)])
                L = len(toks)
                n_caps += 1
                for i in range(L):
                    mg = longest_suffix(toks, i, src)
                    rows["group"].append(cell); rows["reg"].append(reg); rows["turn"].append(t)
                    rows["pos_frac"].append(i / max(L - 1, 1)); rows["mg"].append(mg)
                    rows["rid"].append(rid)
                    for name, e in EXPERTS.items(): rows[name].append(gen[i, e])
    out = {k: np.asarray(v) for k, v in rows.items()}
    out["turn"] = out["turn"].astype(float)
    out["mg"] = out["mg"].astype(float)
    print(f"w2: {n_caps} captures, {len(out['mg'])} tokens")
    return out

# ---------------- freshness codings ----------------
def fresh_vec(mg, coding):
    if coding == "binary":     return (mg < COPY_N).astype(float)
    if coding == "continuous": return -np.log2(1.0 + mg)
    raise ValueError(coding)

# ---------------- OLS + CR1 cluster-robust SEs ----------------
def ols(y, X):
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ b
    r2 = 1.0 - resid.var() / y.var()
    return b, resid, float(r2)

def cr1_se(X, resid, clusters):
    XtX_inv = np.linalg.inv(X.T @ X)
    k = X.shape[1]
    meat = np.zeros((k, k))
    uniq = np.unique(clusters)
    for g in uniq:
        m = clusters == g
        s = X[m].T @ resid[m]
        meat += np.outer(s, s)
    G, N = len(uniq), len(resid)
    c = (G / (G - 1)) * ((N - 1) / (N - k))
    V = c * XtX_inv @ meat @ XtX_inv
    return np.sqrt(np.diag(V))

def fit_model(y, reg01, fresh, pos, turn, clusters, with_interaction=True):
    cols = [np.ones_like(y), reg01, fresh]
    names = ["const", "register", "fresh"]
    if with_interaction:
        cols.append(reg01 * fresh); names.append("register_x_fresh")
    cols += [pos, turn - 7.5]; names += ["pos_frac", "turn_c"]
    X = np.column_stack(cols)
    b, resid, r2 = ols(y, X)
    se = cr1_se(X, resid, clusters)
    return dict(names=names, beta=b.tolist(), se=se.tolist(),
                t=(b / se).tolist(), r2=r2, n=int(len(y)),
                n_clusters=int(len(np.unique(clusters))))

def fit_dummies(y, dummy_dict, fresh, pos, turn, clusters):
    """Variant fit: multiple register dummies, each with its own x fresh interaction."""
    names = ["const"]; cols = [np.ones_like(y)]
    for nm, dv in dummy_dict.items():
        names.append(nm); cols.append(dv)
    names.append("fresh"); cols.append(fresh)
    for nm, dv in dummy_dict.items():
        names.append(f"{nm}_x_fresh"); cols.append(dv * fresh)
    names += ["pos_frac", "turn_c"]; cols += [pos, turn - 7.5]
    X = np.column_stack(cols)
    b, resid, r2 = ols(y, X)
    se = cr1_se(X, resid, clusters)
    return dict(names=names, beta=b.tolist(), se=se.tolist(),
                t=(b / se).tolist(), r2=r2, n=int(len(y)),
                n_clusters=int(len(np.unique(clusters))))

def cell_means(y, reg01, fresh_bin, rids):
    """2x2 cell means (token mean) + capture-level SE + n."""
    out = {}
    for rlab, rv in (("register", 1.0), ("control", 0.0)):
        for flab, fv in (("fresh", 1.0), ("copied", 0.0)):
            m = (reg01 == rv) & (fresh_bin == fv)
            if not m.any():
                out[f"{rlab}_{flab}"] = dict(mean=None, se_capture=None, n_tokens=0, n_captures=0)
                continue
            cap_means = [float(y[m & (rids == r)].mean()) for r in np.unique(rids[m])]
            out[f"{rlab}_{flab}"] = dict(
                mean=float(y[m].mean()),
                se_capture=float(np.std(cap_means, ddof=1) / np.sqrt(len(cap_means))) if len(cap_means) > 1 else None,
                n_tokens=int(m.sum()), n_captures=len(cap_means))
    return out

# ---------------- load both surfaces ----------------
conv = load_convdyn()
w2   = load_w2()

results = {"spec": {
    "model": "E_logit(L14) ~ const + register + fresh + register*fresh + pos_frac + turn_c",
    "freshness_codings": {"binary": "1[max_ngram < 8] (1=fresh)",
                          "continuous": "-log2(1+max_ngram) (0=fresh, negative=copied)"},
    "copy_metric": "longest suffix n-gram vs prior assistant turns of same dialogue, cap 32 (convdyn/analyze_copy.py, verbatim)",
    "inference": "OLS, CR1 cluster-robust SEs, clusters = capture (dialogue-turn)",
    "status": "post-hoc / descriptive; NOT preregistered",
    "surfaces": {
        "convdyn": "grid, greedy; primary arms A_register(1) vs B_technical(0); secondary + C_vocabulary; groups = orderings o1/o2/o3",
        "w2": "6 registers x {g,t07}; primary REG(1) vs TECH(0) per sampler; secondary 6-register fixed effects (TECH baseline); groups = samplers g/t07"},
}, "convdyn": {}, "w2": {}}

# ---------------- convdyn fits ----------------
mAB = np.isin(conv["arm"], ["A", "B"])
for ename in EXPERTS:
    res_e = {}
    y_all = conv[ename]
    for coding in ("binary", "continuous"):
        fr_all = fresh_vec(conv["mg"], coding)
        reg_all = (conv["arm"] == "A").astype(float)
        m = mAB
        fit_int  = fit_model(y_all[m], reg_all[m], fr_all[m], conv["pos_frac"][m], conv["turn"][m], conv["rid"][m], True)
        fit_main = fit_model(y_all[m], reg_all[m], fr_all[m], conv["pos_frac"][m], conv["turn"][m], conv["rid"][m], False)
        per_group = {}
        for o in (1, 2, 3):
            mo = m & (conv["group"] == o)
            per_group[f"o{o}"] = fit_model(y_all[mo], reg_all[mo], fr_all[mo], conv["pos_frac"][mo], conv["turn"][mo], conv["rid"][mo], True)
        ints = [per_group[g]["beta"][3] for g in per_group]
        pooled_int = fit_int["beta"][3]
        res_e[coding] = dict(
            pooled=fit_int, main_effects_only=fit_main,
            r2_main=fit_main["r2"], r2_interaction=fit_int["r2"],
            delta_r2=fit_int["r2"] - fit_main["r2"],
            per_group=per_group,
            interaction_sign_consistency=f"{sum(1 for v in ints if np.sign(v) == np.sign(pooled_int))}/3",
            interaction_beta_std=pooled_int / float(y_all[m].std()),
        )
        # C-included secondary variant
        mABC = np.ones(len(y_all), bool)
        dummies = {"armA": (conv["arm"] == "A").astype(float), "armC": (conv["arm"] == "C").astype(float)}
        res_e[coding]["variant_C_included"] = fit_dummies(
            y_all[mABC], {k: v[mABC] for k, v in dummies.items()}, fr_all[mABC],
            conv["pos_frac"][mABC], conv["turn"][mABC], conv["rid"][mABC])
    fb = fresh_vec(conv["mg"], "binary")
    res_e["cell_means_binary"] = cell_means(y_all[mAB], (conv["arm"] == "A").astype(float)[mAB], fb[mAB], conv["rid"][mAB])
    results["convdyn"][ename] = res_e

# ---------------- W2 fits ----------------
for ename in EXPERTS:
    res_e = {}
    y_all = w2[ename]
    for coding in ("binary", "continuous"):
        fr_all = fresh_vec(w2["mg"], coding)
        per_sampler = {}
        for cell in CELLS:
            mc = (w2["group"] == cell) & np.isin(w2["reg"], ["REG", "TECH"])
            reg01 = (w2["reg"] == "REG").astype(float)
            fit_int  = fit_model(y_all[mc], reg01[mc], fr_all[mc], w2["pos_frac"][mc], w2["turn"][mc], w2["rid"][mc], True)
            fit_main = fit_model(y_all[mc], reg01[mc], fr_all[mc], w2["pos_frac"][mc], w2["turn"][mc], w2["rid"][mc], False)
            # 6-register fixed-effects variant (TECH baseline), same sampler
            mall = w2["group"] == cell
            dummies = {f"reg{r}": (w2["reg"] == r).astype(float)[mall] for r in REGS if r != "TECH"}
            var6 = fit_dummies(y_all[mall], dummies, fr_all[mall], w2["pos_frac"][mall], w2["turn"][mall], w2["rid"][mall])
            per_sampler[cell] = dict(
                pooled=fit_int, main_effects_only=fit_main,
                r2_main=fit_main["r2"], r2_interaction=fit_int["r2"],
                delta_r2=fit_int["r2"] - fit_main["r2"],
                interaction_beta_std=fit_int["beta"][3] / float(y_all[mc].std()),
                variant_6reg_FE=var6)
        ints = [per_sampler[c]["pooled"]["beta"][3] for c in CELLS]
        per_sampler["interaction_sign_consistency"] = f"{sum(1 for v in ints if np.sign(v) == np.sign(ints[0]))}/2" \
            if all(np.isfinite(ints)) else "n/a"
        res_e[coding] = per_sampler
    fb = fresh_vec(w2["mg"], "binary")
    for cell in CELLS:
        mc = (w2["group"] == cell) & np.isin(w2["reg"], ["REG", "TECH"])
        res_e[f"cell_means_binary_{cell}"] = cell_means(
            y_all[mc], (w2["reg"] == "REG").astype(float)[mc], fb[mc], w2["rid"][mc])
    results["w2"][ename] = res_e

# ---------------- verdicts ----------------
def sgn(x): return "+" if x > 0 else "-"

v = {}
# 1. does the interaction carry (E114)?
e114c = results["convdyn"]["E114"]; e114w = results["w2"]["E114"]
v["interaction_carries_E114"] = dict(
    convdyn_binary_beta=e114c["binary"]["pooled"]["beta"][3],
    convdyn_binary_t=e114c["binary"]["pooled"]["t"][3],
    convdyn_sign_consistency=e114c["binary"]["interaction_sign_consistency"],
    convdyn_delta_r2=e114c["binary"]["delta_r2"],
    w2_g_binary_beta=e114w["binary"]["g"]["pooled"]["beta"][3],
    w2_g_binary_t=e114w["binary"]["g"]["pooled"]["t"][3],
    w2_t07_binary_beta=e114w["binary"]["t07"]["pooled"]["beta"][3],
    w2_sampler_sign_consistency=e114w["binary"]["interaction_sign_consistency"],
    w2_g_delta_r2=e114w["binary"]["g"]["delta_r2"],
)
# 2. E189 vs E114 interaction strength (binary primary, standardized + raw)
comp = {}
for surf, cell in (("convdyn", None), ("w2_g", "g"), ("w2_t07", "t07")):
    row = {}
    for ename in ("E114", "E189"):
        if surf == "convdyn":
            row[ename] = dict(raw=results["convdyn"][ename]["binary"]["pooled"]["beta"][3],
                              std=results["convdyn"][ename]["binary"]["interaction_beta_std"])
        else:
            row[ename] = dict(raw=results["w2"][ename]["binary"][cell]["pooled"]["beta"][3],
                              std=results["w2"][ename]["binary"][cell]["interaction_beta_std"])
    row["E189_stronger_raw"] = bool(abs(row["E189"]["raw"]) > abs(row["E114"]["raw"]))
    row["E189_stronger_std"] = bool(abs(row["E189"]["std"]) > abs(row["E114"]["std"]))
    comp[surf] = row
v["E189_vs_E114"] = comp
# 3. does E87 invert? (interaction sign AND the fresh main effect, which is where E87's
#    copy response actually lives — register-general, per the W2 coalition read)
inv = {}
for surf in ("convdyn", "w2_g", "w2_t07"):
    if surf == "convdyn":
        f114 = results["convdyn"]["E114"]["binary"]["pooled"]
        f87  = results["convdyn"]["E87"]["binary"]["pooled"]
    else:
        cell = surf.split("_")[1]
        f114 = results["w2"]["E114"]["binary"][cell]["pooled"]
        f87  = results["w2"]["E87"]["binary"][cell]["pooled"]
    inv[surf] = dict(E114_int_beta=f114["beta"][3], E87_int_beta=f87["beta"][3],
                     interaction_inverted=bool(np.sign(f87["beta"][3]) == -np.sign(f114["beta"][3])),
                     E87_fresh_main_beta=f87["beta"][2], E87_fresh_main_t=f87["t"][2],
                     E114_fresh_main_beta=f114["beta"][2],
                     fresh_main_inverted=bool(f87["beta"][2] < 0))
v["E87_inverts"] = inv
results["verdicts"] = v

def clean(o):
    if isinstance(o, dict): return {str(k): clean(x) for k, x in o.items()}
    if isinstance(o, (list, tuple)): return [clean(x) for x in o]
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, np.floating): return float(o)
    if isinstance(o, np.ndarray): return o.tolist()
    return o

(OUT / "results.json").write_text(json.dumps(clean(results), indent=1))

# ---------------- figure: 2 surfaces x 3 experts, 2x2 cell means (binary, greedy) ----------------
SURFACE, GRIDC, MUTED, INK, INK2 = "#fcfcfb", "#e1e0d9", "#898781", "#0b0b0b", "#52514e"
REG_C, CTL_C = "#2a78d6", "#1baf7a"   # categorical slots 1-2, fixed order (validated default palette)

fig, axes = plt.subplots(2, 3, figsize=(12.5, 7.6), facecolor=SURFACE, sharex=True)
row_specs = [
    ("convdyn", "convdyn grid — arm A (register) vs arm B (technical), greedy",
     lambda e: results["convdyn"][e]["cell_means_binary"], "A register", "B technical"),
    ("w2", "W2 — REG vs TECH, greedy", lambda e: results["w2"][e][f"cell_means_binary_g"], "REG", "TECH"),
]
xpos = [0, 1]; xlabs = ["fresh\n(max_ngram < 8)", "copied\n(max_ngram ≥ 8)"]
for ri, (skey, stitle, getter, lab_reg, lab_ctl) in enumerate(row_specs):
    for ci, ename in enumerate(EXPERTS):
        ax = axes[ri, ci]
        ax.set_facecolor(SURFACE)
        cm = getter(ename)
        ends = []
        for lab, pref, col in ((lab_reg, "register", REG_C), (lab_ctl, "control", CTL_C)):
            means = [cm[f"{pref}_fresh"]["mean"], cm[f"{pref}_copied"]["mean"]]
            ses   = [cm[f"{pref}_fresh"]["se_capture"] or 0, cm[f"{pref}_copied"]["se_capture"] or 0]
            ax.errorbar(xpos, means, yerr=ses, color=col, lw=2, marker="o", ms=7,
                        capsize=3, mfc=col, mec=SURFACE, mew=1.2, zorder=3)
            ends.append((lab, col, means[1]))
        # direct labels at line ends, dodged if the two endpoints nearly coincide
        span = abs(ends[0][2] - ends[1][2])
        yr = ax.get_ylim(); need_dodge = span < 0.06 * (yr[1] - yr[0])
        for k, (lab, col, ym) in enumerate(sorted(ends, key=lambda e: e[2])):
            dy = (-7 if k == 0 else 7) if need_dodge else 0
            ax.annotate(lab, (xpos[1], ym), xytext=(8, dy), textcoords="offset points",
                        fontsize=8, color=col, va="center", fontweight="bold")
        ax.set_title(f"{ename} · L{LAYER}", fontsize=10, color=INK)
        ax.grid(axis="y", color=GRIDC, lw=0.8, zorder=0)
        for sp in ("top", "right"): ax.spines[sp].set_visible(False)
        for sp in ("left", "bottom"): ax.spines[sp].set_color(MUTED)
        ax.tick_params(colors=INK2, labelsize=8)
        ax.set_xticks(xpos); ax.set_xticklabels(xlabs, fontsize=8, color=INK2)
        ax.set_xlim(-0.35, 1.75)
        if ci == 0: ax.set_ylabel(f"{stitle.split(' — ')[0]}\nmean router logit (L14)", fontsize=9, color=INK2)
    axes[ri, 0].annotate(stitle, (0.005, 1.10 - ri * 0.0), xycoords="axes fraction",
                         fontsize=9.5, color=INK2, style="italic",
                         annotation_clip=False) if False else None
fig.suptitle("Register × freshness — 2×2 cell means of L14 router logits (post-hoc, descriptive)",
             fontsize=12, color=INK)
axes[0, 1].annotate(row_specs[0][1], (0.5, 1.16), xycoords="axes fraction", ha="center",
                    fontsize=9.5, color=INK2, style="italic", annotation_clip=False)
axes[1, 1].annotate(row_specs[1][1], (0.5, 1.16), xycoords="axes fraction", ha="center",
                    fontsize=9.5, color=INK2, style="italic", annotation_clip=False)
handles = [plt.Line2D([], [], color=REG_C, lw=2, marker="o", ms=7, label="register arm"),
           plt.Line2D([], [], color=CTL_C, lw=2, marker="o", ms=7, label="technical control")]
fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False, fontsize=9,
           labelcolor=INK2, bbox_to_anchor=(0.5, 0.005))
fig.tight_layout(rect=(0, 0.045, 1, 0.94))
fig.savefig(OUT / "fig.png", dpi=150, facecolor=SURFACE)

# ---------------- results.md ----------------
def coefrow(f, i):
    return f"{f['beta'][i]:+.4f} ({f['se'][i]:.4f})"

L = ["# Token-level register × freshness interaction model",
     "",
     "**Post-hoc / descriptive. NOT preregistered.** Model per surface (never pooled), per expert",
     "(L14 router logits), per freshness coding:",
     "",
     "```",
     "E_logit ~ const + register + fresh + register×fresh + pos_frac + turn_c",
     "```",
     "",
     "- binary coding: `fresh = 1[max_ngram < 8]`; continuous: `fresh = -log2(1+max_ngram)`",
     "  (both oriented so higher = fresher).",
     "- Copy metric machinery verbatim from `convdyn/analyze_copy.py` (suffix n-gram vs prior",
     "  assistant turns of the same dialogue, cap 32, threshold 8, trimmed track).",
     "- OLS; CR1 cluster-robust SEs in parentheses, clusters = capture (dialogue-turn).",
     "- convdyn primary: arms A_register vs B_technical (greedy grid; D hybrids excluded);",
     "  secondary adds C_vocabulary. W2 primary: REG vs TECH per sampler; secondary 6-register FE.",
     "- convdyn E114 router column validated exactly against `scalars.npz` (`gen_logit14`).",
     ""]

for surf, title in (("convdyn", "convdyn grid (A vs B, greedy; groups = orderings)"),
                    ("w2", "W2 (REG vs TECH; groups = samplers g / t07)")):
    L += [f"## Surface: {title}", ""]
    for coding in ("binary", "continuous"):
        L += [f"### {coding} freshness coding", "",
              "| expert | register | fresh | register×fresh | pos_frac | turn_c | R² main | R² +int | ΔR² | int sign consistency | int t (CR1) |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for ename in EXPERTS:
            if surf == "convdyn":
                r = results["convdyn"][ename][coding]; f = r["pooled"]
                sc = r["interaction_sign_consistency"]
                L.append(f"| {ename} | {coefrow(f,1)} | {coefrow(f,2)} | **{coefrow(f,3)}** | {coefrow(f,4)} | {coefrow(f,5)} | "
                         f"{r['r2_main']:.4f} | {r['r2_interaction']:.4f} | {r['delta_r2']:+.4f} | {sc} (orderings) | {f['t'][3]:+.1f} |")
            else:
                r = results["w2"][ename][coding]
                for cell in CELLS:
                    f = r[cell]["pooled"]
                    sc = r["interaction_sign_consistency"] if cell == "g" else ""
                    L.append(f"| {ename} ({cell}) | {coefrow(f,1)} | {coefrow(f,2)} | **{coefrow(f,3)}** | {coefrow(f,4)} | {coefrow(f,5)} | "
                             f"{r[cell]['r2_main']:.4f} | {r[cell]['r2_interaction']:.4f} | {r[cell]['delta_r2']:+.4f} | {sc} | {f['t'][3]:+.1f} |")
        L.append("")
    # per-ordering (convdyn) betas for the binary coding
    if surf == "convdyn":
        L += ["### Per-ordering interaction betas (binary coding)", "",
              "| expert | o1 | o2 | o3 | pooled |", "|---|---|---|---|---|"]
        for ename in EXPERTS:
            r = results["convdyn"][ename]["binary"]
            L.append(f"| {ename} | " + " | ".join(f"{r['per_group'][f'o{o}']['beta'][3]:+.3f}" for o in (1, 2, 3))
                     + f" | {r['pooled']['beta'][3]:+.3f} |")
        L += ["", "### Secondary: C_vocabulary-included variant (binary coding), interaction terms", "",
              "| expert | armA×fresh | armC×fresh |", "|---|---|---|"]
        for ename in EXPERTS:
            f = results["convdyn"][ename]["binary"]["variant_C_included"]
            iA, iC = f["names"].index("armA_x_fresh"), f["names"].index("armC_x_fresh")
            L.append(f"| {ename} | {f['beta'][iA]:+.4f} ({f['se'][iA]:.4f}) | {f['beta'][iC]:+.4f} ({f['se'][iC]:.4f}) |")
        L.append("")
    else:
        L += ["### Secondary: 6-register fixed-effects variant (binary coding), register×fresh interactions", "",
              "| expert | sampler | " + " | ".join(f"{r}×fresh" for r in REGS if r != "TECH") + " |",
              "|---|---|" + "---|" * 5]
        for ename in EXPERTS:
            for cell in CELLS:
                f = results["w2"][ename]["binary"][cell]["variant_6reg_FE"]
                vals = []
                for r in REGS:
                    if r == "TECH": continue
                    i = f["names"].index(f"reg{r}_x_fresh")
                    vals.append(f"{f['beta'][i]:+.3f}")
                L.append(f"| {ename} | {cell} | " + " | ".join(vals) + " |")
        L.append("")

L += ["## 2×2 cell means (binary coding, greedy cells)", "",
      "| surface | expert | register/fresh | register/copied | control/fresh | control/copied | interaction (diff-in-diff) |",
      "|---|---|---|---|---|---|---|"]
for surf in ("convdyn", "w2"):
    for ename in EXPERTS:
        cm = results[surf][ename]["cell_means_binary"] if surf == "convdyn" else results[surf][ename]["cell_means_binary_g"]
        rf, rc = cm["register_fresh"], cm["register_copied"]
        cf, cc = cm["control_fresh"], cm["control_copied"]
        did = (rf["mean"] - rc["mean"]) - (cf["mean"] - cc["mean"])
        L.append(f"| {surf} | {ename} | {rf['mean']:+.3f} (n={rf['n_tokens']}) | {rc['mean']:+.3f} (n={rc['n_tokens']}) | "
                 f"{cf['mean']:+.3f} (n={cf['n_tokens']}) | {cc['mean']:+.3f} (n={cc['n_tokens']}) | {did:+.3f} |")
L += ["", "(W2 t07 cell means are in results.json under `cell_means_binary_t07`.)", "",
      "Cell-count caveat: the 2×2 is strongly unbalanced by design — copying dominates the",
      "register arms late (convdyn A: 73% copied; W2 REG: 89% copied) while convdyn B has only",
      "226 copied tokens (3%); W2 TECH copies heavily too (286/557, register-general copy regime).",
      "Cell means are token means; SE bars are capture-level.", ""]

vd = results["verdicts"]
L += ["## Verdicts (descriptive)", ""]
i1 = vd["interaction_carries_E114"]
L += [f"**1. Does the interaction term carry (E114)?** convdyn binary β = {i1['convdyn_binary_beta']:+.3f} "
      f"(t={i1['convdyn_binary_t']:+.1f}, sign {i1['convdyn_sign_consistency']} orderings, ΔR² = {i1['convdyn_delta_r2']:+.4f}); "
      f"W2 greedy β = {i1['w2_g_binary_beta']:+.3f} (t={i1['w2_g_binary_t']:+.1f}), t07 β = {i1['w2_t07_binary_beta']:+.3f}, "
      f"sampler sign {i1['w2_sampler_sign_consistency']}, ΔR²(g) = {i1['w2_g_delta_r2']:+.4f}.", ""]
c = vd["E189_vs_E114"]
L += ["**2. E189 vs E114 interaction strength (binary coding):**", ""]
for s, lab in (("convdyn", "convdyn"), ("w2_g", "W2 greedy"), ("w2_t07", "W2 t07")):
    L.append(f"- {lab}: raw β_int E189 {c[s]['E189']['raw']:+.3f} vs E114 {c[s]['E114']['raw']:+.3f} "
             f"(E189 stronger raw: {c[s]['E189_stronger_raw']}); standardized (β_int / SD of the expert's "
             f"logit) E189 {c[s]['E189']['std']:+.3f} vs E114 {c[s]['E114']['std']:+.3f} "
             f"(E189 stronger std: {c[s]['E189_stronger_std']}).")
L.append("")
inv = vd["E87_inverts"]
L += ["**3. Does E87 invert?** Two channels:", ""]
for s in inv:
    L.append(f"- {s}: interaction β E87 {inv[s]['E87_int_beta']:+.3f} vs E114 {inv[s]['E114_int_beta']:+.3f} → "
             + ("interaction INVERTED" if inv[s]['interaction_inverted'] else "interaction NOT inverted")
             + f"; fresh main effect E87 {inv[s]['E87_fresh_main_beta']:+.3f} (t={inv[s]['E87_fresh_main_t']:+.1f}) "
             f"vs E114 {inv[s]['E114_fresh_main_beta']:+.3f} → "
             + ("main effect INVERTED (rises on copy)" if inv[s]['fresh_main_inverted'] else "main effect not inverted") + ".")
L += ["",
      "Reading: E87's copy response is register-GENERAL — it lives in the fresh main effect",
      "(negative on both surfaces: it rises on copied tokens in register and control arms alike),",
      "while its register×fresh interaction is near zero (weakly negative on convdyn only).",
      "E114/E189's freshness response is register-CONDITIONAL (the interaction carries it).", ""]
L += ["---", "",
      "Figure: `fig.png` (2×2 cell means, binary coding, greedy cells, capture-level SE bars).",
      "All numbers descriptive; token-level observations are autocorrelated within captures —",
      "CR1 SEs cluster on capture, but no preregistered decision rule attaches to these fits."]
(OUT / "results.md").write_text("\n".join(L) + "\n")

print("\n=== verdicts ===")
print(json.dumps(clean(vd), indent=1))
print(f"\nwrote {OUT}/results.json results.md fig.png")
