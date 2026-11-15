#!/usr/bin/env python3
"""analyze_convdyn.py — LOCAL analysis for the E114 conversational-dynamics experiment.

Implements the frozen analysis plan in prereg_convdyn_v1.json (v1.1). Reads the pulled
box outputs (extracted tarballs) and writes figures + results.

  --smoke [--root pulled/convdyn_smoke] : smoke-gate report for Arm A ordering 1 —
        five-feature plot + example traces + new-slot ignition + proj/logit agreement.
        Output: analysis_smoke.png, smoke_report.md.  THE GRID DOES NOT LAUNCH UNTIL
        JEFFREY HAS SEEN THIS PLOT AND APPROVED.
  --grid  [--root pulled/convdyn_grid]  : full deliverables — feature curves raw + A−B,
        history-swap bars, knee analysis, traces, results.md scoring every prediction.

All feature definitions are the prereg's; the knee penalty is FIXED in code here
(BIC, k_1seg=3, k_2seg=5, n=14) and was frozen before any capture existed.
"""
import argparse, json, pathlib, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
BLUE, GRAY, ORANGE, INK = "#2563eb", "#9ca3af", "#ea580c", "#374151"  # A, B, C, ink (repo style)
ARM_COLOR = {"A": BLUE, "B": GRAY, "C": ORANGE}
N_TURNS = 14

# ---------------- loading ----------------
def load_root(root):
    root = pathlib.Path(root)
    if not root.exists(): sys.exit(f"missing {root} — pull + extract the box tarball first")
    npz  = np.load(root / "scalars.npz")
    meta = json.loads((root / "scalars_meta.json").read_text())["meta"]
    trans = json.loads((root / "transcripts.json").read_text())
    hyb = json.loads((root / "hybrids.json").read_text()) if (root / "hybrids.json").exists() else {}
    return npz, meta, trans, hyb

def series(npz, meta, rid):
    """Trimmed response proj14 for one capture (None if missing/empty)."""
    key = f"{rid}__gen_proj14"
    if key not in npz.files: return None
    n_trim = meta[rid]["n_trim"] or 0
    x = np.asarray(npz[key][:n_trim], dtype=np.float64)
    return x if len(x) else None

# ---------------- per-turn features (prereg definitions) ----------------
def fit_decay(x, floor):
    i = int(np.argmax(x)); tail = x[i:] - floor
    if len(tail) < 16: return None, None
    t = np.arange(len(tail)); best = (None, None, -np.inf)
    for tau in range(2, 301, 2):
        e = np.exp(-t / tau)
        A = float(tail @ e / (e @ e))
        if A <= 0: continue
        ss = np.sum((tail - tail.mean()) ** 2)
        r2 = 1 - np.sum((tail - A * e) ** 2) / max(ss, 1e-12)
        if r2 > best[2]: best = (tau, A, r2)
    return best[0], best[2] if best[0] else None

def turn_features(npz, meta, dlg, t):
    x = series(npz, meta, f"{dlg}_t{t:02d}")
    f = dict(peak=np.nan, floor_a=np.nan, floor_b=np.nan, var=np.nan, skew=np.nan,
             auc=np.nan, decay_tau=np.nan, decay_r2=np.nan)
    if x is None: return f
    f["peak"] = x.max()
    f["floor_a"] = x[-15:].mean() if len(x) >= 15 else x.mean()
    f["var"] = x.var()
    sd = x.std()
    f["skew"] = float(((x - x.mean()) ** 3).mean() / sd ** 3) if sd > 1e-6 else 0.0
    f["auc"] = x.sum()
    tau, r2 = fit_decay(x, f["floor_a"])
    if tau: f["decay_tau"], f["decay_r2"] = tau, r2
    # floor variant (b): next turn's incoming-user-segment prefill mean
    nxt = f"{dlg}_t{t+1:02d}"
    if t < N_TURNS and nxt in meta and meta[nxt]["userseg_start"] >= 0:
        pf = npz[f"{nxt}__prefill_proj14"]
        f["floor_b"] = float(pf[meta[nxt]["userseg_start"]:meta[nxt]["userseg_end"]].mean())
    return f

