#!/usr/bin/env python3
"""analyze_convdyn_T.py — LOCAL scorer for convdyn-T (prereg_convdyn_T_v1.json v1.2).

Scores T1–T5 + T-null with the frozen decision rules. Copy-metric machinery is identical
to analyze_copy.py (token-level longest suffix n-gram vs prior assistant turns / provided
frozen history; cap 32, flag >= 8). Features per prereg v1.5 definitions on trimmed E114
logit series. Outputs: results_T.md, analysis_T.png, results_T.json.
"""
import json, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE / "pulled/convdyn_T"
BLUE, GRAY, ORANGE, INK, RED = "#2563eb", "#9ca3af", "#ea580c", "#374151", "#dc2626"
N_TURNS, NMAX, COPY_N = 14, 32, 8

npz  = np.load(ROOT / "scalars.npz")
meta = json.loads((ROOT / "scalars_meta.json").read_text())["meta"]
trans = json.loads((ROOT / "transcripts.json").read_text())
hyb   = json.loads((ROOT / "hybrids.json").read_text())
armP  = json.loads((HERE / "armP_histories_v1.json").read_text())

CELLS = ["t0s0", "T05s0", "T05s1", "T05s2", "T07s0", "T07s1", "T07s2"]
TEMP_OF = {"t0s0": 0.0, "T05s0": 0.5, "T05s1": 0.5, "T05s2": 0.5, "T07s0": 0.7, "T07s1": 0.7, "T07s2": 0.7}

def capdir(rid):
    for cd in ROOT.glob("cap_*"):
        p = cd / rid
        if p.is_dir(): return p
    raise FileNotFoundError(rid)

def gen_tokens(rid, n_trim):
    ents = json.loads((capdir(rid) / "generated_tokens.json").read_text())[:n_trim]
    return [e["token_id"] for e in ents]

def series(rid):
    key = f"{rid}__gen_logit14"
    if key not in npz.files: return None
    n_trim = meta[rid]["n_trim"] or 0
    if n_trim <= 0: return None
    return np.asarray(npz[key][:n_trim], dtype=np.float64)

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

def copy_mask_dialogue(dlg):
    """{turn: (bool mask over trimmed tokens, max_ngram array)} vs prior turns of same dialogue."""
    turns = {}
    for e in trans[dlg]:
        rid = f"{dlg}_t{e['turn']:02d}"
        if series(rid) is None: continue
        turns[e["turn"]] = gen_tokens(rid, meta[rid]["n_trim"])
    out = {}
    for t, toks in sorted(turns.items()):
        S = ngram_sets([turns[j] for j in range(1, t) if j in turns])
        mg = np.array([longest_suffix(toks, i, S) for i in range(len(toks))])
        out[t] = (mg >= COPY_N, mg)
    return out

def floor_a(x): return x[-15:].mean() if len(x) >= 15 else x.mean()

def ols_slope(y):
    t = np.arange(1, N_TURNS + 1, dtype=float); m = np.isfinite(y)
    return float(np.polyfit(t[m], y[m], 1)[0]) if m.sum() >= 4 else np.nan

def knee(y, c_lo=3, c_hi=12):
    t = np.arange(1, N_TURNS + 1, dtype=float); m = np.isfinite(y); t, y = t[m], y[m]; n = len(y)
    X1 = np.column_stack([np.ones(n), t]); b1, *_ = np.linalg.lstsq(X1, y, rcond=None)
    sse1 = float(np.sum((y - X1 @ b1) ** 2)); bic1 = n * np.log(max(sse1, 1e-12) / n) + 3 * np.log(n)
    best = (None, np.inf)
    for c in range(c_lo, c_hi + 1):
        X2 = np.column_stack([np.ones(n), t, np.maximum(0, t - c)])
        b2, *_ = np.linalg.lstsq(X2, y, rcond=None)
        sse2 = float(np.sum((y - X2 @ b2) ** 2))
        if sse2 < best[1]: best = (c, sse2)
    c, sse2 = best
    bic2 = n * np.log(max(sse2, 1e-12) / n) + 5 * np.log(n)
    return dict(accepted=bool(bic2 < bic1), c=c, bic1=round(bic1, 2), bic2=round(bic2, 2))

