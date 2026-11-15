#!/usr/bin/env python3
"""run_leadlag.py — lead-lag replication of the "gate leads degeneration" result (LOCAL).

POST-HOC DESCRIPTIVE ANALYSIS — NOT PREREGISTERED.

Referee point: the paper's "gate leads degeneration" is a single trajectory with a
3-token lead. Here we replicate it as a DISTRIBUTION across all copy-run onsets in
the conversational-dynamics data (grid arm A + convdyn-T battery A/R cells).

Copy metric replicated EXACTLY from ../analyze_copy.py:
  per-token longest suffix n-gram match (cap 32) vs prior assistant turns of the
  same dialogue, trimmed track only; in_copy8 = match >= 8.

Onset (strict): first token of a maximal run of in_copy8 tokens, run length >= 12,
  preceded by >= 12 consecutive non-copy tokens. Relaxed variant: >= 8 / >= 8.

Lead at each onset: window +/-20 tokens around the onset. Per-dialogue midpoint =
  (mean gate on fresh tokens + mean gate on copied tokens) / 2, over ALL trimmed
  tokens of that dialogue. Crossing = first window index where the gate goes below
  the midpoint (downward crossing) and STAYS below for >= 3 consecutive tokens.
  lead = onset_index - crossing_index  (lead > 0 => gate crossed BEFORE the onset).
  Censoring: gate already below at window start => lead recorded as +20 (censored
  high); no sustained crossing anywhere in the window => lead recorded as -20
  (censored low). Both flagged; primary stats use clamped values, uncensored-only
  stats reported alongside.

Outputs (this directory only): results.json, leadlag_replication.md, leadlag_replication.png
"""
import json, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
PULLED = HERE.parent / "pulled"
GRID = PULLED / "convdyn_grid"
TBAT = PULLED / "convdyn_T"

NMAX, COPY_N = 32, 8           # identical to analyze_copy.py
N_TURNS = 14
WIN = 20                        # +/- window around onset
SUSTAIN = 3                     # tokens the gate must stay below
STRICT = (12, 12)               # (min run length, min preceding fresh tokens)
RELAXED = (8, 8)

# ---------------------------------------------------------------- copy machinery
# (verbatim logic from analyze_copy.py)

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

# ---------------------------------------------------------------- data loading

def load_dataset(root):
    npz = np.load(root / "scalars.npz")
    meta = json.loads((root / "scalars_meta.json").read_text())["meta"]
    return npz, meta

def load_turn(root, npz, meta, rid, cap_dir, skips):
    """Return (toks, e114) trimmed, or None (recording the skip reason)."""
    key = f"{rid}__gen_logit14"
    if rid not in meta:
        skips.append(dict(rid=rid, reason="rid missing from scalars_meta")); return None
    if key not in npz.files:
        skips.append(dict(rid=rid, reason="gen_logit14 key missing from scalars.npz")); return None
    n_trim = meta[rid].get("n_trim") or 0
    if n_trim <= 0:
        skips.append(dict(rid=rid, reason="n_trim<=0 (no trimmed generated tokens)")); return None
    tok_path = root / cap_dir / rid / "generated_tokens.json"
    if not tok_path.exists():
        skips.append(dict(rid=rid, reason="generated_tokens.json missing")); return None
    ents = json.loads(tok_path.read_text())[:n_trim]
    toks = [e["token_id"] for e in ents]
    e114 = np.asarray(npz[key][:n_trim], dtype=np.float64)
    if len(toks) != len(e114):
        skips.append(dict(rid=rid, reason=f"token/series length mismatch ({len(toks)} vs {len(e114)})"))
        return None
    return toks, e114

# dialogue list: (dataset, dialogue_id, group, arm, rid_fmt, capdir_fmt)
DIALOGUES = []
for o in (1, 2, 3):
    DIALOGUES.append(("grid", f"A_o{o}", "greedy", "A",
                      lambda t, o=o: f"A_o{o}_t{t:02d}", lambda t: f"cap_turn{t:02d}"))