FEATS = ["peak", "floor_a", "floor_b", "var", "skew", "auc"]

def dialogue_table(npz, meta, dlg):
    return {ft: np.array([turn_features(npz, meta, dlg, t)[ft] for t in range(1, N_TURNS + 1)])
            for ft in FEATS + ["decay_tau", "decay_r2"]}

def ols_slope(y):
    t = np.arange(1, N_TURNS + 1, dtype=float)
    m = np.isfinite(y)
    if m.sum() < 4: return np.nan
    tt, yy = t[m], y[m]
    return float(np.polyfit(tt, yy, 1)[0])

def sign_consistency(slopes, direction):
    good = sum(1 for s in slopes if np.isfinite(s) and (s > 0) == (direction > 0) and s != 0)
    return good, ("strong" if good == 3 else "weak" if good == 2 else "unsupported")

# ---------------- knee (frozen BIC rule) ----------------
def knee(y):
    t = np.arange(1, N_TURNS + 1, dtype=float)
    m = np.isfinite(y); t, y = t[m], y[m]; n = len(y)
    X1 = np.column_stack([np.ones(n), t])
    b1, *_ = np.linalg.lstsq(X1, y, rcond=None)
    sse1 = float(np.sum((y - X1 @ b1) ** 2))
    bic1 = n * np.log(max(sse1, 1e-12) / n) + 3 * np.log(n)
    best = (None, np.inf, None)
    for c in range(3, 13):
        X2 = np.column_stack([np.ones(n), t, np.maximum(0, t - c)])
        b2, *_ = np.linalg.lstsq(X2, y, rcond=None)
        sse2 = float(np.sum((y - X2 @ b2) ** 2))
        if sse2 < best[1]: best = (c, sse2, b2)
    c, sse2, b2 = best
    bic2 = n * np.log(max(sse2, 1e-12) / n) + 5 * np.log(n)
    return dict(accepted=bool(bic2 < bic1), c=c, bic1=bic1, bic2=bic2, b1=b1.tolist(), b2=b2.tolist())