# ---------------- per-cell A/B floors, copy fractions, per-token tables ----------------
cellstats = {}
for cell in CELLS:
    st = dict(cell=cell, temp=TEMP_OF[cell])
    masks = {arm: copy_mask_dialogue(f"{arm}_{cell}") for arm in ("A", "B")}
    for arm in ("A", "B"):
        fl, cf = [], []
        for t in range(1, N_TURNS + 1):
            x = series(f"{arm}_{cell}_t{t:02d}")
            fl.append(floor_a(x) if x is not None else np.nan)
            cf.append(float(masks[arm][t][0].mean()) if t in masks[arm] else np.nan)
        st[f"floor_{arm}"] = fl; st[f"copyfrac_{arm}"] = cf
    st["AB_floor_slope"] = ols_slope(np.array(st["floor_A"]) - np.array(st["floor_B"]))
    st["copyfrac_A_late"] = float(np.nanmean(st["copyfrac_A"][4:]))
    # per-token table for T2 residualization (A+B pooled within cell)
    rows = []
    for arm in ("A", "B"):
        for t, (cm, mg) in masks[arm].items():
            x = series(f"{arm}_{cell}_t{t:02d}")
            selfS = [set() for _ in range(NMAX + 1)]
            toks = gen_tokens(f"{arm}_{cell}_t{t:02d}", meta[f"{arm}_{cell}_t{t:02d}"]["n_trim"])
            for i in range(len(toks)):
                sr = longest_suffix(toks, i, selfS)
                rows.append((arm, t, mg[i], sr, x[i]))
                for n in range(1, min(NMAX, i + 1) + 1): selfS[n].add(tuple(toks[i - n + 1:i + 1]))
    arm_a = np.array([r[0] for r in rows]); turn_a = np.array([r[1] for r in rows], dtype=float)
    mg_a = np.array([r[2] for r in rows], dtype=float); sr_a = np.array([r[3] for r in rows], dtype=float)
    e_a = np.array([r[4] for r in rows])
    X = np.column_stack([np.ones(len(e_a)), np.log2(1 + mg_a), (mg_a >= COPY_N).astype(float), np.log2(1 + sr_a)])
    b, *_ = np.linalg.lstsq(X, e_a, rcond=None)
    e_adj = e_a - (X @ b - b[0])
    fA, fB = [], []
    for t in range(1, N_TURNS + 1):
        for arm, acc in (("A", fA), ("B", fB)):
            idx = np.where((arm_a == arm) & (turn_a == t))[0]
            acc.append(e_adj[idx[-15:]].mean() if len(idx) >= 15 else (e_adj[idx].mean() if len(idx) else np.nan))
    st["AB_floor_slope_adj"] = ols_slope(np.array(fA) - np.array(fB))
    st["absorbed"] = (1 - st["AB_floor_slope_adj"] / st["AB_floor_slope"]) if st["AB_floor_slope"] else np.nan
    cellstats[cell] = st

# ---------------- arm R ----------------
Rstats = {}
for cell in ("t0s0", "T07s0", "T07s1", "T07s2"):
    dlg = f"R_{cell}"
    masks = copy_mask_dialogue(dlg)
    fl = [floor_a(series(f"{dlg}_t{t:02d}")) if series(f"{dlg}_t{t:02d}") is not None else np.nan
          for t in range(1, N_TURNS + 1)]
    cf = [float(masks[t][0].mean()) if t in masks else np.nan for t in range(1, N_TURNS + 1)]
    Rstats[cell] = dict(floor=fl, copyfrac=cf, knee=knee(np.array(fl), c_lo=2, c_hi=12))

# ---------------- arm P ----------------
def hist_tokens_for(o, cond, k):
    blk = armP[f"o{o}"][cond]
    return [gen_hist_ids[(o, cond, e["turn"])] for e in blk if e["turn"] < k]

# tokenize frozen history texts ONCE via captured prompt tokens? Simpler: n-gram source from
# the frozen text is what the model saw; but our copy metric is token-id based. We recover
# history token ids from the capture's prompt_tokens.json (the actual prompt encoding).
Pstats = {}
for o in (1, 2, 3):
    for cond in ("replay", "para"):
        for k in (4, 8, 12):
            rid = f"P_{cond}_o{o}_k{k:02d}"
            x = series(rid)
            if x is None: Pstats[rid] = None; continue
            pd = capdir(rid)
            ptoks = json.loads((pd / "prompt_tokens.json").read_text(errors="replace"))
            pids = [t["token_id"] for t in ptoks]
            S = ngram_sets([pids])   # whole prompt (history+probe) as copy source
            toks = gen_tokens(rid, meta[rid]["n_trim"])
            mg = np.array([longest_suffix(toks, i, S) for i in range(len(toks))])
            Pstats[rid] = dict(floor=float(floor_a(x)), peak=float(x.max()), auc=float(x.sum()),
                               copyfrac=float((mg >= COPY_N).mean()), n_trim=len(toks))