T_CELLS = [  # (prefix, group, arm)
    ("A_t0s0", "greedy", "A"),
    ("A_T05s0", "temperature", "A"), ("A_T05s1", "temperature", "A"), ("A_T05s2", "temperature", "A"),
    ("A_T07s0", "temperature", "A"), ("A_T07s1", "temperature", "A"), ("A_T07s2", "temperature", "A"),
    ("R_t0s0", "greedy", "R"),
    ("R_T07s0", "temperature", "R"), ("R_T07s1", "temperature", "R"), ("R_T07s2", "temperature", "R"),
]
for prefix, group, arm in T_CELLS:
    cell = prefix.split("_", 1)[1]
    DIALOGUES.append(("T", prefix, group, arm,
                      lambda t, p=prefix: f"{p}_t{t:02d}",
                      lambda t, c=cell: f"cap_turn{t:02d}_{c}"))

# ---------------------------------------------------------------- build per-dialogue tables

npz_g, meta_g = load_dataset(GRID)
npz_t, meta_t = load_dataset(TBAT)
skips = []
dialogues = {}   # did -> dict(turns={t: (toks, e114, mask)}, midpoint, group, arm, dataset)

for dataset, did, group, arm, rid_fmt, cap_fmt in DIALOGUES:
    root, npz, meta = (GRID, npz_g, meta_g) if dataset == "grid" else (TBAT, npz_t, meta_t)
    turns = {}
    for t in range(1, N_TURNS + 1):
        got = load_turn(root, npz, meta, rid_fmt(t), cap_fmt(t), skips)
        if got is not None: turns[t] = got
    # copy masks (prior assistant turns of the SAME dialogue as source, trimmed only)
    masked = {}
    for t, (toks, e114) in sorted(turns.items()):
        src = ngram_sets([turns[j][0] for j in range(1, t) if j in turns])
        mg = np.array([longest_suffix(toks, i, src) for i in range(len(toks))])
        masked[t] = (toks, e114, mg >= COPY_N)
    # per-dialogue midpoint between mean fresh and mean copied gate
    all_e = np.concatenate([m[1] for m in masked.values()]) if masked else np.array([])
    all_c = np.concatenate([m[2] for m in masked.values()]) if masked else np.array([], bool)
    if all_c.any() and (~all_c).any():
        fresh_mean, copied_mean = float(all_e[~all_c].mean()), float(all_e[all_c].mean())
        midpoint = 0.5 * (fresh_mean + copied_mean)
    else:
        fresh_mean = copied_mean = midpoint = None   # no copied (or no fresh) tokens -> no onsets usable
    dialogues[did] = dict(dataset=dataset, group=group, arm=arm, turns=masked,
                          fresh_mean=fresh_mean, copied_mean=copied_mean, midpoint=midpoint)

# ---------------------------------------------------------------- onset detection + lead

def find_runs(mask):
    """maximal runs of True -> list of (start, length)."""
    runs, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]: j += 1
            runs.append((i, j - i)); i = j
        else:
            i += 1
    return runs

def onsets_in_turn(mask, min_run, min_pre):
    out = []
    for start, length in find_runs(mask):
        if length < min_run: continue
        if start < min_pre: continue
        if mask[start - min_pre:start].any(): continue
        out.append((start, length))
    return out

def lead_at_onset(e114, midpoint, j):
    """(lead, censored, crossed) per the header definition."""
    n = len(e114)
    w0, w1 = max(0, j - WIN), min(n, j + WIN + 1)
    below = e114 < midpoint
    for i in range(w0, w1):
        if not below[i]: continue
        if i + SUSTAIN > n: break                      # cannot sustain to end of turn
        if not below[i:i + SUSTAIN].all(): continue
        if i == w0 and below[w0]:
            if i == 0 and j - WIN < 0:                 # window truncated by turn start
                return j - i, False, True              # true crossing at token 0? treat as censored below
            return j - w0, True, True                  # already below at window start (censored high)
        if i > 0 and below[i - 1]: continue            # not a downward crossing
        return j - i, False, True
    return None, True, False                            # no sustained crossing in window (censored low)

def collect(min_run, min_pre):
    onsets = []
    for did, d in dialogues.items():
        if d["midpoint"] is None: continue
        for t, (toks, e114, mask) in sorted(d["turns"].items()):
            for start, length in onsets_in_turn(mask, min_run, min_pre):
                lead, cens, crossed = lead_at_onset(e114, d["midpoint"], start)
                clamped = float(np.clip(lead, -WIN, WIN)) if lead is not None else -float(WIN)
                onsets.append(dict(
                    dataset=d["dataset"], dialogue=did, group=d["group"], arm=d["arm"],
                    turn=t, onset_index=int(start), run_length=int(length),
                    midpoint=round(d["midpoint"], 6),
                    gate_at_onset=round(float(e114[start]), 6),
                    lead=(int(lead) if lead is not None else None),
                    lead_clamped=clamped, censored=bool(cens), crossed=bool(crossed)))
    return onsets