# ---------------- smoke ----------------
def run_smoke(root):
    npz, meta, trans, _ = load_root(root)
    dlg = "A_o1"
    tab = dialogue_table(npz, meta, dlg)
    ents = trans[dlg]
    # gates (prereg smoke_gate)
    n_cap = sum(1 for e in ents if f"{dlg}_t{e['turn']:02d}__gen_proj14" in npz.files)
    long_enough = sum(1 for e in ents if e["n_trim"] >= 15)
    peaks_by_slot = {e["slot"]: tab["peak"][e["turn"] - 1] for e in ents}
    vals = [v for s, v in peaks_by_slot.items() if s <= "S10"]
    # v1.5 scale-free ignition rule: new-slot peak within the validated range, tolerance
    # half the validated spread below its min (projections live on a signed/offset scale)
    bar = min(vals) - 0.5 * (max(vals) - min(vals))
    new_ok = {s: (peaks_by_slot[s] >= bar) for s in ("S11", "S12", "S13", "S14")}
    r_pool = np.corrcoef(
        np.concatenate([npz[f"{dlg}_t{t:02d}__gen_proj14"] for t in range(1, 15) if f"{dlg}_t{t:02d}__gen_proj14" in npz.files]),
        np.concatenate([npz[f"{dlg}_t{t:02d}__gen_logit14"] for t in range(1, 15) if f"{dlg}_t{t:02d}__gen_logit14" in npz.files]))[0, 1]
    verdict = (n_cap == 14 and long_enough >= 12 and all(new_ok.values()) and r_pool > 0.999)

    fig, axes = plt.subplots(2, 3, figsize=(15, 8), facecolor="white")
    tx = np.arange(1, 15)
    for ax, ft, lab in zip(axes.flat, ["peak", "floor_a", "auc", "var", "skew"],
                           ["peak", "floor (last-15; dashed = next-prefill)", "AUC (register mass)", "variance", "skew"]):
        ax.plot(tx, tab[ft], "o-", color=BLUE, lw=2, ms=5)
        if ft == "floor_a": ax.plot(tx, tab["floor_b"], "s--", color=BLUE, lw=1.2, ms=4, alpha=0.6)
        ax.set_title(f"Arm A ord1 · {lab}", color=INK, fontsize=10)
        ax.set_xlabel("turn"); ax.grid(alpha=0.15)
    ax = axes.flat[5]
    for t, col in ((2, BLUE), (12, ORANGE)):
        x = series(npz, meta, f"{dlg}_t{t:02d}")
        if x is not None: ax.plot(x, color=col, lw=1.6, label=f"turn {t}")
    ax.set_title("per-token proj14: turn 2 vs 12", color=INK, fontsize=10)
    ax.set_xlabel("response token"); ax.legend(frameon=False); ax.grid(alpha=0.15)
    fig.suptitle(f"SMOKE — Arm A ordering 1 ({'PASS' if verdict else 'FAIL'})", color=INK)
    fig.tight_layout(); fig.savefig(HERE / "analysis_smoke.png", dpi=150)

    rep = [f"# Smoke report — {'PASS' if verdict else 'FAIL'}",
           f"- captured turns: {n_cap}/14", f"- turns with >=15-token responses: {long_enough}/14 (need >=12)",
           f"- new-slot ignition (peak >= min(validated) - 0.5*spread = {bar:+.2f}; v1.5 rule): "
           + ", ".join(f"{s}:{peaks_by_slot[s]:+.2f} {'OK' if v else 'FAIL'}" for s, v in new_ok.items()),
           f"- pooled r(proj14, raw logit14) = {r_pool:.6f} (need > 0.999)",
           f"- per-turn peaks: " + " ".join(f"t{t}:{v:+.2f}" for t, v in zip(tx, tab['peak'])),
           "", "HARD GATE: show analysis_smoke.png to Jeffrey; the grid does not launch without his approval."]
    (HERE / "smoke_report.md").write_text("\n".join(rep) + "\n")
    print("\n".join(rep))

