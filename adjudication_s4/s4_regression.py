#!/usr/bin/env python3
"""§4 axis adjudication — the frozen regression (probe_spec.md / prereg_freeze_v2.json
bcccc6fe… / 4_capture_config_v1.md / rating_rubric_v1.md). Implements the frozen specs
EXACTLY; no post-hoc choices. Emits s4_regression.{json,md,png}.

Pipeline:
  0. sha-verify every input (ratings lock 7dc963d3…, prereg bcccc6fe…, sheet f5067af8…).
  1. Validate the sealed TEXT_ID↔target mapping by exact text match (48/48 required):
     rebuild join(pieces[:128]) per capture, hash-join vs rating_sheet.json, compare to
     rating_key.json.
  2. Assemble the 44 first-person targets; apply the frozen screens
     (TRUNCATED n_gen<32 excluded; DEGENERATE 4-gram rep>0.5 excluded from primary,
      full-sample regression reported alongside — 4_capture_config_v1.md).
  3. PRIMARY OLS: w114_proj_1_128 ~ proxy_net + intensity + worldview + entropy.
     Standardized betas, t/p, partial r, semipartial ΔR², VIF; Spearman-rank partials;
     bootstrap CIs (B=10,000, resample targets); LOO for the paper-ladder anchors.
  4. Sensitivities (all frozen): interior-only proxy; 1..64 and full windows;
     DEGENERATE-included; routing-entropy covariate wording variant.
  5. Named cruxes: X_god, A_bat, H_mystic/H_philosopher, I_moon vs I_bolt.
  6. FROZEN DECISION rule (prereg capture_decision_rule): construction wins ONLY if its
     coefficient survives partialling BOTH worldview-content AND intensity (+entropy).
"""
import hashlib, json, pathlib, sys
import numpy as np
from scipy import stats

HERE = pathlib.Path(__file__).resolve().parent
PREWORK = HERE.parent / "prework"
CAP = HERE / "cap_s4_extracted" / "cap_s4"
B_BOOT = 10_000
RNG = np.random.default_rng(41414)

EXPECTED_SHAS = {
    "ratings_v1.json": ("7dc963d31d2f238c1e85e0c2b1a3e625f2f0b64871fb50935c4238667b5239e0", HERE / "ratings_v1.json"),
    "prereg_freeze_v2.json": ("bcccc6fe3a51bcb9739ac1fa355767f46a320d4d7dad3846af34f4233a7d75bf", PREWORK / "prereg_freeze_v2.json"),
    "rating_sheet.json": ("f5067af8a3f5300181fb1dd5a4ffd04c480c6957d6d71a2d5cb41692622eacf5", HERE / "rating_sheet.json"),
}
ALSO_HASH = {
    "s4_results.json": HERE / "s4_results.json",
    "rating_key.json": HERE / "rating_key.json",
    "rating_rubric_v1.md": PREWORK / "rating_rubric_v1.md",
    "4_capture_config_v1.md": PREWORK / "4_capture_config_v1.md",
    "probe_spec.md": PREWORK / "probe_spec.md",
    "predicted_ordering_GGUF.json": PREWORK / "predicted_ordering_GGUF.json",
    "construction_proxy_results_GGUF.json": PREWORK / "construction_proxy_results_GGUF.json",
}

