# Lead-lag replication: does the E114 gate cross before copy-run onsets?

**POST-HOC DESCRIPTIVE ANALYSIS — NOT PREREGISTERED.**

Referee point addressed: the paper's “gate leads degeneration” result was a single
trajectory with a 3-token lead. Here the same ordering question is asked as a distribution
across every clean copy-run onset in the conversational-dynamics data (grid arm A × 3
orderings + convdyn-T battery A/R cells, greedy and temperature).

## Method
- Copy metric: token-level longest suffix n-gram match (cap 32) vs prior assistant
  turns of the same dialogue, trimmed track only; in_copy8 = match ≥ 8
  (replicated exactly from `analyze_copy.py`).
- Onset (strict): first token of a maximal in_copy8 run of length ≥ 12, preceded by
  ≥ 12 consecutive non-copy tokens. Relaxed variant: ≥ 8 / ≥ 8.
- Gate series: `gen_logit14` (E114 router logit, L14), window ±20 tokens around each onset.
- Midpoint: per-dialogue midpoint between mean fresh-token gate and mean copied-token gate.
- Lead = onset index − first window index where the gate crosses below the midpoint and stays
  below ≥ 3 tokens. Lead > 0 = gate crossed BEFORE the onset token.
- Censoring: already below at window start → recorded +20; no sustained crossing in the
  window → recorded −20. Both flagged in results.json; uncensored-only stats also given.

## Data coverage
- Dialogues analysed: 14 (grid: A_o1/2/3 greedy; battery: A_t0s0, A_T05s0-2,
  A_T07s0-2, R_t0s0, R_T07s0-2).
- Captures skipped for token/series alignment or missing data: 0.
- **De-duplication:** battery cell A_t0s0 is token-identical to grid A_o1 across all 14
  turns (greedy determinism re-capture), so its onsets duplicate A_o1's exactly. Primary
  stats below exclude it; results.json flags its onsets `duplicate_of: A_o1` and also
  reports the including-duplicate totals.
- Arm R (repeat-probe) contributes ZERO clean onsets at either threshold: in R dialogues
  copying begins at the start of each turn, so no copy run is ever preceded by ≥ 8 fresh
  tokens. All onsets below are arm A.

## Strict onsets (run ≥ 12, preceded by ≥ 12 fresh) — PRIMARY, de-duplicated

- n onsets = 55
- median lead = -8.0 tokens (IQR [-18.5, -5.0]; censored values clamped to ±20)
- fraction gate-leading (lead > 0) = 0.109 (6/55)
- censored: 1 already-below at window start (recorded +20), 11 with no sustained crossing in window (recorded −20)
- uncensored-only (n=43): median -6.0, IQR [-10.0, -4.5]
- including the A_t0s0 duplicate re-capture: n = 62, median -7.5, gate-leading 0.113

### Split: greedy cells (grid A_o1/2/3; A_t0s0 excluded as duplicate)

- n onsets = 21
- median lead = -7.0 tokens (IQR [-15.0, -6.0]; censored values clamped to ±20)
- fraction gate-leading (lead > 0) = 0.095 (2/21)
- censored: 0 already-below at window start (recorded +20), 3 with no sustained crossing in window (recorded −20)
- uncensored-only (n=18): median -6.5, IQR [-9.8, -3.0]

### Split: temperature cells (T=0.5, T=0.7)

- n onsets = 34
- median lead = -8.0 tokens (IQR [-19.0, -5.0]; censored values clamped to ±20)
- fraction gate-leading (lead > 0) = 0.118 (4/34)
- censored: 1 already-below at window start (recorded +20), 8 with no sustained crossing in window (recorded −20)
- uncensored-only (n=25): median -5.0, IQR [-10.0, -5.0]

### Split: arm A vs arm R (repeat-probe)

- arm A: n = 55, median -8.0, gate-leading 0.109
- arm R: n = 0 (no clean onsets)

## Relaxed onsets (run ≥ 8, preceded by ≥ 8 fresh) — sensitivity variant

- n onsets = 79
- median lead = -7.0 tokens (IQR [-19.0, -1.5]; censored values clamped to ±20)
- fraction gate-leading (lead > 0) = 0.228 (18/79)
- censored: 5 already-below at window start (recorded +20), 18 with no sustained crossing in window (recorded −20)
- uncensored-only (n=56): median -5.5, IQR [-10.0, -0.8]

- greedy: n = 22, median -7.5, gate-leading 0.091
- temperature: n = 57, median -7.0, gate-leading 0.281
- including the A_t0s0 duplicate re-capture: n = 86

## Comparison to the original result

Across 55 strict copy-run onsets (de-duplicated) the median lead is -8.0 tokens (IQR [-18.5, -5.0]), with the gate crossing below the midpoint before the onset in 11% of onsets (6/55): the original single-trajectory +3-token gate lead does NOT replicate as the typical ordering — the typical gate crossing FOLLOWS the copy onset, and a lead of ≥ +3 tokens occurs in only 11% of onsets.

![lead-lag figure](leadlag_replication.png)

Figure: (left) distribution of per-onset leads, greedy vs temperature, with the original
single-trajectory +3 lead marked; (right) onset-aligned average gate trace (midpoint-
relative), pooled IQR band.

*Post-hoc descriptive analysis; NOT preregistered. Onset/window/midpoint definitions were
fixed before computing leads but after seeing the grid data in prior analyses.*