# ---------------- scoring ----------------
res = {"cells": cellstats, "R": Rstats, "P": Pstats}
t0_slope = cellstats["t0s0"]["AB_floor_slope"]

# T1
t07 = [cellstats[c] for c in ("T07s0", "T07s1", "T07s2")]
cf07 = float(np.mean([c["copyfrac_A_late"] for c in t07]))
shallower = sum(1 for c in t07 if abs(c["AB_floor_slope"]) < 0.5 * abs(t0_slope))
steeper   = sum(1 for c in t07 if abs(c["AB_floor_slope"]) >= abs(t0_slope) and np.sign(c["AB_floor_slope"]) == np.sign(t0_slope))
T1_fragile = (cf07 < 0.30) and (shallower >= 2)
T1_robust  = (cf07 >= 0.50) and (steeper >= 2)
res["T1"] = dict(copyfrac_A_late_t07=cf07, t0_slope=t0_slope,
                 slopes_t07=[c["AB_floor_slope"] for c in t07],
                 fragile=bool(T1_fragile), robust=bool(T1_robust))

# T2 (per temp, >=2/3 seeds absorbed>=50%, scored where raw |slope|>0.02)
T2 = {}
for temp, cells in (("0.5", ["T05s0", "T05s1", "T05s2"]), ("0.7", ["T07s0", "T07s1", "T07s2"])):
    scored = [c for c in cells if abs(cellstats[c]["AB_floor_slope"]) > 0.02]
    hits = sum(1 for c in scored if cellstats[c]["absorbed"] >= 0.5)
    T2[temp] = dict(n_scored=len(scored), n_absorbed_ge50=hits,
                    absorbed=[round(float(cellstats[c]["absorbed"]), 2) if np.isfinite(cellstats[c]["absorbed"]) else None for c in cells],
                    supported=bool(len(scored) >= 2 and hits >= 2))
res["T2"] = T2

# T3
Rg = Rstats["t0s0"]
cf_t2 = Rg["copyfrac"][1]
T3_primary = (cf_t2 >= 0.60) and Rg["knee"]["accepted"] and Rg["knee"]["c"] in (2, 3)
cf_t2_07 = float(np.nanmean([Rstats[c]["copyfrac"][1] for c in ("T07s0", "T07s1", "T07s2")]))
res["T3"] = dict(greedy_copyfrac_t2=cf_t2, knee=Rg["knee"], primary=bool(T3_primary),
                 secondary_t07_t2_copyfrac=cf_t2_07, secondary=bool(cf_t2 - cf_t2_07 >= 0.3))

# T4
d8 = []
for o in (1, 2, 3):
    pr, pp = Pstats[f"P_replay_o{o}_k08"], Pstats[f"P_para_o{o}_k08"]
    d8.append((pp["floor"] - pr["floor"]) if (pr and pp) else np.nan)
d8m = float(np.nanmean(d8)); d8pos = sum(1 for v in d8 if np.isfinite(v) and v > 0)
cf_rep = float(np.nanmean([Pstats[f"P_replay_o{o}_k08"]["copyfrac"] for o in (1, 2, 3)]))
cf_par = float(np.nanmean([Pstats[f"P_para_o{o}_k08"]["copyfrac"] for o in (1, 2, 3)]))
sec = {k: float(np.nanmean([Pstats[f"P_para_o{o}_k{k:02d}"]["floor"] - Pstats[f"P_replay_o{o}_k{k:02d}"]["floor"] for o in (1, 2, 3)])) for k in (4, 12)}
res["T4"] = dict(delta8=d8, delta8_mean=d8m, delta8_pos=d8pos,
                 supported=bool(d8m > 0.40 and d8pos >= 2),
                 copyfrac_replay_k8=cf_rep, copyfrac_para_k8=cf_par,
                 fork_source_agnostic=bool(cf_par >= 0.5 and not (d8m > 0.40 and d8pos >= 2)),
                 delta_k4=sec[4], delta_k12=sec[12])

# T5 — coalition replication at temp 0.7 (pooled seeds, arm A, measured masks)
tok_copy, L14 = [], []
sel_fresh, sel_copy = [], []
for cell in ("T07s0", "T07s1", "T07s2"):
    dlg = f"A_{cell}"
    masks = copy_mask_dialogue(dlg)
    for t, (cm, mg) in masks.items():
        rid = f"{dlg}_t{t:02d}"
        n_p, n_tr = meta[rid]["n_prompt"], meta[rid]["n_trim"]
        R = np.load(capdir(rid) / "router/ffn_moe_logits-14.npy")[n_p:n_p + n_tr].astype(np.float64)
        L14.append(R); tok_copy.append(cm)
        sel = np.asarray(npz[f"{rid}__gen_sel14"][:n_tr], dtype=float)
        sel_fresh.append(sel[~cm]); sel_copy.append(sel[cm])