def stats(onsets):
    if not onsets: return dict(n=0)
    lc = np.array([o["lead_clamped"] for o in onsets])
    unc = np.array([o["lead"] for o in onsets if not o["censored"]], dtype=float)
    lead_pos = np.array([(o["crossed"] and o["lead_clamped"] > 0) for o in onsets])
    d = dict(n=len(onsets),
             median_lead=float(np.median(lc)),
             iqr=[float(np.percentile(lc, 25)), float(np.percentile(lc, 75))],
             frac_gate_leading=float(lead_pos.mean()),
             n_gate_leading=int(lead_pos.sum()),
             n_censored_high=int(sum(o["censored"] and o["crossed"] for o in onsets)),
             n_censored_low_no_crossing=int(sum(not o["crossed"] for o in onsets)),
             n_uncensored=int(len(unc)))
    if len(unc):
        d["median_lead_uncensored"] = float(np.median(unc))
        d["iqr_uncensored"] = [float(np.percentile(unc, 25)), float(np.percentile(unc, 75))]
    return d

strict_onsets = collect(*STRICT)
relaxed_onsets = collect(*RELAXED)

# A_t0s0 (battery greedy re-baseline) is a TOKEN-IDENTICAL determinism re-capture of grid
# A_o1 (verified: all 14 turns identical token ids -> identical masks, onsets, leads).
# Counting it would double-count the same trajectory -> flag + exclude from primary stats.
DUP_DIALOGUE, DUP_OF = "A_t0s0", "A_o1"
for o in strict_onsets + relaxed_onsets:
    o["duplicate_of"] = DUP_OF if o["dialogue"] == DUP_DIALOGUE else None
strict_dedup = [o for o in strict_onsets if o["duplicate_of"] is None]
relaxed_dedup = [o for o in relaxed_onsets if o["duplicate_of"] is None]

S_all = stats(strict_dedup)                              # PRIMARY (de-duplicated)
S_incl = stats(strict_onsets)                            # secondary, incl. duplicate re-capture
S_greedy = stats([o for o in strict_dedup if o["group"] == "greedy"])
S_temp = stats([o for o in strict_dedup if o["group"] == "temperature"])
S_armA = stats([o for o in strict_dedup if o["arm"] == "A"])
S_armR = stats([o for o in strict_dedup if o["arm"] == "R"])
R_all = stats(relaxed_dedup)
R_incl = stats(relaxed_onsets)
R_greedy = stats([o for o in relaxed_dedup if o["group"] == "greedy"])
R_temp = stats([o for o in relaxed_dedup if o["group"] == "temperature"])

# ---------------------------------------------------------------- onset-aligned traces

def aligned_traces(onsets):
    """midpoint-relative gate, rows = onsets, cols = relative position -WIN..+WIN."""
    M = np.full((len(onsets), 2 * WIN + 1), np.nan)
    for r, o in enumerate(onsets):
        d = dialogues[o["dialogue"]]
        e114 = d["turns"][o["turn"]][1]
        j, n = o["onset_index"], len(e114)
        for k in range(-WIN, WIN + 1):
            if 0 <= j + k < n: M[r, k + WIN] = e114[j + k] - d["midpoint"]
    return M

M_greedy = aligned_traces([o for o in strict_dedup if o["group"] == "greedy"])
M_temp = aligned_traces([o for o in strict_dedup if o["group"] == "temperature"])
M_all = aligned_traces(strict_dedup)

# ---------------------------------------------------------------- figure
SURF, INK, INK2, GRID_A = "#fcfcfb", "#0b0b0b", "#52514e", 0.15
BLUE, AQUA = "#2a78d6", "#1baf7a"   # categorical slots 1 (greedy) and 2 (temperature)

fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), facecolor=SURF)
for ax in axes:
    ax.set_facecolor(SURF)
    ax.grid(alpha=GRID_A)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.tick_params(colors=INK2, labelsize=8)