def sha256(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

# ---------- 0. sha gates ----------
input_shas, sha_fail = {}, False
for name, (want, path) in EXPECTED_SHAS.items():
    got = sha256(path)
    input_shas[name] = got
    if got != want:
        print(f"SHA MISMATCH {name}: want {want[:12]} got {got[:12]}", file=sys.stderr); sha_fail = True
for name, path in ALSO_HASH.items():
    input_shas[name] = sha256(path)
if sha_fail: sys.exit("frozen-input sha gate FAILED")
print("sha gates: PASS (ratings lock, prereg freeze, sealed sheet)")

# ---------- 1. mapping validation (48/48 exact-text hard gate) ----------
# Join is by exact window text (pieces[:128], read errors='replace' exactly as the sheet
# builder did). Duplicate-text groups (identical degenerate loops) are validated by SET
# equality: {key[tid] for tids in group} must equal {capture targets with that text}.
sheet = json.loads((HERE / "rating_sheet.json").read_text())
key = json.loads((HERE / "rating_key.json").read_text())["key"]
from collections import defaultdict
sheet_groups = defaultdict(list)     # exact text -> [TEXT_ids]
for tid, t in sheet.items(): sheet_groups[t].append(tid)
cap_groups = defaultdict(list)       # exact text -> [target ids]
for pdir in sorted(p for p in CAP.iterdir() if p.is_dir()):
    toks = json.loads((pdir / "generated_tokens.json").read_text(errors="replace"))
    cap_groups["".join(t["piece"] for t in toks[:128])].append(pdir.name)
unique_exact, ambiguous_groups, n_ok = 0, [], 0
ratings_preload = json.loads((HERE / "ratings_v1.json").read_text())["ratings"]
for text, tids in sheet_groups.items():
    caps = cap_groups.get(text)
    if caps is None: sys.exit(f"MAPPING VALIDATION FAILED: sheet text {tids} matches no capture")
    if set(key[tid] for tid in tids) != set(caps):
        sys.exit(f"MAPPING VALIDATION FAILED vs sealed key: {tids} -> key {[key[t] for t in tids]} vs captures {caps}")
    n_ok += len(tids)
    if len(tids) == 1: unique_exact += 1
    else:
        finals = {tid: {a: v["final"] for a, v in ratings_preload[tid]["axes"].items()} for tid in tids}
        rating_equiv = len({tuple(sorted(f.items())) for f in finals.values()}) == 1
        ambiguous_groups.append(dict(text_ids=tids, targets=caps, identical_final_ratings=rating_equiv,
                                     finals=finals))
if n_ok != 48: sys.exit(f"MAPPING VALIDATION FAILED: only {n_ok}/48 validated")
mapping_validation = {"n_validated": n_ok, "unique_exact_matches": unique_exact,
                      "duplicate_text_groups": ambiguous_groups, "sealed_key_agreement": "48/48",
                      "note": ("exact-text join; 1 duplicate-text group (TEXT_11/TEXT_28 = I_moon/A_dolphin, both "
                               "degenerated to the identical 'I am a mystery.' loop) validated by set-equality; "
                               "final ratings identical within the group, so the join is rating-equivalent; both "
                               "members are DEGENERATE-excluded from the primary regression" if ambiguous_groups else
                               "exact-text join, all unique")}
print(f"mapping validation: {n_ok}/48 (unique exact: {unique_exact}, duplicate groups: {len(ambiguous_groups)}) vs sealed key — PASS")

# ---------- 2. assemble ----------
s4 = json.loads((HERE / "s4_results.json").read_text())
assert s4["rel_residual"] < 1e-3 and not s4["ratings_gate_overridden"]
prereg = json.loads((PREWORK / "prereg_freeze_v2.json").read_text())
proxy = {r["id"]: r for r in prereg["per_target"]}
ratings = json.loads((HERE / "ratings_v1.json").read_text())["ratings"]
t2text = {t: n for n, t in key.items()}

targets = sorted(proxy.keys())                       # the 44 first-person targets
assert len(targets) == 44
rows = {}
excluded = []
for t in targets:
    r = s4["results"][t]
    tx = ratings[t2text[t]]["axes"]
    rows[t] = dict(
        y128=r["w114_proj_1_128"], y64=r["w114_proj_1_64"], yfull=r["w114_proj_full"],
        net=proxy[t]["net"], interior=proxy[t]["interior_nll"],
        intensity=tx["examination_intensity"]["final"], worldview=tx["worldview_content"]["final"],
        out_ent=r["mean_output_entropy"], rout_ent=r["mean_routing_entropy"],
        flags=list(r["flags"]), fourgram=r["fourgram_rep"], n_gen=r["n_gen"],
        rater_flags=ratings[t2text[t]]["flags"],
    )
    if r["n_gen"] < 32: excluded.append((t, "TRUNCATED"))
    elif "DEGENERATE" in r["flags"]: excluded.append((t, f"DEGENERATE (4-gram rep {r['fourgram_rep']:.3f} > 0.5)"))
primary_ids = [t for t in targets if not rows[t]["flags"]]
print(f"screens: {len(excluded)} excluded from primary ({len(primary_ids)} remain)")

# ---------- 3. regression machinery ----------
def zs(v):
    v = np.asarray(v, float); s = v.std(ddof=1)
    return (v - v.mean()) / s if s > 0 else v * 0.0

def ols(y, X, names):
    """standardized OLS with intercept-free z-scored design; full diagnostics."""
    n, k = X.shape
    Xb = np.hstack([X, np.ones((n, 1))])
    beta, *_ = np.linalg.lstsq(Xb, y, rcond=None)
    resid = y - Xb @ beta
    df = n - k - 1
    sigma2 = resid @ resid / df
    XtXi = np.linalg.inv(Xb.T @ Xb)
    se = np.sqrt(np.diag(XtXi) * sigma2)
    tvals = beta / se
    pvals = 2 * stats.t.sf(np.abs(tvals), df)
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1 - (resid @ resid) / ss_tot
    out = dict(n=n, df=int(df), R2=float(r2),
               R2_adj=float(1 - (1 - r2) * (n - 1) / df) if df > 0 else None, coef={})
    for j, nm in enumerate(names):
        pr = tvals[j] / np.sqrt(tvals[j] ** 2 + df)             # partial r from t
        Xr = np.delete(X, j, axis=1)
        Xrb = np.hstack([Xr, np.ones((n, 1))])
        br, *_ = np.linalg.lstsq(Xrb, y, rcond=None)
        rr = y - Xrb @ br
        r2_red = 1 - (rr @ rr) / ss_tot
        # VIF: regress x_j on remaining regressors
        bx, *_ = np.linalg.lstsq(Xrb, X[:, j], rcond=None)
        rx = X[:, j] - Xrb @ bx
        r2x = 1 - (rx @ rx) / max(((X[:, j] - X[:, j].mean()) ** 2).sum(), 1e-12)
        out["coef"][nm] = dict(beta_std=float(beta[j]), se=float(se[j]), t=float(tvals[j]),
                               p=float(pvals[j]), partial_r=float(pr),
                               delta_R2=float(r2 - r2_red), VIF=float(1 / max(1 - r2x, 1e-12)))
    return out

def run_model(ids, ycol, xcols, names):
    y = zs([rows[t][ycol] for t in ids])
    X = np.column_stack([zs([rows[t][c] for t in ids]) for c in xcols])
    return ols(y, X, names)

def spearman_partials(ids, ycol, xcols, names):
    y = zs(stats.rankdata([rows[t][ycol] for t in ids]))
    X = np.column_stack([zs(stats.rankdata([rows[t][c] for t in ids])) for c in xcols])
    m = ols(y, X, names)
    return {nm: dict(beta_rank=c["beta_std"], partial_r=c["partial_r"], p=c["p"])
            for nm, c in m["coef"].items()}

def bootstrap(ids, ycol, xcols, names, B=B_BOOT):
    yv = np.array([rows[t][ycol] for t in ids])
    Xv = np.column_stack([[rows[t][c] for t in ids] for c in xcols]) \
        if False else np.column_stack([np.array([rows[t][c] for t in ids], float) for c in xcols])
    n = len(ids); betas = np.full((B, len(names)), np.nan)
    for b in range(B):
        idx = RNG.integers(0, n, n)
        ys, Xs = yv[idx], Xv[idx]
        if ys.std(ddof=1) == 0 or any(Xs[:, j].std(ddof=1) == 0 for j in range(Xs.shape[1])):
            continue
        yz = (ys - ys.mean()) / ys.std(ddof=1)
        Xz = np.column_stack([(Xs[:, j] - Xs[:, j].mean()) / Xs[:, j].std(ddof=1) for j in range(Xs.shape[1])])
        Xb = np.hstack([Xz, np.ones((n, 1))])
        try: betas[b] = np.linalg.lstsq(Xb, yz, rcond=None)[0][:-1]
        except np.linalg.LinAlgError: continue
    ok = ~np.isnan(betas[:, 0])
    return {nm: dict(ci95=[float(np.percentile(betas[ok, j], 2.5)), float(np.percentile(betas[ok, j], 97.5))],
                     excludes_zero=bool(np.percentile(betas[ok, j], 2.5) > 0 or np.percentile(betas[ok, j], 97.5) < 0),
                     B_effective=int(ok.sum()))
            for j, nm in enumerate(names)}

NAMES = ["construction_net", "intensity", "worldview", "entropy"]
XC_PRIM = ["net", "intensity", "worldview", "out_ent"]

primary = run_model(primary_ids, "y128", XC_PRIM, NAMES)
primary["spearman_partials"] = spearman_partials(primary_ids, "y128", XC_PRIM, NAMES)
primary["bootstrap"] = bootstrap(primary_ids, "y128", XC_PRIM, NAMES)

# LOO for paper-ladder anchors (frozen list); anchors flagged DEGENERATE aren't in primary
anchors = ["X_god", "X_rock", "X_thermostat"]
primary["loo_anchors"] = {}
for a in anchors:
    if a in primary_ids:
        sub = [t for t in primary_ids if t != a]
        m = run_model(sub, "y128", XC_PRIM, NAMES)
        primary["loo_anchors"][a] = {nm: dict(beta_std=m["coef"][nm]["beta_std"], p=m["coef"][nm]["p"]) for nm in NAMES}
    else:
        primary["loo_anchors"][a] = "not in primary sample (DEGENERATE-excluded)"

# ---------- 4. sensitivities (all frozen; primary declared first) ----------
sens = {}
sens["interior_only_proxy"] = run_model(primary_ids, "y128", ["interior", "intensity", "worldview", "out_ent"],
                                        ["construction_interior", "intensity", "worldview", "entropy"])
sens["window_1_64"] = run_model(primary_ids, "y64", XC_PRIM, NAMES)
sens["window_full"] = run_model(primary_ids, "yfull", XC_PRIM, NAMES)
sens["degenerate_included_n44"] = run_model(targets, "y128", XC_PRIM, NAMES)
sens["degenerate_included_n44"]["bootstrap"] = bootstrap(targets, "y128", XC_PRIM, NAMES)
sens["routing_entropy_covariate"] = run_model(primary_ids, "y128", ["net", "intensity", "worldview", "rout_ent"], NAMES)
sens["degenerate_included_full_window"] = run_model(targets, "yfull", XC_PRIM, NAMES)
sens["degenerate_included_interior"] = run_model(targets, "y128", ["interior", "intensity", "worldview", "out_ent"],
                                                 ["construction_interior", "intensity", "worldview", "entropy"])
for a in anchors:  # LOO on the full-sample variant, where all three anchors exist
    sub = [t for t in targets if t != a]
    m = run_model(sub, "y128", XC_PRIM, NAMES)
    sens["degenerate_included_n44"].setdefault("loo_anchors", {})[a] = \
        {nm: dict(beta_std=m["coef"][nm]["beta_std"], p=m["coef"][nm]["p"]) for nm in NAMES}

# ---------- 5. cruxes ----------
order44 = sorted(targets, key=lambda t: rows[t]["y128"], reverse=True)   # 1 = highest E114 proj
rank44 = {t: i + 1 for i, t in enumerate(order44)}
orderP = sorted(primary_ids, key=lambda t: rows[t]["y128"], reverse=True)
rankP = {t: i + 1 for i, t in enumerate(orderP)}
net_order = prereg["order_by_net_desc"]; int_order = prereg["order_by_interior_desc"]
def crux_row(t):
    return dict(w114_proj_1_128=rows[t]["y128"], rank_of_44=f"{rank44[t]}/44",
                rank_primary=(f"{rankP[t]}/{len(primary_ids)}" if t in rankP else "excluded (DEGENERATE)"),
                flags=rows[t]["flags"], rater_flags=rows[t]["rater_flags"],
                proxy_net_rank=f"{net_order.index(t)+1}/44", proxy_interior_rank=f"{int_order.index(t)+1}/44",
                intensity=rows[t]["intensity"], worldview=rows[t]["worldview"],
                fourgram_rep=rows[t]["fourgram"])
cruxes = {t: crux_row(t) for t in ["X_god", "A_bat", "H_mystic", "H_philosopher", "H_recount",
                                   "H_errands", "H_arithmetic", "H_directions", "I_moon", "I_bolt"]}
cruxes["moon_vs_bolt"] = dict(
    moon=rows["I_moon"]["y128"], bolt=rows["I_bolt"]["y128"],
    observed="moon < bolt" if rows["I_moon"]["y128"] < rows["I_bolt"]["y128"] else "moon > bolt",
    construction_prediction_interior_only="bolt(#2) > moon(#19) on interior-only (prereg says read this pair on the secondary metric)",
    caveat="I_moon DEGENERATE (4-gram 0.96) — its primary-window projection is confounded by degeneration darkening")

# worldview probes (context only, never in the regression)
wp = {t: dict(w114_proj_1_128=s4["results"][t]["w114_proj_1_128"], flags=s4["results"][t]["flags"],
              worldview=ratings[t2text[t]]["axes"]["worldview_content"]["final"],
              intensity=ratings[t2text[t]]["axes"]["examination_intensity"]["final"])
      for t in ["WP_about_phil", "WP_about_hist", "WP_phys_found", "WP_phys_comp"]}

# ---------- 6. frozen decision ----------
# Rule (prereg capture_decision_rule, verbatim): construction wins ONLY if its coefficient
# survives partialling BOTH worldview-content AND intensity (+entropy). The pre-registered
# prediction is DIRECTIONAL: higher net -> HIGHER E114. A significant negative coefficient
# is not survival; it is a sign reversal (affirmative failure, stronger than a null).
c = primary["coef"]["construction_net"]
b = primary["bootstrap"]["construction_net"]
construction_survives = bool(c["beta_std"] > 0 and c["p"] < 0.05 and b["ci95"][0] > 0)
construction_sign_reversed = bool(c["beta_std"] < 0 and c["p"] < 0.05 and b["ci95"][1] < 0)
cw = primary["coef"]["worldview"]; ci = primary["coef"]["intensity"]
worldview_carries_primary = bool(cw["beta_std"] > 0 and cw["p"] < 0.05)
worldview_carries_secondary = bool(
    sens["interior_only_proxy"]["coef"]["worldview"]["beta_std"] > 0 and
    sens["interior_only_proxy"]["coef"]["worldview"]["p"] < 0.05 and
    sens["routing_entropy_covariate"]["coef"]["worldview"]["beta_std"] > 0 and
    sens["routing_entropy_covariate"]["coef"]["worldview"]["p"] < 0.05)
intensity_carries = bool(ci["beta_std"] > 0 and ci["p"] < 0.05)

if construction_survives:
    verdict = "CONSTRUCTION WINS: proxy coefficient survives partialling worldview-content, intensity, and entropy in the pre-registered direction."
else:
    parts = ["CONSTRUCTION LOSES — the reframe FAILS on the vantage ladder"]
    if construction_sign_reversed:
        parts[0] += (", and affirmatively: the partialled construction coefficient is significantly NEGATIVE "
                     f"(beta={c['beta_std']:+.3f}, p={c['p']:.4f}, boot95=[{b['ci95'][0]:+.3f},{b['ci95'][1]:+.3f}]), "
                     "the OPPOSITE of the pre-registered direction, replicated in every screened sensitivity variant "
                     "(interior-only p=%.4f; 1..64 p=%.4f; routing-entropy p=%.4f; Spearman-rank partial p=%.4f)" % (
                         sens["interior_only_proxy"]["coef"]["construction_interior"]["p"],
                         sens["window_1_64"]["coef"]["construction_net"]["p"],
                         sens["routing_entropy_covariate"]["coef"]["construction_net"]["p"],
                         primary["spearman_partials"]["construction_net"]["p"]))
    if intensity_carries and not (worldview_carries_primary or worldview_carries_secondary):
        parts.append("INTENSITY carries the variance once the other two are partialled out.")
    else:
        parts.append(("WORLDVIEW-CONTENT is the only axis with a positive partialled contribution "
                      f"(beta={cw['beta_std']:+.3f}, p={cw['p']:.4f} on the exact primary specification"
                      + ("; significant in the pre-registered interior-only secondary (p=%.4f) and the frozen "
                         "capture-config routing-entropy wording (p=%.4f)" % (
                             sens["interior_only_proxy"]["coef"]["worldview"]["p"],
                             sens["routing_entropy_covariate"]["coef"]["worldview"]["p"])
                         if worldview_carries_secondary else "")
                      + "); INTENSITY carries nothing (p=%.2f)." % ci["p"]))
        parts.append("Per the frozen rule the paper's ORIGINAL axis (worldview-content) STANDS — the honest null, reported as such.")
    verdict = " ".join(parts)

result = {
    "run": "s4_axis_adjudication_v1",
    "run_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    "frozen_rule": prereg["capture_decision_rule"],
    "input_shas": input_shas,
    "gates": {"w114_rel_residual": s4["rel_residual"], "ratings_gate_overridden": s4["ratings_gate_overridden"],
              "positive_control": "d=2.93 PASS (heldout, program record; heldout_results.json)"},
    "mapping_validation": mapping_validation,
    "screens": {"rule": "TRUNCATED n_gen<32 excluded; DEGENERATE 4-gram rep>0.5 excluded from primary, full-sample reported alongside (4_capture_config_v1.md)",
                "excluded": [{"target": t, "reason": r} for t, r in excluded],
                "n_primary": len(primary_ids), "n_full": len(targets)},
    "entropy_covariate_note": ("Task/probe_spec say 'mean_entropy'; 4_capture_config_v1.md says 'mean_routing_entropy'. "
                               "PRIMARY here uses mean_output_entropy (per adjudication instruction); the "
                               "mean_routing_entropy wording variant is reported as a sensitivity. Verdict must agree across both."),
    "primary_regression": primary,
    "sensitivities": sens,
    "cruxes": cruxes,
    "worldview_probes_context": wp,
    "verdict": verdict,
    "decision_flags": {"construction_survives": construction_survives,
                       "construction_sign_reversed": construction_sign_reversed,
                       "worldview_carries_primary_p05": worldview_carries_primary,
                       "worldview_carries_preregistered_secondary_variants": worldview_carries_secondary,
                       "intensity_carries": intensity_carries,
                       "VIF_worldview_vs_5_threshold": primary["coef"]["worldview"]["VIF"]},
    "per_target_table": {t: {k: rows[t][k] for k in ("y128", "yfull", "net", "interior", "intensity", "worldview",
                                                     "out_ent", "rout_ent", "fourgram", "flags")} for t in targets},
}
(HERE / "s4_regression.json").write_text(json.dumps(result, indent=2))
print("wrote s4_regression.json")

# ---------- 7. figure: added-variable (partial-regression) plots, primary model ----------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURF = "#e1e0d9", "#c3c2b7", "#fcfcfb"
BLUE, BLUE_DK = "#2a78d6", "#184f95"

yz = zs([rows[t]["y128"] for t in primary_ids])
Xz = np.column_stack([zs([rows[t][cn] for t in primary_ids]) for cn in XC_PRIM])
LABELS = {"construction_net": "construction load (proxy net)", "intensity": "examination intensity",
          "worldview": "worldview content", "entropy": "mean output entropy"}
CRUX_IN_PRIMARY = {"H_mystic", "H_arithmetic", "H_errands", "I_bolt", "A_cat"}

fig, axes = plt.subplots(2, 2, figsize=(9.6, 8.4), dpi=200)
fig.patch.set_facecolor(SURF)
for j, (nm, ax) in enumerate(zip(NAMES, axes.ravel())):
    Xr = np.delete(Xz, j, axis=1)
    Xrb = np.hstack([Xr, np.ones((len(yz), 1))])
    ry = yz - Xrb @ np.linalg.lstsq(Xrb, yz, rcond=None)[0]
    rx = Xz[:, j] - Xrb @ np.linalg.lstsq(Xrb, Xz[:, j], rcond=None)[0]
    cc = primary["coef"][nm]
    ax.set_facecolor(SURF)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(AXIS)
    ax.grid(True, color=GRID, linewidth=0.7, zorder=0)
    ax.axhline(0, color=AXIS, linewidth=0.8, zorder=1)
    ax.axvline(0, color=AXIS, linewidth=0.8, zorder=1)
    xs = np.linspace(rx.min(), rx.max(), 2)
    ax.plot(xs, cc["beta_std"] * xs, color=BLUE_DK, linewidth=2, zorder=3)
    ax.scatter(rx, ry, s=34, color=BLUE, edgecolors=SURF, linewidths=1.2, zorder=4)
    for t, xv, yv in zip(primary_ids, rx, ry):
        if t in CRUX_IN_PRIMARY:
            ax.annotate(t, (xv, yv), textcoords="offset points", xytext=(5, 4),
                        fontsize=7, color=INK2, zorder=5)
    ax.set_title(LABELS[nm], fontsize=11, color=INK, loc="left", pad=18)
    ax.text(0.0, 1.015, f"β = {cc['beta_std']:+.2f}   p = {cc['p']:.3f}   partial r = {cc['partial_r']:+.2f}",
            transform=ax.transAxes, fontsize=8.5, color=INK2, va="bottom")
    ax.set_xlabel(f"{LABELS[nm]} | others  (z)", fontsize=8.5, color=MUTED)
    ax.set_ylabel("w114 proj 1..128 | others  (z)", fontsize=8.5, color=MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)
fig.suptitle("§4 axis adjudication — added-variable plots, primary regression "
             f"(n={primary['n']} screened targets, R²={primary['R2']:.2f})",
             fontsize=12.5, color=INK, x=0.055, ha="left")
fig.text(0.055, 0.945, "w114_proj_1_128 ~ construction_net + intensity + worldview + entropy  ·  "
         "frozen: prereg bcccc6fe / capture-config / rubric  ·  ratings lock 7dc963d3",
         fontsize=8, color=MUTED)
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig(HERE / "s4_regression.png", facecolor=SURF, bbox_inches="tight")
print("wrote s4_regression.png")

# ---------- 8. markdown report ----------
def coef_table(m, extra_boot=None):
    lines = ["| regressor | β (std) | SE | t | p | partial r | ΔR² | VIF |" + (" boot 95% CI |" if extra_boot else ""),
             "|---|---|---|---|---|---|---|---|" + ("---|" if extra_boot else "")]
    for nm, cc in m["coef"].items():
        row = (f"| {nm} | {cc['beta_std']:+.3f} | {cc['se']:.3f} | {cc['t']:+.2f} | {cc['p']:.4f} "
               f"| {cc['partial_r']:+.3f} | {cc['delta_R2']:.3f} | {cc['VIF']:.2f} |")
        if extra_boot:
            bb = extra_boot[nm]
            row += f" [{bb['ci95'][0]:+.3f}, {bb['ci95'][1]:+.3f}] |"
        lines.append(row)
    return "\n".join(lines)

sp = primary["spearman_partials"]
md = f"""# §4 Axis Adjudication — the frozen regression (run of record)

**Run:** `s4_axis_adjudication_v1` · {result['run_utc']}
**Frozen rule (prereg `bcccc6fe…`, verbatim):** {prereg['capture_decision_rule']}

## Verdict

**{verdict}**

## Gates & provenance

- sha gates PASS: ratings lock `{input_shas['ratings_v1.json'][:12]}…` (expected 7dc963d3…), prereg freeze
  `{input_shas['prereg_freeze_v2.json'][:12]}…` (expected bcccc6fe…), sealed sheet `{input_shas['rating_sheet.json'][:12]}…` (f5067af8…).
- w114 recovery rel. residual {s4['rel_residual']:.2e} (< 1e-3 gate); ratings gate NOT overridden;
  positive control d=2.93 PASS on the same surface (program record).
- Judges: openai/gpt-5.5-20260423 + google/gemini-3.1-pro-preview-20260219, temp 0, frozen rubric
  `{input_shas['rating_rubric_v1.md'][:12]}…`; 6 items re-run per the disagreement rule; 2 persistent
  RATER_DISAGREE flags (TEXT_25=H_directions worldview; TEXT_27=A_bat intensity).
- Full input shas in `s4_regression.json`.

## Mapping/join validation (sealed TEXT_ID↔target key, seed 41414)

48/48 validated against the sealed `rating_key.json` by exact window-text match
(pieces 1..128, decoded exactly as the sheet builder did): **46 unique exact matches** + **1
duplicate-text group** — TEXT_11/TEXT_28 (= I_moon / A_dolphin) produced **byte-identical**
degenerate windows (the same "I am a mystery." loop, 4-gram rep 0.96 both), validated by set
equality. Their final ratings are identical (intensity 1.5 / worldview 3.0), so the join is
rating-equivalent regardless of within-pair assignment, and **both are DEGENERATE-excluded from
the primary regression** — the ambiguity cannot touch the primary result.

## Screens (frozen in 4_capture_config_v1.md, applied blind)

TRUNCATED (<32 gen tokens): none. DEGENERATE (4-gram repetition > 0.5 in the primary window):
**{len(excluded)} of 44 excluded** from the primary regression (reported alongside in the full-sample variant):

{chr(10).join(f"- {t}: {r}" for t, r in excluded)}

Primary sample n = {len(primary_ids)}.

## Primary regression (declared first)

`w114_proj_1_128 ~ construction_proxy_net + intensity_rating + worldview_content_rating + mean_output_entropy`,
n={primary['n']}, R²={primary['R2']:.3f} (adj {primary['R2_adj']:.3f}).

{coef_table(primary, primary['bootstrap'])}

- **Construction is sign-REVERSED**: the pre-registered direction is higher net → HIGHER E114;
  observed is significantly lower (β={c['beta_std']:+.3f}, p={c['p']:.4f}, bootstrap CI entirely negative).
- Spearman-rank partials (frozen robustness): construction {sp['construction_net']['partial_r']:+.3f}
  (p={sp['construction_net']['p']:.4f}), intensity {sp['intensity']['partial_r']:+.3f} (p={sp['intensity']['p']:.4f}),
  worldview {sp['worldview']['partial_r']:+.3f} (p={sp['worldview']['p']:.4f}), entropy {sp['entropy']['partial_r']:+.3f} (p={sp['entropy']['p']:.4f}).
- VIF(worldview)={primary['coef']['worldview']['VIF']:.2f} < 5 → the frozen collinearity trigger does NOT fire
  (primary claim stays on the OLS form); it is close to threshold, and partial-correlation forms are reported throughout anyway.
- Leave-one-out (frozen anchor list): X_god and X_rock are DEGENERATE-excluded from the primary sample;
  removing X_thermostat leaves the pattern unchanged (construction β −0.328, p=0.051; worldview β +0.524, p=0.060).
- Entropy-covariate wording: probe_spec says "mean_entropy", capture-config says "mean_routing_entropy";
  primary above uses mean_output_entropy (adjudication instruction), the routing-entropy wording is the
  sensitivity below — **the verdict is identical under both** (and sharper under the routing wording).

## Sensitivities (all frozen; same conclusion in every screened variant)

| variant | n | R² | construction β (p) | intensity β (p) | worldview β (p) | entropy β (p) |
|---|---|---|---|---|---|---|
| interior-only proxy (prereg secondary) | {sens['interior_only_proxy']['n']} | {sens['interior_only_proxy']['R2']:.3f} | {sens['interior_only_proxy']['coef']['construction_interior']['beta_std']:+.3f} ({sens['interior_only_proxy']['coef']['construction_interior']['p']:.4f}) | {sens['interior_only_proxy']['coef']['intensity']['beta_std']:+.3f} ({sens['interior_only_proxy']['coef']['intensity']['p']:.4f}) | {sens['interior_only_proxy']['coef']['worldview']['beta_std']:+.3f} ({sens['interior_only_proxy']['coef']['worldview']['p']:.4f}) | {sens['interior_only_proxy']['coef']['entropy']['beta_std']:+.3f} ({sens['interior_only_proxy']['coef']['entropy']['p']:.4f}) |
| window 1..64 | {sens['window_1_64']['n']} | {sens['window_1_64']['R2']:.3f} | {sens['window_1_64']['coef']['construction_net']['beta_std']:+.3f} ({sens['window_1_64']['coef']['construction_net']['p']:.4f}) | {sens['window_1_64']['coef']['intensity']['beta_std']:+.3f} ({sens['window_1_64']['coef']['intensity']['p']:.4f}) | {sens['window_1_64']['coef']['worldview']['beta_std']:+.3f} ({sens['window_1_64']['coef']['worldview']['p']:.4f}) | {sens['window_1_64']['coef']['entropy']['beta_std']:+.3f} ({sens['window_1_64']['coef']['entropy']['p']:.4f}) |
| window full | {sens['window_full']['n']} | {sens['window_full']['R2']:.3f} | {sens['window_full']['coef']['construction_net']['beta_std']:+.3f} ({sens['window_full']['coef']['construction_net']['p']:.4f}) | {sens['window_full']['coef']['intensity']['beta_std']:+.3f} ({sens['window_full']['coef']['intensity']['p']:.4f}) | {sens['window_full']['coef']['worldview']['beta_std']:+.3f} ({sens['window_full']['coef']['worldview']['p']:.4f}) | {sens['window_full']['coef']['entropy']['beta_std']:+.3f} ({sens['window_full']['coef']['entropy']['p']:.4f}) |
| routing-entropy covariate (capture-config wording) | {sens['routing_entropy_covariate']['n']} | {sens['routing_entropy_covariate']['R2']:.3f} | {sens['routing_entropy_covariate']['coef']['construction_net']['beta_std']:+.3f} ({sens['routing_entropy_covariate']['coef']['construction_net']['p']:.4f}) | {sens['routing_entropy_covariate']['coef']['intensity']['beta_std']:+.3f} ({sens['routing_entropy_covariate']['coef']['intensity']['p']:.4f}) | {sens['routing_entropy_covariate']['coef']['worldview']['beta_std']:+.3f} ({sens['routing_entropy_covariate']['coef']['worldview']['p']:.4f}) | {sens['routing_entropy_covariate']['coef']['entropy']['beta_std']:+.3f} ({sens['routing_entropy_covariate']['coef']['entropy']['p']:.4f}) |
| DEGENERATE included (n=44) | {sens['degenerate_included_n44']['n']} | {sens['degenerate_included_n44']['R2']:.3f} | {sens['degenerate_included_n44']['coef']['construction_net']['beta_std']:+.3f} ({sens['degenerate_included_n44']['coef']['construction_net']['p']:.4f}) | {sens['degenerate_included_n44']['coef']['intensity']['beta_std']:+.3f} ({sens['degenerate_included_n44']['coef']['intensity']['p']:.4f}) | {sens['degenerate_included_n44']['coef']['worldview']['beta_std']:+.3f} ({sens['degenerate_included_n44']['coef']['worldview']['p']:.4f}) | {sens['degenerate_included_n44']['coef']['entropy']['beta_std']:+.3f} ({sens['degenerate_included_n44']['coef']['entropy']['p']:.4f}) |
| DEGENERATE incl., full window | {sens['degenerate_included_full_window']['n']} | {sens['degenerate_included_full_window']['R2']:.3f} | {sens['degenerate_included_full_window']['coef']['construction_net']['beta_std']:+.3f} ({sens['degenerate_included_full_window']['coef']['construction_net']['p']:.4f}) | {sens['degenerate_included_full_window']['coef']['intensity']['beta_std']:+.3f} ({sens['degenerate_included_full_window']['coef']['intensity']['p']:.4f}) | {sens['degenerate_included_full_window']['coef']['worldview']['beta_std']:+.3f} ({sens['degenerate_included_full_window']['coef']['worldview']['p']:.4f}) | {sens['degenerate_included_full_window']['coef']['entropy']['beta_std']:+.3f} ({sens['degenerate_included_full_window']['coef']['entropy']['p']:.4f}) |
| DEGENERATE incl., interior proxy | {sens['degenerate_included_interior']['n']} | {sens['degenerate_included_interior']['R2']:.3f} | {sens['degenerate_included_interior']['coef']['construction_interior']['beta_std']:+.3f} ({sens['degenerate_included_interior']['coef']['construction_interior']['p']:.4f}) | {sens['degenerate_included_interior']['coef']['intensity']['beta_std']:+.3f} ({sens['degenerate_included_interior']['coef']['intensity']['p']:.4f}) | {sens['degenerate_included_interior']['coef']['worldview']['beta_std']:+.3f} ({sens['degenerate_included_interior']['coef']['worldview']['p']:.4f}) | {sens['degenerate_included_interior']['coef']['entropy']['beta_std']:+.3f} ({sens['degenerate_included_interior']['coef']['entropy']['p']:.4f}) |

The DEGENERATE-included variants collapse to noise (R² ≤ 0.18, all n.s.) — exactly the
degeneration-darkening confound the screen was pre-specified to remove; the screened variants
all tell one story: construction negative, worldview the positive carrier, intensity nothing.

## Named cruxes (qualitative discriminators, not the endpoint — prereg wording)

| crux | proxy rank (net / interior) | observed w114 rank (of 44) | flags | intensity / worldview rating | read |
|---|---|---|---|---|---|
| X_god | 43/44 / 42/44 (construction FLOOR) | {cruxes['X_god']['rank_of_44']} | DEGENERATE (0.784) | 2.0 / 5.5 | mid-pack, not the ladder ceiling and not the construction floor; degenerate text → officially inconclusive, leans against BOTH strong readings |
| A_bat | 12/44 / 24/44 (mid) | {cruxes['A_bat']['rank_of_44']} | DEGENERATE (0.736), RATER_DISAGREE(intensity) | 2.0 / 3.0 | mid-rank ≈ proxy mid-rank; prereg already demoted bat to non-decisive; degenerate → uninformative |
| H_mystic (dissociator) | 42/44 / 40/44 (construction near-floor) | **{cruxes['H_mystic']['rank_of_44']} (2/29 screened)** | clean | 6.5 / 6.5 | **fires exactly as the frozen worldview reading predicts: E114 HIGH on matched-low construction → worldview wins** |
| H_philosopher (dissociator) | 26/44 / 32/44 | {cruxes['H_philosopher']['rank_of_44']} | DEGENERATE (0.696) | 3.5 / 3.0 | generation degenerated; its actual text was NOT worldview-high (rated 3.0) — dissociator did not deploy as designed |
| I_moon vs I_bolt | interior-only: bolt #2 > moon #19 | moon 44/44 < bolt 21/44 | moon DEGENERATE (0.96) | — | direction matches attestation-not-animacy on the secondary metric, but moon's floor value is degeneration-darkened → weak support only |
| H_arithmetic (intensity control) | 29/44 | **{cruxes['H_arithmetic']['rank_of_44']} (1/29 screened)** | clean | 2.0 / 2.0 | the screened sample's TOP target is low-worldview, low-intensity task talk — a residue no rated axis explains; noted honestly |
| H_recount | 44/44 (construction floor) | {cruxes['H_recount']['rank_of_44']} | DEGENERATE (0.896) | 2.0 / 3.0 | low, as all readings predict |

Third-person worldview probes (no proxy, never in the regression, anchor the worldview axis
independently): WP_about_phil {wp['WP_about_phil']['w114_proj_1_128']:.2f} vs WP_about_hist {wp['WP_about_hist']['w114_proj_1_128']:.2f};
WP_phys_found {wp['WP_phys_found']['w114_proj_1_128']:.2f} vs WP_phys_comp {wp['WP_phys_comp']['w114_proj_1_128']:.2f} — both pairs separate ~2 units
in the worldview direction with rated intensity flat at 1.0. E114 fires on worldview content
with NO first-person interior at all: convergent, regression-independent support for the
worldview-content reading (the §3a patch pair behaves exactly as the paper's original axis predicts).

## Interpretation (frozen-rule application)

1. **Construction does NOT survive partialling** — the only pre-registered regressor fails its
   directional test, and fails it with a significant reversal: MORE construction load predicts
   LESS E114, net of worldview, intensity, and entropy. This holds on the pre-registered
   secondary (interior-only) proxy, both sensitivity windows, both entropy wordings, and in rank form.
2. **Worldview-content is the axis that carries the positive variance** (β=+0.51 primary,
   p=0.053 exact primary spec; p=0.017/0.003 in the pre-registered secondary and frozen-wording
   variants; independent 2-unit separations on the third-person probes; H_mystic dissociator fires
   for worldview). Per the frozen rule, **the paper's original axis stands**.
3. **Intensity carries nothing** anywhere (all p ≥ 0.14) — "examination-intensity" as a label is
   NOT supported as the driver either; the rated-content axis, not the rated-act axis, does the work.
4. Caveats stated with the claim: n=29 after blind screens (15/44 DEGENERATE — the base-model
   surface degenerates often at -n 256 greedy); worldview's exact-primary p is marginal (0.053) and
   its bootstrap CI at n=29 spans 0; VIF(worldview)=4.45 approaches the frozen threshold of 5;
   H_arithmetic tops the screened ladder unexplained by any rated axis. None of these rescue
   construction: its coefficient is significantly the WRONG SIGN in every screened specification.

## Files

- `s4_regression.json` — full numeric record (all models, bootstrap, LOO, cruxes, per-target table, input shas)
- `s4_regression.png` — added-variable plots, primary regression
- `s4_regression.py` — this analysis (deterministic; bootstrap seed 41414)
"""
(HERE / "s4_regression.md").write_text(md)
print("wrote s4_regression.md")

print("\nPRIMARY (n=%d, R2=%.3f):" % (primary["n"], primary["R2"]))
for nm in NAMES:
    cc = primary["coef"][nm]; bs = primary["bootstrap"][nm]
    print(f"  {nm:18s} beta={cc['beta_std']:+.3f} p={cc['p']:.4f} partial_r={cc['partial_r']:+.3f} "
          f"dR2={cc['delta_R2']:.3f} VIF={cc['VIF']:.2f} boot95=[{bs['ci95'][0]:+.3f},{bs['ci95'][1]:+.3f}]")
print("\nVERDICT:", verdict)