L14 = np.vstack(L14); tok_copy = np.concatenate(tok_copy)
a, b = L14[tok_copy], L14[~tok_copy]
sp = np.sqrt((a.var(0, ddof=1) * (len(a) - 1) + b.var(0, ddof=1) * (len(b) - 1)) / max(len(a) + len(b) - 2, 1))
d14 = (a.mean(0) - b.mean(0)) / np.maximum(sp, 1e-9)
p_sel_f = float(np.nanmean(np.concatenate(sel_fresh))); p_sel_c = float(np.nanmean(np.concatenate(sel_copy)))
res["T5"] = dict(n_copy=int(tok_copy.sum()), n_compose=int((~tok_copy).sum()),
                 E87_d=float(d14[87]), E114_d=float(d14[114]), E34_d=float(d14[34]),
                 sel_ratio=(p_sel_f / max(p_sel_c, 1e-6)),
                 p_sel_compose=p_sel_f, p_sel_copied=p_sel_c,
                 supported=bool(d14[87] > 1.0 and d14[114] < -1.0),
                 secondary=dict(E34_gt1=bool(d14[34] > 1.0), sel_ratio_ge5=bool(p_sel_f / max(p_sel_c, 1e-6) >= 5)))

res["T_null"] = not any([res["T1"]["fragile"], res["T1"]["robust"], T2["0.5"]["supported"] or T2["0.7"]["supported"],
                         res["T3"]["primary"], res["T4"]["supported"], res["T5"]["supported"]])
(HERE / "results_T.json").write_text(json.dumps(res, indent=1, default=float))

# ---------------- figure ----------------
fig, axes = plt.subplots(2, 2, figsize=(14, 9.5), facecolor="white")
tx = np.arange(1, 15)
ax = axes[0, 0]
for cell, col, lw in (("t0s0", INK, 2.4), ("T05s0", BLUE, 1.2), ("T05s1", BLUE, 1.2), ("T05s2", BLUE, 1.2),
                      ("T07s0", ORANGE, 1.2), ("T07s1", ORANGE, 1.2), ("T07s2", ORANGE, 1.2)):
    d = np.array(cellstats[cell]["floor_A"]) - np.array(cellstats[cell]["floor_B"])
    ax.plot(tx, d, "o-", color=col, lw=lw, ms=3, alpha=0.9 if lw > 2 else 0.55)
ax.axhline(0, color=INK, lw=0.5)
ax.set_title("A−B floor: greedy (black) vs T0.5 (blue) vs T0.7 (orange)", color=INK, fontsize=10)
ax.set_xlabel("turn"); ax.grid(alpha=0.15)
ax = axes[0, 1]
for cell, col in (("t0s0", INK), ("T05s0", BLUE), ("T05s1", BLUE), ("T05s2", BLUE),
                  ("T07s0", ORANGE), ("T07s1", ORANGE), ("T07s2", ORANGE)):
    ax.plot(tx, cellstats[cell]["copyfrac_A"], "o-", color=col, lw=1.4, ms=3, alpha=0.7)
ax.set_title("arm-A copy fraction by turn (all cells)", color=INK, fontsize=10)
ax.set_xlabel("turn"); ax.grid(alpha=0.15)
ax = axes[1, 0]
for cell, col in (("t0s0", INK), ("T07s0", ORANGE), ("T07s1", ORANGE), ("T07s2", ORANGE)):
    ax.plot(tx, Rstats[cell]["floor"], "o-", color=col, lw=1.6, ms=3, alpha=0.8,
            label=f"R {cell} (knee c={Rstats[cell]['knee']['c']}{'*' if Rstats[cell]['knee']['accepted'] else ''})")
ax.set_title("arm R (repeat probe) floors", color=INK, fontsize=10)
ax.set_xlabel("turn"); ax.legend(frameon=False, fontsize=7); ax.grid(alpha=0.15)
ax = axes[1, 1]
w = 0.35; ks = (4, 8, 12)
for i, cond, col in ((0, "replay", GRAY), (1, "para", BLUE)):
    vals = [float(np.nanmean([Pstats[f"P_{cond}_o{o}_k{k:02d}"]["floor"] for o in (1, 2, 3)])) for k in ks]
    ax.bar([x + (i - 0.5) * w for x in range(3)], vals, width=w, color=col, label=cond)