# ---------------- grid ----------------
def run_grid(root):
    npz, meta, trans, hyb = load_root(root)
    tabs = {(a, o): dialogue_table(npz, meta, f"{a}_o{o}") for a in "ABC" for o in (1, 2, 3)}
    diff = {pair: {ft: {o: tabs[(pair[0], o)][ft] - tabs[(pair[2], o)][ft] for o in (1, 2, 3)} for ft in FEATS}
            for pair in ("A-B", "C-B")}
    mean_diff = {pair: {ft: np.nanmean([diff[pair][ft][o] for o in (1, 2, 3)], axis=0) for ft in FEATS}
                 for pair in diff}

    slopes = {pair: {ft: {o: ols_slope(diff[pair][ft][o]) for o in (1, 2, 3)} for ft in FEATS} for pair in diff}
    mslope = {pair: {ft: ols_slope(mean_diff[pair][ft]) for ft in FEATS} for pair in diff}

    # ---- history swap ----
    swap = {}
    for k in (4, 8, 12):
        ds = []
        for o in (1, 2, 3):
            pa = tabs[("A", o)]["peak"][k - 1]
            xd = series(npz, meta, f"D_o{o}_k{k:02d}")
            ds.append(pa - xd.max() if xd is not None else np.nan)
        swap[k] = ds
    d8 = swap[8]; d8pos = sum(1 for v in d8 if np.isfinite(v) and v > 0)

    # ---- knee on mean A−B floor_a ----
    kn = knee(mean_diff["A-B"]["floor_a"])
    y = mean_diff["A-B"]["floor_a"]; pk = mean_diff["A-B"]["peak"]
    conv = None
    if kn["accepted"]:
        c = kn["c"]; gap = np.abs(pk - y)
        conv = bool(np.nanmean(gap[c:]) < 0.5 * np.nanmean(gap[:c]))

    # ---- prediction scoring (prereg formulas) ----
    def sc(pair, ft, direction): return sign_consistency([slopes[pair][ft][o] for o in (1, 2, 3)], direction)
    ps, fs = mslope["A-B"]["peak"], mslope["A-B"]["floor_a"]
    fs_b = mslope["A-B"]["floor_b"]
    auc_slope = mslope["A-B"]["auc"]
    auc_mass = np.nanmean(mean_diff["A-B"]["auc"][10:14]) >= 0.8 * np.nanmean(mean_diff["A-B"]["auc"][0:4])
    P = {
      "P-habituation": ps < 0 and abs(fs) < 0.25 * abs(ps),
      "P-accumulation": fs > 0 or (np.isfinite(fs_b) and fs_b > 0),
      "P-spikes-to-swells": ps < 0 and fs > 0 and (auc_slope >= 0 or auc_mass),
      "P-knee": bool(kn["accepted"] and conv),
      "P-null": all(sc("A-B", ft, np.sign(mslope["A-B"][ft]) or 1)[1] == "unsupported" for ft in FEATS if np.isfinite(mslope["A-B"][ft])),
    }
    vocab_flag = {ft: (np.isfinite(mslope["C-B"][ft]) and abs(mslope["C-B"][ft]) >= 0.5 * abs(mslope["A-B"][ft]))
                  for ft in FEATS}

    # ---- figures ----
    tx = np.arange(1, 15)
    fig, axes = plt.subplots(5, 2, figsize=(13, 17), facecolor="white")
    for r, ft in enumerate(["peak", "floor_a", "auc", "var", "skew"]):
        ax = axes[r, 0]
        for a in "ABC":
            ax.plot(tx, np.nanmean([tabs[(a, o)][ft] for o in (1, 2, 3)], axis=0), "o-",
                    color=ARM_COLOR[a], lw=2, ms=4, label=f"Arm {a}" if r == 0 else None)
        ax.set_title(f"{ft} · raw (mean over orderings)", color=INK, fontsize=10); ax.grid(alpha=0.15)
        ax = axes[r, 1]
        for o in (1, 2, 3):
            ax.plot(tx, diff["A-B"][ft][o], color=BLUE, lw=0.8, alpha=0.35)
        ax.plot(tx, mean_diff["A-B"][ft], "o-", color=BLUE, lw=2.2, ms=4)
        ax.plot(tx, mean_diff["C-B"][ft], "--", color=ORANGE, lw=1.4, alpha=0.8)
        ax.axhline(0, color=INK, lw=0.5)
        ax.set_title(f"{ft} · A−B (thin: per ordering; dashed: C−B)", color=INK, fontsize=10); ax.grid(alpha=0.15)
    axes[0, 0].legend(frameon=False, fontsize=9)
    for ax in axes[-1]: ax.set_xlabel("turn")
    fig.tight_layout(); fig.savefig(HERE / "analysis_features.png", dpi=150)

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 4.4), facecolor="white")
    w = 0.22
    for i, o in enumerate((1, 2, 3)):
        ax1.bar([k + (i - 1) * w for k in (4, 8, 12)], [swap[k][o - 1] for k in (4, 8, 12)],
                width=w, color=BLUE, alpha=0.35 + 0.2 * i, label=f"ord {o}")
    ax1.plot([4, 8, 12], [np.nanmean(swap[k]) for k in (4, 8, 12)], "o-", color=INK, lw=2, label="mean")
    ax1.axhline(0, color=INK, lw=0.5); ax1.set_xticks([4, 8, 12])
    ax1.set_title("history swap: peak(A,k) − peak(D,k)", color=INK, fontsize=10)
    ax1.set_xlabel("k"); ax1.legend(frameon=False, fontsize=8); ax1.grid(alpha=0.15)
    ax2.plot(tx, y, "o-", color=BLUE, lw=2)
    t_ = np.arange(1, 15, dtype=float)
    ax2.plot(t_, kn["b1"][0] + kn["b1"][1] * t_, "--", color=GRAY, lw=1.2, label="1-seg")
    b2 = kn["b2"]; ax2.plot(t_, b2[0] + b2[1] * t_ + b2[2] * np.maximum(0, t_ - kn["c"]), "-", color=ORANGE, lw=1.4,
                            label=f"2-seg (c={kn['c']})")
    ax2.set_title(f"knee on A−B floor: BIC {kn['bic2']:.1f} vs {kn['bic1']:.1f} -> {'ACCEPT' if kn['accepted'] else 'reject'}",
                  color=INK, fontsize=10)
    ax2.set_xlabel("turn"); ax2.legend(frameon=False, fontsize=8); ax2.grid(alpha=0.15)
    for t, col in ((2, BLUE), (12, ORANGE)):
        x = series(npz, meta, f"A_o1_t{t:02d}")
        if x is not None: ax3.plot(x, color=col, lw=1.6, label=f"turn {t}")
    ax3.set_title("Arm A ord1 per-token proj14", color=INK, fontsize=10)
    ax3.set_xlabel("response token"); ax3.legend(frameon=False, fontsize=8); ax3.grid(alpha=0.15)
    fig.tight_layout(); fig.savefig(HERE / "analysis_swap_knee_traces.png", dpi=150)

    # ---- results.md (contrasts table first, prose second, caveats inline) ----
    L = ["# Conversational dynamics — results (prereg v1.5, sha 4356e500…)", "",
         "## Contrast table (slopes vs turn index, A−B primary)", "",
         "| feature | A−B slope (mean) | per-ord signs | C−B slope | vocab-driven? |", "|---|---|---|---|---|"]
    for ft in FEATS:
        n_ok, lab = sc("A-B", ft, np.sign(mslope["A-B"][ft]) or 1)
        L.append(f"| {ft} | {mslope['A-B'][ft]:+.4f} | {n_ok}/3 ({lab}) | {mslope['C-B'][ft]:+.4f} | {'YES' if vocab_flag[ft] else 'no'} |")
    L += ["", "## History swap", "",
          "| k | ord1 | ord2 | ord3 | mean |", "|---|---|---|---|---|"]
    for k in (4, 8, 12):
        L.append(f"| {k} | " + " | ".join(f"{v:+.3f}" for v in swap[k]) + f" | {np.nanmean(swap[k]):+.3f} |")
    L += ["", f"PRIMARY: Delta_8 = {np.nanmean(d8):+.3f}, positive in {d8pos}/3 orderings -> "
          + ("accumulated context DRIVES ignition" if np.nanmean(d8) > 0 and d8pos >= 2 else "not supported"), "",
          "## Predictions", ""]
    for k, v in P.items(): L.append(f"- **{k}**: {'SUPPORTED' if v else 'not supported'}")
    L += ["", f"## Knee", f"- {'ACCEPTED' if kn['accepted'] else 'rejected'} at c={kn['c']} "
          f"(BIC 2-seg {kn['bic2']:.2f} vs 1-seg {kn['bic1']:.2f}; frozen penalty (5-3)ln14=5.28); "
          f"peak/floor convergence: {conv}", "",
          "## Caveats (inline)",
          f"- flags: " + json.dumps({d: [f"t{e['turn']}:{k}" for e in trans[d] for k, v in e["flags"].items() if v]
                                     for d in sorted(trans) if any(any(e["flags"].values()) for e in trans[d])}),
          "- decay taus reported per turn in features (sparse where post-peak < 16 tokens); see npz for raw series",
          "- KV cache f16 (llama.cpp default) = prior validated surface; brief's bf16 pin amended in prereg",
          "- n=3 orderings: direction claims use sign consistency, no parametric p-values"]
    (HERE / "results.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--grid", action="store_true")
    ap.add_argument("--root", default=None)
    a = ap.parse_args()
    if a.smoke: run_smoke(a.root or HERE / "pulled/convdyn_smoke")
    elif a.grid: run_grid(a.root or HERE / "pulled/convdyn_grid")
    else: sys.exit("pass --smoke or --grid")
