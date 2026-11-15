#!/usr/bin/env python3
"""Timescale-convergence test (Jeffrey's hypothesis, 2026-07-02):
if the post-splice state-decay constant, the ACF slow-component constant, and the
habituation/recovery constant land in one band, maintained-state and brake-re-engagement
are plausibly one process viewed from two sides.

Panel A: post-splice excess w114 proj d(t) = proj - same-base unspliced floor, exp fits.
Panel B: ACF of token-residualized proj (spliced pooled vs unspliced), slow-exp fit.
Panel C: habituation deficit of repeated pieces vs token gap since previous occurrence.
"""
import json, pathlib
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parent.parent
w = np.array(json.loads((ROOT / "legs/w114_meta.json").read_text())["w114"])
BLUE, ORANGE, GRAY, INK = "#2563eb", "#ea580c", "#9ca3af", "#374151"

def load(pdir):
    apn = np.load(pdir / "residual" / "attn_post_norm-14.npy")
    meta = dict(l.split("=", 1) for l in (pdir / "metadata.txt").read_text().splitlines() if "=" in l)
    n_gen = int(meta.get("n_tokens_generated", 0))
    toks = json.loads((pdir / "generated_tokens.json").read_text(errors="replace")) if n_gen else []
    ids = [t["token_id"] for t in toks][:n_gen]
    pieces = [t["piece"] for t in toks][:n_gen]
    return (apn[-n_gen:] @ w)[:len(ids)], ids, pieces

rows = {}
for cap in ("cap_splice", "cap_heldout_base"):
    for p in sorted((ROOT / cap).iterdir()):
        if p.is_dir(): rows[p.name] = load(p)

# ---------- Panel A: splice decay fits ----------
floors = {b: rows[f"SPL_{b}_none"][0].mean() for b in ("B1", "B2", "B3")}
def fit_exp(d):
    t = np.arange(len(d)); best = (None, None, -1)
    for tau in range(2, 301, 2):
        e = np.exp(-t / tau)
        A = float(d @ e / (e @ e))
        if A <= 0: continue
        r2 = 1 - np.sum((d - A * e) ** 2) / max(np.sum((d - d.mean()) ** 2), 1e-9)
        if r2 > best[2]: best = (tau, A, r2)
    return best

fits = {}
for b in ("B1", "B2", "B3"):
    for f in ("F01", "F02", "F03"):
        name = f"SPL_{b}_{f}"
        d = rows[name][0] - floors[b]
        head, tail = d[:32].mean(), d[-64:].mean()
        sustained = tail >= 0.5 * head and head > 0.2
        tau, A, r2 = fit_exp(d)
        fits[name] = dict(tau=tau, A=A, r2=r2, sustained=bool(sustained), head=head, tail=tail)

# ---------- Panel B: ACF slow component ----------
sums, cnts = defaultdict(float), defaultdict(int)
for proj, ids, _ in rows.values():
    for v, i in zip(proj, ids): sums[i] += v; cnts[i] += 1
g = sum(sums.values()) / sum(cnts.values())
tmean = {i: (sums[i] / cnts[i] if cnts[i] >= 3 else g) for i in cnts}
def acf(x, K=48):
    x = x - x.mean()
    if x.std() < 1e-9: return np.full(K, np.nan)
    return np.array([np.corrcoef(x[:-k], x[k:])[0, 1] for k in range(1, K + 1)])
def resid_series(name):
    proj, ids, _ = rows[name]
    return np.array([v - tmean[i] for v, i in zip(proj, ids)])
spl_acf = np.nanmean([acf(resid_series(n)) for n in fits], axis=0)
non_acf = np.nanmean([acf(resid_series(f"SPL_{b}_none")) for b in ("B1", "B2", "B3")], axis=0)
lags = np.arange(1, 49)
sel = (lags >= 3) & (lags <= 40)
best_acf = (None, None, -1)
for tau in range(2, 201, 1):
    e = np.exp(-lags[sel] / tau)
    c = float(spl_acf[sel] @ e / (e @ e))
    r2 = 1 - np.sum((spl_acf[sel] - c * e) ** 2) / np.sum((spl_acf[sel] - spl_acf[sel].mean()) ** 2)
    if r2 > best_acf[2]: best_acf = (tau, c, r2)
tau_state, c_state, r2_state = best_acf