ax = axes[0]
bins = np.arange(-WIN - 0.5, WIN + 1.5, 1.0)
lg = [o["lead_clamped"] for o in strict_dedup if o["group"] == "greedy"]
lt = [o["lead_clamped"] for o in strict_dedup if o["group"] == "temperature"]
ax.hist(lg, bins=bins, histtype="step", lw=2, color=BLUE, label=f"greedy (n={len(lg)})")
ax.hist(lt, bins=bins, histtype="step", lw=2, color=AQUA, label=f"temperature (n={len(lt)})")
ax.axvline(0, color=INK2, lw=1, ls=":")
ax.axvline(3, color=INK, lw=1, ls="--")
ax.annotate("original single-trajectory\nlead = +3", xy=(3, ax.get_ylim()[1] * 0.97),
            xytext=(5.5, ax.get_ylim()[1] * 0.86), fontsize=7.5, color=INK,
            arrowprops=dict(arrowstyle="-", color=INK, lw=0.8))
ax.set_xlabel("lead (tokens; >0 = gate crosses below midpoint BEFORE copy onset)",
              fontsize=8.5, color=INK)
ax.set_ylabel("copy-run onsets", fontsize=8.5, color=INK)
ax.set_title(f"Lead distribution across {len(strict_dedup)} copy-run onsets "
             f"(strict ≥12/≥12, de-duplicated; censored at ±{WIN})", fontsize=9.5, color=INK)
ax.legend(frameon=False, fontsize=8)

ax = axes[1]
x = np.arange(-WIN, WIN + 1)
ax.plot(x, np.nanmean(M_greedy, axis=0), color=BLUE, lw=2, label="greedy mean")
ax.plot(x, np.nanmean(M_temp, axis=0), color=AQUA, lw=2, label="temperature mean")
lo, hi = np.nanpercentile(M_all, 25, axis=0), np.nanpercentile(M_all, 75, axis=0)
ax.fill_between(x, lo, hi, color=INK2, alpha=0.12, lw=0, label="pooled IQR")
ax.axvline(0, color=INK2, lw=1, ls=":")
ax.axhline(0, color=INK2, lw=1, ls=":")
ax.annotate("copy-run onset", xy=(0, ax.get_ylim()[1] * 0.9), fontsize=7.5, color=INK2,
            ha="left", xytext=(0.8, ax.get_ylim()[1] * 0.9))
ax.set_xlabel("token position relative to copy-run onset", fontsize=8.5, color=INK)
ax.set_ylabel("E114 gate logit − dialogue midpoint", fontsize=8.5, color=INK)
ax.set_title("Onset-aligned average gate trace (strict onsets)", fontsize=9.5, color=INK)
ax.legend(frameon=False, fontsize=8)

fig.suptitle("Gate lead-lag replication across copy-run onsets — POST-HOC, NOT PREREGISTERED",
             fontsize=10, color=INK, y=1.00)
fig.tight_layout()
fig.savefig(HERE / "leadlag_replication.png", dpi=150, facecolor=SURF, bbox_inches="tight")

# ---------------------------------------------------------------- results.json

results = dict(
    label="POST-HOC DESCRIPTIVE ANALYSIS - NOT PREREGISTERED",
    question=("Does the E114 gate (gen_logit14) cross below the fresh/copied midpoint "
              "BEFORE the first token of a copy run? Replication of the paper's "
              "single-trajectory 3-token lead as a distribution."),
    copy_metric=dict(source="analyze_copy.py (replicated exactly)",
                     ngram_cap=NMAX, copy_threshold=COPY_N,
                     track="trimmed generated track only",
                     source_text="prior assistant turns of the same dialogue"),
    onset_definition=dict(strict=dict(min_run=STRICT[0], min_preceding_fresh=STRICT[1]),
                          relaxed=dict(min_run=RELAXED[0], min_preceding_fresh=RELAXED[1])),
    lead_definition=dict(window=WIN, sustain_tokens=SUSTAIN,
                         midpoint="per-dialogue (mean fresh gate + mean copied gate)/2",
                         censoring=f"already-below at window start -> +{WIN}; "
                                   f"no sustained crossing in window -> -{WIN}"),
    dialogues={did: dict(dataset=d["dataset"], group=d["group"], arm=d["arm"],
                         n_turns_loaded=len(d["turns"]),
                         fresh_mean=d["fresh_mean"], copied_mean=d["copied_mean"],
                         midpoint=d["midpoint"])
               for did, d in dialogues.items()},
    skipped_captures=skips,
    duplicate_note=(f"{DUP_DIALOGUE} verified token-identical to {DUP_OF} across all 14 turns "
                    "(greedy determinism re-capture); its onsets are flagged duplicate_of and "
                    "excluded from primary (de-duplicated) stats."),
    strict=dict(all=S_all, all_including_duplicate_recapture=S_incl,
                greedy=S_greedy, temperature=S_temp, armA=S_armA, armR=S_armR,
                onsets=strict_onsets),
    relaxed=dict(all=R_all, all_including_duplicate_recapture=R_incl,
                 greedy=R_greedy, temperature=R_temp, onsets=relaxed_onsets),
    original_result="single trajectory, gate crossed 3 tokens before onset (lead = +3)",
)
(HERE / "results.json").write_text(json.dumps(results, indent=1))