ax.set_xticks(range(3)); ax.set_xticklabels([f"k={k}" for k in ks])
ax.set_title("arm P: probe-turn floor, replay vs paraphrased history", color=INK, fontsize=10)
ax.legend(frameon=False, fontsize=8); ax.grid(alpha=0.15)
fig.tight_layout(); fig.savefig(HERE / "analysis_T.png", dpi=150)

# ---------------- results_T.md ----------------
L = ["# convdyn-T results (prereg v1.2 sha 64964043…)", "",
     f"276/276 captures verified; redundancy r=1.000000 (extract log).", "",
     "## Cell table", "",
     "| cell | temp | A−B floor slope | adj (resid) | absorbed | A copy-frac late |",
     "|---|---|---|---|---|---|"]
for c in CELLS:
    s = cellstats[c]
    L.append(f"| {c} | {s['temp']} | {s['AB_floor_slope']:+.4f} | {s['AB_floor_slope_adj']:+.4f} | "
             + (f"{s['absorbed']:.0%}" if np.isfinite(s['absorbed']) else "—")
             + f" | {s['copyfrac_A_late']:.2f} |")
T1 = res["T1"]
L += ["", "## Predictions", "",
      f"- **T1-copy-fragile**: {'SUPPORTED' if T1['fragile'] else 'not supported'} · "
      f"**T1-copy-robust**: {'SUPPORTED' if T1['robust'] else 'not supported'} "
      f"(T0.7 late copy-frac {T1['copyfrac_A_late_t07']:.2f}; slopes {['%+.3f' % v for v in T1['slopes_t07']]} vs greedy {T1['t0_slope']:+.3f})",
      f"- **T2-mediation**: 0.5 -> {'SUPPORTED' if T2['0.5']['supported'] else 'not supported'} {T2['0.5']['absorbed']}; "
      f"0.7 -> {'SUPPORTED' if T2['0.7']['supported'] else 'not supported'} {T2['0.7']['absorbed']}",
      f"- **T3-repeat-knee**: {'SUPPORTED' if res['T3']['primary'] else 'not supported'} "
      f"(greedy R copy-frac t2 = {res['T3']['greedy_copyfrac_t2']:.2f}; knee {res['T3']['knee']}); "
      f"secondary {'SUPPORTED' if res['T3']['secondary'] else 'not supported'} (t0.7 t2 copy-frac {res['T3']['secondary_t07_t2_copyfrac']:.2f})",
      f"- **T4-paraphrase-restores**: {'SUPPORTED' if res['T4']['supported'] else 'not supported'} "
      f"(Δ_P(8) = {res['T4']['delta8_mean']:+.3f}, positive {res['T4']['delta8_pos']}/3; per-ord {['%+.2f' % v for v in res['T4']['delta8']]}; "
      f"k4 {res['T4']['delta_k4']:+.2f}, k12 {res['T4']['delta_k12']:+.2f}; "
      f"manip check copy-frac replay {res['T4']['copyfrac_replay_k8']:.2f} vs para {res['T4']['copyfrac_para_k8']:.2f}"
      + ("; **FORK: source-agnostic affordance**" if res['T4']['fork_source_agnostic'] else "") + ")",
      f"- **T5-coalition**: {'SUPPORTED' if res['T5']['supported'] else 'not supported'} "
      f"(E87 d={res['T5']['E87_d']:+.2f}, E114 d={res['T5']['E114_d']:+.2f}, E34 d={res['T5']['E34_d']:+.2f}; "
      f"sel compose {res['T5']['p_sel_compose']:.3f} vs copied {res['T5']['p_sel_copied']:.3f}, ratio {res['T5']['sel_ratio']:.1f})",
      f"- **T-null**: {'SUPPORTED' if res['T_null'] else 'not supported'}", "",
      "## Arm R floors/copy", ""]
for cell in ("t0s0", "T07s0", "T07s1", "T07s2"):
    r = Rstats[cell]
    L.append(f"- {cell}: floors " + " ".join(f"{v:+.2f}" for v in r["floor"][:6]) + " … ; copy-frac "
             + " ".join(f"{v:.2f}" for v in r["copyfrac"][:6]) + " … ; knee {}".format(r["knee"]))
L += ["", "## Caveats", "- n=3 seeds/orderings, sign consistency only; CAP_HIT as in grid; single box/build;",
      "  copy metric identical to grid post-hoc calibration (prereg mediator_definition).",
      "", "Scored strictly per prereg_convdyn_T_v1.json v1.2 frozen rules."]
(HERE / "results_T.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
