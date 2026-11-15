# W5 results — dose-response titration of copy availability

Scored 2026-07-03, strictly against **`prereg_W5_dose_v1.json` v1.0** (frozen 2026-07-03 pre-capture),
sha256 `7bfc9c4dff252dc39a0c85382f9618c2f09c363bfeaf6991df99afc77178c47e` (verified against `W5_PREREG_SHA.txt`).
Histories `armW5_histories_v1.json` sha `9b027a35…` verified. Data: `pulled/A1_W5/w5.tgz` sha `7006fa1e…` verified,
15/15 captures present (P5_o{1..3}_d{0,2,4,6,7}), router npy shapes = (n_prompt+n_gen, 256) at layers 13/14/15/26,
probe and all seven history texts verified verbatim in each prompt, dose conditions follow the frozen latest-first rule.

![figure](results_W5.png)

## Prediction verdicts

| prediction | frozen rule (quoted) | outcome | verdict |
|---|---|---|---|
| W5-monotone | "pooled Spearman rho(floor_a, dose) > 0.8 across the 15 cells AND per-ordering dose curves nondecreasing with at most one adjacent violation in >= 2/3 orderings. Manipulation check (reported): measured copy fraction decreases with dose." | rho = **0.556** (fails > 0.8); nondecreasing ≤1 violation in **1/3** orderings (o1: 2, o2: 2, o3: 1) — both conjuncts fail | **NOT SUPPORTED** |
| W5-null | "complement" | — | **SUPPORTED** |

## Dose curves (floor_a = last-15 trimmed mean of the E114 L14 logit)

| ordering | d0 | d2 | d4 | d6 | d7 | adjacent violations |
|---|---|---|---|---|---|---|
| o1 | -6.693 | -6.798 | -6.036 | -5.168 | -6.277 | 2 (0→2, 6→7) |
| o2 | -6.313 | -4.568 | -5.001 | -4.700 | -4.756 | 2 (2→4, 6→7) |
| o3 | -6.422 | -6.512 | -5.981 | -5.786 | -5.527 | 1 (0→2) |
| pooled mean | -6.476 | -5.959 | -5.673 | -5.218 | -5.520 | — |

Pooled Spearman rho(floor_a, dose) = **0.5565** (tie-corrected, p = 0.031, n = 15). Direction positive but far below the frozen 0.8 bar.

## Manipulation check (reported per prereg, not scored)

| ordering | d0 | d2 | d4 | d6 | d7 |
|---|---|---|---|---|---|
| o1 | 0.939 | 0.939 | 0.791 | 0.156 | 0.746 |
| o2 | 0.856 | 0.014 | 0.465 | 0.069 | 0.112 |
| o3 | 0.950 | 0.606 | 0.289 | 0.135 | 0.078 |
| mean | 0.915 | 0.520 | 0.515 | 0.120 | 0.312 |

Measured copy fraction (vs the provided history) **decreases with dose overall** (Spearman rho = -0.628),
so the manipulation check passes directionally — but it is **leaky at the cell level**:
- **P5_o1_d7** copies its fully-paraphrased history heavily (copy fraction 0.746) and its floor stays cold (−6.277). This is
  the source-agnostic-copying pattern of convdyn-T T4's frozen interpretation fork, firing here in one of the three fully-paraphrased d7 cells.
- **P5_o2_d2** declines to copy although five verbatim turns are available (copy fraction 0.014) and its floor recovers (−4.568).
- P5_o1_d0/d2 pin at copy fraction 0.939 with the two coldest floors; dose 6 has lower measured copying (0.120) than dose 7 (0.312).

## Endpoint consistency with convdyn-T T4 (validity check per frozen caveat, not a prediction)

| ordering | W5 d0 floor | T4 replay floor | W5 d7 floor | T4 para floor | W5 Δ(d7−d0) | T4 Δ(para−replay) |
|---|---|---|---|---|---|---|
| o1 | -6.693 | -6.685 | -6.277 | -6.364 | +0.416 | +0.321 |
| o2 | -6.313 | -6.317 | -4.756 | -5.310 | +1.556 | +1.008 |
| o3 | -6.422 | -6.424 | -5.527 | -5.493 | +0.895 | +0.931 |
| pooled | | | | | +0.956 | +0.753 |

d0 floors reproduce the T4 replay floors to **≤ 0.011 in all three orderings** (same eog binary sha `8095c95e…`, different
box/GPU) — an unusually strong signature-level replication. d7 vs para floors agree within 0.09/0.55/0.03; Δ is positive 3/3
in both experiments and of comparable magnitude (pooled +0.956 here vs +0.753 in T4). The endpoints are consistent with T4;
the failure is in the interior of the dose curve. Copy-fraction endpoints also align: d0 0.939/0.856/0.950 vs T4 replay 0.947/0.856/0.961; d7 0.746/0.112/0.078 vs T4 para 0.815/0.212/0.039 (per ordering).

## Exploratory (NOT preregistered, clearly labeled)

Across the 15 cells, floor_a vs the *measured* copy fraction: Spearman rho = **-0.885** (p = 1.2e-05), Pearson r = -0.847.
The mediator→floor link is strong and in the predicted direction; what failed is dose→mediator (the paraphrase dose only
leakily controls how much the model actually copies). Strictly per the frozen rule, W5-monotone is unsupported and W5-null
stands; the exploratory pattern belongs in discussion, not in the verdict.

## Data-integrity flags & deviations

- floor_a computed as mean of the last 15 trimmed generated tokens of the E114 L14 router logit; trim by the frozen decoded-text rule (cut at first literal <|im_start|>/<|im_end|>/<|endoftext|>, token count via piece lengths; straddling token excluded). In P5_o1_* a ".<" merge token straddles the cut and is excluded (grid-v1.3-consistent).
- Copy-metric source = the 7 frozen provided-history assistant texts (armW5_histories_v1.json), token sequences recovered by char-span alignment on prompt_tokens.json; edge tokens straddling markup boundaries drop <=12 chars of ~600-950 per turn - negligible for the >=8-gram metric.
- Pooled Spearman computed tie-corrected (scipy) over the 15 cells; dose has 3-way ties by design.
- All 15 captures ran to the -n 180 cap (CAP_HIT); stop-at-eog was armed but the base surface emits <|im_end|> as BPE literals, so the text trim is binding, as expected.
- Same eog binary sha as convdyn-T, different box/GPU: endpoint comparison is signature-level per program policy, and in fact d0 floors reproduce T4 replay floors to <=0.011 in all three orderings.

Surfaces never pooled: all 15 W5 cells are scored alone; convdyn-T numbers appear only in the endpoint-consistency table,
clearly separated, per the frozen caveat. n=3 orderings sign-consistency caveat applies as frozen.