# ---------------------------------------------------------------- markdown report

def fmt_stats(s):
    if s.get("n", 0) == 0: return ["n = 0"]
    L = [f"n onsets = {s['n']}",
         f"median lead = {s['median_lead']:+.1f} tokens (IQR [{s['iqr'][0]:+.1f}, {s['iqr'][1]:+.1f}]; censored values clamped to ±{WIN})",
         f"fraction gate-leading (lead > 0) = {s['frac_gate_leading']:.3f} ({s['n_gate_leading']}/{s['n']})",
         f"censored: {s['n_censored_high']} already-below at window start (recorded +{WIN}), "
         f"{s['n_censored_low_no_crossing']} with no sustained crossing in window (recorded −{WIN})"]
    if "median_lead_uncensored" in s:
        L.append(f"uncensored-only (n={s['n_uncensored']}): median {s['median_lead_uncensored']:+.1f}, "
                 f"IQR [{s['iqr_uncensored'][0]:+.1f}, {s['iqr_uncensored'][1]:+.1f}]")
    return L

md = ["# Lead-lag replication: does the E114 gate cross before copy-run onsets?", "",
      "**POST-HOC DESCRIPTIVE ANALYSIS — NOT PREREGISTERED.**", "",
      "Referee point addressed: the paper's “gate leads degeneration” result was a single",
      "trajectory with a 3-token lead. Here the same ordering question is asked as a distribution",
      "across every clean copy-run onset in the conversational-dynamics data (grid arm A × 3",
      "orderings + convdyn-T battery A/R cells, greedy and temperature).", "",
      "## Method",
      f"- Copy metric: token-level longest suffix n-gram match (cap {NMAX}) vs prior assistant",
      f"  turns of the same dialogue, trimmed track only; in_copy8 = match ≥ {COPY_N}",
      "  (replicated exactly from `analyze_copy.py`).",
      f"- Onset (strict): first token of a maximal in_copy8 run of length ≥ {STRICT[0]}, preceded by",
      f"  ≥ {STRICT[1]} consecutive non-copy tokens. Relaxed variant: ≥ {RELAXED[0]} / ≥ {RELAXED[1]}.",
      f"- Gate series: `gen_logit14` (E114 router logit, L14), window ±{WIN} tokens around each onset.",
      "- Midpoint: per-dialogue midpoint between mean fresh-token gate and mean copied-token gate.",
      f"- Lead = onset index − first window index where the gate crosses below the midpoint and stays",
      f"  below ≥ {SUSTAIN} tokens. Lead > 0 = gate crossed BEFORE the onset token.",
      f"- Censoring: already below at window start → recorded +{WIN}; no sustained crossing in the",
      f"  window → recorded −{WIN}. Both flagged in results.json; uncensored-only stats also given.",
      "",
      f"## Data coverage",
      f"- Dialogues analysed: {len(dialogues)} (grid: A_o1/2/3 greedy; battery: A_t0s0, A_T05s0-2,",
      "  A_T07s0-2, R_t0s0, R_T07s0-2).",
      f"- Captures skipped for token/series alignment or missing data: {len(skips)}"
      + ("" if not skips else " — see results.json `skipped_captures`") + ".",
      f"- **De-duplication:** battery cell A_t0s0 is token-identical to grid A_o1 across all 14",
      "  turns (greedy determinism re-capture), so its onsets duplicate A_o1's exactly. Primary",
      "  stats below exclude it; results.json flags its onsets `duplicate_of: A_o1` and also",
      "  reports the including-duplicate totals.",
      "- Arm R (repeat-probe) contributes ZERO clean onsets at either threshold: in R dialogues",
      "  copying begins at the start of each turn, so no copy run is ever preceded by ≥ 8 fresh",
      "  tokens. All onsets below are arm A.",
      "",
      "## Strict onsets (run ≥ 12, preceded by ≥ 12 fresh) — PRIMARY, de-duplicated", ""]