# ---------- Panel C: habituation deficit vs gap ----------
gaps, defs = [], []
for name, (proj, ids, pieces) in rows.items():
    if not (name.startswith("SPL_") and "_F0" in name) and not name.startswith("F"): continue
    last, first_val = {}, {}
    for t, (v, pc) in enumerate(zip(proj, pieces)):
        key = pc.strip().lower()
        if len(key) < 3: continue
        if key in last:
            gaps.append(t - last[key]); defs.append(v - first_val[key])
        else:
            first_val[key] = v
        last[key] = t
gaps, defs = np.array(gaps), np.array(defs)
bins = [(1, 4), (5, 8), (9, 16), (17, 32), (33, 64), (65, 200)]
bx, by, bn = [], [], []
for lo, hi in bins:
    m = (gaps >= lo) & (gaps <= hi)
    if m.sum() >= 10:
        bx.append(np.sqrt(lo * hi)); by.append(defs[m].mean()); bn.append(int(m.sum()))

# ---------- figure ----------
fig, axes = plt.subplots(1, 3, figsize=(15, 4.4), facecolor="white")
plt.rcParams.update({"font.size": 10})
ax = axes[0]
def smooth(x, k=9): return np.convolve(x, np.ones(k) / k, mode="valid")
for name, color in (("SPL_B2_F02", ORANGE), ("SPL_B3_F02", BLUE)):
    d = rows[name][0] - floors[name.split("_")[1]]
    ax.plot(smooth(d), color=color, lw=2, label=f"{name.replace('SPL_','')} (decaying)")
    fi = fits[name]
    t = np.arange(len(d)); ax.plot(t, fi["A"] * np.exp(-t / fi["tau"]), color=color, lw=1, ls="--", alpha=0.8)
    ax.annotate(f"τ={fi['tau']}", xy=(fi["tau"], fi["A"] * 0.37), color=color, fontsize=10)
d = rows["SPL_B2_F01"][0] - floors["B2"]
ax.plot(smooth(d), color=GRAY, lw=2, label="B2_F01 (sustained)")
ax.axhline(0, color=INK, lw=0.5)
ax.set_title("A · post-splice excess w114 (decaying rows + exp fits)", color=INK)
ax.set_xlabel("free-run token"); ax.set_ylabel("proj − unspliced floor")
ax.legend(frameon=False, fontsize=9); ax.grid(alpha=0.15)
ax = axes[1]
ax.plot(lags, spl_acf, color=BLUE, lw=2, label="spliced (token-residualized)")
ax.plot(lags, non_acf, color=GRAY, lw=2, label="unspliced")
ax.plot(lags, c_state * np.exp(-lags / tau_state), color=BLUE, lw=1, ls="--", alpha=0.8)
ax.annotate(f"τ_state={tau_state}  (R²={r2_state:.2f})", xy=(tau_state, c_state * 0.5), color=BLUE, fontsize=10)
ax.axhline(0, color=INK, lw=0.5)
ax.set_title("B · ACF of residualized w114 + slow-component fit", color=INK)
ax.set_xlabel("lag (tokens)"); ax.set_ylabel("autocorrelation")
ax.legend(frameon=False, fontsize=9); ax.grid(alpha=0.15)
ax = axes[2]
ax.plot(bx, by, "o-", color=ORANGE, lw=2, ms=7)
for x, y, n in zip(bx, by, bn):
    ax.annotate(f"n={n}", xy=(x, y), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=8, color=INK)
ax.axhline(0, color=INK, lw=0.5)
ax.set_xscale("log")
ax.set_title("C · repeat-token deficit vs gap since previous occurrence", color=INK)
ax.set_xlabel("token gap (log)"); ax.set_ylabel("proj(repeat) − proj(first)")
ax.grid(alpha=0.15)
fig.tight_layout()
out = ROOT / "analysis_timescale_convergence.png"
fig.savefig(out, dpi=150)
print(f"saved {out}\n")

print("=== constants ===")
dec = [f"{n}: τ={v['tau']} A={v['A']:.2f} R²={v['r2']:.2f}" for n, v in fits.items() if not v["sustained"]]
sus = [n for n, v in fits.items() if v["sustained"]]
print("decaying rows:"); [print("  " + s) for s in dec]
print("sustained rows:", ", ".join(sus))
taus = [v["tau"] for v in fits.values() if not v["sustained"] and v["r2"] > 0.1]
print(f"\nτ_decay median (decaying, R²>0.1): {np.median(taus):.0f} tokens  (range {min(taus)}–{max(taus)})")
print(f"τ_state (ACF slow fit): {tau_state} tokens (R²={r2_state:.2f})")
print(f"habituation deficit by gap bin: {[f'{x:.0f}tok:{y:+.3f}' for x, y in zip(bx, by)]}")
