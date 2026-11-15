# §4 Axis Adjudication — the frozen regression (run of record)

**Run:** `s4_axis_adjudication_v1` · 2026-07-03T18:13:59.514403+00:00
**Frozen rule (prereg `bcccc6fe…`, verbatim):** Adjudication remains the S4 regression w114 ~ construction_proxy + intensity_rating + worldview_content_rating + mean_entropy. Construction wins ONLY if its coefficient survives partialling out BOTH worldview-content AND intensity. Named-target reads (X_god, H_mystic, H_philosopher) are qualitative discriminators, not the endpoint.

## Verdict

**CONSTRUCTION LOSES — the reframe FAILS on the vantage ladder, and affirmatively: the partialled construction coefficient is significantly NEGATIVE (beta=-0.327, p=0.0474, boot95=[-0.566,-0.067]), the OPPOSITE of the pre-registered direction, replicated in every screened sensitivity variant (interior-only p=0.0013; 1..64 p=0.0112; routing-entropy p=0.0041; Spearman-rank partial p=0.0499) WORLDVIEW-CONTENT is the only axis with a positive partialled contribution (beta=+0.508, p=0.0531 on the exact primary specification; significant in the pre-registered interior-only secondary (p=0.0168) and the frozen capture-config routing-entropy wording (p=0.0027)); INTENSITY carries nothing (p=0.28). Per the frozen rule the paper's ORIGINAL axis (worldview-content) STANDS — the honest null, reported as such.**

## Gates & provenance

- sha gates PASS: ratings lock `7dc963d31d2f…` (expected 7dc963d3…), prereg freeze
  `bcccc6fe3a51…` (expected bcccc6fe…), sealed sheet `f5067af8a3f5…` (f5067af8…).
- w114 recovery rel. residual 1.99e-05 (< 1e-3 gate); ratings gate NOT overridden;
  positive control d=2.93 PASS on the same surface (program record).
- Judges: openai/gpt-5.5-20260423 + google/gemini-3.1-pro-preview-20260219, temp 0, frozen rubric
  `ef491b083958…`; 6 items re-run per the disagreement rule; 2 persistent
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
**15 of 44 excluded** from the primary regression (reported alongside in the full-sample variant):

- A_bat: DEGENERATE (4-gram rep 0.736 > 0.5)
- A_child: DEGENERATE (4-gram rep 0.808 > 0.5)
- A_chimp: DEGENERATE (4-gram rep 0.568 > 0.5)
- A_dog: DEGENERATE (4-gram rep 0.776 > 0.5)
- A_dolphin: DEGENERATE (4-gram rep 0.960 > 0.5)
- H_philosopher: DEGENERATE (4-gram rep 0.696 > 0.5)
- H_recount: DEGENERATE (4-gram rep 0.896 > 0.5)
- I_fire: DEGENERATE (4-gram rep 0.864 > 0.5)
- I_gravel: DEGENERATE (4-gram rep 0.864 > 0.5)
- I_moon: DEGENERATE (4-gram rep 0.960 > 0.5)
- I_sea: DEGENERATE (4-gram rep 0.536 > 0.5)
- I_shadow: DEGENERATE (4-gram rep 0.824 > 0.5)
- I_wind: DEGENERATE (4-gram rep 0.816 > 0.5)
- X_god: DEGENERATE (4-gram rep 0.784 > 0.5)
- X_rock: DEGENERATE (4-gram rep 0.792 > 0.5)

Primary sample n = 29.

## Primary regression (declared first)

`w114_proj_1_128 ~ construction_proxy_net + intensity_rating + worldview_content_rating + mean_output_entropy`,
n=29, R²=0.663 (adj 0.607).

| regressor | β (std) | SE | t | p | partial r | ΔR² | VIF | boot 95% CI |
|---|---|---|---|---|---|---|---|---|
| construction_net | -0.327 | 0.156 | -2.09 | 0.0474 | -0.392 | 0.061 | 1.74 | [-0.566, -0.067] |
| intensity | +0.204 | 0.186 | +1.10 | 0.2820 | +0.219 | 0.017 | 2.46 | [-0.460, +1.372] |
| worldview | +0.508 | 0.250 | +2.03 | 0.0531 | +0.384 | 0.058 | 4.45 | [-0.643, +1.152] |
| entropy | -0.166 | 0.181 | -0.92 | 0.3686 | -0.184 | 0.012 | 2.33 | [-0.477, +0.442] |

- **Construction is sign-REVERSED**: the pre-registered direction is higher net → HIGHER E114;
  observed is significantly lower (β=-0.327, p=0.0474, bootstrap CI entirely negative).
- Spearman-rank partials (frozen robustness): construction -0.388
  (p=0.0499), intensity +0.043 (p=0.8354),
  worldview +0.304 (p=0.1315), entropy +0.115 (p=0.5770).