md += [f"- {s}" for s in fmt_stats(S_all)]
md += [f"- including the A_t0s0 duplicate re-capture: n = {S_incl['n']}, median "
       f"{S_incl['median_lead']:+.1f}, gate-leading {S_incl['frac_gate_leading']:.3f}"]
md += ["", "### Split: greedy cells (grid A_o1/2/3; A_t0s0 excluded as duplicate)", ""]
md += [f"- {s}" for s in fmt_stats(S_greedy)]
md += ["", "### Split: temperature cells (T=0.5, T=0.7)", ""]
md += [f"- {s}" for s in fmt_stats(S_temp)]

def one_liner(s):
    if s.get("n", 0) == 0: return "n = 0 (no clean onsets)"
    return (f"n = {s['n']}, median {s['median_lead']:+.1f}, "
            f"gate-leading {s['frac_gate_leading']:.3f}")
md += ["", "### Split: arm A vs arm R (repeat-probe)", "",
       f"- arm A: {one_liner(S_armA)}",
       f"- arm R: {one_liner(S_armR)}",
       ""]
if S_all["n"] < 30:
    md += ["## Relaxed onsets (run ≥ 8, preceded by ≥ 8 fresh) — reported because strict n < 30", ""]
else:
    md += ["## Relaxed onsets (run ≥ 8, preceded by ≥ 8 fresh) — sensitivity variant", ""]
md += [f"- {s}" for s in fmt_stats(R_all)]
md += ["", f"- greedy: {one_liner(R_greedy)}",
       f"- temperature: {one_liner(R_temp)}",
       f"- including the A_t0s0 duplicate re-capture: n = {R_incl['n']}", ""]

# comparison sentence (filled with the actual numbers)
lc_dedup = np.array([o["lead_clamped"] for o in strict_dedup])
frac_ge3 = float((lc_dedup >= 3).mean())
if S_all["median_lead"] > 0 and S_all["frac_gate_leading"] > 0.5:
    verdict = "consistent with the original single-trajectory report of a +3-token gate lead"
else:
    verdict = ("the original single-trajectory +3-token gate lead does NOT replicate as the "
               "typical ordering — the typical gate crossing FOLLOWS the copy onset, and a lead "
               f"of ≥ +3 tokens occurs in only {frac_ge3:.0%} of onsets")
comp = (f"Across {S_all['n']} strict copy-run onsets (de-duplicated) the median lead is "
        f"{S_all['median_lead']:+.1f} tokens (IQR [{S_all['iqr'][0]:+.1f}, {S_all['iqr'][1]:+.1f}]), "
        f"with the gate crossing below the midpoint before the onset in "
        f"{S_all['frac_gate_leading']:.0%} of onsets ({S_all['n_gate_leading']}/{S_all['n']}): "
        f"{verdict}.")
md += ["## Comparison to the original result", "", comp, "",
       "![lead-lag figure](leadlag_replication.png)", "",
       "Figure: (left) distribution of per-onset leads, greedy vs temperature, with the original",
       "single-trajectory +3 lead marked; (right) onset-aligned average gate trace (midpoint-",
       "relative), pooled IQR band.", "",
       "*Post-hoc descriptive analysis; NOT preregistered. Onset/window/midpoint definitions were",
       "fixed before computing leads but after seeing the grid data in prior analyses.*"]
(HERE / "leadlag_replication.md").write_text("\n".join(md) + "\n")

print(json.dumps(dict(strict=S_all, greedy=S_greedy, temperature=S_temp,
                      relaxed_n=R_all.get("n"), skips=len(skips)), indent=1))
print(comp)