- VIF(worldview)=4.45 < 5 → the frozen collinearity trigger does NOT fire
  (primary claim stays on the OLS form); it is close to threshold, and partial-correlation forms are reported throughout anyway.
- Leave-one-out (frozen anchor list): X_god and X_rock are DEGENERATE-excluded from the primary sample;
  removing X_thermostat leaves the pattern unchanged (construction β −0.328, p=0.051; worldview β +0.524, p=0.060).
- Entropy-covariate wording: probe_spec says "mean_entropy", capture-config says "mean_routing_entropy";
  primary above uses mean_output_entropy (adjudication instruction), the routing-entropy wording is the
  sensitivity below — **the verdict is identical under both** (and sharper under the routing wording).

## Sensitivities (all frozen; same conclusion in every screened variant)

| variant | n | R² | construction β (p) | intensity β (p) | worldview β (p) | entropy β (p) |
|---|---|---|---|---|---|---|
| interior-only proxy (prereg secondary) | 29 | 0.744 | -0.480 (0.0013) | +0.182 (0.2723) | +0.531 (0.0168) | -0.273 (0.1001) |
| window 1..64 | 29 | 0.622 | -0.455 (0.0112) | +0.304 (0.1356) | +0.185 (0.4899) | -0.053 (0.7856) |
| window full | 29 | 0.371 | -0.388 (0.0814) | -0.211 (0.4141) | +0.690 (0.0543) | -0.609 (0.0214) |
| routing-entropy covariate (capture-config wording) | 29 | 0.782 | -0.403 (0.0041) | -0.052 (0.7523) | +0.584 (0.0027) | -0.403 (0.0009) |
| DEGENERATE included (n=44) | 44 | 0.173 | -0.065 (0.7313) | +0.114 (0.6040) | +0.262 (0.3263) | +0.027 (0.8913) |
| DEGENERATE incl., full window | 44 | 0.065 | -0.031 (0.8771) | -0.187 (0.4252) | +0.249 (0.3812) | -0.266 (0.2036) |
| DEGENERATE incl., interior proxy | 44 | 0.176 | -0.093 (0.6318) | +0.107 (0.6268) | +0.257 (0.3231) | +0.015 (0.9406) |

The DEGENERATE-included variants collapse to noise (R² ≤ 0.18, all n.s.) — exactly the
degeneration-darkening confound the screen was pre-specified to remove; the screened variants
all tell one story: construction negative, worldview the positive carrier, intensity nothing.

## Named cruxes (qualitative discriminators, not the endpoint — prereg wording)

| crux | proxy rank (net / interior) | observed w114 rank (of 44) | flags | intensity / worldview rating | read |
|---|---|---|---|---|---|
| X_god | 43/44 / 42/44 (construction FLOOR) | 27/44 | DEGENERATE (0.784) | 2.0 / 5.5 | mid-pack, not the ladder ceiling and not the construction floor; degenerate text → officially inconclusive, leans against BOTH strong readings |
| A_bat | 12/44 / 24/44 (mid) | 15/44 | DEGENERATE (0.736), RATER_DISAGREE(intensity) | 2.0 / 3.0 | mid-rank ≈ proxy mid-rank; prereg already demoted bat to non-decisive; degenerate → uninformative |
| H_mystic (dissociator) | 42/44 / 40/44 (construction near-floor) | **3/44 (2/29 screened)** | clean | 6.5 / 6.5 | **fires exactly as the frozen worldview reading predicts: E114 HIGH on matched-low construction → worldview wins** |
| H_philosopher (dissociator) | 26/44 / 32/44 | 23/44 | DEGENERATE (0.696) | 3.5 / 3.0 | generation degenerated; its actual text was NOT worldview-high (rated 3.0) — dissociator did not deploy as designed |
| I_moon vs I_bolt | interior-only: bolt #2 > moon #19 | moon 44/44 < bolt 21/44 | moon DEGENERATE (0.96) | — | direction matches attestation-not-animacy on the secondary metric, but moon's floor value is degeneration-darkened → weak support only |
| H_arithmetic (intensity control) | 29/44 | **2/44 (1/29 screened)** | clean | 2.0 / 2.0 | the screened sample's TOP target is low-worldview, low-intensity task talk — a residue no rated axis explains; noted honestly |
| H_recount | 44/44 (construction floor) | 38/44 | DEGENERATE (0.896) | 2.0 / 3.0 | low, as all readings predict |

Third-person worldview probes (no proxy, never in the regression, anchor the worldview axis
independently): WP_about_phil -3.66 vs WP_about_hist -5.80;
WP_phys_found -3.72 vs WP_phys_comp -5.27 — both pairs separate ~2 units
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
